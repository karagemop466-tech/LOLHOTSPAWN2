#!/usr/bin/env python3
"""External market lines for LoL matches.

Sources, in priority order:
  1. Pinnacle        - established sharp sportsbook, public guest JSON feed.
  2. Unibet (Kambi)  - established European/Australian sportsbook network, public Kambi JSON feed.
  3. Bovada          - established North-American sportsbook, public coupon JSON.
  4. Polymarket      - prediction market, public Gamma API.

Every price is de-vigged (two-way normalisation) before it is stored, and every
provider is deduplicated to at most one main match-winner market per fixture so
child prop boards can never inflate consensus counts. No price from Hotspawn is
used anywhere in this file.
"""
from __future__ import annotations

import json
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from lib_common import (clamp, decimal_from_american, devig_two, get_json, log,
                        norm, now_utc, utc_iso, write_json)

OUT = "data/cache/markets.json"
PIN_KEY = {"x-api-key": "CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R", "Accept": "application/json"}
PIN_BASE = "https://guest.api.arcadia.pinnacle.com/0.1"
PIN_PAGE = "https://guest.api.arcadia.pinnacle.com/0.1/sports/12/leagues?all=false"

UNIBET_APIS = (
    ("https://eu-offering-api.kambicdn.com/offering/v2018/ubca/listView/"
     "esports/league_of_legends/all/all/matches.json?lang=en_GB&market=ZZ&useCombined=true"),
    ("https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/"
     "esports/league_of_legends/all/all/matches.json?lang=en_GB&market=GB&useCombined=true"),
)
UNIBET_PAGE = "https://www.unibet.com.au/betting/sports/filter/esports/league_of_legends/all/matches"
UNIBET_EVENT_URL = "https://www.unibet.com.au/betting/sports/event/"

BOVADA_APIS = (
    ("https://www.bovada.lv/services/sports/event/coupon/events/A/description/"
     "esports?marketFilterId=def&preMatchOnly=true&lang=en"),
    ("https://www.bovada.lv/services/sports/event/coupon/events/A/description/"
     "esports/league-of-legends?marketFilterId=def&preMatchOnly=true&lang=en"),
    ("https://www.bovada.lv/services/sports/event/coupon/events/A/description/"
     "esports?marketFilterId=def&lang=en"),
)
BOVADA_PAGE = "https://www.bovada.lv/sports/esports/league-of-legends"
POLY_PAGE = "https://polymarket.com/event/"
POLY_API = "https://gamma-api.polymarket.com"

_LATIN_FOLD = str.maketrans({
    "Ø": "O", "ø": "o", "Æ": "AE", "æ": "ae", "Œ": "OE", "œ": "oe",
    "ß": "ss", "Đ": "D", "đ": "d", "Ł": "L", "ł": "l",
})
_PROP_CRIT_RE = re.compile(
    # Plural forms matter: books label these boards "Kills", "Maps", "Towers".
    # Deliberately no plural on "odd", because "Match Odds" is the main market.
    r"\b(maps?|games?|kills?|towers?|turrets?|dragons?|barons?|inhibitors?|handicaps?|"
    r"totals?|over|under|first|blood|scores?|odd|even|duration|nashors?)\b",
    re.I,
)


def _norm_team(s: str) -> str:
    return norm((s or "").translate(_LATIN_FOLD))


def _dedup_key(team_a: str, team_b: str, start_utc: str) -> tuple:
    pair = tuple(sorted((_norm_team(team_a), _norm_team(team_b))))
    return (pair, (start_utc or "")[:10])


def _record(source_name, source_key, competition, start, team_a, team_b, prob_a, prob_b,
            url, decimal_a=None, decimal_b=None, note="", raw=None):
    if not team_a or not team_b or start is None:
        return None
    if _norm_team(team_a) in ("", "tbd") or _norm_team(team_b) in ("", "tbd"):
        return None
    if _norm_team(team_a) == _norm_team(team_b):
        return None
    pa, pb = clamp(prob_a), clamp(prob_b)
    s = pa + pb
    return {
        "source": source_name,
        "source_key": source_key,
        "competition": competition or "",
        "start_utc": utc_iso(start),
        "team_a": team_a,
        "team_b": team_b,
        "prob_a": round(pa / s, 4),
        "prob_b": round(pb / s, 4),
        "decimal_a": round(decimal_a, 4) if decimal_a else None,
        "decimal_b": round(decimal_b, 4) if decimal_b else None,
        "url": url,
        "note": note,
        "raw": raw or {},
    }


def _select_pinnacle_moneyline(markets: list[dict], matchup_id: int) -> dict | None:
    """Select the parent full-match/series moneyline (period == 0) for matchup_id only.

    Never fall back to period != 0 (Map 1/2/3) or child prop matchups (Kills,
    Towers, Dragons, Barons, Inhibitors), which share related straight markets
    in Pinnacle's Arcadia API.
    """
    for mk in markets or []:
        if mk.get("matchupId") != matchup_id:
            continue
        if mk.get("type") != "moneyline" or mk.get("period") != 0:
            continue
        if mk.get("isAlternate"):
            continue
        if mk.get("status") not in (None, "open"):
            continue
        prices = {p.get("designation"): p.get("price") for p in mk.get("prices") or []}
        if "home" in prices and "away" in prices:
            return mk
    return None


def fetch_pinnacle() -> dict:
    status = {"source": "Pinnacle", "key": "pinnacle", "url": PIN_PAGE, "status": "error", "count": 0}
    sports, r = get_json(f"{PIN_BASE}/sports", PIN_KEY)
    if not isinstance(sports, list):
        status["error"] = f"sports feed HTTP {r.get('status')}"
        return {"status": status, "records": []}
    esports = [s for s in sports if s.get("id") == 12 or "esport" in str(s.get("name", "")).lower()]
    records = []
    seen = set()
    leagues_seen = []
    skipped_children = 0
    for sport in esports:
        leagues, _ = get_json(f"{PIN_BASE}/sports/{sport['id']}/leagues", PIN_KEY)
        if not isinstance(leagues, list):
            continue
        for league in leagues:
            name = str(league.get("name") or "")
            if "league of legends" not in name.lower():
                continue
            leagues_seen.append(name)
            lid = league.get("id")
            matchups, _ = get_json(f"{PIN_BASE}/leagues/{lid}/matchups", PIN_KEY)
            if not isinstance(matchups, list):
                continue
            straight, _ = get_json(f"{PIN_BASE}/leagues/{lid}/markets/straight", PIN_KEY)
            by_mid: dict[int, list[dict]] = defaultdict(list)
            if isinstance(straight, list):
                for mk in straight:
                    if isinstance(mk, dict) and mk.get("matchupId") is not None:
                        by_mid[mk["matchupId"]].append(mk)

            for m in matchups:
                # Exclude child prop matchups (Kills/Towers/Dragons/Barons/Inhibitors),
                # specials/outrights, and live in-play boards.
                if m.get("type") != "matchup" or m.get("isLive"):
                    continue
                if m.get("parentId") is not None or str(m.get("units") or "Regular") != "Regular":
                    skipped_children += 1
                    continue
                parts = m.get("participants") or []
                if len(parts) != 2 or not m.get("hasMarkets"):
                    continue
                p_home = next((p for p in parts if p.get("alignment") == "home"), parts[0])
                p_away = next((p for p in parts if p.get("alignment") == "away"), parts[1])
                start = m.get("startTime")
                try:
                    start_dt = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
                except Exception:
                    continue
                mid = m.get("id")
                cands = by_mid.get(mid) or []
                if not cands:
                    rel, _ = get_json(f"{PIN_BASE}/matchups/{mid}/markets/related/straight", PIN_KEY)
                    if isinstance(rel, list):
                        cands = rel
                    time.sleep(0.1)
                ml = _select_pinnacle_moneyline(cands, mid)
                if not ml:
                    continue
                prices = {p.get("designation"): p.get("price") for p in ml.get("prices") or []}
                da = decimal_from_american(prices.get("home"))
                db = decimal_from_american(prices.get("away"))
                dv = devig_two(da, db)
                if not dv:
                    continue
                pin_url = f"{PIN_BASE}/matchups/{mid}/markets/related/straight" if mid else PIN_PAGE
                rec = _record(
                    "Pinnacle", "pinnacle", name, start_dt,
                    p_home.get("name"), p_away.get("name"), dv[0], dv[1],
                    pin_url, da, db,
                    note=f"Pinnacle series moneyline (matchup {mid})",
                    raw={"matchup_id": mid, "league_id": lid,
                         "american_home": prices.get("home"), "american_away": prices.get("away"),
                         "market_type": "series",
                         "api": f"{PIN_BASE}/leagues/{lid}/markets/straight"},
                )
                if rec:
                    dk = _dedup_key(rec["team_a"], rec["team_b"], rec["start_utc"])
                    if dk not in seen:
                        seen.add(dk)
                        records.append(rec)
            time.sleep(0.15)
    status.update({
        "status": "ok" if records else "no_data",
        "count": len(records),
        "leagues": leagues_seen,
        "skipped_child_matchups": skipped_children,
        "note": "Public guest JSON feed (parent Regular moneylines only); re-check pinnacle.com before betting.",
    })
    return {"status": status, "records": records}


def _select_unibet_offer(bet_offers: list[dict]) -> dict | None:
    """Pick the main 2-way pre-match Match Odds offer; reject maps/handicaps/totals/props."""
    best = None
    best_rank = 0
    for bo in bet_offers or []:
        if not isinstance(bo, dict):
            continue
        btype = bo.get("betOfferType") or {}
        if btype.get("id") != 2 and str(btype.get("englishName") or "").lower() != "match":
            continue
        crit_obj = bo.get("criterion") or {}
        crit = str(crit_obj.get("englishLabel") or crit_obj.get("label") or "").strip()
        if _PROP_CRIT_RE.search(crit):
            continue
        if crit.lower() not in ("match odds", "match", "winner", "match winner", "full time"):
            continue
        outs = [o for o in (bo.get("outcomes") or []) if o.get("status") in (None, "OPEN")]
        if len(outs) != 2:
            continue
        tags = bo.get("tags") or []
        if tags and "OFFERED_PREMATCH" not in tags and "MAIN" not in tags:
            continue
        rank = 2 if "MAIN" in tags else 1
        if rank > best_rank:
            best, best_rank = bo, rank
    return best


def fetch_unibet() -> dict:
    status = {"source": "Unibet", "key": "unibet", "url": UNIBET_PAGE, "status": "error", "count": 0}
    data, r, used = None, {}, None
    for url in UNIBET_APIS:
        data, r = get_json(url, headers={"Accept": "application/json"})
        if isinstance(data, dict) and isinstance(data.get("events"), list):
            used = url
            break
        time.sleep(0.4)
    if not (isinstance(data, dict) and isinstance(data.get("events"), list)):
        status["error"] = f"Kambi feed HTTP {r.get('status')} (no events list)"
        return {"status": status, "records": []}
    status["feed"] = used
    records = []
    seen = set()
    groups = set()
    for item in data.get("events") or []:
        ev = (item or {}).get("event") or {}
        if str(ev.get("state") or "NOT_STARTED") != "NOT_STARTED":
            continue
        ev_tags = ev.get("tags") or ["MATCH"]
        if "MATCH" not in ev_tags:
            continue
        ta = str(ev.get("homeName") or "").strip()
        tb = str(ev.get("awayName") or "").strip()
        if not ta or not tb:
            continue
        try:
            start_dt = datetime.fromisoformat(str(ev.get("start") or "").replace("Z", "+00:00"))
        except Exception:
            continue
        bo = _select_unibet_offer(item.get("betOffers") or [])
        if not bo:
            continue
        outs = [o for o in (bo.get("outcomes") or []) if o.get("status") in (None, "OPEN")]
        o_home = next((o for o in outs if o.get("type") == "OT_ONE"), None)
        o_away = next((o for o in outs if o.get("type") == "OT_TWO"), None)
        if not o_home or not o_away:
            continue
        try:
            da = float(o_home.get("odds") or 0) / 1000.0
            db = float(o_away.get("odds") or 0) / 1000.0
        except (TypeError, ValueError):
            continue
        dv = devig_two(da, db)
        if not dv:
            continue
        ev_id = ev.get("id")
        comp = str(ev.get("group") or "League of Legends")
        groups.add(comp)
        ev_url = f"{UNIBET_EVENT_URL}{ev_id}" if ev_id else UNIBET_PAGE
        rec = _record(
            "Unibet", "unibet", comp, start_dt, ta, tb, dv[0], dv[1],
            ev_url, da, db,
            note=f"Unibet (Kambi) Match Odds (event {ev_id})",
            raw={"event_id": ev_id, "bet_offer_id": bo.get("id"),
                 "american_home": o_home.get("oddsAmerican"),
                 "american_away": o_away.get("oddsAmerican"),
                 "market_type": "series"},
        )
        if rec:
            dk = _dedup_key(rec["team_a"], rec["team_b"], rec["start_utc"])
            if dk not in seen:
                seen.add(dk)
                records.append(rec)
    status.update({
        "status": "ok" if records else "no_data",
        "count": len(records),
        "competitions": sorted(groups),
        "note": "Public Kambi pre-match Match Odds feed powering Unibet.",
    })
    return {"status": status, "records": records}


def _bovada_groups(data):
    """Accept a list of coupon groups, a bare event list, or a wrapped object."""
    if isinstance(data, dict):
        for key in ("events", "data", "results"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
    if not isinstance(data, list):
        return []
    if data and isinstance(data[0], dict) and "competitors" in data[0]:
        return [{"path": [], "events": data}]
    return data


def _bovada_series_moneyline(mk: dict) -> bool:
    """True only for Bovada's full-series (head-to-head) moneyline.

    Bovada labels the full-event period ``Game`` with ``main: true``
    (display group "Game Lines", descriptionKey "Head To Head") — the same
    period carries the series map-total (e.g. Total 4.5 in a Bo5), so it is
    the series market, not Map 1. Numbered periods ("Game 1", "Map 2") and
    any explicit map period are single-game markets and stay rejected.
    Evidence: committed coupon snapshot ``data/diag/bovada_prematch.json``
    (Worlds + EMEA Masters events, replayed in
    ``verification/test_entity_and_books.py``). The previous rule rejected
    every market whose period contained "game", which silently discarded
    100% of Bovada LoL moneylines (status ``no_data`` during Worlds).
    """
    if str(mk.get("description", "")).strip().lower() != "moneyline":
        return False
    if mk.get("status") not in (None, "O", "OPEN"):
        return False
    if len(mk.get("outcomes") or []) != 2:
        return False
    period = mk.get("period") or {}
    prd = str(period.get("description") or "").strip().lower()
    if re.search(r"(game|map)\s*\d", prd) or "map" in prd:
        return False
    if period.get("main") is True:
        return prd in ("game", "match", "full game", "full match", "")
    # No explicit main flag: only accept an unnumbered full-event period.
    return prd in ("game", "match", "full game", "full match", "")


def _parse_bovada_groups(groups: list) -> tuple[list, list, int]:
    """Parse coupon groups into (records, competition names, events seen)."""
    records = []
    seen = set()
    comps = []
    events_seen = 0
    for group in groups:
        if not isinstance(group, dict):
            continue
        path = group.get("path") or []
        if path and not any(
            "/league-of-legends" in str(p.get("link") or "").lower()
            or "league of legends" in str(p.get("description") or "").lower()
            for p in path if isinstance(p, dict)
        ):
            continue
        comp = path[0].get("description") if path and isinstance(path[0], dict) else "League of Legends"
        if comp and comp not in comps:
            comps.append(comp)
        for ev in group.get("events") or []:
            events_seen += 1
            if ev.get("live"):
                continue
            comps_names = [c.get("name") for c in ev.get("competitors") or []]
            if len(comps_names) != 2:
                continue
            try:
                start_dt = datetime.fromtimestamp(int(ev["startTime"]) / 1000.0, timezone.utc)
            except Exception:
                continue
            market = None
            for dg in ev.get("displayGroups") or []:
                for mk in dg.get("markets") or []:
                    if _bovada_series_moneyline(mk):
                        market = mk
                        break
                if market:
                    break
            if not market:
                continue
            outs = market["outcomes"]
            da = float(outs[0].get("price", {}).get("decimal") or 0) or None
            db = float(outs[1].get("price", {}).get("decimal") or 0) or None
            dv = devig_two(da, db)
            if not dv:
                continue
            ev_link = str(ev.get("link") or "").strip()
            if ev_link:
                if ev_link.startswith("http"):
                    bov_url = ev_link
                elif ev_link.startswith("/sports/"):
                    bov_url = "https://www.bovada.lv" + ev_link
                elif ev_link.startswith("/"):
                    bov_url = "https://www.bovada.lv/sports" + ev_link
                else:
                    bov_url = "https://www.bovada.lv/sports/" + ev_link
            else:
                bov_url = BOVADA_PAGE
            rec = _record(
                "Bovada", "bovada", comp, start_dt,
                outs[0].get("description"), outs[1].get("description"), dv[0], dv[1],
                bov_url, da, db,
                note=f"Bovada moneyline (event {ev.get('id')})",
                raw={"event_id": ev.get("id"), "market_type": "series",
                     "american_a": outs[0].get("price", {}).get("american"),
                     "american_b": outs[1].get("price", {}).get("american")},
            )
            if rec:
                dk = _dedup_key(rec["team_a"], rec["team_b"], rec["start_utc"])
                if dk not in seen:
                    seen.add(dk)
                    records.append(rec)
    return records, comps, events_seen


def fetch_bovada() -> dict:
    status = {"source": "Bovada", "key": "bovada", "url": BOVADA_PAGE, "status": "error", "count": 0}
    data, r, used = None, {}, None
    for url in BOVADA_APIS:
        data, r = get_json(url, headers={"Referer": BOVADA_PAGE, "Origin": "https://www.bovada.lv"})
        groups = _bovada_groups(data)
        if any(g.get("events") for g in groups if isinstance(g, dict)):
            used = url
            break
        time.sleep(0.5)
    groups = _bovada_groups(data)
    if not groups:
        status["error"] = f"coupon feed HTTP {r.get('status')} (no event groups)"
        return {"status": status, "records": []}
    status["feed"] = used or BOVADA_APIS[0]
    records, comps, events_seen = _parse_bovada_groups(groups)
    status.update({"status": "ok" if records else "no_data", "count": len(records),
                   "competitions": comps, "events_seen": events_seen,
                   "note": ("Public Bovada pre-match League of Legends coupon JSON (2-way main moneyline only)."
                            if records else
                            f"Bovada coupon feed reachable ({events_seen} LoL event(s) listed); "
                            "0 open pre-match full-series moneylines parsed; no Bovada price used.")})
    return {"status": status, "records": records}


def _poly_teams(title: str):
    m = re.match(r"^\s*LoL:\s*(.+?)\s+vs\.?\s+(.+?)\s*(?:\((?:BO\d+)\))?\s*[-–—]", title or "", re.I)
    if not m:
        m = re.match(r"^\s*LoL:\s*(.+?)\s+vs\.?\s+(.+?)\s*\((?:BO\d+)\)", title or "", re.I)
    return (m.group(1).strip(), m.group(2).strip()) if m else (None, None)


def _poly_best_of(title: str) -> int | None:
    m = re.search(r"\(BO([1235])\)", title or "", re.I)
    return int(m.group(1)) if m else None


def _select_poly_market(ev: dict, a: str, b: str, title: str):
    """Pick the best market for a match.

    Preference: event-level market > explicit series/match-winner > neutral >
    single-game. Any Game-N/Map-N child market is tagged "game" and is only
    usable for a fixture that is known to be a Bo1 (checked by the model).
    """
    chosen, chosen_rank, chosen_kind = None, 0, None
    for mk in ev.get("markets") or []:
        try:
            outs = json.loads(mk.get("outcomes") or "[]")
            prices = [float(x) for x in json.loads(mk.get("outcomePrices") or "[]")]
        except Exception:
            continue
        if len(outs) != 2 or len(prices) != 2:
            continue
        if {str(outs[0]).strip().lower(), str(outs[1]).strip().lower()} != {a.lower(), b.lower()}:
            continue
        q = (mk.get("question") or "").lower()
        label = (mk.get("groupItemTitle") or "").lower()
        blob = f"{q} {label}"
        is_single = bool(re.search(r"(game|map)\s*\d+", blob))
        is_series = ("match winner" in blob) or ("series winner" in blob) or ("series" in label)
        if is_single:
            rank, kind = 1, "game"
        elif is_series:
            rank, kind = 3, "series"
        else:
            rank, kind = 2, "series"
        if not is_single and q.strip() == title.strip().lower():
            rank = 4
        if rank > chosen_rank:
            chosen, chosen_rank, chosen_kind = (outs, prices, mk), rank, kind
        if rank == 4:
            break
    if not chosen:
        return None
    outs, prices, mk = chosen
    return outs, prices, mk, chosen_kind


def fetch_polymarket() -> dict:
    status = {"source": "Polymarket", "key": "polymarket", "url": POLY_API, "status": "error", "count": 0}
    events = []
    for offset in (0, 100):
        url = (f"{POLY_API}/events?tag_slug=league-of-legends&active=true&closed=false"
               f"&limit=100&offset={offset}")
        data, r = get_json(url)
        if isinstance(data, list):
            events += data
        else:
            status.setdefault("errors", []).append(f"offset {offset}: HTTP {r.get('status')}")
        time.sleep(0.4)
    now = now_utc()
    records = []
    seen = set()
    for ev in events:
        title = ev.get("title") or ""
        a, b = _poly_teams(title)
        if not a or not b:
            continue
        end = None
        for dt_key in ("startDate", "endDate"):
            if ev.get(dt_key):
                try:
                    cand = datetime.fromisoformat(str(ev.get(dt_key)).replace("Z", "+00:00"))
                    if dt_key == "endDate" or cand >= now - timedelta(days=2):
                        end = cand
                except Exception:
                    pass
        try:
            end = datetime.fromisoformat(str(ev.get("endDate")).replace("Z", "+00:00"))
        except Exception:
            pass
        if end and (end < now - timedelta(days=2) or end > now + timedelta(days=21)):
            continue
        chosen = _select_poly_market(ev, a, b, title)
        if not chosen:
            continue
        outs, prices, mk, market_type = chosen
        if str(outs[0]).strip().lower() == a.lower():
            pa, pb = prices[0], prices[1]
        else:
            pa, pb = prices[1], prices[0]
        bo_num = _poly_best_of(title)
        rec = _record(
            "Polymarket", "polymarket", "Polymarket: " + title, end, a, b, pa, pb,
            POLY_PAGE + str(ev.get("slug") or ""),
            note=f"Polymarket: {mk.get('question')}",
            raw={"event_slug": ev.get("slug"), "market": mk.get("question"),
                 "group": mk.get("groupItemTitle"),
                 "market_type": market_type, "best_of": bo_num,
                 "volume": ev.get("volume"), "liquidity": ev.get("liquidity")},
        )
        if rec:
            dk = _dedup_key(rec["team_a"], rec["team_b"], rec["start_utc"])
            if dk not in seen:
                seen.add(dk)
                records.append(rec)
    status.update({
        "status": "ok" if records else "no_data",
        "count": len(records),
        "events_seen": len(events),
        "note": "Public Polymarket Gamma API series/match-winner prices (view-only in US; reference data only).",
    })
    return {"status": status, "records": records}


def main() -> int:
    results = []
    statuses = []
    for fn in (fetch_pinnacle, fetch_unibet, fetch_bovada, fetch_polymarket):
        try:
            out = fn()
        except Exception as e:  # noqa: BLE001 - one broken book must not stop the run
            log(f"{fn.__name__} crashed: {e!r}")
            out = {"status": {"source": fn.__name__, "key": fn.__name__, "status": "error",
                              "error": repr(e)[:200], "count": 0}, "records": []}
        statuses.append(out["status"])
        results += out["records"]
        log(f"markets: {out['status'].get('source')} -> {out['status'].get('status')} "
            f"({out['status'].get('count', 0)} records)")
    payload = {"generated_at": utc_iso(now_utc()), "statuses": statuses,
               "count": len(results), "records": results}
    write_json(OUT, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

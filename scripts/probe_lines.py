#!/usr/bin/env python3
"""Probe betting-line sources for the fixtures our model currently has to price.

Why this file exists
--------------------
On 2026-10-24 the published payload had 169 fixtures and only 9 of them had an
external betting line. Pinnacle's own league index listed a single League of
Legends competition (the World Championship), so PRM 2nd/3rd Division, RIVALS
LEAGUE, Tunisian Super League, Arabian League 2nd Division, 4 Nations,
Komplettligaen, LCP Promotion and LigaGG were priced by our Elo model alone.

The brief asks for external lines wherever they exist, in this order:
  1. established League of Legends betting sites,
  2. esportsbooks,
  3. esports betting lines / aggregators.

This probe does not price anything. It asks, source by source, one question:
*can we read structured per-match two-way prices from CI, and do any of them
actually belong to a fixture we currently price with the model?* For each
candidate it records the HTTP status, whether the payload is JSON, how many
two-way prices were extracted, and how many of the currently unpriced Hotspawn
fixtures those prices would cover.

Output: data/diag/line_probe.json (committed for manual review).
A source is promoted into scripts/fetch_markets.py only if this probe shows
structured per-match prices that match real fixtures, and the sample rows are
re-checked by hand. The exit code is always 0: a probe must never break a run.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher

from lib_common import fetch, get_json, log, norm, now_utc, parse_iso, utc_iso, write_json

OUT = "data/diag/line_probe.json"
PICKS = "docs/data/picks.json"

_LATIN_FOLD = str.maketrans({
    "Ø": "O", "ø": "o", "Æ": "AE", "æ": "ae", "Œ": "OE", "œ": "oe",
    "ß": "ss", "Đ": "D", "đ": "d", "Ł": "L", "ł": "l",
})

# Established LoL betting sites / Kambi-powered sportsbooks.
KAMBI_OPERATORS = [
    ("Unibet", "ub", "GB"),
    ("Betsson", "betsson", "SE"),
    ("NordicBet", "nordicbet", "SE"),
    ("LeoVegas", "leovegas", "SE"),
    ("Unibet FR", "ubfr", "FR"),
    ("Unibet IT", "ubit", "IT"),
    ("Betcity", "betcity", "NL"),
]


def _key(s) -> str:
    return norm((s or "").translate(_LATIN_FOLD))


def _similar(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.95 if min(len(a), len(b)) >= 4 else 0.6
    return SequenceMatcher(None, a, b).ratio()


class FixtureIndex:
    """Loose name/date matcher against the published fixture list."""

    def __init__(self, matches):
        self.matches = matches
        self.unpriced = {m["id"] for m in matches if not m.get("market")}

    def match(self, team_a, team_b, start, hours: int = 48):
        ka, kb = _key(team_a), _key(team_b)
        if not ka or not kb or ka == kb:
            return None
        start_dt = parse_iso(start) if start is not None else None
        best, best_score = None, 0.0
        for m in self.matches:
            m1, m2 = _key(m.get("team1")), _key(m.get("team2"))
            if not m1 or not m2:
                continue
            direct = min(_similar(ka, m1), _similar(kb, m2))
            swapped = min(_similar(ka, m2), _similar(kb, m1))
            score = max(direct, swapped)
            if score < 0.82:
                continue
            if start_dt:
                mdt = parse_iso(m.get("start_utc"))
                if mdt and abs((start_dt - mdt).total_seconds()) > hours * 3600:
                    continue
            if score > best_score:
                best, best_score = m, score
        return (best, round(best_score, 3)) if best else None


def _two_way(records, source, url, competition="", start=None, team_a=None, team_b=None,
             dec_a=None, dec_b=None, note=""):
    """Append a normalised two-way candidate record; skip anything incomplete."""
    try:
        da, db = float(dec_a), float(dec_b)
    except (TypeError, ValueError):
        return None
    if da <= 1.0 or db <= 1.0 or da > 60 or db > 60:
        return None
    return {
        "source": source, "url": url, "competition": competition or "",
        "start": utc_iso(parse_iso(start)) if start is not None else None,
        "team_a": str(team_a or "").strip(), "team_b": str(team_b or "").strip(),
        "decimal_a": round(da, 4), "decimal_b": round(db, 4), "note": note,
    }


# --------------------------------------------------------------------------- #
# 1. Kambi-powered sportsbooks (established betting sites)
# --------------------------------------------------------------------------- #
def probe_kambi(op_name, op_slug, market):
    name = f"Kambi / {op_name}"
    url = ("https://eu-offering-api.kambicdn.com/offering/v2018/"
           f"{op_slug}/listView/esports/league_of_legends/all/all/matches.json"
           f"?lang=en_GB&market={market}&useCombined=true")
    data, r = get_json(url, headers={"Accept": "application/json"}, retries=1)
    recs, comps = [], []
    if isinstance(data, dict) and isinstance(data.get("events"), list):
        for item in data["events"]:
            ev = (item or {}).get("event") or {}
            comp = str(ev.get("group") or "")
            if comp and comp not in comps:
                comps.append(comp)
            best = None
            for bo in item.get("betOffers") or []:
                btype = (bo.get("betOfferType") or {})
                if btype.get("id") != 2 and str(btype.get("englishName") or "").lower() != "match":
                    continue
                crit = str((bo.get("criterion") or {}).get("englishLabel") or "").lower()
                if crit not in ("match odds", "match", "winner", "match winner", "full time"):
                    continue
                outs = [o for o in (bo.get("outcomes") or []) if o.get("status") in (None, "OPEN")]
                if len(outs) != 2:
                    continue
                best = best or outs
            if not best:
                continue
            o1 = next((o for o in best if o.get("type") == "OT_ONE"), None)
            o2 = next((o for o in best if o.get("type") == "OT_TWO"), None)
            if not o1 or not o2:
                continue
            rec = _two_way(recs, name, url, comp, ev.get("start"), ev.get("homeName"),
                           ev.get("awayName"), (o1.get("odds") or 0) / 1000.0,
                           (o2.get("odds") or 0) / 1000.0)
            if rec:
                recs.append(rec)
    return {
        "name": name, "kind": "established-sportsbook", "url": url,
        "http_status": r.get("status"), "bytes": len(r.get("text") or ""),
        "is_json": isinstance(data, dict), "competitions": comps[:25],
        "records": recs,
        "error": None if recs else (r.get("error") or "no two-way Match Odds market found"),
    }


# --------------------------------------------------------------------------- #
# 2. SofaScore (esports results + bookmaker odds aggregator, public JSON)
# --------------------------------------------------------------------------- #
def probe_sofascore(days: int = 3):
    name = "SofaScore (esports schedule + odds)"
    base = "https://api.sofascore.com/api/v1"
    recs, comps, status, bytes_total, detail = [], [], None, 0, {}
    day = now_utc().date()
    for i in range(days):
        d = (day + timedelta(days=i)).isoformat()
        data, r = get_json(f"{base}/sport/esports/scheduled-events/{d}", retries=1)
        status = status or r.get("status")
        bytes_total += len(r.get("text") or "")
        if not isinstance(data, dict) or not isinstance(data.get("events"), list):
            continue
        for ev in data["events"]:
            tour = (ev.get("tournament") or {})
            cat = str((tour.get("category") or {}).get("name") or "")
            ut = str((tour.get("uniqueTournament") or {}).get("name") or tour.get("name") or "")
            if "league of legends" not in cat.lower() and "league of legends" not in ut.lower() \
                    and "lol" not in ut.lower():
                continue
            comp = ut or cat
            if comp not in comps:
                comps.append(comp)
            recs.append({"source": name, "url": "https://www.sofascore.com/esports/league-of-legends",
                         "competition": comp, "start": utc_iso(parse_iso(ev.get("startTimestamp"))),
                         "team_a": str((ev.get("homeTeam") or {}).get("name") or ""),
                         "team_b": str((ev.get("awayTeam") or {}).get("name") or ""),
                         "decimal_a": None, "decimal_b": None,
                         "note": f"schedule only; event id {ev.get('id')}", "event_id": ev.get("id")})
    # Do the odds endpoints expose prices at all from CI?
    odds_checked, odds_hits = 0, 0
    for rec in [x for x in recs if x.get("event_id")][:6]:
        od, orr = get_json(f"{base}/event/{rec['event_id']}/odds/1/all", retries=1)
        odds_checked += 1
        detail.setdefault("odds_statuses", []).append(orr.get("status"))
        if isinstance(od, dict):
            keys = sorted(od.keys())[:8]
            detail.setdefault("odds_keys", keys)
            text = json.dumps(od)[:4000]
            decs = [float(x) for x in re.findall(r'"decimalValue"\s*:\s*"?([0-9.]+)', text)]
            if len(decs) >= 2:
                odds_hits += 1
                markets = od.get("markets") or od.get("odds") or []
                if isinstance(markets, list) and markets:
                    m0 = markets[0]
                    choices = m0.get("choices") if isinstance(m0, dict) else None
                    if isinstance(choices, list) and len(choices) == 2:
                        rec.update({"decimal_a": choices[0].get("decimalValue"),
                                    "decimal_b": choices[1].get("decimalValue"),
                                    "note": f"odds market {m0.get('marketId')} via SofaScore (event {rec['event_id']})"})
    detail.update({"odds_events_checked": odds_checked, "odds_events_with_prices": odds_hits})
    priced = [r for r in recs if r.get("decimal_a")]
    return {
        "name": name, "kind": "odds-aggregator", "url": "https://www.sofascore.com/esports/league-of-legends",
        "http_status": status, "bytes": bytes_total, "is_json": bool(recs),
        "competitions": comps[:30], "records": priced or [],
        "schedule_records": len(recs), "detail": detail,
        "error": None if priced else f"{len(recs)} scheduled LoL events read, no two-way prices returned",
    }


# --------------------------------------------------------------------------- #
# 3. bo3.gg (esports match database with bookmaker odds)
# --------------------------------------------------------------------------- #
def probe_bo3():
    name = "bo3.gg (esports match DB + odds)"
    attempts = [
        "https://api.bo3.gg/api/v1/matches?page[limit]=100&sort=-start_date&filter[matches.discipline_id][$eq]=2",
        "https://api.bo3.gg/api/v1/matches?page[limit]=100&sort=start_date",
        "https://api.bo3.gg/api/v1/disciplines",
    ]
    recs, status, bytes_total, detail = [], None, 0, {}
    for url in attempts:
        data, r = get_json(url, retries=1)
        status = status or r.get("status")
        bytes_total += len(r.get("text") or "")
        detail.setdefault("attempts", []).append({"url": url, "status": r.get("status"),
                                                 "is_json": isinstance(data, (dict, list))})
        if not isinstance(data, (dict, list)):
            continue
        items = data.get("data") if isinstance(data, dict) else data
        if not isinstance(items, list):
            continue
        detail["item_count"] = len(items)
        for it in items[:100]:
            if not isinstance(it, dict):
                continue
            attrs = it.get("attributes") if isinstance(it.get("attributes"), dict) else it
            teams = []
            for side in ("home_team", "away_team", "team1", "team2"):
                t = attrs.get(side)
                if isinstance(t, dict):
                    teams.append(str((t.get("attributes") or t).get("name") or t.get("name") or ""))
                elif isinstance(t, str):
                    teams.append(t)
            if len(teams) < 2:
                continue
            odds = attrs.get("odds") if isinstance(attrs.get("odds"), dict) else {}
            recs.append({"source": name, "url": "https://bo3.gg/matches",
                         "competition": str(attrs.get("tournament_name") or attrs.get("tournament") or ""),
                         "start": utc_iso(parse_iso(attrs.get("start_date") or attrs.get("start_time"))),
                         "team_a": teams[0], "team_b": teams[1],
                         "decimal_a": odds.get("team1") or odds.get("home"),
                         "decimal_b": odds.get("team2") or odds.get("away"),
                         "note": "bo3.gg match record"})
        if recs:
            break
    priced = [r for r in recs if r.get("decimal_a")]
    return {"name": name, "kind": "esports-aggregator", "url": "https://api.bo3.gg/api/v1/matches",
            "http_status": status, "bytes": bytes_total, "is_json": bool(recs or detail.get("attempts")),
            "records": priced, "schedule_records": len(recs), "detail": detail,
            "error": None if priced else "no odds fields in the public match payload"}


# --------------------------------------------------------------------------- #
# 4. 1xBet-family esportsbooks (public LineFeed JSON, deep tier-3 coverage)
# --------------------------------------------------------------------------- #
ONEXBET_HOSTS = ["1xbet.com", "betwinner.com", "melbet.com"]


def probe_onexbet(host):
    name = f"1xBet-family / {host}"
    recs, detail, status = [], {}, None
    base = f"https://{host}/LineFeed"
    sports, r = get_json(f"{base}/GetSportsShortZip?lng=en&country=1&partner=51", retries=1)
    status = r.get("status")
    esports_ids = []
    if isinstance(sports, dict) and isinstance(sports.get("Value"), list):
        for s in sports["Value"]:
            nm = str(s.get("N") or s.get("NS") or "")
            if "esport" in nm.lower():
                esports_ids.append(s.get("I"))
        detail["esports_sport_ids"] = esports_ids
    for sid in (esports_ids or [3, 12, 70, 85, 109]):
        data, rr = get_json(
            f"{base}/Get1x2_VZip?sports={sid}&count=1000&lng=en&mode=4&country=1&partner=51&getEmpty=true",
            retries=1)
        status = status or rr.get("status")
        detail.setdefault("sport_attempts", []).append({"sport_id": sid, "status": rr.get("status")})
        if not (isinstance(data, dict) and isinstance(data.get("Value"), list)):
            continue
        vals = data["Value"]
        detail.setdefault("sport_items", {})[str(sid)] = len(vals)
        for v in vals:
            if not isinstance(v, dict):
                continue
            league = str(v.get("L") or v.get("LE") or "")
            if "league of legends" not in league.lower() and "lol" not in str(v.get("SN") or "").lower():
                continue
            rec = _two_way(recs, name, f"https://{host}/en/line/",
                           league, v.get("S"), v.get("T1"), v.get("T2"),
                           v.get("O1"), v.get("O2"), note=f"LineFeed event {v.get('I')}")
            if rec:
                recs.append(rec)
        if recs:
            break
    return {"name": name, "kind": "esportsbook", "url": f"https://{host}/en/line/",
            "http_status": status, "bytes": 0, "is_json": bool(recs or detail),
            "records": recs, "detail": detail,
            "error": None if recs else "no League of Legends two-way prices in the LineFeed payload"}


# --------------------------------------------------------------------------- #
# 5. Status-only probes (documented, never parsed)
# --------------------------------------------------------------------------- #
STATUS_ONLY = [
    ("eGamersWorld LoL odds", "https://egamersworld.com/lol/bets", "aggregator-page"),
    ("Oddspedia LoL", "https://oddspedia.com/esports/league-of-legends", "aggregator-page"),
    ("GGScore LoL", "https://ggscore.com/en/lol/matches", "aggregator-page"),
    ("BetExplorer esports", "https://www.betexplorer.com/esports/", "aggregator-page"),
    ("Winamax LoL", "https://www.winamax.fr/paris-sportifs/sports/2/57", "established-sportsbook"),
    ("Marathonbet esports", "https://www.marathonbet.com/en/betting/Esports/", "established-sportsbook"),
    ("Betano esports", "https://www.betano.de/esports/", "established-sportsbook"),
    ("Vave esports", "https://vave.com/sports/esports", "esportsbook"),
    ("Rainbet esports", "https://rainbet.com/esports/league-of-legends", "esportsbook"),
    ("Thunderpick LoL", "https://thunderpick.io/esports/league-of-legends", "esportsbook"),
    ("GG.Bet LoL", "https://gg.bet/en/esports/lol", "esportsbook"),
    ("Rivalry LoL", "https://www.rivalry.com/lol", "esportsbook"),
]


def probe_status(name, url, kind):
    r = fetch(url, timeout=25, retries=1)
    text = r.get("text") or ""
    is_json = False
    hits = None
    try:
        data = json.loads(text)
        is_json = True
        hits = sum(1 for _ in re.finditer(r"league of legends", json.dumps(data)[:200000].lower()))
    except Exception:
        hits = text.lower().count("league of legends") or None
    return {"name": name, "kind": kind, "url": url, "http_status": r.get("status"),
            "bytes": len(text.encode("utf-8", "ignore")), "is_json": is_json,
            "lol_mentions": hits, "records": [],
            "error": None if r.get("status") == 200 else f"HTTP {r.get('status')}"}


# --------------------------------------------------------------------------- #
# Controls: sources already in production, re-measured for comparison
# --------------------------------------------------------------------------- #
def probe_pinnacle():
    pin_key = {"x-api-key": "CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R", "Accept": "application/json"}
    base = "https://guest.api.arcadia.pinnacle.com/0.1"
    recs, leagues, detail = [], [], {}
    sports, r = get_json(f"{base}/sports", pin_key, retries=1)
    status = r.get("status")
    esports = [s for s in (sports or []) if isinstance(s, dict) and
               (s.get("id") == 12 or "esport" in str(s.get("name", "")).lower())]
    for sport in esports:
        ls, _ = get_json(f"{base}/sports/{sport['id']}/leagues", pin_key, retries=1)
        for league in ls or []:
            nm = str(league.get("name") or "")
            if "league of legends" not in nm.lower():
                continue
            leagues.append(nm)
            ms, _ = get_json(f"{base}/leagues/{league.get('id')}/matchups", pin_key, retries=1)
            for m in ms or []:
                if m.get("type") != "matchup" or m.get("parentId") is not None:
                    continue
                parts = m.get("participants") or []
                if len(parts) != 2:
                    continue
                recs.append({"source": "Pinnacle", "url": "https://www.pinnacle.com/en/esports/league-of-legends",
                             "competition": nm, "start": utc_iso(parse_iso(m.get("startTime"))),
                             "team_a": parts[0].get("name"), "team_b": parts[1].get("name"),
                             "decimal_a": None, "decimal_b": None, "note": f"matchup {m.get('id')}"})
    detail["leagues"] = leagues
    return {"name": "Pinnacle (control)", "kind": "established-sportsbook",
            "url": "https://www.pinnacle.com/en/esports/league-of-legends",
            "http_status": status, "bytes": 0, "is_json": True,
            "competitions": leagues, "records": [], "schedule_records": len(recs), "detail": detail,
            "error": None}


def probe_polymarket():
    url = ("https://gamma-api.polymarket.com/events?tag_slug=league-of-legends"
           "&active=true&closed=false&limit=200")
    data, r = get_json(url, retries=1)
    recs, comps = [], []
    for ev in (data or []):
        title = str(ev.get("title") or "")
        if " vs " not in title.lower():
            continue
        comps.append(title[:80])
        recs.append({"source": "Polymarket", "url": f"https://polymarket.com/event/{ev.get('slug')}",
                     "competition": title, "start": utc_iso(parse_iso(ev.get("endDate"))),
                     "team_a": None, "team_b": None, "decimal_a": None, "decimal_b": None,
                     "note": "market-level price in outcomes JSON"})
    return {"name": "Polymarket (control)", "kind": "prediction-market", "url": url,
            "http_status": r.get("status"), "bytes": len(r.get("text") or ""),
            "is_json": isinstance(data, list), "records": [], "schedule_records": len(recs),
            "detail": {"match_markets": len(recs), "sample": comps[:8]}, "error": None}


# --------------------------------------------------------------------------- #
def summarise(res, index: FixtureIndex) -> dict:
    recs = res.get("records") or []
    matched, unpriced_hits, samples = 0, 0, []
    seen_fixtures = set()
    for rec in recs:
        hit = index.match(rec.get("team_a"), rec.get("team_b"), rec.get("start"))
        rec["matched_fixture"] = None
        if hit:
            m, score = hit
            matched += 1
            rec["matched_fixture"] = {"id": m["id"], "team1": m["team1"], "team2": m["team2"],
                                      "tournament": m["tournament"], "start_utc": m["start_utc"],
                                      "had_market": bool(m.get("market")), "name_score": score}
            if m["id"] in index.unpriced:
                unpriced_hits += 1
            seen_fixtures.add(m["id"])
        if len(samples) < 6:
            samples.append({k: rec.get(k) for k in
                            ("team_a", "team_b", "competition", "start", "decimal_a", "decimal_b",
                             "matched_fixture", "note", "url")})
    res["priced_records"] = len(recs)
    res["records_matched_to_fixtures"] = matched
    res["fixtures_matched"] = len(seen_fixtures)
    res["fixtures_matched_and_previously_unpriced"] = unpriced_hits
    res["samples"] = samples
    res.pop("records", None)
    if res.get("http_status") == 200 and unpriced_hits:
        res["verdict"] = ("usable: structured two-way prices that cover fixtures we currently price "
                          "with the model — verify the samples by hand before adding an adapter")
    elif res.get("http_status") == 200 and recs:
        res["verdict"] = "structured prices found but they only duplicate fixtures we already price from a book"
    elif res.get("http_status") == 200:
        res["verdict"] = ("reachable, but no two-way per-match price was extracted"
                          + (f" ({res.get('error')})" if res.get("error") else ""))
    else:
        res["verdict"] = f"not usable from CI (HTTP {res.get('http_status')})"
    return res


def main() -> int:
    picks = None
    try:
        with open(PICKS, "r", encoding="utf-8") as f:
            picks = json.load(f)
    except (OSError, json.JSONDecodeError):
        log("probe: no docs/data/picks.json; fixture matching disabled")
    matches = (picks or {}).get("matches") or []
    index = FixtureIndex(matches)
    log(f"probe: {len(matches)} fixtures, {len(index.unpriced)} without an external line")

    results = []

    def add(fn, *args):
        try:
            res = fn(*args)
        except Exception as e:  # noqa: BLE001 - a probe must never break the job
            res = {"name": getattr(fn, "__name__", "probe"), "kind": "error", "url": None,
                   "http_status": None, "records": [], "error": repr(e)[:200]}
        try:
            res = summarise(res, index)
        except Exception as e:  # noqa: BLE001
            res.setdefault("records", [])
            res["verdict"] = f"probe summarisation error: {repr(e)[:150]}"
        log(f"probe: {res.get('name')} -> HTTP {res.get('http_status')} "
            f"priced={res.get('priced_records')} unpriced_covered={res.get('fixtures_matched_and_previously_unpriced')}")
        results.append(res)

    add(probe_pinnacle)
    add(probe_polymarket)
    for op_name, slug, mkt in KAMBI_OPERATORS:
        add(probe_kambi, op_name, slug, mkt)
    add(probe_sofascore)
    add(probe_bo3)
    for host in ONEXBET_HOSTS:
        add(probe_onexbet, host)
    for name, url, kind in STATUS_ONLY:
        add(probe_status, name, url, kind)

    usable = [r for r in results if r.get("fixtures_matched_and_previously_unpriced")]
    write_json(OUT, {
        "checked_at": utc_iso(now_utc()),
        "fixture_count": len(matches),
        "fixtures_without_external_line": len(index.unpriced),
        "candidates_with_new_coverage": [r["name"] for r in usable],
        "candidates": results,
        "rule": ("A candidate is promoted into scripts/fetch_markets.py only when it returns "
                 "structured two-way per-match prices for fixtures in the published list and the "
                 "sample rows are re-checked by hand. Status-only probes never contribute a price."),
    })
    log(f"probe: wrote {OUT} ({len(results)} candidates, {len(usable)} with new coverage)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

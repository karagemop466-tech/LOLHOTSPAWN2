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
import time
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
# Kambi powers many European sportsbooks from one odds pool, but each operator
# and each country market offers a different *set of competitions*. Prime League
# is a German league, so the German market matters more than the operator.
# One operator, several markets, spaced out: the CDN answers 429 when hammered
# (observed 2026-10-24 on Betsson/NordicBet).
KAMBI_OPERATORS = [
    ("Unibet / GB", "ub", "GB"),
    ("Unibet / DE", "ub", "DE"),
    ("Unibet / SE", "ub", "SE"),
    ("Unibet / IT", "ub", "IT"),
    ("Unibet / NL", "ub", "NL"),
    ("Unibet / FR", "ub", "FR"),
    ("Unibet / PL", "ub", "PL"),
    ("Unibet / AU", "ub", "AU"),
    ("Unibet / ZZ", "ub", "ZZ"),
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
    ("Prime League official (organizer)", "https://www.primeleague.gg/en/liga2", "organizer-results"),
    ("RIVALS LEAGUE official (organizer)", "https://www.rivalsleague.gg/", "organizer-results"),
    ("BetOnline LoL", "https://www.betonline.ag/sportsbook/esports/league-of-legends", "established-sportsbook"),
    ("SportsBetting.ag LoL", "https://sportsbetting.ag/sportsbook/esports/league-of-legends", "established-sportsbook"),
    ("Stake LoL", "https://stake.com/sports/esports/league-of-legends", "esportsbook"),
    ("BC.Game LoL", "https://bc.game/sports/esports/league-of-legends", "esportsbook"),
    ("William Hill esports", "https://sports.williamhill.com/betting/en-gb/esports", "established-sportsbook"),
    ("Parimatch LoL", "https://www.parimatch.com/en/esports/league-of-legends", "established-sportsbook"),
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

def probe_kambi_all_esports():
    """List every esports competition Kambi exposes, not just the LoL path."""
    name = "Kambi / Unibet (all esports view)"
    url = ("https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/esports/all/all/"
           "matches.json?lang=en_GB&market=GB&useCombined=true")
    data, r = get_json(url, headers={"Accept": "application/json"}, retries=1)
    groups = []
    recs = []
    if isinstance(data, dict) and isinstance(data.get("events"), list):
        for item in data["events"]:
            ev = (item or {}).get("event") or {}
            path = " / ".join(str((ev.get(k) or {}).get("name") or "") for k in
                              ("sport", "path", "group")).strip(" /")
            if path and path not in groups:
                groups.append(path)
            if "league of legends" not in path.lower():
                continue
            for bo in item.get("betOffers") or []:
                if (bo.get("betOfferType") or {}).get("id") != 2:
                    continue
                outs = [o for o in (bo.get("outcomes") or []) if o.get("status") in (None, "OPEN")]
                if len(outs) != 2:
                    continue
                o1 = next((o for o in outs if o.get("type") == "OT_ONE"), None)
                o2 = next((o for o in outs if o.get("type") == "OT_TWO"), None)
                if not o1 or not o2:
                    continue
                rec = _two_way(recs, name, url, path, ev.get("start"), ev.get("homeName"),
                               ev.get("awayName"), (o1.get("odds") or 0) / 1000.0,
                               (o2.get("odds") or 0) / 1000.0, note=f"event {ev.get('id')}")
                if rec:
                    recs.append(rec)
    return {"name": name, "kind": "established-sportsbook", "url": url,
            "http_status": r.get("status"), "bytes": len(r.get("text") or ""),
            "is_json": isinstance(data, dict), "competitions": groups[:60],
            "records": recs, "detail": {"competition_count": len(groups)},
            "error": None if recs else "no League of Legends two-way prices in the all-esports view"}


def probe_bmbets():
    """bmbets is an esports odds-comparison page (HTML, decimal 1/2 per bookmaker)."""
    name = "bmbets LoL odds comparison"
    url = "https://www.bmbets.com/e-sports/world/lol---world-championship/"
    r = fetch(url, timeout=25, retries=1)
    text = r.get("text") or ""
    # Keep the evidence auditable: count what a parser would see, plus an excerpt.
    odds_pairs = re.findall(r">\s*([0-9]+\.[0-9]{2})\s*<", text)
    rows = re.findall(r"(?is)<tr[^>]*>(.{0,400}?)</tr>", text)
    leagues = sorted(set(re.findall(r'href="(/e-sports/[^"]*lol[^"]*)"', text, re.I)))[:40]
    return {"name": name, "kind": "aggregator-page", "url": url,
            "http_status": r.get("status"), "bytes": len(text.encode("utf-8", "ignore")),
            "is_json": False, "records": [],
            "detail": {"odd_cells": len(odds_pairs), "table_rows": len(rows),
                       "lol_league_links": leagues,
                       "excerpt": re.sub(r"\s+", " ", text[:1200]) if text else ""},
            "error": None if r.get("status") == 200 else f"HTTP {r.get('status')}"}


FRAC_RE = re.compile(r">\s*(\d{1,3})\s*/\s*(\d{1,3})\s*<")
# Anchors are matched whole (attributes + inner text) because attribute order is
# not guaranteed: a greedy `[^>]*` after `href` swallows a following `title`, which
# is exactly the bug the offline self-test caught on 2026-10-25.
ANCHOR_RE = re.compile(r"<a\b(?P<attrs>[^>]*)>(?P<inner>.*?)</a>", re.I | re.S)
HREF_RE = re.compile(r'href="[^"]*?/e-sports/(?P<slug>[a-z0-9\-]+?)-(?P<eid>\d{5,})"', re.I)
TITLE_RE = re.compile(r'title="(?P<title>[^"]{3,200})"', re.I)
TAG_RE = re.compile(r"<[^>]+>")
DAY_RE = re.compile(
    r"\b(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day\s+(\d{1,2})\s+"
    r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
    re.I,
)
TIME_RE = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b")
VS_SPLIT_RE = re.compile(r"^(.{2,70}?)\s+vs\.?\s+(.{2,70}?)(?:\s+betting\s+odds)?$", re.I)
MONTHS = {m.lower(): i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June",
     "July", "August", "September", "October", "November", "December"])}


def _frac_to_decimal(num: int, den: int):
    """UK fractional price -> decimal odds. 7/17 -> 1.4118 ; 8/5 -> 2.6."""
    if den <= 0:
        return None
    return round(1.0 + num / den, 4)


def parse_oddsdigger(text: str):
    """Pure parser for OddsDigger's upcoming-LoL board -> (records, detail).

    Kept separate from the network call so the extraction rules can be unit-tested
    offline (`verification/test_line_probe.py`); `probe_oddsdigger` only adds the GET.
    """
    detail = {"event_links": 0, "events": 0, "odds_tokens": 0, "day_headings": 0, "excerpt": ""}
    records: list[dict] = []
    if not text:
        return records, detail

    # 1. Ordered, de-duplicated list of event links with their team pair.
    hits = []
    for a in ANCHOR_RE.finditer(text):
        hm = HREF_RE.search(a.group("attrs"))
        if not hm:
            continue
        tm = TITLE_RE.search(a.group("attrs"))
        inner = re.sub(r"\s+", " ", TAG_RE.sub(" ", a.group("inner"))).strip()
        hits.append({"pos": a.start(), "eid": hm.group("eid"), "slug": hm.group("slug"),
                     "title": tm.group("title").strip() if tm else "", "inner": inner})
    detail["event_links"] = len(hits)
    events: list[dict] = []
    seen: set[str] = set()
    for h in hits:
        eid = h["eid"]
        if eid in seen:
            continue
        team_a = team_b = None
        m = VS_SPLIT_RE.match(h["title"])
        if m:
            team_a, team_b = m.group(1).strip(), m.group(2).strip()
        else:
            # No title attribute: the board repeats one anchor per team, so take the
            # first two distinct non-navigation labels that carry this event id.
            names: list[str] = []
            for x in hits:
                if x["eid"] != eid or not x["inner"]:
                    continue
                if x["inner"].lower() in ("all odds", "odds", "bet now"):
                    continue
                if x["inner"] not in names:
                    names.append(x["inner"])
            if len(names) >= 2:
                team_a, team_b = names[0], names[1]
        if not team_a or not team_b or _key(team_a) == _key(team_b):
            continue
        seen.add(eid)
        events.append({"eid": eid, "slug": h["slug"], "team_a": team_a, "team_b": team_b,
                       "pos": h["pos"],
                       "url": f"https://oddsdigger.com/e-sports/{h['slug']}-{eid}"})
    detail["events"] = len(events)

    # 2. Date headings, so a fixture can be matched on name AND kickoff.
    days = [(d.start(), int(d.group(1)), MONTHS[d.group(2).lower()], int(d.group(3)))
            for d in DAY_RE.finditer(text)]
    detail["day_headings"] = len(days)

    # 3. Slice the HTML between one event's link run and the next event's first link.
    for i, ev in enumerate(events):
        same = [h["pos"] for h in hits if h["eid"] == ev["eid"]]
        lo = min(same)
        nxt = [h["pos"] for h in hits if h["eid"] != ev["eid"] and h["pos"] > lo]
        hi = min(nxt) if nxt else len(text)
        chunk = text[lo:hi]
        fr = list(FRAC_RE.finditer(chunk))
        detail["odds_tokens"] += len(fr)
        if len(fr) < 2:
            continue
        first, second = fr[0], fr[1]
        # The prices must belong to THIS row: the last row on the board has no next
        # event to bound its chunk, so an unbounded slice runs into the page footer
        # (which contains "Handicap" navigation and unrelated prices) and both
        # discards a real row and can pair prices from two different rows.
        if first.start() > 1500:
            continue
        if second.start() - first.end() > 300:
            continue
        # A map/handicap market is not a series winner price — never use one. Checked
        # only on the text between the team links and the first price, not the footer.
        if re.search(r"\bMap\s*\d|\bGame\s*\d|handicap|total\s*maps",
                     chunk[:first.start()], re.I):
            continue
        fa = (int(first.group(1)), int(first.group(2)))
        fb = (int(second.group(1)), int(second.group(2)))
        da = _frac_to_decimal(*fa)
        db = _frac_to_decimal(*fb)
        if not da or not db or da <= 1.0 or db <= 1.0:
            continue
        # Best-price-per-side sanity check: the pair must carry a book overround.
        implied = 1.0 / da + 1.0 / db
        if not (1.0 < implied < 1.40):
            continue
        # The board prints the kickoff immediately BEFORE the two team links, so the
        # time is looked for in a short window behind the anchor, not inside the chunk
        # (searching forward picks up the next row's time — caught by the self-test).
        back = text[max(0, lo - 250):lo]
        bms = list(TIME_RE.finditer(back))
        tm = bms[-1] if bms else TIME_RE.search(chunk)
        start = None
        if tm and days:
            prev = [d for d in days if d[0] < lo]
            if prev:
                _, dd, mm, yy = prev[-1]
                try:
                    start = datetime(yy, mm, dd, int(tm.group(1)), int(tm.group(2)),
                                     tzinfo=timezone.utc)
                except ValueError:
                    start = None
        rec = _two_way(records, "OddsDigger upcoming LoL board", ev["url"],
                       "OddsDigger upcoming LoL", start, ev["team_a"], ev["team_b"], da, db,
                       note=(f"best price per side {fa[0]}/{fa[1]} vs "
                             f"{fb[0]}/{fb[1]} (implied sum {implied:.3f})"))
        if rec:
            records.append(rec)
    detail["excerpt"] = re.sub(r"\s+", " ", text[:1500])
    return records, detail


def probe_oddsdigger():
    """OddsDigger's upcoming-LoL board (HTML, UK fractional, best price per side).

    Hand-verified 2026-10-25: this board carries a two-way *series* winner price for
    `Vitality Rising Bees vs Mental Rush` (LGC Rising 2026 Playoffs, 2026-10-27 17:00
    UTC, 7/17 vs 8/5) and for `Ground Zero vs Frank Esports` (LCP 2027 Promotion,
    2026-11-11 09:00 UTC, 1/67 vs 22/3) — two fixtures the four production feeds do
    not price. Books named on the page: bet365, LuckyMate, Copybet, 10Bet, Spreadex.

    The parser is deliberately conservative: it only reads the *first two* fractional
    prices that follow an event link run, drops anything under a "Map N" label, and
    records an excerpt so a human can audit exactly what was seen. Prices shown are
    the best available per side (possibly from different books), so the implied
    probabilities are normalised rather than de-vigged against a single overround.
    """
    name = "OddsDigger upcoming LoL board"
    url = "https://oddsdigger.com/e-sports/league-of-legends/upcoming"
    r = fetch(url, timeout=25, retries=1)
    text = r.get("text") or ""
    status = r.get("status")
    records, detail = parse_oddsdigger(text)
    err = None if status == 200 else f"HTTP {status}"
    return {"name": name, "kind": "aggregator-page", "url": url,
            "http_status": status, "bytes": len(text.encode("utf-8", "ignore")),
            "is_json": False, "records": records, "detail": detail, "error": err}


# Verdicts a human reached by opening the page and cross-checking the row against
# independent sources. A probe can measure coverage; it cannot judge whether the
# orientation of a price is trustworthy, so that judgement is recorded here and
# printed next to the measured numbers instead of being left implicit.
HAND_VERIFIED_VERDICTS = {
    "OddsDigger upcoming LoL board": (
        "NOT promoted to a probability input (hand-verified 2026-10-25). It prices two fixtures "
        "the four production feeds miss. Row 1 agrees with production: Vitality Rising Bees vs "
        "Mental Rush, LGC Rising 2026 Playoffs, 7/17 vs 8/5 -> 64.8%/35.2%, against our published "
        "Polymarket-sourced 64.5%/35.5%. Row 2 contradicts it: Ground Zero vs Frank Esports, LCP "
        "2027 Promotion, 1/67 vs 22/3 -> 89.1%/10.9% for Ground Zero, while our Elo says Frank "
        "Esports 61.7% and eGamersWorld (rating 448 v 530, 0-4 head-to-head) and rft.gg (0-9 "
        "head-to-head) both favour Frank Esports. One row in two agreeing is not enough to let an "
        "affiliate-rendered board override the model, so the disagreement is published on the "
        "Flagged page for review instead. research/betting-sources.md §20."
    ),
}


def summarise(res, index: FixtureIndex) -> dict:
    recs = res.get("records") or []
    matched, unpriced_hits, samples = 0, 0, []
    unmatched: list[str] = []
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
        else:
            unmatched.append(f'{rec.get("team_a")} vs {rec.get("team_b")}'
                             + (f' @ {rec.get("start")}' if rec.get("start") else ""))
        if len(samples) < 20:
            samples.append({k: rec.get(k) for k in
                            ("team_a", "team_b", "competition", "start", "decimal_a", "decimal_b",
                             "matched_fixture", "note", "url")})
    res["priced_records"] = len(recs)
    res["records_matched_to_fixtures"] = matched
    res["fixtures_matched"] = len(seen_fixtures)
    res["fixtures_matched_and_previously_unpriced"] = unpriced_hits
    res["samples"] = samples
    # Published so a human can see what a source offered that we could NOT tie to a
    # fixture, instead of only the rows that matched. Kept bounded.
    res["records_not_matched"] = unmatched[:20]
    res.pop("records", None)
    sched = res.get("schedule_records") or 0
    if res.get("http_status") == 200 and not unpriced_hits and not recs and sched:
        res["verdict"] = (f"reachable; lists {sched} LoL match(es), but none in a competition we "
                          "cannot already price from a book")
        return res
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
    override = HAND_VERIFIED_VERDICTS.get(res.get("name"))
    if override:
        # Keep the measured numbers; replace only the recommendation, which is a
        # human judgement rather than something a probe can compute.
        res["verdict"] = override
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
    for i, (op_name, slug, mkt) in enumerate(KAMBI_OPERATORS):
        if i:
            time.sleep(3.5)   # the Kambi CDN answers 429 to a burst of operators
        add(probe_kambi, op_name, slug, mkt)
    add(probe_sofascore)
    add(probe_bo3)
    for host in ONEXBET_HOSTS:
        add(probe_onexbet, host)
    add(probe_kambi_all_esports)
    add(probe_bmbets)
    add(probe_oddsdigger)
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

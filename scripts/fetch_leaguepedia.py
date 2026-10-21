#!/usr/bin/env python3
"""Leaguepedia (lol.fandom.com) results and schedule.

Why Special:CargoExport rather than api.php: api.php's Cargo endpoint is rate
limited for anonymous/shared IPs (HTTP 200 with {"error":{"code":"ratelimited"}}),
while the wiki's own Cargo export endpoint is not. Every row is a real recorded
match: Team1/Team2 scores, Winner 1|2, exact UTC time and tournament page.

Used for:
  * our own Elo model (past results, all tiers, incl. Prime League 3rd Division,
    Tunisian Super League, 4 Nations, RIVALS LEAGUE, Komplettligaen, ...),
  * canonical team spellings for the Hotspawn fixture names,
  * an independent UTC cross-check of every Hotspawn start time.
"""
from __future__ import annotations

import time
import urllib.parse
from datetime import datetime, timedelta, timezone

from lib_common import fetch, load_json, log, norm, now_utc, source, utc_iso, write_json

OUT = "data/cache/leaguepedia.json"
EXPORT = "https://lol.fandom.com/wiki/Special:CargoExport?"
API = "https://lol.fandom.com/api.php"
FIELDS = "Team1,Team2,Team1Score,Team2Score,Winner,DateTime_UTC,OverviewPage,BestOf,Tab"
TABLE_URL = "https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule"
TEAMS_URL = "https://lol.fandom.com/wiki/Special:CargoTables/Teams"
SLEEP = 2.6


def _get(params: dict, timeout=90):
    url = EXPORT + urllib.parse.urlencode(params)
    r = fetch(url, timeout=timeout, retries=3)
    return r, r["text"]


def _rows(params: dict):
    r, text = _get(params)
    if r["status"] != 200:
        return None, f"HTTP {r['status']}"
    try:
        data = __import__("json").loads(text)
    except Exception:
        return None, "non-JSON response: " + text[:120]
    if not isinstance(data, list):
        return None, "unexpected JSON shape"
    return data, None


def date_windows(start: datetime, end: datetime, days: int = 75):
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=days), end)
        yield cur, nxt
        cur = nxt


def fetch_window(a: datetime, b: datetime, depth: int = 0):
    params = {
        "tables": "MatchSchedule", "fields": FIELDS,
        "where": (f"DateTime_UTC >= '{a.strftime('%Y-%m-%d %H:%M:%S')}' "
                  f"AND DateTime_UTC < '{b.strftime('%Y-%m-%d %H:%M:%S')}'"),
        "order_by": "DateTime_UTC ASC", "limit": "5000", "format": "json",
    }
    rows, err = _rows(params)
    time.sleep(SLEEP)
    if err:
        return [], err
    if len(rows) >= 5000 and depth < 2 and (b - a).days > 2:
        mid = a + (b - a) / 2
        log(f"leaguepedia: window {a.date()}->{b.date()} hit 5000, splitting")
        left, e1 = fetch_window(a, mid, depth + 1)
        right, e2 = fetch_window(mid, b, depth + 1)
        return left + right, e1 or e2
    return rows, None


def _norm_row(x: dict) -> dict | None:
    g = lambda k: x.get(k, x.get(k.replace("_", " ")))  # noqa: E731
    t1, t2 = g("Team1"), g("Team2")
    dt = g("DateTime_UTC")
    if not t1 or not t2 or not dt:
        return None
    if norm(t1) == norm(t2):
        return None
    try:
        when = datetime.strptime(str(dt), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    try:
        winner = int(g("Winner")) if g("Winner") not in (None, "") else None
    except (TypeError, ValueError):
        winner = None
    if winner not in (1, 2):
        winner = None
    try:
        bo = int(g("BestOf")) if g("BestOf") not in (None, "") else None
    except (TypeError, ValueError):
        bo = None
    try:
        s1 = int(g("Team1Score")) if g("Team1Score") not in (None, "") else None
        s2 = int(g("Team2Score")) if g("Team2Score") not in (None, "") else None
    except (TypeError, ValueError):
        s1 = s2 = None
    return {"team1": t1, "team2": t2, "score1": s1, "score2": s2, "winner": winner,
            "start_utc": utc_iso(when), "overview": g("OverviewPage") or "", "best_of": bo,
            "tab": g("Tab") or ""}


def main() -> int:
    now = now_utc()
    start = now - timedelta(days=730)
    end = now + timedelta(days=60)
    rows, errors, calls = [], [], 0
    for a, b in date_windows(start, end, 75):
        chunk, err = fetch_window(a, b)
        calls += 1
        if err:
            errors.append({"from": a.date().isoformat(), "to": b.date().isoformat(), "error": err})
        rows += chunk
        log(f"leaguepedia: {a.date()} -> {b.date()} got {len(chunk)} rows (total {len(rows)})")

    seen, clean = set(), []
    for x in rows:
        r = _norm_row(x)
        if not r:
            continue
        key = (norm(r["team1"]), norm(r["team2"]), r["start_utc"][:10], norm(r["overview"]))
        if key in seen:
            continue
        seen.add(key)
        clean.append(r)
    clean.sort(key=lambda r: r["start_utc"])

    cutoff = now - timedelta(minutes=90)
    results = [r for r in clean if r["winner"] and r["start_utc"] < utc_iso(cutoff)]
    schedule = [r for r in clean if r["start_utc"] >= utc_iso(now - timedelta(days=2))]

    # canonical team spellings
    teams = []
    r, text = _get({"tables": "Teams", "fields": "Name,OverviewPage,Location,Region",
                    "limit": "5000", "format": "json"})
    calls += 1
    try:
        import json
        teams = json.loads(text) if isinstance(json.loads(text), list) else []
    except Exception:
        errors.append({"table": "Teams", "error": text[:120]})
    time.sleep(SLEEP)

    from collections import Counter
    tour_counts = Counter(x["overview"] for x in results)
    payload = {
        "generated_at": utc_iso(now),
        "counts": {"rows": len(clean), "results": len(results), "schedule": len(schedule),
                   "teams": len(teams), "export_calls": calls},
        "errors": errors,
        "tournaments": [{"page": k, "results": v} for k, v in tour_counts.most_common(120)],
        "sources": [
            source("Leaguepedia MatchSchedule (Cargo export)", TABLE_URL,
                   "Recorded match results and schedules with exact UTC time, BestOf and series score."),
            source("Leaguepedia Teams", TEAMS_URL, "Canonical team spellings and region."),
        ],
        "results": results,
        "schedule": schedule,
        "teams": teams,
    }
    if len(results) < 1000:
        raise SystemExit(f"Leaguepedia returned only {len(results)} results - refusing to overwrite good data")
    write_json(OUT, payload)
    log(f"leaguepedia: {len(results)} results, {len(schedule)} schedule rows, {len(teams)} teams")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

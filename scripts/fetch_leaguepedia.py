#!/usr/bin/env python3
"""Leaguepedia (lol.fandom.com) results, schedule, standings and redirects.

Why Special:CargoExport rather than api.php: api.php's Cargo endpoint is rate
limited for anonymous/shared IPs (HTTP 200 with {"error":{"code":"ratelimited"}}),
while the wiki's own Cargo export endpoint is not. Every row is a real recorded
match or split standing: Team1/Team2 scores, Winner 1|2, exact UTC time and
tournament page.

Used for:
  * our own Elo model (past results, all tiers, incl. Prime League 3rd Division,
    Tunisian Super League, 4 Nations, RIVALS LEAGUE, Komplettligaen, ...),
  * current-split series/game standings for newly formed or renamed regional teams,
  * canonical team spellings and official TeamRedirects for Hotspawn fixture names,
  * an independent UTC cross-check of every Hotspawn start time (plus TBD-time
    upcoming MatchSchedule pairings).
"""
from __future__ import annotations

import json
import time
import urllib.parse
from collections import Counter
from datetime import datetime, timedelta, timezone

from lib_common import fetch, load_json, log, norm, now_utc, source, utc_iso, write_json

OUT = "data/cache/leaguepedia.json"
EXPORT = "https://lol.fandom.com/wiki/Special:CargoExport?"
API = "https://lol.fandom.com/api.php"
FIELDS = "Team1,Team2,Team1Score,Team2Score,Winner,DateTime_UTC,OverviewPage,BestOf,Tab"
STANDINGS_FIELDS = "OverviewPage,Team,WinSeries,LossSeries,TieSeries,WinGames,LossGames,Place"
TABLE_URL = "https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule"
STANDINGS_URL = "https://lol.fandom.com/wiki/Special:CargoTables/Standings"
TEAMS_URL = "https://lol.fandom.com/wiki/Special:CargoTables/Teams"
REDIRECTS_URL = "https://lol.fandom.com/wiki/Special:CargoTables/TeamRedirects"
SLEEP = 2.4


def _get(params: dict, timeout=90):
    url = EXPORT + urllib.parse.urlencode(params)
    r = fetch(url, timeout=timeout, retries=3)
    return r, r["text"]


def _rows(params: dict):
    r, text = _get(params)
    if r["status"] != 200:
        return None, f"HTTP {r['status']}"
    try:
        data = json.loads(text)
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
    if norm(str(t1)) == norm(str(t2)):
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
    return {"team1": str(t1), "team2": str(t2), "score1": s1, "score2": s2, "winner": winner,
            "start_utc": utc_iso(when), "overview": str(g("OverviewPage") or ""), "best_of": bo,
            "tab": str(g("Tab") or "")}


def _norm_unscheduled_row(x: dict) -> dict | None:
    g = lambda k: x.get(k, x.get(k.replace("_", " ")))  # noqa: E731
    t1, t2 = str(g("Team1") or "").strip(), str(g("Team2") or "").strip()
    ov = str(g("OverviewPage") or "").strip()
    if not t1 or not t2 or not ov:
        return None
    if norm(t1) in ("", "tbd") or norm(t2) in ("", "tbd") or norm(t1) == norm(t2):
        return None
    try:
        bo = int(g("BestOf")) if g("BestOf") not in (None, "") else None
    except (TypeError, ValueError):
        bo = None
    return {"team1": t1, "team2": t2, "score1": None, "score2": None, "winner": None,
            "start_utc": None, "overview": ov, "best_of": bo, "tab": str(g("Tab") or "")}


def _int_or_zero(v) -> int:
    try:
        return int(v) if v not in (None, "") else 0
    except (TypeError, ValueError):
        return 0


def fetch_unscheduled_upcoming() -> tuple[list[dict], str | None]:
    """Fetch upcoming 2026/2027 MatchSchedule rows whose DateTime_UTC is TBD/null."""
    params = {
        "tables": "MatchSchedule",
        "fields": FIELDS,
        "where": ("DateTime_UTC IS NULL AND (Winner IS NULL OR Winner = '') "
                  "AND (OverviewPage LIKE '%2026%' OR OverviewPage LIKE '%2027%')"),
        "limit": "5000",
        "format": "json",
    }
    rows, err = _rows(params)
    time.sleep(SLEEP)
    if err:
        return [], err
    seen, out = set(), []
    for x in rows or []:
        r = _norm_unscheduled_row(x)
        if not r:
            continue
        k = (norm(r["team1"]), norm(r["team2"]), norm(r["overview"]), r["tab"])
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out, None


def fetch_standings() -> tuple[list[dict], str | None]:
    """Fetch current-season 2026/2027 Standings rows for low-tier & renamed teams."""
    out = []
    seen = set()
    for offset in (0, 5000):
        params = {
            "tables": "Standings",
            "fields": STANDINGS_FIELDS,
            "where": "OverviewPage LIKE '%2026%' OR OverviewPage LIKE '%2027%'",
            "limit": "5000",
            "offset": str(offset),
            "format": "json",
        }
        rows, err = _rows(params)
        time.sleep(SLEEP)
        if err:
            return out, err
        for x in rows or []:
            ov = str(x.get("OverviewPage") or "").strip()
            tm = str(x.get("Team") or "").strip()
            if not ov or not tm or norm(tm) in ("", "tbd"):
                continue
            ws = _int_or_zero(x.get("WinSeries"))
            ls = _int_or_zero(x.get("LossSeries"))
            ts = _int_or_zero(x.get("TieSeries"))
            wg = _int_or_zero(x.get("WinGames"))
            lg = _int_or_zero(x.get("LossGames"))
            key = (norm(ov), norm(tm))
            rec = {
                "overview": ov,
                "team": tm,
                "win_series": ws,
                "loss_series": ls,
                "tie_series": ts,
                "win_games": wg,
                "loss_games": lg,
                "place": str(x.get("Place") or ""),
            }
            if key in seen:
                # Keep the row with more played games if a split has multiple stages
                for idx, prev in enumerate(out):
                    if (norm(prev["overview"]), norm(prev["team"])) == key:
                        if (ws + ls + wg + lg) > (prev["win_series"] + prev["loss_series"] + prev["win_games"] + prev["loss_games"]):
                            out[idx] = rec
                        break
            else:
                seen.add(key)
                out.append(rec)
        if not rows or len(rows) < 5000:
            break
    return out, None


def fetch_hotspawn_redirects(known_names: set[str]) -> tuple[dict[str, str], str | None]:
    """Resolve unknown Hotspawn fixture team names via Leaguepedia TeamRedirects."""
    hs = load_json("data/cache/hotspawn.json") or {}
    known_norm = {norm(n) for n in known_names if n}
    missing = sorted({
        str(t).strip()
        for f in (hs.get("fixtures") or [])
        for t in (f.get("team1"), f.get("team2"))
        if t and norm(str(t)) not in known_norm and '"' not in str(t) and "'" not in str(t)
    })
    if not missing:
        return {}, None
    quoted = ",".join(f'"{name}"' for name in missing[:80])
    params = {
        "tables": "TeamRedirects",
        "fields": "AllName,_pageName=PageName",
        "where": f"AllName IN ({quoted})",
        "limit": "500",
        "format": "json",
    }
    rows, err = _rows(params)
    time.sleep(1.2)
    if err:
        return {}, err
    redirects = {}
    for x in rows or []:
        src_name = str(x.get("AllName") or "").strip()
        dst_name = str(x.get("PageName") or "").strip()
        if src_name and dst_name:
            redirects[src_name] = dst_name
    return redirects, None


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

    unscheduled, u_err = fetch_unscheduled_upcoming()
    calls += 1
    if u_err:
        errors.append({"table": "MatchSchedule(unscheduled)", "error": u_err})

    standings, s_err = fetch_standings()
    calls += 1
    if s_err:
        errors.append({"table": "Standings", "error": s_err})

    # canonical team spellings
    teams = []
    r, text = _get({"tables": "Teams", "fields": "Name,OverviewPage,Location,Region",
                    "limit": "5000", "format": "json"})
    calls += 1
    try:
        parsed_teams = json.loads(text)
        teams = parsed_teams if isinstance(parsed_teams, list) else []
    except Exception:
        errors.append({"table": "Teams", "error": text[:120]})
    time.sleep(SLEEP)

    known_names = (
        {x["team1"] for x in clean}
        | {x["team2"] for x in clean}
        | {x["team"] for x in standings}
        | {str(t.get("Name") or "") for t in teams}
    )
    redirects, r_err = fetch_hotspawn_redirects(known_names)
    if redirects or r_err:
        calls += 1
    if r_err:
        errors.append({"table": "TeamRedirects", "error": r_err})

    tour_counts = Counter(x["overview"] for x in results)
    payload = {
        "generated_at": utc_iso(now),
        "degraded": False,
        "counts": {
            "rows": len(clean),
            "results": len(results),
            "schedule": len(schedule),
            "unscheduled": len(unscheduled),
            "standings": len(standings),
            "teams": len(teams),
            "redirects": len(redirects),
            "export_calls": calls,
        },
        "errors": errors,
        "tournaments": [{"page": k, "results": v} for k, v in tour_counts.most_common(120)],
        "sources": [
            source("Leaguepedia MatchSchedule (Cargo export)", TABLE_URL,
                   "Recorded match results and schedules with exact UTC time, BestOf and series score."),
            source("Leaguepedia Standings (Cargo export)", STANDINGS_URL,
                   "Current-split series and game win-loss records for active tournaments."),
            source("Leaguepedia Teams", TEAMS_URL, "Canonical team spellings and region."),
            source("Leaguepedia TeamRedirects", REDIRECTS_URL, "Official team rename/alias redirects."),
        ],
        "results": results,
        "schedule": schedule,
        "unscheduled": unscheduled,
        "standings": standings,
        "redirects": redirects,
        "teams": teams,
    }
    if len(results) < 1000:
        prev = load_json(OUT)
        if prev and prev.get("results"):
            prev["degraded"] = True
            prev["degraded_reason"] = (f"fresh export returned only {len(results)} results "
                                       f"({len(errors)} errors); using snapshot from "
                                       f"{prev.get('generated_at')}")
            prev["last_attempt_utc"] = utc_iso(now)
            write_json(OUT, prev)
            log("leaguepedia: " + prev["degraded_reason"])
            return 0
        raise SystemExit(f"Leaguepedia returned only {len(results)} results and no fallback snapshot exists")
    if standings:
        write_json("data/diag/standings.json", {
            "generated_at": utc_iso(now),
            "source": STANDINGS_URL,
            "rows": len(standings),
            "pages": sorted({str(r.get("overview")) for r in standings if r.get("overview")}),
            "standings": standings,
        })
    write_json(OUT, payload)
    log(f"leaguepedia: {len(results)} results, {len(schedule)} schedule rows, "
        f"{len(unscheduled)} unscheduled, {len(standings)} standings, {len(teams)} teams")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

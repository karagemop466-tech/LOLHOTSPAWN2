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
STANDINGS_URL = "https://lol.fandom.com/wiki/Special:CargoTables/Standings"
STANDINGS_FIELDS = "OverviewPage,Team,Place,WinSeries,LossSeries,WinGames,LossGames,Points"
SLEEP = 2.6

# Standings are the one independent, official record available for leagues that no
# bookmaker prices (Prime League 2nd/3rd Division, RIVALS LEAGUE, Tunisian Super
# League, Komplettligaen, LigaGG, Arabian League 2nd Division, ...). Field names
# verified against the wiki's own table definition:
#   https://lol.fandom.com/wiki/Special:CargoTables/Standings
# No value is inferred: a row is used only when the team is listed on the page.
_PAGE_TOKEN_FIX = (
    ("worlds", "world championship"),
    ("prm", "prime league"),
    ("26-27", " "), ("26/27", " "),
    ("em ", "emea masters "),
    ("lgc rising", "lol game changers"),
    ("celol", "celol"),
)
_PAGE_TOKEN_STOP = {"season", "split", "the", "of", "and", "vs", "2026", "2027", "2025"}


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


def page_tokens(name: str) -> set[str]:
    """Distinctive tokens of a tournament/page name (years and split words dropped)."""
    t = str(name or "").lower().replace("_", " ")
    for a, b in _PAGE_TOKEN_FIX:
        t = t.replace(a, b)
    toks = set()
    for w in __import__("re").findall(r"[a-z0-9]+", t):
        if w in _PAGE_TOKEN_STOP or w.isdigit():
            continue
        toks.add(w)
    return toks


def page_score(tournament: str, page: str) -> float:
    """How well a Leaguepedia overview page name matches a Hotspawn tournament name."""
    a, b = page_tokens(tournament), page_tokens(page)
    if len(a) < 2 or not b:
        return 0.0
    overlap = len(a & b)
    if overlap < 2:
        return 0.0
    return overlap / len(a)


def _standings_row(x: dict) -> dict | None:
    def num(key):
        v = x.get(key)
        try:
            return int(float(v)) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None
    page, team = x.get("OverviewPage"), x.get("Team")
    if not page or not team:
        return None
    return {"page": str(page), "team": str(team), "place": num("Place"),
            "wins": num("WinSeries"), "losses": num("LossSeries"),
            "win_games": num("WinGames"), "loss_games": num("LossGames"),
            "points": num("Points")}


def schedule_pages(fixtures: list[dict], schedule_rows: list[dict]) -> dict[str, set[str]]:
    """Tournament -> Leaguepedia pages whose schedule lists at least two of its teams.

    This is a purely observational bridge: it uses only rows already returned by the
    MatchSchedule export, never a guessed competition name.
    """
    team_pages: dict[str, set[str]] = {}
    for r in schedule_rows:
        page = str(r.get("overview") or "")
        if not page:
            continue
        for key in (norm(r.get("team1")), norm(r.get("team2"))):
            if key:
                team_pages.setdefault(key, set()).add(page)
    out: dict[str, set[str]] = {}
    by_tour: dict[str, set[str]] = {}
    for f in fixtures:
        t = (f.get("tournament") or "").strip()
        if t:
            by_tour.setdefault(t, set()).update({norm(f.get("team1")), norm(f.get("team2"))})
    for tour, teams in by_tour.items():
        counts: dict[str, int] = {}
        for team in teams:
            for page in team_pages.get(team, ()):
                counts[page] = counts.get(page, 0) + 1
        out[tour] = {p for p, c in counts.items() if c >= 2}
    return out


def fetch_standings(hotspawn_fixtures: list[dict], hints: dict[str, set[str]] | None = None) -> dict:
    """Official win-loss tables for the leagues in the current fixture list.

    Two independent ways to find the right page, both data-driven:
      1. the Leaguepedia page already matched to a fixture of the same tournament;
      2. a token overlap between the Hotspawn tournament name and the standings page.
    A page is only kept when at least one fixture of that tournament has BOTH teams
    listed on it — otherwise the numbers could belong to another division.
    """
    out = {"rows": [], "pages": [], "tournaments": {}, "errors": [], "calls": 0}
    if not hotspawn_fixtures:
        return out

    by_tour: dict[str, set[str]] = {}
    for f in hotspawn_fixtures:
        t = (f.get("tournament") or "").strip()
        if t:
            by_tour.setdefault(t, set()).add(f["id"])

    # 1. every standings page name, one request
    pages_list, err = _rows({"tables": "Standings", "fields": "OverviewPage",
                             "group_by": "OverviewPage", "limit": "5000", "format": "json"})
    out["calls"] += 1
    time.sleep(SLEEP)
    if err or not pages_list:
        out["errors"].append({"table": "Standings", "step": "page-list", "error": err or "empty"})
        return out
    all_pages = sorted({str(r.get("OverviewPage")) for r in pages_list if r.get("OverviewPage")})

    # pages already attached to fixtures by the schedule join are strong evidence
    hints = hints or {}
    candidates: dict[str, list[tuple[float, str]]] = {}
    for tour in by_tour:
        scored = [(1.0, p) for p in hints.get(tour, ())]
        for p in all_pages:
            sc = page_score(tour, p)
            if sc >= 0.7:
                scored.append((sc, p))
        dedup = {}
        for sc, p in scored:
            dedup[p] = max(sc, dedup.get(p, 0.0))
        candidates[tour] = sorted(((sc, p) for p, sc in dedup.items()), reverse=True)[:3]

    wanted = sorted({p for lst in candidates.values() for _, p in lst})
    if not wanted:
        return out

    cache: dict[str, list[dict]] = {}
    for page in wanted:
        rows, err = _rows({"tables": "Standings", "fields": STANDINGS_FIELDS,
                           "where": "OverviewPage = '" + page.replace("'", "''") + "'",
                           "limit": "500", "format": "json"})
        out["calls"] += 1
        time.sleep(SLEEP)
        if err or not rows:
            out["errors"].append({"table": "Standings", "page": page, "error": err or "no rows"})
            continue
        clean = [r for r in (_standings_row(x) for x in rows) if r]
        if clean:
            cache[page] = clean

    # keep only pages whose team list matches the tournament's fixtures
    for tour, scored in candidates.items():
        teams = set()
        for f in hotspawn_fixtures:
            if (f.get("tournament") or "").strip() == tour:
                teams.add(norm(f["team1"]))
                teams.add(norm(f["team2"]))
        accepted = []
        for sc, page in scored:
            if page not in cache:
                continue
            listed = {norm(r["team"]) for r in cache[page]}
            if len(teams & listed) >= 2:
                accepted.append(page)
        if accepted:
            out["tournaments"][tour] = accepted
            out["pages"] += [p for p in accepted if p not in out["pages"]]

    keep = set(out["pages"])
    out["rows"] = [r for p in keep for r in cache.get(p, [])]
    return out


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

    # ---- official win-loss tables for the leagues in the current fixture list ----
    fixtures = (load_json("data/cache/hotspawn.json", {}) or {}).get("fixtures") or []
    standings = {"rows": [], "pages": [], "tournaments": {}, "errors": [], "calls": 0}
    if fixtures:
        hints = schedule_pages(fixtures, clean)
        standings = fetch_standings(fixtures, hints)
        calls += standings.get("calls", 0)
        errors += standings.get("errors", [])
        log(f"leaguepedia: standings for {len(standings['pages'])} page(s), "
            f"{len(standings['rows'])} team rows")

    from collections import Counter
    tour_counts = Counter(x["overview"] for x in results)
    payload = {
        "generated_at": utc_iso(now),
        "degraded": False,
        "counts": {"rows": len(clean), "results": len(results), "schedule": len(schedule),
                   "teams": len(teams), "export_calls": calls,
                   "standings_pages": len(standings["pages"]),
                   "standings_rows": len(standings["rows"])},
        "errors": errors,
        "tournaments": [{"page": k, "results": v} for k, v in tour_counts.most_common(120)],
        "sources": [
            source("Leaguepedia MatchSchedule (Cargo export)", TABLE_URL,
                   "Recorded match results and schedules with exact UTC time, BestOf and series score."),
            source("Leaguepedia Teams", TEAMS_URL, "Canonical team spellings and region."),
            source("Leaguepedia Standings", STANDINGS_URL,
                   "Official win-loss records per league, used for teams without enough "
                   "recorded series for the Elo model."),
        ],
        "results": results,
        "schedule": schedule,
        "teams": teams,
        "standings": standings["rows"],
        "standings_pages": standings["pages"],
        "standings_by_tournament": standings["tournaments"],
    }
    if len(results) < 1000:
        # A rate-limited / broken run must not wipe good data. Fall back to the
        # last good snapshot, mark it degraded and let the pipeline publish with
        # an explicit degraded source status instead of failing the whole run.
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
    write_json(OUT, payload)
    log(f"leaguepedia: {len(results)} results, {len(schedule)} schedule rows, {len(teams)} teams")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

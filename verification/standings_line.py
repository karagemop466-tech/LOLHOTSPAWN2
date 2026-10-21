#!/usr/bin/env python3
"""
standings_line.py — standings-based line for fixtures that have no bookmaker
price and no per-game results (the honest middle ground before 50/50).

Why standings: for the current amateur seasons (PRM 3rd Division 2027 Fall,
RIVALS LEAGUE Season 2, 4 Nations Halloween Heist, Komplettligaen 2026 Autumn,
Tunisian Super League 2026 …) Leaguepedia has MatchSchedule + Standings but
often **no ScoreboardGames** rows yet, so an Elo cannot be fitted. The official
win-loss record still carries real information.

Model:
    wr(team) = (WinSeries + a) / (WinSeries + LossSeries + 2a)      a = 2
    p1 = wr1 / (wr1 + wr2)          (Bradley–Terry on smoothed series rates)
falling back to WinGames/LossGames (a = 4) when series columns are empty.
Confidence: HIGH if both teams have >=5 decided series, MEDIUM >=2, LOW otherwise.

Leaguepedia `Standings` fields are exactly:
    OverviewPage, Team, PageAndTeam, N, Place, WinSeries, LossSeries, TieSeries,
    WinGames, LossGames, Points, PointsTiebreaker, Streak, StreakDirection
(verified 2026-10-21 via api.php?action=cargofields&table=Standings)

Usage (offline with a snapshot):
  python3 verification/standings_line.py --standings data/diag/lp_standings.json
Usage (live, in GitHub Actions — paced, CargoExport endpoint):
  python3 verification/standings_line.py --fetch
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIKI = "https://lol.fandom.com/wiki/"
CARGO = "https://lol.fandom.com/wiki/Special:CargoExport"
UA = ("Mozilla/5.0 (compatible; LOLHOTSPAWN2-standings/1.0; "
      "+https://github.com/karagemop466-tech/LOLHOTSPAWN2)")

from check_leaguepedia_coverage import LEAGUE_MAP  # noqa: E402  (same directory)

FIELDS = ("OverviewPage,Team,Place,WinSeries,LossSeries,WinGames,LossGames,Points")


def http_json(url: str, timeout: float = 45.0, retries: int = 3):
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                   "Accept": "application/json",
                                                   "Accept-Encoding": "gzip"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
            if raw[:2] == b"\x1f\x8b":
                import gzip
                raw = gzip.decompress(raw)
            return json.loads(raw.decode("utf-8", "replace"))
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(2 + 3 * attempt)
    raise RuntimeError(f"failed {url}: {last!r}")


def fetch_pages(pages: list[str]) -> list[dict]:
    rows: list[dict] = []
    for page in pages:
        where = f"OverviewPage = '{page.replace(chr(39), chr(39) * 2)}'"
        url = CARGO + "?" + urllib.parse.urlencode({
            "tables": "Standings", "fields": FIELDS, "where": where,
            "limit": "200", "format": "json"})
        try:
            data = http_json(url)
            if isinstance(data, list):
                rows += [r for r in data if isinstance(r, dict)]
                print(f"  {len(data):3} rows  {page}", file=sys.stderr)
            else:
                print(f"  no rows   {page}: {str(data)[:120]}", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR     {page}: {exc!r}", file=sys.stderr)
        time.sleep(3.0)  # Leaguepedia anonymous rate limit
    return rows


def num(v, default=0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def rate(r: dict):
    ws, ls = num(r.get("WinSeries")), num(r.get("LossSeries"))
    if ws + ls > 0:
        a = 2.0
        return (ws + a) / (ws + ls + 2 * a), int(ws + ls), "series"
    wg, lg = num(r.get("WinGames")), num(r.get("LossGames"))
    if wg + lg > 0:
        a = 4.0
        return (wg + a) / (wg + lg + 2 * a), int(wg + lg), "games"
    return None, 0, "none"


def norm(s) -> str:
    return re.sub(r"[^a-z0-9]", "", (str(s or "")).lower())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--picks", default=os.path.join(ROOT, "docs", "data", "picks.json"))
    ap.add_argument("--standings", default="", help="JSON snapshot (list of Standings rows)")
    ap.add_argument("--fetch", action="store_true", help="fetch from Leaguepedia CargoExport")
    ap.add_argument("--out", default=os.path.join(ROOT, "verification", "standings_line.json"))
    ap.add_argument("--all-rows", action="store_true",
                    help="score every row, not only UNRESOLVED/MODEL_ELO")
    args = ap.parse_args()

    picks = json.load(open(args.picks, encoding="utf-8"))
    rows = picks.get("matches", [])
    pages_needed = sorted({p for t in {m.get("tournament", "").strip() for m in rows}
                           for p in LEAGUE_MAP.get(t, [])})
    if args.fetch:
        standings = fetch_pages(pages_needed)
    elif args.standings and os.path.exists(args.standings):
        standings = json.load(open(args.standings, encoding="utf-8"))
        if isinstance(standings, dict):
            standings = standings.get("cargoquery") or standings.get("rows") or []
        standings = [r.get("title", r) if isinstance(r, dict) else r for r in standings]
    else:
        print("need --fetch or --standings <snapshot>", file=sys.stderr)
        return 2

    by_page: dict[str, dict[str, dict]] = {}
    for r in standings:
        if not isinstance(r, dict):
            continue
        page = str(r.get("OverviewPage") or "")
        team = str(r.get("Team") or "")
        if page and team:
            by_page.setdefault(page, {})[norm(team)] = r

    out, moved = [], 0
    for m in rows:
        if not args.all_rows and m.get("method") not in ("UNRESOLVED", "MODEL_ELO"):
            continue
        tour = (m.get("tournament") or "").strip()
        page = next((p for p in LEAGUE_MAP.get(tour, []) if p in by_page), None)
        rec = {"team1": m["team1"], "team2": m["team2"], "tournament": tour,
               "method": m.get("method"), "leaguepedia_page": page,
               "source_url": (WIKI + page.replace(" ", "_")) if page else None}
        if not page:
            rec.update({"status": "NO_STANDINGS_PAGE", "prob_team1": 0.5, "prob_team2": 0.5})
            out.append(rec)
            continue
        t = by_page[page]
        r1, r2 = t.get(norm(m["team1"])), t.get(norm(m["team2"]))
        wr1, n1, kind1 = rate(r1) if r1 else (None, 0, "none")
        wr2, n2, kind2 = rate(r2) if r2 else (None, 0, "none")
        if wr1 is None or wr2 is None:
            rec.update({"status": "TEAM_NOT_IN_STANDINGS", "prob_team1": 0.5,
                        "prob_team2": 0.5,
                        "teams_found": [bool(r1), bool(r2)]})
            out.append(rec)
            continue
        p = wr1 / (wr1 + wr2)
        p = round(min(0.95, max(0.05, p)), 4)
        if abs(p - 0.5) >= 0.02:
            moved += 1
        conf = "HIGH" if min(n1, n2) >= 5 else "MEDIUM" if min(n1, n2) >= 2 else "LOW"
        ws1 = f"{int(num(r1.get('WinSeries')))}-{int(num(r1.get('LossSeries')))}"
        ws2 = f"{int(num(r2.get('WinSeries')))}-{int(num(r2.get('LossSeries')))}"
        rec.update({
            "status": "SCORED", "prob_team1": p, "prob_team2": round(1 - p, 4),
            "confidence": conf, "basis": kind1,
            "records": [ws1, ws2], "decided": [n1, n2],
            "evidence": (f"Leaguepedia standings ({page}): {m['team1']} {ws1} vs "
                         f"{m['team2']} {ws2}"),
        })
        out.append(rec)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pages_available": sorted(by_page),
        "rows_scored": sum(1 for r in out if r.get("status") == "SCORED"),
        "rows_moved_off_50_50": moved,
        "rows_no_page": sum(1 for r in out if r.get("status") == "NO_STANDINGS_PAGE"),
        "rows_team_missing": sum(1 for r in out if r.get("status") == "TEAM_NOT_IN_STANDINGS"),
        "scored": len(out),
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump({"summary": summary, "rows": out}, open(args.out, "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

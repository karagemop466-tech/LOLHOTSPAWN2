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
import difflib
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
    ap.add_argument("--schedule", default="", help="MatchSchedule snapshot (name bridge)")
    ap.add_argument("--fetch", action="store_true", help="fetch from Leaguepedia CargoExport")
    ap.add_argument("--out", default=os.path.join(ROOT, "verification", "standings_line.json"))
    ap.add_argument("--all-rows", action="store_true",
                    help="score every row, not only UNRESOLVED/MODEL_ELO")
    args = ap.parse_args()

    def load_rows(path):
        data = json.load(open(path, encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("cargoquery") or data.get("rows") or []
        return [r.get("title", r) if isinstance(r, dict) else r for r in data]

    schedule_by_page: dict[str, list[tuple[str, str]]] = {}
    if args.schedule and os.path.exists(args.schedule):
        for r in load_rows(args.schedule):
            if not isinstance(r, dict):
                continue
            pg = str(r.get("OverviewPage") or "")
            t1 = str(r.get("Team1") or "")
            t2 = str(r.get("Team2") or "")
            if pg and t1 and t2:
                schedule_by_page.setdefault(pg, []).append((t1, t2))

    def name_score(ours: str, theirs: str) -> int:
        a, b = norm(ours), norm(theirs)
        if not a or not b:
            return 0
        if a == b:
            return 3
        if a in b or b in a:
            return 2
        return 1 if difflib.SequenceMatcher(None, a, b).ratio() >= 0.8 else 0

    def resolve_pair(page: str, team: str, other: str):
        """Bridge Hotspawn -> Leaguepedia names using the fixture pair on the same page."""
        best, best_score = None, 0
        for t1, t2 in schedule_by_page.get(page, []):
            for cand, opp in ((t1, t2), (t2, t1)):
                if name_score(other, opp) < 2:
                    continue
                sc = name_score(team, cand) + name_score(other, opp)
                if sc > best_score:
                    best, best_score = cand, sc
        return (best, "schedule") if best_score >= 4 else (None, "missing")

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

    by_page: dict[str, dict[str, list[dict]]] = {}
    for r in standings:
        if not isinstance(r, dict):
            continue
        page = str(r.get("OverviewPage") or "")
        team = str(r.get("Team") or "")
        if page and team:
            by_page.setdefault(page, {}).setdefault(norm(team), []).append(r)

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

        def pick(team):
            """Resolve a Hotspawn name to one standings row; detect division ambiguity."""
            recs = t.get(norm(team)) or []
            if not recs:  # fuzzy fallback (same page), needs a close match
                close = difflib.get_close_matches(norm(team), list(t), n=1, cutoff=0.86)
                recs = t[close[0]] if close else []
            if not recs:
                return None, "missing"
            signatures = {(num(x.get("WinSeries")), num(x.get("LossSeries")),
                           num(x.get("WinGames")), num(x.get("LossGames"))) for x in recs}
            if len(signatures) > 1:
                return None, "ambiguous"   # same team name in two divisions with different records
            return recs[0], "ok"

        r1, why1 = pick(m["team1"])
        r2, why2 = pick(m["team2"])
        bridged = [None, None]
        if why1 == "missing" and schedule_by_page:
            nm, how = resolve_pair(page, m["team1"], m["team2"])
            if nm:
                rec1, _why = pick(nm)
                r1, why1, bridged[0] = rec1, "bridged", nm
        if why2 == "missing" and schedule_by_page:
            nm, how = resolve_pair(page, m["team2"], m["team1"])
            if nm:
                rec2, _why = pick(nm)
                r2, why2, bridged[1] = rec2, "bridged", nm
        wr1, n1, kind1 = rate(r1) if r1 else (None, 0, "none")
        wr2, n2, kind2 = rate(r2) if r2 else (None, 0, "none")
        if why1 == "ambiguous" or why2 == "ambiguous":
            rec.update({"status": "AMBIGUOUS_DIVISION", "prob_team1": 0.5, "prob_team2": 0.5,
                        "why": [why1, why2]})
            out.append(rec)
            continue
        if wr1 is None or wr2 is None:
            rec.update({"status": "NO_RECORD", "prob_team1": 0.5, "prob_team2": 0.5,
                        "why": [why1, why2]})
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
            "names_used": [bridged[0] or m["team1"], bridged[1] or m["team2"]],
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
        "rows_no_record": sum(1 for r in out if r.get("status") == "NO_RECORD"),
        "rows_ambiguous": sum(1 for r in out if r.get("status") == "AMBIGUOUS_DIVISION"),
        "scored": len(out),
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump({"summary": summary, "rows": out}, open(args.out, "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

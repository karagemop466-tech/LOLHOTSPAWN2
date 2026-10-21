#!/usr/bin/env python3
"""
apply_standings.py — enrich the published picks with a sourced standings line.

For every row that has no market price (UNRESOLVED / MODEL_ELO), attempt:
  1. map the Hotspawn tournament to its Leaguepedia league page (verified map),
  2. bridge team names through the Leaguepedia MatchSchedule fixture pair,
  3. read the official Standings record (WinSeries/LossSeries, else WinGames/LossGames),
  4. compute p = smoothed win-rate / (smoothed win-rate of both teams),
  5. publish method MODEL_STANDINGS with the league page as source_url and the
     exact records in the evidence string.

Rows that cannot be scored keep their 50/50 but gain:
  * the league page as `source_url` (so a human can check),
  * an explicit reason (`standings_status`: NO_PAGE / NO_RECORD / AMBIGUOUS_DIVISION).
Nothing is invented: a team with no completed series stays unscored.

Usage (offline test):
  python3 verification/apply_standings.py --standings snap.json --schedule sched.json --dry-run
Usage (production, GitHub Actions):
  python3 verification/apply_standings.py --fetch --write
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from check_leaguepedia_coverage import LEAGUE_MAP  # noqa: E402
from standings_line import calibrate, fetch_pages, norm, rate  # noqa: E402

WIKI = "https://lol.fandom.com/wiki/"
MODEL_METHOD = "MODEL_STANDINGS"


def page_url(page: str) -> str:
    return WIKI + page.replace(" ", "_")


def load_rows(path: str) -> list[dict]:
    data = json.load(open(path, encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("cargoquery") or data.get("rows") or []
    return [r.get("title", r) if isinstance(r, dict) else r for r in data]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--picks", default=os.path.join(ROOT, "docs", "data", "picks.json"))
    ap.add_argument("--standings", default="")
    ap.add_argument("--schedule", default=os.path.join(ROOT, "data", "diag", "lp_schedule.json"))
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--out", default="", help="write enriched payload here (default: --write paths)")
    ap.add_argument("--write", action="store_true",
                    help="overwrite data/picks.json and docs/data/picks.json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    payload = json.load(open(args.picks, encoding="utf-8"))
    rows = payload.get("matches", [])
    pages_needed = sorted({p for m in rows for p in LEAGUE_MAP.get((m.get("tournament") or "").strip(), [])})
    if args.fetch:
        standings = fetch_pages(pages_needed)
    elif args.standings and os.path.exists(args.standings):
        standings = load_rows(args.standings)
    else:
        print("need --fetch or --standings", file=sys.stderr)
        return 2

    by_page: dict[str, dict[str, list[dict]]] = {}
    for r in standings:
        if isinstance(r, dict) and r.get("OverviewPage") and r.get("Team"):
            by_page.setdefault(str(r["OverviewPage"]), {}).setdefault(norm(r["Team"]), []).append(r)

    sched_by_page: dict[str, list[tuple[str, str]]] = {}
    if args.fetch and not (args.schedule and os.path.exists(args.schedule)):
        import time as _time
        import urllib.parse
        import urllib.request
        CARGO = "https://lol.fandom.com/wiki/Special:CargoExport"
        UA_ = ("Mozilla/5.0 (compatible; LOLHOTSPAWN2-schedule/1.0; "
               "+https://github.com/karagemop466-tech/LOLHOTSPAWN2)")
        for page in pages_needed:
            url = CARGO + "?" + urllib.parse.urlencode({
                "tables": "MatchSchedule",
                "fields": "Team1,Team2,DateTime_UTC,OverviewPage,BestOf",
                "where": f"OverviewPage = '{page}'",
                "order_by": "DateTime_UTC DESC", "limit": "200", "format": "json"})
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA_,
                                                           "Accept": "application/json",
                                                           "Accept-Encoding": "gzip"})
                with urllib.request.urlopen(req, timeout=45) as r:
                    raw = r.read()
                if raw[:2] == b"\x1f\x8b":
                    import gzip
                    raw = gzip.decompress(raw)
                for row in json.loads(raw.decode("utf-8", "replace")):
                    if row.get("Team1") and row.get("Team2"):
                        sched_by_page.setdefault(page, []).append(
                            (str(row["Team1"]), str(row["Team2"])))
            except Exception as exc:  # noqa: BLE001
                print(f"schedule fetch failed for {page}: {exc!r}", file=sys.stderr)
            _time.sleep(3.0)
    if args.schedule and os.path.exists(args.schedule):
        for r in load_rows(args.schedule):
            if isinstance(r, dict) and r.get("OverviewPage") and r.get("Team1") and r.get("Team2"):
                sched_by_page.setdefault(str(r["OverviewPage"]), []).append(
                    (str(r["Team1"]), str(r["Team2"])))

    import difflib

    def name_score(a: str, b: str) -> int:
        x, y = norm(a), norm(b)
        if not x or not y:
            return 0
        if x == y:
            return 3
        if x in y or y in x:
            return 2
        return 1 if difflib.SequenceMatcher(None, x, y).ratio() >= 0.8 else 0

    def resolve(page: str, team: str, other: str) -> str | None:
        for t1, t2 in sched_by_page.get(page, []):
            for cand, opp in ((t1, t2), (t2, t1)):
                if name_score(team, cand) + name_score(other, opp) >= 4:
                    return cand
        return None

    def record(page: str, team: str) -> tuple[dict | None, str]:
        recs = by_page.get(page, {}).get(norm(team)) or []
        if not recs:
            close = difflib.get_close_matches(norm(team), list(by_page.get(page, {})), n=1, cutoff=0.88)
            recs = by_page[page][close[0]] if close else []
        if not recs:
            return None, "NO_RECORD"
        sigs = {(float(r.get("WinSeries") or 0), float(r.get("LossSeries") or 0),
                 float(r.get("WinGames") or 0), float(r.get("LossGames") or 0)) for r in recs}
        if len(sigs) > 1:
            return None, "AMBIGUOUS_DIVISION"
        return recs[0], "OK"

    scored = updated = 0
    status_counts: dict[str, int] = {}
    for m in rows:
        if str(m.get("method") or "").startswith("MARKET"):
            continue  # market rows keep their market price
        tour = (m.get("tournament") or "").strip()
        pages = LEAGUE_MAP.get(tour, [])
        page = next((p for p in pages if p in by_page), None)
        if not page:
            m["standings_status"] = "NO_PAGE"
            status_counts["NO_PAGE"] = status_counts.get("NO_PAGE", 0) + 1
            continue
        m["source_url"] = page_url(page)
        n1, n2 = m["team1"], m["team2"]
        if norm(n1) not in by_page.get(page, {}) or norm(n2) not in by_page.get(page, {}):
            b1 = resolve(page, n1, n2)
            b2 = resolve(page, n2, n1)
            n1, n2 = b1 or n1, b2 or n2
        r1, why1 = record(page, n1)
        r2, why2 = record(page, n2)
        for why in (why1, why2):
            status_counts[why] = status_counts.get(why, 0) + 1
        if not r1 or not r2:
            m["standings_status"] = "AMBIGUOUS_DIVISION" if "AMBIGUOUS_DIVISION" in (why1, why2) else "NO_RECORD"
            missing = [t for t, r in ((n1, r1), (n2, r2)) if not r]
            m["evidence"] = (f"No completed series for {', '.join(missing)} on Leaguepedia "
                             f"({page}); 50/50 placeholder — see the league page")
            continue
        wr1, g1, kind = rate(r1)
        wr2, g2, _ = rate(r2)
        if wr1 is None or wr2 is None:
            m["standings_status"] = "NO_RECORD"
            continue
        multi = sum(1 for recs in by_page[page].values() for x in recs
                    if int(float(x.get("Place") or 0)) == 1) > 1
        p = calibrate(wr1 / (wr1 + wr2), multi)
        rec1 = f"{int(float(r1.get('WinSeries') or 0))}-{int(float(r1.get('LossSeries') or 0))}"
        rec2 = f"{int(float(r2.get('WinSeries') or 0))}-{int(float(r2.get('LossSeries') or 0))}"
        conf = "High — official standings, ≥5 series" if min(g1, g2) >= 5 else \
               "Medium — official standings, 2-4 series" if min(g1, g2) >= 2 else \
               "Low — official standings, ≤1 series"
        if multi:
            conf = "Low — multi-division standings (division not published in the data); shrunk toward 50%"
        m.update({
            "prob_team1": p, "prob_team2": round(1 - p, 4),
            "pick": m["team1"] if p >= 0.5 else m["team2"],
            "pick_prob": max(p, 1 - p),
            "method": MODEL_METHOD,
            "evidence": (f"Leaguepedia standings ({page}): {n1} {rec1} vs {n2} {rec2} "
                         f"[{kind} win rate, smoothed]"),
            "confidence": conf,
            "source_url": page_url(page),
            "standings": {"records": [rec1, rec2], "decided": [g1, g2], "basis": kind,
                          "multi_division": multi,
                          "names_used": [n1, n2]},
            "standings_status": "SCORED",
        })
        scored += 1
        updated += 1

    counts = {}
    for m in rows:
        counts[m.get("method")] = counts.get(m.get("method"), 0) + 1
    payload["counts_by_method"] = counts
    payload["count"] = len(rows)
    payload.setdefault("debug", {})
    payload["debug"]["standings"] = {
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "pages": sorted(by_page),
        "rows_scored": scored,
        "status_counts": status_counts,
        "model": "smoothed series win-rate (a=2) -> Bradley-Terry; games fallback (a=4)",
    }
    summary = {"rows_scored": scored, "method_counts": counts, "status_counts": status_counts}

    if args.dry_run:
        print(json.dumps(summary, indent=1))
        return 0
    targets = []
    if args.out:
        targets.append(args.out)
    if args.write:
        targets += [os.path.join(ROOT, "data", "picks.json"),
                    os.path.join(ROOT, "docs", "data", "picks.json")]
    if not targets:
        print("nothing written (use --out or --write or --dry-run)", file=sys.stderr)
        return 2
    for t in targets:
        os.makedirs(os.path.dirname(t), exist_ok=True)
        json.dump(payload, open(t, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print("wrote", t, file=sys.stderr)
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

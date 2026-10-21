#!/usr/bin/env python3
"""
leaguepedia_line.py — independent, auditable results model for fixtures that no
bookmaker prices (used by T12 as a differential check and as a drop-in
post-processor if the production model cannot use Leaguepedia results).

Method (deliberately simple and explainable):
  * Elo over Leaguepedia ScoreboardGames rows (Team1, Team2, Winner, DateTime UTC),
    K=24, start 1500, only games within --window-days (default 400).
  * Probability p = 1/(1+10**((r2-r1)/400)), shrunk toward 0.5 by sample size:
        p' = 0.5 + (p-0.5) * m/(m+6),  m = games of the thinner team
  * Teams with no games in the window are rated 1500 and shrink double.
  * Every fixture keeps a per-league source link (Leaguepedia overview page).

This is NOT a substitute for a market line and is labelled as an own model.
Usage:
  python3 verification/leaguepedia_line.py \
      --picks docs/data/picks.json --schedule data/diag/lp_schedule.json \
      --results data/diag/lp_recent_sg.json --out verification/leaguepedia_line.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIKI = "https://lol.fandom.com/wiki/"
try:
    from check_leaguepedia_coverage import LEAGUE_MAP  # same directory
except Exception:  # noqa: BLE001
    import importlib.util
    _spec = importlib.util.spec_from_file_location(
        "cov", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "check_leaguepedia_coverage.py"))
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    LEAGUE_MAP = _mod.LEAGUE_MAP


def norm(s) -> str:
    return re.sub(r"[^a-z0-9]", "", (str(s or "")).lower())


def parse_dt(v) -> datetime | None:
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v / 1000, timezone.utc)
    s = str(v or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:19], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def field(row: dict, *names):
    for n in names:
        if n in row and row[n] not in (None, ""):
            return row[n]
    low = {str(k).lower().replace("_", " "): v for k, v in row.items()}
    for n in names:
        v = low.get(str(n).lower().replace("_", " "))
        if v not in (None, ""):
            return v
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--picks", default=os.path.join(ROOT, "docs", "data", "picks.json"))
    ap.add_argument("--schedule", default=os.path.join(ROOT, "data", "diag", "lp_schedule.json"))
    ap.add_argument("--results", default=os.path.join(ROOT, "data", "diag", "lp_recent_sg.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "verification", "leaguepedia_line.json"))
    ap.add_argument("--window-days", type=int, default=400)
    ap.add_argument("--only-unresolved", action="store_true", default=True)
    ap.add_argument("--all-rows", dest="only_unresolved", action="store_false")
    args = ap.parse_args()

    picks = json.load(open(args.picks, encoding="utf-8"))
    rows = picks.get("matches", [])
    results = []
    if os.path.exists(args.results):
        results = json.load(open(args.results, encoding="utf-8"))
        if isinstance(results, dict):
            results = results.get("cargoquery") or results.get("rows") or []
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.window_days)

    games = []
    for r in results:
        if not isinstance(r, dict):
            continue
        r = r.get("title", r)
        t1, t2 = field(r, "Team1", "team1"), field(r, "Team2", "team2")
        w = field(r, "Winner", "winner")
        dt = parse_dt(field(r, "DateTime UTC", "DateTime_UTC", "date"))
        if not (t1 and t2 and w and dt) or dt < cutoff:
            continue
        games.append((dt, str(t1), str(t2), str(w)))
    games.sort(key=lambda g: g[0])

    ratings: dict[str, float] = {}
    played: dict[str, int] = {}
    for dt, t1, t2, w in games:
        a, b = norm(t1), norm(t2)
        ra, rb = ratings.get(a, 1500.0), ratings.get(b, 1500.0)
        ea = 1 / (1 + 10 ** ((rb - ra) / 400))
        win_a = w.strip() in ("1", "1.0") or w.strip().lower() == t1.strip().lower()
        delta = 24 * ((1 if win_a else 0) - ea)
        ratings[a], ratings[b] = ra + delta, rb - delta
        played[a] = played.get(a, 0) + 1
        played[b] = played.get(b, 0) + 1

    schedule = []
    if os.path.exists(args.schedule):
        schedule = json.load(open(args.schedule, encoding="utf-8"))
        if isinstance(schedule, dict):
            schedule = schedule.get("cargoquery") or schedule.get("rows") or []
    sched_by_pair: dict[tuple[str, str], dict] = {}
    for r in schedule:
        if isinstance(r, dict):
            r = r.get("title", r)
            k = (norm(field(r, "Team1")), norm(field(r, "Team2")))
            if all(k):
                sched_by_pair.setdefault(k, r)

    output, changed = [], 0
    for m in rows:
        if args.only_unresolved and m.get("method") not in ("UNRESOLVED", "MODEL_ELO"):
            continue
        a, b = norm(m["team1"]), norm(m["team2"])
        ra, rb = ratings.get(a, 1500.0), ratings.get(b, 1500.0)
        ga, gb = played.get(a, 0), played.get(b, 0)
        raw = 1 / (1 + 10 ** ((rb - ra) / 400))
        thin = min(ga, gb)
        shrink = thin / (thin + 6) if thin else 0.0
        p = 0.5 + (raw - 0.5) * shrink if thin else 0.5
        p = round(min(0.95, max(0.05, p)), 4)
        page = (LEAGUE_MAP.get((m.get("tournament") or "").strip()) or [None])[0]
        rec = {
            "team1": m["team1"], "team2": m["team2"], "tournament": m.get("tournament"),
            "prob_team1": p, "prob_team2": round(1 - p, 4),
            "elo_raw": round(raw, 4), "ratings": [round(ra), round(rb)],
            "games_in_window": [ga, gb], "shrink": round(shrink, 3),
            "source_url": (WIKI + page.replace(" ", "_")) if page else None,
            "evidence": (f"Own Elo v2 (Leaguepedia ScoreboardGames, {args.window_days}d): "
                         f"{m['team1']} {round(ra)} ({ga}g) vs {m['team2']} {round(rb)} ({gb}g)"),
        }
        if abs(p - 0.5) >= 0.02:
            changed += 1
        output.append(rec)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "games_used": len(games),
        "teams_rated": len(ratings),
        "fixtures_scored": len(output),
        "fixtures_moved_off_50_50": changed,
        "window_days": args.window_days,
        "results_source": os.path.relpath(args.results, ROOT) if os.path.exists(args.results) else None,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump({"summary": summary, "rows": output}, open(args.out, "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    print(json.dumps(summary, indent=1))
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

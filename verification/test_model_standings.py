#!/usr/bin/env python3
"""Offline regression test for the standings line and the tier prior.

Builds a small synthetic Leaguepedia payload (results + standings) and checks that
scripts/model.py produces the documented behaviour:

  * a fixture where one side has no results but IS listed in the official standings
    gets a MODEL_STANDINGS pick that links the exact league page;
  * the unrated side is no longer priced off a single pooled global median — the
    tournament's own tier prior is used;
  * a fixture with no results and no standings row stays UNRESOLVED / 50-50.

No network access is used, so this runs in the offline verification job.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import model  # noqa: E402

NOW = datetime.now(timezone.utc)


def iso(days_ago: float) -> str:
    return (NOW - timedelta(days=days_ago)).isoformat().replace("+00:00", "Z")


def fixture(fid, t1, t2, tournament, hours=12):
    start = (NOW + timedelta(hours=hours)).isoformat().replace("+00:00", "Z")
    return {"id": fid, "team1": t1, "team2": t2, "tournament": tournament,
            "competition_id": "1", "tier": "C", "stage": "group", "points": 10,
            "best_of": 3, "start_utc": start, "status": "scheduled",
            "hotspawn_url": f"https://www.hotspawn.com/matches/{fid}",
            "source_lobby": "https://play.hotspawn.com/lol-pickems",
            "crowd": {"team1_pct": 50, "team2_pct": 50, "total_picks": 1,
                      "note": "context only"}}


PAGE = "Prime League 2nd Division/2027 Season/Fall Split"

results = []
# Rated teams with plenty of history inside the same competition
for i in range(12):
    results.append({"team1": "Rated One", "team2": f"Filler {i % 3}", "winner": 1 if i % 2 else 2,
                    "score1": 2, "score2": 1, "start_utc": iso(30 + i),
                    "overview": PAGE, "best_of": 3, "tab": ""})
for i in range(12):
    results.append({"team1": "Rated Two", "team2": f"Filler {i % 3}", "winner": 1 if i % 4 else 2,
                    "score1": 2, "score2": 1, "start_utc": iso(31 + i),
                    "overview": PAGE, "best_of": 3, "tab": ""})

leaguepedia = {
    "results": results,
    "schedule": [],
    "teams": [],
    "standings": [
        {"page": PAGE, "team": "Rated One", "place": 1, "wins": 8, "losses": 1,
         "win_games": 17, "loss_games": 4, "points": 24},
        {"page": PAGE, "team": "Brand New", "place": 5, "wins": 3, "losses": 5,
         "win_games": 8, "loss_games": 12, "points": 9},
        {"page": PAGE, "team": "Rated Two", "place": 2, "wins": 6, "losses": 3,
         "win_games": 14, "loss_games": 8, "points": 18},
        {"page": PAGE, "team": "With Record", "place": 7, "wins": 4, "losses": 5,
         "win_games": 9, "loss_games": 12, "points": 12},
        {"page": PAGE, "team": "Another", "place": 8, "wins": 2, "losses": 6,
         "win_games": 6, "loss_games": 14, "points": 6},
    ],
    "standings_pages": [PAGE],
    "standings_by_tournament": {"PRM 2nd Division 27 Fall": [PAGE]},
}

hotspawn = {
    "fixtures": [
        fixture("1", "Rated One", "Brand New", "PRM 2nd Division 27 Fall"),
        fixture("2", "Rated One", "Unlisted Team", "PRM 2nd Division 27 Fall"),
        fixture("3", "Brand New", "With Record", "PRM 2nd Division 27 Fall"),
        fixture("4", "Nobody A", "Nobody B", "Obscure Cup 2026"),
        fixture("5", "Rated One", "Rated Two", "PRM 2nd Division 27 Fall"),
    ],
    "count": 5,
}
markets = {"records": [], "statuses": []}


def main() -> int:
    payload = model.build_matches(hotspawn, leaguepedia, markets, model.load_aliases())
    rows = {r["id"]: r for r in payload["matches"]}
    ok = True

    def check(cond, msg):
        nonlocal ok
        print(f"  [{'ok' if cond else 'FAILED'}] {msg}")
        ok = ok and bool(cond)

    r = rows["1"]
    check(r["method"] == "MODEL_STANDINGS",
          f"one side unrated but in standings -> MODEL_STANDINGS (got {r['method']})")
    check((r.get("standings") or {}).get("page") == PAGE, "row links the standings page it used")
    check((r.get("source_url") or "").startswith("https://lol.fandom.com/wiki/"),
          "source_url points at the league page")
    check(abs(r["prob_team1"] - 0.5) > 0.02, f"line is not a coin flip ({r['prob_team1']})")
    check("STANDINGS_LINE_USED" in r["flags"], "row is flagged STANDINGS_LINE_USED")

    r = rows["3"]
    check(r["method"] == "MODEL_STANDINGS", "both sides from standings -> MODEL_STANDINGS")
    check(r["confidence"] in ("Low", "Medium"), f"confidence is honest ({r['confidence']})")

    r = rows["2"]
    check(r["method"] == "MODEL_LEAGUE_PRIOR", "unlisted side falls back to the tier prior")
    check(r["model"].get("prior_used") != "global median",
          f"prior is not the pooled global median ({r['model'].get('prior_used')})")
    check(1460 <= float(r["model"]["elo_prior"]) <= 1520,
          f"prior is the Prime League tier, not a Worlds median ({r['model']['elo_prior']})")

    r = rows["4"]
    check(r["method"] == "UNRESOLVED" and abs(r["prob_team1"] - 0.5) < 1e-9,
          "no results and no standings -> explicit 50/50")

    r = rows["5"]
    check(r["method"] in ("MODEL_ELO", "MODEL_ELO_THIN"), "both rated -> Elo model")

    print(f"\n{'PASS' if ok else 'FAIL'} — standings/tier-prior regression test")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

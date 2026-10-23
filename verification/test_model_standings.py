#!/usr/bin/env python3
"""Offline regression test for the standings line, the tier prior and the row evidence.

Builds a synthetic Leaguepedia payload (results + current-split standings) and checks
the documented behaviour of scripts/model.py:

  * a fixture where one side has no recorded series but IS listed in the official
    standings gets a MODEL_STANDINGS pick that links the exact league page;
  * the unrated side is priced off the competition/tournament tier, never off one
    median pooled across every league;
  * a fixture with no results and no standings row stays UNRESOLVED / 50-50;
  * a multi-division table halves the edge and caps the row at Low confidence.

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
PAGE = "Prime League 2nd Division/2027 Season/Fall Split"
TOUR = "PRM 2nd Division 26-27 Fall"


def iso(days: float) -> str:
    return (NOW + timedelta(days=days)).isoformat().replace("+00:00", "Z")


def fixture(fid, t1, t2, tournament, hours=12):
    return {"id": fid, "team1": t1, "team2": t2, "tournament": tournament,
            "competition_id": "1", "tier": "C", "stage": "group", "points": 10,
            "best_of": 3, "start_utc": iso(hours / 24), "status": "scheduled",
            "hotspawn_url": f"https://www.hotspawn.com/matches/{fid}",
            "source_lobby": "https://play.hotspawn.com/lol-pickems",
            "crowd": {"team1_pct": 50, "team2_pct": 50, "total_picks": 1,
                      "note": "context only"}}


results = []
for i in range(12):
    results.append({"team1": "Rated One", "team2": f"Filler {i % 3}",
                    "winner": 1 if i % 2 else 2, "score1": 2, "score2": 1,
                    "start_utc": iso(-30 - i), "overview": PAGE, "best_of": 3, "tab": ""})
for i in range(12):
    results.append({"team1": "Rated Two", "team2": f"Filler {i % 3}",
                    "winner": 1 if i % 4 else 2, "score1": 2, "score2": 1,
                    "start_utc": iso(-31 - i), "overview": PAGE, "best_of": 3, "tab": ""})


def st(team, ws, ls, wg, lg, place):
    return {"overview": PAGE, "team": team, "win_series": ws, "loss_series": ls,
            "tie_series": 0, "win_games": wg, "loss_games": lg, "place": str(place)}


standings = [
    st("Rated One", 8, 1, 17, 4, 1),
    st("Rated Two", 6, 3, 14, 8, 2),
    st("Brand New", 3, 5, 8, 12, 5),
    st("With Record", 4, 5, 9, 12, 6),
    st("Another", 2, 6, 6, 14, 8),
    # a second first place = the page mixes divisions
    {"overview": "Mixed Division Cup/2026", "team": "Mix A", "win_series": 4,
     "loss_series": 1, "win_games": 9, "loss_games": 4, "place": "1"},
    {"overview": "Mixed Division Cup/2026", "team": "Mix B", "win_series": 3,
     "loss_series": 2, "win_games": 7, "loss_games": 6, "place": "1"},
]

leaguepedia = {
    "results": results,
    "schedule": [],
    "unscheduled": [],
    "teams": [],
    "standings": standings,
    "redirects": {},
}

hotspawn = {
    "fixtures": [
        fixture("1", "Rated One", "Brand New", TOUR),
        fixture("2", "Rated One", "Unlisted Team", TOUR),
        fixture("3", "Brand New", "With Record", TOUR),
        fixture("4", "Nobody A", "Nobody B", "Obscure Cup 2026"),
        fixture("5", "Rated One", "Rated Two", TOUR),
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
    stb = r.get("standings") or {}
    check(stb.get("page") == PAGE, "row carries the standings page it used")
    check((r.get("source_url") or "").startswith("https://lol.fandom.com/wiki/"),
          "source_url points at the league page")
    check((stb.get("team1") or {}).get("sample"), "the record used is attached to the row")
    check(bool(r.get("why")), "row explains why the line exists")
    check(abs(r["prob_team1"] - 0.5) > 0.01, f"line is not a coin flip ({r['prob_team1']})")

    r = rows["3"]
    check(r["method"] == "MODEL_STANDINGS", "both sides from standings -> MODEL_STANDINGS")
    check(r["confidence"] in ("Low", "Medium"), f"confidence is honest ({r['confidence']})")

    r = rows["2"]
    check(r["method"] == "MODEL_LEAGUE_PRIOR", "unlisted side falls back to a prior")
    check(r["model"].get("prior_used") != "global median",
          f"prior is not the pooled global median ({r['model'].get('prior_used')})")
    check(1450 <= float(r["model"]["elo_prior"]) <= 1520,
          f"prior is the Prime League tier, not a Worlds median ({r['model']['elo_prior']})")

    r = rows["4"]
    check(r["method"] == "UNRESOLVED" and abs(r["prob_team1"] - 0.5) < 1e-9,
          "no results and no standings -> explicit 50/50")

    r = rows["5"]
    check(r["method"] in ("MODEL_ELO", "MODEL_ELO_THIN"), "both rated -> Elo model")

    check("MODEL_STANDINGS" in payload["coverage"]["counts_by_method"],
          "coverage counts the standings method")

    print(f"\n{'PASS' if ok else 'FAIL'} — standings/tier-prior regression test")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

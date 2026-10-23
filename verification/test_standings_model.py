#!/usr/bin/env python3
"""Offline unit test for the MODEL_STANDINGS fallback (no network).

Builds tiny synthetic inputs where the two fixture teams have NO recorded
results (so Elo cannot rate them) but DO have Leaguepedia Standings records:
  Alpha 5-1 vs Beta 1-5  ->  wr = (5+2)/(6+4)=0.7 vs (1+2)/(6+4)=0.3
  Bradley-Terry p(Alpha) = 0.7 / (0.7+0.3) = 0.70, confidence Medium (>=5 decided).
Also checks: equal records -> 0.50; missing standings -> UNRESOLVED 50/50;
standings never overrides a rated Elo pair.
Run: python3 verification/test_standings_model.py
"""
import os
import sys
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from lib_common import now_utc, utc_iso  # noqa: E402
import model as M  # noqa: E402

NOW = now_utc()
PAGE = "Test League/2026 Season/Split 1"
ALIASES = {"hotspawn_to_leaguepedia": {}, "market_aliases": {}}
failures = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  {detail}" if detail else ""))
    if not cond:
        failures.append(name)


def fixture(fid, t1, t2, when):
    return {"id": fid, "team1": t1, "team2": t2, "tournament": "Test League 2026",
            "competition_id": "1", "tier": "C", "stage": "group", "points": 10,
            "best_of": 3, "start_utc": utc_iso(when), "status": "scheduled",
            "hotspawn_url": "https://www.hotspawn.com/matches/x",
            "source_lobby": "https://play.hotspawn.com/lol-pickems", "crowd": {}}


def sched_row(t1, t2, when, winner=None, s1=None, s2=None):
    return {"team1": t1, "team2": t2, "score1": s1, "score2": s2, "winner": winner,
            "start_utc": utc_iso(when), "overview": PAGE, "best_of": 3, "tab": ""}


def standings_row(team, ws, ls):
    return {"overview": PAGE, "team": team, "place": None, "win_series": ws,
            "loss_series": ls, "tie_series": 0, "win_games": None, "loss_games": None}


future = NOW + timedelta(days=2)
# Other teams' played results give the league a prior, but Alpha/Beta never play.
results = [sched_row("Gamma", "Delta", NOW - timedelta(days=10 - i), winner=1, s1=2, s2=0)
           for i in range(6)]
schedule = [sched_row("Alpha", "Beta", future)]

hotspawn = {"fixtures": [fixture("1", "Alpha", "Beta", future)]}
markets = {"records": []}

# 1) Standings 5-1 vs 1-5 -> MODEL_STANDINGS 0.70 Medium with league source link
lp = {"results": results, "schedule": schedule, "teams": [],
      "standings": [standings_row("Alpha", 5, 1), standings_row("Beta", 1, 5)]}
out = M.build_matches(hotspawn, lp, markets, ALIASES)["matches"][0]
check("standings method", out["method"] == "MODEL_STANDINGS", out["method"])
check("standings prob 0.70", abs(out["prob_team1"] - 0.70) < 1e-6, str(out["prob_team1"]))
check("standings pick", out["pick"] == "Alpha" and abs(out["pick_prob"] - 0.70) < 1e-6)
check("standings confidence Medium", out["confidence"] == "Medium", out["confidence"])
check("standings source page", any(PAGE.replace(" ", "_") in (s.get("url") or "")
                                   for s in out["sources"]), str(out["sources"]))
check("standings evidence has records", "5-1" in out["evidence"] and "1-5" in out["evidence"],
      out["evidence"])

# 2) Equal standings -> 50/50 but still a real (labelled) standings row
lp2 = dict(lp, standings=[standings_row("Alpha", 3, 3), standings_row("Beta", 3, 3)])
out2 = M.build_matches(hotspawn, lp2, markets, ALIASES)["matches"][0]
check("equal records 0.50", out2["method"] == "MODEL_STANDINGS" and abs(out2["prob_team1"] - 0.5) < 1e-6,
      f"{out2['method']} {out2['prob_team1']}")

# 3) No standings at all -> honest UNRESOLVED placeholder
lp3 = dict(lp, standings=[])
out3 = M.build_matches(hotspawn, lp3, markets, ALIASES)["matches"][0]
check("no signal unresolved", out3["method"] == "UNRESOLVED" and out3["pick_prob"] == 0.5,
      f"{out3['method']} {out3['pick_prob']}")

# 4) Rated Elo pair beats standings (standings must not override Elo)
played = []
for i in range(10):
    played.append(sched_row("Alpha", "Gamma", NOW - timedelta(days=30 - i), winner=2, s1=0, s2=2))
    played.append(sched_row("Beta", "Delta", NOW - timedelta(days=30 - i), winner=1, s1=2, s2=0))
lp4 = dict(lp, results=results + played)
out4 = M.build_matches(hotspawn, lp4, markets, ALIASES)["matches"][0]
check("elo preferred over standings", out4["method"] in ("MODEL_ELO", "MODEL_ELO_THIN"), out4["method"])

# 6) Teams that exist ONLY in the standings table still resolve (4-0 vs 0-4 -> 0.75)
lp6 = {"results": results, "schedule": [], "teams": [],
       "standings": [standings_row("Newcomers", 4, 0), standings_row("Strugglers", 0, 4)]}
out6 = M.build_matches({"fixtures": [fixture("9", "Newcomers", "Strugglers", future)]},
                       lp6, markets, ALIASES)["matches"][0]
check("standings-only teams resolve", out6["method"] == "MODEL_STANDINGS"
      and abs(out6["prob_team1"] - 0.75) < 1e-6, f"{out6['method']} {out6['prob_team1']}")

# 5) Zero-decided standings rows are not evidence
lp5 = dict(lp, standings=[standings_row("Alpha", 0, 0), standings_row("Beta", 0, 0)])
out5 = M.build_matches(hotspawn, lp5, markets, ALIASES)["matches"][0]
check("0-0 standings not used", out5["method"] != "MODEL_STANDINGS", out5["method"])

print(f"\n{'ALL PASS' if not failures else 'FAILURES: ' + ', '.join(failures)}")
raise SystemExit(1 if failures else 0)

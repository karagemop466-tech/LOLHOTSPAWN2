#!/usr/bin/env python3
"""Offline behavioural test for the MODEL_STANDINGS path (no network).

Merged production semantics (sessions arena/92bfcdd3 + arena/0fb2d0c7):
when a side has no Elo but has a current-split Leaguepedia Standings record
(>=1 decided series), the record becomes a smoothed Elo offset from the
competition prior and the row is labelled MODEL_STANDINGS (Low confidence).
Exact probabilities depend on priors/shrinkage, so this test asserts
behaviour, not a specific formula output:
  * stronger standings record is favoured and picked,
  * equal records price ~50/50,
  * no standings + no Elo stays an honest UNRESOLVED 50/50,
  * a rated Elo pair is never overridden by standings,
  * 0-0 standings rows are not evidence.
Run: python3 verification/test_standings_model.py
"""
import os
import sys
from datetime import timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.chdir(ROOT)

from lib_common import now_utc, utc_iso  # noqa: E402
import model as M  # noqa: E402

NOW = now_utc()
PAGE = "Test League/2026 Season/Split 1"
ALIASES = M.load_aliases("data/aliases.json")
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


def standings_row(team, ws, ls, wg=None, lg=None):
    return {"overview": PAGE, "team": team, "place": None, "win_series": ws,
            "loss_series": ls, "tie_series": 0,
            "win_games": (2 * ws if wg is None else wg),
            "loss_games": (2 * ls if lg is None else lg)}


future = NOW + timedelta(days=2)
results = [sched_row("Gamma", "Delta", NOW - timedelta(days=10 - i), winner=1, s1=2, s2=0)
           for i in range(6)]
schedule = [sched_row("Alpha", "Beta", future)]
hotspawn = {"fixtures": [fixture("1", "Alpha", "Beta", future)]}
markets = {"records": []}

# 1) No Elo for either side + standings 5-1 vs 1-5 -> MODEL_STANDINGS favours Alpha
lp = {"results": results, "schedule": schedule, "teams": [],
      "standings": [standings_row("Alpha", 5, 1), standings_row("Beta", 1, 5)]}
out = M.build_matches(hotspawn, lp, markets, ALIASES)["matches"][0]
check("standings method", out["method"] == "MODEL_STANDINGS", out["method"])
check("stronger record favoured", 0.55 < out["prob_team1"] < 0.90, str(out["prob_team1"]))
check("standings pick", out["pick"] == "Alpha")
check("standings capped Low", out["confidence"] == "Low", out["confidence"])
check("evidence cites standings", "standings" in out["evidence"].lower(), out["evidence"][:100])

# 2) Equal records -> ~50/50, still a labelled standings row
lp2 = dict(lp, standings=[standings_row("Alpha", 3, 3), standings_row("Beta", 3, 3)])
out2 = M.build_matches(hotspawn, lp2, markets, ALIASES)["matches"][0]
check("equal records ~0.50", out2["method"] == "MODEL_STANDINGS" and abs(out2["prob_team1"] - 0.5) < 0.03,
      f"{out2['method']} {out2['prob_team1']}")

# 3) No standings and no Elo for the pair -> UNRESOLVED placeholder
lp3 = dict(lp, standings=[])
out3 = M.build_matches(hotspawn, lp3, markets, ALIASES)["matches"][0]
check("no signal unresolved", out3["method"] == "UNRESOLVED" and out3["pick_prob"] == 0.5,
      f"{out3['method']} {out3['pick_prob']}")

# 4) Rated Elo pair beats standings
played = []
for i in range(10):
    played.append(sched_row("Alpha", "Gamma", NOW - timedelta(days=30 - i), winner=2, s1=0, s2=2))
    played.append(sched_row("Beta", "Delta", NOW - timedelta(days=30 - i), winner=1, s1=2, s2=0))
lp4 = dict(lp, results=results + played)
out4 = M.build_matches(hotspawn, lp4, markets, ALIASES)["matches"][0]
check("elo preferred over standings", out4["method"] in ("MODEL_ELO", "MODEL_ELO_THIN"), out4["method"])

# 5) 0-0 standings rows are not evidence
lp5 = dict(lp, standings=[standings_row("Alpha", 0, 0, wg=0, lg=0),
                          standings_row("Beta", 0, 0, wg=0, lg=0)])
out5 = M.build_matches(hotspawn, lp5, markets, ALIASES)["matches"][0]
check("0-0 standings not used", out5["method"] != "MODEL_STANDINGS", out5["method"])

# 6) One Elo side + one standings side still resolves via standings blend
lp6 = dict(lp, results=results + [r for r in played if r["team1"] == "Alpha"])  # Beta only in standings
out6 = M.build_matches(hotspawn, lp6, markets, ALIASES)["matches"][0]
check("elo+standings blend resolves", out6["method"] == "MODEL_STANDINGS", out6["method"])

print(f"\n{'ALL PASS' if not failures else 'FAILURES: ' + ', '.join(failures)}")
raise SystemExit(1 if failures else 0)

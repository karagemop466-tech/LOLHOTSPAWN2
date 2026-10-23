#!/usr/bin/env python3
"""Offline regression tests for the T17/T18 additions.

Covers:
  * book de-duplication (one book must count once, props excluded),
  * the standings branch (both teams have a current-season record),
  * the untouched fallbacks (league prior when only one side is rated,
    UNRESOLVED when nothing is known).

Run: python3 audit/test_model.py   (no network)
"""
from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.chdir(ROOT)

import model  # noqa: E402
from fetch_markets import dedupe_records, is_prop_name  # noqa: E402


def fixture(**kw):
    base = {
        "id": "1", "team1": "Alpha", "team2": "Beta", "tournament": "Test League 2027",
        "competition_id": "9", "tier": "C", "stage": "group", "points": 10, "best_of": 3,
        "start_utc": "2026-10-24T12:00:00Z", "status": "scheduled",
        "hotspawn_url": "https://www.hotspawn.com/matches/x",
        "source_lobby": "https://play.hotspawn.com/lol-pickems",
        "crowd": {"team1_pct": 50, "team2_pct": 50, "total_picks": 1, "note": "context only"},
    }
    base.update(kw)
    return base


def market_record(source, key, a, b, start, prob_a, mid):
    return {"source": source, "source_key": key, "team_a": a, "team_b": b,
            "start_utc": start, "prob_a": prob_a, "prob_b": 1 - prob_a,
            "url": "https://example.invalid/market", "note": "", "raw": {"matchup_id": mid}}


SCHEDULE = [{"team1": "Alpha", "team2": "Beta", "score1": None, "score2": None, "winner": None,
             "start_utc": "2026-10-24T12:00:00Z", "overview": "Test League/2027 Season/Fall",
             "best_of": 3, "tab": ""}]
STANDINGS = [
    {"_page": "Test League/2027 Season/Fall", "Team": "Alpha", "WinSeries": 6, "LossSeries": 1,
     "WinGames": ""},
    {"_page": "Test League/2027 Season/Fall", "Team": "Beta", "WinSeries": 2, "LossSeries": 4,
     "WinGames": ""},
]


def leaguepedia(results=None, schedule=None, standings=None):
    return {"results": results or [], "schedule": schedule or [],
            "teams": [{"Name": "Alpha"}, {"Name": "Beta"}, {"Name": "Gamma"}],
            "standings": standings or []}


class TestDedupe(unittest.TestCase):
    def test_one_book_counts_once(self):
        rows = [market_record("Pinnacle", "pinnacle", "Gen.G", "Invictus Gaming",
                              "2026-10-23T18:00:00Z", 0.764, i) for i in range(1, 5)]
        rows.append(market_record("Bovada", "bovada", "Gen.G", "Invictus Gaming",
                                  "2026-10-23T18:00:00Z", 0.766, 9))
        rows.append(market_record("Polymarket", "polymarket", "Gen.G", "Invictus Gaming",
                                  "2026-10-23T18:00:00Z", 0.775, 11))
        kept, dropped = dedupe_records(rows)
        self.assertEqual(len(kept), 3, "three books must remain three records")
        self.assertEqual(len(dropped), 3, "three duplicate board rows must be collapsed")
        pinn = [r for r in kept if r["source_key"] == "pinnacle"][0]
        self.assertEqual(len(pinn["raw"]["duplicates_collapsed"]), 3)

    def test_prop_markets_rejected(self):
        self.assertTrue(is_prop_name("Gen.G (Kills)"))
        self.assertTrue(is_prop_name("Top Esports (Maps)"))
        self.assertFalse(is_prop_name("Gen.G"))
        self.assertFalse(is_prop_name("Anyone's Legend"))


class TestModel(unittest.TestCase):
    def _run(self, fixtures, lp, markets=None):
        out = model.build_matches({"fixtures": fixtures}, lp, markets or {"records": []},
                                  model.load_aliases("data/aliases.json"))
        return {m["id"]: m for m in out["matches"]}

    def test_standings_line_when_no_elo(self):
        rows = self._run([fixture()], leaguepedia(schedule=SCHEDULE, standings=STANDINGS))
        m = rows["1"]
        self.assertEqual(m["method"], "MODEL_STANDINGS")
        self.assertGreater(m["prob_team1"], 0.5)
        self.assertLess(m["prob_team1"], 0.85, "small samples must be shrunk")
        self.assertTrue(m["source_url"].startswith("https://lol.fandom.com/wiki/Test_League"))
        self.assertIn("standings", m["evidence"].lower())
        self.assertEqual(m["confidence"], "Low")

    def test_market_wins_over_model(self):
        rec = market_record("Pinnacle", "pinnacle", "Alpha", "Beta",
                            "2026-10-24T12:00:00Z", 0.30, 1)
        rows = self._run([fixture()], leaguepedia(schedule=SCHEDULE, standings=STANDINGS),
                         {"records": [rec]})
        m = rows["1"]
        self.assertEqual(m["method"], "MARKET_SINGLE")
        self.assertAlmostEqual(m["pick_prob"], 0.70, places=2)
        self.assertTrue(m["market"]["sources"])

    def test_league_prior_when_only_one_side_rated(self):
        results = [{"team1": "Alpha", "team2": "Gamma", "score1": 2, "score2": 0, "winner": 1,
                    "start_utc": f"2026-09-0{i}T12:00:00Z",
                    "overview": "Test League/2027 Season/Fall", "best_of": 3, "tab": ""}
                   for i in range(1, 6)]
        rows = self._run([fixture()], leaguepedia(results=results, schedule=SCHEDULE))
        self.assertEqual(rows["1"]["method"], "MODEL_LEAGUE_PRIOR")
        self.assertIn("ONE_TEAM_NO_HISTORY", rows["1"]["flags"])

    def test_unresolved_when_nothing_known(self):
        rows = self._run([fixture()], leaguepedia())
        m = rows["1"]
        self.assertEqual(m["method"], "UNRESOLVED")
        self.assertEqual(m["pick_prob"], 0.5)
        self.assertIn("NO_VERIFIED_SIGNAL", m["flags"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""Offline regressions: evidence freshness, actual history citations, probe limits.

Run: python3 verification/test_evidence_scope.py
No link-only check is treated as official organizer verification.
"""
import copy
import json
from pathlib import Path
import sys
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "verification")]
import model
from lib_common import utc_iso
from update_picks import build_payload
from source_probe import _verdict
from check_source_pages import titles_from


class EvidenceScopeTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 25, 14, tzinfo=timezone.utc)
        self.saved = json.loads((ROOT / "docs/data/picks.json").read_text())

    def payload(self, degraded=False, timestamp="2026-10-20T12:00:00Z", starts=None):
        rows = copy.deepcopy(self.saved["matches"][:3])
        for row, start in zip(rows, starts or [self.now + timedelta(hours=h) for h in (-1, 2, 25)]):
            row["start_utc"] = utc_iso(start)
        fixtures = {"lobby": "https://play.hotspawn.com/lol-pickems", "count": 3,
                    "generated_at": utc_iso(self.now - timedelta(minutes=8))}
        markets = {"statuses": [], "generated_at": utc_iso(self.now - timedelta(minutes=7))}
        lp = {"counts": {"results": 2000, "standings": 2, "standings_pages": 1},
              "standings": [], "degraded": degraded, "generated_at": timestamp,
              "degraded_reason": "using previous snapshot" if degraded else None}
        picks = {"matches": rows, "coverage": self.saved["coverage"], "model": self.saved["model"]}
        with patch("update_picks.now_utc", return_value=self.now):
            return build_payload(fixtures, markets, lp, picks)

    def test_input_timestamp_not_replaced_by_build_time(self):
        out = self.payload(degraded=True)
        community = out["input_freshness"][2]
        self.assertEqual(community["as_of"], "2026-10-20T12:00:00Z")
        self.assertNotEqual(community["as_of"], out["generated_at"])
        self.assertEqual(community["status"], "degraded")
        statuses = {s["name"]: s for s in out["sources_status"]}
        self.assertEqual(statuses["Leaguepedia Standings"]["status"], "degraded")
        self.assertEqual(statuses["Leaguepedia MatchSchedule"]["status"], "degraded")

    def test_missing_timestamp_stays_blank(self):
        self.assertIsNone(self.payload(timestamp=None)["input_freshness"][2]["as_of"])

    def test_next24_excludes_past_and_beyond_window(self):
        out = self.payload()
        self.assertEqual(out["counts"]["next_24h"], 1)

    def test_next24_includes_exact_upper_bound(self):
        out = self.payload(starts=[self.now, self.now + timedelta(hours=24), self.now + timedelta(hours=24, seconds=1)])
        self.assertEqual(out["counts"]["next_24h"], 2)

    def test_all_cited_history_pages_checked_once_per_row(self):
        out = {"matches": [{"leaguepedia_url": "https://lol.fandom.com/wiki/New_Split",
                            "sources": [{"url": u} for u in [
                                "https://lol.fandom.com/wiki/New_Split",
                                "https://lol.fandom.com/wiki/Old_Split#Results",
                                "https://lol.fandom.com/wiki/Old%20Split",
                                "https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule",
                                "https://www.hotspawn.com/matches/x"]]}]}
        self.assertEqual(titles_from(out), {"New Split": 1, "Old Split": 1})

    def test_http_status_is_not_evidence_of_coverage_or_paid_plan(self):
        self.assertIn("unverified", _verdict(401, False, None, "sportsbook-api"))
        self.assertIn("unverified", _verdict(429, False, None, "sportsbook-api"))
        self.assertIn("unverified", _verdict(200, True, 0, "sportsbook-api"))
        self.assertNotIn("without any League of Legends match market", _verdict(200, True, 0, "sportsbook-api"))

    def test_model_cites_historical_competition_not_only_future_split(self):
        old = "Evidence Test/2025 Season/Split"
        new = "Evidence Test/2026 Season/Split"
        def row(t1, t2, days, page, winner):
            return {"team1": t1, "team2": t2, "score1": 2 if winner == 1 else 0,
                    "score2": 0 if winner == 1 else 2, "winner": winner,
                    "start_utc": utc_iso(self.now + timedelta(days=days)), "overview": page,
                    "best_of": 3, "tab": ""}
        results = [row("Evidence Alpha", "Evidence Beta", -20 + i, old, 1) for i in range(10)]
        schedule = [row("Evidence Alpha", "Evidence Beta", 2, new, None)]
        fixture = {"id": "evidence-test", "team1": "Evidence Alpha", "team2": "Evidence Beta",
                   "tournament": "Evidence Test", "start_utc": schedule[0]["start_utc"], "best_of": 3,
                   "hotspawn_url": "https://www.hotspawn.com/matches/evidence-test"}
        lp = {"results": results, "schedule": schedule, "standings": [], "teams": []}
        with patch("model.now_utc", return_value=self.now):
            out = model.build_matches({"fixtures": [fixture]}, lp, {"records": []}, model.DEFAULT_ALIASES)["matches"][0]
        links = {s["url"] for s in out["sources"]}
        self.assertIn("https://lol.fandom.com/wiki/Evidence_Test/2025_Season/Split", links)
        self.assertIn("https://lol.fandom.com/wiki/Evidence_Test/2026_Season/Split", links)
        self.assertNotEqual(out["method"], "UNRESOLVED")


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""
test_verifier.py — self-tests for scripts/verify_site.py.

Each test builds a synthetic payload that violates exactly one rule and asserts
that the corresponding check FAILs (so a green verification run cannot be a
false negative). Run: python3 verification/test_verifier.py
"""
from __future__ import annotations

import copy
import importlib.util
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("verify_site",
                                              os.path.join(ROOT, "scripts", "verify_site.py"))
vs = importlib.util.module_from_spec(spec)
sys.modules["verify_site"] = vs
spec.loader.exec_module(vs)

NOW = datetime.now(timezone.utc).isoformat()

BASE_ROW = {
    "team1": "Team A", "team2": "Team B",
    "tournament": "Test League", "tier": "C", "points": "10",
    "start_raw": "Oct 22, 12:00", "start_utc": "2026-10-22T12:00:00+00:00",
    "hotspawn_url": "https://www.hotspawn.com/matches/team-a-vs-team-b-test-1",
    "source_lobby": "https://play.hotspawn.com/lol-pickems",
    "market_url": "https://polymarket.com/event/test",
    "prob_team1": 0.6, "prob_team2": 0.4, "pick": "Team A", "pick_prob": 0.6,
    "method": "MARKET_POLYMARKET",
    "evidence": "Polymarket: Team A vs Team B (BO1) - Test",
    "confidence": "High",
}


def payload(rows, **kw):
    p = {"generated_at": NOW, "count": len(rows),
         "counts_by_method": {m: sum(1 for r in rows if r.get("method") == m)
                              for m in vs.METHODS},
         "matches": rows}
    p.update(kw)
    return p


def run(rows, **kw):
    rep = vs.Report()
    vs.verify_data(rep, payload(rows, **kw), "test.json", 8.0)
    return {c["id"]: c for c in rep.checks}


def assert_status(checks, cid, want, label):
    got = checks.get(cid, {}).get("status")
    ok = got == want
    print(f"  [{'ok' if ok else 'FAILED'}] {label}: {cid} = {got} (want {want})")
    return ok


def main() -> int:
    results = []

    # baseline: a clean row must pass every data check
    c = run([copy.deepcopy(BASE_ROW)])
    results += [assert_status(c, i, vs.PASS, "clean row passes")
                for i in ("D2", "D3", "D4", "D5", "D6", "D7", "D8a", "D8c", "D8d", "D9", "D12", "D20")]

    # pick not one of the teams
    r = copy.deepcopy(BASE_ROW); r["pick"] = "Team C"
    results.append(assert_status(run([r]), "D3", vs.FAIL, "bad pick"))
    # probabilities off by 10 points
    r = copy.deepcopy(BASE_ROW); r["prob_team1"], r["prob_team2"] = 0.6, 0.5
    results.append(assert_status(run([r]), "D4", vs.FAIL, "probs do not sum to 1"))
    # pick_prob inconsistent
    r = copy.deepcopy(BASE_ROW); r["pick_prob"] = 0.9
    results.append(assert_status(run([r]), "D5", vs.FAIL, "pick_prob wrong"))
    # unknown method
    r = copy.deepcopy(BASE_ROW); r["method"] = "GUT_FEEL"
    results.append(assert_status(run([r]), "D6", vs.FAIL, "undocumented method"))
    # no source link anywhere
    r = copy.deepcopy(BASE_ROW)
    for k in ("market_url", "source_url", "hotspawn_url", "source_lobby"):
        r.pop(k, None)
    r["evidence"] = "trust me"
    results.append(assert_status(run([r]), "D7", vs.FAIL, "no source link"))
    # market row with no market URL
    r = copy.deepcopy(BASE_ROW); r["market_url"] = ""
    r["source_url"] = "https://lol.fandom.com/wiki/Test"
    results.append(assert_status(run([r]), "D8a", vs.FAIL, "market row without market url"))
    # model row missing a recorded-results source URL
    r = copy.deepcopy(BASE_ROW); r["method"] = "MODEL_ELO"; r.pop("market_url", None)
    r["sources"] = [{"name": "Hotspawn fixture", "url": r["hotspawn_url"]}]
    results.append(assert_status(run([r]), "D8c", vs.FAIL, "model row without results source"))
    # generic results table without the explicit provenance warning
    r = copy.deepcopy(BASE_ROW); r["method"] = "MODEL_ELO"; r.pop("market_url", None)
    r["source_url"] = "https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule"
    results.append(assert_status(run([r]), "D8d", vs.FAIL, "generic model source without flag"))
    r["flags"] = ["GENERIC_RESULTS_SOURCE"]
    results.append(assert_status(run([r]), "D8d", vs.PASS, "generic model source correctly flagged"))
    # unresolved row that is not 50/50
    r = copy.deepcopy(BASE_ROW); r["method"] = "UNRESOLVED"; r["prob_team1"] = 0.7
    r["prob_team2"] = 0.3; r["pick"] = "Team A"; r["pick_prob"] = 0.7
    r["evidence"] = "no data"; r["confidence"] = "Unresolved"
    results.append(assert_status(run([r]), "D8b", vs.FAIL, "unresolved not 50/50"))
    # hotspawn cited as the probability source
    r = copy.deepcopy(BASE_ROW)
    r["market_url"] = "https://www.hotspawn.com/lol-pickems"
    results.append(assert_status(run([r]), "D12", vs.FAIL, "hotspawn as prob source"))
    # duplicate fixture
    rows = [copy.deepcopy(BASE_ROW), copy.deepcopy(BASE_ROW)]
    results.append(assert_status(run(rows), "D9", vs.FAIL, "duplicate fixture"))
    # counts_by_method lies
    r = copy.deepcopy(BASE_ROW)
    p = payload([r]); p["counts_by_method"]["UNRESOLVED"] = 5
    rep = vs.Report(); vs.verify_data(rep, p, "t.json", 8.0)
    results.append(assert_status({x["id"]: x for x in rep.checks}, "D10", vs.FAIL,
                                 "counts_by_method mismatch"))
    # Game-1 market used as a series price
    r = copy.deepcopy(BASE_ROW)
    r["evidence"] = "Polymarket: LoL: Team A vs Team B - Game 1 Winner"
    results.append(assert_status(run([r]), "D16", vs.FAIL, "game-1 as series"))
    # BO1 game-1 style evidence is fine when marked BO1
    r = copy.deepcopy(BASE_ROW)
    r["evidence"] = "Polymarket: Team A vs Team B (BO1) - Worlds Group Stage"
    results.append(assert_status(run([r]), "D16", vs.PASS, "BO1 market ok"))
    # duplicate bookmaker board rows inside market.sources must fail D20
    r = copy.deepcopy(BASE_ROW)
    r["method"] = "MARKET_CONSENSUS"
    r["market"] = {
        "source_count": 2,
        "sources": [
            {"source": "Pinnacle", "source_key": "pinnacle", "prob_team1": 0.6,
             "url": "https://www.pinnacle.com/en/esports/league-of-legends"},
            {"source": "Pinnacle", "source_key": "pinnacle", "prob_team1": 0.6,
             "url": "https://www.pinnacle.com/en/esports/league-of-legends"},
        ],
    }
    results.append(assert_status(run([r]), "D20", vs.FAIL, "duplicate bookmaker in market.sources"))
    # prop market board leaked into market.sources must fail D20
    r = copy.deepcopy(BASE_ROW)
    r["method"] = "MARKET_SINGLE"
    r["market"] = {
        "source_count": 1,
        "sources": [
            {"source": "Pinnacle", "source_key": "pinnacle", "prob_team1": 0.782,
             "market": "First Baron", "url": "https://www.pinnacle.com/en/esports/league-of-legends"},
        ],
    }
    results.append(assert_status(run([r]), "D20", vs.FAIL, "prop market leaked into market.sources"))
    # external-source probe row without an https link / carrying a probability must fail D22
    good_probe = {"checked_at": NOW, "summary": {"checked": 1},
                  "books": [{"name": "Example book", "url": "https://example.com/lol",
                             "http_status": 403, "verdict": "blocked"}]}
    results.append(assert_status(run([copy.deepcopy(BASE_ROW)], market_probe=good_probe),
                                 "D22", vs.PASS, "clean probe row"))
    bad = copy.deepcopy(good_probe); bad["books"][0]["url"] = "http://example.com/lol"
    results.append(assert_status(run([copy.deepcopy(BASE_ROW)], market_probe=bad),
                                 "D22", vs.FAIL, "probe row without https"))
    bad2 = copy.deepcopy(good_probe); bad2["books"][0]["prob_team1"] = 0.61
    results.append(assert_status(run([copy.deepcopy(BASE_ROW)], market_probe=bad2),
                                 "D22", vs.FAIL, "probe row carrying a probability"))
    # D23: wired production feeds must be counted consistently with the summary
    wired_probe = {
        "checked_at": NOW,
        "summary": {"checked": 2, "wired_feeds_checked": 2, "wired_feeds_reachable": 1},
        "books": [
            {"name": "Pinnacle (wired feed)", "url": "https://guest.api.arcadia.pinnacle.com/0.1/sports/12/matchups",
             "category": "wired", "wired": True, "http_status": 200, "reachable": True, "verdict": "reachable"},
            {"name": "Unibet (wired feed)", "url": "https://eu-offering-api.kambicdn.com/x.json",
             "category": "wired", "wired": True, "http_status": 503, "reachable": False, "verdict": "not reachable"},
        ],
    }
    results.append(assert_status(run([copy.deepcopy(BASE_ROW)], market_probe=copy.deepcopy(wired_probe)),
                                 "D23", vs.PASS, "wired feeds counted consistently"))
    lied = copy.deepcopy(wired_probe); lied["summary"]["wired_feeds_reachable"] = 2
    results.append(assert_status(run([copy.deepcopy(BASE_ROW)], market_probe=lied),
                                 "D23", vs.FAIL, "summary claims a dead feed is reachable"))
    # stale data
    old = "2020-01-01T00:00:00+00:00"
    rep = vs.Report(); vs.verify_data(rep, payload([copy.deepcopy(BASE_ROW)],
                                                   generated_at=old), "t.json", 8.0)
    results.append(assert_status({x["id"]: x for x in rep.checks}, "D1", vs.FAIL,
                                 "stale generated_at"))

    # cron parser
    for expr, want in [("0 */6 * * *", 6.0), ("0 */4 * * *", 4.0),
                       ("0 */12 * * *", 12.0), ("30 2 * * *", None),
                       ("0 0,6,12,18 * * *", 6.0)]:
        got = vs.cron_interval_hours(expr)
        ok = got == want
        print(f"  [{'ok' if ok else 'FAILED'}] cron {expr!r} -> {got} (want {want})")
        results.append(ok)

    print(f"\n{sum(results)}/{len(results)} verifier self-tests passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

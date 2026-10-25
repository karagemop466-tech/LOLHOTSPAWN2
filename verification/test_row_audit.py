#!/usr/bin/env python3
"""Negative self-tests for scripts/audit_rows.py.

Every rule in the row auditor must actually fail on a payload that breaks it,
otherwise a green audit is meaningless. Each case below mutates ONE thing in a
copy of the committed payload and asserts the check that is supposed to catch it
reports FAIL (or WARN where the rule is advisory). Run: python3
verification/test_row_audit.py
"""
from __future__ import annotations

import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import audit_rows  # noqa: E402

PAYLOAD = os.path.join(ROOT, "docs", "data", "picks.json")
FAILURES: list[str] = []
RUN = 0


def status(rep, cid):
    for r in rep.rows:
        if r["id"] == cid:
            return r["status"]
    return "MISSING"


def case(name, cid, mutate, want="FAIL"):
    """Mutate a copy of the payload and assert check `cid` reports `want`."""
    global RUN
    RUN += 1
    with open(PAYLOAD, encoding="utf-8") as fh:
        data = json.load(fh)
    before = status(audit_rows.audit(copy.deepcopy(data)), cid)
    mutate(data)
    after = status(audit_rows.audit(data), cid)
    ok = before == "PASS" and after == want
    if not ok:
        FAILURES.append(f"{cid} ({name}): clean payload={before}, mutated={after}, expected {want}")
    print(f"{'ok  ' if ok else 'FAIL'} {cid:5s} {name} (clean={before} mutated={after})")


def first_market(d):
    return next(m for m in d["matches"] if m.get("market"))


def first_model(d):
    return next(m for m in d["matches"] if not m.get("market"))


# ----------------------------------------------------------------- mutations
def m_dup_id(d):
    d["matches"][1]["id"] = d["matches"][0]["id"]


def m_same_team(d):
    d["matches"][0]["team2"] = d["matches"][0]["team1"]


def m_bad_start(d):
    d["matches"][0]["start_utc"] = "25/10/2026 16:00"


def m_old_fixture(d):
    d["matches"][0]["start_utc"] = "2020-01-01T00:00:00Z"


def m_probs_not_100(d):
    d["matches"][0]["prob_team2"] = 0.30


def m_pick_is_loser(d):
    row = d["matches"][0]
    row["pick"] = row["team2"] if row["prob_team1"] > row["prob_team2"] else row["team1"]


def m_pick_prob_mismatch(d):
    row = d["matches"][0]
    row["pick_prob"] = round(min(row["prob_team1"], row["prob_team2"]), 4)


def m_method_without_market(d):
    row = first_model(d)
    row["method"] = "MARKET_CONSENSUS"


def m_market_with_model_method(d):
    row = first_market(d)
    row["method"] = "MODEL_ELO"


def m_duplicate_book(d):
    row = first_market(d)
    row["market"]["sources"].append(dict(row["market"]["sources"][0]))
    row["market"]["source_count"] = len(row["market"]["sources"])


def m_unresolved_not_5050(d):
    row = first_model(d)
    row["method"] = "UNRESOLVED"
    row["prob_team1"], row["prob_team2"] = 0.62, 0.38
    row["resolved"] = True


def m_standings_without_flag(d):
    row = next((m for m in d["matches"] if m.get("method") == "MODEL_ELO_STANDINGS"), None)
    if row is None:
        row = first_model(d)
        row["method"] = "MODEL_ELO_STANDINGS"
    row["flags"] = [f for f in (row.get("flags") or []) if f != "STANDINGS_BLEND_APPLIED"]


def m_devig_wrong(d):
    src = next(s for s in first_market(d)["market"]["sources"] if s.get("decimal_team1"))
    src["decimal_team1"] = round(src["decimal_team1"] * 1.35, 4)


def m_consensus_wrong(d):
    row = first_market(d)
    row["market"]["consensus_team1"] = round(row["market"]["consensus_team1"] * 0.6, 4)
    row["prob_team1"] = row["market"]["consensus_team1"]
    row["prob_team2"] = round(1 - row["prob_team1"], 4)


def m_dispersion_wrong(d):
    first_market(d)["market"]["dispersion"] = 0.4242


def m_crowd_is_probability(d):
    for m in d["matches"]:
        if m.get("market") or not (m.get("crowd") or {}).get("team1_pct"):
            continue
        m["prob_team1"] = m["crowd"]["team1_pct"] / 100.0
        m["prob_team2"] = round(1 - m["prob_team1"], 4)


def m_crowd_note_removed(d):
    for m in d["matches"]:
        if m.get("crowd"):
            m["crowd"].pop("note", None)


def m_no_sources(d):
    d["matches"][0]["sources"] = []


def m_only_hotspawn(d):
    d["matches"][0]["sources"] = [s for s in d["matches"][0]["sources"]
                                  if "hotspawn" in (s.get("url") or "")]


def m_unapproved_host(d):
    d["matches"][0]["sources"].append({"name": "Random blog", "url": "https://example.invalid/x",
                                       "claim": "someone said so"})


def m_hotspawn_claim(d):
    row = d["matches"][0]
    for s in row["sources"]:
        if "hotspawn" in (s.get("url") or ""):
            s["claim"] = "Probability taken from the Hotspawn crowd percentage."


def m_counts_wrong(d):
    d["counts"]["fixtures"] = len(d["matches"]) + 7
    d["counts"]["market"] = 0


def m_method_tally_wrong(d):
    d["coverage"]["counts_by_method"] = {"MODEL_ELO": 1}


def m_coverage_wrong(d):
    d["coverage"]["resolved_pct"] = 42.0
    d["coverage"]["with_external_market"] = 0


def m_league_wrong(d):
    d["league_breakdown"][0]["fixtures"] = 999


def m_league_missing(d):
    d["league_breakdown"] = d["league_breakdown"][1:]


def m_excluded_also_priced(d):
    if d.get("excluded_fixtures"):
        d["excluded_fixtures"][0]["id"] = d["matches"][0]["id"]


def m_duplicate_listing(d):
    dup = copy.deepcopy(d["matches"][0])
    d["matches"].append(dup)
    d["matches"][-1]["id"] = str(int(dup["id"]) + 900000)
    d["counts"]["fixtures"] = len(d["matches"])
    d["coverage"]["fixtures"] = len(d["matches"])
    d["coverage"]["counts_by_method"][dup["method"]] = \
        d["coverage"]["counts_by_method"].get(dup["method"], 0) + 1
    for b in d["league_breakdown"]:
        if b["tournament"] == dup["tournament"]:
            b["fixtures"] += 1


def m_spread_wrong(d):
    first_market(d)["market"]["time_spread_hours"] = 9.9


def m_delta_wrong(d):
    src = next(s for s in first_market(d)["market"]["sources"] if s.get("start_utc"))
    src["start_utc"] = "2026-11-02T05:00:00Z"


def m_featured_bogus(d):
    d["featured"] = ["999999999"] + list(d.get("featured") or [])


def m_next24_outside_window(d):
    late = max(d["matches"], key=lambda m: m.get("start_utc") or "")
    d["next_24h"] = [{"id": late["id"]}]


CASES = [
    ("duplicate fixture id", "R1", m_dup_id),
    ("both sides are the same team", "R1", m_same_team),
    ("unparseable start time", "R1", m_bad_start),
    ("fixture already played at generation time", "R1b", m_old_fixture, "WARN"),
    ("probabilities do not sum to 100%", "R2", m_probs_not_100),
    ("pick is the lower probability", "R2", m_pick_is_loser),
    ("pick_prob is not the favourite's probability", "R2", m_pick_prob_mismatch),
    ("MARKET_* label with no market block", "R3", m_method_without_market),
    ("MODEL_* label while a market block exists", "R3", m_market_with_model_method),
    ("the same book counted twice on one fixture", "R3", m_duplicate_book),
    ("UNRESOLVED row that is not an exact 50/50", "R3", m_unresolved_not_5050),
    ("standings blend without its flag", "R3", m_standings_without_flag),
    ("a cited decimal price that does not de-vig to the published probability", "R4", m_devig_wrong),
    ("consensus that does not recompute from its own sources", "R5", m_consensus_wrong),
    ("dispersion that does not recompute", "R6", m_dispersion_wrong),
    ("probabilities copied from the Hotspawn crowd percentage", "R7", m_crowd_is_probability),
    ("crowd percentage published without its context-only note", "R7b", m_crowd_note_removed),
    ("row with no source link", "R8", m_no_sources),
    ("row whose only source is Hotspawn", "R8", m_only_hotspawn),
    ("citation to a host outside the approved provenance list", "R8b", m_unapproved_host, "WARN"),
    ("Hotspawn cited as the probability source", "R8c", m_hotspawn_claim),
    ("counts block that does not re-foot", "R9", m_counts_wrong),
    ("method tally that does not re-foot", "R9", m_method_tally_wrong),
    ("coverage block that does not re-foot", "R9b", m_coverage_wrong),
    ("per-league row that does not re-foot", "R10", m_league_wrong),
    ("a league present in the rows but missing from the breakdown", "R10", m_league_missing),
    ("a cancelled fixture that is still priced", "R12", m_excluded_also_priced),
    ("the same pair+tournament+day listed twice", "R13", m_duplicate_listing, "WARN"),
    ("time spread that does not follow from the cited start times", "R15", m_spread_wrong),
    ("a book start time whose published delta is wrong", "R16", m_delta_wrong),
    ("featured list pointing at a row that does not exist", "R14", m_featured_bogus),
    ("next-24h list pointing outside the 24h window", "R14", m_next24_outside_window),
]


def main() -> int:
    with open(PAYLOAD, encoding="utf-8") as fh:
        data = json.load(fh)
    rep = audit_rows.audit(data)
    clean_fail = rep.fails
    print(f"clean payload: {len(rep.rows)} checks, {len(clean_fail)} FAIL")
    if clean_fail:
        FAILURES.append(f"committed payload fails: {[r['id'] for r in clean_fail]}")
    for args in CASES:
        case(*args)
    print()
    if FAILURES:
        print(f"{len(FAILURES)} of {RUN} negative self-tests FAILED:")
        for f in FAILURES:
            print("  -", f)
        return 1
    print(f"ALL {RUN} negative self-tests passed (every rule fails on a payload that breaks it).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

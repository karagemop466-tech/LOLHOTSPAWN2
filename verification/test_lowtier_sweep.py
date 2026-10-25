#!/usr/bin/env python3
"""Offline unit tests for scripts/probe_lowtier.py.

The sweep's HTTP statuses can only be measured by a machine with a route to the
candidate hosts (CI), so what is testable offline is everything that decides
whether a measured response *counts*: the price parsers, the rejection of child
prop boards, the fixture matcher, the scope rule (only fixtures without a book
line), the verdict wording and the markdown writer. Each test feeds a synthetic
response shaped like the real feed and asserts the outcome.

Run: python3 verification/test_lowtier_sweep.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import probe_lowtier as pl  # noqa: E402

PAYLOAD = json.load(open(os.path.join(ROOT, "docs", "data", "picks.json"), encoding="utf-8"))
MATCHES = PAYLOAD["matches"]
INDEX = pl.FixtureIndex(MATCHES)
UNPRICED = {str(m["id"]) for m in MATCHES if not m.get("market")}
PRICED = {str(m["id"]) for m in MATCHES if m.get("market")}

FAILED: list[str] = []
RUN = 0


def check(name, got, want):
    global RUN
    RUN += 1
    ok = got == want
    if not ok:
        FAILED.append(f"{name}: got {got!r}, want {want!r}")
    print(f"{'ok  ' if ok else 'FAIL'} {name}")


def check_true(name, cond, detail=""):
    global RUN
    RUN += 1
    if not cond:
        FAILED.append(f"{name}: {detail}")
    print(f"{'ok  ' if cond else 'FAIL'} {name}{'' if cond else ' — ' + detail}")


# ---------------------------------------------------------------- fixtures used
LOW_TIER = next(m for m in MATCHES if str(m["id"]) not in PRICED)          # model-priced row
WORLD = next(m for m in MATCHES if str(m["id"]) in PRICED)                  # book-priced row


def kambi_body(events):
    return json.dumps({"events": events})


def kambi_event(name_a, name_b, start, label="Match Odds", odds=(1850, 1950), extra=()):
    offers = [{"criterion": {"label": label},
               "outcomes": [{"participant": name_a, "odds": odds[0]},
                            {"participant": name_b, "odds": odds[1]}]}]
    offers.extend(extra)
    return {"event": {"id": 424242, "name": f"{name_a} - {name_b}", "start": start,
                      "group": "Prime League 2nd Division"},
            "betOffers": offers}


def bovada_body(market_type="moneyline", american=(120, -140)):
    return json.dumps({"events": [{"id": "32740000", "startTime": LOW_TIER["start_utc"],
                                   "competition": {"name": "PRM 2nd Division"},
                                   "competitors": [{"name": LOW_TIER["team1"]},
                                                   {"name": LOW_TIER["team2"]}],
                                   "markets": [{"marketType": market_type,
                                                "outcomes": [
                                                    {"competitor": LOW_TIER["team1"],
                                                     "price": {"american": american[0]}},
                                                    {"competitor": LOW_TIER["team2"],
                                                     "price": {"american": american[1]}}]}]}]})


def _epoch(iso):
    from datetime import datetime
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())


def linefeed_body():
    return json.dumps({"Value": [{"ChampId": 111, "Id": 222, "Start": _epoch(LOW_TIER["start_utc"]),
                                  "Champs": [{"Name": "PRM 2nd Division"}],
                                  "Odds1": [{"v": [[LOW_TIER["team1"], 1.9],
                                                  [LOW_TIER["team2"], 1.9]]}]}]})


def sofascore_body(with_odds=True):
    ev = {"event": {"slug": "babos-gaming-hannover", "homeTeam": {"name": LOW_TIER["team1"]},
                    "awayTeam": {"name": LOW_TIER["team2"]},
                    "startTimestamp": _epoch(LOW_TIER["start_utc"]),
                    "tournament": {"name": "PRM 2nd Division"}}}
    if with_odds:
        ev["odds"] = {"1": ["1.90", "1.90"]}
    return json.dumps({"events": [ev]})


# ----------------------------------------------------------------------- tests
p, m = pl.extract_and_match("kambi", kambi_body([kambi_event(LOW_TIER["team1"], LOW_TIER["team2"],
                                                             LOW_TIER["start_utc"])]),
                            INDEX, UNPRICED, "https://example.test/board")
check("T1 kambi two-way price is extracted", len(p), 1)
check("T1b kambi decimals are odds/1000", (p[0]["decimal_a"], p[0]["decimal_b"]), (1.85, 1.95))
check("T1c it matches the real unpriced fixture", [x["fixture"] for x in m], [str(LOW_TIER["id"])])
check("T1d the human link is the candidate's own page", m[0]["url"], "https://example.test/board")
check("T1e the per-event reference is kept beside it", m[0]["source_ref"], "kambi-event:424242")

prop = [kambi_event(LOW_TIER["team1"], LOW_TIER["team2"], LOW_TIER["start_utc"], label="Map Handicap"),
        kambi_event(LOW_TIER["team1"], LOW_TIER["team2"], LOW_TIER["start_utc"], label="Total Maps")]
p2, m2 = pl.extract_and_match("kambi", kambi_body(prop), INDEX, UNPRICED)
check("T2 child prop boards are never extracted", (len(p2), len(m2)), (0, 0))

p3, m3 = pl.extract_and_match("bovada-family", bovada_body(), INDEX, UNPRICED)
check("T3 bodog-family moneyline extracted", len(p3), 1)
check_true("T3b american prices converted to decimal",
           p3 and abs(p3[0]["decimal_a"] - 2.20) < 1e-6 and abs(p3[0]["decimal_b"] - 1.714286) < 1e-4,
           str(p3[:1]))
check("T3c it matches the real unpriced fixture", [x["fixture"] for x in m3], [str(LOW_TIER["id"])])

p4, m4 = pl.extract_and_match("bovada-family", bovada_body(market_type="total"), INDEX, UNPRICED)
check("T4 non-moneyline boards are never extracted", (len(p4), len(m4)), (0, 0))

p5, m5 = pl.extract_and_match("linefeed", linefeed_body(), INDEX, UNPRICED)
check("T5 linefeed two-way price extracted and matched", (len(p5), len(m5)), (1, 1))

p6, m6 = pl.extract_and_match("sofascore", sofascore_body(), INDEX, UNPRICED)
check("T6 sofascore odds extracted when present", len(p6), 1)
p6b, _ = pl.extract_and_match("sofascore", json.dumps({"events": [{"event": {}}]}), INDEX, UNPRICED)
check("T6c malformed sofascore rows are skipped, not guessed at", len(p6b), 0)
p7, m7 = pl.extract_and_match("sofascore", sofascore_body(with_odds=False), INDEX, UNPRICED)
check("T6b sofascore events without odds yield nothing", (len(p7), len(m7)), (0, 0))

# scope rule: a price for a fixture that already has a book line must not count
p8, m8 = pl.extract_and_match("kambi", kambi_body([kambi_event(WORLD["team1"], WORLD["team2"],
                                                              WORLD["start_utc"])]),
                              INDEX, UNPRICED)
check_true("T7 a Worlds price is parsed but does NOT count as covering an unpriced fixture",
           len(p8) == 1 and m8 == [], f"prices={len(p8)} matched={m8}")

check_true("T7b the unpriced scope equals the rows without a market block",
           len(UNPRICED) == sum(1 for x in MATCHES if not x.get("market")) and not (UNPRICED & PRICED),
           f"unpriced={len(UNPRICED)} priced={len(PRICED)}")

# verdict wording is what the site publishes, so it is pinned here
verdicts = {
    200: {"prices_found": 1, "matched_fixtures": [{"fixture": "1"}], "team_name_hits": [],
          "league_name_hits": [], "category": "market", "http_status": 200},
    200.5: {"prices_found": 2, "matched_fixtures": [], "team_name_hits": [], "league_name_hits": [],
            "category": "market", "http_status": 200},
    200.75: {"prices_found": 0, "matched_fixtures": [], "team_name_hits": ["Babos Gaming"],
             "league_name_hits": ["primeleague2nddivision"], "category": "market", "http_status": 200},
    200.9: {"prices_found": 0, "matched_fixtures": [], "team_name_hits": [], "league_name_hits": [],
            "category": "results", "http_status": 200},
    403: {"http_status": 403}, 404: {"http_status": 404}, 410: {"http_status": 410},
    203: {"http_status": 203}, 0: {"http_status": 0}, 401: {"http_status": 401},
}
expect = {
    200: "STRUCTURED PRICES MATCHING PUBLISHED FIXTURES",
    200.5: "none of them is one of the fixtures we price",
    200.75: "no machine-readable two-way price",
    200.9: "never a probability input",
    403: "blocked to automated requests",
    404: "no such endpoint",
    410: "no such endpoint",
    203: "geo-restriction",
    0: "not reachable from CI",
    401: "key-gated",
}
for key, row in verdicts.items():
    text = pl._verdict(dict(row))
    check_true(f"T8 verdict for HTTP {row['http_status']} ({key})", expect[key] in text, text)

# the candidate list must be https, unique and non-empty
urls = [c[1] for c in pl.CANDIDATES]
check_true("T9 every candidate URL is https", all(u.startswith("https://") for u in urls), str(urls[:3]))
check("T9b no candidate URL is listed twice", len(urls), len(set(urls)))
check_true("T9c the list is not empty", len(pl.CANDIDATES) >= 10, str(len(pl.CANDIDATES)))
check_true("T9d every candidate names a shape the sweep understands or 'html'",
           all(c[2] in ("html", *pl.PARSERS) for c in pl.CANDIDATES),
           str({c[2] for c in pl.CANDIDATES}))

# name scan: long team names are found, short ones are not scanned at all
body = pl.norm(f"<html><body>{LOW_TIER['team1']} vs {LOW_TIER['team2']} Prime League 2nd Division</body></html>")
teams = sorted({t for mm in MATCHES if str(mm["id"]) in UNPRICED
                for t in (mm["team1"], mm["team2"]) if t and len(pl.norm(t)) >= 6})
hits = pl._team_hits(body, teams)
check_true("T10 a low-tier team name is found in a normalised HTML body",
           LOW_TIER["team1"] in hits, str(hits[:4]))
check_true("T10b the league key is found", "primeleague2nddivision" in pl._league_hits(body),
           str(pl._league_hits(body)))
short = [t for mm in MATCHES for t in (mm["team1"], mm["team2"]) if t and len(pl.norm(t)) < 6]
check_true("T10c 3-4 letter team names are excluded from the scan (false-positive guard)",
           all(t not in teams for t in short), str(short[:5]))

# markdown writer: one row per candidate, plus the matched table when there is one
sample = {"checked_at": "2026-10-25T15:00:00Z", "payload_generated_at": PAYLOAD["generated_at"],
          "summary": {"checked": 2, "reachable": 1, "with_readable_two_way_prices": 1,
                      "sources_matching_an_unpriced_fixture": 1,
                      "unpriced_fixtures_asked_about": len(UNPRICED),
                      "unpriced_team_names_scanned": len(teams), "note": "x"},
          "sources": [
              {"name": "A", "url": "https://a.test/", "shape": "kambi", "category": "market",
               "why": "because", "http_status": 200, "bytes": 10, "is_json": True, "prices_found": 1,
               "matched_fixtures": [{"fixture": "1", "match": "X vs Y", "tournament": "T",
                                     "source_teams": ["X", "Y"], "decimal": [1.9, 1.9],
                                     "start_utc": "2026-10-25T16:00:00Z", "similarity": 1.0,
                                     "url": "https://a.test/", "source_ref": "kambi-event:1"}],
               "team_name_hits": [], "team_name_hits_total": 1, "league_name_hits": ["primeleague"],
               "verdict": "candidate"},
              {"name": "B", "url": "https://b.test/", "shape": "html", "category": "results",
               "why": "because", "http_status": 403, "bytes": 0, "is_json": False, "prices_found": 0,
               "matched_fixtures": [], "team_name_hits": [], "team_name_hits_total": 0,
               "league_name_hits": [], "verdict": "blocked"}]}
with tempfile.TemporaryDirectory() as td:
    md = os.path.join(td, "research", "sweep.md")
    pl.write_markdown(sample, md)
    text = open(md, encoding="utf-8").read()
check_true("T11 markdown has one table row per candidate", text.count("| [A](https://a.test/)") == 1
           and text.count("| [B](https://b.test/)") == 1, text[:200])
check_true("T11b markdown lists a matched fixture with its link", "Fixtures a candidate source actually priced" in text
           and "X vs Y" in text, text[-300:])
check_true("T11c markdown states the no-probability rule",
           "nothing in this table is used in a probability" in text.lower(),
           "the disclaimer line is missing from the generated markdown")

# the probe itself: one candidate, no network needed to prove it cannot raise
idx = pl.FixtureIndex(MATCHES)
ids = set(UNPRICED)
dead = pl.probe_one(("selftest unroutable", "https://probe-lowtier-selftest.invalid/x",
                     "html", "market", "deliberately unroutable"), idx, teams, ids)
check_true("T12 probe_one never raises and reports an unreachable source as such",
           dead["http_status"] in (0, None) and bool(dead["verdict"]),
           f"http={dead['http_status']} verdict={dead['verdict'][:80]!r}")
check_true("T12b an unreachable source yields no prices and no matched fixtures",
           dead["prices_found"] == 0 and dead["matched_fixtures"] == [],
           f"prices={dead['prices_found']} matched={dead['matched_fixtures']}")

out = pl.sweep(PAYLOAD, limit=2)
check_true("T12c sweep() returns one row per candidate, in candidate order",
           [r["name"] for r in out["sources"]] == [c[0] for c in pl.CANDIDATES[:2]],
           str([r["name"] for r in out["sources"]]))
check_true("T12d every sweep row carries an http status, a verdict and the fields the report needs",
           all(r["http_status"] is not None and r["verdict"] and r["url"].startswith("https://")
               and "matched_fixtures" in r and "team_name_hits" in r for r in out["sources"]),
           str([{k: r[k] for k in ("name", "http_status")} for r in out["sources"]]))
check_true("T12e the sweep summary states how many unpriced fixtures it asked about, and that "
           "nothing it reads is a probability",
           out["summary"]["unpriced_fixtures_asked_about"] == len(UNPRICED)
           and out["summary"]["unpriced_team_names_scanned"] == len(teams)
           and "no value read here is used in any probability" in out["summary"]["note"],
           str({k: out["summary"][k] for k in ("unpriced_fixtures_asked_about",
                                               "unpriced_team_names_scanned")}))
check_true("T12f the sweep result carries both timestamps it is compared against",
           bool(out.get("checked_at")) and out.get("payload_generated_at") == PAYLOAD["generated_at"],
           f"{out.get('checked_at')} vs {out.get('payload_generated_at')}")

print()
if FAILED:
    print(f"{len(FAILED)} of {RUN} tests FAILED:")
    for f in FAILED:
        print("  -", f)
    sys.exit(1)
print(f"ALL {RUN} low-tier sweep unit tests passed.")

#!/usr/bin/env python3
"""Offline self-tests for the OddsDigger line-source parser (session arena/419cd73a).

Why this exists
---------------
`scripts/probe_lines.py::probe_oddsdigger` is the first candidate in this project
that was found to publish a two-way winner price for fixtures the four production
feeds (Pinnacle, Unibet/Kambi, Bovada, Polymarket) do not price. The parser runs
in CI against the live page, but CI cannot be the only evidence that the parser is
correct: these tests pin the extraction rules against a synthetic page built from
the rows a human opened and read on 2026-10-25.

    Vitality Rising Bees vs Mental Rush — LGC Rising 2026 Playoffs, Tue 27 Oct 2026
    17:00 UTC, best price per side 7/17 vs 8/5
      https://oddsdigger.com/e-sports/vitality-rising-bees-vs-mental-rush-23670799
    Ground Zero vs Frank Esports — LCP 2027 Promotion, Wed 11 Nov 2026 09:00 UTC,
    best price per side 1/67 vs 22/3
      https://oddsdigger.com/e-sports/ground-zero-vs-frank-esports-23662613

Nothing here writes a probability. The probe stays diagnostic; see
research/betting-sources.md §20 for why this source is not promoted.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

from probe_lines import (  # noqa: E402
    HAND_VERIFIED_VERDICTS,
    FixtureIndex,
    _frac_to_decimal,
    parse_oddsdigger,
    summarise,
)

PASS = FAIL = 0


def check(cond, label):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"PASS  {label}")
    else:
        FAIL += 1
        print(f"FAIL  {label}")


def ev_link(slug, eid, a, b):
    """One OddsDigger event link, repeated the way the board repeats it."""
    href = f"https://oddsdigger.com/e-sports/{slug}-{eid}"
    title = f"{a} vs {b} betting odds"
    return (f'<a href="{href}" title="{title}"><span>{a}</span></a>'
            f'<a href="{href}" title="{title}"><span>{b}</span></a>')


def board():
    """Synthetic upcoming-LoL board carrying the two hand-verified 2026-10-25 rows."""
    return f"""
<html><body>
<h2>Sunday 25 October 2026</h2>
<div class="row"><span>17:00</span>
{ev_link("invictus-gaming-vs-hanwha-life", "23672372", "Hanwha Life", "Invictus Gaming")}
<span class="odd">4/13</span><span class="odd">11/4</span>
<a href="https://oddsdigger.com/e-sports/invictus-gaming-vs-hanwha-life-23672372">All Odds</a></div>
<h2>Tuesday 27 October 2026</h2>
<div class="row"><span>17:00</span>
{ev_link("vitality-rising-bees-vs-mental-rush", "23670799", "Vitality Rising Bees", "Mental Rush")}
<span class="odd">7/17</span><span class="odd">8/5</span>
<a href="https://oddsdigger.com/e-sports/vitality-rising-bees-vs-mental-rush-23670799">All Odds</a></div>
<h2>Wednesday 11 November 2026</h2>
<div class="row"><span>09:00</span>
{ev_link("ground-zero-vs-frank-esports", "23662613", "Ground Zero", "Frank Esports")}
<span class="odd">1/67</span><span class="odd">22/3</span>
<a href="https://oddsdigger.com/e-sports/ground-zero-vs-frank-esports-23662613">All Odds</a></div>
<div class="row"><span>09:00</span>
{ev_link("map-market-control-vs-control", "23600001", "Map Market Control", "Control")}
<span>Map 1 Winner</span><span class="odd">3/20</span><span class="odd">13/4</span></div>
<div class="row"><span>09:00</span>
{ev_link("broken-overround-vs-broken", "23600002", "Broken Overround", "Broken")}
<span class="odd">1/2</span><span class="odd">3/1</span></div>
</body></html>"""


def main() -> int:
    # --- fractional -> decimal ---------------------------------------------
    check(_frac_to_decimal(7, 17) == 1.4118, "7/17 -> 1.4118 decimal")
    check(_frac_to_decimal(8, 5) == 2.6, "8/5 -> 2.6 decimal")
    check(_frac_to_decimal(1, 67) == 1.0149, "1/67 -> 1.0149 decimal (heavy favourite)")
    check(_frac_to_decimal(22, 3) == 8.3333, "22/3 -> 8.3333 decimal")
    check(_frac_to_decimal(5, 0) is None, "zero denominator is rejected, not a crash")

    records, detail = parse_oddsdigger(board())
    by_pair = {(r["team_a"], r["team_b"]): r for r in records}

    check(detail["events"] == 5, f"5 events seen on the board (got {detail['events']})")
    check(len(records) == 3, f"3 valid two-way series records (got {len(records)})")

    # --- the two hand-verified rows ----------------------------------------
    vrb = by_pair.get(("Vitality Rising Bees", "Mental Rush"))
    check(vrb is not None, "Vitality Rising Bees vs Mental Rush parsed")
    if vrb:
        check(vrb["decimal_a"] == 1.4118 and vrb["decimal_b"] == 2.6,
              f"VRB/MR prices 7/17 v 8/5 -> {vrb['decimal_a']} / {vrb['decimal_b']}")
        check(vrb["url"].endswith("/vitality-rising-bees-vs-mental-rush-23670799"),
              "VRB/MR record links its own OddsDigger event page")
        check(vrb["start"] == "2026-10-27T17:00:00Z",
              f"VRB/MR kickoff read from the day heading + time ({vrb['start']})")
        imp = 1 / vrb["decimal_a"] + 1 / vrb["decimal_b"]
        check(abs((1 / vrb["decimal_a"]) / imp - 0.6481) < 0.001,
              "VRB/MR normalises to 64.8% — the figure quoted in research §20")

    gz = by_pair.get(("Ground Zero", "Frank Esports"))
    check(gz is not None, "Ground Zero vs Frank Esports parsed")
    if gz:
        check(gz["decimal_a"] == 1.0149 and gz["decimal_b"] == 8.3333,
              f"GZ/FAK prices 1/67 v 22/3 -> {gz['decimal_a']} / {gz['decimal_b']}")
        check(gz["start"] == "2026-11-11T09:00:00Z",
              f"GZ/FAK kickoff read from the day heading + time ({gz['start']})")
        imp = 1 / gz["decimal_a"] + 1 / gz["decimal_b"]
        check(abs((1 / gz["decimal_a"]) / imp - 0.8914) < 0.001,
              "GZ/FAK normalises to 89.1% — the figure that contradicts our model")

    # --- the guards ---------------------------------------------------------
    check(("Map Market Control", "Control") not in by_pair,
          "a Map-1 price is never read as a series winner price")
    check(("Broken Overround", "Broken") not in by_pair,
          "a pair with no book overround (1/2 + 3/1 -> implied sum 0.917) is rejected")
    check(("Hanwha Life", "Invictus Gaming") in by_pair,
          "a normal Worlds row on the same board still parses (parser is not over-tuned)")

    # --- fixture matching against the published list -------------------------
    index = FixtureIndex([
        {"id": "A1", "team1": "Mental Rush", "team2": "Vitality Rising Bees",
         "tournament": "LGC Rising 2026 Playoffs", "start_utc": "2026-10-27T17:00:00+00:00"},
        {"id": "A2", "team1": "Ground Zero Gaming", "team2": "Frank Esports",
         "tournament": "LCP 2027 Promotion", "start_utc": "2026-11-11T09:00:00+00:00"},
        {"id": "A3", "team1": "Gen.G", "team2": "LYON",
         "tournament": "Worlds 2026 Main Event", "start_utc": "2026-10-25T22:00:00+00:00",
         "market": {"consensus": 0.775}},
    ])
    res = summarise({"name": "OddsDigger upcoming LoL board", "kind": "aggregator-page",
                     "url": "https://oddsdigger.com/e-sports/league-of-legends/upcoming",
                     "http_status": 200, "records": records, "detail": detail}, index)
    check(res["records_matched_to_fixtures"] == 2,
          f"both hand-verified rows match a published fixture (got "
          f"{res['records_matched_to_fixtures']})")
    check(res["fixtures_matched_and_previously_unpriced"] == 2,
          f"both are fixtures that had no external line (got "
          f"{res['fixtures_matched_and_previously_unpriced']})")
    check(res["verdict"] == HAND_VERIFIED_VERDICTS["OddsDigger upcoming LoL board"],
          "the hand-verified verdict replaces the automatic 'usable' recommendation")
    check("NOT promoted" in res["verdict"], "the verdict states the source is not promoted")

    # --- negative self-tests: the rules must actually fire -------------------
    empty_recs, empty_detail = parse_oddsdigger("")
    check(empty_recs == [] and empty_detail["events"] == 0, "empty body -> no records, no crash")
    no_odds, _ = parse_oddsdigger(
        ev_link("a-vs-b", "23600003", "Alpha", "Beta"))
    check(no_odds == [], "an event with no prices yields no record")
    evens, _ = parse_oddsdigger(
        '<h2>Tuesday 27 October 2026</h2>' + ev_link("c-vs-d", "23600004", "Ce", "Dee")
        + '<span>1/1</span><span>1/1</span>')
    check(evens == [], "a 1/1 v 1/1 pair (implied sum 2.0, not a real board) is rejected")

    # Attribute order is not guaranteed: a title-less board must still yield the pair,
    # taken from the two team-name anchors that share the event id.
    href = "https://oddsdigger.com/e-sports/no-title-vs-row-23600005"
    no_title, _ = parse_oddsdigger(
        '<h2>Tuesday 27 October 2026</h2><div><span>17:00</span>'
        f'<a href="{href}"><img src="a.svg">Alpha Gaming</a>'
        f'<a href="{href}"><img src="b.svg">Beta Squad</a>'
        '<span class="odd">4/6</span><span class="odd">6/5</span>'
        f'<a href="{href}">All Odds</a></div>')
    check(len(no_title) == 1 and no_title[0]["team_a"] == "Alpha Gaming"
          and no_title[0]["team_b"] == "Beta Squad",
          "a board without title attributes still yields the pair from the team anchors")
    check(no_title and no_title[0]["start"] == "2026-10-27T17:00:00Z",
          "kickoff is still read on the title-less layout")
    check(no_title and "All Odds" not in (no_title[0]["team_a"], no_title[0]["team_b"]),
          "the navigation anchor is never mistaken for a team name")

    print(f"\n{PASS} passed / {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())

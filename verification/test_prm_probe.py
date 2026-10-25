#!/usr/bin/env python3
"""Unit tests for the strict price matcher in scripts/probe_prm_lines.py.

The first version of that probe matched single generic words ("Berlin", "cloud",
"atomic") near any number and reported five sources as "odds near a team". Every
one of those hits was a false positive: a German basketball fixture, a CSS
gradient and a meta description. These tests pin down the stricter rule — both
full team names in the same window plus two odds-like decimals — so the probe
cannot silently start reporting fantasy prices again.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from probe_prm_lines import find_prices, fixture_names  # noqa: E402

results: list[tuple[bool, str]] = []


def check(ok: bool, name: str) -> None:
    results.append((bool(ok), name))


PAIRS = [("Babos Gaming", "Hannover Esports e.V."), ("Berlin 5", "Cloud eSport")]

# 1. A real price block: both teams plus two decimals.
real = """
<div class="event"><span>Babos Gaming</span><span class="odds">1.72</span>
<span>Hannover Esports e.V.</span><span class="odds">2.10</span></div>
"""
n, hits = find_prices(real, PAIRS)
check(n == 1 and hits and hits[0]["odds_seen"][:2] == ["1.72", "2.10"],
      "real two-way block is detected with both odds")

# 2. Basketball page: 'Berlin' appears, but never with 'Cloud eSport' and no odds pair.
basketball = """
<div class="event"><span class="teams"><a>Alba Berlin &mdash; Ratiopharm Ulm</a></span></div>
<div class="event"><span class="teams"><a>Fuchse Berlin &mdash; HSG Wetzlar</a></span></div>
"""
n2, _ = find_prices(basketball, PAIRS)
check(n2 == 0, "a basketball page containing 'Berlin' detects nothing")

# 3. CSS gradient containing 'atomic'/'cloud' and numbers, no team pairing.
css = ":root .has-atomic-cream-gradient-background{background:linear-gradient(135deg,#fdd79a,#004a59)}" * 20
n3, _ = find_prices(css, PAIRS)
check(n3 == 0, "a stylesheet with colour numbers detects nothing")

# 4. League name only, no prices.
league_only = "<h3>Prime League 2. Liga 2026 Fall</h3><span>LIVE</span>"
n4, _ = find_prices(league_only, PAIRS)
check(n4 == 0, "a league name without prices detects nothing")

# 5. Both names but only one odd: not a two-way market.
one_odd = "<div>Babos Gaming</div><div>Hannover Esports e.V.</div><div>1.72</div>"
n5, _ = find_prices(one_odd, PAIRS)
check(n5 == 0, "both names with a single odd is rejected")

# 6. Names too far apart (outside the window) are rejected.
far = "<div>Babos Gaming</div>" + ("<p>filler</p>" * 200) + "<div>Hannover Esports e.V.</div><div>1.72</div><div>2.10</div>"
n6, _ = find_prices(far, PAIRS)
check(n6 == 0, "names outside the match window are rejected")

# 7. Dates/ids must not be read as odds.
dated = "<time>2026-10-25T16:00:00Z</time><i>id 1079027</i><b>Babos Gaming Hannover Esports e.V.</b>"
n7, _ = find_prices(dated, PAIRS)
check(n7 == 0, "timestamps and ids are not counted as odds")

# 8. fixture_names only returns rows without an external market.
sample = [{"team1": "A Team", "team2": "B Team", "market": {"x": 1}},
          {"team1": "C Team", "team2": "D Team", "market": None},
          {"team1": "C Team", "team2": "D Team"}]
check(fixture_names(sample) == [("C Team", "D Team")],
      "fixture_names skips priced rows and de-duplicates")

failed = [r for r in results if not r[0]]
for ok, name in results:
    print(f"[{'ok' if ok else 'FAIL'}] {name}")
print(f"\n{len(results) - len(failed)}/{len(results)} price-matcher tests passed")
raise SystemExit(1 if failed else 0)

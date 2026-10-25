## What this changes

**1. Every match has a pick, and the site now says so plainly.**

The payload already priced all 156 upcoming Hotspawn LoL fixtures, but the executive summary's only coverage number
was `Unresolved: 0`, which reads as "no picks". The summary now opens with five separate numbers —
**matches listed · have a pick · from a bookmaker line · model-priced (no book line) · no pick at all** — and,
immediately below them, a **"Picks for the next matches"** panel: the six soonest fixtures as full-width tap cards
with both team names at 19 px, the pick and its probability on their own high-contrast line, method chip, start time
in the reader's local time, and a 44 px minimum tap target into the match detail.

**2. The unresolved section is now literally that: matches that cannot be resolved the way the featured picks are.**

New section on the executive summary, *"Matches with no bookmaker line — and the limits"*, stating **147 model-priced
/ 0 without a pick**, with the per-league limitation table, the sources re-checked this run, and the written
limitations. `unresolved.html` was rebuilt in the same vocabulary and order (mix → no pick at all → low confidence →
by league → sources checked → limitations → what we do instead of guessing). Nav renamed on all seven pages to
"Limits & no-book picks".

**3. Fresh source research, measured rather than asserted** (`research/betting-sources.md` §20).

Following the brief's order — established LoL betting sites → esportsbooks → esports betting lines — this pass opened
the sources that *advertise or list the exact competitions Hotspawn uses*:

| Source | What it actually returned (2026-10-25) |
|---|---|
| Cloudbet — Prime League 2nd Division | page opens, events tab: **"No Prime League 2nd Division events available"** |
| Cloudbet public API | **HTTP 401** (partner key required; none configured and none invented) |
| BMBets PRM 2nd Division | HTTP 200, index lists only Worlds / LCP / Game Changers Rising — no PRM prices |
| Betmonitor PRM 2nd Division | HTTP 200 but serves the generic football/tennis/basketball index |
| esportbet.com | names "Prime League 2. Liga 2026 Fall — LIVE", publishes no prices |
| Tipico (DE) | HTTP 200 with **0** League of Legends references (client-rendered) |
| NEO.bet / bwin / bet365.de | **HTTP 403** |
| Everygame | **HTTP 404** |
| eGamersWorld | **HTTP 403** |
| Oddspedia | **HTTP 410 gone** |
| 1xBet LineFeed | **HTTP 203** geo stub |

New `scripts/probe_prm_lines.py` (+ `prm-line-probe.yml`) asks the reproducible question — *does any source show both
team names of an unpriced fixture in one 700-character window with two odds-like decimals?* — across all 147
model-only fixtures: **16 sources probed, 8 reachable, 5 name one of our competitions, 0 publish a two-way price**
(`data/diag/prm_line_probe.json`). Nine newly measured sources were added to the payload's `checked_unavailable`
(now 35) and seven to the every-6-hours `source_probe.py` (44 candidates), so the site keeps showing what was tried.

**4. Verification**

* `scripts/verify_site.py` **45 PASS · 0 FAIL · 0 WARN** (1 SKIP offline: Leaguepedia snapshot not available locally)
* `verification/test_verifier.py` 45/45 · `test_entity_and_books.py` 17/17 · `test_standings_model.py` ALL PASS ·
  `audit/test_model.py` 23/23 · `test_dom_contract.py` 7/7 · `check_dom_contract.py` PASS · `test_freshness.cjs` PASS
* `verification/check_dom_render.js` **63/63** (five new assertions for the pick panel, the coverage strip and section
  order, plus the coin-flip labelling checks contributed by the session that merged first)
* **new** `verification/check_mobile_css.py` 10/10 — viewport, no non-media width > 390 px, tables scroll and stack,
  ≥ 44 px tap targets, ≥ 11 px text; wired into `pipeline-test.yml` **and** `verify.yml`
* **new** `verification/test_prm_probe.py` 8/8 — a basketball page, a CSS gradient, a league-name-only page, a single
  odd, names outside the window, and timestamps must all yield **no** price
* Row-level audit of all 156 rows: probabilities sum to 1, pick = higher probability, `pick_prob` matches, unique ids,
  ≥ 2 https source links per row, market rows cite a book, model rows cite Leaguepedia → **0 issues**
* `check_source_pages.py` in CI: **12 cited Leaguepedia pages, 12 exist, 0 missing**
* Live Hotspawn lobby cross-check: the fixtures and crowd percentages recorded in the payload match what the lobby
  renders (e.g. Babos Gaming 15 / Hannover 85, AceGaming Hearts 76 / Emperors Bremen 24)
* `verification/spot-checks-2026-10-25.md` records every check with the page that was read

## Sources used (links for manual review)

Hotspawn lobby <https://play.hotspawn.com/lol-pickems> · Hotspawn fixtures API
<https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures> · Leaguepedia Prime League 2nd Division
<https://lol.fandom.com/wiki/Prime_League_2nd_Division/2027_Season/Fall_Split> · Leaguepedia Worlds 2026 Main Event
<https://lol.fandom.com/wiki/2026_Season_World_Championship/Main_Event> · Cloudbet PRM2
<https://www.cloudbet.com/en/esports/league-of-legends/germany-t8205-prime-league-2nd-division> · BMBets PRM2
<https://www.bmbets.com/e-sports/world/lol---prime-league-2nd-division/> · Betmonitor PRM2
<https://www.betmonitor.com/odds-comparison/esports/prime-league-2nd-division/10024464> · esportbet
<https://esportbet.com/league-of-legends/> · Tipico <https://www.tipico.de/en/esports/league-of-legends/>

## Flagged for review (non-blocking, published on the Flagged page)

* **R1** One scheduled refresh failed at 2026-10-25T03:05Z; the next run rebuilt the payload. The exact cause is
  **unconfirmed** — the Actions log API was rate-limited during this session.
* **R2** No reachable book prices the 147 model-only fixtures; those picks are our own line, not a market price.
* **R3** Cloudbet's Prime League 2nd Division coverage claim is **UNVERIFIED** (no live events; API 401).
* **R4** Tipico / NEO.bet / bwin / bet365.de serve a client-rendered shell or 403, so their Prime League coverage is
  **UNVERIFIED**; no price is claimed from them.
* **R5** The first version of the new probe reported five sources as showing odds; all five were false positives
  (basketball fixture, CSS gradient, meta tag). Fixed, and eight regression tests now pin the rule.

## Operational notes

* Refresh cadence unchanged: every 6 hours (`0 */6 * * *`), inside the requested 4–8 hour window; Hotspawn is used for
  the fixture list only and its crowd percentages are never a probability input (enforced by verifier rule W3).
* `COORDINATION.md` carries this session's claim, results and sources; no other session's scope was edited.

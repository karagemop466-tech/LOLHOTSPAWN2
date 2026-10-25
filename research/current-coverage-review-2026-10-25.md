# Current coverage and source review — 2026-10-25

## Scope and latest integrated snapshot

This is an independent audit of the integrated repository state, not a generated-data update. Snapshot read from `docs/data/picks.json` on branch base `028c5a5` (`origin/main`): generated **2026-10-25T14:31:30.074855Z**; next scheduled refresh **2026-10-25T20:31:30.074855Z**.

| Measure | Snapshot value | What it means |
|---|---:|---|
| Upcoming Hotspawn LoL fixtures | 156 | Current lobby fixture set; 9 cancelled fixtures are excluded from pricing |
| Fixtures with a pick and two probabilities | 156 / 156 | Every listed upcoming fixture has a published pick |
| External market rows | 9 (8 consensus, 1 single) | External odds are available for only a small share of the listed fixtures |
| Model rows | 147 (91 `MODEL_ELO`, 54 `MODEL_ELO_STANDINGS`, 2 `MODEL_ELO_THIN`) | Model estimates, not sportsbook lines |
| Unresolved placeholders | 0 | No current fixture is left without a pick; this does not mean every pick is market-priced or official |
| Low-confidence rows | 11 | Payload confidence flag; not a guarantee of accuracy |
| Matches in next 24 hours | 27 | Rendered in the executive summary's starting-soon cards |

Hotspawn provides the fixture list and scheduled lock times only. Its crowd percentages are not probability inputs. Production market adapters and the project's results-based model supply probabilities; model evidence includes Leaguepedia, a community-maintained database, not an official Riot or organizer odds/result feed. Prices and schedules can change between six-hour refreshes.

## Findings against the requested experience

The current integrated site passes the offline requirements checks for complete fixture coverage, two probabilities per row, source links, a separately linked unresolved/limitations area, executive-summary links to picks, responsive/mobile rendering, automatic refresh, and exclusion of Hotspawn crowd percentages. The unresolved count is 0, but the dedicated page still usefully describes model-only coverage, low confidence and other limitations. Treat “156 picks” as full pick coverage, not full bookmaker coverage.

The current page text has one wording inconsistency worth a follow-up: `docs/index.html` and methodology disclose that Leaguepedia is community-maintained and model estimates are not official odds, while `docs/unresolved.html` calls its per-tournament links “verified source link[s].” A link may establish provenance without independently verifying a result or probability. The precise follow-up is to relabel that phrase “evidence source link” (or equivalent) and retain the official-verification caveat. This session did not modify `docs/**`, which is under an active coordination claim.

## Verification evidence and limitations

- Local, offline `python scripts/verify_site.py` on the integrated 14:29Z payload: **47 PASS, 0 FAIL, 0 WARN, 1 SKIP**. D18 was skipped because no fresh Leaguepedia MatchSchedule snapshot was supplied locally. The check passed full 156/156 lobby coverage, source/method shape, probability arithmetic, mobile contracts, summary links, distinct limitations section, 6-hour schedule and no crowd-probability use.
- Current local regression checks: `python verification/test_verifier.py` **55/55**; `python verification/test_dom_contract.py` **7/7**; `python verification/check_dom_contract.py` PASS; `node verification/check_dom_render.js` **67/67** across seven pages; `node verification/render_check.cjs` PASS.
- The latest committed `verification/report.json` on the base is timestamped **2026-10-25T14:27:55Z** and reports **48 PASS, 1 FAIL, 0 WARN, 0 SKIP**. D18 passed on a fresh Leaguepedia snapshot from 14:25:49Z (133/133 comparable times matched, 23 absent, 0 differed; Hotspawn remains authoritative for fixture lock times). X1 failed because 27/35 tested links returned 2xx/3xx, 6 were host-blocked, 0 transient/5xx, and 1 was reported dead (404/410). The exact dead URL is the Polymarket PRM 1st Division page below. This is a published-link irregularity, not evidence that a current Hotspawn fixture price is wrong.
- Local DOM rendering showed 61 near-even “coin-flip” picks under the site's ≤53% favourite rule. These are model/market estimates labelled as toss-ups, not unresolved 50/50 placeholders.
- Static/offline checks validate contracts and rendering, not the truth of every historical result or live odds quote. No value from a diagnostic HTML mention, search snippet, or source probe was copied into the generated probabilities.

## External-source evidence

### Current diagnostic probes (not probability inputs)

The payload's embedded market probe ran at **14:31:30Z**: 43 named candidates checked, 23 reachable, 6 structured JSON responses and 4 with LoL references (38 market candidates; 20 reachable; 3 reachable results/metadata sources). It is an endpoint-level discovery check, not a count of usable fixture prices. The separate fixture-matched line probe in `data/diag/line_probe.json` ran at **14:18:48Z** and checked all 147 fixtures without an external line; no candidate produced new matching coverage. That fixture-matched probe is older than the current payload and is cited only as historical evidence, not as a new 14:31 verification. Only validated production adapters can contribute odds.

Representative observations from the latest payload's probe:

| Candidate | Recorded observation | Handling | Source |
|---|---|---|---|
| OddsPortal LoL | HTTP 200 HTML; no structured per-match prices parsed | Human cross-check only; no probability added | [OddsPortal LoL](https://www.oddsportal.com/lol/) |
| Betmonitor Prime League 2nd Division | HTTP 200 HTML; no structured per-match prices parsed | No price promoted | [Betmonitor PRM 2D](https://www.betmonitor.com/odds-comparison/esports/prime-league-2nd-division/10024464) |
| BMBets Prime League | HTTP 200 HTML; no structured per-match prices parsed | No price promoted | [BMBets Prime League](https://www.bmbets.com/e-sports/world/lol---prime-league/) |
| EsportBet / EsportsBets | EsportBet unreachable in that probe; EsportsBets HTTP 200 HTML but no structured match prices parsed | Discovery only; no price promoted | [EsportBet LoL odds](https://esportbet.com/odds/league-of-legends/) · [EsportsBets LoL](https://www.esportsbets.com/betting/league-of-legends/) |
| eGamersWorld | HTTP 403 to the automated probe | Not readable from that run; not proof that no odds exist | [eGamersWorld LoL odds](https://egamersworld.com/lol/bets) |
| OddsPapi | Probed API path returned HTTP 404; no key configured | No value used; endpoint/key availability unresolved | [OddsPapi LoL coverage](https://oddspapi.io/sports/esports/lol) |
| Kalshi esports series | HTTP 200 response with no LoL references | No LoL market found in that response | [Kalshi esports series API](https://api.elections.kalshi.com/trade-api/v2/series?category=Esports) |
| Manifold search | HTTP 200 with LoL references in a small sample | Candidate only; not integrated | [Manifold search API](https://api.manifold.markets/v0/search-markets?term=league%20of%20legends&limit=5) |
| Riot LoL Esports schedule API | HTTP 403 from the probe runner | This run did not verify the official schedule endpoint | [Riot schedule endpoint](https://esports-api.lolesports.com/persisted/gw/getSchedule?hl=en-US) |

Only **9/156** current fixtures have external market rows. The other 147 picks use the documented results model. No diagnostic discovery result is equivalent to a current, fixture-matched two-way series price.

## Flagged for review / coordination request

1. **Dead published link:** the latest main verification reports `https://polymarket.com/esports/league-of-legends/prime-league-1st-division` as 404. It appears in `docs/flagged.html` and is repeated in the research audit. The link is a source-discovery reference for PRM 1st Division, not a probability input. Request the active site/audit owner to replace it with a valid, direct reference or mark it unavailable, then rerun X1. This branch leaves the claimed page/research scopes untouched.
2. **Terminology:** replace “verified source link” on `docs/unresolved.html` with wording that distinguishes source provenance from official verification; see above. Request the active `docs/**` owner to consider this in their current change.
3. **Coverage:** 147 of 156 picks are estimates without an external market line; 11 are low confidence. Keep the summary's market/model distinction and the visible limitations disclosures.
4. **Unverified endpoints:** the six host-blocked links and the API/page failures are not established as dead or as proof no odds exist. Do not turn HTTP 403/404 from discovery probes into a claim about match prices.
5. **Freshness:** the payload updates every six hours, not continuously; preserve its generated/next-refresh timestamps and avoid calling an older payload “live.”

No probability values, generated artifacts, pages, or source adapters were changed in this audit. See the coordination request and test record appended to `COORDINATION.md`.

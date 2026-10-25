# Source and evidence audit — 2026-10-25 (session c1e74f5e)

## Executive findings

- Live branch pipeline [40201255132](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40201255132) completed successfully. Its saved snapshot was generated **2026-10-25T14:15:45.147298Z**: **156** lobby fixtures, **9** market-derived estimates, **147** model-derived estimates, **0 unresolved**, **11** low-confidence. These are dated counts, not permanent coverage promises.
- A separate live [line-source research run 40201699912](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40201699912) checked **38** source/market variants at **2026-10-25T14:20:34.293372Z** against **147** non-market fixtures. It found **0** candidate adapters with parsed prices matching a previously unpriced fixture.
- That does **not** establish that no bookmaker offers those markets. Blocked pages, client-rendered prices, authentication, incomplete endpoint coverage and fixture/name mismatches limit the search. No unseen price was copied or inferred.
- Production order remains external market → own chronological Elo / same-competition standings → explicit competition prior (Low) → unresolved. Hotspawn supplies the listing only, never probability.
- Every row has a first-party Hotspawn fixture/lobby reference. Model history is from **Leaguepedia, a community database**, not independently verified primary-organizer result records. All official-result confirmation fields are deliberately **null**; the site lists each non-market fixture on **[Flagged for Review](../docs/flagged.html#official-results-audit)**. An organizer homepage or a successful page-existence request is not result-by-result verification.

## Established books → esportsbooks → esports betting lines

The table below transcribes the diagnostic artifact, not a fresh assertion about permanent coverage. “Parsed records” is the probe’s parser output (controls may inspect schedules rather than prices); a zero does not mean the publisher has no odds. Repeated Kambi country markets are **not independent bookmakers**.

| Publisher / endpoint | Type | HTTP | Parsed records | New fixture coverage | Observation |
|---|---|---:|---:|---:|---|
| [Pinnacle (control)](https://www.pinnacle.com/en/esports/league-of-legends) | established-sportsbook | 200 | 0 | 0 | reachable; lists 8 LoL match(es), but none in a competition we cannot already price from a book |
| [Polymarket (control)](https://gamma-api.polymarket.com/events?tag_slug=league-of-legends&active=true&closed=false&limit=200) | prediction-market | 200 | 0 | 0 | reachable; lists 17 LoL match(es), but none in a competition we cannot already price from a book |
| [Kambi / Unibet / GB](https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=GB&useCombined=true) | established-sportsbook | 200 | 8 | 0 | structured prices found but they only duplicate fixtures we already price from a book |
| [Kambi / Unibet / DE](https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=DE&useCombined=true) | established-sportsbook | 200 | 8 | 0 | structured prices found but they only duplicate fixtures we already price from a book |
| [Kambi / Unibet / SE](https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=SE&useCombined=true) | established-sportsbook | 200 | 8 | 0 | structured prices found but they only duplicate fixtures we already price from a book |
| [Kambi / Unibet / IT](https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=IT&useCombined=true) | established-sportsbook | 200 | 8 | 0 | structured prices found but they only duplicate fixtures we already price from a book |
| [Kambi / Unibet / NL](https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=NL&useCombined=true) | established-sportsbook | 200 | 8 | 0 | structured prices found but they only duplicate fixtures we already price from a book |
| [Kambi / Unibet / FR](https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=FR&useCombined=true) | established-sportsbook | 200 | 8 | 0 | structured prices found but they only duplicate fixtures we already price from a book |
| [Kambi / Unibet / PL](https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=PL&useCombined=true) | established-sportsbook | 200 | 8 | 0 | structured prices found but they only duplicate fixtures we already price from a book |
| [Kambi / Unibet / AU](https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=AU&useCombined=true) | established-sportsbook | 200 | 8 | 0 | structured prices found but they only duplicate fixtures we already price from a book |
| [Kambi / Unibet / ZZ](https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=ZZ&useCombined=true) | established-sportsbook | 200 | 8 | 0 | structured prices found but they only duplicate fixtures we already price from a book |
| [SofaScore (esports schedule + odds)](https://www.sofascore.com/esports/league-of-legends) | odds-aggregator | 403 | 0 | 0 | not usable from CI (HTTP 403) |
| [bo3.gg (esports match DB + odds)](https://api.bo3.gg/api/v1/matches) | esports-aggregator | 200 | 0 | 0 | reachable, but no two-way per-match price was extracted (no odds fields in the public match payload) |
| [1xBet-family / 1xbet.com](https://1xbet.com/en/line/) | esportsbook | 203 | 0 | 0 | not usable from CI (HTTP 203) |
| [1xBet-family / betwinner.com](https://betwinner.com/en/line/) | esportsbook | 203 | 0 | 0 | not usable from CI (HTTP 203) |
| [1xBet-family / melbet.com](https://melbet.com/en/line/) | esportsbook | 203 | 0 | 0 | not usable from CI (HTTP 203) |
| [Kambi / Unibet (all esports view)](https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/esports/all/all/matches.json?lang=en_GB&market=GB&useCombined=true) | established-sportsbook | 404 | 0 | 0 | not usable from CI (HTTP 404) |
| [bmbets LoL odds comparison](https://www.bmbets.com/e-sports/world/lol---world-championship/) | aggregator-page | 200 | 0 | 0 | reachable, but no two-way per-match price was extracted |
| [Prime League official (organizer)](https://www.primeleague.gg/en/liga2) | organizer-results | 403 | 0 | 0 | not usable from CI (HTTP 403) |
| [RIVALS LEAGUE official (organizer)](https://www.rivalsleague.gg/) | organizer-results | 200 | 0 | 0 | reachable, but no two-way per-match price was extracted |
| [BetOnline LoL](https://www.betonline.ag/sportsbook/esports/league-of-legends) | established-sportsbook | 200 | 0 | 0 | reachable, but no two-way per-match price was extracted |
| [SportsBetting.ag LoL](https://sportsbetting.ag/sportsbook/esports/league-of-legends) | established-sportsbook | 403 | 0 | 0 | not usable from CI (HTTP 403) |
| [Stake LoL](https://stake.com/sports/esports/league-of-legends) | esportsbook | 403 | 0 | 0 | not usable from CI (HTTP 403) |
| [BC.Game LoL](https://bc.game/sports/esports/league-of-legends) | esportsbook | 200 | 0 | 0 | reachable, but no two-way per-match price was extracted |
| [William Hill esports](https://sports.williamhill.com/betting/en-gb/esports) | established-sportsbook | 403 | 0 | 0 | not usable from CI (HTTP 403) |
| [Parimatch LoL](https://www.parimatch.com/en/esports/league-of-legends) | established-sportsbook | 403 | 0 | 0 | not usable from CI (HTTP 403) |
| [eGamersWorld LoL odds](https://egamersworld.com/lol/bets) | aggregator-page | 403 | 0 | 0 | not usable from CI (HTTP 403) |
| [Oddspedia LoL](https://oddspedia.com/esports/league-of-legends) | aggregator-page | 410 | 0 | 0 | not usable from CI (HTTP 410) |
| [GGScore LoL](https://ggscore.com/en/lol/matches) | aggregator-page | 403 | 0 | 0 | not usable from CI (HTTP 403) |
| [BetExplorer esports](https://www.betexplorer.com/esports/) | aggregator-page | 404 | 0 | 0 | not usable from CI (HTTP 404) |
| [Winamax LoL](https://www.winamax.fr/paris-sportifs/sports/2/57) | established-sportsbook | 403 | 0 | 0 | not usable from CI (HTTP 403) |
| [Marathonbet esports](https://www.marathonbet.com/en/betting/Esports/) | established-sportsbook | 403 | 0 | 0 | not usable from CI (HTTP 403) |
| [Betano esports](https://www.betano.de/esports/) | established-sportsbook | 403 | 0 | 0 | not usable from CI (HTTP 403) |
| [Vave esports](https://vave.com/sports/esports) | esportsbook | 200 | 0 | 0 | reachable, but no two-way per-match price was extracted |
| [Rainbet esports](https://rainbet.com/esports/league-of-legends) | esportsbook | 404 | 0 | 0 | not usable from CI (HTTP 404) |
| [Thunderpick LoL](https://thunderpick.io/esports/league-of-legends) | esportsbook | 403 | 0 | 0 | not usable from CI (HTTP 403) |
| [GG.Bet LoL](https://gg.bet/en/esports/lol) | esportsbook | 403 | 0 | 0 | not usable from CI (HTTP 403) |
| [Rivalry LoL](https://www.rivalry.com/lol) | esportsbook | 503 | 0 | 0 | not usable from CI (HTTP 503) |

## Wider reachability probe

Checked at **2026-10-25T14:15:45.146532Z**; 37 candidates with overlapping publishers above. Only the four production feeds contribute market probabilities. This table verifies HTTP observations, not official match results or usable betting odds.

| Source | HTTP | Structured JSON | Observed verdict |
|---|---:|---|---|
| [Pinnacle (guest JSON)](https://guest.api.arcadia.pinnacle.com/0.1/sports/12/leagues) | 200 | True | reachable JSON with League of Legends references — candidate for an adapter only after a human verifies a sample price; not used in any probability yet |
| [Betfair Exchange](https://www.betfair.com/exchange/plus/) | 403 | False | blocked to automated requests (HTTP 403) — no line can be read |
| [Smarkets API (sports index)](https://api.smarkets.com/v3/sports/) | 404 | False | endpoint not found (HTTP 404) — path may have moved; nothing used |
| [Betway Esports LoL](https://www.betway.com/en/esports/league-of-legends) | 404 | False | endpoint not found (HTTP 404) — path may have moved; nothing used |
| [BetOnline LoL](https://www.betonline.ag/sportsbook/esports/league-of-legends) | 200 | False | reachable HTML only — no structured per-match prices parsed; human cross-check only, never used in a probability |
| [SportsBetting.ag LoL](https://www.sportsbetting.ag/sportsbook/esports/league-of-legends) | 403 | False | blocked to automated requests (HTTP 403) — no line can be read |
| [TonyBet LoL](https://tonybet.com/en/esports/league-of-legends) | 200 | False | reachable HTML only — no structured per-match prices parsed; human cross-check only, never used in a probability |
| [Unibet LoL (HTML shell)](https://www.unibet.com/betting/sports/filter/esports/league_of_legends) | 503 | False | not reachable from CI this run (HTTP 503) — nothing used |
| [GG.Bet LoL](https://gg.bet/en/esports/lol) | 403 | False | blocked to automated requests (HTTP 403) — no line can be read |
| [Thunderpick LoL](https://thunderpick.io/esports/league-of-legends) | 403 | False | blocked to automated requests (HTTP 403) — no line can be read |
| [Rivalry LoL](https://www.rivalry.com/lol) | 503 | False | not reachable from CI this run (HTTP 503) — nothing used |
| [Midnite LoL](https://www.midnite.com/esports/league-of-legends) | 200 | False | reachable HTML only — no structured per-match prices parsed; human cross-check only, never used in a probability |
| [BC.Game LoL](https://bc.game/sports/esports/league-of-legends) | 200 | False | reachable HTML only — no structured per-match prices parsed; human cross-check only, never used in a probability |
| [Stake LoL](https://stake.com/sports/esports/league-of-legends) | 403 | False | blocked to automated requests (HTTP 403) — no line can be read |
| [1xBet line feed (sports index)](https://1xbet.com/LineFeed/GetSportsShortZip?lng=en&country=1) | 203 | False | served an interstitial/redirect page (HTTP 203) instead of the feed — no line can be read |
| [OddsPapi (API — no key configured)](https://api.oddspapi.io/v1/sports) | 404 | False | endpoint not found (HTTP 404) — path may have moved; nothing used |
| [odds-api.io (API — no key configured)](https://api.odds-api.io/v3/sports) | 200 | True | endpoint answers without a key, but the payload carries no League of Legends match market — its data needs a paid API key that is not configured here; nothing used |
| [PandaScore LoL upcoming (API — no token configured)](https://api.pandascore.co/lol/matches/upcoming) | 403 | False | blocked to automated requests (HTTP 403) — no line can be read |
| [OddsPortal LoL](https://www.oddsportal.com/lol/) | 200 | False | reachable HTML only — no structured per-match prices parsed; human cross-check only, never used in a probability |
| [BetExplorer LoL](https://www.betexplorer.com/lol/) | 404 | False | endpoint not found (HTTP 404) — path may have moved; nothing used |
| [eGamersWorld LoL odds](https://egamersworld.com/lol/bets) | 403 | False | blocked to automated requests (HTTP 403) — no line can be read |
| [Betmonitor — Prime League 2nd Division comparison](https://www.betmonitor.com/odds-comparison/esports/prime-league-2nd-division/10024464) | 200 | False | reachable HTML only — no structured per-match prices parsed; human cross-check only, never used in a probability |
| [Betmonitor — esports odds hub](https://www.betmonitor.com/odds-comparison/esports/) | 200 | False | reachable HTML only — no structured per-match prices parsed; human cross-check only, never used in a probability |
| [EsportBet — LoL odds board](https://esportbet.com/odds/league-of-legends/) | 0 | False | not reachable from CI this run (HTTP network error) — nothing used |
| [EsportsBets — LoL betting guide](https://www.esportsbets.com/betting/league-of-legends/) | 200 | False | reachable HTML only — no structured per-match prices parsed; human cross-check only, never used in a probability |
| [Oddspedia — generic LoL odds path (410 as of 2026-10-24)](https://oddspedia.com/league-of-legends/odds) | 410 | False | endpoint not found (HTTP 410) — path may have moved; nothing used |
| [BMBets — LoL Prime League (book-by-book comparison)](https://www.bmbets.com/e-sports/world/lol---prime-league/) | 200 | False | reachable HTML only — no structured per-match prices parsed; human cross-check only, never used in a probability |
| [Strafe — LoL odds (Oddspedia feed)](https://www.strafe.com/esports-betting/odds/league-of-legends/) | 200 | False | reachable HTML only — no structured per-match prices parsed; human cross-check only, never used in a probability |
| [Unibet DE Kambi brand feed (control)](https://eu-offering-api.kambicdn.com/offering/v2018/ubde/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=DE&useCombined=true) | 400 | False | HTTP 400 — nothing used |
| [Unibet Kambi feed with market=DE (coverage control)](https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=DE&useCombined=true) | 200 | True | reachable JSON with League of Legends references — candidate for an adapter only after a human verifies a sample price; not used in any probability yet |
| [Kalshi esports series](https://api.elections.kalshi.com/trade-api/v2/series?category=Esports) | 200 | True | reachable JSON without any League of Legends match market in the response — nothing used |
| [Manifold Markets LoL search](https://api.manifold.markets/v0/search-markets?term=league%20of%20legends&limit=5) | 200 | True | reachable JSON with League of Legends references — candidate for an adapter only after a human verifies a sample price; not used in any probability yet |
| [gol.gg tournament index](https://gol.gg/tournament/list/) | 200 | False | reachable results/metadata page (HTML or API) — not parsed, and never a probability input; Leaguepedia remains the results source and this is a manual cross-check only |
| [bo3.gg LoL matches](https://bo3.gg/lol/matches) | 200 | False | reachable results/metadata page (HTML or API) — not parsed, and never a probability input; Leaguepedia remains the results source and this is a manual cross-check only |
| [Oracle's Elixir downloads (community CSVs)](https://oracleselixir.com/tools/downloads) | 403 | False | blocked to automated requests (HTTP 403) — no line can be read |
| [Riot LoLESports official schedule](https://esports-api.lolesports.com/persisted/gw/getSchedule?hl=en-US) | 403 | False | blocked to automated requests (HTTP 403) — no line can be read |
| [Liquipedia LoL API](https://liquipedia.net/leagueoflegends/api.php?action=query&meta=siteinfo&format=json) | 200 | True | reachable results/metadata page (HTML or API) — not parsed, and never a probability input; Leaguepedia remains the results source and this is a manual cross-check only |

## Row-by-row checks and limitations

- Coverage reconciliation: all 156 upcoming lobby fixtures represented; 9 upstream cancelled/withdrawn fixtures excluded, with source references on Flagged. No completed/cancelled fixture was silently replaced by an invented pick.
- Each row’s two probabilities sum to one; its selected team is the larger probability when a signal exists; each market provider contributes at most once; Hotspawn crowd fields are not model inputs.
- Recomputed all **24 saved decimal-price pairs** as `(1 / odds1) / ((1 / odds1) + (1 / odds2))`; no mismatches at 0.0003 rounding tolerance. Prediction-market decimal fields remain null, not synthesized. All 9 consensus rows are recomputable from their saved source probabilities. This checks arithmetic only, not that a quote remains current.
- Leaguepedia page-existence check: **12 cited competition pages exist**, 0 missing (`data/diag/source_pages.log`). This does not prove every historical game on those pages against organizer records.
- The stored diagnostic schedule export used by D18 is from 2026-10-21; the verifier warns it is stale. Do not interpret that comparison as a current official schedule verification. Current pipeline inputs are fetched separately; Hotspawn’s epoch timestamp remains the listing/lock-time authority.
- No API keys, paid subscriptions, account creation, geoblock bypass or personal betting accounts were used. Authentication and inaccessible endpoints are limitations, not evidence of absent markets.
- Market and model values can change within the six-hour refresh window. The site now preserves the concurrent fail-closed freshness fix: missing/invalid timestamps never receive a green freshness indicator; it says “Recent snapshot · not live odds.”

## Mobile verification

- A real Chromium browser (npm-distributed binary) exercised all **seven pages at 320, 390, 768 and 1280 px**: **78/78 checks passed** after fixing actual 320px overflow from long team/league badges.
- Checked document width, populated picks navigation, search behavior, browser errors, a ≥44px primary picks target above the fold, and the first pick plus both win chances above the fold at phone widths. JSDOM tests additionally cover all pick/source rows, filter deep links, unresolved synthetic rows and the new blank official-confirmation table.
- Optional reproducible browser harness: `verification/check_mobile_browser.cjs`. Browser dependencies/screenshots are not committed; CI uploads a small JSON evidence artifact.

## Evidence files

- [`docs/data/picks.json`](../docs/data/picks.json) — latest published source/probability metadata (may advance after this report).
- [`data/diag/line_probe.json`](../data/diag/line_probe.json) — dated focused research.
- [`data/diag/source_probe.json`](../data/diag/source_probe.json) — dated broad reachability.
- [`data/diag/pipeline.log`](../data/diag/pipeline.log) — fetch, count and model decisions.
- [`data/diag/source_pages.log`](../data/diag/source_pages.log) — page existence only.
- [`scripts/provenance.py`](../scripts/provenance.py) — source authority metadata and arithmetic recomputation.
- [`verification/test_verifier.py`](../verification/test_verifier.py) — 55 positive/negative verifier tests; deliberately malformed source authority, official-confirmation and odds arithmetic must fail.

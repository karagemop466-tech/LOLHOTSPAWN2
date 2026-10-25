# Evidence and missing-line audit — 2026-10-25

## Scope and honest conclusions

The existing collector was retained. Hotspawn is the authoritative **list for the Pick'em game**, not a probability input. Our model probabilities are calculations, never official verified facts. Leaguepedia is community-maintained; no row is newly certified as organizer-verified by this audit. Missing bookmaker prices remain absent (`market: null`), not invented.

## Fresh requests performed in this session

[Line-source probe run 40201225819](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40201225819) **succeeded**. Its artifact is [`data/diag/line_probe.json`](../data/diag/line_probe.json), checked at **2026-10-25T14:14:25Z**, matched against the **156-fixture snapshot collected at 10:41:50Z**. 147 fixtures had no external line in that snapshot. **38 endpoint probes; zero new coverage of those 147 fixtures.** This does not mean that no sportsbook anywhere offers those fixtures.

Research order: established books / production controls → Kambi country markets → esportsbooks and comparison sources → community/result sources. Observed responses, not assumed coverage:

| Group | Observed in this run | Review source |
|---|---|---|
| Production controls | Pinnacle league index and Polymarket were reachable; this diagnostic did not extract two-way prices from those controls. The separate production collector did retrieve 8 Pinnacle and 9 Polymarket records. | [Pinnacle guest index](https://guest.api.arcadia.pinnacle.com/0.1/sports/12/leagues?all=false), [Polymarket Gamma](https://gamma-api.polymarket.com) |
| Unibet/Kambi, nine country queries | Eight two-way prices in each GB/DE/SE/IT/NL/FR/PL/AU/ZZ response; no newly covered model-only fixture. Country responses are not nine independent bookmakers. | [Kambi operator feed, DE](https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=DE&useCombined=true) |
| Esportsbooks | GG.Bet, Thunderpick, Stake, SportsBetting.ag: HTTP 403; Rivalry: HTTP 503. Coverage remains unverified, not absent. | [GG.Bet](https://gg.bet/en/esports/lol), [Thunderpick](https://thunderpick.io/esports/league-of-legends), [Rivalry](https://www.rivalry.com/lol) |
| More line feeds | 1xBet / Betwinner / Melbet returned HTTP 203 interstitials. No price imported, no access restrictions bypassed. | [1xBet feed](https://1xbet.com/LineFeed/Get1x2_VZip?sports=3&count=1000&lng=en&mode=4&country=1&partner=51) |
| HTML comparison and book pages | bmbets, BetOnline, BC.Game and Vave returned HTTP 200 but this diagnostic extracted no validated per-match price. Client-side/blocked prices are not inferred. | [bmbets](https://www.bmbets.com/e-sports/world/lol---world-championship/), [BetOnline](https://www.betonline.ag/sportsbook/esports/league-of-legends) |
| Official organizer reachability | Prime League returned 403, RIVALS returned 200. Reachability does not verify team records, match times or probabilities. | [Prime League](https://www.primeleague.gg/en/liga2), [RIVALS](https://www.rivalsleague.gg/) |
| Community / results | bo3.gg returned 200 with no odds extracted; SofaScore 403. These were not promoted to probability sources. Leaguepedia remains the recorded-results source. | [bo3.gg API](https://api.bo3.gg/api/v1/matches), [Leaguepedia records](https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule) |

The first live pipeline [40201225832](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40201225832) successfully fetched and built **156 rows, 9 market, 147 model, 0 unresolved, 11 Low confidence** at **14:15:22Z**, and passed both DOM render harnesses. Its external-link gate correctly failed because the new static Pinnacle retail URL returned **404**. That new review link was corrected to the actual public Pinnacle guest index observed as 200. A subsequent run must pass before merge; failure is not hidden or reclassified as success.

## Targeted fixes and verification

- Separate source collection timestamps from dashboard build time (`input_freshness`). Cached/degraded community inputs are warned about on **all seven pages**, even when the dashboard itself is fresh. Standings shares the degraded status instead of looking healthy simply because cached rows exist.
- Cite the latest recorded competition used for each team's historical rating in addition to the upcoming split page. The latest competition is not falsely described as all 24 months of input history. Source-page verification now inspects **every cited Leaguepedia page**, not only `leaguepedia_url`.
- “Source link” replaces “verified link.” HTTP 200, a known domain, and an organizer homepage are not proof that each value is officially confirmed.
- Exact 50/50 and unresolved placeholders have **no preferred team** in the UI. The backwards-compatible raw `pick` field is explicitly documented as non-actionable in these cases.
- Matches with past Hotspawn lock times are labelled as such. “Next 24 hours” has both a lower and an upper bound. The next scheduled refresh now identifies the next 00/06/12/18 UTC cron tick (Actions may be delayed).
- Real Chromium testing found horizontal overflow: the Picks and Leagues pages were **430px wide on a 390px viewport**, due to non-wrapping long team names. After wrapping pick/league badges, **28/28 page–viewport checks** passed at **320, 390, 768 and 1280px**, with no page runtime errors or stuck loading indicators. Mobile bottom-nav targets were 60px high. Evidence: [`verification/mobile-browser-2026-10-25.json`](../verification/mobile-browser-2026-10-25.json); reproducible test: `node verification/check_browser.cjs` after installing the packages listed in its header. This is not a screen-reader audit.

## Non-blocking items for review

Published on [Flagged for Review](../docs/flagged.html#evidence-limits): community records lack independent organizer verification; inaccessible books may still carry additional lines; line collection is indicative, not an executable quote; a historical team rating does not verify current rosters; 50/50 rows must never imply an evidence-backed edge. No claim of newly discovered low-tier bookmaker coverage is made.

# Verification report — PASS
_2026-10-24T16:22:00.794510+00:00_
169 matches · MARKET_SINGLE: 1 · MODEL_ELO_THIN: 67 · MODEL_ELO: 93 · MARKET_POLYMARKET: 0 · MARKET_CONSENSUS: 8 · MARKET_BOOKS: 0 · UNRESOLVED: 0 · MODEL_LEAGUE_PRIOR: 0 · MODEL_STANDINGS: 0

| check | status | detail |
|---|---|---|
| D1 payload parses, has matches and a fresh generated_at | PASS | 169 matches, generated_at=2026-10-24T15:28:56.619239Z (0.9h old) |
| D2 two distinct teams and a start time on every match | PASS | all 169 rows have team1, team2 and a start time |
| D3 a pick exists and is one of the two teams | PASS | every match has a pick equal to team1 or team2 |
| D4 probabilities are in range and sum to 1 | PASS | every row sums to 1.0 within 0.005 |
| D5 pick_prob equals the larger probability | PASS | pick_prob matches max(prob_team1, prob_team2) on every row |
| D6 method is one of ['MARKET_BOOKS', 'MARKET_CONSENSUS', 'MARKET_POLYMARKET', 'MARKET_SINGLE', 'MODEL_ELO', 'MODEL_ELO_THIN', 'MODEL_LEAGUE_PRIOR', 'MODEL_STANDINGS', 'UNRESOLVED'] | PASS | all methods documented |
| D6b confidence labels are from the documented set | PASS | High/Medium/Low/None only |
| D7c every source URL is absolute http(s) | PASS | all source URLs well formed |
| D7 every row links at least one source URL | PASS | all 169 rows carry at least one source URL |
| D8a market rows link a bookmaker/prediction-market URL | PASS | every market row links its market |
| D8c model rows link a results-source URL | PASS | every model row links a results source |
| D8d model rows with generic results-table sources are flagged | PASS | generic Leaguepedia table links are explicitly flagged as less directly auditable |
| D8b unresolved rows are explicit unverified 50/50 (limitations published) | PASS | every unresolved row is 0.50 and labelled unverified |
| D9 no duplicate fixtures | PASS | no duplicate (teams,start) rows |
| D16 no single-game (Game 1/Map 1) market used as a series probability | PASS | no non-BO1 row cites a single-game market |
| D12 Hotspawn is never the probability source (fixture list only) | PASS | no market/model row cites hotspawn.com as its probability source |
| D10 declared counts agree with the rows | PASS | counts.resolved/unresolved consistent |
| D11 declared count equals number of rows | PASS | declared=169, rows=169 |
| D20 each external market provider counted at most once per fixture | PASS | every market row has unique provider keys and matching source_count |
| D21 every upcoming Hotspawn lobby fixture is priced; no excluded fixture is priced | PASS | lobby upcoming=169, priced=169, missing=0, extra=0, excluded=14, leaked=0 |
| D13 rows without team evidence are 50/50 and explicitly labelled | PASS | 0 row(s) lack team evidence (UNRESOLVED / NO_TEAM_HISTORY); 0 labelled, 0 non-50/50. Info: 69 model row(s) land within ±2 pts of 50% — these are even-matchup estimates from recorded results, not placeholders. |
| D18 start times cross-checked against Leaguepedia MatchSchedule | SKIP | no --leaguepedia-schedule snapshot supplied |
| D14 single published data file (site copy) | PASS | only docs/data/picks.json exists — site copy is the single source |
| S1 all required site files exist | PASS | 10 files present |
| S10 phone bottom nav has one grid column per link on every page | PASS | 6 links, 6 columns on every page |
| S11 executive summary has a separate unresolved section (fixture list + per-league limits) with the picks listed first and linked in-site | PASS | unresolved section ids present; picks before unresolved section: yes; in-site pick links: yes |
| S12 every CSS class used by a page has a stylesheet rule | PASS | 54 classes used, 0 unstyled |
| S13 jsdom render harness exists and runs in CI | PASS | harness present; wired into pipeline-test.yml, verify.yml |
| S2 every page is mobile-ready (viewport width=device-width) | PASS | all pages declare a responsive viewport |
| S3 every page links the shared picks navigation | PASS | navigation present |
| S4 executive summary links in-site to picks + unresolved and states limitations | PASS | exec summary checks: {'links_picks': True, 'links_unresolved': True, 'mentions_limitations': True, 'mentions_updated': True} |
| S5 separate unresolved section with limitations | PASS | unresolved page states limitations |
| S5c third-party data sources are attributed on Method & Sources | PASS | attribution present |
| S6 no broken internal links | PASS | all internal href/src resolve |
| S7 shared JS/CSS exist and are responsive | PASS | assets load data and contain responsive rules |
| S8 root index.html sends visitors into the site | PASS | root redirects to docs/ |
| S9 all external links use https | PASS | 15 external link(s) collected for manual review; 0 plain-http |
| W1 picks update is scheduled every 4-8 hours | PASS | update-picks.yml: cron '0 */6 * * *' = every 6h |
| W2 update workflow runs the generator with contents: write | PASS | audit-pipeline.yml runs scripts/update_picks.py; contents write present |
| W3 Hotspawn crowd % is never a probability input | PASS | static scan found no crowd->probability usage |
| REQ requirements traceability | PASS | REQ1 PASS; REQ2 PASS; REQ3 PASS; REQ4 PASS; REQ5 PASS; REQ6 PASS; REQ7 PASS; REQ8 PASS; REQ9 PASS; REQ10 PASS; REQ11 PASS; REQ12 PASS |

## Requirements traceability

| id | requirement | status | checks |
|---|---|---|---|
| REQ1 | A pick exists for every match (pick is one of the two teams) | PASS | D3, D11 |
| REQ2 | Win probabilities for both teams on every match, summing to 100% | PASS | D4, D5 |
| REQ3 | Probabilities come from outside Hotspawn (books/markets/our results model) | PASS | D12, W3 |
| REQ4 | External betting lines used where they exist (markets first) | PASS | D8a, D6, D20 |
| REQ5 | Every match without a market line still gets a pick + documented method | PASS | D8b, D13 |
| REQ6 | Separate unresolved section, with limitations, linked from the exec summary | PASS | S4, S5, S5b |
| REQ7 | Executive summary links in-site to the updated picks list | PASS | S4 |
| REQ8 | Every row links its source; non-official or generic evidence is disclosed and flagged | PASS | D7, D7b, D8a, D8b, D8c, D8d, D17 |
| REQ9 | Mobile-friendly: responsive viewport + responsive CSS + readable cards | PASS | S2, S7 |
| REQ10 | Automatic refresh every 4-8 hours, no manual input | PASS | W1, W2, D1 |
| REQ11 | Site integrity: no broken internal links, root entry point works | PASS | S1, S6, S8 |
| REQ12 | Third-party sources attributed where their data is used | PASS | S5c |

**REQ items:**
- REQ1: A pick exists for every match (pick is one of the two teams) -> PASS
- REQ2: Win probabilities for both teams on every match, summing to 100% -> PASS
- REQ3: Probabilities come from outside Hotspawn (books/markets/our results model) -> PASS
- REQ4: External betting lines used where they exist (markets first) -> PASS
- REQ5: Every match without a market line still gets a pick + documented method -> PASS
- REQ6: Separate unresolved section, with limitations, linked from the exec summary -> PASS
- REQ7: Executive summary links in-site to the updated picks list -> PASS
- REQ8: Every row links its source; non-official or generic evidence is disclosed and flagged -> PASS
- REQ9: Mobile-friendly: responsive viewport + responsive CSS + readable cards -> PASS
- REQ10: Automatic refresh every 4-8 hours, no manual input -> PASS
- REQ11: Site integrity: no broken internal links, root entry point works -> PASS
- REQ12: Third-party sources attributed where their data is used -> PASS

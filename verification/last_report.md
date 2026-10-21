# Verification report — PASS
_2026-10-21T21:13:06.097143+00:00_
208 matches · MODEL_ELO: 92 · MARKET_POLYMARKET: 0 · MARKET_CONSENSUS: 9 · MARKET_BOOKS: 0 · MODEL_ELO_THIN: 72 · MODEL_LEAGUE_PRIOR: 35 · MODEL_STANDINGS: 0 · MARKET_SINGLE: 0 · UNRESOLVED: 0

| check | status | detail |
|---|---|---|
| D1 payload parses, has matches and a fresh generated_at | PASS | 208 matches, generated_at=2026-10-21T21:12:59.142737Z (0.0h old) |
| D2 two distinct teams and a start time on every match | PASS | all 208 rows have team1, team2 and a start time |
| D3 a pick exists and is one of the two teams | PASS | every match has a pick equal to team1 or team2 |
| D4 probabilities are in range and sum to 1 | PASS | every row sums to 1.0 within 0.005 |
| D5 pick_prob equals the larger probability | PASS | pick_prob matches max(prob_team1, prob_team2) on every row |
| D6 method is one of ['MARKET_BOOKS', 'MARKET_CONSENSUS', 'MARKET_POLYMARKET', 'MARKET_SINGLE', 'MODEL_ELO', 'MODEL_ELO_THIN', 'MODEL_LEAGUE_PRIOR', 'MODEL_STANDINGS', 'UNRESOLVED'] | PASS | all methods documented |
| D6b confidence labels are from the documented set | PASS | High/Medium/Low/None only |
| D7c every source URL is absolute http(s) | PASS | all source URLs well formed |
| D7 every row links at least one official/trusted source | PASS | all 208 rows carry at least one source URL |
| D8a market rows link a bookmaker/prediction-market URL | PASS | every market row links its market |
| D8b unresolved rows are explicit unverified 50/50 (limitations published) | PASS | every unresolved row is 0.50 and labelled unverified |
| D9 no duplicate fixtures | PASS | no duplicate (teams,start) rows |
| D16 no single-game (Game 1/Map 1) market used as a series probability | PASS | no non-BO1 row cites a single-game market |
| D12 Hotspawn is never the probability source (fixture list only) | PASS | no market/model row cites hotspawn.com as its probability source |
| D10 declared counts agree with the rows | PASS | counts.resolved/unresolved consistent |
| D11 declared count equals number of rows | PASS | declared=208, rows=208 |
| D13 rows without team evidence are 50/50 and explicitly labelled | PASS | 0 row(s) lack team evidence (UNRESOLVED / NO_TEAM_HISTORY); 0 labelled, 0 non-50/50. Info: 77 model row(s) land within ±2 pts of 50% — these are even-matchup estimates from recorded results, not placeholders. |
| D18 start times cross-checked against Leaguepedia MatchSchedule | WARN | 149/153 matched fixture times agree with Leaguepedia; 55 fixture(s) not in the snapshot; 4 differ (Hotspawn is authoritative for pick lock times; differences are flagged for review) |
| D14 single published data file (site copy) | PASS | only docs/data/picks.json exists — site copy is the single source |
| S1 all required site files exist | PASS | 9 files present |
| S2 every page is mobile-ready (viewport width=device-width) | PASS | all pages declare a responsive viewport |
| S3 every page links the shared picks navigation | PASS | navigation present |
| S4 executive summary links in-site to picks + unresolved and states limitations | PASS | exec summary checks: {'links_picks': True, 'links_unresolved': True, 'mentions_limitations': True, 'mentions_updated': True} |
| S5 separate unresolved section with limitations | PASS | unresolved page states limitations |
| S5c third-party data sources are attributed on Method & Sources | PASS | attribution present |
| S6 no broken internal links | PASS | all internal href/src resolve |
| S7 shared JS/CSS exist and are responsive | PASS | assets load data and contain responsive rules |
| S8 root index.html sends visitors into the site | PASS | root redirects to docs/ |
| S9 all external links use https | PASS | 1 external link(s) collected for manual review; 0 plain-http |
| W1 picks update is scheduled every 4-8 hours | PASS | update-picks.yml: cron '0 */6 * * *' = every 6h |
| W2 update workflow runs the generator with contents: write | PASS | update-picks.yml runs scripts/update_picks.py; contents write present |
| W3 Hotspawn crowd % is never a probability input | PASS | static scan found no crowd->probability usage |
| REQ requirements traceability | PASS | REQ1 PASS; REQ2 PASS; REQ3 PASS; REQ4 PASS; REQ5 PASS; REQ6 PASS; REQ7 PASS; REQ8 PASS; REQ9 PASS; REQ10 PASS; REQ11 PASS; REQ12 PASS |

## Requirements traceability

| id | requirement | status | checks |
|---|---|---|---|
| REQ1 | A pick exists for every match (pick is one of the two teams) | PASS | D3, D11 |
| REQ2 | Win probabilities for both teams on every match, summing to 100% | PASS | D4, D5 |
| REQ3 | Probabilities come from outside Hotspawn (books/markets/our results model) | PASS | D12, W3 |
| REQ4 | External betting lines used where they exist (markets first) | PASS | D8a, D6 |
| REQ5 | Every match without a market line still gets a pick + documented method | PASS | D8b, D13 |
| REQ6 | Separate unresolved section, with limitations, linked from the exec summary | PASS | S4, S5, S5b |
| REQ7 | Executive summary links in-site to the updated picks list | PASS | S4 |
| REQ8 | Every table row carries an official/trusted source link (or is flagged unverified) | PASS | D7, D8a, D8b, D17 |
| REQ9 | Mobile-friendly: responsive viewport + responsive CSS + readable cards | PASS | S2, S7 |
| REQ10 | Automatic refresh every 4-8 hours, no manual input | PASS | W1, W2, D1 |
| REQ11 | Site integrity: no broken internal links, root entry point works | PASS | S1, S6, S8 |
| REQ12 | Third-party sources attributed where their data is used | PASS | S5c |

**D18 items:**
- DMG Esports Sweden vs Northern Wolves Esports: ours=2026-10-24 16:30 lp=2026-10-28 17:30
- Lundqvist Darkside vs Mazepa: ours=2026-10-24 16:30 lp=2026-10-28 18:00
- DMG Esports Sweden vs FlameHard: ours=2026-10-25 17:30 lp=2026-11-01 17:00
- Hannover Esports e.V. vs Reveal Multigaming: ours=2026-11-03 17:00 lp=2026-10-23 16:00

**REQ items:**
- REQ1: A pick exists for every match (pick is one of the two teams) -> PASS
- REQ2: Win probabilities for both teams on every match, summing to 100% -> PASS
- REQ3: Probabilities come from outside Hotspawn (books/markets/our results model) -> PASS
- REQ4: External betting lines used where they exist (markets first) -> PASS
- REQ5: Every match without a market line still gets a pick + documented method -> PASS
- REQ6: Separate unresolved section, with limitations, linked from the exec summary -> PASS
- REQ7: Executive summary links in-site to the updated picks list -> PASS
- REQ8: Every table row carries an official/trusted source link (or is flagged unverified) -> PASS
- REQ9: Mobile-friendly: responsive viewport + responsive CSS + readable cards -> PASS
- REQ10: Automatic refresh every 4-8 hours, no manual input -> PASS
- REQ11: Site integrity: no broken internal links, root entry point works -> PASS
- REQ12: Third-party sources attributed where their data is used -> PASS

# Verification report — PASS
_2026-10-21T20:30:01.829317+00:00_
195 matches · MARKET_POLYMARKET: 8 · UNRESOLVED: 126 · MODEL_ELO: 61 · MARKET_BOOKS: 0

| check | status | detail |
|---|---|---|
| D1 payload parses, has matches and a fresh generated_at | PASS | 195 matches, generated_at=2026-10-21T20:16:23.617204+00:00 (0.2h old) |
| D2 two distinct teams and a start time on every match | PASS | all 195 rows have team1, team2 and a start time |
| D3 a pick exists and is one of the two teams | PASS | every match has a pick equal to team1 or team2 |
| D4 probabilities are in range and sum to 1 | PASS | every row sums to 1.0 within 0.005 |
| D5 pick_prob equals the larger probability | PASS | pick_prob matches max(prob_team1, prob_team2) on every row |
| D6 method is one of ['MARKET_BOOKS', 'MARKET_POLYMARKET', 'MODEL_ELO', 'UNRESOLVED'] | PASS | all methods documented |
| D7 every row links at least one official/trusted source | PASS | all 195 rows carry at least one source URL |
| D7b source host recognised as official/trusted | WARN | 61 row(s) link a host not on the allowlist — manual review |
| D8a market rows link a bookmaker/prediction-market URL | PASS | every market row links its market |
| D8b unresolved rows are explicit unverified 50/50 (limitations published) | PASS | every unresolved row is 0.50 and labelled unverified |
| D9 no duplicate fixtures | PASS | no duplicate (teams,start) rows |
| D12 Hotspawn is never the probability source (fixture list only) | PASS | no market/model row cites hotspawn.com as its probability source |
| D10 counts_by_method agrees with the rows | PASS | counts consistent |
| D11 declared count equals number of rows | PASS | count=195, rows=195 |
| D13 coverage: share of matches without an external market line | WARN | 126/195 rows are UNRESOLVED 50/50 (64.6%). A non-zero share is allowed only when published as an unresolved section with limitations — see S4 and the site's Unresolved page. |
| D14 canonical data and site data are identical | PASS | identical |
| S1 all required site files exist | PASS | 8 files present |
| S2 every page is mobile-ready (viewport width=device-width) | PASS | all pages declare a responsive viewport |
| S3 every page links the shared picks navigation | PASS | navigation present |
| S4 executive summary links in-site to picks + unresolved and states limitations | PASS | exec summary checks: {'links_picks': True, 'links_unresolved': True, 'mentions_limitations': True, 'mentions_updated': True} |
| S5 separate unresolved section with limitations | PASS | unresolved page states limitations |
| S5b unresolved page names each unresolved league (per-league limits) | WARN | 0/10 unresolved tournaments named on the page |
| S5c third-party data sources are attributed on Method & Sources | PASS | attribution present |
| S6 no broken internal links | PASS | all internal href/src resolve |
| S7 shared JS/CSS exist and are responsive | PASS | assets load data and contain responsive rules |
| S8 root index.html sends visitors into the site | PASS | root redirects to docs/ |
| S9 all external links use https | PASS | 8 external link(s) collected for manual review; 0 plain-http |
| W1 picks update is scheduled every 4-8 hours | PASS | update-picks.yml: cron '0 */6 * * *' = every 6h |
| W2 update workflow runs the generator with contents: write | PASS | update-picks.yml runs scripts/update_picks.py; contents write present |
| W3 Hotspawn crowd % is never a probability input | PASS | static scan found no crowd->probability usage |

**D7b items:**
- Team VDS vs Pegasus Esports -> model evidence link is a docs page: https://lol.fandom.com/api.php?action=help&modules=cargoquery
- Reveal Multigaming vs Hannover Esports e.V. -> model evidence link is a docs page: https://lol.fandom.com/api.php?action=help&modules=cargoquery
- NextGeneration Esports vs Pegasus Esports -> model evidence link is a docs page: https://lol.fandom.com/api.php?action=help&modules=cargoquery
- Team VDS vs Team Reds -> model evidence link is a docs page: https://lol.fandom.com/api.php?action=help&modules=cargoquery
- AceGaming vs Babos Gaming -> model evidence link is a docs page: https://lol.fandom.com/api.php?action=help&modules=cargoquery
- LØS vs T1 -> model evidence link is a docs page: https://lol.fandom.com/api.php?action=help&modules=cargoquery
- JSK Esports vs El Menzah Esports -> model evidence link is a docs page: https://lol.fandom.com/api.php?action=help&modules=cargoquery
- Simplicity Gaming vs JSK Academy -> model evidence link is a docs page: https://lol.fandom.com/api.php?action=help&modules=cargoquery
- JSK Academy vs New Era Team -> model evidence link is a docs page: https://lol.fandom.com/api.php?action=help&modules=cargoquery
- Babos Gaming vs Hannover Esports e.V. -> model evidence link is a docs page: https://lol.fandom.com/api.php?action=help&modules=cargoquery
- Reveal Multigaming vs AceGaming -> model evidence link is a docs page: https://lol.fandom.com/api.php?action=help&modules=cargoquery
- Neko Elite Kittens vs spongecord prime -> model evidence link is a docs page: https://lol.fandom.com/api.php?action=help&modules=cargoquery

**S5b items:**
- 4 Nations 2026 Halloween Heist
- Arabian League 2nd Division 2026 Summer
- Arabian Regional Championship 2026: Lebanon-Libya-Syria-Palestine
- Komplettligaen 2026 Autumn
- LGC Rising 2026 Playoffs
- LigaGG CELOL B 2026 Split 2 Playoffs
- PRM 2nd Division 26-27 Fall
- PRM 3rd Division 26-27 Fall
- RIVALS LEAGUE Season 2
- Tunisian Super League 2026

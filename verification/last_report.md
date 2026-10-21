# Verification report — FAIL
_2026-10-21T20:32:06.971821+00:00_
195 matches · MARKET_POLYMARKET: 8 · MARKET_BOOKS: 0 · UNRESOLVED: 126 · MODEL_ELO: 61

| check | status | detail |
|---|---|---|
| D1 payload parses, has matches and a fresh generated_at | PASS | 195 matches, generated_at=2026-10-21T20:16:23.617204+00:00 (0.3h old) |
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
| D16 no single-game (Game 1/Map 1) market used as a series probability | FAIL | 1 row(s) violate this rule |
| D17 unresolved rows point at a fixture/league source, not a generic wiki page | WARN | 126 unresolved row(s) cite the generic Leaguepedia main page — a per-league/fixture source is preferable |
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
| REQ requirements traceability | WARN | REQ1 PASS; REQ2 PASS; REQ3 PASS; REQ4 PASS; REQ5 WARN; REQ6 WARN; REQ7 PASS; REQ8 WARN; REQ9 PASS; REQ10 PASS; REQ11 PASS; REQ12 PASS |

## Requirements traceability

| id | requirement | status | checks |
|---|---|---|---|
| REQ1 | A pick exists for every match (pick is one of the two teams) | PASS | D3, D11 |
| REQ2 | Win probabilities for both teams on every match, summing to 100% | PASS | D4, D5 |
| REQ3 | Probabilities come from outside Hotspawn (books/markets/our results model) | PASS | D12, W3 |
| REQ4 | External betting lines used where they exist (markets first) | PASS | D8a, D6 |
| REQ5 | Every match without a market line still gets a pick + documented method | WARN | D8b, D13 |
| REQ6 | Separate unresolved section, with limitations, linked from the exec summary | WARN | S4, S5, S5b |
| REQ7 | Executive summary links in-site to the updated picks list | PASS | S4 |
| REQ8 | Every table row carries an official/trusted source link (or is flagged unverified) | WARN | D7, D8a, D8b, D17 |
| REQ9 | Mobile-friendly: responsive viewport + responsive CSS + readable cards | PASS | S2, S7 |
| REQ10 | Automatic refresh every 4-8 hours, no manual input | PASS | W1, W2, D1 |
| REQ11 | Site integrity: no broken internal links, root entry point works | PASS | S1, S6, S8 |
| REQ12 | Third-party sources attributed where their data is used | PASS | S5c |

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

**D16 items:**
- Galions vs Solary — evidence is a single-game market: Polymarket: LoL: Galions vs Solary - Game 1 Winner

**D17 items:**
- Ascent Gaming vs NTNUI Kometkameratene -> generic wiki link https://lol.fandom.com/wiki/Leaguepedia:League_of_Legends_Esports_Wiki
- Solid Gaming vs DMG Esports Norway -> generic wiki link https://lol.fandom.com/wiki/Leaguepedia:League_of_Legends_Esports_Wiki
- Volda E-Sport vs CNG Royal -> generic wiki link https://lol.fandom.com/wiki/Leaguepedia:League_of_Legends_Esports_Wiki
- Your Saviours vs Mixlag fra Trondheim -> generic wiki link https://lol.fandom.com/wiki/Leaguepedia:League_of_Legends_Esports_Wiki
- Turbo Gaming vs Fritt Fall -> generic wiki link https://lol.fandom.com/wiki/Leaguepedia:League_of_Legends_Esports_Wiki
- BlackDivision vs Babos Gaming Academy -> generic wiki link https://lol.fandom.com/wiki/Leaguepedia:League_of_Legends_Esports_Wiki
- Absolved vs The Bandits UK -> generic wiki link https://lol.fandom.com/wiki/Leaguepedia:League_of_Legends_Esports_Wiki
- Brod n Friends vs Crownless -> generic wiki link https://lol.fandom.com/wiki/Leaguepedia:League_of_Legends_Esports_Wiki
- Good Chi vs Inari Esports -> generic wiki link https://lol.fandom.com/wiki/Leaguepedia:League_of_Legends_Esports_Wiki
- HL Tauri Esports vs Bulldog Esports -> generic wiki link https://lol.fandom.com/wiki/Leaguepedia:League_of_Legends_Esports_Wiki

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

**REQ items:**
- REQ1: A pick exists for every match (pick is one of the two teams) -> PASS
- REQ2: Win probabilities for both teams on every match, summing to 100% -> PASS
- REQ3: Probabilities come from outside Hotspawn (books/markets/our results model) -> PASS
- REQ4: External betting lines used where they exist (markets first) -> PASS
- REQ5: Every match without a market line still gets a pick + documented method -> WARN
- REQ6: Separate unresolved section, with limitations, linked from the exec summary -> WARN
- REQ7: Executive summary links in-site to the updated picks list -> PASS
- REQ8: Every table row carries an official/trusted source link (or is flagged unverified) -> WARN
- REQ9: Mobile-friendly: responsive viewport + responsive CSS + readable cards -> PASS
- REQ10: Automatic refresh every 4-8 hours, no manual input -> PASS
- REQ11: Site integrity: no broken internal links, root entry point works -> PASS
- REQ12: Third-party sources attributed where their data is used -> PASS

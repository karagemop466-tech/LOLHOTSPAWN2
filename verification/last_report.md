# Verification report — PASS
_2026-10-25T15:09:51.821751+00:00_
156 matches · MODEL_ELO: 91 · UNRESOLVED: 0 · MARKET_CONSENSUS: 8 · MARKET_SINGLE: 1 · MODEL_LEAGUE_PRIOR: 0 · MODEL_ELO_STANDINGS: 54 · MARKET_BOOKS: 0 · MODEL_ELO_THIN: 2 · MARKET_POLYMARKET: 0 · MODEL_STANDINGS: 0

| check | status | detail |
|---|---|---|
| D1 payload parses, has matches and a fresh generated_at | PASS | 156 matches, generated_at=2026-10-25T15:01:00.334336Z (0.1h old) |
| D2 two distinct teams and a start time on every match | PASS | all 156 rows have team1, team2 and a start time |
| D3 a pick exists and is one of the two teams | PASS | every match has a pick equal to team1 or team2 |
| D4 probabilities are in range and sum to 1 | PASS | every row sums to 1.0 within 0.005 |
| D5 pick_prob equals the larger probability | PASS | pick_prob matches max(prob_team1, prob_team2) on every row |
| D6 method is one of ['MARKET_BOOKS', 'MARKET_CONSENSUS', 'MARKET_POLYMARKET', 'MARKET_SINGLE', 'MODEL_ELO', 'MODEL_ELO_STANDINGS', 'MODEL_ELO_THIN', 'MODEL_LEAGUE_PRIOR', 'MODEL_STANDINGS', 'UNRESOLVED'] | PASS | all methods documented |
| D6b confidence labels are from the documented set | PASS | High/Medium/Low/None only |
| D7c every source URL is absolute http(s) | PASS | all source URLs well formed |
| D7 every row links at least one source URL | PASS | all 156 rows carry at least one source URL |
| D8a market rows link a bookmaker/prediction-market URL | PASS | every market row links its market |
| D8c model rows link a results-source URL | PASS | every model row links a results source |
| D8d model rows with generic results-table sources are flagged | PASS | generic Leaguepedia table links are explicitly flagged as less directly auditable |
| D8b unresolved rows are explicit unverified 50/50 (limitations published) | PASS | every unresolved row is 0.50 and labelled unverified |
| D9 no duplicate fixtures | PASS | no duplicate (teams,start) rows |
| D16 no single-game (Game 1/Map 1) market used as a series probability | PASS | no non-BO1 row cites a single-game market |
| D12 Hotspawn is never the probability source (fixture list only) | PASS | no market/model row cites hotspawn.com as its probability source |
| D10 declared counts agree with the rows | PASS | counts.resolved/unresolved consistent |
| D11 declared count equals number of rows | PASS | declared=156, rows=156 |
| D20 each external market provider counted at most once per fixture | PASS | every market row has unique provider keys and matching source_count |
| D21 every upcoming Hotspawn lobby fixture is priced; no excluded fixture is priced | PASS | lobby upcoming=156, priced=156, missing=0, extra=0, excluded=9, leaked=0 |
| D22 external-source probe rows are sourced and never carry a probability | PASS | 43 probed source(s), each with an https link, HTTP status and verdict |
| D24 estimates are distinguished from official results verification | PASS | 156 rows audited; official confirmation left blank |
| D25 saved decimal prices reproduce no-vig probabilities and consensus | PASS | Recomputed from saved values only, not a current quote or outcome guarantee |
| D13 rows without team evidence are 50/50 and explicitly labelled | PASS | 0 row(s) lack team evidence (UNRESOLVED / NO_TEAM_HISTORY); 0 labelled, 0 non-50/50. Info: 38 model row(s) land within ±2 pts of 50% — these are even-matchup estimates from recorded results, not placeholders. |
| D18 start times cross-checked against Leaguepedia MatchSchedule | WARN | 104/117 matched fixture times agree with Leaguepedia; 39 fixture(s) not in the snapshot; 13 differ (Hotspawn is authoritative for pick lock times; verify current organizer schedules before relying on a delta). Snapshot captured 2026-10-21T20:44:30.124894+00:00 (90.4h old). This is a stale diagnostic snapshot; deltas are historical and do not verify the current schedule. |
| D14 single published data file (site copy) | PASS | only docs/data/picks.json exists — site copy is the single source |
| D23 no committed artifact contains git conflict markers | PASS | no conflict markers in docs/, data/, verification/, research/, scripts/, .github/ |
| S1 all required site files exist | PASS | 10 files present |
| S10 phone bottom nav has one grid column per link on every page | PASS | 6 links, 6 columns on every page |
| S13 executive summary has a separate unresolved section (every unresolved fixture listed + per-league limits) with the picks listed first | PASS | unresolved section ids present; picks before unresolved section: yes; in-site pick links: yes |
| S14 no page reuses the 12px .bar probability rule as its header | PASS | headers use .header-inner on every page |
| S15 jsdom render harness exists and runs in CI | PASS | harness present; wired into pipeline-test.yml, verify.yml |
| S16 coin-flip picks are labelled, counted in the summary and filterable | PASS | toss-up threshold, chip, summary link and picks filter present |
| S2 every page is mobile-ready (viewport width=device-width) | PASS | all pages declare a responsive viewport |
| S3 every page links the shared picks navigation | PASS | navigation present |
| S4 executive summary links in-site to picks + unresolved and states limitations | PASS | exec summary checks: {'links_picks': True, 'links_unresolved': True, 'mentions_limitations': True, 'mentions_updated': True} |
| S4c executive summary has a dedicated in-site picks block | PASS | 4 in-site links, counts bound to ids; 0 missing |
| S5 separate unresolved section with limitations | PASS | unresolved page states limitations |
| S5c third-party data sources are attributed on Method & Sources | PASS | attribution present |
| S6 no broken internal links | PASS | all internal href/src resolve |
| S7 shared JS/CSS exist and are responsive | PASS | assets load data and contain responsive rules |
| S8 root index.html sends visitors into the site | PASS | root redirects to docs/ |
| S9 all external links use https | PASS | 45 external link(s) collected for manual review; 0 plain-http |
| S11 every CSS class used by a page is defined in style.css | PASS | 7 page(s), no unstyled class |
| S18 every page has the same quick-jump bar; the summary explains non-featured picks in-site | PASS | 7 pages, 6 jump targets, #nonfeatured present with a source table |
| S19 phone layout contract: viewport meta, a <=430px breakpoint, no fixed width above 430px | PASS | 390px-safe: device-width viewport on every page, phone breakpoint present, no fixed width above 430px |
| S12 all pages share one navigation, freshness slot and unique ids | PASS | 7 pages, identical nav with 6 primary targets |
| S18 site is installable on a phone home screen (manifest, icons, per-page links) | PASS | 7 pages link the manifest + apple-touch-icon; 3 declared icon(s) present with matching sizes |
| S17 manual-review tables link a source on every row | PASS | 16 reviewed row(s) across 2 section(s), every one links an external page |
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

**D18 items:**
- Duplex Silva Pigeons Edition vs Sissi State Punks: ours=2026-10-25 17:00 lp=2026-10-25 16:00
- Mazepa vs B2U: ours=2026-10-26 18:00 lp=2026-10-24 17:00
- Karolinerna vs Turbo Gaming: ours=2026-10-27 18:00 lp=2026-10-24 16:30
- FlameHard vs B2U: ours=2026-10-28 17:00 lp=2026-10-24 16:30
- Babos Gaming Academy vs VfB x Engines Stuttgart: ours=2026-10-29 18:00 lp=2026-10-25 16:00
- Playwell Rød Q vs Your Saviours: ours=2026-10-30 17:00 lp=2026-10-01 17:45
- Volda E-Sport vs Ascent Gaming: ours=2026-10-30 17:00 lp=2026-09-26 17:00
- Fritt Fall vs Team Lucidity Esports: ours=2026-10-31 17:30 lp=2026-10-24 16:30
- Karolinerna vs Lund Esports Organization OGs: ours=2026-11-01 18:00 lp=2026-10-25 18:00
- Rich Gang Sweden vs Northern Wolves Esports: ours=2026-11-01 18:00 lp=2026-10-25 17:30
- 2 Massive vs Lund Esports Organization OGs: ours=2026-11-03 18:00 lp=2026-10-24 16:30
- Packmiko E-Sports DACH vs Atruvia Münster Esports: ours=2026-11-05 17:00 lp=2026-10-27 16:30

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

# Row-by-row audit of the published payload

Payload `docs/data/picks.json` generated **2026-10-25T15:32:40.608816Z** (schema 3): 156 fixtures, 156 resolved, 0 unresolved, 9 with an external line.

Auditor: `scripts/audit_rows.py` — offline, read-only, recomputes each row's arithmetic from the numbers that row cites. It never invents a value: anything it cannot confirm is reported as `UNVERIFIED`.

| Check | Result | Detail |
|---|---|---|
| R1 fixture identity: unique ids, two distinct named teams, real UTC start | PASS | 156 rows; duplicate ids=0; bad identity=0 |
| R1b no row was already more than 15 min old when the payload was generated | PASS | 0 row(s) start before generated_at-15min |
| R2 probabilities sum to 100% and the pick is the higher probability | PASS | sum failures=0; pick failures=0 |
| R3 method label agrees with the evidence carried on the row | PASS | method mismatches=0; unresolved mismatches=0; standings mismatches=0 |
| R4 every cited decimal price re-converts to the probability published for that source | PASS | 16 de-vig conversions recomputed; 0 disagree by >0.2pt |
| R5 published consensus and row probability recompute from the row's own sources | PASS | 9 market rows recomputed (median >=3 sources, else weighted mean); 0 disagree by >0.15pt |
| R6 dispersion and weighted mean recomputed | PASS | 0 disagreement(s) |
| R7 Hotspawn crowd percentages are not the published probability | PASS | 147 model rows compared with the crowd number: mean \|published - crowd\| = 0.3677, 0 row(s) (0.0%) within 0.5pt (coincidence, not a copy) |
| R7b every crowd figure carries its 'context only' note | PASS | crowd.note present on every row that publishes a crowd percentage |
| R8 every row cites https sources, at least one independent of Hotspawn | PASS | rows without a source=0; rows whose only source is Hotspawn=0 |
| R8b every cited host is on the approved provenance allowlist | PASS | 0 citation(s) to an unapproved host; hosts seen: lol.fandom.com(415), www.hotspawn.com(156), polymarket.com(9), guest.api.arcadia.pinnacle.com(8), www.unibet.com.au(8) |
| R8c the Hotspawn citation states it is the fixture list only | PASS | 0 Hotspawn citation(s) that could be read as a probability source |
| R9 the published counts block re-foots against the rows | PASS | 0 count mismatch(es); 0 method-tally mismatch(es) |
| R9b the coverage block re-foots against the rows | PASS | 0 mismatch(es) |
| R10 every per-league row re-foots against the rows it summarises | PASS | 12 league rows, 156 fixtures; 0 mismatch(es); leagues missing from the breakdown: none |
| R11 Hotspawn tier values as published (never inferred) | INFO | 108 of 156 rows carry no tier from Hotspawn and are shown as 'Tier not published'; observed values: WAITING FOR INFORMATION=108, C=36, S=11, A=1 |
| R12 no cancelled/excluded fixture is priced | PASS | 9 excluded fixture(s); 0 also priced |
| R13 the same pair in the same competition on the same day is listed once | PASS | 0 duplicate listing(s) |
| R14 the featured and next-24h lists point at real rows inside their window | PASS | 0 problem(s) |
| R15 the published book/Hotspawn time spread recomputes from the timestamps on the row | PASS | 0 market row(s) whose time_spread_hours does not follow from the start times it cites |
| R16 every per-source start delta recomputes (unsigned by design, both timestamps shown) | PASS | 25 book start times compared with their fixture; 0 disagree |

**20 PASS · 0 FAIL · 0 WARN · 1 INFO · 0 UNVERIFIED**

## Market rows: consensus recomputed from the row's own sources

| Fixture | Match | Sources | Recomputed consensus | Published consensus | Row probability |
|---|---|---|---|---|---|
| 1075817 | Invictus Gaming vs Hanwha Life Esports | 3 | 0.281 | 0.281 | 0.281 |
| 1075816 | Top Esports vs G2 Esports | 3 | 0.4493 | 0.4493 | 0.4493 |
| 1075819 | Dplus KIA vs Movistar KOI | 3 | 0.7592 | 0.7592 | 0.7592 |
| 1075818 | Gen.G vs LYON | 3 | 0.8962 | 0.8962 | 0.8962 |
| 1075821 | T1 vs CTBC Flying Oyster | 3 | 0.8428 | 0.8428 | 0.8428 |
| 1075820 | Karmine Corp vs Bilibili Gaming | 3 | 0.3129 | 0.3129 | 0.3129 |
| 1075822 | LØS vs Team Secret Whales | 3 | 0.3564 | 0.3564 | 0.3564 |
| 1075823 | Team Liquid vs Anyone's Legend | 3 | 0.3141 | 0.3141 | 0.3141 |
| 1079080 | Mental Rush vs Vitality Rising Bees | 1 | 0.365 | 0.365 | 0.365 |

## De-vig recomputed for every cited decimal price

| Fixture | Source | Decimals (team1 / team2) | Published p(team1) | Recomputed | Δ |
|---|---|---|---|---|---|
| 1075817 | Pinnacle | 3.38 / 1.3333 | 0.2829 | 0.2829 | 0.0 |
| 1075817 | Unibet | 3.3 / 1.29 | 0.281 | 0.281 | 0.0 |
| 1075816 | Pinnacle | 2.14 / 1.7463 | 0.4493 | 0.4493 | 0.0 |
| 1075816 | Unibet | 2.08 / 1.67 | 0.4453 | 0.4453 | 0.0 |
| 1075819 | Pinnacle | 1.2558 / 3.96 | 0.7592 | 0.7592 | 0.0 |
| 1075819 | Unibet | 1.27 / 3.45 | 0.7309 | 0.7309 | 0.0 |
| 1075818 | Pinnacle | 1.0642 / 9.19 | 0.8962 | 0.8962 | 0.0 |
| 1075818 | Unibet | 1.07 / 7.5 | 0.8751 | 0.8751 | 0.0 |
| 1075821 | Pinnacle | 1.1287 / 6.05 | 0.8428 | 0.8428 | 0.0 |
| 1075821 | Unibet | 1.12 / 5.4 | 0.8282 | 0.8282 | 0.0 |
| 1075820 | Pinnacle | 3.06 / 1.3937 | 0.3129 | 0.3129 | 0.0 |
| 1075820 | Unibet | 2.85 / 1.38 | 0.3262 | 0.3262 | 0.0 |
| 1075822 | Pinnacle | 2.69 / 1.4902 | 0.3565 | 0.3565 | 0.0 |
| 1075822 | Unibet | 2.6 / 1.44 | 0.3564 | 0.3564 | 0.0 |
| 1075823 | Pinnacle | 3.05 / 1.3968 | 0.3141 | 0.3141 | 0.0 |
| 1075823 | Unibet | 2.8 / 1.4 | 0.3333 | 0.3333 | 0.0 |

## Cited hosts

- `lol.fandom.com` — 415 citation(s)
- `www.hotspawn.com` — 156 citation(s)
- `polymarket.com` — 9 citation(s)
- `guest.api.arcadia.pinnacle.com` — 8 citation(s)
- `www.unibet.com.au` — 8 citation(s)

Rows audited: **156**.

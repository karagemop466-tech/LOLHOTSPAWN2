# Row-by-row audit of the published payload

Payload `docs/data/picks.json` generated **2026-10-25T17:03:55.791951Z** (schema 3): 139 fixtures, 139 resolved, 0 unresolved, 8 with an external line.

Auditor: `scripts/audit_rows.py` — offline, read-only, recomputes each row's arithmetic from the numbers that row cites. It never invents a value: anything it cannot confirm is reported as `UNVERIFIED`.

| Check | Result | Detail |
|---|---|---|
| R1 fixture identity: unique ids, two distinct named teams, real UTC start | PASS | 139 rows; duplicate ids=0; bad identity=0 |
| R1b no row was already more than 15 min old when the payload was generated | PASS | 0 row(s) start before generated_at-15min |
| R2 probabilities sum to 100% and the pick is the higher probability | PASS | sum failures=0; pick failures=0 |
| R3 method label agrees with the evidence carried on the row | PASS | method mismatches=0; unresolved mismatches=0; standings mismatches=0 |
| R4 every cited decimal price re-converts to the probability published for that source | PASS | 21 de-vig conversions recomputed; 0 disagree by >0.2pt |
| R5 published consensus and row probability recompute from the row's own sources | PASS | 8 market rows recomputed (median >=3 sources, else weighted mean); 0 disagree by >0.15pt |
| R6 dispersion and weighted mean recomputed | PASS | 0 disagreement(s) |
| R7 Hotspawn crowd percentages are not the published probability | PASS | 131 model rows compared with the crowd number: mean \|published - crowd\| = 0.3655, 0 row(s) (0.0%) within 0.5pt (coincidence, not a copy) |
| R7b every crowd figure carries its 'context only' note | PASS | crowd.note present on every row that publishes a crowd percentage |
| R8 every row cites https sources, at least one independent of Hotspawn | PASS | rows without a source=0; rows whose only source is Hotspawn=0 |
| R8b every cited host is on the approved provenance allowlist | PASS | 0 citation(s) to an unapproved host; hosts seen: lol.fandom.com(370), www.hotspawn.com(139), polymarket.com(8), guest.api.arcadia.pinnacle.com(7), www.unibet.com.au(7), www.bovada.lv(7) |
| R8c the Hotspawn citation states it is the fixture list only | PASS | 0 Hotspawn citation(s) that could be read as a probability source |
| R9 the published counts block re-foots against the rows | PASS | 0 count mismatch(es); 0 method-tally mismatch(es) |
| R9b the coverage block re-foots against the rows | PASS | 0 mismatch(es) |
| R10 every per-league row re-foots against the rows it summarises | PASS | 12 league rows, 139 fixtures; 0 mismatch(es); leagues missing from the breakdown: none |
| R11 Hotspawn tier values as published (never inferred) | INFO | 94 of 139 rows carry no tier from Hotspawn and are shown as 'Tier not published'; observed values: WAITING FOR INFORMATION=94, C=34, S=10, A=1 |
| R12 no cancelled/excluded fixture is priced | PASS | 18 excluded fixture(s); 0 also priced |
| R13 the same pair in the same competition on the same day is listed once | PASS | 0 duplicate listing(s) |
| R14 the featured and next-24h lists point at real rows inside their window | PASS | 0 problem(s) |
| R15 the published book/Hotspawn time spread recomputes from the timestamps on the row | PASS | 0 market row(s) whose time_spread_hours does not follow from the start times it cites |
| R16 every per-source start delta recomputes (unsigned by design, both timestamps shown) | PASS | 29 book start times compared with their fixture; 0 disagree |

**20 PASS · 0 FAIL · 0 WARN · 1 INFO · 0 UNVERIFIED**

## Market rows: consensus recomputed from the row's own sources

| Fixture | Match | Sources | Recomputed consensus | Published consensus | Row probability |
|---|---|---|---|---|---|
| 1075816 | Top Esports vs G2 Esports | 4 | 0.4602 | 0.4602 | 0.4602 |
| 1075819 | Dplus KIA vs Movistar KOI | 4 | 0.7638 | 0.7638 | 0.7638 |
| 1075818 | Gen.G vs LYON | 4 | 0.8947 | 0.8947 | 0.8947 |
| 1075821 | T1 vs CTBC Flying Oyster | 4 | 0.8396 | 0.8396 | 0.8396 |
| 1075820 | Karmine Corp vs Bilibili Gaming | 4 | 0.318 | 0.318 | 0.318 |
| 1075822 | LØS vs Team Secret Whales | 4 | 0.3507 | 0.3507 | 0.3507 |
| 1075823 | Team Liquid vs Anyone's Legend | 4 | 0.3133 | 0.3133 | 0.3133 |
| 1079080 | Mental Rush vs Vitality Rising Bees | 1 | 0.39 | 0.39 | 0.39 |

## De-vig recomputed for every cited decimal price

| Fixture | Source | Decimals (team1 / team2) | Published p(team1) | Recomputed | Δ |
|---|---|---|---|---|---|
| 1075816 | Pinnacle | 2.03 / 1.8333 | 0.4745 | 0.4745 | 0.0 |
| 1075816 | Unibet | 2.08 / 1.67 | 0.4453 | 0.4453 | 0.0 |
| 1075816 | Bovada | 2.1 / 1.69 | 0.4459 | 0.4459 | 0.0 |
| 1075819 | Pinnacle | 1.2551 / 3.97 | 0.7598 | 0.7598 | 0.0 |
| 1075819 | Unibet | 1.21 / 4.0 | 0.7678 | 0.7678 | 0.0 |
| 1075819 | Bovada | 1.2353 / 3.85 | 0.7571 | 0.7571 | 0.0 |
| 1075818 | Pinnacle | 1.066 / 9.04 | 0.8945 | 0.8945 | 0.0 |
| 1075818 | Unibet | 1.07 / 7.5 | 0.8751 | 0.8751 | 0.0 |
| 1075818 | Bovada | 1.0556 / 9.0 | 0.895 | 0.895 | 0.0 |
| 1075821 | Pinnacle | 1.1287 / 6.05 | 0.8428 | 0.8428 | 0.0 |
| 1075821 | Unibet | 1.12 / 5.4 | 0.8282 | 0.8282 | 0.0 |
| 1075821 | Bovada | 1.125 / 5.75 | 0.8364 | 0.8364 | 0.0 |
| 1075820 | Pinnacle | 3.06 / 1.3937 | 0.3129 | 0.3129 | 0.0 |
| 1075820 | Unibet | 2.85 / 1.38 | 0.3262 | 0.3262 | 0.0 |
| 1075820 | Bovada | 2.9 / 1.3846 | 0.3232 | 0.3232 | 0.0 |
| 1075822 | Pinnacle | 2.69 / 1.4902 | 0.3565 | 0.3565 | 0.0 |
| 1075822 | Unibet | 2.6 / 1.44 | 0.3564 | 0.3564 | 0.0 |
| 1075822 | Bovada | 2.85 / 1.4 | 0.3294 | 0.3294 | 0.0 |
| 1075823 | Pinnacle | 3.05 / 1.3968 | 0.3141 | 0.3141 | 0.0 |
| 1075823 | Unibet | 2.8 / 1.4 | 0.3333 | 0.3333 | 0.0 |
| 1075823 | Bovada | 3.0 / 1.3636 | 0.3125 | 0.3125 | 0.0 |

## Cited hosts

- `lol.fandom.com` — 370 citation(s)
- `www.hotspawn.com` — 139 citation(s)
- `polymarket.com` — 8 citation(s)
- `guest.api.arcadia.pinnacle.com` — 7 citation(s)
- `www.unibet.com.au` — 7 citation(s)
- `www.bovada.lv` — 7 citation(s)

Rows audited: **139**.

# Line-by-line payload audit — 2026-10-25 (session `arena/b5f85948`)

- Payload: `docs/data/picks.json`, generated `2026-10-25T15:01:00.334336Z` (0.2 h old at audit time)
- Rows: **156** · declared fixtures: **156**
- Next scheduled update: `2026-10-25T18:00:00Z` · stale after: `2026-10-25T23:01:00.334336Z`

## Method and confidence mix

| Method | Rows |
|---|---:|
| `MARKET_CONSENSUS` | 8 |
| `MARKET_SINGLE` | 1 |
| `MODEL_ELO` | 91 |
| `MODEL_ELO_STANDINGS` | 54 |
| `MODEL_ELO_THIN` | 2 |

Confidence: {'High': 23, 'Medium': 122, 'Low': 11}  
Upcoming starts: 156 · already-started rows in payload: 0  
Bookmaker source citations: 25 · Leaguepedia citations: 415 · Hotspawn fixture citations: 156

## Per-competition tally (re-derived from rows)

| Competition | Rows | Tier labels seen |
|---|---:|---|
| PRM 3rd Division 26-27 Fall | 59 | WAITING FOR INFORMATION |
| PRM 2nd Division 26-27 Fall | 36 | C |
| Tunisian Super League 2026 | 20 | WAITING FOR INFORMATION |
| RIVALS LEAGUE Season 2 | 15 | WAITING FOR INFORMATION |
| Worlds 2026 Main Event | 8 | S |
| 4 Nations 2026 Halloween Heist | 4 | WAITING FOR INFORMATION |
| Arabian League 2nd Division 2026 Summer | 4 | WAITING FOR INFORMATION |
| Komplettligaen 2026 Autumn Playoffs | 3 | WAITING FOR INFORMATION |
| LCP 2027 Promotion | 3 | S |
| LigaGG CELOL A 2026 Split 2 Playoffs | 2 | WAITING FOR INFORMATION |
| LGC Rising 2026 Playoffs | 1 | A |
| LigaGG CELOL B 2026 Split 2 Playoffs | 1 | WAITING FOR INFORMATION |

## Excluded fixtures (9)

- `1074661` DMG Esports Sweden vs FlameHard — cancelled: Hotspawn status is 'cancelled'; not priced (source present)
- `1074665` Northern Wolves Esports vs Rich Gang Sweden — cancelled: Hotspawn status is 'cancelled'; not priced (source present)
- `1074662` Karolinerna vs Lund Esports Organization OGs — cancelled: Hotspawn status is 'cancelled'; not priced (source present)
- `1079143` Pegasus Esports vs Team Reds — cancelled: Hotspawn status is 'cancelled'; not priced (source present)
- `1079035` AceGaming vs ex-A41G — cancelled: Hotspawn status is 'cancelled'; not priced (source present)
- `1079148` Void Walkers vs Victorious Demons — cancelled: Hotspawn status is 'cancelled'; not priced (source present)
- `1079044` Hannover Esports e.V. vs Reveal Multigaming — cancelled: Hotspawn status is 'cancelled'; not priced (source present)
- `1079052` ex-A41G vs Babos Gaming — cancelled: Hotspawn status is 'cancelled'; not priced (source present)
- `1079061` BvP vs ex-A41G — cancelled: Hotspawn status is 'cancelled'; not priced (source present)

## External-source probe (43 rows in this payload)

Reachable (HTTP 200): 23/43. Every row has an https URL, integer status and an auto-generated verdict; no row carries a probability. Full table on the Unresolved page.

## Verdict

**PASS** — every row satisfies the source, probability, pick and flag invariants; declared counts reconcile to the rows; excluded fixtures are sourced and never priced; the probe is structural and probability-free.

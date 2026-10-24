# Line-by-line source spot checks — 2026-10-24 (session `arena/df8a86d2`, task T21)

Payload under test: `docs/data/picks.json`, generated **2026-10-24T15:28:56.619239Z**
(169 fixtures · 169 priced · 9 market rows · 0 unresolved · 14 excluded cancelled).
All live checks performed 2026-10-24 ~16:1x–16:35 UTC against the **official feed or official page** named in each row's `sources`.

## Method

For each sampled row: read the row's `market.sources` / `sources` entries from the payload, fetch the cited
official endpoint directly, recompute the value the row claims (de-vig where applicable), and compare.
Recompute = two-way probability `p_i = (1/dec_i) / (1/dec_a + 1/dec_b)` for book rows; direction/standings
comparison for model rows.

## Results — priced (market) rows

| # | Fixture (row) | Cited source & official endpoint | Live observation | Payload claim | Verdict |
|---|---|---|---|---|---|
| 1 | Dplus KIA vs T1 · Worlds | Polymarket Gamma `https://gamma-api.polymarket.com/events?slug=lol-dk-t1-2026-10-24` | `outcomePrices ["0.435","0.565"]`, market updated 16:14:39Z | 0.435 / 0.565 | ✅ exact |
| 2 | Top Esports vs Anyone's Legend · Worlds | Polymarket Gamma `…?slug=lol-tes-al-2026-10-24` | `["0.365","0.635"]`, updated 16:10:39Z | 0.365 / 0.635 | ✅ exact |
| 3 | Dplus KIA vs T1 · Worlds | Pinnacle guest API `https://guest.api.arcadia.pinnacle.com/0.1/matchups/1639127310` + `/markets/related/straight` | parent matchup (`parentId: null`, `units: Regular`), participants Dplus KIA/T1, start `2026-10-24T23:00:00Z`; period-0 moneyline `home +117 → 2.17`, `away -137 → 1.7299`; devig = 0.4436/0.5564 | 0.4436 / 0.5564, matchup id 1639127310 | ✅ exact |
| 4 | Hanwha Life vs Gen.G · Worlds | Unibet/Kambi `https://eu-offering-api.kambicdn.com/offering/v2018/ubca/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=ZZ&useCombined=true` event `1029609640` | Match Odds 2.20 / 1.60 (changed 06:39:38Z, before snapshot); devig HLE = 0.42106 | 0.4211 | ✅ exact |
| 5 | Team Liquid vs Bilibili Gaming · Worlds | same Kambi feed, event `1029609649` | 3.35 / 1.29; devig BLG = 0.72199 | 0.722 | ✅ exact |
| 6 | Top Esports vs AL · Worlds | Kambi event `1029609648` | 2.65 / 1.42; devig TES = 0.34888 | 0.349 | ✅ exact |
| 7 | CTBC Flying Oyster vs Movistar KOI · Worlds | Kambi event `1029609639` | 2.75 / 1.40; devig MKOI = 0.66266 | 0.663 | ✅ exact |
| 8 | G2 Esports vs LØS · Worlds | Kambi event `1029609646` | 1.18 / 4.40; devig G2 = 0.78854 | 0.788 | ✅ exact |
| 9 | Invictus Gaming vs Team Secret Whales · Worlds | Kambi event `1029609647` | 1.33 / 3.05; devig IG = 0.69635 | 0.696 | ✅ exact |
| 10 | Dplus KIA vs T1 · Worlds | Kambi event `1029609638` | 2.33 / 1.54 at `changedDate 16:15:37Z` | 2.20 / 1.60 recorded 15:28:56Z | ⚠️ book moved 46 min **after** generation — recorded value correct at snapshot; next refresh picks up |
| 11 | LYON vs Karmine Corp · Worlds | Kambi event `1029609641` | devig LYON 0.457 at `changedDate 15:29:55Z` | 0.462 recorded 15:28:56Z | ⚠️ odds updated 59 s after generation — same class as #10, not an error |
| 12 | Mental Rush vs Vitality Rising Bees · LGC Rising | Polymarket `https://gamma-api.polymarket.com/markets?slug=lol-rb-mr-2026-10-27` — **"Match Winner"** market id `6036989` | `outcomePrices ["0.61","0.39"]`, updated 16:12:39Z | 0.615 / 0.385 (series row) | ✅ consistent (0.5 pt drift after snapshot). Confirmed the cited market is the **series** market — the same event's child `Game N Winner` markets show dead `0.5/0.5` prices and are not cited |

Before generation-time comparison, two pricing sources were double-checked to be the right market type:
Pinnacle row uses only parent `Regular` matchups (prop/child boards rejected — verified `parentId: null`),
and the Polymarket row uses `groupItemTitle: "Match Winner"` (never `Game N`).

## Results — model rows (no book line)

| # | Fixture (row) | Cited source | Observation | Verdict |
|---|---|---|---|---|
| 13 | JSK Esports vs El Menzah Esports · Tunisian Super League 2026 (`MODEL_ELO_THIN`, 57.1% / 42.9%) | `https://lol.fandom.com/wiki/Tunisian_Super_League/2026_Season` | Standings table: JSK Esports **4-0 (100%)**, El Menzah Esports **1-3 (25%)** — model's stronger-side pick matches the cited standings direction | ✅ direction confirmed |
| 14 | Whalepower Humpbacks vs 1. Esport Club Frankfurt · PRM 3rd Division (`MODEL_ELO`, 48.2% / 51.8%) | `https://lol.fandom.com/wiki/Prime_League_3rd_Division/2027_Season/Fall_Split` + Hotspawn fixture page | Row cites exact Leaguepedia competition page; Elo evidence string present (1443 vs 1460, 19/19 games) | ✅ sourced & documented |
| 15 | Karolinerna vs Turbo Gaming · RIVALS LEAGUE (`MODEL_ELO_THIN`) | `https://lol.fandom.com/wiki/RIVALS_LEAGUE/2026_Season/Season_2` | Row transparently flags the Hotspawn/Leaguepedia start-time difference (D18 class) instead of hiding it | ✅ flagged as required |

## Fixture-list / coverage checks

| # | Check | Official source | Observation | Payload | Verdict |
|---|---|---|---|---|---|
| 16 | Lobby total LoL fixtures | `https://play.hotspawn.com/lol-pickems` | header `All tiers (241)` | `lobby_lol_listed: 241` | ✅ exact |
| 17 | Lobby card for row 1075731 | same lobby page | Oct 24 **13:30**, crowd **72% / 28%** (n=25) | `start_utc 2026-10-24T17:30:00Z` (=13:30 UTC), crowd 72/28 n=25 | ✅ exact |
| 18 | Coverage rule | payload `coverage_reconciliation` | `missing=[]`, `extra=[]`, 14 excluded all `cancelled` | 169 upcoming = 169 priced | ✅ full coverage of upcoming lobby fixtures |

## Suite results on this commit (local)

| Suite | Result |
|---|---|
| `verification/check_dom_contract.py` | PASS |
| `verification/test_verifier.py` | 35/35 |
| `verification/test_entity_and_books.py` | 10/10 |
| `verification/test_standings_model.py` | ALL PASS |
| `audit/test_model.py` | 20/20 |
| `scripts/verify_site.py` | **PASS · 36 pass · 0 fail · 0 warn · 1 skip** (REQ1–REQ12 all PASS) |

Report artifacts: `verification/report.json`, `verification/last_report.md` (run 2026-10-24T16:16:07Z).

## Irregularities (non-blocking)

- **#10/#11** post-snapshot odds drift — expected behaviour of a 6-hour snapshot; values were correct at generation.
- Lobby counter `This week 161 matches` (was `139` on 10-23) still has no verifiable definition — remains flagged, never used.

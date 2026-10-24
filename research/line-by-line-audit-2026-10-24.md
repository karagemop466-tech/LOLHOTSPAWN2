# Line-by-Line Repository & Live Data Audit — 2026-10-24

**Session / Branch:** `arena/607dddb0-lolhotspawn2`  
**Audit Date (UTC):** `2026-10-24`  
**Baseline Dataset Audited:** `docs/data/picks.json` (`generated_at`: `2026-10-24T15:28:56.619239Z`, 169 upcoming fixtures across 12 competitions) + live external APIs verified directly on `2026-10-24`.

---

## 1. Executive Summary of Findings & Fixes

1. **Hotspawn Lobby Reconciliation (`play.hotspawn.com/lobby` vs `play.hotspawn.com/lol-pickems`):**
   - `https://play.hotspawn.com/lobby` defaults to the CS2 tab (`226 matches this week` across games), while switching to League of Legends (`https://play.hotspawn.com/lol-pickems`) displays **`All tiers (241)`** League of Legends week entries (`169` upcoming + `72` locked/started at `15:28:56Z`; `161` active on the rolling week header).
   - **Zero** Hotspawn crowd percentages, pick shares, or popularity indicators are ingested or stored anywhere in `scripts/` or `docs/`.

2. **100% Competition Provenance & Entity Disambiguation (`T34`):**
   - Audited every non-identical canonical team resolution across all 169 fixtures against official Leaguepedia `MatchSchedule` Cargo exports and tournament pages.
   - Found **exactly 1 erroneous resolution** out of 169 fixtures:
     - **Fixture `1081700` (`Inari Esports vs Bulldog Esports`, `4 Nations 2026 Halloween Heist`, `2026-10-26T19:00:00Z`):** `Resolver.resolve_with_meta()` previously matched `"Inari Esports"` via 4-letter substring containment (`"nari"` inside `"inariesports"`) to unrelated team **`NARI`**, causing `match_fixture_to_schedule()` to miss the official Leaguepedia schedule row (`Inari Esports (British Team)` vs `Bulldog Esports`, `BestOf: 3`, Round 2) and emit the repo's **only** `GENERIC_RESULTS_SOURCE` (`leaguepedia_url: null`, `best_of: null`).
     - **Verified Fix:** Added `"Inari Esports" -> "Inari Esports (British Team)"` (with `HOTSPAWN_NAME_COLLISION` flag and official wiki citation `https://lol.fandom.com/wiki/4_Nations/2026_Season/Halloween_Heist`) plus `"4 Nations 2026 Halloween Heist"` and `"Komplettligaen 2026 Autumn Playoffs"` tournament page seeds in `data/aliases.json` and `scripts/entity_resolution.py`.
   - Verified all `Rich Gang` regional variants across active competitions:
     - `Komplettligaen 2026 Autumn Playoffs` (`1083040`, `VES Japan vs Rich Gang`, `2026-10-30T17:00:00Z`, Bo5) and `PRM 3rd Division 26-27 Fall` (`1075758`, `1075762`, `1075786`, `1075803`): **`Rich Gang (Norwegian Team)`** — verified on `Komplettligaen/2026 Season/Autumn Playoffs` and `Prime League 3rd Division/2027 Season/Fall Split`.
     - `RIVALS LEAGUE Season 2` (`1074657`, `1083037`): **`Rich Gang Sweden`** — verified on `RIVALS LEAGUE/2026 Season/Season 2`.
     - `4 Nations 2026 Halloween Heist` (`1081702`, `Ruddy Ultras vs Rich Gang UK`, `2026-11-02T19:00:00Z`, Bo3): **`Rich Gang UK`** — verified on `4 Nations/2026 Season/Halloween Heist`.

3. **Bovada Sportsbook Restoration (`0 -> 8` Live Worlds Moneylines) (`T35`):**
   - Previous runs reported `Bovada: no_data (0)` because of **three** compounding issues in `scripts/fetch_markets.py`:
     1. `/services/sports/event/coupon/events/A/description/esports/league-of-legends?...` returns `{}` (empty object), whereas `/services/sports/event/coupon/events/A/description/esports?marketFilterId=def&preMatchOnly=true&lang=en` returns HTTP `200 OK` with all 8 live `World Championship '26` League of Legends pre-match moneylines (`path` contains `/esports/league-of-legends`).
     2. Bovada labels its main series moneyline period `{"description": "Game", "abbreviation": "G", "main": true}`, which `"game" not in prd` erroneously rejected. Fixed to reject only sub-map periods (`Map 1`, `Game 1`, or `period.main is False`).
     3. Bovada event `link` values start with `"/esports/..."`, which returns HTTP `404` unless prefixed with `"/sports"` (`https://www.bovada.lv/sports/esports/...`, verified HTTP `200 OK`).
   - Restoring Bovada upgrades all 8 `Worlds 2026 Main Event` fixtures from 3-book consensus to **4-source consensus** (`Pinnacle + Unibet + Bovada + Polymarket`).

4. **Pinnacle Reachable Per-Matchup URLs (`T35`):**
   - `https://www.pinnacle.com/en/esports/league-of-legends` returns HTTP `404` (`Page Not Found`). Replaced `PIN_PAGE` with `https://guest.api.arcadia.pinnacle.com/0.1/sports/12/leagues?all=false` (`200 OK`) and per-row Pinnacle links with `https://guest.api.arcadia.pinnacle.com/0.1/matchups/{mid}/markets/related/straight` (`200 OK`), eliminating dead external URLs under `verify_site.py --check-external`.

5. **Liquipedia MediaWiki API Normalization & CI Runtime Cut (`T35`):**
   - `probe_liquipedia_pages()` previously iterated all 169 raw fixture tournament strings (`169 × 2.2s ≈ 6.2 min`), querying non-existent prefixes (`PRM 3rd Division...`) and returning `status: "no_data" (0)`.
   - Normalized and deduplicated inputs to ≤8 canonical Liquipedia MediaWiki `apprefix` strings (`World_Championship/2026`, `Prime_League`, `Arabian_League`, `Komplettligaen`, `LCP/2027`, `Game_Changers`, `EMEA_Masters`) via `api.php` (`gzip`, `≥2.2s` spacing, contact UA, never HTML), cutting ~6 minutes off every refresh run and restoring `status: "ok"`.

---

## 2. Tournament-by-Tournament Provenance Table (All 12 Active Competitions)

| Hotspawn Competition | Fixtures | Verified Official Leaguepedia `OverviewPage` | Wiki Source URL (`HTTP 200`) | External Market Coverage |
|---|---:|---|---|---|
| `PRM 3rd Division 26-27 Fall` | 73 | `Prime League 3rd Division/2027 Season/Fall Split` | <https://lol.fandom.com/wiki/Prime_League_3rd_Division/2027_Season/Fall_Split> | None (`NO_EXTERNAL_MARKET`; Tier-2 Elo + Standings) |
| `PRM 2nd Division 26-27 Fall` | 35 | `Prime League 2nd Division/2027 Season/Fall Split` | <https://lol.fandom.com/wiki/Prime_League_2nd_Division/2027_Season/Fall_Split> | None (`NO_EXTERNAL_MARKET`; Tier-2 Elo + Standings) |
| `PRM 1st Division 26-27 Fall` | 26 | `Prime League 1st Division/2027 Season/Fall Split` | <https://lol.fandom.com/wiki/Prime_League_1st_Division/2027_Season/Fall_Split> | None (`NO_EXTERNAL_MARKET`; Tier-2 Elo + Standings) |
| `RIVALS LEAGUE Season 2` | 9 | `RIVALS LEAGUE/2026 Season/Season 2` | <https://lol.fandom.com/wiki/RIVALS_LEAGUE/2026_Season/Season_2> | None (`NO_EXTERNAL_MARKET`; Tier-2 Elo + Standings) |
| `Worlds 2026 Main Event` | 8 | `2026 Season World Championship/Main Event` | <https://lol.fandom.com/wiki/2026_Season_World_Championship/Main_Event> | **8/8 `MARKET_CONSENSUS`** (`Pinnacle + Unibet + Bovada + Polymarket`) |
| `LigaGG CELOL B 2026 Split 2 Playoffs` | 6 | `LigaGG/CELOL Série B/2026 Season/Split 2 Playoffs` | <https://lol.fandom.com/wiki/LigaGG/CELOL_S%C3%A9rie_B/2026_Season/Split_2_Playoffs> | None (`NO_EXTERNAL_MARKET`; Tier-2 Elo) |
| `Arabian League 2nd Division 2026 Fall Playoffs` | 4 | `Arabian League 2nd Division/2026 Season/Fall Playoffs` | <https://lol.fandom.com/wiki/Arabian_League_2nd_Division/2026_Season/Fall_Playoffs> | None (`NO_EXTERNAL_MARKET`; Tier-2 Elo) |
| `4 Nations 2026 Halloween Heist` | 3 | `4 Nations/2026 Season/Halloween Heist` | <https://lol.fandom.com/wiki/4_Nations/2026_Season/Halloween_Heist> | None (`NO_EXTERNAL_MARKET`; Tier-2 Elo; `1081700` fixed) |
| `LGC Rising 2026 Playoffs` | 2 | `LoL Game Changers/2026 Season/Playoffs` | <https://lol.fandom.com/wiki/LoL_Game_Changers/2026_Season/Playoffs> | **1/2 `MARKET_SINGLE`** (`1079017` `Solary vs Galions` on Polymarket) |
| `LigaGG CELOL A 2026 Split 2 Playoffs` | 1 | `LigaGG/CELOL Série A/2026 Season/Split 2 Playoffs` | <https://lol.fandom.com/wiki/LigaGG/CELOL_S%C3%A9rie_A/2026_Season/Split_2_Playoffs> | None (`NO_EXTERNAL_MARKET`; Tier-2 Elo) |
| `LCP 2027 Promotion` | 1 | `LCP/2027 Season/Promotion` | <https://lol.fandom.com/wiki/LCP/2027_Season/Promotion> | None (`NO_EXTERNAL_MARKET`; Tier-2 Elo) |
| `Komplettligaen 2026 Autumn Playoffs` | 1 | `Komplettligaen/2026 Season/Autumn Playoffs` | <https://lol.fandom.com/wiki/Komplettligaen/2026_Season/Autumn_Playoffs> | None (`NO_EXTERNAL_MARKET`; Tier-2 Elo) |

---

## 3. Verified Live Sportsbook & Prediction Market Lines (2026-10-24 UTC)

All prices below were fetched directly from each book's live public JSON endpoint on `2026-10-24` (pre-match 2-way series winner only; zero child/map/kill/baron prop boards):

| Fixture ID | Match (`Bo`) | Pinnacle (Arcadia) | Unibet (Kambi) | Bovada (Coupon JSON) | Polymarket (Gamma) |
|---|---|---:|---:|---:|---:|
| `1082940` | `CTBC Flying Oyster vs Movistar KOI` (`Bo3`) | `2.86 / 1.448` (`mid 1639069648`) | `2.65 / 1.44` (`ev 1029609551`) | `2.85 / 1.40` (`+185 / -250`) | `0.345 / 0.655` |
| `1082941` | `Top Esports vs Anyone's Legend` (`Bo3`) | `2.70 / 1.500` (`mid 1639069650`) | `2.55 / 1.48` (`ev 1029609574`) | `2.55 / 1.49` (`+155 / -205`) | `0.365 / 0.635` |
| `1067683` | `G2 Esports vs LØS` (`Bo3`) | `1.132 / 6.32` (`mid 1639073409`) | `1.10 / 6.00` (`ev 1029609612`) | `1.18 / 4.50` (`-550 / +350`) | `0.855 / 0.145` |
| `1067684` | `LYON vs Karmine Corp` (`Bo3`) | `2.07 / 1.794` (`mid 1639073403`) | `1.95 / 1.78` (`ev 1029609614`) | `2.00 / 1.77` (`EVEN / -130`) | `0.485 / 0.515` |
| `1067685` | `Invictus Gaming vs Team Secret Whales` (`Bo3`) | `1.366 / 3.23` (`mid 1639099210`) | `1.33 / 3.10` (`ev 1029609634`) | `1.33 / 3.20` (`-300 / +220`) | `0.735 / 0.265` |
| `1083043` | `Hanwha Life Esports vs Gen.G` (`Bo5`) | `2.32 / 1.641` (`mid 1639127312`) | `2.25 / 1.60` (`ev 1029609639`) | `2.20 / 1.65` (`+120 / -155`) | `0.415 / 0.585` |
| `1083044` | `Dplus KIA vs T1` (`Bo5`) | `2.45 / 1.581` (`mid 1639127314`) | `2.20 / 1.62` (`ev 1029609644`) | `2.20 / 1.65` (`+120 / -155`) | `0.405 / 0.595` |
| `1083045` | `Team Liquid vs Bilibili Gaming` (`Bo5`) | `3.32 / 1.351` (`mid 1639127316`) | `3.25 / 1.32` (`ev 1029609640`) | `3.25 / 1.32` (`+225 / -310`) | `0.275 / 0.725` |
| `1079017` | `Solary vs Galions` (`LGC Rising`, `Bo5`) | — | — | — | `0.385 / 0.615` |

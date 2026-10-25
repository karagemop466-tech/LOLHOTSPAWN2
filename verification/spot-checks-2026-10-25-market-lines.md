# Line-by-line spot checks — 2026-10-25 (session `arena/419cd73a`, task T28)

Payload under test: `docs/data/picks.json`, **generated 2026-10-25T10:41:50Z** —
156 fixtures · 156 priced · 0 unresolved · 9 market rows · 147 model rows (92 `MODEL_ELO`,
53 `MODEL_ELO_STANDINGS`, 2 `MODEL_ELO_THIN`) · 9 excluded cancelled fixtures.

Every value below was read from the cited live endpoint **during this session**
(2026-10-25, 14:0x–14:5x UTC). Nothing is inferred: where a value could not be
confirmed from an official source it is recorded as *not verified* and flagged.

## 1. Market rows re-checked against the book feeds they cite

American prices → decimal: `+206 → 3.06`, `-254 → 1 + 100/254 = 1.3937`.
Kambi `odds` is decimal × 1000. De-vig = `implied / Σ implied`.

| Fixture (published row) | Live source read this session | Live value | Payload value | Result |
|---|---|---|---|---|
| **Karmine Corp vs Bilibili Gaming** (Worlds, 2026-10-26 17:00Z) | [Pinnacle matchup 1639227252](https://guest.api.arcadia.pinnacle.com/0.1/matchups/1639227252/markets/related/straight), `period 0` `moneyline` `status open` | home **+206** → 3.06 · away **−254** → 1.3937; de-vig **0.3129 / 0.6871** | `decimal_team1 3.06`, `decimal_team2 1.3937`, `prob_team1 0.3129` | ✅ **exact** |
| **T1 vs CTBC Flying Oyster** (Worlds, 2026-10-26 18:00Z) | [Kambi/Unibet listView](https://eu-offering-api.kambicdn.com/offering/v2018/ubca/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=ZZ) event **1029621121** Match Odds, `changedDate 2026-10-25T06:38:31Z` (**before** the 10:41 snapshot) | T1 **1120** → 1.12 · CFO **5400** → 5.40; de-vig **0.8282 / 0.1718** | `prob_team1 0.8282` | ✅ **exact** |
| **Mental Rush vs Vitality Rising Bees** (LGC Rising, 2026-10-27 17:00Z) | [Polymarket market 6036989](https://gamma-api.polymarket.com/markets/6036989), `groupItemTitle "Match Winner"`, `sportsMarketType "moneyline"`, `updatedAt 2026-10-25T14:18:37Z` | `outcomePrices ["0.63","0.37"]`, bestBid 0.61 / bestAsk 0.65 | `0.355 / 0.645` (recorded 10:41Z) | ✅ **pick + direction confirmed**; price drifted 0.645 → 0.630 after the snapshot (`oneDayPriceChange +0.02`), so the recorded value was correct at generation |
| Invictus Gaming vs Hanwha Life Esports (Worlds, 2026-10-25 18:00Z) | Kambi event **1029621111**, `changedDate 2026-10-25T11:57:49Z` | HLE 1290 → 1.29 · IG 3300 → 3.30; de-vig **0.2810 / 0.7190** | `0.3002 / 0.6998` | ⚠️ line moved **after** the snapshot; direction unchanged, pick unchanged |
| Gen.G vs LYON (Worlds, 2026-10-25 19:00Z) | Kambi event **1029621112**, `changedDate 2026-10-25T12:03:37Z` | Gen.G 1070 → 1.07 · LYON 7500 → 7.50; de-vig **0.8751 / 0.1249** | `0.8564 / 0.1436` | ⚠️ post-snapshot drift; pick unchanged |
| Dplus KIA vs Movistar KOI (Worlds, 2026-10-25 22:00Z) | Kambi event **1029621119**, `changedDate 2026-10-25T13:15:28Z` | DK 1270 → 1.27 · MKOI 3450 → 3.45; de-vig **0.7309 / 0.2691** | `0.7190 / 0.2810` | ⚠️ post-snapshot drift; pick unchanged |
| Top Esports vs G2 Esports (Worlds, 2026-10-25 17:00Z) | Kambi event **1029621110**, `changedDate 2026-10-25T11:49:25Z` | TES 2080 → 2.08 · G2 1670 → 1.67; de-vig **0.4453 / 0.5547** | `0.4415 / 0.5585` | ⚠️ post-snapshot drift; pick unchanged |

**Two rows verified digit-for-digit** against the exact feeds the rows cite; the remaining
four differ only because the book moved the line after our 10:41Z snapshot — the same
pattern §19.1 recorded on 2026-10-24, and by design the 6-hour refresh picks the new price
up. **No pick changed direction on any row checked.**

### 1.1 The Polymarket selector is picking the series market, not a game market

The same event read (`lol-rb-mr-2026-10-27`) contains child markets
`LoL: … - Game 1 Winner` (id 6036985) and `Game 2 Winner` (id 6036986) whose
`outcomePrices` are the dead placeholder `["0.5","0.5"]`. The published row cites
market **6036989**, whose `groupItemTitle` is **`Match Winner`** and whose
`sportsMarketType` is `moneyline`. Verifier rule **D16** gates this and passes.

## 2. Irregularities found while verifying (all non-blocking, all published on *Flagged*)

| Ref | What is wrong | Evidence | Disposition |
|---|---|---|---|
| **V25.1** | **The Polymarket source record's `start_utc` is the market's `endDate` (close time), not the kickoff.** For `lol-rb-mr-2026-10-27` the payload records `start_utc 2026-10-27T22:00:00Z` and therefore `start_delta_hours 5.0`. The market's own `gameStartTime` is `2026-10-27 16:00:00+00` and `eventStartTime` `2026-10-27T16:00:00Z`; `endDate` is `22:00Z`. `scripts/fetch_markets.py` (≈line 544) deliberately overwrites `end` with `endDate` and passes it to `_record()` as the start. Consequence: `start_delta_hours` is meaningless for Polymarket rows, and the delta cannot be used to detect a genuine schedule disagreement on them. | [market 6036989 JSON](https://gamma-api.polymarket.com/markets/6036989) vs the payload row | **Flagged, not fixed here.** Exact fix: prefer `mk["gameStartTime"]`/`ev["eventStartTime"]` and fall back to `endDate`, plus a unit test in `verification/test_entity_and_books.py`. Left to a session that can run the live pipeline end-to-end on the change, because `_dedup_key()` keys on `start_utc[:10]` and a careless change could merge two different fixtures. |
| **V25.2** | **Hotspawn and Polymarket disagree by 1 hour on the LGC Rising kickoff.** Hotspawn's epoch timestamp (authoritative for the pick lock) says 2026-10-27 **17:00 UTC**; Polymarket's description says "initially scheduled for October 27, 2026 at 12:00 PM ET" and its `gameStartTime` says **16:00 UTC**. 12:00 EDT is 16:00 UTC, so Polymarket is self-consistent and Hotspawn differs. | [Polymarket market 6036989](https://gamma-api.polymarket.com/markets/6036989) · [Hotspawn lobby](https://play.hotspawn.com/lol-pickems) | Upstream data. Our row keeps Hotspawn's time by rule (it governs the lock); recorded here because it is a real 1-hour disagreement, not a parsing artefact. |
| **V25.3** | **`Mental Rush vs Vitality Rising Bees` rests on a single production feed** (`MARKET_SINGLE`, Polymarket, dispersion 0.0). Two *non-production* sources now independently corroborate it — OddsDigger's books at 64.8% VRB (`research/betting-sources.md` §26.2) and eGamersWorld's LGC board at ≈66% (§19.2) — but neither is wired into the pipeline, so the row stays Medium confidence. | §26.2 links | No change; disclosed. |
| **V25.4** | **The 53 `MODEL_ELO_STANDINGS` rows were *not* independently re-read this session.** The Leaguepedia Cargo API answered `{"error":{"code":"ratelimited"}}` when queried for `Standings` on `Prime League 3rd Division/2027 Season/Fall Split`, and the human-readable page paginates 19 chunks deep. The records quoted in the rows' evidence (e.g. `AceGaming Hearts 0-3` vs `Emperors Bremen 2-1`) are therefore **not confirmed by this session**. | [Cargo query attempted](https://lol.fandom.com/api.php?action=cargoquery&tables=Standings&fields=Standings.Team,Standings.WinSeries,Standings.LossSeries&where=Standings.OverviewPage%3D%22Prime+League+3rd+Division%2F2027+Season%2FFall+Split%22&format=json) | **Left blank rather than assumed.** CI still verifies that every cited tournament page exists (`verification/check_source_pages.py`) and that every model row resolves to a competition-specific page (`verification/check_leaguepedia_coverage.py`); those checks pass. A session with a non-throttled IP should re-read the three sample rows. |
| **V25.5** | The lobby header counter (`This week 185 matches`, tier filter `All tiers (234)`) still does not reconcile to any definition Hotspawn publishes. Our own reconciliation (`lobby_lol_listed 236` at generation, `lobby_upcoming 156`, `lobby_past_not_priced 80`) is computed from the fixtures API and is internally consistent, but the header figure itself remains unverified. Flagged since 2026-10-23. | [Hotspawn lobby](https://play.hotspawn.com/lol-pickems) | Unverified upstream counter; never used in data. |

## 3. Fixture coverage re-checked against the live lobby

| Check | Value | Source |
|---|---|---|
| Live lobby tier filter at 14:0x UTC | `All tiers (234)`, header `This week 185 matches` | [play.hotspawn.com/lol-pickems](https://play.hotspawn.com/lol-pickems) |
| Payload `coverage_reconciliation` (generated 10:41Z) | `lobby_lol_listed 236` · `lobby_upcoming 156` · `lobby_past_not_priced 80` · `lobby_upcoming_missing_from_priced []` · `priced_not_in_lobby []` | `docs/data/picks.json` |
| Verifier **D21** | PASS — every upcoming lobby fixture is priced; no excluded fixture is priced (lobby upcoming 156 = priced 156, missing 0, extra 0, excluded 9, leaked 0) | `scripts/verify_site.py` |

The lobby's 234 vs our 236 is a ~3.5-hour gap in a list that changes as matches start and
finish; both counts include played fixtures, and only the *upcoming* subset is priced. The
tournament filter on the live lobby lists 29 competitions; the 12 that carry upcoming
fixtures are exactly the 12 in the payload's per-tournament tally.

## 4. Suites run on this commit

| Check | Result |
|---|---|
| `scripts/verify_site.py --leaguepedia-schedule data/diag` | **44 PASS · 0 FAIL · 1 WARN** (WARN = D18, the stale 2026-10-21 Leaguepedia diagnostic snapshot, by design) |
| `verification/test_verifier.py` | 45/45 |
| `verification/test_dom_contract.py` | 7/7 |
| `verification/test_entity_and_books.py` | 17/17 |
| `verification/test_standings_model.py` | ALL PASS |
| `verification/test_line_probe.py` (new this session) | 29/29 |
| `audit/test_model.py` | 23/23 |
| `verification/check_dom_contract.py` | PASS (7 pages) |

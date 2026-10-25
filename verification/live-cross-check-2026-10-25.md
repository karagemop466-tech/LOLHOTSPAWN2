# Live cross-check of the published payload — 2026-10-25 (session `arena/e5e9f360`)

Independent re-read of the sources behind the payload that `main` published at
**2026-10-25T14:29:06Z** (`docs/data/picks.json`, schema 3, 156 fixtures · 156 resolved ·
0 unresolved · 9 rows with an external betting line · 147 rows priced by our own model).

Every number below was read from the source's own live endpoint/page on **2026-10-25 between
14:35Z and 15:55Z** from outside CI (a different network path than the GitHub runner uses),
so it is an independent check rather than a re-read of our own cache. Nothing here was inferred:
where a value could not be read, the row says **UNVERIFIED**.

---

## 1. Unibet (Kambi) — all 8 priced rows re-read from the book's own feed

Feed used by production (`ub`, market GB):
<https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=GB&useCombined=true>
Second feed in the same rotation (`ubca`, market ZZ) re-read as a control:
<https://eu-offering-api.kambicdn.com/offering/v2018/ubca/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=ZZ&useCombined=true>

Both feeds returned **exactly 8 League of Legends events**, every one of them in the group
`World Championship` (path `Esports › League of Legends › World Championship`). No Prime League,
Tunisian Super League, RIVALS LEAGUE, 4 Nations, Arabian League, Komplettligaen, LigaGG/CELOL or
LCP event exists on either feed. Kambi publishes odds ×1000.

| Fixture | Match (row) | Kambi event | Kambi `start` (live) | Live decimals (home/away) | Payload decimals (team1/team2) | Agree? | Kambi price `changedDate` |
|---|---|---|---|---|---|---|---|
| 1075817 | Invictus Gaming vs Hanwha Life Esports | [1029621111](https://www.unibet.com.au/betting/sports/event/1029621111) | 2026-10-25T17:00:00Z | HLE 1.29 / IG 3.30 | 3.30 / 1.29 | ✅ exact | 2026-10-25T11:57:49Z |
| 1075816 | Top Esports vs G2 Esports | [1029621110](https://www.unibet.com.au/betting/sports/event/1029621110) | 2026-10-25T18:00:00Z | TOP 2.08 / G2 1.67 | 2.08 / 1.67 | ✅ exact | 2026-10-25T11:49:25Z |
| 1075819 | Dplus KIA vs Movistar KOI | [1029621119](https://www.unibet.com.au/betting/sports/event/1029621119) | 2026-10-25T19:00:00Z | DK 1.27 / MKOI 3.45 | 1.27 / 3.45 | ✅ exact | 2026-10-25T13:15:28Z |
| 1075818 | Gen.G vs LYON | [1029621112](https://www.unibet.com.au/betting/sports/event/1029621112) | 2026-10-25T22:00:00Z | Gen.G 1.07 / Lyon 7.50 | 1.07 / 7.50 | ✅ exact | 2026-10-25T12:03:37Z |
| 1075821 | T1 vs CTBC Flying Oyster | [1029621121](https://www.unibet.com.au/betting/sports/event/1029621121) | 2026-10-26T17:00:00Z | T1 1.12 / CFO 5.40 | 1.12 / 5.40 | ✅ exact | 2026-10-25T06:38:31Z |
| 1075820 | Karmine Corp vs Bilibili Gaming | [1029621120](https://www.unibet.com.au/betting/sports/event/1029621120) | 2026-10-26T18:00:00Z | KC 2.85 / BLG 1.38 | 2.85 / 1.38 | ✅ exact | 2026-10-25T06:38:24Z |
| 1075822 | LØS vs Team Secret Whales | [1029621122](https://www.unibet.com.au/betting/sports/event/1029621122) | 2026-10-26T19:00:00Z | LØS 2.60 / TSW 1.44 | 2.60 / 1.44 | ✅ exact | 2026-10-25T06:46:03Z |
| 1075823 | Team Liquid vs Anyone's Legend | [1029621123](https://www.unibet.com.au/betting/sports/event/1029621123) | 2026-10-26T22:00:00Z | TL 2.80 / AL 1.40 | 2.80 / 1.40 | ✅ exact | 2026-10-25T06:53:47Z |

**8 of 8 agree to the cent.** Child boards were present on four of these events
(`Map Handicap` and `Total Maps`, e.g. DK −1.5 maps 2.00 / +1.5 1.71, and Total Maps Over 2.06 /
Under 1.68 at 2.5) and none of them reached the payload — `_select_unibet_offer()` in
`scripts/fetch_markets.py` only accepts the `Match Odds` (`betOfferType.id == 2`) board, which is
what verifier check **D20** enforces. Confirmed by re-reading the row data, not by trusting the code
comment.

## 2. Polymarket — its own hub lists exactly the 9 markets we price

* LoL hub read at ~14:37Z: <https://polymarket.com/esports/league-of-legends> → **"LoL (9)"**,
  split **LGC Rising (1)** and **Worlds (8)**. Our payload has exactly 9 rows with a Polymarket
  source (8 Worlds + 1 LGC Rising), so no open LoL market on Polymarket is being missed by the
  `tag_slug=league-of-legends` filter in `scripts/fetch_markets.py`.
* Live hub prices vs the payload's de-vigged Polymarket probability (hub read 14:37Z, payload
  generated 14:29Z — drift is expected and is *not* treated as a discrepancy):

| Fixture | Hub price (¢) | De-vigged | Payload `prob_team1` | Δ |
|---|---|---|---|---|
| 1075816 Top Esports vs G2 Esports | TES 48 / G2 53 | 0.4752 | 0.4750 | 0.0002 ✅ |
| 1075817 Invictus Gaming vs Hanwha Life | HLE 74 / IG 27 | 0.2673 (IG) | 0.2650 (IG) | 0.0023 ✅ drift |
| 1075819 Dplus KIA vs Movistar KOI | DK 79 / MKOI 22 | 0.7822 | 0.7850 | 0.0028 ✅ drift |

* `public-search?q=prime league` (<https://gamma-api.polymarket.com/public-search?q=prime%20league>)
  returns Prime League **1st** Division markets only, and all of them **closed** (e.g.
  `lol-big1-g2nord-2026-08-27`, endDate 2026-08-27, volume $901,960). Polymarket does not list
  PRM 2nd or 3rd Division, so it cannot price any of our 147 model-only rows.

## 3. Pinnacle and Bovada — read by CI, not by this pass

* Pinnacle's guest API answers **HTTP 401 `No authorization token provided`** without the
  `x-api-key` header (<https://guest.api.arcadia.pinnacle.com/0.1/sports/12/leagues?all=true>,
  re-read 15:05Z), so its 8 rows could not be re-read from this network path. CI's own run of the
  same feed reported `status: ok, count: 8` at 14:29:06Z (`sources_status` in the payload).
  **UNVERIFIED independently in this pass**; the payload's Pinnacle decimals are however
  re-derived from the decimals the row cites by auditor rule **R4** (24/24 conversions exact).
* Bovada's coupon endpoint returned an empty object (`{}`) to this network path at 15:10Z
  (<https://www.bovada.lv/services/sports/event/coupon/events/A/description/esports/league-of-legends?marketFilterId=def&preMatchOnly=true&lang=en>),
  while CI read `status: ok, count: 8` at 14:29:06Z. Recorded as **UNVERIFIED from this path**,
  not as a defect: an empty body over a proxy is not evidence about the book.

## 4. Hotspawn lobby — the fixture list the payload claims to mirror

Lobby re-read at ~14:35Z: <https://play.hotspawn.com/lol-pickems>

* Header: **"This week 185 matches this week"**; tier filter **"All tiers (234) · A (1) · C (44) ·
  D (8) · S (11)"**; the tournament filter lists 29 competitions totalling **234**.
* The payload's own reconciliation says `lobby_lol_listed: 234`, `lobby_upcoming: 156`,
  `lobby_past_not_priced: 78`. **156 + 78 = 234**, i.e. the lobby's own total is fully accounted
  for by "priced upcoming" + "already played". This is the same assertion CI enforces as verifier
  check **D21**.
* Per-competition comparison (lobby filter count vs priced rows): PRM 3rd Division 60/60,
  PRM 2nd Division 36/36, Worlds 2026 Main Event 8/8, Komplettligaen 2026 Autumn Playoffs 3/3,
  LCP 2027 Promotion 3/3, LGC Rising 2026 Playoffs 1/1, Tunisian Super League 24 listed → 20 priced,
  RIVALS LEAGUE Season 2 24 → 14, Arabian League 2nd Division 8 → 4, 4 Nations 5 → 4,
  LigaGG CELOL A Playoffs 4 → 2, LigaGG CELOL B Playoffs 3 → 1. The differences are part of the 78
  already-played fixtures; **this pass did not itemise those 78 card by card**, so the per-league
  difference is *not* independently itemised here — the union gate (D21) and the 156+78=234
  reconciliation are the checks that were re-verified.
* Crowd percentages on the lobby cards (e.g. Babos Gaming 15% / Hannover Esports e.V. 85%) are
  display-only in the payload and are **not** the published probability: our row for that fixture
  says 57.9% / 42.1%. Auditor rule **R7** measures this across all 147 model rows — mean
  |published − crowd| = **0.3672**, and **0 of 147** rows sit within 0.5 pt of the crowd number.

## 5. Row-by-row arithmetic audit of the same payload

`scripts/audit_rows.py` (new this session) re-derives each row's arithmetic from the numbers that
row cites, offline: **20 PASS · 0 FAIL · 0 WARN · 1 INFO over 156 rows**;
`verification/test_row_audit.py` proves all 21 rules fail on a payload that breaks them
(**32/32 negative self-tests**). Full table: [`verification/row_audit.md`](row_audit.md).

Highlights: 24/24 cited decimal prices re-convert to the probability published for that source
(R4); 9/9 market rows' consensus recomputes from their own sources — median with ≥3 books,
weighted mean otherwise (R5); `counts`, `coverage` and all 12 `league_breakdown` rows re-foot
against the rows they summarise (R9/R9b/R10); no cancelled fixture is priced (R12); every row
cites ≥1 https source and ≥1 source that is not Hotspawn (R8).

---

## 6. Irregularities found (published for review, none blocks the merge)

| ID | Irregularity | Evidence | Status |
|---|---|---|---|
| X1 | **Two rows carry a start-time warning the source no longer supports.** Rows 1075819 (Dplus KIA vs Movistar KOI) and 1075818 (Gen.G vs LYON) are flagged `START_TIME_DISAGREES_WITH_BOOKS` and four Oct-25 rows publish `time_spread_hours` of 1.0/3.0, all derived from Unibet start times recorded at 14:29Z (17:00Z for the 18:00Z fixture, 18:00Z for the 17:00Z fixture, 19:00Z for the 22:00Z fixture, 22:00Z for the 19:00Z fixture). Re-reading the *same Kambi event ids* at ~15:45Z on **both** feeds returns starts that agree with Hotspawn exactly (17:00 / 18:00 / 19:00 / 22:00 UTC), i.e. the upstream feed's start times moved, not our arithmetic. | Kambi feed links in §1; payload rows 1075816–1075819; auditor rules R15/R16 both **PASS**, which is what proves our arithmetic is internally consistent with the timestamps it cites | Flagged. Expected to clear on the next scheduled refresh (16:29Z) because the value is re-read live every run. If it persists, the flag wording should state that the disagreement is with the feed as read at generation time. |
| X2 | **`start_delta_hours` is unsigned.** `scripts/model.py` matches books to fixtures on `abs(delta)`, so a book whose start is *earlier* than Hotspawn's publishes a positive number (row 1075816: Unibet 17:00Z vs fixture 18:00Z → published `1.0`, not `-1.0`). The match page prints both timestamps beside the delta, so the direction is visible to a reader; the number itself is not wrong, but it cannot be read as "later". | `scripts/model.py` line with `delta_h = abs(...)`; payload rows above | Logged as a request to the session that owns `scripts/model.py` / `docs/assets/app.js` (both claimed by open PRs #67/#70/#71) — not edited here. |
| X3 | **108 of 156 rows carry Hotspawn's own placeholder tier string** `waiting for information` (upper-cased by `scripts/fetch_hotspawn.py` when the API returns no tier). The site renders it as "Tier not published" and never as a strength claim, and no tier is invented for those rows. | auditor rule **R11** (INFO): `WAITING FOR INFORMATION=108, C=36, S=11, A=1`; `docs/assets/app.js` `/^WAITING/i` branch | Verified as handled; recorded so the string is not mistaken for data. |
| X4 | **Behind 10 rows the Elo rating was built in a different competition than the fixture.** A team's rating follows its most recent recorded series wherever it was played: row 1079054 (The Bandits Prime vs VfB eSports, PRM 2nd Division, 50.2/49.8, Low) rests partly on a `Kanji Cup 2026` record for one side (8 games in 365d vs 51 for the other) and row 1080934 (JSK Esports vs Olympique Mnihla, Tunisian Super League, 57.4/42.6, Low) on an `Arabian League/2026 Season/Spring Split` record. Both carry `CROSS_LEAGUE_MODEL`. Across all 156 rows, **236 team-sides** have their most recent series in another competition than the fixture they appear in. The *citations* are unaffected — **0 of 156 rows** link a Leaguepedia page other than their own tournament page (checked by comparing every row's `sources[].url` title with its `leaguepedia_page`). | payload rows 1079054, 1080934, 1075821; `model.teamN_recent_competition` / `model.cross_league` | Disclosed on the row and on the Unresolved page; no change made. |
| X5 | **Per-league lobby differences were not itemised card by card** in this pass (see §4). | this file §4 | Open item for the next verification pass; the union gate D21 covers it in CI. |

### Checked and found clean (recorded so it is not re-investigated)

* **No row cites a foreign league page.** All 210 `lol.fandom.com` citations were compared with the
  tournament page of the row that carries them: 0 mismatches. (An earlier suspicion that row
  `1075758`, Rich Gang vs LOOKSMAXXER, cited a Komplettligaen page is **not** an irregularity: its
  cited page is `Prime_League_3rd_Division/2027_Season/Fall_Split`, its own league. Komplettligaen
  appears only inside `model.team1_recent_competition`, which is where that team last played — see X4.)
* **Kambi child boards never leak into the payload.** Four of the eight events also publish
  `Map Handicap` and `Total Maps` boards; none of their prices appear in any row (verifier D20).
* **The lobby total reconciles.** 234 listed = 156 priced upcoming + 78 already played.

### What was checked and could not be verified (left blank on purpose)

| Item | Why it is blank |
|---|---|
| Pinnacle's 8 rows re-read from the live guest API | HTTP 401 without the `x-api-key` header from this network path (CI holds the key). |
| Bovada's 8 rows re-read from the live coupon JSON | empty body (`{}`) over this network path; CI read 8 events at 14:29:06Z. |
| Itemised list of the 78 already-played lobby fixtures | the lobby page renders them without a machine-readable id in the fetched HTML; not itemised rather than guessed. |
| Any bookmaker line for the 147 model-only fixtures | none exists on any source measured today — see `research/low-tier-sweep-2026-10-25.md`. |

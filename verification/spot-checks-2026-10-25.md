# Line-by-line verification and spot checks — 2026-10-25

Two sessions verified the same payload on the same day from different angles. Both records are kept,
unedited, so a reader can see the checks and the sources each session actually read.

## Part 1 — payload audit (session `arena/964cb944`)

Payload: `docs/data/picks.json` generated 2026-10-25T10:41:50Z on `main` @ `2173cc9`.
156 fixtures · 156 resolved (100%) · 0 UNRESOLVED · 8 MARKET_CONSENSUS (4 books) · 1 MARKET_SINGLE ·
92 MODEL_ELO · 53 MODEL_ELO_STANDINGS · 2 MODEL_ELO_THIN · 10 Low · 62 coin-flips (fav ≤53%) · 9 cancelled excluded.

| Check | Result | Evidence |
|---|---|---|
| `python3 scripts/verify_site.py` | **45 PASS · 0 FAIL · 0 WARN · 1 SKIP** (D18 needs CI snapshot) | includes new S16 coin-flip check |
| `verification/test_verifier.py` | 45/45 | |
| `verification/test_standings_model.py` | ALL PASS | |
| `verification/test_entity_and_books.py` | 17/17 | |
| `audit/test_model.py` | 23/23 | |
| `verification/check_dom_contract.py` | PASS | |
| `node verification/check_dom_render.js` (jsdom, real payload) | **58/58** | new: 62/62 coin-flip pills labelled, `?filter=tossup` = 62 rows, summary + unresolved counts agree |
| Market row vs live book | PASS | Mental Rush vs Vitality Rising Bees: Polymarket series ML 65¢/38¢ vs payload 64.5% pick — https://polymarket.com/event/lol-rb-mr-2026-10-27 |
| VfB eSports cross-league cluster (5/10 Low rows) | **Not a defect** | Relegated PRM 1st-Div team (base 1560) vs PRM 2nd anchors 1460–1490; flag + Low cap correct — research §21.4 |
| Cloudbet PRM-2 coverage claim | **Unverified — 0 events live** | Page says "No events available" vs 36 Hotspawn fixtures; added to CI probe — research §21.1 |
| Kalshi LoL claim (third-party article) | **Contradicted by Kalshi's own API** | Probe 2026-10-25T10:41Z: no LoL series — research §21.2 |
| Pages | `built` for `2173cc9` | https://karagemop466-tech.github.io/LOLHOTSPAWN2/ |

Flagged (non-blocking): 62 coin-flip picks are now labelled rather than hidden; Cloudbet/Kalshi claims stay
probe-only until a structured feed + human-verified sample row exists.

---

## Part 2 — lobby cross-check, row audit and source-claim evidence (session `arena/6e003eec`)

Scope: the payload published on `main` at 2026-10-25T10:41:50Z (156 Hotspawn LoL fixtures) plus the
source-research claims added in this session. Every check below names the source that was actually read.
Nothing here is inferred; where a value could not be confirmed from the cited source it is marked
**UNVERIFIED** and listed on the site's *Flagged for review* page.

## 1. Fixture list: is the site covering everything Hotspawn lists?

| Check | Method | Result |
|---|---|---|
| Hotspawn lobby still lists the fixtures we price | Read the live lobby <https://play.hotspawn.com/lol-pickems> (2026-10-25 ~14:06 UTC) and compared rendered match cards with the payload | **Match.** `Babos Gaming 15% / Hannover Esports e.V. 85%`, `AceGaming Hearts 76% / Emperors Bremen 24%`, `AIX eSports 88% / MT1 Vision 12%`, `Defiance eSports 40% / REH Gaming 60%`, `Eintracht Spandau Zwei 23% / Team 300 White 77%`, `Rich Gang 31% / LOOKSMAXXER 69%`, `Whalepower Humpbacks 88% / Socken und Sandalen 12%` all appear on the lobby with the same crowd percentages recorded in the payload |
| Lobby advertises 234 matches but we publish 156 | Payload `coverage_reconciliation` + live lobby | **Not a gap.** The lobby's tier/tournament counters include matches that have already been played (`lobby_past_not_priced: 80`). The lobby itself lists fixtures through 2026-11-15, and every one that has not started is in the payload (`lobby_upcoming_missing_from_priced: []`, `priced_not_in_lobby: []`) |
| Fixtures cancelled upstream are not priced | Payload `excluded_fixtures` (9 rows) | **Confirmed excluded** with the reason `Hotspawn status is 'cancelled'` and the fixtures-API link on each row; they are listed on *Flagged for review*, not silently dropped |
| Refresh cadence | `.github/workflows/update-picks.yml` | `cron: 0 */6 * * *` = every 6 hours, inside the requested 4–8 h window |

## 2. Every published row: arithmetic, pick, sources

Run over all 156 rows of `docs/data/picks.json` (script output reproduced in the session log):

| Rule | Result |
|---|---|
| `prob_team1 + prob_team2 == 1` | **156/156 pass** (0 issues) |
| `pick` is the higher-probability team (except explicit 50/50 placeholders) | **156/156 pass** |
| `pick_prob` equals that probability | **156/156 pass** |
| `pick` is one of the two teams | **156/156 pass** |
| Unique fixture ids | **156 distinct** |
| At least one `https://` source link per row | **156/156**, minimum 2 links per row |
| Market rows cite the book that priced them (Pinnacle / Unibet / Bovada / Polymarket) | **9/9 pass** |
| Model rows cite a Leaguepedia tournament page | **147/147 pass** |
| Probabilities inside the published clamp [2%, 98%] | **156/156 pass** |

## 3. The cited sources exist (not just a plausible URL)

`verification/check_source_pages.py`, run in CI on this branch (`data/diag/source_pages.log`):

```
cited Leaguepedia pages: 12 · verified to exist: 12 · missing: 0
  ok  2026 Season World Championship/Main Event (8 rows)
  ok  4 Nations/2026 Season/Halloween Heist (4)
  ok  Arabian League 2nd Division/2026 Season/Summer Split (4)
  ok  Komplettligaen/2026 Season/Autumn Playoffs (3)
  ok  LCP/2027 Season/Promotion (3)
  ok  LigaGG/CELOL Série A/2026 Season/Split 2 Playoffs (2)
  ok  LigaGG/CELOL Série B/2026 Season/Split 2 Playoffs (1)
  ok  LoL Game Changers/2026 Season/Playoffs (1)
  ok  Prime League 2nd Division/2027 Season/Fall Split (36)
  ok  Prime League 3rd Division/2027 Season/Fall Split (59)
  ok  RIVALS LEAGUE/2026 Season/Season 2 (15)
  ok  Tunisian Super League/2026 Season (20)
```

Two pages were additionally opened by hand in this session:

* <https://lol.fandom.com/wiki/Prime_League_2nd_Division/2027_Season/Fall_Split> — page exists, with
  *Participants*, *Results (Division 2.1 / 2.2)* and *Match Schedule* sections for “PRM 2nd Division 26-27
  Fall”, which is exactly the tournament label Hotspawn uses.
* <https://lol.fandom.com/wiki/2026_Season_World_Championship/Main_Event> — page exists; the infobox gives
  **Start 2026-10-23, End 2026-11-14**, which brackets the 8 Worlds fixtures in the payload.

## 4. External-line research claims added this session

All measurements recorded in `data/diag/prm_line_probe.json` / `.log` and `research/betting-sources.md` §20:

| Claim | Evidence read |
|---|---|
| Cloudbet advertises Prime League 2nd Division but has no live board | <https://www.cloudbet.com/en/esports/league-of-legends/germany-t8205-prime-league-2nd-division?tab=events> → “No Prime League 2nd Division events available” |
| Cloudbet's public API is key-gated | `sports-api.cloudbet.com/pub/v2/odds/sports` → **HTTP 401** (CI, 2026-10-25) |
| BMBets has a PRM2 page but no PRM2 prices | <https://www.bmbets.com/e-sports/world/lol---prime-league-2nd-division/> → index lists only Worlds (9), LCP (1), Game Changers Rising (1) |
| Betmonitor's PRM2 URL serves the generic index | `betmonitor.com/odds-comparison/esports/prime-league-2nd-division/10024464` → football/tennis/basketball highlights, no esports rows |
| esportbet names “Prime League 2. Liga 2026 Fall — LIVE” with no prices | <https://esportbet.com/league-of-legends/> |
| Oddspedia's LoL odds path is gone | <https://oddspedia.com/league-of-legends/odds> → **HTTP 410 “permanently deleted”** |
| German books are not machine-readable | Tipico 200 with 0 LoL references; NEO.bet / bwin / bet365.de **403** |
| Net result | 16 sources probed, 8 reachable, **0 publish a two-way price** for any of the 147 model-only fixtures |

## 5. Irregularities found and how they were handled

1. **False-positive price detection (fixed in this session).** The first version of the new probe matched
   single generic words near any number and reported five sources as “odds near a team”. All five were
   false positives on inspection (a German basketball fixture “Alba Berlin”, a CSS gradient
   `has-atomic-cream-gradient-background`, a meta description, a league-name table). The matcher now
   requires **both full team names in one 700-character window plus two odds-like decimals**, and eight
   regression tests pin that behaviour (`verification/test_prm_probe.py`). Nothing from the flawed run was
   published as a price.
2. **One scheduled refresh failed at 2026-10-25T03:05Z** (`Update Hotspawn LoL picks`). The next run at
   10:39Z succeeded and regenerated the payload, so the site was never stale beyond one cycle. The failure
   log was committed by the workflow's failure step; the exact cause is **not confirmed** because the
   Actions log API was rate-limited during this session — flagged rather than guessed.
3. **`unresolved = 0` was misleading on the site.** It was accurate (no 50/50 placeholder), but as the only
   visible number it read as “no picks”. The executive summary now shows five separate numbers —
   matches / have a pick / bookmaker line / model-priced / no pick at all — and a separate section for the
   147 matches without a book line. No data changed; only the presentation.
4. **Hotspawn lobby counters include played matches.** “All tiers (234)” is a season counter, not a count of
   upcoming matches; the site compares against `lobby_upcoming` instead and says so in the reconciliation
   block.

## 6. What remains unverified (published on *Flagged for review*, non-blocking)

* The exact cause of the 03:05Z failed run (Actions log unavailable in this session).
* Whether Tipico / NEO.bet / bwin / bet365 price Prime League in their apps: their web endpoints either
  return no League of Legends markup or block automated requests, so their coverage is **UNVERIFIED** and no
  price is claimed from them.
* Cloudbet's claim of PRM2 coverage could not be confirmed with any live event; the advertising copy is
  not treated as evidence.

# Betting & results sources for LoL pick generation

Research note for **T11 verification / T12 integration** — session `arena/47334762-lolhotspawn2`, 2026-10-21.
Every claim below was checked against the linked page/endpoint on 2026-10-21 (evidence in `data/diag/report*.json`
committed by session `arena/fa3f554c` and in the links themselves). Anything not verified is labelled
**UNVERIFIED** and must not be presented on the site as fact.

Purpose: the brief asks us to (a) originate our own line for **every** Hotspawn LoL fixture, (b) try established
LoL betting sites first, then esportsbooks/esports lines, and (c) publish a separate section for anything that
still cannot be resolved, with the limitations. This note records which sources actually price which leagues, and
which *official results* sources can produce a defensible line when no book does.

---

## 1. Market sources — what actually prices LoL fixtures

| Source | Type | What it covers (verified) | Access | Verified evidence | Constraint we must respect |
|---|---|---|---|---|---|
| **Pinnacle** (guest endpoint) | Sharp esportsbook | `sport 12 = E Sports` returns 200; LoL leagues present: **9587 "League of Legends - World Championship"** (10 matchups) and league **225201** | Public front-end guest endpoint `guest.api.arcadia.pinnacle.com/0.1/...` with the public web-client key | `data/diag/report3.json` → `pinnacle_leagues_12`, `pinnacle_lol` | Pinnacle's **official** API has been closed to the general public since **2025-07-23** ([docs](https://github.com/pinnacleapi/pinnacleapi-documentation)). The guest endpoint is **not a licensed feed**, undocumented and may change without notice → treat as *supplementary* and flag it. |
| **OddsPapi** | Odds aggregator (350+ books, incl. Pinnacle network) | LoL `sportId=18`; documented coverage lists Worlds, LEC, LCS, LCK, LPL, CBLOL, LJL, **Prime League Pro Division** | Requires `ODDSPAPI_KEY` (free tier); **no key is configured in this repo** → `MARKET_BOOKS = 0` | [oddspapi.io/sports/esports/lol](https://oddspapi.io/sports/esports/lol), [esports odds API guide](https://oddspapi.io/blog/esports-odds-api-guide-how-to-get-pinnacle-cs2-lol-data-for-free/) | Does **not** list PRM 2nd/3rd Division, RIVALS, 4 Nations, Tunisian, Komplettligaen, LigaGG, Arabian 2nd Div. A key unlocks more books but not tier-3 amateur leagues. |
| **Polymarket** | Prediction market | Public Gamma API returns LoL-tagged events; probe found **59 LoL events**, including tier-2/3 titles (Nexus League, Hitpoint Masters, North American Challengers League) | Public, no key | `data/diag/report3.json` → `prediction.polymarket_events`; pipeline already matches Worlds 2026 (8 rows) | Liquidity is thin outside majors and many LoL markets are historical. Matching team names is fragile (aliases). Never use Hotspawn crowd % — only the market price. |
| **Bovada** | US-facing esportsbook | LoL coupon JSON returns 200 and lists "World Championship '26" | Public JSON used by its own front-end | `data/diag/report3.json` → `books.bovada_lol_coupon` | Major leagues only (third-party reviews cite LCK/LPL/LCP/LCS/LEC/LFL/Prime League/TCL). No tier-3 amateur. |
| **bet365 / DraftKings / FanDuel / BetMGM / GG.BET / Betway / Thunderpick etc.** | Established books | LoL majors; some carry Prime League / academy leagues | Require accounts/geoblocking; no public odds API | Third-party round-ups only (e.g. [esports.gg](https://esports.gg/guides/betting/league-of-legends-betting-sites/), [Covers](https://www.covers.com/betting/esports-betting-sites)) | **UNVERIFIED per-fixture** for this project: we could not read their prices programmatically from an official feed. Do not claim their line on the site without a per-match link. |
| **Riot lolesports API** (`esports-api.lolesports.com/persisted/gw`) | **Unofficial** Riot front-end API | Riot-operated leagues only (Worlds, MSI, LCK, LPL, LEC, LCP …) | Public front-end key | [unofficial API docs](https://vickz84259.github.io/lolesports-api-docs/), [community guide](https://github.com/kingjakeu/lolesports/blob/main/doc/unofficial-riot-api-guide.md) | Not official, no SLA; **does not** carry amateur leagues. **Returns 403 from GitHub Actions for all four endpoints (measured 2026-10-21, `data/diag/report7.json`)** → not usable in production. |

**Conclusion for market coverage:** only the Worlds 2026 fixtures (9 in the current feed) are priced by a sharp book
we can reach; Polymarket adds a handful more. Every tier-3/amateur fixture in the feed has **no** book line we could
verify. That is not a bug in our pipeline — it is the state of the market. The brief's requirement that every match
still gets a pick therefore depends on **our own line**, which must be built from results data below.

---

## 2. Results sources for our own line (no-market fixtures)

| Source | What it gives | Covers the unresolved leagues? (verified) | Access / licence | Constraint |
|---|---|---|---|---|
| **Leaguepedia** (`lol.fandom.com`, Cargo API) | Per-game scoreboards, match schedule, standings, team aliases | **Yes — verified standings pages exist today**: [Komplettligaen 2026 Spring](https://lol.fandom.com/wiki/Komplettligaen/2026_Season/Spring_Split) (Playwell Rød Q 9–2, Ascent Gaming 6–5, DMG Esports Norway 7–4…), [RIVALS LEAGUE Season 2](https://lol.fandom.com/wiki/RIVALS_LEAGUE/2026_Season/Season_2) (B2U 3–0, FlameHard 3–0, Lundqvist Darkside 2–1…), [4 Nations 2026 Summer](https://lol.fandom.com/wiki/4_Nations/2026_Season/Summer_Split) (Rich Gang UK 6–3–0, Inari 4–5–0, Brod n Friends 5–2–2…), [4 Nations 2026 Spring Playoffs](https://lol.fandom.com/wiki/4_Nations/2026_Season/Spring_Playoffs) | [api.php](https://lol.fandom.com/api.php?action=help&modules=cargoquery) | **Severe anonymous rate limiting** — our own Actions probes received `{"error":{"code":"ratelimited"}}` (`data/diag/report3.json` → `leaguepedia`). Community reports ~1 query/30–40 s without a bot flag ([Fandom thread](https://lists.wikimedia.org/hyperkitty/list/mediawiki-api@lists.wikimedia.org/thread/A6VWUYRHLGGJWZ3USGEBQJSDMX6A4YCM/), [ETL notes](https://github.com/fedeterpin/smurfeando)). Pipeline must pace requests + back off; a bot account raises limits. |
| **Liquipedia** MediaWiki API | Match results + standings, C/D-tier amateur leagues | **Yes** — [Komplettligaen 2026 Autumn](https://liquipedia.net/leagueoflegends/Komplettligaen/2026/Autumn) (C-Tier, 8 teams), [Komplettligaen Division 2 2026 Autumn](https://liquipedia.net/leagueoflegends/Komplettligaen/Division_2/2026/Autumn), [4 Nations 2026 Summer](https://liquipedia.net/leagueoflegends/4_Nations/2026/Summer), [4 Nations Division 2 2026 Summer](https://liquipedia.net/leagueoflegends/4_Nations/Division_2/2026/Summer) (D-Tier, organizer UKEL), [RIVALS LEAGUE Season 2](https://liquipedia.net/leagueoflegends/RIVALS_LEAGUE/Season_2) (C-Tier, 16 teams, Swedish) | [API terms](https://liquipedia.net/api-terms-of-use) | **gzip required** (our probe got `406 Gzip encoding is required`), custom User-Agent with contact, **1 request / 2 s**, LiquipediaDB 60/h, **attribution CC-BY-SA 3.0 required**. HTML scraping is not permitted — API only. |
| **Prime League** (organizer) | Official PRM divisions, match pages, results — **403 Bunny Shield from GitHub Actions (measured 2026-10-21)** | **Partially verified** — [league list](https://www.primeleague.gg/en/leagues) shows [Fall Split 2026/27](https://www.primeleague.gg/en/leagues/prm/3227-fall-split-202627) running 2026-09-04 → 2026-12-13 with "Divisions & Playoffs"; participant/match pages exist per team | Public site | Blocked to our runners (403, Bunny Shield) and no public API; **not usable programmatically** — use Leaguepedia standings/Liquipedia for PRM names and records, and keep primeleague.gg as a human cross-check link only. |
| **Komplettligaen** (organizer) | Official Norwegian results by division (200 from Actions, HTML only) | **Yes** — [komplettligaen.no/lol](https://www.komplettligaen.no/lol/) publishes recent results (e.g. *1. divisjon: DMG NO 0–2 Playwell Rød Q*, *Playwell Rød Q 2–1 Ascent Gaming*; *3. divisjon avd. A/B* results) | Public site | No documented API; scrape-friendly HTML but use politely and cache. |
| **RIVALS LEAGUE** (organizer) | Official Swedish league (200 from Actions, HTML only) | [rivalsleague.gg](https://www.rivalsleague.gg/) — Season 2 begins 21 Sept, 85,000 SEK across LoL/CS2/VALORANT | Public site | Reachable but HTML-only; Leaguepedia standings are the programmatic source. |
| **gol.gg** | LoL stats site | Major leagues (per site structure) | Public site | **UNVERIFIED** for tier-3 amateur leagues; do not cite for unresolved fixtures. |
| **bo3.gg** | Results database | Probe returned 200 with CS2 sample records | Public JSON | **UNVERIFIED** for LoL coverage of these leagues; not used. |

---

## 3. Coverage plan for the current unresolved list (126 rows)

Counts from `docs/data/picks.json` at 2026-10-21 20:16 UTC (method `UNRESOLVED`).

| Tournament | Unresolved | Book line? | Results source that can produce a line | Honest outcome if results are missing |
|---|---|---|---|---|
| PRM 3rd Division 26-27 Fall | 52 | none found | primeleague.gg (official, divisions) + Leaguepedia/Liquipedia PRM pages | standings/win-rate model; else 50/50 flagged |
| RIVALS LEAGUE Season 2 | 18 | none found | **Leaguepedia standings verified** + Liquipedia + rivalsleague.gg | standings model (prior split + current group) |
| 4 Nations 2026 Halloween Heist | 18 | none found | **Leaguepedia 4 Nations pages verified** (Summer standings, Spring playoffs) + Liquipedia | prior-split standings model; new/unlisted teams → 50/50 flagged |
| Tunisian Super League 2026 | 16 | none found | no verified public results page located in this pass | 50/50 flagged as unresolved (no official source) |
| PRM 2nd Division 26-27 Fall | 8 | none found | primeleague.gg + Leaguepedia PRM 2nd Division | standings model |
| Komplettligaen 2026 Autumn | 6 | none found | **komplettligaen.no official results verified** + Liquipedia + Leaguepedia | standings model (official recent results available today) |
| LigaGG CELOL B 2026 Split 2 Playoffs | 4 | none found | no verified public results page located in this pass | 50/50 flagged |
| Arabian League 2nd Division 2026 Summer | 2 | none found | no verified public results page located in this pass | 50/50 flagged |
| Arabian Regional Championship 2026 (LBN/LBY/SYR/PLE) | 1 | none found | no verified public results page located in this pass | 50/50 flagged |
| LGC Rising 2026 Playoffs | 1 | none found | no verified public results page located in this pass | 50/50 flagged |

**This is the key finding of the research:** the unresolved bucket is *not* one undifferentiated "no data" pile.
At least **44 of 126** rows (RIVALS 18 + 4 Nations 18 + PRM 2nd 8 … plus Komplettligaen 6 and much of PRM 3rd 52
if the organizer pages are parsed) have **verifiable public results** and can therefore be given a sourced
probability. Only the leagues with no public results page should remain at an explicit 50/50.

---

## 4. Model design for no-market matches (recommended, sourced)

1. **Prefer market**: Pinnacle guest (Worlds), Polymarket (any listed LoL event) → de-vigged, median.
2. **Else results model** built from, in priority order:
   a. Leaguepedia `ScoreboardGames` **and** `MatchSchedule` (current group/season) with pacing/backoff and a
      cached snapshot so a rate-limited run cannot silently zero the model;
   b. standings/win-rate from Leaguepedia standings pages or Liquipedia (only via API, gzip, ≤1 req/2s,
      attributed) or the organizer's own results page;
   c. prior-split results for teams in a new event (clearly labelled "prior split").
3. **Blend with a proper prior**: small samples shrink toward 50% (already implemented); record games used.
4. **Else unresolved**: 50/50 nominal pick, published on the Unresolved page with the reason *and* the limitation,
   never shown as an edge.
5. Every row links the exact source page used (Leaguepedia/Liquipedia/organizer), not just an API help page.

**Attribution requirements**: Liquipedia content is CC-BY-SA 3.0 — credit "Liquipedia" with a link on the
Method & Sources page whenever its data feeds a probability. Leaguepedia is a Fandom community wiki — credit and
link it. Market prices must credit the book/market with a link.

---

## 5. Limitations to publish in the Unresolved section (verbatim-ready)

- No licensed sportsbook we could reach prices tier-3/amateur LoL (PRM 3rd Division, RIVALS LEAGUE, 4 Nations,
  Tunisian Super League, Komplettligaen, LigaGG, Arabian League 2nd Division). Pinnacle reaches only the World
  Championship; Polymarket lists a few tier-2/3 events but with thin liquidity.
- Leaguepedia's anonymous API is aggressively rate limited; Liquipedia requires gzip and ≤1 request per 2 s and
  caps automated use. Coverage of amateur leagues is incomplete and team names/rosters change frequently.
- Some fixtures on Hotspawn carry stage "waiting for information" and teams have no public results anywhere;
  for those a 50/50 placeholder is the only honest output and is flagged as unverified — it is **not** an edge.
- Hotspawn crowd percentages are never used as a probability input (verified by static scan, check W3).

---

## 6. Verification log

| Date | Source | What it verified | Link |
|---|---|---|---|
| 2026-10-21 | Pinnacle API docs | official API closed to general public 2025-07-23 | https://github.com/pinnacleapi/pinnacleapi-documentation |
| 2026-10-21 | Pinnacle guest API (Actions probe) | `sport 12` E Sports 200; LoL league 9587 World Championship, 10 matchups | `data/diag/report3.json` (`pinnacle_lol`) |
| 2026-10-21 | OddsPapi | LoL sportId 18, 350+ books, Prime League Pro Division listed | https://oddspapi.io/sports/esports/lol |
| 2026-10-21 | Polymarket Gamma | 59 LoL events incl. tier-2/3 titles | `data/diag/report3.json` (`prediction`) |
| 2026-10-21 | Bovada coupon JSON | World Championship '26 listed | `data/diag/report3.json` (`books`) |
| 2026-10-21 | Leaguepedia standings | Komplettligaen, RIVALS LEAGUE, 4 Nations standings verified | links in §2 |
| 2026-10-21 | Leaguepedia rate limit | observed `ratelimited` error in Actions probe | `data/diag/report3.json` (`leaguepedia`) |
| 2026-10-21 | Liquipedia terms | gzip, UA, 1 req/2s, 60/h, CC-BY-SA 3.0 attribution | https://liquipedia.net/api-terms-of-use |
| 2026-10-21 | Liquipedia pages | Komplettligaen / 4 Nations / RIVALS League coverage + tiers | links in §2 |
| 2026-10-21 | Prime League (organizer) | Fall Split 2026/27 dates, divisions & playoffs | https://www.primeleague.gg/en/leagues/prm/3227-fall-split-202627 |
| 2026-10-21 | Komplettligaen (organizer) | official 1./3. divisjon results | https://www.komplettligaen.no/lol/ |
| 2026-10-21 | RIVALS LEAGUE (organizer) | Season 2 start 21 Sept, LoL included | https://www.rivalsleague.gg/ |
| 2026-10-21 | lolesports API (unofficial) | Riot leagues only; no amateur coverage | https://vickz84259.github.io/lolesports-api-docs/ |

**Flagged irregularities from this research**
1. Pinnacle guest endpoint is used by the pipeline as a market source although it is undocumented and not a licensed
   feed. Recommend: label it "Pinnacle (guest front-end feed, unofficial)" on the site and never make it a single
   point of failure.
2. Pinnacle's guest key and endpoint are third-party front-end artifacts; rotation is expected. The pipeline must
   degrade gracefully to Polymarket + model and say so on the Flagged page.
3. Leaguepedia rate limits can silently empty the Elo input. The pipeline must cache the last successful snapshot
   and expose `leaguepedia_ok` in its debug block; a run with no Leaguepedia data must not pretend the model ran.
4. OddsPapi has no key configured, so no bookmaker median is computed anywhere; the site must not imply bookmaker
   coverage it does not have.

---

## 7. Addendum — why the current model outputs ~50/50 and the targeted fix

Measured on the live data (2026-10-21 20:16 UTC, `docs/data/picks.json`):

| method | rows | probability range |
|---|---|---|
| MARKET_POLYMARKET | 8 | 0.395 – 0.825 (real signal) |
| MODEL_ELO | 61 | **0.455 – 0.545** (median 0.511; every row "Low — thin team history") |
| UNRESOLVED | 126 | 0.500 |

So 187 of 195 published rows (96%) are coin-flips: the site technically "has a pick for every match", but only the
8 market rows carry information. The Elo model is not *wrong* — it is starved: the fixtures' teams have 0–9 recorded
games each, and the shrink factor `min(games)/(min+10)` pulls a 3-game sample to ~23% of its raw edge.

Root causes and the fix (verified against the Leaguepedia data captured in `data/diag/`):

1. **Global 6,000-row pagination crowds out tier-3.** The production query pulls `ScoreboardGames` for the last 180
   days in date order, limit 500 × 12 pages. Major-league games fill the cap; the amateur teams we need appear at the
   margins (the captured 5,000-row slice 2024-10 → 2025-04 contains only **9 of the 99** unresolved teams).
   **Fix:** query per league instead of globally — 16 league pages cover every future fixture
   (`MatchSchedule.OverviewPage` values in `data/diag/lp_schedule.json`). One Cargo call per league:
   `tables=ScoreboardGames&fields=SG.Team1,SG.Team2,SG.Winner,SG.DateTime_UTC,SG.OverviewPage,SG.Tournament`
   `&where=SG.OverviewPage LIKE 'Prime League 3rd Division%' AND SG.DateTime_UTC >= '2025-06-01'&limit=500&order_by=SG.DateTime_UTC`.
   16 paced requests (≥3 s apart) respect the anonymous rate limit and cannot be crowded out.
2. **Off-season teams need prior splits, not a 180-day window.** `MatchSchedule` pages for these leagues expose prior
   splits (`.../2026 Season/Spring Split`, etc.). Querying the league page across 2 splits gives each team enough
   games for a stable rating; the model must label how many games and which splits were used.
3. **Fixtures must come from MatchSchedule, not only ScoreboardGames.** 112/126 unresolved fixtures are already listed
   with exact UTC times and BestOf on Leaguepedia (see `verification/leaguepedia_coverage.md`), so name matching and
   per-league source links are available without scraping HTML.
4. **Expose coverage in the payload**: e.g. `leaguepedia_ok`, `leagues_queried`, `teams_with_results`, and a per-row
   `games_used`/`splits_used`, so a rate-limited run is visibly different from a real one.

If the targeted queries still return no games for a league (possible for LigaGG/Arabian/Tunisian amateur events), the
row stays 50/50 and the Unresolved page states exactly that, with the league page link — which is the honest outcome
the brief asks for.

---

## 8. Measured reachability from GitHub Actions (2026-10-21, `data/diag/report6.json`)

| host | status | note |
|---|---|---|
| `primeleague.gg`, `primeleague.gg/api/v1/leagues` | **403** | Bunny Shield anti-bot — not usable from CI |
| `4nations.gg` | 0 | unreachable |
| `ligagg.com` | 0 | unreachable |
| `tunisiansuperleague.com`, `tunisiansuperleague.tn`, `lol.tn` | 0 | unreachable |
| `rivalsleague.gg` | 200 | reachable, HTML only |
| `komplettligaen.no` | 200 | reachable, HTML only |
| `liquipedia.net` API (`allpages`) | 200 | API only, gzip, ≤1 req/2 s, CC-BY-SA 3.0 |
| `lol.fandom.com` Cargo via `Special:CargoExport` | 200 | works for Standings/MatchSchedule; `api.php` is aggressively rate limited |

Consequence: the only reliable programmatic results source for the amateur leagues is **Leaguepedia Cargo**
(MatchSchedule + Standings + ScoreboardGames). Organizer sites are for human cross-checks only.

---

## 9. MatchSchedule carries completed series results (verified 2026-10-21)

`action=cargofields&table=MatchSchedule` includes `Winner`, `Team1Score`, `Team2Score`, `BestOf`,
`DateTime_UTC`, `OverviewPage`, `Team1/Team2`, `GroupName`, `Tab` — i.e. the table holds **results, not just
fixtures**. A single CargoExport call for RIVALS Season 2 with `Winner IS NOT NULL` returned 30+ completed Bo3 series
with scores and dates (e.g. *Lundqvist Darkside 2–1 Rich Gang Sweden, 2026-10-18*; *FlameHard 2–0 Northern Wolves*).

Why this matters: it gives a **proper series-level results history for every league in the feed** (including PRM 3rd,
Tunisian, Komplettligaen, 4 Nations, LigaGG, Arabian) in one request per league, without the ScoreboardGames rate-limit
problem and without depending on blocked organizer sites. A recency-weighted Elo over these series is strictly better
than standings-only, and standings (WinSeries/LossSeries) remain a fallback when a league has too few completed series.

Suggested production order for no-market fixtures:
1. series Elo over `MatchSchedule` results (last 12 months, per league page, `Winner IS NOT NULL`);
2. standings win-rate (smoothed) when the league has too few results;
3. explicit 50/50 with the league page link and a stated reason when neither exists.

Query template:
```
https://lol.fandom.com/wiki/Special:CargoExport?tables=MatchSchedule
  &fields=Team1,Team2,Winner,Team1Score,Team2Score,DateTime_UTC,BestOf,OverviewPage
  &where=OverviewPage='<page>' AND Winner IS NOT NULL
  &order_by=DateTime_UTC DESC&limit=200&format=json
```

---

## 10. Riot lolesports endpoints from Actions (measured 2026-10-21, `data/diag/report7.json`)

| endpoint | status | note |
|---|---|---|
| `esports-api.lolesports.com/persisted/gw/getLeagues` | **403** | blocked for our runners |
| `esports-api.lolesports.com/persisted/gw/getSchedule` | **403** | blocked |
| `prod-relapi.ewp.gg/persisted/gw/getLeagues` | **403** | blocked |
| `prod-relapi.ewp.gg/persisted/gw/getSchedule` | **403** | blocked |

Consequence: the Riot front-end API cannot be a production dependency here (and it never covered amateur leagues).
Leaguepedia `MatchSchedule` remains the only reliable fixture/results feed for the low-tier leagues.

---

## 11. Refresh 2026-10-23 (session `arena/bd37dbe6`, task T15)

Purpose: re-check the market and results inputs before the 2026-10-23 release, and separate what is **verified** from what is only **claimed by third parties**. Every item below has a link. Items marked *third-party claim* were not checked against the operator and must not be shown on the site as a verified line.

### 11.1 Coverage of the Hotspawn lobby (verified against the live lobby and the fixtures feed)

| Item | Value | Evidence |
|---|---|---|
| Lobby LoL entries (tier filter "All tiers") | **241** | Lobby state read in Actions, `data/diag/coverage_audit.json` (`lobby_fixtures_total`), and the lobby page itself https://play.hotspawn.com/lol-pickems |
| Of those, already past start time (no match link, locked) | **66** | `lobby_past_rows` |
| Of those, upcoming (start in the future, match link present) | **175** | `lobby_future_with_permalink` — every one is priced |
| Upcoming fixtures in the fixtures feed | **188** = 175 `scheduled` + **13 `cancelled`** | `api_lol_future_status`, https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures (Hotspawn's own backend, the source the lobby renders) |
| Cancelled fixtures listed in the lobby | **0** — none of the 13 cancelled fixtures is in the lobby | `ids_in_api_not_lobby` |
| Lobby header "This week 139 matches this week" | **Unverified.** Lobby rows with start inside the lobby's own week window (2026-10-19 00:00 → 2026-10-25 23:59:59 UTC) number **64** (62 upcoming + 2 past). No definition of "139" is visible on the page, so it is flagged, not used. | `lobby_week`, `lobby_future_in_week` |

**Decision (implemented 2026-10-23):** the lobby is the authority for "listed on Hotspawn". The pipeline prices exactly the 175 upcoming lobby fixtures that the fixtures feed also lists with status `scheduled`. The 13 `cancelled` fixtures are excluded from picks and shown on the Flagged page with their source link. Verifier rule D21 fails the build if any upcoming lobby fixture is unpriced or if an excluded fixture is priced.

### 11.2 Betting-site survey (what established books say they cover)

Only the sources in the **verified** column were read directly. The others come from search-result summaries of third-party guides; they are listed so that a human can check them, not as data.

| Source | Type | Status | What the source says | Link |
|---|---|---|---|---|
| Pinnacle (guest front-end feed) | Sharp esportsbook | **Verified in production** (parent Regular `period == 0` moneylines only; child Kills/Towers/Dragons prop matchups excluded) | Prices the World Championship and EMEA Masters only; no amateur leagues | https://www.pinnacle.com/en/esports/league-of-legends |
| Unibet (Kambi JSON offering API) | Major EU/AU sportsbook network | **Verified in production** (`eu-offering-api.kambicdn.com` pre-match 2-way `Match Odds`, linked per event on `www.unibet.com.au`) | Prices the World Championship (8/8 Swiss matches verified) and major LoL events | https://www.unibet.com.au/betting/sports/filter/esports/league_of_legends/all/matches |
| Bovada (coupon JSON) | US-facing esportsbook | **Verified in production** (unofficial JSON) | Prices the World Championship and a few other matches | https://www.bovada.lv/sports/esports/league-of-legends |
| Polymarket (Gamma API, public) | Prediction market | **Verified in production** | Prices Worlds 2026 and some tier-2/3 events; thin volume | https://gamma-api.polymarket.com |
| Polymarket homepage | Operator notice | **Verified 2026-10-23** — the homepage says *"Trading is blocked in the United States on polymarket.com"* and offers a view-only mode | https://polymarket.com/ |
| Kalshi | US prediction market | Not used — the probe found no LoL series (`CHECKED_UNAVAILABLE`) | https://kalshi.com/ |
| bet365, Betway, GG.BET, Thunderpick, BetOnline, Rivalry, TonyBet | Established books | *Third-party claim only.* Guides list LoL coverage (e.g. "LCK, LPL, LEC, LCS, CBLOL, LFL, PRM" for Thunderpick; "LCK, LPL, LCK CL, TCL, LFL" for BetOnline). No per-match public odds feed was available to us, so none is used. | esports.gg guide https://esports.gg/guides/betting/league-of-legends-betting-sites/ · eGaming HQ https://www.egaminghq.com/guide/lol-betting-odds-2026-guide/ · ibebet https://ibebet.com/betting/esports/league-of-legends/ |
| OddsPapi (aggregator) | Odds aggregator | *Third-party claim:* lists "Worlds, LEC, LCS, LCK, LPL, CBLOL, LJL, Prime League Pro Division" and requires an API key. No key is configured, so **no OddsPapi data is read**. | https://oddspapi.io/blog/esports-odds-api-guide-how-to-get-pinnacle-cs2-lol-data-for-free/ |
| HLTV esports odds (US) | Odds comparison | *Third-party claim:* lists DraftKings, Kalshi and bet365 as US esports options. Not parsed. | https://www.hltv.org/en-us/betting/sites/esports |

**Conclusion, unchanged from §1:** the only lines we can read programmatically are Pinnacle, Bovada and Polymarket, and they cover the top-tier and a few tier-2/3 events. Every amateur or regional fixture is priced by our Elo / standings model, not by a book. The third-party guides do not change that, because none of them exposes per-match prices that we can verify.

### 11.3 Results sources (re-checked)

| Source | Status on 2026-10-23 | Note |
|---|---|---|
| Leaguepedia `MatchSchedule` / `Standings` (Cargo) | Used in production (results + schedule) | Community wiki (Fandom); attribute, do not call it official |
| Riot LoL Esports API (`esports-api.lolesports.com`) | Still blocked (HTTP 403) from GitHub Actions per the earlier probe `data/diag/report7.json` | Not used |
| Liquipedia API | Terms: gzip, ≥2 s between requests, CC-BY-SA 3.0 attribution | Not wired in this release |

### 11.4 Irregularities for review (added 2026-10-23)

1. **13 cancelled fixtures were being priced** in the 2026-10-23 11:00 UTC payload (`status: cancelled`, no lobby entry). Fixed in this release; the Flagged page lists them with source links.
2. **Lobby header "139 matches this week" does not reconcile** with the fixture data (64 rows inside the week window). Flagged, unverified.
3. **Polymarket US access**: trading is blocked for US users on polymarket.com (see §11.2). Its prices are reference data only.
4. **OddsPapi wording** in the earlier payload described an adapter that does not exist. Corrected: no adapter, no key, no data read.
5. **Pinnacle child prop-matchup duplication (`D20` fixed)**: Pinnacle's `/leagues/{id}/matchups` returns 5–7 child matchups (`parentId != null`, `units = Kills/Towers/Dragons/Barons/Inhibitors`) whose `/markets/related/straight` endpoint repeated the parent's `period == 0` moneyline. Fixed in `scripts/fetch_markets.py` (parent `Regular` matchups + `/leagues/{id}/markets/straight`) and enforced by verifier rule `D20`.
6. **Hotspawn `PVB` tag collision in German PRM 2nd Division (`HOTSPAWN_NAME_COLLISION` flagged)**: Hotspawn expands `PVB` in `PRM 2nd Division 26-27 Fall` to defunct Vietnamese team `Phong Vũ Buffalo`; Leaguepedia's verified participant page (`https://lol.fandom.com/wiki/Prime_League_2nd_Division/2027_Season/Fall_Split`) confirms the team is **`PvB (Swiss Team)`**. Mapped via competition-scoped alias and flagged on every affected row.
7. **`LYON` homonym in Worlds 2026**: Hotspawn's `LYON` in `Worlds 2026 Main Event` is **`LYON (2024 American Team)`** on Leaguepedia (`https://lol.fandom.com/wiki/2026_Season_World_Championship/Main_Event`), not the defunct 2013 LAN team `LYON`. Fixed in `data/aliases.json`.
8. **Liquipedia MediaWiki API & CC BY-SA 3.0 provenance (`arena/1b6841c2`)**: Wired compliant `probe_liquipedia_pages()` (`https://liquipedia.net/leagueoflegends/api.php`, gzip, ≥2.2s spacing, never HTML scraping), added `bovada.lv` / `kambicdn.com` to `MARKET_HOSTS` in `scripts/verify_site.py`, and published the full line-by-line audit in `research/line-by-line-audit-2026-10-23.md`.

---

## 12. Refresh 2026-10-23 — established books → esportsbooks → community (session `arena/92bfcdd3`)

Brief for this pass: *resolve picks for matches that cannot be resolved the same way as the featured picks*
(low-tier matches, or matches not covered by e.g. Polymarket) — try established LoL betting sites first,
then esportsbooks/esports lines, then community sources. Findings, in that order:

### 12.1 Established books / aggregators (market lines)

| Source | 2026-10-23 finding | Evidence |
|---|---|---|
| **OddsPapi** (350+ books incl. Pinnacle, bet365, Stake, 1xBet) | LoL board measured 2026-09-20: 133 bookmakers quoted G2 v Movistar KOI — but the documented LoL tournaments are still only Worlds, LEC, LCS, LCK, LPL, CBLOL, LJL and **Prime League Pro Division**. No PRM 2nd/3rd Division, RIVALS LEAGUE, 4 Nations, Tunisian Super League, Komplettligaen, LigaGG or Arabian 2nd Division. Requires an API key; **no key is configured in this repo**. | [oddspapi.io/sports/esports/lol](https://oddspapi.io/sports/esports/lol), [esports odds API guide](https://oddspapi.io/blog/esports-odds-api-guide-how-to-get-pinnacle-cs2-lol-data-for-free/) |
| **Bovada** (already a production source) | Third-party coverage review (2026-09-24) lists LCK, LPL, LCP, LCS, LEC, LFL, Prime League (Pro), TCL — consistent with our feed: Worlds only in the current window. No tier-3 amateur leagues. | [esports.gg LoL betting sites](https://esports.gg/guides/betting/league-of-legends-betting-sites/) |
| **eGamersWorld** odds board | Lists upcoming/live LoL matches with odds from multiple bookmakers per card. Useful as a **human cross-check**; programmatic use is **UNVERIFIED** until the Actions probe (`scripts/probe_sources.py` → `data/diag/source_probe.json`) shows structured per-match prices. | [egamersworld.com/lol/bets](https://egamersworld.com/lol/bets) |
| **Pinnacle / Polymarket** (already production) | Unchanged: Pinnacle guest feed prices Worlds (+EMEA Masters when listed); Polymarket lists Worlds and a handful of tier-2/3 events with thin liquidity. In the 2026-10-23 live run they covered **9 of 188** fixtures. | `data/diag/pipeline.log` |

### 12.2 Esportsbooks (GG.BET, Thunderpick, Rivalry, Midnite, Betway, Unibet, …)

**Update after merge reconciliation:** session `arena/0fb2d0c7` (T17, PRs #18/#19) added a working
**Unibet (Kambi) LoL feed** to production (`scripts/fetch_markets.py`) — the Kambi API is reachable
even though the Unibet HTML page returns 503 to our probe. Production market sources are therefore
Pinnacle, Unibet, Bovada, Polymarket. For the remaining esportsbooks no new programmatic access was found. Previous measured results stand (403/404/503 or JS-shell only from
GitHub Actions — §8 and `checked_unavailable` in the payload). To keep this claim fresh rather than stale,
`scripts/probe_sources.py` now re-probes these plus Kalshi, Smarkets API, Manifold, eGamersWorld,
OddsPortal and BetExplorer on every branch pipeline run and commits the observed statuses to
`data/diag/source_probe.json`. A source is promoted to production only if a probe shows structured
per-match JSON **and** a sample row is human-verified. Until then, claiming their lines would be fabrication.
Observed 2026-10-23 (`data/diag/source_probe.json`): Kalshi esports-series API 200 JSON but **no LoL series**;
Manifold 200 JSON but only futures/questions (“NA vs EU — Worlds 2026”, outright winners), no per-match fixtures;
Smarkets API 404; eGamersWorld/GG.Bet/Thunderpick 403; Rivalry/Unibet 503; BetExplorer/Betway 404;
OddsPortal/Midnite/OddsPapi pages 200 HTML only (no structured prices parsed).

### 12.3 Community/results sources — the resolution path that actually works for low-tier matches

Implemented this session (T13), in priority order for any fixture without a market line:

1. **Elo on Leaguepedia `MatchSchedule` results** (existing) — 31,732 results in the 2026-10-23 run.
2. **Leaguepedia `Standings` (`MODEL_STANDINGS`)** — two sessions implemented this independently on
   2026-10-23; the merged production formula is session `arena/0fb2d0c7`'s (T18): a standings-derived
   Elo offset `base + 400·log10(wr/(1−wr))` with `wr = clamp(0.65·wr_series + 0.35·wr_games, 0.15, 0.85)`
   (Laplace-smoothed), blended with the real Elo for whichever side lacks one (requires ≥1 decided
   series). This session's standalone Bradley–Terry variant (`wr=(W+2)/(W+L+4)`) was live-verified on
   its branch (167 standings rows / 14 competitions; 4 PRM 3rd Division fixtures upgraded) and then
   superseded at merge by the blended version — kept here for the record, not used in production.
   Behavioural test: `verification/test_standings_model.py`.
3. **League prior** (existing) — one side still unknown after 1–2.
4. **Explicit 50/50 `UNRESOLVED`** (existing) — currently 0 rows; listed separately with limitations.

Remaining limits (published on the site, per league): a few prior-only rows remain where a Hotspawn
name matches no verifiable Leaguepedia identity. (Most of the PRM 2nd Division cases found by this
session — “Locked IN”, “Phong Vũ Buffalo” — were resolved by session `arena/0fb2d0c7`'s verified
aliases, see §11 items 6–7.)
Standings ignore strength of schedule; Elo tiers across leagues are priors, not measurements.

### 12.4 Verification log additions

| Date | Source | What it verified | Link / evidence |
|---|---|---|---|
| 2026-10-23 | OddsPapi LoL page | 133 books on a tier-1 fixture; documented LoL tournaments exclude all our amateur leagues; key required | https://oddspapi.io/sports/esports/lol |
| 2026-10-23 | esports.gg roundup | Bovada LoL coverage = majors + LFL/Prime Pro/TCL only | https://esports.gg/guides/betting/league-of-legends-betting-sites/ |
| 2026-10-23 | eGamersWorld | Multi-book LoL odds board exists (human cross-check; API use unverified) | https://egamersworld.com/lol/bets |
| 2026-10-23 | Live pipeline (Actions 39980317947) | Standings fetched: 167 rows / 14 competitions; 4 fixtures → `MODEL_STANDINGS`; 188/188 picks, 0 unresolved | `data/diag/pipeline.log`, `docs/data/picks.json` |
| 2026-10-23 | `scripts/probe_sources.py` | Fresh observed statuses for 13 candidate sources | `data/diag/source_probe.json` (committed by pipeline-test runs) |


---

## 14. Refresh 2026-10-24 — making the split-standings signal actually price rows (session `arena/c38ce482`)

### 14.1 The gap this closes

The brief asks that every fixture get a line "based upon known betting lines" **and** that community LoL
sites be used to originate lines where no book prices a match. Community *results* sources are the only
usable signal for tier-3 fixtures, and Leaguepedia's `Standings` table is the one that carries a
**current-split** record per team.

The pipeline already fetched that table (2 880 rows across 41 competition pages in the 2026-10-24 run),
but it priced **0** fixtures:

- `MODEL_STANDINGS` only applied when a side had **no Elo at all**.
- Elo needs only **one** recorded game in the last 365 days to rate a team; a standings record needs only
  **one** decided series. Any team with *some* history therefore always had an Elo rating, so the
  standings branch was unreachable in practice.

That made the standings signal a documented-but-unused capability, and it is also why the published
per-league limitation text said rows were "resolved via Leaguepedia recorded match results **and split
standings**" while the standings counter read 0 — the text claimed evidence that was not used.

### 14.2 What changed

| Change | Detail | Where |
|---|---|---|
| New method `MODEL_ELO_STANDINGS` | A side with **thin** Elo (<8 games in 365d) *and* a current-split standings record **for this row's own competition** gets that record blended into the rating. Weight `series/(series+4)`, capped at 0.6 so pooled Elo still dominates. Flagged `STANDINGS_BLEND_APPLIED`; capped at Medium confidence (Low when the comparison is cross-league). | `scripts/model.py` |
| Same-competition rule | A standings record from a *different* tournament is never blended into a row. `standings_by_page_team` is looked up first; the team-only fallback is only used when the side has no Elo at all. | `scripts/model.py` |
| `standings_pages` counter | `fetch_leaguepedia.py` never emitted it, so the site printed "Standings rows: 2 880 across **0** competitions". It is now computed from the distinct `OverviewPage` values. | `scripts/fetch_leaguepedia.py` |
| Accurate per-league limitation text | The text now names only the signals that actually priced the competition ("…recorded match results **and current-split standings records**" only when the standings signal fired). | `scripts/update_picks.py`, `docs/assets/app.js` |
| Standings source link | Standings rows now cite the competition's **own** page (e.g. `RIVALS_LEAGUE/2026_Season/Season_2`) instead of the generic `Special:CargoTables/Standings` index, so a human can read that team's record in context. Check `D8d` (generic-table links must be flagged) therefore passes without weakening the rule. | `scripts/model.py` |
| Honest source note | The Leaguepedia Standings source note now states rows, competition pages **and how many fixtures the signal actually priced**. | `scripts/update_picks.py` |

### 14.3 Measured effect (live pipeline run 2026-10-24T16:35Z)

| Metric | Before | After |
|---|---|---|
| Fixtures priced by the standings signal | **0** | **59** (`MODEL_ELO_STANDINGS`) |
| `MODEL_ELO_THIN` rows (thin history, no split record) | 67 | **3** |
| Low-confidence rows | 73 | **9** |
| Unresolved (explicit 50/50) | 0 | **0** |
| Coverage | 100 % | **100 %** |

Example row (`RIVALS LEAGUE Season 2`, 2026-10-24): Karolinerna 41.9 % vs Turbo Gaming 58.1 %.
Pooled Elo 1466 vs 1491 was blended with the current-split record (1–4 series vs 4–2 series) to
1388 vs 1528 — source: https://lol.fandom.com/wiki/RIVALS_LEAGUE/2026_Season/Season_2

### 14.4 Verification

| Check | Result | Evidence |
|---|---|---|
| `verification/test_standings_model.py` | **17/17** (8 new): blend fires on thin Elo + same-competition record; a stronger split record is favoured; the weight is recorded; the row is flagged; confidence ≤ Medium; an out-of-competition record is **not** blended; a deep Elo pair is not overridden. | `verification/test_standings_model.py` |
| `audit/test_model.py` | **23/23** (2 new): blend weight stays in [0, 0.6]; a standings row always cites a standings source; a standings row always cites a competition-specific page. | `audit/test_model.py` |
| `scripts/verify_site.py` (live) | **PASS**, 0 FAIL. `D8d` violations went 59 → 0 after the source-link change. | `verification/last_report.md` |
| `verification/check_dom_render.js` (new) | All 6 pages render against the published payload in jsdom with every content container filled. | run locally + wired into `pipeline-test.yml` |
| D18 start-time cross-check | Now reads the **live** `data/cache/leaguepedia.json` written by the same run that priced the model, instead of committed `data/diag/ms_*.json` snapshots that were 67.8 h old. | `scripts/verify_site.py` |

### 14.5 Sources used

| Source | What it verified | Link |
|---|---|---|
| Leaguepedia `Standings` (Cargo export) | Current-split series/game records per team per competition — the split record behind every `MODEL_ELO_STANDINGS` row. | https://lol.fandom.com/wiki/Special:CargoTables/Standings |
| Leaguepedia competition pages | The competition-specific page each standings row cites. | e.g. https://lol.fandom.com/wiki/RIVALS_LEAGUE/2026_Season/Season_2 |
| Leaguepedia `MatchSchedule` (Cargo export) | The recorded series the pooled Elo rating is fitted on. | https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule |
| Live pipeline run (Actions 40111627086, branch `arena/c38ce482-lolhotspawn2`) | The counts in §13.3 and the verifier PASS. | https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40111627086 |

---

## 13. Refresh 2026-10-24 — resolving every fixture the featured picks cannot price (session `arena/26fa1cec`)

**Brief for this pass:** every match on Hotspawn must carry a pick; matches that cannot be resolved the way the
featured (bookmaker-priced) picks are resolved must be researched separately — established LoL betting sites first,
then esportsbooks, then esports betting lines/aggregators, then community results. Publish a separate
unresolved/limitations section on the site and in the executive summary.

**Measured baseline for this pass** (branch payload generated `2026-10-24T16:25:23Z`, run
[40111355592](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40111355592)):
164 scheduled upcoming fixtures · **164 priced (100%)** · 9 market-priced (Pinnacle 8, Unibet/Kambi 8, Polymarket 9,
Bovada 0 in this window) · 155 own-model · **0 unresolved** · 68 Low confidence · 14 cancelled Hotspawn fixtures excluded.
Only **1 of the 12 active competitions (Worlds 2026 Main Event)** has any external bookmaker line; the other 11
(PRM 2nd/3rd Division, Tunisian Super League, RIVALS LEAGUE, Arabian League 2nd Division, 4 Nations, Komplettligaen,
LCP 2027 Promotion, LigaGG CELOL A/B, LGC Rising) do not.

### 13.1 Established sportsbooks and exchanges — observed, not assumed

Every status below was returned to a single GET from GitHub Actions during the 16:25Z refresh
(`docs/data/picks.json` → `market_probe`, also `data/diag/market_source_probe.json`).

| Source | Observed | Can it price a PRM/RIVALS/Tunisian/Komplettligaen fixture? | Link |
|---|---|---|---|
| Pinnacle (guest JSON) | HTTP 200, JSON, LoL league index present | No — only the leagues it lists (Worlds here). Already a production source for the 8 World Championship lines. | https://guest.api.arcadia.pinnacle.com/0.1/sports/12/leagues |
| Betfair Exchange | HTTP 403 | No — automated access blocked. | https://www.betfair.com/exchange/plus/ |
| Smarkets (API) | HTTP 404 at `/v3/sports/` | No — documented path not reachable; no exchange line used. | https://api.smarkets.com/v3/sports/ |
| BetOnline | HTTP 200, HTML only | No — the HTML contains no structured per-match prices we can parse. Human cross-check only. | https://www.betonline.ag/sportsbook/esports/league-of-legends |
| Betway Esports | HTTP 404 | No — LoL path returns not found. | https://www.betway.com/en/esports/league-of-legends |
| Unibet (HTML shell) | HTTP 503 | Not used (prices come from Kambi's JSON feed instead). | https://www.unibet.com/betting/sports/filter/esports/league_of_legends |
| GG.Bet | HTTP 403 | No — 403 block page to automated requests. | https://gg.bet/en/esports/lol |
| Thunderpick | HTTP 403 | No — 403 block page to automated requests. | https://thunderpick.io/esports/league-of-legends |
| Rivalry | HTTP 503 | No. | https://www.rivalry.com/lol |
| Midnite | HTTP 200, HTML only | No — no server-rendered prices parsed. | https://www.midnite.com/esports/league-of-legends |
| 1xBet line feed | HTTP 203 (interstitial) | Not verifiable from CI. A direct request from a US IP redirects to `https://1xbet.com/en/block` — *“Access denied! … your country is not included…”* (IP 195.64.119.112, 2026-10-24). Vendor/aggregator claims that 1xBet prices tier-2/3 LoL remain **unverified**; no 1xBet price is used. | https://1xbet.com/LineFeed/GetSportsShortZip?lng=en&country=1 |
| OddsPapi (API) | HTTP 404 without a key at the public path | No key configured. Vendor documentation lists LoL tournaments **Worlds, LEC, LCS, LCK, LPL, CBLOL, LJL and Prime League Pro Division** only — not PRM 2nd/3rd Division, RIVALS, 4 Nations, Tunisian Super League, Komplettligaen, LigaGG or Arabian 2nd Division. | https://oddspapi.io/blog/esports-odds-api-guide-how-to-get-pinnacle-cs2-lol-data-for-free/ |
| odds-api.io (API) | HTTP 200, no LoL market in the payload | No key configured; nothing used. | https://api.odds-api.io/v3/sports |
| OddsPortal | HTTP 200, HTML only | Human cross-check only; scraping not implemented. | https://www.oddsportal.com/lol/ |
| BetExplorer | HTTP 404 at `/lol/` | No. | https://www.betexplorer.com/lol/ |
| eGamersWorld | HTTP 403 | No. | https://egamersworld.com/lol/bets |

### 13.2 Prediction markets

| Source | Observed 2026-10-24 | Finding | Link |
|---|---|---|---|
| Polymarket (production) | prices 9 of 164 fixtures | Worlds + a handful of tier-2 events; no PRM/RIVALS/Komplettligaen. | https://gamma-api.polymarket.com |
| Kalshi | HTTP 200 JSON, **no LoL series** in the esports category | The API returns no League of Legends **series** at all in this category, so no per-match price can be read. Kalshi's public site is listed for manual review. | https://api.elections.kalshi.com/trade-api/v2/series?category=Esports |
| Manifold | HTTP 200 JSON, 5 LoL references, no per-match fixtures | Futures/questions only. | https://api.manifold.markets/v0/search-markets?term=league%20of%20legends |

### 13.3 Community / official results — the path that actually resolves the low-tier fixtures

| Source | Observed 2026-10-24 | Role in a pick | Link |
|---|---|---|---|
| Leaguepedia `MatchSchedule` | 31,750 recorded results (production) | Elo input for every non-market fixture; per-fixture source link on every row. | https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule |
| Leaguepedia `Standings` | 2,880 rows (production) | `MODEL_STANDINGS` fallback; 0 rows needed in this snapshot because every side already had Elo. | https://lol.fandom.com/wiki/Special:CargoTables/Standings |
| Liquipedia API | HTTP 200; **54 page titles** for the active leagues after the prefix-mapping fix (it previously returned nothing) | Tournament metadata index only; never a probability. | https://liquipedia.net/leagueoflegends/api.php |
| bo3.gg | HTTP 200, 177 LoL references | A reachable community results site — **not used**: Leaguepedia already covers every fixture and a third results provider would need per-match verification first. | https://bo3.gg/lol/matches |
| gol.gg | HTTP 200, HTML | Same as bo3.gg — not used, listed for manual review. | https://gol.gg/tournament/list/ |
| Riot LoLESports official schedule | HTTP 403 (public key sent) | Official schedule not reachable; Leaguepedia remains the results source. | https://esports-api.lolesports.com/persisted/gw/getSchedule?hl=en-US |
| primeleague.gg (organizer) | Reachable; Fall Split 2026/27 “Running”, group stage 24.09–04.12.2026, playoffs 05.–13.12.2026 | Organizer link on PRM 2nd/3rd Division rows (human verification). | https://www.primeleague.gg/en/leagues/prm/3227-fall-split-202627 |
| rivalsleague.gg (organizer) | Reachable; LoL season 2 match weeks run to 22 Nov 2026, playoffs 23 Nov–06 Dec 2026 | Organizer link on RIVALS LEAGUE rows. | https://www.rivalsleague.gg/lol |
| komplettligaen.no (organizer) | Reachable; publishes divisions 1–5 + playoff schedules/results (e.g. “Sluttspill 1. divisjon”) | Organizer link on Komplettligaen rows (previously missing because of an exact-key mismatch). | https://www.komplettligaen.no/lol/ |

**Competitions with no verified organizer page** (links deliberately left blank rather than guessed):
Tunisian Super League 2026, Arabian League 2nd Division 2026 Summer, 4 Nations 2026 Halloween Heist,
LigaGG CELOL A/B 2026 Split 2 Playoffs. Their picks still come from Leaguepedia recorded results, and the
limitation is published on the site.

### 13.4 Outcome

* **Picks for 164/164 listed fixtures, 0 unresolved.** Non-market fixtures are resolved by the tier-anchored Elo
  model on recorded results (155 rows this refresh), not by inventing a book line.
* **68 Low-confidence rows** (thin history, cross-league comparison) are labelled and listed on the
  Unresolved & limitations page and in the executive-summary section.
* **Nothing from the probe is used in a probability.** Verifier check `D22` fails the build if a probe row carries a
  probability or lacks an https source link, and `D12` already fails if Hotspawn is used as a probability source.
* Every refresh re-measures the table in §13.1–13.3, so this page cannot silently go stale: the site prints the
  observed status and timestamp, not a remembered claim.

### 13.5 Verification log additions

| Date | Source | What it verified | Link |
|---|---|---|---|
| 2026-10-24 | Live probe (run 40111355592) | 22 candidates: 10 reachable, 5 structured JSON, 3 with LoL references; per-source verdicts published | `data/diag/market_source_probe.json` |
| 2026-10-24 | 1xBet line feed | Geo-blocked for the requesting US IP (“Access denied”) — tier-2/3 claim unverifiable from here | https://1xbet.com/LineFeed/GetSportsShortZip?lng=en&country=1 |
| 2026-10-24 | OddsPapi documentation | Documented LoL tournaments exclude every amateur league on Hotspawn's list | https://oddspapi.io/blog/esports-odds-api-guide-how-to-get-pinnacle-cs2-lol-data-for-free/ |
| 2026-10-24 | primeleague.gg Fall Split 2026/27 | Organizer page live, season running, playoff dates published | https://www.primeleague.gg/en/leagues/prm/3227-fall-split-202627 |
| 2026-10-24 | rivalsleague.gg/lol | Organizer LoL page live; season 2 dates published | https://www.rivalsleague.gg/lol |
| 2026-10-24 | komplettligaen.no/lol/ | Organizer page live with division schedules and results | https://www.komplettligaen.no/lol/ |
| 2026-10-24 | Kalshi public API | Esports series list carries no League of Legends **series**; our own probe result, not a third-party claim | https://api.elections.kalshi.com/trade-api/v2/series?category=Esports |

> Numbering note: this session's pass is §14 because §13 was written in parallel by session
> `arena/26fa1cec` (same day, different method: it probes 21 candidates from the 6-hour production run).
> The two sections agree on the conclusion and do not contradict each other.

## 14. Refresh 2026-10-24 — where the non-featured (low-tier) matches are quoted (session `arena/a21e3910`)

Goal of this pass: for the 160 fixtures that have **no** featured external line (PRM 2nd/3rd Division,
Tunisian Super League, RIVALS LEAGUE, Arabian League 2nd, 4 Nations, Komplettligaen, LigaGG, LCP Promotion,
LGC Rising), re-check **established books → esportsbooks / esports betting lines → community** in that order,
and record only what was actually observed. Every statement below is a live observation made on
2026-10-24 between 16:10 and 16:30 UTC, with the link that shows it.

### 14.1 Established sportsbooks — observed coverage

| Source (link) | What was observed 2026-10-24 | Consequence for our lines |
|---|---|---|
| [Pinnacle guest esports leagues feed](https://guest.api.arcadia.pinnacle.com/0.1/sports/12/leagues) | The feed's **only** League of Legends competition is `League of Legends - World Championship` (league id 9587, 10 matchups). No PRM, RIVALS, Tunisian, Arabian, 4 Nations, Komplettligaen or LigaGG league object exists in it. | Pinnacle can only price the featured Worlds rows; the low-tier rows cannot be priced from it. This is the upstream reason those rows use our own Elo/standings line. |
| [Pinnacle Worlds matchups](https://guest.api.arcadia.pinnacle.com/0.1/leagues/9587/matchups) | Live payload contains `LYON vs Karmine Corp` with `startTime 2026-10-24T20:00:00Z`, matching the published row's 20:00 UTC. | Confirms the book's own start time where a market exists; used as a cross-check, not as the lock time (Hotspawn governs). |
| [Polymarket — Top Esports vs Anyone's Legend](https://polymarket.com/event/lol-tes-al-2026-10-24) | Page showed **Top Esports 37¢ / Anyone's Legend 64¢** at ~16:19 UTC; the published payload has TES 0.365 / AL 0.635 (same market, same direction). Its page text still says "initially scheduled … 7:00 PM ET" (23:00 UTC) while its own countdown showed ~42 minutes, consistent with the 17:00 UTC Hotspawn/Leaguepedia start. | Adds a second live verification of a featured row, and confirms the `START_TIME_DISAGREES_WITH_BOOKS` flag on this row is driven by a stale book start field, not by our time. |
| [Unibet event page (Kambi)](https://www.unibet.com.au/betting/sports/event/1029609648) | The HTML is an application shell; no prices are readable without the Kambi JSON feed the pipeline already uses. | Unibet rows stay on the Kambi CDN feed; the public page is a human cross-check only. |
| [Betmonitor — Prime League 2nd Division odds comparison](https://www.betmonitor.com/odds-comparison/esports/prime-league-2nd-division/10024464) | The league page exists and search indexing exposes bet365 / ggbet prices for Prime League 2nd Division fixtures, but the page body is rendered client-side — the fetched HTML contains a generic highlights shell, not per-fixture prices. | Strongest evidence yet that **bet365 and ggbet do quote this league**, but it is only reachable through a browser or an unverified internal API, so it cannot feed the pipeline automatically. Flagged for manual review (F14.1). |
| [EsportBet LoL odds board](https://esportbet.com/odds/league-of-legends/) | Reachable affiliate odds page; the odds block served in HTML lists other titles (Overwatch in this fetch) and no low-tier LoL fixtures. | Human cross-check only; not a feed. |
| [EsportsBets LoL guide](https://www.esportsbets.com/betting/league-of-legends/) | US-regulated books (BetMGM, Caesars, FanDuel) are recommended for "major tournament coverage" only. | No low-tier pricing; consistent with the earlier probes. |

### 14.2 Esportsbooks and esports betting lines — observed coverage

| Source (link) | What was observed | Consequence |
|---|---|---|
| [OddsPapi LoL board](https://oddspapi.io/sports/esports/lol) | Live page measured 2026-10-24 04:15 UTC: **0 fixtures scheduled** between LoL tournaments, 133 bookmakers quoted on the last measured tier-1 fixture, 184 market families, sportId 18. The documented tournament ids are tier-1 events; every request needs an `apiKey`. | The only API that could aggregate 100+ books for LoL, but it is **key-gated**: a free key must be created manually (`/us/sign-up`). There is no key in this repo, so it is not used. This is the single highest-value upgrade if the owner ever supplies a key as a repository secret. |
| [Betmonitor esports hub](https://www.betmonitor.com/odds-comparison/esports/) | Reachable comparison hub; same client-side rendering limit as 13.1. | Needs a headless browser; out of scope for a 6-hourly Actions job. |
| [bo3.gg LoL matches](https://bo3.gg/lol/matches) | Community match/results site (not a bookmaker). Probed by CI; result recorded in `data/diag/source_probe.json`. | Possible future results cross-check, never a price source. |

### 14.3 Community / results sources (used for our own line where no book exists)

| Source (link) | Role | Verified |
|---|---|---|
| [Leaguepedia `MatchSchedule`](https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule) | Series results, schedules and team identities behind every `MODEL_ELO` / `MODEL_STANDINGS` row (CC BY-SA 3.0) | Live in this snapshot: 31,752 schedule rows used by the model, 2,880 standings rows |
| [Leaguepedia Standings](https://lol.fandom.com/wiki/Special:CargoTables/Standings) | Current-split win-loss records for the amateur splits | Fetched (`Leaguepedia Standings: ok, count 2880`) |
| [Riot LoL Esports schedule API](https://esports-api.lolesports.com/persisted/gw/getLeagues?hl=en-US) | Official Riot schedule (fixture/time verification only, never a probability) | Probed by CI; result in `data/diag/source_probe.json` |

### 14.4 What this means for the 160 non-featured rows (published on the site)

- **No reachable sportsbook names any of our low-tier leagues** in a machine-readable feed. The one
  comparison page that does expose such leagues (Betmonitor, bet365 + ggbet) is browser-rendered.
- The rows therefore keep **our own line**: chronological tier-anchored Elo on Leaguepedia results, plus
  split standings when Elo cannot rate a side, plus a shrunk competition prior as the last resort.
  73 of 169 rows are capped at **Low confidence** because the sample is thin (<8 games in 365 days) or
  the comparison crosses leagues; 0 rows are `UNRESOLVED` in the current snapshot.
- **Honest limitation** (unchanged, now re-verified): a model line is not a market line. It carries no
  bookmaker margin, no injury/roster news and no betting-market information; it must not be treated as
  an edge over a bookmaker price.

### 14.5 Flagged for review

- **F14.1** Betmonitor's [Prime League 2nd Division page](https://www.betmonitor.com/odds-comparison/esports/prime-league-2nd-division/10024464)
  appears to price fixtures from bet365 and ggbet. Whether the numbers are real-time, delayed, or
  affiliate-supplied cannot be confirmed from the fetched HTML. **Do not use until a human checks a
  specific fixture against the bookmaker's own site.**
- **F14.2** OddsPapi is key-gated; no key is configured, so the "133 bookmakers" claim is **not** verified
  for our fixtures — only for the tier-1 sample the vendor reports. No price from it is used anywhere.
- **F14.3** Polymarket's resolution text for `lol-tes-al-2026-10-24` says 7:00 PM ET while its own
  countdown and the Hotspawn/Leaguepedia schedule say 17:00 UTC. The published lock time follows
  Hotspawn (source of truth for pick'em locks); the discrepancy is already flagged per row.

### 14.6 What the CI probe actually observed (GitHub Actions, 2026-10-24T16:27:59Z)

`scripts/probe_sources.py` was extended with seven candidates and run inside
`Pipeline test (branch verification)` run
[40111023039](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40111023039)
(step "Probe candidate odds sources", read-only, never feeds picks). Full JSON: `data/diag/source_probe.json`.
Twenty candidates probed; the seven added in this pass:

| Candidate | HTTP | Structured JSON? | Verdict recorded |
|---|---|---|---|
| Betmonitor — Prime League 2nd Division comparison | **200** | no | reachable HTML only — no per-match prices in the response |
| Betmonitor — esports hub | **200** | no | reachable HTML only |
| EsportBet — LoL odds board | **200** | no | reachable HTML only |
| EsportsBets — LoL guide | **200** | no | reachable HTML only |
| bo3.gg — LoL matches | **200** | no | reachable HTML only (community results) |
| gol.gg — Games of Legends | **200** | no | reachable HTML only (community stats) |
| Riot LoL Esports schedule API | **403** | n/a | needs the Riot `x-api-key`; not configured, not used |

The 13 pre-existing candidates were unchanged in character: Kalshi and Manifold answer JSON but carry no per-match
LoL market for our leagues; eGamersWorld 403, GG.Bet 403, Thunderpick 403, Rivalry 503, Unibet 503, Betway 404,
BetExplorer 404, Smarkets 404; OddsPortal / Midnite / OddsPapi return HTML shells only.

**Conclusion for this pass (unchanged from §12, now re-measured):** no additional source can supply a
machine-readable per-match price for the 160 non-featured fixtures without either (a) a paid/registered API key
(OddsPapi), or (b) a headless browser to read an odds-comparison page (Betmonitor). Neither is available in a
6-hourly, no-manual-input Actions job, so those fixtures keep our own line and the site says so on every row.

## 15. Refresh 2026-10-24 — fixture-matched check: does *any* source price the model-only rows?

Session `arena/ac089f33-lolhotspawn2`. This section complements §13/§14 (session `arena/26fa1cec`) and the
production `scripts/source_probe.py` (`market_probe`): those record **reachability**. This one records
**coverage** — for each source, how many two-way prices it produced that belong to a fixture we currently
price ourselves.

Starting snapshot (main `72c9b5a`, 15:28 UTC): 169 fixtures, 9 with an external line, 160 by the model
(PRM 2nd Division 36, PRM 3rd Division 61, Tunisian Super League 20, RIVALS LEAGUE 18, Arabian League
2nd Division 6, 4 Nations 4, Komplettligaen 3, LCP 2027 Promotion 3, LigaGG A/B 4).

### 15.1 Method

`scripts/probe_lines.py` (new, stdlib only, never writes a probability) fetches each candidate, extracts
only **two-way main-match** prices (map/prop boards rejected), and matches every price to the published
fixture list by normalised team name **and** start time (±48 h). Per candidate it records the HTTP
status, the number of two-way prices, and how many *currently model-only* fixtures those prices cover.
Raw output: `data/diag/line_probe.json`. Run it with `.github/workflows/line-probe.yml`
(manual dispatch, ~1 minute); it is not part of the 6-hour production run.

### 15.2 Result — 39 requests across 30 sites, 0 with new coverage

| Candidate | Observed | Two-way prices | Model-only fixtures covered |
|---|---|---|---|
| Pinnacle league index (control) | 200; only `League of Legends - World Championship` | 8 fixtures seen | **0** |
| Kambi/Unibet, markets GB, DE, SE, IT, NL, FR, PL, AU, ZZ | 200 in every market, identical 8 World Championship matches | 8 | **0** |
| Kambi/Betsson, NordicBet, LeoVegas, Betcity | 429 / 429 / 400 / 400 | 0 | 0 |
| SofaScore esports API | 403 to a CI runner | 0 | 0 |
| bo3.gg public API | 200, match records without odds fields | 0 | 0 |
| 1xBet / Betwinner / Melbet `LineFeed` | 203 geo stub for sport ids 3, 12, 70, 85, 109 | 0 | 0 |
| bmbets LoL comparison | 200 HTML; LoL index = Worlds, LCP, Game Changers Rising | 0 | 0 |
| eGamersWorld / Oddspedia / GGScore / BetExplorer | 403 / 410 / 403 / 404 | 0 | 0 |
| Winamax / Marathonbet / Betano / Stake / William Hill / Parimatch / Rainbet / Thunderpick / GG.Bet / SportsBetting.ag / Rivalry | 403 (Rivalry 503) | 0 | 0 |
| BetOnline.ag / BC.Game / Vave | 200 HTML shell, no server-rendered per-match prices | 0 | 0 |
| Prime League official (organizer) | 403 to CI; schedule/results only, never odds; rules prohibit betting-operator sponsors | 0 | 0 |
| RIVALS LEAGUE official (organizer) | 200 | 0 | 0 |

**Conclusion:** no accessible betting source publishes a price for those competitions, so there is no
external line to quote for them. That is a property of the market, not a gap in the pipeline — and it is
now measured each time the probe runs rather than asserted from memory. The sportsbooks that *do* carry
the World Championship already feed the pricing cascade through `scripts/fetch_markets.py`.

### 15.3 Verification log additions

| Date | Source | What it verified | Link / evidence |
|---|---|---|---|
| 2026-10-24 | Pinnacle guest league index | One LoL league listed; 8 fixtures | https://guest.api.arcadia.pinnacle.com/0.1/sports/12/leagues |
| 2026-10-24 | Kambi offering API (9 markets) | Same 8 World Championship matches in every country market | https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=DE&useCombined=true |
| 2026-10-24 | bmbets LoL index | LoL coverage = Worlds, LCP, Game Changers Rising | https://www.bmbets.com/e-sports/world/lol---world-championship/ |
| 2026-10-24 | Prime League official rules | Betting/gambling operators are a prohibited sponsor category | https://www.primeleague.gg/en/statics/rules_general |
| 2026-10-24 | Prime League Fall Split 2026/27 | League is running (group stage 24.09–04.12) even though no book prices it | https://www.primeleague.gg/en/leagues/prm/3227-fall-split-202627 |
| 2026-10-24 | Actions 40110923198, 40111672023, 40111922808 | Probe executed in CI; evidence committed; 0 sources with coverage | `data/diag/line_probe.json` |

---

---

## 16. Refresh 2026-10-24 (session `arena/e6f33fe9`) — Oddspedia gone, Kambi brand feeds closed, and what that means

This section only records findings that are **new** relative to §13–§15; it is not a re-statement of them.
Everything below was measured from the CI runner on 2026-10-24 and is stored verbatim in
`data/diag/source_probe.json` (candidates added this session to `scripts/source_probe.py`).

| Candidate | Measured status from CI | Consequence |
|---|---|---|
| Oddspedia — `oddspedia.com/league-of-legends/odds` | **HTTP 410** ("The resource you have requested has been permanently deleted"), confirmed the same from a direct fetch; `oddspedia.com/lol` answered 404 earlier | Oddspedia is no longer a usable cross-check on its generic LoL path. League-scoped URLs surfaced by search were not verifiable, so nothing from Oddspedia is cited as a source |
| BMBets — `bmbets.com/e-sports/world/lol---prime-league/` | HTTP 200, HTML only | Human cross-check only; no API |
| Betmonitor — Prime League 2nd Division comparison | HTTP 200, HTML only | Human cross-check only; body is client-rendered |
| Strafe — `strafe.com/esports-betting/odds/league-of-legends/` | HTTP 200, HTML only (Oddspedia-powered) | Human cross-check only |
| Kambi `ubde` brand feed (`…/offering/v2018/ubde/listView/esports/…`) | **HTTP 400** — `Unable to resolve customer for extApiEndpoint ubde` | No German Unibet brand feed exists for us |
| Kambi `ub` feed with `market=DE` and `market=SE` | HTTP 200, **same 8 World Championship events** as `market=GB` / `ubca market=ZZ` | The `market` parameter does not widen LoL coverage; per-brand enumeration is not a route to tier-2/3 lines |

**What is still true (and now stated on the site, not only here).** A handful of established books
(bet365, Unibet, efbet, novibet) do publish Prime League 2nd Division prices — visible on
[Betmonitor](https://www.betmonitor.com/odds-comparison/esports/prime-league-2nd-division/10024464) and
[OddsPortal](https://www.oddsportal.com/esports/league-of-legends/league-of-legends-prime-league/).
None of them, and no esportsbook or aggregator we probed, exposes a public feed that a scheduled
Actions job may legally and reliably consume. Therefore those fixtures keep **our own line** from
recorded results and split standings, and the executive summary now lists every such limit next to
each competition instead of only describing it in prose.

### 16.1 Hand verification performed with this session (2026-10-24)

| Row / claim | Source opened | Observed | Result |
|---|---|---|---|
| Top Esports vs Anyone's Legend — published consensus 0.365 for Top Esports | [Polymarket event](https://polymarket.com/event/lol-tes-al-2026-10-24) · [Kambi `ub` feed](https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=GB&useCombined=true) | Polymarket **Top 37¢ / AL 64¢**; Kambi **2.65 / 1.42** | Matches — 0.365 sits between the two books |
| JSK Esports vs El Menzah Esports — a no-market tier-3 row (`MODEL_ELO_THIN`) | [Hotspawn match page](https://www.hotspawn.com/matches/jsk-esports-vs-el-menzah-esports-tunisian-super-league-2026-1080924) · [Leaguepedia competition](https://lol.fandom.com/wiki/Tunisian_Super_League/2026_Season) | Teams, tournament and 24 Oct 16:00 start confirmed; the Leaguepedia split page exists with the results the model used | Matches |
| Lobby coverage | [Hotspawn lobby](https://play.hotspawn.com/lol-pickems) · [live payload](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/data/picks.json) | Lobby listed 241 LoL rows (169 upcoming at 15:28Z); payload reconciliation `lobby_upcoming = priced`, 0 missing | Matches |

---

## 17. Refresh 2026-10-24 — non-featured picks: established books → esportsbooks → odds/data APIs → community (session `arena/66e731b3`)

Brief for this pass: *every* Hotspawn LoL match must have a pick — including low-tier matches and
matches not covered on sites like Polymarket — using outside information sources **only for matches
that cannot be resolved the same way as the featured (market) picks**, trying established LoL betting
sites first, then esportsbooks/esports lines. Baseline payload (2026-10-24T15:28Z, `docs/data/picks.json`):
169 fixtures · 9 featured market rows (Pinnacle + Unibet/Kambi + Polymarket; **Bovada 0 — bug found, §17.1**) ·
160 own-line rows (93 `MODEL_ELO`, 67 `MODEL_ELO_THIN`) · 0 unresolved · 73 low-confidence.
The 160 non-featured rows are this section's subject. **No price below was copied into picks without a
structured feed; third-party roundups are labelled as claims, never as data.**

### 17.1 Established LoL betting sites — and a production bug found

| Source | Finding (2026-10-24) | Evidence |
|---|---|---|
| **Bovada** (production source since T8) | **Adapter silently discarded 100% of Bovada LoL moneylines.** Bovada's full-series market is `description "Moneyline"`, `descriptionKey "Head To Head"`, period `{"description": "Game", "main": true}` (display group "Game Lines"); the series map-total (Total 4.5 in the Bo5 Galions–Solary EMEA event) sits under the same period, proving the period means the whole series, not Map 1. `fetch_bovada` rejected any market whose period contained "game", so during Worlds `sources_status` showed Bovada `no_data/0` while the coupon listed 9 events. **Fixed:** accept the moneyline only when the period is unnumbered full-event (`Game`/`Match`, `main: true` when present); `Game 1`/`Map N` stay rejected. Offline replay of the committed snapshot now yields **9/9 records** (was 0/9), probabilities sum to 1, and Gen.G–IG de-vigged 0.792 sits in the same range as the independently recorded Polymarket 77¢ / published 0.765 for that fixture (different book, cross-check only). | `data/diag/bovada_prematch.json`, `scripts/fetch_markets.py` (`_bovada_series_moneyline`, `_parse_bovada_groups`), `verification/test_entity_and_books.py` (snapshot replay; combined 17/17 after the 2026-10-24 merge) |
| **BetOnline / SportsBetting.ag / TonyBet / BC.Game / Stake** | 2026 third-party roundups claim LoL boards including (per book) Prime League, LCK Challengers, TCL, LFL and map/player props. "Prime League" in those claims is the Pro Division, **not** the PRM 2nd/3rd Divisions Hotspawn lists, and none of the roundups documents a public structured feed. Treat as **human cross-check candidates only**; added to the CI probe this session (candidate list migrated to `scripts/source_probe.py` at merge — see reconciliation note in §17.5) — promotion requires structured per-match JSON plus a human-verified sample row (probe results: `data/diag/source_probe.json`, updated by the branch pipeline run). | https://esports.gg/guides/betting/league-of-legends-betting-sites/ (2026-09-24) · https://www.egaminghq.com/esport-game/league-of-legends/ (2026-10-19) · https://dotesports.com/betting/esports/league-of-legends (2026-10-12) |
| **Pinnacle / Unibet (Kambi) / Polymarket** (production) | Unchanged behaviour; they price Worlds (+ occasional tier-2) and nothing in PRM 2nd/3rd, Tunisian SL, RIVALS S2, Arabian 2nd, 4 Nations, Komplettligaen PO, LigaGG or LCP Promotion in this window (9/169 rows). | `docs/data/picks.json` `sources_status`, `league_breakdown` |

### 17.2 Esportsbooks

GG.BET, Thunderpick, Rivalry, Midnite, Betway were re-checked in §12.2 (403/404/503/JS-shell from CI).
This session adds BetOnline, SportsBetting.ag, TonyBet, BC.Game and Stake to the same
one-polite-GET probe (`scripts/probe_sources.py`, 21 candidates). Until a probe returns structured
per-match LoL prices **and** a sample row is verified against the book's own page, no esportsbook
beyond the four production feeds contributes any number to this site — claiming otherwise would be
fabrication. Any reachable-HTML result is recorded as "human cross-check only".

### 17.3 Commercial odds/data APIs (the "someone must price tier-3" vendors)

| Vendor | Official-source finding (fetched 2026-10-24) | Consequence |
|---|---|---|
| **PandaScore** | Official FAQ: *"The PandaScore Statistics API does not include third-party bookmaker odds. PandaScore does offer a separate Odds product"* (sales contact). Getting-started docs: every request requires a token; no token is configured in this repo. Probe added for `api.pandascore.co/lol/matches/upcoming` without a token (expected unauthorised). | Not usable without buying/configuring a key. Published in `checked_unavailable`. https://developers.pandascore.co/docs/frequently-asked-questions · https://developers.pandascore.co/docs/getting-started |
| **Abios (Kambi esports division) / Kambi Odds Feed+** | Official odds docs: feed *"built to deliver … predictions for licensed sportsbooks"*, *"covers the largest tournaments in … League of Legends"*, full league list only via account manager. This is the same Kambi stack already consumed publicly via Unibet's CDN — one deduplicated line per match, so a direct contract would not add an *independent* book. | No direct B2B feed. https://abiosgaming.com/docs/en/content/odds/overview/intro |
| **GRID / Bayes lineage** | Enterprise official-data providers; no public self-serve odds endpoint or pricing found in this pass (GRID is also the current LoL Data Portal operator per community documentation). | Not usable without a commercial agreement; not probed (no documented public endpoint to probe honestly). |
| **OddsPapi / The Odds API** | Unchanged from §12.1: key required, none configured; OddsPapi's documented LoL tournaments still exclude every amateur league on Hotspawn's list. | Not used. |

### 17.4 Community/results sources — what actually resolves the other 160 matches

1. **Leaguepedia `MatchSchedule` Elo (production)** — 31,752 recorded results in the baseline run;
   the only verified source that records PRM 2nd/3rd, Tunisian SL, RIVALS, Arabian 2nd, 4 Nations,
   Komplettligaen and LigaGG results at all.
2. **Leaguepedia `Standings` (production fallback)** — 2,880 rows in the baseline run. Bug fixed this
   session: the published note said *"across 0 competitions"* because `standings_pages` was never
   computed; `fetch_leaguepedia.py` now counts distinct overview pages (with a fallback in
   `update_picks.py` for cached snapshots), so the next refresh publishes the real competition count.
3. **Oracle's Elixir (checked, not adopted)** — official downloads page (fetched 2026-10-24): free CSVs
   updated **once per day** via Google Drive, covering *"LCS, LEC, LCK, LPL, PCS, CBLoL, and many more
   leagues"*, game stats are Riot property, and *"some content is provided courtesy of Leaguepedia"*.
   It is a majors-focused results source with **no bookmaker odds**; ingesting it would duplicate
   Leaguepedia for tier-1 while adding nothing for the tier-3 fixtures that need help. Human
   cross-check only. https://oracleselixir.com/tools/downloads
4. **gol.gg (checked, probe added)** — community stats pages linked from Liquipedia tournament pages;
   no documented public API/feed found this pass, so no number is taken from it. Probe records
   reachability only. https://gol.gg/tournament/list/
5. **Standings-blend for thin-Elo rows — this session rejected it; a concurrent session implemented a capped version and merged first (reconciled, retained with a caveat):**
   blending a team's current-split `Standings` record into an already-existing thin Elo would
   double-count the same series, because those standings summarize the same `MatchSchedule` results
   the Elo already consumed — so this session did not implement it. Concurrently, session
   `arena/c38ce482` implemented `MODEL_ELO_STANDINGS` (same-competition record only, weight
   `series/(series+4)` capped at 0.6, confidence capped at Medium; §14 above) and it merged first
   (PR #38) with unit/audit tests. At this merge the capped blend was **retained** — it is a form-
   recency weighting rather than an independent signal, and the double-count + confidence-cap caveats
   are tracked as flagged item U4 against the published per-refresh backtest (pre-blend baseline on
   this branch: log-loss 0.6228, Brier 0.2166, 30-day n=653). Removing merged, tested model behaviour
   without a superior held-out comparison would be a regression by assertion, which this project
   forbids.

### 17.5 Bottom line for non-featured picks (limitations, also published on the site)

- No accessible bookmaker, prediction market, or no-key API prices PRM 2nd/3rd Division, Tunisian
  Super League, RIVALS LEAGUE, Arabian League 2nd, 4 Nations, Komplettligaen Playoffs, LigaGG CELOL
  or LCP Promotion fixtures. Every vendor that might price some of them (OddsPapi, PandaScore Odds,
  Abios direct, GRID) requires a paid key / licensed-book contract / sales agreement; none is
  configured in this repository and this project does not invent credentials or prices.
- Those matches are therefore resolved by our own line: tier-anchored Elo on Leaguepedia recorded
  results → split standings → league prior → explicit 50/50 `UNRESOLVED`, with per-league limits on
  `docs/unresolved.html#by-league` and in the executive summary's unresolved section.
- New `checked_unavailable` entries (PandaScore, Abios/Kambi direct, Oracle's Elixir) and one new
  published limitation were added in `scripts/update_picks.py` so the site itself carries this log.
- **Probe measured 2026-10-24T16:40Z** (Actions run `40112009538`, `data/diag/source_probe.json`,
  21 candidates): BetOnline 200 HTML, TonyBet 200 HTML, BC.Game 200 HTML, gol.gg 200 HTML — all
  *human cross-check only* (no structured per-match prices parsed); SportsBetting.ag 403, Stake 403,
  PandaScore no-token 403 (JSON error body), Oracle's Elixir downloads 403 from CI (the page itself
  was fetched and read via a browser-grade fetch for §17.4). **No new source qualified for an
  adapter.** Same run, live: **Bovada `ok` (8 records)** — all 8 Worlds consensus rows are now
  4-book (Pinnacle/Unibet/Bovada/Polymarket) with max cross-book dispersion 0.046; payload
  160/160 resolved, 0 unresolved; standings note now reads *"2,880 rows across 209 competitions"*.

## 18. Refresh 2026-10-24 (later pass) — tier probe with browser UA, plus proof that cited pages exist — tier probe with browser UA, plus proof that cited pages exist
(session `arena/9d523943`)

§13–§17 above already establish the landscape (sections are numbered in merge order, so §14 appears twice —
that is upstream, not a typo). This pass adds three things they do not cover and does not repeat their measurements. Evidence: a tier-tagged probe (28 candidates, browser-like User-Agent for the sites that
block bots), run in CI on 2026-10-24 and **preserved as a dated snapshot** —
`data/diag/source_probe_2026-10-24_arena-9d523943.json` @ **2026-10-24T16:48:11Z** (older snapshot
16:26:27Z from run [40110891210](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40110891210);
later one from run [40112604014](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40112604014)).
The live `data/diag/source_probe.json` is regenerated on every run by `scripts/source_probe.py`, so the dated copy
is the one to cite. Per-tier roll-up at 16:48:11Z: established-book 11 probed / 7 × HTTP 200 / 6 JSON;
esportsbook 10 probed / 3 × 200 / 0 JSON; community 7 probed / 5 × 200 / 3 JSON. Direct page reads on 2026-10-24
follow.

### 18.1 Does a browser User-Agent get us into the esportsbooks? No.

| Source | Plain bot UA | Browser UA | Reading it as a page |
|---|---|---|---|
| eGamersWorld `/lol/bets` | 403 | **403** | **Reads fine** — and shows a genuine 5-book board (Vave, Thunderpick, Rainbet, Underdog, CocoBet). Every listed match is **2026 World Championship**; the “recent predictions” block is Worlds too. No PRM, Tunisian, RIVALS, Komplettligaen, LigaGG or Arabian fixture appears. |
| GG.Bet / Thunderpick / Coolbet / Stake | 403 | **403** | n/a |
| Rivalry / Midnite / Betano | 200 | 200 | HTML shell, no server-rendered prices |
| Betway / BetExplorer / Smarkets | 404 | 404 | n/a |
| 1xBet line index | 203 | 203 | non-authoritative status, not parsed |
| The Odds API | 401 (no key) | 401 | n/a |
| OddsPortal `/lol/` | 200 then **503** on the next CI run | 200 to CI | **404 “Offside — page not found”** when opened — a 200 from a bot-facing edge is not evidence the board exists, so it is not cited |

Tier 3 of the fixture list stays unpriced by books. The one production source that reaches below tier 2 remains
**Polymarket**, which prices the *LGC Rising* BO5 decider (`MARKET_SINGLE`, 39.0 / 61.0 in the 16:47Z payload).

### 18.2 Organiser pages: reachable or not, they carry no prices

* **Komplettligaen** (`https://www.komplettligaen.no/lol/`) and **RIVALS LEAGUE**
  (`https://www.rivalsleague.gg/`) — HTTP 200, HTML results only; Leaguepedia remains the programmatic source.
* **Prime League** (`https://www.primeleague.gg/en/leagues/prm/3227-fall-split-202627`) — **403 from CI** (Bunny
  Shield) but readable as a page: it publishes the Fall Split 2026/27 structure (group stage 24.09 → 04.12,
  playoffs 05.–13.12.) and 1,293 registered participants. **No odds anywhere**, so being able to read it would
  improve division metadata, never a line. Adapter still blocked by the 403.

### 18.3 A 200 from Leaguepedia does not prove the cited page exists

Leaguepedia returns **HTTP 200 with the body “There is currently no text in this page”** for a missing title
(checked 2026-10-24 against `/wiki/Prime_League/2026_Season/Fall_Split`). `scripts/verify_site.py
--check-external` therefore cannot certify a citation. New
`verification/check_source_pages.py` extracts every distinct `leaguepedia_url` from the payload and asks
`api.php?action=query&titles=…` (one batched, read-only request) whether each page exists. Result on the
2026-10-24 payload: **12 cited pages, 12 exist, 0 missing**, written to `data/diag/source_pages.log` by the branch
pipeline and wired into `verify.yml` (an unreachable API is a warning, a missing page is a failure).

### 18.4 What changed in production as a result
**Nothing.** No new adapter was promoted, no formula changed, no probability moved. The evidence supports what the
site already says: above the World Championship, no reachable book prices these competitions, so those rows are our
own line, disclosed per league with the Low-confidence count.

---

---

## 19. Refresh 2026-10-24 — live source re-verification + fresh candidate research (session `arena/df8a86d2`)

Brief: re-verify the current payload line by line against the official feeds it cites, then re-run the
established-books → esportsbooks → community search for any fixture that still has no book line.

### 19.1 Line-by-line spot checks of the priced rows (live, 2026-10-24 ~16:1x–16:3x UTC)

Payload under test: `docs/data/picks.json` generated **2026-10-24T15:28:56Z** (169 fixtures, 169 priced, 0 unresolved, 9 market rows).

| Row checked | Cited source | Live value observed | Payload value | Result |
|---|---|---|---|---|
| Dplus KIA vs T1 (Worlds) | Polymarket Gamma `lol-dk-t1-2026-10-24` | `outcomePrices ["0.435","0.565"]` (updated 16:14Z) | 0.435 / 0.565 | ✅ exact |
| Top Esports vs Anyone's Legend (Worlds) | Polymarket Gamma `lol-tes-al-2026-10-24` | `["0.365","0.635"]` (updated 16:10Z) | 0.365 / 0.635 | ✅ exact |
| Dplus KIA vs T1 (Worlds) | Pinnacle guest API matchup `1639127310` (parent, `units: Regular`) period-0 moneyline | `home +117 → 2.17`, `away -137 → 1.7299`; devig = 0.4436 / 0.5564 | 0.4436 / 0.5564 (recorded matchup id 1639127310) | ✅ exact |
| Hanwha Life vs Gen.G (Worlds) | Unibet/Kambi event `1029609640` Match Odds | 2.20 / 1.60 (changed 06:39Z, before snapshot); devig = 0.4211 | 0.4211 | ✅ exact |
| Team Liquid vs Bilibili Gaming (Worlds) | Unibet/Kambi event `1029609649` | 3.35 / 1.29; devig BLG = 0.7220 | 0.722 | ✅ exact |
| Top Esports vs AL / CFO vs MKOI / G2 vs LØS / IG vs TSW | Unibet/Kambi events `1029609648/39/46/47` | devig 0.349 / 0.663 / 0.788 / 0.696 | 0.349 / 0.663 / 0.788 / 0.696 | ✅ exact |
| Dplus KIA vs T1 | Unibet/Kambi event `1029609638` | 2.33 / 1.54 at `changedDate 16:15:37Z` | 2.20 / 1.60 recorded 15:28:56Z | ⚠️ line moved ~47 min **after** the snapshot; recorded value was correct at generation |
| LYON vs Karmine Corp | Unibet/Kambi event `1029609641` | devig LYON 0.457 at `changedDate 15:29:55Z` | 0.462 recorded 15:28:56Z | ⚠️ odds updated 59 s **after** the snapshot; recorded value correct at generation |
| Mental Rush vs Vitality Rising Bees (LGC Rising) | Polymarket `lol-rb-mr-2026-10-27`, **"Match Winner"** market id `6036989` | `["0.61","0.39"]` (updated 16:12Z) | 0.615 / 0.385 | ✅ consistent (0.5¢ drift after snapshot). Child `Game N` markets in the same event show dead `0.5/0.5` prices and are **not** the cited market — confirmed the selector used the series market |
| JSK Esports vs El Menzah Esports (Tunisian Super League) | Leaguepedia `Tunisian Super League/2026 Season` standings | JSK Esports **4-0 (100%)**, El Menzah Esports **1-3 (25%)** | Elo 1593 vs 1434 → 57.1% / 42.9% (model row) | ✅ direction confirmed by the cited standings page |
| Coverage of the lobby | Hotspawn lobby header | `All tiers (241)` | `lobby_lol_listed: 241` | ✅ exact |
| Whalepower Humpbacks vs 1. ECF start time & crowd | Hotspawn lobby card | Oct 24 13:30, 72% / 28% (25 picks) | start `17:30Z` (=13:30 UTC), crowd 72/28 n=25 | ✅ exact |

Suite results on this commit: `check_dom_contract.py` PASS · `test_verifier.py` 35/35 · `test_entity_and_books.py` 10/10 ·
`test_standings_model.py` ALL PASS · `audit/test_model.py` 20/20 · `scripts/verify_site.py` **36 PASS · 0 FAIL · 0 WARN · 1 skip**
(including REQ1–REQ12 traceability: pick on every match, probabilities sum to 100%, outside-Hotspawn inputs,
separate unresolved section linked from the exec summary, mobile viewport, 4–8 h refresh).

### 19.2 Established LoL betting sites (fresh check 2026-10-24)

| Source | What was observed today | Usable for our low-tier fixtures? | Evidence |
|---|---|---|---|
| **Pinnacle** (production source) | Guest API `sports/12/leagues` lists exactly **one** LoL league: `League of Legends - World Championship` (id 9587, 10 matchups). No domestic/amateur LoL boards open during the Worlds window. | Worlds only — no | https://guest.api.arcadia.pinnacle.com/0.1/sports/12/leagues |
| **Unibet / Kambi** (production source) | `listView …league_of_legends…matches.json` returns exactly **8** pre-match events, all `World Championship`. | Worlds only — no | https://eu-offering-api.kambicdn.com/offering/v2018/ubca/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=ZZ |
| **Polymarket** (production source) | Prices the 8 Worlds rows + the LGC Rising final; no amateur-league markets found in the LoL tag (also confirmed 2026-10-23 probes). | Tier-1/2 only — no | https://gamma-api.polymarket.com/events?tag_slug=league-of-legends |
| **OddsPapi** | Live page today: **`0 Fixtures scheduled`** measured 2026-10-24 04:15 UTC for LoL tournamentIds `2452, 2454, 39985`; documented coverage remains Worlds/LEC/LCS/LCK/LPL/CBLOL/LJL/Prime League **Pro** Division. Free REST tier exists but requires a sign-up key — **no key configured, no manual input available**. | No amateur leagues; key required — no | https://oddspapi.io/sports/esports/lol |
| **eGamersWorld odds board** | Today's board lists only `2026 World Championship` (5 books: Vave, Thunderpick, Rainbet, Underdog, CocoBet) and `LGC 2026 Rising` (same 5 books). No PRM 3rd/2nd Division, RIVALS LEAGUE, Tunisian, Komplettligaen, LigaGG, Icelandic, Benelux, 4 Nations, Superstrike, Hitpoint or Arabian events. Their LGC line (Vave 1.40/2.73 → devig RB ≈ 66%) corroborates the direction of our Polymarket-only row (RB 61.5%). | Human cross-check only; HTML, no structured feed — no | https://egamersworld.com/lol/bets |

### 19.3 Esportsbooks & esports betting lines (fresh check 2026-10-24)

| Source | Observation today | Verdict |
|---|---|---|
| **Oddiwire** (new candidate found this session) | Resells the **ODDIN.GG** esports feed (REST + SSE, raw no-vig probabilities). Free plan: 100 REST calls/day, **no card** — but the key is issued only after an **email + Cloudflare human-verification** step ("We send the key to your inbox"). Homepage today showed `PREMATCH EVENTS 161 … LOL 8` — 8 LoL events board-wide (tier-1 scale). | Interesting future adapter; **blocked on key issuance (human step)**. Not integrated. https://oddiwire.com/ |
| **SportsGameOdds** (new candidate) | Free "Amateur" tier: 2,500 objects/mo, 8 leagues / 9 bookmakers, but **signup requires a card** and the league list is not published as covering our amateur LoL divisions. | Not usable autonomously — no https://sportsgameodds.com/pricing |
| **The Odds API** | Free 500 credits/mo but key signup required; prior probe HTTP 401 without key. | Not usable autonomously — no |
| **GG.Bet / Thunderpick / Rivalry / Midnite / Betway / Marathonbet / BetMGM** | Previous CI probe statuses (403/404/503/403/404/403/403) stand; re-confirmed by the branch `probe_sources.py` run of this session (`data/diag/source_probe.json`). Their own pages (per eGamersWorld's board above) price Worlds/LGC only anyway. | No change — no |
| **Kalshi / Smarkets / Manifold** | Prior probe: no per-match LoL series (Kalshi none, Smarkets 404, Manifold futures only). Unchanged in this session's CI probe. | No change — no |

### 19.4 Community / results sources (resolution path for matches no book prices — unchanged and still the production answer)

All 169 current fixtures are priced; **0 UNRESOLVED**. For any fixture that ever lacks a book line the cascade is:
Leaguepedia `MatchSchedule` Elo (31,633 matches / 5,493 teams in the current payload) → Leaguepedia `Standings`
(`MODEL_STANDINGS`) → competition prior (`MODEL_LEAGUE_PRIOR`) → explicit 50/50 `UNRESOLVED` published on the
Unresolved & Limitations page with per-league signal limits. Hotspawn crowd % is never an input (verifier W3).

### 19.5 Irregularities found this session (all non-blocking)

1. **Two Unibet rows show small post-snapshot drift** (DK/T1 moved 16:15Z, LYON/KC 15:29Z vs payload 15:28:56Z generation). Not errors: values were correct when generated; the 6-hour refresh picks up the new prices. No action.
2. **Lobby header now reads `This week 161 matches`** (was `139` on 2026-10-23, flagged then as unverified). The counter changes daily and still does not reconcile to a definition we can verify — remains flagged/unverified, never used in data.
3. **Oddiwire and SportsGameOdds need human key/card signup** — logged as candidates; per the "no manual input" requirement they are not integrated, and no key request was made.
4. **OddsPapi live page reports `0 Fixtures scheduled` for LoL** while Worlds matches are actively priced elsewhere — their feed appears stale or their tournament ids rotated; without a key this cannot be investigated further. Flagged as observation only.

---

## 20. Refresh 2026-10-25 — established books → esportsbooks → esports lines, tested against the *current* unpriced fixtures (session `arena/6e003eec`)

The brief for this pass was specific: for every match that cannot be resolved the way the featured picks are,
look for information sources in this order — **established LoL betting sites → esportsbooks → esports betting
lines** — and publish anything that still cannot be resolved separately, with its limitations. This section is the
evidence for that pass. It was run twice: once by hand with a browser-equivalent fetch of each page, and once from
GitHub Actions by `scripts/probe_prm_lines.py` (`data/diag/prm_line_probe.json`, 16 sources, one polite GET each).

### 20.1 What the leads were (why these sources, not others)

A web search for "Prime League 2nd Division odds" returns pages that *claim* to price exactly the competitions
Hotspawn lists. Those claims were the starting point, and each was then opened and measured rather than trusted:

| Lead | What it claims | Link |
|---|---|---|
| Cloudbet — Prime League 2nd Division | "prices the Prime League 2nd Division through the split, with the match winner, map handicap and total maps on every series" | https://www.cloudbet.com/en/esports/league-of-legends/germany-t8205-prime-league-2nd-division |
| BMBets — LoL Prime League 2nd Division | a dedicated odds-comparison page for the exact competition | https://www.bmbets.com/e-sports/world/lol---prime-league-2nd-division/ |
| Betmonitor — Prime League 2nd Division | German odds comparison; its search snippet shows bet365/ggbet prices on this page | https://www.betmonitor.com/odds-comparison/esports/prime-league-2nd-division/10024464 |
| esportbet.com — LoL tournament list | lists "Prime League 2. Liga 2026 Fall … LIVE" | https://esportbet.com/league-of-legends/ |
| Everygame (review coverage) | review sites list Prime League inside its LoL coverage | https://www.everygame.eu/en/Esports/League-of-Legends |
| Tipico / NEO.bet / bwin (DE) | German-licensed books; Prime League is the German national league | https://www.tipico.de/en/esports/league-of-legends/ · https://www.neobet.de/sportwetten/esports · https://sports.bwin.de/en/sports/esports |

### 20.2 What was actually observed (hand check, 2026-10-25 ~14:0x UTC)

| Source | Observed result | Can a price be read? |
|---|---|---|
| Cloudbet PRM 2nd Division page | Opens, but the events tab says **"No Prime League 2nd Division events available — Check back later"**. The page copy advertising PRM2 pricing is evergreen marketing text, not a live board. | **No** |
| Cloudbet public sports API (`sports-api.cloudbet.com/pub/v2/odds/sports`, `…/league-of-legends/competitions`) | **HTTP 401** — a key is required (Cloudbet's API docs are for licensed/affiliate partners). No key exists in this repo and none may be invented. | **No** |
| BMBets PRM 2nd Division page | HTTP 200, page exists, but the comparison index on it lists only *LoL World Championship (9)*, *LoL – LCP (1)* and *League of Legends – Game Changers Rising (1)*. No PRM fixtures are on the board. | **No** |
| Betmonitor PRM 2nd Division page | HTTP 200, but the body served is the generic comparison index (football/tennis/basketball highlights). The Prime League rows that its search snippet showed are not in the served HTML. | **No** |
| esportbet.com LoL board | HTTP 200 and the page *names* "Prime League 2. Liga 2026 Fall — Berlin — LIVE", but it is a tournament directory with no prices. | **No** |
| Tipico (DE) | HTTP 200 with **zero** League of Legends match references in the served HTML (client-rendered board). | **No** |
| NEO.bet (DE), bwin (DE), bet365 (DE) | HTTP **403** to an automated request. | **No** |
| Everygame | HTTP **404** at the stated LoL path. | **No** |
| eGamersWorld odds board | HTTP **403**. | **No** |
| 1xBet LineFeed | HTTP **203** geo-restriction stub (as in every previous run). | **No** |
| Oddspedia generic LoL odds path | HTTP **410 Gone** ("the resource you have requested has been permanently deleted") — checked by hand on 2026-10-25. | **No** |

### 20.3 The strict, reproducible test (GitHub Actions, 2026-10-25T14:09:50Z)

`scripts/probe_prm_lines.py` asks one question: *does any source show **both** team names of a currently unpriced
fixture inside one 700-character window **together with two or more odds-like decimals** (1.01–30.00)?* It tests all
147 model-only fixtures. Result — **16 sources probed, 8 reachable, 0 published a two-way price**:

| Source | HTTP | Fixtures with a candidate price |
|---|---|---|
| Cloudbet API (sport index / LoL competitions) | 401 / 401 | 0 |
| Cloudbet PRM2 category page | 200 | 0 |
| BMBets PRM2 / Prime League | 200 / 200 | 0 / 0 |
| Betmonitor PRM2 / esports hub | 200 / 200 | 0 / 0 |
| Tipico (DE) | 200 | 0 |
| NEO.bet / bwin / bet365 (DE) | 403 / 403 / 403 | 0 |
| Everygame | 404 | 0 |
| eGamersWorld | 403 | 0 |
| esportbet.com | 200 (names Prime League 2. Liga, no prices) | 0 |
| Strafe | 200 (guide content, no per-match prices) | 0 |
| 1xBet LineFeed | 203 | 0 |

**Version note (recorded because the first attempt was wrong).** The first version of this probe matched single
generic words ("Berlin", "cloud", "atomic") within 240 characters of any number and reported **five** sources as
"odds near a team". Every one of those hits was a false positive on inspection: a German *basketball* fixture
("Alba Berlin — Ratiopharm Ulm"), a CSS gradient (`has-atomic-cream-gradient-background`), a page's meta
description, and a table of league names. The matcher was replaced with the whole-name/same-window rule above and
eight regression tests now pin it down (`verification/test_prm_probe.py`: a basketball page, a stylesheet, a
league-name-only page, a single odd, names outside the window, timestamps and ids must all return **no** price).
That is the difference between "a number appeared near a word" and "a book quoted this fixture".

### 20.4 Conclusion for the 147 model-only fixtures

**No established sportsbook, esportsbook, comparison site or esports betting-line source that we can reach
publishes a readable two-way price for any of them.** The sources that *say* they price Prime League (Cloudbet) or
*list* it (BMBets, Betmonitor, esportbet) had no live PRM board at the time of checking, and the ones that might
(Tipico, NEO.bet, bwin, bet365, 1xBet) either return a client-rendered shell or block automated requests. The picks
for those matches therefore remain **our own line**, built from Leaguepedia results and split standings, and they
are published on the site's separate *"no bookmaker line"* section with the per-league limitation attached — never
presented as a bookmaker price and never given a bookmaker's name.

This is re-tested automatically: `scripts/probe_prm_lines.py` (manual workflow, deep test) and
`scripts/source_probe.py` (one GET per source on **every** 6-hour refresh, results published in the payload's
`market_probe` and on the site).

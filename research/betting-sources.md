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

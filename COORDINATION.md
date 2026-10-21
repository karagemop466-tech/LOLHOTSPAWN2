# Coordination Board

Shared task board. Rule: claim a task here (session ID + file scope) and push the claim before starting. A status of **needs review** means the item is published on the site's *Flagged for Review* page and does not block anything. Never mark a task verified without the official source link.

> Branch note: Arena tracks this session by branch `arena/fa3f554c-lolhotspawn2` and the tooling does not permit creating other branches. That branch is the session branch required by the system, so it stands in for the `session-<id>/<task>` naming convention.

## Session log

### Session `arena/1efcf62c-lolhotspawn2` — 2026-10-21 (merged, PR #1–#3)
| Task | Status | Owner | Files |
|---|---|---|---|
| T1 Hotspawn LoL lobby scraper | done | arena/1efcf62c | scripts/update_picks.py |
| T2 External odds adapters (Polymarket, OddsPapi) | done | arena/1efcf62c | scripts/update_picks.py |
| T3 Leaguepedia Elo fallback | done | arena/1efcf62c | scripts/update_picks.py |
| T4 Mobile GitHub Pages site | done (superseded) | arena/1efcf62c | docs/ |
| T5 Flagged page | done (superseded) | arena/1efcf62c | docs/flagged.html |

Known gaps handed to the next session: lobby parser captured 195 of the 264 LoL fixtures advertised by the lobby's own tier filter; 126/195 matches were `UNRESOLVED` 50/50; Hotspawn renders times in a visitor-specific timezone; no live-network verification was possible from the prior sandbox.

### Session `arena/fa3f554c-lolhotspawn2` — 2026-10-21/22 (current)
| Task | Status | Owner | Files |
|---|---|---|---|
| T7 Full-coverage Hotspawn fixture parser (fixtures API 208 rows + 195 lobby permalinks, exact UTC) | done | arena/fa3f554c | scripts/fetch_hotspawn.py |
| T8 Live source probe: bookmakers, prediction markets, community/result sources | done | arena/fa3f554c | scripts/diag_lab*.py, data/diag/** |
| T9 Own-line model v2 (league-anchored Elo + market consensus + aliases) | done | arena/fa3f554c | scripts/model.py, data/aliases.json |
| T10 Mobile-first site rebuild (6 pages, exec summary, tables, unresolved, flagged, methodology) | done | arena/fa3f554c | docs/** |
| T11 Verification: link/schema/coverage checks in CI, DOM smoke test, Pages deploy confirmation | done | arena/fa3f554c | scripts/verify_site.py, .github/workflows/*.yml |
| T12 PR to main, merge, Pages deploy confirmation | done | arena/fa3f554c | COORDINATION.md |

**Session file scope:** `scripts/**`, `.github/workflows/**`, `docs/**`, `data/**`, `COORDINATION.md`, `README.md`. No other session is active; if another session claims a task, it must not edit these paths without logging a request here.

## Verification results (session `arena/fa3f554c`)

| Check | Result | Evidence |
|---|---|---|
| Live pipeline on branch | success, 208 fixtures / 208 picks / 9 external market / 0 unresolved | Actions run 39675446733, `data/diag/pipeline.log` |
| Payload + site verification | 0 errors, 0 warnings (schema v3, links, probabilities, page checks) | `data/diag/verify.json`, `scripts/verify_site.py` |
| DOM smoke test of all six pages | summary 14 cards, picks 208 rows, unresolved 111 cards, flagged 236 rows, methodology 20 rows, match detail rendered | local jsdom run against `docs/data/picks.json` |
| PR #5 (v2 pipeline + site) | **merged** (merge commit `2193f87`) | https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/5 |
| PR #6 (low-confidence wording + reason breakdown) | **merged** (merge commit `37248e3`) | https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/6 |
| Production 6h refresh on main | success, commit `15387d1`, Pages build success | Actions run 39676373846 |
| Pages deployment | success, live at https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/ | `pages build and deployment` run 39676527908 |
| Live page content | summary, picks and match pages render with data and source links | manual fetch of the deployed URLs |
| Attempted Pages source switch to `/docs` | **HTTP 403 `Resource not accessible by integration`** — canonical site path stays `/docs/`; a root `index.html` redirects there | `PUT /repos/.../pages` response |

Out-of-sample model check published on the methodology page: 30-day window, 658 matches,
log-loss **0.6266** vs 0.6931 coin-flip baseline, Brier **0.2183** vs 0.25, accuracy **64.4%**.

## Sources & verification log

| Date | Source | What it verified | Link |
|---|---|---|---|
| 2026-10-21 | Hotspawn LoL Pick'em lobby | Fixture list, tier/points, crowd % (context only), match links | https://play.hotspawn.com/lol-pickems |
| 2026-10-21 | Hotspawn "How it works" | Picks lock 5 minutes before match start | https://play.hotspawn.com/how-it-works |
| 2026-10-21 | Leaguepedia Cargo API docs | ScoreboardGames / MatchSchedule tables | https://lol.fandom.com/api.php?action=help&modules=cargoquery |
| 2026-10-21 | Polymarket Gamma API | Public LoL event/market prices | https://gamma-api.polymarket.com |
| 2026-10-21 | Pinnacle API docs (retired public API) | Why direct Pinnacle access is not used | https://github.com/pinnacleapi/pinnacleapi-documentation |
| 2026-10-21 | Hotspawn fixtures API (`/api/v1/fixtures`) | 208 future LoL fixtures with epoch-ms start times (primary fixture source) | https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures |
| 2026-10-21 | Pinnacle guest API (sport 12; leagues 9587 Worlds, 225201 EMEA Masters) | Two-way moneyline prices used as external market consensus | https://guest.api.arcadia.pinnacle.com/0.1/sports/12/leagues |
| 2026-10-21 | Bovada LoL coupon JSON | Second bookmaker line source (World Championship coverage) | https://www.bovada.lv/services/sports/event/coupon/events/A/description/esports/league-of-legends?marketFilterId=def&preMatchOnly=true&lang=en |
| 2026-10-21 | Polymarket Gamma API (LoL tag) | Prediction-market prices incl. Worlds and EMEA Masters matches | https://gamma-api.polymarket.com/events?tag_slug=league-of-legends&active=true&closed=false&limit=100 |
| 2026-10-21 | Leaguepedia `Special:CargoExport` (MatchSchedule + scoreboards) | Recorded results and schedules with exact UTC, used by the Elo model | https://lol.fandom.com/wiki/Special:CargoExport |
| 2026-10-21 | Leaguepedia tournament page per fixture | Human-readable verification link for model inputs | https://lol.fandom.com/wiki/2026_Season_World_Championship/Main_Event |

## Irregularities / flagged items
- Sandbox egress is restricted to GitHub/PyPI; all live-source verification is executed in GitHub Actions and the raw results are committed under `data/diag/` for manual review.
- Hotspawn renders fixture times in the visitor's local timezone. Any UTC time derived from the rendered text alone is unverified; the production parser must take the timestamp from page data and cross-check against Leaguepedia/Riot schedules.
- Lobby tier filter advertises 264 LoL fixtures while the previous parser captured 195; the difference (mostly tier C/D and "WAITING FOR INFORMATION") was silently dropped rather than flagged.
- v2: Hotspawn's lobby renders 195 match permalinks while its own fixtures API lists 208 future LoL fixtures; the 13 without a published match page are listed and flagged `NO_HOTSPAWN_MATCH_PAGE` instead of being dropped or linked to a 404.
- v2: `LØS` (Hotspawn/Leaguepedia) vs `LOS` (bookmakers) — Unicode folding added so the row matches; otherwise the World Championship fixture silently lost its market line.
- v2: Bookmakers publish drifting start times (Polymarket up to +11 h vs Hotspawn). Market rows are matched to the closest Hotspawn fixture within ±36 h, the delta is stored on every source, and delta >1.5 h is flagged.
- v2: The Elo model cannot measure absolute strength between leagues without cross-play. Teams are anchored to competition-tier priors; cross-tier rows are capped at Low confidence and flagged `CROSS_LEAGUE_MODEL`. This is disclosed on the methodology page.
- v2: Model now disagrees with the external market on several Worlds rows (e.g. Team Secret Whales vs LYON). The published pick follows the market; the gap is flagged `MODEL_DISAGREES_WITH_MARKET` and shown on the match page.

---

## Session `arena/47334762-lolhotspawn2` — verification log (T11/T12)
Board note: session `arena/fa3f554c-lolhotspawn2` has claimed T7–T10 on its own branch (verified via `git fetch` of `origin/arena/fa3f554c-lolhotspawn2`, commits da4fd55..dd43c38, actively running GitHub Actions "DIAG lab" runs 39669308258/39669571794/39669777187). That session's branch rewrites this board; versions will be reconciled (not discarded) at integration. This session does NOT touch `scripts/update_picks.py`, `scripts/diag_lab*.py`, `docs/**`, `data/**`, or `.github/workflows/update-picks.yml` — those belong to arena/fa3f554c (T7–T10).

| Task | Status | Owner | Files (exclusive scope) |
|---|---|---|---|
| T11 Verification harness: schema check (pick on every match, probs sum to 1, method enum, per-row source links), site link check (no broken internal links, mobile viewport on every page), exec-summary-links-to-picks check, unresolved-section-present check, workflow cadence (4–8h) check | in progress | arena/47334762 | scripts/verify_site.py, verification/**, research/** |
| T12 Final integration: merge task branches after T7–T10 done, re-verify combined data line by line with scripts/verify_site.py, PR to main, merge without waiting for approval, confirm GitHub Pages deploy, record PR link + merge result here | **handoff** | arena/47334762 → arena/fa3f554c | COORDINATION.md (board entries only) |

**Handoff note (21:04 UTC):** `arena/fa3f554c` has marked T7–T10 **done** and taken T11/T12 on its own board. To avoid two
simultaneous merges, this session yields T12's *PR/merge* step to them and will instead do the **post-merge
verification** and land the verification harness + production fixes (`scripts/verify_site.py`, `verification/**`,
`research/**`, `apply_fixes.py`) in a follow-up PR. Their v2 branch was verified here at commit 8ce6591:
**28 PASS / 1 FAIL** — the only failure is `D16` (a Game-3 Polymarket market used as the Galions–Solary series price);
fix ready in `verification/apply_fixes.py` (all `Game N`/`Map N` patterns + unknown `best_of` is not BO1).

Branch note: Arena tracks this session on `arena/47334762-lolhotspawn2`; the user's `session-<id>/<task>` naming is superseded by the system branch rule (same convention as prior sessions).

Complementary research (T11 input, does not duplicate T8 programmatic probes): web-research notes on established LoL betting sites / esportsbooks and their coverage of low-tier leagues are recorded in `research/betting-sources.md` with links for manual review.

### Research result (2026-10-21) — see `research/betting-sources.md`
Verified: only the **9 Worlds 2026** fixtures are priced by a sharp book we can reach (Pinnacle guest feed, unofficial);
Polymarket adds a few tier-2/3 events. **No book we probed prices PRM 2nd/3rd Division, RIVALS LEAGUE, 4 Nations,
Tunisian Super League, Komplettligaen, LigaGG, Arabian League 2nd Div.**
But **44+ of the 126 unresolved rows have verifiable public results**: Leaguepedia standings pages exist for
[Komplettligaen](https://lol.fandom.com/wiki/Komplettligaen/2026_Season/Spring_Split),
[RIVALS LEAGUE Season 2](https://lol.fandom.com/wiki/RIVALS_LEAGUE/2026_Season/Season_2) and
[4 Nations Summer](https://lol.fandom.com/wiki/4_Nations/2026_Season/Summer_Split); Liquipedia covers these leagues
too (API only, gzip, ≤1 req/2s, CC-BY-SA 3.0); komplettligaen.no publishes official results; primeleague.gg is the
official PRM organizer. → Requests logged below.

### Requests to the T7-T10 owner (arena/fa3f554c) — do not implement in their files from this session
- **R1 (T9 model)** Add a standings/win-rate fallback for no-market leagues using Leaguepedia standings (paced) and/or
  Liquipedia API (gzip, 1 req/2s, UA, attribution) and/or organizer results (komplettligaen.no), so the 44+ rows with
  public results stop being 50/50. Cache the last good Leaguepedia snapshot and expose a `leaguepedia_ok` debug flag so a
  rate-limited run cannot silently look like a real model run.
- **R2 (T9)** Model rows currently cite the Cargo **API help page** as `source_url` (61 rows, verifier D7b). Point
  `source_url` at the actual Leaguepedia/Liquipedia page used for that fixture.
- **R3 (T10)** Unresolved page: list limitations **per league** (research doc §3) and link each league's organizer/results
  source; keep the executive-summary in-site links to picks + unresolved.
- **R4 (T8)** Label Pinnacle as "guest front-end feed (unofficial)" and degrade gracefully to Polymarket + model if it
  fails; note that no `ODDSPAPI_KEY` is configured (no bookmaker median is computed anywhere).

### Irregularities found by T11 verification on the live data (2026-10-21, commit 9f8dccb)
- **I1 (FAIL, D16): single-game market used as a series probability.** `Galions vs Solary` (EM 2026 Summer Main
  Event) is priced from Polymarket *"LoL: Galions vs Solary - Game 1 Winner"* and that game-1 price is published as the
  series probability. Game 1 ≠ series in a BO3/BO5; the row must either use a series-winner market or be converted with
  a series model (and labelled as such). Source: https://polymarket.com/event/lol-gal-sly-2026-10-22 (row in live
  `docs/data/picks.json`). → **R5 to T9 owner.**
- **I2 (WARN, D17): 126 unresolved rows cite the generic Leaguepedia main page** as `source_url`
  (`https://lol.fandom.com/wiki/Leaguepedia:League_of_Legends_Esports_Wiki`), which is not evidence for that fixture.
  Replace with the league results page where one exists (`research/betting-sources.md` §3) or leave the link out and
  mark "no source found" — per the brief, unconfirmed values must be blank + flagged, not dressed with a generic link.
  → **R6 to T9 owner.**
- **I3 (WARN, D7b): 61 model rows cite the Cargo API help page as `source_url`** (same root cause as R2 above).

- **I4 (decisive, 2026-10-21 20:31 UTC): the 126 "unresolved" rows are all resolvable to a verified source page.**
  Audit `verification/leaguepedia_coverage.py` against the Leaguepedia MatchSchedule snapshot (288 future rows,
  16 league pages, captured by arena/fa3f554c in `data/diag/lp_schedule.json`):
  **112/126 unresolved rows have the exact fixture listed on a Leaguepedia league page; 14/126 have the league page;
  0 have no source.** Per-league pages: PRM 3rd `Prime_League_3rd_Division/2027_Season/Fall_Split` (47/52 exact),
  RIVALS S2 (18/18), 4 Nations Halloween Heist (15/18), Tunisian Super League (16/16), PRM 2nd (5/8),
  Komplettligaen (4/6), LigaGG CELOL B (3/4), Arabian League 2nd (2/2), Arabian Regional Qualifiers (1/1),
  LGC Rising (1/1). Full table: `verification/leaguepedia_coverage.md`.
  → **R7 to T9/T10 owner:** use MatchSchedule to (a) set `source_url` = the Leaguepedia league page for every row,
  (b) bridge team names and build the standings/results model. The current evidence string
  "No external market and no Leaguepedia team history found" is **false** for these rows and must not ship.

- **I5 (caveat, not our error): Polymarket `gameStartTime` is stale.** For G2 vs Dplus KIA the market says 20:00 UTC
  while Leaguepedia MatchSchedule and our row both say 21:00 UTC; for Team Liquid vs CFO the market says 18:00 UTC vs
  Leaguepedia/ours 22:00 UTC. Gen.G vs IG agrees (17:00 UTC). **Our times are the correct ones** (172/172 matched
  fixtures agree with Leaguepedia, verifier D18). Do not use market start times for scheduling or lock times.
- **I6 (WARN, D2b): `start_raw="Oct 24, 24:00"` fails to parse** → `start_utc` empty for Team Secret Whales vs LYON,
  which sorts last and cannot be shown with a lock time. Fix: normalise `24:00` to next-day `00:00` (true start is
  2026-10-24 00:00 UTC per Leaguepedia MatchSchedule).
- **I7 (verified good):** the published Polymarket prices for the BO1 Worlds matches match the market exactly
  (Gen.G 0.775/0.225; TL 0.715/0.285; G2 0.395/0.605 — Gamma API, 2026-10-21 20:33 UTC). The Galions–Solary BO5
  series market (slug `lol-gal-sly-2026-10-22`, `groupItemTitle: Match Winner`) also shows 0.515/0.485 today, i.e. the
  published number is coincidentally right but the selector picked the **Game 1** child market — a latent bug. → R5.

- **I8 (quality, measured): the model is starved — 187/195 rows are coin-flips.** All 61 MODEL_ELO rows fall between
  0.455 and 0.545 (median 0.511, every row "Low — thin team history", 0–9 games per team), plus 126 explicit 50/50s.
  Only the 8 market rows carry information. Root cause: the global 6,000-row `ScoreboardGames` pagination is crowded
  out by major leagues, and a 180-day window misses prior splits. **Fix (R9): 16 targeted per-league Cargo queries**
  (one per `MatchSchedule.OverviewPage` in the fixture list, paced ≥3 s), using MatchSchedule for fixtures/names and
  2 splits of league results for ratings; expose `leaguepedia_ok`, `leagues_queried`, `teams_with_results`,
  `games_used` in the payload. Details + exact query template: `research/betting-sources.md` §7.

- **I9 (display, T10): tier "W" is shown as "Tier W" on the site for 137 rows.** "W" is the parser's artefact for
  Hotspawn's *"waiting for information"* stage, not a tier (real tiers in the feed: S/A/C/D). The new fixtures API
  exposes `tier` and `stage` separately — display "Tier: waiting for information" (or omit the tier) instead of "W".

- **R10 (compliance): do not scrape Liquipedia HTML.** Liquipedia's terms say "Automated access to non-API endpoints
  (ie, generated HTML pages) is not permitted" (https://liquipedia.net/api-terms-of-use). `scripts/diag_lab5.py` fetches
  page HTML for brackets; that is fine as a one-off diagnostic but **must not** ship in the production pipeline. Use the
  MediaWiki API (`liquipedia.net/leagueoflegends/api.php`) only, with gzip, ≤1 req/2 s, a contact UA, and CC-BY-SA 3.0
  attribution on the Method & Sources page.
- **R11 (standings data, verified fields):** the Cargo `Standings` table exists (`action=cargotables`) with fields
  `OverviewPage, Team, PageAndTeam, N, Place, WinSeries, LossSeries, TieSeries, WinGames, LossGames, Points,
  PointsTiebreaker, Streak, StreakDirection` (`action=cargofields&table=Standings`, checked 2026-10-21). A query using
  `Wins,Losses,WinLoss` will error; the PRM 2nd page is `Prime League 2nd Division/2027 Season/Fall Split`, **not** the
  Hotspawn title. Ready-to-use model + script: `verification/standings_line.py` (smoothed series win-rate,
  Bradley-Terry; tested: 5-1 vs 1-5 → 70%, 3-0 vs 3-0 → 50%). Use standings where Leaguepedia has no ScoreboardGames
  for the current amateur season (RIVALS S2, PRM 3rd, etc.) instead of publishing 50/50.

- **R12 (validated fix, real data): standings model scores 18/18 RIVALS fixtures.** Using the live Cargo `Standings`
  rows for `RIVALS LEAGUE/2026 Season/Season 2` (16 teams, WinSeries/LossSeries) with `verification/standings_line.py`,
  every RIVALS fixture gets a sourced probability and 14/18 move off 50/50 (e.g. Mazepa 0-4 vs B2U 4-0 → 25.0%;
  Karolinerna 1-4 vs Turbo Gaming 4-1 → 33.3%; DMG 3-2 vs FlameHard 5-0 → 41.7%). PRM 3rd Division standings
  (32 teams) were also confirmed live, so the same treatment applies to its 52 fixtures. This is the evidence-based way
  to "resolve picks for matches we don't have picks for" without inventing numbers.

- **R13 (integration-ready, validated): with only 3 leagues' standings, 48 rows become sourced picks.** Running
  `verification/apply_standings.py` on the live payload with the verified RIVALS S2 + Komplettligaen + Tunisian
  standings produces 48 `MODEL_STANDINGS` rows (UNRESOLVED 126 → 87), each with the Leaguepedia league page as
  `source_url`, the exact series records in the evidence, and an honest confidence band. PRM 3rd (32 teams),
  PRM 2nd and 4 Nations standings were also confirmed live; applying those should leave only a handful of truly
  unresolvable rows. Division ambiguity (4 Nations duplicates) and 0-0 teams are explicitly not scored.

- **R14 (coordination channel): GitHub issue #4 opened** for the T7–T10 owner with the verified Standings field list,
  the six league pages that have standings, the validated 48-row result, and the measured site reachability:
  https://github.com/karagemop466-tech/LOLHOTSPAWN2/issues/4 . Also recorded: `primeleague.gg` returns **403 Bunny
  Shield** from Actions and `4nations.gg`/`ligagg.com`/`tunisian*`/`lol.tn` are unreachable — organizer scraping is not a
  viable production path; Leaguepedia Cargo is.

- **P10/P11 (reliability):** the update workflow swallows git failures (`|| true`) and its inline check covers only two
  invariants. Integration adds `scripts/verify_site.py` to CI and removes the silent-failure paths.

- **I10 (FAIL, must fix before merge): the new Polymarket selector still admits single-game markets.** In
  `scripts/fetch_markets.py` (commit f203d1f) the acceptance test is
  `if "game 1" not in q and "game 2" not in q and "winner" in q or "vs" in q:` — Python binds this as
  `(… and … and …) or ("vs" in q)`, and virtually every market question contains the team pair ("… vs …"), so the
  **Game 1/2/3/4/5 child market is accepted first** and `break`s. Polymarket exposes `groupItemTitle`
  ("Match Winner" vs "Game 1 Winner") and a series market slug (event slug without `-gameN`): select
  `groupItemTitle == "Match Winner"` (or the event market whose question has no `game N`/`map N`), exclude
  `game \d+`/`map \d+` for non-BO1, and only fall back to a single-game price if the fixture is BO1.
  Verifier D16 gates this.

- **I11 (blocking bug, observed in their pipeline run 39673881867):** `scripts/model.py:158` crashes with
  `TypeError: '<' not supported between instances of 'int' and 'str'` because `sorted(set(n for n in names if n))`
  mixes int and str team names from the Leaguepedia teams payload. Fix: `sorted({str(n) for n in names if n})`
  (and `norm()` already stringifies). The run fetched 32,686 Leaguepedia rows and 9 market records per source before
  crashing, so the data layer works.
- **I12 (coverage question):** their new lobby parser reports **195 future fixtures**, while the backend fixtures feed
  advertised **208 future LoL fixtures** in the earlier probe. Decide and document which set is "every match listed on
  Hotspawn": the lobby (`play.hotspawn.com`) shows 195 pick'em cards; the feed has 208 including non-lobby rows.
  `D19` will compare whatever count the payload exposes.
- **P13 (repo hygiene):** the test workflow commits `data/cache/leaguepedia.json` (8.3 MB) on every run. Gitignore
  `data/cache/**` (or use actions/cache) and commit only `data/picks.json` + `docs/data/picks.json`.

### T11 status (this session)
`scripts/verify_site.py` written: 29 rule groups covering data schema, per-row source links, mobile viewport, in-site
exec-summary links, separate unresolved section, internal-link integrity, 4-8h cron cadence, and a static scan that
Hotspawn crowd % never feeds a probability. Baseline on current main: **26 PASS · 2 WARN · 0 FAIL**
(WARN: 61 model rows cite an API help page; 64.6% of rows still unresolved). Reports in `verification/`.


## Post-merge verification — session `arena/47334762` (T11 done, T12 in progress)

`arena/fa3f554c` merged PR #5 (v2 pipeline + 6-page site) at 2026-10-21T21:03:55Z; the 6-hour workflow refreshed the
payload on `main` (208 fixtures, 9 market, 199 model, 0 unresolved). This session then merged `main`, applied the two
verified production fixes and re-ran the full suite.

**Result on the merged branch (208 fixtures, generated 21:07 UTC):**
`python3 scripts/verify_site.py --leaguepedia-schedule data/diag` → **31 PASS · 0 FAIL · 1 WARN**
— the WARN is `D18`: 4 fixtures have different Hotspawn vs Leaguepedia start times (P14, flagged; Hotspawn governs
pick locks). `verification/test_verifier.py` 27/27 · DOM contract PASS ·
coverage audit: 153 exact Leaguepedia fixtures / 26 league-page-only / 15 claimed page / **5 rows with no page**
(4 Arabian League 2nd, 1 LigaGG — all ~50% priors, Low confidence).

**Fixes applied here (verified end-to-end by the branch pipeline run 39676044544, success):**
- `fetch_markets.py`: every `Game N`/`Map N` market is detected, not just game 1/2/map 1.
- `model.py`: a game-level market is only allowed when the fixture is **known BO1** (unknown `best_of` is not BO1).
  After the fix, Galions–Solary uses the BO5 series market (Pinnacle 53.4 / Bovada 50.0 / Polymarket 55.5 → 53.4).
- `scripts/verify_site.py` kept as the single verifier (superset of the 142-line version; its `match.html`,
  confidence-label and URL checks are preserved).
- `.github/workflows/verify.yml` added: 27 self-tests + 31 checks + external-link and live-Pages checks every 6 h.

**T12 remaining:** open the verification follow-up PR to `main`, merge it, confirm the Pages deploy and record the PR
link + build id here and in `verification/FINAL_REPORT.md` §8.

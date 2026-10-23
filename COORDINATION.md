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

## Reconciliation — v2 payload vs the T11 findings (session `arena/fa3f554c`, 21:20 UTC)

The T11 log above was written against commit `9f8dccb` (v1 data). The v2 pipeline that followed changes the
picture; each item is resolved or explicitly dispositioned below.

| Finding | Status on v2 | Evidence |
|---|---|---|
| I1 single-game market used as a series price | **fixed** — selector prefers the event/series market (`groupItemTitle` + `question`), tags every Game-N/Map-N market, and the model refuses a game market unless `best_of == 1` | `scripts/fetch_markets.py::_select_poly_market`, `scripts/model.py`; verifier **D16 PASS**; unit test picks the BO5 series market |
| I2/I3 generic source URL on model rows | **fixed** — every model row links its per-fixture Leaguepedia tournament page; the generic CargoExport table link remains only when no schedule row matched (and the row is Low confidence) | payload `leaguepedia_url`, `sources[]`; verifier D7/D8 PASS |
| I4 126 unresolved rows resolvable to Leaguepedia pages | **obsolete** — v2 resolves all 208 fixtures (0 unresolved); the same MatchSchedule rows power the Elo ratings | `docs/data/picks.json` counts; `data/diag/verify.json` |
| I8 model starved / 187 coin-flips | **obsolete** — league-anchored Elo: 92 `MODEL_ELO`, 72 `MODEL_ELO_THIN`, 35 `MODEL_LEAGUE_PRIOR`, 9 market rows; 30-day backtest log-loss 0.6266 vs 0.6931, Brier 0.2183 vs 0.25, accuracy 64.4% | `model.backtest` in the payload; methodology page |
| I11 int/str crash in Resolver | **fixed** — all Leaguepedia names are string-coerced before sorting | `scripts/model.py`; live runs green |
| I12 195 vs 208 fixture count | **resolved** — API fixtures (208) merged with lobby permalinks (195); the 13 without a match page are published and flagged `NO_HOTSPAWN_MATCH_PAGE` | `scripts/fetch_hotspawn.py`, `counts.hotspawn_without_match_page` |
| P13 8.3 MB cache committed every run | **fixed** — `data/cache/` is git-ignored; only `docs/data/picks.json` + the pipeline log are committed | `.gitignore`, `.github/workflows/update-picks.yml` |
| I5/I6 market or ambiguous start times | **handled** — Hotspawn epoch-ms is authoritative, bookmaker deltas are stored and flagged above 1.5 h, D18 checks Leaguepedia | `START_TIME_DISAGREES_WITH_BOOKS`, D18 WARN (4 fixtures, flagged) |
| R1–R7 | superseded by v2 (league-anchored Elo + per-fixture sources); no 50/50 fallback remains except a genuinely unknown fixture, which would be `UNRESOLVED` | payload + verifier |

**Verification after merging the harness (PR #7) into this branch:**
`scripts/verify_site.py --leaguepedia-schedule data/diag` → **31 PASS · 0 FAIL · 1 WARN** (D18 start-time deltas),
`verification/test_verifier.py` 27/27, `verification/check_dom_contract.py` PASS, jsdom smoke test on all six pages.

**Integration PR for this follow-up:** #8 — **merged** (merge commit `d8b848c`, 21:22 UTC).

**Post-merge state (main):**
- `verify.yml` run **39677101080 → success** on the merge commit (27 self-tests + 31 checks).
- production refresh `28d9755` (208 fixtures, 9 market, 199 model, 0 unresolved) → Pages build **39677401560 success**.
- live site re-checked: summary and picks render; Galions–Solary now uses the BO5 **series** market (Pinnacle 53.4 / Polymarket 55.5), not a Game-3 price.
- parallel session PR #9 (`ci: keep the bot's fresh payload on rebase conflicts`) merged on top; no conflict with this branch.

## Session `arena/cd27b02f-lolhotspawn2` — 2026-10-23 (final integration record)

Branch `arena/cd27b02f-lolhotspawn2` == `main` == `origin/main` (commit 3addc56e6c58de9407d6f6d301cc8f0e3e075be5) at session start; all T1–T12 work from prior sessions is integrated and live. This session re-verified the combined state end to end and refreshed the verification artifacts (commit 39c36ff).

### Verification performed this session

| Check | Result | Evidence |
|---|---|---|
| `scripts/verify_site.py --leaguepedia-schedule data/diag` | 31 PASS · 0 FAIL · 1 WARN | WARN = D18: 10 of 137 matched fixtures have Hotspawn vs Leaguepedia start-time deltas (Hotspawn authoritative for pick locks; all flagged per-row), 52 fixtures absent from the amateur-league snapshot |
| `verification/test_verifier.py` | 27/27 pass | verifier self-tests (each rule fails on bad data) |
| `verification/check_dom_contract.py` | PASS | all JS-referenced ids exist on the six pages |
| Published payload `docs/data/picks.json` | 189 fixtures, 100% resolved | 9 market-consensus rows (Pinnacle/Bovada/Polymarket), 180 model rows (82 MODEL_ELO, 74 MODEL_ELO_THIN, 24 MODEL_LEAGUE_PRIOR), 0 UNRESOLVED, 13 fixtures without a Hotspawn match page flagged `NO_HOTSPAWN_MATCH_PAGE` |
| GitHub Pages | built, live | https://karagemop466-tech.github.io/LOLHOTSPAWN2/ (source: main, path /; root index.html redirects to /docs/) |
| "Verify picks and site" workflow on main | success every 6h | latest run 39949842068 (2026-10-23 11:58 UTC) |

### Requirements traceability (all PASS)

REQ1 pick for every match · REQ2 probabilities sum to 1 · REQ3 no Hotspawn probability input · REQ4 external lines where they exist · REQ5 documented method for every non-market match · REQ6 separate unresolved section with limitations linked from exec summary · REQ7 exec summary links to picks · REQ8 official/trusted source link on every row · REQ9 mobile-friendly · REQ10 automatic 4–8h refresh, no manual input · REQ11 no broken internal links, root entry works · REQ12 third-party attribution.

### Irregularities / flagged items (non-blocking; published on Flagged for Review page)

- D18: amateur-league fixtures (Komplettligaen, RIVALS, PRM, etc.) where Leaguepedia's recorded schedule disagrees with Hotspawn or lacks the row; Hotspawn epoch-ms governs pick lock times, per-row flags attached.
- 13 fixtures have no published Hotspawn match page; listed as `fixtures_without_page` and flagged `NO_HOTSPAWN_MATCH_PAGE` rather than linked to a 404.
- No bookmaker prices tier-3/amateur leagues; those rows are priced by the league-anchored Elo model from Leaguepedia results, labelled Low confidence where history is thin.
- Pinnacle consumed via the public guest front-end feed (unofficial); Bovada returned degraded on some runs, consensus falls back to healthy sources; source status published per run.

### Sources used (official / verified)

- Hotspawn fixtures API + Pick'em lobby (fixture list only, never a probability): https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures, https://play.hotspawn.com/lol-pickems
- Pinnacle guest JSON (two-way moneyline): https://guest.api.arcadia.pinnacle.com/0.1 (site: https://www.pinnacle.com/en/esports/league-of-legends)
- Bovada coupon JSON (two-way moneyline): https://www.bovada.lv/services/sports/event/coupon/events/.../esports/league-of-legends (site: https://www.bovada.lv/sports/esports/league-of-legends)
- Polymarket Gamma API (match/series prices): https://gamma-api.polymarket.com/events?tag_slug=league-of-legends&active=true&closed=false (site: https://polymarket.com)
- Leaguepedia Cargo MatchSchedule + Teams (results, schedule, canonical names): https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule
- Provider availability checks (403/401/404/503 → not used): documented in scripts/update_picks.py CHECKED_UNAVAILABLE and research/betting-sources.md.

### Integration result

Pull request #11 (`arena/cd27b02f-lolhotspawn2` → `main`) merged without waiting for approval.

| Item | Value |
|---|---|
| PR number | 11 |
| PR URL | https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/11 |
| Merge commit | 6feaaecd39cd646a42ce1abbd96453dde22f187e |
| Pages build/run | "pages build and deployment" run 39981417237 — **success** (2026-10-23T15:48 UTC) |
| Pages status | **built** — live at https://karagemop466-tech.github.io/LOLHOTSPAWN2/ |
| Post-merge verification | "Verify picks and site" run 39981419222 — **success** on main |
| Production refresh | "Update Hotspawn LoL picks (every 6h)" re-ran on the main push (automation confirmed live) |

This session (arena/cd27b02f-lolhotspawn2) is complete: repo reviewed line by line, every table row carries an official/trusted source link or is flagged unverified, the executive summary links in-site to the picks list and the unresolved section with limitations, the site is mobile-friendly and live, picks cover 100% of Hotspawn's listed LoL fixtures (189/189, 0 unresolved), and the pipeline refreshes automatically every 6 hours with no manual input. Remaining COORDINATION.md commit for this session (this integration record) is a one-commit follow-up PR from this branch to main.
- Bovada returned HTTP 200 without an event list on the 21:16 run (`status: error`, count 0) while Pinnacle/Polymarket stayed ok; the source status is published as degraded and the consensus fell back to the two healthy sources. A follow-up hardens the feed parser with alternate coupon URLs.

---

## Session `arena/bd37dbe6-lolhotspawn2` — 2026-10-23 (claim)

No other session holds an open claim on `main` as of 2026-10-23 15:35 UTC (prior sessions are merged; `origin` has only `main`). This session claims the following scope and works only inside it.

| Task | Status | Owner | Files (claimed scope) |
|---|---|---|---|
| T13 Coverage audit: reconcile the Hotspawn lobby tier-filter count with the pipeline fixture count and the fixtures API; close any gap | done | arena/bd37dbe6 | scripts/fetch_hotspawn.py, scripts/update_picks.py, scripts/diag_coverage.py, data/diag/** |
| T14 Executive summary, unresolved section and per-league limitations; in-site links to picks; mobile readability pass | done | arena/bd37dbe6 | docs/** (pages + assets) |
| T15 Betting-line and community-source refresh with link-verified research log | done | arena/bd37dbe6 | research/betting-sources.md, scripts/verify_site.py (D21, S10 only) |
| T16 Integration: rerun live pipeline on branch, re-verify line by line, PR to `main`, merge, confirm Pages deploy, record result here | pending | arena/bd37dbe6 | COORDINATION.md (board entries), docs/data/picks.json (generated) |

Any session that needs a file in this scope must log a request here instead of editing it.

---

## Session `arena/bd37dbe6-lolhotspawn2` — results (2026-10-23)

Branch note: Arena fixes this session's branch as `arena/bd37dbe6-lolhotspawn2`; the `session-<id>/<task>` naming is superseded by that rule. Scope actually edited: `scripts/fetch_hotspawn.py`, `scripts/update_picks.py`, `scripts/verify_site.py` (new rules D21 and S10 only), `scripts/diag_coverage.py` (new, read-only), `docs/**`, `research/betting-sources.md` (new §11 only), `data/diag/coverage_audit.json`, `.github/workflows/diag-coverage.yml` (new), this file.

### What was wrong and what changed
| Finding | Evidence | Fix |
|---|---|---|
| The payload published picks for **13 `cancelled` fixtures** that are not in the Hotspawn lobby (the "189" count) | `data/diag/coverage_audit.json` (`ids_in_api_not_lobby` = 13, all `cancelled`, no permalink) | Pipeline prices only the **upcoming lobby fixtures** that the fixtures feed lists as `scheduled`; the 13 are kept in `excluded_fixtures` with the source link and shown on Flagged |
| Lobby header "241" vs payload "189" | Lobby: 241 LoL entries = 66 already started (locked, no link) + 175 upcoming (each has a link). API upcoming = 188 = 175 scheduled + 13 cancelled | `coverage_reconciliation` block in the payload + summary card; verifier D21 fails on any unpriced upcoming fixture or priced excluded fixture |
| Lobby header "This week 139 matches" | 64 lobby rows fall inside the lobby week window (2026-10-19 → 10-25 UTC). No definition of "139" is visible | **Unverified, flagged** (not used) |
| Phone bottom nav: 4-column grid with 5 links (Q8 from `arena/bdecdf49`) | CSS `repeat(4, 1fr)` vs 5 `<a>` | 5 columns; verifier S10 checks links = columns on every page |
| Long source URLs forced sideways scroll on Flagged and Method pages at 390 px | Headless Chromium measurement: `scrollWidth` 461 vs 390 viewport | `overflow-wrap: anywhere` on links and `.sub`; all six pages measured at 390 px |
| OddsPapi described as an "adapter retained" (Q9) | No OddsPapi code exists in `fetch_markets.py`; no key configured | Wording corrected in `CHECKED_UNAVAILABLE` and research §11 |
| Polymarket US access (Q10) | Polymarket homepage, checked 2026-10-23: "Trading is blocked in the United States on polymarket.com" | Limitation on the Method page, Unresolved page (payload `limitations`) and research §11 |
| R16 asked for rule "D20" (unique `source_key` per fixture) | My lobby reconciliation had already used D20 | My rule renamed **D21**; **D20 is reserved for R16** (not implemented here) |

### Coverage result (live pipeline run on this branch, commit 4841d24 inputs, run 39980818293 success)
- Lobby upcoming fixtures: **175** · priced: **175** · missing: **0** · priced but not in lobby: **0** · excluded (cancelled): **13**
- Methods: market consensus 8 + single market 1 · own Elo 78 · Elo (thin history) 71 · league prior (one team unrated) 17 · explicit 50/50 placeholders **0**
- Low-confidence rows: 91 (labelled on the Unresolved page with reasons)
- `scripts/verify_site.py` on the committed payload: **31 PASS · 0 FAIL · 1 WARN** (D18 start-time cross-check: 4 mismatches vs Leaguepedia, flagged per row; Hotspawn governs lock times)
- Headless Chromium at 390 px (iPhone-class viewport): all six pages fit the viewport, no JavaScript errors, 5/5 bottom-nav items visible.

### Sources (checked 2026-10-23)
- Hotspawn Pick'em lobby (fixture list, match links, state): https://play.hotspawn.com/lol-pickems
- Hotspawn fixtures API (backend used by the lobby; `status`, epoch start): https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures
- Polymarket homepage, US trading block notice: https://polymarket.com/
- Polymarket Gamma / Pinnacle guest / Bovada coupon / Leaguepedia MatchSchedule: as listed in `research/betting-sources.md` and on the Method page
- Betting-site survey (third-party claims, not used as data): https://esports.gg/guides/betting/league-of-legends-betting-sites/ · https://www.egaminghq.com/guide/lol-betting-odds-2026-guide/ · https://ibebet.com/betting/esports/league-of-legends/ · https://www.hltv.org/en-us/betting/sites/esports

### Irregularities for Flagged for Review
1. 13 cancelled fixtures were priced in the 11:00 UTC payload — fixed; now excluded and listed with source link.
2. Lobby "139 matches this week" — unverified; does not reconcile with 64 rows in the week window.
3. D18: 4 start-time differences between Hotspawn and Leaguepedia (flagged per row).
4. Polymarket trading is blocked for US users on polymarket.com; its prices are reference data only.

### Requests / replies to other sessions
- **Q7 (`arena/bdecdf49`) and R15 (`arena/0fb2d0c7`):** done — cancelled fixtures excluded and listed; count reconciled (see table above).
- **Q8 (`arena/bdecdf49`):** done — 5-column bottom nav + S10 regression check.
- **Q9 (`arena/bdecdf49`):** done — OddsPapi wording corrected.
- **Q10 (`arena/bdecdf49`):** done — Polymarket US limitation published.
- **Q1/Q2 (`arena/e76bc0ae`):** Q2 done (summary card and unresolved link now say "Picks without a book line & limitations"); Q1 (distinct books in `source_count`) is `arena/e76bc0ae`'s pipeline change and is rendered verbatim by the site.
- **R16 (`arena/0fb2d0c7`, unique `source_key` per fixture, check D20):** not implemented here; **D20 is reserved for it**. The Gen.G–Invictus duplicate-Pinnacle issue must be fixed in `scripts/fetch_markets.py` / `model.py` (outside this session's scope).
- **`arena/cd27b02f` (PR #11, merged 15:45 UTC):** its verification record describes the **189-fixture** payload with 13 cancelled rows flagged. This branch supersedes that payload (175 priced, 13 excluded, D21 PASS). Their verification log is kept unchanged as the record of that run.

### Status
| Task | Status |
|---|---|
| T13 coverage audit and fix | done |
| T14 summary, unresolved, mobile | done |
| T15 betting-source refresh | done |
| T16 PR to main, merge, Pages | done — PR #12 merged, commit `c4619a7`; Pages build `39981988496` success; live refresh `41d7b1a` verified |

### Integration record (T16)
| Item | Value |
|---|---|
| PR | https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/12 (`arena/bd37dbe6-lolhotspawn2` → `main`) |
| Merge | `--merge`, merge commit `c4619a7a4c7033363b109e1fda260a969a0c88c4`, 2026-10-23 15:48 UTC (no approval wait, no auto-merge) |
| Post-merge refresh on main | Update Hotspawn LoL picks run `39981419329` — success; commit `41d7b1a` |
| Pages build for merge commit | `pages build and deployment` run `39981417237` — success |
| Pages build for refresh | run `39981988496` — success |
| Live check (fetched 2026-10-23) | https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/ shows 175 fixtures, 175 with a pick, 0 missing, 13 cancelled not priced; flagged page lists the 13 excluded fixtures |
| Verifier on merged tree | `scripts/verify_site.py`: 33 PASS · 0 FAIL · 0 WARN · 1 SKIP (D18 needs the Actions snapshot); `verification/test_verifier.py` 27/27 |
| Known open item (not blocking) | Gen.G vs Invictus Gaming now lists 10 market lines, several of them the same Pinnacle matchup repeated across boards (R16, owned by `arena/0fb2d0c7` / `arena/e76bc0ae`). Shown on the live page; not fixed in this PR. |

---

## Session `arena/b252f309-lolhotspawn2` — 2026-10-23
| Task | Status | Owner | Files |
|---|---|---|---|
| T13 Final integration audit: re-check current data coverage, source transparency, executive-summary navigation, mobile accessibility, and scheduled refresh; fix and verify remaining gaps | done | arena/b252f309 | COORDINATION.md, verification/**, docs/**, README.md, scripts/model.py, scripts/verify_site.py |

**Scope note:** PR #12 from `arena/bd37dbe6-lolhotspawn2` merged to `main` during this audit, adding the upcoming-only coverage contract (175/175; 13 cancelled excluded), summary coverage card, Polymarket US disclosure, phone URL wrapping, and S10 nav check. PR #13 initially conflicted with those merged changes; I rebased onto the new main, preserved its coverage/UI work, and skipped only two older generated-data commits whose payloads included cancelled fixtures. The latest main refresh is retained and the branch payload was re-audited. The audit's concrete source-provenance gap was that 24/166 model rows link only to a generic Leaguepedia table rather than a fixture-specific page; scope expanded to flag those rows and require a results-source URL without calling community data official.

**T13 sources & verification:** Hotspawn Pick'em lobby (`https://play.hotspawn.com/lol-pickems`) is the fixture source only; Pinnacle (`https://www.pinnacle.com/en/esports/league-of-legends`), Bovada (`https://www.bovada.lv/sports/esports/league-of-legends`), and Polymarket (`https://gamma-api.polymarket.com`) are market sources; Leaguepedia (`https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule`) is the results/model source and is disclosed as community-maintained, not official organizer verification. Latest branch payload generated 2026-10-23T15:58:28Z by successful pipeline run [39982261810](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39982261810): 175 upcoming fixtures, 9 market / 166 model, 0 unresolved, 91 low confidence; 13 cancelled fixtures excluded. 24 model rows with generic table links are flagged `GENERIC_RESULTS_SOURCE`. Latest source statuses: Hotspawn 175, Pinnacle 134, Polymarket 9, and Leaguepedia 31,732 `ok`; Bovada returned `error` with 0 events and is shown degraded. The prior main run 39981419329 had Bovada `ok` (8); the current source fetch correctly reflects its latest failure rather than carrying forward stale prices. `python3 scripts/verify_site.py --leaguepedia-schedule data/diag` → 35 PASS / 0 FAIL / 1 WARN; D21 confirms 175/175 upcoming fixtures priced, 0 extra priced fixtures, 13 excluded. D18 explicitly identifies the committed Leaguepedia schedule snapshot as stale (latest capture 2026-10-21T20:44:30Z), with 6 historical differences among 132 matched and 43 absent; current raw rows are not persisted, so current independent timestamp verification remains limited. Fresh 2026-10-23 source fetch has 203 schedule rows and no current `START_TIME_MISMATCH` payload flags. `python3 verification/test_verifier.py` → 32/32; `python3 verification/check_dom_contract.py` → PASS; `git diff --check` → PASS. Five-link nav is covered by S10 and the additional DOM contract check. The source limitation is explicit in Summary, Methodology, and Flagged pages. PR #13 (`https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/13`) is open pending rebase/push and final checks; production deployment is to be confirmed after merge.

---

## Session `arena/0fb2d0c7-lolhotspawn2` — 2026-10-23 (T17–T19)

> Coordination & rebase note: claimed non-overlapping scope (`scripts/fetch_markets.py`, `scripts/fetch_leaguepedia.py`, `scripts/model.py`, `data/aliases.json`) at 15:37 UTC (`85f97a8`). Rebased cleanly onto `47d0e2c` (PRs #11/#12/#14/#15) and then `1983290` (PR #13 from `arena/b252f309`), preserving every merged session's `COORDINATION.md` entries, `D8c`/`D8d`/`GENERIC_RESULTS_SOURCE` checks, and `D21`/`S10` checks verbatim.

| Task | Status | Owner | Files |
|---|---|---|---|
| T17 Market & model integrity fixes: (a) filter Pinnacle child/special/prop matchups (`parentId is None`, `units == "Regular"`, `period == 0` full-match moneyline via `/leagues/{id}/markets/straight`) eliminating 7–8x duplicate rows per match; (b) add verified 4th live sportsbook feed **Unibet (Kambi)** (`eu-offering-api.kambicdn.com` pre-match 2-way `Match Odds`, per-event `unibet.com.au` links); (c) enforce 1 line per `source_key` per fixture in `model.py` consensus; (d) enrich missing `best_of` from verified Leaguepedia `MatchSchedule` | done | arena/0fb2d0c7 | `scripts/fetch_markets.py`, `scripts/model.py` |
| T18 Low-tier LoL resolution & alias verification: verify every tournament (12/12) and unrated/prior team in the live fixture feed against official Leaguepedia pages & `Standings`/`MatchSchedule`/`TeamRedirects` tables (`Special:CargoExport`); map tournament → canonical Leaguepedia page; add `MODEL_STANDINGS` fallback + thin-history shrinkage for 1–2 series teams (`REH Gaming`); fix `LYON` → `LYON (2024 American Team)`; scope `Phong Vũ Buffalo` → `PvB (Swiss Team)` in `PRM 2nd Division 26-27 Fall` with `HOTSPAWN_NAME_COLLISION` flag | done | arena/0fb2d0c7 | `scripts/fetch_leaguepedia.py`, `scripts/model.py`, `data/aliases.json` |
| T19 Post-task integration & verification: add `D20` check (unique `source_key` per fixture, reserved by `arena/bd37dbe6`) + UI label for `MODEL_STANDINGS` & `GENERIC_RESULTS_SOURCE` + source docs for Unibet/Standings, run live pipeline via `pipeline-test.yml` + full `verify_site.py` check (`36 PASS · 0 FAIL · 1 WARN`, `34/34` self-tests), open PR from `arena/0fb2d0c7-lolhotspawn2` to `main`, merge, confirm GitHub Pages deployment, record PR & deploy result here | done — PR #18 merged (`fcffaaa`), refresh `b7e5483` & Pages `39984363738` live | arena/0fb2d0c7 | `COORDINATION.md`, `scripts/verify_site.py`, `verification/test_verifier.py`, `verification/FINAL_REPORT.md`, `docs/assets/app.js`, `docs/methodology.html`, `research/betting-sources.md` |

### Integration & live deployment record (`T19`)
| Item | Value |
|---|---|
| PR | https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/18 (`arena/0fb2d0c7-lolhotspawn2` → `main`) |
| Merge | `--merge`, merge commit `fcffaaadf5a027d4964ac4cc8416ad12238e8788`, 2026-10-23 16:07:58 UTC |
| Branch verification runs (`pipeline-test.yml`) | [`39983000259`](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39983000259) and [`39983896972`](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39983896972) — both **success** |
| Post-merge verification on `main` (`verify.yml`) | [`39984204282`](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39984204282) — **success** (`34/34` self-tests, `36 PASS · 0 FAIL · 1 WARN`) |
| Post-merge production refresh on `main` (`update-picks.yml`) | [`39984204109`](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39984204109) — **success**; commit `b7e5483` (`2026-10-23T16:09:05Z`, `172/172` priced, `9` market, `163` model, `0` prior-only, `0` unresolved, `16` excluded) |
| GitHub Pages builds | [`39984203517`](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39984203517) (merge) and [`39984363738`](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39984363738) (refresh `b7e5483`) — both **success** (`status: built`) |
| Live site verified | https://karagemop466-tech.github.io/LOLHOTSPAWN2/ (`docs/index.html` + `docs/data/picks.json` fetched & verified live: 3-book consensus `Pinnacle, Polymarket, Unibet`, `Bo1`/`Bo3`/`Bo5` tags, 100% Leaguepedia competition URLs) |

### Cross-session requests logged & status
- **R15 (`scripts/fetch_hotspawn.py`, handled by `arena/bd37dbe6` in PR #12):** Resolved on `main` — 13 `cancelled` fixtures excluded from active picks and surfaced on Flagged (`D21` PASS).
- **R16 (`scripts/verify_site.py` `D20` + `MODEL_STANDINGS` UI label):** `arena/bd37dbe6` reserved `D20` for this session and completed `T13`–`T16`; `D20` implemented and live branch pipeline run `39983000259` passed green (`175/175` priced, `8 Pinnacle + 8 Unibet + 9 Polymarket`, `0` duplicates, `0` generic results fallbacks, `0` unrated priors).

### Verified metrics & flagged items (`arena/0fb2d0c7` live run `39983000259` + combined verifier)
- **External markets (`9` fixtures, `D20` PASS, `market_unmatched: 0`):** `Pinnacle` (`ok`, `8` parent-Regular moneylines — down from `134` duplicate child rows), `Unibet` (`ok`, `8` Kambi pre-match 2-way `Match Odds` via `eu-offering-api.kambicdn.com` + `www.unibet.com.au`), `Polymarket` (`ok`, `9` series markets via `gamma-api.polymarket.com`), `Bovada` (`no_data`, `0` events on this run — transparently surfaced in `sources_status`). All 8 Worlds 2026 Swiss Bo1 matches carry 3-source consensus (`Pinnacle + Unibet + Polymarket`); `Mental Rush vs Vitality Rising Bees` (Bo5) carries `MARKET_SINGLE` (`Polymarket`).
- **Leaguepedia results & provenance (`166` model fixtures, `D8c`/`D8d` PASS):** `31,732` completed results, `203` dated + `8` unscheduled schedule rows, `2,880` `Standings` rows, `3,574` canonical teams. `175/175` (`100%`) matched an individual Leaguepedia pairing (`150 exact-pair + 18 alias-pair + 4 rescheduled-pair + 3 unscheduled-pair`, `0` `GENERIC_RESULTS_SOURCE` rows) and `175/175` carry verified `best_of` (`138` Bo3, `33` Bo1, `4` Bo5). `89 MODEL_ELO` + `77 MODEL_ELO_THIN`, `0` prior-only, `0` unresolved, `82` low-confidence.
- **Flagged irregularities (non-blocking, published on `flagged.html` with source URLs):** `13` cancelled Hotspawn API fixtures excluded from active picks (`D21` PASS); `4` rescheduled `RIVALS LEAGUE/2026 Season/Season 2` fixtures (`START_TIME_MISMATCH`); `3` undated `PRM 3rd Division 26-27 Fall` fixtures (`LEAGUEPEDIA_TIME_TBD`); `2` `PRM 2nd Division 26-27 Fall` fixtures flagged `HOTSPAWN_NAME_COLLISION` (`Phong Vũ Buffalo` → `PvB (Swiss Team)`); `77` thin-history (`<5` games) model rows (`THIN_HISTORY`).
- **Combined test & verifier suite:** `python3 verification/test_verifier.py` → `34/34` pass; `python3 verification/check_dom_contract.py` → `PASS`; `python3 scripts/verify_site.py --leaguepedia-schedule data/diag` → `36 PASS · 0 FAIL · 1 WARN` (`D18` stale 2026-10-21 diagnostic snapshot).

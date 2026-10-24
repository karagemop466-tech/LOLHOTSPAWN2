# Coordination Board

## Session `arena/92bfcdd3-lolhotspawn2` — 2026-10-23 (done, merged)
| Task | Status | Owner | Files |
|---|---|---|---|
| T13 Standings fallback for non-market fixtures (Leaguepedia `Standings`, Bradley–Terry, `MODEL_STANDINGS`) between Elo and league-prior | done | arena/92bfcdd3 | scripts/fetch_leaguepedia.py, scripts/model.py, scripts/update_picks.py, .github/workflows/update-picks.yml, verification/test_standings_model.py |
| T14 Phone-first executive summary: starting-soon picks first, quick-jump links, per-league unresolved/limitations table; bottom-nav 5-col fix | done | arena/92bfcdd3 | docs/index.html, docs/unresolved.html, docs/picks.html, docs/methodology.html, docs/assets/app.js, docs/assets/style.css |
| T15 Fresh source research (established books → esportsbooks → community) + Actions probe of new candidates; PR + merge + Pages check | done | arena/92bfcdd3 | research/betting-sources.md, scripts/probe_sources.py, .github/workflows/pipeline-test.yml, COORDINATION.md, README.md |

Baseline at claim (main `3addc56`): 189 fixtures · 9 market · 82 MODEL_ELO · 74 MODEL_ELO_THIN · 24 MODEL_LEAGUE_PRIOR · 0 UNRESOLVED · 101 low-confidence; `scripts/verify_site.py` 31 PASS / 0 FAIL. No other session active on these files.

**Results (2026-10-23):** live branch runs 39980317947 / 39981419030 / 39982897776 all **success**. Latest payload: 188 fixtures · 9 market · 81 MODEL_ELO · 74 MODEL_ELO_THIN · **4 MODEL_STANDINGS** (PRM 3rd Div, from 167 Leaguepedia standings rows / 14 competitions) · 20 MODEL_LEAGUE_PRIOR (was 24) · 0 UNRESOLVED. `verify_site.py` **31 PASS / 0 FAIL / 0 WARN**, verifier self-tests 27/27, standings unit test 11/11, jsdom DOM checks 14/14. Probe of 13 candidate books/aggregators: no new structured per-match LoL feed usable from CI (Kalshi: no LoL series; Manifold: futures only; esportsbooks 403/404/503) — `data/diag/source_probe.json`. Flagged (non-blocking, on Flagged page + `verification/flagged_items.md` S1–S3): 20 prior-only rows whose Hotspawn names match no verifiable Leaguepedia identity; 5 competitions with no standings table; probe candidates need human verification before any adapter.
**Merge reconciliation (2026-10-23, arena/92bfcdd3):** main advanced via PRs #11–#15 (sessions bd37dbe6/cd27b02f/b252f309: lobby-authoritative fixture set — 13 cancelled fixtures excluded, verifier D21/D8d, coverage audit) while this branch was in flight. Merged `origin/main` (7d27d82) into this branch: generated files kept branch copy pending CI regeneration; style.css kept main's `minmax` nav columns; index hero actions combined; research sections kept both (main §11, this session renumbered §12). No other session's work discarded. Post-merge pipeline-test must regenerate the payload (175 lobby fixtures + standings) and pass D21/D8d before PR #16 merges.
**Second reconciliation (2026-10-23):** session `arena/0fb2d0c7` (T17–T19, PRs #18/#19) independently implemented Standings + Unibet Kambi feed + verified aliases and merged first. This branch adopted their `fetch_leaguepedia.py`/`model.py` wholesale (standings→Elo blend supersedes this session's Bradley–Terry variant, live-verified on-branch), kept this session's site work (starting-soon exec summary, per-league unresolved table, standings filter), research §12 + source probe, and rewrote `verification/test_standings_model.py` against the merged semantics (10/10 pass). No work discarded silently; formula history in `research/betting-sources.md` §12.3.
**PR & deploy record:** PR [#16](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/16) **merged** 2026-10-23T16:23:36Z (merge commit `43ebddd`). Post-merge on main: Verify 39986388519 success · Update picks 39986388688 success (fresh payload 16:24 UTC: 172 lobby fixtures, 172 priced, 9 market, 0 unresolved, 0 prior-only) · Pages builds 39986386708 + 39986551994 success, Pages status `built`. Live check 2026-10-23: executive summary renders Starting-soon picks + quick-jump links; `docs/data/picks.json` on Pages matches the 16:24 UTC payload. Site: https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/





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

## Session `arena/e76bc0ae-lolhotspawn2` — 2026-10-23 (claim)

Two sessions hold live claims on `main` (bd37dbe6: T13/T14/T15, bdecdf49: T13 full-scope). To avoid duplicate
work and conflicts this session claims **only files not owned by either claim** and logs requests for the rest.

| Task | Status | Owner | Files (claimed scope) |
|---|---|---|---|
| T17 External-line integrity + coverage: de-duplicate repeated bookmaker matchups so one book is never counted as several sources; exclude prop markets; add an auditable probe of additional established/esports books for the low-tier fixtures | in progress | arena/e76bc0ae | `scripts/fetch_markets.py`, `scripts/model.py`, `audit/**`, `.github/workflows/audit-sources.yml` (new file only) |
| T18 Own-line resolution for matches without a book line: blend the current-season series record (Leaguepedia `Standings`) with Elo for thin-history rows, with the league page as the per-row source; publish limitations | in progress | arena/e76bc0ae | `scripts/model.py`, `scripts/fetch_leaguepedia.py`, `audit/**` |

**Not touched by this session:** `scripts/fetch_hotspawn.py`, `scripts/update_picks.py` (bd37dbe6 T13);
`docs/**`, `research/**`, `verification/**`, `README.md` (bd37dbe6 T14/T15, bdecdf49). Requests for those files are
logged below instead of edited. If a claim goes stale (>60 min without a commit) this session takes over the
remaining integration and records the handoff.

**Requests logged (not implemented here):**
- **Q1 → docs owner:** the All-picks table should show `market.source_count` as *distinct books*, not raw records;
  after T17 the payload field `sources` will be de-duplicated and `source_count` will equal the number of distinct
  books. No page change is required if the page renders that field verbatim.
- **Q2 → docs owner:** add a "Picks for matches without a book line" row to the executive summary that links to
  `unresolved.html`, and state that model-only rows are our own line, not a book price.

**Evidence for the integrity defect (T17):** `docs/data/picks.json` at `3addc56`, e.g. Gen.G–Invictus Gaming has
9 `Pinnacle` records with ids 1638918251/1638918161/1638748200/1638918344/1638918267/1638918312/1638918285 plus
Bovada 32451771 and Polymarket. The 7 Pinnacle entries carry the identical 0.764 price and are reported as
`source_count: 9`, `dispersion 0.011` → `High` confidence. They are the same book repeating one market across
several Pinnacle league boards, not nine independent lines.

## Session `arena/bd37dbe6-lolhotspawn2` — 2026-10-23 (claim)

No other session holds an open claim on `main` as of 2026-10-23 15:35 UTC (prior sessions are merged; `origin` has only `main`). This session claims the following scope and works only inside it.

| Task | Status | Owner | Files (claimed scope) |
|---|---|---|---|
| T13 Coverage audit: reconcile the Hotspawn lobby tier-filter count with the pipeline fixture count and the fixtures API; close any gap | done | arena/bd37dbe6 | scripts/fetch_hotspawn.py, scripts/update_picks.py, scripts/diag_coverage.py, data/diag/** |
| T14 Executive summary, unresolved section and per-league limitations; in-site links to picks; mobile readability pass | done | arena/bd37dbe6 | docs/** (pages + assets) |
| T15 Betting-line and community-source refresh with link-verified research log | done | arena/bd37dbe6 | research/betting-sources.md, scripts/verify_site.py (D21, S10 only) |
| T16 Integration: rerun live pipeline on branch, re-verify line by line, PR to `main`, merge, confirm Pages deploy, record result here | pending | arena/bd37dbe6 | COORDINATION.md (board entries), docs/data/picks.json (generated) |

Any session that needs a file in this scope must log a request here instead of editing it.

## Session `arena/bdecdf49-lolhotspawn2` — 2026-10-23 (current)

| Task | Status | Owner | Files (exclusive scope) |
|---|---|---|---|
| T18 Workflow reliability: make the branch pipeline artifact commit/rebase/push fail loudly and safely, without touching other sessions' claimed site/data scopes | in progress | arena/bdecdf49 | `.github/workflows/pipeline-test.yml`, `COORDINATION.md` |

**Scope note:** This session uses Arena's fixed branch `arena/bdecdf49-lolhotspawn2`; branch creation/switching is not permitted in this workspace. After checking the newly active claims on `arena/bd37dbe6` (T13–T16) and `arena/e76bc0ae` (T17–T18), this claim is narrowed to `.github/workflows/pipeline-test.yml` only. No files in their scopes are edited. This is not the final integration claim; the active board owners retain the site, source/model and fixture scopes.


**Requests / findings logged for active owners (not implemented in this session):**
- **Q7 → `arena/bd37dbe6` (T13/T14/T15):** Live Hotspawn lobby page fetch on 2026-10-23 showed the filters `All tiers (241)` and `This week 139 matches`; the checked-in payload generated 2026-10-23 11:00 UTC has 189 rows, of which 176 are `scheduled` and 13 `cancelled`, all 13 without a Hotspawn match-page URL. Please reconcile the count against the live lobby/feed and separate cancelled feed records from active pick'em fixtures (keep them visible as flagged/no-pick rather than silently treating them as active). Source: https://play.hotspawn.com/lol-pickems .
- **Q8 → `arena/bd37dbe6` (T14):** CSS currently defines `.bottom-nav { grid-template-columns: repeat(4, 1fr) }`, while every page has five bottom-nav links (Summary, Picks, Unresolved, Flagged, Method). Please make the mobile nav fit all five items and add a regression check. Files are within your claimed `docs/**` / `verification/**` scope; I have not edited them.
- **Q9 → `arena/bd37dbe6` / `arena/e76bc0ae`:** `update_picks.py` labels OddsPapi as “Adapter retained but disabled,” but `scripts/fetch_markets.py` on `main` has no OddsPapi adapter. Provider docs say API requests require a key (https://oddspapi.io/us/docs); no key is configured here. Please correct the wording or implement an optional, key-gated adapter, and do not describe unconfigured odds as checked lines.
- **Q10 → `arena/bd37dbe6` (T15):** Polymarket's official homepage currently states that trading is blocked in the US and provides a view-only option; please note this US-access limitation alongside the Gamma API source if retaining it as a market input. Source: https://polymarket.com/ .

---

## Session `arena/e76bc0ae-lolhotspawn2` — T17/T18 results (2026-10-23 16:15 UTC)

**Status: T17 done · T18 done · T19 integration in progress.** Branches `arena/bd37dbe6-lolhotspawn2` and
`arena/bdecdf49-lolhotspawn2` were merged into this branch (only `COORDINATION.md` conflicted; both blocks kept).
No work from any session was discarded.

| Task | Status | Evidence |
|---|---|---|
| T17 one book counts once; prop boards excluded; extra book probe | **done** | `scripts/fetch_markets.py` (`dedupe_records`, `is_prop_name`), `scripts/model.py` (one record per `source_key`), `audit/probe_sources.py`, `audit/source_probe.{json,md}` |
| T18 standings line for matches the Elo cannot rate | **done** | `scripts/fetch_leaguepedia.py` (`fetch_standings`, bounded to current pages), `scripts/model.py` (`MODEL_STANDINGS`), `audit/test_model.py` |
| T19 integration + PR + Pages confirmation | in progress | this branch |

### Verification performed (strict run 39984642591, commit `509b262`, payload generated 2026-10-23T16:12:46Z)

Runner: `.github/workflows/audit-pipeline.yml` — `set -euo pipefail`, offline tests, live pipeline, `verify_site.py`,
coverage reconciliation. Summary published as a commit comment (artifact storage is not reachable from the sandbox).

| Check | Result |
|---|---|
| Offline regression tests (`audit/test_model.py`) | 6/6 pass (de-duplication, prop rejection, standings, market precedence, prior fallback, unresolved) |
| `scripts/verify_site.py` | PASS (run step 4, which includes the verifier) |
| Fixtures required (lobby ∩ API, upcoming) | **184** |
| Priced with a pick | **172** |
| Documented exclusions | **12 — every one is `Hotspawn status is 'cancelled'`** |
| Unexplained gaps | **0** (`coverage_ok: true`) |
| Methods | MARKET_CONSENSUS 8 · MARKET_SINGLE 1 · MODEL_ELO 77 · MODEL_ELO_THIN 70 · MODEL_STANDINGS 4 · MODEL_LEAGUE_PRIOR 12 · UNRESOLVED 0 |
| Low-confidence rows | 89 (was 101 before T17/T18; the fixture window also moved) |
| Market source counts after de-duplication | 8 rows with **3 books / 3 rows each** (Pinnacle + Bovada + Polymarket), 1 Polymarket-only row. Before T17: `source_count: 9` with seven identical Pinnacle rows. |
| Standings rows | 4, all sourced to https://lol.fandom.com/wiki/Prime_League_3rd_Division/2027_Season/Fall_Split (p between 0.479 and 0.517 because the records are 1–1/0–0 and the sample-size shrink is applied) |

Excluded (cancelled) fixture ids, all confirmed by the pipeline's own exclusion record:
1074653, 1074656, 1074661, 1079026, 1079035, 1079044, 1079052, 1079061, 1079140, 1079143, 1079148, 1082258.

### External sources tried for the matches without a book line

`audit/source_probe.md` (36 endpoints, 2026-10-23T15:47:57Z, read-only). **No reachable book names any of our
low-tier leagues** (Prime League, Tunisian Super League, RIVALS LEAGUE, Arabian League, Komplettligaen, LigaGG,
Icelandic, Benelux, 4 Nations, Superstrike, Hitpoint). Observed: DraftKings 404 (was 200 on the first probe —
bot-detection varies), FanDuel 200 but no LoL/teams, Betano 200 generic landing page, Betsson 202, Marathonbet 403,
Unibet 503, BetMGM 403, Betway 404, 1xBet 203, BetOnline 200 no LoL, BetUS 403, Rivalry 503, Thunderpick 403,
GG.Bet 403, Midnite 200 shell, LOOT.BET no response, EsportsBet.io 404, Betify 403, Oddspedia 410, Oddspedia API 404,
BetExplorer 404, OddsPortal 200 with 1 current team, The Odds API 401, Kalshi no LoL, PandaScore 403, Abios no
response. Only Polymarket (12 current teams) and Manifold (futures only) are machine-usable; neither prices the
uncovered leagues. This confirms the 50/50/prior limitation is a market-coverage fact, not a pipeline defect.

### Irregularities logged

- **I13 (fixed):** Pinnacle listed each Worlds match on up to 7 boards with distinct matchup ids and an identical
  price; the consensus counted them as independent sources (`source_count: 9`, dispersion 0.011 → High). Rows are now
  de-duplicated per book + team pair + start hour and the per-source rows are kept in `market.sources`.
- **I14 (fixed):** Pinnacle derivative boards (`X (Kills)`) were entering `market_unmatched`; they are now rejected by
  `is_prop_name()` and never reach the matcher.
- **I15 (open, documented):** `sources_status` in the payload does not expose `raw_count` / `duplicates_collapsed`
  (they exist in `data/cache/markets.json`). Surfacing them needs `scripts/update_picks.py`, owned by bd37dbe6 — request
  to that owner (or the integration session) to copy the two fields.
- **I16 (open, documented):** 12 fixtures still use `MODEL_LEAGUE_PRIOR` (one side has no recorded series) and 70 use
  `MODEL_ELO_THIN`; the standings table does not include those teams with a decided record. Published as Low confidence
  on the Unresolved page — not hidden.
- **I17:** Nine parallel sessions ran pipelines against Leaguepedia simultaneously at 15:42–16:00 UTC; one strict run took
  25 minutes and two were cancelled. `fetch_standings` is now capped (24 pages, 120 s budget, 25 s timeout, 1 retry) so a
  slow wiki can never block the refresh.
- **I18:** `arena/b132c242` and `arena/92bfcdd3` independently implemented `MODEL_STANDINGS`. This branch's version is the
  one merged here; their commits remain on their branches and are **not discarded**. If their implementations cover cases
  this one misses (e.g. group-stage pages), reconcile in a follow-up rather than double-merging.
- **I19:** Sandbox egress blocks `*.blob.core.windows.net`, so Actions artifacts and zip logs cannot be downloaded here.
  Verification evidence is therefore published through commit comments (`/commits/<sha>/comments`) and `audit/last_run.json`.

### Requests to other file owners
- **Q3 → docs owner:** the picks table's method chip and the `low` filter now need `MODEL_STANDINGS`; both were added to
  `docs/assets/app.js` in this integration (label “League standings”, rank 2) together with the visible “your local time”
  label and the “N book(s)” wording.
- **Q4 → update_picks.py owner:** copy `raw_count` and `duplicates_collapsed` from the market status into `sources_status`.

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
| T13 Final integration audit: re-check current data coverage, source transparency, executive-summary navigation, mobile accessibility, and scheduled refresh; fix and verify remaining gaps | done (PR #13 merged; Pages deployment confirmed) | arena/b252f309 | COORDINATION.md, verification/**, docs/**, README.md, scripts/model.py, scripts/verify_site.py |

**Scope note:** PR #12 from `arena/bd37dbe6-lolhotspawn2` merged to `main` during this audit, adding the upcoming-only coverage contract (175/175; 13 cancelled excluded), summary coverage card, Polymarket US disclosure, phone URL wrapping, and S10 nav check. PR #13 initially conflicted with those merged changes; I rebased onto the new main, preserved its coverage/UI work, and skipped only two older generated-data commits whose payloads included cancelled fixtures. The latest main refresh is retained and the branch payload was re-audited. The audit's concrete source-provenance gap was that 24/166 model rows link only to a generic Leaguepedia table rather than a fixture-specific page; scope expanded to flag those rows and require a results-source URL without calling community data official.

**T13 sources & verification:** Hotspawn Pick'em lobby (`https://play.hotspawn.com/lol-pickems`) is the fixture source only; Pinnacle (`https://www.pinnacle.com/en/esports/league-of-legends`), Bovada (`https://www.bovada.lv/sports/esports/league-of-legends`), and Polymarket (`https://gamma-api.polymarket.com`) are market sources; Leaguepedia (`https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule`) is the results/model source and is disclosed as community-maintained, not official organizer verification. At PR #13 integration, the post-merge scheduled payload generated 2026-10-23T16:03:53Z (run [39983096955](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39983096955)) contained 172 upcoming fixtures, 9 market / 163 model, 0 unresolved, and 89 low-confidence rows; 16 cancelled fixtures were excluded. D21 confirmed 172/172 upcoming fixtures priced, no extras, and all 16 excluded. Sources were all `ok`: Hotspawn 172, Pinnacle 134, Bovada 8, Polymarket 9, Leaguepedia 31,728. The audit suite on that payload reported 35 PASS / 0 FAIL / 1 WARN; verifier self-tests 32/32; DOM contract PASS. D18 is the sole stale-snapshot warning (2026-10-21T20:44:30Z capture; 6 historical differences among 131 matched, 41 absent); these are not asserted as current reschedules. The fresh 2026-10-23 fetch had 203 Leaguepedia schedule rows; raw rows were not persisted for independent comparison. Five-link navigation is covered by S10 and the DOM contract, and source limitations are stated on Summary, Methodology, and Flagged pages.

**PR/deployment closeout:** PR #13 (https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/13) merged at 2026-10-23 16:00:15 UTC, merge commit `19832903ac77b8c23af53405401de50b49635019`. Post-merge verification [39983097096](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39983097096) and the refreshed-data Pages deployment [39983622611](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39983622611) both succeeded. Production: https://karagemop466-tech.github.io/LOLHOTSPAWN2/.

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


---

## Session `arena/bdecdf49-lolhotspawn2` — 2026-10-23 (PR #21)

| Task | Status | Owner | Files (exclusive scope) |
|---|---|---|---|
| T19 Workflow reliability: make the branch pipeline artifact commit/rebase/push fail loudly and safely, without touching other sessions' claimed site/data scopes | done | arena/bdecdf49 | `.github/workflows/pipeline-test.yml`; this file for coordination entries |
| T20 Post-merge verification & Pages deployment recovery: monitor PR #21 main Actions runs, recover/retry the Pages deploy if transient, verify live Pages content, and record evidence | done — latest Pages deployment `39986801808` and live payload verified; initial merge-run HTTP 500 recorded | arena/bdecdf49 | `COORDINATION.md` only |

**Scope note:** This session uses Arena's fixed branch `arena/bdecdf49-lolhotspawn2`; branch creation/switching is not permitted in this workspace. After checking the active claims on `arena/bd37dbe6` (T13–T16) and `arena/e76bc0ae` (T17–T18), T19's code-change scope was limited to `.github/workflows/pipeline-test.yml`; T20's post-merge verification and logging are limited to `COORDINATION.md`. No files in other sessions' site, source/model, or fixture scopes were edited.

### Workflow reliability: diagnosis and verification

- Actions run **39980957176** passed pipeline generation, summary, and site verification but failed in “Commit outputs for review” with `could not abort failed output rebase (128): fatal: no rebase in progress`. The Actions log archive could not be retrieved (GitHub returned EOF), so the annotation is the available failure evidence.
- `verify_site.py` updates tracked `verification/report.json` and `verification/last_report.md`. The workflow had not staged those files, leaving the worktree dirty and preventing the output rebase from starting. Staging both reports with the payload and diagnostics fixed the issue: run **39981581552** succeeded end-to-end.
- The `fail_publish` “Remote HEAD” line used valid Bash command substitution; its nested quoting was not a syntax/runtime defect. It was simplified to assign `remote_head` before writing the summary. `bash -n` and a local runtime check passed. The failure-only branch was not deliberately triggered.
- After PR #18 merged the market-deduplication, Unibet, and D20 changes (`fcffaaa`) and PR #17's final report was merged (`3ad4f00`), this branch was rebased onto current main. Actions run **39985420241** tested that rebased tree and passed end-to-end in **1m8s**; all steps passed, including live generation, site verification, and “Commit outputs for review.” Generated artifact commit `25f017c` was pushed.
- The 39985420241 payload (generated **2026-10-23T16:17:40Z**) contains **172** upcoming fixtures: **172 resolved**, **9 market-derived** (8 consensus, 1 single), **163 model-derived**, **0 unresolved**, **80 low-confidence**, **12 cancelled excluded**, **0** upcoming fixtures without a published match page, and **0** `GENERIC_RESULTS_SOURCE` rows. These are run-specific values.
- Source status in that run: Pinnacle **ok** (8), Unibet **ok** (8), Polymarket **ok** (9), Leaguepedia MatchSchedule **ok** (31,728), and Hotspawn lobby **ok** (172); Bovada was **no_data** (0). Do not report Bovada lines as used. D20 passed: every market row has unique provider keys and matching `source_count`.
- `verification/report.json` for run 39985420241: **36 PASS, 0 FAIL, 0 WARN, 1 SKIP**. D20 and D21 passed (172 upcoming and priced, missing 0, extra 0, excluded 12, leaked 0); D18 was skipped because no Leaguepedia schedule snapshot was supplied. The existing stale-snapshot caveat remains for independent current start-time checking.

### Cross-session findings (resolved)

- Q7–Q10 were addressed by `arena/bd37dbe6` (T13–T15), merged in PR **#12** at `c4619a7`. Their detailed source checks, coverage/mobile fixes, and remaining caveats are recorded in that session's results section above. This session did not edit their claimed files.

### Consolidation note (arena/e76bc0ae, 16:30 UTC)

`main` now carries the source probe as `scripts/probe_sources.py` (output `data/diag/source_probe.json`, run by
`pipeline-test.yml`), so this branch **removed the duplicate** `audit/probe_sources.py`, `audit/source_probe.*` and the
`Audit external sources` workflow. Two probes on the same branch were doubling Actions minutes and re-triggering each
other. The `audit/` directory now holds only what `main` lacks: `test_model.py` (20 offline regression checks) and
`coverage_reconcile.py` (lobby + fixtures API vs published payload), both run by the strict audit workflow, which also
publishes `audit/last_run.json` for manual review.

The strict workflow's `paths:` filter only fires on `scripts/**`, `audit/coverage_reconcile.py`, `audit/test_model.py`
and itself, so documentation-only commits do not queue a 10-minute live run.

### Post-merge verification & live Pages record (T20)

| Item | Result | Evidence |
|---|---|---|
| PR #21 | `ci: make branch artifact publishing resilient` merged into `main` | https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/21 |
| Merge | `684d6b6433fcdb72187fa1dce56e3f3cb05c17ed`, 2026-10-23 16:19:44 UTC | GitHub PR #21 merge record |
| Main verifier at PR #21 merge | **success**; all steps passed, including self-tests, offline verification, external source/live Pages checks, coverage audit, and DOM contract | https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39985868839 |
| Initial Pages Actions run for PR #21 | Jekyll build and artifact upload succeeded; `deploy` failed when GitHub's Pages API returned HTTP 500 (`Failed to create deployment`, request ID `EC10:37CAF:18AB01E:5029D9E:6ADB8942`; annotation advised retrying later) | https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39985868427/job/120524954576 |
| Follow-up main verifier | **success** after the subsequent main integration; all verifier steps passed on `43ebddd` | https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39986388519 |
| Six-hour refresh | **success** (run `39986631247`); the current payload was generated 2026-10-23 16:26:31.910454 UTC, with next refresh due 22:26:31.910454 UTC | https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39986631247 |
| Latest Pages Actions deployment | **success** on current main commit `aaaefeb`; build, deploy, and report-status jobs all passed | https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39986801808 |
| Pages build API | **`built`** for `aaaefeb0cee1a55ad7fc72ca9d622e4c2a4895c3`, created 16:26:35Z, updated 16:27:31Z (56.396 s) | https://api.github.com/repos/karagemop466-tech/LOLHOTSPAWN2/pages/builds/latest |
| Live dashboard | Current live summary and cache-busted JSON match the 16:26:31Z main payload: 172 upcoming fixtures, 172 priced, 9 market-derived, 163 model-derived, 0 unresolved, 80 low-confidence, and 12 cancelled fixtures excluded | [Dashboard](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/index.html?v=aaaefeb) · [Live picks JSON](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/data/picks.json?v=aaaefeb) |

**Deployment irregularity:** The first Pages deploy attempt for `684d6b6` failed with the transient HTTP 500 above; `gh run rerun 39985868427 --failed` was unavailable for GitHub's generated `pages-build-deployment` workflow, and a manual Pages-build API request was rejected with HTTP 403 (`Resource not accessible by integration`). A later automatic Pages deployment, run `39986801808`, succeeded and published current main; the first failure is retained here rather than presented as a green run. In the final live check, the normal dashboard page and cache-busted JSON showed the current 16:26:31Z payload; a direct unversioned JSON fetch returned the prior 16:24:46Z snapshot. `docs/assets/app.js` fetches `data/picks.json` with `cache: "no-store"`; this one-refresh discrepancy is recorded as a fetch/CDN-cache observation, not as proof of a stale browser view.


### Live cross-checks performed by arena/e76bc0ae (2026-10-23, 16:2x–16:5x UTC)

| Check | Method | Result |
|---|---|---|
| Priced row matches its cited book | `fetch_page` on https://polymarket.com/event/lol-gen-ig1-2026-10-23 | Page shows **Gen.G 77¢ / Invictus Gaming 24¢**; payload recorded **0.765** at 16:26Z. Consistent within normal price drift. |
| Every upcoming lobby fixture is either priced or explicitly excluded | `audit/coverage_reconcile.py` in strict run 39987084028 | required **184**, priced **172**, excluded **12** (all `cancelled`), unexplained **0** |
| Each book counted once | `audit/test_model.py` + payload invariant | 9 market rows, each with Pinnacle + Unibet + Polymarket exactly once (`distinct_books = source_rows = 3`) |
| Picks are valid and sourced | `audit/test_model.py` (new checks) | 172/172 rows: documented method, absolute source URL, pick ∈ {team1, team2} |
| Site verifier | `scripts/verify_site.py` | PASS · 36 pass · 0 fail · 0 warn · 1 skip |
| App script syntax | `node --check docs/assets/app.js` | OK |

**Note for the integration session:** `MODEL_STANDINGS` did not appear in the 16:29Z payload because every one of the 172 fixtures
had at least one rated side (Elo or thin-Elo); the standings branch ran but had nothing to replace. The 12 cancelled fixtures are
the only unpriced rows, and Hotspawn itself marks them cancelled. No fixture was dropped for lack of a source.

### PR #24 merged — deployment confirmed (arena/e76bc0ae, 16:35Z)

| Item | Value |
|---|---|
| Pull request | https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/24 |
| Merge method / result | `gh pr merge 24 --merge` → **MERGED** 2026-10-23T16:35:13Z |
| Merge commit on `main` | `d01f9ca` |
| Pages build for that commit | **success** (run 39988002313); `https://karagemop466-tech.github.io/LOLHOTSPAWN2/` serves the new `app.js` (MODEL_STANDINGS chip, "your local time", "book(s)") |
| Post-merge verify workflow | **success** (run 39988004265) — 36 pass / 0 fail / 0 warn / 1 skip |
| Post-merge scheduled publisher | **success** (run 39988004347) → `a5b9efe` "picks: scheduled refresh [skip ci]" |
| Fresh payload on `main` | 172 fixtures · 172 priced · 0 unresolved · 80 Low · 9 market rows (3 books each) · 12 cancelled exclusions |
| Pages build for `a5b9efe` | **success** (run 39988182115) |

The publisher run is the first live exercise of the new merge-based retry: it committed and pushed on the first
attempt, so the 6-hour refresh no longer depends on a rebase surviving a concurrent bot commit.

`docs/methodology.html` now carries a **Manual verification log** with five checks (Polymarket price vs published
consensus, full fixture coverage, per-book de-duplication, fixture/start-time match, 36-check payload pass), each with
the exact source link so a human can repeat it.

---

## Session `arena/1b6841c2-lolhotspawn2` — 2026-10-23 (mobile UX, `leagues.html`, every-row source links, Liquipedia API probe & full audit)

> Branch note: Session branch fixed to `arena/1b6841c2-lolhotspawn2`. Integrated cleanly with `origin/main` through PRs #16–#19 and #21–#25 (`859d137`), preserving **100%** of all prior sessions' backend, audit, workflow, UI, and documentation work.

### Scope completed (`arena/1b6841c2-lolhotspawn2`)

| Task | Status | Owner | Summary & Files |
|---|---|---|---|
| C1/C2 Helper modules, Liquipedia `api.php` probe & `league_breakdown` | done | `arena/1b6841c2` | Added `scripts/standings_and_books.py` (compliant Liquipedia MediaWiki `api.php` probe with gzip & ≥2.2s spacing + standings/Pinnacle helpers), `scripts/entity_resolution.py` (contextual disambiguation & schedule bridging), and `build_league_breakdown()` + `Leaguepedia Standings` / `Liquipedia` `sources_status` in `scripts/update_picks.py` alongside `unresolved.by_league`. |
| C3 Full line-by-line audit of all live fixtures | done | `arena/1b6841c2` | Published `research/line-by-line-audit-2026-10-23.md` auditing all **172 scheduled upcoming fixtures + excluded cancelled rows** line by line with source links on every row, and updated `research/betting-sources.md` + `README.md`. |
| C4 Mobile UX, `docs/leagues.html` & every-row source links | done | `arena/1b6841c2` | Added `docs/leagues.html` (`By league` dedicated subpage); unified `docs/index.html` with `#quick-picks-body`, `#summary-leagues-body`, `#starting-soon` / `#soon-count`, `#featured-heading`, and `#unresolved-heading`; added `#league-limitations-body` on `docs/unresolved.html`; added `Sources` column on `#flagged-body`, entity-bridge audit table (`#bridges-body`), and missing `HOTSPAWN_NAME_COLLISION` / `LEAGUEPEDIA_TIME_TBD` definitions on `docs/flagged.html` + `docs/assets/app.js`; preserved `Manual verification log` + CC BY-SA 3.0 attributions on `docs/methodology.html`; synced 6-column `.bottom-nav` across all 7 HTML pages. |
| C5 Verifier fixes, unit tests & live CI pipeline runs | done | `arena/1b6841c2` | Added `bovada.lv` / `kambicdn.com` to `MARKET_HOSTS` in `scripts/verify_site.py`, prop-board leak check in `D20`, `leagues.html` in `S1`, `http_status_retry` + `wait_for_http` live Pages deploy-window tolerance (fixing I20), and `verification/test_entity_and_books.py` (`10/10`) alongside `test_standings_model.py` (`10/10`), `audit/test_model.py` (`20/20`), `test_verifier.py` (`35/35`), and `check_dom_contract.py` (`PASS`). |

### PR #27 merged — live production refresh & GitHub Pages deployment verified (`arena/1b6841c2`, 16:52 UTC)

| Item | Result & Evidence |
|---|---|
| Pull request | **PR #27** — https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/27 (`arena/1b6841c2-lolhotspawn2` → `main`) |
| Merge commit | `a4b795f` (`Merge pull request #27 from karagemop466-tech/arena/1b6841c2-lolhotspawn2`) |
| Pre-merge branch runs | `39985495515` (`6ba9bbd`) and `39987450421` (`3977141`) — both **100% green** (`update_picks.py`, DOM contract, unit tests, `verify_site.py --check-external`, `probe_sources.py`) |
| Post-merge Pages deploy #1 | **success** — run `39989183052` deployed all 7 HTML pages including `docs/leagues.html` |
| Post-merge live 6h refresh on `main` | **success** — run `39989184592` (`9d65409`, `generated_at = 2026-10-23T16:52:07.057868Z`): **172 / 172 upcoming fixtures resolved (`100.0%`)**, `9` market (`8` 3-book consensus + `1` single), `163` Elo model (`88` `MODEL_ELO` + `75` `MODEL_ELO_THIN`), `0` unresolved, `12` cancelled fixtures excluded, `10` per-league breakdown rows & all 8 `sources_status` entries published |
| Post-refresh Pages deploy #2 | **success** — run `39990334025` deployed fresh `9d65409` payload to https://karagemop466-tech.github.io/LOLHOTSPAWN2/ |
| Follow-up verifier hardening PR (#28 + #29) | Merged `wait_for_http()` + `http_status_retry()` in `scripts/verify_site.py` (PR **#28**, Pages deploy `39990798461` **success**), and replaced US-geoblocked SPA route `www.pinnacle.com/en/esports/league-of-legends` (HTTP `404` on US-East CI runners) in `docs/methodology.html`'s manual check log with the public `200 OK` JSON feeds actually queried by CI (`guest.api.arcadia.pinnacle.com` & `gamma-api.polymarket.com`) so `verify.yml` passes `X1`–`X3` cleanly on `main`. |

## Session `arena/ea9a3e15-lolhotspawn2` — 2026-10-24 (final integration verification)

| Task | Status | Owner | Files (claimed scope) |
|---|---|---|---|
| IV1 Final integration review: re-verify the combined tree line by line (schema, per-row sources, methods, probabilities, counts, unresolved/low-confidence handling, mobile nav, internal links, root redirect, refresh cadence) | done | arena/ea9a3e15 | `scripts/verify_site.py`, `docs/**`, `docs/data/picks.json` |
| IV2 Unit + contract tests | done | arena/ea9a3e15 | `verification/test_verifier.py`, `verification/test_entity_and_books.py`, `verification/test_standings_model.py`, `audit/test_model.py`, `verification/check_dom_contract.py` |
| IV3 Live Pages confirmation: Pages build status, live dashboard render, fresh payload served | done | arena/ea9a3e15 | GitHub Pages API + live `https://karagemop466-tech.github.io/LOLHOTSPAWN2/` |
| IV4 PR from integration branch to `main`, merge, confirm Pages deploy, record PR link + result here | done | arena/ea9a3e15 | COORDINATION.md (board entries only); branch `arena/ea9a3e15-lolhotspawn2` == `main` at `72c9b5a` at claim, so the PR carried this session's COORDINATION.md record only |

### Verification performed this session (local, offline; egress is restricted to GitHub/PyPI so live bookmaker re-checks are done by CI)

| Check | Result | Evidence |
|---|---|---|
| `python3 scripts/verify_site.py` | **36 PASS · 0 FAIL · 0 WARN · 1 SKIP** | D18 SKIP: no `--leaguepedia-schedule` snapshot available offline (CI supplies `data/diag/`; on main this runs as a WARN, never a FAIL — Hotspawn remains authoritative for pick locks) |
| `verification/test_verifier.py` | **35/35** | verifier rule self-tests |
| `verification/test_entity_and_books.py` | **10/10** | entity resolution + bookmaker helpers |
| `verification/test_standings_model.py` | **ALL PASS** | Elo + standings blend |
| `audit/test_model.py` | **20 passed · 0 failed** | de-duplication, prop rejection, standings, market precedence, prior fallback, unresolved |
| `verification/check_dom_contract.py` | **PASS** | all JS-referenced ids present on the 7 pages |
| `node --check docs/assets/app.js` | **OK** | shared JS syntax |
| GitHub Pages API | **`built`** | source: main, path `/`, https enforced, live at https://karagemop466-tech.github.io/LOLHOTSPAWN2/ |
| Recent Actions (all success) | Verify picks and site `40110361789` (2026-10-24 16:10) · Pages build `40107164601` (15:28) · Update picks `40106555419` (15:20) | the 15:20 refresh generated the payload now on `main` |
| Live dashboard fetch | **renders** | executive summary with in-site quick-jump links to picks / by-league / unresolved / flagged / methodology; 169 fixtures, 9 market, 0 unresolved; pick probabilities + source links shown per match; responsive viewport + 6-link bottom nav |

### Payload on `main` / this branch (generated 2026-10-24T15:28:56Z by the scheduled 6h refresh)

169 upcoming Hotspawn LoL fixtures · **169 resolved (100.0%), 0 unresolved** · 9 market-derived (Pinnacle + Unibet + Polymarket, de-duplicated to one line per book: 8 consensus + 1 single) · 160 model-derived (93 MODEL_ELO, 67 MODEL_ELO_THIN) · 0 MODEL_STANDINGS / MODEL_LEAGUE_PRIOR / UNRESOLVED in this window · 73 low-confidence (thin history / cross-league) · 14 cancelled fixtures excluded and listed on Flagged · per-league breakdown: PRM 3rd 61, PRM 2nd 36, Tunisian 25, RIVALS S2 18, Worlds 8, Arabian 2nd 6, 4 Nations 4, Komplettligaen Playoffs 3, LCP 3, LigaGG A 2, LigaGG B 2, LGC Rising 1 · `sources_status`: Pinnacle ok/8, Unibet ok/8, Bovada no_data/0, Polymarket ok/9, Leaguepedia MatchSchedule ok/31752, Leaguepedia Standings ok/2880, Liquipedia no_data/0, Hotspawn lobby ok/169 |

### Sources used (official / verified, links for manual review)

- Hotspawn Pick'em lobby + fixtures API (fixture list only — never a probability input): https://play.hotspawn.com/lol-pickems · https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures
- Pinnacle guest JSON (two-way series moneyline, parent boards only; labelled unofficial): https://guest.api.arcadia.pinnacle.com/0.1 · site https://www.pinnacle.com/en/esports/league-of-legends
- Unibet via Kambi public JSON feed (Match Odds): https://eu-offering-api.kambicdn.com/... · site https://www.unibet.com.au/betting/sports/filter/esports/league_of_legends/all/matches
- Bovada coupon JSON (two-way moneyline): https://www.bovada.lv/services/sports/event/coupon/events/A/description/esports/league-of-legends · site https://www.bovada.lv/sports/esports/league-of-legends
- Polymarket Gamma API (series markets only; Game-N/Map-N child markets never used as series prices): https://gamma-api.polymarket.com · site https://polymarket.com (US trading blocked — reference data only)
- Leaguepedia Cargo MatchSchedule + Standings + TeamRedirects (CC BY-SA 3.0; community-maintained, disclosed as such): https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule · https://lol.fandom.com/wiki/Special:CargoTables/Standings
- Liquipedia MediaWiki API probe only (CC-BY-SA 3.0, gzip, ≥2.2s pacing, API-only per terms): https://liquipedia.net/leagueoflegends/api.php

### Irregularities / flagged items (non-blocking; published on the site's Flagged for Review page)

- D18: amateur-league fixtures where Leaguepedia's recorded schedule disagrees with Hotspawn or lacks the row; Hotspawn epoch-ms governs pick lock times, per-row `START_TIME_MISMATCH` flags attached.
- 14 fixtures cancelled on the Hotspawn feed are excluded from picks and listed with source link (not silently dropped).
- No bookmaker prices tier-3/amateur leagues; those rows are priced by the league-anchored Elo model from Leaguepedia results, labelled Low confidence where history is thin.
- Pinnacle consumed via the public guest front-end feed (unofficial); Bovada returned `no_data` on this run — consensus fell back to healthy sources, source status published per run.
- Polymarket trading is blocked for US users; its prices are reference data only (disclosed on Methodology + Unresolved pages).
- Liquipedia API returned no usable data in this run (rate-limited/blocked); the pipeline degrades gracefully and publishes `no_data`.
- 73 rows are Low confidence (thin history <8 games, cross-league tier comparison, or league prior); these are estimates, not edges, and are flagged per row.
- `MODEL_STANDINGS` / `MODEL_LEAGUE_PRIOR` / `UNRESOLVED` did not appear in this window because every fixture had a rated side; the fallback code paths remain covered by unit tests and the unresolved/limitations section exists for any future window.

### Requirement traceability (all PASS — see `verification/report.json`)

REQ1 pick for every match · REQ2 probabilities sum to 1 · REQ3 no Hotspawn probability input · REQ4 external lines where they exist · REQ5 pick + documented method for every non-market match · REQ6 separate unresolved section with limitations linked from exec summary · REQ7 exec summary links in-site to picks · REQ8 official/trusted source link on every row or flagged unverified · REQ9 mobile-friendly · REQ10 automatic 6h refresh, no manual input · REQ11 no broken internal links, root entry works · REQ12 third-party attribution (Leaguepedia / Liquipedia CC BY-SA 3.0).

### Integration result

Pull request #30 (`arena/ea9a3e15-lolhotspawn2` → `main`) **merged** via `gh pr merge 30 --merge` on 2026-10-24; merge commit `215656b7250d2272490fadeeec777e40d1d238e8`. Pages build for `215656b`: status **`built`** (created 2026-10-24T16:17:47Z, updated 16:18:19Z); `pages build and deployment` workflow **completed success**. Site live at https://karagemop466-tech.github.io/LOLHOTSPAWN2/ serving the merged payload (169 fixtures, 169 resolved, 0 unresolved). PR URL: https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/30

This session (arena/ea9a3e15-lolhotspawn2) is complete: repo reviewed line by line, every table row carries a source link or is flagged unverified, the executive summary links in-site to the picks list and the unresolved section with per-league limitations, the site is mobile-friendly and live, picks cover 100% of Hotspawn's listed LoL fixtures (169/169, 0 unresolved), and the pipeline refreshes automatically every 6 hours with no manual input.

---

## Session `arena/047af680-lolhotspawn2` — 2026-10-24 (integration)

Branch note: fixed branch `arena/047af680-lolhotspawn2`, branched from `main` at `72c9b5a7c27b35dcd346c3d5f955e5ebee9ba727` (branch == main at claim time; all prior T1–T21 work from earlier sessions is already integrated on `main`). Per the branch rule this session works only on `arena/047af680-lolhotspawn2` and pushes only to it; the PR/merge step lands on `main` via `gh`.

| Task | Status | Owner | Files |
|---|---|---|---|
| T20 Line-by-line repo review: scripts, docs, data payload, workflows, verification harness | done | arena/047af680 | scripts/*, docs/*, data/*, .github/workflows/*, verification/*, research/* |
| T21 Confirm end-to-end requirements: pick for every match, separate unresolved section w/ limitations linked from exec summary, mobile dashboard, 4–8h refresh, source link on every row | done | arena/047af680 | docs/*, scripts/update_picks.py, scripts/model.py, scripts/verify_site.py, .github/workflows/update-picks.yml |
| T22 PR to main, merge without waiting, confirm GitHub Pages deploy, record PR link + merge result here | in progress | arena/047af680 | COORDINATION.md (board entries only); PR lands on `main` |

### Verification performed this session (offline; live-source fetches run in GitHub Actions)

| Check | Result | Evidence |
|---|---|---|
| `python3 scripts/verify_site.py` | **36 PASS · 0 FAIL · 0 WARN · 1 SKIP** | `verification/report.json` + `verification/last_report.md` committed this session |
| D18 start-time cross-check vs Leaguepedia | SKIP | no `--leaguepedia-schedule` snapshot available in the sandbox; CI runs it against `data/diag` |
| `python3 verification/test_verifier.py` | **35/35 pass** | self-tests: each rule fails on bad data |
| `python3 verification/check_dom_contract.py` | **PASS** | all JS-referenced ids exist on the seven site pages |
| `node --check docs/assets/app.js` | OK | shared JS parses |
| `docs/data/picks.json` snapshot | **169 fixtures · 169 resolved (100%) · 0 unresolved · 9 market · 160 model (93 MODEL_ELO / 67 MODEL_ELO_THIN) · 73 low confidence · 14 excluded (cancelled)** | local payload `generated_at 2026-10-24T15:28:56.619239Z` |
| Requirements traceability REQ1–REQ12 | **all PASS** | verify_site.py REQ aggregate check |

### Irregularities flagged for review (non-blocking; published on the Flagged for Review page)

- **Bovada `no_data`** this run (0 events returned); consensus fell back to Pinnacle + Unibet + Polymarket. Published per-run in `sources_status`; listed in `scripts/update_picks.py` `CHECKED_UNAVAILABLE`. Not a defect — source status is transparent on the site.
- **Polymarket US access**: Polymarket's homepage states trading is blocked in the United States (view-only). Prices are reference data only; disclosed on Methodology, Unresolved and `research/betting-sources.md`.
- **73 Low-confidence rows**: thin history (<5 games in 365d), cross-league comparisons capped at Low, or one unrated side vs the competition prior. Every row keeps its method label, evidence and source links; none are hidden.
- **14 cancelled fixtures**: excluded from picks with reason + Hotspawn fixtures API link; listed under Excluded on Flagged for review.
- **0 unresolved placeholders** in this snapshot; the separate Unresolved & limitations page and its executive-summary section remain live and would publish any future 50/50 rows with per-league limitations.
- **Sources are best-effort verified**: Pinnacle is consumed via its public guest front-end feed (unofficial; its official API closed 2025-07-23) and flagged as such. Leaguepedia/Liquipedia are community sources under CC BY-SA 3.0, attributed on Methodology — not official organizer odds feeds.

### Sources used (official / verified; links for manual review)

| Source | Used for | Link |
|---|---|---|
| Hotspawn Pick'em lobby / fixtures API | Fixture list, UTC start times, match links (never a probability input) | https://play.hotspawn.com/lol-pickems · https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures |
| Pinnacle guest JSON | 2-way series moneyline (Worlds 2026 etc.) | https://guest.api.arcadia.pinnacle.com/0.1 (site: https://www.pinnacle.com/en/esports/league-of-legends) |
| Unibet (Kambi CDN JSON) | 2-way pre-match Match Odds | https://eu-offering-api.kambicdn.com/offering/v2018/ubca/listView/esports/league_of_legends/all/all/matches.json (site: https://www.unibet.com.au/betting/sports/filter/esports/league_of_legends/all/matches) |
| Bovada coupon JSON | 2-way pre-match moneyline | https://www.bovada.lv/services/sports/event/coupon/events/A/description/esports/league-of-legends (site: https://www.bovada.lv/sports/esports/league-of-legends) |
| Polymarket Gamma API | Prediction-market reference prices | https://gamma-api.polymarket.com/events?tag_slug=league-of-legends&active=true&closed=false |
| Leaguepedia Cargo Export | Recorded results, schedule, standings, canonical names (CC BY-SA 3.0) | https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule |
| Liquipedia MediaWiki API | Compliant tournament metadata index only (CC BY-SA 3.0, gzip, ≥2.2s pacing, HTML never scraped) | https://liquipedia.net/leagueoflegends/api.php?action=query&meta=siteinfo&format=json |

PR/merge record — completed 2026-10-24:

| Item | Value |
|---|---|
| PR number | 32 |
| PR URL | https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/32 |
| Merge method | `gh pr merge 32 --merge` |
| Merge commit | `7b2bab5` (Merge pull request #32 from karagemop466-tech/arena/047af680-lolhotspawn2) |
| Pages build run | latest build created 2026-10-24T16:26:33Z, status `built` (source: main, path `/`) |
| Pages status | **built** — live |
| Live site | https://karagemop466-tech.github.io/LOLHOTSPAWN2/ (serving the merged payload: 169 fixtures, 169 resolved, 0 unresolved; live dashboard render confirmed) |

---

## Session `arena/26fa1cec-lolhotspawn2` — 2026-10-24 (claim)

**Baseline at claim:** `main`/session branch `72c9b5a` (payload generated 2026-10-24T15:28:56Z): 169 scheduled upcoming fixtures · **169 priced (100%)** · 9 market (8 consensus + 1 single) · 160 model (93 `MODEL_ELO` + 67 `MODEL_ELO_THIN`) · 0 `MODEL_STANDINGS` · 0 `MODEL_LEAGUE_PRIOR` · **0 `UNRESOLVED`** · 73 Low confidence · 14 cancelled Hotspawn fixtures excluded. No other session is active on `COORDINATION.md`. No commits by another session on these paths observed in `git log` since 2026-10-23T16:52Z.

| Task | Status | Owner | Files (exclusive scope) |
|---|---|---|---|
| T20 Phone-first executive summary: one consistent header/nav on all 7 pages, a prominent in-site "where the updated picks are" block above the fold, explicit unresolved-picks + limitations section in the executive summary, remove non-functional controls, verify mobile readability | in progress | arena/26fa1cec | `docs/*.html`, `docs/assets/style.css`, `docs/assets/app.js`, `verification/check_dom_contract.py` (only if the contract needs extending) |
| T21 External-source research v2 for fixtures the featured (market) picks cannot price: established books → esportsbooks → betting lines/aggregators → community results; live probe of untried endpoints on every refresh; promote any adapter that shows structured per-match LoL prices, otherwise publish the attempted sources + observed HTTP status + limitation on the site | in progress | arena/26fa1cec | `scripts/source_probe.py` (**new**, added to this claim), `scripts/probe_sources.py`, `scripts/update_picks.py`, `research/betting-sources.md`, `docs/methodology.html`, `docs/unresolved.html`, `README.md` |
| T21b Liquipedia probe fix: `probe_liquipedia_pages()` was called with whole Hotspawn tournament labels as MediaWiki `apprefix`, so it always returned `no_data`; map labels → page prefixes in `update_picks.py` | in progress | arena/26fa1cec | `scripts/update_picks.py` (only this file; `standings_and_books.py` untouched) |
| T22 Integration: full local + CI verification, PR to `main` from this branch, merge, confirm GitHub Pages deploy, record PR/deploy/live-check here | in progress | arena/26fa1cec | `COORDINATION.md`, `verification/**` |

**Scope rule:** this session edits only the paths above. `scripts/fetch_markets.py`, `scripts/fetch_leaguepedia.py`, `scripts/model.py`, `data/aliases.json`, and `.github/workflows/**` are **not** modified; any change needed there is logged as a request instead of edited.

### Results so far (`arena/26fa1cec`, 2026-10-24)

| Item | Status | Evidence |
|---|---|---|
| T20 phone-first summary + unified nav | implemented, verified locally (38 PASS / 0 FAIL / 0 WARN) | `docs/index.html`, `docs/unresolved.html`, `docs/assets/style.css`, `docs/assets/app.js`; new verifier check `S4c` (dedicated `#picks-here` block with 4 in-site links + bound counts) |
| T21 external-source probe on every refresh | implemented; 22 candidates measured live, results published in the payload + site | `scripts/source_probe.py` (new), `scripts/update_picks.py`, `scripts/probe_sources.py`; verifier check `D22` |
| T21b Liquipedia prefix fix | implemented; probe now returns **54 page titles** (was `no_data`) | `scripts/update_picks.py`; `docs/data/picks.json` → `sources_status` |
| Organizer links | substring matching (fixes the missing Komplettligaen row); 3 organizer pages re-verified live 2026-10-24 | `scripts/update_picks.py`; `research/betting-sources.md` §13.3 |
| T22 integration | done (merged via PR #33) | — |

**Live measurements used (run [40111355592](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40111355592), payload `2026-10-24T16:25:23Z`):** 164 upcoming fixtures · 164 priced (100%) · 9 market · 155 model · 0 unresolved · 68 low confidence · 14 cancelled excluded. Probe: 22 candidates, 10 reachable, 5 structured JSON, 3 with LoL references. Pinnacle 200 JSON, Betfair 403, Smarkets 404, Betway 404, BetOnline 200 HTML, Unibet shell 503, GG.Bet 403, Thunderpick 403, Rivalry 503, Midnite 200 HTML, 1xBet 203 (US geo-block confirmed separately), OddsPapi 404 (no key), odds-api.io 200 no LoL, OddsPortal 200 HTML, BetExplorer 404, eGamersWorld 403, Kalshi 200 no LoL series, Manifold 200 futures only, gol.gg 200, bo3.gg 200 (177 LoL references), Riot LoLESports 403, Liquipedia 200. **No new market adapter was justified**: no probed source returned a structured per-match LoL price, and vendor documentation (OddsPapi) excludes every amateur league on Hotspawn's list.

**Irregularities found & fixed this session** (also on the site's Flagged page and in `verification/flagged_items.md` S4–S9):
1. **Clipped header on the executive summary + unresolved page** — `<div class="wrap bar">` collided with the `.bar` probability-bar component (`height:12px; overflow:hidden`), so the brand/nav/theme button were clipped to a 12px strip on phones; `.brand`, `.mark`, `.bar-end`, `.status-strip`, `.nav-list`, `.covbar` and `.stat b` had no CSS at all. Fixed by moving all 7 pages to one header component and adding the missing styles.
2. **Dead `#theme-toggle` button** (no JS handler) — removed; dark mode follows `prefers-color-scheme`.
3. **Liquipedia probe always returned `no_data`** because whole Hotspawn tournament labels were passed as MediaWiki `apprefix`; now mapped to page prefixes (54 pages found).
4. **`probe_sources.py` broke on `retries=0`** (`lib_common.fetch` returns `None`), so the first probe run recorded 22 `AttributeError`s; fixed to a single attempt and the results are now real.
5. **`sources_status` printed “2880 standings across 0 competitions”** (missing `standings_pages` key) — computed from the rows and exposed as `model.standings_pages`.
6. **Komplettligaen organizer link never rendered** (exact-key mismatch: `Komplettligaen 2026 Autumn` vs `… Autumn Playoffs`) — substring matching now; 5 competitions have no verified organizer page and stay blank + flagged rather than guessed.
7. **1xBet is US-geo-blocked** (`https://1xbet.com/en/block`, "Access denied") — its claimed tier-2/3 coverage stays unverified and unused.

**Open items for review (non-blocking, published on the Flagged page):** S8 1xBet geo-block; S7 five competitions without a verified organizer page; S2 probe verdicts are observations only.

### PR / merge / deploy record (`arena/26fa1cec`, 2026-10-24)

| Item | Value |
|---|---|
| Pull request | [PR #33](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/33) — `arena/26fa1cec-lolhotspawn2` → `main` |
| Merge | `gh pr merge 33 --merge` → **MERGED** 2026-10-24T16:30:56Z, merge commit `fb4ad13` |
| Pre-merge branch CI | `pipeline-test.yml` run [40111740168](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40111740168) — **success** (live pipeline + `verify_site.py --check-external` + all unit suites) |
| Post-merge verification on `main` | `verify.yml` run [40111916819](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40111916819) — **success**, all 8 steps (self-tests, offline + external/live-Pages verify, coverage audit, DOM contract) |
| Post-merge production refresh | `update-picks.yml` run [40111916813](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40111916813) — **success**, commit `1901334`, payload `2026-10-24T16:32:38Z`: **160 upcoming fixtures · 160 priced (100%) · 9 market · 151 model · 0 unresolved · 64 low confidence · 18 cancelled excluded · 22 probe rows** |
| GitHub Pages | build [40112050113](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40112050113) — **success**; Pages API `status: built` for `1901334` (16:33:19Z) |
| Live site checked | https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/ — rendered summary shows “📌 Where the updated picks are” with **160 / 25 / 12 / 0 unresolved · 64 low confidence**, the refresh line “Updated … 160/160 listed matches priced (100%)”, and the Unresolved page renders the 22-row external-source table (Pinnacle 200, Betfair 403, BetOnline 200 HTML, 1xBet 203, Kalshi 200 no LoL, Liquipedia 200, …) |

**Follow-up commit (same session):** probe verdict wording is now category-aware (results/metadata pages are no longer
described in odds language) and the probe table labels the type as “Market”/“Results”. No data or probability behaviour changes.

| Item (continued) | Value |
|---|---|
| Follow-up PR | [PR #34](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/34) — **MERGED** 2026-10-24T16:36:32Z, merge commit `5d71d0b`; `verify.yml` [40112346967](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40112346967) success; Pages build [40112346904](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40112346904) success |
| Production refresh after #34 | `update-picks.yml` [40112346993](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40112346993) — success, commit `fc1d438`, payload `2026-10-24T16:40:07Z`: 160 fixtures · 160 priced (100%) · 9 market · 151 model · 0 unresolved · 64 low confidence · 22 probe rows (8 reachable this run) |
| Live checks on production | summary renders the 4 picks cards (160 / 25 / 12 / 0 unresolved · 64 low) + refresh line; `picks.html?filter=next24` renders 25 of 160 rows with both win probabilities, ✅ pick pill and source links; `unresolved.html#sources-checked` renders the 22-row probe table |

**Irregularity 8 (fixed):** two-way percentages were rounded independently, so two rows displayed **99.9%**
(e.g. JSK Academy 50.7% + New Era Team 49.2%) and market rows could display 100.1%. `pctPair()` in
`docs/assets/app.js` now rounds the first side and derives the second from 100 − first, so every displayed pair
sums to exactly 100.0%. Stored probabilities were always correct (`D4` tolerance) — this was display-only.
Verified with a jsdom pass over all 160 rendered rows: 160/160 pairs sum to 100.0%.

---

## Session `arena/607dddb0-lolhotspawn2` — 2026-10-24 (live sportsbook & wiki forensic audit: Bovada 8-match restoration, `Inari Esports` entity repair, 404 URL elimination, Liquipedia API normalization & 6h CI hardening)

> Branch & coordination note: Fixed session branch `arena/607dddb0-lolhotspawn2` (integrated cleanly with `origin/main` through PRs #33 & #34 `5d71d0b`, preserving 100% of all prior sessions' entries and code). Scope restricted strictly to unclaimed files (`data/aliases.json`, `scripts/entity_resolution.py`, `scripts/fetch_markets.py`, `scripts/standings_and_books.py`, `.github/workflows/update-picks.yml`, `research/line-by-line-audit-2026-10-24.md`, `COORDINATION.md`).

| Task | Status | Owner | Exclusive file scope |
|---|---|---|---|
| T34 Tournament/entity alias & 100% Leaguepedia provenance repair: map `4 Nations 2026 Halloween Heist`, `Komplettligaen 2026 Autumn Playoffs`, `PRM 1st Division 26-27 Fall`, `Arabian League 2nd Division 2026 Fall Playoffs`, and fix `Inari Esports` -> `Inari Esports (British Team)` (`1081700` was previously mis-resolved to unrelated `NARI` via 4-letter substring containment, producing `GENERIC_RESULTS_SOURCE`) | done (CI verified `40111870194`, `40112196096`) | arena/607dddb0 | `data/aliases.json`, `scripts/entity_resolution.py` |
| T35 Live sportsbook & Liquipedia restoration: (1) restore Bovada from `no_data (0)` to `ok (8)` by querying `/description/esports` filtered to LoL coupon groups, accepting Bovada's `period={"description":"Game","main":true}` series moneyline while rejecting `Map N`/`Game N` sub-boards, and prefixing `/sports` on event URLs (`200 OK`); (2) replace 404 `www.pinnacle.com/en/esports/league-of-legends` with `200 OK` Arcadia JSON URLs; (3) normalize/deduplicate Liquipedia `api.php` prefixes (`≤8` queries, `status: "ok"`) | done (CI verified `40111870194`, `40112196096`) | arena/607dddb0 | `scripts/fetch_markets.py`, `scripts/standings_and_books.py` |
| T36 Scheduled 6h workflow hardening: add `data/aliases.json` to `update-picks.yml` push trigger and discard unstaged `verification/` reports before the `git merge -X ours` push-retry loop | done | arena/607dddb0 | `.github/workflows/update-picks.yml` |
| T37 Full line-by-line 2026-10-24 live external source audit (`research/line-by-line-audit-2026-10-24.md`), CI branch verification (`pipeline-test.yml`), PR → `main`, merge & Pages confirmation | done | arena/607dddb0 | `research/line-by-line-audit-2026-10-24.md`, `COORDINATION.md` |

### Irregularities discovered & fixed during live external audit (`2026-10-24`)
- **I20 (FIXED — wrong entity disambiguation & `GENERIC_RESULTS_SOURCE` on fixture `1081700`):** `Inari Esports vs Bulldog Esports` (`4 Nations 2026 Halloween Heist`, `2026-10-26T19:00:00Z`) resolved `"Inari Esports"` to unrelated team `NARI` (`"nari"` substring inside `"inariesports"`), missing Leaguepedia's official schedule row (`Inari Esports (British Team)` vs `Bulldog Esports`, `BestOf: 3`, Round 2) at <https://lol.fandom.com/wiki/4_Nations/2026_Season/Halloween_Heist>. Fixed in `data/aliases.json` + `scripts/entity_resolution.py` with `HOTSPAWN_NAME_COLLISION` flag (`GENERIC_RESULTS_SOURCE` reduced to **0** across all 160 fixtures).
- **I21 (FIXED — Bovada triple-bug caused false `no_data (0)` despite 8 live Worlds moneylines):** `/description/esports/league-of-legends` returns `{}`, whereas `/description/esports?marketFilterId=def&preMatchOnly=true&lang=en` returns HTTP `200 OK` with all 8 `World Championship '26` LoL moneylines (`path` includes `/esports/league-of-legends`). In addition, `fetch_bovada()` previously rejected `period.description == "Game"` (`main: true`) and built `/esports/...` links (HTTP 404) instead of `/sports/esports/...` (HTTP 200). Verified live in CI runs `40111870194` & `40112196096`: Bovada `ok (8)`, upgrading all 8 Worlds matches to **4-source consensus** (`Pinnacle + Unibet + Bovada + Polymarket`).
- **I22 (FIXED — Pinnacle 404 URL & Liquipedia prefix normalization):** Replaced 404 `https://www.pinnacle.com/en/esports/league-of-legends` with `200 OK` `https://guest.api.arcadia.pinnacle.com/0.1/matchups/{mid}/markets/related/straight` (`X1`: `0 dead 404/410` in CI) and normalized `probe_liquipedia_pages()` to verified Liquipedia `apprefix` strings (`ok`).

### PR / merge / live GitHub Pages deployment record (`arena/607dddb0`, 2026-10-24)

| Item | Result & Evidence |
|---|---|
| Pull request | [PR #35](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/35) — `arena/607dddb0-lolhotspawn2` → `main` |
| Merge | `gh pr merge 35 --merge` → **MERGED** `2026-10-24T16:40:53Z`, merge commit `0b822dd1a5ab677740528745e5120addcb54803d` |
| Pre-merge branch CI | `pipeline-test.yml` runs [40111870194](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40111870194) (`1m34s`) & [40112196096](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40112196096) (`3m23s`) — **100% green** (`verify_site.py --check-external` `X1: 0 dead 404/410` + all unit suites) |
| Post-merge verification on `main` | `verify.yml` run [40112685479](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40112685479) — **success** |
| Post-merge production refresh on `main` | `update-picks.yml` run [40112685473](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40112685473) — **success** (`1m36s`), commit `d5e3127`, payload `2026-10-24T16:42:29.066048Z`: **160 upcoming fixtures · 160 resolved (`100.0%`) · 0 unresolved · 9 market (`8` 4-book Worlds consensus + `1` single Polymarket) · 151 Elo model (`94` `MODEL_ELO` + `57` `MODEL_ELO_THIN`) · `8/8` `sources_status` `ok` (`Bovada: ok/8`, `Liquipedia: ok`) · `0` `GENERIC_RESULTS_SOURCE`** |
| GitHub Pages builds | [40112685075](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40112685075) & post-refresh [40112807856](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40112807856) — **success**, Pages API `status: built` for `d5e3127` (`2026-10-24T16:43:03Z`) |
| Live site verification | Live checks on <https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/>, `match.html?id=1067688` (4-book consensus: Pinnacle + Unibet + Bovada + Polymarket with `200 OK` links), and `match.html?id=1081700` (`Inari Esports (British Team)` Bo3 on `4 Nations/2026 Season/Halloween Heist`) all confirmed live. |

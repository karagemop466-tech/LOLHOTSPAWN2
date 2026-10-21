# Coordination Board
Session: arena/1efcf62c-lolhotspawn2 (this session, branch arena/1efcf62c-lolhotspawn2 per Arena tracking; user-named session-* branch superseded by system branch rule)
| Task | Status | Owner | Files |
|---|---|---|---|
| T1 Hotspawn LoL lobby scraper (reverse-engineer play.hotspawn.com/lol-pickems) | in progress | arena/1efcf62c | scripts/update_picks.py, .github/workflows/update-picks.yml |
| T2 External odds adapters (Polymarket public, OddsPapi/TheOddsAPI if key secret set) | in progress | arena/1efcf62c | scripts/update_picks.py |
| T3 Fallback own-line model (Leaguepedia Cargo Elo) + unresolved-picks logic | in progress | arena/1efcf62c | scripts/update_picks.py, docs/unresolved.html |
| T4 Mobile-first GitHub Pages site + executive summary | in progress | arena/1efcf62c | docs/ |
| T5 Flagged for Review page (unverified/unresolved, limitations) | in progress | arena/1efcf62c | docs/flagged.html |
| T6 Verify build, PR to main, merge, confirm Pages deploy | unclaimed | arena/1efcf62c | - |
Sources (verified 2026-10-21): Hotspawn lobby https://play.hotspawn.com/lol-pickems (264 LoL matches listed at check), How-it-works https://play.hotspawn.com/how-it-works (picks lock 5 min before start), Leaguepedia Cargo API https://lol.fandom.com/api.php?action=help&modules=cargoquery, Polymarket Gamma API https://gamma-api.polymarket.com, OddsPapi LoL https://oddspapi.io/sports/esports/lol
Irregularities: sandbox cannot reach play.hotspawn.com directly (curl 000) - scraper runs in GitHub Actions; 189/264 Hotspawn rows show tier "WAITING FOR INFORMATION" = low-information fixtures, expected to fall to T3/unresolved.

## Session arena/47334762-lolhotspawn2 — claims (2026-10-21 ~20:25 UTC)
Board note: session `arena/fa3f554c-lolhotspawn2` has claimed T7–T10 on its own branch (verified via `git fetch` of `origin/arena/fa3f554c-lolhotspawn2`, commits da4fd55..dd43c38, actively running GitHub Actions "DIAG lab" runs 39669308258/39669571794/39669777187). That session's branch rewrites this board; versions will be reconciled (not discarded) at integration. This session does NOT touch `scripts/update_picks.py`, `scripts/diag_lab*.py`, `docs/**`, `data/**`, or `.github/workflows/update-picks.yml` — those belong to arena/fa3f554c (T7–T10).

| Task | Status | Owner | Files (exclusive scope) |
|---|---|---|---|
| T11 Verification harness: schema check (pick on every match, probs sum to 1, method enum, per-row source links), site link check (no broken internal links, mobile viewport on every page), exec-summary-links-to-picks check, unresolved-section-present check, workflow cadence (4–8h) check | in progress | arena/47334762 | scripts/verify_site.py, verification/**, research/** |
| T12 Final integration: merge task branches after T7–T10 done, re-verify combined data line by line with scripts/verify_site.py, PR to main, merge without waiting for approval, confirm GitHub Pages deploy, record PR link + merge result here | in progress | arena/47334762 | COORDINATION.md (board entries only) |

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

### T11 status (this session)
`scripts/verify_site.py` written: 29 rule groups covering data schema, per-row source links, mobile viewport, in-site
exec-summary links, separate unresolved section, internal-link integrity, 4-8h cron cadence, and a static scan that
Hotspawn crowd % never feeds a probability. Baseline on current main: **26 PASS · 2 WARN · 0 FAIL**
(WARN: 61 model rows cite an API help page; 64.6% of rows still unresolved). Reports in `verification/`.


## Completion log (2026-10-21, arena/1efcf62c)
- T1-T5 done. PR #1 merged (site+pipeline), PR #2 merged (Pages root redirect + push trigger).
- Live verification: workflow run 39668843544 success on main; picks bot commit f269386; Pages build success.
- Live data at check: 195 matches parsed & priced — MARKET_POLYMARKET 8, MODEL_ELO 61, UNRESOLVED 126, MARKET_BOOKS 0 (no ODDSPAPI_KEY secret set; optional).
- Live site: https://karagemop466-tech.github.io/LOLHOTSPAWN2/ -> /docs/ Executive Summary (verified rendered with data).
- Flagged (non-blocking, on Flagged page): lobby header said 264 LoL matches but parser extracted 195 cards (likely cards beyond initial SSR payload/pagination) — parser should be extended if Hotspawn exposes a fixtures API; all 195 extracted rows verified pick+prob sum. Tier WAITING FOR INFORMATION rows and 50/50 unresolved rows as above.

# Hotspawn LoL picks — verification & delivery report

**Session:** `arena/47334762-lolhotspawn2` (T11 verification, T12 integration)
**Date:** 2026-10-21 · all times UTC
**Live site:** https://karagemop466-tech.github.io/LOLHOTSPAWN2/
**Data source of truth:** `docs/data/picks.json` (schema v3)
**Not betting advice.** Pick'em on Hotspawn is free-to-play.

> Status: **DEPLOYED** — merged to `main` through PR #5 (v2 pipeline and 6-page site) and the verification PR
> recorded in §8. Every check below is reproducible with the commands in §7.

---

## 1. What the brief asked for, and how it is verified

| # | Requirement | Where it is implemented | How it is verified |
|---|---|---|---|
| REQ1 | A pick for **every** LoL match listed on Hotspawn | fixtures feed → `scripts/update_picks.py` | `D3` pick ∈ {team1, team2} on every row; `D11` declared fixtures = rows (208) |
| REQ2 | Win probability for both teams, summing to 100% | payload `prob_team1/prob_team2` | `D4` sum = 1 ±0.005; `D5` pick = larger probability |
| REQ3 | Probabilities from **outside Hotspawn** (books, markets, our own results model) | market adapters + Leaguepedia results model | `D12` no probability-source field cites hotspawn.com; `W3` static scan: crowd % never feeds a probability |
| REQ4 | Established LoL betting sites / esportsbooks used where they exist | Pinnacle + Bovada + Polymarket consensus (9 rows) | `D8a` market rows link each book/market with per-source prices; `D6` methods documented |
| REQ5 | Matches with no book line still get a pick **and** an explained method | league-anchored Elo over 31,742 recorded series; 0 explicit 50/50s | `D8b`, `D13`, `S5b` |
| REQ6 | Separate unresolved section with limitations, included in the executive summary | `docs/unresolved.html` + `docs/index.html` | `S4`, `S5`, `S5b`, `S5c` |
| REQ7 | Executive summary links in-site to the updated picks list | `docs/index.html` → `picks.html` | `S4` (`links_picks`, `links_unresolved`, `mentions_limitations`, `mentions_updated`) |
| REQ8 | Every row links an official/trusted source; unconfirmed values blank + flagged | per-row `sources[]` with URLs and claims | `D7`, `D7c`, `D8a`, `D8b` |
| REQ9 | Mobile-friendly, readable on a phone | 6-page responsive site, bottom nav, safe-area insets | `S2`, `S7`, `S9`, DOM contract |
| REQ10 | Automatic refresh every 4–8 h, no manual input | `.github/workflows/update-picks.yml` (6-hour cron) | `W1`, `W2`, `D1` |
| REQ11 | Site builds with no broken links | GitHub Pages | `S1`, `S6`, `S8`, `X1`–`X3` (live) |
| REQ12 | Third-party data attributed | Method & Sources page | `S5c` (Leaguepedia, Liquipedia CC-BY-SA 3.0) |

## 2. Sources (verified, with links)

**Fixture list (the only use of Hotspawn):**
- Lobby: https://play.hotspawn.com/lol-pickems (picks lock 5 minutes before start: https://play.hotspawn.com/how-it-works)
- Backend fixture feed (undocumented, used by the lobby itself):
  `https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures` — epoch-ms UTC, tier, points, participants
  (evidence: `data/diag/report2.json`). 208 future LoL fixtures at the last run; 195 have a published match page.

**Market / betting lines (never Hotspawn):**
- **Pinnacle** guest feed — sport 12 (E Sports), LoL leagues 9587 (World Championship) and 225201 (EMEA Masters).
  https://www.pinnacle.com/en/esports/league-of-legends — official API retired 2025-07-23
  (https://github.com/pinnacleapi/pinnacleapi-documentation), so the front-end guest feed is used and labelled as such.
- **Bovada** LoL coupon JSON — https://www.bovada.lv/sports/esports/league-of-legends
- **Polymarket** Gamma API — https://gamma-api.polymarket.com ; **series markets only** (a Game-N/Map-N child market is
  never used as a series probability; see I1/I10 below).
- Checked and unavailable (published on the site): Betfair (403), Smarkets (403), OddsPapi (401, no key), The Odds API
  (401), OddsPortal (503), BetExplorer (404), GG.Bet (403), Thunderpick (403), Betway (404), Unibet (503), Rivalry
  (502), Midnite (no server-rendered prices), Kalshi (no LoL series), Manifold (no per-match prices), Riot LoLESports
  (403). Evidence: `docs/data/picks.json` → `checked_unavailable`.

**Results / community sources for our own line:**
- **Leaguepedia Cargo** via `Special:CargoExport`: `MatchSchedule` (completed series with scores and exact UTC) and
  `ScoreboardGames`. 31,742 results used; 5,496 teams rated. Fields verified via
  `api.php?action=cargofields&table=MatchSchedule|Standings`.
- Leaguepedia team pages per fixture: e.g. https://lol.fandom.com/wiki/2026_Season_World_Championship/Main_Event
- Liquipedia API (CC-BY-SA 3.0, API only, gzip, ≤1 req/2 s): https://liquipedia.net/api-terms-of-use
- Organizer sites are human cross-checks only: `primeleague.gg` returns **403 Bunny Shield** from Actions;
  `4nations.gg`, `ligagg.com`, the Tunisian sites and `lol.tn` are unreachable; `rivalsleague.gg` and
  `komplettligaen.no` are reachable but HTML-only (`data/diag/report6.json`).

## 3. The core problem — and what changed

**Before (2026-10-21 20:16 UTC, main):** 195 fixtures; **126 were explicit 50/50 `UNRESOLVED`** and **61 were Elo rows
between 0.455 and 0.545** — 187/195 rows (96%) carried no real signal; only 8 market rows did. The uncertainty was not
in the market, it was in the pipeline: a global 180-day `ScoreboardGames` scan was crowded out by major leagues, so the
amateur teams the feed lists had 0–9 recorded games each.

**What the research established (see `research/betting-sources.md`):**
- No licensed book we can reach prices PRM 2nd/3rd Division, RIVALS LEAGUE, 4 Nations, Tunisian Super League,
  Komplettligaen, LigaGG or the Arabian 2nd Division. Pinnacle/Bovada/Polymarket cover the World Championship and
  EMEA Masters only. Organizer sites are blocked or unstable from CI.
- **Leaguepedia's `MatchSchedule` carries completed series with scores and exact UTC for every one of those leagues** —
  one CargoExport request per league. Standings (`WinSeries`/`LossSeries`, verified field names) are the fallback.
- Every previously "unresolved" fixture had a Leaguepedia league page; 112 of 126 had the exact fixture listed
  (`verification/leaguepedia_coverage.md`).

**After (live payload, 2026-10-21 21:07 UTC):**

| metric | value |
|---|---|
| Hotspawn LoL fixtures published | **208 / 208** (13 lack a published match page and are flagged) |
| Rows with an external market line | **9** — Pinnacle + Bovada + Polymarket consensus |
| Rows priced by our own model | **199** — 92 `MODEL_ELO`, 72 `MODEL_ELO_THIN`, 35 `MODEL_LEAGUE_PRIOR` |
| Explicit 50/50 rows | **0** |
| Low-confidence rows, listed on the site | **111** |
| Model backtest (30-day holdout, n=658) | log-loss **0.6266** (coin flip 0.6931), Brier **0.2183** (0.25), accuracy **64.4%** |
| Results used | **31,742** recorded series; 5,496 teams rated |

## 4. Irregularities — fixed vs still flagged

**Fixed in this delivery (verified after the fix):**
| id | issue | fix |
|---|---|---|
| I1/I10 | A Polymarket **Game 3** child market was used as the Galions–Solary (BO5) series probability | detect every `Game N`/`Map N` market and only allow a game-level price when the fixture is **known BO1**; the row now uses the BO5 series market (Pinnacle 53.4% / Bovada 50.0% / Polymarket 55.5% → 53.4%) |
| I8 | 96% of rows had no real signal | league-anchored Elo over MatchSchedule results; 0 unresolved, backtested |
| I2/I3 | rows linked generic API/doc pages | every row now carries `sources[]` with the book URL and the Leaguepedia tournament page |
| I6 | `"Oct 24, 24:00"` failed to parse | fixtures come from the epoch-ms feed; all 208 rows have UTC |
| I9 | tier "W" shown as a tier | tier and stage are separate fields; "waiting for information" is displayed as such |
| P10/P11 | workflow swallowed git failures and checked only two invariants | pipeline fails loudly; full verifier runs in the workflow |
| P13 | 8.3 MB Leaguepedia cache committed each run | `data/cache/` and the duplicate `data/picks.json` are gitignored |

**Still flagged for review (full evidence: `verification/flagged_items.md`, also on the site's Flagged page):**
- **P1** Pinnacle is reached through its guest front-end feed, not a licensed API (official API closed 2025-07-23).
- **P4** Organizer sites blocked/unreachable from CI — Leaguepedia is the only programmatic results source.
- **P5** Leaguepedia's anonymous Cargo API is aggressively rate limited; the pipeline paces requests and logs status.
- **P7** Polymarket liquidity is thin outside majors; prices move between fetch and publish.
- **P8** Hotspawn's fixture feed is undocumented; the rendered-lobby parser remains as a fallback.
- **P9** Team-name differences (e.g. `Rich Gang` vs `Rich Gang (Norwegian Team)`, `LØS` vs `LOS`) are bridged by an
  explicit alias map; unmatched names are flagged, never inferred.
- **P12** Data is rendered client-side; with JS disabled the lists show "Loading…".
- **P14** Four fixtures have different Hotspawn vs Leaguepedia start times (likely reschedules). Hotspawn governs pick
  lock times; the differences are listed in the verification report.
- **D13** 111 rows are labelled Low confidence (thin history or one team unrated). They are published on the
  Unresolved & low-confidence page with reasons, and the model limitations are stated in the executive summary.

## 5. Verification performed (line by line)

- **31 checks PASS, 0 FAIL, 1 WARN** on the published 208-fixture payload (`verification/report.json`): pick on every
  match; probabilities in range and summing to 1; `pick_prob` = larger probability; documented method/confidence
  labels; **an absolute http(s) source on every row**; market rows link each book; unresolved rows (none today) are
  exactly 50/50 and labelled; no duplicate fixtures; counts agree; Hotspawn is never a probability source; a **static
  scan proves the crowd % never feeds a probability**; mobile viewport and shared nav on all six pages; exec summary
  links picks + unresolved and states limitations; separate unresolved/low-confidence section with limitations; no
  broken internal links; root redirect; 6-hour cron with `contents: write`; third-party attribution present.
- **27 self-tests** prove every rule fails on deliberately broken data (`verification/test_verifier.py`).
- **Start times cross-checked against Leaguepedia MatchSchedule**: 149/153 matched fixtures agree; 4 differ (P14);
  55 fixtures are not in the captured snapshot.
- **Published prices spot-checked at source**: Gen.G 0.775, Team Liquid 0.708, G2 0.426 — each with Pinnacle, Bovada
  and Polymarket prices and URLs on the row.
- **Per-row coverage audit**: of 199 model rows, 153 have the exact fixture on a Leaguepedia league page, 26 have the
  league page, 15 cite a page outside the snapshot, and **5 have no Leaguepedia page** (4 Arabian League 2nd Division,
  1 LigaGG) — all five are ~50% prior rows at Low confidence and are flagged.
- **DOM contract**: every one of the 30 element ids used by `app.js` exists across the six pages; every dynamic page
  includes the shared script and every page the stylesheet.
- **Live deployment** (X2/X3): the Pages site answers 200 and serves the same payload the repository publishes.

## 6. How to reproduce

```bash
python3 verification/test_verifier.py                                    # 27/27
python3 scripts/verify_site.py --leaguepedia-schedule data/diag          # 31 PASS / 0 FAIL / 1 WARN
python3 verification/check_leaguepedia_coverage.py --rows model --schedule-dir data/diag
python3 verification/check_dom_contract.py                              # DOM contract PASS
python3 scripts/verify_site.py --check-external \
  --live-url https://karagemop466-tech.github.io/LOLHOTSPAWN2/           # production check (needs network)
python3 verification/summarize.py                                       # coverage_by_league.md
```

CI runs the same suite in `.github/workflows/verify.yml` (on push to `main`, every 6 h at :30, and on demand).

## 7. Files added by this session

`scripts/verify_site.py` (31 rules + REQ1–REQ12 matrix + live/external checks) ·
`verification/test_verifier.py` (27 self-tests) · `verification/check_leaguepedia_coverage.py` ·
`verification/check_dom_contract.py` · `verification/standings_line.py` + `verification/apply_standings.py`
(independent standings line, validated: 18/18 RIVALS fixtures, 30/31 Komplettligaen+Tunisian) ·
`verification/leaguepedia_line.py` (independent Elo) · `verification/apply_fixes.py` (idempotent production fixes) ·
`verification/summarize.py` · `verification/flagged_items.md` · `research/betting-sources.md` ·
`verification/FINAL_REPORT.md` · `.github/workflows/verify.yml`

## 8. Deployment record

_Filled in after merging the verification PR._

## 9. Follow-up integration audit — 2026-10-23 (Arena session `arena/b252f309-lolhotspawn2`)

This dated audit supplements (it does not overwrite) the 2026-10-21 run metrics above. The current repository snapshot
was generated at **2026-10-23 11:00:24 UTC** and was **4.7 hours old** at verification. It contains **189 fixtures**:
9 with external market data, 180 Elo-model estimates, and 0 unresolved placeholders. The six-hour scheduled refresh is
configured; the latest observed main-branch refresh (Actions run [39942806398](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39942806398))
and Pages build ([39943048408](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39943048408)) succeeded. The latest scheduled
verification run ([39949842068](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39949842068)) also succeeded.

The audit found and fixed two presentation/provenance issues:

1. The mobile fixed navigation had **five destinations but only four CSS grid columns**, which could strand the last
   destination on an extra row on narrow screens. It now has five responsive columns; `verification/check_dom_contract.py`
   checks that every page's mobile-nav link count equals the stylesheet's column count.
2. **38/180 model rows** linked only to a generic Leaguepedia Cargo table, not a fixture-specific competition page.
   The model now adds `GENERIC_RESULTS_SOURCE` for this case; the 38 rows in the current payload carry the flag, and the
   Flagged page explains it. The verifier now requires each model row to have a results-source URL and fails if a generic
   Cargo table is not accompanied by the flag. The source is community-maintained, not official organizer verification;
   that caveat is now explicit in the executive summary, Methodology, and Flagged for review pages.

Updated audit suite: **33 PASS, 0 FAIL, 1 WARN**; `verification/test_verifier.py` **32/32**; DOM contract PASS.
The sole warning is **D18**: the captured Leaguepedia schedule snapshot covers 137 matched fixtures, of which 10 have
start-time differences from Hotspawn; 52 additional fixtures are absent from the snapshot. Hotspawn remains the displayed
pick-lock source. These mismatches and the uncertainty of missing snapshot rows are disclosed for review rather than
silently resolved. The all-table mobile navigation and internal-link checks pass. No current-day market/source fetch was
performed from the restricted local sandbox; the cited source verification artifacts and latest successful main workflow
runs are the available evidence. Re-run the scheduled pipeline/verification workflow for fresh external-source checks.

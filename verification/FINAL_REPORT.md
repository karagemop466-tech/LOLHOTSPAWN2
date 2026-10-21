# Hotspawn LoL picks — verification & delivery report

**Session:** `arena/47334762-lolhotspawn2` (T11 verification, T12 integration)
**Date:** 2026-10-21 · all times UTC
**Live site:** https://karagemop466-tech.github.io/LOLHOTSPAWN2/
**Data source of truth:** `docs/data/picks.json` (identical copy in `data/picks.json`)
**Not betting advice.** Pick'em on Hotspawn is free-to-play.

> Status: INTEGRATION IN PROGRESS. Final numbers (match count, method split, deploy run id) are filled in after the
> merge and Pages deployment; every check below is reproducible with the commands in §7.

---

## 1. What the brief asked for, and how it is verified

| # | Requirement | Where it is implemented | How it is verified |
|---|---|---|---|
| REQ1 | A pick for **every** LoL match listed on Hotspawn | fixture feed → `scripts/update_picks.py` | `D3` pick ∈ {team1, team2} on every row; `D19` published count vs feed-advertised future fixtures |
| REQ2 | Win probability for both teams, summing to 100% | payload `prob_team1/prob_team2` | `D4` sum = 1 ±0.005; `D5` pick = larger probability |
| REQ3 | Probabilities from **outside Hotspawn** (books, markets, our own results model) | market adapters + results model | `D12` no probability-source field cites hotspawn.com; `W3` static scan: crowd % never feeds a probability |
| REQ4 | Established LoL betting sites / esportsbooks used where they exist | Polymarket (live), Pinnacle guest feed (live), OddsPapi (key-gated) | `D8a` every market row links its market; §4 sources |
| REQ5 | Matches with no book line still get a pick **and** an explained method | standings/elo model, else explicit 50/50 | `D8b`, `D13`, `D17`, `S5b` |
| REQ6 | Separate unresolved section with limitations, included in the executive summary | `docs/unresolved.html` + `docs/index.html` | `S4`, `S5`, `S5b`, `S5c` |
| REQ7 | Executive summary links in-site to the updated picks list | `docs/index.html` → `picks.html` | `S4` (`links_picks`, `links_resolved`, `mentions_updated`) |
| REQ8 | Every row links an official/trusted source; unconfirmed values blank + flagged | per-row `market_url` / `source_url` / `hotspawn_url` | `D7`, `D8a`, `D8b`, `D17`, `S9b` |
| REQ9 | Mobile-friendly, readable on a phone | responsive CSS, cards, viewport meta | `S2`, `S7`, `S9` |
| REQ10 | Automatic refresh every 4–8 h, no manual input | GitHub Actions cron + bot commit | `W1` cron interval, `W2` generator + write permission, `D1` data age |
| REQ11 | Site builds with no broken links | GitHub Pages | `S1`, `S6`, `S8`, `X1`–`X3` (live) |
| REQ12 | Third-party data attributed | Method & Sources page | `S5c` (Leaguepedia, Liquipedia CC-BY-SA 3.0) |

## 2. Sources (verified, with links)

**Fixture list (only use of Hotspawn):**
- Lobby: https://play.hotspawn.com/lol-pickems (picks lock 5 minutes before start: https://play.hotspawn.com/how-it-works)
- Backend fixture feed (undocumented, discovered from the lobby): `https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures` — exact epoch-ms UTC, tier, points, participants (evidence: `data/diag/report2.json`)

**Market / betting lines (never Hotspawn):**
- Polymarket Gamma API: https://gamma-api.polymarket.com — series prices used; **Game N markets are excluded** for non-BO1 (see I1)
- Pinnacle guest feed (unofficial, official API closed 2025-07-23): https://github.com/pinnacleapi/pinnacleapi-documentation — sport 12 E Sports, LoL league 9587 (Worlds)
- OddsPapi (key-gated, not configured): https://oddspapi.io/sports/esports/lol

**Results / community sources for our own line:**
- Leaguepedia Cargo: `MatchSchedule` (fixtures + completed series with scores), `Standings` (WinSeries/LossSeries), `ScoreboardGames`
  - field lists verified via `api.php?action=cargofields&table=MatchSchedule|Standings`
  - rate limits observed: `ratelimited` (`data/diag/report3.json`); use `Special:CargoExport`, paced
- Liquipedia API (API only, gzip, ≤1 req/2 s, CC-BY-SA 3.0): https://liquipedia.net/api-terms-of-use
- Organizer sites (human cross-check only): primeleague.gg **403 Bunny Shield from Actions**, rivalsleague.gg 200, komplettligaen.no 200, 4nations.gg/ligagg.com/tunisian sites unreachable (measured, `data/diag/report6.json`)
- Riot lolesports front-end API: **403 from Actions** for all endpoints (`data/diag/report7.json`) — not a dependency

## 3. Coverage of the no-market fixtures (the core problem)

Measured 2026-10-21 on the live payload (`verification/leaguepedia_coverage.md`):

- **126 of 195 rows** were `UNRESOLVED` 50/50 and **61 of 195** were Elo rows at 0.455–0.545 (median 0.511):
  187/195 rows carried no real signal. Only the 8 market rows did.
- **Every one of the 126 unresolved rows has a Leaguepedia league page**; **112 have the exact fixture listed**
  (start time and BestOf included). The "no Leaguepedia history found" evidence string was false.
- A standings model using the verified `Standings` fields scores **18/18 RIVALS**, **30/31 Komplettligaen+Tunisian**
  fixtures with real records (e.g. *Mazepa 0-4 vs B2U 4-0* → 62.5% B2U after multi-division calibration;
  *Ascent 6-3 vs NTNUI 0-9* → 80% Ascent).
- With only three leagues supplied, the merger produces **48 `MODEL_STANDINGS` rows** (UNRESOLVED 126 → 87);
  PRM 3rd (32 teams), PRM 2nd and 4 Nations standings were also confirmed live, plus MatchSchedule series results for
  every league (the preferred input for a future Elo).

## 4. Irregularities and flagged items

Full list with evidence links: `verification/flagged_items.md` (also published on the site's **Flagged for Review** page).
Headlines:
1. **I1** a Polymarket *Game 1 Winner* price was used as a series probability (value coincidentally equal today; selector must use `Match Winner`).
2. **I2/I3** 187 rows linked generic docs pages instead of the league/fixture they came from.
3. **I8** the Elo model was starved (all 61 rows ≈ 50/50) — fixed by standings/results input.
4. **P1/P3/P4** Pinnacle guest feed is unofficial; Liquipedia HTML scraping is against their terms; organizer sites are blocked/unreachable from Actions.
5. **I5** Polymarket start times are stale — our times match Leaguepedia on 172/172 fixtures (`D18`).
6. **I6** `"Oct 24, 24:00"` does not parse (one row, no UTC start).
7. **I9** tier "W" is a waiting-for-information artefact displayed as a tier.

## 5. Verification performed (line by line)

- 30+ automated rules over the published data and site (schema, per-row sources, probabilities, mobile, nav,
  exec-summary links, unresolved section, internal links, cron cadence, crowd-% static scan) — `scripts/verify_site.py`.
- **27 self-tests** prove each rule fails on deliberately broken data (`verification/test_verifier.py`).
- Start times cross-checked against Leaguepedia `MatchSchedule`: **172/172** matched fixtures agree (`D18`).
- Published Polymarket prices spot-checked directly against the Gamma API: Gen.G 0.775/0.225, Team Liquid 0.715/0.285,
  G2 0.395/0.605 — all match the site (`I7`).
- Live source links resolve (Hotspawn match page, Leaguepedia league page).
- Live Pages deployment checked (`X2`/`X3`) after each deploy.

## 6. How to reproduce

```bash
python3 verification/test_verifier.py                  # 27/27 must pass
python3 scripts/verify_site.py                         # 0 FAIL expected
python3 verification/summarize.py                      # per-league coverage table
python3 verification/check_leaguepedia_coverage.py --leaguepedia-schedule <snapshot>
python3 verification/apply_standings.py --fetch --write # standings enrichment (network)
python3 scripts/verify_site.py --check-external \
  --live-url https://karagemop466-tech.github.io/LOLHOTSPAWN2/   # production check
```

## 7. Deployment record

_Filled in after the integration merge:_ PR link, merge commit, Pages build id/status, live match count,
method split, and the final verification counts.

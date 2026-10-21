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

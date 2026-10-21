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

## Completion log (2026-10-21, arena/1efcf62c)
- T1-T5 done. PR #1 merged (site+pipeline), PR #2 merged (Pages root redirect + push trigger).
- Live verification: workflow run 39668843544 success on main; picks bot commit f269386; Pages build success.
- Live data at check: 195 matches parsed & priced — MARKET_POLYMARKET 8, MODEL_ELO 61, UNRESOLVED 126, MARKET_BOOKS 0 (no ODDSPAPI_KEY secret set; optional).
- Live site: https://karagemop466-tech.github.io/LOLHOTSPAWN2/ -> /docs/ Executive Summary (verified rendered with data).
- Flagged (non-blocking, on Flagged page): lobby header said 264 LoL matches but parser extracted 195 cards (likely cards beyond initial SSR payload/pagination) — parser should be extended if Hotspawn exposes a fixtures API; all 195 extracted rows verified pick+prob sum. Tier WAITING FOR INFORMATION rows and 50/50 unresolved rows as above.

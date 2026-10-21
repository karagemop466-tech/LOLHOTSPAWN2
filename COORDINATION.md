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

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
| T11 Verification: link/schema/coverage checks in CI, DOM smoke test, Pages deploy confirmation | in progress | arena/fa3f554c | scripts/update_picks.py, .github/workflows/*.yml |
| T12 PR to main, merge, Pages deploy confirmation | pending | arena/fa3f554c | COORDINATION.md |

**Session file scope:** `scripts/**`, `.github/workflows/**`, `docs/**`, `data/**`, `COORDINATION.md`, `README.md`. No other session is active; if another session claims a task, it must not edit these paths without logging a request here.

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

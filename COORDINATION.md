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
| T7 Full-coverage Hotspawn lobby parser (all tiers incl. "WAITING FOR INFORMATION", exact UTC times) | in progress | arena/fa3f554c | scripts/update_picks.py, scripts/lobby_parse.py |
| T8 Live source probe: established bookmakers, esportsbooks, prediction markets, community sources | in progress | arena/fa3f554c | scripts/diag_lab.py, data/diag/** |
| T9 Own-line model v2 (Leaguepedia + Liquipedia + aliases + roster fallback) for no-market matches | in progress | arena/fa3f554c | scripts/model.py, scripts/update_picks.py |
| T10 Mobile-first site rebuild: executive summary with in-site links, table views, unresolved section | in progress | arena/fa3f554c | docs/** |
| T11 Verification: link check, schema check, coverage check, deploy confirmation | unclaimed | — | scripts/verify_site.py |
| T12 PR to main, merge, Pages deploy confirmation | unclaimed | — | COORDINATION.md |

**Session file scope:** `scripts/**`, `.github/workflows/**`, `docs/**`, `data/**`, `COORDINATION.md`, `README.md`. No other session is active; if another session claims a task, it must not edit these paths without logging a request here.

## Sources & verification log

| Date | Source | What it verified | Link |
|---|---|---|---|
| 2026-10-21 | Hotspawn LoL Pick'em lobby | Fixture list, tier/points, crowd % (context only), match links | https://play.hotspawn.com/lol-pickems |
| 2026-10-21 | Hotspawn "How it works" | Picks lock 5 minutes before match start | https://play.hotspawn.com/how-it-works |
| 2026-10-21 | Leaguepedia Cargo API docs | ScoreboardGames / MatchSchedule tables | https://lol.fandom.com/api.php?action=help&modules=cargoquery |
| 2026-10-21 | Polymarket Gamma API | Public LoL event/market prices | https://gamma-api.polymarket.com |
| 2026-10-21 | Pinnacle API docs (retired public API) | Why direct Pinnacle access is not used | https://github.com/pinnacleapi/pinnacleapi-documentation |

## Irregularities / flagged items
- Sandbox egress is restricted to GitHub/PyPI; all live-source verification is executed in GitHub Actions and the raw results are committed under `data/diag/` for manual review.
- Hotspawn renders fixture times in the visitor's local timezone. Any UTC time derived from the rendered text alone is unverified; the production parser must take the timestamp from page data and cross-check against Leaguepedia/Riot schedules.
- Lobby tier filter advertises 264 LoL fixtures while the previous parser captured 195; the difference (mostly tier C/D and "WAITING FOR INFORMATION") was silently dropped rather than flagged.

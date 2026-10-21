# verification/ — how to check this project line by line

| file | purpose | run |
|---|---|---|
| `../scripts/verify_site.py` | 30+ rule checks over the published data, every row's source link, mobile viewport, in-site summary links, unresolved section, internal links, 4–8h workflow cadence, crowd-% static scan, plus a REQ1–REQ12 traceability matrix | `python3 scripts/verify_site.py [--leaguepedia-schedule data/diag/lp_schedule.json] [--check-external] [--live-url https://karagemop466-tech.github.io/LOLHOTSPAWN2/]` |
| `test_verifier.py` | 27 self-tests: each check must FAIL on deliberately broken data (no false negatives) | `python3 verification/test_verifier.py` |
| `check_leaguepedia_coverage.py` | per-fixture audit: is there an official/trusted results page for each unresolved row? | `python3 verification/check_leaguepedia_coverage.py --schedule <MatchSchedule snapshot>` |
| `leaguepedia_line.py` | independent, explainable Elo line from Leaguepedia ScoreboardGames (differential check / fallback for no-market fixtures) | `python3 verification/leaguepedia_line.py --results <SG snapshot> --schedule <schedule snapshot>` |
| `INTEGRATION.md` | T12 integration checklist (merge → verify → CI → PR → deploy) | read |
| `report.json`, `last_report.md` | latest verifier output (machine + human readable) | generated |
| `leaguepedia_coverage.*` | latest coverage audit | generated |

Rules used by every report: a value is only "verified" with a link to the page it came from. Unconfirmed values are
left blank/50-50 and flagged — never inferred. Hotspawn is a fixture source only; its crowd percentages never feed a
probability.

# LOLHOTSPAWN2 — Hotspawn LoL Pick'em, priced for every match

Mobile-first dashboard published with GitHub Pages:
**[Executive summary](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/)** (the repo root redirects there) ·
[all picks](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/picks.html) ·
[unresolved & low confidence](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/unresolved.html) ·
[flagged for review](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/flagged.html) ·
[methodology & sources](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/methodology.html).

Every League of Legends fixture listed on
[Hotspawn's Pick'em lobby](https://play.hotspawn.com/lol-pickems) gets a pick and a win
probability for both teams. Rows are priced in this order:

1. **External market consensus** — de-vigged two-way lines from Pinnacle, Bovada and
   Polymarket (median if ≥3 sources, otherwise a fixed-quality weighted mean).
2. **Our own Elo model** — chronological ratings from Leaguepedia's recorded results,
   anchored to competition-strength tiers, with inactivity decay, BestOf/margin weighting,
   head-to-head smoothing and shrinkage for thin history.
3. **Official league standings** — no book prices the national/amateur leagues, but
   Leaguepedia publishes their win–loss tables. The record is converted to a rating
   (shrunk by sample size) and compared with the other side; thin Elo samples are
   blended 50/50 with it. Rows are labelled `MODEL_STANDINGS` /
   `STANDINGS_BLENDED` and link the exact league page.
4. **League prior** — one team has neither enough history nor a standings row: the
   competition median / tournament tier prior is substituted, shrunk toward 50/50 and
   labelled `MODEL_LEAGUE_PRIOR` (low confidence).
5. **Unresolved** — no market, no history and no standings row: published as an explicit
   50/50 placeholder, listed on its own page with the written limitations. Never an edge.

**Hotspawn is used for the fixture list only.** Its crowd percentages are displayed as
context and are never an input to any probability. Unverified or irregular rows are
published on the *Flagged for review* page, with source links, and do not block a release.

## Automation

`.github/workflows/update-picks.yml` runs every 6 hours (and on demand / on `main` script
changes): it fetches the Hotspawn fixture list, external prices and Leaguepedia results,
rebuilds the model, verifies the payload and the static site
(`scripts/verify_site.py`), then commits `docs/data/picks.json`. GitHub Pages serves
`main:/docs`, so the site refreshes with the commit.

`.github/workflows/pipeline-test.yml` is the branch verification runner: it executes the
same live pipeline on `arena/**` and commits the payload + `data/diag/pipeline.log` for
inspection.

## Data sources

| Source | Used for | Link |
|---|---|---|
| Hotspawn fixture API | Fixture list, tournament, exact UTC start, match links | https://play.hotspawn.com/lol-pickems |
| Pinnacle guest JSON | Two-way moneyline | https://www.pinnacle.com/en/esports/league-of-legends |
| Bovada coupon JSON | Two-way moneyline | https://www.bovada.lv/sports/esports/league-of-legends |
| Polymarket Gamma API | Match/series prices | https://gamma-api.polymarket.com |
| Leaguepedia CargoExport | Recorded results + schedule + canonical team names | https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule |
| Leaguepedia Standings | Official win–loss table per league (low-tier fixtures with no book) | https://lol.fandom.com/wiki/Special:CargoTables/Standings |

`scripts/probe_markets.py` requests 31 additional books/exchanges/aggregators once per
pipeline run and records the measured HTTP status and whether the body contained
two-way prices (`data/diag/market_probe.json`). The results are published on the
*Flagged for review* page. Providers that were checked and could not be used (403/404/502,
paid key required, no per-match markets) are listed with their observed status on the
[Flagged page](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/flagged.html).

## Local run

```bash
python3 scripts/probe_markets.py           # measure candidate betting sources
python3 scripts/update_picks.py            # live fetch + model + publish
python3 scripts/update_picks.py --use-cache  # reuse data/cache/*.json
python3 scripts/verify_site.py             # schema + link + page checks
python3 verification/test_model_standings.py  # offline standings / tier-prior test
```

Caches (`data/cache/`) are generated and git-ignored. Not betting advice; no affiliation
with Hotspawn, Riot Games or any bookmaker.

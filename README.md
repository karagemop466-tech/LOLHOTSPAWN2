# LOLHOTSPAWN2 — Hotspawn LoL Pick'em, priced for every match

Mobile-first dashboard published with GitHub Pages:
**[Executive summary](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/)** (the repo root redirects there) ·
[all picks](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/picks.html) ·
[by league / tier](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/leagues.html) ·
[unresolved & low confidence](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/unresolved.html) ·
[flagged for review](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/flagged.html) ·
[methodology & sources](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/methodology.html).

Every upcoming scheduled League of Legends fixture listed on
[Hotspawn's Pick'em lobby](https://play.hotspawn.com/lol-pickems) gets a clear pick and win
probability (%) for both teams. Cancelled upstream fixtures are excluded and audited on Flagged.
Rows are priced in a strict 5-tier cascade:

1. **External market consensus (`MARKET_CONSENSUS` / `MARKET_SINGLE`)** — deduplicated full-match two-way lines (1 main board per bookmaker; all child prop/map markets rejected, enforced by check `D20`) from Pinnacle, Unibet (Kambi), Bovada and Polymarket (median if ≥3 sources, otherwise a fixed-quality weighted mean).
2. **Chronological Tier-Anchored Elo (`MODEL_ELO` / `MODEL_ELO_THIN`)** — computed from 24 months of completed series on Leaguepedia (`MatchSchedule`), anchored to competition-strength tiers, with inactivity decay, BestOf/margin weighting, head-to-head smoothing, competition-scoped disambiguation, and deterministic UTC schedule bridging.
3. **Standings model (`MODEL_STANDINGS` 📊)** — when there is no book line and a side has no Elo yet but has a current-split win-loss record on Leaguepedia *Standings*, the record becomes a smoothed Elo offset from the competition prior, capped at Low/Medium confidence because it ignores strength of schedule.
4. **League prior (`MODEL_LEAGUE_PRIOR`)** — one team lacks both match history and split standings; the competition median/tier prior is substituted, shrunk toward 50/50 and capped at Low confidence.
5. **Unresolved (`UNRESOLVED`)** — neither external lines nor recorded team/standings evidence exist: published strictly as an explicit `50.0% / 50.0%` placeholder on its own Unresolved & Limitations page (including a per-league table of which signal prices each league). Never an edge.

**Hotspawn is used for the fixture list only.** Its crowd percentages are displayed as
context and are never an input to any probability. Every table row carries direct links to
its verified sources, and any upstream irregularity is surfaced on *Flagged for review*.

## Automation & Verification

- `.github/workflows/update-picks.yml` runs every 6 hours (`0 */6 * * *`), fetches live fixtures, market odds, Leaguepedia results/standings, and Liquipedia API metadata, runs `scripts/verify_site.py`, and commits updated `docs/data/picks.json` directly to `main`.
- `.github/workflows/verify.yml` runs every 6 hours (`30 */6 * * *`) against external links and the deployed GitHub Pages URL (`--check-external --live-url`).
- `.github/workflows/pipeline-test.yml` runs end-to-end live verification on `arena/**` branches (`check_dom_contract.py`, `test_verifier.py`, `test_entity_and_books.py`, `verify_site.py --leaguepedia-schedule data/diag --check-external`).

## Data sources

| Source | Used for | Link |
|---|---|---|
| Hotspawn Pick'em lobby & fixtures API | Upcoming scheduled fixture list, UTC lock timestamps, match links | https://play.hotspawn.com/lol-pickems |
| Pinnacle guest JSON | Sharp 2-way match moneyline (main parent boards only) | https://www.pinnacle.com/en/esports/league-of-legends |
| Unibet (Kambi CDN JSON) | 2-way pre-match series moneyline | https://www.unibet.com/betting/sports/filter/esports/league_of_legends |
| Bovada coupon JSON | 2-way pre-match series moneyline | https://www.bovada.lv/sports/esports/league-of-legends |
| Polymarket Gamma API | Public prediction-market reference probabilities | https://gamma-api.polymarket.com |
| Leaguepedia CargoExport (CC BY-SA 3.0) | Recorded series results (`MatchSchedule`) + split standings (`Standings`) | https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule |
| Liquipedia MediaWiki API (CC-BY-SA 3.0) | Compliant tournament metadata index (`api.php`, gzip, ≥2.2s pacing) | https://liquipedia.net/leagueoflegends/api.php?action=query&meta=siteinfo&format=json |

## Mobile experience

The site is one dashboard with one shared header, one shared primary nav and one shared
six-item thumb bar; every page is designed for a 360–430 px phone first. The executive
summary opens with a **Where the picks are** card that jumps straight to the updated
list, the next 24 hours, the per-league view, or the unresolved/limitations page, each
with a live count. A colour-theme button in the header works on every page.
`verification/mobile_audit.md` records the 2026-10-24 audit (eight defects found and
fixed — including an executive-summary header that was clipped to 12 px by a
class-name collision, and a theme button with no handler) and lists the checks that now
make those regressions fail CI.

## Local verification

```bash
python3 scripts/update_picks.py                 # live fetch + model + publish
python3 verification/check_dom_contract.py      # C1–C6: ids, header/nav skeleton, class coverage, dead controls, mobile rules
python3 verification/test_dom_contract.py       # 7/7 negative self-tests for the contract above
npm install --no-save jsdom@24 && node verification/render_smoke.js   # 63/63 real-app render checks
python3 verification/test_verifier.py           # 35/35 verifier unit self-tests
python3 verification/test_entity_and_books.py   # 10/10 entity & bookmaker unit tests
python3 scripts/verify_site.py                  # full schema + link + page audit
python3 scripts/probe_sources.py                # refresh the candidate-source measurements (CI, not sandbox)
```

Not affiliated with Hotspawn, Riot Games or any bookmaker. Not betting advice.

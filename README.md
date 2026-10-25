# LOLHOTSPAWN2 — Hotspawn LoL Pick'em, priced for every match

Mobile-first dashboard published with GitHub Pages. The executive summary opens with a
**"Where the updated picks are"** block (four large in-site links: all picks, next 24 h, by league,
unresolved & limits) and repeats the unresolved-picks + limitations section in full:
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

> **Finding the picks on a phone.** Every page carries the same six-target **quick-jump
> bar** (All picks · Next 24 h · No book line · By league · Unresolved · Flagged) directly
> under the header, plus the fixed bottom bar (Summary · Picks · Leagues · Unresolved ·
> Flagged · Method). The executive summary then runs: *Where the updated picks are* →
> the matches locking soonest (cards) → coverage → **"🧮 Matches without a featured
> betting line — how each pick is made"** → per-competition table → featured picks →
> unresolved. **Unresolved picks and their limitations are a separate section on the
> executive summary itself** — every unresolved fixture is listed there with its source
> links, next to a per-league table of what prices that league and where its limit is.
> Long research tables are collapsed into `<details>` so a 390 px phone reaches the picks
> without scrolling past them.

1. **External market consensus (`MARKET_CONSENSUS` / `MARKET_SINGLE`)** — deduplicated full-match two-way lines (1 main board per bookmaker; all child prop/map markets rejected, enforced by check `D20`) from Pinnacle, Unibet (Kambi), Bovada and Polymarket (median if ≥3 sources, otherwise a fixed-quality weighted mean).
2. **Chronological Tier-Anchored Elo (`MODEL_ELO` / `MODEL_ELO_THIN`)** — computed from 24 months of completed series on Leaguepedia (`MatchSchedule`), anchored to competition-strength tiers, with inactivity decay, BestOf/margin weighting, head-to-head smoothing, competition-scoped disambiguation, and deterministic UTC schedule bridging.
3. **Standings model (`MODEL_STANDINGS` 📊)** — when there is no book line and a side has no Elo yet but has a current-split win-loss record on Leaguepedia *Standings*, the record becomes a smoothed Elo offset from the competition prior, capped at Low/Medium confidence because it ignores strength of schedule.
4. **League prior (`MODEL_LEAGUE_PRIOR`)** — one team lacks both match history and split standings; the competition median/tier prior is substituted, shrunk toward 50/50 and capped at Low confidence.
5. **Unresolved (`UNRESOLVED`)** — neither external lines nor recorded team/standings evidence exist: published strictly as an explicit `50.0% / 50.0%` placeholder on its own Unresolved & Limitations page (including a per-league table of which signal prices each league). Never an edge.

Every refresh also re-requests a fixed list of 22 established sportsbooks, esportsbooks, exchanges,
odds aggregators, prediction markets and community/official result pages **once each** and publishes
exactly what they returned (`market_probe`: HTTP status, JSON or HTML, and whether any League of Legends
match market was visible). That is reachability evidence only — no probed value is ever used in a
probability, and the sources needing API keys are recorded as such instead of guessed at.

**Hotspawn is used for the fixture list only.** Its crowd percentages are displayed as
context and are never an input to any probability. Every table row carries direct links to
its verified sources, and any upstream irregularity is surfaced on *Flagged for review*.

## Matches the featured picks cannot resolve

Everything with a bookmaker line is a *featured* pick. Everything else still gets a pick,
from our own line, and the site says exactly what that line is built on: a
**"Matches without a featured betting line"** section on the executive summary with one
row per competition (fixtures, how many have a book line, the Elo / split-standings /
prior mix behind the rest, the confidence cap and the competition's results page) plus a
dated table of the books and esportsbooks that were actually opened for those leagues and
what each returned. Nothing in that table is used as a probability input.

**Coverage rule (fixed 2026-10-25).** A fixture is priced when it is listed on the
Hotspawn lobby with status `scheduled`, taking the **union** of the lobby transfer state
and the fixtures API. Before this change the priced set came from the API rows only, so a
fixture the lobby listed but the API lagged on was silently dropped: `Team Lucidity
Esports vs Fritt Fall` (RIVALS LEAGUE Season 2, 2026-10-31T17:30Z, fixture 1090065) had
no pick and no exclusion entry in the 2026-10-25T10:41Z payload. `merge_fixture_sources()`
now unions both sources, `coverage_reconciliation.lobby_only_in_union` /
`lobby_only_priced` record what came from that path, `audit/coverage_reconcile.py`
re-reads both sources with its own parser after every refresh, and
`audit/coverage_gate.py` fails a refresh when a Hotspawn fixture that starts more than 30
minutes later has neither a pick nor a documented exclusion.

## Line-source research: is there a book line for the low-tier fixtures?

The 164-fixture snapshot of 2026-10-24 had 9 fixtures with an external betting line; the rest (PRM 2nd/3rd
Division, Tunisian Super League, RIVALS LEAGUE, Arabian League 2nd Division, 4 Nations, Komplettligaen, LCP
Promotion, LigaGG) were priced by our model. Two probes answer whether that is avoidable:

* `scripts/source_probe.py` runs in **every** production refresh and publishes `market_probe` — reachability
  status for every established book, esportsbook, aggregator and community site (rendered on the
  Unresolved & Method pages).
* `scripts/probe_lines.py` (`.github/workflows/line-probe.yml`, manual, ~1 min) goes further: it asks each
  source for **two-way main-match prices**, then matches what it finds to the published fixtures by team
  name **and** start time, so it can report how many of our model-only rows a source would actually cover.
  Evidence: `data/diag/line_probe.json`; write-up: `research/betting-sources.md` §15.

**Measured result (39 requests, 30 sites): 0 sources cover a single model-only fixture.** Pinnacle's league
index lists one LoL league (World Championship); nine Kambi/Unibet country markets return the same eight
World Championship matches; bmbets' LoL index stops at Worlds, LCP and Game Changers Rising; SofaScore,
eGamersWorld, Oddspedia, GGScore, Winamax, Marathonbet, Betano, Stake, GG.Bet, Thunderpick and others answer
403/404/410/503 to CI; the 1xBet/Betwinner/Melbet LineFeed returns a geo-restriction stub; bo3.gg has no odds
fields. A source is only promoted into `scripts/fetch_markets.py` when it returns prices for fixtures in the
published list **and** a human has verified a sample row — neither probe ever writes a probability.

## Automation & Verification

- `.github/workflows/update-picks.yml` runs every 6 hours (`0 */6 * * *`), fetches live fixtures, market odds, Leaguepedia results/standings, and Liquipedia API metadata, runs `scripts/verify_site.py`, and commits updated `docs/data/picks.json` directly to `main`.
- Both publisher workflows run `audit/coverage_reconcile.py` + `audit/coverage_gate.py` after
  the payload is written, so a Hotspawn fixture with no pick fails the run instead of
  disappearing, and the reconciliation report is committed next to the payload.
- `.github/workflows/verify.yml` runs every 6 hours (`30 */6 * * *`) against external links and the deployed GitHub Pages URL (`--check-external --live-url`), and runs the jsdom render harness so a page that fails to render cannot pass verification.
- `verification/check_dom_render.js` renders all seven pages from the committed payload in jsdom and asserts the visible result: row counts, pick ∈ {team1, team2}, probabilities summing to 100%, a source link on every row, the summary's in-site pick links, and the separate unresolved section (including a synthetic payload with unresolved fixtures, so the section is never vacuous).
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
| Liquipedia MediaWiki API (CC-BY-SA 3.0) | Compliant tournament metadata index (`api.php`, gzip, ≥2.2s pacing) — page-prefix probe fixed 2026-10-24 | https://liquipedia.net/leagueoflegends/api.php?action=query&meta=siteinfo&format=json |
| External-source probe (22 candidates, diagnostic) | Per-refresh reachability of books/esportsbooks/aggregators; never a probability input | https://github.com/karagemop466-tech/LOLHOTSPAWN2/blob/main/research/betting-sources.md |

## Local verification

```bash
python3 scripts/update_picks.py                 # live fetch + model + external-source probe + publish
python3 verification/check_dom_contract.py      # C1–C7: ids, header/nav skeleton, class coverage, dead controls, mobile rules
python3 verification/test_dom_contract.py       # negative self-tests — every rule must fail on a broken page
python3 verification/test_verifier.py           # verifier rule self-tests (incl. D22 probe + S11–S15 structure)
python3 verification/test_entity_and_books.py   # entity & bookmaker unit tests (incl. Bovada period regression)
python3 verification/test_lobby_union.py        # lobby ∪ fixtures-API merge (coverage rule)
python3 verification/check_source_pages.py      # every cited Leaguepedia tournament page must exist (needs network)
python3 audit/coverage_reconcile.py             # independent lobby/API vs payload reconciliation (needs network)
python3 audit/coverage_gate.py                  # fails only on a real coverage hole (>30 min out)
python3 scripts/verify_site.py                  # full schema + link + page audit (incl. S11–S15)
python3 scripts/probe_lines.py                  # fixture-matched line-source probe (diagnostic)
npm i --no-save jsdom && node verification/render_check.cjs   # executes the real JS on all pages (incl. the theme toggle)
node verification/check_dom_render.js           # jsdom render checks (all pages)
```

The header carries a working colour-theme button on every page (`<html data-theme>`, persisted in
`localStorage`, overriding the OS preference in both directions). `check_source_pages.py` exists because
Leaguepedia answers **HTTP 200 with an empty body** for a title that does not exist, so a 200 from
`verify_site.py --check-external` is not proof that a cited tournament page is real; the script asks the
MediaWiki API in one batched read-only request. `verification/mobile_audit.md` records the 2026-10-24 audit
of the pages against their stylesheet.

`scripts/verify_site.py` includes **S16** (every page ships the same quick-jump bar and the
executive summary itself contains the non-featured section with its source table) and
**S17** (phone layout contract: `width=device-width` everywhere, a breakpoint at or below
430 px, and no hard-coded width above 430 px), on top of **S11** (every CSS class a page uses must have a rule in `style.css` — the
check that catches an unstyled or clipped header) and **S12** (all pages share one navigation, a visible
freshness slot and unique ids). `verification/render_check.cjs` loads each page in jsdom with the committed
payload and asserts that the picks, tables and counts actually render.

Not affiliated with Hotspawn, Riot Games or any bookmaker. Not betting advice.

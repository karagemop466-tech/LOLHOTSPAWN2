# Coordination Board

## Session `arena/91450d23-lolhotspawn2` — 2026-10-25 (reliability + diagnosability)

> Branch note: Arena fixes this session to `arena/91450d23-lolhotspawn2`; the tooling does not permit creating other
> branches, so that branch stands in for `session-<id>/<task>`.

**Overlap resolved.** This session first claimed the same four workstreams as session `arena/6e003eec` (T25–T28,
claimed 14:06:54Z — three minutes before this session's first claim). Under the board rule *never start a task another
session has claimed*, this session dropped verification/research/site/integration and kept only the reliability work
below. `main` meanwhile advanced through PRs #67/#68/#70/#73 and more sessions; this branch was then **reset onto
`main` (`bc38b0b`)** so it carries exactly one change on top of current `main`.

| Task | Status | Owner | Files |
|---|---|---|---|
| W1 Forensics: why did the scheduled refresh `40156916426` (2026-10-25T03:05Z) fail? | done | arena/91450d23 | `COORDINATION.md` |
| W2 Diagnosability: a failed refresh must explain itself in the one log the workflow keeps | done | arena/91450d23 | `scripts/update_picks.py` |
| W3 Independent verification of `main` at `bc38b0b` (all suites + verifier + jsdom render) | done | arena/91450d23 | `COORDINATION.md` |
| W4 Takeover of another session's tasks | not needed — no claim went stale while this session ran | — | — |
| PR + merge + deploy record | done — PR #80 merged, publisher and Pages green | arena/91450d23 | `COORDINATION.md` |

### W1 — what is established, and what is not

| Question | Answer | Evidence |
|---|---|---|
| Which step failed? | Step 6 **“Verify the published payload”** of run [40156916426](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40156916426); steps 1–5 succeeded, step 7 (failure log) succeeded, step 8 (commit) was skipped. | job `121060138275`, step list via the Actions API |
| Did the generator work? | Yes. The committed log reads `hotspawn: 145 future LoL fixtures`, `markets: Pinnacle ok (8) · Unibet ok (8) · Bovada ok (6) · Polymarket ok (9)`, `leaguepedia: 31739 results … 2880 standings`, `model: 145 fixtures, 145 resolved, 0 unresolved`, `wrote docs/data/picks.json`. | `git show 195d230:data/diag/pipeline.log` |
| Which verifier check failed? | **Not established and not guessed.** The step's console log is only served through a 302 to `productionresultssa5.blob.core.windows.net`, which this sandbox cannot reach (curl exit 000); the step uploaded no artifact, and the only file the failure step commits is `pipeline.log` — the generator's own output. | attempts on `/actions/jobs/121060138275/logs` → 302 → host unreachable |
| User-visible effect | The site kept the 2026-10-24T20:10Z payload until the next successful run (2026-10-25T10:39Z) — 6 h 18 m — and because `stale_after_utc` is 8 h the freshness banner never fired, so nothing on the site said a refresh had failed. | run list; payload `generated_at` before/after |

### W2 — the fix (this branch's only code change)

`scripts/update_picks.py` now re-runs `scripts/verify_site.py` on the payload it just wrote and copies the failing check
ids plus their annotation lines into stderr — the stream the workflow tees into `data/diag/pipeline.log`, the one file a
failed run commits. It never edits the payload, never raises, and its exit status is ignored: the workflow's own verify
step stays the gate.

* Live proof on the earlier branch run [40202018891](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40202018891):
  the committed log contains `preflight: verify_site.py PASS (exit 0) — == PASS · pass 44 · fail 0 · warn 0 · skip 1 ==`.
* Non-vacuity proof: corrupting three fields (a probability that no longer sums to 1, a pick that is not a team, a
  duplicated fixture) drops the verifier to **37 pass / 7 fail** and the pre-flight reproduces the failing check ids and
  rows in the log; restoring the payload returns **49 pass / 0 fail**.

### W3 — verification of `main` at `bc38b0b` (independent of the other sessions)

| Gate | Result |
|---|---|
| `python3 scripts/verify_site.py` | **49 PASS · 0 FAIL · 0 WARN · 1 SKIP** (D18 skipped without a schedule snapshot) |
| `verification/check_dom_contract.py` / `test_dom_contract.py` | PASS / 7/7 |
| `verification/test_verifier.py` | 64/64 (includes the new `S19` phone-layout self-tests) |
| `verification/test_entity_and_books.py` | 17/17 |
| `verification/test_standings_model.py` / `test_evidence_scope.py` | ALL PASS / OK |
| `audit/test_model.py` | 23 passed · 0 failed |
| `node verification/render_check.cjs` / `check_dom_render.js` | RENDER CHECK PASS / 67/67 |

### Irregularities found during this session

| ID | Item | State |
|---|---|---|
| R1 | **Dead external citation blocked `main`'s own verification.** `docs/flagged.html` row A12 linked `https://polymarket.com/esports/league-of-legends/prime-league-1st-division`, which returns **404**; `main`'s scheduled *Verify picks and site* run [40202537346](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40202537346) failed at step 6 for that reason, and this branch's live run [40202799707](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40202799707) reproduced it (`X1 … 1 dead (404/410)`). | **Fixed upstream** while this session ran: another session rewrote A12 as “Historical Polymarket PRM category link is unverified” (no price inferred). Verified present in `main@bc38b0b`; this branch deliberately carries no duplicate edit. |
| R2 | A failed production refresh keeps **no verifier output**, so its cause cannot be recovered afterwards (W1). | Mitigated in the generator by W2. The remaining gap is a workflow line this session does not own: add `verification/report.json` and `verification/last_report.md` to the failure step's `git add` in `.github/workflows/update-picks.yml`. |
| R3 | This session's first branch state silently reverted newer `main` files (`-X theirs` applied to the branch's own pipeline-test merge). Caught by `verification/test_verifier.py` — 9 self-tests failed because `S19` was missing from `scripts/verify_site.py`. | **Fixed** by resetting the branch onto `main@bc38b0b` and re-applying only the pre-flight; no other session's work was involved or lost (`backup-91450d23` kept locally for audit). |

### PR & deploy record (this session)

| Item | Result |
|---|---|
| PR | [#80](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/80) — **merged** 2026-10-25T14:59Z (merge commit `1944655`), 2 code/doc files plus generated artefacts, no probability, pick or layout change |
| Branch checks before merge | Pipeline test [40204771866](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40204771866) **success** on head `ab0e409` (live pipeline + all suites + jsdom 82/82 + external link check) |
| Post-merge publisher | *Update Hotspawn LoL picks* run [40204777006](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40204777006) **success** on `1944655` (payload 2026-10-25T14:59Z) |
| Post-merge Pages | *pages build and deployment* run [40204776704](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40204776704) **success** for `1944655`; Pages API `status: built` |
| Pre-flight in production | `main`'s published `data/diag/pipeline.log` now ends every refresh with e.g. `[2026-10-25T15:02:30+00:00] preflight: verify_site.py PASS (exit 0) - == PASS · pass 51 · fail 0 · warn 0 · skip 1 ==` — the next failure will name its check and row instead of only "step 6 failed" |
| Live snapshot after the merge | payload `generated_at 2026-10-25T15:02:30.411019Z` · **156 fixtures · 156 resolved · 0 unresolved** · 9 with external market (8 four-book consensus + 1 single Polymarket line) · 54 priced with split standings · 11 low-confidence, all flagged · 9 cancelled fixtures excluded and listed |
| Site | https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/ (root `index.html` redirects to `docs/`) |

Any other session that needs a file in this scope must log a request here instead of editing it.

## Session `arena/0e9a9550-lolhotspawn2` — 2026-10-25 (claim, pushed before work)

No other session has an active claim on the files below as of 2026-10-25 14:15 UTC: the newest board entry
(`arena/26d1e778`, reliability fixes) is **merged to `main`** (PR #58) and its follow-up PR #59 only appends to
this board. `main` is at `2173cc9` ("picks: scheduled refresh [skip ci]", payload generated 2026-10-25T10:41:50Z,
156 fixtures / 0 unresolved). This session works only inside the claimed scope.

| Task | Status | Owner | Files (claimed scope) |
|---|---|---|---|
| T25 Live coverage re-verification against the *current* Hotspawn lobby: read the lobby as a visitor, reconcile its listed/upcoming LoL count with the published payload, and confirm no upcoming fixture is missing | claimed | arena/0e9a9550 | `audit/**`, `verification/**` |
| T26 Fresh, link-verified research for the fixtures that **cannot** be priced like the featured picks (established LoL betting sites → esportsbooks → esports betting lines → community), and wire the probed per-competition URLs into the diagnostic probes so CI re-checks them every run | claimed | arena/0e9a9550 | `research/betting-sources.md`, `scripts/probe_lines.py`, `scripts/source_probe.py` |
| T27 Phone/mobile usability pass: a first-screen "next picks" block and a jump bar on the executive summary, a separate **non-featured picks** section (how each is resolved + which sources were checked), per-competition source coverage on `unresolved.html`, 390 px readability | claimed | arena/0e9a9550 | `docs/*.html`, `docs/assets/*` |
| T28 Verifier extensions for the new required sections (exec-summary non-featured section with a source link on every row, jump bar on every page, mobile CSS has no fixed width > 390 px) + self-tests | claimed | arena/0e9a9550 | `scripts/verify_site.py`, `verification/**` |
| T29 Integration: live pipeline run on this branch, full re-verification, PR → `main`, merge without waiting, confirm GitHub Pages deploy, record PR + merge result here | claimed | arena/0e9a9550 | `COORDINATION.md`, `README.md`, generated `docs/data/picks.json` |

### Results (session `arena/0e9a9550`, 2026-10-25)

**Parallel-session note.** While this session worked, four other branches opened PRs on the same day
(#61 `arena/52743a08`, #64 `arena/970403ae`, #65 `arena/964cb944`, #66 `arena/6d169c43`), two of them on
the executive summary and the source-research log. This session kept its edits additive on `docs/**` and
`research/betting-sources.md` (new section §23, never a rewrite), wrote only new verifier rules (S18/S19) and
new files, and logged the overlap here instead of touching anything another claim names. Any merge conflict
is resolved by keeping both sides.

| Task | Status | Result |
|---|---|---|
| T25 live coverage re-verification | **done** | The 2026-10-25T10:41Z payload (156 fixtures) did **not** price `Team Lucidity Esports vs Fritt Fall` (RIVALS LEAGUE Season 2, 2026-10-31T17:30Z, fixture 1090065, <https://www.hotspawn.com/matches/team-lucidity-esports-vs-fritt-fall-rivals-league-season-2-1090065>) and carried no exclusion entry for it. Root cause: the priced set was built from the fixtures-API rows only, so a lobby-listed fixture the API lagged on was dropped silently. Independent audit on the branch run afterwards: **165 required future fixtures, 156 priced, 9 excluded for a stated reason (cancelled), 0 unexplained**, and the fixture is now priced (`MODEL_ELO_STANDINGS` 60.0%, Medium). `lobby_lol_listed: 234` equals the lobby header's own “All tiers (234)”. |
| T26 fresh source research for the non-featured matches | **done** | Five sources opened on 2026-10-25 with the exact wording recorded (OddsPortal LoL index + Prime League page, bmbets Prime League 2nd Division, Cloudbet Prime League 2nd Division, Betmonitor Prime League 2nd Division). **None** publishes a two-way price for PRM 2nd/3rd, RIVALS, Tunisian, Arabian 2nd, 4 Nations, Komplettligaen, LigaGG or LGC Rising. Written up as `research/betting-sources.md` §23.2 and published on the site with a link per row. |
| T27 phone/mobile usability pass | **done** | Six-target quick-jump bar on all 7 pages; summary reordered (picks before prose); new separate summary section “🧮 Matches without a featured betting line — how each pick is made” with the dated book check and a per-competition table; long research tables collapsed into `<details>`; 390 px typography pass for match cards. |
| T28 verifier extensions | **done** | **S18** (same jump bar on every page + the summary itself carries the non-featured section with its source table + `#nonfeatured` linked from the summary) and **S19** (phone layout contract: `width=device-width` everywhere, a breakpoint ≤430 px, no hard-coded width >430 px), both with negative self-tests (`test_verifier.py` 54/54). New `verification/test_lobby_union.py` (11 assertions) and jsdom assertions for the new section (`check_dom_render.js` 58/58). |
| T29 integration | **in progress** | see the PR/merge record below |

**Files changed:** `scripts/fetch_hotspawn.py` (union), `audit/coverage_gate.py` (new), `audit/coverage_reconcile.{json,md}` (regenerated),
`verification/test_lobby_union.py` (new), `verification/test_verifier.py`, `verification/check_dom_render.js`,
`scripts/verify_site.py` (S18/S19 + review hosts), `.github/workflows/{update-picks,pipeline-test,verify}.yml`,
`docs/index.html`, `docs/unresolved.html`, `docs/{picks,leagues,flagged,methodology,match}.html` (jump bar),
`docs/assets/{app.js,style.css}`, `research/betting-sources.md` §23, `README.md`, `docs/data/picks.json`,
`verification/report.json`, `verification/last_report.md`.

**Verification performed (branch run 40201598428, success, payload 2026-10-25T14:20:19Z):**
`verify_site.py` **47 PASS / 0 FAIL / 1 WARN** (X1: two external hosts blocked from the runner — reachability only),
S18/S19 PASS, D21 PASS (lobby upcoming 156 = priced 156, missing 0, excluded 9, leaked 0);
`audit/coverage_reconcile.py` `coverage_ok: true`, 0 unexplained; `audit/coverage_gate.py` PASS.
Local: `check_dom_contract` PASS, `test_dom_contract` 7/7, `test_verifier` 54/54, `test_entity_and_books` 17/17,
`test_standings_model` ALL PASS, `test_lobby_union` 5/5 (11 assertions), `audit/test_model` 23/23,
`render_check.cjs` PASS, `check_dom_render.js` 58/58.

**Irregularities carried forward (non-blocking, published on *Flagged for review*):**
1. **Coverage drop fixed, cause explained** — the silent-drop failure mode above; the fixtures API can lag the
   lobby. Now unioned and gated (a fixture starting >30 min out with no pick and no exclusion fails the run).
2. **No book covers the non-featured competitions** — measured again today on five sources (§23.2). The pick for
   those matches is our own line; that limitation is stated on the summary and on `unresolved.html`.
3. **Komplettligaen Playoffs lobby cards link to placeholder URLs** (`https://www.hotspawn.com/?fixtures=waiting-for-information-2208`)
   instead of a match page, so no per-match permalink exists upstream. The row keeps the fixture id and the
   Leaguepedia competition page; flagged for review rather than presented as a match page.
4. **`D18` remains a WARN** — the Leaguepedia schedule snapshot used for the cross-check is 89.5 h old
   (`data/diag`); the payload's own times are Hotspawn-authoritative and audited by D21. Not a defect in the site.


Any session that needs a file in this scope must log a request here instead of editing it.

## Session `arena/b95df72a-lolhotspawn2` — 2026-10-25 (claim; handoff from stale `arena/df8a86d2`)

The `arena/df8a86d2` claim below was made 2026-10-24 16:15 UTC with no commits on that
branch since (checked `origin/arena/df8a86d2-lolhotspawn2` is absent and `main`'s latest
commit is the scheduled refresh `2173cc9`, payload generated 2026-10-25T10:41:50Z) — older
than the 60-minute takeover rule, so this session takes over T21–T24 as T25–T28. Nothing
of that session's is discarded (it produced no commits). Baseline verified by this session:
156 fixtures · 9 market · 92 MODEL_ELO · 53 MODEL_ELO_STANDINGS · 2 MODEL_ELO_THIN ·
0 UNRESOLVED · 10 low-confidence; `scripts/verify_site.py` **44 PASS / 0 FAIL / 0 WARN / 1 SKIP**.

Defects found at baseline (verified in code, not inferred):
1. The executive summary's "Next 24 hours" section renders only 6 cards
   (`docs/assets/app.js` `.slice(0, 6)`) while its own count says 28 matches lock in 24 h,
   and the payload stores only 8 IDs (`scripts/update_picks.py` `next_24h[:8]`).
2. On a phone the first actual pick sits below the hero, a 7-chip legend, the link grid,
   the stat tiles and the coverage/reconciliation card.
3. The unresolved summary renders the per-league limitations table and the written
   limitations twice (once inside `#unresolved-summary`, once in the static
   `#exec-league-limits-body` / `#exec-limitations` blocks).

| Task | Status | Owner | Files (claimed scope) |
|---|---|---|---|
| T25 Show **every** next-24 h pick on the executive summary (no 6-card / 8-ID truncation); heading count must equal cards shown | claimed | arena/b95df72a | `docs/assets/app.js`, `scripts/update_picks.py` (next_24h lines only), `verification/check_dom_render.js` (assert count equality) |
| T26 Phone-first executive summary: starting-soon picks immediately after the hero, legend collapsed, duplicated per-league/limitations blocks rendered once; unresolved & limitations stays a separate section linked from the summary | claimed | arena/b95df72a | `docs/index.html`, `docs/assets/app.js` |
| T27 Fresh 2026-10-25 source research for low-tier/unpriced matches (established LoL betting sites → esportsbooks → betting-line aggregators → community), link-verified, appended to the research log | claimed | arena/b95df72a | `research/betting-sources.md` |
| T28 Integration: re-verify (unit suites + `verify_site.py` + jsdom DOM), live pipeline on this branch, PR → `main`, merge without waiting, confirm GitHub Pages deploy, record PR + merge here | claimed | arena/b95df72a | `COORDINATION.md`, `docs/data/picks.json` (generated) |

**Results (2026-10-25, arena/b95df72a):**
- **T25 done.** Live CI payload generated 2026-10-25T14:18:04Z on this branch: 156 fixtures ·
  9 market · 147 model (54 standings-blended) · 0 unresolved · 11 low-confidence ·
  `counts.next_24h` 27 **and** 27 stored `next_24h` IDs (previously count 28 vs 8 IDs, 6 cards
  rendered). DOM harness now asserts card-count == window size: "27 cards vs 27 in the
  next-24h window".
- **T26 done.** Summary order on a phone is now hero → starting-soon picks (all of them) →
  featured market picks → "Where the updated picks are" link grid → coverage →
  per-competition → separate Unresolved-picks-&-limitations section → sources. The method
  legend is tap-to-expand; the per-league table and written limitations render once
  (in-page anchors `#exec-per-league`, `#exec-written-limits`).
- **T27 done.** `research/betting-sources.md` §23 (renumbered twice at merge: other sessions published §20/§21/§22 the same day; §21.1 independently confirms the Cloudbet finding): Cloudbet's PRM 2nd Division board empty
  despite its pricing claim; BookMaker public lines have no LoL; Esports Insider's
  FENNEL–Nothin'Here 62/38 is their own model ("No bookmaker prices yet" on their match
  page), direction-agreeing with our thin-Elo 56.5% but not a market line; OddsPapi's own
  covered-tournament list stops at Prime League Pro Division. No new attributable structured
  source for low-tier fixtures; flagged F23.1/F23.2 (non-blocking).
- **Line-by-line verification of the fresh payload:** all 156 rows — probabilities sum to 1,
  pick = argmax, pick_prob consistent, every row has ≥1 https source; de-vig recomputed from
  stored decimals for every book on all 9 market rows (Pinnacle/Unibet/Bovada/Polymarket):
  no discrepancies. Independent cross-check against today's Esports Insider best-price board:
  TES–G2 ours 44.8% vs ESI-implied 44.9%; DK–KOI 75.8% vs 76.6%; GenG–LYON 89.6% vs 90.4%.
  `verify_site.py` 44 PASS / 0 FAIL; jsdom 55/55; render_check PASS; unit suites
  (dom-contract 7/7, verifier 45/45, standings, entity/books 17/17, model audit 23/23) PASS;
  CI-committed `verification/report.json` PASS and Leaguepedia source-page existence PASS.
- **T28:** PR + merge + Pages confirmation recorded below in this entry once executed.

**Merge reconciliation (2026-10-25):** while this branch was in flight, sessions
`arena/6d169c43` (PR #66), `arena/f931cee9` (PR #62) and `arena/7dbe0fbd` (PRs #60/#63)
merged to `main`, including the same legend-collapse idea and a same-day research §20.
Merged `origin/main` into this branch: generated files (`docs/data/picks.json`, `data/diag/*`,
`verification/report.json`, `verification/last_report.md`) took main's copy pending CI
regeneration; the research log keeps both sections (6d169c43 as §20, this session renumbered
§21); the summary keeps main's legend placement inside this session's picks-first order;
their T27–T30 numbering and this session's T25–T28 coexist below. No work discarded.
Irregularity flagged for its owner (not edited here): `main` carries the `arena/85bba52b` research §22
heading twice with non-identical bodies (53 vs 47 lines) — that session should de-duplicate its own section.


## Session `arena/6d169c43-lolhotspawn2` — 2026-10-25 (active)

No other session holds an open claim younger than 60 minutes as of 2026-10-25 14:15 UTC. All prior sessions' results are merged to `main` (latest scheduled refresh `2173cc9`, payload generated 2026-10-25T10:41:50Z, 156 matches, 156 picks resolved, 9 market rows, 147 model rows, 0 unresolved). This session works strictly inside the claimed scope.

| Task | Status | Owner | Files (claimed scope) |
|---|---|---|---|
| T27 Line-by-line verification: run all unit suites, test_verifier, test_standings_model, test_dom_contract, test_entity_and_books, jsdom render harnesses, verify_site.py (REQ1–REQ12) | done | arena/6d169c43 | `verification/**`, `scripts/verify_site.py` |
| T28 Fresh source research for low-tier LoL matches (established betting sites, esportsbooks, prediction markets, and community results); document findings for 2026-10-25 | done | arena/6d169c43 | `research/betting-sources.md`, `data/**` |
| T29 Site usability & mobile experience pass: verify and polish the executive summary with in-site links to updated picks, starting-soon immediate picks, mobile layout at 375px–390px, and separate unresolved & limitations section | done | arena/6d169c43 | `docs/**`, `README.md` |
| T30 Integration, PR & merge: verify all contracts, PR → `main`, merge without waiting, confirm deployment, record evidence here | in progress | arena/6d169c43 | `COORDINATION.md` |

### Results & Verification Log (Session `arena/6d169c43` — 2026-10-25)

1. **Task T27 (Full Re-Verification Line-by-Line):**
   - Verified all 156 matches in `docs/data/picks.json` (100% resolved: 8 `MARKET_CONSENSUS`, 1 `MARKET_SINGLE`, 92 `MODEL_ELO`, 53 `MODEL_ELO_STANDINGS`, 2 `MODEL_ELO_THIN`, 0 `UNRESOLVED`, 10 `Low` confidence).
   - Every single row contains valid teams, start timestamps, picks matching team1 or team2, and two-way probabilities summing to 1.000 (±0.005).
   - Verified unit suites: `test_verifier.py` (45/45 PASS), `test_dom_contract.py` (7/7 PASS), `test_standings_model.py` (ALL PASS), `test_entity_and_books.py` (17/17 PASS), `audit/test_model.py` (23/23 PASS).
   - Verified render harnesses: `node verification/render_check.cjs` (7/7 pages executed and rendered with dark/light theme switch), `node verification/check_dom_render.js` (53/53 DOM assertions passed).
   - `python3 scripts/verify_site.py`: **44 PASS / 0 FAIL / 0 WARN / 1 SKIP** (D1–D23, S1–S15, W1–W3, and REQ1–REQ12 all PASS).

2. **Task T28 (Fresh Source Research for Low-Tier LoL Matches):**
   - Conducted comprehensive source re-evaluation across all tiers on 2026-10-25, documented in `research/betting-sources.md` §20:
     - Established sportsbooks (Pinnacle guest API, Bovada JSON, Unibet Kambi API, bet365, DraftKings): all confirm coverage is limited to tier-1 major events (Worlds 2026); no commercial sportsbooks offer lines on PRM 2nd/3rd Division, Tunisian Super League, RIVALS LEAGUE, 4 Nations, or Komplettligaen.
     - Esportsbooks & prediction markets (Polymarket Gamma API, GG.BET, Thunderpick, Rivalry, Midnite, Oddiwire/ODDIN.GG, SportsGameOdds, OddsPapi, The Odds API, Kalshi, Manifold): confirmed that Polymarket covers Worlds and select tier-2 finals (LGC Rising Playoffs), while other platforms enforce bot-blockers, require paid API subscriptions, or demand credit cards/human onboarding.
     - Community & official tournament databases (Leaguepedia Cargo API, Liquipedia MediaWiki API, Komplettligaen, RIVALS LEAGUE, Prime League): confirm that our chronological Elo + split standings model is the only rigorous, bias-free, and verifiable path to originate accurate win probabilities for all 147 non-market matches.
   - Spot-checked 12 representative fixtures across all tiers against official pages with 100% agreement.

3. **Task T29 (Site Usability & Mobile Experience Pass):**
   - Polished executive summary (`docs/index.html`): placed the 4 primary navigation cards ("All updated picks", "Next 24 hours only", "Picks by league & tier", "Unresolved & limitations") immediately below the `#picks-here` section header on mobile, moving the method chip definitions into an expandable details container.
   - Verified mobile responsive layout: 6-column bottom navigation, 60px touch heights, responsive cards on screens <760px, high-contrast pick pills, and full-width action buttons.
   - Updated `verification/flagged_items.md` with items V1, V2, and V3.

Any session that needs a file in this scope must log a request here instead of editing it.

**Second merge reconciliation (2026-10-25):** `main` advanced again (PR #70 PWA manifest/icons,
PR #73 coin-flip picks) before PR #68 merged. Merged in: generated files took main's copy
pending CI regeneration; the unresolved summary box now carries main's coin-flip count with
this session's de-duplicated per-league/limitations rendering; the summary page keeps main's
PWA head links inside the picks-first order. No work discarded.


## Session `arena/6d169c43-lolhotspawn2` — 2026-10-25 (done, merged)

No other session holds an open claim younger than 60 minutes as of 2026-10-25 14:15 UTC. All prior sessions' results are merged to `main` (latest scheduled refresh `2173cc9`, payload generated 2026-10-25T10:41:50Z, 156 matches, 156 picks resolved, 9 market rows, 147 model rows, 0 unresolved). This session works strictly inside the claimed scope.

| Task | Status | Owner | Files (claimed scope) |
|---|---|---|---|
| T27 Line-by-line verification: run all unit suites, test_verifier, test_standings_model, test_dom_contract, test_entity_and_books, jsdom render harnesses, verify_site.py (REQ1–REQ12) | done | arena/6d169c43 | `verification/**`, `scripts/verify_site.py` |
| T28 Fresh source research for low-tier LoL matches (established betting sites, esportsbooks, prediction markets, and community results); document findings for 2026-10-25 | done | arena/6d169c43 | `research/betting-sources.md`, `data/**` |
| T29 Site usability & mobile experience pass: verify and polish the executive summary with in-site links to updated picks, starting-soon immediate picks, mobile layout at 375px–390px, and separate unresolved & limitations section | done | arena/6d169c43 | `docs/**`, `README.md` |
| T30 Integration, PR & merge: verify all contracts, PR → `main`, merge without waiting, confirm deployment, record evidence here | done | arena/6d169c43 | `COORDINATION.md` |

### Results & Verification Log (Session `arena/6d169c43` — 2026-10-25)

1. **Task T27 (Full Re-Verification Line-by-Line):**
   - Verified all 156 matches in `docs/data/picks.json` (100% resolved: 8 `MARKET_CONSENSUS`, 1 `MARKET_SINGLE`, 92 `MODEL_ELO`, 53 `MODEL_ELO_STANDINGS`, 2 `MODEL_ELO_THIN`, 0 `UNRESOLVED`, 10 `Low` confidence).
   - Every single row contains valid teams, start timestamps, picks matching team1 or team2, and two-way probabilities summing to 1.000 (±0.005).
   - Verified unit suites: `test_verifier.py` (45/45 PASS), `test_dom_contract.py` (7/7 PASS), `test_standings_model.py` (ALL PASS), `test_entity_and_books.py` (17/17 PASS), `audit/test_model.py` (23/23 PASS).
   - Verified render harnesses: `node verification/render_check.cjs` (7/7 pages executed and rendered with dark/light theme switch), `node verification/check_dom_render.js` (53/53 DOM assertions passed), `node verification/test_freshness.cjs` (PASS).
   - `python3 scripts/verify_site.py`: **44 PASS / 0 FAIL / 0 WARN / 1 SKIP** (D1–D23, S1–S15, W1–W3, and REQ1–REQ12 all PASS).

2. **Task T28 (Fresh Source Research for Low-Tier LoL Matches):**
   - Conducted comprehensive source re-evaluation across all tiers on 2026-10-25, documented in `research/betting-sources.md` §20:
     - Established sportsbooks (Pinnacle guest API, Bovada JSON, Unibet Kambi API, bet365, DraftKings): all confirm coverage is limited to tier-1 major events (Worlds 2026); no commercial sportsbooks offer lines on PRM 2nd/3rd Division, Tunisian Super League, RIVALS LEAGUE, 4 Nations, or Komplettligaen.
     - Esportsbooks & prediction markets (Polymarket Gamma API, GG.BET, Thunderpick, Rivalry, Midnite, Oddiwire/ODDIN.GG, SportsGameOdds, OddsPapi, The Odds API, Kalshi, Manifold): confirmed that Polymarket covers Worlds and select tier-2 finals (LGC Rising Playoffs), while other platforms enforce bot-blockers, require paid API subscriptions, or demand credit cards/human onboarding.
     - Community & official tournament databases (Leaguepedia Cargo API, Liquipedia MediaWiki API, Komplettligaen, RIVALS LEAGUE, Prime League): confirm that our chronological Elo + split standings model is the only rigorous, bias-free, and verifiable path to originate accurate win probabilities for all 147 non-market matches.
   - Spot-checked 12 representative fixtures across all tiers against official pages with 100% agreement.

3. **Task T29 (Site Usability & Mobile Experience Pass):**
   - Polished executive summary (`docs/index.html`): placed the 4 primary navigation cards ("All updated picks", "Next 24 hours only", "Picks by league & tier", "Unresolved & limitations") immediately below the `#picks-here` section header on mobile, moving the method chip definitions into an expandable details container.
   - Verified mobile responsive layout: 6-column bottom navigation, 60px touch heights, responsive cards on screens <760px, high-contrast pick pills, and full-width action buttons.
   - Updated `verification/flagged_items.md` with items V1, V2, and V3.

4. **Task T30 (Integration, PR & Deployment):**
   - Opened PR [#66](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/66) from `arena/6d169c43-lolhotspawn2` to `main`.
   - Merged PR #66 without waiting for external approval via `gh pr merge 66 --merge` (merge commit `7a8b8d1`, 2026-10-25T14:18:04Z).
   - Confirmed GitHub Pages deployment status: `status: built` via GitHub Pages API (`https://api.github.com/repos/karagemop466-tech/LOLHOTSPAWN2/pages`).
   - Live canonical URL: https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/ (root `index.html` redirects to `docs/`).

Any session that needs a file in this scope must log a request here instead of editing it.

## Session `arena/df8a86d2-lolhotspawn2` — 2026-10-24 (done, merged)

No other session holds an open claim that is younger than 60 minutes as of 2026-10-24 16:15 UTC; all prior sessions' results are merged to `main` (latest scheduled refresh `72c9b5a`, payload generated 2026-10-24T15:28:56Z). This session works only inside the claimed scope.

| Task | Status | Owner | Files (claimed scope) |
|---|---|---|---|
| T21 Full re-verification of the current payload line-by-line: run all unit suites + `verify_site.py`, coverage reconciliation, spot-check priced rows against their cited official sources, mobile/exec-summary link audit | claimed | arena/df8a86d2 | `verification/**`, `audit/**`, `scripts/verify_site.py` (fixes only if a check is wrong) |
| T22 Fresh source research for low-tier / unpriced matches (established LoL betting sites → esportsbooks → esports betting lines → community), update the research log with link-verified results | claimed | arena/df8a86d2 | `research/betting-sources.md`, `scripts/probe_sources.py` |
| T23 Site usability pass: executive summary with in-site links to the picks list, unresolved/limitations section reachable from the summary, phone/mobile readability at 390 px | claimed | arena/df8a86d2 | `docs/**` |
| T24 Integration: run the live pipeline on this branch, re-verify, PR → `main`, merge without waiting, confirm GitHub Pages deploy, record PR + merge result here | claimed | arena/df8a86d2 | `COORDINATION.md` (board entries), `docs/data/picks.json` (generated) |

Any session that needs a file in this scope must log a request here instead of editing it.

## Session `arena/92bfcdd3-lolhotspawn2` — 2026-10-23 (done, merged)
| Task | Status | Owner | Files |
|---|---|---|---|
| T13 Standings fallback for non-market fixtures (Leaguepedia `Standings`, Bradley–Terry, `MODEL_STANDINGS`) between Elo and league-prior | done | arena/92bfcdd3 | scripts/fetch_leaguepedia.py, scripts/model.py, scripts/update_picks.py, .github/workflows/update-picks.yml, verification/test_standings_model.py |
| T14 Phone-first executive summary: starting-soon picks first, quick-jump links, per-league unresolved/limitations table; bottom-nav 5-col fix | done | arena/92bfcdd3 | docs/index.html, docs/unresolved.html, docs/picks.html, docs/methodology.html, docs/assets/app.js, docs/assets/style.css |
| T15 Fresh source research (established books → esportsbooks → community) + Actions probe of new candidates; PR + merge + Pages check | done | arena/92bfcdd3 | research/betting-sources.md, scripts/probe_sources.py, .github/workflows/pipeline-test.yml, COORDINATION.md, README.md |

Baseline at claim (main `3addc56`): 189 fixtures · 9 market · 82 MODEL_ELO · 74 MODEL_ELO_THIN · 24 MODEL_LEAGUE_PRIOR · 0 UNRESOLVED · 101 low-confidence; `scripts/verify_site.py` 31 PASS / 0 FAIL. No other session active on these files.

**Results (2026-10-23):** live branch runs 39980317947 / 39981419030 / 39982897776 all **success**. Latest payload: 188 fixtures · 9 market · 81 MODEL_ELO · 74 MODEL_ELO_THIN · **4 MODEL_STANDINGS** (PRM 3rd Div, from 167 Leaguepedia standings rows / 14 competitions) · 20 MODEL_LEAGUE_PRIOR (was 24) · 0 UNRESOLVED. `verify_site.py` **31 PASS / 0 FAIL / 0 WARN**, verifier self-tests 27/27, standings unit test 11/11, jsdom DOM checks 14/14. Probe of 13 candidate books/aggregators: no new structured per-match LoL feed usable from CI (Kalshi: no LoL series; Manifold: futures only; esportsbooks 403/404/503) — `data/diag/source_probe.json`. Flagged (non-blocking, on Flagged page + `verification/flagged_items.md` S1–S3): 20 prior-only rows whose Hotspawn names match no verifiable Leaguepedia identity; 5 competitions with no standings table; probe candidates need human verification before any adapter.
**Merge reconciliation (2026-10-23, arena/92bfcdd3):** main advanced via PRs #11–#15 (sessions bd37dbe6/cd27b02f/b252f309: lobby-authoritative fixture set — 13 cancelled fixtures excluded, verifier D21/D8d, coverage audit) while this branch was in flight. Merged `origin/main` (7d27d82) into this branch: generated files kept branch copy pending CI regeneration; style.css kept main's `minmax` nav columns; index hero actions combined; research sections kept both (main §11, this session renumbered §12). No other session's work discarded. Post-merge pipeline-test must regenerate the payload (175 lobby fixtures + standings) and pass D21/D8d before PR #16 merges.
**Second reconciliation (2026-10-23):** session `arena/0fb2d0c7` (T17–T19, PRs #18/#19) independently implemented Standings + Unibet Kambi feed + verified aliases and merged first. This branch adopted their `fetch_leaguepedia.py`/`model.py` wholesale (standings→Elo blend supersedes this session's Bradley–Terry variant, live-verified on-branch), kept this session's site work (starting-soon exec summary, per-league unresolved table, standings filter), research §12 + source probe, and rewrote `verification/test_standings_model.py` against the merged semantics (10/10 pass). No work discarded silently; formula history in `research/betting-sources.md` §12.3.
**PR & deploy record:** PR [#16](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/16) **merged** 2026-10-23T16:23:36Z (merge commit `43ebddd`). Post-merge on main: Verify 39986388519 success · Update picks 39986388688 success (fresh payload 16:24 UTC: 172 lobby fixtures, 172 priced, 9 market, 0 unresolved, 0 prior-only) · Pages builds 39986386708 + 39986551994 success, Pages status `built`. Live check 2026-10-23: executive summary renders Starting-soon picks + quick-jump links; `docs/data/picks.json` on Pages matches the 16:24 UTC payload. Site: https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/





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
| T11 Verification: link/schema/coverage checks in CI, DOM smoke test, Pages deploy confirmation | done | arena/fa3f554c | scripts/verify_site.py, .github/workflows/*.yml |
| T12 PR to main, merge, Pages deploy confirmation | done | arena/fa3f554c | COORDINATION.md |

**Session file scope:** `scripts/**`, `.github/workflows/**`, `docs/**`, `data/**`, `COORDINATION.md`, `README.md`. No other session is active; if another session claims a task, it must not edit these paths without logging a request here.

## Verification results (session `arena/fa3f554c`)

| Check | Result | Evidence |
|---|---|---|
| Live pipeline on branch | success, 208 fixtures / 208 picks / 9 external market / 0 unresolved | Actions run 39675446733, `data/diag/pipeline.log` |
| Payload + site verification | 0 errors, 0 warnings (schema v3, links, probabilities, page checks) | `data/diag/verify.json`, `scripts/verify_site.py` |
| DOM smoke test of all six pages | summary 14 cards, picks 208 rows, unresolved 111 cards, flagged 236 rows, methodology 20 rows, match detail rendered | local jsdom run against `docs/data/picks.json` |
| PR #5 (v2 pipeline + site) | **merged** (merge commit `2193f87`) | https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/5 |
| PR #6 (low-confidence wording + reason breakdown) | **merged** (merge commit `37248e3`) | https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/6 |
| Production 6h refresh on main | success, commit `15387d1`, Pages build success | Actions run 39676373846 |
| Pages deployment | success, live at https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/ | `pages build and deployment` run 39676527908 |
| Live page content | summary, picks and match pages render with data and source links | manual fetch of the deployed URLs |
| Attempted Pages source switch to `/docs` | **HTTP 403 `Resource not accessible by integration`** — canonical site path stays `/docs/`; a root `index.html` redirects there | `PUT /repos/.../pages` response |

Out-of-sample model check published on the methodology page: 30-day window, 658 matches,
log-loss **0.6266** vs 0.6931 coin-flip baseline, Brier **0.2183** vs 0.25, accuracy **64.4%**.

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

---

## Session `arena/47334762-lolhotspawn2` — verification log (T11/T12)
Board note: session `arena/fa3f554c-lolhotspawn2` has claimed T7–T10 on its own branch (verified via `git fetch` of `origin/arena/fa3f554c-lolhotspawn2`, commits da4fd55..dd43c38, actively running GitHub Actions "DIAG lab" runs 39669308258/39669571794/39669777187). That session's branch rewrites this board; versions will be reconciled (not discarded) at integration. This session does NOT touch `scripts/update_picks.py`, `scripts/diag_lab*.py`, `docs/**`, `data/**`, or `.github/workflows/update-picks.yml` — those belong to arena/fa3f554c (T7–T10).

| Task | Status | Owner | Files (exclusive scope) |
|---|---|---|---|
| T11 Verification harness: schema check (pick on every match, probs sum to 1, method enum, per-row source links), site link check (no broken internal links, mobile viewport on every page), exec-summary-links-to-picks check, unresolved-section-present check, workflow cadence (4–8h) check | in progress | arena/47334762 | scripts/verify_site.py, verification/**, research/** |
| T12 Final integration: merge task branches after T7–T10 done, re-verify combined data line by line with scripts/verify_site.py, PR to main, merge without waiting for approval, confirm GitHub Pages deploy, record PR link + merge result here | **handoff** | arena/47334762 → arena/fa3f554c | COORDINATION.md (board entries only) |

**Handoff note (21:04 UTC):** `arena/fa3f554c` has marked T7–T10 **done** and taken T11/T12 on its own board. To avoid two
simultaneous merges, this session yields T12's *PR/merge* step to them and will instead do the **post-merge
verification** and land the verification harness + production fixes (`scripts/verify_site.py`, `verification/**`,
`research/**`, `apply_fixes.py`) in a follow-up PR. Their v2 branch was verified here at commit 8ce6591:
**28 PASS / 1 FAIL** — the only failure is `D16` (a Game-3 Polymarket market used as the Galions–Solary series price);
fix ready in `verification/apply_fixes.py` (all `Game N`/`Map N` patterns + unknown `best_of` is not BO1).

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

### Irregularities found by T11 verification on the live data (2026-10-21, commit 9f8dccb)
- **I1 (FAIL, D16): single-game market used as a series probability.** `Galions vs Solary` (EM 2026 Summer Main
  Event) is priced from Polymarket *"LoL: Galions vs Solary - Game 1 Winner"* and that game-1 price is published as the
  series probability. Game 1 ≠ series in a BO3/BO5; the row must either use a series-winner market or be converted with
  a series model (and labelled as such). Source: https://polymarket.com/event/lol-gal-sly-2026-10-22 (row in live
  `docs/data/picks.json`). → **R5 to T9 owner.**
- **I2 (WARN, D17): 126 unresolved rows cite the generic Leaguepedia main page** as `source_url`
  (`https://lol.fandom.com/wiki/Leaguepedia:League_of_Legends_Esports_Wiki`), which is not evidence for that fixture.
  Replace with the league results page where one exists (`research/betting-sources.md` §3) or leave the link out and
  mark "no source found" — per the brief, unconfirmed values must be blank + flagged, not dressed with a generic link.
  → **R6 to T9 owner.**
- **I3 (WARN, D7b): 61 model rows cite the Cargo API help page as `source_url`** (same root cause as R2 above).

- **I4 (decisive, 2026-10-21 20:31 UTC): the 126 "unresolved" rows are all resolvable to a verified source page.**
  Audit `verification/leaguepedia_coverage.py` against the Leaguepedia MatchSchedule snapshot (288 future rows,
  16 league pages, captured by arena/fa3f554c in `data/diag/lp_schedule.json`):
  **112/126 unresolved rows have the exact fixture listed on a Leaguepedia league page; 14/126 have the league page;
  0 have no source.** Per-league pages: PRM 3rd `Prime_League_3rd_Division/2027_Season/Fall_Split` (47/52 exact),
  RIVALS S2 (18/18), 4 Nations Halloween Heist (15/18), Tunisian Super League (16/16), PRM 2nd (5/8),
  Komplettligaen (4/6), LigaGG CELOL B (3/4), Arabian League 2nd (2/2), Arabian Regional Qualifiers (1/1),
  LGC Rising (1/1). Full table: `verification/leaguepedia_coverage.md`.
  → **R7 to T9/T10 owner:** use MatchSchedule to (a) set `source_url` = the Leaguepedia league page for every row,
  (b) bridge team names and build the standings/results model. The current evidence string
  "No external market and no Leaguepedia team history found" is **false** for these rows and must not ship.

- **I5 (caveat, not our error): Polymarket `gameStartTime` is stale.** For G2 vs Dplus KIA the market says 20:00 UTC
  while Leaguepedia MatchSchedule and our row both say 21:00 UTC; for Team Liquid vs CFO the market says 18:00 UTC vs
  Leaguepedia/ours 22:00 UTC. Gen.G vs IG agrees (17:00 UTC). **Our times are the correct ones** (172/172 matched
  fixtures agree with Leaguepedia, verifier D18). Do not use market start times for scheduling or lock times.
- **I6 (WARN, D2b): `start_raw="Oct 24, 24:00"` fails to parse** → `start_utc` empty for Team Secret Whales vs LYON,
  which sorts last and cannot be shown with a lock time. Fix: normalise `24:00` to next-day `00:00` (true start is
  2026-10-24 00:00 UTC per Leaguepedia MatchSchedule).
- **I7 (verified good):** the published Polymarket prices for the BO1 Worlds matches match the market exactly
  (Gen.G 0.775/0.225; TL 0.715/0.285; G2 0.395/0.605 — Gamma API, 2026-10-21 20:33 UTC). The Galions–Solary BO5
  series market (slug `lol-gal-sly-2026-10-22`, `groupItemTitle: Match Winner`) also shows 0.515/0.485 today, i.e. the
  published number is coincidentally right but the selector picked the **Game 1** child market — a latent bug. → R5.

- **I8 (quality, measured): the model is starved — 187/195 rows are coin-flips.** All 61 MODEL_ELO rows fall between
  0.455 and 0.545 (median 0.511, every row "Low — thin team history", 0–9 games per team), plus 126 explicit 50/50s.
  Only the 8 market rows carry information. Root cause: the global 6,000-row `ScoreboardGames` pagination is crowded
  out by major leagues, and a 180-day window misses prior splits. **Fix (R9): 16 targeted per-league Cargo queries**
  (one per `MatchSchedule.OverviewPage` in the fixture list, paced ≥3 s), using MatchSchedule for fixtures/names and
  2 splits of league results for ratings; expose `leaguepedia_ok`, `leagues_queried`, `teams_with_results`,
  `games_used` in the payload. Details + exact query template: `research/betting-sources.md` §7.

- **I9 (display, T10): tier "W" is shown as "Tier W" on the site for 137 rows.** "W" is the parser's artefact for
  Hotspawn's *"waiting for information"* stage, not a tier (real tiers in the feed: S/A/C/D). The new fixtures API
  exposes `tier` and `stage` separately — display "Tier: waiting for information" (or omit the tier) instead of "W".

- **R10 (compliance): do not scrape Liquipedia HTML.** Liquipedia's terms say "Automated access to non-API endpoints
  (ie, generated HTML pages) is not permitted" (https://liquipedia.net/api-terms-of-use). `scripts/diag_lab5.py` fetches
  page HTML for brackets; that is fine as a one-off diagnostic but **must not** ship in the production pipeline. Use the
  MediaWiki API (`liquipedia.net/leagueoflegends/api.php`) only, with gzip, ≤1 req/2 s, a contact UA, and CC-BY-SA 3.0
  attribution on the Method & Sources page.
- **R11 (standings data, verified fields):** the Cargo `Standings` table exists (`action=cargotables`) with fields
  `OverviewPage, Team, PageAndTeam, N, Place, WinSeries, LossSeries, TieSeries, WinGames, LossGames, Points,
  PointsTiebreaker, Streak, StreakDirection` (`action=cargofields&table=Standings`, checked 2026-10-21). A query using
  `Wins,Losses,WinLoss` will error; the PRM 2nd page is `Prime League 2nd Division/2027 Season/Fall Split`, **not** the
  Hotspawn title. Ready-to-use model + script: `verification/standings_line.py` (smoothed series win-rate,
  Bradley-Terry; tested: 5-1 vs 1-5 → 70%, 3-0 vs 3-0 → 50%). Use standings where Leaguepedia has no ScoreboardGames
  for the current amateur season (RIVALS S2, PRM 3rd, etc.) instead of publishing 50/50.

- **R12 (validated fix, real data): standings model scores 18/18 RIVALS fixtures.** Using the live Cargo `Standings`
  rows for `RIVALS LEAGUE/2026 Season/Season 2` (16 teams, WinSeries/LossSeries) with `verification/standings_line.py`,
  every RIVALS fixture gets a sourced probability and 14/18 move off 50/50 (e.g. Mazepa 0-4 vs B2U 4-0 → 25.0%;
  Karolinerna 1-4 vs Turbo Gaming 4-1 → 33.3%; DMG 3-2 vs FlameHard 5-0 → 41.7%). PRM 3rd Division standings
  (32 teams) were also confirmed live, so the same treatment applies to its 52 fixtures. This is the evidence-based way
  to "resolve picks for matches we don't have picks for" without inventing numbers.

- **R13 (integration-ready, validated): with only 3 leagues' standings, 48 rows become sourced picks.** Running
  `verification/apply_standings.py` on the live payload with the verified RIVALS S2 + Komplettligaen + Tunisian
  standings produces 48 `MODEL_STANDINGS` rows (UNRESOLVED 126 → 87), each with the Leaguepedia league page as
  `source_url`, the exact series records in the evidence, and an honest confidence band. PRM 3rd (32 teams),
  PRM 2nd and 4 Nations standings were also confirmed live; applying those should leave only a handful of truly
  unresolvable rows. Division ambiguity (4 Nations duplicates) and 0-0 teams are explicitly not scored.

- **R14 (coordination channel): GitHub issue #4 opened** for the T7–T10 owner with the verified Standings field list,
  the six league pages that have standings, the validated 48-row result, and the measured site reachability:
  https://github.com/karagemop466-tech/LOLHOTSPAWN2/issues/4 . Also recorded: `primeleague.gg` returns **403 Bunny
  Shield** from Actions and `4nations.gg`/`ligagg.com`/`tunisian*`/`lol.tn` are unreachable — organizer scraping is not a
  viable production path; Leaguepedia Cargo is.

- **P10/P11 (reliability):** the update workflow swallows git failures (`|| true`) and its inline check covers only two
  invariants. Integration adds `scripts/verify_site.py` to CI and removes the silent-failure paths.

- **I10 (FAIL, must fix before merge): the new Polymarket selector still admits single-game markets.** In
  `scripts/fetch_markets.py` (commit f203d1f) the acceptance test is
  `if "game 1" not in q and "game 2" not in q and "winner" in q or "vs" in q:` — Python binds this as
  `(… and … and …) or ("vs" in q)`, and virtually every market question contains the team pair ("… vs …"), so the
  **Game 1/2/3/4/5 child market is accepted first** and `break`s. Polymarket exposes `groupItemTitle`
  ("Match Winner" vs "Game 1 Winner") and a series market slug (event slug without `-gameN`): select
  `groupItemTitle == "Match Winner"` (or the event market whose question has no `game N`/`map N`), exclude
  `game \d+`/`map \d+` for non-BO1, and only fall back to a single-game price if the fixture is BO1.
  Verifier D16 gates this.

- **I11 (blocking bug, observed in their pipeline run 39673881867):** `scripts/model.py:158` crashes with
  `TypeError: '<' not supported between instances of 'int' and 'str'` because `sorted(set(n for n in names if n))`
  mixes int and str team names from the Leaguepedia teams payload. Fix: `sorted({str(n) for n in names if n})`
  (and `norm()` already stringifies). The run fetched 32,686 Leaguepedia rows and 9 market records per source before
  crashing, so the data layer works.
- **I12 (coverage question):** their new lobby parser reports **195 future fixtures**, while the backend fixtures feed
  advertised **208 future LoL fixtures** in the earlier probe. Decide and document which set is "every match listed on
  Hotspawn": the lobby (`play.hotspawn.com`) shows 195 pick'em cards; the feed has 208 including non-lobby rows.
  `D19` will compare whatever count the payload exposes.
- **P13 (repo hygiene):** the test workflow commits `data/cache/leaguepedia.json` (8.3 MB) on every run. Gitignore
  `data/cache/**` (or use actions/cache) and commit only `data/picks.json` + `docs/data/picks.json`.

### T11 status (this session)
`scripts/verify_site.py` written: 29 rule groups covering data schema, per-row source links, mobile viewport, in-site
exec-summary links, separate unresolved section, internal-link integrity, 4-8h cron cadence, and a static scan that
Hotspawn crowd % never feeds a probability. Baseline on current main: **26 PASS · 2 WARN · 0 FAIL**
(WARN: 61 model rows cite an API help page; 64.6% of rows still unresolved). Reports in `verification/`.


## Post-merge verification — session `arena/47334762` (T11 done, T12 in progress)

`arena/fa3f554c` merged PR #5 (v2 pipeline + 6-page site) at 2026-10-21T21:03:55Z; the 6-hour workflow refreshed the
payload on `main` (208 fixtures, 9 market, 199 model, 0 unresolved). This session then merged `main`, applied the two
verified production fixes and re-ran the full suite.

**Result on the merged branch (208 fixtures, generated 21:07 UTC):**
`python3 scripts/verify_site.py --leaguepedia-schedule data/diag` → **31 PASS · 0 FAIL · 1 WARN**
— the WARN is `D18`: 4 fixtures have different Hotspawn vs Leaguepedia start times (P14, flagged; Hotspawn governs
pick locks). `verification/test_verifier.py` 27/27 · DOM contract PASS ·
coverage audit: 153 exact Leaguepedia fixtures / 26 league-page-only / 15 claimed page / **5 rows with no page**
(4 Arabian League 2nd, 1 LigaGG — all ~50% priors, Low confidence).

**Fixes applied here (verified end-to-end by the branch pipeline run 39676044544, success):**
- `fetch_markets.py`: every `Game N`/`Map N` market is detected, not just game 1/2/map 1.
- `model.py`: a game-level market is only allowed when the fixture is **known BO1** (unknown `best_of` is not BO1).
  After the fix, Galions–Solary uses the BO5 series market (Pinnacle 53.4 / Bovada 50.0 / Polymarket 55.5 → 53.4).
- `scripts/verify_site.py` kept as the single verifier (superset of the 142-line version; its `match.html`,
  confidence-label and URL checks are preserved).
- `.github/workflows/verify.yml` added: 27 self-tests + 31 checks + external-link and live-Pages checks every 6 h.

**T12 remaining:** open the verification follow-up PR to `main`, merge it, confirm the Pages deploy and record the PR
link + build id here and in `verification/FINAL_REPORT.md` §8.

## Reconciliation — v2 payload vs the T11 findings (session `arena/fa3f554c`, 21:20 UTC)

The T11 log above was written against commit `9f8dccb` (v1 data). The v2 pipeline that followed changes the
picture; each item is resolved or explicitly dispositioned below.

| Finding | Status on v2 | Evidence |
|---|---|---|
| I1 single-game market used as a series price | **fixed** — selector prefers the event/series market (`groupItemTitle` + `question`), tags every Game-N/Map-N market, and the model refuses a game market unless `best_of == 1` | `scripts/fetch_markets.py::_select_poly_market`, `scripts/model.py`; verifier **D16 PASS**; unit test picks the BO5 series market |
| I2/I3 generic source URL on model rows | **fixed** — every model row links its per-fixture Leaguepedia tournament page; the generic CargoExport table link remains only when no schedule row matched (and the row is Low confidence) | payload `leaguepedia_url`, `sources[]`; verifier D7/D8 PASS |
| I4 126 unresolved rows resolvable to Leaguepedia pages | **obsolete** — v2 resolves all 208 fixtures (0 unresolved); the same MatchSchedule rows power the Elo ratings | `docs/data/picks.json` counts; `data/diag/verify.json` |
| I8 model starved / 187 coin-flips | **obsolete** — league-anchored Elo: 92 `MODEL_ELO`, 72 `MODEL_ELO_THIN`, 35 `MODEL_LEAGUE_PRIOR`, 9 market rows; 30-day backtest log-loss 0.6266 vs 0.6931, Brier 0.2183 vs 0.25, accuracy 64.4% | `model.backtest` in the payload; methodology page |
| I11 int/str crash in Resolver | **fixed** — all Leaguepedia names are string-coerced before sorting | `scripts/model.py`; live runs green |
| I12 195 vs 208 fixture count | **resolved** — API fixtures (208) merged with lobby permalinks (195); the 13 without a match page are published and flagged `NO_HOTSPAWN_MATCH_PAGE` | `scripts/fetch_hotspawn.py`, `counts.hotspawn_without_match_page` |
| P13 8.3 MB cache committed every run | **fixed** — `data/cache/` is git-ignored; only `docs/data/picks.json` + the pipeline log are committed | `.gitignore`, `.github/workflows/update-picks.yml` |
| I5/I6 market or ambiguous start times | **handled** — Hotspawn epoch-ms is authoritative, bookmaker deltas are stored and flagged above 1.5 h, D18 checks Leaguepedia | `START_TIME_DISAGREES_WITH_BOOKS`, D18 WARN (4 fixtures, flagged) |
| R1–R7 | superseded by v2 (league-anchored Elo + per-fixture sources); no 50/50 fallback remains except a genuinely unknown fixture, which would be `UNRESOLVED` | payload + verifier |

**Verification after merging the harness (PR #7) into this branch:**
`scripts/verify_site.py --leaguepedia-schedule data/diag` → **31 PASS · 0 FAIL · 1 WARN** (D18 start-time deltas),
`verification/test_verifier.py` 27/27, `verification/check_dom_contract.py` PASS, jsdom smoke test on all six pages.

**Integration PR for this follow-up:** #8 — **merged** (merge commit `d8b848c`, 21:22 UTC).

**Post-merge state (main):**
- `verify.yml` run **39677101080 → success** on the merge commit (27 self-tests + 31 checks).
- production refresh `28d9755` (208 fixtures, 9 market, 199 model, 0 unresolved) → Pages build **39677401560 success**.
- live site re-checked: summary and picks render; Galions–Solary now uses the BO5 **series** market (Pinnacle 53.4 / Polymarket 55.5), not a Game-3 price.
- parallel session PR #9 (`ci: keep the bot's fresh payload on rebase conflicts`) merged on top; no conflict with this branch.

## Session `arena/cd27b02f-lolhotspawn2` — 2026-10-23 (final integration record)

Branch `arena/cd27b02f-lolhotspawn2` == `main` == `origin/main` (commit 3addc56e6c58de9407d6f6d301cc8f0e3e075be5) at session start; all T1–T12 work from prior sessions is integrated and live. This session re-verified the combined state end to end and refreshed the verification artifacts (commit 39c36ff).

### Verification performed this session

| Check | Result | Evidence |
|---|---|---|
| `scripts/verify_site.py --leaguepedia-schedule data/diag` | 31 PASS · 0 FAIL · 1 WARN | WARN = D18: 10 of 137 matched fixtures have Hotspawn vs Leaguepedia start-time deltas (Hotspawn authoritative for pick locks; all flagged per-row), 52 fixtures absent from the amateur-league snapshot |
| `verification/test_verifier.py` | 27/27 pass | verifier self-tests (each rule fails on bad data) |
| `verification/check_dom_contract.py` | PASS | all JS-referenced ids exist on the six pages |
| Published payload `docs/data/picks.json` | 189 fixtures, 100% resolved | 9 market-consensus rows (Pinnacle/Bovada/Polymarket), 180 model rows (82 MODEL_ELO, 74 MODEL_ELO_THIN, 24 MODEL_LEAGUE_PRIOR), 0 UNRESOLVED, 13 fixtures without a Hotspawn match page flagged `NO_HOTSPAWN_MATCH_PAGE` |
| GitHub Pages | built, live | https://karagemop466-tech.github.io/LOLHOTSPAWN2/ (source: main, path /; root index.html redirects to /docs/) |
| "Verify picks and site" workflow on main | success every 6h | latest run 39949842068 (2026-10-23 11:58 UTC) |

### Requirements traceability (all PASS)

REQ1 pick for every match · REQ2 probabilities sum to 1 · REQ3 no Hotspawn probability input · REQ4 external lines where they exist · REQ5 documented method for every non-market match · REQ6 separate unresolved section with limitations linked from exec summary · REQ7 exec summary links to picks · REQ8 official/trusted source link on every row · REQ9 mobile-friendly · REQ10 automatic 4–8h refresh, no manual input · REQ11 no broken internal links, root entry works · REQ12 third-party attribution.

### Irregularities / flagged items (non-blocking; published on Flagged for Review page)

- D18: amateur-league fixtures (Komplettligaen, RIVALS, PRM, etc.) where Leaguepedia's recorded schedule disagrees with Hotspawn or lacks the row; Hotspawn epoch-ms governs pick lock times, per-row flags attached.
- 13 fixtures have no published Hotspawn match page; listed as `fixtures_without_page` and flagged `NO_HOTSPAWN_MATCH_PAGE` rather than linked to a 404.
- No bookmaker prices tier-3/amateur leagues; those rows are priced by the league-anchored Elo model from Leaguepedia results, labelled Low confidence where history is thin.
- Pinnacle consumed via the public guest front-end feed (unofficial); Bovada returned degraded on some runs, consensus falls back to healthy sources; source status published per run.

### Sources used (official / verified)

- Hotspawn fixtures API + Pick'em lobby (fixture list only, never a probability): https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures, https://play.hotspawn.com/lol-pickems
- Pinnacle guest JSON (two-way moneyline): https://guest.api.arcadia.pinnacle.com/0.1 (site: https://www.pinnacle.com/en/esports/league-of-legends)
- Bovada coupon JSON (two-way moneyline): https://www.bovada.lv/services/sports/event/coupon/events/.../esports/league-of-legends (site: https://www.bovada.lv/sports/esports/league-of-legends)
- Polymarket Gamma API (match/series prices): https://gamma-api.polymarket.com/events?tag_slug=league-of-legends&active=true&closed=false (site: https://polymarket.com)
- Leaguepedia Cargo MatchSchedule + Teams (results, schedule, canonical names): https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule
- Provider availability checks (403/401/404/503 → not used): documented in scripts/update_picks.py CHECKED_UNAVAILABLE and research/betting-sources.md.

### Integration result

Pull request #11 (`arena/cd27b02f-lolhotspawn2` → `main`) merged without waiting for approval.

| Item | Value |
|---|---|
| PR number | 11 |
| PR URL | https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/11 |
| Merge commit | 6feaaecd39cd646a42ce1abbd96453dde22f187e |
| Pages build/run | "pages build and deployment" run 39981417237 — **success** (2026-10-23T15:48 UTC) |
| Pages status | **built** — live at https://karagemop466-tech.github.io/LOLHOTSPAWN2/ |
| Post-merge verification | "Verify picks and site" run 39981419222 — **success** on main |
| Production refresh | "Update Hotspawn LoL picks (every 6h)" re-ran on the main push (automation confirmed live) |

This session (arena/cd27b02f-lolhotspawn2) is complete: repo reviewed line by line, every table row carries an official/trusted source link or is flagged unverified, the executive summary links in-site to the picks list and the unresolved section with limitations, the site is mobile-friendly and live, picks cover 100% of Hotspawn's listed LoL fixtures (189/189, 0 unresolved), and the pipeline refreshes automatically every 6 hours with no manual input. Remaining COORDINATION.md commit for this session (this integration record) is a one-commit follow-up PR from this branch to main.
- Bovada returned HTTP 200 without an event list on the 21:16 run (`status: error`, count 0) while Pinnacle/Polymarket stayed ok; the source status is published as degraded and the consensus fell back to the two healthy sources. A follow-up hardens the feed parser with alternate coupon URLs.

---

## Session `arena/e76bc0ae-lolhotspawn2` — 2026-10-23 (claim)

Two sessions hold live claims on `main` (bd37dbe6: T13/T14/T15, bdecdf49: T13 full-scope). To avoid duplicate
work and conflicts this session claims **only files not owned by either claim** and logs requests for the rest.

| Task | Status | Owner | Files (claimed scope) |
|---|---|---|---|
| T17 External-line integrity + coverage: de-duplicate repeated bookmaker matchups so one book is never counted as several sources; exclude prop markets; add an auditable probe of additional established/esports books for the low-tier fixtures | in progress | arena/e76bc0ae | `scripts/fetch_markets.py`, `scripts/model.py`, `audit/**`, `.github/workflows/audit-sources.yml` (new file only) |
| T18 Own-line resolution for matches without a book line: blend the current-season series record (Leaguepedia `Standings`) with Elo for thin-history rows, with the league page as the per-row source; publish limitations | in progress | arena/e76bc0ae | `scripts/model.py`, `scripts/fetch_leaguepedia.py`, `audit/**` |

**Not touched by this session:** `scripts/fetch_hotspawn.py`, `scripts/update_picks.py` (bd37dbe6 T13);
`docs/**`, `research/**`, `verification/**`, `README.md` (bd37dbe6 T14/T15, bdecdf49). Requests for those files are
logged below instead of edited. If a claim goes stale (>60 min without a commit) this session takes over the
remaining integration and records the handoff.

**Requests logged (not implemented here):**
- **Q1 → docs owner:** the All-picks table should show `market.source_count` as *distinct books*, not raw records;
  after T17 the payload field `sources` will be de-duplicated and `source_count` will equal the number of distinct
  books. No page change is required if the page renders that field verbatim.
- **Q2 → docs owner:** add a "Picks for matches without a book line" row to the executive summary that links to
  `unresolved.html`, and state that model-only rows are our own line, not a book price.

**Evidence for the integrity defect (T17):** `docs/data/picks.json` at `3addc56`, e.g. Gen.G–Invictus Gaming has
9 `Pinnacle` records with ids 1638918251/1638918161/1638748200/1638918344/1638918267/1638918312/1638918285 plus
Bovada 32451771 and Polymarket. The 7 Pinnacle entries carry the identical 0.764 price and are reported as
`source_count: 9`, `dispersion 0.011` → `High` confidence. They are the same book repeating one market across
several Pinnacle league boards, not nine independent lines.

## Session `arena/bd37dbe6-lolhotspawn2` — 2026-10-23 (claim)

No other session holds an open claim on `main` as of 2026-10-23 15:35 UTC (prior sessions are merged; `origin` has only `main`). This session claims the following scope and works only inside it.

| Task | Status | Owner | Files (claimed scope) |
|---|---|---|---|
| T13 Coverage audit: reconcile the Hotspawn lobby tier-filter count with the pipeline fixture count and the fixtures API; close any gap | done | arena/bd37dbe6 | scripts/fetch_hotspawn.py, scripts/update_picks.py, scripts/diag_coverage.py, data/diag/** |
| T14 Executive summary, unresolved section and per-league limitations; in-site links to picks; mobile readability pass | done | arena/bd37dbe6 | docs/** (pages + assets) |
| T15 Betting-line and community-source refresh with link-verified research log | done | arena/bd37dbe6 | research/betting-sources.md, scripts/verify_site.py (D21, S10 only) |
| T16 Integration: rerun live pipeline on branch, re-verify line by line, PR to `main`, merge, confirm Pages deploy, record result here | pending | arena/bd37dbe6 | COORDINATION.md (board entries), docs/data/picks.json (generated) |

Any session that needs a file in this scope must log a request here instead of editing it.

## Session `arena/bdecdf49-lolhotspawn2` — 2026-10-23 (current)

| Task | Status | Owner | Files (exclusive scope) |
|---|---|---|---|
| T18 Workflow reliability: make the branch pipeline artifact commit/rebase/push fail loudly and safely, without touching other sessions' claimed site/data scopes | in progress | arena/bdecdf49 | `.github/workflows/pipeline-test.yml`, `COORDINATION.md` |

**Scope note:** This session uses Arena's fixed branch `arena/bdecdf49-lolhotspawn2`; branch creation/switching is not permitted in this workspace. After checking the newly active claims on `arena/bd37dbe6` (T13–T16) and `arena/e76bc0ae` (T17–T18), this claim is narrowed to `.github/workflows/pipeline-test.yml` only. No files in their scopes are edited. This is not the final integration claim; the active board owners retain the site, source/model and fixture scopes.


**Requests / findings logged for active owners (not implemented in this session):**
- **Q7 → `arena/bd37dbe6` (T13/T14/T15):** Live Hotspawn lobby page fetch on 2026-10-23 showed the filters `All tiers (241)` and `This week 139 matches`; the checked-in payload generated 2026-10-23 11:00 UTC has 189 rows, of which 176 are `scheduled` and 13 `cancelled`, all 13 without a Hotspawn match-page URL. Please reconcile the count against the live lobby/feed and separate cancelled feed records from active pick'em fixtures (keep them visible as flagged/no-pick rather than silently treating them as active). Source: https://play.hotspawn.com/lol-pickems .
- **Q8 → `arena/bd37dbe6` (T14):** CSS currently defines `.bottom-nav { grid-template-columns: repeat(4, 1fr) }`, while every page has five bottom-nav links (Summary, Picks, Unresolved, Flagged, Method). Please make the mobile nav fit all five items and add a regression check. Files are within your claimed `docs/**` / `verification/**` scope; I have not edited them.
- **Q9 → `arena/bd37dbe6` / `arena/e76bc0ae`:** `update_picks.py` labels OddsPapi as “Adapter retained but disabled,” but `scripts/fetch_markets.py` on `main` has no OddsPapi adapter. Provider docs say API requests require a key (https://oddspapi.io/us/docs); no key is configured here. Please correct the wording or implement an optional, key-gated adapter, and do not describe unconfigured odds as checked lines.
- **Q10 → `arena/bd37dbe6` (T15):** Polymarket's official homepage currently states that trading is blocked in the US and provides a view-only option; please note this US-access limitation alongside the Gamma API source if retaining it as a market input. Source: https://polymarket.com/ .

---

## Session `arena/e76bc0ae-lolhotspawn2` — T17/T18 results (2026-10-23 16:15 UTC)

**Status: T17 done · T18 done · T19 integration in progress.** Branches `arena/bd37dbe6-lolhotspawn2` and
`arena/bdecdf49-lolhotspawn2` were merged into this branch (only `COORDINATION.md` conflicted; both blocks kept).
No work from any session was discarded.

| Task | Status | Evidence |
|---|---|---|
| T17 one book counts once; prop boards excluded; extra book probe | **done** | `scripts/fetch_markets.py` (`dedupe_records`, `is_prop_name`), `scripts/model.py` (one record per `source_key`), `audit/probe_sources.py`, `audit/source_probe.{json,md}` |
| T18 standings line for matches the Elo cannot rate | **done** | `scripts/fetch_leaguepedia.py` (`fetch_standings`, bounded to current pages), `scripts/model.py` (`MODEL_STANDINGS`), `audit/test_model.py` |
| T19 integration + PR + Pages confirmation | in progress | this branch |

### Verification performed (strict run 39984642591, commit `509b262`, payload generated 2026-10-23T16:12:46Z)

Runner: `.github/workflows/audit-pipeline.yml` — `set -euo pipefail`, offline tests, live pipeline, `verify_site.py`,
coverage reconciliation. Summary published as a commit comment (artifact storage is not reachable from the sandbox).

| Check | Result |
|---|---|
| Offline regression tests (`audit/test_model.py`) | 6/6 pass (de-duplication, prop rejection, standings, market precedence, prior fallback, unresolved) |
| `scripts/verify_site.py` | PASS (run step 4, which includes the verifier) |
| Fixtures required (lobby ∩ API, upcoming) | **184** |
| Priced with a pick | **172** |
| Documented exclusions | **12 — every one is `Hotspawn status is 'cancelled'`** |
| Unexplained gaps | **0** (`coverage_ok: true`) |
| Methods | MARKET_CONSENSUS 8 · MARKET_SINGLE 1 · MODEL_ELO 77 · MODEL_ELO_THIN 70 · MODEL_STANDINGS 4 · MODEL_LEAGUE_PRIOR 12 · UNRESOLVED 0 |
| Low-confidence rows | 89 (was 101 before T17/T18; the fixture window also moved) |
| Market source counts after de-duplication | 8 rows with **3 books / 3 rows each** (Pinnacle + Bovada + Polymarket), 1 Polymarket-only row. Before T17: `source_count: 9` with seven identical Pinnacle rows. |
| Standings rows | 4, all sourced to https://lol.fandom.com/wiki/Prime_League_3rd_Division/2027_Season/Fall_Split (p between 0.479 and 0.517 because the records are 1–1/0–0 and the sample-size shrink is applied) |

Excluded (cancelled) fixture ids, all confirmed by the pipeline's own exclusion record:
1074653, 1074656, 1074661, 1079026, 1079035, 1079044, 1079052, 1079061, 1079140, 1079143, 1079148, 1082258.

### External sources tried for the matches without a book line

`audit/source_probe.md` (36 endpoints, 2026-10-23T15:47:57Z, read-only). **No reachable book names any of our
low-tier leagues** (Prime League, Tunisian Super League, RIVALS LEAGUE, Arabian League, Komplettligaen, LigaGG,
Icelandic, Benelux, 4 Nations, Superstrike, Hitpoint). Observed: DraftKings 404 (was 200 on the first probe —
bot-detection varies), FanDuel 200 but no LoL/teams, Betano 200 generic landing page, Betsson 202, Marathonbet 403,
Unibet 503, BetMGM 403, Betway 404, 1xBet 203, BetOnline 200 no LoL, BetUS 403, Rivalry 503, Thunderpick 403,
GG.Bet 403, Midnite 200 shell, LOOT.BET no response, EsportsBet.io 404, Betify 403, Oddspedia 410, Oddspedia API 404,
BetExplorer 404, OddsPortal 200 with 1 current team, The Odds API 401, Kalshi no LoL, PandaScore 403, Abios no
response. Only Polymarket (12 current teams) and Manifold (futures only) are machine-usable; neither prices the
uncovered leagues. This confirms the 50/50/prior limitation is a market-coverage fact, not a pipeline defect.

### Irregularities logged

- **I13 (fixed):** Pinnacle listed each Worlds match on up to 7 boards with distinct matchup ids and an identical
  price; the consensus counted them as independent sources (`source_count: 9`, dispersion 0.011 → High). Rows are now
  de-duplicated per book + team pair + start hour and the per-source rows are kept in `market.sources`.
- **I14 (fixed):** Pinnacle derivative boards (`X (Kills)`) were entering `market_unmatched`; they are now rejected by
  `is_prop_name()` and never reach the matcher.
- **I15 (open, documented):** `sources_status` in the payload does not expose `raw_count` / `duplicates_collapsed`
  (they exist in `data/cache/markets.json`). Surfacing them needs `scripts/update_picks.py`, owned by bd37dbe6 — request
  to that owner (or the integration session) to copy the two fields.
- **I16 (open, documented):** 12 fixtures still use `MODEL_LEAGUE_PRIOR` (one side has no recorded series) and 70 use
  `MODEL_ELO_THIN`; the standings table does not include those teams with a decided record. Published as Low confidence
  on the Unresolved page — not hidden.
- **I17:** Nine parallel sessions ran pipelines against Leaguepedia simultaneously at 15:42–16:00 UTC; one strict run took
  25 minutes and two were cancelled. `fetch_standings` is now capped (24 pages, 120 s budget, 25 s timeout, 1 retry) so a
  slow wiki can never block the refresh.
- **I18:** `arena/b132c242` and `arena/92bfcdd3` independently implemented `MODEL_STANDINGS`. This branch's version is the
  one merged here; their commits remain on their branches and are **not discarded**. If their implementations cover cases
  this one misses (e.g. group-stage pages), reconcile in a follow-up rather than double-merging.
- **I19:** Sandbox egress blocks `*.blob.core.windows.net`, so Actions artifacts and zip logs cannot be downloaded here.
  Verification evidence is therefore published through commit comments (`/commits/<sha>/comments`) and `audit/last_run.json`.

### Requests to other file owners
- **Q3 → docs owner:** the picks table's method chip and the `low` filter now need `MODEL_STANDINGS`; both were added to
  `docs/assets/app.js` in this integration (label “League standings”, rank 2) together with the visible “your local time”
  label and the “N book(s)” wording.
- **Q4 → update_picks.py owner:** copy `raw_count` and `duplicates_collapsed` from the market status into `sources_status`.

---

## Session `arena/bd37dbe6-lolhotspawn2` — results (2026-10-23)

Branch note: Arena fixes this session's branch as `arena/bd37dbe6-lolhotspawn2`; the `session-<id>/<task>` naming is superseded by that rule. Scope actually edited: `scripts/fetch_hotspawn.py`, `scripts/update_picks.py`, `scripts/verify_site.py` (new rules D21 and S10 only), `scripts/diag_coverage.py` (new, read-only), `docs/**`, `research/betting-sources.md` (new §11 only), `data/diag/coverage_audit.json`, `.github/workflows/diag-coverage.yml` (new), this file.

### What was wrong and what changed
| Finding | Evidence | Fix |
|---|---|---|
| The payload published picks for **13 `cancelled` fixtures** that are not in the Hotspawn lobby (the "189" count) | `data/diag/coverage_audit.json` (`ids_in_api_not_lobby` = 13, all `cancelled`, no permalink) | Pipeline prices only the **upcoming lobby fixtures** that the fixtures feed lists as `scheduled`; the 13 are kept in `excluded_fixtures` with the source link and shown on Flagged |
| Lobby header "241" vs payload "189" | Lobby: 241 LoL entries = 66 already started (locked, no link) + 175 upcoming (each has a link). API upcoming = 188 = 175 scheduled + 13 cancelled | `coverage_reconciliation` block in the payload + summary card; verifier D21 fails on any unpriced upcoming fixture or priced excluded fixture |
| Lobby header "This week 139 matches" | 64 lobby rows fall inside the lobby week window (2026-10-19 → 10-25 UTC). No definition of "139" is visible | **Unverified, flagged** (not used) |
| Phone bottom nav: 4-column grid with 5 links (Q8 from `arena/bdecdf49`) | CSS `repeat(4, 1fr)` vs 5 `<a>` | 5 columns; verifier S10 checks links = columns on every page |
| Long source URLs forced sideways scroll on Flagged and Method pages at 390 px | Headless Chromium measurement: `scrollWidth` 461 vs 390 viewport | `overflow-wrap: anywhere` on links and `.sub`; all six pages measured at 390 px |
| OddsPapi described as an "adapter retained" (Q9) | No OddsPapi code exists in `fetch_markets.py`; no key configured | Wording corrected in `CHECKED_UNAVAILABLE` and research §11 |
| Polymarket US access (Q10) | Polymarket homepage, checked 2026-10-23: "Trading is blocked in the United States on polymarket.com" | Limitation on the Method page, Unresolved page (payload `limitations`) and research §11 |
| R16 asked for rule "D20" (unique `source_key` per fixture) | My lobby reconciliation had already used D20 | My rule renamed **D21**; **D20 is reserved for R16** (not implemented here) |

### Coverage result (live pipeline run on this branch, commit 4841d24 inputs, run 39980818293 success)
- Lobby upcoming fixtures: **175** · priced: **175** · missing: **0** · priced but not in lobby: **0** · excluded (cancelled): **13**
- Methods: market consensus 8 + single market 1 · own Elo 78 · Elo (thin history) 71 · league prior (one team unrated) 17 · explicit 50/50 placeholders **0**
- Low-confidence rows: 91 (labelled on the Unresolved page with reasons)
- `scripts/verify_site.py` on the committed payload: **31 PASS · 0 FAIL · 1 WARN** (D18 start-time cross-check: 4 mismatches vs Leaguepedia, flagged per row; Hotspawn governs lock times)
- Headless Chromium at 390 px (iPhone-class viewport): all six pages fit the viewport, no JavaScript errors, 5/5 bottom-nav items visible.

### Sources (checked 2026-10-23)
- Hotspawn Pick'em lobby (fixture list, match links, state): https://play.hotspawn.com/lol-pickems
- Hotspawn fixtures API (backend used by the lobby; `status`, epoch start): https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures
- Polymarket homepage, US trading block notice: https://polymarket.com/
- Polymarket Gamma / Pinnacle guest / Bovada coupon / Leaguepedia MatchSchedule: as listed in `research/betting-sources.md` and on the Method page
- Betting-site survey (third-party claims, not used as data): https://esports.gg/guides/betting/league-of-legends-betting-sites/ · https://www.egaminghq.com/guide/lol-betting-odds-2026-guide/ · https://ibebet.com/betting/esports/league-of-legends/ · https://www.hltv.org/en-us/betting/sites/esports

### Irregularities for Flagged for Review
1. 13 cancelled fixtures were priced in the 11:00 UTC payload — fixed; now excluded and listed with source link.
2. Lobby "139 matches this week" — unverified; does not reconcile with 64 rows in the week window.
3. D18: 4 start-time differences between Hotspawn and Leaguepedia (flagged per row).
4. Polymarket trading is blocked for US users on polymarket.com; its prices are reference data only.

### Requests / replies to other sessions
- **Q7 (`arena/bdecdf49`) and R15 (`arena/0fb2d0c7`):** done — cancelled fixtures excluded and listed; count reconciled (see table above).
- **Q8 (`arena/bdecdf49`):** done — 5-column bottom nav + S10 regression check.
- **Q9 (`arena/bdecdf49`):** done — OddsPapi wording corrected.
- **Q10 (`arena/bdecdf49`):** done — Polymarket US limitation published.
- **Q1/Q2 (`arena/e76bc0ae`):** Q2 done (summary card and unresolved link now say "Picks without a book line & limitations"); Q1 (distinct books in `source_count`) is `arena/e76bc0ae`'s pipeline change and is rendered verbatim by the site.
- **R16 (`arena/0fb2d0c7`, unique `source_key` per fixture, check D20):** not implemented here; **D20 is reserved for it**. The Gen.G–Invictus duplicate-Pinnacle issue must be fixed in `scripts/fetch_markets.py` / `model.py` (outside this session's scope).
- **`arena/cd27b02f` (PR #11, merged 15:45 UTC):** its verification record describes the **189-fixture** payload with 13 cancelled rows flagged. This branch supersedes that payload (175 priced, 13 excluded, D21 PASS). Their verification log is kept unchanged as the record of that run.

### Status
| Task | Status |
|---|---|
| T13 coverage audit and fix | done |
| T14 summary, unresolved, mobile | done |
| T15 betting-source refresh | done |
| T16 PR to main, merge, Pages | done — PR #12 merged, commit `c4619a7`; Pages build `39981988496` success; live refresh `41d7b1a` verified |

### Integration record (T16)
| Item | Value |
|---|---|
| PR | https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/12 (`arena/bd37dbe6-lolhotspawn2` → `main`) |
| Merge | `--merge`, merge commit `c4619a7a4c7033363b109e1fda260a969a0c88c4`, 2026-10-23 15:48 UTC (no approval wait, no auto-merge) |
| Post-merge refresh on main | Update Hotspawn LoL picks run `39981419329` — success; commit `41d7b1a` |
| Pages build for merge commit | `pages build and deployment` run `39981417237` — success |
| Pages build for refresh | run `39981988496` — success |
| Live check (fetched 2026-10-23) | https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/ shows 175 fixtures, 175 with a pick, 0 missing, 13 cancelled not priced; flagged page lists the 13 excluded fixtures |
| Verifier on merged tree | `scripts/verify_site.py`: 33 PASS · 0 FAIL · 0 WARN · 1 SKIP (D18 needs the Actions snapshot); `verification/test_verifier.py` 27/27 |
| Known open item (not blocking) | Gen.G vs Invictus Gaming now lists 10 market lines, several of them the same Pinnacle matchup repeated across boards (R16, owned by `arena/0fb2d0c7` / `arena/e76bc0ae`). Shown on the live page; not fixed in this PR. |

---

## Session `arena/b252f309-lolhotspawn2` — 2026-10-23
| Task | Status | Owner | Files |
|---|---|---|---|
| T13 Final integration audit: re-check current data coverage, source transparency, executive-summary navigation, mobile accessibility, and scheduled refresh; fix and verify remaining gaps | done (PR #13 merged; Pages deployment confirmed) | arena/b252f309 | COORDINATION.md, verification/**, docs/**, README.md, scripts/model.py, scripts/verify_site.py |

**Scope note:** PR #12 from `arena/bd37dbe6-lolhotspawn2` merged to `main` during this audit, adding the upcoming-only coverage contract (175/175; 13 cancelled excluded), summary coverage card, Polymarket US disclosure, phone URL wrapping, and S10 nav check. PR #13 initially conflicted with those merged changes; I rebased onto the new main, preserved its coverage/UI work, and skipped only two older generated-data commits whose payloads included cancelled fixtures. The latest main refresh is retained and the branch payload was re-audited. The audit's concrete source-provenance gap was that 24/166 model rows link only to a generic Leaguepedia table rather than a fixture-specific page; scope expanded to flag those rows and require a results-source URL without calling community data official.

**T13 sources & verification:** Hotspawn Pick'em lobby (`https://play.hotspawn.com/lol-pickems`) is the fixture source only; Pinnacle (`https://www.pinnacle.com/en/esports/league-of-legends`), Bovada (`https://www.bovada.lv/sports/esports/league-of-legends`), and Polymarket (`https://gamma-api.polymarket.com`) are market sources; Leaguepedia (`https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule`) is the results/model source and is disclosed as community-maintained, not official organizer verification. At PR #13 integration, the post-merge scheduled payload generated 2026-10-23T16:03:53Z (run [39983096955](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39983096955)) contained 172 upcoming fixtures, 9 market / 163 model, 0 unresolved, and 89 low-confidence rows; 16 cancelled fixtures were excluded. D21 confirmed 172/172 upcoming fixtures priced, no extras, and all 16 excluded. Sources were all `ok`: Hotspawn 172, Pinnacle 134, Bovada 8, Polymarket 9, Leaguepedia 31,728. The audit suite on that payload reported 35 PASS / 0 FAIL / 1 WARN; verifier self-tests 32/32; DOM contract PASS. D18 is the sole stale-snapshot warning (2026-10-21T20:44:30Z capture; 6 historical differences among 131 matched, 41 absent); these are not asserted as current reschedules. The fresh 2026-10-23 fetch had 203 Leaguepedia schedule rows; raw rows were not persisted for independent comparison. Five-link navigation is covered by S10 and the DOM contract, and source limitations are stated on Summary, Methodology, and Flagged pages.

**PR/deployment closeout:** PR #13 (https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/13) merged at 2026-10-23 16:00:15 UTC, merge commit `19832903ac77b8c23af53405401de50b49635019`. Post-merge verification [39983097096](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39983097096) and the refreshed-data Pages deployment [39983622611](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39983622611) both succeeded. Production: https://karagemop466-tech.github.io/LOLHOTSPAWN2/.

---

## Session `arena/0fb2d0c7-lolhotspawn2` — 2026-10-23 (T17–T19)

> Coordination & rebase note: claimed non-overlapping scope (`scripts/fetch_markets.py`, `scripts/fetch_leaguepedia.py`, `scripts/model.py`, `data/aliases.json`) at 15:37 UTC (`85f97a8`). Rebased cleanly onto `47d0e2c` (PRs #11/#12/#14/#15) and then `1983290` (PR #13 from `arena/b252f309`), preserving every merged session's `COORDINATION.md` entries, `D8c`/`D8d`/`GENERIC_RESULTS_SOURCE` checks, and `D21`/`S10` checks verbatim.

| Task | Status | Owner | Files |
|---|---|---|---|
| T17 Market & model integrity fixes: (a) filter Pinnacle child/special/prop matchups (`parentId is None`, `units == "Regular"`, `period == 0` full-match moneyline via `/leagues/{id}/markets/straight`) eliminating 7–8x duplicate rows per match; (b) add verified 4th live sportsbook feed **Unibet (Kambi)** (`eu-offering-api.kambicdn.com` pre-match 2-way `Match Odds`, per-event `unibet.com.au` links); (c) enforce 1 line per `source_key` per fixture in `model.py` consensus; (d) enrich missing `best_of` from verified Leaguepedia `MatchSchedule` | done | arena/0fb2d0c7 | `scripts/fetch_markets.py`, `scripts/model.py` |
| T18 Low-tier LoL resolution & alias verification: verify every tournament (12/12) and unrated/prior team in the live fixture feed against official Leaguepedia pages & `Standings`/`MatchSchedule`/`TeamRedirects` tables (`Special:CargoExport`); map tournament → canonical Leaguepedia page; add `MODEL_STANDINGS` fallback + thin-history shrinkage for 1–2 series teams (`REH Gaming`); fix `LYON` → `LYON (2024 American Team)`; scope `Phong Vũ Buffalo` → `PvB (Swiss Team)` in `PRM 2nd Division 26-27 Fall` with `HOTSPAWN_NAME_COLLISION` flag | done | arena/0fb2d0c7 | `scripts/fetch_leaguepedia.py`, `scripts/model.py`, `data/aliases.json` |
| T19 Post-task integration & verification: add `D20` check (unique `source_key` per fixture, reserved by `arena/bd37dbe6`) + UI label for `MODEL_STANDINGS` & `GENERIC_RESULTS_SOURCE` + source docs for Unibet/Standings, run live pipeline via `pipeline-test.yml` + full `verify_site.py` check (`36 PASS · 0 FAIL · 1 WARN`, `34/34` self-tests), open PR from `arena/0fb2d0c7-lolhotspawn2` to `main`, merge, confirm GitHub Pages deployment, record PR & deploy result here | done — PR #18 merged (`fcffaaa`), refresh `b7e5483` & Pages `39984363738` live | arena/0fb2d0c7 | `COORDINATION.md`, `scripts/verify_site.py`, `verification/test_verifier.py`, `verification/FINAL_REPORT.md`, `docs/assets/app.js`, `docs/methodology.html`, `research/betting-sources.md` |

### Integration & live deployment record (`T19`)
| Item | Value |
|---|---|
| PR | https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/18 (`arena/0fb2d0c7-lolhotspawn2` → `main`) |
| Merge | `--merge`, merge commit `fcffaaadf5a027d4964ac4cc8416ad12238e8788`, 2026-10-23 16:07:58 UTC |
| Branch verification runs (`pipeline-test.yml`) | [`39983000259`](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39983000259) and [`39983896972`](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39983896972) — both **success** |
| Post-merge verification on `main` (`verify.yml`) | [`39984204282`](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39984204282) — **success** (`34/34` self-tests, `36 PASS · 0 FAIL · 1 WARN`) |
| Post-merge production refresh on `main` (`update-picks.yml`) | [`39984204109`](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39984204109) — **success**; commit `b7e5483` (`2026-10-23T16:09:05Z`, `172/172` priced, `9` market, `163` model, `0` prior-only, `0` unresolved, `16` excluded) |
| GitHub Pages builds | [`39984203517`](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39984203517) (merge) and [`39984363738`](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39984363738) (refresh `b7e5483`) — both **success** (`status: built`) |
| Live site verified | https://karagemop466-tech.github.io/LOLHOTSPAWN2/ (`docs/index.html` + `docs/data/picks.json` fetched & verified live: 3-book consensus `Pinnacle, Polymarket, Unibet`, `Bo1`/`Bo3`/`Bo5` tags, 100% Leaguepedia competition URLs) |

### Cross-session requests logged & status
- **R15 (`scripts/fetch_hotspawn.py`, handled by `arena/bd37dbe6` in PR #12):** Resolved on `main` — 13 `cancelled` fixtures excluded from active picks and surfaced on Flagged (`D21` PASS).
- **R16 (`scripts/verify_site.py` `D20` + `MODEL_STANDINGS` UI label):** `arena/bd37dbe6` reserved `D20` for this session and completed `T13`–`T16`; `D20` implemented and live branch pipeline run `39983000259` passed green (`175/175` priced, `8 Pinnacle + 8 Unibet + 9 Polymarket`, `0` duplicates, `0` generic results fallbacks, `0` unrated priors).

### Verified metrics & flagged items (`arena/0fb2d0c7` live run `39983000259` + combined verifier)
- **External markets (`9` fixtures, `D20` PASS, `market_unmatched: 0`):** `Pinnacle` (`ok`, `8` parent-Regular moneylines — down from `134` duplicate child rows), `Unibet` (`ok`, `8` Kambi pre-match 2-way `Match Odds` via `eu-offering-api.kambicdn.com` + `www.unibet.com.au`), `Polymarket` (`ok`, `9` series markets via `gamma-api.polymarket.com`), `Bovada` (`no_data`, `0` events on this run — transparently surfaced in `sources_status`). All 8 Worlds 2026 Swiss Bo1 matches carry 3-source consensus (`Pinnacle + Unibet + Polymarket`); `Mental Rush vs Vitality Rising Bees` (Bo5) carries `MARKET_SINGLE` (`Polymarket`).
- **Leaguepedia results & provenance (`166` model fixtures, `D8c`/`D8d` PASS):** `31,732` completed results, `203` dated + `8` unscheduled schedule rows, `2,880` `Standings` rows, `3,574` canonical teams. `175/175` (`100%`) matched an individual Leaguepedia pairing (`150 exact-pair + 18 alias-pair + 4 rescheduled-pair + 3 unscheduled-pair`, `0` `GENERIC_RESULTS_SOURCE` rows) and `175/175` carry verified `best_of` (`138` Bo3, `33` Bo1, `4` Bo5). `89 MODEL_ELO` + `77 MODEL_ELO_THIN`, `0` prior-only, `0` unresolved, `82` low-confidence.
- **Flagged irregularities (non-blocking, published on `flagged.html` with source URLs):** `13` cancelled Hotspawn API fixtures excluded from active picks (`D21` PASS); `4` rescheduled `RIVALS LEAGUE/2026 Season/Season 2` fixtures (`START_TIME_MISMATCH`); `3` undated `PRM 3rd Division 26-27 Fall` fixtures (`LEAGUEPEDIA_TIME_TBD`); `2` `PRM 2nd Division 26-27 Fall` fixtures flagged `HOTSPAWN_NAME_COLLISION` (`Phong Vũ Buffalo` → `PvB (Swiss Team)`); `77` thin-history (`<5` games) model rows (`THIN_HISTORY`).
- **Combined test & verifier suite:** `python3 verification/test_verifier.py` → `34/34` pass; `python3 verification/check_dom_contract.py` → `PASS`; `python3 scripts/verify_site.py --leaguepedia-schedule data/diag` → `36 PASS · 0 FAIL · 1 WARN` (`D18` stale 2026-10-21 diagnostic snapshot).


---

## Session `arena/bdecdf49-lolhotspawn2` — 2026-10-23 (PR #21)

| Task | Status | Owner | Files (exclusive scope) |
|---|---|---|---|
| T19 Workflow reliability: make the branch pipeline artifact commit/rebase/push fail loudly and safely, without touching other sessions' claimed site/data scopes | done | arena/bdecdf49 | `.github/workflows/pipeline-test.yml`; this file for coordination entries |
| T20 Post-merge verification & Pages deployment recovery: monitor PR #21 main Actions runs, recover/retry the Pages deploy if transient, verify live Pages content, and record evidence | done — latest Pages deployment `39986801808` and live payload verified; initial merge-run HTTP 500 recorded | arena/bdecdf49 | `COORDINATION.md` only |

**Scope note:** This session uses Arena's fixed branch `arena/bdecdf49-lolhotspawn2`; branch creation/switching is not permitted in this workspace. After checking the active claims on `arena/bd37dbe6` (T13–T16) and `arena/e76bc0ae` (T17–T18), T19's code-change scope was limited to `.github/workflows/pipeline-test.yml`; T20's post-merge verification and logging are limited to `COORDINATION.md`. No files in other sessions' site, source/model, or fixture scopes were edited.

### Workflow reliability: diagnosis and verification

- Actions run **39980957176** passed pipeline generation, summary, and site verification but failed in “Commit outputs for review” with `could not abort failed output rebase (128): fatal: no rebase in progress`. The Actions log archive could not be retrieved (GitHub returned EOF), so the annotation is the available failure evidence.
- `verify_site.py` updates tracked `verification/report.json` and `verification/last_report.md`. The workflow had not staged those files, leaving the worktree dirty and preventing the output rebase from starting. Staging both reports with the payload and diagnostics fixed the issue: run **39981581552** succeeded end-to-end.
- The `fail_publish` “Remote HEAD” line used valid Bash command substitution; its nested quoting was not a syntax/runtime defect. It was simplified to assign `remote_head` before writing the summary. `bash -n` and a local runtime check passed. The failure-only branch was not deliberately triggered.
- After PR #18 merged the market-deduplication, Unibet, and D20 changes (`fcffaaa`) and PR #17's final report was merged (`3ad4f00`), this branch was rebased onto current main. Actions run **39985420241** tested that rebased tree and passed end-to-end in **1m8s**; all steps passed, including live generation, site verification, and “Commit outputs for review.” Generated artifact commit `25f017c` was pushed.
- The 39985420241 payload (generated **2026-10-23T16:17:40Z**) contains **172** upcoming fixtures: **172 resolved**, **9 market-derived** (8 consensus, 1 single), **163 model-derived**, **0 unresolved**, **80 low-confidence**, **12 cancelled excluded**, **0** upcoming fixtures without a published match page, and **0** `GENERIC_RESULTS_SOURCE` rows. These are run-specific values.
- Source status in that run: Pinnacle **ok** (8), Unibet **ok** (8), Polymarket **ok** (9), Leaguepedia MatchSchedule **ok** (31,728), and Hotspawn lobby **ok** (172); Bovada was **no_data** (0). Do not report Bovada lines as used. D20 passed: every market row has unique provider keys and matching `source_count`.
- `verification/report.json` for run 39985420241: **36 PASS, 0 FAIL, 0 WARN, 1 SKIP**. D20 and D21 passed (172 upcoming and priced, missing 0, extra 0, excluded 12, leaked 0); D18 was skipped because no Leaguepedia schedule snapshot was supplied. The existing stale-snapshot caveat remains for independent current start-time checking.

### Cross-session findings (resolved)

- Q7–Q10 were addressed by `arena/bd37dbe6` (T13–T15), merged in PR **#12** at `c4619a7`. Their detailed source checks, coverage/mobile fixes, and remaining caveats are recorded in that session's results section above. This session did not edit their claimed files.

### Consolidation note (arena/e76bc0ae, 16:30 UTC)

`main` now carries the source probe as `scripts/probe_sources.py` (output `data/diag/source_probe.json`, run by
`pipeline-test.yml`), so this branch **removed the duplicate** `audit/probe_sources.py`, `audit/source_probe.*` and the
`Audit external sources` workflow. Two probes on the same branch were doubling Actions minutes and re-triggering each
other. The `audit/` directory now holds only what `main` lacks: `test_model.py` (20 offline regression checks) and
`coverage_reconcile.py` (lobby + fixtures API vs published payload), both run by the strict audit workflow, which also
publishes `audit/last_run.json` for manual review.

The strict workflow's `paths:` filter only fires on `scripts/**`, `audit/coverage_reconcile.py`, `audit/test_model.py`
and itself, so documentation-only commits do not queue a 10-minute live run.

### Post-merge verification & live Pages record (T20)

| Item | Result | Evidence |
|---|---|---|
| PR #21 | `ci: make branch artifact publishing resilient` merged into `main` | https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/21 |
| Merge | `684d6b6433fcdb72187fa1dce56e3f3cb05c17ed`, 2026-10-23 16:19:44 UTC | GitHub PR #21 merge record |
| Main verifier at PR #21 merge | **success**; all steps passed, including self-tests, offline verification, external source/live Pages checks, coverage audit, and DOM contract | https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39985868839 |
| Initial Pages Actions run for PR #21 | Jekyll build and artifact upload succeeded; `deploy` failed when GitHub's Pages API returned HTTP 500 (`Failed to create deployment`, request ID `EC10:37CAF:18AB01E:5029D9E:6ADB8942`; annotation advised retrying later) | https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39985868427/job/120524954576 |
| Follow-up main verifier | **success** after the subsequent main integration; all verifier steps passed on `43ebddd` | https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39986388519 |
| Six-hour refresh | **success** (run `39986631247`); the current payload was generated 2026-10-23 16:26:31.910454 UTC, with next refresh due 22:26:31.910454 UTC | https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39986631247 |
| Latest Pages Actions deployment | **success** on current main commit `aaaefeb`; build, deploy, and report-status jobs all passed | https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/39986801808 |
| Pages build API | **`built`** for `aaaefeb0cee1a55ad7fc72ca9d622e4c2a4895c3`, created 16:26:35Z, updated 16:27:31Z (56.396 s) | https://api.github.com/repos/karagemop466-tech/LOLHOTSPAWN2/pages/builds/latest |
| Live dashboard | Current live summary and cache-busted JSON match the 16:26:31Z main payload: 172 upcoming fixtures, 172 priced, 9 market-derived, 163 model-derived, 0 unresolved, 80 low-confidence, and 12 cancelled fixtures excluded | [Dashboard](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/index.html?v=aaaefeb) · [Live picks JSON](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/data/picks.json?v=aaaefeb) |

**Deployment irregularity:** The first Pages deploy attempt for `684d6b6` failed with the transient HTTP 500 above; `gh run rerun 39985868427 --failed` was unavailable for GitHub's generated `pages-build-deployment` workflow, and a manual Pages-build API request was rejected with HTTP 403 (`Resource not accessible by integration`). A later automatic Pages deployment, run `39986801808`, succeeded and published current main; the first failure is retained here rather than presented as a green run. In the final live check, the normal dashboard page and cache-busted JSON showed the current 16:26:31Z payload; a direct unversioned JSON fetch returned the prior 16:24:46Z snapshot. `docs/assets/app.js` fetches `data/picks.json` with `cache: "no-store"`; this one-refresh discrepancy is recorded as a fetch/CDN-cache observation, not as proof of a stale browser view.


### Live cross-checks performed by arena/e76bc0ae (2026-10-23, 16:2x–16:5x UTC)

| Check | Method | Result |
|---|---|---|
| Priced row matches its cited book | `fetch_page` on https://polymarket.com/event/lol-gen-ig1-2026-10-23 | Page shows **Gen.G 77¢ / Invictus Gaming 24¢**; payload recorded **0.765** at 16:26Z. Consistent within normal price drift. |
| Every upcoming lobby fixture is either priced or explicitly excluded | `audit/coverage_reconcile.py` in strict run 39987084028 | required **184**, priced **172**, excluded **12** (all `cancelled`), unexplained **0** |
| Each book counted once | `audit/test_model.py` + payload invariant | 9 market rows, each with Pinnacle + Unibet + Polymarket exactly once (`distinct_books = source_rows = 3`) |
| Picks are valid and sourced | `audit/test_model.py` (new checks) | 172/172 rows: documented method, absolute source URL, pick ∈ {team1, team2} |
| Site verifier | `scripts/verify_site.py` | PASS · 36 pass · 0 fail · 0 warn · 1 skip |
| App script syntax | `node --check docs/assets/app.js` | OK |

**Note for the integration session:** `MODEL_STANDINGS` did not appear in the 16:29Z payload because every one of the 172 fixtures
had at least one rated side (Elo or thin-Elo); the standings branch ran but had nothing to replace. The 12 cancelled fixtures are
the only unpriced rows, and Hotspawn itself marks them cancelled. No fixture was dropped for lack of a source.

### PR #24 merged — deployment confirmed (arena/e76bc0ae, 16:35Z)

| Item | Value |
|---|---|
| Pull request | https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/24 |
| Merge method / result | `gh pr merge 24 --merge` → **MERGED** 2026-10-23T16:35:13Z |
| Merge commit on `main` | `d01f9ca` |
| Pages build for that commit | **success** (run 39988002313); `https://karagemop466-tech.github.io/LOLHOTSPAWN2/` serves the new `app.js` (MODEL_STANDINGS chip, "your local time", "book(s)") |
| Post-merge verify workflow | **success** (run 39988004265) — 36 pass / 0 fail / 0 warn / 1 skip |
| Post-merge scheduled publisher | **success** (run 39988004347) → `a5b9efe` "picks: scheduled refresh [skip ci]" |
| Fresh payload on `main` | 172 fixtures · 172 priced · 0 unresolved · 80 Low · 9 market rows (3 books each) · 12 cancelled exclusions |
| Pages build for `a5b9efe` | **success** (run 39988182115) |

The publisher run is the first live exercise of the new merge-based retry: it committed and pushed on the first
attempt, so the 6-hour refresh no longer depends on a rebase surviving a concurrent bot commit.

`docs/methodology.html` now carries a **Manual verification log** with five checks (Polymarket price vs published
consensus, full fixture coverage, per-book de-duplication, fixture/start-time match, 36-check payload pass), each with
the exact source link so a human can repeat it.

---

## Session `arena/1b6841c2-lolhotspawn2` — 2026-10-23 (mobile UX, `leagues.html`, every-row source links, Liquipedia API probe & full audit)

> Branch note: Session branch fixed to `arena/1b6841c2-lolhotspawn2`. Integrated cleanly with `origin/main` through PRs #16–#19 and #21–#25 (`859d137`), preserving **100%** of all prior sessions' backend, audit, workflow, UI, and documentation work.

### Scope completed (`arena/1b6841c2-lolhotspawn2`)

| Task | Status | Owner | Summary & Files |
|---|---|---|---|
| C1/C2 Helper modules, Liquipedia `api.php` probe & `league_breakdown` | done | `arena/1b6841c2` | Added `scripts/standings_and_books.py` (compliant Liquipedia MediaWiki `api.php` probe with gzip & ≥2.2s spacing + standings/Pinnacle helpers), `scripts/entity_resolution.py` (contextual disambiguation & schedule bridging), and `build_league_breakdown()` + `Leaguepedia Standings` / `Liquipedia` `sources_status` in `scripts/update_picks.py` alongside `unresolved.by_league`. |
| C3 Full line-by-line audit of all live fixtures | done | `arena/1b6841c2` | Published `research/line-by-line-audit-2026-10-23.md` auditing all **172 scheduled upcoming fixtures + excluded cancelled rows** line by line with source links on every row, and updated `research/betting-sources.md` + `README.md`. |
| C4 Mobile UX, `docs/leagues.html` & every-row source links | done | `arena/1b6841c2` | Added `docs/leagues.html` (`By league` dedicated subpage); unified `docs/index.html` with `#quick-picks-body`, `#summary-leagues-body`, `#starting-soon` / `#soon-count`, `#featured-heading`, and `#unresolved-heading`; added `#league-limitations-body` on `docs/unresolved.html`; added `Sources` column on `#flagged-body`, entity-bridge audit table (`#bridges-body`), and missing `HOTSPAWN_NAME_COLLISION` / `LEAGUEPEDIA_TIME_TBD` definitions on `docs/flagged.html` + `docs/assets/app.js`; preserved `Manual verification log` + CC BY-SA 3.0 attributions on `docs/methodology.html`; synced 6-column `.bottom-nav` across all 7 HTML pages. |
| C5 Verifier fixes, unit tests & live CI pipeline runs | done | `arena/1b6841c2` | Added `bovada.lv` / `kambicdn.com` to `MARKET_HOSTS` in `scripts/verify_site.py`, prop-board leak check in `D20`, `leagues.html` in `S1`, `http_status_retry` + `wait_for_http` live Pages deploy-window tolerance (fixing I20), and `verification/test_entity_and_books.py` (`10/10`) alongside `test_standings_model.py` (`10/10`), `audit/test_model.py` (`20/20`), `test_verifier.py` (`35/35`), and `check_dom_contract.py` (`PASS`). |

### PR #27 merged — live production refresh & GitHub Pages deployment verified (`arena/1b6841c2`, 16:52 UTC)

| Item | Result & Evidence |
|---|---|
| Pull request | **PR #27** — https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/27 (`arena/1b6841c2-lolhotspawn2` → `main`) |
| Merge commit | `a4b795f` (`Merge pull request #27 from karagemop466-tech/arena/1b6841c2-lolhotspawn2`) |
| Pre-merge branch runs | `39985495515` (`6ba9bbd`) and `39987450421` (`3977141`) — both **100% green** (`update_picks.py`, DOM contract, unit tests, `verify_site.py --check-external`, `probe_sources.py`) |
| Post-merge Pages deploy #1 | **success** — run `39989183052` deployed all 7 HTML pages including `docs/leagues.html` |
| Post-merge live 6h refresh on `main` | **success** — run `39989184592` (`9d65409`, `generated_at = 2026-10-23T16:52:07.057868Z`): **172 / 172 upcoming fixtures resolved (`100.0%`)**, `9` market (`8` 3-book consensus + `1` single), `163` Elo model (`88` `MODEL_ELO` + `75` `MODEL_ELO_THIN`), `0` unresolved, `12` cancelled fixtures excluded, `10` per-league breakdown rows & all 8 `sources_status` entries published |
| Post-refresh Pages deploy #2 | **success** — run `39990334025` deployed fresh `9d65409` payload to https://karagemop466-tech.github.io/LOLHOTSPAWN2/ |
| Follow-up verifier hardening PR (#28 + #29) | Merged `wait_for_http()` + `http_status_retry()` in `scripts/verify_site.py` (PR **#28**, Pages deploy `39990798461` **success**), and replaced US-geoblocked SPA route `www.pinnacle.com/en/esports/league-of-legends` (HTTP `404` on US-East CI runners) in `docs/methodology.html`'s manual check log with the public `200 OK` JSON feeds actually queried by CI (`guest.api.arcadia.pinnacle.com` & `gamma-api.polymarket.com`) so `verify.yml` passes `X1`–`X3` cleanly on `main`. |

\n## Session `arena/ea9a3e15-lolhotspawn2` — 2026-10-24 (final integration verification)\n\n| Task | Status | Owner | Files (claimed scope) |\n|---|---|---|---|\n| IV1 Final integration review: re-verify the combined tree line by line (schema, per-row sources, methods, probabilities, counts, unresolved/low-confidence handling, mobile nav, internal links, root redirect, refresh cadence) | done | arena/ea9a3e15 | `scripts/verify_site.py`, `docs/**`, `docs/data/picks.json` |\n| IV2 Unit + contract tests | done | arena/ea9a3e15 | `verification/test_verifier.py`, `verification/test_entity_and_books.py`, `verification/test_standings_model.py`, `audit/test_model.py`, `verification/check_dom_contract.py` |\n| IV3 Live Pages confirmation: Pages build status, live dashboard render, fresh payload served | done | arena/ea9a3e15 | GitHub Pages API + live `https://karagemop466-tech.github.io/LOLHOTSPAWN2/` |\n| IV4 PR from integration branch to `main`, merge, confirm Pages deploy, record PR link + result here | in progress → PR opened | arena/ea9a3e15 | COORDINATION.md (board entries only); branch `arena/ea9a3e15-lolhotspawn2` == `main` at `72c9b5a` at claim, so the PR carries this session's COORDINATION.md record only |\n\n### Verification performed this session (local, offline; egress is restricted to GitHub/PyPI so live bookmaker re-checks are done by CI)\n\n| Check | Result | Evidence |\n|---|---|---|\n| `python3 scripts/verify_site.py` | **36 PASS · 0 FAIL · 0 WARN · 1 SKIP** | D18 SKIP: no `--leaguepedia-schedule` snapshot available offline (CI supplies `data/diag/`; on main this runs as a WARN, never a FAIL — Hotspawn remains authoritative for pick locks) |\n| `verification/test_verifier.py` | **35/35** | verifier rule self-tests |\n| `verification/test_entity_and_books.py` | **10/10** | entity resolution + bookmaker helpers |\n| `verification/test_standings_model.py` | **ALL PASS** | Elo + standings blend |\n| `audit/test_model.py` | **20 passed · 0 failed** | de-duplication, prop rejection, standings, market precedence, prior fallback, unresolved |\n| `verification/check_dom_contract.py` | **PASS** | all JS-referenced ids present on the 7 pages |\n| `node --check docs/assets/app.js` | **OK** | shared JS syntax |\n| GitHub Pages API | **`built`** | source: main, path `/`, https enforced, live at https://karagemop466-tech.github.io/LOLHOTSPAWN2/ |\n| Recent Actions (all success) | Verify picks and site `40110361789` (2026-10-24 16:10) · Pages build `40107164601` (15:28) · Update picks `40106555419` (15:20) | the 15:20 refresh generated the payload now on `main` |\n| Live dashboard fetch | **renders** | executive summary with in-site quick-jump links to picks / by-league / unresolved / flagged / methodology; 169 fixtures, 9 market, 0 unresolved; pick probabilities + source links shown per match; responsive viewport + 6-link bottom nav |\n\n### Payload on `main` / this branch (generated 2026-10-24T15:28:56Z by the scheduled 6h refresh)\n\n169 upcoming Hotspawn LoL fixtures · **169 resolved (100.0%), 0 unresolved** · 9 market-derived (Pinnacle + Unibet + Polymarket, de-duplicated to one line per book: 8 consensus + 1 single) · 160 model-derived (93 MODEL_ELO, 67 MODEL_ELO_THIN) · 0 MODEL_STANDINGS / MODEL_LEAGUE_PRIOR / UNRESOLVED in this window · 73 low-confidence (thin history / cross-league) · 14 cancelled fixtures excluded and listed on Flagged · per-league breakdown: PRM 3rd 61, PRM 2nd 36, Tunisian 25, RIVALS S2 18, Worlds 8, Arabian 2nd 6, 4 Nations 4, Komplettligaen Playoffs 3, LCP 3, LigaGG A 2, LigaGG B 2, LGC Rising 1 · `sources_status`: Pinnacle ok/8, Unibet ok/8, Bovada no_data/0, Polymarket ok/9, Leaguepedia MatchSchedule ok/31752, Leaguepedia Standings ok/2880, Liquipedia no_data/0, Hotspawn lobby ok/169 |\n\n### Sources used (official / verified, links for manual review)\n\n- Hotspawn Pick'em lobby + fixtures API (fixture list only — never a probability input): https://play.hotspawn.com/lol-pickems · https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures\n- Pinnacle guest JSON (two-way series moneyline, parent boards only; labelled unofficial): https://guest.api.arcadia.pinnacle.com/0.1 · site https://www.pinnacle.com/en/esports/league-of-legends\n- Unibet via Kambi public JSON feed (Match Odds): https://eu-offering-api.kambicdn.com/... · site https://www.unibet.com.au/betting/sports/filter/esports/league_of_legends/all/matches\n- Bovada coupon JSON (two-way moneyline): https://www.bovada.lv/services/sports/event/coupon/events/A/description/esports/league-of-legends · site https://www.bovada.lv/sports/esports/league-of-legends\n- Polymarket Gamma API (series markets only; Game-N/Map-N child markets never used as series prices): https://gamma-api.polymarket.com · site https://polymarket.com (US trading blocked — reference data only)\n- Leaguepedia Cargo MatchSchedule + Standings + TeamRedirects (CC BY-SA 3.0; community-maintained, disclosed as such): https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule · https://lol.fandom.com/wiki/Special:CargoTables/Standings\n- Liquipedia MediaWiki API probe only (CC-BY-SA 3.0, gzip, ≥2.2s pacing, API-only per terms): https://liquipedia.net/leagueoflegends/api.php\n\n### Irregularities / flagged items (non-blocking; published on the site's Flagged for Review page)\n\n- D18: amateur-league fixtures where Leaguepedia's recorded schedule disagrees with Hotspawn or lacks the row; Hotspawn epoch-ms governs pick lock times, per-row `START_TIME_MISMATCH` flags attached.\n- 14 fixtures cancelled on the Hotspawn feed are excluded from picks and listed with source link (not silently dropped).\n- No bookmaker prices tier-3/amateur leagues; those rows are priced by the league-anchored Elo model from Leaguepedia results, labelled Low confidence where history is thin.\n- Pinnacle consumed via the public guest front-end feed (unofficial); Bovada returned `no_data` on this run — consensus fell back to healthy sources, source status published per run.\n- Polymarket trading is blocked for US users; its prices are reference data only (disclosed on Methodology + Unresolved pages).\n- Liquipedia API returned no usable data in this run (rate-limited/blocked); the pipeline degrades gracefully and publishes `no_data`.\n- 73 rows are Low confidence (thin history <8 games, cross-league tier comparison, or league prior); these are estimates, not edges, and are flagged per row.\n- `MODEL_STANDINGS` / `MODEL_LEAGUE_PRIOR` / `UNRESOLVED` did not appear in this window because every fixture had a rated side; the fallback code paths remain covered by unit tests and the unresolved/limitations section exists for any future window.\n\n### Requirement traceability (all PASS — see `verification/report.json`)\n\nREQ1 pick for every match · REQ2 probabilities sum to 1 · REQ3 no Hotspawn probability input · REQ4 external lines where they exist · REQ5 pick + documented method for every non-market match · REQ6 separate unresolved section with limitations linked from exec summary · REQ7 exec summary links in-site to picks · REQ8 official/trusted source link on every row or flagged unverified · REQ9 mobile-friendly · REQ10 automatic 6h refresh, no manual input · REQ11 no broken internal links, root entry works · REQ12 third-party attribution (Leaguepedia / Liquipedia CC BY-SA 3.0).\n\n### Integration result (pending)\n\nBranch `arena/ea9a3e15-lolhotspawn2` is at `72c9b5a`, identical to `main`; this session's only change is this COORDINATION.md record. A PR from this branch to `main` is opened below, merged without waiting for approval, and the merge commit + Pages build id are recorded here after the deploy confirms.\n

---

## Session `arena/66e731b3-lolhotspawn2` — 2026-10-24 (in progress)

> Branch note: Arena tracks this session by branch `arena/66e731b3-lolhotspawn2` (branched from `72c9b5a`, fast-forwarded to `215656b` after PR #30 merged). It stands in for `session-<id>/<task>`.

Baseline at claim (main `215656b`, payload generated 2026-10-24T15:28:56Z): 169 fixtures · 9 market (8 `MARKET_CONSENSUS` + 1 `MARKET_SINGLE`, Pinnacle/Unibet/Polymarket only, **Bovada 0**) · 93 `MODEL_ELO` · 67 `MODEL_ELO_THIN` · 0 `MODEL_STANDINGS` · 0 `MODEL_LEAGUE_PRIOR` · 0 `UNRESOLVED` · 73 low-confidence · 14 cancelled excluded. `scripts/verify_site.py` 36 PASS / 0 FAIL / 0 WARN / 1 SKIP; all unit tests green locally. No other session active on these files (open PRs #20/#26 are stale branches from 2026-10-23, not claimed here).

| Task | Status | Owner | Files |
|---|---|---|---|
| U1 Fresh source research for non-featured (low-tier / no-Polymarket) matches: established LoL books → esportsbooks → odds/data APIs → community results; expand CI probe | done | arena/66e731b3 | research/betting-sources.md (§13), scripts/probe_sources.py, data/diag/source_probe.json (CI) |
| U2 Fix Bovada adapter dropping every LoL moneyline (period `Game`/`main:true` rejected as single-game) + `standings_pages` count bug (published "across 0 competitions") | done | arena/66e731b3 | scripts/fetch_markets.py, scripts/fetch_leaguepedia.py, scripts/update_picks.py, verification/test_entity_and_books.py |
| U3 Phone-first executive summary: picks first, one clear find-your-picks link block, fix dead `#status-strip`/"Loading…" header on summary+unresolved (app.js never populated it) | done | arena/66e731b3 | docs/index.html, docs/unresolved.html, docs/assets/app.js, docs/assets/style.css |
| U4 Unresolved & limitations section in exec summary always populated (unresolved + low-confidence reasons + per-league no-book limits + link to unresolved.html#by-league) | done | arena/66e731b3 | docs/index.html, docs/assets/app.js |
| U5 Line-by-line verification of fresh CI payload, PR → merge → Pages confirmation | in progress | arena/66e731b3 | COORDINATION.md, README.md if counts change |

**Scope rule honoured:** no price is copied from any newly researched source into picks without a structured-feed probe from CI plus a human-verifiable sample row. Hotspawn crowd % remains never an input.

**Results (2026-10-24, branch pipeline run `40112009538` — all steps success):** fresh payload generated 2026-10-24T16:40:01Z: **160 fixtures · 160 resolved (100%) · 0 unresolved** · 9 market (8 `MARKET_CONSENSUS` now **4-book** Pinnacle/Unibet/**Bovada**/Polymarket, max dispersion 0.046 · 1 `MARKET_SINGLE`) · 93 `MODEL_ELO` · 58 `MODEL_ELO_THIN` · 64 low-confidence · 18 cancelled excluded. Bovada `ok/8` live (was `no_data/0` — U1/U2 bug, snapshot replay 0/9→9/9, `test_entity_and_books.py` 14/14). Standings note fixed: *"2,880 rows across 209 competitions"* (was 0). Probe of 21 sources measured 16:40Z (`data/diag/source_probe.json`): BetOnline/TonyBet/BC.Game/gol.gg 200 HTML (human cross-check only); SportsBetting.ag/Stake/PandaScore-no-token/Oracle's-Elixir 403 — **no new adapter qualified**; key-only vendors documented from official docs (PandaScore FAQ: stats API has no bookmaker odds; Abios: licensed books + largest tournaments) and published in payload `checked_unavailable` (18 entries) + limitations (10). Independent line-by-line audit of the fresh payload: 160 rows, 0 errors (prob sums, pick=max-prob team, https sources on every row, one line per book, Bovada host `bovada.lv`, league sums 160/9/64). `verify_site.py` 36 PASS/0 FAIL/0 WARN/1 SKIP locally and green in CI with `--check-external`; DOM contract PASS; verifier 35/35; standings ALL PASS; audit 20/20. Site: exec summary now phone-first (starting-soon picks first, pricing-cascade card, single link set, unresolved box lists no-book leagues), summary+unresolved headers unified (was unstyled/clipped — `.bar` collision, dead `#status-strip`/`#theme-toggle`). Flagged (non-blocking): `verification/flagged_items.md` U1–U4. **PR & deploy record:** filled in after merge (below).

---

---

## Session `arena/e6f33fe9-lolhotspawn2` — 2026-10-24 (executive-summary findability, on-page unresolved section, mobile UX, source re-probe, jsdom render check)

> Branch note: Arena fixes this session to `arena/e6f33fe9-lolhotspawn2`; branch switching/creation is not permitted, so it stands in for `session-<id>/<task>`. Claim pushed before any edit.

| Task | Status | Owner | Files (exclusive scope) |
|---|---|---|---|
| E1 Exec-summary restructure: picks first on mobile, big in-site pick links, "where are the picks" block; separate unresolved section **inside the executive summary** listing every unresolved fixture + per-league signal/limitation table | done | arena/e6f33fe9 | `docs/index.html`, `docs/assets/app.js`, `docs/assets/style.css` |
| E2 Mobile readability pass: tap targets ≥44px, no horizontal overflow, viewport meta on every page, readable pick/probability at 360-390px | done | arena/e6f33fe9 | `docs/assets/style.css`, `docs/*.html` (markup only) |
| E3 Live re-probe of lower-tier odds sources (established books → esportsbooks → aggregators) and publish findings with source links; add candidates to the CI probe | done | arena/e6f33fe9 | `scripts/probe_sources.py`, `research/betting-sources.md` |
| E4 Automated DOM render check with jsdom against the real payload (all 7 pages) + verifier assertions for the new exec-summary anchors | done | arena/e6f33fe9 | `verification/check_dom_render.js`, `scripts/verify_site.py`, `.github/workflows/pipeline-test.yml`, `.github/workflows/verify.yml` |
| E5 Line-by-line spot verification of live rows against Leaguepedia/Polymarket + integration, PR, merge, Pages deploy confirmation | done | arena/e6f33fe9 | `COORDINATION.md`, `verification/*.md` |

Baseline at claim (branch == `main` @ `72c9b5a`): payload `generated_at` 2026-10-24T15:28:56Z — **169 fixtures, 169 priced, 9 market, 160 model, 0 unresolved, 73 low-confidence**, 14 cancelled exclusions; `scripts/verify_site.py` **36 PASS / 0 FAIL / 0 WARN / 1 SKIP**; `test_verifier.py` 35/35; `check_dom_contract.py` PASS. Open PRs #20 and #26 belong to other sessions and are not touched. No other session has claimed `docs/**`, `scripts/probe_sources.py`, `scripts/verify_site.py` or `verification/**` today.

### Results (session `arena/e6f33fe9`, 2026-10-24)

**What was wrong before this session (verified, not assumed).**

1. `docs/index.html` and `docs/unresolved.html` — the two pages a phone visitor lands on first — used
   `<div class="wrap bar">` for their header. `.bar` is the **12px probability bar** rule in
   `style.css`, so the header was clipped to a 12px strip with `overflow:hidden`; the classes used
   for that header (`.brand`, `.mark`, `.bar-end`, `.status-strip`, `.icon-btn`) had **no CSS at all**,
   and `.covbar`, `.nav-list` and `.stat b/.stat span` were likewise unstyled. Both pages now use the
   same `.header-inner` / `.logo` header as the other five, and every class a page uses now has a rule.
2. The executive summary's "unresolved" section only rendered counts, a reason list and four
   limitation bullets — it **did not list a single unresolved fixture**, and the per-league
   limitation table existed only on `unresolved.html`.
3. Nothing verified that the pages actually *render*: `check_dom_contract.py` only checks that the
   ids the script references exist.

**What changed.** Picks-first executive summary (one 54px "Find every pick" button → "Where the
picks are" card grid with live counts → matches locking soonest + quick-scan table → coverage →
separate unresolved section listing **every** unresolved fixture plus a per-league limitation table
→ per-competition breakdown → market picks → sources). Mobile: full-width hero buttons under 620px,
≥44px tap targets, `scroll-margin-top` on anchored sections so in-page jumps clear the sticky
header. Every page keeps the six-item bottom nav.

**Verification performed on this branch**

| Check | Result |
|---|---|
| `node verification/check_dom_render.js` (new, jsdom, real payload) | **43/43 pass** — renders all 7 pages, asserts row counts vs payload, pick ∈ {team1, team2}, probabilities sum to 100%, a source link on every row, the summary's in-site pick links, and that a synthetic 2-fixture unresolved payload is listed |
| `python3 scripts/verify_site.py` | **39 PASS · 0 FAIL · 0 WARN · 1 SKIP** (new checks S11 exec-summary unresolved section + ordering, S12 every CSS class styled, S13 render harness wired into CI) |
| `python3 verification/check_dom_contract.py` | PASS |
| `test_verifier.py` / `test_standings_model.py` / `test_entity_and_books.py` / `audit/test_model.py` | 35/35 · ALL PASS · 10/10 · 20/20 |
| Live pipeline on branch, run [`40111948960`](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40111948960) | **success** — 160 fixtures, 160 priced, 0 unresolved, 9 market rows (Pinnacle 8 · Unibet 8 · Polymarket 9), 18 cancelled excluded, `verify_site.py` PASS 39 / 0 fail |
| First run [`40111240395`](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40111240395) | **failure, fixed** — X1 found one dead external link: the methodology page pointed at `github.com/.../blob/main/verification/check_dom_render.js`, which does not exist on `main` yet (the harness was new on this branch). The link was removed rather than left broken. |

**Source research (E3), all re-measured from CI on 2026-10-24** — `data/diag/source_probe.json`,
written up in `research/betting-sources.md` §13:

| Candidate | Observed | Used? |
|---|---|---|
| Betmonitor — PRM 2nd Division comparison | HTTP 200, HTML only; page shows bet365 1.98/1.92, Unibet 2.50, efbet 3.38, novibet 5.25/12.25 for a real fixture | No (no API, Cloudflare/ToS) |
| BMBets — LoL Prime League | HTTP 200, HTML only | No |
| OddsPortal — LoL Prime League | bot-protected comparison page | No |
| Strafe LoL odds | HTTP 200, HTML only | No |
| Oddspedia generic LoL odds | **HTTP 410 permanently deleted** (CI + direct fetch) | No |
| eGamersWorld LoL odds | 200; board carried only 2026 World Championship fixtures on 2026-10-24 | Human cross-check only |
| Kambi `ubca` / `ub` (in production) | 8–9 World Championship events; `market=DE`/`SE` return the same set; `…/ubde/…` answers HTTP 400 | Already used; cannot widen coverage |

Conclusion recorded on the site: tier-2/3 fixtures have **no accessible licensed feed**, so their
picks stay on our own Elo/standings line, and their limits are now stated in the executive summary
itself rather than buried on a subpage. No scraper was built.

**Line-by-line spot verification against official sources (2026-10-24)**

| Row checked | Source opened | Observed | Result |
|---|---|---|---|
| Top Esports vs Anyone's Legend (`MARKET_CONSENSUS`, published 0.365) | [Polymarket event](https://polymarket.com/event/lol-tes-al-2026-10-24) · [Kambi feed](https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=GB&useCombined=true) | Polymarket 37¢ / 64¢; Kambi 2.65 / 1.42 | Matches (median 0.365 between books) |
| JSK Esports vs El Menzah Esports (`MODEL_ELO_THIN`, Tunisian Super League 2026, 24 Oct 16:00) | [Hotspawn match page](https://www.hotspawn.com/matches/jsk-esports-vs-el-menzah-esports-tunisian-super-league-2026-1080924) · [Leaguepedia competition](https://lol.fandom.com/wiki/Tunisian_Super_League/2026_Season) | Both teams, tournament and start time confirmed; Leaguepedia page exists with the split's results | Matches |
| Hotspawn lobby vs payload | [Lobby](https://play.hotspawn.com/lol-pickems) · [live payload](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/data/picks.json) | Lobby lists 241 LoL rows (169 upcoming at 15:28Z); payload carries `lobby_upcoming = priced` with 0 missing | Matches |

**Flagged irregularities for human review (non-blocking)**

- Tier-2/3 line existence vs access: Betmonitor shows bet365 pricing Prime League 2nd Division, so
  "no bookmaker prices these leagues" is **too strong** — the accurate statement, now used on the
  site, is "no bookmaker feed we may legally use prices them". A human may want to license one.
- Oddspedia's generic LoL odds paths return HTTP 410; older research (session `arena/92bfcdd3`, §12)
  cited eGamersWorld/OddsPortal as human cross-checks only — that remains true.
- D18 stays WARN by design: it compares against a 2026-10-21 diagnostic snapshot that is now ~68h
  old; the verifier labels it stale rather than pretending it verifies the current schedule.

---

## Session `arena/ac089f33-lolhotspawn2` — 2026-10-24 (coverage for low-tier fixtures, mobile executive summary)

Branch note: Arena fixes this session to `arena/ac089f33-lolhotspawn2`; that branch stands in for `session-<id>/<task>`.

| Task | Status | Owner | Files (exclusive scope) |
|---|---|---|---|
| T21 Line-source expansion: probe established books → esportsbooks → esports aggregators for per-match LoL prices that cover the 160 fixtures currently priced only by our model; implement an adapter only for a source that actually returns structured per-match prices, otherwise publish the evidence | done — 39 requests / 30 sites, **0 with new coverage** (evidence in `data/diag/line_probe.json`, table on Method & Sources, summary card on the exec summary) | arena/ac089f33-lolhotspawn2 | scripts/probe_lines.py (new), scripts/update_picks.py, .github/workflows/line-probe.yml (new), .github/workflows/pipeline-test.yml, data/diag/line_probe.json, docs/methodology.html, research/betting-sources.md §13 |
| T22 Executive summary: explicit in-site "where the picks are" links, a separate unresolved-picks section (counts, per-league limitations, jump links to the filtered rows) | done — header/stats/coverage-meter CSS that was missing is added; separate section now lists every unpriced match, its signal and its limit, with direct links | arena/ac089f33-lolhotspawn2 | docs/index.html, docs/unresolved.html, docs/assets/app.js, docs/assets/style.css |
| T23 Mobile readability pass on the picks views (tap targets ≥44px, full-width primary actions, card layout under 760px, wrapping long league names) | done | arena/ac089f33-lolhotspawn2 | docs/assets/style.css, docs/assets/app.js, docs/*.html |
| T24 Verification, PR to main, merge, Pages deploy confirmation | in progress | arena/ac089f33-lolhotspawn2 | COORDINATION.md, README.md, research/betting-sources.md |

No other session is active. Read-only check before claiming (2026-10-24): `main` = `72c9b5a`, payload 169 fixtures / 169 priced / 9 external-market / 160 model / 0 unresolved; Pinnacle `leagues_seen` contains only `League of Legends - World Championship`, so no accessible book currently prices PRM 2nd/3rd Division, Tunisian Super League, RIVALS LEAGUE, Arabian League 2nd Division, 4 Nations, Komplettligaen, LCP Promotion or LigaGG.


### T21–T23 results (session `arena/ac089f33-lolhotspawn2`, 2026-10-24)

**Starting state (main `72c9b5a`, payload 15:28 UTC):** 169 fixtures · 169 priced · 9 external-market · 160 model · 0 unresolved · 73 low confidence. Pinnacle's own league index contained one LoL league (World Championship), so nothing on the open market priced PRM 2nd/3rd Division, RIVALS LEAGUE, Tunisian Super League, Arabian League 2nd Division, 4 Nations, Komplettligaen, LCP Promotion or LigaGG.

| Check | Result | Evidence |
|---|---|---|
| Live pipeline on branch | success; payload regenerated (164 fixtures at 16:26 UTC) | Actions run 40110923198 (`data/diag/pipeline.log`) |
| Line probe (full) | 39 requests / 30 sites, **0 candidates with new coverage** | run 40110923198 step 8, `data/diag/line_probe.json` |
| Line probe (fast workflow) | success; Kambi country sweep GB/DE/SE/IT/NL/FR/PL/AU/ZZ all return the same 8 World Championship matches | run 40111672023 |
| Verifier | 36 PASS · 0 FAIL · 0 WARN · 1 SKIP | local `python3 scripts/verify_site.py`, CI step 6 |
| Unit tests | verifier 35/35 · entity/books 10/10 · standings PASS · model checks 20/20 | local runs, CI step 6 |
| DOM contract | PASS (43 js ids, 58 page ids) | local + CI |
| jsdom render of all 7 pages | all assertions pass (exec summary: 12 quick rows, 12 league rows, 12 unresolved-league rows, 9 featured cards; unresolved: 12 league rows, 73 low-confidence cards; picks: 169 rows; flagged: 167 rows) | local harness with the real payload |
| New payload field | `line_probe` (checked_at, 30 sites, 39 requests, 0 with coverage, per-candidate verdicts) exposed for the exec summary and Method page | `scripts/update_picks.py` |

**Site defects fixed (found while reviewing the markup against `style.css`):** `docs/index.html` and `docs/unresolved.html` were still using the legacy header markup (`.brand`, `.mark`, `.bar-end`, `.icon-btn`, `.status-strip`), none of which existed in the stylesheet — so the landing page had an unstyled header, a permanently "Loading latest picks…" strip, no freshness indicator, an invisible coverage meter and a dead theme-toggle button. Both pages now use the same styled header as the other five pages, `#updated`/`#freshness` are populated, `.covbar` and `.stat b/span` are styled, and the "Site sections" list is replaced by tappable `linkcard` blocks.

**Flagged (non-blocking, published on Method & Sources and the exec summary):** no accessible source prices the low-tier competitions (the separate Unresolved section states this per competition); Prime League's own rules prohibit betting-operator sponsors, so the organizer page is never an odds source; SofaScore/eGamersWorld/Oddspedia/GGScore/Winamax/Marathonbet/Betano/Stake/GG.Bet/Thunderpick/Rainbet/Rivalry/SportsBetting.ag block CI (403/404/410/503) and are listed with their observed status.

---

## Session `arena/ea9a3e15-lolhotspawn2` — 2026-10-24 (final integration verification)

| Task | Status | Owner | Files (claimed scope) |
|---|---|---|---|
| IV1 Final integration review: re-verify the combined tree line by line (schema, per-row sources, methods, probabilities, counts, unresolved/low-confidence handling, mobile nav, internal links, root redirect, refresh cadence) | done | arena/ea9a3e15 | `scripts/verify_site.py`, `docs/**`, `docs/data/picks.json` |
| IV2 Unit + contract tests | done | arena/ea9a3e15 | `verification/test_verifier.py`, `verification/test_entity_and_books.py`, `verification/test_standings_model.py`, `audit/test_model.py`, `verification/check_dom_contract.py` |
| IV3 Live Pages confirmation: Pages build status, live dashboard render, fresh payload served | done | arena/ea9a3e15 | GitHub Pages API + live `https://karagemop466-tech.github.io/LOLHOTSPAWN2/` |
| IV4 PR from integration branch to `main`, merge, confirm Pages deploy, record PR link + result here | done | arena/ea9a3e15 | COORDINATION.md (board entries only); branch `arena/ea9a3e15-lolhotspawn2` == `main` at `72c9b5a` at claim, so the PR carried this session's COORDINATION.md record only |

### Verification performed this session (local, offline; egress is restricted to GitHub/PyPI so live bookmaker re-checks are done by CI)

| Check | Result | Evidence |
|---|---|---|
| `python3 scripts/verify_site.py` | **36 PASS · 0 FAIL · 0 WARN · 1 SKIP** | D18 SKIP: no `--leaguepedia-schedule` snapshot available offline (CI supplies `data/diag/`; on main this runs as a WARN, never a FAIL — Hotspawn remains authoritative for pick locks) |
| `verification/test_verifier.py` | **35/35** | verifier rule self-tests |
| `verification/test_entity_and_books.py` | **10/10** | entity resolution + bookmaker helpers |
| `verification/test_standings_model.py` | **ALL PASS** | Elo + standings blend |
| `audit/test_model.py` | **20 passed · 0 failed** | de-duplication, prop rejection, standings, market precedence, prior fallback, unresolved |
| `verification/check_dom_contract.py` | **PASS** | all JS-referenced ids present on the 7 pages |
| `node --check docs/assets/app.js` | **OK** | shared JS syntax |
| GitHub Pages API | **`built`** | source: main, path `/`, https enforced, live at https://karagemop466-tech.github.io/LOLHOTSPAWN2/ |
| Recent Actions (all success) | Verify picks and site `40110361789` (2026-10-24 16:10) · Pages build `40107164601` (15:28) · Update picks `40106555419` (15:20) | the 15:20 refresh generated the payload now on `main` |
| Live dashboard fetch | **renders** | executive summary with in-site quick-jump links to picks / by-league / unresolved / flagged / methodology; 169 fixtures, 9 market, 0 unresolved; pick probabilities + source links shown per match; responsive viewport + 6-link bottom nav |

### Payload on `main` / this branch (generated 2026-10-24T15:28:56Z by the scheduled 6h refresh)

169 upcoming Hotspawn LoL fixtures · **169 resolved (100.0%), 0 unresolved** · 9 market-derived (Pinnacle + Unibet + Polymarket, de-duplicated to one line per book: 8 consensus + 1 single) · 160 model-derived (93 MODEL_ELO, 67 MODEL_ELO_THIN) · 0 MODEL_STANDINGS / MODEL_LEAGUE_PRIOR / UNRESOLVED in this window · 73 low-confidence (thin history / cross-league) · 14 cancelled fixtures excluded and listed on Flagged · per-league breakdown: PRM 3rd 61, PRM 2nd 36, Tunisian 25, RIVALS S2 18, Worlds 8, Arabian 2nd 6, 4 Nations 4, Komplettligaen Playoffs 3, LCP 3, LigaGG A 2, LigaGG B 2, LGC Rising 1 · `sources_status`: Pinnacle ok/8, Unibet ok/8, Bovada no_data/0, Polymarket ok/9, Leaguepedia MatchSchedule ok/31752, Leaguepedia Standings ok/2880, Liquipedia no_data/0, Hotspawn lobby ok/169 |

### Sources used (official / verified, links for manual review)

- Hotspawn Pick'em lobby + fixtures API (fixture list only — never a probability input): https://play.hotspawn.com/lol-pickems · https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures
- Pinnacle guest JSON (two-way series moneyline, parent boards only; labelled unofficial): https://guest.api.arcadia.pinnacle.com/0.1 · site https://www.pinnacle.com/en/esports/league-of-legends
- Unibet via Kambi public JSON feed (Match Odds): https://eu-offering-api.kambicdn.com/... · site https://www.unibet.com.au/betting/sports/filter/esports/league_of_legends/all/matches
- Bovada coupon JSON (two-way moneyline): https://www.bovada.lv/services/sports/event/coupon/events/A/description/esports/league-of-legends · site https://www.bovada.lv/sports/esports/league-of-legends
- Polymarket Gamma API (series markets only; Game-N/Map-N child markets never used as series prices): https://gamma-api.polymarket.com · site https://polymarket.com (US trading blocked — reference data only)
- Leaguepedia Cargo MatchSchedule + Standings + TeamRedirects (CC BY-SA 3.0; community-maintained, disclosed as such): https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule · https://lol.fandom.com/wiki/Special:CargoTables/Standings
- Liquipedia MediaWiki API probe only (CC-BY-SA 3.0, gzip, ≥2.2s pacing, API-only per terms): https://liquipedia.net/leagueoflegends/api.php

### Irregularities / flagged items (non-blocking; published on the site's Flagged for Review page)

- D18: amateur-league fixtures where Leaguepedia's recorded schedule disagrees with Hotspawn or lacks the row; Hotspawn epoch-ms governs pick lock times, per-row `START_TIME_MISMATCH` flags attached.
- 14 fixtures cancelled on the Hotspawn feed are excluded from picks and listed with source link (not silently dropped).
- No bookmaker prices tier-3/amateur leagues; those rows are priced by the league-anchored Elo model from Leaguepedia results, labelled Low confidence where history is thin.
- Pinnacle consumed via the public guest front-end feed (unofficial); Bovada returned `no_data` on this run — consensus fell back to healthy sources, source status published per run.
- Polymarket trading is blocked for US users; its prices are reference data only (disclosed on Methodology + Unresolved pages).
- Liquipedia API returned no usable data in this run (rate-limited/blocked); the pipeline degrades gracefully and publishes `no_data`.
- 73 rows are Low confidence (thin history <8 games, cross-league tier comparison, or league prior); these are estimates, not edges, and are flagged per row.
- `MODEL_STANDINGS` / `MODEL_LEAGUE_PRIOR` / `UNRESOLVED` did not appear in this window because every fixture had a rated side; the fallback code paths remain covered by unit tests and the unresolved/limitations section exists for any future window.

### Requirement traceability (all PASS — see `verification/report.json`)

REQ1 pick for every match · REQ2 probabilities sum to 1 · REQ3 no Hotspawn probability input · REQ4 external lines where they exist · REQ5 pick + documented method for every non-market match · REQ6 separate unresolved section with limitations linked from exec summary · REQ7 exec summary links in-site to picks · REQ8 official/trusted source link on every row or flagged unverified · REQ9 mobile-friendly · REQ10 automatic 6h refresh, no manual input · REQ11 no broken internal links, root entry works · REQ12 third-party attribution (Leaguepedia / Liquipedia CC BY-SA 3.0).

### Integration result

Pull request #30 (`arena/ea9a3e15-lolhotspawn2` → `main`) **merged** via `gh pr merge 30 --merge` on 2026-10-24; merge commit `215656b7250d2272490fadeeec777e40d1d238e8`. Pages build for `215656b`: status **`built`** (created 2026-10-24T16:17:47Z, updated 16:18:19Z); `pages build and deployment` workflow **completed success**. Site live at https://karagemop466-tech.github.io/LOLHOTSPAWN2/ serving the merged payload (169 fixtures, 169 resolved, 0 unresolved). PR URL: https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/30

This session (arena/ea9a3e15-lolhotspawn2) is complete: repo reviewed line by line, every table row carries a source link or is flagged unverified, the executive summary links in-site to the picks list and the unresolved section with per-league limitations, the site is mobile-friendly and live, picks cover 100% of Hotspawn's listed LoL fixtures (169/169, 0 unresolved), and the pipeline refreshes automatically every 6 hours with no manual input.

---

## Session `arena/047af680-lolhotspawn2` — 2026-10-24 (integration)

Branch note: fixed branch `arena/047af680-lolhotspawn2`, branched from `main` at `72c9b5a7c27b35dcd346c3d5f955e5ebee9ba727` (branch == main at claim time; all prior T1–T21 work from earlier sessions is already integrated on `main`). Per the branch rule this session works only on `arena/047af680-lolhotspawn2` and pushes only to it; the PR/merge step lands on `main` via `gh`.

| Task | Status | Owner | Files |
|---|---|---|---|
| T20 Line-by-line repo review: scripts, docs, data payload, workflows, verification harness | done | arena/047af680 | scripts/*, docs/*, data/*, .github/workflows/*, verification/*, research/* |
| T21 Confirm end-to-end requirements: pick for every match, separate unresolved section w/ limitations linked from exec summary, mobile dashboard, 4–8h refresh, source link on every row | done | arena/047af680 | docs/*, scripts/update_picks.py, scripts/model.py, scripts/verify_site.py, .github/workflows/update-picks.yml |
| T22 PR to main, merge without waiting, confirm GitHub Pages deploy, record PR link + merge result here | in progress | arena/047af680 | COORDINATION.md (board entries only); PR lands on `main` |

### Verification performed this session (offline; live-source fetches run in GitHub Actions)

| Check | Result | Evidence |
|---|---|---|
| `python3 scripts/verify_site.py` | **36 PASS · 0 FAIL · 0 WARN · 1 SKIP** | `verification/report.json` + `verification/last_report.md` committed this session |
| D18 start-time cross-check vs Leaguepedia | SKIP | no `--leaguepedia-schedule` snapshot available in the sandbox; CI runs it against `data/diag` |
| `python3 verification/test_verifier.py` | **35/35 pass** | self-tests: each rule fails on bad data |
| `python3 verification/check_dom_contract.py` | **PASS** | all JS-referenced ids exist on the seven site pages |
| `node --check docs/assets/app.js` | OK | shared JS parses |
| `docs/data/picks.json` snapshot | **169 fixtures · 169 resolved (100%) · 0 unresolved · 9 market · 160 model (93 MODEL_ELO / 67 MODEL_ELO_THIN) · 73 low confidence · 14 excluded (cancelled)** | local payload `generated_at 2026-10-24T15:28:56.619239Z` |
| Requirements traceability REQ1–REQ12 | **all PASS** | verify_site.py REQ aggregate check |

### Irregularities flagged for review (non-blocking; published on the Flagged for Review page)

- **Bovada `no_data`** this run (0 events returned); consensus fell back to Pinnacle + Unibet + Polymarket. Published per-run in `sources_status`; listed in `scripts/update_picks.py` `CHECKED_UNAVAILABLE`. Not a defect — source status is transparent on the site.
- **Polymarket US access**: Polymarket's homepage states trading is blocked in the United States (view-only). Prices are reference data only; disclosed on Methodology, Unresolved and `research/betting-sources.md`.
- **73 Low-confidence rows**: thin history (<5 games in 365d), cross-league comparisons capped at Low, or one unrated side vs the competition prior. Every row keeps its method label, evidence and source links; none are hidden.
- **14 cancelled fixtures**: excluded from picks with reason + Hotspawn fixtures API link; listed under Excluded on Flagged for review.
- **0 unresolved placeholders** in this snapshot; the separate Unresolved & limitations page and its executive-summary section remain live and would publish any future 50/50 rows with per-league limitations.
- **Sources are best-effort verified**: Pinnacle is consumed via its public guest front-end feed (unofficial; its official API closed 2025-07-23) and flagged as such. Leaguepedia/Liquipedia are community sources under CC BY-SA 3.0, attributed on Methodology — not official organizer odds feeds.

### Sources used (official / verified; links for manual review)

| Source | Used for | Link |
|---|---|---|
| Hotspawn Pick'em lobby / fixtures API | Fixture list, UTC start times, match links (never a probability input) | https://play.hotspawn.com/lol-pickems · https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures |
| Pinnacle guest JSON | 2-way series moneyline (Worlds 2026 etc.) | https://guest.api.arcadia.pinnacle.com/0.1 (site: https://www.pinnacle.com/en/esports/league-of-legends) |
| Unibet (Kambi CDN JSON) | 2-way pre-match Match Odds | https://eu-offering-api.kambicdn.com/offering/v2018/ubca/listView/esports/league_of_legends/all/all/matches.json (site: https://www.unibet.com.au/betting/sports/filter/esports/league_of_legends/all/matches) |
| Bovada coupon JSON | 2-way pre-match moneyline | https://www.bovada.lv/services/sports/event/coupon/events/A/description/esports/league-of-legends (site: https://www.bovada.lv/sports/esports/league-of-legends) |
| Polymarket Gamma API | Prediction-market reference prices | https://gamma-api.polymarket.com/events?tag_slug=league-of-legends&active=true&closed=false |
| Leaguepedia Cargo Export | Recorded results, schedule, standings, canonical names (CC BY-SA 3.0) | https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule |
| Liquipedia MediaWiki API | Compliant tournament metadata index only (CC BY-SA 3.0, gzip, ≥2.2s pacing, HTML never scraped) | https://liquipedia.net/leagueoflegends/api.php?action=query&meta=siteinfo&format=json |

PR/merge record — completed 2026-10-24:

| Item | Value |
|---|---|
| PR number | 32 |
| PR URL | https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/32 |
| Merge method | `gh pr merge 32 --merge` |
| Merge commit | `7b2bab5` (Merge pull request #32 from karagemop466-tech/arena/047af680-lolhotspawn2) |
| Pages build run | latest build created 2026-10-24T16:26:33Z, status `built` (source: main, path `/`) |
| Pages status | **built** — live |
| Live site | https://karagemop466-tech.github.io/LOLHOTSPAWN2/ (serving the merged payload: 169 fixtures, 169 resolved, 0 unresolved; live dashboard render confirmed) |

---

## Session `arena/26fa1cec-lolhotspawn2` — 2026-10-24 (claim)

**Baseline at claim:** `main`/session branch `72c9b5a` (payload generated 2026-10-24T15:28:56Z): 169 scheduled upcoming fixtures · **169 priced (100%)** · 9 market (8 consensus + 1 single) · 160 model (93 `MODEL_ELO` + 67 `MODEL_ELO_THIN`) · 0 `MODEL_STANDINGS` · 0 `MODEL_LEAGUE_PRIOR` · **0 `UNRESOLVED`** · 73 Low confidence · 14 cancelled Hotspawn fixtures excluded. No other session is active on `COORDINATION.md`. No commits by another session on these paths observed in `git log` since 2026-10-23T16:52Z.

| Task | Status | Owner | Files (exclusive scope) |
|---|---|---|---|
| T20 Phone-first executive summary: one consistent header/nav on all 7 pages, a prominent in-site "where the updated picks are" block above the fold, explicit unresolved-picks + limitations section in the executive summary, remove non-functional controls, verify mobile readability | in progress | arena/26fa1cec | `docs/*.html`, `docs/assets/style.css`, `docs/assets/app.js`, `verification/check_dom_contract.py` (only if the contract needs extending) |
| T21 External-source research v2 for fixtures the featured (market) picks cannot price: established books → esportsbooks → betting lines/aggregators → community results; live probe of untried endpoints on every refresh; promote any adapter that shows structured per-match LoL prices, otherwise publish the attempted sources + observed HTTP status + limitation on the site | in progress | arena/26fa1cec | `scripts/source_probe.py` (**new**, added to this claim), `scripts/probe_sources.py`, `scripts/update_picks.py`, `research/betting-sources.md`, `docs/methodology.html`, `docs/unresolved.html`, `README.md` |
| T21b Liquipedia probe fix: `probe_liquipedia_pages()` was called with whole Hotspawn tournament labels as MediaWiki `apprefix`, so it always returned `no_data`; map labels → page prefixes in `update_picks.py` | in progress | arena/26fa1cec | `scripts/update_picks.py` (only this file; `standings_and_books.py` untouched) |
| T22 Integration: full local + CI verification, PR to `main` from this branch, merge, confirm GitHub Pages deploy, record PR/deploy/live-check here | in progress | arena/26fa1cec | `COORDINATION.md`, `verification/**` |

**Scope rule:** this session edits only the paths above. `scripts/fetch_markets.py`, `scripts/fetch_leaguepedia.py`, `scripts/model.py`, `data/aliases.json`, and `.github/workflows/**` are **not** modified; any change needed there is logged as a request instead of edited.

### Results so far (`arena/26fa1cec`, 2026-10-24)

| Item | Status | Evidence |
|---|---|---|
| T20 phone-first summary + unified nav | implemented, verified locally (38 PASS / 0 FAIL / 0 WARN) | `docs/index.html`, `docs/unresolved.html`, `docs/assets/style.css`, `docs/assets/app.js`; new verifier check `S4c` (dedicated `#picks-here` block with 4 in-site links + bound counts) |
| T21 external-source probe on every refresh | implemented; 22 candidates measured live, results published in the payload + site | `scripts/source_probe.py` (new), `scripts/update_picks.py`, `scripts/probe_sources.py`; verifier check `D22` |
| T21b Liquipedia prefix fix | implemented; probe now returns **54 page titles** (was `no_data`) | `scripts/update_picks.py`; `docs/data/picks.json` → `sources_status` |
| Organizer links | substring matching (fixes the missing Komplettligaen row); 3 organizer pages re-verified live 2026-10-24 | `scripts/update_picks.py`; `research/betting-sources.md` §13.3 |
| T22 integration | done (merged via PR #33) | — |

**Live measurements used (run [40111355592](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40111355592), payload `2026-10-24T16:25:23Z`):** 164 upcoming fixtures · 164 priced (100%) · 9 market · 155 model · 0 unresolved · 68 low confidence · 14 cancelled excluded. Probe: 22 candidates, 10 reachable, 5 structured JSON, 3 with LoL references. Pinnacle 200 JSON, Betfair 403, Smarkets 404, Betway 404, BetOnline 200 HTML, Unibet shell 503, GG.Bet 403, Thunderpick 403, Rivalry 503, Midnite 200 HTML, 1xBet 203 (US geo-block confirmed separately), OddsPapi 404 (no key), odds-api.io 200 no LoL, OddsPortal 200 HTML, BetExplorer 404, eGamersWorld 403, Kalshi 200 no LoL series, Manifold 200 futures only, gol.gg 200, bo3.gg 200 (177 LoL references), Riot LoLESports 403, Liquipedia 200. **No new market adapter was justified**: no probed source returned a structured per-match LoL price, and vendor documentation (OddsPapi) excludes every amateur league on Hotspawn's list.

**Irregularities found & fixed this session** (also on the site's Flagged page and in `verification/flagged_items.md` S4–S9):
1. **Clipped header on the executive summary + unresolved page** — `<div class="wrap bar">` collided with the `.bar` probability-bar component (`height:12px; overflow:hidden`), so the brand/nav/theme button were clipped to a 12px strip on phones; `.brand`, `.mark`, `.bar-end`, `.status-strip`, `.nav-list`, `.covbar` and `.stat b` had no CSS at all. Fixed by moving all 7 pages to one header component and adding the missing styles.
2. **Dead `#theme-toggle` button** (no JS handler) — removed; dark mode follows `prefers-color-scheme`.
3. **Liquipedia probe always returned `no_data`** because whole Hotspawn tournament labels were passed as MediaWiki `apprefix`; now mapped to page prefixes (54 pages found).
4. **`probe_sources.py` broke on `retries=0`** (`lib_common.fetch` returns `None`), so the first probe run recorded 22 `AttributeError`s; fixed to a single attempt and the results are now real.
5. **`sources_status` printed “2880 standings across 0 competitions”** (missing `standings_pages` key) — computed from the rows and exposed as `model.standings_pages`.
6. **Komplettligaen organizer link never rendered** (exact-key mismatch: `Komplettligaen 2026 Autumn` vs `… Autumn Playoffs`) — substring matching now; 5 competitions have no verified organizer page and stay blank + flagged rather than guessed.
7. **1xBet is US-geo-blocked** (`https://1xbet.com/en/block`, "Access denied") — its claimed tier-2/3 coverage stays unverified and unused.

**Open items for review (non-blocking, published on the Flagged page):** S8 1xBet geo-block; S7 five competitions without a verified organizer page; S2 probe verdicts are observations only.

### PR / merge / deploy record (`arena/26fa1cec`, 2026-10-24)

| Item | Value |
|---|---|
| Pull request | [PR #33](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/33) — `arena/26fa1cec-lolhotspawn2` → `main` |
| Merge | `gh pr merge 33 --merge` → **MERGED** 2026-10-24T16:30:56Z, merge commit `fb4ad13` |
| Pre-merge branch CI | `pipeline-test.yml` run [40111740168](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40111740168) — **success** (live pipeline + `verify_site.py --check-external` + all unit suites) |
| Post-merge verification on `main` | `verify.yml` run [40111916819](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40111916819) — **success**, all 8 steps (self-tests, offline + external/live-Pages verify, coverage audit, DOM contract) |
| Post-merge production refresh | `update-picks.yml` run [40111916813](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40111916813) — **success**, commit `1901334`, payload `2026-10-24T16:32:38Z`: **160 upcoming fixtures · 160 priced (100%) · 9 market · 151 model · 0 unresolved · 64 low confidence · 18 cancelled excluded · 22 probe rows** |
| GitHub Pages | build [40112050113](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40112050113) — **success**; Pages API `status: built` for `1901334` (16:33:19Z) |
| Live site checked | https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/ — rendered summary shows “📌 Where the updated picks are” with **160 / 25 / 12 / 0 unresolved · 64 low confidence**, the refresh line “Updated … 160/160 listed matches priced (100%)”, and the Unresolved page renders the 22-row external-source table (Pinnacle 200, Betfair 403, BetOnline 200 HTML, 1xBet 203, Kalshi 200 no LoL, Liquipedia 200, …) |

**Follow-up commit (same session):** probe verdict wording is now category-aware (results/metadata pages are no longer
described in odds language) and the probe table labels the type as “Market”/“Results”. No data or probability behaviour changes.

---

## Session `arena/a21e3910-lolhotspawn2` — 2026-10-24 (claim)

Baseline at claim: branch == `origin/main` == `72c9b5a`, payload generated 2026-10-24T15:28:56Z
(169 upcoming fixtures, 169 priced, 0 unresolved, 73 Low confidence, 14 cancelled excluded).
Local baseline before any edit: `scripts/verify_site.py` **36 PASS / 0 FAIL / 0 WARN / 1 SKIP**,
`verification/test_verifier.py` 35/35, `audit/test_model.py` 20/20, `verification/test_entity_and_books.py` 10/10,
`verification/check_dom_contract.py` PASS, `node --check docs/assets/app.js` OK. No other session holds a live
claim on these files (all prior sessions are merged into `main`).

| Task | Status | Owner | Files (claimed scope) |
|---|---|---|---|
| T23 Executive-summary & navigation integrity: fix the broken header/NAV markup introduced on `index.html` + `unresolved.html` (undefined CSS classes `.brand`/`.mark`/`.bar-end`/`.icon-btn`/`.status-strip`/`.nav-list`/`.covbar`, `.bar` height collision clipping the header to 12 px), unify the header across all 7 pages, make the picks path obvious on a phone, add verifier rules for CSS class coverage, duplicate ids and cross-page nav consistency, plus self-tests | done | arena/a21e3910 | docs/index.html, docs/unresolved.html, docs/assets/style.css, scripts/verify_site.py (new rules only), verification/test_verifier.py, verification/check_dom_contract.py |
| T24 Fresh external-source research for matches with no featured line (established books → esportsbooks/esports betting lines → community), with the probe re-run on CI and every claim linked | done | arena/a21e3910 | research/**, scripts/probe_sources.py, data/diag/source_probe.json |
| T25 Integration: re-run the live pipeline on this branch, re-verify line by line, PR to `main`, merge, confirm Pages deploy, record PR/run links here | in progress | arena/a21e3910 | COORDINATION.md, generated payload |

**Files not edited by this session:** `scripts/update_picks.py`, `scripts/fetch_*.py`, `scripts/model.py`,
`.github/workflows/update-picks.yml` (production pipeline behaviour is unchanged; this session only touches the
presentation layer and verification). Any request for those files is logged here instead of implemented.

### T23 / T24 results (arena/a21e3910, 2026-10-24)

> Task ids in this session are T23–T25: `arena/047af680` had already used T20–T22 for its own
> integration pass, so the numbers are kept unique. Files and scope are unchanged.

| Task | Status | Evidence |
|---|---|---|
| T23 Executive-summary & navigation integrity | **done** | `docs/index.html`, `docs/unresolved.html`, `docs/assets/style.css`, `docs/assets/app.js`, `docs/match.html`, `scripts/verify_site.py`, `verification/test_verifier.py`, `verification/render_check.cjs` |
| T24 Fresh external-source research for non-featured matches | **done** | `research/betting-sources.md` §13, `scripts/probe_sources.py`, `data/diag/source_probe.json`, `docs/methodology.html` (`#low-tier-sources`), `docs/flagged.html` (`#source-coverage-flags`) |
| T22 Integration | in progress | this branch |

**Defect found and fixed (T23).** `docs/index.html` and `docs/unresolved.html` (rewritten by an earlier session) shipped a
header using `.brand`, `.mark`, `.bar-end`, `.icon-btn`, `.status-strip` — none of which exist in `style.css` — inside a
`<div class="wrap bar">`. `.bar` is the 12 px coverage/probability bar, so jsdom computed the executive summary header as
`height: 12px; overflow: hidden`: the site title, freshness timestamp and **all six navigation links were clipped**.
The same pages also used `.nav-list` and `.covbar`, which had no CSS either, and `match.html` highlighted no nav item.
Fixes: both pages were given the shared header/nav markup; the missing `.covbar` rule was added; `match.html` now
marks *All picks* current; the dead `#theme-toggle` button (no handler anywhere in `app.js`) was removed. When
`origin/main` was later merged, session `arena/26fa1cec` had independently replaced those two headers with the same
shared markup plus a richer “📌 Where the updated picks are” block (counts for all / next-24h / leagues / unresolved /
low-confidence). That version was adopted as the base, this session's duplicate `#picks-cta` strip and its now-unused
`.cta-strip`/`.nav-list` CSS were removed, and the duplicate `.covbar` rule was dropped in favour of main's.

**New verification rules.** `S11` — every class a page uses must have a rule in `style.css` (this is the check that
would have caught the clipped header). `S12` — all pages share one primary nav and one phone bottom nav (same targets,
same order), every page carries the `#updated`/`#freshness` slot, and no page has duplicate ids. `S10` no longer
overwrites `S3`'s findings (it reused `nav_bad`, which silently forced S3 green). Rules are self-tested with synthetic
bad pages (`verification/test_verifier.py`, now **42/42**). New `verification/render_check.cjs` executes the real
`app.js` against the real payload in jsdom on all 7 pages and asserts that rows/cards/tables actually render, that no
loading placeholder is visible, that `#error-box` is empty and that the header is not a fixed-height strip; it skips
cleanly when jsdom is absent and is wired into `pipeline-test.yml` and `verify.yml`.

**Verification performed (local, payload 2026-10-24T16:27:29Z):** `verify_site.py --leaguepedia-schedule data/diag`
→ **38 PASS / 0 FAIL / 1 WARN / 0 SKIP** (WARN = `D18`, 10 fixtures whose Hotspawn time differs from a >24 h old
Leaguepedia snapshot; snapshot age is stated in the check). `test_verifier.py` 42/42 · `audit/test_model.py` 20/20 ·
`test_entity_and_books.py` 10/10 · `check_dom_contract.py` PASS · `node verification/render_check.cjs` PASS on all 7
pages · `node --check docs/assets/app.js` OK. Payload row audit: 164/164 rows have a Hotspawn + Leaguepedia source
link, every pick equals the higher probability, probabilities sum to 1, all URLs https.

**Live source checks (T21), each with the link that was fetched:** Pinnacle's esports feed lists **only**
`League of Legends - World Championship` (id 9587) → no sharp line exists for the other 11 competitions
(https://guest.api.arcadia.pinnacle.com/0.1/sports/12/leagues); Pinnacle's `LYON vs Karmine Corp` start
20:00 UTC matches our row (https://guest.api.arcadia.pinnacle.com/0.1/leagues/9587/matchups); Polymarket
`lol-tes-al-2026-10-24` showed 37¢/64¢ vs our 0.365/0.635
(https://polymarket.com/event/lol-tes-al-2026-10-24); Betmonitor exposes a **Prime League 2nd Division**
comparison page (bet365/ggbet) but renders client-side; OddsPapi is key-gated (0 fixtures scheduled at the
04:15Z measurement). CI probe run
[40111023039](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40111023039) re-measured 20
candidates: Betmonitor 200/HTML, EsportBet 200/HTML, EsportsBets 200/HTML, bo3.gg 200/HTML, gol.gg 200/HTML,
Riot LoL Esports API 403 (needs `x-api-key`), OddsPapi 200/HTML, plus the 13 earlier candidates unchanged
(GG.Bet/Thunderpick/eGamersWorld 403, Rivalry/Unibet 503, Betway/BetExplorer/Smarkets 404). **No new
machine-readable per-match feed was found**, so the non-featured rows keep our own line and every page says so.

**Irregularities published (non-blocking):** F13.1 Betmonitor prices PL2 but is browser-only and unverified —
not used; F13.2 OddsPapi key-gated — no data used; F13.3 Polymarket's resolution text says 7:00 PM ET while its
own countdown and the Hotspawn/Leaguepedia schedule say 17:00 UTC (row already carries
`START_TIME_DISAGREES_WITH_BOOKS`); F13.4 Pinnacle has no LoL league beyond Worlds (upstream cause of 155
model-priced rows). All four are on **Flagged for review** (`#source-coverage-flags`) with their source links,
and the same evidence is in `research/betting-sources.md` §13 and on Methodology (`#low-tier-sources`).

**Merge note (2026-10-24, after `origin/main` advanced to `fc1d438`/PRs #33–#34):** `origin/main` gained session
`arena/26fa1cec`'s work (production `scripts/source_probe.py` with 21 candidates published as `market_probe`, a
“Where the updated picks are” exec-summary block, category-aware probe verdicts) while this session was running.
The merge kept **all** of it: `docs/index.html`, `docs/unresolved.html`, `docs/assets/app.js`,
`scripts/probe_sources.py`, `README.md` and `research/betting-sources.md` use main's structure, with this session's
four extra candidates (Betmonitor ×2, EsportBet, EsportsBets) added to `scripts/source_probe.py`, its `#low-tier-sources`
table kept on Methodology and its `F14.1–F14.4` flags kept on Flagged. This session's research section was renumbered
**§14** (main had already written §13) and all cross-references updated. Nothing from the other session was discarded.
After the merge the verifier runs **40 PASS / 0 FAIL / 0 WARN / 1 SKIP** and `render_check.cjs` passes on all 7 pages
against the merged payload (160 fixtures, generated 2026-10-24T16:39Z). Task ids for this session are T23–T25 because
`arena/047af680` had already used T20–T22.

---

| Item (continued) | Value |
|---|---|
| Follow-up PR | [PR #34](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/34) — **MERGED** 2026-10-24T16:36:32Z, merge commit `5d71d0b`; `verify.yml` [40112346967](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40112346967) success; Pages build [40112346904](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40112346904) success |
| Production refresh after #34 | `update-picks.yml` [40112346993](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40112346993) — success, commit `fc1d438`, payload `2026-10-24T16:40:07Z`: 160 fixtures · 160 priced (100%) · 9 market · 151 model · 0 unresolved · 64 low confidence · 22 probe rows (8 reachable this run) |
| Live checks on production | summary renders the 4 picks cards (160 / 25 / 12 / 0 unresolved · 64 low) + refresh line; `picks.html?filter=next24` renders 25 of 160 rows with both win probabilities, ✅ pick pill and source links; `unresolved.html#sources-checked` renders the 22-row probe table |

**Irregularity 8 (fixed):** two-way percentages were rounded independently, so two rows displayed **99.9%**
(e.g. JSK Academy 50.7% + New Era Team 49.2%) and market rows could display 100.1%. `pctPair()` in
`docs/assets/app.js` now rounds the first side and derives the second from 100 − first, so every displayed pair
sums to exactly 100.0%. Stored probabilities were always correct (`D4` tolerance) — this was display-only.
Verified with a jsdom pass over all 160 rendered rows: 160/160 pairs sum to 100.0%.

---

## Session `arena/607dddb0-lolhotspawn2` — 2026-10-24 (live sportsbook & wiki forensic audit: Bovada 8-match restoration, `Inari Esports` entity repair, 404 URL elimination, Liquipedia API normalization & 6h CI hardening)

> Branch & coordination note: Fixed session branch `arena/607dddb0-lolhotspawn2` (integrated cleanly with `origin/main` through PRs #33 & #34 `5d71d0b`, preserving 100% of all prior sessions' entries and code). Scope restricted strictly to unclaimed files (`data/aliases.json`, `scripts/entity_resolution.py`, `scripts/fetch_markets.py`, `scripts/standings_and_books.py`, `.github/workflows/update-picks.yml`, `research/line-by-line-audit-2026-10-24.md`, `COORDINATION.md`).

| Task | Status | Owner | Exclusive file scope |
|---|---|---|---|
| T34 Tournament/entity alias & 100% Leaguepedia provenance repair: map `4 Nations 2026 Halloween Heist`, `Komplettligaen 2026 Autumn Playoffs`, `PRM 1st Division 26-27 Fall`, `Arabian League 2nd Division 2026 Fall Playoffs`, and fix `Inari Esports` -> `Inari Esports (British Team)` (`1081700` was previously mis-resolved to unrelated `NARI` via 4-letter substring containment, producing `GENERIC_RESULTS_SOURCE`) | done (CI verified `40111870194`, `40112196096`) | arena/607dddb0 | `data/aliases.json`, `scripts/entity_resolution.py` |
| T35 Live sportsbook & Liquipedia restoration: (1) restore Bovada from `no_data (0)` to `ok (8)` by querying `/description/esports` filtered to LoL coupon groups, accepting Bovada's `period={"description":"Game","main":true}` series moneyline while rejecting `Map N`/`Game N` sub-boards, and prefixing `/sports` on event URLs (`200 OK`); (2) replace 404 `www.pinnacle.com/en/esports/league-of-legends` with `200 OK` Arcadia JSON URLs; (3) normalize/deduplicate Liquipedia `api.php` prefixes (`≤8` queries, `status: "ok"`) | done (CI verified `40111870194`, `40112196096`) | arena/607dddb0 | `scripts/fetch_markets.py`, `scripts/standings_and_books.py` |
| T36 Scheduled 6h workflow hardening: add `data/aliases.json` to `update-picks.yml` push trigger and discard unstaged `verification/` reports before the `git merge -X ours` push-retry loop | done | arena/607dddb0 | `.github/workflows/update-picks.yml` |
| T37 Full line-by-line 2026-10-24 live external source audit (`research/line-by-line-audit-2026-10-24.md`), CI branch verification (`pipeline-test.yml`), PR → `main`, merge & Pages confirmation | done | arena/607dddb0 | `research/line-by-line-audit-2026-10-24.md`, `COORDINATION.md` |

### Irregularities discovered & fixed during live external audit (`2026-10-24`)
- **I20 (FIXED — wrong entity disambiguation & `GENERIC_RESULTS_SOURCE` on fixture `1081700`):** `Inari Esports vs Bulldog Esports` (`4 Nations 2026 Halloween Heist`, `2026-10-26T19:00:00Z`) resolved `"Inari Esports"` to unrelated team `NARI` (`"nari"` substring inside `"inariesports"`), missing Leaguepedia's official schedule row (`Inari Esports (British Team)` vs `Bulldog Esports`, `BestOf: 3`, Round 2) at <https://lol.fandom.com/wiki/4_Nations/2026_Season/Halloween_Heist>. Fixed in `data/aliases.json` + `scripts/entity_resolution.py` with `HOTSPAWN_NAME_COLLISION` flag (`GENERIC_RESULTS_SOURCE` reduced to **0** across all 160 fixtures).
- **I21 (FIXED — Bovada triple-bug caused false `no_data (0)` despite 8 live Worlds moneylines):** `/description/esports/league-of-legends` returns `{}`, whereas `/description/esports?marketFilterId=def&preMatchOnly=true&lang=en` returns HTTP `200 OK` with all 8 `World Championship '26` LoL moneylines (`path` includes `/esports/league-of-legends`). In addition, `fetch_bovada()` previously rejected `period.description == "Game"` (`main: true`) and built `/esports/...` links (HTTP 404) instead of `/sports/esports/...` (HTTP 200). Verified live in CI runs `40111870194` & `40112196096`: Bovada `ok (8)`, upgrading all 8 Worlds matches to **4-source consensus** (`Pinnacle + Unibet + Bovada + Polymarket`).
- **I22 (FIXED — Pinnacle 404 URL & Liquipedia prefix normalization):** Replaced 404 `https://www.pinnacle.com/en/esports/league-of-legends` with `200 OK` `https://guest.api.arcadia.pinnacle.com/0.1/matchups/{mid}/markets/related/straight` (`X1`: `0 dead 404/410` in CI) and normalized `probe_liquipedia_pages()` to verified Liquipedia `apprefix` strings (`ok`).

### PR / merge / live GitHub Pages deployment record (`arena/607dddb0`, 2026-10-24)

| Item | Result & Evidence |
|---|---|
| Pull request | [PR #35](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/35) — `arena/607dddb0-lolhotspawn2` → `main` |
| Merge | `gh pr merge 35 --merge` → **MERGED** `2026-10-24T16:40:53Z`, merge commit `0b822dd1a5ab677740528745e5120addcb54803d` |
| Pre-merge branch CI | `pipeline-test.yml` runs [40111870194](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40111870194) (`1m34s`) & [40112196096](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40112196096) (`3m23s`) — **100% green** (`verify_site.py --check-external` `X1: 0 dead 404/410` + all unit suites) |
| Post-merge verification on `main` | `verify.yml` run [40112685479](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40112685479) — **success** |
| Post-merge production refresh on `main` | `update-picks.yml` run [40112685473](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40112685473) — **success** (`1m36s`), commit `d5e3127`, payload `2026-10-24T16:42:29.066048Z`: **160 upcoming fixtures · 160 resolved (`100.0%`) · 0 unresolved · 9 market (`8` 4-book Worlds consensus + `1` single Polymarket) · 151 Elo model (`94` `MODEL_ELO` + `57` `MODEL_ELO_THIN`) · `8/8` `sources_status` `ok` (`Bovada: ok/8`, `Liquipedia: ok`) · `0` `GENERIC_RESULTS_SOURCE`** |
| GitHub Pages builds | [40112685075](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40112685075) & post-refresh [40112807856](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40112807856) — **success**, Pages API `status: built` for `d5e3127` (`2026-10-24T16:43:03Z`) |
| Live site verification | Live checks on <https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/>, `match.html?id=1067688` (4-book consensus: Pinnacle + Unibet + Bovada + Polymarket with `200 OK` links), and `match.html?id=1081700` (`Inari Esports (British Team)` Bo3 on `4 Nations/2026 Season/Halloween Heist`) all confirmed live. |

---

## Session `arena/c38ce482-lolhotspawn2` — 2026-10-24 (standings blend → PR #38)

**Root cause found and fixed.** The split-standings signal — the only *community* source that prices tier-3
fixtures where no book does — was fetched but never applied, because `MODEL_STANDINGS` required a side with
**no Elo at all**, while Elo needs only one recorded game in 365 days. Every priced side therefore always had
an Elo rating, so the standings branch was unreachable: **0 rows across every production run**.

| Fix | Detail |
|---|---|
| New method `MODEL_ELO_STANDINGS` | A side with **thin** Elo (<8 games in 365d) **and** a current-split standings record **for this row's own competition** has that record blended into the rating. Weight `series/(series+4)`, capped at 0.6 so pooled Elo still dominates. Flagged `STANDINGS_BLEND_APPLIED`; confidence ≤ Medium (Low when cross-league). A record from a **different** competition is never blended in. |
| `standings_pages` counter | `fetch_leaguepedia.py` never emitted it, so the site printed "Standings rows: 2 880 across **0** competitions". Now computed from the distinct `OverviewPage` values → **209** competitions. |
| Accurate per-league limitation text | Names only the signals that actually priced the competition, instead of always claiming "recorded match results **and split standings**". |
| Standings source link | Standings rows cite the competition's **own** page (e.g. `RIVALS_LEAGUE/2026_Season/Season_2`), not the generic `Special:CargoTables/Standings` index, so check `D8d` keeps its meaning instead of being weakened. |
| `D18` reads the live cache | The start-time cross-check now uses `data/cache/leaguepedia.json`, written by the same run that priced the model, instead of committed `data/diag/ms_*.json` snapshots that were **67.8 h old** and could not verify the current schedule. |
| Exec summary per-league limitations | The executive summary carries the per-league limitations table itself, and reads correctly whether or not anything is unresolved ("0 fixtures lack …" was confusing). |
| New DOM render regression test | `verification/check_dom_render.js` renders all six pages against the published payload in jsdom and asserts every content container was filled. Wired into `pipeline-test.yml` (skips cleanly when jsdom is unavailable). |

**Measured effect** (live pipeline, Actions 40112986629, payload `2026-10-24T16:46:33Z`):

| Metric | Before | After |
|---|---|---|
| Fixtures priced by the standings signal | **0** | **55** |
| `MODEL_ELO_THIN` rows | 67 | **2–3** |
| Low-confidence rows | 73 | **9** |
| Unresolved (explicit 50/50) | 0 | **0** |
| Coverage of the Hotspawn lobby | 100 % | **100 %** |

Example row (`RIVALS LEAGUE Season 2`, 2026-10-24): Karolinerna 41.9 % vs Turbo Gaming 58.1 %. Pooled Elo
1466 vs 1491 blended with the current-split record (1–4 series vs 4–2 series) to 1388 vs 1528 — source:
https://lol.fandom.com/wiki/RIVALS_LEAGUE/2026_Season/Season_2

**Verification performed**

| Check | Result | Evidence |
|---|---|---|
| Live pipeline + verifier on the branch | **success**, **38 PASS / 0 FAIL** (was 1 FAIL on the first attempt) | Actions run 40112986629; `verification/last_report.md` (52 PASS rows) |
| `verification/test_standings_model.py` | **17/17** (8 new: blend fires, favours the stronger split record, records the weight, is flagged, confidence ≤ Medium, an out-of-competition record is **not** blended, a deep Elo pair is not overridden) | `verification/test_standings_model.py` |
| `audit/test_model.py` | **23/23** (2 new: blend weight in [0, 0.6]; standings rows cite a standings source and a competition-specific page) | `audit/test_model.py` |
| `verification/test_verifier.py` | 38/38 | unchanged |
| `verification/test_entity_and_books.py` | 10/10 | unchanged |
| `verification/check_dom_contract.py` | PASS | unchanged |
| `verification/check_dom_render.js` (new) | all 6 pages render, 0 empty containers | run locally + in `pipeline-test.yml` |
| `D8d` regression | violations 59 → 0 after the source-link change | simulated against the CI payload before the fix landed |
| `D18` start-time cross-check | **now PASS**: 139/139 matched fixture times agree with Leaguepedia, 0 differ, snapshot 0.0 h old | `verification/last_report.md` |

**Irregularities flagged for review (non-blocking, on the Flagged page / `research/betting-sources.md` §14)**

- `MODEL_ELO_STANDINGS` rows are Medium confidence, not Low: the split record is in-competition evidence but
  ignores strength of schedule and roster changes.
- The committed `data/diag/ms_*.json` snapshots remain as the D18 fallback and are stale by nature; the live
  cache is now preferred.
- `X1` still WARNs on one link: `Special:CargoTables/MatchSchedule` returns **403** to the verifier's bot
  User-Agent (Fandom bot protection). It is 0 dead links; the link is a table index, not a dead page.
- `D18` still notes that Hotspawn's epoch timestamp governs pick lock times when Leaguepedia disagrees.

**Coordination note.** This session was rebased onto `main` repeatedly while other sessions merged PRs
#30–#39. Every `COORDINATION.md` conflict was resolved by keeping **both** session blocks (the board is
append-only); the resolver is committed at `scripts/resolve_coordination_conflict.py`. No other session's work
was discarded at any point. `research/betting-sources.md` §13 (session `arena/26fa1cec`) and §14 (this
session) are both present and renumbered so the section numbers stay unique.

### T24 merge reconciliation (session `arena/ac089f33-lolhotspawn2`, 2026-10-24 ~17:0x UTC)

While this session was running, `main` advanced (`72c9b5a` → `a5f1c8a`, PRs #36–#39 and three scheduled
refreshes). Two of those sessions solved the same two problems independently, so this session reconciled
rather than duplicated:

| Overlap | Resolution |
|---|---|
| Session `arena/a21e3910` / `26fa1cec` built `scripts/source_probe.py` + the `market_probe` payload key and rendered a source-by-source table (`#sources-status`, `unresolved.html#sources-checked`) — a reachability probe that runs in every 6-hour production refresh | **Adopted as the single production probe.** This session's `line_probe` payload field, its exec-summary card and its Method-page table were removed to avoid two competing probe surfaces; `scripts/probe_lines.py` is kept as the deeper **fixture-matched coverage** probe (it is the only thing that answers "would this source price a row we currently price ourselves"), runs from its own `.github/workflows/line-probe.yml`, and is no longer part of `pipeline-test.yml`. |
| Session `arena/c38ce482` + `26fa1cec` already delivered the "Where the updated picks are" cards with counts (`#picks-here`), the per-league limitations table on the exec summary (`#exec-league-limits-body`), the fixed `.covbar`/`.stat` styling and the jsdom render check (`verification/check_dom_render.js`) | **Adopted `main`'s `docs/**` wholesale.** This session's equivalent markup/JS was dropped, not merged, to keep one implementation. Two additive mobile rules that `main` still lacked were kept: `details > summary { min-height: 44px }` and full-width `.hero-actions .btn` under 640 px. |

Unique contributions kept from this session: `scripts/probe_lines.py` + `data/diag/line_probe.json`,
`.github/workflows/line-probe.yml`, the 11 new `CHECKED_UNAVAILABLE` rows and the re-test `LIMITATIONS`
entry in `scripts/update_picks.py`, `research/betting-sources.md` §15, and the README line-source section.

**Verified on the merged tree (local):** `scripts/verify_site.py` → 40 PASS · 0 FAIL · 0 WARN · 1 SKIP;
`check_dom_contract.py` → PASS; `test_verifier.py` → 45/45; `test_standings_model.py` → PASS;
`test_entity_and_books.py` → 10/10; `audit/test_model.py` → 23/23;
`node verification/check_dom_render.js` → all 6 pages render with content (0 containers left loading).

---

---

## Session `arena/f0a8380a-lolhotspawn2` — 2026-10-24 (structural `Resolver` short-tag & disambiguation hardening + full line-by-line verification)

### Claimed tasks (`F1`–`F4`)
- **F1 — Structural entity-resolution hardening (`scripts/model.py`)**:
  - Audited all non-exact entity resolutions across the entire Hotspawn fixture slate and identified the root cause of the `1081700` (`4 Nations 2026 Halloween Heist`: `Inari Esports vs Bulldog Esports`) false match: `contains(a, b)` in `scripts/model.py` previously accepted any substring (`na in nb or nb in na`), allowing 4-character SEA tag `"NARI"` (`"nari"` in `"inariesports"`) to beat `"Inari Esports (British Team)"` whenever an explicit alias was absent.
  - Hardened `contains(a, b)` in `scripts/model.py` to require `len(short) >= 5` for non-identical substring matching, preventing 3–4 character team tags (`"NARI"`, `"TES"`, `"BLG"`, `"GEN"`, `"PNS"`) from substring-matching inside unrelated multi-word team names.
  - Added stripped-parenthetical disambiguation resolution (`_strip_disambig`: `"Inari Esports (British Team)" -> "Inari Esports"`, `"Locked In (Dutch Team)" -> "Locked In"`, `"Rich Gang (Norwegian Team)" -> "Rich Gang"`) to `Resolver.resolve_with_meta` ahead of substring fallback, and synced `DEFAULT_ALIASES` in `scripts/model.py` (`"Inari Esports": "Inari Esports (British Team)"`, `"4 Nations 2026 Halloween Heist"`, `"Komplettligaen 2026 Autumn Playoffs"`, `"EM 2026 Summer Main Event"`).
- **F2–F4 — Regression tests & end-to-end verification (`verification/test_entity_and_books.py`)**:
  - Added 3 unit tests in `verification/test_entity_and_books.py` (`13/13` passing) verifying that `contains("Inari Esports", "NARI")` is `False`, `Resolver` resolves `"Inari Esports"` to `"Inari Esports (British Team)"` even when `"NARI"` is in the candidate pool and no explicit alias is passed, and `tournament_pages` maps `"4 Nations 2026 Halloween Heist"` and `"Komplettligaen 2026 Autumn Playoffs"`.
  - Integrated concurrent merges on `main` (PRs #32–#39) without discarding any session's work.
  - Verified all automated suites on the merged tree:
    - `python3 scripts/verify_site.py`: **40 PASS · 0 FAIL · 0 WARN · 1 SKIP** (`REQ1`–`REQ12` all PASS; 160 upcoming fixtures, 160 resolved `100.0%`, 0 unresolved, 9 external market rows, 151 model rows including 55 `MODEL_ELO_STANDINGS` rows)
    - `python3 verification/test_verifier.py`: **45/45** self-tests passed
    - `python3 verification/check_dom_contract.py`: **PASS** (48 JS target IDs, 76 page IDs across 7 HTML pages)
    - `python3 audit/test_model.py`: **23/23** passed
    - `python3 verification/test_standings_model.py`: **18/18** passed
    - `python3 verification/test_entity_and_books.py`: **13/13** passed


**Merge reconciliation (2026-10-24, `arena/66e731b3`):** `main` advanced through PRs #32–#43 (sessions `26fa1cec`/`c38ce482`/`a21e3910`/`f0a8380a`: shared-header fix + S11/S12, `MODEL_ELO_STANDINGS` blend, `market_probe`/`source_probe.py`, Resolver hardening, DOM render tests) while this branch was in flight. Merged `origin/main` (`f5734a8`) into this branch, 18 conflicts resolved without discarding any session's work: generated payloads/reports took main's (CI regenerates); site pages/`app.js` adopted main's newer render-tested versions (this session's header diagnosis matched flagged S4/S5; its exec-summary rewrite was superseded by main's `#picks-here` cards + per-league limits + probe strip); Bovada kept this session's stricter `_bovada_series_moneyline` + snapshot-replay tests grafted with main's LoL-path filter, open-status guard and URL builder (both sessions fixed the same period-`Game` bug independently; merged replay 9/9); probe candidates from this session (SportsBetting.ag, TonyBet, BC.Game, Stake, PandaScore no-token, Oracle's Elixir) migrated into `scripts/source_probe.py` (32 candidates), `probe_sources.py` kept as main's wrapper; `checked_unavailable` +3 official-doc entries and the key-only-vendor limitation (now citing §15) kept; research section renumbered **§15** (main already used §13/§14) with the standings-blend item rewritten as reconciled + flagged U4; CI `pipefail` retained in all three generator workflows. Merged tree locally: `verify_site.py` **40 PASS/0 FAIL/0 WARN/1 SKIP**, verifier 45/45, DOM contract PASS, entity/books **17/17**, standings ALL PASS, audit 23/23, jsdom `render_check.cjs` PASS (all 7 pages).

---

### PR & GitHub Pages Deployment Record (`arena/f0a8380a-lolhotspawn2`)
| Item | Value |
|---|---|
| Pull Request | [PR #43](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/43) (`arena/f0a8380a-lolhotspawn2` → `main`) — **MERGED** (`2026-10-24T16:53:05Z`, merge commit `5a7d73f6ffc51194d58548c44f50e0e6f77597d0`) |
| Post-merge pipeline refresh on `main` | `update-picks.yml` run [40113603161](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40113603161) — **success** (`1m41s`), commit `f5734a89986d9276bbc3a08dedb01e96c89a241c`, payload `2026-10-24T16:54:25.197732Z`: **160 upcoming fixtures · 160 resolved (`100.0%`) · 0 unresolved · 9 external market rows · 151 model rows** |
| GitHub Pages deployment | `pages-build-deployment` run [40113723631](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40113723631) — **success**, Pages API `status: "built"` for commit `f5734a89986d9276bbc3a08dedb01e96c89a241c` (`2026-10-24T16:56:49Z`, duration `123.8s`) at <https://karagemop466-tech.github.io/LOLHOTSPAWN2/> |



### T24 PR & deployment record (session `arena/ac089f33-lolhotspawn2`)

| Item | Result | Evidence |
|---|---|---|
| Pull request | **PR [#42](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/42)** — `arena/ac089f33-lolhotspawn2` → `main` | https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/42 |
| Merge | `gh pr merge 42 --merge` → **MERGED** 2026-10-24T16:58:59Z, merge commit `633a273` | GitHub PR record |
| Branch CI before merge | **success** — live pipeline, unit suites, `verify_site.py --check-external`, DOM contract, probe (`Pipeline test (branch verification)` run 40113728002, head `f1506ac`) | Actions run 40113728002 |
| Post-merge verify on `main` | **success** | Actions run 40114030726 |
| Pages deployment | **built** for `633a273c7c5a2dd0288c758460a3925c7d2c4293` at 2026-10-24T16:59:46Z | `GET /repos/.../pages/builds/latest` |
| Live executive summary | renders the freshness line ("Updated Sat, Oct 24, 12:54 PM · next refresh 22:54 UTC · 160/160 listed matches priced"), the four "Where the updated picks are" cards with counts (160 matches / 25 next-24h / 12 competitions / 0 unresolved · 9 low confidence), the coverage reconciliation block and the separate unresolved/limitations section with per-competition limits | https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/ |
| Live payload | `generated_at` 2026-10-24T16:58:27Z · 160 fixtures · 160 priced · 9 external-market · 151 model (55 blended with split standings) · 0 unresolved · 9 low-confidence · `market_probe` 26 sources · `checked_unavailable` 24 rows (11 added here) · 11 limitations (1 added here) | https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/data/picks.json |
| Live stylesheet | serves this session's final mobile rules (`details > summary { min-height: 44px }`, full-width `.hero-actions .btn` under 640 px) | https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/assets/style.css |
| Line-probe evidence | committed; 39 requests / 30 sites / 0 with coverage | `data/diag/line_probe.json`, `research/betting-sources.md` §15 |
| Next automatic refresh | 6-hour schedule (`0 */6 * * *`) continues on `main`; no manual input required | `.github/workflows/update-picks.yml` |

### Irregularity found on the live site after the #42 deploy (session `arena/ac089f33-lolhotspawn2`)

**What:** the executive summary and the unresolved page reported a pricing breakdown that did not add up.
Live text on `633a273`: "9 from external betting lines, 41 from our chronological Elo model, 55 from split
standings, 0 from competition priors, 0 placeholders" — 105 of 160 fixtures. The unresolved page separately
said "**0** by split standings" while its own per-league table showed 19 + 4 + 18 … standings rows.

**Cause (verified against the payload and `docs/assets/app.js`):**
1. `stCount` read `cov.with_standings_model`, which the generator does not emit, so it fell back to
   `counts.standings`; the Elo figure was then computed as `with_team_specific_model - stCount`
   (96 − 55 = 41) — subtracting one signal from another.
2. `nStand` counted only `MODEL_STANDINGS` and ignored `MODEL_ELO_STANDINGS`, the method the current
   generator actually emits for 55 fixtures (`{"MARKET_CONSENSUS": 8, "MARKET_SINGLE": 1, "MODEL_ELO": 94,
   "MODEL_ELO_THIN": 2, "MODEL_ELO_STANDINGS": 55}`).

**Fix:** a single `pricingMix()` helper in `docs/assets/app.js` counts the mix from the rows themselves
(market / `MODEL_ELO`+`MODEL_ELO_THIN` / `MODEL_STANDINGS`+`MODEL_ELO_STANDINGS` / `MODEL_LEAGUE_PRIOR` /
`UNRESOLVED`), and both pages render from it, printing the total so a mismatch is visible immediately.
Rendered result with the current payload: **9 + 96 + 55 + 0 + 0 = 160**.

**Verified:** `node verification/check_dom_render.js` → all pages render; `python3 scripts/verify_site.py` →
40 PASS · 0 FAIL · 0 WARN · 1 SKIP; `test_verifier.py` 45/45; `check_dom_contract.py` PASS.

---

**Second merge reconciliation (2026-10-24, `arena/66e731b3`):** merged `origin/main` again after PR #41 (`arena/e6f33fe9`: fixture-matched `probe_lines.py`, S13–S15, jsdom render gate) + scheduled refresh `6017b92`. Kept both sessions' `checked_unavailable` additions (their 9 fixture-matched entries + this session's 3 official-doc entries); research renumbered to **§17** and appended after main's §15/§16; generated files took main's pending CI regeneration. Twice-merged tree locally: `verify_site.py` **43 PASS/0 FAIL/0 WARN/1 SKIP**, verifier 45/45, DOM PASS, entity/books 17/17, standings ALL PASS, audit 23/23, JS syntax OK. Branch pipeline on the first merged tree (run `40114283132`, payload 2026-10-24T17:05Z) was **success**: 159/159 resolved, 0 unresolved, `checked_unavailable` 18 published, `market_probe` 32 sources (this session's 6 new candidates measured live: TonyBet/BC.Game 200 HTML-only; SportsBetting.ag/Stake/PandaScore/Oracle's Elixir 403).

---

### Hotfix `arena/e6f33fe9` — conflicted generated artifacts reached `main` (2026-10-24 17:0x UTC)

**What happened.** While integrating `origin/main` twice (twice within minutes, because other sessions were
merging concurrently), three machine-written files were committed with git conflict markers still in them:
`docs/data/picks.json`, `data/diag/source_probe.json` and `data/diag/pipeline.log`. `picks.json` was the
serious one: the dashboard's payload was unparsable, so `verify_site.py` **D1** failed and the post-merge
`Verify picks and site` run on `main` (**40114322258**) went red in 7s; the Pages deployment that followed
published a dashboard that could not load its data.

**How it was detected.** The failing run had no retrievable log (the job-log blob endpoint returned EOF, the
same limitation earlier sessions hit), so the merged tree was reconstructed with `git archive origin/main`
and the verifier suite was run locally against it — that reproduced D1 immediately.

**How it was fixed.** The 6-hour `update-picks` run (**40114322196**, success) regenerated `picks.json` and
`pipeline.log` from the live pipeline, which healed both. `data/diag/source_probe.json` is *not* rewritten
when a probe newer than 30 minutes already exists, so it stayed broken; this branch restores it from the last
clean commit (`9ad7c10`) and adds a permanent guard.

**New guard — verifier check `D23`.** Every file under `docs/`, `data/`, `verification/`, `research/`,
`scripts/` and `.github/` is scanned for `<<<<<<<` / `=======` / `>>>>>>>` markers, and the check **fails the
run** if any is found. Verified non-vacuous: planting a marker file turns D23 red, removing it turns it green.

**Lesson recorded for future integration sessions.** Generated artifacts (`docs/data/picks.json`,
`data/diag/*.json|log`, `verification/report.json`, `verification/last_report.md`) must never be hand-merged.
Resolve them by taking one complete side (`git checkout --theirs <file>`), then confirm with
`python3 -c "import json;json.load(open('<file>'))"` before committing. `D23` now catches the mistake at CI
time regardless.

### PR #41 merged + deploy verified (session `arena/e6f33fe9`, 2026-10-24)

| Item | Value |
|---|---|
| Pull request | [#41](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/41) — **MERGED** 2026-10-24T17:02:38Z, merge commit `173a8d6` |
| Integration work | Merged `origin/main` three times while other sessions landed concurrently; every collision was resolved without discarding either side. Two generated artefacts (`docs/data/picks.json`, `data/diag/pipeline.log`) ended up committed with conflict markers at that moment — see the hotfix record below |
| Hotfix pull request | [#49](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/49) — **MERGED**, merge commit `872418f`; new verifier check **D23** blocks any future commit that ships conflict markers |
| Post-merge verify on `main` (before hotfix) | **failure** [40114322258](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40114322258) — D1 could not parse the payload |
| Post-merge verify on `main` (after hotfix) | **success** [40114894011](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40114894011) — 25 s |
| Six-hour refresh after the merge | **success** [40114322196](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40114322196) — regenerated the payload and healed `picks.json` / `pipeline.log` |
| Pages deployment | **success** [40114893488](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40114893488); Pages API `status: built` for `872418f` at 17:10:52Z |
| Live dashboard (fetched 17:1xZ) | `docs/index.html?v=872418f` renders: hero **Find every pick (159)**, **Next 24 hours (31)**, **Unresolved (0)**; "Where the updated picks are" cards with 159 / 31 / 12 / 0 counts; coverage 159/159 priced, 8 market, 41 Elo, **55 Elo + split standings**, 0 priors, 0 placeholders; 11 cancelled fixtures excluded |
| Live payload | `docs/data/picks.json?v=872418f` parses; `generated_at 2026-10-24T17:09:15Z`, `counts.fixtures 159`, `unresolved 0`, `lobby_upcoming 159 = priced 159`, `lobby_upcoming_missing_from_priced []` |

**Flagged for review (non-blocking, published on the site):**

1. `excluded_fixtures` currently mixes two reasons — *cancelled by Hotspawn* (10 rows) and *not listed in
   the lobby* (1 row: `Top Esports vs Anyone's Legend`, id 1067688, which had already started at 17:00Z).
   The row is honestly labelled with its own reason and source, but a reader may expect "excluded" to mean
   cancelled only. Worth a wording change by whoever next touches `scripts/update_picks.py`.
2. D18 remains a WARN by design (stale 2026-10-21 Leaguepedia diagnostic snapshot, not a current check).
3. The X1 external-link check tolerates host-blocked links (Polymarket/Unibet geoblocks from US runners)
   and fails only on genuinely dead links — that is how the dead `github.com/.../blob/main/...` link was
   caught during this session.

### PR #44 merged — production refresh & Pages verified (`arena/66e731b3`, 2026-10-24 17:13–17:18 UTC)

| Item | Result & evidence |
|---|---|
| Pull request | **PR #44** https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/44 — **MERGED** 2026-10-24T17:13:30Z, merge commit `e6849d6` |
| Post-merge production refresh on `main` | **success** — run `40115143658` (Update Hotspawn LoL picks), then refresh commit `a64173f`; payload generated 2026-10-24T17:18:06Z: **159/159 resolved, 0 unresolved**, Bovada in 4-book consensus, `checked_unavailable` 27, probe 37 sources |
| GitHub Pages | builds `40115143605` + `40115498312` **success**; Pages API `built` for `a64173f`; live fetch verified: exec summary renders picks-first cards, 159/159 priced, "Market consensus from Bovada, Pinnacle, Polymarket, Unibet (4 independent book(s))" on Worlds rows — https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/ |
| Tasks U1–U5 | **done** |
| Follow-up fix (this commit) | Coverage/resolution-mix sub-counts double-subtracted the standings blend (live read "41 from Elo" for 94 `MODEL_ELO` + 2 thin; resolution-mix omitted the 55 blend rows). Both texts now derive from `counts_by_method` (buckets sum to fixtures), and `with_team_specific_model` includes `MODEL_ELO_STANDINGS`. Local: verify 44 PASS, DOM PASS, render_check PASS, check_dom_render 50/50. |

---

### Fix `arena/e6f33fe9` — unresolved page contradicted itself on split-standings counts

The "How this snapshot was resolved" line on `unresolved.html` reported **0 by split standings** while the
league table further down the same page showed **55**, and the executive summary showed 55 as well. Cause: the
line counted `m.method === "MODEL_STANDINGS"`, an id the pipeline never emits — the real id is
`MODEL_ELO_STANDINGS` — so it fell back to 0, and "by our Elo model" absorbed those 55 by subtraction.

Fixed by one shared `methodMix()` helper in `docs/assets/app.js` that reads the pipeline's own
`coverage.counts_by_method` tally (falling back to scanning `matches`) and is used by **both** the summary and
the unresolved page, so the two can no longer drift. `verification/check_dom_render.js` now asserts the
reported standings/Elo counts match the payload **and** that they equal the sum of the per-league standings
column (3 new checks, 53/53). Verified non-vacuous: restoring the old `app.js` fails exactly the standings check.

---

### T26 — pricing-breakdown fix + published model track record (`arena/ac089f33-lolhotspawn2`, 2026-10-24 17:20–17:40 UTC)

| Item | Result & evidence |
|---|---|
| **PR #47** (fix) | https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/47 — **MERGED** 17:20:24Z, merge commit `94e6da4` |
| Bug | Exec summary read "9 external, 41 Elo, 55 standings" = **105 of 160**, and the unresolved page read "**0** by split standings" while its own per-league table showed 44. Cause: `stCount` read a coverage field the generator never emits, so Elo was computed by *subtracting* standings (`96 − 55`), and `nStand` only counted `MODEL_STANDINGS`, never the `MODEL_ELO_STANDINGS` rows the pipeline actually emits. |
| Fix | One `pricingMix(d)` helper counts the mix from the rows themselves (market / `MODEL_ELO`+`MODEL_ELO_THIN` / `MODEL_STANDINGS`+`MODEL_ELO_STANDINGS` / `MODEL_LEAGUE_PRIOR` / `UNRESOLVED`) and both pages print the total, so a mismatch is visible at a glance. |
| Live proof | https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/ → "**159 of 159** … **8** from external betting lines, **96** from our chronological Elo model, **55** from split standings, **0** priors, **0** placeholders (total 159)"; `unresolved.html` reads the same triple and "total 159". |
| **PR #54** (feature) | https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/54 — **MERGED** 17:35:51Z, merge commit `29d15c6`; branch pipeline run `40116032467` success; post-merge `Verify picks and site` `40116844699` success; Pages `built` for `29d15c6` |
| What it adds | `model.backtest()` now also returns `by_band` (log-loss / Brier / accuracy per competition strength band) and `calibration` (stated confidence bucket vs measured hit rate + gap), from the **same frozen ratings and the same 30-day holdout** — no refitting, no new data. Rendered as two tables on `methodology.html` and one line in the executive summary that names **both** the best and weakest band, so the number cannot be read as cherry-picked. |
| Measured (2026-10-24T17:30Z run, n=651) | bands: national/amateur `0.6020` (n=469), regional `0.6659` (n=34), major `0.6807` (n=148); calibration: 50-59% stated 54.4% → won 57.4% (−3.0 pts), 60-69% 64.1% → 74.7% (−10.7), 70-79% 73.5% → 85.4% (−11.9), 80%+ 81.8% → 95.0% (−13.2). Every bucket came out *under*-confident in this window; published as-is, including the small buckets (n=20, n=34). |
| Local gates | `check_dom_render.js` **50/50** (real payload and a band-injected payload); `verify_site.py` 44 PASS · 0 FAIL · 0 WARN · 1 SKIP; `check_dom_contract.py` PASS; `test_verifier.py` 45/45; `backtest()` unit-checked so band and calibration rows sum to `n` exactly. |
| Notes for the next session | `verification/report.json`, `last_report.md`, `docs/data/picks.json`, `data/diag/*` are CI-generated: always resolve to **theirs**, never hand-merge. The branch also receives `pipeline: test run [skip ci]` commits from `pipeline-test.yml` while a run is in flight, so a push can be rejected as non-fast-forward mid-run — re-fetch the branch and merge it before pushing. |
| Line coverage (unchanged, re-stated) | 151 of 159 rows have **no** reachable bookmaker line; the source field was re-read this session and still returns: Pinnacle = Worlds only; nine Kambi/Unibet country markets = the same 8 Worlds matches (DE does not carry Prime League); bmbets = Worlds / LCP / Game Changers Rising only; everything else 403/410/404/429/geo-stub/client-rendered. No new line source was found, so no pick changed on market grounds. |

---

## Session `arena/26d1e778-lolhotspawn2` — 2026-10-24 (T21–T25: reliability of the 6-hour publisher)

> Branch note: Arena fixes this session to `arena/26d1e778-lolhotspawn2`; the system branch stands in for the
> `session-<id>/<task>` convention and no other branch may be created or pushed.

**Claim (pushed before work):** commit `3e3cb81` appended the original T21–T25 claim (data integrity, source
research, mobile executive summary, verifier extensions, live run → PR). Exclusive scope was
`scripts/fetch_leaguepedia.py`, `scripts/update_picks.py`, `scripts/probe_sources.py`, `docs/*`, `docs/assets/*`,
`scripts/verify_site.py`, `verification/**`, `README.md`, `research/betting-sources.md`, `COORDINATION.md`.

### What this session found and changed

Main advanced through other sessions while this branch was running; `origin/main` already contains the
`standings_pages` fix, a Bovada series-moneyline parser, the unified mobile header, a market-source probe and a
jsdom render check. To avoid regressing any of that, this branch **adopted `origin/main`'s integrated tree**
(merge `fd703c1`) and re-applied only the two reliability fixes that main does not have, both derived from
failures observed on this branch today:

| Fix | Evidence | Files |
|---|---|---|
| **Leaguepedia fetch budget + snapshot guard.** Requests were capped at 90 s with 3 retries (~20 calls), so a throttled runner IP could burn the whole 40-minute job before any fallback. Now 25 s / 2 retries, a 600 s wall-clock budget, and the previous snapshot is preferred if a fresh export is under 85% of its size (a partial export silently drops teams). Partial exports are published as `degraded` rather than looking clean. | Branch run `40112232282`: “Run the live pipeline” was still executing after 37 minutes and was only stopped by the next push's concurrency cancel. Branch run `40115157991` completed the same pipeline in 7m54s. | `scripts/fetch_leaguepedia.py`, both workflows (`actions/cache` for `data/cache`, explicit step timeouts) |
| **Publisher cannot lose a run in an aborted rebase.** The publish step rebased in a detached-HEAD checkout; when the rebase refused to start, `git rebase --abort` exited 128 and the step failed, discarding the freshly generated payload. Replaced with `git merge --no-edit -X ours` (keeps this run's files, no-op when the branch has not moved). The 6-hour publisher no longer runs `git reset --hard HEAD~1` after a rejected push, which used to discard the refresh and push a stale tree on the next attempt. | Branch run `40111481359`: probe, pipeline and the full verify step all **succeeded**, then the publish step failed with `could not abort failed output rebase (128): fatal: no rebase in progress` — the run's payload was never committed. | `.github/workflows/pipeline-test.yml`, `.github/workflows/update-picks.yml` |

### Verification performed

* Offline suite (`scripts`, `verification`, `audit`): `py_compile` all, `node --check`, DOM contract,
  `test_dom_contract`, `test_verifier`, `test_standings_model`, `test_entity_and_books`, `audit/test_model`,
  `verify_site.py` — all green on the adopted tree plus the two fixes (see the PR run for the CI copy).
* Earlier branch runs exercised the full live pipeline end-to-end: `40115157991` (7m54s) published
  `schema_version 4`, 159 fixtures, 0 unresolved, 8 market rows, 27-source probe, and `40117535357`
  published Bovada `ok` with 7 two-way prices after the coupon-shape fix (superseded by main's own fix).
* This session did **not** use Hotspawn crowd percentages, did not infer a value from a blocked source, and
  published every looked-at source with its observed status and date.

### Irregularities carried forward (for review)

| ID | Item | State |
|---|---|---|
| I10 | Bovada's *series* moneyline is labelled period “Game”; rejecting every “game” period discarded all prices. CI probe also saw 250 KB JSON while `fetch_bovada()` reported no groups. | **Fixed on `main`** by another session (`_bovada_series_moneyline`); this branch does not re-fix it. |
| I11 | `pipeline-test` publish rebase (see above) and the publisher's `reset --hard` on push rejection. | **Fixed here**; acceptance = first branch run after this commit. |
| I12 | Leaguepedia can throttle a shared runner IP; 90 s x 3 retries x ~20 calls exceeds the job timeout. | **Fixed here** (budget + cache + partial-export guard); a live run must confirm the step stays under 25 min. |

---

## Session `arena/57975298-lolhotspawn2` — 2026-10-25 (claim)

Baseline at claim: `main` = `2173cc9` (scheduled refresh), payload generated 2026-10-25T10:41:50Z: **156 fixtures, 156 priced, 0 unresolved**, 9 rows from external lines (Worlds 8 + LGC Rising 1), 147 model rows, 10 Low-confidence. `scripts/verify_site.py` 44 PASS / 0 FAIL / 0 WARN at claim. Other sessions' PRs #55 and #59 are open against `main`; this session does **not** touch their files or merge their branches.

| Task | Status | Owner | Files (claimed scope) |
|---|---|---|---|
| T27 Fresh line-source research for the 147 fixtures with no bookmaker line (established books → esportsbooks → esports betting lines → aggregators), evidence recorded with URLs + date | done | arena/57975298 | `research/betting-sources.md`, `scripts/source_probe.py`, `scripts/update_picks.py` (source lists only) |
| T28 Publish the re-tested sources in every refresh (`checked_unavailable` + `market_probe`) so the site states what was actually tried today | done | arena/57975298 | `scripts/update_picks.py`, `scripts/source_probe.py` |
| T29 Executive-summary clarity: state explicitly how many published matches had **no** reachable betting line, with in-site links to those lists, and keep the separate unresolved/limitations section | done | arena/57975298 | `docs/index.html`, `docs/assets/app.js`, `verification/check_dom_render.js` |
| T30 Integration: branch pipeline run, re-verify, PR → `main`, merge without waiting, confirm Pages deploy, record here | done | arena/57975298 | `COORDINATION.md`, generated `docs/data/picks.json` |

No other session holds a claim younger than 60 minutes. Scope is non-overlapping with #55 (`docs/assets/app.js` conflict markers — already absent on `main`; this session rewrites only the executive-summary block in that file) and #59 (coordination record only).

## Session `arena/c1e74f5e-lolhotspawn2` — 2026-10-25 (claim)

All earlier claims are over 60 minutes old; baseline `2173cc9` is the current main. This session uses the Arena-fixed branch above (no alternate branch). No other active claim was found in the board; existing open PRs are left untouched.

| Task | Status | Owner | File scope |
|---|---|---|---|
| C1 Audit current coverage, provenance and unresolved semantics; fix defects with regression tests | done | arena/c1e74f5e | `scripts/**`, `verification/**`, `audit/**` |
| C2 Research external line availability using fresh CI probes; document official vs community evidence and limitations | done | arena/c1e74f5e | `research/**`, `data/diag/**`, `README.md` |
| C3 Mobile summary/picks/limitations integration and honest evidence labels | done | arena/c1e74f5e | `docs/**` |
| C4 Integration, live refresh, tests, PR merge and Pages confirmation | done | arena/c1e74f5e | `.github/workflows/**`, `COORDINATION.md` |

Network note: this sandbox allows GitHub/npm/PyPI only. Source verification requiring other hosts must run in GitHub Actions, with timestamped artifacts; blocked local requests will not be described as source verification.

**Parallel-session discovery (2026-10-25 14:13 UTC):** main advanced to PR #60's audit-only records after this session's claim. PR #62 concurrently edits `docs/assets/app.js` freshness and the phrase "verified pick"; this session does not change freshness behavior and will preserve that session's result during integration. Our distinct work is per-row source authority metadata, blank primary-organizer confirmation, the match-by-match unverified evidence table, and regression checks for those contracts. Any textual overlap is limited to removing false verification claims. PR #61 is audit documentation only. Existing reports are not overwritten as final findings; generated verifier reports are rebuilt by CI.

## Session `arena/81e6a4e3-lolhotspawn2` — 2026-10-25 (claim)

All earlier open claims in this board are dated 2026-10-24 or earlier (>60 minutes old);
this session takes over the stale integration/re-verification scope. Baseline is main
`2173cc9`. Arena requires the fixed branch `arena/81e6a4e3-lolhotspawn2` (no extra branches).

| Task | Status | Owner | File scope |
|---|---|---|---|
| V1 Audit current coverage, provenance, stale data and unresolved/tied recommendations; add targeted regression gates | done | arena/81e6a4e3 | `scripts/**`, `verification/**`, `audit/**` |
| V2 Research missing-line alternatives using established books, esportsbooks and community sources; distinguish unreachable from verified | done | arena/81e6a4e3 | `research/**`, `data/diag/**` |
| V3 Mobile picks/executive-summary clarity and honest evidence labels; integrate tested fixes | done | arena/81e6a4e3 | `docs/**`, `README.md` |
| V4 Live workflow, PR/merge, Pages confirmation and coordination evidence | done | arena/81e6a4e3 | `.github/workflows/**`, `COORDINATION.md` |

Initial blocker: GitHub Actions REST request returned HTTP 403 API rate limit exceeded
at 2026-10-25T14:09Z; git fetch succeeds. External hosts are unavailable directly from
this sandbox; live source verification must run through GitHub Actions, not be claimed
from cached data. No verified status will be inferred from a source link alone.

**Concurrent-claim discovery (2026-10-25, during the audit):** Actions revealed three other Oct-25
sessions that claimed on their own branches, invisible in this checkout at the
initial read: `arena/964cb944` (toss-up labels / VfB aliases / sources),
`arena/57975298` (missing-market counts / sources), `arena/6e003eec` (line probe).
Request to final integrators: retain their work; this session's changes are confined
to source timestamp/provenance presentation, explicit no-pick on exact 50/50,
passed-lock/24h boundaries, and checks of ALL cited history pages. No formula,
market adapter or alias is changed here. Shared-file integration requests:
`docs/assets/app.js` keep their summary/toss-up features alongside this session's
`pickPill`, `setHeader`, source labels and time-bound fixes;
`scripts/update_picks.py` keep their source-list additions alongside input timestamps;
`scripts/model.py` keep their alias/rating changes alongside latest-history source links.
This is an integration claim, not permission to overwrite their implementations.

**V1–V3 findings:** live run `40201225832` fetched/builds all 156 fixtures (9 market,
147 model; 0 unresolved; 11 Low). DOM rendering 59/59; evidence regression 8/8;
verifier self-tests 45/45; contracts 7/7; books/entity 17/17; audit 23/23.
Its external-link check correctly failed on a new Pinnacle retail link (404);
fixed to the observed-200 public guest endpoint, pending rerun. Fresh line-probe
`40201225819` success at 14:14:25Z: 38 requests, 147 model-only fixtures, zero new
validated coverage. Research: `research/evidence-audit-2026-10-25.md`.

**Mobile defect verified and fixed:** real Chromium 153/Playwright showed Picks
and Leagues scrolling to 430px on a 390px phone because long pick names inherited
`white-space: nowrap`. Scoped mobile badge wrapping now passes 28/28 page–viewport
checks (7 pages × 320/390/768/1280px), nav target heights 60px. Script and measured
report are in `verification/check_browser.cjs` / `mobile-browser-2026-10-25.json`.
This session requests CSS integrators retain this additive @media block alongside
any toss-up styling. Browser packages remain ignored under node_modules.

---

## Session `arena/964cb944-lolhotspawn2` — 2026-10-25 (claim)

Baseline at claim (branch == `main` @ `2173cc9`, payload generated 2026-10-25T10:41:50Z): **156 fixtures · 156 resolved (100%) · 0 UNRESOLVED** · 8 `MARKET_CONSENSUS` + 1 `MARKET_SINGLE` · 92 `MODEL_ELO` · 53 `MODEL_ELO_STANDINGS` · 2 `MODEL_ELO_THIN` · 10 Low-confidence · 9 cancelled excluded. `verify_site.py` **44 PASS / 0 FAIL / 0 WARN / 1 SKIP**; verifier 45/45, standings ALL PASS, entity/books 17/17, audit 23/23, DOM contract PASS. Pages `built` for `2173cc9`. Open PRs #20/#26/#48/#50/#55/#59 belong to other sessions (stale, 2026-10-23/24) — not touched. Remaining gaps this session targets: **62 rows priced within ±3 pts of 50/50** (picks exist but are near coin-flips — must be labelled as toss-ups on mobile, not presented as edges); **5 of 10 Low rows involve VfB eSports** (`CROSS_LEAGUE_MODEL` inside its own tournament — investigate before touching); fresh 2026-10-25 low-tier source research.

| Task | Status | Owner | Files (claimed scope) |

## Session `arena/c7fd40e5-lolhotspawn2` — 2026-10-25 (claimed)
| Task | Status | Owner | Files |
|---|---|---|---|
| T38 Fresh line-source research for model-only/low-tier fixtures (established books → esportsbooks → aggregators/community); record fixture-matched results, promote nothing unverified | claimed | arena/c7fd40e5 | `research/betting-sources.md`, `data/diag/line_probe.json` (CI-generated) |
| T39 Verify exec-summary → picks links, separate unresolved/limitations section, 390px mobile readability; fix only if a check fails | claimed | arena/c7fd40e5 | `docs/**` (fixes only), `verification/**` |
| T40 Live refresh on branch, re-verify, PR→main, merge, confirm Pages deploy | claimed | arena/c7fd40e5 | `COORDINATION.md`, `docs/data/picks.json` (CI-generated) |
Baseline 2026-10-25: payload 2026-10-25T10:41Z, 156 fixtures, 156 resolved, 9 market, 0 unresolved, verify_site 44 PASS/0 FAIL.

### Session `arena/c7fd40e5` results (2026-10-25)
T38 done: CI line-probe 40201469095 — 38 candidates, 0 cover any of 147 model-only fixtures (research §20). T39 done: verify_site 44 PASS/0 FAIL, DOM render 53/53, verifier 45/45, entity/books 17/17; exec summary hero "Find every pick" + Where-the-picks-are cards + separate `#unresolved-section` confirmed in `docs/index.html`. T40: PR/merge/Pages recorded below. Irregularity: local sandbox probe HTTP 0 for all hosts — discarded, CI is authoritative (now documented in `scripts/probe_lines.py`); GitHub API secondary rate-limit delayed dispatch, push-triggered runs succeeded.
## Session `arena/964cb944-lolhotspawn2` — 2026-10-25 (claim)
Baseline at claim (branch == `main` @ `2173cc9`, payload generated 2026-10-25T10:41:50Z): **156 fixtures · 156 resolved (100%) · 0 UNRESOLVED** · 8 `MARKET_CONSENSUS` + 1 `MARKET_SINGLE` · 92 `MODEL_ELO` · 53 `MODEL_ELO_STANDINGS` · 2 `MODEL_ELO_THIN` · 10 Low-confidence · 9 cancelled excluded. `verify_site.py` **44 PASS / 0 FAIL / 0 WARN / 1 SKIP**; verifier 45/45, standings ALL PASS, entity/books 17/17, audit 23/23, DOM contract PASS. Pages `built` for `2173cc9`. Open PRs #20/#26/#48/#50/#55/#59 belong to other sessions (stale, 2026-10-23/24) — not touched. Remaining gaps this session targets: **62 rows priced within ±3 pts of 50/50** (picks exist but are near coin-flips — must be labelled as toss-ups on mobile, not presented as edges); **5 of 10 Low rows involve VfB eSports** (`CROSS_LEAGUE_MODEL` inside its own tournament — investigate before touching); fresh 2026-10-25 low-tier source research.
| T27 Toss-up transparency: label near-50/50 model rows as coin-flips in exec summary + picks + unresolved views so a phone user can see which picks are weak; count them in the exec-summary unresolved/limitations section | claimed | arena/964cb944 | `docs/index.html`, `docs/picks.html`, `docs/unresolved.html`, `docs/assets/app.js`, `docs/assets/style.css`, `scripts/verify_site.py` (new check only), `verification/check_dom_render.js` |
| T28 Investigate VfB eSports cross-league cluster + near-50 concentration; fix only if a verified defect (wrong anchor/alias), otherwise document with Leaguepedia links | claimed | arena/964cb944 | `scripts/model.py`, `data/aliases.json` (only if defect proven), `research/betting-sources.md` |
| T29 Fresh source research 2026-10-25 for low-tier fixtures (established books → esportsbooks → lines/aggregators → community ratings e.g. gol.gg); add any genuinely new candidate to the CI probe, never copy a price without a structured feed + human-verifiable sample | claimed | arena/964cb944 | `research/betting-sources.md`, `scripts/source_probe.py`, `scripts/probe_lines.py` |
| T30 Integration: live pipeline on branch, line-by-line re-verify, PR → merge, Pages confirmation, record here | claimed | arena/964cb944 | `COORDINATION.md`, generated payload |
Any session needing a file in this scope must log a request here instead of editing it.
## Session arena/f931cee9 — 2026-10-25
Branch fixed by Arena: `arena/f931cee9-lolhotspawn2`. Previous claims are older than 60 minutes. Claim: freshness/verification audit and targeted mobile data-quality fixes; scope `docs/assets/app.js`, `docs/assets/style.css`, `verification/test_freshness.cjs`, `verification/session-2026-10-25.md`, `COORDINATION.md`. No other open PR scopes will be modified intentionally. Status: in progress. Research will use existing official-source adapters through GitHub Actions because this sandbox only permits GitHub/package-registry outbound hosts. Community estimates are not official verified facts.
Session f931cee9 progress: local site verification 44 PASS / 0 FAIL / 1 SKIP, seven-page DOM rendering 53/53, freshness regression 10/10. Corrected false “verified pick”/“Live data” labels and fail-open timestamp handling. Details and source links: `verification/session-2026-10-25.md`. GitHub briefly returned a rate-limit error; retry available. No newly fetched lines claimed. Scope adds the audit report and freshness unit test only; generated verification artifacts left unchanged.
## Session `arena/7dbe0fbd-lolhotspawn2` — 2026-10-25 (claim: final user-requirement audit)
**Claim:** final independent audit of the already-integrated LoL picks dashboard against the requested
coverage, source traceability, unresolved/limitations, mobile findability, and scheduled-refresh requirements.
Scope: `verification/**`, `audit/**`, and this coordination log only. Existing older verification/integration
claims in this board have no commits newer than 2026-10-24 and are more than 60 minutes old; this session
records the handoff under the board's takeover rule. No changes to generated picks, models, shared site
navigation, or workflow code unless a critical verifiable defect is found; if one is found, log a request
rather than touching another scope. Baseline: `2173cc9` (`origin/main`); payload timestamp
`2026-10-25T10:41:50Z`, 156 fixtures, 9 market-derived, 147 model-derived, 0 unresolved, 10 low-confidence.
### Final requirements audit results (`arena/7dbe0fbd`, 2026-10-25)
No code changes were necessary: the requested mobile summary, pick tables, external-market-first resolver,
non-market model path, per-league limitations, flagged page, and 6-hour updater are already present on the
branch baseline and pass the repository's non-vacuous checks. This audit did not generate or substitute any
probabilities and did not use Hotspawn crowd percentages.
| Check | Result / evidence |
| Current committed pick snapshot | `docs/data/picks.json`, generated `2026-10-25T10:41:50Z`: 156 upcoming fixtures; 9 market-derived, 147 model-derived (92 Elo, 53 Elo+standings, 2 thin Elo); 0 unresolved placeholders; 10 low-confidence; 156/156 lobby fixtures reconciled. |
| Wider source probe in that same snapshot | 37 named candidates, checked `2026-10-25T10:41:50Z`; includes 32 market candidates and 3 reachable results sources. Probe output is diagnostic only, never a probability input. The dated `data/diag/source_probe.json` is older (2026-10-24T18:18Z); the current in-payload `market_probe` is the authoritative latest observation. |
| Full site/data verifier | `python3 scripts/verify_site.py`: **44 PASS, 0 FAIL, 0 WARN, 1 SKIP**. D18 skipped because this local audit did not supply a fresh Leaguepedia MatchSchedule snapshot. |
| Live-source verification attempt | `python3 scripts/verify_site.py --leaguepedia-schedule data/diag --check-external`: **44 PASS, 0 FAIL, 2 WARN, 0 SKIP**. D18 reports a stale 2026-10-21 schedule snapshot (89.4 h old): 9 historical time deltas and 39 rows absent from that snapshot; this is explicitly not current verification and Hotspawn remains the lock-time source. X1 could reach only 4/18 links from this sandbox; the other 14 returned transport status 0 (restricted/unreachable here), with no 404/410. These are not treated as broken or as evidence of current lines. |
| Model/source tests | `verification/test_standings_model.py` ALL PASS; `verification/test_entity_and_books.py` **17/17**; `audit/test_model.py` **23/23**; `verification/test_verifier.py` **45/45**. |
| Mobile and render contracts | DOM contract PASS; negative contract self-tests **7/7**; `node --check docs/assets/app.js` OK; with temporary `jsdom@24`, `verification/check_dom_render.js` **53/53** and `verification/render_check.cjs` PASS across all seven pages. No npm files were committed. |
| Refresh automation / Pages | `update-picks.yml` schedules `0 */6 * * *`; verifier checks full lobby coverage and probability/source invariants. GitHub Pages API reports `status: built`, source `main:/`, HTTPS enforced. `gh run list` was unavailable due GitHub API rate limiting (HTTP 403); no claim is made here about a new deploy from this audit-only branch. |
| Limits for manual review | The latest snapshot has 0 unresolved because all 156 fixtures have a market or a model estimate; that does not mean every row has an external bookmaker line (only 9 do). Low-tier prices use Leaguepedia community results/standings, not an official odds feed, and 10 rows are low-confidence. Paid odds APIs / human account signup remain unavailable without owner-provided credentials and are not fabricated. The site discloses these limits and keeps flagged/source links visible. |
**Audit disposition:** task done; no non-overlapping site/model code defect was established by this audit, so no feature files
were modified. The two live-check caveats above remain non-blocking and should remain visible to readers; do not mark the
stale schedule snapshot or blocked source checks as freshly verified.
### PR / publication record for final audit
- **PR #60** — https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/60 — merged 2026-10-25T14:12:23Z by merge commit `65de12bc5c75c7c721a965db1dc0e53941c8d0c5`.
- Post-merge Pages build `1313374096` was still reported as `building` at the time of this record (source commit `65de12b`). The public dashboard was fetched successfully during the verification window and rendered the current snapshot: 156/156 picks, 9 bookmaker-line matches, 0 unresolved placeholders, 10 low-confidence, next refresh shown as 16:41Z. This confirms the existing published site content; it is not evidence that the new audit-only commit has finished deployment.
- The site implementation and scheduled publisher were already present on `main`; PR #60 only adds this verification/coordination record. The GitHub Actions run list endpoint returned HTTP 403 rate-limit response, so no current action-run conclusion is asserted.

---

## Session `arena/07b651a3-lolhotspawn2` — 2026-10-25 (claim: data-consistency fixes, mobile stacked-table labels & live verification)

> Branch note: Arena tracks this session on fixed branch `arena/07b651a3-lolhotspawn2`, which stands in for `session-<id>/<task>`. No active (<60 min) open claims exist on `main` (`arena/7dbe0fbd` completed PRs #60/#63; prior claims date to 2026-10-24).

| Task | Status | Owner | Files (claimed scope) |
|---|---|---|---|
| A1 Line-by-line repo/payload verification + fix `unresolved.reasons` mismatch for 5–7 game `MODEL_ELO_THIN` rows (`scripts/update_picks.py`) + document 2026-10-25 line-by-line audit & fresh low-tier source findings | done | arena/07b651a3 | `scripts/update_picks.py`, `scripts/model.py`, `research/line-by-line-audit-2026-10-25.md`, `research/betting-sources.md` |
| A2 Mobile UX & executive-summary audit fixes: remove duplicate sourceless per-league table inside `#unresolved-summary` on `index.html`, add missing mobile `data-label` attributes on all `<td>` cells (`match.html`, `flagged.html`, `methodology.html`, `app.js`), surface blended Elo on `match.html`, unify `viewport-fit=cover` + `color-scheme` + icon across all 7 pages, replace broken relative `../research/betting-sources.md` links, and replace stale hardcoded snapshot counts (`73 of 169`, `160 fixtures`, `31,752`) with live payload bindings | done | arena/07b651a3 | `docs/*.html`, `docs/assets/app.js` |
| A3 Non-vacuous regression tests for mobile `data-label` coverage, no duplicate sourceless tables, no stale hardcoded counts / broken `.md` relative links, and `MODEL_ELO_THIN` reason tally consistency | done | arena/07b651a3 | `verification/check_dom_contract.py`, `verification/test_dom_contract.py`, `verification/check_dom_render.js`, `audit/test_model.py` |
| A4 Live branch pipeline refresh, reconcile any concurrent `origin/main` merges without discarding other sessions' work, re-verify all suites, PR → `main`, merge, confirm GitHub Pages deployment, record results | in progress — merged PRs #67/#68/#70/#71/#72/#76, running final combined CI gate | arena/07b651a3 | `COORDINATION.md`, `docs/data/picks.json` (CI-generated) |


---

Reconciliation f931cee9: main advanced via audit-only PR #60; both coordination entries preserved in the append-only conflict. No feature or generated payload conflict. Branch live pipeline 40201194918 SUCCESS (all fetch, render, external verification and probe steps); refreshed 14:15:07 UTC: 156 fixtures, 9 market, 147 model, 54 standings, 11 low-confidence, zero unresolved.

**Integration reconciliation (14:21 UTC, c1e74f5e):** merged `origin/main` `7a8b8d1` (PRs #60/#63 audit, #62 freshness, #66 collapsed method legend). Coordination append conflict keeps both sessions' entries. `app.js` conflict was the same removal of “verified pick”; adopted #62's “published pick or estimate” wording, retaining its fail-closed freshness and focus handlers plus this session's provenance labels. `index.html` automatically preserves #66's collapsed legend and our above-fold action. Generated data/log/report conflicts keep the newer branch live snapshot (14:15:45 vs main 14:15:07), including provenance metadata, pending another complete regeneration; no generated rows hand-merged. No source fact or other session's feature discarded. Browser audit caught and fixed actual 320px badge overflow, not just a CSS contract check.

**Safe rebase note:** after the main integration merge, a routine `git pull --rebase` tried to flatten/replay already integrated main commits and hit the append-only coordination conflict. Rebase was immediately aborted; the completed integration merge and all other sessions' changes remain intact. Subsequent pulls use merge-preserving rebases; no force push or history discard.

**Final integration reconciliation (2026-10-25 14:26 UTC):** main advanced through PR #65 (near-50% coin-flip labels/filter, extra source probes). Adopted all toss-up/filter/count tests and new candidates, retained no-recommendation behavior for unsupported UNRESOLVED rows and per-row provenance. Combined both descriptions in match cards/detail and kept community-not-official labeling. Append-only board keeps both claims. Generated snapshot/log/report files adopted main's newer 14:24:11 run pending full branch regeneration; no hand-merging generated rows. Mobile CSS keeps all badges wrapping, including coin-flip labels.

### C1–C3 completion evidence (`arena/c1e74f5e`, 2026-10-25)

| Task | Status | Evidence |
|---|---|---|
| C1 Coverage, authority and arithmetic | done | First full live pipeline [40201255132](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40201255132) success. Additive `verification` metadata deliberately leaves primary-organizer confirmation null; source authority is hostname-based, not inferred from a source's name. D24 checks every row. D25 independently recomputes saved no-vig/consensus arithmetic. **55/55** verifier positive/negative tests, source-policy tests **4/4**, entity/book tests **17/17**, model **23/23**, standings ALL PASS. |
| C2 Fresh low-tier source research | done | Dedicated [40201699912](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40201699912) success: 38 source/market variants at 14:20:34 UTC, 0 newly covered fixtures among 147 non-market matches. Full dated publisher URLs and observed statuses in `research/source-audit-2026-10-25-c1e74f5e.md`; 37-source broad probe at 14:15:45 UTC. Historical and current observations are distinguished, no price from an unparsed endpoint. |
| C3 Phone-first UI and evidence audit | done | Real Chromium on seven pages × four widths (320/390/768/1280): **78/78**, including primary CTA and first pick + both chances above the phone fold. Fixed real 320px overflow without clipping names. Integrated concurrent freshness/legend/toss-up work; combined JSDOM **63/63**; DOM contract PASS. No arbitrary team recommendation for UNRESOLVED placeholders. |
| C4 Integration / PR / Pages | in progress | Final branch CI and deploy confirmation to follow; no owner review requested. |
| Primary-organizer result audit | needs review | Not implemented/claimed. Every affected non-market fixture is published on `docs/flagged.html#official-results-audit` with null official-confirmation fields and source references. Leaguepedia page existence is not primary-source verification. |

The source audit's dated counts describe that exact snapshot. Later refreshes and added candidates from concurrent sessions may change counts; the live executive summary and source tables always derive from the latest payload. No browser binary, npm dependencies, or screenshots are committed.

### T27–T30 results (session `arena/964cb944`, 2026-10-25) — PR #65 MERGED

**Integration reconciliation:** main advanced via PR #62 (f931cee9 fail-closed
freshness) and #66 (6d169c43 mobile navigation/source notes). Merged main locally:
kept their stricter `isFresh`/freshness wording and navigation changes; retained
our separate input-health/source timestamps. Coordination append conflict keeps
both complete session logs. All research/flagged additions from main retained.
Generated payload/log conflicts temporarily keep the newer 14:15:22 branch
snapshot (it contains the new input timestamps); verifier report adopts main's
copy pending CI regeneration. No model/alias/formula work from another session
was discarded. Re-running integration/browser/freshness checks before publishing.

**Second reconciliation / CI gate:** PR #65 merged the concurrent <=53% coin-flip
filter, labels and source candidates. All are retained; exact 50/50 still says
"no preferred team" and also carries the coin-flip label. Mobile wrap CSS remains
additive. Board append conflict retains both sessions' records; generated data
is regenerated rather than hand-merged. Run `40201686037` passed live collection,
DOM and external/source-page checks (50/50 cited wiki pages exist), but the new
real-browser gate failed. Logs could not be downloaded from the restricted
results-receiver host. Browser diagnostics are now committed on success/failure,
Node is upgraded to supported 24, and bundled Lambda libraries are used only if
system NSS is absent (needed in the sandbox, not on standard Ubuntu runners).
No failed browser gate is waived; the next run must pass before PR #67 merges.

**V1–V3 complete; V4 ready to merge:** PR [#67](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/67).
Final live run [40202147232](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40202147232)
**SUCCESS** (2m31s): snapshot 14:27:19Z, 156/156 upcoming lobby fixtures, 9 market,
147 model, 54 standings/blend, 0 unresolved, 11 Low; zero missing; 9 cancelled
excluded. Verifier **46 PASS / 0 FAIL / 1 WARN** (blocked external hosts). Source
page API audit **50/50 exist**, not a claim of official value verification.
Real Chromium CI **28/28**, integrated DOM **64/64**, freshness **10/10**, evidence
**8/8**. The browser runtime fix passed, not waived. Evidence in
`data/diag/browser.{json,log}`, `source_pages.log`, `verification/report.json`, and
`research/evidence-audit-2026-10-25.md`.

After the green run, main's scheduled refresh `85ab307` conflicted only in the
machine-generated payload/log: main timestamp 14:24:11Z vs branch 14:27:19Z. The
newer verified branch copy was retained. No source/model/site code changed in
that reconciliation; local combined DOM/freshness/evidence checks re-passed.
Unverified community organizer confirmation / inaccessible betting lines remain
**needs review** on `docs/flagged.html#evidence-limits` and do not block publication.

---

## Session `arena/85bba52b-lolhotspawn2` — 2026-10-25 (claim)

> Branch note: Arena fixes this session to `arena/85bba52b-lolhotspawn2`; the system branch stands in for the
> `session-<id>/<task>` convention (no other branch may be created or pushed).
>
> Claim check at 14:10 UTC: `origin/main` = `2173cc9` (scheduled refresh, payload generated 2026-10-25T10:41:50Z).
> The newest board claim (`arena/26d1e778`, 2026-10-24 18:23Z) is a **PR #59 record**, not an active work claim, and
> every open PR (#59, #55, #50, #48, #26, #20) is from 2026-10-24 or earlier. No claim younger than 60 minutes touches
> the files below, so this session claims them now and pushes this claim before editing anything.

| Task | Status | Owner | Files (claimed scope) |
|---|---|---|---|
| T27 Fresh external-source research for the fixtures the featured (book-priced) picks cannot resolve — established LoL betting sites → esportsbooks → odds aggregators/comparison pages → community results; every claim dated and linked, nothing inferred | in progress | arena/85bba52b | `research/betting-sources.md` (§20), `scripts/source_probe.py` (candidate list only) |
| T28 Phone-first site pass: per-row "why this pick" evidence on the picks table (mobile cards), installable home-screen manifest + icons, and an exec-summary pointer that survives a 390 px viewport | in progress | arena/85bba52b | `docs/*.html`, `docs/assets/*`, `docs/manifest.webmanifest` |
| T29 Verification: full offline suites, line-by-line spot-checks of priced rows against their cited official pages, exact-count reconciliation (Hotspawn lobby vs priced), mobile/DOM render checks | in progress | arena/85bba52b | `verification/**` (read-only unless a check is provably wrong) |
| T30 Integration: live pipeline on this branch, re-verify the combined data, PR → `main`, merge without waiting, confirm GitHub Pages deploy, record PR/run/deploy links here | in progress | arena/85bba52b | `COORDINATION.md`, generated `docs/data/picks.json` |

**No-file-conflict statement:** T27 touches only the research note and the probe candidate tuple; T28 touches only
`docs/`; T29 is read-only verification; T30 touches only this board plus CI-generated artifacts. Any request from
another session to change a file outside this scope will be logged here instead of edited.

---

## Session `arena/85bba52b-lolhotspawn2` — 2026-10-25 (completion record)

Tasks T27–T30 are **done on this branch**; the PR/merge/deploy links are appended after the merge below.

### What changed (T27–T30)

| Task | Result | Files |
|---|---|---|
| T27 fresh external-source research | `research/betting-sources.md` §20 (+20.1–20.3): Cloudbet (advertises PRM 2D, events tab empty; API needs `X-API-Key`), bmbets (LoL index = Worlds 9 / LCP 1 / Game Changers Rising 1, no PRM; page also renders an over-quota reCAPTCHA widget), Betmonitor (PRM 2D page returns its generic cross-sport highlights, twice), esportsinsider (PRM **1st** division only), Polymarket (PRM **1st** division only). 4 new candidates added to `scripts/source_probe.py`. | `research/betting-sources.md`, `scripts/source_probe.py` |
| T28 phone-first site pass | Per-row plain-language "why this pick" (`.sub` chips), amber ⏱ row warning, **"Start time by source"** card on every match page (Hotspawn feed + each book's own `start_utc` + delta + link), installable manifest + 4 PNG icons + apple-touch-icon on all 7 pages, 5th exec-summary link card to `flagged.html`, phone "Add to Home Screen" tip. | `docs/**` |
| T29 verification | `verify_site.py` **46 PASS / 0 FAIL / 0 WARN / 1 SKIP**; `test_verifier.py` **55/55**; `check_dom_render.js` **60/60**; `render_check.cjs` PASS; `check_dom_contract.py` PASS; `test_dom_contract` 7/7; `test_entity_and_books` 17/17; `test_standings_model` ALL PASS; `audit/test_model` 23/0. | `scripts/verify_site.py`, `verification/**` |
| T30 integration | `research/line-by-line-audit-2026-10-25.md` (gates, PRM 2D 7/7 time table, Worlds irregularities, PvB collision, 6 market rows vs Polymarket, 147-no-line evidence, organizer coverage, "could not verify" table); `docs/flagged.html` `#audit-2026-10-25` A1–A12 with a source link on **every** row; new verifier **S17** enforcing exactly that. | `research/**`, `docs/flagged.html`, `docs/methodology.html`, `scripts/verify_site.py` |

Merge reconciliations (main advanced via PRs #62/#63 + `arena/6d169c43` §20 during this session): nothing discarded — generated files took main's whole side, COORDINATION kept both blocks, main's legend restructure adopted (coin-flip legend line dropped with it; explained instead in the unresolved section + chip tooltip), this session's research renumbered **§21**. Verification on merged tree: `verify_site.py` 45 PASS/0 FAIL, jsdom 58/58, all unit suites green incl. `test_freshness.cjs`. Spot-check: Polymarket Mental Rush vs Vitality Rising Bees series ML 65¢/38¢ vs payload 64.5% pick ✓. Flagged (non-blocking): 61 coin-flip picks now labelled; Cloudbet/Kalshi probe-only; Liquipedia metadata probe degraded one run (published).

**Artifact-only reconciliation (14:30 UTC):** PR #75 opened. Main advanced through #72/#73 source-research records; merge `47cee78` retains all board/research entries and adopts main's generated diagnostics (no generated row hand-merge). The only production-independent code change is a diagnostic bo3.gg probe header. Dashboard/model functionality is unchanged from the successful local integrated audits. Fresh CI will regenerate the complete payload with source authority and blank official-confirmation fields before PR merge.

### Resolved irregularities (evidence, not assertions)

* **I-Worlds-times** — the 10:41Z payload carried 25 Oct Worlds times 1–3 h off Hotspawn's own match pages, Leaguepedia and
  Polymarket, with GEN–LYON / DK–KOI swapped. **No manual edit was made.** The 14:16Z refresh re-read the same feed field and
  all four corrected themselves; `START_TIME_MISMATCH` = **0** rows now (2 rows keep `START_TIME_DISAGREES_WITH_BOOKS`,
  where a book's own kickoff field lags ≤3 h). Documented as A1 on `flagged.html` and re-stated in methodology §1.
* **Betmonitor PRM 2D prices** — an earlier search-engine excerpt showed a full PRM 2D table (bet365 1.90, ggbet 2.12 …).
  Two direct reads on 2026-10-25 returned the generic highlights index with the correct page title and no LoL row. The
  prices are therefore recorded as **not reproducible → not used** (A9), and the earlier note is superseded by this record.
* **bmbets "blocked"** — both readings are true: the league index loads (Worlds/LCP/LGC Rising only), while the page also
  prints an over-quota reCAPTCHA widget. Recorded that way (A10) so nobody re-litigates it.
* **Phong Vũ Buffalo** — Hotspawn tag-expansion artefact for DACH entrant **PvB (Swiss Team)**; 6 rows priced as PvB, all
  flagged `HOTSPAWN_NAME_COLLISION` (A2).
* **Unverified organizers** — Tunisian (TUNESF template shell), 4 Nations (UKEL), Arabian 2nd Division, LigaGG CELOL,
  Komplettligaen playoffs (fixtures absent), RIVALS bracket ("TBD") → A3–A8, each with the page that was read.

### Counts on the branch payload (2026-10-25T14:16:18Z, schema 3)

156 fixtures · 156 priced · **0 unresolved** · 9 market (8 consensus + 1 single) · 147 model · 11 Low confidence ·
9 cancelled fixtures excluded · 12 competitions · 27 fixtures locking in the next 24 h · lobby reconciliation
234 listed / 156 upcoming / 78 past / 9 excluded / 0 unexplained.

### Standing rules honoured

No Hotspawn crowd percentage and no Hotspawn price is used as an input; every probability is either a de-vigged
multi-book consensus or our own Elo/standings model; every table row on the review pages links an external page
(now enforced by S17); nothing was inferred from a blocked source.

**Full integration refresh (14:34 UTC):** latest code run [40202349776](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40202349776) passed every step, including real browser checks and fresh source verification. Main then advanced through PWA #70, deeper audit #68 and other sessions' records. Adopted their install assets, complete next-24h rendering (no six-card truncation), short why-lines, source-time warnings, official-audit findings and new probe candidates. Kept our shorter hero, above-fold controls, per-row provenance, unsupported-row NO PICK behavior, blank official-confirmation audit and odds arithmetic. Resolved append-only board and section-placement conflicts by retaining both; generated files adopt newer main until CI regeneration. Found integration duplicate check ID S16 (coin-flip and installability): renamed only installability to S18 plus its self-tests; both tests remain enforced. No conflicting feature silently dropped.

**Final CI correction and coverage integration (14:40 UTC):** run 40202840025 passed fetch, JSDOM and real mobile checks, then correctly failed X1 on one real 404: an A12 Polymarket category reference added by a parallel audit. A12 is now explicitly unverified, its historical claim superseded, with the attempted path retained as text plus working publisher/check references; no external checks were weakened. Main advanced through lobby-union coverage safeguards and in-page refresh controls: retained their code/workflows/regression suites, combining appended CSS. Generated artifacts adopt main pending final union-aware refresh. User-facing source facts remain blank/unverified where the failed category cannot confirm them. Both earlier live successes and this detected failure are recorded, not hidden.

**Final integration race:** PR #67 merge attempt was correctly rejected because
main advanced while it was being checked: PRs #70/#72/#73 (per-row reasons,
start-time-by-source disclosure, installability, audit table and new research).
Their code, icons, manifest, tests and notes have all been retained by merging
main. Only append-only coordination and generated evidence conflicted; both
coordination blocks were preserved and main's generated files adopted pending
one final pipeline regeneration of the new input-timestamp fields. Nothing is
force-merged, and source fields are not manually edited. Full combined gates
must pass again before merging #67.

**404 caught in combined upstream work:** run `40202528210` passed collection,
all DOM tests and real Chromium, but failed X1 on the newly merged static A12
Polymarket Prime League category link (HTTP 404). A12 now explicitly records
that historical coverage claim as **unverified / needs review** and links the
reachable official Gamma API plus dated failure evidence instead of presenting
a dead category as current coverage. No check was weakened. Main #68's full
next-24h summary cards, phone-first reorder and limitation de-duplication are
also retained; the 5-minute grace was removed consistently from both payload
and UI so a passed lock is never included as an upcoming pick. All docs/site
changes require a new green integration run before merge.

**Coverage integration:** final green pre-union run `40202944643` passed all live,
DOM, browser and external-source gates. While it completed, main #71 added a
necessary union fix: a lobby-only RIVALS fixture (1090065) can be absent from the
backend API, so using their intersection was not full coverage. This session
retains the union parser and all independent coverage gates/unit tests from
#71, its new nonfeatured summary, and both phone CSS additions. Conflicts were
append-only UI sections/CSS/workflow tests plus generated data; both sets of
features are kept. Main's union-generated payload is adopted pending fresh CI.
New wording again identifies Leaguepedia as community records, never an official
organizer source. A final union-aware live run is required before #67 merges.

### T30 integration result — PR, merge, deploy (recorded 2026-10-25)

| Item | Value |
|---|---|
| Pull request | **[#70](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/70)** — "Phone-first picks site: start-time-by-source evidence, audit table A1-A12, installability + stricter verifier" |
| Merged | **2026-10-25T14:28:07Z**, merge commit **`331e753c761985d96699e67244769b7c74323aef`** (merge without waiting for review, as the brief requires) |
| Merge conflicts | `COORDINATION.md` (append-only → resolved with `scripts/resolve_coordination_conflict.py`, both sessions' blocks kept), `research/betting-sources.md` (my new section renumbered **§20 → §22** because two other sessions already own §20/§21), `docs/index.html` (kept the other session's method-chip legend **and** the phone tip), and the generated artifacts (`verification/report.json`, `verification/last_report.md`, `data/diag/source_probe.json`, `docs/data/picks.json`) → took the incoming/CI copy, never hand-merged |
| Rebase hygiene | the two `pipeline: test run [skip ci]` commits on this branch had already committed **conflict markers** into `docs/data/picks.json` / `data/diag/*` during a rebase; they were **dropped** and the payload re-taken verbatim from CI. Verifier D23 ("no committed artifact contains conflict markers") now passes on `main` |
| Pages builds | `028c5a56` built 14:31:32Z · `9714344` built 14:36:37Z (both contain this work; earlier `31c989d4` errored on an unrelated concurrent merge) |
| Live pipeline after merge | `picks: scheduled refresh [skip ci]` published **`generated_at 2026-10-25T14:31:30Z`** — 156 fixtures, 156 priced, 0 unresolved, 9 market, 147 model, 11 Low, 9 excluded, **43 probe sources** (up from 41: Cloudbet PRM-2D events, bmbets, Betmonitor, esportsinsider now probed every run) |
| Verification on `main` after the merge | `verify_site.py` **49 PASS / 0 FAIL / 0 WARN / 1 SKIP** · `test_verifier.py` **64/64** · `check_dom_contract.py` PASS · `audit/test_model.py` 23/0 (run in a throw-away worktree of `origin/main`) |

**Measured outcome of the start-time finding:** `START_TIME_MISMATCH` went 10 → **0** between the 10:41:50Z and 14:24:11Z
payloads with no code change — the upstream feed corrected itself, and the four 25 Oct Worlds rows now read 17:00 / 18:00 /
19:00 / 22:00 UTC. Two rows still carry `START_TIME_DISAGREES_WITH_BOOKS` (Unibet's own kickoff field 1.0 h and 3.0 h off).
The full evidence trail is `research/line-by-line-audit-2026-10-25.md` §2.2 and `flagged.html#audit-2026-10-25` A1.

**Final union-aware gate SUCCESS:** [40203290312](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40203290312)
completed successfully, including live collection, actual Chromium, all source
checks, union unit tests, and the independent lobby/API coverage gate. After
that run, main advanced only via the #76 coordination/report record: both board
appends are preserved and this run's verifier report retained. No tested code
changed in this last merge. PR #67 is ready for immediate autonomous merge;
Pages publication will be confirmed separately below.

### Session `arena/07b651a3-lolhotspawn2` — A1–A3 results & combined verification (2026-10-25)

- **A1 (Data consistency & audit documentation):** Unified low-confidence reason classification via `_low_conf_reason(m)` in `scripts/update_picks.py` so 5–7 game `MODEL_ELO_THIN` rows (`1081741` locked IN vs ZennIT, `1081742` Senshi eSports vs Coalesce) are counted consistently in both `unresolved.reasons` and `unresolved.low_confidence_reasons` (`Cross-league comparison: 9`, `Thin history (<8 games in 365 days): 2`, zero `"Other model uncertainty"` drift); synced `DEFAULT_ALIASES` fallback in `scripts/model.py` with `data/aliases.json`; documented full findings in `research/line-by-line-audit-2026-10-25.md` §7 and `research/betting-sources.md` §25.
- **A2 (Mobile stacked-table labels, live bindings & broken relative-link elimination):** Added `data-label` attributes to every static and JS-rendered `<tbody>` `<td>` across all 7 HTML pages and `docs/assets/app.js` (so CSS `@media (max-width:700px)` stacked mobile cards never render unlabelled cells); removed the redundant sourceless inner `<table>` inside `#unresolved-summary` on `docs/index.html` while keeping `#exec-league-limits-body` (with verified external `https://` source links on every row); surfaced `Blended Elo` (`standings_blend.blended_elo1`/`blended_elo2`), both teams' raw decimal odds (`odds_team1`/`odds_team2`), and `elo_known`/`elo_prior` sample breakdown on `docs/match.html`; replaced broken `../research/*.md` links across `docs/` with canonical GitHub blob URLs; bound prose counts on `methodology.html` / `leagues.html` / `flagged.html` to live `picks.json` values; and unified `viewport-fit=cover` + `color-scheme: light dark` across all 7 pages. Also replaced the dead seasonal Polymarket Prime League 1st Division link (`HTTP 404`) in `docs/flagged.html` `A12` with the live Gamma LoL events endpoint (`HTTP 200`) + dated failure evidence link.
- **A3 (Non-vacuous regression coverage):** Added static DOM contract rules `C6` (`viewport-fit=cover` + `color-scheme` on all 7 pages), `C7` (every static `<tbody>` `<td>` carries `data-label`), and `C8` (no `../` parent-escape relative links in `docs/`) with 3 negative self-tests in `verification/test_dom_contract.py` (`9/9`); added runtime jsdom assertions across all 7 rendered pages in `verification/check_dom_render.js` (`89/89`); and added low-confidence reason-tally parity assertion in `audit/test_model.py` (`24/24`).
- **Combined tree verification (after merging `origin/main` through PRs #67, #68, #70, #71, #72, #76):** `check_dom_contract.py` PASS · `test_dom_contract.py` `9/9` · `test_verifier.py` `64/64` · `test_lobby_union.py` `5/5` · `test_evidence_scope.py` `8/8` · `test_entity_and_books.py` `17/17` · `test_standings_model.py` ALL PASS · `audit/test_model.py` `24/24` · `verify_site.py` `49 PASS / 0 FAIL` · `render_check.cjs` PASS · `check_dom_render.js` `89/89` · `test_freshness.cjs` `10/10`.


---

---

**Final combined evidence integration (14:46 UTC):** full union-aware run [40203413920](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40203413920) SUCCESS: 156 fixtures, 9 market, 147 model, 54 standings, 11 Low, 0 unresolved; verifier 52 PASS / 0 FAIL, blocked-source warning only, zero dead links. Main then merged #67/#76 evidence-age disclosure and another real-browser audit. Retained input collection timestamps/degraded-cache warnings, recent historical competition links, neutral exact ties, passed-lock labels, new source findings and both browser harnesses; source authority/null official-confirmation metadata remains additive. A12 correction combined by retaining the explicit attempted path, observed 404 and working publisher/check links. All other text conflicts used the more limited “no usable line found by configured adapters” phrasing. Adopted main's generated files until next refresh. No new source quote or outcome inferred.

### Session arena/81e6a4e3 — publication complete (2026-10-25)

| Item | Verified result / source |
|---|---|
| PR | [#67](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/67) **MERGED** 2026-10-25T14:43:30Z; merge commit `bc38b0b8c9430058fa60bd6dfd2314328dc24c53` |
| Final combined branch verification | [40203290312](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40203290312) **SUCCESS**; 50 PASS / 0 FAIL / 1 WARN (blocked sources), DOM 78/78, real Chromium 28/28, 50/50 cited wiki pages exist, union and independent coverage gates pass |
| Pages deployment of merged site | [40203578912](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40203578912) **SUCCESS**, Jekyll build and deploy both successful for `bc38b0b` |
| Post-merge verification of live site | [40203579452](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40203579452) **SUCCESS**, including external source/live Pages checks, both DOM suites, real phone/tablet browser gate, source-page audit and coverage tests |
| Production automatic publisher | [40203579379](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40203579379) **SUCCESS**; snapshot 2026-10-25T14:45:47Z: 156 fixtures, 9 market, 147 model, 54 standings/blend, 0 unresolved, 11 Low, 9 cancelled excluded; next nominal refresh 18:00 UTC |
| Pages deployment of refreshed payload | [40203768505](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40203768505) **SUCCESS**, source commit `53a6dbf7c21303742f1b9fb8d2ef9c61f0cbb709` |
| Site | https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/ · [all picks](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/picks.html) · [Flagged](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/flagged.html#evidence-limits) |
| Remaining limitations | **needs review**, not blockers: 147 model rows lack retrieved bookmaker lines; blocked books' coverage is unknown; community results are not independently organizer-verified; exact ties/unresolved rows have no preferred team. Flagged page/source links disclose these limits. No bookmaker line was fabricated. |
| Tasks V1–V4 | **done**; all implementation, integration and publication checks complete |

The follow-up commit containing this record changes documentation only. It does
not regenerate, manually patch, or replace the already published source data.

### Publication gate — PR #75 (`arena/c1e74f5e`, 2026-10-25)

Final **full integrated** pipeline [40203809275](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40203809275) **SUCCESS** (2m54s): all live fetches, both real Chromium suites, JSDOM, source/page verification, lobby-union tests and independent coverage gate passed. Snapshot `2026-10-25T14:48:26Z`: 156 fixtures, 9 market, 147 model, 54 Elo+standings, 11 Low confidence, 0 unresolved. Broader probe 43 candidates. Verifier **52 PASS / 0 FAIL / 1 WARN** (7 host-blocked URLs, no 404/410); arithmetic/provenance and official-confirmation-null gates passed on all rows. Local combined suites: verifier 74/74, JSDOM 82/82, phone/browser 78/78, independent browser all layouts PASS, evidence-scope 8/8, provenance/CSS 5/5, entity/books 17/17, model 23/23, freshness 10/10, union ALL PASS.

Main advanced only through generated files and publication notes after that tested code base (`bc38b0b` → `0c33092`): this final reconciliation retains the **tested 14:48:26 payload/coverage/log as a unit** and both sessions' append-only publication records. No source, model, website or workflow code changed after the successful integrated run. This artifact-only commit uses `[skip ci]` to avoid re-fetching sources and racing another generated-file commit; all local invariants are rechecked before merge. PR: https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/75 . Merge and Pages result will be appended after the operation.


### PR #75 merged; production and Pages verified (`arena/c1e74f5e`, 2026-10-25)

| Item | Confirmed result |
|---|---|
| Feature PR | [#75](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/75) **MERGED** 2026-10-25T14:51:04Z; merge commit `6603cee2f438f001d984ee3625077d252559f973`. No owner approval wait. |
| Final pre-merge complete CI | [40203809275](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40203809275) **SUCCESS**: fresh sources, 82/82 JSDOM, 78/78 mobile suite plus independent real-browser suite, source verification, model/evidence/unit tests, and union-aware independent coverage gate. No dead external links; host-blocked references remain explicit warnings. |
| Post-merge main verification | [40204165842](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40204165842) **SUCCESS**, including the live GitHub Pages URL, PWA/site contracts, external links, cited pages and both browser suites. |
| Merge Pages deployment | [40204165046](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40204165046) **SUCCESS**, exact source commit `6603cee`; GitHub Pages API matched this commit during deployment. |
| Production six-hour publisher | [40204165856](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40204165856) **SUCCESS** (2m21s); refresh commit `0c31956`, payload `2026-10-25T14:53:17Z`: 156 fixtures, 9 external-market estimates, 147 model estimates, 54 standings blend, 11 Low, 0 unresolved; 43 probed candidates; official-results-confirmation remains null on all 156 rows. Schedule stays `0 */6 * * *` (00/06/12/18 UTC). |
| Public dashboard | https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/ — direct picks `/docs/picks.html`, unverified match evidence `/docs/flagged.html#official-results-audit`, unresolved/limitations `/docs/unresolved.html`. |
| C1 / C2 / C3 / C4 | **done**. Primary-organizer result-by-result confirmation remains **needs review**, explicitly published with blank official-confirmation fields; not silently represented as verified. |

This record-only follow-up changes no website, model, workflow or generated value. The primary PR is merged and the deployed feature code, production publisher and live-site verifier have all succeeded. Runtime deprecation/Ubuntu migration annotations are infrastructure notices, not failed checks; both browser suites ran successfully on the current runner.

### Session `arena/57975298-lolhotspawn2` — T27–T30 close-out: PR #83 MERGED, main pipeline + Pages verified (recorded 2026-10-25)

| Item | Confirmed result |
|---|---|
| Feature PR | [#83](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/83) **MERGED** 2026-10-25T15:20:28Z; merge commit `47a9205`. Merged autonomously without waiting for owner approval (`mergeable=true`, 3 merges of `origin/main` resolved keeping both sides). |
| Pre-merge branch verification | [40205638717](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40205638717) **SUCCESS** on `f73a1d9`; verifier 52 PASS / 0 FAIL / 1 WARN (7 host-blocked URLs, **0 dead 404/410**), X1 34/42 sources 2xx. |
| Local gates on the final merged tree | `verify_site.py` **51 PASS / 0 FAIL / 0 WARN / 1 skip** · `check_dom_render.js` **98/98** · `render_check.cjs` PASS · `check_dom_contract.py` PASS · `test_dom_contract.py` 7/7 · `test_verifier.py` **74/74** · `test_evidence_scope.py` OK · `test_provenance.py` OK · `test_entity_and_books.py` 17/17 · `test_standings_model.py` ALL PASS · `audit/test_model.py` 23 · `test_lobby_union.py` 5/5 · `test_freshness.cjs` PASS |
| Post-merge `main` verification | [40206470192](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40206470192) **SUCCESS** on `47a9205` (live sources, external link check, both DOM suites). |
| Pages deployment of the merged site | [40206469662](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40206469662) **SUCCESS** for `47a9205`. |
| Live-site confirmation (read after deploy) | [Executive summary](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/index.html) serves the new no-line count (**147** of **156**) plus `#unresolved-summary`; [methodology](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/methodology.html#what-this-site-promises) serves all **12** requirement rows; [Flagged](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/flagged.html) serves the L1–L6 line-source re-test section. |
| Production six-hourly publisher after merge | [40206470193](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40206470193) **SUCCESS**; refresh commit `7a82d49` (`picks: scheduled refresh [skip ci]`), payload `2026-10-25T15:22:49Z`: **156 fixtures, 9 market, 147 model, 54 standings blend, 11 Low, 0 unresolved, 9 cancelled excluded**, 42 probed candidates. Re-verified on this branch after fast-forwarding to `7a82d49`: verifier **51 PASS / 0 FAIL**, DOM **98/98**. |
| Work shipped by T27–T30 | New **line-source re-test** for the 147 no-line fixtures (Flagged `#line-source-retest-2026-10-25`, L1–L6; `research/betting-sources.md` §26); executive-summary **no-line count paragraph** with in-site links; the 12-row **requirement → proof** table at `docs/methodology.html#what-this-site-promises`; A12 / Everygame dead-link removal (no URL published that we did not actually read); README probe-count correction. |
| Remaining limitations (needs review, not blockers) | The 147 model rows still have **no retrieved bookmaker line** — no accessible established book, esportsbook, odds-comparison site or prediction market priced them on 2026-10-25 (Cloudbet "no events", OddsPortal archive-only, bmbets/betmonitor no PRM board, Rainbet blocked locally while CI gets HTML, Everygame LoL paths 404, Polymarket lists only Worlds + LGC Rising). 7 sources are **host-blocked (403/Turnstile), not dead**; they stay `WARN` on X1, not `FAIL`. Community results/standings remain not organizer-verified. No value was inferred or filled in. |
| Tasks T27 / T28 / T29 / T30 | **done**, all implementation, integration, merge and deployment checks complete. |

This record changes documentation only; it does not regenerate, patch or replace the published payload.

**Close-out addendum (terminal record):** the close-out record above merged as PR [#85](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/85) → merge commit `90e7753` at 2026-10-25T15:23:57Z, and its Pages deployment [40206741369](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40206741369) succeeded. This addendum is documentation-only and is the final board entry for this session: PR #83 (feature) and PR #85 (record) are both merged, `main` is green, and the six-hourly publisher continues on `0 */6 * * *`. No further recording chain is required.

---

## Session `arena/e5e9f360-lolhotspawn2` — 2026-10-25 (claim: independent row audit + fresh low-tier line sweep)

> Branch note: Arena fixes this session to `arena/e5e9f360-lolhotspawn2`; that branch stands in for the
> `session-<id>/<task>` convention. Claim written and pushed **before** any work started (14:5x UTC).
> Baseline at claim: `origin/main` = `4914cb1` (PR #70 merged), payload generated `2026-10-25T14:29:06Z`:
> **156 fixtures · 156 resolved · 0 UNRESOLVED · 9 market rows (8 MARKET_CONSENSUS + 1 MARKET_SINGLE) ·
> 92 MODEL_ELO · 53 MODEL_ELO_STANDINGS · 2 MODEL_ELO_THIN · 11 low-confidence · 9 cancelled excluded**.
> 13 PRs from other sessions are open (#20/#26/#48/#50/#55/#59/#61/#64/#67/#68/#71/#74/#75). This session
> edits **only new files** plus one additive block, so no other session's scope is touched.

| Task | Status | Owner | Files (claimed scope — all NEW unless noted) |
|---|---|---|---|
| T44 Independent row-by-row auditor of the published payload: recompute each market row's de-vig **and** consensus from the decimals the row itself cites, guard against Hotspawn crowd-percentage leakage into any probability, cross-foot `counts` / `coverage` / `league_breakdown` against `matches`, verify pick == argmax, probabilities sum to 100%, every row carries ≥1 official source link, and publish the result as a machine-readable + human-readable audit | claimed | arena/e5e9f360 | `scripts/audit_rows.py`, `verification/row_audit.json`, `verification/row_audit.md`, `.github/workflows/row-audit.yml` |
| T45 Fresh 2026-10-25 low-tier line sweep of candidates **no session has probed before** (Oddsdigger, EsportBet odds board, the BetOnline/Bovada-family coupon API, Everygame, Sofascore events API, rft.gg, 1xBet LineFeed geo-block evidence, non-Unibet Kambi operator slugs, bmbets PRM 2nd/3rd Division, Betmonitor PRM 3rd Division), fixture-matched against the published list; nothing promoted without a structured feed + human-verifiable sample | claimed | arena/e5e9f360 | `scripts/probe_lowtier.py`, `.github/workflows/lowtier-sweep.yml`, `data/diag/lowtier_sweep.json`, `research/low-tier-sweep-2026-10-25.md` |
| T46 Live cross-check of every priced row against the book's own feed, re-read today **from outside CI** (Kambi/Unibet event JSON decimals, Polymarket's own open-market count, Hotspawn lobby tier/tournament filter counts vs the priced list) | claimed | arena/e5e9f360 | `verification/live-cross-check-2026-10-25.md`, one additive block in `docs/unresolved.html` |
| T47 Integration: live pipeline on this branch, all offline suites green, PR → `main`, merge without waiting, confirm GitHub Pages deploy, record PR/run/deploy links here | claimed | arena/e5e9f360 | `COORDINATION.md` (board entries only), CI-generated `docs/data/picks.json`, `data/diag/**`, `verification/report.json`, `verification/last_report.md` |

Requests to other sessions' files: **none**. If T44/T45 finds a defect whose fix belongs in `scripts/model.py`,
`scripts/fetch_markets.py`, `scripts/fetch_hotspawn.py`, `docs/assets/app.js` or `scripts/verify_site.py`, it is
logged here as a request instead of being edited.

### T44–T46 done (this session) — results, evidence, and two change requests

| Task | Result | Files |
|---|---|---|
| **T44** independent row-by-row auditor | `scripts/audit_rows.py` re-derives every row's arithmetic **offline** from the numbers that row cites: 21 rules (R1–R16 + R1b/R7b/R8b/R8c/R9b). On the committed payload (`2026-10-25T14:29:06Z`, 156 rows): **20 PASS · 0 FAIL · 0 WARN · 1 INFO · 0 UNVERIFIED**. The single INFO is R11: 108 rows carry Hotspawn's placeholder tier string. Key evidence: 24/24 cited decimals re-convert to the probability published for that source (R4); 9/9 market consensuses recompute (median with ≥3 books, weighted mean otherwise — R5); `counts`/`coverage`/all 12 `league_breakdown` rows re-foot (R9/R9b/R10); no cancelled fixture is priced (R12); **R7 crowd-leakage guard: mean \|published − Hotspawn crowd\| = 0.3672 over the 147 model rows, 0 rows (0.0%) within 0.5 pt** — the crowd percentage is demonstrably not the probability. New rules R15/R16 recompute each row's published book-time spread and per-source start delta from the timestamps the row itself cites (both PASS → our arithmetic is internally consistent; see X1). | `scripts/audit_rows.py`, `verification/row_audit.json`, `verification/row_audit.md` |
| **T44 tests** | `verification/test_row_audit.py`: **32/32 negative self-tests** — every rule is run against a payload mutated to break it and must FAIL (a green audit can never mean "the auditor stopped working"). | `verification/test_row_audit.py` |
| **T45** fresh low-tier line sweep | `scripts/probe_lowtier.py`: 19 candidate endpoints no session had probed before, one polite GET each, fanned over 5 workers; asks each one about the **147 fixtures with no book line** (105 team names, 102 of them ≥6 chars so a 3-letter fragment cannot fake a hit). Only two-way match-winner offers are parsed (`Map Handicap` / `Total Maps` / 3-way rejected); a price counts only if it matches one of our unpriced fixtures through the production matcher (`probe_lines.FixtureIndex`, similarity ≥0.82, ±48 h); malformed prices are skipped, never coerced; every hit carries its `source_ref` **and** the fixture link. Writes `data/diag/lowtier_sweep.json` + `research/low-tier-sweep-latest.md`, always exits 0. **Sandbox has no route to these hosts, so no sweep artifact was committed from here** — the first real measurement comes from CI. | `scripts/probe_lowtier.py`, `data/diag/lowtier_sweep.json` (CI), `research/low-tier-sweep-latest.md` (CI) |
| **T45 tests** | `verification/test_lowtier_sweep.py`: **42/42**, incl. synthetic Kambi/Bovada/LineFeed/SofaScore bodies that must match the *real* fixture `1079027` (Babos Gaming vs Hannover Esports e.V., PRM 2nd, 1.85/1.95, similarity 1.0), child-prop rejection, American→decimal conversion, malformed-row skip, verdict wording for HTTP 200/200.5/200.75/200.9/401/403/404/410/203/0, and `probe_one`/`sweep` behaviour on an unroutable host. | `verification/test_lowtier_sweep.py` |
| **T45 CI** | **Scope change, logged:** the sweep is a step inside `.github/workflows/row-audit.yml` rather than a separate `lowtier-sweep.yml` — one workflow runs both gates (negative self-tests → row audit → live sweep → job summary → artifact upload → commit artifacts back **only** on a non-main push, with a 3-attempt fetch/merge `-X ours`/push retry and a hard failure if all three fail). Triggers: push to non-main branches (path-filtered), pull_request (same paths), `schedule: 45 */6 * * *` (15 min after the 6-hour publisher), `workflow_dispatch`. | `.github/workflows/row-audit.yml` |
| **T46** live cross-check from outside CI | `verification/live-cross-check-2026-10-25.md`: all **8 of 8** Kambi/Unibet decimals re-read exact from the book's own feed on two operator/market pairs (`ub`/GB and `ubca`/ZZ), Polymarket's own hub lists exactly the **9** open LoL events we price (de-vig agrees to 0.2–0.3 pt over 8 minutes of drift), Hotspawn lobby **234 = 156 priced + 78 played**, and 0 of 156 rows cite a Leaguepedia page other than their own tournament. Pinnacle (401 without the key) and Bovada (empty body on this path) are recorded as **UNVERIFIED from this network path**, not as absent. Plus the dated low-tier sweep `research/low-tier-sweep-2026-10-25.md` (20 endpoints measured by hand today, all empty/blocked/geo-stubbed/client-rendered). | `verification/live-cross-check-2026-10-25.md`, `research/low-tier-sweep-2026-10-25.md`, additive block `#recheck-2026-10-25` in `docs/unresolved.html` |

### Irregularities published this session (X1–X5, all on `docs/unresolved.html#recheck-2026-10-25`)

* **X1 — two rows carry a start-time warning the source no longer supports.** Rows `1075819` and `1075818` are flagged
  `START_TIME_DISAGREES_WITH_BOOKS`, and four 25 Oct rows publish `time_spread_hours` 1.0/3.0, all from Unibet
  `start_utc` values recorded at 14:29Z (the four Oct-25 World Championship starts were pairwise swapped against
  Hotspawn). Re-reading the **same Kambi event ids** at ~15:45Z on both feeds returns starts that agree with Hotspawn
  exactly (17:00 / 18:00 / 19:00 / 22:00 UTC) while prices and event URLs are unchanged → upstream drift between
  generation and re-read, not our arithmetic (new auditor rules R15/R16 PASS, which is what proves internal
  consistency). Expected to self-clear on the next 6-hour refresh; **no manual edit made**.
* **X2 — `start_delta_hours` is unsigned** (see request 2 below).
* **X3 — 108 of 156 rows carry Hotspawn's own placeholder tier string** `waiting for information`, rendered as
  "Tier not published" and flagged `TIER_UNVERIFIED`; no tier is invented.
* **X4 — behind 10 rows the Elo was built in a different competition than the fixture** (`CROSS_LEAGUE_MODEL`); across
  all 156 rows, 236 team-sides have their most recent recorded series elsewhere (e.g. `1079054` partly from
  *Kanji Cup 2026*, `1080934` partly from *Arabian League Spring Split*). Disclosed on the row; the **citations** are
  unaffected — 0 of 156 rows link a foreign league page.
* **X5 — the 78 already-played lobby fixtures were not itemised card by card** in this pass (their total reconciles and
  the union gate D21 covers "no upcoming fixture missing"); left open rather than asserted.

### Requests to files owned by other sessions (not edited here)

1. **`scripts/fetch_hotspawn.py` (~line 91, owner PR #71)** — when the lobby API returns no tier, the placeholder string
   `"waiting for information"` is upper-cased into the payload's `tier` field, so 108 rows carry a non-tier value that
   every consumer must know to suppress (`docs/assets/app.js` already does, via `/^WAITING/i`). Cleaner: publish
   `tier: null` plus an explicit `tier_source: "unpublished"`. Cosmetic only — nothing downstream reads it as strength.
2. **`scripts/model.py` (~lines 685 and 730, owner PR #67)** — market matching uses
   `delta_h = abs((fstart - rec_start).total_seconds())/3600` and publishes `round(delta_h, 1)`, so a book whose start is
   **earlier** than Hotspawn's reads as a positive offset (row `1075816`: Unibet 17:00Z vs fixture 18:00Z → published
   `1.0`, not `-1.0`). Request: keep the ±36 h match window and the >1.5 h flag on the absolute value, but publish the
   **signed** delta so the match page's "start time by source" card can say earlier/later. Both timestamps are already
   printed, so this is a readability fix, not a correctness one.

### Cross-scope minimal fix made this session (logged, one line of content)

* **`docs/flagged.html` row A12 cited a dead link.** `https://polymarket.com/esports/league-of-legends/prime-league-1st-division`
  now returns **"Page not found"** (re-read 2026-10-25 ~16:15Z; CI's own committed `verification/last_report.md`
  @ `14:27:55Z` records it as `-> 404`, which is why that report says **FAIL** on X1). Because X1 fails *every* branch
  that runs `verify_site.py --check-external`, the row was repaired rather than left: A12 now cites the two pages that
  were actually read today — the LoL hub (exactly **9** open events: 8 Worlds + 1 LGC Rising) and Polymarket's Gamma
  `public-search?q=prime%20league` (PRM **1st** Division markets, all **closed**, e.g. `lol-big1-g2nord-2026-08-27`) —
  and its text states that PRM 2nd/3rd Division is not covered, so Polymarket cannot price the 95 PRM rows. Sessions
  #67/#71 touching `docs/flagged.html`: this is additive to that one `<td>` pair; keep it or replace it with a live
  link, but do not restore the 404. `research/betting-sources.md` and `research/line-by-line-audit-2026-10-25.md` still
  quote the dead URL in prose; they are not HTTP-checked by the site verifier, and both are owned by other sessions, so
  they were left alone (request: update the same URL there when convenient).
* `verification/report.json` / `verification/last_report.md` were **left untouched** even though a local run of the same
  command rewrote them to PASS: they are CI-owned, and the local run cannot perform X1 (this sandbox has no route to the
  internet), so its report would be missing exactly the check that main's copy failed. The next `pipeline-test` run on
  this branch regenerates both with `--check-external` and should show X1 PASS now that the 404 link is gone.

### Gates re-run locally before push (all green)

`scripts/verify_site.py` **47 PASS · 0 FAIL · 0 WARN · 1 SKIP** (D18 skips without `--leaguepedia-schedule`) ·
`verification/check_dom_contract.py` PASS · `test_dom_contract.py` 7/7 · `test_verifier.py` 55/55 ·
`test_entity_and_books.py` 17/17 · `test_standings_model.py` ALL PASS · `audit/test_model.py` 23 passed · 0 failed ·
`node verification/render_check.cjs` RENDER CHECK PASS · `node verification/check_dom_render.js` 65/65 ·
`verification/test_row_audit.py` 32/32 · `verification/test_lowtier_sweep.py` 42/42.

### T47 in progress — rebase onto `main`, conflicts, and what the newer payload showed

* **Rebased** this branch onto `origin/main` = `f91c3ff` (174 commits past the `4914cb1` baseline this session
  claimed at). Three conflicts, all resolved by keeping both sides' work:
  * `COORDINATION.md` — both sessions appended at the tail; kept main's entries then this session's claim block, and
    inserted the blank line before this session's `---` separator so main's last paragraph is not turned into a
    setext heading.
  * `docs/unresolved.html` — main added `#lowtier-books` (established books checked for a low-tier line) at the same
    insertion point as this session's `#recheck-2026-10-25`; **both sections are kept**, main's first.
  * `docs/flagged.html` — **this session's A12 edit was dropped in favour of main's.** Main had already repaired the
    same dead Polymarket PRM 1st Division URL (its 14:40Z board entry records the X1 404 and rewrites A12 as
    "category claim not confirmed", keeping the path as `<code>` text rather than a link). Nothing was lost: the
    finding is identical, main's wording is already merged.
* **Auditor re-run against main's newer payload `2026-10-25T15:32:40Z`** (the 6-hourly publisher ran while this
  session was writing): **20 PASS · 0 FAIL · 0 WARN · 1 INFO over 156 rows** — the same result as on the
  `14:29:06Z` snapshot, on a payload that has three books per market row instead of four and two new top-level keys
  (`evidence_policy`, `input_freshness`). `verification/row_audit.{json,md}` in this commit are that newer run.
  Rule counts moved for a real reason, not a code change: R4 24 → 16 de-vig conversions and R16 33 → 25 book start
  times, both because **Bovada's coupon feed came back empty** (see X6).
* **X1 is verified cleared, not merely predicted.** In the `15:32:40Z` payload all 8 Unibet `start_utc` values equal
  Hotspawn's exactly, every `time_spread_hours` is 0.2 (Pinnacle's 15-minutes-early listing convention) and **0 rows**
  carry `START_TIME_DISAGREES_WITH_BOOKS`. No manual edit was made at any point — the 6-hourly re-read fixed it, which
  is the behaviour the site claims.
* **X6 (new): Bovada's coupon feed went empty upstream.** CI's own read at 15:30:52Z recorded
  `Bovada: status "error", count 0, "coupon feed HTTP 200 (no event groups)"`, so the eight Worlds consensus rows now
  rest on 3 books (Pinnacle, Unibet/Kambi, Polymarket) instead of 4. Consensus is still the median of the books present
  and recomputes exactly (R5 9/9): row `1075817` moved 0.273 → 0.281 with dispersion 0.040 → 0.018. This also confirms
  the empty `{}` body this session read from a second network path at 15:10Z was upstream, not a sandbox artefact.
  No code change; the feed is re-read every 6 h and the source table shows the book as `error` rather than hiding it.
* **Two repo gates this session had to comply with after the rebase** (both new on `main`, both now satisfied):
  * `check_dom_contract.py` requires `data-label` on **every** `<td>` for the mobile card layout → 36 labels added to
    the two new tables in `docs/unresolved.html`.
  * **C8 forbids parent-relative hrefs escaping `docs/`** ("break for repo `.md` files on GitHub Pages"). The working
    papers are therefore linked as `github.com/karagemop466-tech/LOLHOTSPAWN2/tree/main/verification` (and `/research`)
    with the exact filename as the link label, because a `blob/main/<file>` link to a file that only lands with this PR
    would 404 in the pre-merge X1 external-link check and fail the run. **Follow-up for whoever integrates next:** once
    this PR is merged, those four links can be flipped to `blob/main/<path>` for one-click precision — X1 will be green
    by then. `scripts/model.py` (X2 evidence) already links `blob/main` since that file is on main.
* **Gates re-run after the rebase, all green:** `scripts/verify_site.py` **51 PASS · 0 FAIL · 0 WARN · 1 SKIP** ·
  `check_dom_contract.py` PASS · `test_dom_contract.py` 9/9 · `test_verifier.py` 74/74 · `audit/test_model.py` 24/0 ·
  `test_entity_and_books.py` 17/17 · `test_standings_model.py` ALL PASS · `node render_check.cjs` PASS ·
  `node check_dom_render.js` 98/98 · `test_row_audit.py` 32/32 · `test_lowtier_sweep.py` 42/42.
  `verification/report.json` / `last_report.md` were deliberately **not** committed: this sandbox has no route to the
  internet, so a local run cannot perform X1 and its report would omit exactly the check that matters here. CI
  regenerates both with `--check-external`.

### T47 — CI results on this branch, and the third payload

| Run | Commit | Result |
|---|---|---|
| [Pipeline test 40214473175](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40214473175) | `00caae8` | **success** — `verify_site.py --check-external` **52 PASS · 0 FAIL · 1 WARN · 0 SKIP**; the single WARN is X1 reachability with **0 dead links** (8 hosts blocked automated requests: `lol.fandom.com` 403 ×6, `oddsportal.com` 503). The 404 that made `main`'s committed report say FAIL is gone. Live pipeline, jsdom render checks and all unit suites ran green. |
| [Row audit & low-tier sweep 40214473210](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40214473210) | `00caae8` | **success** — first live measurement of the new sweep: **19 candidates · 7 HTTP 200 · 0 readable two-way prices · 0 matches against the 147 unpriced fixtures · 102 team names scanned**. Artifacts committed back to this branch as `30f6d04`. |
| [Line-source probe 40214473223](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40214473223) | `00caae8` | **success** (`14e3d00`). |

* The branch pipeline also regenerated the payload: **`2026-10-25T17:03:55Z`, 139 upcoming fixtures · 8 market rows ·
  131 model rows · 0 unresolved · 18 cancelled excluded · lobby reconciliation 234 = 139 + 95 with both difference
  lists empty**. 17 fixtures left the upcoming list because they started or finished (PRM 3rd 59 → 50, PRM 2nd 36 → 34,
  Tunisian 20 → 15, and the Invictus Gaming vs Hanwha Life market row), not because coverage regressed.
* `scripts/audit_rows.py` re-run on that payload: **20 PASS · 0 FAIL · 0 WARN · 1 INFO over 139 rows** (INFO = R11,
  94 rows with Hotspawn's placeholder tier). Three consecutive payloads — 156, 156 and 139 rows, four books then three
  then three — audit clean with no change to the auditor, which is the point of the exercise.
* **Push races (logged, nothing discarded):** two `git push` attempts were rejected non-fast-forward because CI had
  committed artifacts to this branch in between (`9936e5a pipeline: test run [skip ci]`, `14e3d00 diag: line-source
  probe [skip ci]`, plus their merge commits). Each was resolved with `fetch` → `rebase` → `push`; no CI artifact and no
  other session's work was overwritten. `verification/report.json` / `last_report.md` keep CI's versions.

### T47 done — PR #87 merged, Pages live, and the follow-up that closed the loop

| Step | Result |
|---|---|
| PR | [#87](https://github.com/karagemop466-tech/LOLHOTSPAWN2/pull/87) `arena/e5e9f360-lolhotspawn2` → `main` |
| Merge | **MERGED** 2026-10-25T17:12:15Z, merge commit `4cf3e73` (no approval waited for, per the standing brief) |
| GitHub Pages | [pages build and deployment 40215326580](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40215326580) **success** |
| Live check | <https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/unresolved.html> fetched after deploy: `#recheck-2026-10-25` renders both tables — the six re-check rows (Kambi 8/8, Polymarket 9, lobby 234 = 156 + 78 / 139 + 95, auditor 20 PASS, Pinnacle+Bovada unverified-from-this-path, no low-tier line anywhere) and irregularities **X1–X6**, each with its source link |
| Post-merge main runs | [Verify picks and site 40215327352](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40215327352) **success** · [Update Hotspawn LoL picks 40215327379](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40215327379) **success** (payload `2026-10-25T17:14:35Z`, 139 fixtures) · [pages build 40215521364](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40215521364) for that payload |
| Auditor on the 4th consecutive payload | `2026-10-25T17:14:35Z`, 139 rows → **20 PASS · 0 FAIL · 0 WARN · 1 INFO** (INFO = R11 placeholder tiers). Four payloads, 156/156/139/139 rows, four books then three, audited clean with no edit to the auditor. |

**Follow-up (this commit, PR #88):** the seven working-paper links on `docs/unresolved.html` were pointing at
`github.com/.../tree/main/{verification,research}` because a `blob/main/<file>` link to a file that only landed with
PR #87 would have 404'd in the pre-merge X1 check. The files are on `main` now, so all seven were flipped to exact-file
`blob/main` links (X1 stays green — every one of them resolves). Two cells were also tightened: the crowd-leakage
figure is stated once (`0.367`, `0 rows` within 0.5 pt, measured the same way on two payloads) instead of three ways,
and the Pinnacle/Bovada cell now points at **X6** for the Bovada outage that followed this pass. `verification/row_audit.{json,md}`
are refreshed for the `17:14:35Z` payload.

**Observation for whoever maintains `.github/workflows/row-audit.yml`:** run
[40215204630](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40215204630), triggered by a
CI-generated merge commit on the branch, finished `action_required` with **no jobs** — a pending approval that this
token could neither approve nor cancel (403 on both endpoints). It blocks nothing and the two real runs
([40214473210](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40214473210),
[40214945867](https://github.com/karagemop466-tech/LOLHOTSPAWN2/actions/runs/40214945867)) both succeeded, but if it
recurs and leaves PRs `UNSTABLE`, the fix is a job-level guard so the workflow does not queue on bot merge commits
(e.g. skip when the head commit's author is the actions bot and only generated artifacts changed).

### Standing rules honoured by this session

No Hotspawn crowd percentage and no Hotspawn price entered any probability — rule **R7** now measures that on every
run instead of asserting it (mean |published − crowd| = 0.367, 0 of 147 rows within 0.5 pt). Every new table row on
the site carries an external source link; nothing unverifiable was filled in (Pinnacle's and Bovada's rows are marked
unverified **from this network path** rather than guessed, and the 78/95 already-played lobby fixtures are recorded as
not itemised rather than listed from memory). No file claimed by another session was edited except the one-row
`docs/flagged.html` repair, which was **dropped in favour of main's own fix** on rebase. Defects belonging to
`scripts/model.py` (unsigned start delta) and `scripts/fetch_hotspawn.py` (placeholder tier string) were logged as
requests, not edits.

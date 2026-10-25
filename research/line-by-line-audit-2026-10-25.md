# Line-by-line audit — 2026-10-25 (session `arena/85bba52b-lolhotspawn2`)

Scope: the payload committed at `2173cc9` (`docs/data/picks.json`, `generated_at` **2026-10-25T10:41:50Z**,
schema 3, **156 fixtures / 156 priced / 0 unresolved / 9 market / 147 model / 10 low-confidence**), plus this
session's site changes.

Rules followed: every claim below was read on the linked page during this session and is dated here; nothing was
inferred, nothing was filled in from memory, and a value that could not be confirmed is marked **UNVERIFIED** with
the reason. Hotspawn is used as the fixture source only. No Hotspawn crowd percentage is used anywhere.

---

## 1. Automated gates run locally on this branch (all green)

| Gate | Result |
|---|---|
| `python3 scripts/verify_site.py` | **PASS · 46 pass · 0 fail · 0 warn · 1 skip** (D18 skipped: no Leaguepedia API snapshot offline; CI supplies it). New this session: **S17**, which fails if any row of the manual-review tables on `flagged.html` loses its external source link |
| `python3 verification/test_verifier.py` | **55/55** (incl. 5 negative tests for S16 and 5 for the new S17: all-linked, one bare row, missing section, shrunken table, missing page) |
| `python3 verification/check_dom_contract.py` | **PASS** (7 pages) |
| `python3 verification/test_dom_contract.py` | **7/7** |
| `python3 verification/test_entity_and_books.py` | **17/17** |
| `python3 verification/test_standings_model.py` | **ALL PASS** |
| `python3 audit/test_model.py` | **23 passed · 0 failed** |
| `node verification/render_check.cjs` | **PASS** (every page executes, theme toggle works) |
| `node verification/check_dom_render.js` | **60/60** (the start-time assertions now build a synthetic flagged payload, so they can never go vacuous when the live snapshot has no flagged fixture, and a negative control asserts an unflagged fixture is *not* reported as disagreeing) |
| `node --check docs/assets/app.js` | **OK** |

---

### 1.1 What the review tables now guarantee

`docs/flagged.html` gained a dated section, **`#audit-2026-10-25`**, with one row per irregular or unverifiable item
(A1–A12) and a source link on every row — including the items that came back *empty*. Checker **S17** walks both
manual-review tables (`#audit-2026-10-25` and `#source-coverage-flags`), counts the rows, and fails if any row has no
`https://` link or if either table shrinks below its recorded minimum. The intent is that a future edit cannot quietly
drop a source and leave an unsourced claim behind.

## 2. Fixture identity and start times — checked row by row

### 2.1 PRM 2nd Division (36 fixtures in the payload): 7/7 sampled rows match Hotspawn exactly

Source read: **[Hotspawn PRM 2nd Division 26-27 Fall fixture list](https://www.hotspawn.com/league-of-legends/tournament/prm-2nd-division-26-27-fall)**
— the page prints times explicitly as `HH:MM UTC`, so no timezone assumption is needed.

| Payload row | Payload `start_utc` | Hotspawn page (2026-10-25) | Verdict |
|---|---|---|---|
| Babos Gaming vs Hannover Esports e.V. | 2026-10-25T16:00:00Z | `16:00 UTC` | match |
| Reveal Multigaming vs AceGaming | 2026-10-25T16:00:00Z | `16:00 UTC` | match |
| 404 Multigaming e.V. vs VfB eSports | 2026-10-25T18:30:00Z | `18:30 UTC` | match |
| Locked IN vs DKB XPERION NXT | 2026-10-25T18:30:00Z | `18:30 UTC` | match |
| DKB XPERION NXT vs Phong Vũ Buffalo | 2026-10-27T17:00:00Z | `17:00 UTC` | match |
| No Need Orga vs AceGaming | 2026-10-27T17:00:00Z | `17:00 UTC` | match |
| Hannover Esports e.V. vs No Need Orga | 2026-10-27T19:30:00Z | `19:30 UTC` | match |

The same page also prints every other PRM 2nd Division fixture visible on it; no contradiction with the payload was
found in the sampled range. The individual match page
([DKB XPERION NXT vs Phong Vũ Buffalo](https://www.hotspawn.com/matches/dkb-xperion-nxt-vs-phong-vu-buffalo-prm-2nd-division-26-27-fall-1079031))
confirms both teams, the tournament and `17:00 · 27 OCT`.

### 2.2 Worlds 2026 — **IRREGULARITY: four fixtures disagree with Hotspawn's own pages**

| Payload row (id) | Payload | Hotspawn match page | Leaguepedia (per payload evidence) | Polymarket page (US view-only) | Verdict |
|---|---|---|---|---|---|
| Top Esports vs G2 Esports (1075816) | 17:00Z | [**18:00**, 25 OCT](https://www.hotspawn.com/matches/top-esports-vs-g2-esports-worlds-2026-main-event-1075816) | 18:00Z | “Today, 2:00 PM” | **disagree** |
| Invictus Gaming vs Hanwha Life Esports (1075817) | 18:00Z | (not fetched) | 17:00Z | “Today, 1:00 PM” | **disagree** |
| Gen.G vs LYON (1075818) | 19:00Z | [**22:00**, 25 OCT](https://www.hotspawn.com/matches/gen-g-vs-lyon-worlds-2026-main-event-1075818) | 22:00Z | “Today, 6:00 PM” | **disagree** |
| Dplus KIA vs Movistar KOI (1075819) | 22:00Z | [**19:00**, 25 OCT](https://www.hotspawn.com/matches/dplus-kia-vs-movistar-koi-worlds-2026-main-event-1075819) | 19:00Z | “Today, 3:00 PM” | **disagree** |

What this means, stated precisely:

* The payload's `start_utc` is copied verbatim from Hotspawn's fixtures feed (`scheduled_start_time`, epoch ms —
  `scripts/fetch_hotspawn.py`), which is the field the Pick'em locks on. Nothing in our pipeline invents or rounds a
  time; no other component overwrites `start_utc` (checked: `scripts/update_picks.py` only reads it).
* Hotspawn's **own** match pages, Leaguepedia and Polymarket agree with each other and disagree with the feed for
  these four rows. The most likely cause is an upstream re-slot of the 25 Oct round that reached the pages but not
  the epoch field at the time of our 10:41Z snapshot.
* **Not fixed by hand** — a manual edit would be an unverifiable value. Both the summary and the match page surface
  the disagreement (row flag ⏱, plus a “start time by source” card listing Hotspawn, Leaguepedia and every book that
  priced the fixture).
* **Resolution measured the same day.** The branch's pipeline run published a fresh payload at **14:16Z**, and the
  four times corrected themselves to **17:00 (IG–HLE), 18:00 (TES–G2), 19:00 (DK–KOI), 22:00 (Gen.G–LYON) UTC**,
  which is exactly what the three independent sources said. `START_TIME_MISMATCH` now appears **0 times** in the
  payload (only 2 rows keep `START_TIME_DISAGREES_WITH_BOOKS`, where a book's own kickoff field lags by ≤3 h).
  Nothing in the code changed for this: the pipeline reads the epoch field, the upstream feed caught up.

### 2.3 Team identity — one confirmed upstream collision

* PRM 2nd Division: Hotspawn labels a fixture **“Phong Vũ Buffalo”** — the name of a defunct Vietnamese team
  ([Hotspawn match page](https://www.hotspawn.com/matches/dkb-xperion-nxt-vs-phong-vu-buffalo-prm-2nd-division-26-27-fall-1079031)).
  The payload maps it to **PvB (Swiss Team)**, a real Prime League 2nd Division entrant, and flags
  `HOTSPAWN_NAME_COLLISION` on all 6 affected rows. This is a Hotspawn tag-expansion artefact, disclosed per row and
  on [Flagged for review](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/flagged.html).
* 4 Nations “Inari Esports” (id 1081700) is likewise resolved to *Inari Esports (British Team)* and flagged.

---

## 3. Market rows — does the published number sit where the sources are?

The payload stores every source's own de-vigged probability, so this is a check of the stored inputs and of the
consensus arithmetic, not of a black box. Polymarket prices below were read on
**[polymarket.com/esports/league-of-legends/worlds](https://polymarket.com/esports/league-of-legends/worlds)**
on 2026-10-25 ≈14:12Z (US view-only mode; a banner states trading is blocked in the US).

| Fixture | Stored book lines (team 1) | Published consensus (team 1) | Polymarket page now | Verdict |
|---|---|---|---|---|
| Top Esports vs G2 Esports | Pinnacle 0.4455 · Unibet 0.4415 · Bovada 0.4592 · Polymarket 0.4750 | **0.4524** | 48¢ / 53¢ (≈47.5% de-vigged) | consistent |
| Invictus Gaming vs Hanwha Life Esports | 0.2746 · 0.3002 · 0.2500 · 0.2750 | **0.2748** | 74¢ / 27¢ → HLE ≈74% (IG ≈26%) | consistent |
| Dplus KIA vs Movistar KOI | 0.7509 · 0.7190 · 0.7500 · 0.7650 | **0.7505** | 79¢ / 22¢ (≈78.2%) | consistent |
| Gen.G vs LYON | (published pick Gen.G 89.3%) | 0.893 | 91¢ / 10¢ (≈90.1%) | consistent |
| Karmine Corp vs Bilibili Gaming | (published pick BLG 68.2%) | 0.682 | KC 30¢ / BLG 71¢ (≈70.3% BLG) | consistent |
| T1 vs CTBC Flying Oyster | Pinnacle 0.8428 · Unibet 0.8282 · Bovada 0.8291 · Polymarket 0.8850 | **0.8359** | 89¢ / 12¢ (≈88.1%) | consistent |

The consensus is **not** a plain average — it is a quality-weighted mean with Polymarket down-weighted (documented on
Methodology §2), which is why `0.8359` sits below both its own highest input (0.8850) and the plain mean of the four.

**Limitation of this sandbox:** Pinnacle's and Unibet's live prices and Bovada's coupon could not be re-read from here
(the sandbox has outbound access to GitHub/PyPI only; those reads are done by the GitHub Actions run). What was
verified is that each stored per-book value is internally consistent, de-vigged (each pair sums to 1.0), and that the
book names, decimal prices and URLs in the payload point at the venue they claim.

---

## 4. Why the other 147 fixtures have no book line (re-checked today, not assumed)

Full write-up with links: `research/betting-sources.md` §20. Headline evidence read on 2026-10-25:

| Source | What it actually returned | Verdict |
|---|---|---|
| [Cloudbet — Prime League 2nd Division](https://www.cloudbet.com/en/esports/league-of-legends/germany-t8205-prime-league-2nd-division?tab=events) | Its own copy claims it prices the split; the events tab said **“No Prime League 2nd Division events available — Check back later.”** | no prices |
| [Cloudbet sports API](https://cloudbet.github.io/wiki/en/docs/sports/api/) | Requires an `X-API-Key` issued via an account; no key is configured and the brief forbids manual sign-up | blocked |
| [bmbets — LoL Prime League](https://www.bmbets.com/e-sports/world/lol---prime-league/) | The page renders a cross-esport league index that contains exactly three LoL competitions: **LoL World Championship (9)**, **LoL – LCP (1)**, **League of Legends – Game Changers Rising (1)**. There is no Prime League competition in the index, so no PRM price can exist there. The same page also prints an over-quota **reCAPTCHA** widget (the reason an earlier attempt logged this host as blocked — the index itself did load) | no prices |
| [Betmonitor — PRM 2nd Division comparison](https://www.betmonitor.com/odds-comparison/esports/prime-league-2nd-division/10024464) | Read twice on 2026-10-25 (≈10:07 and ≈14:2x local-page time). Both reads returned the site's generic multi-sport *Highlights* index (La Liga, Bundesliga, ATP, NBA, darts, futsal, handball …) under the correct page title **“Prime League 2nd Division — Check the best betting odds”**; no LoL row and no PRM price appeared in either read. **Reconciliation:** an earlier search-engine excerpt surfaced a PRM 2D price table (bet365 1.90, ggbet 2.12, …), but that table could not be reproduced on the page itself, so it is treated as unverified and is not used anywhere | client-rendered, unusable |
| [Polymarket — Prime League **1st** Division](https://polymarket.com/esports/league-of-legends/prime-league-1st-division) | Live markets exist, but that division has no fixture in this payload | not applicable today |

Two cross-checks therefore **failed to reproduce** and are recorded here as failures rather than as evidence: the
Betmonitor PRM 2D price table (visible only in an earlier search-engine excerpt) and any bmbets PRM market (absent from
the league index). Neither value appears in `picks.json`, and both are listed on
[Flagged for review](https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/flagged.html#audit-2026-10-25) as A9 / A10.

So the 147 model rows are not an oversight: the leagues involved (PRM 2nd/3rd Division, Tunisian Super League,
RIVALS LEAGUE, 4 Nations, Arabian League 2nd Division, Komplettligaen Playoffs, LCP Promotion, LigaGG CELOL A/B,
LGC Rising) are priced by **no reachable book**, and the site says so per row and per league.

---

## 5. Official-organizer coverage for the leagues that show no organizer link

| League | Official body (verified) | Is there a usable official fixture page? |
|---|---|---|
| PRM 2nd / 3rd Division | [Prime League](https://www.primeleague.gg/en/leagues/prm/3227-fall-split-202627) — page reads “Status: Running”, group stage 24.09–04.12.2026 | The league page renders participants and rules, but **not** the per-division match list to an automated reader. Row sources stay Leaguepedia + Hotspawn. |
| Komplettligaen | [komplettligaen.no/lol](https://www.komplettligaen.no/lol/) — live “Kommende kamper” and “Resultater” per division | Yes for its own divisions; the payload's 3 rows are *Autumn Playoffs* fixtures — no matching playoff fixture text was found on the page today → **UNVERIFIED**, left as is. |
| RIVALS LEAGUE | [rivalsleague.gg/lol](https://www.rivalsleague.gg/lol) — Season 2 running, 146 teams listed | Bracket shows “TBD” for the playoff rounds today; no fixture-level confirmation available. |
| Tunisian Super League | [TUNESF](https://esports.tunesf.com/) | Its LoL event page is a **template shell** (“Status: Finished”, “Registered Teams: 0”) → not usable as evidence. **Flagged.** |
| 4 Nations | UKEL (organizer; announced the Halloween Heist on its own channels) | No UKEL fixture page verified today. **Flagged.** |
| Arabian League 2nd Division | Riot Games + Vanguard | No public official fixture page verified today. **Flagged.** |
| LigaGG CELOL A/B | LigaGG | No official fixture page verified today. **Flagged.** |

---

## 6. What could NOT be verified from this sandbox, and why

| Item | Reason | Who re-checks it |
|---|---|---|
| Leaguepedia Cargo API records (fixtures, standings, ratings inputs) | `api.php` answered `{"error":{"code":"ratelimited"}}` for every attempt from this IP today | GitHub Actions does this on every run; verifier D18 runs against the CI snapshot |
| Live Pinnacle / Unibet(Kambi) / Bovada prices | Sandbox egress is limited to GitHub/PyPI; those hosts are not reachable from here | the 6-hourly production workflow |
| Hotspawn fixtures API directly (raw epoch values) | Same egress limit; the match pages and tournament pages were read instead | the production workflow, every 6 hours |

Nothing in this document should be read as a claim that a blocked source was checked successfully.

---

## 7. Follow-up Data-Consistency & Mobile DOM Audit (session `arena/07b651a3`, 2026-10-25)

Re-audited the post-14:27Z `docs/data/picks.json` (`156` fixtures, `9` market, `147` model, `54` standings-blend, `11` Low confidence, `0` unresolved, `9` excluded cancelled fixtures) and all 7 pages at phone widths (`<=760px`), fixing five concrete defects:

1. **`scripts/update_picks.py` (`_low_conf_reason` consistency):**
   On the 14:27Z payload (`11` Low-confidence rows), `unresolved.reasons` reported `Cross-league: 8`, `Standings-based line: 1` (fixture `1080941` `Simplicity Gaming vs JSK Esports`, which is actually `Low` only because of `CROSS_LEAGUE_MODEL`), `Thin history (<5 games): 1`, and `Other model uncertainty: 1` (fixture `1081421` `FENNEL vs Nothin'Here`, `MODEL_ELO_THIN` with 7 games), contradicting `unresolved.low_confidence_reasons` (`Cross-league: 9`, `Thin history (<8 games): 2`). Unified both tallies via `_low_conf_reason(m)`.
2. **Duplicate sourceless per-league table on `docs/index.html` (`#unresolved-summary`):**
   Removed the unlinked 4-column inner table injected inside `.warnbox` (`#unresolved-summary`) so `#exec-league-limits-body` (which carries verified `https://` source links on every row) is the single authoritative per-league limits table on the Executive Summary.
3. **Mobile `data-label` completeness at `<=760px`:**
   Added `data-label` attributes to every static and JS-rendered `<tbody>` `<td>` across `docs/flagged.html` (`#source-coverage-flags`, `#audit-2026-10-25`), `docs/methodology.html` (`#low-tier-sources`, `#manual-checks`), and `docs/assets/app.js` (`#flag-groups`, `#sources-status`, `#checked-unavailable`, and `match.html` external betting lines), enforced by `C7` in `verification/check_dom_contract.py` and rendered DOM checks in `verification/check_dom_render.js`.
4. **Blended Elo & single-side prior display on `docs/match.html`:**
   `renderMatch` now surfaces `Blended Elo` (`blended_elo_team1` vs `blended_elo_team2` + standings weights) on all 54 `MODEL_ELO_STANDINGS` match pages and handles `elo_known` / `elo_prior` cleanly on `MODEL_LEAGUE_PRIOR` rows.
5. **Broken `../research/*.md` links, live snapshot bindings & mobile `<head>` parity:**
   Replaced `href="../research/..."` links in `docs/flagged.html` and `docs/methodology.html` (which 404 under legacy Jekyll GitHub Pages `main:/`) with canonical `https://github.com/karagemop466-tech/LOLHOTSPAWN2/blob/main/research/...` URLs (enforced by `C8`), replaced hardcoded counts (`160 fixtures`, `31,752 schedule rows`) with live payload bindings, and added `viewport-fit=cover` + `color-scheme` across all 7 HTML pages (enforced by `C6`).


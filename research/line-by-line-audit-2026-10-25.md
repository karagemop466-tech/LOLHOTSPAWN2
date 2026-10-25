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
| `python3 scripts/verify_site.py` | **PASS · 45 pass · 0 fail · 0 warn · 1 skip** (D18 skipped: no Leaguepedia API snapshot offline; CI supplies it) |
| `python3 verification/test_verifier.py` | **50/50** (incl. 5 new negative tests for check S16) |
| `python3 verification/check_dom_contract.py` | **PASS** (7 pages) |
| `python3 verification/test_dom_contract.py` | **7/7** |
| `python3 verification/test_entity_and_books.py` | **17/17** |
| `python3 verification/test_standings_model.py` | **ALL PASS** |
| `python3 audit/test_model.py` | **23 passed · 0 failed** |
| `node verification/render_check.cjs` | **PASS** (every page executes, theme toggle works) |
| `node verification/check_dom_render.js` | **59/59** (was 50/50; +9 new assertions) |
| `node --check docs/assets/app.js` | **OK** |

---

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
* **Not fixed by hand** — a manual edit would be an unverifiable value. The next scheduled refresh (16:41Z) re-reads
  the feed. Both the summary and the match page now surface the disagreement (row flag ⏱, plus a
  “start time by source” card listing Hotspawn, Leaguepedia and every book that priced the fixture).

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
| [bmbets — LoL Prime League](https://www.bmbets.com/e-sports/world/lol---prime-league/) | Its LoL league index listed only **World Championship (9)**, **LCP (1)** and **Game Changers Rising (1)**; no PRM fixture | no prices |
| [Betmonitor — PRM 2nd Division comparison](https://www.betmonitor.com/odds-comparison/esports/prime-league-2nd-division/10024464) | Returned the site's generic football/tennis/basketball highlights; no LoL match row, no PRM price | client-rendered, unusable |
| [Polymarket — Prime League **1st** Division](https://polymarket.com/esports/league-of-legends/prime-league-1st-division) | Live markets exist, but that division has no fixture in this payload | not applicable today |

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

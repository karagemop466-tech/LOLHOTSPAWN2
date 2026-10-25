# Low-tier line sweep — 2026-10-25 (session `arena/e5e9f360`)

**Question asked:** for the fixtures we price with our own model because no betting site covered
them, does *any* reachable source publish a bookmaker line? Everything below is a measurement with
the observed result, not an assumption. Where a source could not be read, the row says so.

**Scope** (`docs/data/picks.json` generated `2026-10-25T14:29:06Z`): 156 published fixtures, of
which **147 carry no bookmaker line** (`method != MARKET_*`, and every one of them carries the flag
`NO_EXTERNAL_MARKET`), covering **105 distinct team names** across 10 competitions. The other 9 rows
are the priced ones (8 Worlds 2026 Main Event + 1 LGC Rising 2026 Playoffs) and are out of scope
here — they are cross-checked in [`verification/live-cross-check-2026-10-25.md`](../verification/live-cross-check-2026-10-25.md).

| Competition (`tournament` field, verbatim) | Rows without a book line |
|---|---:|
| PRM 3rd Division 26-27 Fall | 59 |
| PRM 2nd Division 26-27 Fall | 36 |
| Tunisian Super League 2026 | 20 |
| RIVALS LEAGUE Season 2 | 15 |
| 4 Nations 2026 Halloween Heist | 4 |
| Arabian League 2nd Division 2026 Summer | 4 |
| Komplettligaen 2026 Autumn Playoffs | 3 |
| LCP 2027 Promotion | 3 |
| LigaGG CELOL A 2026 Split 2 Playoffs | 2 |
| LigaGG CELOL B 2026 Split 2 Playoffs | 1 |
| **Total** | **147** |

Methods on those rows: `MODEL_ELO` 91, `MODEL_ELO_STANDINGS` 54, `MODEL_ELO_THIN` 2. Confidence
bands: Medium 121, High 15, Low 11. Other flags present: `TIER_UNVERIFIED` 108,
`STANDINGS_BLEND_APPLIED` 54, `THIN_HISTORY` 42, `CROSS_LEAGUE_MODEL` 9,
`HOTSPAWN_NAME_COLLISION` 6, `LEAGUEPEDIA_TIME_TBD` 5.

**Result: 0 of 147 fixtures have a published bookmaker line on any source measured today.**

---

## A. Measured today from this network path (2026-10-25, 14:30–15:55Z)

| Source | URL measured | Observed result |
|---|---|---|
| Kambi / Unibet LoL board (`ub`, GB) | <https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=GB&useCombined=true> | HTTP 200, **8 events, all `World Championship`**. No low-tier league on the board. |
| Kambi / Unibet LoL board (`ubca`, ZZ) — control feed | <https://eu-offering-api.kambicdn.com/offering/v2018/ubca/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=ZZ&useCombined=true> | HTTP 200, same 8 events, same prices. Second operator/market pair confirms the first. |
| Kambi country variants (`bs` SE, `nb` NO, `lbs`) | e.g. <https://eu-offering-api.kambicdn.com/offering/v2018/bs/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=SE> | HTTP 200, body **"No access"** — the LoL board is not licensed for those operator/market pairs. |
| Oddsdigger LoL board | <https://www.oddsdigger.com/e-sports/league-of-legends/> | HTTP 200, board = **World Championship only** (fixtures 25–26 Oct). |
| Oddsdigger PRM 2nd Division | <https://www.oddsdigger.com/e-sports/league-of-legends/prime-league-2nd-division/> | HTTP **410 Gone** — the league page has been removed. |
| Oddsdigger PRM 3rd Division | <https://www.oddsdigger.com/e-sports/league-of-legends/prime-league-3rd-division/> | HTTP **410 Gone**. |
| BMBets PRM 2nd Division | <https://www.bmbets.com/e-sports/world/lol---prime-league-2nd-division/> | HTTP 200, body contains the site index and a reCAPTCHA quota notice; **no odds rows** in the served HTML (client-rendered). |
| BMBets PRM 3rd Division | <https://www.bmbets.com/e-sports/world/lol---prime-league-3rd-division/> | HTTP **404** — the book does not have that league. |
| Betmonitor PRM 2nd Division event page | <https://www.betmonitor.com/odds-comparison/esports/prime-league-2nd-division/10024464> | HTTP 200, body is the cross-sport "Most Anticipated" list; **no PRM odds** in the served HTML (client-rendered). |
| Oddschecker esports | <https://www.oddschecker.com/esports/> | HTTP **404** — no esports comparison board. |
| EsportBet odds index | <https://www.esportbet.com/odds/> | HTTP 200, **affiliate bookmaker reviews only** — no prices. `<https://www.esportbet.com/odds/league-of-legends/>` failed to fetch at all. |
| rft.gg LoL board | <https://rft.gg/lol> → HTTP **404**; <https://rft.gg/> → HTTP 200 | Homepage lists upcoming LoL: World Championship (8 matches) + LCP 2027 Promotion (2). **No odds anywhere on the page** — fixture/result coverage only. |
| Polymarket LoL hub | <https://polymarket.com/esports/league-of-legends> | HTTP 200, **"LoL (9)"** = LGC Rising (1) + Worlds (8). Nothing else open. |
| Polymarket search "prime league" | <https://gamma-api.polymarket.com/public-search?q=prime%20league> | HTTP 200, Prime League **1st** Division markets only and **all closed** (e.g. `lol-big1-g2nord-2026-08-27`, endDate 2026-08-27). |
| Pinnacle guest API | <https://guest.api.arcadia.pinnacle.com/0.1/sports/12/leagues?all=true> | HTTP **401** `No authorization token provided` without `x-api-key`; `/0.1/sports` shows E Sports = id 12 with Worlds as the only league CI can reach. |
| Bovada coupon JSON | <https://www.bovada.lv/services/sports/event/coupon/events/A/description/esports/league-of-legends?marketFilterId=def&preMatchOnly=true&lang=en> | empty object `{}` from this network path (CI reads 8 Worlds events from it). **UNVERIFIED from here**, not evidence of absence. |
| SofaScore scheduled events | <https://api.sofascore.com/api/v1/sport/esports/scheduled-events/2026-10-25> | HTTP **403** (blocked at the edge). |
| 1xBet / LineFeed | <https://1xbet.com/LineFeed/Get1x2_VZip?sports=12&count=400&lng=en&mode=4&country=71&getEmpty=true> | redirected to `1xbet.com/en/block` — geo-blocked from this path. |
| Fon.bet line feed | <https://fon.bet/streams/v6/sports> | HTTP 200, JSON shell of sport ids; **no LoL events or prices**. |

Sources measured earlier today by a parallel session and merged into
[`research/betting-sources.md`](betting-sources.md) §22 — Cloudbet's PRM 2nd Division page
("No Prime League 2nd Division events available"; its API needs `X-API-Key`), the Tunisian
Super League page on TUNESF (template shell, no fixtures), Kalshi (no LoL markets), Manifold
(futures only), Betcity/leon.bet/Vbet (geo-block or client-rendered), Betfair/Smarkets/
SportsBetting/GG.Bet/Betway/Thunderpick/BetOnline/Betano/Winamax/Rivalry/Coolbet/Betsson/
Bet365/Marathonbet/Stake/Betano/188BET (no LoL board or blocked) — are **not re-measured here**.

## B. Queued for measurement from CI (unreachable from this sandbox)

`scripts/probe_lowtier.py` (new this session) re-asks a rotating set of 19 candidate endpoints
about the unpriced fixtures and records what came back, once per 6-hour refresh window. It is the
durable version of table A: it publishes a dated report and a machine-readable record so the
"nothing covers these leagues" claim is re-measured instead of remembered.

* Script: [`scripts/probe_lowtier.py`](../scripts/probe_lowtier.py)
* Negative self-tests (36, all passing): [`verification/test_lowtier_sweep.py`](../verification/test_lowtier_sweep.py)
* Records: `data/diag/lowtier_sweep.json` (machine) and `research/low-tier-sweep-latest.md` (human)
* It scans HTML bodies for **102** of the 105 team names — the 3 whose normalised name is shorter
  than 6 characters are excluded from string scanning so that a three-letter fragment cannot
  produce a false "this source mentions our team" hit. The three excluded names are
  `B2U`, `BvP` and `PNS`; they are still matched by the structured parsers, which compare full
  team names rather than substrings.
* Scheduled by [`.github/workflows/row-audit.yml`](../.github/workflows/row-audit.yml), which also
  runs the row-by-row arithmetic auditor over every published row.

Safety rules built into the script, because a wrong number is worse than no number:

1. Only **two-way match-winner** offers are considered. `Map Handicap`, `Total Maps`, 3-way and
   outrights are rejected by name (`T2`/`T4` in the self-tests).
2. A price must **match one of our own unpriced fixtures** by the same team-similarity function the
   production matcher uses (`probe_lines.FixtureIndex`, threshold 0.82, ±48 h). A page that merely
   mentions a team name produces **no** price.
3. A malformed price (non-numeric, ≤ 1.0, or missing a side) is **skipped**, never coerced.
4. Every hit is written with its `source_ref` **and** the link to the fixture it matched, so any
   claim is traceable to both ends.
5. Report headers and the CI job summary carry the line: **"a price found here is a line, not a
   probability — nothing in this table is used in a probability until the market matcher adopts it"**.

## C. Conclusion, stated without softening it

For the 10 competitions above there is **no reachable bookmaker line**, so no row among the 147 can
carry an external price. That is the whole content of the site's
["Unresolved picks & limitations"](../docs/unresolved.html) section, and it is why those rows are
labelled `Own estimate · community records · official results unverified`, show a
`LOW_CONFIDENCE` flag when the model's own margin is under the confidence threshold, and show
`TOSSUP` when the two sides are within `TOSSUP_MAX = 0.53`.

What the 147 rows *are* built from, with a link on every row: our Elo model over
**31,628** historical Leaguepedia/Liquipedia matches (5,484 teams rated, 365-day half-life,
prior 1469.3), plus — for the 54 fixtures where a standings table exists — that tournament's
official win/loss record and map record. Both are cited per row and re-verified by CI.

What they are **not** built from: Hotspawn's crowd percentages. The mean distance between our
published probability and the crowd number across those 147 rows is **0.3672**, and **0 rows**
land within 0.5 percentage points of it (auditor rule R7).

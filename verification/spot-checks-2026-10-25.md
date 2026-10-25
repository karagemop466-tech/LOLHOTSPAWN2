# Line-by-line verification — 2026-10-25 (session arena/964cb944)

Payload: `docs/data/picks.json` generated 2026-10-25T10:41:50Z on `main` @ `2173cc9`.
156 fixtures · 156 resolved (100%) · 0 UNRESOLVED · 8 MARKET_CONSENSUS (4 books) · 1 MARKET_SINGLE ·
92 MODEL_ELO · 53 MODEL_ELO_STANDINGS · 2 MODEL_ELO_THIN · 10 Low · 62 coin-flips (fav ≤53%) · 9 cancelled excluded.

| Check | Result | Evidence |
|---|---|---|
| `python3 scripts/verify_site.py` | **45 PASS · 0 FAIL · 0 WARN · 1 SKIP** (D18 needs CI snapshot) | includes new S16 coin-flip check |
| `verification/test_verifier.py` | 45/45 | |
| `verification/test_standings_model.py` | ALL PASS | |
| `verification/test_entity_and_books.py` | 17/17 | |
| `audit/test_model.py` | 23/23 | |
| `verification/check_dom_contract.py` | PASS | |
| `node verification/check_dom_render.js` (jsdom, real payload) | **58/58** | new: 62/62 coin-flip pills labelled, `?filter=tossup` = 62 rows, summary + unresolved counts agree |
| Market row vs live book | PASS | Mental Rush vs Vitality Rising Bees: Polymarket series ML 65¢/38¢ vs payload 64.5% pick — https://polymarket.com/event/lol-rb-mr-2026-10-27 |
| VfB eSports cross-league cluster (5/10 Low rows) | **Not a defect** | Relegated PRM 1st-Div team (base 1560) vs PRM 2nd anchors 1460–1490; flag + Low cap correct — research §20.4 |
| Cloudbet PRM-2 coverage claim | **Unverified — 0 events live** | Page says "No events available" vs 36 Hotspawn fixtures; added to CI probe — research §20.1 |
| Kalshi LoL claim (third-party article) | **Contradicted by Kalshi's own API** | Probe 2026-10-25T10:41Z: no LoL series — research §20.2 |
| Pages | `built` for `2173cc9` | https://karagemop466-tech.github.io/LOLHOTSPAWN2/ |

Flagged (non-blocking): 62 coin-flip picks are now labelled rather than hidden; Cloudbet/Kalshi claims stay
probe-only until a structured feed + human-verified sample row exists.

# Mobile & executive-summary findability audit — 2026-10-25 (session `arena/b5f85948`)

Scope: the seven published pages under `docs/`, shared `docs/assets/style.css` (431 lines) and
`docs/assets/app.js` (883 lines), against the live payload `docs/data/picks.json` (156 fixtures,
generated 2026-10-25T10:41Z). Method: static contract review of every breakpoint and tap target,
plus the jsdom harnesses `verification/render_check.cjs` and `verification/check_dom_render.js`,
which execute the real `app.js` against the real payload on all seven pages. jsdom has no layout
engine, so pixel rendering is out of scope (same disclosed limitation as the 2026-10-24 audit);
every finding below is a fact about the committed files and is backed by an automated guard.

## 1. The user's exact requirement — "find the picks easily on my phone"

| Requirement | Where it is satisfied (tap path from the landing page) | Guard |
|---|---|---|
| Executive summary links in-site to the updated picks list | Hero button **"📋 Find every pick (156)"** → `picks.html`; second hero button **"⏰ Next 24 hours (n)"** → `picks.html?filter=next24`; dedicated **"📌 Where the updated picks are"** card grid with four destinations and live counts; top nav strip; fixed 6-item bottom nav | `verify_site.py` S4, S4c, S13; `check_dom_render.js` counts bound to payload |
| Readable on a phone at 390 px | 16 px base font (no iOS input zoom), `width=device-width` viewport on all 7 pages, tables become stacked cards at `max-width:760px` with `data-label` captions, single-column stat tiles ≤380 px, full-width hero buttons ≤620 px | S2, S7, S10; `check_dom_contract.py` C6 |
| Obvious what the pick is | Each row shows both win %, a green **pick pill** naming the team and the larger probability; mobile cards put the two probabilities and pick first (`@media max-width:760px`) | D3/D4/D5; `check_dom_render.js` per-row assertions |
| Separate unresolved section + limitations, reachable from the summary | `index.html#unresolved-section` on the landing page itself (unresolved list, per-league limits, probe strip, written limitations) plus a full `unresolved.html`; hero **"⚠️ Unresolved (0)"** button and a "Where the updated picks are" card both link there | S5, S13 |
| No manual input; stays current | 6-hour cron `0 */6 * * *` (within the requested 4–8 h), freshness line + stale-after banner on every page | W1, W2 |

## 2. Independent checks performed this session

1. **Render harness (real payload, all pages):** `node verification/render_check.cjs` → RENDER CHECK PASS;
   `node verification/check_dom_render.js` → **53/53 passed**, including the theme toggle click/persist
   test on every page and the pricing-mix arithmetic (market + Elo + standings + prior + unresolved = total).
2. **No unstyled classes / duplicate ids / nav drift:** `verify_site.py` S11/S12 PASS; the header skeleton
   (`.site-header > .header-inner`) is identical on all seven pages — the 2026-10-24 clipped-header defect
   class (`.bar` wrapper) cannot recur because S14 fails any page reusing the 12 px bar rule as a header.
3. **Tap targets (390 px):** bottom nav links 60 px height in six `minmax(0,1fr)` columns with
   `env(safe-area-inset-bottom)`; top-nav pills `min-height:44px`; buttons 48 px (`btn.big` 54 px);
   `details > summary` 44 px; theme button 42×42 px. All meet/exceed the 44 px iOS HIG minimum.
4. **Horizontal-overflow sweep:** the only fixed `min-width`s (`td.teams-cell 220px`, `.probcell 130px`)
   are explicitly reset to `min-width:0` inside the `max-width:760px` card block; every `white-space:nowrap`
   is paired with `overflow:hidden; text-overflow:ellipsis` or lives in the horizontally scrollable nav;
   long source URLs are wrapped by `overflow-wrap:anywhere`; the bottom-nav labels ellipsize inside
   `min-width:0` cells. No element can force sideways scroll at 390 px.
5. **Type legibility:** body 16 px, secondary 13–14 px; the only 10–11 px text is uppercase captions,
   icon-nav labels and the logo subtitle — never body content or probabilities (probabilities render at
   15–16 px on phones).
6. **Dead-control check:** every `<button id>` has a handler (`check_dom_contract.py` C4). The theme
   toggle flips `<html data-theme>`, swaps icon/aria-label and persists to `localStorage` on all 7 pages
   (asserted by `render_check.cjs`). The 2026-10-24 dead-toggle defect is closed.
7. **Root entry:** repository-root `index.html` meta-refreshes to `docs/` and carries a manual continue
   link (S8); GitHub Pages serves the dashboard at `/LOLHOTSPAWN2/docs/` with the same payload.

## 3. Result

No new structural defect found; no markup or CSS change was required this session. The mobile/exec-summary
work completed on 2026-10-24 (shared header, "Where the updated picks are" card, stacked-card tables,
bottom nav, theme toggle, live counts) is intact and all of it is covered by CI gates that fail on
regression. The only disclosed limitation remains the absence of a real layout engine in CI (jsdom cannot
measure pixels/contrast); a physical-phone pass should find nothing structural, per the 2026-10-24 audit.

## 4. Reproduce

```bash
python3 scripts/verify_site.py --leaguepedia-schedule data/diag   # S1–S15, W1–W3, REQ1–REQ12
python3 verification/check_dom_contract.py                        # C1–C6 markup/CSS contract
node verification/render_check.cjs                                # real app.js on all 7 pages
node verification/check_dom_render.js                             # 53 render assertions
```

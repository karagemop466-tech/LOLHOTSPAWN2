# Mobile & accessibility audit — 2026-10-24

Scope: the seven published pages (`docs/index.html`, `picks.html`, `leagues.html`,
`unresolved.html`, `flagged.html`, `methodology.html`, `match.html`), the shared stylesheet
`docs/assets/style.css` and the shared script `docs/assets/app.js`.

Method: every page's markup was read against the selectors that actually exist in `style.css`, and every
selector `app.js` writes against the ids that actually exist in each page. Nothing below needs a browser to
establish — each finding is a fact about the files in this repository — and each one is now covered by an
automated check.

Two sessions audited this area on the same day. Session `arena/c38ce482` landed the shared header/nav skeleton
and the “Where the updated picks are” card on `main` first; this audit's conflicting work was reconciled onto
theirs (see *Merge note* at the end) rather than duplicating it.

---

## 1. Defects found and fixed

| # | Where | Defect | Why it mattered on a phone | Fix |
|---|---|---|---|---|
| D1 | `index.html`, `unresolved.html` | The header wrapper was `<div class="wrap bar">`, and `.bar` is the *probability progress bar* (`display:flex; height:12px; overflow:hidden`). Logo, title and primary navigation were clipped to a 12 px strip. | The landing page — the page that must lead to the picks — had a header that could not be read or tapped. | Shared `<header class="site-header"> → .header-inner` skeleton on all seven pages. `render_check.cjs` now fails if the header computes to a fixed height < 40 px or clips its content. |
| D2 | `index.html`, `unresolved.html` | Primary nav was `<nav class="top-nav"><a>…</a></nav>` with no `<ul>`; `style.css` styles `.top-nav ul` as the horizontal 40 px tap strip. | Nav links fell back to inline text: no scroll strip, uneven tap targets, wrapping on narrow screens. | Six-section `<ul>` nav on every page, one active item per page. |
| D3 | `index.html`, `unresolved.html` | The freshness/timestamp slots (`#updated`, `#freshness`) did not exist; an unscripted `#status-strip` sat there instead. | The executive summary displayed “Loading latest picks…” permanently — a reader could not tell whether the numbers were current. | Both slots exist on every page; `C5` enforces it. |
| D4 | all pages | `<button id="theme-toggle">` existed with **no handler** in `app.js` — a dead control — and the stylesheet had no theme override at all. | A button that does nothing is worse than no button, and readers had no way to override the OS theme. | Real toggle on all seven pages: flips `<html data-theme>`, swaps icon + `aria-label`, persists in `localStorage`, overrides the OS preference in both directions. `C4` fails on any handler-less `<button id>`; `render_check.cjs` clicks it on every page and asserts the flip persists. |
| D5 | `index.html` | Seven classes had **no rule** in `style.css` (`brand`, `mark`, `bar-end`, `icon-btn`, `nav-list`, `covbar`, `status-strip`). | The section cards and the coverage bar rendered as bare text. | Legacy markup replaced by the shared header classes; `.covbar`, `.icon-btn` and the link-card grid now exist. `C1` (and `verify_site.py`'s `S11`) fail on any unstyled class. |
| D6 | `index.html` | Stat tiles used `<b>`/`<span>` while the stylesheet sizes `.stat .n` / `.stat .l`. | Headline counts rendered at body size instead of as large numbers. | Markup aligned with the CSS. |
| D7 | `methodology.html` | `<table class="table">` used a class defined nowhere. | Cosmetic. | Class removed; `C1` keeps it out. |
| D8 | `index.html` | The picks list was reachable only through the (broken) nav. | The brief requires the summary itself to link to where the picks are. | **“📌 Where the updated picks are”** block at the top of the summary: all picks · next 24 h · by league · unresolved/limits, each with a live count. |

## 2. Verified already correct

| Area | Evidence |
|---|---|
| Responsive viewport | `width=device-width` on all seven pages (`C6`). |
| Wide tables on phones | `@media (max-width: 760px)` turns `table/thead/tbody/tr/td` into stacked cards with `data-label` captions (`C6` asserts the rule survives). |
| Bottom navigation | 6 links, `repeat(6, …)` grid, 60 px tap height, safe-area inset (`C2`/`render_check`). |
| Tap targets | `.btn` 48 px, `.chipbtn` 40 px, `.top-nav a` 40 px, `.bottom-nav a` 60 px, `.icon-btn` 42 px. |
| Type | 16 px base, 13–14 px secondary, `-webkit-text-size-adjust:100%`. |
| Long source URLs | `main a, .sub, .small { overflow-wrap:anywhere }` prevents sideways scroll from Leaguepedia URLs. |

## 3. Checks added

1. `verification/check_dom_contract.py` — `C1` class↔CSS coverage, `C2` header/nav skeleton + the six destinations,
   `C3` no non-header class inside the header (the D1 regression), `C4` no dead `<button id>`, `C5` the ids `app.js`
   writes on every page, `C6` mobile contracts (viewport, theme-color, table→card rule, ≥16 px body), plus the
   original id and bottom-nav-column checks.
2. `verification/test_dom_contract.py` — **7/7** negative self-tests: each rule must fail on an injected defect
   (the `.bar` header, an undefined class, a missing `#updated`, a handler-less button, a `top-nav` without `<ul>`,
   a missing viewport meta) while the untouched copy passes.
3. `verification/render_check.cjs` — extended: on every page it now also clicks the theme button and asserts
   `data-theme` flips, the choice is stored, and the `aria-label` updates.
4. `verification/check_source_pages.py` — every cited Leaguepedia tournament page must exist; Leaguepedia answers
   **200 with an empty body** for a missing title, so a URL check alone cannot certify a citation.

All four run in `.github/workflows/verify.yml`, and 1–3 also run in `.github/workflows/pipeline-test.yml`.

## 4. Merge note (coordination)

`main` moved while this audit was open: session `arena/c38ce482` had independently fixed D1/D2/D8 and added a jsdom
render harness (`verification/render_check.cjs`) plus `S11`/`S12` class-and-nav checks in `verify_site.py`.
The merge kept **their** header markup, “Where the updated picks are” card and render harness, and kept this
session's theme toggle, `C1`–`C6` contract, negative self-tests and source-page check; this session's duplicate
render harness (`render_smoke.js`) was **deleted** rather than shipped twice. Nothing was overwritten silently.

## 5. Remaining limitation (disclosed, not hidden)

There is no real browser in the CI runners. This audit covers DOM, CSS-rule presence and script behaviour, not
rendered pixels; jsdom has no layout engine and cannot measure wrapping, overlap or contrast. A manual pass on a
physical phone remains the final check — the audit is designed to leave that pass with nothing structural to find.

## 6. Reproduce

```bash
python3 verification/check_dom_contract.py      # C1–C6 contract
python3 verification/test_dom_contract.py       # 7/7 negative self-tests
npm install --no-save jsdom@24
node verification/render_check.cjs              # renders all 7 pages + theme toggle
python3 verification/check_source_pages.py      # cited Leaguepedia pages exist (network)
```

## 7. Addendum — 2026-10-25 (session `arena/419cd73a`, task T29)

One structural defect found and fixed on the executive summary.

**Defect.** Inside `#picks-here` ("📌 Where the updated picks are") the child order was
`H2 → P.small → DIV.legend → DIV.linkgrid`. The seven-chip method glossary (400+ characters)
sat *between* the heading and the four pick links. `style.css:429` collapses `.legend` to a
single column below its breakpoint, so on a 390 px phone the glossary rendered as roughly
14 lines of chip-plus-explanation before the first tappable link — exactly the "I can't find
the picks" failure the site is meant to avoid.

**Fix.** The glossary moved *below* the four link cards and into a collapsed
`<details class="hero-details">` ("What the method chips mean (tap to expand)"). Rendered
child order is now `H2 → P.small → DIV.linkgrid → DETAILS`, so the links are the first thing
under the heading. No content was removed.

**Verification (all run this session, on this tree).**

| Check | Result |
|---|---|
| `node verification/check_dom_render.js` | **55/55** (was 53; two new assertions added) |
| New assertion: *the pick links come before the method glossary* | passes at `linkgrid at 2, glossary at 3` |
| New assertion: *glossary is collapsed by default* | passes at `DETAILS closed` |
| **Non-vacuity of both** | re-inserting a `.legend` in front turns them **FAIL** (`linkgrid at 3, glossary at 2`; `DIV closed`) — 53/55 |
| `node verification/render_check.cjs` | RENDER CHECK PASS (all 7 pages + theme toggle) |
| `python3 verification/check_dom_contract.py` | PASS (7 pages) |
| `python3 scripts/verify_site.py --leaguepedia-schedule data/diag` | 44 PASS · 0 FAIL · 1 WARN (D18 stale snapshot, by design) |

**First attempt was wrong and was caught.** The initial assertion used
`k.querySelector(".legend")`, which does not match a child that *is* the legend, so a bare
`.legend` re-inserted in front of the links still passed. Replaced with
`k.matches(".legend") || k.querySelector(".legend")` and re-run against the broken layout
until it failed. The negative run above is that run.

**Still true from §5:** jsdom has no layout engine, so this is a DOM-order and CSS-rule
audit, not a pixel measurement. A manual pass on a physical phone remains the final check.

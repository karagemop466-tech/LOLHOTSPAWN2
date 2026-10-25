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

---

## 7. Re-verification — 2026-10-25 (session `arena/6e003eec`)

Re-ran the whole mobile picture after the executive summary was rebuilt, and added a check that measures the
properties a phone reader actually depends on instead of trusting them by eye.

| Property | Where it is enforced | Measured today |
|---|---|---|
| Viewport is `device-width`, not a fixed width | `C6` + `M1` | 7/7 pages |
| Nothing outside a `min-width` media query is wider than 390 px | `M3` | 0 offenders |
| Wide tables scroll inside their own box instead of pushing the page sideways | `M2` (`.table-wrap { overflow-x:auto }`) + `M4` (every table sits in a `.table-wrap`) | 6/6 tables wrapped |
| Tables become stacked cards at ≤760 px | `C6` + `M5` | rule present once, plus the `data-label` captions |
| Body copy is 16 px; nothing interactive is under 44 px tall | `M6` | `.btn` 48, `.chipbtn` 44, `.bottom-nav a` 60, `.icon-btn` 44, `.pickcard` ≥ 44 |
| Summary pick cards are tappable and readable | `check_dom_render.js` (63/63) | 6 cards, pick + whole-number probability in every card |
| The picks come before the limits text | `check_dom_render.js` (section order) | `#picks-now` → `#picks-here` → coverage → `#starting-soon` → `#unresolved-section` |

New: `verification/check_mobile_css.py` (**10 pass · 0 fail**) parses `style.css` and every page and asserts the rows
above; it runs in `pipeline-test.yml` and `verify.yml`, so a restyle that breaks the phone layout fails the build.
`verification/test_prm_probe.py` (**8/8**) is wired next to it.

Limits of this pass, stated plainly: still no real browser in CI (jsdom has no layout engine), so these are
structural facts about the CSS and markup, not screenshots. A physical-phone pass remains the last mile; nothing in
this audit claims a pixel-level result.

**What a reader sees first on a phone (390 px), in order:** the refreshed-at line and five counts
(156 matches · 156 with a pick · 9 from a bookmaker line · 147 model-priced · 0 with no pick) → the four buttons →
six "picks for the next matches" cards, each with both teams at 19 px, a pick, its probability and a tap target into
the match page → the "where the picks are" link grid → the no-book-line section with the per-league limits.

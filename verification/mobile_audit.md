# Mobile & accessibility audit — 2026-10-24 (session `arena/9d523943`)

Scope: the seven published pages (`docs/index.html`, `picks.html`, `leagues.html`,
`unresolved.html`, `flagged.html`, `methodology.html`, `match.html`), the shared
stylesheet `docs/assets/style.css` and the shared script `docs/assets/app.js`.

Method: the markup of every page was read against the selectors that actually exist
in `style.css`, and the selectors that `app.js` writes against the ids that actually
exist in each page. Every finding below is a reproducible fact about the files in this
repository — no browser was required to establish it — and each one is now covered by
an automated check (see *Verification added*).

---

## 1. Defects found (all fixed in this session)

| # | Page | Defect | Why it mattered on a phone | Fix |
|---|---|---|---|---|
| D1 | `index.html` (executive summary) and `unresolved.html` | The header wrapper was `<div class="wrap bar">`. `.bar` is the **probability progress-bar** component: `display:flex; height:12px; border-radius:999px; overflow:hidden`. The logo, page title and primary navigation were therefore clipped to a 12 px-tall strip with `overflow:hidden`. | The landing page — the one the brief says must lead to the picks — rendered a header that could not be read or tapped. | Header rebuilt to the same `<header class="site-header"> → .header-inner` structure the other five pages use. Check `C3` now rejects any non-header class inside the header. |
| D2 | `index.html`, `unresolved.html` | Primary navigation was `<nav class="top-nav"><a>…</a></nav>` with no `<ul>`. `style.css` styles `.top-nav ul` as the horizontal, scrollable, 40 px-tall tap strip. | Nav links fell back to inline text: no scroll strip, uneven tap targets, and wrapping on narrow screens. | Standardised on `<nav class="top-nav"><ul><li><a>` with the six sections, on all seven pages. Checks `C2`. |
| D3 | `index.html`, `unresolved.html` | The freshness/timestamp block targeted `#updated` and `#freshness`, which did not exist on those two pages; instead there was a `#status-strip` div that no script ever wrote to. | The executive summary permanently displayed “Loading latest picks…” — a reader could not tell whether the numbers were current. | Both pages now carry the `#updated` / `#freshness` header block; check `C5` requires those ids on every page. |
| D4 | `index.html`, `unresolved.html` | `<button id="theme-toggle">` existed but no script handled it — a dead control. There was also no theme logic anywhere: dark mode came only from `prefers-color-scheme`. | A button that does nothing is worse than no button; readers on phones in bright light had no override. | Working toggle added to all seven pages: flips `<html data-theme>`, swaps icon + `aria-label`, persists in `localStorage`, and overrides the OS preference in both directions. Check `C4` fails on any handler-less `<button id>`. |
| D5 | `index.html` | Unstyled classes: `brand`, `mark`, `bar-end`, `icon-btn`, `nav-list`, `covbar`, `status-strip` had **no rule** in `style.css`. The “site sections” cards and the coverage bar rendered as bare text. | The four big section cards (All picks / By league / Unresolved / Flagged) — the site's main navigation affordance — were unformatted text on phones. | `.nav-list`, `.covbar`, `.icon-btn` added; the legacy `brand`/`mark`/`bar-end`/`status-strip` markup was removed in favour of the shared header classes. Check `C1` fails on any class with no stylesheet rule. |
| D6 | `index.html` | The four stat tiles used `<b>`/`<span>` but the stylesheet sizes `.stat .n` / `.stat .l`. | Headline counts (matches, market rows, model rows, unresolved) rendered at body size instead of as large numbers. | Markup now uses `.n` / `.l`. |
| D7 | `methodology.html` | `<table class="table">` used a class that is not defined anywhere. | Cosmetic only — table styling comes from the element selector. | Class removed; `C1` keeps it from coming back. |
| D8 | all pages | The six primary destinations were only reachable through the top nav (D2 made it unusable on two pages) or the fixed bottom bar. | The brief asks for an executive summary that *links to where the picks are*. | New `#where` section at the top of the summary: four large tap targets with live counts (all picks, next 24 h, by league, unresolved + low-confidence), plus a `📍 Where the picks are ↓` chip in the hero. |

## 2. What was checked and found already correct

| Area | Evidence |
|---|---|
| Responsive viewport | `width=device-width` on all seven pages (`C6`). |
| Wide tables on phones | `@media (max-width: 760px)` turns `table/thead/tbody/tr/td` into stacked cards with `data-label` captions (`C6` asserts the rule still exists). |
| Bottom navigation | 6 links, `grid-template-columns: repeat(6, …)`, 60 px tap height, safe-area inset (`C2` + `C6`). |
| Tap targets | `.btn` 48 px, `.chipbtn` 40 px, `.top-nav a` 40 px, `.bottom-nav a` 60 px, `.icon-btn` 42 px. |
| Dark mode | Full variable set for dark, plus the new explicit override; `.dot.stale` / `.dot.bad` freshness states. |
| Long source URLs | `main a, .sub, .small { overflow-wrap:anywhere }` prevents sideways scroll from Leaguepedia URLs. |
| Body type | 16 px base, 13–14 px secondary, `-webkit-text-size-adjust:100%`. |

## 3. Verification added

1. `verification/check_dom_contract.py` — extended from one check (ids exist) to seven:
   `C1` class coverage, `C2` header/nav skeleton + six nav sections, `C3` no
   non-header class inside the header, `C4` no dead `<button id>`, `C5` the ids
   `app.js` writes on every page, `C6` mobile contracts (viewport, theme-color,
   table→card rule, 16 px body).
2. `verification/test_dom_contract.py` — **7/7 negative self-tests**: it copies
   `docs/`, injects one defect at a time (the `.bar` header, an undefined class, a
   missing `#updated`, a handler-less button, a `top-nav` without `<ul>`, a missing
   viewport meta) and asserts the contract fails with the right message. The
   baseline copy must pass.
3. `verification/render_smoke.js` — jsdom run of the **real** `app.js` against the
   **real** `docs/data/picks.json` on all seven pages: no uncaught errors, header
   timestamp and freshness populated, the summary counters filled, one picks row per
   fixture with an outbound source link on every row, match detail rendered, and the
   theme button flips `data-theme`, persists, and is re-applied on reload.
   **63/63 checks pass**; two injected defects (removed `#updated`, renamed theme
   button) produced exactly two failures, so the harness is not vacuous.

Both new test runners are wired into `.github/workflows/verify.yml` and
`.github/workflows/pipeline-test.yml`, so a regression fails CI instead of shipping.

## 4. Remaining limitation (disclosed, not hidden)

There is no real browser in the CI runners, so this audit covers DOM, CSS-rule
presence and script behaviour, not rendered pixels. jsdom has no layout engine:
it cannot measure wrapping, overlap or contrast. A manual pass on a physical phone
or a browser device-emulation view is still the final check, and the audit above is
designed to leave that pass with nothing structural to find.

## 5. Reproduce

```bash
python3 verification/check_dom_contract.py      # C1–C6 contract
python3 verification/test_dom_contract.py       # 7/7 negative self-tests
npm install --no-save jsdom@24
node verification/render_smoke.js               # 63/63 render checks
```

# T12 integration checklist (session arena/47334762)

Final integration runs only after the T7–T10 owner (`arena/fa3f554c`) marks its work done or its claim goes
stale (>60 min without commits). Nothing below overwrites their work; conflicts are resolved by keeping both.

## 1. Merge
- [ ] `git fetch origin` and confirm `origin/arena/fa3f554c-lolhotspawn2` is the final state of T7–T10.
- [ ] Merge it into `arena/47334762-lolhotspawn2` (merge, not rebase, to preserve their history).
- [ ] Resolve `COORDINATION.md` conflicts by **keeping both session sections** + the sources/irregularities log.
- [ ] Never delete `data/diag/**` (raw evidence for manual review) unless it exceeds repo limits.

## 2. Verify the combined data (must be 0 FAIL)
- [ ] `python3 scripts/verify_site.py` → 0 FAIL (WARN allowed; each WARN must be published on Flagged).
- [ ] `python3 verification/check_leaguepedia_coverage.py --schedule <new schedule snapshot>`
      → every unresolved row must have a Leaguepedia league page (currently 126/126).
- [ ] Confirm REQ1–REQ12 matrix; every FAIL blocks only until fixed, WARN is published.
- [ ] Confirm all 126+ unresolved rows either (a) now carry a sourced probability, or (b) are explicitly
      50/50 with a per-league limitation and a source link (no generic wiki link).
- [ ] Spot-check 5 rows by hand against their source page (teams, start time, method, probability direction).

## 3. Site
- [ ] Root `index.html` → `docs/` works; exec summary links in-site to picks + unresolved; data age visible.
- [ ] Mobile: viewport meta on every page, nav usable at 360 px, tables/cards readable, tap targets ≥40 px.
- [ ] No broken internal links (S6); external links https (S9).
- [ ] `python3 verification/check_dom_contract.py` → PASS (every id the shared JS uses exists in the HTML;
      every dynamic page includes assets/app.js; every page includes the stylesheet). This caught the new
      app.js referencing 28 ids while the old HTML only provided 8.
- [ ] Unresolved page: per-league limitations + source links + why no book prices these leagues.

## 4. CI verification (added by integration, after T7–T10 files are free)
Create `.github/workflows/verify.yml`:

```yaml
name: Verify picks + site
on:
  push: {branches: [main]}
  schedule: [{cron: "30 */6 * * *"}]   # 30 min after the picks update
  workflow_dispatch:
permissions: {contents: read}
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - name: Verify data + site (internal)
        run: python3 scripts/verify_site.py
      - name: Verify external source links + live Pages deploy
        run: python3 scripts/verify_site.py --check-external --live-url https://karagemop466-tech.github.io/LOLHOTSPAWN2/
      - uses: actions/upload-artifact@v4
        if: always()
        with: {name: verification, path: verification/}
```

- [ ] Add the workflow, commit, push.
- [ ] Confirm the workflow run is green on main (external link checks may WARN on bot-blocked hosts).

## 5. PR, merge, deploy
- [ ] Open a PR from `arena/47334762-lolhotspawn2` → `main` with: summary, sources, verification table,
      flagged irregularities, PR link.
- [ ] Merge with `gh pr merge <n> --merge` (no approval wait), then confirm Pages build success
      (`gh api repos/.../pages/builds/latest`) and that the live JSON has a fresh `generated_at`.
- [ ] Run `python3 scripts/verify_site.py --live-url ...` against production; record result.
- [ ] Record the PR link, merge result, deploy status, verification counts and any new irregularities in
      `COORDINATION.md`, then push the final commit (branch is auto-saved; main already contains the PR).

## 6. Report to the user
- [ ] `verification/FINAL_REPORT.md`: what is verified, sources (linked), coverage stats, unresolved breakdown
      with limitations, flagged items, deploy confirmation, and how to re-run everything.

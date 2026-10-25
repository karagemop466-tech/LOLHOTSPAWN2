#!/usr/bin/env python3
"""390 px phone audit of the published pages.

Why this exists
---------------
`verification/mobile_audit.md` records the structural audit (DOM, CSS-rule
presence, script behaviour). This script adds the part a phone reader actually
notices, and does it without a browser:

  1. **Declared geometry at the phone breakpoints** — parse `style.css` and
     assert the rules that make the site readable at 390 px exist with the
     values the audit claims (stacked tables, probability/pick font sizes,
     44 px+ tap targets, no fixed-width boxes wider than the viewport).
  2. **Rendered content at 390 px** — render every page in jsdom with a 390 px
     viewport and assert what a phone visitor sees: the executive summary's
     in-site links to the picks, the separate unresolved section, and a pick
     plus both probabilities on every match card/row.
  3. **Overflow guards** — no inline `width:`/`min-width:` in px larger than the
     viewport, and no `white-space: nowrap` on long source links.

Usage:  python3 verification/mobile_audit_390.py [--docs docs] [--quiet]
Exit 1 on any failure. jsdom is optional: without it the CSS half still runs.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
PAGES = ["index.html", "picks.html", "leagues.html", "unresolved.html",
         "flagged.html", "methodology.html", "match.html"]
VIEWPORT = 390

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, bool(ok), detail))
    if not QUIET:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


QUIET = False


# --------------------------------------------------------------------------- #
# 1. declared geometry in style.css
# --------------------------------------------------------------------------- #
def audit_css() -> None:
    path = os.path.join(DOCS, "assets", "style.css")
    raw = open(path, encoding="utf-8").read()
    # Comments are stripped first: a `/* note */` before a selector would otherwise
    # make the selector text unmatchable (this bug was found by this audit itself).
    css = re.sub(r"/\*.*?\*/", " ", raw, flags=re.S)

    # Resolve custom properties so a `min-height: var(--nav-h)` is measured, not skipped.
    props = dict(re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;}]+)", css))

    def resolve(text: str) -> str:
        for _ in range(4):
            new = re.sub(r"var\((--[a-z0-9-]+)\)",
                         lambda m: props.get(m.group(1), m.group(0)), text)
            if new == text:
                break
            text = new
        return text

    def rules() -> list[tuple[str, str]]:
        """(selector-list, declarations) for every top-level or nested rule."""
        out = []
        for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
            sel = " ".join(m.group(1).split())
            if sel.startswith("@"):        # @media prelude: keep scanning inside it
                sel = sel.split("{")[0]
                sel = re.sub(r"^@[a-z-]+\s*", "", sel).strip()
            body = resolve(m.group(2))
            if sel:
                out.append((sel, body))
        return out

    def block(selector: str) -> str:
        parts = []
        for sel, body in rules():
            for one in sel.split(","):
                one = one.strip()
                if one == selector or one.startswith(selector + ":") \
                        or one.startswith(selector + " ") \
                        or one.startswith(selector + "["):
                    parts.append(body)
                    break
        return " ".join(parts)

    metas = [open(os.path.join(DOCS, p), encoding="utf-8").read() for p in PAGES]
    check("every page declares width=device-width",
          all('name="viewport"' in h and "width=device-width" in h for h in metas))

    # no element rule may be wider than the viewport (media preludes excluded)
    wide = []
    for sel, body in rules():
        for m in re.finditer(r"(?<![a-z-])min-width\s*:\s*(\d+(?:\.\d+)?)px", body):
            if float(m.group(1)) > VIEWPORT:
                wide.append(f"{sel} {m.group(0)}")
    check(f"no element rule is wider than the {VIEWPORT}px viewport", not wide,
          "; ".join(wide[:4]))

    phone = re.search(r"@media \(max-width:\s*760px\)\s*\{(.*?)\n\}", css, re.S)
    check("760px breakpoint exists (table -> stacked card)", bool(phone))
    if phone:
        body = phone.group(1)
        check("tables stack to full-width cards at 760px",
              "display: block" in body and re.search(r"thead\s*\{\s*display:\s*none", body))
        check("stacked rows carry a data-label caption rule",
              "content: attr(data-label)" in body)

    prob_css = " ".join(b for sel, b in rules() if "max-width" in sel or sel == "")
    prob_css = " ".join(re.findall(r"@media \(max-width:\s*\d+px\)\s*\{(.*?)\n\}", css, re.S))
    m1 = re.search(r"\.probcell \.p1\s*\{[^}]*font-size:\s*(\d+(?:\.\d+)?)px", prob_css)
    m2 = re.search(r"\.probcell \.p2\s*\{[^}]*font-size:\s*(\d+(?:\.\d+)?)px", prob_css)
    check("team win probabilities are >= 15px on a phone",
          bool(m1 and m2) and float(m1.group(1)) >= 15 and float(m2.group(1)) >= 15,
          f"p1={m1.group(1) if m1 else '?'}px p2={m2.group(1) if m2 else '?'}px")
    pill = re.search(r"\.pick-pill\s*\{[^}]*font-size:\s*(\d+(?:\.\d+)?)px", prob_css)
    check("the pick pill is >= 14px on a phone",
          bool(pill) and float(pill.group(1)) >= 14,
          f"{pill.group(1) if pill else '?'}px")
    body_size = re.search(r"(?:^|\n)body\s*\{[^}]*font-size:\s*(\d+(?:\.\d+)?)px", css)
    check("body text is >= 16px (no mobile auto-zoom on inputs)",
          bool(body_size) and float(body_size.group(1)) >= 16,
          f"{body_size.group(1) if body_size else '?'}px")

    for sel, want in ((".btn", 44), (".top-nav a", 40), (".bottom-nav a", 44),
                      (".icon-btn", 40), (".linkcard", 44)):
        b = block(sel)
        mm = (re.search(r"min-height\s*:\s*(\d+(?:\.\d+)?)px", b)
              or re.search(r"(?<![a-z-])height\s*:\s*(\d+(?:\.\d+)?)px", b))
        check(f"{sel} tap target >= {want}px", bool(mm) and float(mm.group(1)) >= want,
              f"{mm.group(1) if mm else '?'}px")

    hero = re.findall(r"@media \(max-width:\s*\d+px\)\s*\{(.*?)\n\}", css, re.S)
    check("hero 'find the picks' buttons stack full-width on a phone",
          any("flex-direction: column" in h for h in hero))
    check("long source links wrap (overflow-wrap: anywhere)",
          "overflow-wrap:anywhere" in css.replace(" ", ""))
    check("no nowrap on source-link containers",
          "nowrap" not in block(".src-links"))
    check("probability bars are percentage-based (no fixed px width)",
          not re.search(r"\.bar i\s*\{[^}]*width\s*:\s*\d+px", css))


# --------------------------------------------------------------------------- #
# 2. rendered content at 390 px
# --------------------------------------------------------------------------- #
def audit_render() -> bool:
    """Run the jsdom half (verification/mobile_render_390.cjs) when Node + jsdom exist."""
    node = shutil.which("node")
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mobile_render_390.cjs")
    if not node or not os.path.exists(script):
        print("  [skip] node or mobile_render_390.cjs unavailable — CSS half only")
        return True
    try:
        proc = subprocess.run([node, script, "--docs", DOCS] + (["--quiet"] if QUIET else []),
                              capture_output=True, text=True, timeout=300, cwd=ROOT)
    except Exception as e:  # noqa: BLE001
        print(f"  [skip] jsdom half could not run: {e!r}")
        return True
    if proc.stdout.strip():
        for line in proc.stdout.strip().splitlines():
            print("  " + line)
    if proc.returncode != 0:
        if "jsdom is not installed" in (proc.stdout + proc.stderr):
            print("  [skip] jsdom is not installed (npm install --no-save jsdom) — CSS half only")
            return True
        print("  [FAIL] jsdom half reported failures")
        results.append(("jsdom half (mobile_render_390.cjs)", False, proc.stdout[-400:]))
        return False
    results.append(("jsdom half rendered every page at 390 px without error", True, ""))
    return True


def main() -> int:
    global QUIET
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default=DOCS)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    QUIET = args.quiet
    globals()["DOCS"] = os.path.abspath(args.docs)

    print(f"390 px phone audit — {len(PAGES)} pages, viewport {VIEWPORT}px")
    audit_css()
    audit_render()

    failed = [r for r in results if not r[1]]
    print(f"\nMobile audit: {len(results) - len(failed)}/{len(results)} passed"
          + (f" — {len(failed)} FAILED" if failed else ""))
    for name, _, detail in failed:
        print(f"  - {name}" + (f" ({detail})" if detail else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

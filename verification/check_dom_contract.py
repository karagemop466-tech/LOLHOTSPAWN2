#!/usr/bin/env python3
"""
check_dom_contract.py — do the pages and the shared JS/CSS agree with each other?

Extracted element ids referenced by docs/assets/app.js (`$("#id")`,
`getElementById("id")`, `querySelector("#id")`) and checks that each id exists
in at least one docs/*.html page. Also verifies every page loads the shared
stylesheet and script, and reports ids that only some pages provide (the JS is
page-aware, so ids used by one page's render path need not exist everywhere).

Mobile/UX contracts added 2026-10-24 after the executive summary shipped with a
header whose wrapper reused the progress-bar class (`height:12px;overflow:hidden`)
and a theme button with no handler:

  C1  every `class` token in every page is actually defined in style.css
  C2  every page has the same header skeleton (logo, #updated, #freshness,
      theme button), a `top-nav` with a <ul> of the 6 sections, and a 6-column
      bottom nav
  C3  nothing inside the header uses a class that another component defines
      with a fixed height / hidden overflow (the `bar` regression)
  C4  every <button id> in the pages is wired up in app.js (no dead controls)
  C5  every page carries the ids app.js writes on *every* page
      (#error-box, #freshness-warning, #updated, #freshness)
  C6  mobile: responsive viewport meta on every page, and style.css still turns
      wide tables into stacked cards at phone width

Exit 1 if any referenced id exists on no page, any page is missing the assets,
or any of C1–C6 fails.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")

PRIMARY_SECTIONS = ["summary", "picks", "leagues", "unresolved", "flagged", "methodology"]

# Written by setHeader()/toastError() on every page, whatever the page renders.
ALWAYS_PRESENT_IDS = ["error-box", "freshness-warning", "updated", "freshness"]

# Classes that are allowed inside <header>/<nav> markup. Anything else inside the
# header is reported, because that is how the progress-bar class leaked in.
HEADER_ALLOWED_CLASSES = {
    "site-header", "header-inner", "logo", "logo-mark", "logo-text", "header-meta",
    "freshness", "dot", "icon-btn", "top-nav", "skip",
}


class Ids(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: set[str] = set()
        self.refs: set[str] = set()
        self.classes: set[str] = set()
        self.buttons: list[str] = []
        self.header_classes: set[str] = set()
        self.in_header = 0
        self._button_open: str | None = None
        self._button_id: str | None = None
        self.top_nav_items = 0
        self._in_top_nav = 0
        self._in_li = 0
        self._has_ul = False
        self.viewport = ""
        self._in_theme_color = False

    # -- helpers ----------------------------------------------------------
    @staticmethod
    def _class_tokens(d: dict) -> list[str]:
        return [c for c in str(d.get("class") or "").split() if c]

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        classes = self._class_tokens(d)
        self.classes.update(classes)
        if tag == "meta":
            if str(d.get("name") or "").lower() == "viewport":
                self.viewport = str(d.get("content") or "")
            if str(d.get("name") or "").lower() == "theme-color":
                self._in_theme_color = True
        if d.get("id"):
            self.ids.add(d["id"])
        for key in ("href", "src"):
            if d.get(key):
                self.refs.add(d[key])

        if tag == "header" and "site-header" in classes:
            self.in_header = 1
        elif self.in_header:
            if tag == "header":
                self.in_header += 1
            if tag not in ("nav",):
                self.header_classes.update(classes)
        if tag == "nav" and "top-nav" in classes:
            self._in_top_nav = 1
        elif self._in_top_nav:
            if tag == "nav":
                self._in_top_nav += 1
            if tag == "ul":
                self._has_ul = True
            if tag == "li":
                self._in_li += 1
            if tag == "a" and self._in_li:
                self.top_nav_items += 1
        if tag == "button":
            self._button_open = "button"
            self._button_id = d.get("id")

    def handle_endtag(self, tag):
        if tag == "header" and self.in_header:
            self.in_header -= 1
        if tag == "nav" and self._in_top_nav:
            self._in_top_nav -= 1
        if tag == "li" and self._in_li:
            self._in_li -= 1
        if tag == "button" and self._button_open:
            if self._button_id:
                self.buttons.append(self._button_id)
            self._button_open = None
            self._button_id = None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default=DOCS)
    args = ap.parse_args()
    docs = args.docs
    js_path = os.path.join(docs, "assets", "app.js")
    css_path = os.path.join(docs, "assets", "style.css")
    if not os.path.exists(js_path):
        print("no docs/assets/app.js — nothing to check")
        return 1
    js = open(js_path, encoding="utf-8").read()
    css = open(css_path, encoding="utf-8").read()
    used = set(re.findall(r'\$\(["\']#([A-Za-z0-9_-]+)["\']\)', js))
    used |= set(re.findall(r'getElementById\(["\']([A-Za-z0-9_-]+)["\']\)', js))
    used |= set(re.findall(r'querySelector\(["\']#([A-Za-z0-9_-]+)["\']\)', js))

    pages: dict[str, Ids] = {}
    html: dict[str, str] = {}
    for name in sorted(os.listdir(docs)):
        if name.endswith(".html"):
            page_html = open(os.path.join(docs, name), encoding="utf-8").read()
            p = Ids()
            p.feed(page_html)
            pages[name] = p
            html[name] = page_html

    all_ids = set().union(*(p.ids for p in pages.values())) if pages else set()
    missing = sorted(u for u in used if u not in all_ids)
    problems: list[str] = []
    for name, p in pages.items():
        refs = " ".join(p.refs)
        if "assets/style.css" not in refs:
            problems.append(f"{name}: does not load assets/style.css")
        if "load(" in html[name] and "assets/app.js" not in refs:
            problems.append(f"{name}: uses load() but does not include assets/app.js")

    # The fixed mobile navigation must have one visible grid column per link.
    grid = re.search(r"\.bottom-nav\s*\{[^}]*grid-template-columns:\s*repeat\((\d+),", css, re.S)
    columns = int(grid.group(1)) if grid else 0
    if not grid:
        problems.append("style.css: could not determine mobile bottom-nav column count")
    else:
        for name, page_html in html.items():
            nav = re.search(r'<nav[^>]*class="bottom-nav"[^>]*>(.*?)</nav>', page_html, re.S)
            if not nav:
                problems.append(f"{name}: no mobile bottom-nav")
                continue
            links = len(re.findall(r"<a\b", nav.group(1)))
            if links != columns:
                problems.append(f"{name}: mobile bottom nav has {links} links but {columns} grid columns")

    # ---- C1: every class used in markup must exist in the stylesheet -------
    defined = lambda c: re.search(r"\." + re.escape(c) + r"(?![\w-])", css) is not None
    for name, p in pages.items():
        for c in sorted(p.classes):
            if not defined(c):
                problems.append(f"C1 {name}: class '{c}' has no rule in style.css (renders unstyled)")

    # ---- C2: identical header + primary nav skeleton on every page ----------
    for name, p in pages.items():
        for needed in ("site-header", "header-inner", "logo", "logo-mark", "header-meta"):
            if needed not in p.classes:
                problems.append(f"C2 {name}: header is missing .{needed}")
        if "site-header" not in p.classes:
            problems.append(f"C2 {name}: no <header class=\"site-header\">")
        if not p._has_ul:
            problems.append(f"C2 {name}: .top-nav has no <ul> (links are not a scrollable strip)")
        if p.top_nav_items != len(PRIMARY_SECTIONS):
            problems.append(
                f"C2 {name}: .top-nav has {p.top_nav_items} section links, expected {len(PRIMARY_SECTIONS)}")
        nav_ids = set(re.findall(r'data-nav="([a-z]+)"', html[name]))
        if not set(PRIMARY_SECTIONS).issubset(nav_ids):
            problems.append(f"C2 {name}: nav data-nav targets {sorted(nav_ids)} miss "
                            f"{sorted(set(PRIMARY_SECTIONS) - nav_ids)}")

    # ---- C3: no cross-component class reuse inside the header --------------
    for name, p in pages.items():
        bad = sorted(p.header_classes - HEADER_ALLOWED_CLASSES)
        if bad:
            problems.append(f"C3 {name}: header uses non-header class(es) {bad} — "
                            "component classes can carry layout rules that clip the header")

    # ---- C4: no dead buttons ------------------------------------------------
    for name, p in pages.items():
        for bid in p.buttons:
            if f"#{bid}" not in js and f'"{bid}"' not in js:
                problems.append(f"C4 {name}: button #{bid} has no handler in app.js (dead control)")

    # ---- C5: ids the shared JS writes on every page -------------------------
    for name, p in pages.items():
        for needed in ALWAYS_PRESENT_IDS:
            if needed not in p.ids:
                problems.append(f"C5 {name}: missing #{needed}, which app.js writes on every page")

    # ---- C6: mobile ---------------------------------------------------------
    for name, p in pages.items():
        if "width=device-width" not in p.viewport:
            problems.append(f"C6 {name}: viewport meta missing 'width=device-width'")
        if 'name="theme-color"' not in html[name]:
            problems.append(f"C6 {name}: no theme-color meta")
    def _media_blocks(text: str) -> list[str]:
        """Return the bodies of every `@media (max-width: Npx)` block (brace matched)."""
        bodies = []
        for m in re.finditer(r"@media\s*\(max-width:\s*(\d+)px\)\s*\{", text):
            i, depth = m.end(), 1
            while i < len(text) and depth:
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                i += 1
            bodies.append(text[m.end():i - 1])
        return bodies

    cellular = any(
        re.search(r"\btable\b[^{}]*\{[^}]*display:\s*block", body)
        for body in _media_blocks(css)
    )
    if not cellular:
        problems.append("C6 style.css: wide tables no longer collapse to stacked cards at phone width")
    body_rule = re.search(r"\nbody\s*\{([^}]*)\}", css, re.S)
    if body_rule:
        size = re.search(r"font-size:\s*(\d+(?:\.\d+)?)px", body_rule.group(1))
        if size and float(size.group(1)) < 16:
            problems.append(f"C6 style.css: body font-size {size.group(1)}px is below 16px")
    else:
        problems.append("C6 style.css: no body rule found")

    print(f"ids referenced by app.js: {len(used)} · ids present in pages: {len(all_ids)}")
    if missing:
        print("MISSING (referenced but on no page):")
        for m in missing:
            print("  -", m)
    for name, p in pages.items():
        only_here = used & p.ids
        print(f"  {name:20} ids={len(p.ids):3}  classes={len(p.classes):3}  "
              f"nav={p.top_nav_items}  js-targets-present={len(only_here):3}")
    for pr in problems:
        print("PROBLEM:", pr)
    ok = not missing and not problems
    print("DOM contract:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

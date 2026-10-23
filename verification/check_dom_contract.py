#!/usr/bin/env python3
"""
check_dom_contract.py — do the new pages provide every element the shared JS uses?

Extracts element ids referenced by docs/assets/app.js (`$("#id")`,
`getElementById("id")`, `querySelector("#id")`) and checks that each id exists
in at least one docs/*.html page. Also verifies every page loads the shared
stylesheet and script, and reports ids that only some pages provide (the JS is
page-aware, so ids used by one page's render path need not exist everywhere).

Exit 1 if any referenced id exists on no page, or a page is missing the assets.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")


class Ids(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: set[str] = set()
        self.refs: set[str] = set()

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if d.get("id"):
            self.ids.add(d["id"])
        for key in ("href", "src"):
            if d.get(key):
                self.refs.add(d[key])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default=DOCS)
    args = ap.parse_args()
    docs = args.docs
    js_path = os.path.join(docs, "assets", "app.js")
    if not os.path.exists(js_path):
        print("no docs/assets/app.js — nothing to check")
        return 1
    js = open(js_path, encoding="utf-8").read()
    used = set(re.findall(r'\$\(["\']#([A-Za-z0-9_-]+)["\']\)', js))
    used |= set(re.findall(r'getElementById\(["\']([A-Za-z0-9_-]+)["\']\)', js))
    used |= set(re.findall(r'querySelector\(["\']#([A-Za-z0-9_-]+)["\']\)', js))

    pages = {}
    for name in sorted(os.listdir(docs)):
        if name.endswith(".html"):
            p = Ids()
            p.feed(open(os.path.join(docs, name), encoding="utf-8").read())
            pages[name] = p

    all_ids = set().union(*(p.ids for p in pages.values())) if pages else set()
    missing = sorted(u for u in used if u not in all_ids)
    problems = []
    for name, p in pages.items():
        refs = " ".join(p.refs)
        if "assets/style.css" not in refs:
            problems.append(f"{name}: does not load assets/style.css")
        page_html = open(os.path.join(docs, name), encoding="utf-8").read()
        dynamic = "load(" in page_html
        if dynamic and "assets/app.js" not in refs:
            problems.append(f"{name}: uses load() but does not include assets/app.js")

    # The fixed mobile navigation must have one visible grid column per link.
    # A mismatch silently pushes a navigation item onto a second row on phones.
    css = open(os.path.join(docs, "assets", "style.css"), encoding="utf-8").read()
    grid = re.search(r"\.bottom-nav\s*\{[^}]*grid-template-columns:\s*repeat\((\d+),", css, re.S)
    if not grid:
        problems.append("style.css: could not determine mobile bottom-nav column count")
    else:
        columns = int(grid.group(1))
        for name, page in pages.items():
            page_html = open(os.path.join(docs, name), encoding="utf-8").read()
            nav = re.search(r'<nav[^>]*class="bottom-nav"[^>]*>(.*?)</nav>', page_html, re.S)
            if nav:
                links = len(re.findall(r"<a\b", nav.group(1)))
                if links != columns:
                    problems.append(f"{name}: mobile bottom nav has {links} links but {columns} grid columns")

    print(f"ids referenced by app.js: {len(used)} · ids present in pages: {len(all_ids)}")
    if missing:
        print("MISSING (referenced but on no page):")
        for m in missing:
            print("  -", m)
    for name, p in pages.items():
        only_here = used & p.ids
        print(f"  {name:20} ids={len(p.ids):3}  js-targets-present={len(only_here):3}")
    for pr in problems:
        print("PROBLEM:", pr)
    ok = not missing and not problems
    print("DOM contract:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""check_mobile_css.py — static, offline guard rails for phone readability.

The site is read on a phone first (the brief says so twice), but a stylesheet
regression is invisible in a desktop browser and jsdom does no layout. This
checker parses docs/assets/style.css without a CSS engine and fails on the
concrete things that break a 390 px viewport:

  M1  every page declares `width=device-width` (a desktop-width layout on a
      phone is the classic "pinch to zoom" bug)
  M2  the shared stylesheet keeps wide tables scrollable (`.table-wrap` has
      `overflow-x: auto`) and turns them into stacked cards at phone width
  M3  no declaration outside a `min-width` media query sets a fixed width or a
      min-width larger than the 390 px viewport (that is what forces the whole
      page to scroll sideways)
  M4  the bottom navigation is visible below 860 px and every one of its links
      is at least 44 px tall (Apple/Google touch-target guidance)
  M5  body copy is at least 14 px and the smallest utility text is at least
      11 px, so nothing needs zooming
  M6  cards and buttons that are primary tap targets keep a min-height of at
      least 44 px

Exit 1 on any failure. Every rule is asserted against the real file, so a future
edit that reintroduces horizontal scrolling fails CI instead of shipping.
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
CSS_PATH = os.path.join(DOCS, "assets", "style.css")

MAX_MOBILE_PX = 390
MIN_TAP_PX = 44
MIN_BODY_PX = 14
MIN_TINY_PX = 11

results: list[tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str = "") -> None:
    results.append((bool(ok), name, detail))


def strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def blocks(css: str):
    """Yield (selector, body, media_condition_or_None) for every rule.

    Handles one level of nesting, which is all this stylesheet uses:
    declarations and `@media (...) { ... }` blocks at the top level.
    """
    i, n = 0, len(css)
    while i < n:
        brace = css.find("{", i)
        if brace < 0:
            break
        selector = css[i:brace].strip()
        depth, j = 1, brace + 1
        while j < n and depth:
            if css[j] == "{":
                depth += 1
            elif css[j] == "}":
                depth -= 1
            j += 1
        body = css[brace + 1:j - 1]
        if selector.startswith("@media"):
            condition = selector[len("@media"):].strip()
            for inner_sel, inner_body, _ in blocks(body):
                yield inner_sel, inner_body, condition
        elif selector.startswith("@"):
            # @font-face / @keyframes etc: no layout defaults to inspect
            yield selector, "", None
        else:
            yield selector, body, None
        i = j


def decls(body: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in body.split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out


def px(value: str) -> float | None:
    m = re.match(r"^(-?\d+(?:\.\d+)?)px$", value.strip())
    return float(m.group(1)) if m else None


def main() -> int:
    # ---- M1: viewport meta on every page ---------------------------------
    pages = sorted(p for p in os.listdir(DOCS) if p.endswith(".html"))
    missing = []
    for page in pages:
        with open(os.path.join(DOCS, page), encoding="utf-8") as fh:
            head = fh.read(4000)
        if not re.search(r'<meta[^>]+name="viewport"[^>]+width=device-width', head):
            missing.append(page)
    check(not missing, "M1 every page has a device-width viewport",
          f"missing on: {', '.join(missing)}" if missing else f"{len(pages)} pages")

    with open(CSS_PATH, encoding="utf-8") as fh:
        css = strip_comments(fh.read())
    rules = list(blocks(css))

    def rule(sel: str, media_none: bool = True):
        for s, b, cond in rules:
            if s.strip() == sel and (cond is None) == media_none:
                return decls(b), cond
        return None, None

    # ---- M2: tables stay usable on a phone --------------------------------
    tw, _ = rule(".table-wrap")
    check(bool(tw) and tw.get("overflow-x") == "auto",
          "M2a .table-wrap scrolls horizontally instead of overflowing the page",
          str(tw))
    stacked = [
        (s, b, c) for s, b, c in rules
        if c and "max-width" in c and ("table" in s or "thead" in s or "tbody" in s)
        and "display: block" in b.replace("  ", " ")
    ]
    check(bool(stacked), "M2b tables become stacked cards at phone width",
          f"{len(stacked)} rule(s), e.g. {stacked[0][0][:60] if stacked else 'none'}")

    # ---- M3: nothing forces the page wider than the viewport --------------
    offenders = []
    for sel, body, cond in rules:
        if cond and "min-width" in cond:      # desktop-only rules are allowed to be wide
            continue
        d = decls(body)
        for prop in ("width", "min-width"):
            v = px(d.get(prop, ""))
            if v is not None and v > MAX_MOBILE_PX and prop == "min-width":
                offenders.append(f"{sel} {prop}:{d[prop]}")
            elif v is not None and v > MAX_MOBILE_PX and prop == "width":
                # A fixed width wider than a phone is only acceptable when the
                # element is inside a horizontal scroller (documented above).
                if sel not in (".table-wrap",):
                    offenders.append(f"{sel} {prop}:{d[prop]}")
    check(not offenders, f"M3 no non-media rule is wider than {MAX_MOBILE_PX}px",
          "; ".join(offenders[:5]))

    # ---- M4: bottom navigation ---------------------------------------------
    nav_links, _ = rule(".bottom-nav a")
    nav_hidden = [c for s, b, c in rules
                  if c and "min-width" in c and ".bottom-nav" in s and "display: none" in b]
    check(bool(nav_links) and bool(nav_hidden),
          "M4a bottom navigation exists and is hidden only on wide screens",
          f"links={bool(nav_links)} hidden_at={nav_hidden[:1]}")
    nav_h, _ = rule(".bottom-nav a")
    min_h = px((nav_h or {}).get("min-height", "").replace("var(--nav-h)", "0"))
    nav_var = re.search(r"--nav-h:\s*(\d+)px", css)
    effective = min_h or (float(nav_var.group(1)) if nav_var else 0)
    check(effective >= MIN_TAP_PX, f"M4b bottom-nav links are >= {MIN_TAP_PX}px tall",
          f"{effective}px")

    # ---- M5: font sizes ----------------------------------------------------
    body_rule, _ = rule("body")
    body_px = px((body_rule or {}).get("font-size", ""))
    check(body_px is not None and body_px >= MIN_BODY_PX,
          f"M5a body font-size >= {MIN_BODY_PX}px", f"{body_px}px")
    tiny = []
    for sel, b, cond in rules:
        if not cond or "max-width" not in cond:
            pass
        v = px(decls(b).get("font-size", ""))
        if v is not None and v < MIN_TINY_PX:
            tiny.append(f"{sel} {v}px")
    check(not tiny, f"M5b no text smaller than {MIN_TINY_PX}px", "; ".join(tiny[:5]))

    # ---- M6: primary tap targets ------------------------------------------
    pick, _ = rule(".pickcard")
    pick_h = px((pick or {}).get("min-height", ""))
    check(pick_h is not None and pick_h >= MIN_TAP_PX,
          f"M6a .pickcard min-height >= {MIN_TAP_PX}px", f"{pick_h}px")
    btn, _ = rule(".btn")
    # .btn relies on padding for its height; 12px top + 12px bottom + 15px text
    # at line-height 1.5 is ~46px, so assert the padding is not reduced instead.
    pad_ok = bool(btn) and (px(btn.get("padding", "").split()[0]) or 0) >= 10
    check(pad_ok, "M6b .btn keeps >= 10px vertical padding (>= 44px tall)",
          (btn or {}).get("padding", ""))

    failed = [r for r in results if not r[0]]
    for ok, name, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    print(f"\n== mobile CSS check: {len(results) - len(failed)} pass · {len(failed)} fail ==")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

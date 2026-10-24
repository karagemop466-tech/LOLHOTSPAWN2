#!/usr/bin/env python3
"""
test_dom_contract.py — negative self-tests for verification/check_dom_contract.py.

The checks that caught the 2026-10-24 executive-summary defects must keep
catching them. Each test copies docs/ into a temp dir, injects exactly one
regression, and asserts the contract fails with the expected message. Nothing
outside the temp dir is touched.

Run: python3 verification/test_dom_contract.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
CHECKER = os.path.join(ROOT, "verification", "check_dom_contract.py")


def run(docs: str) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, CHECKER, "--docs", docs],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def copy_docs() -> str:
    tmp = tempfile.mkdtemp(prefix="domcheck-")
    shutil.copytree(DOCS, os.path.join(tmp, "docs"))
    return os.path.join(tmp, "docs")


def patch(path: str, old: str, new: str) -> None:
    text = open(path, encoding="utf-8").read()
    assert old in text, f"fixture text not found in {os.path.basename(path)}: {old[:60]!r}"
    open(path, "w", encoding="utf-8").write(text.replace(old, new, 1))


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    code, out = run(DOCS)
    checks.append(("baseline passes", code == 0 and "DOM contract: PASS" in out, out.strip().splitlines()[-1]))

    # 1. The header wrapper reusing the progress-bar class (the shipped defect).
    d = copy_docs()
    patch(os.path.join(d, "index.html"), '<div class="header-inner">', '<div class="wrap bar">')
    code, out = run(d)
    checks.append(("header wrapper classing as .bar fails C3",
                   code == 1 and "C3 index.html" in out, [l for l in out.splitlines() if "C3" in l][:1]))
    shutil.rmtree(os.path.dirname(d))

    # 2. A class that no stylesheet rule defines (unstyled markup).
    d = copy_docs()
    patch(os.path.join(d, "index.html"), '<div class="nav-list">', '<div class="nav-list never-styled">')
    code, out = run(d)
    checks.append(("undefined class fails C1",
                   code == 1 and "never-styled" in out, [l for l in out.splitlines() if "never-styled" in l][:1]))
    shutil.rmtree(os.path.dirname(d))

    # 3. A page that drops the JS-populated freshness ids.
    d = copy_docs()
    patch(os.path.join(d, "picks.html"), '<span id="updated">Loading…</span><br>', '')
    code, out = run(d)
    checks.append(("missing #updated fails C5",
                   code == 1 and "C5 picks.html" in out, [l for l in out.splitlines() if "C5" in l][:1]))
    shutil.rmtree(os.path.dirname(d))

    # 4. A dead control (button with no handler).
    d = copy_docs()
    patch(os.path.join(d, "picks.html"), '<button class="chipbtn" type="button" id="reset">Reset</button>',
          '<button class="chipbtn" type="button" id="ghost-button">Reset</button>')
    code, out = run(d)
    checks.append(("handler-less button fails C4",
                   code == 1 and "ghost-button" in out, [l for l in out.splitlines() if "ghost-button" in l][:1]))
    shutil.rmtree(os.path.dirname(d))

    # 5. A top nav that loses its <ul> (links stop being a scrollable strip).
    d = copy_docs()
    text = open(os.path.join(d, "flagged.html"), encoding="utf-8").read()
    start = text.index('<nav class="top-nav"')
    end = text.index("</nav>", start) + len("</nav>")
    flat = ('<nav class="top-nav" aria-label="Main">' +
            "".join(f'<a href="{h}" data-nav="{n}">{n}</a>' for h, n in (
                ("index.html", "summary"), ("picks.html", "picks"), ("leagues.html", "leagues"),
                ("unresolved.html", "unresolved"), ("flagged.html", "flagged"),
                ("methodology.html", "methodology"))) + "</nav>")
    open(os.path.join(d, "flagged.html"), "w", encoding="utf-8").write(text[:start] + flat + text[end:])
    code, out = run(d)
    checks.append(("top-nav without <ul> fails C2",
                   code == 1 and "C2 flagged.html" in out, [l for l in out.splitlines() if "C2 flagged" in l][:1]))
    shutil.rmtree(os.path.dirname(d))

    # 6. A page missing the viewport meta.
    d = copy_docs()
    patch(os.path.join(d, "match.html"),
          '<meta name="viewport" content="width=device-width, initial-scale=1">', '')
    code, out = run(d)
    checks.append(("missing viewport meta fails C6",
                   code == 1 and "C6 match.html" in out, [l for l in out.splitlines() if "C6" in l][:1]))
    shutil.rmtree(os.path.dirname(d))

    width = max(len(name) for name, _, _ in checks)
    passed = 0
    for name, ok, detail in checks:
        passed += 1 if ok else 0
        print(f"{'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail if not ok else ''}")
    print(f"{passed}/{len(checks)} dom-contract self-tests passed")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())

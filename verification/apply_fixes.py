#!/usr/bin/env python3
"""
apply_fixes.py — idempotent integration fixes for the T7-T10 pipeline.

Each fix is a text replacement that is only applied when the original text is
present; when the owning session has already fixed it, the script reports
"already applied / not found" and exits 0. Also fixes .gitignore so the 8 MB
Leaguepedia cache is no longer committed.

Run at integration:
    python3 verification/apply_fixes.py            # apply to the working tree
    python3 verification/apply_fixes.py --check    # report only, change nothing
"""
from __future__ import annotations

import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FIX_MODEL_NAMES = (
    "scripts/model.py",
    'self.names = sorted(set(n for n in names if n))',
    'self.names = sorted({str(n) for n in names if n})  # leaguepedia team names can be ints',
    "Fix int/str TypeError in Resolver (model.py:158)",
)

OLD_MARKET = '''            if {str(outs[0]).strip().lower(), str(outs[1]).strip().lower()} == {a.lower(), b.lower()}:
                q = (mk.get("question") or "").lower()
                if "game 1" not in q and "game 2" not in q and "winner" in q or "vs" in q:
                    chosen = (outs, prices, mk)
                    break
                if chosen is None:
                    chosen = (outs, prices, mk)'''

NEW_MARKET = '''            if {str(outs[0]).strip().lower(), str(outs[1]).strip().lower()} == {a.lower(), b.lower()}:
                q = (mk.get("question") or "").lower()
                label = (mk.get("groupItemTitle") or "").lower()
                blob = q + " " + label
                is_single_game = bool(re.search(r"(game|map)\\s*\\d+", blob))
                is_series = ("match winner" in blob) or ("series winner" in blob) or ("series" in label)
                if is_series and not is_single_game:
                    chosen = (outs, prices, mk)          # explicit series/match market wins
                    break
                if not is_single_game and chosen is None:
                    chosen = (outs, prices, mk)          # neutral market (e.g. a BO1)
                if is_single_game and fallback_single is None:
                    fallback_single = (outs, prices, mk)  # only used when nothing better exists'''

FIX_MARKET = ("scripts/fetch_markets.py", OLD_MARKET, NEW_MARKET,
              "Never use a Game-N/Map-N child market as a series price (I1/I10)")

FIX_GAME_REGEX = (
    "scripts/fetch_markets.py",
    '                game = "game 1" in q or "game 2" in q or "map 1" in q',
    '                game = bool(re.search(r"(game|map)\\s*\\d+", q))',
    "Detect every Game-N/Map-N market (not only game 1/2, map 1)",
)

FIX_BO_UNKNOWN = (
    "scripts/model.py",
    '            if (rec.get("raw") or {}).get("market_type") == "game1" and (f.get("best_of") or 1) > 1:',
    '            if (rec.get("raw") or {}).get("market_type") == "game1" and f.get("best_of") != 1:',
    "Only allow a game-level market when the fixture is known BO1 (unknown best_of is not BO1)",
)

NEED_FALLBACK = ("scripts/fetch_markets.py", "        chosen = None\n",
                 "        chosen = None\n        fallback_single = None\n",
                 "declare fallback_single before the market loop")


def apply_fix(path: str, old: str, new: str, label: str, check: bool) -> str:
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        return f"SKIP   {path}: file not found ({label})"
    text = open(full, encoding="utf-8").read()
    if new.strip() and new.strip() in text:
        return f"OK     {label}: already applied"
    if old not in text:
        return f"MANUAL {label}: pattern not found in {path} — inspect manually"
    if check:
        return f"WOULD  {label}: pattern found in {path}"
    open(full, "w", encoding="utf-8").write(text.replace(old, new, 1))
    return f"FIXED  {label} in {path}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    print(apply_fix(*FIX_MODEL_NAMES[:3], FIX_MODEL_NAMES[3], args.check))
    print(apply_fix(*NEED_FALLBACK, args.check))
    print(apply_fix(*FIX_MARKET, args.check))
    print(apply_fix(*FIX_GAME_REGEX, args.check))
    print(apply_fix(*FIX_BO_UNKNOWN, args.check))

    # market loop needs the fallback used after the loop
    mk = os.path.join(ROOT, "scripts", "fetch_markets.py")
    if os.path.exists(mk):
        text = open(mk, encoding="utf-8").read()
        if "fallback_single" in text and "chosen = fallback_single" not in text:
            needle = "        if not chosen:\n            continue\n"
            repl = ("        if not chosen:\n            chosen = fallback_single\n"
                    "        if not chosen:\n            continue\n")
            if needle in text:
                if not args.check:
                    open(mk, "w", encoding="utf-8").write(text.replace(needle, repl, 1))
                print(("WOULD  " if args.check else "FIXED  ")
                      + "use single-game fallback only when no better market exists")
            else:
                print("MANUAL fallback wiring: pattern not found — inspect fetch_markets.py")

    # gitignore the cache
    gi = os.path.join(ROOT, ".gitignore")
    lines = open(gi, encoding="utf-8").read().splitlines() if os.path.exists(gi) else []
    if "data/cache/" not in lines:
        if not args.check:
            with open(gi, "a", encoding="utf-8") as fh:
                fh.write("\n# pipeline cache (8+ MB, regenerated every run)\ndata/cache/\n")
        print(("WOULD  " if args.check else "FIXED  ") + "gitignore data/cache/")
    else:
        print("OK     data/cache/ already gitignored")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

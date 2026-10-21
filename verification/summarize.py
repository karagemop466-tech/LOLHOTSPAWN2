#!/usr/bin/env python3
"""summarize.py — per-league coverage table for the published picks (markdown)."""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--picks", default=os.path.join(ROOT, "docs", "data", "picks.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "verification", "coverage_by_league.md"))
    args = ap.parse_args()

    data = json.load(open(args.picks, encoding="utf-8"))
    rows = data.get("matches", [])
    by = defaultdict(list)
    for m in rows:
        by[(m.get("tournament") or "—")].append(m)

    lines = ["# Coverage by league", "",
             f"_generated {data.get('generated_at', '?')} · {len(rows)} matches_", "",
             "| League | rows | market | model | unresolved | rows with a source link |",
             "|---|---|---|---|---|---|"]
    tot = Counter()
    for league, rs in sorted(by.items(), key=lambda kv: -len(kv[1])):
        c = Counter(m.get("method") for m in rs)
        market = sum(v for k, v in c.items() if str(k).startswith("MARKET"))
        model = sum(v for k, v in c.items() if str(k).startswith("MODEL"))
        linked = sum(1 for m in rs if any(m.get(k) for k in ("market_url", "source_url", "hotspawn_url"))
                     or m.get("sources"))
        lines.append(f"| {league} | {len(rs)} | {market} | {model} | {c.get('UNRESOLVED', 0)} "
                     f"| {linked}/{len(rs)} |")
        tot.update(c)
    lines += ["", f"**Totals:** " + " · ".join(f"{k}: {v}" for k, v in sorted(tot.items()))]
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    open(args.out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

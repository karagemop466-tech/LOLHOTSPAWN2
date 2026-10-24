#!/usr/bin/env python3
"""Resolve an append-only COORDINATION.md conflict by keeping both sides.

The board is append-only: every session appends its own block. When two
sessions' branches are rebased, git reports a conflict in the shared file.
The correct resolution is to keep BOTH blocks - one session's record must
never displace another session's.

Usage:  python3 scripts/resolve_coordination_conflict.py COORDINATION.md
"""
import sys


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "COORDINATION.md"
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")

    start = next((i for i, l in enumerate(lines) if l.startswith("<<<<<<<")), None)
    if start is None:
        print("no conflict markers found")
        return 0
    mid = next(i for i, l in enumerate(lines) if l.startswith("=======") and i > start)
    end = next(i for i, l in enumerate(lines) if l.startswith(">>>>>>>") and i > mid)

    ours = lines[start + 1:mid]      # the branch we are rebasing onto (main)
    theirs = lines[mid + 1:end]      # our session's block

    merged = lines[:start] + ours + ["", "---", ""] + theirs + lines[end + 1:]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(merged))

    # keep every session heading exactly once
    heads = [l for l in merged if l.startswith("## Session ")]
    dupes = {h for h in heads if heads.count(h) > 1}
    if dupes:
        print("WARNING duplicate session headings kept:", dupes)
    print(f"resolved {path}: kept both sides ({len(ours)} + {len(theirs)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

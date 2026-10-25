#!/usr/bin/env python3
"""Unit tests for the lobby ∪ fixtures-API merge in scripts/fetch_hotspawn.py.

Why this exists: on 2026-10-25 the Hotspawn lobby listed `Team Lucidity Esports vs
Fritt Fall` (RIVALS LEAGUE Season 2, 2026-10-31T17:30Z, fixture id 1090065) while
the fixtures API payload did not contain that id. The pipeline iterated only the
API rows, so the fixture got no pick and appeared in no exclusion list either.
`merge_fixture_sources()` makes that impossible: the priced set is the union of
both Hotspawn sources.

Run: python3 verification/test_lobby_union.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

from fetch_hotspawn import merge_fixture_sources  # noqa: E402

FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(f"{'PASS' if cond else 'FAIL'}  {name}{('  ' + detail) if detail else ''}")
    if not cond:
        FAILS.append(name)


def fx(fid: str, t1: str = "A", t2: str = "B") -> dict:
    return {"id": fid, "sport_alias": "lol", "participants0_name": t1, "participants1_name": t2}


def main() -> int:
    api = [fx("1"), fx("2"), fx("3")]
    lobby = [fx("2", "A2", "B2"), fx("3"), fx("1090065", "Team Lucidity Esports", "Fritt Fall")]

    merged, lobby_only = merge_fixture_sources(api, lobby)
    ids = [r["id"] for r in merged]
    check("union keeps every API id", {"1", "2", "3"} <= set(ids), str(sorted(ids)))
    check("union adds the lobby-only id", "1090065" in ids)
    check("union has no duplicate ids", len(ids) == len(set(ids)), f"{len(ids)} rows")
    check("lobby-only ids are reported", [r["id"] for r in lobby_only] == ["1090065"], str(lobby_only))
    kept = next(r for r in merged if r["id"] == "2")
    check("shared id keeps the API row", kept.get("participants0_name") == "A", str(kept))

    merged2, only2 = merge_fixture_sources([], [fx("9")])
    check("API empty still yields the lobby row", [r["id"] for r in merged2] == ["9"])
    check("API empty reports the lobby row as lobby-only", [r["id"] for r in only2] == ["9"])

    merged3, only3 = merge_fixture_sources(api, [])
    check("lobby empty keeps the API rows", len(merged3) == 3 and only3 == [])

    merged4, only4 = merge_fixture_sources(None, None)
    check("both sources empty is safe", merged4 == [] and only4 == [])

    dup_api = [fx("5"), fx("5", "C", "D")]
    merged5, only5 = merge_fixture_sources(dup_api, [])
    check("duplicate API ids collapse to one row", len(merged5) == 1 and only5 == [])

    rows_without_id = [{"sport_alias": "lol"}]
    merged6, only6 = merge_fixture_sources(rows_without_id, rows_without_id)
    check("rows without an id are ignored", merged6 == [] and only6 == [])

    print()
    if FAILS:
        print(f"{len(FAILS)} FAILED: {', '.join(FAILS)}")
        return 1
    print("5/5 union tests passed (9 assertions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

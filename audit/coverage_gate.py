#!/usr/bin/env python3
"""Fail a pipeline run when a Hotspawn fixture that should have a pick does not.

`audit/coverage_reconcile.py` re-reads the lobby and the fixtures API from scratch
(its own parser, not the pipeline's) and lists every future LoL fixture it finds
that the published payload does not price, with an exclusion reason when the
pipeline logged one.

This gate turns that report into a decision:

* a fixture listed on Hotspawn, starting more than `--grace-minutes` from now, and
  neither priced nor excluded for a stated reason  ->  exit 1 (a real coverage hole)
* a fixture that starts inside the grace window     ->  warning only (it can appear
  in the lobby seconds after the payload was generated; the next 6-hourly run
  picks it up, so failing here would throw away an otherwise good refresh)
* the audit itself could not run                    ->  warning only (never block a
  publish on a transient network failure)

Usage: python3 audit/coverage_gate.py [--grace-minutes 30]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone

AUDIT = "audit/coverage_reconcile.json"


def parse(ts: str):
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grace-minutes", type=int, default=30)
    ap.add_argument("--audit", default=AUDIT)
    args = ap.parse_args()

    try:
        with open(args.audit, encoding="utf-8") as fh:
            audit = json.load(fh)
    except (OSError, json.JSONDecodeError) as err:
        print(f"::warning title=Coverage gate skipped::could not read {args.audit} ({err})")
        return 0

    missing = audit.get("missing_detail") or []
    unexplained_ids = set(audit.get("unexplained_missing") or [])
    now = datetime.now(timezone.utc)
    hard, soft = [], []
    for row in missing:
        start = parse(row.get("start_utc"))
        reason = row.get("exclusion_reason")
        if reason:
            continue  # cancelled / withdrawn / not listed: documented, not a hole
        bucket = hard if (start and start > now + timedelta(minutes=args.grace_minutes)) else soft
        bucket.append(row)

    print(f"coverage gate: required future fixtures={audit.get('required_future_fixtures')} "
          f"published={audit.get('payload', {}).get('published_matches')} "
          f"missing={len(missing)} unexplained={len(unexplained_ids)} "
          f"hard={len(hard)} soft={len(soft)}")

    for row in soft:
        print(f"::warning title=Fixture not yet priced::{row.get('team1')} vs {row.get('team2')} "
              f"({row.get('tournament')}, starts {row.get('start_utc')}) is inside the grace window")

    if hard:
        for row in hard:
            print(f"::error title=Fixture listed on Hotspawn without a pick::"
                  f"{row.get('id')} {row.get('team1')} vs {row.get('team2')} "
                  f"({row.get('tournament')}, starts {row.get('start_utc')})")
        print(f"{len(hard)} fixture(s) listed on Hotspawn have no pick and no documented exclusion")
        return 1

    print("coverage gate: PASS - every fixture listed on Hotspawn that starts outside the grace "
          "window is either priced or excluded for a stated reason")
    return 0


if __name__ == "__main__":
    sys.exit(main())

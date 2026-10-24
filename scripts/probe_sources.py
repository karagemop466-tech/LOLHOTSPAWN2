#!/usr/bin/env python3
"""Diagnostic probe of candidate LoL odds/results sources (NOT production).

Since 2026-10-24 the candidate list and the probe logic live in
`scripts/source_probe.py`, which the 6-hour production run also executes: every
refresh publishes `market_probe` (checked_at, per-source HTTP status, verdict)
so the site can state, from live evidence, which external sources were tried
for the fixtures that have no bookmaker line.

This wrapper exists for CI diagnostics: it writes the same result to
`data/diag/source_probe.json` (historical name) and `data/diag/market_source_probe.json`.

Hard rule: nothing probed here is ever used in a probability. A candidate is
promoted into `scripts/fetch_markets.py` only after a probe shows structured
per-match prices and a human verifies a sample row (research/betting-sources.md).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from lib_common import log, write_json
from source_probe import probe_sources

MAX_AGE_MIN = 30
DIAG = "data/diag/market_source_probe.json"


def recent_probe(max_age_min: int = MAX_AGE_MIN):
    """Reuse the probe the production run just wrote instead of re-requesting every host."""
    if not os.path.exists(DIAG):
        return None
    try:
        data = json.load(open(DIAG, encoding="utf-8"))
        ts = datetime.fromisoformat(str(data["checked_at"]).replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - ts).total_seconds() / 60.0
        if age <= max_age_min and data.get("books"):
            log(f"probe: reusing {DIAG} ({age:.1f} min old)")
            return data
    except Exception:
        return None
    return None


def main() -> int:
    data = recent_probe() or probe_sources()
    write_json("data/diag/source_probe.json", data)
    write_json("data/diag/market_source_probe.json", data)
    log(f"probe: {data['summary']['checked']} candidates, "
        f"{data['summary']['market_sources_reachable']} market sources reachable")
    print(json.dumps(data["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

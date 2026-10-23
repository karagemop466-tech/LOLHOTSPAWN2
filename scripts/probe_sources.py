#!/usr/bin/env python3
"""Diagnostic probe of candidate LoL odds/results sources (NOT production).

Purpose: every 4-8h production run prices fixtures from Pinnacle, Bovada,
Polymarket and Leaguepedia only. This probe re-checks the wider field of
established betting sites, esportsbooks and aggregators from GitHub Actions
(the sandbox cannot reach them) and records what is *actually observed* —
HTTP status, whether the response is structured JSON, and whether any LoL
per-match market is visible. Output: data/diag/source_probe.json.

Rules: one polite GET per candidate, no price is ever copied into picks,
and a source is only promoted into scripts/fetch_markets.py after a probe
shows structured per-match prices AND a human verifies a sample row.
Exit code is always 0: a probe must never break the pipeline.
"""
from __future__ import annotations

import json

from lib_common import fetch, log, now_utc, utc_iso, write_json

OUT = "data/diag/source_probe.json"

CANDIDATES = [
    # name, url, kind
    ("Kalshi (esports series)", "https://api.elections.kalshi.com/trade-api/v2/series?category=Esports", "prediction-market-api"),
    ("Smarkets API (popular esports events)", "https://api.smarkets.com/v3/popular/events/sport/esports/", "exchange-api"),
    ("Manifold Markets (LoL search)", "https://api.manifold.markets/v0/search-markets?term=league%20of%20legends&limit=5", "prediction-market-api"),
    ("eGamersWorld LoL odds board", "https://egamersworld.com/lol/bets", "odds-comparison-page"),
    ("OddsPortal LoL", "https://www.oddsportal.com/lol/", "odds-comparison-page"),
    ("BetExplorer LoL", "https://www.betexplorer.com/lol/", "odds-comparison-page"),
    ("GG.Bet LoL", "https://gg.bet/en/esports/lol", "esportsbook-page"),
    ("Thunderpick LoL", "https://thunderpick.io/esports/league-of-legends", "esportsbook-page"),
    ("Rivalry LoL", "https://www.rivalry.com/lol", "esportsbook-page"),
    ("Midnite LoL", "https://www.midnite.com/esports/league-of-legends", "esportsbook-page"),
    ("Betway LoL", "https://www.betway.com/en/esports/league-of-legends", "sportsbook-page"),
    ("Unibet LoL", "https://www.unibet.com/betting/sports/filter/esports/league_of_legends", "sportsbook-page"),
    ("OddsPapi LoL (no key configured)", "https://oddspapi.io/sports/esports/lol", "aggregator-page"),
]


def probe(name, url, kind):
    r = fetch(url, timeout=30, retries=1)
    text = r.get("text") or ""
    status = r.get("status")
    is_json = False
    lol_hits = None
    try:
        data = json.loads(text)
        is_json = True
        if isinstance(data, dict) and isinstance(data.get("series"), list):
            lol_hits = sum(1 for s in data["series"]
                           if "league of legends" in json.dumps(s).lower())
        elif isinstance(data, list):
            lol_hits = sum(1 for s in data[:50]
                           if "league of legends" in json.dumps(s).lower())
    except Exception:
        pass
    return {
        "name": name, "url": url, "kind": kind, "http_status": status,
        "bytes": len(text.encode("utf-8", "ignore")), "is_json": is_json,
        "lol_mentions_in_first_items": lol_hits,
        "verdict": ("reachable; structured JSON — candidate for a future adapter, "
                    "needs per-match price verification before any production use"
                    if status == 200 and is_json else
                    "reachable HTML only — no structured per-match prices parsed; human cross-check only"
                    if status == 200 else
                    f"not usable from CI (HTTP {status})"),
    }


def main() -> int:
    results = []
    for name, url, kind in CANDIDATES:
        try:
            res = probe(name, url, kind)
        except Exception as e:  # noqa: BLE001 - probe must never break the run
            res = {"name": name, "url": url, "kind": kind, "http_status": None,
                   "error": repr(e)[:200], "verdict": "probe error"}
        log(f"probe: {name} -> HTTP {res.get('http_status')} json={res.get('is_json')}")
        results.append(res)
    write_json(OUT, {"checked_at": utc_iso(now_utc()), "candidates": results})
    log(f"probe: wrote {OUT} ({len(results)} candidates)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

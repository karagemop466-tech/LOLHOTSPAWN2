#!/usr/bin/env python3
"""Hotspawn LoL Pick'em fixture list.

Hotspawn is used ONLY for the fixture list (teams, tournament, start time, tier,
points, match link) and for nothing that influences the probability. The lobby is
an Angular SSR page whose <script id="ng-state"> transfer state contains the exact
same /api/v1/fixtures payload the page renders, including epoch-millisecond start
times. If that shape ever changes we fall back to the public fixtures endpoint.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone

from lib_common import fetch, get_json, log, now_utc, source, utc_iso, write_json

LOBBY = "https://play.hotspawn.com/lol-pickems"
FIXTURES_API = "https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures"
LOBBY_GENERIC = "https://play.hotspawn.com/lobby"
OUT = "data/cache/hotspawn.json"


def _ng_state(html: str):
    m = re.search(r'<script[^>]*id="ng-state"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def _from_lobby():
    r = fetch(LOBBY, timeout=90)
    state = _ng_state(r["text"]) if r["status"] == 200 else None
    if not state:
        return None, {"status": r["status"], "error": "ng-state not found"}
    fixtures, permalinks, week = None, {}, {}
    for _, entry in state.items():
        if not isinstance(entry, dict):
            continue
        body, url = entry.get("b"), str(entry.get("u") or "")
        if isinstance(body, list) and url.endswith("/api/v1/fixtures"):
            fixtures = body
        if isinstance(body, dict) and isinstance(body.get("permalinks"), dict):
            permalinks = body["permalinks"]
        if isinstance(body, dict) and body.get("weekStartUtc"):
            week = body
    if not fixtures:
        return None, {"status": 200, "error": "fixtures payload missing from ng-state"}
    return {"fixtures": fixtures, "permalinks": permalinks, "week": week,
            "http": r["status"], "bytes": len(r["text"]), "via": "lobby-ng-state"}, None


def _from_api():
    data, r = get_json(FIXTURES_API, timeout=120)
    if not isinstance(data, list):
        return None, {"status": r.get("status"), "error": "fixtures API unusable"}
    return {"fixtures": data, "permalinks": {}, "week": {},
            "http": r["status"], "bytes": len(r.get("body") or b""), "via": "fixtures-api"}, None


def normalise(raw: dict, permalinks: dict) -> dict | None:
    if str(raw.get("sport_alias") or "").lower() != "lol":
        return None
    t1 = raw.get("participants0_name")
    t2 = raw.get("participants1_name")
    if not t1 or not t2:
        return None
    try:
        start = datetime.fromtimestamp(int(raw["scheduled_start_time"]) / 1000.0, timezone.utc)
    except (KeyError, TypeError, ValueError):
        return None
    fid = str(raw.get("id") or "")
    return {
        "id": fid,
        "team1": t1,
        "team2": t2,
        "team1_id": str(raw.get("participants0_id") or ""),
        "team2_id": str(raw.get("participants1_id") or ""),
        "tournament": raw.get("competition_name") or "",
        "competition_id": str(raw.get("competition_id") or ""),
        "tier": (raw.get("tier") or "waiting for information").upper(),
        "stage": raw.get("stage") or "waiting for information",
        "points": raw.get("offered_points"),
        "best_of": raw.get("best_of"),
        "start_utc": utc_iso(start),
        "status": raw.get("status"),
        "hotspawn_url": permalinks.get(fid),
        "crowd": {
            "team1_pct": raw.get("participants0_picked_percent"),
            "team2_pct": raw.get("participants1_picked_percent"),
            "total_picks": raw.get("total_picks"),
            "note": "Hotspawn community pick percentage. Context only: never used in any probability.",
        },
        "source_lobby": LOBBY,
    }


def main() -> int:
    collected, err = _from_lobby()
    if err:
        log(f"lobby parse failed ({err}); trying fixtures API")
        collected, err = _from_api()
    if err:
        raise SystemExit(f"Hotspawn fixture fetch failed: {err}")

    now = now_utc()
    cutoff = now - timedelta(minutes=10)
    rows = []
    for raw in collected["fixtures"]:
        row = normalise(raw, collected.get("permalinks") or {})
        if not row:
            continue
        start = datetime.fromisoformat(row["start_utc"].replace("Z", "+00:00"))
        if start <= cutoff:
            continue  # pick'em locks 5 minutes before start
        rows.append(row)

    rows.sort(key=lambda r: (r["start_utc"], r["tournament"], r["team1"]))
    if len(rows) < 50:
        raise SystemExit(f"Only {len(rows)} future LoL fixtures parsed - refusing to overwrite good data")

    without_link = sum(1 for r in rows if not r.get("hotspawn_url"))
    payload = {
        "generated_at": utc_iso(now),
        "lobby": LOBBY,
        "lobby_generic": LOBBY_GENERIC,
        "fixtures_api": FIXTURES_API,
        "via": collected["via"],
        "lobby_http": collected.get("http"),
        "lobby_bytes": collected.get("bytes"),
        "week": collected.get("week") or {},
        "count": len(rows),
        "without_match_page": without_link,
        "sources": [
            source("Hotspawn LoL Pick'em lobby", LOBBY,
                   "Fixture list, tier/points, crowd % (display only) and match links."),
            source("Hotspawn fixtures API", FIXTURES_API,
                   "Official backend payload used by the lobby; exact scheduled_start_time (epoch ms)."),
        ],
        "fixtures": rows,
    }
    write_json(OUT, payload)
    log(f"hotspawn: {len(rows)} future LoL fixtures via {collected['via']} "
        f"({without_link} without a published match page)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

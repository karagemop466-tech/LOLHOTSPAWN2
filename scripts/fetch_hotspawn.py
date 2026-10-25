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


def merge_fixture_sources(api_fixtures: list, lobby_fixtures: list) -> tuple[list, list]:
    """Union of the fixtures API and the lobby transfer state, keyed by fixture id.

    The API is the richer feed (it carries rows the lobby has already rotated out),
    but it can *lag* the lobby: on 2026-10-25 the lobby listed `Team Lucidity
    Esports vs Fritt Fall` (RIVALS LEAGUE Season 2, 2026-10-31T17:30Z, id 1090065)
    while the API payload did not contain that id at all, so the fixture was
    silently dropped and never priced. Keys present in both keep the API row; ids
    only the lobby carries are added and returned separately so the payload can
    state how many fixtures came from that path.
    """
    merged: dict[str, dict] = {}
    for raw in api_fixtures or []:
        if isinstance(raw, dict) and raw.get("id") is not None:
            merged[str(raw["id"])] = raw
    lobby_only: list[dict] = []
    for raw in lobby_fixtures or []:
        if not isinstance(raw, dict) or raw.get("id") is None:
            continue
        fid = str(raw["id"])
        if fid not in merged:
            merged[fid] = raw
            lobby_only.append(raw)
    return list(merged.values()), lobby_only


def _start_dt(raw: dict):
    try:
        return datetime.fromtimestamp(int(raw["scheduled_start_time"]) / 1000.0, timezone.utc)
    except (KeyError, TypeError, ValueError):
        return None


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
    # The lobby renders only the fixtures it has match pages for (195 today);
    # the official fixtures endpoint carries every upcoming LoL fixture (208).
    # Merge: API provides the complete list, lobby provides match permalinks.
    api, api_err = _from_api()
    lobby, lobby_err = _from_lobby()
    api_fixtures = [x for x in (api or {}).get("fixtures", []) if str(x.get("sport_alias")).lower() == "lol"]
    lobby_fixtures = [x for x in (lobby or {}).get("fixtures", []) if str(x.get("sport_alias")).lower() == "lol"]
    merged_fixtures, lobby_only_fixtures = merge_fixture_sources(api_fixtures, lobby_fixtures)
    lobby_only_ids = {str(x.get("id")) for x in lobby_only_fixtures}
    if api_fixtures:
        collected = {"fixtures": merged_fixtures, "permalinks": (lobby or {}).get("permalinks") or {},
                     "week": (lobby or {}).get("week") or {},
                     "http": api.get("http"), "bytes": api.get("bytes"),
                     "via": ("fixtures-api+lobby-permalinks" if not lobby_only_fixtures
                             else "fixtures-api+lobby-permalinks+lobby-only-fixtures")}
        if lobby_err:
            log(f"lobby parse issue ({lobby_err}); continuing with API fixtures only")
        elif lobby_only_fixtures:
            log(f"hotspawn: {len(lobby_only_fixtures)} fixture(s) listed in the lobby are absent "
                f"from the fixtures API; pricing them from the lobby payload "
                f"(ids {', '.join(sorted(lobby_only_ids))})")
    elif lobby_fixtures:
        collected = lobby
        collected["via"] = "lobby-ng-state"
    else:
        raise SystemExit(f"Hotspawn fixture fetch failed: api={api_err} lobby={lobby_err}")

    now = now_utc()
    cutoff = now - timedelta(minutes=10)

    # The lobby is the list the user sees. When its state parsed, it is the
    # authority for "listed on Hotspawn"; the API may still carry fixtures the lobby
    # has withdrawn (e.g. status "cancelled"), which must not receive a pick.
    lobby_ids = None
    if lobby and lobby_fixtures:
        lobby_ids = {str(x.get("id")) for x in lobby_fixtures
                     if (lambda d: d is not None and d > now)(_start_dt(x))}

    rows, excluded = [], []
    api_upcoming = 0
    for raw in collected["fixtures"]:
        row = normalise(raw, collected.get("permalinks") or {})
        if not row:
            continue
        start = datetime.fromisoformat(row["start_utc"].replace("Z", "+00:00"))
        if start <= cutoff:
            continue  # pick'em locks 5 minutes before start
        api_upcoming += 1
        reason = None
        if str(row.get("status") or "").lower() != "scheduled":
            reason = f"Hotspawn status is '{row.get('status')}'; not priced"
        elif lobby_ids is not None and row["id"] not in lobby_ids:
            reason = "Not listed in the Hotspawn lobby; not priced"
        if reason:
            excluded.append({"id": row["id"], "team1": row["team1"], "team2": row["team2"],
                             "tournament": row["tournament"], "start_utc": row["start_utc"],
                             "status": row.get("status"), "reason": reason,
                             "source": FIXTURES_API})
            continue
        rows.append(row)

    rows.sort(key=lambda r: (r["start_utc"], r["tournament"], r["team1"]))
    if len(rows) < 50:
        raise SystemExit(f"Only {len(rows)} future LoL fixtures parsed - refusing to overwrite good data")

    row_ids = {r["id"] for r in rows}
    lobby_only_priced = sorted(x for x in lobby_only_ids if x in row_ids)
    reconciliation = {
        "lobby_lol_listed": len(lobby_fixtures) if lobby_fixtures else None,
        "lobby_upcoming": len(lobby_ids) if lobby_ids is not None else None,
        "lobby_past_not_priced": (len(lobby_fixtures) - len(lobby_ids)) if lobby_ids is not None else None,
        "api_upcoming_lol": api_upcoming,
        "api_excluded": len(excluded),
        "priced": len(rows),
        "lobby_only_in_union": sorted(lobby_only_ids),
        "lobby_only_priced": lobby_only_priced,
        "lobby_upcoming_missing_from_priced": (sorted(lobby_ids - row_ids) if lobby_ids is not None else None),
        "priced_not_in_lobby": (sorted(row_ids - lobby_ids) if lobby_ids is not None else None),
        "rule": ("Priced = every upcoming LoL fixture listed in the Hotspawn lobby with status "
                 "'scheduled', taking the union of the lobby transfer state and the fixtures API "
                 "(a fixture the lobby lists but the API lags on is priced from the lobby row)."
                 if lobby_ids is not None else
                 "Lobby state unavailable: priced = API upcoming LoL fixtures with status scheduled."),
    }

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
        "reconciliation": reconciliation,
        "excluded": excluded,
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

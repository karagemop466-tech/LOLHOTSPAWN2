#!/usr/bin/env python3
"""Read-only coverage audit: Hotspawn lobby (ng-state) vs fixtures API vs pipeline payload.

Writes data/diag/coverage_audit.json. Never used by the picks pipeline.
"""
from __future__ import annotations

import collections
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from fetch_hotspawn import FIXTURES_API, LOBBY, _ng_state  # noqa: E402
from lib_common import fetch, get_json, log, now_utc, utc_iso  # noqa: E402

OUT = "data/diag/coverage_audit.json"


def start_of(raw):
    try:
        return datetime.fromtimestamp(int(raw["scheduled_start_time"]) / 1000.0, timezone.utc)
    except (KeyError, TypeError, ValueError):
        return None


def main() -> int:
    now = now_utc()
    out = {"generated_at": utc_iso(now), "lobby": LOBBY, "fixtures_api": FIXTURES_API}

    r = fetch(LOBBY, timeout=90)
    out["lobby_http"] = r["status"]
    out["lobby_bytes"] = len(r["text"])
    state = _ng_state(r["text"]) if r["status"] == 200 else None
    out["lobby_ng_state_found"] = state is not None
    for label, pat in (("count_241", r"\(241\)"), ("count_139", r"139 matches"),
                       ("count_264", r"264"), ("count_195", r"\b195\b")):
        out[label] = len(re.findall(pat, r["text"]))
    if state:
        keys = []
        for k, entry in state.items():
            if isinstance(entry, dict):
                body = entry.get("b")
                keys.append({"key": k[:80], "url": str(entry.get("u") or "")[:200],
                             "type": type(body).__name__,
                             "len": len(body) if isinstance(body, (list, dict)) else None})
        out["ng_state_entries"] = keys
        lobby_fx = []
        permalinks, week = {}, {}
        for _, entry in state.items():
            if not isinstance(entry, dict):
                continue
            body, url = entry.get("b"), str(entry.get("u") or "")
            if isinstance(body, list) and url.endswith("/api/v1/fixtures"):
                lobby_fx = body
            if isinstance(body, dict) and isinstance(body.get("permalinks"), dict):
                permalinks = body["permalinks"]
            if isinstance(body, dict) and body.get("weekStartUtc"):
                week = body
        out["lobby_week"] = week
        out["lobby_permalinks"] = len(permalinks)
        lol_lobby = [x for x in lobby_fx if str(x.get("sport_alias")).lower() == "lol"]
        out["lobby_fixtures_total"] = len(lobby_fx)
        out["lobby_lol_total"] = len(lol_lobby)
        out["lobby_lol_future"] = sum(1 for x in lol_lobby if (start_of(x) or now) > now)
        out["lobby_lol_status"] = dict(collections.Counter(str(x.get("status")) for x in lol_lobby))
        out["lobby_lol_tier"] = dict(collections.Counter(str(x.get("tier")) for x in lol_lobby))
        lobby_ids = {str(x.get("id")) for x in lol_lobby if (start_of(x) or now) > now}
    else:
        lobby_ids = set()

    data, api_r = get_json(FIXTURES_API, timeout=240)
    out["api_http"] = api_r.get("status")
    if isinstance(data, list):
        lol = [x for x in data if str(x.get("sport_alias")).lower() == "lol"]
        fut = [x for x in lol if (start_of(x) or now) > now]
        out["api_total_rows"] = len(data)
        out["api_lol_rows"] = len(lol)
        out["api_lol_future"] = len(fut)
        out["api_lol_future_status"] = dict(collections.Counter(str(x.get("status")) for x in fut))
        out["api_lol_future_tier"] = dict(collections.Counter(str(x.get("tier")) for x in fut))
        api_ids = {str(x.get("id")) for x in fut}
        out["ids_in_lobby_not_api"] = sorted(lobby_ids - api_ids)
        out["ids_in_api_not_lobby"] = len(api_ids - lobby_ids)
        out["api_future_sample_not_in_lobby"] = [
            {"id": str(x.get("id")), "t1": x.get("participants0_name"), "t2": x.get("participants1_name"),
             "tournament": x.get("competition_name"), "status": x.get("status"),
             "start_utc": utc_iso(start_of(x))}
            for x in fut if str(x.get("id")) not in lobby_ids][:300]
        out["api_future_tournaments"] = dict(collections.Counter(x.get("competition_name") for x in fut))
    else:
        out["api_error"] = api_r.get("error")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    log(f"coverage audit written: lobby_lol_future={out.get('lobby_lol_future')} "
        f"api_lol_future={out.get('api_lol_future')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Reconcile the Hotspawn lobby / fixtures API with the published payload.

Answers one question line by line: does `docs/data/picks.json` contain a pick
for *every* League of Legends fixture that Hotspawn is currently listing, and if
not, which fixture ids are missing and why (already started, no match page,
dropped by a filter)?

Read-only. Writes audit/coverage_reconcile.json + .md; never edits the payload.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from fetch_hotspawn import FIXTURES_API, LOBBY, _ng_state, normalise  # noqa: E402
from lib_common import fetch, get_json, load_json, log, now_utc, utc_iso, write_json  # noqa: E402

OUT_JSON = "audit/coverage_reconcile.json"
OUT_MD = "audit/coverage_reconcile.md"


def start_of(raw):
    try:
        return datetime.fromtimestamp(int(raw["scheduled_start_time"]) / 1000.0, timezone.utc)
    except (KeyError, TypeError, ValueError):
        return None


def lol_rows(fixtures, permalinks):
    rows = []
    for raw in fixtures or []:
        if str(raw.get("sport_alias") or "").lower() != "lol":
            continue
        row = normalise(raw, permalinks or {})
        if row:
            rows.append(row)
    return rows


def main() -> int:
    now = now_utc()
    cutoff = now - timedelta(minutes=10)  # picks lock 5 minutes before start

    lobby_r = fetch(LOBBY, timeout=90)
    state = _ng_state(lobby_r["text"]) if lobby_r["status"] == 200 else None
    lobby_fixtures, permalinks = [], {}
    if state:
        for _, entry in state.items():
            if not isinstance(entry, dict):
                continue
            body, url = entry.get("b"), str(entry.get("u") or "")
            if isinstance(body, list) and url.endswith("/api/v1/fixtures"):
                lobby_fixtures = body
            if isinstance(body, dict) and isinstance(body.get("permalinks"), dict):
                permalinks = body["permalinks"]

    api_data, api_r = get_json(FIXTURES_API, timeout=90)
    api_fixtures = api_data if isinstance(api_data, list) else []

    payload = load_json("docs/data/picks.json", {}) or {}
    published = {str(m.get("id")) for m in payload.get("matches") or []}

    out = {
        "generated_at": utc_iso(now),
        "lobby": {"url": LOBBY, "http": lobby_r["status"], "bytes": len(lobby_r["text"] or ""),
                  "ng_state": bool(state), "raw_fixtures": len(lobby_fixtures)},
        "fixtures_api": {"url": FIXTURES_API, "http": api_r.get("status"),
                         "raw_fixtures": len(api_fixtures)},
        "api": {"url": FIXTURES_API, "http": api_r.get("status"),
                "raw_fixtures": len(api_fixtures)},
        "payload": {"generated_at": payload.get("generated_at"),
                    "published_matches": len(published)},
    }

    for label, raw_rows in (("lobby", lobby_fixtures), ("api", api_fixtures)):
        rows = lol_rows(raw_rows, permalinks)
        future = [r for r in rows if datetime.fromisoformat(r["start_utc"].replace("Z", "+00:00")) > cutoff]
        past = len(rows) - len(future)
        ids = {r["id"] for r in future}
        missing = sorted(ids - published)
        extra = sorted(published - {r["id"] for r in rows})
        out[label].update({
            "lol_fixtures": len(rows),
            "future_lol_fixtures": len(future),
            "already_started": past,
            "future_ids_missing_from_payload": missing,
            "payload_ids_not_in_this_source": extra[:25],
            "future_without_match_page": sum(1 for r in future if not r.get("hotspawn_url")),
            "tournaments": dict(Counter(r["tournament"] for r in future).most_common(40)),
        })
        log(f"reconcile: {label} raw={len(raw_rows)} lol={len(rows)} future={len(future)} "
            f"missing={len(missing)}")

    # The fixtures API is the pipeline's primary source; the lobby is the page the
    # brief actually points at. Report both and use the union as the requirement.
    union_future = {}
    for raw_rows in (lobby_fixtures, api_fixtures):
        for r in lol_rows(raw_rows, permalinks):
            if datetime.fromisoformat(r["start_utc"].replace("Z", "+00:00")) > cutoff:
                union_future[r["id"]] = r
    out["required_future_fixtures"] = len(union_future)
    out["missing_from_payload"] = sorted(set(union_future) - published)
    out["missing_detail"] = [
        {"id": fid, "team1": union_future[fid]["team1"], "team2": union_future[fid]["team2"],
         "tournament": union_future[fid]["tournament"], "start_utc": union_future[fid]["start_utc"],
         "hotspawn_url": union_future[fid].get("hotspawn_url")}
        for fid in sorted(set(union_future) - published)
    ]
    out["coverage_ok"] = not out["missing_from_payload"]

    write_json(OUT_JSON, out)
    md = [
        "# Hotspawn coverage reconciliation", "",
        f"Generated {out['generated_at']} · payload generated {out['payload']['generated_at']}", "",
        "| Source | HTTP | Raw rows | LoL fixtures | Future LoL | Already started | Future missing from payload |",
        "|---|---|---|---|---|---|---|",
    ]
    for label in ("lobby", "api"):
        d = out[label]
        md.append(f"| {label} | {d['http']} | {d['raw_fixtures']} | {d['lol_fixtures']} | "
                  f"{d['future_lol_fixtures']} | {d['already_started']} | "
                  f"{len(d['future_ids_missing_from_payload'])} |")
    md += ["", f"Published payload rows: **{out['payload']['published_matches']}** · "
               f"required future fixtures (union): **{out['required_future_fixtures']}** · "
               f"missing: **{len(out['missing_from_payload'])}**", ""]
    if out["missing_detail"]:
        md += ["## Missing fixtures", "", "| id | teams | tournament | start (UTC) |", "|---|---|---|---|"]
        for m in out["missing_detail"]:
            md.append(f"| {m['id']} | {m['team1']} vs {m['team2']} | {m['tournament']} | {m['start_utc']} |")
    else:
        md.append("Every future League of Legends fixture listed by the lobby and the fixtures API "
                  "has a published pick in the payload.")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    log(f"reconcile: coverage_ok={out['coverage_ok']} missing={len(out['missing_from_payload'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

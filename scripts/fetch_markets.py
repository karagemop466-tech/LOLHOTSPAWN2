#!/usr/bin/env python3
"""External market lines for LoL matches.

Sources, in priority order:
  1. Pinnacle        - established sharp sportsbook, public guest JSON feed.
  2. Bovada          - established North-American sportsbook, public coupon JSON.
  3. Polymarket      - prediction market, public Gamma API.

Every price is de-vigged (two-way normalisation) before it is stored. No price
from Hotspawn is used anywhere in this file.
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
from datetime import datetime, timedelta, timezone

from lib_common import (clamp, decimal_from_american, devig_two, fetch, get_json, log,
                        now_utc, source, utc_iso, write_json)

OUT = "data/cache/markets.json"
PIN_KEY = {"x-api-key": "CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R", "Accept": "application/json"}
PIN_BASE = "https://guest.api.arcadia.pinnacle.com/0.1"
PIN_PAGE = "https://www.pinnacle.com/en/esports/league-of-legends"
BOVADA_API = ("https://www.bovada.lv/services/sports/event/coupon/events/A/description/"
              "esports/league-of-legends?marketFilterId=def&preMatchOnly=true&lang=en")
BOVADA_PAGE = "https://www.bovada.lv/sports/esports/league-of-legends"
POLY_PAGE = "https://polymarket.com/event/"
POLY_API = "https://gamma-api.polymarket.com"


def _record(source_name, source_key, competition, start, team_a, team_b, prob_a, prob_b,
            url, decimal_a=None, decimal_b=None, note="", raw=None):
    if not team_a or not team_b or start is None:
        return None
    pa, pb = clamp(prob_a), clamp(prob_b)
    s = pa + pb
    return {
        "source": source_name,
        "source_key": source_key,
        "competition": competition or "",
        "start_utc": utc_iso(start),
        "team_a": team_a,
        "team_b": team_b,
        "prob_a": round(pa / s, 4),
        "prob_b": round(pb / s, 4),
        "decimal_a": round(decimal_a, 4) if decimal_a else None,
        "decimal_b": round(decimal_b, 4) if decimal_b else None,
        "url": url,
        "note": note,
        "raw": raw or {},
    }


def fetch_pinnacle() -> dict:
    status = {"source": "Pinnacle", "key": "pinnacle", "url": PIN_PAGE, "status": "error", "count": 0}
    sports, r = get_json(f"{PIN_BASE}/sports", PIN_KEY)
    if not isinstance(sports, list):
        status["error"] = f"sports feed HTTP {r.get('status')}"
        return {"status": status, "records": []}
    esports = [s for s in sports if s.get("id") == 12 or "esport" in str(s.get("name", "")).lower()]
    records = []
    leagues_seen = []
    for sport in esports:
        leagues, _ = get_json(f"{PIN_BASE}/sports/{sport['id']}/leagues", PIN_KEY)
        if not isinstance(leagues, list):
            continue
        for league in leagues:
            name = str(league.get("name") or "")
            if "league of legends" not in name.lower():
                continue
            leagues_seen.append(name)
            matchups, _ = get_json(f"{PIN_BASE}/leagues/{league['id']}/matchups", PIN_KEY)
            if not isinstance(matchups, list):
                continue
            for m in matchups:
                parts = m.get("participants") or []
                if len(parts) != 2 or not m.get("hasMarkets"):
                    continue
                start = m.get("startTime")
                try:
                    start_dt = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
                except Exception:
                    continue
                markets, _ = get_json(f"{PIN_BASE}/matchups/{m['id']}/markets/related/straight", PIN_KEY)
                if not isinstance(markets, list):
                    continue
                ml = next((x for x in markets if x.get("type") == "moneyline" and x.get("period") == 0), None)
                if ml is None:
                    ml = next((x for x in markets if x.get("type") == "moneyline"), None)
                if not ml:
                    continue
                prices = {p.get("designation"): p.get("price") for p in ml.get("prices") or []}
                da, db = decimal_from_american(prices.get("home")), decimal_from_american(prices.get("away"))
                dv = devig_two(da, db)
                if not dv:
                    continue
                rec = _record("Pinnacle", "pinnacle", name, start_dt,
                              parts[0].get("name"), parts[1].get("name"), dv[0], dv[1],
                              PIN_PAGE, da, db, note=f"Pinnacle moneyline (matchup {m.get('id')})",
                              raw={"matchup_id": m.get("id"), "league_id": league.get("id"),
                                   "american_home": prices.get("home"), "american_away": prices.get("away"),
                                   "api": f"{PIN_BASE}/leagues/{league.get('id')}/matchups"})
                if rec:
                    records.append(rec)
                time.sleep(0.15)
    status.update({"status": "ok" if records else "no_data", "count": len(records),
                   "leagues": leagues_seen,
                   "note": "Public guest JSON feed used by pinnacle.com; re-check the official site before betting."})
    return {"status": status, "records": records}


def fetch_bovada() -> dict:
    status = {"source": "Bovada", "key": "bovada", "url": BOVADA_PAGE, "status": "error", "count": 0}
    data, r = get_json(BOVADA_API, headers={"Referer": BOVADA_PAGE, "Origin": "https://www.bovada.lv"})
    if not isinstance(data, list):
        status["error"] = f"coupon feed HTTP {r.get('status')}"
        return {"status": status, "records": []}
    records = []
    comps = []
    for group in data:
        path = group.get("path") or []
        comp = path[0].get("description") if path else ""
        comps.append(comp)
        for ev in group.get("events") or []:
            comps_names = [c.get("name") for c in ev.get("competitors") or []]
            if len(comps_names) != 2:
                continue
            try:
                start_dt = datetime.fromtimestamp(int(ev["startTime"]) / 1000.0, timezone.utc)
            except Exception:
                continue
            market = None
            for dg in ev.get("displayGroups") or []:
                for mk in dg.get("markets") or []:
                    if str(mk.get("description", "")).lower() == "moneyline" and len(mk.get("outcomes") or []) == 2:
                        market = mk
                        break
                if market:
                    break
            if not market:
                continue
            outs = market["outcomes"]
            da = float(outs[0].get("price", {}).get("decimal") or 0) or None
            db = float(outs[1].get("price", {}).get("decimal") or 0) or None
            dv = devig_two(da, db)
            if not dv:
                continue
            rec = _record("Bovada", "bovada", comp, start_dt, outs[0].get("description"),
                          outs[1].get("description"), dv[0], dv[1],
                          "https://www.bovada.lv" + (ev.get("link") or ""), da, db,
                          note=f"Bovada moneyline (event {ev.get('id')})",
                          raw={"event_id": ev.get("id"), "american_a": outs[0].get("price", {}).get("american"),
                               "american_b": outs[1].get("price", {}).get("american")})
            if rec:
                records.append(rec)
    status.update({"status": "ok" if records else "no_data", "count": len(records), "competitions": comps})
    return {"status": status, "records": records}


def _poly_teams(title: str):
    m = re.match(r"^\s*LoL:\s*(.+?)\s+vs\.?\s+(.+?)\s*(?:\((?:BO\d+)\))?\s*[-–—]", title or "", re.I)
    if not m:
        m = re.match(r"^\s*LoL:\s*(.+?)\s+vs\.?\s+(.+?)\s*\((?:BO\d+)\)", title or "", re.I)
    return (m.group(1).strip(), m.group(2).strip()) if m else (None, None)


def fetch_polymarket() -> dict:
    status = {"source": "Polymarket", "key": "polymarket", "url": POLY_API, "status": "error", "count": 0}
    events = []
    for offset in (0, 100):
        url = (f"{POLY_API}/events?tag_slug=league-of-legends&active=true&closed=false"
               f"&limit=100&offset={offset}")
        data, r = get_json(url)
        if isinstance(data, list):
            events += data
        else:
            status.setdefault("errors", []).append(f"offset {offset}: HTTP {r.get('status')}")
        time.sleep(0.4)
    now = now_utc()
    records = []
    for ev in events:
        title = ev.get("title") or ""
        a, b = _poly_teams(title)
        if not a or not b:
            continue
        end = None
        try:
            end = datetime.fromisoformat(str(ev.get("endDate")).replace("Z", "+00:00"))
        except Exception:
            pass
        if end and (end < now - timedelta(days=2) or end > now + timedelta(days=21)):
            continue
        chosen = None
        for mk in ev.get("markets") or []:
            try:
                outs = json.loads(mk.get("outcomes") or "[]")
                prices = [float(x) for x in json.loads(mk.get("outcomePrices") or "[]")]
            except Exception:
                continue
            if len(outs) != 2 or len(prices) != 2:
                continue
            if {str(outs[0]).strip().lower(), str(outs[1]).strip().lower()} == {a.lower(), b.lower()}:
                q = (mk.get("question") or "").lower()
                game = "game 1" in q or "game 2" in q or "map 1" in q
                # Prefer the series/match market; keep a game-level market only as a
                # fallback and tag it so the model never mixes units on a Bo3/Bo5.
                if not game:
                    chosen = (outs, prices, mk, "series")
                    break
                if chosen is None:
                    chosen = (outs, prices, mk, "game1")
        if not chosen:
            continue
        outs, prices, mk, market_type = chosen
        if str(outs[0]).strip().lower() == a.lower():
            pa, pb = prices[0], prices[1]
        else:
            pa, pb = prices[1], prices[0]
        rec = _record("Polymarket", "polymarket", "Polymarket: " + title, end, a, b, pa, pb,
                      POLY_PAGE + str(ev.get("slug") or ""), note=f"Polymarket: {mk.get('question')}",
                      raw={"event_slug": ev.get("slug"), "market": mk.get("question"),
                           "market_type": market_type,
                           "volume": ev.get("volume"), "liquidity": ev.get("liquidity")})
        if rec:
            records.append(rec)
    status.update({"status": "ok" if records else "no_data", "count": len(records),
                   "events_seen": len(events)})
    return {"status": status, "records": records}


def main() -> int:
    results = []
    statuses = []
    for fn in (fetch_pinnacle, fetch_bovada, fetch_polymarket):
        try:
            out = fn()
        except Exception as e:  # noqa: BLE001 - one broken book must not stop the run
            log(f"{fn.__name__} crashed: {e!r}")
            out = {"status": {"source": fn.__name__, "key": fn.__name__, "status": "error",
                              "error": repr(e)[:200], "count": 0}, "records": []}
        statuses.append(out["status"])
        results += out["records"]
        log(f"markets: {out['status'].get('source')} -> {out['status'].get('status')} "
            f"({out['status'].get('count', 0)} records)")
    payload = {"generated_at": utc_iso(now_utc()), "statuses": statuses,
               "count": len(results), "records": results}
    write_json(OUT, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

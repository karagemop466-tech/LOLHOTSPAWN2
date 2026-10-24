#!/usr/bin/env python3
"""Diagnostic probe of candidate LoL odds/results sources (NOT production).

Purpose: every 4-8h production run prices fixtures from Pinnacle, Unibet (Kambi),
Bovada, Polymarket and Leaguepedia only. This probe re-checks the wider field of
established betting sites, esportsbooks, aggregators and *organiser* results pages
from GitHub Actions (the authoring sandbox cannot reach them) and records what is
*actually observed* — HTTP status, whether the response is structured JSON, and
whether any LoL per-match market or result is visible. Output:
data/diag/source_probe.json.

Rules:
  * one polite GET per candidate, no retries hammering, distinct UA where a site
    needs a browser-like client;
  * no price is ever copied into picks;
  * a source is only promoted into scripts/fetch_markets.py after a probe shows
    structured per-match prices AND a human verifies a sample row;
  * `tier` records what the brief asked us to try in order: established book →
    esportsbook → community/organiser results.
Exit code is always 0: a probe must never break the pipeline.
"""
from __future__ import annotations

import json
import re

from lib_common import fetch, log, now_utc, utc_iso, write_json

OUT = "data/diag/source_probe.json"

BROWSER = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/129.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# name, url, kind, tier, needs_browser_ua
CANDIDATES = [
    # ---- tier 1: established sportsbooks / odds aggregators -----------------
    ("Pinnacle guest LoL leagues (production)", "https://guest.api.arcadia.pinnacle.com/0.1/sports/12/leagues", "book-api", "established-book", False),
    ("Unibet (Kambi) LoL feed (production)", "https://eu-offering-api.kambicdn.com/offering/v2018/ubca/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=ZZ&useCombined=true", "book-api", "established-book", False),
    ("Bovada LoL coupon (production)", "https://www.bovada.lv/services/sports/event/coupon/events/A/description/esports/league-of-legends?marketFilterId=def&preMatchOnly=true&lang=en", "book-api", "established-book", False),
    ("Polymarket Gamma LoL tag (production)", "https://gamma-api.polymarket.com/events?tag_slug=league-of-legends&active=true&closed=false&limit=100", "prediction-market-api", "established-book", False),
    ("OddsPapi LoL (no key configured)", "https://oddspapi.io/sports/esports/lol", "aggregator-page", "established-book", False),
    ("The Odds API LoL (no key configured)", "https://api.the-odds-api.com/v4/sports/", "aggregator-api", "established-book", False),
    ("OddsPortal LoL board", "https://www.oddsportal.com/lol/", "odds-comparison-page", "established-book", True),
    ("BetExplorer LoL board", "https://www.betexplorer.com/lol/", "odds-comparison-page", "established-book", True),
    ("Kalshi esports series", "https://api.elections.kalshi.com/trade-api/v2/series?category=Esports", "prediction-market-api", "established-book", False),
    ("Smarkets esports API", "https://api.smarkets.com/v3/popular/events/sport/esports/", "exchange-api", "established-book", False),
    ("Manifold LoL search", "https://api.manifold.markets/v0/search-markets?term=league%20of%20legends&limit=5", "prediction-market-api", "established-book", False),
    # ---- tier 2: esportsbooks / esports betting lines -----------------------
    ("eGamersWorld LoL odds board", "https://egamersworld.com/lol/bets", "odds-comparison-page", "esportsbook", True),
    ("GG.Bet LoL", "https://gg.bet/en/esports/lol", "esportsbook-page", "esportsbook", True),
    ("Thunderpick LoL", "https://thunderpick.io/esports/league-of-legends", "esportsbook-page", "esportsbook", True),
    ("Rivalry LoL", "https://www.rivalry.com/lol", "esportsbook-page", "esportsbook", True),
    ("Midnite LoL", "https://www.midnite.com/esports/league-of-legends", "esportsbook-page", "esportsbook", True),
    ("Betway LoL", "https://www.betway.com/en/esports/league-of-legends", "esportsbook-page", "esportsbook", True),
    ("Betano esports", "https://www.betano.com/sport/esports/", "esportsbook-page", "esportsbook", True),
    ("Coolbet LoL", "https://www.coolbet.com/en/sports/esports/league-of-legends", "esportsbook-page", "esportsbook", True),
    ("1xBet LoL line", "https://1xbet.com/en/line/esports/", "esportsbook-page", "esportsbook", True),
    ("Stake LoL", "https://stake.com/sports/esports/league-of-legends", "esportsbook-page", "esportsbook", True),
    # ---- tier 3: community / organiser results (how low-tier rows get priced)
    ("Prime League (PRM organiser)", "https://www.primeleague.gg/en/leagues/prm/3227-fall-split-202627", "organiser-page", "community", True),
    ("Komplettligaen (organiser)", "https://www.komplettligaen.no/lol/", "organiser-page", "community", True),
    ("RIVALS LEAGUE (organiser)", "https://www.rivalsleague.gg/", "organiser-page", "community", True),
    ("Liquipedia LoL api.php", "https://liquipedia.net/leagueoflegends/api.php?action=query&list=search&srsearch=Prime_League&format=json", "wiki-api", "community", False),
    ("Leaguepedia Cargo MatchSchedule (production)", "https://lol.fandom.com/api.php?action=cargoquery&tables=MatchSchedule&fields=Team1,Team2,DateTime_UTC&limit=1&format=json", "wiki-api", "community", False),
    ("Leaguepedia Cargo Standings (production)", "https://lol.fandom.com/api.php?action=cargoquery&tables=Standings&fields=Team,WinSeries,LossSeries&limit=1&format=json", "wiki-api", "community", False),
    ("Riot LoLESports public schedule", "https://esports-api.lolesports.com/persisted/gw/getSchedule?hl=en-US", "official-api", "community", False),
]

LOW_TIER_MARKERS = (
    "prime league", "prm", "rivals", "tunisia", "komplett", "ligagg", "arabian",
    "4 nations", "lgc rising", "lfl", "em ea masters", "ultraliga", "hitpoint",
)


def probe(name, url, kind, tier, browser_ua):
    r = fetch(url, headers=BROWSER if browser_ua else None, timeout=30, retries=1)
    text = r.get("text") or ""
    status = r.get("status")
    is_json = False
    lol_hits = None
    detail = {}
    try:
        data = json.loads(text)
        is_json = True
        payload = json.dumps(data)[:400_000].lower()
        lol_hits = payload.count("league of legends")
        if isinstance(data, dict):
            detail["top_level_keys"] = sorted(data.keys())[:12]
            if isinstance(data.get("series"), list):  # Kalshi
                tickers = [str(s.get("ticker", "")) for s in data["series"] if isinstance(s, dict)]
                detail["series_count"] = len(tickers)
                detail["series_ticker_sample"] = tickers[:10]
        elif isinstance(data, list):
            detail["item_count"] = len(data)
            questions = [str(s.get("question", "") or s.get("title", "")) for s in data[:50] if isinstance(s, dict)]
            if questions:
                detail["vs_style_questions"] = sum(1 for q in questions if " vs " in q.lower())
                detail["question_sample"] = questions[:3]
    except Exception:
        pass

    lowered = text.lower()
    low_tier_hits = sorted({m for m in LOW_TIER_MARKERS if m in lowered}) if text else []
    detail["low_tier_markers_seen"] = low_tier_hits[:12]
    detail["bytes"] = len(text.encode("utf-8", "ignore"))

    return {
        "name": name, "url": url, "kind": kind, "tier": tier, "http_status": status,
        "is_json": is_json, "lol_mentions": lol_hits,
        "low_tier_markers_seen": low_tier_hits,
        "detail": detail,
        "verdict": ("reachable; structured JSON — candidate for a future adapter, "
                    "needs per-match price verification before any production use"
                    if status == 200 and is_json else
                    "reachable HTML — human cross-check only; no structured per-match prices parsed"
                    if status == 200 else
                    f"not usable from CI (HTTP {status})"),
    }


def main() -> int:
    results = []
    for name, url, kind, tier, browser_ua in CANDIDATES:
        try:
            res = probe(name, url, kind, tier, browser_ua)
        except Exception as e:  # noqa: BLE001 - probe must never break the run
            res = {"name": name, "url": url, "kind": kind, "tier": tier, "http_status": None,
                   "error": repr(e)[:200], "verdict": "probe error"}
        log(f"probe: {name} -> HTTP {res.get('http_status')} json={res.get('is_json')} "
            f"low_tier_markers={len(res.get('low_tier_markers_seen') or [])}")
        results.append(res)
    by_tier: dict[str, dict[str, int]] = {}
    for r in results:
        t = r.get("tier") or "other"
        bucket = by_tier.setdefault(t, {"probed": 0, "http_200": 0, "json": 0, "reachable_with_low_tier_markers": 0})
        bucket["probed"] += 1
        if r.get("http_status") == 200:
            bucket["http_200"] += 1
            if r.get("is_json"):
                bucket["json"] += 1
            if r.get("low_tier_markers_seen"):
                bucket["reachable_with_low_tier_markers"] += 1
    write_json(OUT, {"checked_at": utc_iso(now_utc()), "candidates": results, "by_tier": by_tier})
    log(f"probe: wrote {OUT} ({len(results)} candidates, tiers={sorted(by_tier)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

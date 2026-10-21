#!/usr/bin/env python3
"""Orchestrator: Hotspawn fixtures -> external markets -> own Elo -> docs/data/picks.json.

Run order is deliberate: markets and Leaguepedia are fetched independently of
Hotspawn, and the model consumes only those two. Hotspawn contributes the fixture
list, never a probability.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import timedelta

import fetch_hotspawn
import fetch_leaguepedia
import fetch_markets
import model
from lib_common import load_json, log, now_utc, utc_iso, write_json

DOCS_DATA = "docs/data/picks.json"

CHECKED_UNAVAILABLE = [
    {"name": "Betfair Exchange", "url": "https://www.betfair.com/exchange/plus/",
     "observed": "HTTP 403 to automated requests", "consequence": "No exchange prices used."},
    {"name": "Smarkets", "url": "https://smarkets.com/sport/esports/league-of-legends",
     "observed": "HTTP 403 (Cloudflare challenge)", "consequence": "No exchange prices used."},
    {"name": "Oddspapi", "url": "https://oddspapi.io/sports/esports/lol",
     "observed": "HTTP 401 without a paid API key", "consequence": "Adapter retained but disabled; no key is stored."},
    {"name": "The Odds API", "url": "https://the-odds-api.com/liveapi/guides/v4/",
     "observed": "HTTP 401 without a paid API key", "consequence": "Not used."},
    {"name": "OddsPortal", "url": "https://www.oddsportal.com/lol/",
     "observed": "HTTP 503 to automated requests", "consequence": "Not used."},
    {"name": "BetExplorer", "url": "https://www.betexplorer.com/lol/",
     "observed": "HTTP 404 at the LoL path", "consequence": "Not used."},
    {"name": "GG.Bet", "url": "https://gg.bet/en/esports/lol",
     "observed": "HTTP 403", "consequence": "Not used."},
    {"name": "Thunderpick", "url": "https://thunderpick.io/esports/league-of-legends",
     "observed": "HTTP 403 (Cloudflare)", "consequence": "Not used."},
    {"name": "Betway Esports", "url": "https://www.betway.com/en/esports/league-of-legends",
     "observed": "HTTP 404 (LoL page unavailable)", "consequence": "Not used."},
    {"name": "Unibet", "url": "https://www.unibet.com/betting/sports/filter/esports/league_of_legends",
     "observed": "HTTP 503", "consequence": "Not used."},
    {"name": "Rivalry", "url": "https://www.rivalry.com/lol",
     "observed": "HTML shell only; API endpoints HTTP 502", "consequence": "No prices parsed."},
    {"name": "Midnite", "url": "https://www.midnite.com/esports/league-of-legends",
     "observed": "HTML shell only, no server-rendered prices", "consequence": "Not used."},
    {"name": "Kalshi", "url": "https://api.elections.kalshi.com/trade-api/v2/series?category=Esports",
     "observed": "No League of Legends series returned", "consequence": "Not used."},
    {"name": "Manifold Markets", "url": "https://api.manifold.markets/v0/search-markets?term=league%20of%20legends",
     "observed": "Only futures/prop markets, no per-match prices", "consequence": "Not used for match picks."},
    {"name": "Riot LoLESports API", "url": "https://esports-api.lolesports.com/persisted/gw/getSchedule?hl=en-US",
     "observed": "HTTP 403 for the public key", "consequence": "Official Riot schedule not used; Leaguepedia is the results source."},
]

LIMITATIONS = [
    "No bookmaker or prediction market we can access prices most tier-3/amateur fixtures. Pinnacle, Bovada and Polymarket list the World Championship and EMEA Masters, not regional amateur leagues.",
    "The Elo model pools results across competitions and anchors each team to a strength tier for its league (international, top regional, ERL, national, academy). Those tiers are a documented prior: without cross-play the absolute gap between two leagues cannot be measured, only estimated. Cross-league rows are flagged and capped at Low confidence.",
    "Leaguepedia's MatchSchedule records results for many regional leagues, but coverage is uneven: some competitions only start being recorded part-way through a split, and brand-new teams have no games at all.",
    "Amateur rosters change frequently between splits, so historic team strength is a weaker signal than in tier-1 leagues.",
    "Where a team has no recorded games, the model falls back to the median rating of its competition (or the global median). That is a prior, not evidence about the team.",
    "A 50/50 row is a nominal placeholder. It is not an edge, not a recommendation, and not derived from Hotspawn's crowd percentage.",
    "Hotspawn shows match times in the visitor's local timezone. This site uses the epoch timestamp from Hotspawn's own fixtures API (UTC) and cross-checks it against Leaguepedia; disagreements over 30 minutes are flagged.",
]


def build_payload(fixtures, markets, leaguepedia, picks):
    now = now_utc()
    matches = picks["matches"]
    unresolved = [m for m in matches if m["method"] == "UNRESOLVED"]
    low_conf = [m for m in matches if m["method"] != "UNRESOLVED" and
                (m["method"] in ("MODEL_ELO_THIN", "MODEL_LEAGUE_PRIOR") or m["confidence"] == "Low")]
    market_matches = [m for m in matches if m["market"]]
    reasons = Counter()
    for m in unresolved:
        if "NO_TEAM_HISTORY" in m["flags"]:
            reasons["No recorded team history"] += 1
        elif "NO_EXTERNAL_MARKET" in m["flags"]:
            reasons["No external market and insufficient history"] += 1
        else:
            reasons["Other"] += 1
    for m in low_conf:
        if "ONE_TEAM_NO_HISTORY" in m["flags"]:
            reasons["One team has no recorded history (league prior used)"] += 1
        elif "THIN_HISTORY" in m["flags"]:
            reasons["Thin history (<5 games in 365 days)"] += 1

    next_24h = [m for m in matches if m["start_utc"] <= utc_iso(now + timedelta(hours=24))]
    tournaments = Counter(m["tournament"] for m in matches)
    source_status = []
    for s in markets.get("statuses", []):
        source_status.append({"name": s.get("source"), "url": s.get("url"), "status": s.get("status"),
                              "count": s.get("count"), "note": s.get("note") or s.get("error")})
    source_status.append({"name": "Leaguepedia MatchSchedule",
                          "url": "https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule",
                          "status": "ok" if leaguepedia["counts"]["results"] > 1000 else "degraded",
                          "count": leaguepedia["counts"]["results"],
                          "note": "Recorded results + schedules, exact UTC."})
    source_status.append({"name": "Hotspawn LoL Pick'em lobby", "url": fixtures["lobby"],
                          "status": "ok" if fixtures["count"] >= 50 else "degraded",
                          "count": fixtures["count"], "note": "Fixture list only."})

    payload = {
        "schema_version": 3,
        "generated_at": utc_iso(now),
        "next_update_utc": utc_iso(now + timedelta(hours=6)),
        "stale_after_utc": utc_iso(now + timedelta(hours=8)),
        "hotspawn_lobby": fixtures["lobby"],
        "hotspawn_lobby_generic": fixtures.get("lobby_generic"),
        "counts": {
            "fixtures": len(matches),
            "next_24h": len(next_24h),
            "market": len(market_matches),
            "model": sum(1 for m in matches if m["method"].startswith("MODEL")),
            "resolved": picks["coverage"]["resolved"],
            "unresolved": picks["coverage"]["unresolved"],
            "low_confidence": len(low_conf),
            "hotspawn_without_match_page": fixtures.get("without_match_page", 0),
        },
        "coverage": picks["coverage"],
        "model": picks["model"],
        "unresolved": {
            "count": len(unresolved),
            "low_confidence_count": len(low_conf),
            "reasons": [{"reason": k, "count": v} for k, v in reasons.most_common()],
            "low_confidence_reasons": [{"reason": k, "count": v}
                                       for k, v in Counter(
                                           "One team has no recorded history (league prior used)"
                                           if "ONE_TEAM_NO_HISTORY" in m["flags"] else
                                           "Cross-league comparison" if "CROSS_LEAGUE_MODEL" in m["flags"] else
                                           "Thin history (<8 games in 365 days)"
                                           for m in low_conf).most_common()],
            "limitations": LIMITATIONS,
        },
        "tournaments": [{"name": k, "count": v} for k, v in tournaments.most_common()],
        "sources_status": source_status,
        "checked_unavailable": CHECKED_UNAVAILABLE,
        "market_unmatched": picks.get("market_unmatched", [])[:40],
        "featured": [m["id"] for m in market_matches],
        "next_24h": [m["id"] for m in next_24h[:8]],
        "fixtures_without_page": [{"team1": m["team1"], "team2": m["team2"], "start_utc": m["start_utc"]}
                                  for m in matches if not m.get("hotspawn_url")],
        "matches": matches,
    }
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--use-cache", action="store_true", help="reuse data/cache/*.json (local debugging)")
    args = ap.parse_args()
    if not args.use_cache:
        fetch_hotspawn.main()
        fetch_markets.main()
        fetch_leaguepedia.main()
    else:
        log("using cached inputs")
    fixtures = load_json("data/cache/hotspawn.json")
    markets = load_json("data/cache/markets.json")
    leaguepedia = load_json("data/cache/leaguepedia.json")
    if not (fixtures and markets and leaguepedia):
        raise SystemExit("missing cache inputs; run without --use-cache")
    picks = model.run(fixtures, leaguepedia, markets)
    payload = build_payload(fixtures, markets, leaguepedia, picks)
    write_json(DOCS_DATA, payload, compact=True)
    log(f"wrote {DOCS_DATA}: {payload['counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

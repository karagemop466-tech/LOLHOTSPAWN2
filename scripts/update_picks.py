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
from source_probe import probe_sources
from standings_and_books import probe_liquipedia_pages

DOCS_DATA = "docs/data/picks.json"

CHECKED_UNAVAILABLE = [
    {"name": "Betfair Exchange", "url": "https://www.betfair.com/exchange/plus/",
     "observed": "HTTP 403 to automated requests", "consequence": "No exchange prices used."},
    {"name": "Smarkets", "url": "https://smarkets.com/sport/esports/league-of-legends",
     "observed": "HTTP 403 (Cloudflare challenge)", "consequence": "No exchange prices used."},
    {"name": "Oddspapi", "url": "https://oddspapi.io/sports/esports/lol",
     "observed": "HTTP 401 without a paid API key; no key is configured in this repository", "consequence": "No OddsPapi adapter exists in the pipeline; nothing is read from it, so no bookmaker line comes from OddsPapi."},
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
    {"name": "Unibet (www.unibet.com HTML shell)", "url": "https://www.unibet.com/betting/sports/filter/esports/league_of_legends",
     "observed": "HTTP 503 on the generic HTML filter URL", "consequence": "HTML shell not used; Unibet prices are read via Kambi's public JSON feed and linked to www.unibet.com.au."},
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
    "No bookmaker or prediction market we can access prices most tier-3/amateur fixtures. Pinnacle, Unibet (Kambi), Bovada and Polymarket list the World Championship and top tier-2/EMEA events, not regional amateur leagues.",
    "The Elo model pools results across competitions and anchors each team to a strength tier for its league (international, top regional, ERL, national, academy). Those tiers are a documented prior: without cross-play the absolute gap between two leagues cannot be measured, only estimated. Cross-league rows are flagged and capped at Low confidence.",
    "Leaguepedia's MatchSchedule and Standings tables record results for many regional leagues, but coverage is uneven: some competitions only start being recorded part-way through a split, and brand-new or withdrawn teams have no games at all.",
    "Amateur rosters change frequently between splits, so historic team strength is a weaker signal than in tier-1 leagues.",
    "The standings fallback (MODEL_STANDINGS) converts a team's current-split win-loss record in that competition into a smoothed Elo offset from the competition prior. It ignores strength of schedule inside the league, roster changes since those games, and any cross-league form, so it is capped at Low confidence and only used when there is no market line and Elo cannot rate that side.",
    "Where a team has no recorded games, the model falls back to the median rating of its competition (or the global median). That is a prior, not evidence about the team.",
    "A 50/50 row is a nominal placeholder. It is not an edge, not a recommendation, and not derived from Hotspawn's crowd percentage.",
    "Polymarket's own homepage (checked 2026-10-23) says trading is blocked in the United States and offers a view-only mode. Its public prices are used here only as reference data; this site never places or recommends a bet.",
    "Hotspawn shows match times in the visitor's local timezone. This site uses the epoch timestamp from Hotspawn's own fixtures API (UTC) and cross-checks it against Leaguepedia; disagreements over 30 minutes are flagged.",
]

# Liquipedia MediaWiki `list=allpages` needs a *page title prefix*, not a Hotspawn
# tournament label. Before 2026-10-24 this probe passed whole tournament names
# ("PRM 3rd Division 26-27 Fall") as `apprefix`, so it always returned no_data.
LIQUIPEDIA_PREFIXES = {
    "prime league": "Prime_League",
    "prm": "Prime_League",
    "rivals": "RIVALS_LEAGUE",
    "komplett": "Komplettligaen",
    "4 nations": "4_Nations",
    "tunisian": "Tunisian",
    "lgc rising": "LGC_Rising",
    "worlds": "2026_Season_World_Championship",
}


def liquipedia_prefixes_for(tournaments: list[str]) -> tuple[str, ...]:
    """Map the active Hotspawn tournament labels to Liquipedia page prefixes."""
    found: list[str] = []
    for t in tournaments:
        low = (t or "").lower()
        for needle, prefix in LIQUIPEDIA_PREFIXES.items():
            if needle in low and prefix not in found:
                found.append(prefix)
    return tuple(found) or ("Prime_League", "RIVALS_LEAGUE", "Komplettligaen")


# Verified operator / official pages. Matched by substring so a split suffix
# ("Komplettligaen 2026 Autumn Playoffs") still finds its league page.
# Only pages a human opened and confirmed on 2026-10-24 are listed here;
# competitions with no verified operator page are simply left without one.
ORGANIZER_LINKS = (
    ("PRM", "Prime League (organizer)", "https://www.primeleague.gg/en/leagues/prm/3227-fall-split-202627"),
    ("RIVALS LEAGUE", "RIVALS LEAGUE (organizer)", "https://www.rivalsleague.gg/lol"),
    ("Komplettligaen", "Komplettligaen (organizer)", "https://www.komplettligaen.no/lol/"),
    ("Worlds", "LoL Esports (official)", "https://lolesports.com/"),
    ("LGC Rising", "LoL Esports (official)", "https://lolesports.com/"),
    ("LCP", "LoL Esports (official)", "https://lolesports.com/"),
)


def organizer_for(tournament: str):
    """Return (name, url) for the first verified organizer page matching the label."""
    low = (tournament or "").lower()
    for needle, name, url in ORGANIZER_LINKS:
        if needle.lower() in low:
            return name, url
    return None



def classify_league_category(tournament: str) -> str:
    t = (tournament or "").lower()
    if any(k in t for k in ("worlds", "world championship", "msi", "first stand", "lck", "lpl", "lec", "lcs", "lta")):
        return "Tier 1 — International & Major Leagues"
    if any(k in t for k in ("emea masters", "em ", "promotion", "lgc rising", "2nd division", "prime league 1")):
        return "Tier 2 — Regional Challenger & Promotion"
    return "Tier 3 — National & Amateur Divisions"


def build_league_breakdown(matches: list[dict]) -> list[dict]:
    by_tour: dict[str, list[dict]] = {}
    for m in matches:
        by_tour.setdefault(m.get("tournament") or "Unknown competition", []).append(m)
    rows = []
    for tour, ms in sorted(by_tour.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        lp_url = next((m.get("leaguepedia_url") for m in ms if m.get("leaguepedia_url")), None)
        lp_page = next((m.get("leaguepedia_page") for m in ms if m.get("leaguepedia_page")), None)
        org = organizer_for(tour)
        mkt = sum(1 for m in ms if m.get("market"))
        elo = sum(1 for m in ms if m.get("method") in ("MODEL_ELO", "MODEL_ELO_THIN"))
        st = sum(1 for m in ms if m.get("method") == "MODEL_STANDINGS")
        prior = sum(1 for m in ms if m.get("method") == "MODEL_LEAGUE_PRIOR")
        unres = sum(1 for m in ms if m.get("method") == "UNRESOLVED")
        low = sum(1 for m in ms if m.get("confidence") == "Low" or m.get("method") in ("MODEL_ELO_THIN", "MODEL_LEAGUE_PRIOR"))
        if mkt == len(ms):
            lim = "Covered by external bookmakers/markets (de-vigged consensus). Polymarket end-dates drift vs UTC lock times; Hotspawn epoch timestamps govern lock times."
        elif mkt > 0:
            lim = f"{mkt}/{len(ms)} match(es) have external market odds; remaining matches rely on Leaguepedia recorded history and split standings."
        elif unres > 0:
            lim = f"No external bookmaker prices this competition; {unres} match(es) lack recorded split history on Leaguepedia and stay explicit 50/50 placeholders."
        elif prior > 0:
            lim = f"No bookmaker prices this league; {prior} match(es) involve a debut/unrecorded side priced against the {lp_page or 'competition'} median prior (Low confidence)."
        else:
            lim = "No external sportsbook prices this division; 100% of fixtures resolved via Leaguepedia recorded match results and split standings."
        rows.append({
            "tournament": tour,
            "category": classify_league_category(tour),
            "fixtures": len(ms),
            "market": mkt,
            "elo": elo,
            "standings": st,
            "league_prior": prior,
            "unresolved": unres,
            "low_confidence": low,
            "leaguepedia_page": lp_page,
            "leaguepedia_url": lp_url,
            "organizer_name": org[0] if org else None,
            "organizer_url": org[1] if org else None,
            "limitation": lim,
        })
    return rows


def build_payload(fixtures, markets, leaguepedia, picks, market_probe=None):
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
        if m["method"] == "MODEL_STANDINGS":
            reasons["Standings-based line (few decided series)"] += 1
        elif "ONE_TEAM_NO_HISTORY" in m["flags"]:
            reasons["One team has no recorded history (league prior used)"] += 1
        elif "CROSS_LEAGUE_MODEL" in m["flags"]:
            reasons["Cross-league comparison (confidence capped at Low)"] += 1
        elif "THIN_HISTORY" in m["flags"]:
            reasons["Thin history (<5 games in 365 days)"] += 1
        else:
            reasons["Other model uncertainty"] += 1

    next_24h = [m for m in matches if m["start_utc"] <= utc_iso(now + timedelta(hours=24))]
    tournaments = Counter(m["tournament"] for m in matches)

    # Per-league resolution breakdown: which signal prices each league, so the
    # Unresolved page (and the executive summary) can state limitations per
    # league instead of one undifferentiated bucket.
    by_league = {}
    for m in matches:
        b = by_league.setdefault(m["tournament"], {
            "tournament": m["tournament"], "fixtures": 0, "market": 0, "elo": 0,
            "standings": 0, "prior_only": 0, "unresolved": 0, "low_confidence": 0})
        b["fixtures"] += 1
        if m["market"]:
            b["market"] += 1
        elif m["method"] in ("MODEL_ELO", "MODEL_ELO_THIN"):
            b["elo"] += 1
        elif m["method"] == "MODEL_STANDINGS":
            b["standings"] += 1
        elif m["method"] == "MODEL_LEAGUE_PRIOR":
            b["prior_only"] += 1
        elif m["method"] == "UNRESOLVED":
            b["unresolved"] += 1
        if m in low_conf:
            b["low_confidence"] += 1
    for b in by_league.values():
        b["best_signal"] = ("External betting lines" if b["market"]
                            else "Elo on recorded results" if b["elo"]
                            else "Official standings record" if b["standings"]
                            else "League prior only" if b["prior_only"]
                            else "No verified signal")
    by_league_list = sorted(by_league.values(),
                             key=lambda b: (-b["unresolved"], -b["low_confidence"], -b["fixtures"]))
    source_status = []
    for s in markets.get("statuses", []):
        source_status.append({"name": s.get("source"), "url": s.get("url"), "status": s.get("status"),
                              "count": s.get("count"), "note": s.get("note") or s.get("error")})
    lp_degraded = bool(leaguepedia.get("degraded")) or leaguepedia["counts"]["results"] <= 1000
    standings_pages = len({(x.get("overview") or "") for x in (leaguepedia.get("standings") or [])
                           if x.get("overview")})
    source_status.append({"name": "Leaguepedia MatchSchedule",
                          "url": "https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule",
                          "status": "degraded" if lp_degraded else "ok",
                          "count": leaguepedia["counts"]["results"],
                          "note": (leaguepedia.get("degraded_reason")
                                   or ("Recorded results + schedules, exact UTC (CC BY-SA 3.0). "
                                       f"Standings rows: {leaguepedia['counts'].get('standings', 0)} "
                                       f"across {standings_pages} competitions."))})
    st_count = leaguepedia["counts"].get("standings", len(leaguepedia.get("standings") or []))
    source_status.append({"name": "Leaguepedia Standings",
                          "url": "https://lol.fandom.com/wiki/Special:CargoTables/Standings",
                          "status": "ok" if st_count > 0 else "no_data",
                          "count": st_count,
                          "note": "Split series/game records for low-tier & amateur leagues (CC BY-SA 3.0)."})
    liq_status = leaguepedia.get("liquipedia")
    if liq_status:
        source_status.append({"name": liq_status.get("name"), "url": liq_status.get("url"),
                              "status": liq_status.get("status"), "count": liq_status.get("count"),
                              "note": liq_status.get("note")})
    source_status.append({"name": "Hotspawn LoL Pick'em lobby", "url": fixtures["lobby"],
                          "status": "ok" if fixtures["count"] >= 50 else "degraded",
                          "count": fixtures["count"], "note": "Fixture list only (crowd % never used)."})

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
            "standings": sum(1 for m in matches if m["method"] == "MODEL_STANDINGS"),
            "resolved": picks["coverage"]["resolved"],
            "unresolved": picks["coverage"]["unresolved"],
            "low_confidence": len(low_conf),
            "hotspawn_without_match_page": fixtures.get("without_match_page", 0),
            "excluded_not_priced": len(fixtures.get("excluded") or []),
        },
        "coverage": picks["coverage"],
        "coverage_reconciliation": fixtures.get("reconciliation") or {},
        "excluded_fixtures": fixtures.get("excluded") or [],
        "model": {**picks["model"], "standings_pages": standings_pages},
        "league_breakdown": build_league_breakdown(matches),
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
            "by_league": by_league_list,
        },
        "tournaments": [{"name": k, "count": v} for k, v in tournaments.most_common()],
        "sources_status": source_status,
        "checked_unavailable": CHECKED_UNAVAILABLE,
        # Live-measured reachability of the wider external source field. Diagnostic
        # only: nothing here is used in a probability (see scripts/source_probe.py).
        "market_probe": market_probe or {"checked_at": None, "books": [], "summary": {}},
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
    if not args.use_cache and not leaguepedia.get("liquipedia"):
        tournaments_seen = sorted({(f.get("tournament") or "") for f in fixtures.get("fixtures") or []})
        leaguepedia["liquipedia"] = probe_liquipedia_pages(liquipedia_prefixes_for(tournaments_seen))
    picks = model.run(fixtures, leaguepedia, markets)
    market_probe = None
    if not args.use_cache:
        try:
            market_probe = probe_sources()
            write_json("data/diag/market_source_probe.json", market_probe)
        except Exception as e:  # noqa: BLE001 - a probe must never break the pipeline
            log(f"market source probe failed: {e!r}")
    payload = build_payload(fixtures, markets, leaguepedia, picks, market_probe)
    write_json(DOCS_DATA, payload, compact=True)
    log(f"wrote {DOCS_DATA}: {payload['counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

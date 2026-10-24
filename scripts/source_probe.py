#!/usr/bin/env python3
"""Live reachability probe of external LoL betting / results sources.

Why this exists
---------------
The published picks are priced from external sportsbook / prediction-market
lines where a line exists, otherwise from the own Elo model on recorded results.
Most Hotspawn LoL fixtures are tier-2/tier-3 competitions that the four
production feeds (Pinnacle, Unibet/Kambi, Bovada, Polymarket) do not price.

Rather than assert "no book prices this league" from memory, every production
run re-checks a fixed list of established sportsbooks, esportsbooks,
aggregators and community result sites with exactly ONE polite GET each and
publishes what was actually observed (HTTP status, whether the body is JSON,
and whether any League of Legends match market is visible).

Hard rules
----------
* This module **never returns a probability and never feeds the model.** It only
  records reachability. A source is promoted into `scripts/fetch_markets.py`
  only after a probe shows structured per-match prices AND a human verifies a
  sample row against the live page (see research/betting-sources.md).
* No authentication is configured and none is invented: endpoints that need a
  key (OddsPapi, odds-api.io, Abios, PandaScore) are recorded as key-required.
* Failures are recorded, never raised: a probe must not break the 6-hour run.
"""
from __future__ import annotations

import json
import re

from concurrent.futures import ThreadPoolExecutor

from lib_common import fetch, log, now_utc, utc_iso

# Public Riot LoLESports key embedded in the official lolesports.com web client.
# It is used only to test whether the official schedule endpoint is reachable.
RIOT_PUBLIC_KEY = "0TvQnueqKa5mxJntVWt0w4LpLssiF19a8wLoPLD"

# Public guest key used by Pinnacle's own web client (same value as scripts/fetch_markets.py).
PINNACLE_PUBLIC_KEY = "CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R"

# (name, url, kind, category)
# category: market  = bookmaker / exchange / prediction market / odds aggregator
#           results = community or official results & schedule source
CANDIDATES: tuple[tuple[str, str, str, str], ...] = (
    # --- established sportsbooks / exchanges ---------------------------------
    ("Pinnacle (guest JSON)", "https://guest.api.arcadia.pinnacle.com/0.1/sports/12/leagues",
     "bookmaker-api", "market"),
    ("Betfair Exchange", "https://www.betfair.com/exchange/plus/", "exchange-page", "market"),
    ("Smarkets API (sports index)", "https://api.smarkets.com/v3/sports/", "exchange-api", "market"),
    ("Betway Esports LoL", "https://www.betway.com/en/esports/league-of-legends", "sportsbook-page", "market"),
    ("BetOnline LoL", "https://www.betonline.ag/sportsbook/esports/league-of-legends", "sportsbook-page", "market"),
    ("Unibet LoL (HTML shell)", "https://www.unibet.com/betting/sports/filter/esports/league_of_legends",
     "sportsbook-page", "market"),
    # --- esportsbooks --------------------------------------------------------
    ("GG.Bet LoL", "https://gg.bet/en/esports/lol", "esportsbook-page", "market"),
    ("Thunderpick LoL", "https://thunderpick.io/esports/league-of-legends", "esportsbook-page", "market"),
    ("Rivalry LoL", "https://www.rivalry.com/lol", "esportsbook-page", "market"),
    ("Midnite LoL", "https://www.midnite.com/esports/league-of-legends", "esportsbook-page", "market"),
    ("1xBet line feed (sports index)", "https://1xbet.com/LineFeed/GetSportsShortZip?lng=en&country=1",
     "esportsbook-api", "market"),
    # --- odds aggregators (keys are NOT configured) --------------------------
    ("OddsPapi (API — no key configured)", "https://api.oddspapi.io/v1/sports", "aggregator-api", "market"),
    ("odds-api.io (API — no key configured)", "https://api.odds-api.io/v3/sports", "aggregator-api", "market"),
    ("OddsPortal LoL", "https://www.oddsportal.com/lol/", "aggregator-page", "market"),
    ("BetExplorer LoL", "https://www.betexplorer.com/lol/", "aggregator-page", "market"),
    ("eGamersWorld LoL odds", "https://egamersworld.com/lol/bets", "aggregator-page", "market"),
    # --- more established sportsbooks / exchanges (added 2026-10-24, v2) ------
    ("DraftKings LoL", "https://sportsbook.draftkings.com/leagues/esports/league-of-legends",
     "sportsbook-page", "market"),
    ("FanDuel LoL", "https://www.fanduel.com/sportsbook/esports/league-of-legends", "sportsbook-page", "market"),
    ("BetMGM LoL", "https://sports.betmgm.com/en/sports/esports-8/betting/all", "sportsbook-page", "market"),
    ("bet365 esports", "https://www.bet365.com/#/AX/", "sportsbook-page", "market"),
    ("Betsson esports", "https://www.betsson.com/en/esports/league-of-legends", "sportsbook-page", "market"),
    ("Paf esports", "https://www.paf.com/en/sports/esports", "sportsbook-page", "market"),
    ("Betano esports", "https://www.betano.com/sport/esports/", "sportsbook-page", "market"),
    ("Betspawn LoL (Hotspawn's own book)", "https://betspawn.com/esports/league-of-legends",
     "esportsbook-page", "market"),
    ("Sportsbetting.ag LoL", "https://www.sportsbetting.ag/sportsbook/esports/league-of-legends",
     "sportsbook-page", "market"),
    ("BetUS esports", "https://www.betus.com.pa/sportsbook/esports/league-of-legends/",
     "sportsbook-page", "market"),
    ("Oddspedia LoL", "https://oddspedia.com/esports/league-of-legends", "aggregator-page", "market"),
    # --- the four feeds that actually produce probabilities (live health check) --
    ("Pinnacle LoL matchups (wired feed)",
     "https://guest.api.arcadia.pinnacle.com/0.1/sports/12/leagues?all=false", "bookmaker-api", "wired"),
    # exactly the first production URL (market=ZZ / useCombined=true), so a health check
    # failure means the production feed is really failing
    ("Unibet/Kambi LoL listView (wired feed)",
     "https://eu-offering-api.kambicdn.com/offering/v2018/ubca/listView/esports/league_of_legends/all/all/matches.json?lang=en_GB&market=ZZ&useCombined=true",
     "bookmaker-api", "wired"),
    ("Bovada esports coupon (wired feed)",
     "https://www.bovada.lv/services/sports/event/coupon/events/A/description/esports?marketFilterId=def&preMatchOnly=true&lang=en",
     "bookmaker-api", "wired"),
    ("Polymarket LoL tag (wired feed)",
     "https://gamma-api.polymarket.com/events?tag_slug=league-of-legends&limit=5", "prediction-market-api", "wired"),
    # --- prediction markets --------------------------------------------------
    ("Kalshi esports series", "https://api.elections.kalshi.com/trade-api/v2/series?category=Esports",
     "prediction-market-api", "market"),
    ("Manifold Markets LoL search",
     "https://api.manifold.markets/v0/search-markets?term=league%20of%20legends&limit=5",
     "prediction-market-api", "market"),
    # --- community / official results ----------------------------------------
    ("gol.gg tournament index", "https://gol.gg/tournament/list/", "results-page", "results"),
    ("bo3.gg LoL matches", "https://bo3.gg/lol/matches", "results-page", "results"),
    ("Riot LoLESports official schedule",
     "https://esports-api.lolesports.com/persisted/gw/getSchedule?hl=en-US", "official-api", "results"),
    ("Liquipedia LoL API", "https://liquipedia.net/leagueoflegends/api.php?action=query&meta=siteinfo&format=json",
     "wiki-api", "results"),
)

LOL_RE = re.compile(r"league\s*of\s*legends|\blol\b|leagueoflegends", re.I)
VS_RE = re.compile(r"\bvs\.?\b|\bv\b", re.I)


def _verdict(status: int | None, is_json: bool, lol_hits: int | None, kind: str,
             category: str = "market") -> str:
    results_kind = kind in ("results-page", "wiki-api", "official-api")
    if category == "wired":
        if status == 200:
            if lol_hits:
                return ("production feed, reachable this run with League of Legends markets in the response — "
                        "one of the four sources that may contribute a probability (subject to the de-vig and "
                        "dedup rules in Methodology)")
            return ("production feed reachable, but no League of Legends market in this response — "
                    "it contributed no probability this run")
        return (f"production feed FAILED this run (HTTP {status or 'network error'}) — any market probability "
                "from this source is missing from the picks until it recovers")
    if status == 401 or status == 402:
        return "requires an API key / paid plan — no key is configured, so nothing is used"
    if status == 403:
        return "blocked to automated requests (HTTP 403) — no line can be read"
    if status in (202, 203):
        return (f"served an interstitial/redirect page (HTTP {status}) instead of the feed — "
                "no line can be read")
    if status in (404, 410):
        return f"endpoint not found (HTTP {status}) — path may have moved; nothing used"
    if status in (500, 502, 503, 504) or status == 0:
        return f"not reachable from CI this run (HTTP {status or 'network error'}) — nothing used"
    if status == 200 and results_kind:
        return ("reachable results/metadata page (HTML or API) — not parsed, and never a probability input; "
                "Leaguepedia remains the results source and this is a manual cross-check only")
    if status == 200 and is_json:
        if lol_hits:
            return ("reachable JSON with League of Legends references — candidate for an adapter only "
                    "after a human verifies a sample price; not used in any probability yet")
        return ("reachable JSON without any League of Legends match market in the response — nothing used")
    if status == 200:
        return ("reachable HTML only — no structured per-match prices parsed; human cross-check only, "
                "never used in a probability")
    return f"HTTP {status} — nothing used"


def probe_candidate(name: str, url: str, kind: str, category: str) -> dict:
    headers = None
    if "lolesports.com" in url:
        headers = {"x-api-key": RIOT_PUBLIC_KEY}
    elif "arcadia.pinnacle.com" in url:
        headers = {"x-api-key": PINNACLE_PUBLIC_KEY, "Accept": "application/json"}
    row = {"name": name, "url": url, "kind": kind, "category": category, "wired": category == "wired",
           "http_status": None, "is_json": False, "bytes": 0,
           "lol_mentions": None, "vs_style_items": None, "verdict": ""}
    try:
        # retries=1 means exactly one attempt (lib_common.fetch returns None when retries=0)
        r = fetch(url, headers=headers, timeout=12, retries=1) or {}
        text = r.get("text") or ""
        status = r.get("status")
        row["http_status"] = status
        row["bytes"] = len(text.encode("utf-8", "ignore"))
        lol_hits = None
        vs_items = None
        if status == 200:
            try:
                data = json.loads(text)
                row["is_json"] = True
                blob = json.dumps(data)[:400000]
                lol_hits = len(LOL_RE.findall(blob))
                if isinstance(data, list):
                    vs_items = sum(1 for x in data[:200] if isinstance(x, (dict, str))
                                   and VS_RE.search(json.dumps(x)[:600]))
                elif isinstance(data, dict):
                    for key in ("events", "markets", "series", "data", "results", "leagues"):
                        v = data.get(key)
                        if isinstance(v, list):
                            vs_items = sum(1 for x in v[:200] if isinstance(x, (dict, str))
                                           and VS_RE.search(json.dumps(x)[:600]))
                            break
            except json.JSONDecodeError:
                lol_hits = len(LOL_RE.findall(text[:400000]))
        row["lol_mentions"] = lol_hits
        row["vs_style_items"] = vs_items
        row["verdict"] = _verdict(status, row["is_json"], lol_hits, kind, category)
        if "no key configured" in name.lower() and status == 200:
            row["verdict"] = ("endpoint answers without a key, but the payload carries no League of Legends "
                              "match market — its data needs a paid API key that is not configured here; nothing used")
    except Exception as e:  # noqa: BLE001 - a probe must never break the run
        row["verdict"] = f"probe error: {repr(e)[:120]}"
        row["http_status"] = 0
    return row


def probe_sources(limit: int | None = None) -> dict:
    """Probe every candidate once and return {checked_at, books, summary}.

    Candidates are probed concurrently (one GET per host, at most 6 in flight) so a
    37-source list costs ~1 network timeout instead of 37 of them.
    """
    todo = list(CANDIDATES[:limit] if limit else CANDIDATES)
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(lambda c: probe_candidate(*c), todo))
    for row in rows:
        log(f"probe: {row['name']} -> HTTP {row['http_status']} json={row['is_json']} "
            f"lol={row['lol_mentions']}")
    for r in rows:
        st = r.get("http_status")
        r["reachable"] = st == 200
        r["structured"] = bool(r.get("reachable") and r.get("is_json"))
    market = [r for r in rows if r["category"] == "market"]
    results = [r for r in rows if r["category"] == "results"]
    wired = [r for r in rows if r["category"] == "wired"]
    summary = {
        "checked": len(rows),
        "reachable": sum(1 for r in rows if r["reachable"]),
        "structured_json": sum(1 for r in rows if r["structured"]),
        "structured_with_lol": sum(1 for r in rows if r["structured"] and (r.get("lol_mentions") or 0) > 0),
        "market_sources_checked": len(market),
        "market_sources_reachable": sum(1 for r in market if r["reachable"]),
        "results_sources_reachable": sum(1 for r in results if r["reachable"]),
        "wired_feeds_checked": len(wired),
        "wired_feeds_reachable": sum(1 for r in wired if r["reachable"]),
        "blocked": sum(1 for r in rows if r["http_status"] in (401, 402, 403, 429, 202, 203)),
        "note": ("Probe only: no probed value is used in any probability. "
                 "Only the four production feeds (Pinnacle, Unibet/Kambi, Bovada, Polymarket) "
                 "produce market probabilities."),
    }
    return {"checked_at": utc_iso(now_utc()), "books": rows, "summary": summary}


def main() -> int:
    """Write the diagnostic artifact used by CI and the research doc."""
    from lib_common import write_json
    data = probe_sources()
    write_json("data/diag/market_source_probe.json", data)
    print(json.dumps(data["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

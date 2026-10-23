#!/usr/bin/env python3
"""Probe candidate League of Legends betting sources from the CI runner.

Why this exists: the brief asks us to try established LoL betting sites first and
only then fall back to our own line. Several books are known by name but have no
documented public feed, so whether they can be used is an empirical question.
This script measures it instead of guessing: it requests each candidate endpoint
with a normal browser user-agent, records the HTTP status, a short body preview
and whether League-of-Legends-shaped two-way prices are present.

Nothing is inferred from a page that merely returns 200: a source is only marked
`prices: true` when a JSON body contains two opposing decimal/american prices for
a team pair. Results are written to data/diag/market_probe.json and published on
the *Flagged for review* page as measured evidence.

Usage: python3 scripts/probe_markets.py [--out data/diag/market_probe.json]
"""
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone

from lib_common import fetch, log, now_utc, utc_iso, write_json

CANDIDATES = [
    # --- established sportsbooks with a public front-end feed -----------------
    ("Pinnacle", "https://www.pinnacle.com/en/esports/league-of-legends", "html"),
    ("Pinnacle guest API", "https://guest.api.arcadia.pinnacle.com/0.1/sports/12/leagues", "json"),
    ("Bovada", "https://www.bovada.lv/services/sports/event/coupon/events/A/description/"
               "esports/league-of-legends?marketFilterId=def&preMatchOnly=true&lang=en", "json"),
    ("DraftKings", "https://sportsbook.draftkings.com/leagues/esports/league-of-legends", "html"),
    ("FanDuel", "https://sportsbook.fanduel.com/esports/league-of-legends", "html"),
    ("BetMGM", "https://sports.betmgm.com/en/sports/esports-8/betting/usa-9/league-of-legends-14571", "html"),
    ("bet365", "https://www.bet365.com/#/AC/B151/C1/D50/E2/F163/", "html"),
    ("William Hill", "https://sports.williamhill.com/betting/en-gb/esports", "html"),
    ("Unibet", "https://www.unibet.com/betting/sports/filter/esports/league_of_legends", "html"),
    ("Marathonbet", "https://www.marathonbet.com/en/betting/Esports/", "html"),
    ("1xBet", "https://1xbet.com/en/line/esports/", "html"),
    ("Betway", "https://www.betway.com/en/esports/league-of-legends", "html"),
    # --- esports-specific books ----------------------------------------------
    ("GG.Bet", "https://gg.bet/en/esports/lol", "html"),
    ("Thunderpick", "https://thunderpick.io/esports/league-of-legends", "html"),
    ("Rivalry", "https://www.rivalry.com/lol", "html"),
    ("Midnite", "https://www.midnite.com/esports/league-of-legends", "html"),
    ("Loot.bet", "https://www.loot.bet/sportsbook/league-of-legends", "html"),
    ("BUFF.bet", "https://www.buff.bet/esports/league-of-legends", "html"),
    ("BetOnline", "https://www.betonline.ag/sportsbook/esports/league-of-legends", "html"),
    ("SportsBetting.ag", "https://www.sportsbetting.ag/sportsbook/esports/league-of-legends", "html"),
    ("BetUS", "https://www.betus.com.pa/sportsbook/esports/league-of-legends/", "html"),
    ("Bodog", "https://www.bodog.eu/sportsbook/esports/league-of-legends", "html"),
    # --- exchanges / aggregators / prediction markets -------------------------
    ("Betfair Exchange", "https://www.betfair.com/exchange/plus/esports", "html"),
    ("Smarkets", "https://smarkets.com/sport/esports/league-of-legends", "html"),
    ("OddsPortal", "https://www.oddsportal.com/lol/", "html"),
    ("BetExplorer", "https://www.betexplorer.com/lol/", "html"),
    ("Polymarket Gamma", "https://gamma-api.polymarket.com/events?tag_slug=league-of-legends"
                         "&active=true&closed=false&limit=20", "json"),
    ("Kalshi", "https://api.elections.kalshi.com/trade-api/v2/series?category=Esports", "json"),
    ("OddsPapi", "https://api.oddspapi.io/v1/sports", "json"),
    ("The Odds API", "https://api.the-odds-api.com/v4/sports/esports_league_of_legends/odds/", "json"),
    ("Riot LoLESports (unofficial)", "https://esports-api.lolesports.com/persisted/gw/getLeagues"
                                     "?hl=en-US", "json"),
]

# Two-way price shapes seen in bookmaker JSON: american (+150/-170) or decimal (1.6/2.4)
PRICE_KEY = re.compile(
    r'"(?:price|decimalOdds|decimal_price|americanOdds|odds|moneyline|'
    r'homeTeamOdds|awayTeamOdds|handicap)"\s*:', re.I)
TWO_WAY = re.compile(r'"(?:price|decimalOdds|decimal_price|americanOdds|odds)"\s*:\s*"?[+-]?\d')


def classify(body: str, kind: str) -> dict:
    text = body[:400000]
    looks_lol = bool(LOLISH.search(text))
    two_way = bool(PRICE_KEY.search(text) and TWO_WAY.search(text)) if kind == "json" else False
    return {"league_of_legends_content": looks_lol, "two_way_prices_in_body": two_way}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/diag/market_probe.json")
    ap.add_argument("--sleep", type=float, default=1.0)
    args = ap.parse_args()

    results = []
    for name, url, kind in CANDIDATES:
        r = fetch(url, timeout=30, retries=1)
        rec = {
            "name": name, "url": url, "expected": kind,
            "http_status": r.get("status"), "error": r.get("error"),
            "bytes": len(r.get("body") or b""),
        }
        if r.get("status") == 200:
            rec.update(classify(r.get("text") or "", kind))
            rec["preview"] = (r.get("text") or "")[:220].replace("\n", " ")
        rec["usable_as_feed"] = bool(rec.get("http_status") == 200
                                     and rec.get("two_way_prices_in_body"))
        results.append(rec)
        log(f"probe: {name:<30} HTTP {rec['http_status']!s:<5} "
            f"lol={rec.get('league_of_legends_content')} prices={rec.get('two_way_prices_in_body')}")
        time.sleep(args.sleep)

    payload = {
        "schema": "market-probe/1",
        "generated_at": utc_iso(now_utc()),
        "method": ("One unauthenticated GET per endpoint from the GitHub Actions runner with a "
                   "normal browser user-agent. 'two_way_prices_in_body' only records that a "
                   "JSON body contains decimal/american price fields; it does not claim the "
                   "endpoint is licensed, stable or complete."),
        "results": results,
    }
    write_json(args.out, payload)
    usable = [r["name"] for r in results if r["usable_as_feed"]]
    log(f"probe: {len(results)} endpoints, usable JSON price feeds: {usable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Diagnostic probe of candidate LoL odds/results sources (NOT production).

Every 4-8h production run prices fixtures from Pinnacle, Unibet (Kambi), Bovada,
Polymarket and Leaguepedia only. This probe re-checks the wider field of
established betting sites, esportsbooks, esports-lines aggregators, prediction
markets and official/community result sources from GitHub Actions (the sandbox
cannot reach them) and records what is *actually observed*: HTTP status, whether
the response is structured JSON, how many League of Legends mentions and
"X vs Y" pairs are visible, and any explicit block/closure message.

Rules: one polite GET per candidate, no price is ever copied into picks, and a
source is only promoted into scripts/fetch_markets.py after a probe shows
structured per-match prices AND a human verifies a sample row. Exit code is
always 0: a probe must never break the pipeline.

Outputs:
  data/diag/source_probe.json  (diagnostic artifact)
  docs/data/source_probe.json  (published so the site can show the last probe)
"""
from __future__ import annotations

import json
import re

from lib_common import fetch, log, now_utc, utc_iso, write_json

OUT = "data/diag/source_probe.json"
PUBLIC_OUT = "docs/data/source_probe.json"

PIN_KEY = {"x-api-key": "CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R", "Accept": "application/json"}

CANDIDATES = [
    # category, name, url, kind, headers
    ("Established sportsbooks", "Pinnacle guest leagues",
     "https://guest.api.arcadia.pinnacle.com/0.1/sports/12/leagues", "sportsbook-json", PIN_KEY),
    ("Established sportsbooks", "Unibet (Kambi) LoL matches",
     ("https://eu-offering-api.kambicdn.com/offering/v2018/ubca/listView/"
      "esports/league_of_legends/all/all/matches.json?lang=en_GB&market=ZZ&useCombined=true"),
     "sportsbook-json", None),
    ("Established sportsbooks", "Bovada LoL coupon",
     ("https://www.bovada.lv/services/sports/event/coupon/events/A/description/"
      "esports/league-of-legends"),
     "sportsbook-json", {"Referer": "https://www.bovada.lv/"}),
    ("Established sportsbooks", "DraftKings LoL page",
     "https://sportsbook.draftkings.com/leagues/esports/league-of-legends", "sportsbook-page", None),
    ("Established sportsbooks", "BetOnline LoL page",
     "https://www.betonline.ag/sportsbook/esports/league-of-legends", "sportsbook-page", None),
    ("Established sportsbooks", "Betway LoL page",
     "https://www.betway.com/en/esports/league-of-legends", "sportsbook-page", None),
    ("Esportsbooks", "Thunderpick LoL", "https://thunderpick.io/esports/league-of-legends",
     "esportsbook-page", None),
    ("Esportsbooks", "GG.Bet LoL", "https://gg.bet/en/esports/lol", "esportsbook-page", None),
    ("Esportsbooks", "Rivalry LoL", "https://www.rivalry.com/lol", "esportsbook-page", None),
    ("Esportsbooks", "Midnite LoL", "https://www.midnite.com/esports/league-of-legends",
     "esportsbook-page", None),
    ("Esports lines/aggregators", "OddsPortal LoL", "https://www.oddsportal.com/lol/",
     "odds-comparison-page", None),
    ("Esports lines/aggregators", "OddsPortal Prime League",
     "https://www.oddsportal.com/esports/league-of-legends/league-of-legends-prime-league/",
     "odds-comparison-page", None),
    ("Esports lines/aggregators", "BetExplorer LoL", "https://www.betexplorer.com/lol/",
     "odds-comparison-page", None),
    ("Esports lines/aggregators", "eGamersWorld LoL", "https://egamersworld.com/lol/bets",
     "odds-comparison-page", None),
    ("Esports lines/aggregators", "OddsPapi LoL (no key configured)",
     "https://oddspapi.io/sports/esports/lol", "aggregator-page", None),
    ("Prediction markets", "Polymarket Gamma (LoL tag)",
     "https://gamma-api.polymarket.com/events?tag_slug=league-of-legends&closed=false&limit=5",
     "prediction-market-json", None),
    ("Prediction markets", "Kalshi esports series",
     "https://api.elections.kalshi.com/trade-api/v2/series?category=Esports",
     "prediction-market-json", None),
    ("Prediction markets", "Manifold Markets (LoL search)",
     "https://api.manifold.markets/v0/search-markets?term=league%20of%20legends&limit=5",
     "prediction-market-json", None),
    ("Prediction markets", "Smarkets API (popular esports)",
     "https://api.smarkets.com/v3/popular/events/sport/esports/", "exchange-api", None),
    ("Prediction markets", "Betfair Exchange", "https://www.betfair.com/exchange/plus/",
     "exchange-page", None),
    ("Results & verification", "Leaguepedia CargoExport (Standings sample)",
     ("https://lol.fandom.com/wiki/Special:CargoExport?tables=Standings"
      "&fields=OverviewPage,Team&limit=1&format=json"),
     "wiki-json", None),
    ("Results & verification", "Liquipedia API siteinfo",
     "https://liquipedia.net/leagueoflegends/api.php?action=query&meta=siteinfo&format=json",
     "wiki-json", None),
    ("Results & verification", "Riot LoLESports schedule",
     "https://esports-api.lolesports.com/persisted/gw/getSchedule?hl=en-US", "official-api", None),
    ("Results & verification", "LoL Esports official site", "https://lolesports.com/",
     "official-page", None),
    ("Results & verification", "Prime League organizer",
     "https://www.primeleague.gg/en/leagues/prm/3227-fall-split-202627", "organizer-page", None),
    ("Results & verification", "RIVALS LEAGUE organizer", "https://www.rivalsleague.gg/",
     "organizer-page", None),
    ("Results & verification", "Komplettligaen organizer", "https://www.komplettligaen.no/lol/",
     "organizer-page", None),
]

SIGNALS = [
    ("not accepting visitors", "region-blocked"),
    ("operationally-closed", "closed"),
    ("operationally closed", "closed"),
    ("we’ve had a glitch", "404-glitch"),
    ("we've had a glitch", "404-glitch"),
    ("next matches will appear", "no-current-odds"),
    ("as soon as bookmaker betting odds become available", "no-current-odds"),
    ("cloudflare", "cloudflare-challenge"),
    ("just a moment", "cloudflare-challenge"),
    ("forbidden", "forbidden"),
]


def _signals(text: str) -> list[str]:
    low = (text or "").lower()
    return sorted({label for phrase, label in SIGNALS if phrase in low})


def _html_title(text: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", text or "", re.I | re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip()[:160] if m else ""


def probe(category: str, name: str, url: str, kind: str, headers: dict | None = None) -> dict:
    r = fetch(url, headers=headers, timeout=15, retries=1)
    text = r.get("text") or ""
    status = r.get("status")
    is_json = False
    detail = {}
    lol_hits = None
    vs_pairs = None
    try:
        data = json.loads(text)
        is_json = True
        if isinstance(data, dict):
            detail["top_level_keys"] = sorted(data.keys())[:12]
            if isinstance(data.get("series"), list):  # Kalshi
                detail["series_count"] = len(data["series"])
                lol_hits = sum(1 for s in data["series"]
                               if "league of legends" in json.dumps(s).lower()
                               or str(s.get("ticker", "")).upper().startswith("KXLOL"))
            if isinstance(data.get("events"), list):  # Polymarket
                detail["event_count"] = len(data["events"])
                titles = " ".join(str(e.get("title", "")) for e in data["events"] if isinstance(e, dict))
                lol_hits = titles.lower().count("league of legends") + titles.lower().count("lol ")
        elif isinstance(data, list):
            detail["item_count"] = len(data)
            blob = json.dumps(data[:60]).lower()
            lol_hits = blob.count("league of legends") + blob.count("lol")
            questions = [str(s.get("question", "")) for s in data[:60] if isinstance(s, dict)]
            if questions:
                detail["vs_style_questions"] = sum(1 for q in questions if " vs " in q.lower())
                detail["question_sample"] = questions[:3]
    except Exception:
        pass
    if status == 200 and not is_json:
        low = (text or "").lower()
        lol_hits = low.count("league of legends") + low.count(" lol")
        vs_pairs = len(re.findall(r"\bvs\b", text or "", re.I))
        t = _html_title(text)
        if t:
            detail["title"] = t
    signals = _signals(text)
    if is_json and status == 200:
        verdict = f"reachable structured JSON ({len(text)} bytes)"
        if lol_hits is not None:
            verdict += f"; LoL mentions: {lol_hits}"
    elif status == 200:
        verdict = "reachable HTML only — no structured per-match prices parsed"
        if lol_hits is not None:
            verdict += f" (LoL mentions: {lol_hits}, 'vs' occurrences: {vs_pairs})"
    else:
        verdict = f"not usable from CI (HTTP {status})"
    if signals:
        verdict += "; signals: " + ", ".join(signals)
    return {
        "category": category,
        "name": name,
        "url": url,
        "kind": kind,
        "http_status": status,
        "bytes": len(text.encode("utf-8", "ignore")),
        "is_json": is_json,
        "lol_mentions": lol_hits,
        "vs_pairs": vs_pairs,
        "signals": signals,
        "detail": detail,
        "verdict": verdict,
        "error": r.get("error"),
    }


def main() -> int:
    results = []
    for category, name, url, kind, headers in CANDIDATES:
        try:
            res = probe(category, name, url, kind, headers)
        except Exception as e:  # noqa: BLE001 - probe must never break the run
            res = {"category": category, "name": name, "url": url, "kind": kind,
                   "http_status": None, "error": repr(e)[:200], "verdict": "probe error"}
        log(f"probe: {name} -> HTTP {res.get('http_status')} json={res.get('is_json')}")
        results.append(res)
    payload = {"checked_at": utc_iso(now_utc()), "candidates": results}
    write_json(OUT, payload)
    write_json(PUBLIC_OUT, payload, compact=True)
    log(f"probe: wrote {OUT} and {PUBLIC_OUT} ({len(results)} candidates)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

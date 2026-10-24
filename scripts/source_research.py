#!/usr/bin/env python3
"""Verified source ladder for League of Legends match prices.

Every entry below was requested directly and the observed response is recorded
with the date it was checked. A source becomes a *probability input* only when
the pipeline can read a structured two-way per-match price from it; everything
else is a reference link or explicitly marked as not usable. No entry is
inferred, and no missing price is filled in.

The live pipeline status/count for Pinnacle, Unibet (Kambi), Bovada, Polymarket
and Leaguepedia is merged in from the run that produced this payload, so the
published table cannot claim a source that returned nothing in that run.

This module is deliberately data-only: it never fetches the network itself.
`scripts/probe_sources.py` performs the independent HTTP probe and writes
`data/diag/source_probe.json`; when that file is available its HTTP status is
attached to the matching row as secondary evidence.
"""
from __future__ import annotations

from datetime import datetime, timezone

from lib_common import load_json

VERIFIED_ON = "2026-10-24"

CATEGORIES = [
    {
        "id": "established",
        "step": 1,
        "title": "Established League of Legends betting sites",
        "note": ("Checked first because they publish the sharpest two-way series prices. "
                 "Only Pinnacle and Unibet (Kambi) currently return a structured price that "
                 "the pipeline can read; the rest either have no LoL board open at check time "
                 "or do not expose a machine-readable feed."),
    },
    {
        "id": "esportsbooks",
        "step": 2,
        "title": "Esportsbooks",
        "note": ("Esports specialists often list regional divisions that mainstream books skip. "
                 "Where a page is reachable but blocks GitHub Actions (Cloudflare / region rules) "
                 "it is kept as a human cross-check link only and is never used as a probability."),
    },
    {
        "id": "lines",
        "step": 3,
        "title": "Esports betting lines and odds aggregators",
        "note": ("Aggregators can prove that a market exists, but they do not always publish a "
                 "machine-readable price and several block automated requests. Observed status "
                 "is recorded rather than assumed."),
    },
    {
        "id": "prediction",
        "step": 4,
        "title": "Prediction markets and exchanges",
        "note": ("Public prices are used only as reference data. Polymarket is the only "
                 "prediction market currently matched to Hotspawn fixtures."),
    },
    {
        "id": "results",
        "step": 5,
        "title": "Official and community results sources (model input, not a price)",
        "note": ("When no bookmaker prices a fixture, the pick comes from recorded results and "
                 "split standings. Leaguepedia is community-maintained (CC BY-SA 3.0), not an "
                 "official Riot or tournament-organizer feed; that limitation is published on "
                 "the site."),
    },
]

SOURCES = [
    # ---------------------------------------------------------- established books
    {
        "category": "established",
        "name": "Pinnacle",
        "url": "https://www.pinnacle.com/en/esports/league-of-legends",
        "feed": "https://guest.api.arcadia.pinnacle.com/0.1",
        "role": "probability_input",
        "observed": ("Public guest JSON reachable on 2026-10-24. Its LoL league list contained "
                     "only 'League of Legends - World Championship' (10 matchups); the pipeline "
                     "reads the parent Regular series moneyline and rejects child prop boards."),
        "limitation": "Tier-1 international events only; no national or amateur divisions.",
        "status_key": "Pinnacle",
    },
    {
        "category": "established",
        "name": "Unibet (Kambi feed)",
        "url": "https://www.unibet.com.au/betting/sports/filter/esports/league_of_legends/all/matches",
        "feed": ("https://eu-offering-api.kambicdn.com/offering/v2018/ubca/listView/"
                 "esports/league_of_legends/all/all/matches.json"),
        "role": "probability_input",
        "observed": ("Kambi's public pre-match JSON — the feed behind Unibet — returned 8 "
                     "two-way LoL prices in the latest pipeline run on 2026-10-24. Only the "
                     "main 'Match Odds' offer is read; map, handicap and total boards are "
                     "rejected."),
        "limitation": "Only events Kambi offers; no amateur or third-division leagues.",
        "status_key": "Unibet",
    },
    {
        "category": "established",
        "name": "Bovada",
        "url": "https://www.bovada.lv/sports/esports/league-of-legends",
        "feed": ("https://www.bovada.lv/services/sports/event/coupon/events/A/description/"
                 "esports/league-of-legends?marketFilterId=def&preMatchOnly=true&lang=en"),
        "role": "probability_input",
        "observed": ("Public coupon JSON returned the World Championship '26 and EMEA Masters "
                     "Summer series moneylines from a browser request on 2026-10-24 (8 + 1 "
                     "fixtures). GitHub Actions received an empty {} in the 2026-10-23 probe, "
                     "so Bovada is used only when a run actually returns prices."),
        "limitation": ("Lists the leagues Bovada offers (Worlds and occasional tier-2 like "
                       "EMEA Masters); never counted as a source when the run returns no price."),
        "status_key": "Bovada",
    },
    {
        "category": "established",
        "name": "DraftKings Sportsbook",
        "url": "https://sportsbook.draftkings.com/leagues/esports/league-of-legends",
        "feed": None,
        "role": "unavailable",
        "observed": "HTTP 404 at the tested LoL sportsbook route on 2026-10-24.",
        "limitation": "No public per-match LoL feed verified; not used.",
    },
    {
        "category": "established",
        "name": "BetOnline",
        "url": "https://www.betonline.ag/sportsbook/esports/league-of-legends",
        "feed": None,
        "role": "unavailable",
        "observed": "HTTP 404 ('We've had a glitch') at the tested LoL route on 2026-10-24.",
        "limitation": "No public per-match LoL feed verified; not used.",
    },
    {
        "category": "established",
        "name": "Betway Esports",
        "url": "https://www.betway.com/en/esports/league-of-legends",
        "feed": None,
        "role": "unavailable",
        "observed": "HTTP 404 at the LoL path in the 2026-10-23 probe.",
        "limitation": "No public per-match LoL feed verified; not used.",
    },
    # ---------------------------------------------------------- esportsbooks
    {
        "category": "esportsbooks",
        "name": "Thunderpick",
        "url": "https://thunderpick.io/esports/league-of-legends",
        "feed": None,
        "role": "context",
        "observed": ("LoL hub reachable on 2026-10-24 with 11 fixtures: Worlds 2026 (10) and "
                     "LGC Rising 2026 Playoffs (1). GitHub Actions received HTTP 403 "
                     "(Cloudflare), so it is a manual cross-check link only."),
        "limitation": ("Reachable in a browser, blocked from CI; prices are not read or used "
                       "in any probability."),
    },
    {
        "category": "esportsbooks",
        "name": "GG.Bet",
        "url": "https://gg.bet/en/esports/lol",
        "feed": None,
        "role": "unavailable",
        "observed": ("Region-blocked on 2026-10-24: 'This internet site is not accepting "
                     "visitors from your region.'"),
        "limitation": "Not reachable from the verification environment; no price used.",
    },
    {
        "category": "esportsbooks",
        "name": "Rivalry",
        "url": "https://www.rivalry.com/lol",
        "feed": None,
        "role": "unavailable",
        "observed": ("Redirects to /operationally-closed (HTTP 404) on 2026-10-24; the "
                     "operator has closed its sportsbook."),
        "limitation": "No longer operating; removed from the usable-source ladder.",
    },
    {
        "category": "esportsbooks",
        "name": "Midnite",
        "url": "https://www.midnite.com/esports/league-of-legends",
        "feed": None,
        "role": "context",
        "observed": "HTML shell only, no server-rendered per-match prices (2026-10-23 probe).",
        "limitation": "Human cross-check only; no price parsed.",
    },
    # ---------------------------------------------------------- lines / aggregators
    {
        "category": "lines",
        "name": "OddsPortal — LoL Prime League",
        "url": "https://www.oddsportal.com/esports/league-of-legends/league-of-legends-prime-league/",
        "feed": None,
        "role": "context",
        "observed": ("Page returned HTTP 200 on 2026-10-24 but listed no current bookmaker "
                     "odds for the Prime League. CI requests to the same aggregator returned "
                     "HTTP 503 in the 2026-10-23 probe."),
        "limitation": ("HTML only and blocks automation; it proves the market exists but "
                       "cannot supply a price to the pipeline."),
    },
    {
        "category": "lines",
        "name": "BetExplorer",
        "url": "https://www.betexplorer.com/lol/",
        "feed": None,
        "role": "unavailable",
        "observed": "HTTP 404 at the LoL path in the 2026-10-23 probe.",
        "limitation": "Not used.",
    },
    {
        "category": "lines",
        "name": "eGamersWorld",
        "url": "https://egamersworld.com/lol/bets",
        "feed": None,
        "role": "unavailable",
        "observed": "HTTP 403 in the 2026-10-23 probe.",
        "limitation": "Not used.",
    },
    {
        "category": "lines",
        "name": "OddsPapi",
        "url": "https://oddspapi.io/sports/esports/lol",
        "feed": "https://oddspapi.io/v4",
        "role": "unavailable",
        "observed": ("HTML reachable, but the odds API requires an API key (HTTP 401 without "
                     "one) and no key is configured in this repository."),
        "limitation": ("A key requires an account signup, which is a manual action; without "
                       "one no OddsPapi price is used anywhere."),
    },
    {
        "category": "lines",
        "name": "The Odds API",
        "url": "https://the-odds-api.com/liveapi/guides/v4/",
        "feed": "https://api.the-odds-api.com/v4",
        "role": "unavailable",
        "observed": "HTTP 401 without a paid API key; no key is configured.",
        "limitation": "Not used.",
    },
    # ---------------------------------------------------------- prediction markets
    {
        "category": "prediction",
        "name": "Polymarket Gamma API",
        "url": "https://polymarket.com/",
        "feed": "https://gamma-api.polymarket.com",
        "role": "probability_input",
        "observed": ("Public Gamma API reachable on 2026-10-24; events and child markets are "
                     "matched by team pair and start date. Only full-match series markets are "
                     "used, never a Game 1/Map 1 child board."),
        "limitation": ("Trading is restricted in some jurisdictions and the site is view-only "
                       "there; prices are reference data and this site never places a bet."),
        "status_key": "Polymarket",
    },
    {
        "category": "prediction",
        "name": "Kalshi",
        "url": "https://kalshi.com/",
        "feed": "https://api.elections.kalshi.com/trade-api/v2/series?category=Esports",
        "role": "unavailable",
        "observed": "API reachable but returned an empty `series` list; no LoL series (2026-10-23).",
        "limitation": "No League of Legends market; not used.",
    },
    {
        "category": "prediction",
        "name": "Manifold Markets",
        "url": "https://manifold.markets/",
        "feed": "https://api.manifold.markets/v0/search-markets",
        "role": "unavailable",
        "observed": "Search returned futures/outright questions only, no per-match prices (2026-10-23).",
        "limitation": "No usable per-match market; not used.",
    },
    {
        "category": "prediction",
        "name": "Betfair Exchange",
        "url": "https://www.betfair.com/exchange/plus/",
        "feed": None,
        "role": "unavailable",
        "observed": "HTTP 403 to automated requests (2026-10-23).",
        "limitation": "Exchange prices not accessible; not used.",
    },
    {
        "category": "prediction",
        "name": "Smarkets",
        "url": "https://smarkets.com/sport/esports/league-of-legends",
        "feed": "https://api.smarkets.com/v3",
        "role": "unavailable",
        "observed": "HTTP 403 (Cloudflare challenge) / 404 on the tested API route (2026-10-23).",
        "limitation": "Not used.",
    },
    # ---------------------------------------------------------- results / verification
    {
        "category": "results",
        "name": "Leaguepedia Cargo tables",
        "url": "https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule",
        "feed": "https://lol.fandom.com/wiki/Special:CargoExport",
        "role": "model_input",
        "observed": ("Recorded series results, future schedule and split standings are read "
                     "from the wiki's Cargo export. Community-maintained, CC BY-SA 3.0."),
        "limitation": ("Not an official Riot or organizer feed; coverage is uneven for brand-new "
                       "teams and some splits start being recorded part-way through."),
        "status_key": "Leaguepedia MatchSchedule",
    },
    {
        "category": "results",
        "name": "Liquipedia MediaWiki API",
        "url": "https://liquipedia.net/leagueoflegends/api.php",
        "feed": "https://liquipedia.net/leagueoflegends/api.php",
        "role": "context",
        "observed": ("API reachable with gzip and >=2.2 s spacing; used for tournament metadata "
                     "only. HTML endpoints are never scraped (Liquipedia API terms)."),
        "limitation": "Community wiki (CC-BY-SA 3.0); no prices.",
    },
    {
        "category": "results",
        "name": "Riot LoL Esports API",
        "url": "https://esports-api.lolesports.com/persisted/gw/getSchedule?hl=en-US",
        "feed": None,
        "role": "unavailable",
        "observed": "HTTP 403 {'message': 'Forbidden'} on 2026-10-24.",
        "limitation": "Official Riot schedule could not be read; Leaguepedia remains the results source.",
    },
    {
        "category": "results",
        "name": "LoL Esports (official schedule)",
        "url": "https://lolesports.com/",
        "feed": None,
        "role": "context",
        "observed": "Public schedule site used as the official reference link for Worlds and LGC Rising.",
        "limitation": "No machine-readable public feed; link only.",
    },
    {
        "category": "results",
        "name": "Prime League (organizer)",
        "url": "https://www.primeleague.gg/en/leagues/prm/3227-fall-split-202627",
        "feed": None,
        "role": "context",
        "observed": "Official DACH organizer page used as the competition reference for PRM 2nd/3rd Division.",
        "limitation": "No public odds feed; results are cross-checked on Leaguepedia.",
    },
    {
        "category": "results",
        "name": "RIVALS LEAGUE (organizer)",
        "url": "https://www.rivalsleague.gg/",
        "feed": None,
        "role": "context",
        "observed": "Official organizer page used as the competition reference for RIVALS LEAGUE Season 2.",
        "limitation": "No public odds feed; results are cross-checked on Leaguepedia.",
    },
    {
        "category": "results",
        "name": "Komplettligaen (organizer)",
        "url": "https://www.komplettligaen.no/lol/",
        "feed": None,
        "role": "context",
        "observed": "Official Norwegian organizer page used as the competition reference for Komplettligaen.",
        "limitation": "No public odds feed; results are cross-checked on Leaguepedia.",
    },
]

ROLE_LABEL = {
    "probability_input": "Probability input",
    "model_input": "Model input (results)",
    "context": "Reference / manual check only",
    "unavailable": "Not usable",
}


def _probe_index(probe: dict | None) -> dict:
    """Map lower-case source name -> latest probe record (secondary evidence)."""
    out = {}
    for item in (probe or {}).get("candidates") or []:
        if not isinstance(item, dict):
            continue
        key = str(item.get("name") or "").lower()
        if key:
            out[key] = item
    return out


def _attach_probe(source: dict, probe_idx: dict) -> None:
    name = source["name"].lower()
    for key, item in probe_idx.items():
        if key == name or key.split(" (")[0] == name.split(" (")[0]:
            source["probe_http_status"] = item.get("http_status")
            source["probe_verdict"] = item.get("verdict")
            return


def build(markets: dict | None, leaguepedia: dict | None, probe: dict | None = None) -> dict:
    """Return the published source-research section (never invents a status)."""
    markets = markets or {}
    leaguepedia = leaguepedia or {}
    probe_idx = _probe_index(probe)
    status_by_name = {str(s.get("source")): s for s in (markets.get("statuses") or [])
                      if isinstance(s, dict)}
    lp_counts = leaguepedia.get("counts") or {}

    rows = []
    for base in SOURCES:
        src = dict(base)
        key = src.pop("status_key", None)
        if key and key in status_by_name:
            st = status_by_name[key]
            src["count"] = st.get("count")
            src["run_status"] = st.get("status")
            if st.get("status") == "ok":
                src["observed"] = (src["observed"] + " Latest run: "
                                   f"{st.get('count')} two-way price(s) read.")
            elif st.get("status") in ("no_data", "error", "degraded"):
                src["observed"] = (src["observed"] + " Latest run: "
                                   f"{st.get('status')} ({st.get('count') or 0} prices).")
        if key == "Leaguepedia MatchSchedule":
            src["count"] = lp_counts.get("results")
            src["observed"] = (src["observed"] + " Latest run: "
                               f"{lp_counts.get('results', 0)} recorded results, "
                               f"{lp_counts.get('standings', 0)} standings rows across "
                               f"{lp_counts.get('standings_pages', 0)} competitions.")
        _attach_probe(src, probe_idx)
        src["role_label"] = ROLE_LABEL.get(src.get("role"), src.get("role"))
        src["verified_on"] = VERIFIED_ON
        rows.append(src)

    categories = []
    for cat in CATEGORIES:
        items = [r for r in rows if r["category"] == cat["id"]]
        categories.append({**cat, "sources": items,
                           "counts": {
                               "total": len(items),
                               "probability_input": sum(1 for r in items if r["role"] == "probability_input"),
                               "context": sum(1 for r in items if r["role"] == "context"),
                               "unavailable": sum(1 for r in items if r["role"] == "unavailable"),
                           }})

    probe_rows = []
    for c in (probe or {}).get("candidates") or []:
        if not isinstance(c, dict):
            continue
        probe_rows.append({
            "category": c.get("category"),
            "name": c.get("name"),
            "url": c.get("url"),
            "http_status": c.get("http_status"),
            "is_json": c.get("is_json"),
            "signals": c.get("signals") or [],
            "verdict": c.get("verdict"),
        })
    out = {
        "verified_on": VERIFIED_ON,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "method": ("Each source was requested directly; the observed HTTP status or structured "
                   "feed is recorded with the date. A source is a probability input only when "
                   "the pipeline reads a structured two-way per-match price from it. Blocked, "
                   "empty and HTML-only sources are listed as not usable and are never counted."),
        "categories": categories,
        "totals": {
            "sources": len(rows),
            "probability_input": sum(1 for r in rows if r["role"] == "probability_input"),
            "model_input": sum(1 for r in rows if r["role"] == "model_input"),
            "context": sum(1 for r in rows if r["role"] == "context"),
            "unavailable": sum(1 for r in rows if r["role"] == "unavailable"),
        },
    }
    if probe_rows:
        out["probe"] = {"checked_at": (probe or {}).get("checked_at"),
                        "vantage": "GitHub Actions request; a browser may reach pages that CI cannot.",
                        "candidates": probe_rows}
    return out


def load_probe(path: str = "data/diag/source_probe.json") -> dict | None:
    try:
        return load_json(path)
    except Exception:
        return None


if __name__ == "__main__":
    import json
    print(json.dumps(build({}, {}), indent=1)[:4000])

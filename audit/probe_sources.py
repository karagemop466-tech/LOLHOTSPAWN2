#!/usr/bin/env python3
"""Read-only probe of external LoL betting / odds sources.

Purpose (T17): the brief asks us to try *established* LoL betting sites first,
then esportsbooks and esports betting lines, for the matches that cannot be
priced the same way as the featured (book-priced) picks.

This script only *observes* each endpoint: HTTP status, payload size, whether
the response contains League of Legends match data, and whether it mentions any
team that is actually on the current Hotspawn fixture list. It never writes to
`docs/data/` and never changes a probability. Results land in
`audit/source_probe.json` + `audit/source_probe.md` for manual review.

A source is only marked `usable` when:
  * HTTP 200,
  * the body is machine-readable (JSON) or a server-rendered page that names a
    current Hotspawn team, and
  * the body contains a LoL market/price token.
Everything else is recorded with the observed status and no claim is made.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from lib_common import fetch, load_json, log, norm, now_utc, utc_iso, write_json  # noqa: E402

OUT_JSON = "audit/source_probe.json"
OUT_MD = "audit/source_probe.md"

# (group, name, url, page_url_for_humans)
CANDIDATES = [
    # --- established bookmakers with public front-end feeds -----------------
    ("established book", "Pinnacle (control)", "https://guest.api.arcadia.pinnacle.com/0.1/sports",
     "https://www.pinnacle.com/en/esports/league-of-legends"),
    ("established book", "Bovada (control)",
     "https://www.bovada.lv/services/sports/event/coupon/events/A/description/esports/league-of-legends?marketFilterId=def&lang=en",
     "https://www.bovada.lv/sports/esports/league-of-legends"),
    ("established book", "Betano LoL", "https://www.betano.com/sport/esports/league-of-legends/",
     "https://www.betano.com/sport/esports/league-of-legends/"),
    ("established book", "Betsson LoL", "https://www.betsson.com/en/sportsbook/esports/league-of-legends",
     "https://www.betsson.com/en/sportsbook/esports/league-of-legends"),
    ("established book", "Marathonbet esports",
     "https://www.marathonbet.com/en/betting/e-Sports/League+of+Legends",
     "https://www.marathonbet.com/en/betting/e-Sports"),
    ("established book", "Unibet LoL",
     "https://www.unibet.com/betting/sports/filter/esports/league_of_legends",
     "https://www.unibet.com/betting/sports/filter/esports/league_of_legends"),
    ("established book", "DraftKings LoL",
     "https://sportsbook.draftkings.com/leagues/esports/league-of-legends",
     "https://sportsbook.draftkings.com/leagues/esports/league-of-legends"),
    ("established book", "FanDuel esports", "https://sportsbook.fanduel.com/navigation/esports",
     "https://sportsbook.fanduel.com/navigation/esports"),
    ("established book", "BetMGM esports", "https://www.betmgm.com/en/sports/esports-10",
     "https://www.betmgm.com/en/sports"),
    ("established book", "Betway esports", "https://www.betway.com/en/esports/league-of-legends",
     "https://www.betway.com/en/esports/league-of-legends"),
    ("established book", "1xBet line feed",
     "https://1xbet.com/LineFeed/GetSportsShortZip?sports=all&lng=en&country=1&partner=51",
     "https://1xbet.com/en/line/esports/"),
    ("established book", "1xBet LoL 1x2",
     "https://1xbet.com/LineFeed/Get1x2_VZip?sports=92&count=50&lng=en&mode=4&country=1&partner=51",
     "https://1xbet.com/en/line/esports/"),
    ("established book", "BetOnline esports", "https://www.betonline.ag/sportsbook/esports",
     "https://www.betonline.ag/sportsbook/esports"),
    ("established book", "BetUS esports", "https://www.betus.com.pa/sportsbook/esports/",
     "https://www.betus.com.pa/sportsbook/esports/"),

    # --- esportsbooks -------------------------------------------------------
    ("esportsbook", "Rivalry LoL", "https://www.rivalry.com/lol", "https://www.rivalry.com/lol"),
    ("esportsbook", "Thunderpick LoL", "https://thunderpick.io/esports/league-of-legends",
     "https://thunderpick.io/esports/league-of-legends"),
    ("esportsbook", "GG.Bet LoL", "https://gg.bet/en/esports/lol", "https://gg.bet/en/esports/lol"),
    ("esportsbook", "Midnite LoL", "https://www.midnite.com/esports/league-of-legends",
     "https://www.midnite.com/esports/league-of-legends"),
    ("esportsbook", "LOOT.BET LoL", "https://loot.bet/esports/league-of-legends",
     "https://loot.bet/esports/league-of-legends"),
    ("esportsbook", "EsportsBet.io LoL", "https://esportsbet.io/sport/league-of-legends",
     "https://esportsbet.io/"),
    ("esportsbook", "Betify esports", "https://www.betify.com/en/esports/league-of-legends",
     "https://www.betify.com/en/esports"),

    # --- odds aggregators / lines ------------------------------------------
    ("odds aggregator", "Oddspedia LoL", "https://oddspedia.com/esports/league-of-legends",
     "https://oddspedia.com/esports/league-of-legends"),
    ("odds aggregator", "Oddspedia API (leagues)",
     "https://oddspedia.com/api/v1/getSportLeagues?sport=league-of-legends&limit=5",
     "https://oddspedia.com/esports/league-of-legends"),
    ("odds aggregator", "BetExplorer LoL", "https://www.betexplorer.com/lol/",
     "https://www.betexplorer.com/lol/"),
    ("odds aggregator", "BetExplorer esports", "https://www.betexplorer.com/esports/",
     "https://www.betexplorer.com/esports/"),
    ("odds aggregator", "OddsPortal LoL", "https://www.oddsportal.com/lol/",
     "https://www.oddsportal.com/lol/"),
    ("odds aggregator", "OddsPortal esports", "https://www.oddsportal.com/esports/league-of-legends/",
     "https://www.oddsportal.com/esports/league-of-legends/"),
    ("odds aggregator", "Oddspedia LoL (short path)", "https://oddspedia.com/lol",
     "https://oddspedia.com/lol"),
    ("odds aggregator", "The Odds API sports", "https://api.the-odds-api.com/v4/sports/?apiKey=",
     "https://the-odds-api.com/liveapi/guides/v4/"),

    # --- prediction markets -------------------------------------------------
    ("prediction market", "Polymarket (control)",
     "https://gamma-api.polymarket.com/events?tag_slug=league-of-legends&active=true&closed=false&limit=20",
     "https://polymarket.com/markets/esports"),
    ("prediction market", "Kalshi esports series",
     "https://api.elections.kalshi.com/trade-api/v2/series?category=Esports",
     "https://kalshi.com/markets"),
    ("prediction market", "Manifold LoL",
     "https://api.manifold.markets/v0/search-markets?term=league%20of%20legends&limit=10",
     "https://manifold.markets/"),

    # --- esports data providers (odds columns) ------------------------------
    ("data provider", "PandaScore (no key)", "https://api.pandascore.co/lol/matches/upcoming",
     "https://developers.pandascore.co/docs"),
    ("data provider", "Abios (no key)", "https://api.abiosgaming.com/v2/series",
     "https://abiosgaming.com/"),
    ("data provider", "SofaScore esports schedule",
     "https://api.sofascore.com/api/v1/sport/esports/scheduled-events/2026-10-23",
     "https://www.sofascore.com/esports"),
    ("data provider", "SofaScore LoL rankings",
     "https://api.sofascore.com/api/v1/unique-tournament/325/rankings",
     "https://www.sofascore.com/tournament/league-of-legends/world-championship/325"),
]


def _tournament_tokens():
    """Distinctive words from the low-tier tournaments we cannot price today.

    Their presence on a betting page is the only useful test of whether that
    book actually covers our uncovered fixtures (a majors-only page is not)."""
    d = load_json("docs/data/picks.json", {}) or {}
    toks = set()
    for t in d.get("tournaments") or []:
        name = str(t.get("name") or "")
        for word in ("prime league", "tunisian super league", "rivals league",
                     "arabian league", "komplettligaen", "ligagg", "icelandic esports",
                     "benelux ascend", "4 nations", "superstrike", "hitpoint"):
            if word in name.lower():
                toks.add(word)
    return toks


def _team_tokens():
    d = load_json("docs/data/picks.json", {}) or {}
    names = set()
    for m in d.get("matches") or []:
        for key in ("team1", "team2"):
            n = norm(m.get(key))
            if len(n) >= 4:
                names.add(n)
    return names


def classify(status: int, text: str, ctype: str, teams: set[str]) -> dict:
    low = (text or "").lower()
    hits = sorted(t for t in teams if t in norm(low))
    lol_tokens = [tok for tok in ("league of legends", "worlds", "lol:", "lck", "lpl", "lec ")
                  if tok in low]
    priced = bool(re.search(r"(moneyline|\"price\"|\"odds\"|decimal|american|market)", low))
    return {
        "http_ok": status == 200,
        "bytes": len(text or ""),
        "content_type": ctype,
        "mentions_league_of_legends": bool(lol_tokens),
        "matched_current_teams": hits[:8],
        "matched_team_count": len(hits),
        "has_price_tokens": priced,
        "json": (text or "").lstrip()[:1] in ("{", "["),
        "low_tier_tokens": sorted(t for t in _TOUR_TOKENS if t in low),
    }


def probe(url: str, teams: set[str]) -> dict:
    started = time.time()
    r = fetch(url, timeout=30, retries=1)
    body = r.get("text") or ""
    ctype = ""
    # fetch() does not surface headers; infer from the body, and keep a snippet.
    info = classify(r.get("status", 0), body, ctype, teams)
    info.update({
        "url": url,
        "status": r.get("status", 0),
        "error": r.get("error"),
        "elapsed_s": round(time.time() - started, 2),
        "snippet": re.sub(r"\s+", " ", body[:300]),
    })
    return info


_TOUR_TOKENS: set[str] = set()


def main() -> int:
    global _TOUR_TOKENS
    _TOUR_TOKENS = _tournament_tokens()
    teams = _team_tokens()
    log(f"audit: probing {len(CANDIDATES)} candidate sources against {len(teams)} current team names")
    rows = []
    for group, name, url, human in CANDIDATES:
        res = probe(url, teams)
        # Tightened: a page that merely mentions one team is not a usable feed.
        # Require a price token and either machine-readable JSON or at least two
        # current teams.
        usable = bool(res["http_ok"] and res["has_price_tokens"] and
                      (res["json"] or res["matched_team_count"] >= 2) and
                      (res["mentions_league_of_legends"] or res["matched_team_count"]))
        res.update({"group": group, "name": name, "human_url": human, "usable": usable})
        rows.append(res)
        log(f"audit: {name:32s} {res['status']:>4} {res['bytes']:>8}B "
            f"lol={int(res['mentions_league_of_legends'])} teams={res['matched_team_count']:>3} "
            f"usable={int(usable)}")
        time.sleep(0.8)

    payload = {
        "generated_at": utc_iso(now_utc()),
        "method": ("GET with the project User-Agent; a source is usable only if it returns 200, "
                   "is machine-readable or names at least two current Hotspawn teams, and carries a "
                   "LoL/price token. A page that only mentions one team once is not counted."),
        "teams_checked": len(teams),
        "counts": {
            "candidates": len(rows),
            "http_200": sum(1 for r in rows if r["status"] == 200),
            "usable": sum(1 for r in rows if r["usable"]),
            "names_a_current_team": sum(1 for r in rows if r["matched_team_count"]),
        },
        "sources": rows,
    }
    write_json(OUT_JSON, payload)

    lines = ["# External source probe (read-only)", "",
             f"Generated: {payload['generated_at']} · {len(rows)} endpoints probed against "
             f"{len(teams)} team names on the current Hotspawn fixture list.", "",
             "A source is marked **usable** only when it returns HTTP 200, is machine-readable or names a "
             "current Hotspawn team, and carries a League-of-Legends/price token. No probability is taken "
             "from any row here; this is an evidence log for manual review.", "",
             "| Group | Source | HTTP | Bytes | LoL token | Current teams named | Low-tier leagues named | Price tokens | Usable | Link |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| {group} | {name} | {status} | {bytes} | {lol} | {n} | {lt} | {p} | {u} | {link} |".format(
            group=r["group"], name=r["name"], status=r["status"], bytes=r["bytes"],
            lol="yes" if r["mentions_league_of_legends"] else "no",
            n=r["matched_team_count"],
            lt=", ".join(r["low_tier_tokens"]) if r["low_tier_tokens"] else "no",
            p="yes" if r["has_price_tokens"] else "no",
            u="**yes**" if r["usable"] else "no", link=r["human_url"]))
    lines += ["", "## Observed responses", ""]
    for r in rows:
        lines.append(f"### {r['name']}")
        lines.append(f"- Endpoint: {r['url']}")
        lines.append(f"- Observed: HTTP {r['status']} · {r['bytes']} bytes · {r['elapsed_s']} s")
        if r["matched_current_teams"]:
            lines.append(f"- Current Hotspawn teams found in the body: {', '.join(r['matched_current_teams'])}")
        if r["snippet"]:
            lines.append(f"- Body starts: `{r['snippet'][:220]}`")
        lines.append("")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log(f"audit: wrote {OUT_JSON} and {OUT_MD} ({payload['counts']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Low-tier line sweep: ask *new* sources whether they price the fixtures we
cannot price from a bookmaker line.

Why this file exists
--------------------
`scripts/source_probe.py` re-checks the standing candidate list on every refresh
and `scripts/probe_lines.py` fixture-matches the long-standing books. Both lists
were built up over earlier sessions. This sweep exists so a *fresh* batch of
candidates - comparison sites, aggregator APIs, sister brands of a platform we
already read, and low-tier results sites - can be measured the same way without
touching those two files.

What it measures per candidate, with exactly ONE polite GET each:
  * the HTTP status and body size actually returned,
  * whether the body is JSON,
  * whether the body mentions any of the team names or league names that appear
    in the fixtures we currently price with our own model (normalised substring
    match, so "Babos Gaming" is found as `babosgaming`),
  * whether any machine-readable two-way price could be extracted, and if so
    whether it matches a published fixture by team name AND start time
    (the matcher is `probe_lines.FixtureIndex`, reused rather than reimplemented).

Hard rules (same as every other probe in this repo)
--------------------------------------------------
* It never returns a probability and never feeds the model or the payload.
* A source is promoted into `scripts/fetch_markets.py` only when this sweep shows
  structured prices that match published fixtures AND a human has re-read a
  sample row against the live page (recorded in research/).
* No API keys are configured and none are invented; a key-gated endpoint is
  reported as key-gated.
* Failures are recorded, never raised: exit code is always 0.

Outputs: data/diag/lowtier_sweep.json (machine-readable) and
research/low-tier-sweep-latest.md (the same evidence as a table a person can
read on a phone).
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib_common import (decimal_from_american, fetch, log, norm, now_utc,  # noqa: E402
                        utc_iso, write_json)
from probe_lines import FixtureIndex  # noqa: E402

OUT_JSON = "data/diag/lowtier_sweep.json"
OUT_MD = "research/low-tier-sweep-latest.md"
PICKS = "docs/data/picks.json"

# (name, url, shape, category, note)
#   shape: html            - parse nothing, only scan for names/leagues
#          kambi           - Kambi listView JSON (events[].betOffers[])
#          bovada-family   - Bodog/BetOnline-group coupon JSON
#          linefeed        - 1xBet-family LineFeed JSON
#          sofascore       - Sofascore scheduled-events JSON
#   category: market | results
# Every URL below was requested at least once on 2026-10-25 while building this
# list; the published verdict is always the status measured by THIS run, never
# the status seen while writing the file.
CANDIDATES: tuple[tuple[str, str, str, str, str], ...] = (
    # --- odds comparison sites that are server-rendered (readable without JS) ---
    ("Oddsdigger - LoL board (server-rendered comparison)",
     "https://oddsdigger.com/e-sports/league-of-legends", "html", "market",
     "Comparison page; lists 1/2 prices per match when a book prices it."),
    ("Oddsdigger - LoL upcoming list",
     "https://oddsdigger.com/e-sports/league-of-legends/upcoming", "html", "market",
     "Same site, upcoming-only list."),
    ("Oddsdigger - Prime League 2nd Division path",
     "https://oddsdigger.com/e-sports/league-of-legends/prime-league-2nd-division",
     "html", "market",
     "Requested directly to test whether the lower division has its own board."),
    ("EsportBet - live esports odds board",
     "https://esportbet.com/odds/", "html", "market",
     "Affiliate-run odds board; measured because its LoL guide claims low-tier coverage."),
    ("esportsinsider - LoL odds index",
     "https://esportsinsider.com/betting-odds/lol", "html", "market",
     "Editorial odds index (licensed books), per-league sub-pages."),
    ("Oddschecker - esports section",
     "https://www.oddschecker.com/esports/", "html", "market",
     "UK comparison site; requested to test whether it has an esports board at all."),
    ("Betmonitor - esports comparison hub",
     "https://www.betmonitor.com/odds-comparison/esports/", "html", "market",
     "Client-rendered comparison widget; hub requested for the league index."),
    ("bmbets - LoL Prime League 2nd Division page",
     "https://www.bmbets.com/e-sports/world/lol---prime-league-2nd-division/",
     "html", "market", "BetConstruct-powered comparison page for the division."),
    ("bmbets - LoL Prime League 3rd Division page",
     "https://www.bmbets.com/e-sports/world/lol---prime-league-3rd-division/",
     "html", "market", "Same template, third division."),

    # --- sister platforms of a coupon API production already reads -------------
    ("BetOnline - Bodog-group coupon API (esports)",
     "https://www.betonline.ag/services/sports/event/coupon/events/A/description/esports"
     "?marketFilterId=def&preMatchOnly=true&lang=en", "bovada-family", "market",
     "Bovada's coupon shape on its sister brand, which advertises wider LoL coverage."),
    ("SportsBetting.ag - Bodog-group coupon API (esports)",
     "https://www.sportsbetting.ag/services/sports/event/coupon/events/A/description/esports"
     "?marketFilterId=def&preMatchOnly=true&lang=en", "bovada-family", "market",
     "Second sister brand on the same platform."),

    # --- aggregator / data APIs ------------------------------------------------
    ("Sofascore - esports scheduled-events API (today)",
     "https://api.sofascore.com/api/v1/sport/esports/scheduled-events/"
     + now_utc().strftime("%Y-%m-%d"), "sofascore", "market",
     "Events plus book odds; the site's own HTML is client-rendered."),
    ("1xBet LineFeed - esports two-way prices",
     "https://1xbet.com/LineFeed/Get1x2_VZip?sports=58&count=50&lng=en&mode=4"
     "&country=1&partner=51&getEmpty=true", "linefeed", "market",
     "Widest published LoL board of any book; geo-restricted from US runner IPs."),
    ("Kambi offering API - operator slug 'bs' (control)",
     "https://eu-offering-api.kambicdn.com/offering/v2018/bs/listView/esports/"
     "league_of_legends/all/all/matches.json?lang=en_GB&market=SE&useCombined=true",
     "kambi", "market",
     "Control: is a non-Unibet Kambi brand a route to lower-tier leagues?"),
    ("Kambi offering API - operator slug 'nb' (control)",
     "https://eu-offering-api.kambicdn.com/offering/v2018/nb/listView/esports/"
     "league_of_legends/all/all/matches.json?lang=en_GB&market=NO&useCombined=true",
     "kambi", "market", "Second non-Unibet brand control."),
    ("Everygame - sportsbook esports section",
     "https://www.everygame.eu/sportsbook/esports/", "html", "market",
     "US-facing book named in 2026 esports-betting guides for LoL depth."),

    # --- low-tier results / stats sites (never a probability input) -------------
    ("rft.gg - upcoming LoL matches",
     "https://rft.gg/matches", "html", "results",
     "Independent LoL results/stats site; usable as a second read on a fixture list."),
    ("rft.gg - Prime League 2nd Division event path",
     "https://rft.gg/event/prime-league-2nd-division-26-27-fall", "html", "results",
     "Requested to test whether the lower division has an event page at all."),
    ("gol.gg - Prime League section",
     "https://gol.gg/league/list/", "html", "results",
     "Second community results index (Leaguepedia remains the production source)."),
)

# League names of the fixtures we cannot price from a book, normalised.
LEAGUE_KEYS = ("primeleague2nddivision", "primeleague3rddivision", "prm2nddivision",
               "prm3rddivision", "tunisiansuperleague", "rivalsleague", "komplettligaen",
               "4nations", "arabianleague", "ligagg", "celol", "lcp2027promotion",
               "lgcrising", "primeleague")


def _league_hits(body_norm: str) -> list[str]:
    return [k for k in LEAGUE_KEYS if k in body_norm]


def _team_hits(body_norm: str, teams: list[str]) -> list[str]:
    return [t for t in teams if norm(t) in body_norm]


# --------------------------------------------------------------------------- #
# shape-specific price extraction (two-way main match markets only)
# --------------------------------------------------------------------------- #
def _prices_kambi(data):
    out = []
    for ev in (data or {}).get("events") or []:
        e = ev.get("event") or {}
        for off in ev.get("betOffers") or []:
            crit = (off.get("criterion") or {}).get("label") or ""
            if crit.lower() not in ("match odds", "match", "head to head"):
                continue
            outs = off.get("outcomes") or []
            if len(outs) != 2:
                continue
            a, b = outs
            if not all(o.get("odds") for o in (a, b)):
                continue
            out.append({"team_a": a.get("participant") or a.get("label"),
                        "team_b": b.get("participant") or b.get("label"),
                        "decimal_a": o2d(a["odds"]), "decimal_b": o2d(b["odds"]),
                        "start": e.get("start"), "competition": e.get("group") or "",
                        "url": f"kambi-event:{e.get('id')}"})
    return out


def o2d(odds):
    """Kambi publishes odds x1000."""
    try:
        return round(float(odds) / 1000.0, 4)
    except (TypeError, ValueError):
        return None


def _prices_bovada_family(data):
    out = []

    def walk(node):
        if isinstance(node, dict):
            if "competitors" in node and "markets" in node:
                comp = node.get("competitors") or []
                names = [c.get("name") for c in comp if isinstance(c, dict)]
                for mk in node.get("markets") or []:
                    if (mk.get("marketType") or "").lower() not in ("moneyline", "h2h"):
                        continue
                    prices = {}
                    for o in mk.get("outcomes") or []:
                        if o.get("competitor") and o.get("price"):
                            # Bovada/BetOnline publish American prices; convert so the
                            # recorded number is comparable with the other shapes.
                            prices[o["competitor"]] = decimal_from_american(o["price"].get("american"))
                    if len(names) == 2 and len(prices) == 2 and all(prices.values()):
                        out.append({"team_a": names[0], "team_b": names[1],
                                    "decimal_a": prices.get(names[0]),
                                    "decimal_b": prices.get(names[1]),
                                    "start": node.get("startTime"),
                                    "competition": (node.get("competition") or {}).get("name", ""),
                                    "url": node.get("liveLink") or f"bovada-event:{node.get('id')}"})
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data)
    return out


def _prices_linefeed(data):
    out = []
    for ev in (data or {}).get("Value") or []:
        camps = ev.get("Champs") or []
        comp = camps[0].get("Name") if camps else ""
        for o1 in ev.get("Odds1") or []:
            pairs = (o1.get("v") or [])
            if len(pairs) >= 2 and pairs[0] and pairs[1]:
                out.append({"team_a": pairs[0][0], "team_b": pairs[1][0],
                            "decimal_a": pairs[0][1], "decimal_b": pairs[1][1],
                            "start": ev.get("Start"), "competition": comp,
                            "url": f"https://1xbet.com/en/line/{ev.get('ChampId')}/{ev.get('Id')}"})
    return out


def _prices_sofascore(data):
    """Sofascore nests 1X2 odds under `odds`; the exact shape varies by sport and
    the endpoint answers 403 to automated clients, so this parser only accepts
    shapes it can read unambiguously and never guesses at the rest."""
    out = []
    for ev in (data or {}).get("events") or []:
        if not isinstance(ev, dict):
            continue
        e = ev.get("event") if isinstance(ev.get("event"), dict) else ev
        ha = ((e.get("homeTeam") or {}).get("name")) if isinstance(e.get("homeTeam"), dict) else None
        aw = ((e.get("awayTeam") or {}).get("name")) if isinstance(e.get("awayTeam"), dict) else None
        block = ev.get("odds") if isinstance(ev.get("odds"), dict) else {}
        pair = block.get("1") or block.get("2")
        vals = None
        if isinstance(pair, dict):
            vals = (pair.get("0"), pair.get("1"))
        elif isinstance(pair, list) and len(pair) == 2:
            first = pair[0]
            vals = (first.get("0"), first.get("1")) if isinstance(first, dict) else tuple(pair)
        if not (ha and aw and vals and vals[0] and vals[1]):
            continue
        try:
            da, db = float(vals[0]), float(vals[1])
        except (TypeError, ValueError):
            continue
        if da <= 1.0 or db <= 1.0:
            continue
        out.append({"team_a": ha, "team_b": aw, "decimal_a": da, "decimal_b": db,
                    "start": e.get("startTimestamp"),
                    "competition": (e.get("tournament") or {}).get("name", ""),
                    "url": f"https://www.sofascore.com/esports/match/{e.get('slug')}"})
    return out


PARSERS = {"kambi": _prices_kambi, "bovada-family": _prices_bovada_family,
           "linefeed": _prices_linefeed, "sofascore": _prices_sofascore}


def extract_and_match(shape: str, text: str, index, unpriced_ids: set,
                      source_url: str = "") -> tuple[list, list]:
    """Parse one response body and match its two-way prices to published fixtures.

    Returns (prices, matched). `matched` only ever contains fixtures that are
    currently priced WITHOUT a bookmaker line - a source that re-prices the
    World Championship tells us nothing about the low-tier question this sweep
    exists to answer.
    """
    prices: list = []
    matched: list = []
    if shape not in PARSERS:
        return prices, matched
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return prices, matched
    for p in PARSERS[shape](data) or []:
        prices.append(p)
        hit = index.match(p.get("team_a"), p.get("team_b"), p.get("start"))
        if not hit:
            continue
        m, score = hit
        if str(m.get("id")) not in unpriced_ids:
            continue
        matched.append({"fixture": str(m.get("id")),
                        "match": f"{m.get('team1')} vs {m.get('team2')}",
                        "tournament": m.get("tournament"),
                        "source_teams": [p.get("team_a"), p.get("team_b")],
                        "decimal": [p.get("decimal_a"), p.get("decimal_b")],
                        "start_utc": p.get("start"), "similarity": score,
                        # the link a human re-reads is the candidate's own page;
                        # the per-event reference the parser built is kept beside it
                        "url": source_url or p.get("url") or "",
                        "source_ref": p.get("url") or ""})
    return prices, matched


def _verdict(row) -> str:
    st = row["http_status"]
    if st == 401 or st == 402:
        return "key-gated (HTTP 401/402) - no key is configured, so nothing can be read or used"
    if st == 403:
        return "blocked to automated requests (HTTP 403) - no line can be read from CI"
    if st in (404, 410):
        return f"no such endpoint (HTTP {st}) - the site does not publish this board"
    if st == 203:
        return "geo-restriction/interstitial page (HTTP 203) instead of the feed - nothing readable"
    if st in (0, 500, 502, 503, 504):
        return f"not reachable from CI this run (HTTP {st or 'network error'}) - nothing used"
    if st != 200:
        return f"HTTP {st} - nothing used"
    if row["matched_fixtures"]:
        return ("STRUCTURED PRICES MATCHING PUBLISHED FIXTURES - candidate for an adapter, but only "
                "after a human re-reads a sample row against the live page; not used in any probability")
    if row["prices_found"]:
        return ("structured two-way prices readable, but none of them is one of the fixtures we price "
                "with our model - nothing to add")
    if row["team_name_hits"] or row["league_name_hits"]:
        return ("reachable and mentions our low-tier teams/leagues, but no machine-readable two-way "
                "price in the response - human cross-check only, never a probability input")
    if row["category"] == "results":
        return ("reachable results/stats page - not parsed as a line and never a probability input; "
                "Leaguepedia remains the production results source")
    return "reachable, but carries none of our low-tier fixtures and no readable price - nothing used"


def probe_one(cand: tuple, index: "FixtureIndex", teams: list[str],
              unpriced_ids: set[str]) -> dict:
    """One polite GET at one candidate source. Never raises: a probe must not break a run.

    Kept as a module-level function so `sweep()` can fan the candidates out over a small
    thread pool (5 workers, one request each - the same politeness the other probes in this
    repo use) without changing what a single probe does.
    """
    name, url, shape, category, note = cand
    row = {"name": name, "url": url, "shape": shape, "category": category, "why": note,
           "http_status": None, "bytes": 0, "is_json": False, "prices_found": 0,
           "matched_fixtures": [], "team_name_hits": [], "league_name_hits": [],
           "verdict": ""}
    try:
        r = fetch(url, timeout=25, retries=1) or {}
        text = r.get("text") or ""
        row["http_status"] = r.get("status")
        row["bytes"] = len(text.encode("utf-8", "ignore"))
        body_norm = norm(text[:1500000])
        row["league_name_hits"] = _league_hits(body_norm)
        row["team_name_hits"] = _team_hits(body_norm, teams)[:25]
        row["team_name_hits_total"] = len(_team_hits(body_norm, teams))
        if row["http_status"] == 200 and shape in PARSERS:
            try:
                json.loads(text)
                row["is_json"] = True
            except json.JSONDecodeError:
                row["is_json"] = False
            prices, matched = extract_and_match(shape, text, index, unpriced_ids, url)
            row["prices_found"] = len(prices)
            row["matched_fixtures"] = matched
        elif row["http_status"] == 200:
            try:
                json.loads(text)
                row["is_json"] = True
            except json.JSONDecodeError:
                pass
    except Exception as e:  # noqa: BLE001 - a probe must never break a run
        row["http_status"] = 0
        row["verdict"] = f"probe error: {repr(e)[:160]}"
        log(f"lowtier sweep: {name} -> error {row['verdict']}")
        return row
    row["verdict"] = _verdict(row)
    log(f"lowtier sweep: {name} -> HTTP {row['http_status']} json={row['is_json']} "
        f"prices={row['prices_found']} matched={len(row['matched_fixtures'])} "
        f"teams={row.get('team_name_hits_total', len(row['team_name_hits']))}")
    return row


def sweep(payload: dict, limit: int | None = None) -> dict:
    matches = payload.get("matches") or []
    index = FixtureIndex(matches)
    # Only fixtures without a book line are the question this sweep answers.
    unpriced = [m for m in matches if not m.get("market")]
    teams = sorted({t for m in unpriced for t in (m.get("team1"), m.get("team2"))
                    if t and len(norm(t)) >= 6})
    unpriced_ids = {str(x.get("id")) for x in unpriced}
    cands = CANDIDATES[:limit] if limit else CANDIDATES
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        rows = list(pool.map(lambda c: probe_one(c, index, teams, unpriced_ids), cands))
    summary = {
        "checked": len(rows),
        "reachable": sum(1 for r in rows if r["http_status"] == 200),
        "with_readable_two_way_prices": sum(1 for r in rows if r["prices_found"]),
        "sources_matching_an_unpriced_fixture": sum(1 for r in rows if r["matched_fixtures"]),
        "unpriced_fixtures_asked_about": len(unpriced),
        "unpriced_team_names_scanned": len(teams),
        "note": ("Sweep only: no value read here is used in any probability. A source is promoted into "
                 "scripts/fetch_markets.py only after it shows structured prices for a published fixture "
                 "AND a human re-reads a sample row against the live page."),
    }
    return {"checked_at": utc_iso(now_utc()), "payload_generated_at": payload.get("generated_at"),
            "summary": summary, "sources": rows}


def write_markdown(data: dict, path: str) -> None:
    s = data["summary"]
    lines = [
        "# Low-tier line sweep - latest automated run",
        "",
        f"Generated by `scripts/probe_lowtier.py` at **{data['checked_at']}** against the payload of "
        f"{data['payload_generated_at']}.",
        "",
        f"{s['checked']} candidate sources were each asked once whether they price the "
        f"**{s['unpriced_fixtures_asked_about']} fixtures that have no bookmaker line** "
        f"({s['unpriced_team_names_scanned']} distinct team names scanned). "
        f"{s['reachable']} answered HTTP 200, {s['with_readable_two_way_prices']} exposed a readable "
        f"two-way price, and **{s['sources_matching_an_unpriced_fixture']}** priced one of those fixtures.",
        "",
        "> Nothing in this table is used in a probability. It is reachability and coverage evidence: the "
        "status shown is what the source returned to this run, not what it is believed to return.",
        "",
        "| Source | Status | Readable two-way prices | Matches one of our unpriced fixtures? | Our low-tier names seen | Verdict |",
        "|---|---|---|---|---|---|",
    ]
    for r in data["sources"]:
        names = r.get("team_name_hits_total", len(r.get("team_name_hits") or []))
        leagues = ", ".join(r.get("league_name_hits") or []) or "-"
        lines.append(
            f"| [{r['name']}]({r['url']}) | {r['http_status']} "
            f"{'(JSON)' if r['is_json'] else ''} | {r['prices_found']} | "
            f"{len(r['matched_fixtures'])} | {names} team(s); leagues: {leagues} | {r['verdict']} |")
    matched = [x for r in data["sources"] for x in r["matched_fixtures"]]
    if matched:
        lines += ["", "## Fixtures a candidate source actually priced", "",
                  "| Source | Fixture | Teams (theirs) | Decimals | Start (theirs) | Link |", "|---|---|---|---|---|---|"]
        for r in data["sources"]:
            for x in r["matched_fixtures"]:
                lines.append(f"| {r['name']} | {x['fixture']} {x['match']} ({x['tournament']}) | "
                             f"{x['source_teams'][0]} vs {x['source_teams'][1]} | {x['decimal']} | "
                             f"{x['start_utc']} | [open]({x['url']}) |")
        lines += ["", "Promotion still requires a human to re-read a sample row against the live page "
                     "and record it in `research/`.", ""]
    lines += ["", "## Why each candidate was chosen", ""]
    for r in data["sources"]:
        lines.append(f"- **{r['name']}** ({r['category']}): {r['why']}")
    lines.append("")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main() -> int:
    if not os.path.exists(PICKS):
        log(f"lowtier sweep: {PICKS} missing - nothing to fixture-match against")
        return 0
    with open(PICKS, encoding="utf-8") as fh:
        payload = json.load(fh)
    data = sweep(payload)
    write_json(OUT_JSON, data)
    write_markdown(data, OUT_MD)
    print(json.dumps(data["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

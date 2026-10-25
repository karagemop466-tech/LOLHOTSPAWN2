#!/usr/bin/env python3
"""Focused probe: does any external book publish a price for the fixtures our
model currently has to price?

Context (2026-10-25)
--------------------
The published payload prices every Hotspawn LoL fixture, but only ~9 of ~156 come
from an external betting line. The brief asks for external lines wherever they
exist, tried in this order: established LoL betting sites -> esportsbooks ->
esports betting lines / aggregators.

This probe is the evidence for the statement "no readable line exists for these
fixtures". It takes the team names of the fixtures that have **no** external
market, asks each candidate source for its public page/endpoint, and records:

  * HTTP status, byte count, whether the body is JSON
  * which of our competitions the page even names (context, not a price)
  * how many fixtures have BOTH team names inside one 700-character window
    together with two or more odds-like decimals. This is deliberately strict:
    a loose "team word appears near a number" test produced false positives on
    a basketball page ("Alba Berlin"), a CSS gradient ("atomic") and a meta tag,
    so full team names in the same window are required
  * up to five candidate windows for human review

It never writes a probability, never feeds the model, and always exits 0.

Output: data/diag/prm_line_probe.json (committed for manual review).
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from lib_common import fetch, now_utc, utc_iso, write_json  # noqa: E402

OUT = "data/diag/prm_line_probe.json"
PICKS = "docs/data/picks.json"

# (name, url, kind, note) — one polite GET each, no authentication anywhere.
SOURCES: tuple[tuple[str, str, str, str], ...] = (
    # --- esportsbooks with a documented public API ---------------------------
    ("Cloudbet public sports API (sport index)",
     "https://sports-api.cloudbet.com/pub/v2/odds/sports", "json-api",
     "Cloudbet's own LoL page advertises Prime League 2nd Division pricing"),
    ("Cloudbet public sports API (LoL competitions)",
     "https://sports-api.cloudbet.com/pub/v2/odds/sports/league-of-legends/competitions", "json-api",
     "Competition list would name every LoL league Cloudbet prices"),
    ("Cloudbet — Prime League 2nd Division category page",
     "https://www.cloudbet.com/en/esports/league-of-legends/germany-t8205-prime-league-2nd-division?tab=events",
     "esportsbook-page", "Says it prices PRM 2nd Division through the split"),
    # --- comparison sites that name the low-tier leagues ---------------------
    ("BMBets — LoL Prime League 2nd Division",
     "https://www.bmbets.com/e-sports/world/lol---prime-league-2nd-division/", "aggregator-page",
     "Dedicated comparison page for the exact competition Hotspawn lists"),
    ("BMBets — LoL Prime League (1st Division)",
     "https://www.bmbets.com/e-sports/world/lol---prime-league/", "aggregator-page",
     "Sister page; shows whether the comparison site prices German LoL at all"),
    ("Betmonitor — Prime League 2nd Division comparison",
     "https://www.betmonitor.com/odds-comparison/esports/prime-league-2nd-division/10024464",
     "aggregator-page", "German odds comparison; its search index shows bet365/ggbet prices here"),
    ("Betmonitor — esports hub",
     "https://www.betmonitor.com/odds-comparison/esports/", "aggregator-page",
     "League index: shows which esports competitions Betmonitor tracks"),
    # --- established German / European sportsbooks (the league's home market)
    ("Tipico (DE) esports",
     "https://www.tipico.de/en/esports/league-of-legends/", "sportsbook-page",
     "German-licensed book; Prime League is the German national league"),
    ("NEO.bet (DE) esports", "https://www.neobet.de/sportwetten/esports", "sportsbook-page",
     "German-licensed book"),
    ("bwin (DE) esports", "https://sports.bwin.de/en/sports/esports", "sportsbook-page",
     "German-licensed book"),
    ("bet365 (DE) esports", "https://www.bet365.de/#/AS/B1/", "sportsbook-page",
     "Largest global book; often prices Prime League"),
    ("Everygame esports LoL",
     "https://www.everygame.eu/en/Esports/League-of-Legends", "sportsbook-page",
     "Review sites list Prime League in its LoL coverage"),
    # --- esportsbooks / aggregators known to be blocked or empty ------------
    ("eGamersWorld LoL odds board", "https://egamersworld.com/lol/bets", "aggregator-page",
     "Aggregator with per-match bookmaker prices"),
    ("EsportBet LoL board", "https://esportbet.com/league-of-legends/", "aggregator-page",
     "Lists Prime League 2. Liga as a live tournament"),
    ("Strafe LoL odds", "https://www.strafe.com/esports-betting/odds/league-of-legends/",
     "aggregator-page", "Aggregator; previously returned 200 HTML"),
    ("1xBet LineFeed (esports, sport=3)",
     "https://1xbet.com/LineFeed/Get1x2_VZip?sports=3&count=1000&lng=en&mode=4&country=1&partner=51",
     "esportsbook-api", "Deep tier-3 coverage; geo-restricted in past runs"),
)

# An odds-like decimal: 1.01 .. 30.00, not part of a longer number, date or id.
ODDS_RE = re.compile(r"(?<![\d.,:-])((?:[1-9]|1\d|2\d|30)\.\d{2})(?![\d.,%:-])")
# A candidate price needs BOTH team names inside this window, plus two odds.
MATCH_WINDOW = 700

COMPETITIONS = ("Prime League", "RIVALS LEAGUE", "Tunisian Super League",
                "Arabian League", "4 Nations", "Komplettligaen", "LigaGG", "LGC Rising")


def _name_pattern(name: str) -> re.Pattern | None:
    """Regex for a whole team name: its tokens in order, separators allowed."""
    toks = re.findall(r"[A-Za-z0-9\u00c0-\u024f']+", name or "")
    if not toks:
        return None
    body = r"[^A-Za-z0-9\u00c0-\u024f]{0,6}".join(re.escape(t) for t in toks)
    return re.compile(body, re.I)


def fixture_names(matches: list[dict]) -> list[tuple[str, str]]:
    """(team1, team2) pairs for fixtures with no external market, deduplicated."""
    out: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for m in matches:
        if m.get("market"):
            continue
        a, b = str(m.get("team1") or ""), str(m.get("team2") or "")
        if not a or not b or (a, b) in seen:
            continue
        seen.add((a, b))
        out.append((a, b))
    return out


def find_prices(text: str, pairs: list[tuple[str, str]]) -> tuple[int, list[dict]]:
    """Fixtures whose BOTH team names sit in one window with two or more odds."""
    hits: list[dict] = []
    for a, b in pairs:
        pa, pb = _name_pattern(a), _name_pattern(b)
        if not pa or not pb:
            continue
        for mt in pa.finditer(text):
            window = text[mt.start(): mt.start() + MATCH_WINDOW]
            if not pb.search(window):
                continue
            odds = ODDS_RE.findall(window)
            if len(odds) < 2:
                continue
            hits.append({"team1": a, "team2": b, "odds_seen": odds[:6],
                         "snippet": re.sub(r"\s+", " ", window)[:300]})
            break  # one hit per fixture is enough
    return len(hits), hits


def probe(name: str, url: str, kind: str, note: str, pairs: list[tuple[str, str]]) -> dict:
    row = {"name": name, "url": url, "kind": kind, "note": note,
           "http_status": None, "bytes": 0, "is_json": False,
           "fixtures_matched": 0, "candidate_prices": [], "leagues_named": [], "verdict": ""}
    try:
        r = fetch(url, timeout=20, retries=2) or {}
        text = r.get("text") or ""
        status = r.get("status")
        row["http_status"] = status
        row["bytes"] = len(text.encode("utf-8", "ignore"))
        try:
            json.loads(text)
            row["is_json"] = True
        except (json.JSONDecodeError, ValueError):
            pass
        if status != 200 or not text:
            row["verdict"] = (f"HTTP {status}: no page body readable — no line can be extracted "
                              "from this source in an automated run")
            return row
        n, hits = find_prices(text, pairs)
        row["fixtures_matched"] = n
        row["candidate_prices"] = hits[:5]
        row["leagues_named"] = [lg for lg in COMPETITIONS if re.search(lg, text, re.I)]
        if n:
            row["verdict"] = (f"{n} fixture(s) have BOTH team names in one window with two or more "
                              "odds-like numbers — a human must confirm this is a real two-way line "
                              "for that fixture before any adapter is written")
        elif row["leagues_named"]:
            row["verdict"] = (f"names {', '.join(row['leagues_named'])} but publishes no two-way "
                              "price for any current fixture (no window holds both teams and two prices)")
        else:
            row["verdict"] = ("reachable, but does not name these competitions or fixtures — "
                              "the source does not cover these matches right now")
    except Exception as e:  # noqa: BLE001 - a probe must never break a run
        row["http_status"] = 0
        row["verdict"] = f"probe error: {repr(e)[:140]}"
    return row


def main() -> int:
    matches: list[dict] = []
    try:
        with open(PICKS, encoding="utf-8") as fh:
            matches = (json.load(fh) or {}).get("matches") or []
    except (OSError, json.JSONDecodeError):
        matches = []
    model_only = [m for m in matches if not m.get("market")]
    pairs = fixture_names(matches)
    out = {
        "generated_at": utc_iso(now_utc()),
        "query": ("Which external sources publish a price for the Hotspawn LoL fixtures that "
                  "currently have no external market?"),
        "fixtures_total": len(matches),
        "fixtures_without_external_market": len(model_only),
        "fixtures_tested": len(pairs),
        "sources": [],
        "summary": {},
    }
    for name, url, kind, note in SOURCES:
        row = probe(name, url, kind, note, pairs)
        out["sources"].append(row)
        print(f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] "
              f"{name} -> HTTP {row['http_status']} fixtures_matched={row['fixtures_matched']} "
              f"named={len(row['leagues_named'])}", file=sys.stderr, flush=True)
    readable = [r for r in out["sources"] if r["http_status"] == 200]
    with_price = [r for r in readable if r["fixtures_matched"]]
    out["summary"] = {
        "sources_probed": len(out["sources"]),
        "reachable_200": len(readable),
        "naming_one_of_our_competitions": len([r for r in readable if r["leagues_named"]]),
        "publishing_a_two_way_price_for_a_fixture": len(with_price),
        "conclusion": ("No source returned a readable two-way price for any fixture that currently "
                       "lacks an external line." if not with_price else
                       "Some sources showed both team names next to two odds-like numbers; each "
                       "sample must be verified by hand before use."),
    }
    write_json(OUT, out)
    print(json.dumps(out["summary"], indent=1), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

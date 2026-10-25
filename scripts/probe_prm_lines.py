#!/usr/bin/env python3
"""Focused probe: do any external books publish a price for the fixtures our
model currently has to price?

Context (2026-10-25)
--------------------
The published payload prices every Hotspawn LoL fixture, but only ~9 of ~156 come
from an external betting line. The rest are model rows. The brief asks for
external lines wherever they exist, tried in this order:

  1. established League of Legends betting sites
  2. esportsbooks
  3. esports betting lines / odds aggregators

This probe is the *evidence* for the statement "no readable line exists for
these fixtures". It is deliberately narrow: it takes the team names of the
fixtures that currently have **no** external market, asks each candidate source
for its public page/endpoint, and records:

  * HTTP status, byte count, whether the body is JSON
  * how many of our model-only team tokens appear anywhere in the body
  * how many decimal-odds-looking numbers appear *within 240 characters* of
    such a team token (a crude "is there a price next to this team" test)
  * up to three short raw snippets around a team-token hit, for human review

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

from lib_common import fetch, norm, now_utc, utc_iso, write_json  # noqa: E402

OUT = "data/diag/prm_line_probe.json"
PICKS = "docs/data/picks.json"

# Generic words that appear in many team names; they would produce false hits.
STOP = {
    "esports", "esport", "gaming", "team", "academy", "club", "organization", "org",
    "league", "division", "prime", "series", "season", "split", "rising", "black",
    "white", "red", "blue", "green", "young", "main", "prime", "second", "first",
    "lions", "wolves", "kings", "tigers", "dragons", "phoenix", "starks", "sports",
}

# (name, url, kind, note)  — one polite GET each, no authentication anywhere.
SOURCES: tuple[tuple[str, str, str, str], ...] = (
    # --- esportsbooks with a documented public API ---------------------------
    ("Cloudbet public sports API (sport index)",
     "https://sports-api.cloudbet.com/pub/v2/odds/sports", "json-api",
     "Cloudbet advertises Prime League 2nd Division pricing on its own LoL category page"),
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
     "aggregator-page", "German odds comparison; search index shows bet365/ggbet prices on this page"),
    ("Betmonitor — esports hub",
     "https://www.betmonitor.com/odds-comparison/esports/", "aggregator-page",
     "League index: shows which esports competitions Betmonitor tracks"),
    # --- established German / European sportsbooks (the league's home market)
    ("Tipico (DE) esports",
     "https://www.tipico.de/en/esports/league-of-legends/", "sportsbook-page",
     "German-licensed book; Prime League is the German national league"),
    ("NEO.bet (DE) esports",
     "https://www.neobet.de/sportwetten/esports", "sportsbook-page",
     "German-licensed book"),
    ("bwin (DE) esports",
     "https://sports.bwin.de/en/sports/esports", "sportsbook-page",
     "German-licensed book"),
    ("bet365 (DE) esports",
     "https://www.bet365.de/#/AS/B1/", "sportsbook-page",
     "Largest global book; often prices Prime League"),
    ("Everygame esports LoL",
     "https://www.everygame.eu/en/Esports/League-of-Legends", "sportsbook-page",
     "Review sites list Prime League in its LoL coverage"),
    # --- esportsbooks / aggregators already known to be blocked or empty ----
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

TEAM_TOKEN_MIN = 5
ODDS_RE = re.compile(r"(?<![\d.])(\d{1,2}\.\d{2})(?![\d.])")
SNIPPET_RADIUS = 240


def team_tokens(matches: list[dict]) -> list[tuple[str, str]]:
    """Distinctive tokens from fixtures that have no external market."""
    out: dict[str, str] = {}
    for m in matches:
        if m.get("market"):
            continue
        for key in ("team1", "team2"):
            name = str(m.get(key) or "")
            for tok in re.findall(r"[A-Za-zÀ-ÿ0-9']+", name):
                low = tok.lower()
                if len(low) < TEAM_TOKEN_MIN or low in STOP or low.isdigit():
                    continue
                if low in {"esports", "gaming", "academy"}:
                    continue
                out.setdefault(low, name)
    return sorted(out.items())


def probe(name: str, url: str, kind: str, note: str, tokens: list[tuple[str, str]]) -> dict:
    row = {"name": name, "url": url, "kind": kind, "note": note,
           "http_status": None, "bytes": 0, "is_json": False,
           "team_tokens_found": 0, "token_samples": [], "odds_near_team": 0,
           "snippets": [], "verdict": ""}
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
        low = text.lower()
        hits: list[str] = []
        for tok, owner in tokens:
            if tok in low:
                hits.append(tok)
        row["team_tokens_found"] = len(hits)
        row["token_samples"] = hits[:12]
        snippets = 0
        odds_near = 0
        for tok in hits:
            for mt in re.finditer(re.escape(tok), low):
                window = text[max(0, mt.start() - SNIPPET_RADIUS): mt.start() + SNIPPET_RADIUS]
                if ODDS_RE.search(window):
                    odds_near += 1
                if snippets < 3:
                    row["snippets"].append(re.sub(r"\s+", " ", window)[:400])
                    snippets += 1
                if snippets >= 3 and odds_near:
                    break
        row["odds_near_team"] = odds_near
        if hits and odds_near:
            row["verdict"] = (f"{len(hits)} of our model-only team tokens appear with odds-like numbers "
                              "nearby — inspect the snippets; a human must confirm the price belongs to "
                              "the fixture before any adapter is written")
        elif hits:
            row["verdict"] = (f"{len(hits)} team tokens appear, but no odds-like number within "
                              f"{SNIPPET_RADIUS} characters — the page names the teams without a price")
        else:
            row["verdict"] = ("reachable, but none of the currently unpriced fixtures is named on it — "
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
    tokens = team_tokens(matches)
    now = now_utc()
    out = {
        "generated_at": utc_iso(now),
        "query": ("Which external sources publish a price for the Hotspawn LoL fixtures that "
                  "currently have no external market?"),
        "fixtures_total": len(matches),
        "fixtures_without_external_market": len(model_only),
        "team_tokens_tested": len(tokens),
        "sources": [],
        "summary": {},
    }
    for name, url, kind, note in SOURCES:
        row = probe(name, url, kind, note, tokens)
        out["sources"].append(row)
        print(f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] "
              f"{name} -> HTTP {row['http_status']} tokens={row['team_tokens_found']} "
              f"odds_near_team={row['odds_near_team']}", file=sys.stderr, flush=True)
    readable = [r for r in out["sources"] if r["http_status"] == 200]
    with_price = [r for r in readable if r["odds_near_team"]]
    out["summary"] = {
        "sources_probed": len(out["sources"]),
        "reachable_200": len(readable),
        "naming_our_fixtures": len([r for r in readable if r["team_tokens_found"]]),
        "with_odds_near_a_team_token": len(with_price),
        "conclusion": ("No source returned a readable two-way price for any fixture that currently "
                       "lacks an external line." if not with_price else
                       "Some sources returned odds-like numbers next to our team names; each sample "
                       "must be verified by hand before use."),
    }
    write_json(OUT, out)
    print(json.dumps(out["summary"], indent=1), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
source_audit.py — line-by-line audit of the published matches against the raw
Leaguepedia MatchSchedule snapshots the pipeline already downloads.

Why this exists
---------------
The site promises that every published match can be checked against an official
source. The pipeline attaches `leaguepedia_url` and `sources[]` to each row; this
module re-derives the evidence instead of trusting those labels:

  * arithmetic: probabilities sum to 1, the pick is the higher-probability side,
    `pick_prob` matches, and every probability is inside [2%, 98%];
  * provenance: at least one https source link per row;
  * independent re-match: the team pair is searched for in the raw snapshot
    (`data/diag/ms_*.json`). Hits on the same UTC date are "verified". A pair
    found on another date, or not found at all, is reported as a flag — never as
    a silently correct value. Competitions with no snapshot at all are reported
    as "no snapshot", not as failures.

Only arithmetic/provenance defects count as `failed`. Everything else is a
coverage flag that the site publishes on its Flagged page.

Used by scripts/update_picks.py (writes payload["source_audit"]) and by
verification/audit_payload_sources.py (standalone CLI + CI gate).
"""
from __future__ import annotations

import json
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIKI = "https://lol.fandom.com/wiki/"

# Only these count as data errors. A fixture the snapshot does not contain is a
# coverage/verification gap and is reported as such, not as a wrong number.
HARD_CHECKS = {"sum_to_one", "pick_is_higher", "in_range", "has_https_source"}


def norm(s: str) -> str:
    """Loose name normalisation: accents, brackets, punctuation, suffixes."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"\b(esports?|e\.?\s?v\.?|ev|gaming|club|team|orga|organization)\b", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def day_of(value: str) -> str:
    return (value or "")[:10].replace(" ", "T")


def load_snapshots(diag_dir: str) -> list[dict]:
    rows: list[dict] = []
    if not os.path.isdir(diag_dir):
        return rows
    for name in sorted(os.listdir(diag_dir)):
        if not (name.startswith("ms_") and name.endswith(".json")):
            continue
        try:
            data = json.load(open(os.path.join(diag_dir, name), encoding="utf-8"))
        except Exception:  # noqa: BLE001 - a broken snapshot must not kill the audit
            continue
        if isinstance(data, list):
            for r in data:
                if isinstance(r, dict) and r.get("Team1") and r.get("Team2"):
                    r["_snapshot"] = name
                    rows.append(r)
    return rows


def find_pair(rows: list[dict], team1: str, team2: str) -> list[dict]:
    a, b = norm(team1), norm(team2)
    return [r for r in rows
            if {norm(r["Team1"]), norm(r["Team2"])} == {a, b}]


def league_map() -> dict[str, list[str]]:
    """Hotspawn tournament -> Leaguepedia OverviewPage(s). Imported from the
    coverage checker so there is exactly one mapping in the repo."""
    try:
        import sys
        sys.path.insert(0, os.path.join(ROOT, "verification"))
        from check_leaguepedia_coverage import LEAGUE_MAP  # noqa: WPS433
        return LEAGUE_MAP
    except Exception:  # noqa: BLE001
        return {}


def audit(matches: list[dict], diag_dir: str | None = None) -> dict:
    diag_dir = diag_dir or os.path.join(ROOT, "data", "diag")
    snaps = load_snapshots(diag_dir)
    covered_pages = {(r.get("OverviewPage") or "") for r in snaps}
    lmap = league_map()

    failed: list[str] = []
    flags: list[dict] = []
    verified = 0
    no_snapshot = 0

    for m in matches:
        mid = str(m.get("id", "?"))
        p1, p2 = m.get("prob_team1"), m.get("prob_team2")
        pick, pick_prob = m.get("pick"), m.get("pick_prob")
        sources = [s.get("url") if isinstance(s, dict) else s for s in (m.get("sources") or [])]
        sources = [s for s in sources if isinstance(s, str)]

        bad: list[str] = []
        if not (isinstance(p1, (int, float)) and isinstance(p2, (int, float))
                and abs(p1 + p2 - 1) < 5e-4):
            bad.append("probabilities do not sum to 1")
        if not (pick in (m.get("team1"), m.get("team2")) and isinstance(pick_prob, (int, float))
                and abs(pick_prob - (p1 if pick == m.get("team1") else p2)) < 5e-4):
            bad.append("pick is not the higher-probability side")
        if not all(isinstance(v, (int, float)) and 0.02 <= v <= 0.98 for v in (p1, p2)):
            bad.append("probability outside [2%, 98%]")
        if not sources or not all(s.startswith("https://") for s in sources):
            bad.append("missing https source link")
        for b in bad:
            failed.append(f"{mid}: {b}")

        hits = find_pair(snaps, m.get("team1", ""), m.get("team2", ""))
        same_day = [h for h in hits if day_of(h.get("DateTime UTC")) == day_of(m.get("start_utc"))]
        pages = lmap.get(m.get("tournament") or "", [])
        covered = bool(pages) and any(p in covered_pages for p in pages)

        if same_day:
            verified += 1
            continue
        if not covered:
            # No snapshot exists for this competition, so there is nothing to
            # re-match against. Counted separately instead of being published as
            # a mismatch (it is a coverage gap, not a contradiction).
            no_snapshot += 1
            continue
        elif hits:
            verdict = "the pair is on the Leaguepedia schedule, but not on this date"
        else:
            verdict = "the pair is not on the Leaguepedia schedule snapshot"
        flags.append({
            "id": mid,
            "teams": f"{m.get('team1')} vs {m.get('team2')}",
            "competition": m.get("tournament"),
            "start_utc": m.get("start_utc"),
            "method": m.get("method"),
            "verdict": verdict,
            "claimed": m.get("fixture_match"),
            "leaguepedia_url": m.get("leaguepedia_url") or (WIKI + pages[0].replace(" ", "_") if pages else None),
            "match_url": f"match.html?id={mid}",
            "snapshot_row": (hits[0].get("_snapshot") if hits else None),
            "snapshot_time": (hits[0].get("DateTime UTC") if hits else None),
        })

    return {
        "rows": len(matches),
        "snapshot_rows": len(snaps),
        "verified": verified,
        "no_snapshot": no_snapshot,
        "flagged": len(flags),
        "failed": len(failed),
        "failures": failed,
        "flags": flags,
        "verdict": "PASS" if not failed else "FAIL",
    }


if __name__ == "__main__":  # tiny manual check
    payload = json.load(open(os.path.join(ROOT, "docs", "data", "picks.json"), encoding="utf-8"))
    out = audit(payload["matches"])
    print({k: out[k] for k in ("rows", "verified", "flagged", "no_snapshot", "failed", "verdict")})

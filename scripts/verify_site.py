#!/usr/bin/env python3
"""Verify the published payload and the static site before / after deploy.

Checks are intentionally strict: a row without a source link, a pick that is not
one of the two teams, probabilities that do not sum to 1, or an unresolved row
that is not exactly 50/50 all fail the run.
"""
from __future__ import annotations

import json
import os
import re
import sys
from urllib.parse import urlparse

DATA = "docs/data/picks.json"
PAGES = ["index.html", "picks.html", "unresolved.html", "flagged.html", "methodology.html", "match.html"]
METHODS = {"MARKET_CONSENSUS", "MARKET_SINGLE", "MODEL_ELO", "MODEL_ELO_THIN",
           "MODEL_LEAGUE_PRIOR", "UNRESOLVED"}
CONF = {"High", "Medium", "Low", "None"}


def http_ok(url: str) -> bool:
    try:
        p = urlparse(url)
    except Exception:
        return False
    return p.scheme in ("http", "https") and bool(p.netloc)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    if not os.path.exists(DATA):
        print(f"missing {DATA}", file=sys.stderr)
        return 1
    d = json.load(open(DATA))

    if d.get("schema_version") != 3:
        errors.append(f"schema_version is {d.get('schema_version')!r}, expected 3")
    for key in ("counts", "coverage", "model", "unresolved", "sources_status", "matches"):
        if key not in d:
            errors.append(f"missing top-level key {key}")

    matches = d.get("matches") or []
    if len(matches) < 50:
        errors.append(f"only {len(matches)} fixtures published")

    with_market = sum(1 for m in matches if m.get("market"))
    resolved = sum(1 for m in matches if m.get("resolved"))
    ids = set()
    for m in matches:
        mid = str(m.get("id"))
        if mid in ids:
            errors.append(f"duplicate fixture id {mid}")
        ids.add(mid)
        if m.get("method") not in METHODS:
            errors.append(f"{mid}: unknown method {m.get('method')!r}")
        if m.get("confidence") not in CONF:
            errors.append(f"{mid}: unknown confidence {m.get('confidence')!r}")
        if m.get("pick") not in (m.get("team1"), m.get("team2")):
            errors.append(f"{mid}: pick is not one of the teams")
        try:
            total = float(m["prob_team1"]) + float(m["prob_team2"])
            if abs(total - 1) > 0.005:
                errors.append(f"{mid}: probabilities sum to {total:.4f}")
            if not 0 <= float(m["prob_team1"]) <= 1:
                errors.append(f"{mid}: probability out of range")
        except Exception:
            errors.append(f"{mid}: missing probabilities")
        if m.get("method") == "UNRESOLVED" and abs(float(m.get("pick_prob", 0)) - 0.5) > 1e-6:
            errors.append(f"{mid}: unresolved row is not an explicit 50/50 placeholder")
        srcs = [s for s in (m.get("sources") or []) if s.get("url")]
        if not srcs:
            errors.append(f"{mid}: no source link")
        for s in srcs:
            if not http_ok(s["url"]):
                errors.append(f"{mid}: bad source url {s['url']!r}")
        if m.get("resolved") and not (m.get("market") or m.get("model")):
            errors.append(f"{mid}: resolved without market or model evidence")
        if m.get("market"):
            for r in m["market"].get("sources") or []:
                if not http_ok(r.get("url", "")):
                    errors.append(f"{mid}: market source without url")
        if m.get("start_utc") and not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", m["start_utc"]):
            errors.append(f"{mid}: start time is not ISO UTC ({m['start_utc']!r})")
        if m.get("crowd"):
            # Crowd data may be displayed, but must never be an input. Guard the payload shape.
            if "used_as_input" in m["crowd"] and m["crowd"]["used_as_input"]:
                errors.append(f"{mid}: crowd data marked as a probability input")

    counts = d.get("counts") or {}
    if counts.get("fixtures") != len(matches):
        errors.append("counts.fixtures does not match the match list")
    if counts.get("market") not in (None, with_market):
        errors.append("counts.market does not match the match list")
    if counts.get("resolved") not in (None, resolved):
        errors.append("counts.resolved does not match the match list")

    for page in PAGES:
        path = os.path.join("docs", page)
        if not os.path.exists(path):
            errors.append(f"missing page {path}")
            continue
        html = open(path, encoding="utf-8").read()
        if "assets/app.js" not in html or "assets/style.css" not in html:
            errors.append(f"{page}: missing asset includes")
        if 'data-page="' not in html:
            errors.append(f"{page}: missing body[data-page]")
        if "data-nav=" not in html:
            errors.append(f"{page}: missing navigation")
        if page != "match.html" and "data/picks.json" not in html and "picks.html" not in html:
            warnings.append(f"{page}: no visible link to the data or picks page")
    if not os.path.exists("docs/data/picks.json"):
        errors.append("docs/data/picks.json is missing (Pages would 404)")

    summary = {
        "fixtures": len(matches),
        "with_market": with_market,
        "resolved": resolved,
        "unresolved": len(matches) - resolved,
        "pages": len(PAGES),
        "errors": len(errors),
        "warnings": len(warnings),
    }
    os.makedirs("data/diag", exist_ok=True)
    json.dump({"summary": summary, "errors": errors[:200], "warnings": warnings[:200]},
              open("data/diag/verify.json", "w"), indent=1)
    print(json.dumps(summary, indent=1))
    for w in warnings[:10]:
        print("warning:", w)
    if errors:
        print(f"\n{len(errors)} verification error(s):", file=sys.stderr)
        for e in errors[:40]:
            print(" -", e, file=sys.stderr)
        return 1
    print("site verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

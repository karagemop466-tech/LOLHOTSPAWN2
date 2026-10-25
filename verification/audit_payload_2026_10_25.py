#!/usr/bin/env python3
"""Independent line-by-line audit of docs/data/picks.json (session arena/b5f85948, 2026-10-25).

This is a deliberately redundant check: scripts/verify_site.py already enforces the
contract in CI; this script re-derives every invariant straight from the payload and
prints a markdown table the user can review without running anything. It never writes
the payload and has no network access.

Exit code is non-zero if any hard invariant fails.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAYLOAD = ROOT / "docs" / "data" / "picks.json"

MARKET_METHODS = {"MARKET_CONSENSUS", "MARKET_SINGLE", "MARKET_BOOKS", "MARKET_POLYMARKET"}
MODEL_METHODS = {"MODEL_ELO", "MODEL_ELO_THIN", "MODEL_ELO_STANDINGS",
                 "MODEL_STANDINGS", "MODEL_LEAGUE_PRIOR"}
ALLOWED_METHODS = MARKET_METHODS | MODEL_METHODS | {"UNRESOLVED"}
ALLOWED_CONF = {"High", "Medium", "Low", "None"}


def parse_ts(s):
    return datetime.fromisoformat(str(s).replace("Z", "+00:00"))


def main() -> int:
    d = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    rows = d.get("matches") or []
    errors: list[str] = []
    notes: list[str] = []
    now = datetime.now(timezone.utc)
    gen = parse_ts(d["generated_at"])

    print("# Line-by-line payload audit — 2026-10-25 (session `arena/b5f85948`)\n")
    print(f"- Payload: `docs/data/picks.json`, generated `{d['generated_at']}` "
          f"({(now - gen).total_seconds() / 3600:.1f} h old at audit time)")
    print(f"- Rows: **{len(rows)}** · declared fixtures: **{d['counts']['fixtures']}**")
    print(f"- Next scheduled update: `{d.get('next_update_utc')}` · stale after: `{d.get('stale_after_utc')}`\n")

    seen_keys: set[tuple] = set()
    method_counter: Counter = Counter()
    conf_counter: Counter = Counter()
    tier_counter: Counter = Counter()
    per_league: Counter = Counter()
    n_book_sources = 0
    n_leaguepedia_sources = 0
    n_hotspawn_sources = 0
    future = past = 0

    for m in rows:
        mid = m.get("id", "?")
        t1, t2 = m.get("team1"), m.get("team2")
        # 1. distinct teams + start time
        if not t1 or not t2 or t1 == t2:
            errors.append(f"{mid}: bad teams {t1!r}/{t2!r}")
        st = parse_ts(m.get("start_utc"))
        if not st:
            errors.append(f"{mid}: unparseable start_utc {m.get('start_utc')!r}")
        else:
            if st >= now:
                future += 1
            else:
                past += 1
        key = (t1, t2, m.get("start_utc"))
        if key in seen_keys:
            errors.append(f"{mid}: duplicate fixture key {key}")
        seen_keys.add(key)
        # 2. probabilities in range and sum to 1
        p1, p2 = m.get("prob_team1"), m.get("prob_team2")
        if not (isinstance(p1, (int, float)) and isinstance(p2, (int, float))):
            errors.append(f"{mid}: probabilities not numeric")
        else:
            if not (0.02 <= p1 <= 0.98 and 0.02 <= p2 <= 0.98):
                errors.append(f"{mid}: probability out of clamp range {p1}/{p2}")
            if abs(p1 + p2 - 1.0) > 0.005:
                errors.append(f"{mid}: probabilities sum to {p1 + p2}")
        # 3. pick equals the higher-probability team and pick_prob matches
        pick = m.get("pick")
        if pick not in (t1, t2):
            errors.append(f"{mid}: pick {pick!r} is not one of the teams")
        else:
            expected = t1 if p1 >= p2 else t2
            if pick != expected:
                errors.append(f"{mid}: pick {pick!r} != higher-prob team {expected!r}")
        if abs(m.get("pick_prob", 0) - max(p1, p2)) > 1e-9:
            errors.append(f"{mid}: pick_prob {m.get('pick_prob')} != max prob")
        # 4. method / confidence labels
        method = m.get("method")
        if method not in ALLOWED_METHODS:
            errors.append(f"{mid}: undocumented method {method!r}")
        method_counter[method] += 1
        if m.get("confidence") not in ALLOWED_CONF:
            errors.append(f"{mid}: bad confidence {m.get('confidence')!r}")
        conf_counter[m.get("confidence")] += 1
        tier_counter[m.get("tier") or "?"] += 1
        per_league[m.get("tournament") or "?"] += 1
        # 5. sources: present, https, named, claimed
        srcs = m.get("sources") or []
        if not srcs:
            errors.append(f"{mid}: no source links")
        for s in srcs:
            url = s.get("url", "")
            if not url.startswith("https://"):
                errors.append(f"{mid}: non-https source {url!r}")
            if not s.get("name") or not s.get("claim"):
                errors.append(f"{mid}: source missing name/claim {s}")
            low = url.lower()
            if "pinnacle" in low or "bovada" in low or "polymarket" in low or "kambicdn" in low or "unibet" in low:
                n_book_sources += 1
            if "fandom.com" in low or "leaguepedia" in low:
                n_leaguepedia_sources += 1
            if "hotspawn" in low:
                n_hotspawn_sources += 1
        # 6. method-specific source contracts
        if method in MARKET_METHODS:
            if not m.get("market"):
                errors.append(f"{mid}: market method without market block")
            if not any("hotspawn" in (s.get("url", "").lower()) for s in srcs):
                errors.append(f"{mid}: market row missing Hotspawn fixture source")
        if method in MODEL_METHODS:
            if not any("fandom.com" in s.get("url", "").lower() for s in srcs):
                errors.append(f"{mid}: model row without Leaguepedia source")
        if method == "UNRESOLVED":
            if not (abs(p1 - 0.5) < 1e-9 and abs(p2 - 0.5) < 1e-9):
                errors.append(f"{mid}: UNRESOLVED row is not 50/50")
        # 7. Hotspawn must never be a probability source
        for s in srcs:
            if "hotspawn" in s.get("url", "").lower() and "probability" in s.get("claim", "").lower() \
                    and "never" not in s.get("claim", "").lower():
                errors.append(f"{mid}: Hotspawn cited as probability source: {s.get('claim')}")
        # 8. flags are strings
        if not isinstance(m.get("flags"), list) or not all(isinstance(f, str) for f in m.get("flags", [])):
            errors.append(f"{mid}: malformed flags")

    # 9. declared counts reconcile
    cov = d.get("coverage", {})
    if cov.get("published_picks") != len(rows):
        errors.append("coverage.published_picks != row count")
    if d["counts"].get("resolved") != sum(1 for m in rows if m.get("resolved")):
        errors.append("counts.resolved disagrees with rows")
    if d["counts"].get("unresolved") != method_counter.get("UNRESOLVED", 0):
        errors.append("counts.unresolved disagrees with method tally")
    if cov.get("counts_by_method"):
        for k, v in cov["counts_by_method"].items():
            if method_counter.get(k, 0) != v:
                errors.append(f"counts_by_method[{k}]={v} but rows have {method_counter.get(k, 0)}")
        if sum(cov["counts_by_method"].values()) != len(rows):
            errors.append("counts_by_method does not sum to fixture total")

    # 10. excluded fixtures: reason + source, none leaks into priced rows
    excl = d.get("excluded_fixtures") or []
    priced_ids = {m["id"] for m in rows}
    for e in excl:
        if e.get("id") in priced_ids:
            errors.append(f"excluded fixture {e.get('id')} also priced")
        if not e.get("reason") or not e.get("source"):
            errors.append(f"excluded row missing reason/source: {e.get('id')}")

    # 11. probe block structural (no probabilities, https + status + verdict each)
    probe = d.get("market_probe") or {}
    books = probe.get("books") or []
    for b in books:
        if not str(b.get("url", "")).startswith("https://"):
            errors.append(f"probe row non-https: {b.get('name')}")
        if not isinstance(b.get("http_status"), int):
            errors.append(f"probe row bad status: {b.get('name')}")
        if not b.get("verdict"):
            errors.append(f"probe row missing verdict: {b.get('name')}")
        # the probe must never carry a price/probability of its own
        if any(k in b for k in ("prob", "probability", "prob_team1", "price", "odds")):
            errors.append(f"probe row carries a price/probability field: {b.get('name')}")

    print("## Method and confidence mix\n")
    print("| Method | Rows |")
    print("|---|---:|")
    for k, v in sorted(method_counter.items()):
        print(f"| `{k}` | {v} |")
    print(f"\nConfidence: {dict(conf_counter)}  ")
    print(f"Upcoming starts: {future} · already-started rows in payload: {past}  ")
    print(f"Bookmaker source citations: {n_book_sources} · Leaguepedia citations: {n_leaguepedia_sources} "
          f"· Hotspawn fixture citations: {n_hotspawn_sources}\n")

    print("## Per-competition tally (re-derived from rows)\n")
    print("| Competition | Rows | Tier labels seen |")
    print("|---|---:|---|")
    for tour, n in per_league.most_common():
        tiers = sorted({m.get("tier") or "?" for m in rows if m.get("tournament") == tour})
        print(f"| {tour} | {n} | {', '.join(tiers)} |")

    print(f"\n## Excluded fixtures ({len(excl)})\n")
    for e in excl:
        print(f"- `{e.get('id')}` {e.get('team1')} vs {e.get('team2')} — {e.get('status')}: "
              f"{e.get('reason')} (source {'present' if e.get('source') else 'MISSING'})")

    print(f"\n## External-source probe ({len(books)} rows in this payload)\n")
    reach = sum(1 for b in books if b.get("http_status") == 200)
    print(f"Reachable (HTTP 200): {reach}/{len(books)}. Every row has an https URL, integer status and "
          "an auto-generated verdict; no row carries a probability. Full table on the Unresolved page.\n")

    print("## Verdict\n")
    if errors:
        print(f"**FAIL — {len(errors)} hard invariant violation(s):**\n")
        for e in errors:
            print(f"- {e}")
        return 1
    print("**PASS** — every row satisfies the source, probability, pick and flag invariants; declared "
          "counts reconcile to the rows; excluded fixtures are sourced and never priced; the probe is "
          "structural and probability-free.")
    if notes:
        print("\nNotes:")
        for n in notes:
            print(f"- {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

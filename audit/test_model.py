#!/usr/bin/env python3
"""Offline regression tests for the parts of the pick pipeline that have silently
broken before: per-book de-duplication of market quotes, prop-board rejection,
standings-derived Elo, and the published payload's book-count invariant.

These run with no network access and no secrets. Run:  python3 audit/test_model.py
Exit code 0 = all tests passed.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from fetch_markets import _PROP_CRIT_RE, _dedup_key, _record, _select_unibet_offer  # noqa: E402
from model import METHOD_LABELS, _standings_elo, blend_h2h  # noqa: E402

PASSED: list[str] = []
FAILED: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASSED if cond else FAILED).append(f"{name}{(' — ' + detail) if detail else ''}")
    print(("  [ok]   " if cond else "  [FAIL] ") + name + (f" — {detail}" if detail else ""))


def test_dedup_key_ignores_team_order_and_time() -> None:
    """One book's board for a fixture must collapse onto one key.

    Regression: Pinnacle listed a Worlds match on up to seven child boards with
    distinct matchup ids but identical prices; before the fix each board counted
    as an independent source (source_count 9, dispersion 0.011 -> High).
    """
    a = _dedup_key("Gen.G", "Invictus Gaming", "2026-10-24T11:00:00Z")
    b = _dedup_key("Invictus Gaming", "Gen.G", "2026-10-24T09:30:00Z")
    c = _dedup_key("Gen.G", "Invictus Gaming", "2026-10-25T11:00:00Z")
    check("dedup key collapses team order + same day", a == b, f"{a} vs {b}")
    check("dedup key separates different days", a != c, f"{a} vs {c}")


def test_record_normalises_and_rejects_garbage() -> None:
    start = datetime(2026, 10, 24, 11, 0, tzinfo=timezone.utc)
    rec = _record("Pinnacle", "pinnacle", "Worlds", start, "Gen.G", "Invictus Gaming",
                  0.7355, 0.2645, "https://example.invalid/x")
    total = round(rec["prob_a"] + rec["prob_b"], 6) if rec else None
    check("record keeps a two-way line balanced", rec is not None and total == 1.0, f"sum={total}")
    check("record drops TBD participants",
          _record("Pinnacle", "pinnacle", "Worlds", start, "TBD", "Gen.G", 0.5, 0.5, "u") is None)
    check("record drops a team playing itself",
          _record("Pinnacle", "pinnacle", "Worlds", start, "Gen.G", "gen.g", 0.5, 0.5, "u") is None)


def test_prop_boards_are_rejected() -> None:
    """Kills/maps/totals boards must never become a match-winner price."""
    props = ["Gen.G (Kills)", "Map 1 Winner", "Total Kills Over/Under 24.5",
             "First Blood", "Handicap -1.5"]
    main = ["Match Odds", "Match Winner", "Full Time"]
    check("prop criteria all rejected", all(_PROP_CRIT_RE.search(p) for p in props), ", ".join(props))
    check("main-market criteria not rejected", not any(_PROP_CRIT_RE.search(m) for m in main), ", ".join(main))


def _offer(label: str, tags=None, n=2, btype_id=2):
    return {
        "betOfferType": {"id": btype_id, "englishName": "Match"},
        "criterion": {"englishLabel": label},
        "tags": tags or ["OFFERED_PREMATCH"],
        "outcomes": [{"status": "OPEN", "odds": 1.5}] * n,
    }


def test_unibet_offer_selection() -> None:
    """Only a two-way, pre-match main board may be used as a market line."""
    prop = _offer("Map 1 Winner")
    alt = _offer("Handicap -1.5")
    main = _offer("Match Odds", tags=["OFFERED_PREMATCH", "MAIN"])
    three_way = _offer("Match Odds", n=3)
    picked = _select_unibet_offer([prop, alt, main, three_way])
    check("unibet keeps the 2-way main board", picked is not None and picked.get("tags") == ["OFFERED_PREMATCH", "MAIN"])
    check("unibet rejects a prop-only book", _select_unibet_offer([prop]) is None)
    check("unibet rejects a 3-way board", _select_unibet_offer([three_way]) is None)


def test_standings_elo_direction_and_bounds() -> None:
    """A winning split record must rate above a losing one, and never explode."""
    base = 1500.0
    good = _standings_elo({"win_series": 6, "loss_series": 1, "win_games": 13, "loss_games": 4}, base)
    bad = _standings_elo({"win_series": 1, "loss_series": 6, "win_games": 4, "loss_games": 13}, base)
    empty = _standings_elo({}, base)
    check("standings elo rates a 6-1 split above base", good > base, f"{good:.1f} > {base:.0f}")
    check("standings elo rates a 1-6 split below base", bad < base, f"{bad:.1f} < {base:.0f}")
    check("standings elo with no games returns the prior", abs(empty - base) < 1e-6, f"{empty:.1f}")
    check("standings elo stays finite and bounded", -2000 < good < 2600 and -2000 < bad < 2600)


def test_h2h_blend_is_conservative() -> None:
    p, info = blend_h2h(0.6, 1, 1)
    check("h2h does not move a probability with <3 games", p == 0.6 and info is None)
    p2, info2 = blend_h2h(0.6, 6, 6, weight=0.15)
    check("h2h nudges a probability toward the head-to-head", info2 is not None and p2 > 0.6, f"{p2:.4f}")


def test_payload_book_invariant() -> None:
    """The published payload must count each book once (regression for I13)."""
    path = os.path.join(ROOT, "docs", "data", "picks.json")
    if not os.path.exists(path):
        check("payload book invariant", True, "no payload in this checkout — skipped")
        return
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    bad = []
    rows = 0
    for m in data.get("matches") or []:
        mk = m.get("market")
        if not mk:
            continue
        rows += 1
        srcs = mk.get("sources") or []
        keys = [s.get("source_key") or s.get("source") for s in srcs]
        if len(keys) != len(set(keys)) or mk.get("source_count") != len(keys):
            bad.append(f"{m.get('team1')} vs {m.get('team2')}")
    check("payload counts each book once", not bad,
          f"{rows} market row(s)" + (f", offenders: {bad[:3]}" if bad else ""))

    unknown = sorted({m.get("method") for m in data.get("matches") or []}
                     - set(METHOD_LABELS))
    check("every row uses a documented method", not unknown, f"unknown={unknown}" if unknown else "methods all documented")

    missing_src = [m.get("id") for m in data.get("matches") or []
                   if not (m.get("sources") and all(
                       str(s.get("url", "")).startswith("http") for s in m["sources"]))]
    check("every row links an absolute source URL", not missing_src,
          f"{len(data.get('matches') or [])} rows" + (f", offenders: {missing_src[:3]}" if missing_src else ""))

    bad_pick = [m.get("id") for m in data.get("matches") or []
                if m.get("pick") not in (m.get("team1"), m.get("team2"))]
    check("every pick is one of the two teams", not bad_pick,
          (f"offenders: {bad_pick[:3]}" if bad_pick else "all picks valid"))

    # --- standings blend invariants (MODEL_ELO_STANDINGS) -------------------
    rows = data.get("matches") or []
    blends = [m for m in rows if m.get("method") == "MODEL_ELO_STANDINGS"]
    bad_blend = []
    for m in blends:
        mod = m.get("model") or {}
        w1 = mod.get("standings_weight_team1") or 0.0
        w2 = mod.get("standings_weight_team2") or 0.0
        # weight must stay inside the documented [0, 0.6] band
        if not (0.0 <= w1 <= 0.6 and 0.0 <= w2 <= 0.6):
            bad_blend.append(f"{m.get('id')} weights {w1}/{w2}")
        # a blend must actually use a standings record on at least one side
        if not (mod.get("standings_team1") or mod.get("standings_team2")):
            bad_blend.append(f"{m.get('id')} no standings record")
        # a blend must be flagged so it is auditable from the Flagged page
        if "STANDINGS_BLEND_APPLIED" not in (m.get("flags") or []):
            bad_blend.append(f"{m.get('id')} missing flag")
        # confidence must never exceed Medium for a standings-based row
        if m.get("confidence") not in ("Low", "Medium"):
            bad_blend.append(f"{m.get('id')} confidence {m.get('confidence')}")
    check("standings blend invariants hold", not bad_blend,
          (f"offenders: {bad_blend[:3]}" if bad_blend else f"{len(blends)} blend row(s) ok"))

    # a standings-sourced row must link a standings source explicitly
    no_st_src = [m.get("id") for m in rows
                 if m.get("method") in ("MODEL_STANDINGS", "MODEL_ELO_STANDINGS")
                 and not any("standing" in str(s.get("name") or "").lower()
                             for s in (m.get("sources") or []))]
    check("standings rows link a standings source", not no_st_src,
          (f"offenders: {no_st_src[:3]}" if no_st_src else "all standings rows linked"))

    # a standings row must not hide behind a generic Cargo-table link only
    generic_st = [m.get("id") for m in rows
                  if m.get("method") in ("MODEL_STANDINGS", "MODEL_ELO_STANDINGS")
                  and not any("/Special:CargoTables/" not in str(s.get("url") or "")
                              for s in (m.get("sources") or []))]
    check("standings rows cite a competition-specific page", not generic_st,
          (f"offenders: {generic_st[:3]}" if generic_st else "all standings rows specific"))


def main() -> int:
    for fn in (test_dedup_key_ignores_team_order_and_time,
               test_record_normalises_and_rejects_garbage,
               test_prop_boards_are_rejected,
               test_unibet_offer_selection,
               test_standings_elo_direction_and_bounds,
               test_h2h_blend_is_conservative,
               test_payload_book_invariant):
        print(f"\n{fn.__name__}: {fn.__doc__.strip().splitlines()[0] if fn.__doc__ else ''}")
        fn()
    print(f"\n{len(PASSED)} passed · {len(FAILED)} failed")
    if FAILED:
        print("FAILED: " + " | ".join(FAILED))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

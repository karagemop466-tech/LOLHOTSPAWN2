#!/usr/bin/env python3
"""Unit tests for standings_and_books.py, entity_resolution.py, and model deduplication."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from standings_and_books import (  # noqa: E402
    build_standings_index,
    is_pinnacle_main_matchup,
    standings_probability,
)
from model import Resolver, contains, load_aliases  # noqa: E402
from entity_resolution import (  # noqa: E402
    build_page_rosters,
    build_tournament_page_map,
    discover_schedule_bridges,
    resolve_team_in_context,
    strip_disambig,
)


def main() -> int:
    checks: list[tuple[str, bool]] = []

    def check(name: str, ok: bool) -> None:
        print(f"  [{'ok' if ok else 'FAILED'}] {name}")
        checks.append((name, ok))

    # 1. Pinnacle child-board / prop filtering
    main_board = {
        "id": 1001,
        "parentId": None,
        "units": "Regular",
        "type": "matchup",
        "participants": [
            {"name": "Bilibili Gaming", "alignment": "home"},
            {"name": "Movistar KOI", "alignment": "away"},
        ],
    }
    child_prop = {
        "id": 1002,
        "parentId": 1001,
        "units": "Kills",
        "type": "matchup",
        "participants": [
            {"name": "Bilibili Gaming", "alignment": "home"},
            {"name": "Movistar KOI", "alignment": "away"},
        ],
    }
    baron_prop = {
        "id": 1003,
        "parentId": None,
        "units": "First Baron",
        "type": "matchup",
        "participants": [
            {"name": "Gen.G", "alignment": "home"},
            {"name": "Invictus Gaming", "alignment": "away"},
        ],
    }
    check("pinnacle main matchup accepted", is_pinnacle_main_matchup(main_board))
    check("pinnacle child parentId board rejected", not is_pinnacle_main_matchup(child_prop))
    check("pinnacle First Baron units board rejected", not is_pinnacle_main_matchup(baron_prop))

    # 2. Disambiguation stripping + contextual roster resolution
    check("strip_disambig LYON", strip_disambig("LYON (2024 American Team)") == "LYON")
    check("strip_disambig Locked In", strip_disambig("Locked In (Dutch Team)") == "Locked In")

    sched = [
        {"overview": "Prime League 2nd Division/2027 Season/Fall Split",
         "team1": "PvB (Swiss Team)", "team2": "Locked In (Dutch Team)",
         "start_utc": "2026-10-25T17:00:00Z"},
        {"overview": "Prime League 2nd Division/2027 Season/Fall Split",
         "team1": "Team Orange Gaming", "team2": "PvB (Swiss Team)",
         "start_utc": "2026-10-28T18:00:00Z"},
        {"overview": "Prime League 2nd Division/2027 Season/Fall Split",
         "team1": "reGOLD eSport", "team2": "Team Orange Gaming",
         "start_utc": "2026-10-26T17:00:00Z"},
        {"overview": "Prime League 2nd Division/2027 Season/Fall Split",
         "team1": "Locked In (Dutch Team)", "team2": "reGOLD eSport",
         "start_utc": "2026-10-29T18:00:00Z"},
    ]
    fixtures = [
        {"id": "1", "tournament": "PRM 2nd Division 26-27 Fall",
         "team1": "Phong Vũ Buffalo", "team2": "Locked IN", "start_utc": "2026-10-25T17:00:00Z"},
        {"id": "2", "tournament": "PRM 2nd Division 26-27 Fall",
         "team1": "Team Orange Gaming", "team2": "Phong Vũ Buffalo", "start_utc": "2026-10-28T18:00:00Z"},
        {"id": "3", "tournament": "PRM 2nd Division 26-27 Fall",
         "team1": "ex-A41G", "team2": "Team Orange Gaming", "start_utc": "2026-10-26T17:00:00Z"},
        {"id": "4", "tournament": "PRM 2nd Division 26-27 Fall",
         "team1": "Locked IN", "team2": "ex-A41G", "start_utc": "2026-10-29T18:00:00Z"},
    ]
    tmap = build_tournament_page_map(fixtures, sched)
    rosters = build_page_rosters([], sched)
    all_norms = {"phongvubuffalo", "pvbswissteam", "lockedindutchteam", "teamorangegaming", "regoldesport"}
    bridges = discover_schedule_bridges(fixtures, sched, tmap, rosters, all_norms)
    pvb_b = bridges.get(("PRM 2nd Division 26-27 Fall", "phongvubuffalo"))
    a41_b = bridges.get(("PRM 2nd Division 26-27 Fall", "exa41g"))
    li_res = resolve_team_in_context(
        "Locked IN", tmap["PRM 2nd Division 26-27 Fall"],
        rosters, {}, {}, lambda x: None
    )
    check("Phong Vũ Buffalo bridges to PvB (Swiss Team)", bool(pvb_b and pvb_b["leaguepedia_name"] == "PvB (Swiss Team)" and pvb_b["entity_mismatch"]))
    check("ex-A41G bridges to reGOLD eSport", bool(a41_b and a41_b["leaguepedia_name"] == "reGOLD eSport"))
    check("Locked IN resolves contextually to Locked In (Dutch Team)", li_res == "Locked In (Dutch Team)")

    # 3. Standings probability model
    st_rows = [
        {"overview": "Prime League 3rd Division/2027 Season/Fall Split", "team": "REH Gaming",
         "win_series": 2, "loss_series": 0, "win_games": 4, "loss_games": 0},
        {"overview": "Prime League 3rd Division/2027 Season/Fall Split", "team": "LOOKSMAXXER",
         "win_series": 0, "loss_series": 2, "win_games": 0, "loss_games": 4},
        {"overview": "Prime League 3rd Division/2027 Season/Fall Split", "team": "Zero Team",
         "win_series": 0, "loss_series": 0, "win_games": 0, "loss_games": 0},
    ]
    st_idx = build_standings_index(st_rows)
    p_reh, meta = standings_probability(
        st_idx.get(("Prime League 3rd Division/2027 Season/Fall Split", "rehgaming")),
        st_idx.get(("Prime League 3rd Division/2027 Season/Fall Split", "looksmaxxer")),
    )
    p_zero, _ = standings_probability(
        st_idx.get(("Prime League 3rd Division/2027 Season/Fall Split", "rehgaming")),
        st_idx.get(("Prime League 3rd Division/2027 Season/Fall Split", "zeroteam")),
    )
    check("standings model prices 2-0 vs 0-2 > 0.55", p_reh is not None and p_reh > 0.55 and meta is not None)
    check("0-0 standings entries rejected", p_zero is None)

    # 4. Inari Esports -> Inari Esports (British Team) (never 4-char SEA tag NARI)
    aliases = load_aliases(os.path.join(ROOT, "data", "aliases.json"))
    res_inari = Resolver(["NARI", "Inari Esports (British Team)", "Bulldog Esports"], {})
    check("short 4-char tag NARI does not substring-match Inari Esports",
          not contains("Inari Esports", "NARI"))
    check("Inari Esports stripped-parenthetical beats short substring NARI",
          res_inari.resolve("Inari Esports") == "Inari Esports (British Team)")
    check("tournament_pages maps 4 Nations 2026 Halloween Heist & Komplettligaen Playoffs",
          aliases["tournament_pages"].get("4 Nations 2026 Halloween Heist") == "4 Nations/2026 Season/Halloween Heist"
          and aliases["tournament_pages"].get("Komplettligaen 2026 Autumn Playoffs") == "Komplettligaen/2026 Season/Autumn Playoffs")

    # 5. Bovada series-moneyline period handling (regression: period "Game"
    # with main=true is the full-series market; numbered periods are not).
    import json as _json

    from fetch_markets import _bovada_groups, _bovada_series_moneyline, _parse_bovada_groups

    def _mk(period_desc, main=True):
        return {"description": "Moneyline",
                "period": {"description": period_desc, "main": main},
                "outcomes": [{"description": "A"}, {"description": "B"}]}

    check("bovada Game/main moneyline accepted as series", _bovada_series_moneyline(_mk("Game")))
    check("bovada Game 1 moneyline rejected", not _bovada_series_moneyline(_mk("Game 1")))
    check("bovada Map 1 moneyline rejected", not _bovada_series_moneyline(_mk("Map 1")))
    snap = os.path.join(ROOT, "data", "diag", "bovada_prematch.json")
    if os.path.exists(snap):
        with open(snap, encoding="utf-8") as fh:
            recs, _comps, seen = _parse_bovada_groups(_bovada_groups(_json.load(fh)))
        check("bovada coupon snapshot replays to records (9 events)",
              seen == 9 and len(recs) == 9
              and all(abs(r["prob_a"] + r["prob_b"] - 1) < 0.005 for r in recs)
              and all((r.get("raw") or {}).get("market_type") == "series" for r in recs))
    else:
        check("bovada coupon snapshot replays to records (9 events)", False)

    # ---- Kalshi (regulated exchange) match-winner parsing ----------------- #
    from fetch_markets import _kalshi_start, _slug, fetch_kalshi

    # Live shape, read from api.elections.kalshi.com on 2026-10-25 (G2 vs Top
    # Esports, Worlds 2026). yes bid/ask are dollars per contract.
    def _kalshi_event(ticker, title, ta, ta_bid, ta_ask, tb, tb_bid, tb_ask,
                      rules, occurrence):
        return {"event_ticker": ticker, "title": title, "series_ticker": "KXLOLGAME",
                "markets": [
                    {"yes_sub_title": ta, "yes_bid_dollars": ta_bid,
                     "yes_ask_dollars": ta_ask, "occurrence_datetime": occurrence,
                     "volume_fp": "1000", "rules_primary": rules},
                    {"yes_sub_title": tb, "yes_bid_dollars": tb_bid,
                     "yes_ask_dollars": tb_ask, "occurrence_datetime": occurrence,
                     "volume_fp": "900", "rules_primary": rules},
                ]}

    live = {"events": [
        _kalshi_event(
            "KXLOLGAME-26OCT251300G2TES", "G2 Esports vs Top Esports",
            "G2 Esports", "0.5300", "0.5400", "Top Esports", "0.4600", "0.4700",
            "If G2 Esports wins the Worlds 2026: G2 Esports vs. Top Esports League of "
            "Legends match originally scheduled for Oct 25, 2026 at 1:00 PM EDT, then "
            "the market resolves to Yes.",
            "2026-10-25T21:00:00Z"),
        _kalshi_event(
            "KXLOLGAME-26OCT261800ALTL", "Anyone's Legend vs. Team Liquid",
            "Team Liquid", "0.3000", "0.3200", "Anyone's Legend", "0.6800", "0.6900",
            "If Team Liquid wins the Worlds 2026: Anyone's Legend vs. Team Liquid "
            "League of Legends match originally scheduled for Oct 26, 2026 at 6:00 PM "
            "EDT, then the market resolves to Yes.",
            "2026-10-27T02:00:00Z"),
        # an event with no two-sided market must be skipped, not half-parsed
        {"event_ticker": "KXLOLGAME-26OCT251400IGHLE", "title": "IG vs HLE",
         "series_ticker": "KXLOLGAME", "markets": []},
    ]}

    import fetch_markets as _fm
    _orig_get_json, _orig_write = _fm.get_json, _fm.write_json
    _fm.get_json = lambda url, **kw: (live, {"status": 200, "text": "{}"})
    _fm.write_json = lambda *a, **kw: None
    try:
        out = _fm.fetch_kalshi()
        recs = out["records"]
    finally:
        _fm.get_json, _fm.write_json = _orig_get_json, _orig_write

    check("kalshi status ok with 2 records (empty event skipped)",
          out["status"]["status"] == "ok" and out["status"]["count"] == 2 and len(recs) == 2)
    check("kalshi probabilities are de-vigged to 1.0",
          all(abs(r["prob_a"] + r["prob_b"] - 1) < 0.001 for r in recs))
    check("kalshi mid prices match the live read (G2 53.5% / TES 46.5%)",
          abs(recs[0]["prob_a"] - 0.535) < 0.001 and abs(recs[0]["prob_b"] - 0.465) < 0.001)
    check("kalshi decimal odds are the reciprocal of the probability",
          abs(recs[0]["decimal_a"] - round(1 / 0.535, 4)) < 0.001)
    # The rules text is the real start; occurrence_datetime runs 4 h ahead.
    check("kalshi start parsed from the rules text, not occurrence_datetime",
          recs[0]["start_utc"] == "2026-10-25T17:00:00Z"
          and recs[1]["start_utc"] == "2026-10-26T22:00:00Z")
    check("kalshi competition taken from the rules text (Worlds 2026)",
          recs[0]["competition"] == "Kalshi: Worlds 2026")
    check("kalshi market_type is a series board, never a child game/map prop",
          all((r.get("raw") or {}).get("market_type") == "series" for r in recs))
    check("kalshi record url is the public market page",
          recs[0]["url"] == "https://kalshi.com/markets/g2-esports-vs-top-esports/"
                            "kxlolgame-26oct251300g2tes")
    check("kalshi _slug collapses punctuation", _slug("Anyone's Legend vs. Team Liquid")
          == "anyone-s-legend-vs-team-liquid")
    check("kalshi EDT start offset", _kalshi_start(
        {"rules_primary": "x originally scheduled for Nov 1, 2026 at 9:30 PM EST, then y",
         "occurrence_datetime": "2026-11-02T05:00:00Z"}).isoformat()
        == "2026-11-02T02:30:00+00:00")
    check("kalshi falls back to occurrence_datetime when rules carry no stamp",
          _kalshi_start({"rules_primary": "", "occurrence_datetime": "2026-10-25T21:00:00Z"})
          .isoformat() == "2026-10-25T21:00:00+00:00")
    # Replay the committed live snapshot when one exists (same pattern as Bovada).
    snap = os.path.join(ROOT, "data", "diag", "kalshi_lol.json")
    if os.path.exists(snap):
        import json as _json
        with open(snap, encoding="utf-8") as fh:
            saved = _json.load(fh)
        saved_recs = saved.get("records") or []
        check("kalshi live snapshot replays with two-way prices summing to 1",
              bool(saved_recs) and all(abs(r["prob_a"] + r["prob_b"] - 1) < 0.005
                                       for r in saved_recs))

    passed = sum(1 for _, ok in checks if ok)
    print(f"\n{passed}/{len(checks)} entity & sportsbook unit tests passed")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())

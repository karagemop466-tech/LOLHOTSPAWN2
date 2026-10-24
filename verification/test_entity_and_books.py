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
    liquipedia_search_prefix,
    standings_probability,
)
from update_picks import liquipedia_page_for  # noqa: E402
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

    # 6. Liquipedia lookups: league terms from Hotspawn labels, strict page match
    check("Liquipedia search terms strip the Hotspawn season/stage tail",
          liquipedia_search_prefix("PRM 3rd Division 26-27 Fall") == "PRM 3rd Division"
          and liquipedia_search_prefix("RIVALS LEAGUE Season 2") == "RIVALS LEAGUE"
          and liquipedia_search_prefix("Worlds 2026 Main Event") == "Worlds"
          and liquipedia_search_prefix("") == "")
    liq_cases = [
        ("RIVALS LEAGUE Season 2",
         {"RIVALS LEAGUE": ["RIVALS LEAGUE/Season 1", "RIVALS LEAGUE/Season 2"]},
         "https://liquipedia.net/leagueoflegends/RIVALS_LEAGUE/Season_2"),
        ("Arabian League 2nd Division 2026 Summer",
         {"Arabian League 2nd Division 2026": [
             "Arabian League/2nd Division/2026/Spring",
             "Arabian League/2nd Division/2026/Summer",
             "Arabian League/2nd Division/2026/Spring/Open Qualifier"]},
         "https://liquipedia.net/leagueoflegends/Arabian_League/2nd_Division/2026/Summer"),
        ("Komplettligaen 2026 Autumn Playoffs",
         {"Komplettligaen 2026": ["Komplettligaen/2026/Playoffs",
                                  "Komplettligaen/2026/Autumn",
                                  "Komplettligaen/2026/Spring"]},
         "https://liquipedia.net/leagueoflegends/Komplettligaen/2026/Autumn"),
        ("LCP 2027 Promotion",
         {"LCP 2027": ["LCP/2027/Promotion", "LCP/2027/Promotion/Wild Card Playoffs"]},
         "https://liquipedia.net/leagueoflegends/LCP/2027/Promotion"),
        # refused: wrong split, wrong year, lookalike league, no page
        ("Komplettligaen 2026 Autumn Playoffs",
         {"Komplettligaen 2026": ["Komplettligaen/2026/Playoffs",
                                  "Komplettligaen/2026/Spring"]}, None),
        ("4 Nations 2026 Halloween Heist",
         {"4 Nations 2026": ["4 Nations/2026/Summer", "4 Nations/2026/Spring"]}, None),
        ("LGC Rising 2026 Playoffs", {"LGC Rising 2026": ["LGC/2025/Rising"]}, None),
        ("PRM 3rd Division 26-27 Fall",
         {"PRM 3rd Division": ["Prime League/2023/Pokal"]}, None),
        ("Worlds 2026 Main Event",
         {"Worlds 2026": ["2026 Season World Championship"]}, None),
        ("Tunisian Super League 2026", {}, None),
    ]
    bad = [(label, liquipedia_page_for(label, pages), want)
           for label, pages, want in liq_cases
           if liquipedia_page_for(label, pages) != want]
    check("Liquipedia links only the page that matches the whole label", not bad)
    if bad:
        print("      refused/accepted wrong:", bad)

    passed = sum(1 for _, ok in checks if ok)
    print(f"\n{passed}/{len(checks)} entity & sportsbook unit tests passed")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())

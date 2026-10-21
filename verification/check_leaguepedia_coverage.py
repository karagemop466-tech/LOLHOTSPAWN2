#!/usr/bin/env python3
"""
check_leaguepedia_coverage.py — per-fixture "is this resolvable from an official
results source?" audit for the unresolved (50/50) rows.

Input: a Leaguepedia MatchSchedule snapshot (JSON list of rows with Team1, Team2,
DateTime UTC, OverviewPage, BestOf, Tab). Get it with the Cargo API:

  https://lol.fandom.com/api.php?action=cargoquery&format=json&tables=MatchSchedule
    &fields=MatchSchedule.Team1,MatchSchedule.Team2,MatchSchedule.DateTime_UTC,
            MatchSchedule.OverviewPage,MatchSchedule.BestOf,MatchSchedule.Tab
    &where=MatchSchedule.DateTime_UTC >= '<now>'&order_by=MatchSchedule.DateTime_UTC ASC
    &limit=500

Output: verification/leaguepedia_coverage.json + a markdown summary.
The mapping from Hotspawn tournament names to Leaguepedia overview pages was
verified by hand on 2026-10-21 against the schedule snapshot (see research/betting-sources.md).
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIKI = "https://lol.fandom.com/wiki/"

# Hotspawn tournament -> Leaguepedia OverviewPage(s). Verified 2026-10-21.
LEAGUE_MAP = {
    "Worlds 2026 Main Event": ["2026 Season World Championship/Main Event"],
    "EM 2026 Summer Main Event": ["EMEA Masters/2026 Season/Summer Main Event"],
    "LCP 2027 Promotion": ["LCP/2027 Season/Promotion"],
    "PRM 2nd Division 26-27 Fall": ["Prime League 2nd Division/2027 Season/Fall Split"],
    "PRM 3rd Division 26-27 Fall": ["Prime League 3rd Division/2027 Season/Fall Split"],
    "RIVALS LEAGUE Season 2": ["RIVALS LEAGUE/2026 Season/Season 2",
                               "RIVALS LEAGUE/2026 Season/Season 2 Playoffs"],
    "4 Nations 2026 Halloween Heist": ["4 Nations/2026 Season/Halloween Heist"],
    "Tunisian Super League 2026": ["Tunisian Super League/2026 Season"],
    "Komplettligaen 2026 Autumn": ["Komplettligaen/2026 Season/Autumn Split"],
    "LigaGG CELOL B 2026 Split 2 Playoffs": ["LigaGG/CELOL Série B/2026 Season/Split 2 Playoffs"],
    "Arabian League 2nd Division 2026 Summer": ["Arabian League 2nd Division/2026 Season/Summer Split"],
    "Arabian Regional Championship 2026: Lebanon-Libya-Syria-Palestine":
        ["Arabian Regional Championship 2026/Qualifiers/LB-Li-SY-PS"],
    "LGC Rising 2026 Playoffs": ["LoL Game Changers/2026 Season/Playoffs"],  # candidate, unverified
}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--schedule", default=os.path.join(ROOT, "data", "diag", "lp_schedule.json"))
    ap.add_argument("--schedule-dir", default="",
                    help="directory of MatchSchedule json snapshots to merge (e.g. data/diag)")
    ap.add_argument("--picks", default=os.path.join(ROOT, "docs", "data", "picks.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "verification", "leaguepedia_coverage.json"))
    ap.add_argument("--md", default=os.path.join(ROOT, "verification", "leaguepedia_coverage.md"))
    ap.add_argument("--rows", choices=["unresolved", "model", "all"], default="all")
    args = ap.parse_args()

    rows = json.load(open(args.picks, encoding="utf-8")).get("matches", [])
    if args.schedule_dir:
        schedule = []
        for fn in sorted(os.listdir(args.schedule_dir)):
            if not fn.endswith(".json") or not fn.startswith("ms_"):
                continue
            try:
                part = json.load(open(os.path.join(args.schedule_dir, fn), encoding="utf-8"))
            except Exception:
                continue
            if isinstance(part, dict):
                part = part.get("cargoquery") or part.get("rows") or []
            if isinstance(part, list):
                schedule += part
    else:
        schedule = json.load(open(args.schedule, encoding="utf-8"))
        if isinstance(schedule, dict):  # tolerate {"cargoquery":[{"title":{...}}]} shapes
            schedule = schedule.get("cargoquery") or schedule.get("rows") or []
    sched = []
    for r in schedule:
        r = r.get("title", r) if isinstance(r, dict) else r
        if isinstance(r, dict):
            sched.append({
                "t1": r.get("Team1") or r.get("team1") or "",
                "t2": r.get("Team2") or r.get("team2") or "",
                "page": r.get("OverviewPage") or r.get("overviewpage") or "",
                "start": r.get("DateTime UTC") or r.get("DateTime_UTC") or "",
                "bestof": r.get("BestOf") or r.get("bestof"),
                "tab": r.get("Tab") or r.get("tab") or "",
            })

    by_page: dict[str, list[dict]] = {}
    for r in sched:
        by_page.setdefault(r["page"], []).append(r)

    if args.rows == "unresolved":
        rows = [m for m in rows if m.get("method") == "UNRESOLVED"]
    elif args.rows == "model":
        rows = [m for m in rows if not str(m.get("method", "")).startswith("MARKET")]
    results, unresolved = [], [m for m in rows if m.get("method") == "UNRESOLVED"]
    for m in rows:
        tour = (m.get("tournament") or "").strip()
        pages = LEAGUE_MAP.get(tour, [])
        n1, n2 = norm(m["team1"]), norm(m["team2"])
        hit_page, hit_fixture, sample = None, None, None
        for p in pages:
            for r in by_page.get(p, []):
                if {n1, n2} == {norm(r["t1"]), norm(r["t2"])}:
                    hit_page, hit_fixture, sample = p, r, r
                    break
            if hit_fixture:
                break
        if not hit_fixture:
            for p in pages:
                if by_page.get(p):
                    hit_page = p
                    break
        claimed = (m.get("leaguepedia_page") or "").strip()
        if not hit_page and not claimed:
            u = m.get("leaguepedia_url") or ""
            if "/wiki/" in u:
                claimed = u.split("/wiki/", 1)[1].replace("_", " ")
        if not hit_page and claimed and not by_page.get(claimed):
            hit_page = claimed
            status_override = "CLAIMED_PAGE"
        else:
            status_override = None
        results.append({
            "team1": m["team1"], "team2": m["team2"], "tournament": tour,
            "method": m.get("method"), "start_utc": m.get("start_utc"),
            "leaguepedia_page": hit_page,
            "leaguepedia_url": (WIKI + hit_page.replace(" ", "_")) if hit_page else None,
            "schedule_fixture_found": bool(hit_fixture),
            "schedule_row": sample,
            "status": (status_override or
                       ("MATCHED_FIXTURE" if hit_fixture else
                        "LEAGUE_PAGE_ONLY" if hit_page else "NO_SOURCE")),
        })

    summary = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "schedule_rows": len(sched),
        "schedule_pages": sorted(by_page),
        "matches": len(rows),
        "unresolved": len(unresolved),
        "audited_rows": len(results),
        "matched_fixture": sum(1 for r in results if r["status"] == "MATCHED_FIXTURE"),
        "league_page_only": sum(1 for r in results if r["status"] == "LEAGUE_PAGE_ONLY"),
        "claimed_page": sum(1 for r in results if r["status"] == "CLAIMED_PAGE"),
        "no_source": sum(1 for r in results if r["status"] == "NO_SOURCE"),
        "by_tournament": {},
    }
    for r in results:
        if args.rows == "unresolved" and r["method"] != "UNRESOLVED":
            continue
        b = summary["by_tournament"].setdefault(
            r["tournament"], {"rows": 0, "fixture": 0, "page": 0, "none": 0, "url": r["leaguepedia_url"]})
        b["rows"] += 1
        b[{"MATCHED_FIXTURE": "fixture", "LEAGUE_PAGE_ONLY": "page",
           "CLAIMED_PAGE": "page", "NO_SOURCE": "none"}[r["status"]]] += 1

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump({"summary": summary, "rows": results}, open(args.out, "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)

    md = ["# Leaguepedia coverage audit", "",
          f"_{summary['checked_at']}_ · schedule rows: {summary['schedule_rows']} · "
          f"pages: {len(summary['schedule_pages'])}", "",
          f"**{summary['audited_rows']} audited rows** ({args.rows}) → "
          f"{summary['matched_fixture']} have the exact fixture on a Leaguepedia league page, "
          f"{summary['league_page_only']} have the league page only, "
          f"{summary['claimed_page']} cite a page not present in this snapshot, "
          f"{summary['no_source']} have no Leaguepedia page at all.", "",
          "| Hotspawn tournament | rows | fixture matched | league page only | no source | Leaguepedia page |",
          "|---|---|---|---|---|---|"]
    for t, b in sorted(summary["by_tournament"].items(), key=lambda kv: -kv[1]["rows"]):
        md.append(f"| {t} | {b['rows']} | {b['fixture']} | {b['page']} | {b['none']} | {b['url'] or '—'} |")
    md += ["", "## Rows with no Leaguepedia source", ""]
    none = [r for r in results if r["status"] == "NO_SOURCE"]
    md += [f"- {r['team1']} vs {r['team2']} — {r['tournament']}" for r in none] or ["- none"]
    open(args.md, "w", encoding="utf-8").write("\n".join(md) + "\n")

    print(json.dumps({k: v for k, v in summary.items() if k != "by_tournament"}, indent=1))
    for t, b in sorted(summary["by_tournament"].items(), key=lambda kv: -kv[1]["rows"]):
        print(f"  {b['rows']:3}  fixture={b['fixture']:3} page={b['page']:3} none={b['none']:3}  {t}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Competition-aware team disambiguation, schedule bridging, and tournament mapping.

Why this module exists:
  1. Amateur & international team names collide across regions and eras:
       * 'Rich Gang' appears in Prime League 3rd Division & Komplettligaen as
         'Rich Gang (Norwegian Team)', in RIVALS League as 'Rich Gang Sweden',
         and in 4 Nations as 'Rich Gang UK'.
       * 'LYON' at Worlds 2026 Main Event is 'LYON (2024 American Team)' on
         Leaguepedia (not bare 'LYON').
       * Hotspawn's upstream feed occasionally resolves short tags to defunct or
         renamed teams (e.g. 'Phong Vũ Buffalo' in German PRM 2nd Division 26-27
         Fall, where Leaguepedia's official schedule lists 'PvB (Swiss Team)',
         and 'ex-A41G', where Leaguepedia's official schedule lists 'reGOLD eSport').
  2. Amateur leagues flex-schedule matches across days within a matchweek, so a
     36-hour window misses valid schedule rows on the exact same tournament page.

Every resolution step is deterministic, competition-scoped, backed by an official
Leaguepedia tournament page URL, and explicitly flagged whenever schedule bridging
or upstream entity mismatch correction occurs.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime
from difflib import SequenceMatcher

from lib_common import norm

# Verified Hotspawn competition -> Leaguepedia OverviewPage seed map.
# New splits are ALSO learned dynamically from matched MatchSchedule rows.
TOURNAMENT_PAGE_SEEDS = {
    "Worlds 2026 Main Event": "2026 Season World Championship/Main Event",
    "EM 2026 Summer Main Event": "EMEA Masters/2026 Season/Summer Main Event",
    "PRM 2nd Division 26-27 Fall": "Prime League 2nd Division/2027 Season/Fall Split",
    "PRM 3rd Division 26-27 Fall": "Prime League 3rd Division/2027 Season/Fall Split",
    "RIVALS LEAGUE Season 2": "RIVALS LEAGUE/2026 Season/Season 2",
    "Tunisian Super League 2026": "Tunisian Super League/2026 Season",
    "Komplettligaen 2026 Autumn": "Komplettligaen/2026 Season/Autumn Split",
    "4 Nations 2026 Halloween Heist": "4 Nations/2026 Season/Halloween Heist",
    "Arabian League 2nd Division 2026 Summer": "Arabian League 2nd Division/2026 Season/Summer Split",
    "LigaGG CELOL B 2026 Split 2 Playoffs": "LigaGG/CELOL Série B/2026 Season/Split 2",
    "LigaGG CELOL A 2026 Split 2 Playoffs": "LigaGG/CELOL Série A/2026 Season/Split 2",
    "LCP 2027 Promotion": "LCP/2027 Season/Promotion",
    "LGC Rising 2026 Playoffs": "LGC Rising/2026 Season/Playoffs",
}

PARENTHETICAL_RE = re.compile(r"\s*\([^)]*\)\s*$")


def strip_disambig(name: str) -> str:
    """Strip Leaguepedia trailing disambiguator e.g. 'LYON (2024 American Team)' -> 'LYON'."""
    return PARENTHETICAL_RE.sub("", str(name or "")).strip()


def sim(a: str, b: str) -> float:
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def names_match_in_competition(hs_name: str, lp_name: str) -> bool:
    """Strict name equivalence when comparing within a known tournament."""
    if not hs_name or not lp_name:
        return False
    nh, nl = norm(hs_name), norm(lp_name)
    if nh == nl:
        return True
    nl_base = norm(strip_disambig(lp_name))
    if nl_base and nh == nl_base:
        return True
    if sim(hs_name, lp_name) >= 0.90 or (nl_base and sim(hs_name, strip_disambig(lp_name)) >= 0.92):
        return True
    return False


def build_tournament_page_map(fixtures: list[dict], schedule_rows: list[dict]) -> dict[str, str]:
    """Map every Hotspawn tournament to its verified Leaguepedia OverviewPage."""
    mapping = dict(TOURNAMENT_PAGE_SEEDS)
    votes: dict[str, Counter] = defaultdict(Counter)
    for f in fixtures or []:
        tour = f.get("tournament") or ""
        if not tour:
            continue
        try:
            fstart = datetime.fromisoformat(f["start_utc"].replace("Z", "+00:00"))
        except Exception:
            continue
        for r in schedule_rows or []:
            page = r.get("overview") or ""
            if not page:
                continue
            try:
                when = datetime.fromisoformat(r["start_utc"].replace("Z", "+00:00"))
            except Exception:
                continue
            if abs((when - fstart).total_seconds()) > 36 * 3600:
                continue
            if ((names_match_in_competition(f["team1"], r["team1"]) and
                 names_match_in_competition(f["team2"], r["team2"])) or
                (names_match_in_competition(f["team1"], r["team2"]) and
                 names_match_in_competition(f["team2"], r["team1"]))):
                votes[tour][page] += 1
    for tour, counter in votes.items():
        if counter:
            mapping[tour] = counter.most_common(1)[0][0]
    return mapping


def build_page_rosters(results: list[dict], schedule_rows: list[dict]) -> dict[str, set[str]]:
    """Collect canonical Leaguepedia team spellings observed on each OverviewPage."""
    rosters: dict[str, set[str]] = defaultdict(set)
    for r in (results or []) + (schedule_rows or []):
        page = r.get("overview") or ""
        if not page:
            continue
        if r.get("team1"):
            rosters[page].add(str(r["team1"]).strip())
        if r.get("team2"):
            rosters[page].add(str(r["team2"]).strip())
    return rosters


def resolve_team_in_context(name: str, page: str, page_rosters: dict[str, set[str]],
                            all_names_by_base: dict[str, list[str]],
                            recent_games: dict[str, int],
                            fallback_resolver) -> str | None:
    """Resolve a team name preferring:
      1. Exact or stripped-parenthetical match inside the target competition roster.
      2. Unique or most-active recent team sharing exact stripped base name (e.g.
         'LYON' -> 'LYON (2024 American Team)', 'Locked IN' -> 'Locked In (Dutch Team)').
      3. Standard global resolver fallback.
    """
    if not name:
        return None
    roster = page_rosters.get(page or "", set())
    if roster:
        exact = [x for x in roster if norm(x) == norm(name)]
        if len(exact) == 1:
            return exact[0]
        stripped = [x for x in roster if norm(strip_disambig(x)) == norm(name)]
        if len(stripped) == 1:
            return stripped[0]
        fuzzy = sorted(((sim(name, x), x) for x in roster), reverse=True)
        if fuzzy and fuzzy[0][0] >= 0.90:
            return fuzzy[0][1]

    # Disambiguated Leaguepedia pages whose base name equals `name`
    cands = all_names_by_base.get(norm(name), [])
    if len(cands) == 1:
        return cands[0]
    if len(cands) > 1:
        # Prefer candidates with active games in the last 365 days; only accept if
        # there is a single clearly active team (avoids cross-country ambiguity).
        ranked = sorted(cands, key=lambda c: (recent_games.get(norm(c), 0), norm(c) == norm(name)), reverse=True)
        g_top = recent_games.get(norm(ranked[0]), 0)
        g_second = recent_games.get(norm(ranked[1]), 0)
        if g_top >= 3 and g_second == 0:
            return ranked[0]

    return fallback_resolver(name)


def discover_schedule_bridges(fixtures: list[dict], schedule_rows: list[dict],
                              tour_pages: dict[str, str],
                              page_rosters: dict[str, set[str]],
                              all_lp_norms: set[str]) -> dict[tuple[str, str], dict]:
    """Identify upstream Hotspawn team names (rebrands or wrong-entity tag collisions)
    via unanimous exact-timestamp schedule slot matching within the verified tournament page.

    Requires >= 2 independent exact-timestamp (+/- 30 min) schedule matches against
    distinct verified opponents on the exact same OverviewPage with zero conflicts.
    """
    sched_by_page: dict[str, list[dict]] = defaultdict(list)
    for r in schedule_rows or []:
        if r.get("overview"):
            sched_by_page[r["overview"]].append(r)

    evidence: dict[tuple[str, str], list[tuple[str, str, str]]] = defaultdict(list)
    for f in fixtures or []:
        tour = f.get("tournament") or ""
        page = tour_pages.get(tour)
        if not page or page not in sched_by_page:
            continue
        roster = page_rosters.get(page, set())
        t1, t2 = f["team1"], f["team2"]
        in1 = any(names_match_in_competition(t1, rname) for rname in roster)
        in2 = any(names_match_in_competition(t2, rname) for rname in roster)
        if in1 == in2:
            continue  # either both already known in roster, or neither known
        unknown = t2 if in1 else t1
        known = t1 if in1 else t2
        try:
            fstart = datetime.fromisoformat(f["start_utc"].replace("Z", "+00:00"))
        except Exception:
            continue
        for r in sched_by_page[page]:
            try:
                when = datetime.fromisoformat(r["start_utc"].replace("Z", "+00:00"))
            except Exception:
                continue
            if abs((when - fstart).total_seconds()) > 1800:
                continue
            if names_match_in_competition(known, r["team1"]) and not names_match_in_competition(known, r["team2"]):
                evidence[(tour, unknown)].append((r["team2"], known, r["start_utc"]))
            elif names_match_in_competition(known, r["team2"]) and not names_match_in_competition(known, r["team1"]):
                evidence[(tour, unknown)].append((r["team1"], known, r["start_utc"]))

    bridges: dict[tuple[str, str], dict] = {}
    for (tour, hs_team), hits in evidence.items():
        distinct_targets = {h[0] for h in hits}
        distinct_opponents = {norm(h[1]) for h in hits}
        if len(distinct_targets) == 1 and len(distinct_opponents) >= 2:
            target = next(iter(distinct_targets))
            page = tour_pages[tour]
            entity_collision = (norm(hs_team) in all_lp_norms and norm(hs_team) != norm(strip_disambig(target)))
            bridges[(tour, norm(hs_team))] = {
                "hotspawn_name": hs_team,
                "leaguepedia_name": target,
                "overview": page,
                "exact_slot_matches": len(distinct_opponents),
                "entity_mismatch": entity_collision,
                "note": (f"Hotspawn '{hs_team}' bridged to Leaguepedia '{target}' via "
                         f"{len(distinct_opponents)} exact UTC schedule slots on {page}."),
            }
    return bridges


def match_fixture_to_schedule_contextual(fixture: dict, schedule_rows: list[dict],
                                         page_hint: str, k1: str | None, k2: str | None):
    """Match a Hotspawn fixture to its Leaguepedia schedule row using resolved names.

    Pass 1: within +/-36h across all schedule rows (exact timestamp proximity wins).
    Pass 2: within +/-21d restricted strictly to `page_hint` (captures flex-scheduled
            amateur matches moved within the split while preserving START_TIME_MISMATCH).
    """
    start = datetime.fromisoformat(fixture["start_utc"].replace("Z", "+00:00"))
    cand1 = {norm(fixture["team1"]), norm(strip_disambig(k1 or "")), norm(k1 or "")} - {""}
    cand2 = {norm(fixture["team2"]), norm(strip_disambig(k2 or "")), norm(k2 or "")} - {""}

    def _pair_score(row: dict) -> tuple[float, str] | tuple[None, None]:
        rt1, rt2 = row["team1"], row["team2"]
        r1s = {norm(rt1), norm(strip_disambig(rt1))} - {""}
        r2s = {norm(rt2), norm(strip_disambig(rt2))} - {""}
        if (cand1 & r1s and cand2 & r2s) or (cand1 & r2s and cand2 & r1s):
            return 100.0, "exact-pair"
        f1 = max(sim(fixture["team1"], rt1), sim(fixture["team1"], rt2),
                 sim(k1 or "", rt1), sim(k1 or "", rt2))
        f2 = max(sim(fixture["team2"], rt1), sim(fixture["team2"], rt2),
                 sim(k2 or "", rt1), sim(k2 or "", rt2))
        if f1 >= 0.85 and f2 >= 0.85:
            return (f1 + f2) * 50.0, "fuzzy-pair"
        return None, None

    best, best_score, best_how = None, 0.0, None
    for max_hours, require_page in ((36.0, False), (21.0 * 24.0, True)):
        if require_page and not page_hint:
            break
        for row in schedule_rows:
            if require_page and row.get("overview") != page_hint:
                continue
            try:
                when = datetime.fromisoformat(row["start_utc"].replace("Z", "+00:00"))
            except Exception:
                continue
            hours = abs((when - start).total_seconds()) / 3600.0
            if hours > max_hours:
                continue
            base, how = _pair_score(row)
            if base is None:
                continue
            page_bonus = 5.0 if (page_hint and row.get("overview") == page_hint) else 0.0
            score = base + page_bonus - hours * (1.0 if not require_page else 0.05)
            if score > best_score:
                best, best_score, best_how = row, score, (how if not require_page else f"{how}-flex")
        if best is not None:
            return best, best_how
    return None, None

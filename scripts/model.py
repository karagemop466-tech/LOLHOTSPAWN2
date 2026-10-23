#!/usr/bin/env python3
"""Own-line model + market consensus.

No Hotspawn number is ever used as an input. Hotspawn supplies the fixture list
only. Probabilities come from:
  * external sportsbook / prediction-market prices (Pinnacle, Unibet, Bovada,
    Polymarket), deduplicated to at most one main series line per book,
  * our own Elo + current-split Leaguepedia Standings built from recorded results,
    with a competition median prior when a team genuinely has no recorded games.

The output is a per-fixture probability, a pick, a method, a confidence level and
an explicit list of source links for every row.
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from lib_common import (clamp, load_json, log, median, norm, now_utc, prob_from_elo,
                        utc_iso, write_json)

_LATIN_FOLD = str.maketrans({
    "Ø": "O", "ø": "o", "Æ": "AE", "æ": "ae", "Œ": "OE", "œ": "oe",
    "ß": "ss", "Đ": "D", "đ": "d", "Ł": "L", "ł": "l",
})


def _norm_team(s: str) -> str:
    return norm((s or "").translate(_LATIN_FOLD))


DEFAULT_ALIASES = {
    "hotspawn_to_leaguepedia": {
        "LOS": "LOS",
        "LØS": "LOS",
        "LYON": "LYON (2024 American Team)",
        "Team Secret Whales": "Team Secret Whales",
        "Karmine Corp": "Karmine Corp",
        "Anyone's Legend": "Anyone's Legend",
        "Bilibili Gaming": "Bilibili Gaming",
        "Invictus Gaming": "Invictus Gaming",
        "Dplus KIA": "Dplus KIA",
        "Gen.G": "Gen.G",
        "Hanwha Life Esports": "Hanwha Life Esports",
        "Top Esports": "Top Esports",
        "G2 Esports": "G2 Esports",
        "Movistar KOI": "Movistar KOI",
        "CTBC Flying Oyster": "CTBC Flying Oyster",
        "Team Liquid": "Team Liquid",
        "T1": "T1",
        "Solary": "Solary",
        "Galions": "Galions",
        "Rich Gang": "Rich Gang (Norwegian Team)",
        "Locked IN": "Locked In (Dutch Team)",
        "Victorious Demons": "Team VDS",
        "Team Gromp": "Team Gromp (Australian Team)",
        "Infinity Gaming": "Infinity Gaming (Brazilian Team)",
        "Neon eSports": "Neon eSports (Brazilian Team)",
        "REH Gaming": "REH Gaming",
    },
    "competition_scoped_aliases": {
        "PRM 2nd Division 26-27 Fall": {
            "Phong Vũ Buffalo": {
                "canonical": "PvB (Swiss Team)",
                "flag": "HOTSPAWN_NAME_COLLISION",
                "source_url": "https://lol.fandom.com/wiki/Prime_League_2nd_Division/2027_Season/Fall_Split",
                "note": ("Hotspawn expands the 'PVB' tag to defunct Vietnamese team Phong Vũ Buffalo; "
                         "verified Prime League 2nd Division 26-27 Fall participant is PvB (Swiss Team)."),
            }
        }
    },
    "market_aliases": {
        "pinnacle": {
            "Liquid": "Team Liquid",
            "Bilibili": "Bilibili Gaming",
            "Secret Whales": "Team Secret Whales",
            "Invictus": "Invictus Gaming",
            "Hanwha Life": "Hanwha Life Esports",
            "G2": "G2 Esports",
            "LYON": "LYON (2024 American Team)",
            "Lyon Gaming": "LYON (2024 American Team)",
            "LØS": "LOS",
        },
        "unibet": {
            "LØS": "LOS",
            "Los Grandes": "LOS",
            "Lyon Gaming": "LYON (2024 American Team)",
            "LYON": "LYON (2024 American Team)",
            "Gen.G Esports": "Gen.G",
            "TOP Esports": "Top Esports",
            "Dplus": "Dplus KIA",
        },
        "bovada": {
            "Los Grandes": "LOS",
            "LØS": "LOS",
            "Team Secret": "Team Secret Whales",
            "Lyon Gaming": "LYON (2024 American Team)",
            "LYON": "LYON (2024 American Team)",
        },
        "polymarket": {
            "LYON": "LYON (2024 American Team)",
            "Lyon Gaming": "LYON (2024 American Team)",
            "LØS": "LOS",
        },
    },
    "tournament_pages": {
        "Worlds 2026 Main Event": "2026 Season World Championship/Main Event",
        "LGC Rising 2026 Playoffs": "LoL Game Changers/2026 Season/Playoffs",
        "LCP 2027 Promotion": "LCP/2027 Season/Promotion",
        "PRM 2nd Division 26-27 Fall": "Prime League 2nd Division/2027 Season/Fall Split",
        "PRM 3rd Division 26-27 Fall": "Prime League 3rd Division/2027 Season/Fall Split",
        "Arabian League 2nd Division 2026 Summer": "Arabian League 2nd Division/2026 Season/Summer Split",
        "Arabian Regional Championship 2026: Lebanon-Libya-Syria-Palestine": "Arabian Regional Championship 2026/Qualifiers/LB-Li-SY-PS",
        "Komplettligaen 2026 Autumn": "Komplettligaen/2026 Season/Autumn Split",
        "RIVALS LEAGUE Season 2": "RIVALS LEAGUE/2026 Season/Season 2",
        "Tunisian Super League 2026": "Tunisian Super League/2026 Season",
        "LigaGG CELOL A 2026 Split 2 Playoffs": "LigaGG/CELOL Série A/2026 Season/Split 2 Playoffs",
        "LigaGG CELOL B 2026 Split 2 Playoffs": "LigaGG/CELOL Série B/2026 Season/Split 2 Playoffs",
    },
}

METHOD_LABELS = {
    "MARKET_CONSENSUS": "Market consensus (2+ sources)",
    "MARKET_SINGLE": "Single external market",
    "MODEL_ELO": "Own Elo model",
    "MODEL_ELO_THIN": "Own Elo model (thin history)",
    "MODEL_STANDINGS": "Leaguepedia split standings + Elo",
    "MODEL_LEAGUE_PRIOR": "League/overall prior (no team history)",
    "UNRESOLVED": "Unresolved - no verified signal",
}


def sim(a: str, b: str) -> float:
    return SequenceMatcher(None, _norm_team(a), _norm_team(b)).ratio()


def contains(a: str, b: str) -> bool:
    na, nb = _norm_team(a), _norm_team(b)
    return bool(na and nb) and (na in nb or nb in na)


def load_aliases(path="data/aliases.json"):
    cfg = load_json(path, {}) or {}
    merged = {
        "hotspawn_to_leaguepedia": dict(DEFAULT_ALIASES["hotspawn_to_leaguepedia"]),
        "competition_scoped_aliases": {
            comp: dict(entries)
            for comp, entries in DEFAULT_ALIASES["competition_scoped_aliases"].items()
        },
        "market_aliases": {k: dict(v) for k, v in DEFAULT_ALIASES["market_aliases"].items()},
        "tournament_pages": dict(DEFAULT_ALIASES["tournament_pages"]),
    }
    for k, v in (cfg.get("hotspawn_to_leaguepedia") or {}).items():
        merged["hotspawn_to_leaguepedia"][k] = v
    for comp, entries in (cfg.get("competition_scoped_aliases") or {}).items():
        merged["competition_scoped_aliases"].setdefault(comp, {}).update(entries or {})
    for src, mapping in (cfg.get("market_aliases") or {}).items():
        merged["market_aliases"].setdefault(src, {}).update(mapping or {})
    for k, v in (cfg.get("tournament_pages") or {}).items():
        merged["tournament_pages"][k] = v
    return merged


# Competition strength priors -------------------------------------------------
# Specific sub-divisions MUST precede parent league substrings (e.g. "prime
# league 2nd division" and "prime league 3rd division" before "prime league",
# "arabian league 2nd division" before "arabian league").
_TIER_RULES = (
    ("academy", 1440), ("youth", 1440), ("rookie", 1440), ("university", 1400),
    ("qualifier", 1430), ("nexus tour", 1430), ("amateur", 1430),
    ("world championship", 1720), ("worlds", 1720), ("msi", 1720),
    ("first stand", 1720), ("asia masters", 1710),
    ("emea masters", 1640),
    ("lcp/2027 season/promotion", 1575),
    ("lck cl", 1585), ("ldl", 1585), ("nacl", 1560),
    ("north american challengers", 1560), ("circuito desafiante", 1560),
    ("challengers", 1560),
    ("lck", 1690), ("lpl", 1690), ("lec", 1650), ("lcs", 1650), ("lta", 1630),
    ("cblol", 1625), ("lcp", 1615), ("pcs", 1600), ("vcs", 1595), ("ljl", 1580),
    ("lla", 1580), ("tcl", 1580), ("lco", 1570),
    ("prime league 1", 1560),
    ("prime league 2nd division", 1480),
    ("prime league 3rd division", 1460),
    ("prime league 4th division", 1440),
    ("arabian league 2nd division", 1475),
    ("game changers", 1480),
    ("lfl", 1550), ("nlc", 1545), ("ultraliga", 1540),
    ("superliga", 1540), ("elite series", 1535), ("hitpoint", 1530),
    ("arabian league", 1530), ("rift legends", 1525), ("ligue", 1520),
    ("prime league", 1500), ("prime pokal", 1490), ("2nd division", 1480),
    ("3rd division", 1460), ("empoliga", 1450), ("komplettligaen", 1460),
    ("tunisian", 1450), ("ligagg", 1470), ("rivals league", 1470),
    ("icelandic", 1460), ("blossom", 1470), ("aegis", 1460),
    ("jurassic", 1470), ("4 nations", 1460),
)


def competition_base(page):
    """Base Elo for a competition page (None when unknown)."""
    p = (page or "").lower()
    if not p:
        return None
    for token, base in _TIER_RULES:
        if token in p:
            return float(base)
    return 1490.0


def build_ratings(results, now, priors=None, half_life_days=365.0, k_base=24.0):
    """Chronological Elo anchored to per-competition priors.

    Inactivity drift pulls a team back toward its own competition base rather
    than toward a single global mean, so isolated leagues keep their tier.
    """
    priors = priors or {}
    ratings, games, wins, last_seen, game_dates = {}, Counter(), Counter(), {}, defaultdict(list)
    h2h = defaultdict(lambda: [0, 0])
    rows = [r for r in results if r.get("winner") in (1, 2)]
    rows.sort(key=lambda r: r["start_utc"])
    cutoff = now - timedelta(hours=1)
    used = 0
    for r in rows:
        try:
            when = datetime.fromisoformat(r["start_utc"].replace("Z", "+00:00"))
        except Exception:
            continue
        if when >= cutoff:
            continue
        a, b = r["team1"], r["team2"]
        ka, kb = _norm_team(a), _norm_team(b)
        if not ka or not kb:
            continue
        base_a, base_b = priors.get(ka, 1500.0), priors.get(kb, 1500.0)
        ra, rb = ratings.get(ka, base_a), ratings.get(kb, base_b)
        for key, val, base in ((ka, ra, base_a), (kb, rb, base_b)):
            seen = last_seen.get(key)
            if seen:
                days = max(0.0, (when - seen).total_seconds() / 86400.0)
                drifted = base + (val - base) * math.exp(-math.log(2) * days / half_life_days)
                if key == ka:
                    ra = drifted
                else:
                    rb = drifted
        ea = prob_from_elo(ra, rb)
        bo = r.get("best_of") or 3
        k = k_base * (0.8 if bo == 1 else 1.0 if bo == 3 else 1.3)
        try:
            margin = abs(int(r.get("score1") or 0) - int(r.get("score2") or 0))
        except (TypeError, ValueError):
            margin = 1
        k *= min(1.5, 1.0 + 0.12 * max(0, margin - 1))
        win_a = 1.0 if r["winner"] == 1 else 0.0
        ratings[ka] = ra + k * (win_a - ea)
        ratings[kb] = rb + k * ((1.0 - win_a) - (1.0 - ea))
        games[ka] += 1
        games[kb] += 1
        if win_a:
            wins[ka] += 1
        else:
            wins[kb] += 1
        last_seen[ka] = when
        last_seen[kb] = when
        game_dates[ka].append(when)
        game_dates[kb].append(when)
        key = tuple(sorted((ka, kb)))
        h2h[key][0 if ka == key[0] and win_a or kb == key[0] and not win_a else 1] += 1
        used += 1
    recent = Counter()
    for team, dates in game_dates.items():
        recent[team] = sum(1 for d in dates if (now - d).days <= 365)
    for k in ratings:
        ratings[k] = max(1000.0, min(2200.0, ratings[k]))
    return {"ratings": ratings, "games": games, "recent_games": recent, "wins": wins,
            "last_seen": last_seen, "h2h": dict(h2h), "matches_used": used}


def name_variants(name: str) -> set[str]:
    """Spelling-only variants of a team name (never a different team).

    Leaguepedia disambiguates common names in brackets ("Locked In (Dutch Team)",
    "Neon eSports (Brazilian Team)") while Hotspawn writes the short form. Prefixes
    and suffixes below are the only transformations applied; an ambiguous match is
    still refused by the caller.
    """
    raw = str(name or "").strip()
    variants = {raw}
    for prefix in ("ex-", "ex "):
        if raw.lower().startswith(prefix):
            variants.add(raw[len(prefix):].strip())
    for suffix in (" e.v.", " e.v", " multigaming", " academy"):
        if raw.lower().endswith(suffix):
            variants.add(raw[: -len(suffix)].strip())
    stripped = re.sub(r"\s*\([^)]*\)\s*$", "", raw).strip()
    if stripped and stripped != raw:
        variants.add(stripped)
    return {v for v in variants if v}


class Resolver:
    def __init__(self, names, aliases, scoped_aliases=None):
        self.names = sorted({str(n).strip() for n in names if str(n or "").strip()})
        self.by_norm = {_norm_team(n): n for n in self.names}
        self.aliases = {_norm_team(k): v for k, v in (aliases or {}).items()}
        self.by_var = defaultdict(set)
        for n in self.names:
            for v in name_variants(n):
                self.by_var[_norm_team(v)].add(n)
        self.scoped = {}
        for comp, entries in (scoped_aliases or {}).items():
            c_map = {}
            for raw_team, spec in (entries or {}).items():
                if isinstance(spec, str):
                    spec = {"canonical": spec}
                c_map[_norm_team(raw_team)] = spec
            self.scoped[_norm_team(comp)] = c_map

    def resolve_with_meta(self, name: str | None, tournament: str | None = None) -> tuple[str | None, dict | None]:
        if not name:
            return None, None
        n = _norm_team(name)
        if tournament:
            c_map = self.scoped.get(_norm_team(tournament))
            if c_map and n in c_map:
                spec = c_map[n]
                target = spec.get("canonical")
                resolved = self.by_norm.get(_norm_team(target), target) if target else None
                return resolved, spec
        if n in self.aliases:
            target = self.aliases[n]
            return self.by_norm.get(_norm_team(target), target), None
        if n in self.by_norm:
            return self.by_norm[n], None
        variant_hits = set()
        for v in name_variants(name):
            variant_hits |= self.by_var.get(_norm_team(v), set())
        if len(variant_hits) == 1:
            return next(iter(variant_hits)), None
        cands = [x for x in self.names if contains(name, x)]
        if len(cands) == 1:
            return cands[0], None
        if cands:
            cands.sort(key=lambda x: abs(len(_norm_team(x)) - len(n)))
            return cands[0], None
        best, score = None, 0.0
        for x in self.names:
            s = sim(name, x)
            if s > score:
                best, score = x, s
        return (best if score >= 0.88 else None), None

    def resolve(self, name: str | None, tournament: str | None = None) -> str | None:
        resolved, _ = self.resolve_with_meta(name, tournament=tournament)
        return resolved


def _pair_matches_row(ft1: str, ft2: str, k1: str | None, k2: str | None, row: dict) -> tuple[bool, str, float]:
    """Check whether (ft1, ft2) / canonical (k1, k2) matches a schedule row."""
    rt1, rt2 = str(row["team1"]), str(row["team2"])
    n_rt1, n_rt2 = _norm_team(rt1), _norm_team(rt2)
    n_ft1, n_ft2 = _norm_team(ft1), _norm_team(ft2)
    n_k1 = _norm_team(k1) if k1 else n_ft1
    n_k2 = _norm_team(k2) if k2 else n_ft2

    if (n_rt1 == n_ft1 and n_rt2 == n_ft2) or (n_rt1 == n_ft2 and n_rt2 == n_ft1):
        return True, "exact-pair", 100.0
    if (n_rt1 == n_k1 and n_rt2 == n_k2) or (n_rt1 == n_k2 and n_rt2 == n_k1):
        return True, "alias-pair", 98.0

    f1 = max(sim(ft1, rt1), sim(ft1, rt2), sim(k1 or ft1, rt1), sim(k1 or ft1, rt2))
    f2 = max(sim(ft2, rt1), sim(ft2, rt2), sim(k2 or ft2, rt1), sim(k2 or ft2, rt2))
    if f1 >= 0.84 and f2 >= 0.84:
        return True, "fuzzy-pair", (f1 + f2) * 50.0
    return False, "", 0.0


def match_fixture_to_schedule(
    fixture,
    schedule_rows,
    unscheduled_rows=None,
    resolver: Resolver | None = None,
    tournament_pages: dict | None = None,
):
    """Find the Leaguepedia row for a Hotspawn fixture. Returns (row, how) or (None, None)."""
    ft1, ft2 = fixture["team1"], fixture["team2"]
    tourn = fixture.get("tournament") or ""
    k1 = resolver.resolve(ft1, tournament=tourn) if resolver else ft1
    k2 = resolver.resolve(ft2, tournament=tourn) if resolver else ft2
    expected_page = (tournament_pages or {}).get(tourn)
    start = datetime.fromisoformat(fixture["start_utc"].replace("Z", "+00:00"))

    best, best_score, best_how = None, -1e9, None
    for row in schedule_rows:
        if not row.get("start_utc"):
            continue
        try:
            when = datetime.fromisoformat(row["start_utc"].replace("Z", "+00:00"))
        except Exception:
            continue
        hours = abs((when - start).total_seconds()) / 3600.0
        if hours > 36:
            continue
        ok, how, base_score = _pair_matches_row(ft1, ft2, k1, k2, row)
        if not ok:
            continue
        page_bonus = 4.0 if expected_page and _norm_team(row.get("overview") or "") == _norm_team(expected_page) else 0.0
        score = base_score + page_bonus - hours
        if score > best_score:
            best, best_score, best_how = row, score, how
    if best is not None:
        return best, best_how

    # Pass 2: within the verified tournament OverviewPage, check rescheduled
    # upcoming pairings (±18 days) and TBD-date upcoming pairings.
    if expected_page:
        exp_norm = _norm_team(expected_page)
        resched_best, resched_hours = None, 1e9
        for row in schedule_rows:
            if row.get("winner") in (1, 2) or _norm_team(row.get("overview") or "") != exp_norm:
                continue
            if not row.get("start_utc"):
                continue
            try:
                when = datetime.fromisoformat(row["start_utc"].replace("Z", "+00:00"))
            except Exception:
                continue
            hours = abs((when - start).total_seconds()) / 3600.0
            if hours > 432:
                continue
            ok, _how, _sc = _pair_matches_row(ft1, ft2, k1, k2, row)
            if ok and hours < resched_hours:
                resched_best, resched_hours = row, hours
        if resched_best is not None:
            return resched_best, "rescheduled-pair"

        for row in (unscheduled_rows or []):
            if _norm_team(row.get("overview") or "") != exp_norm:
                continue
            ok, _how, _sc = _pair_matches_row(ft1, ft2, k1, k2, row)
            if ok:
                return row, "unscheduled-pair"

    return None, None


def _side_match_score(m_raw: str, m_res: str | None, f_raw: str, f_res: str | None) -> float:
    """Similarity score in [0, 1] between a market team label and a fixture side."""
    mr_n = _norm_team(m_raw)
    ms_n = _norm_team(m_res) if m_res else mr_n
    fr_n = _norm_team(f_raw)
    fs_n = _norm_team(f_res) if f_res else fr_n
    if not mr_n or not fr_n:
        return 0.0
    if mr_n == fr_n or ms_n == fs_n or mr_n == fs_n or ms_n == fr_n:
        return 1.0
    if contains(m_raw, f_raw) or (f_res and contains(m_raw, f_res)) or (m_res and contains(m_res, f_raw)):
        return 0.94
    return max(
        sim(m_raw, f_raw),
        sim(m_res or m_raw, f_res or f_raw),
        sim(m_raw, f_res or f_raw),
        sim(m_res or m_raw, f_raw),
    )


def _standings_elo(st: dict, base_elo: float) -> float:
    ws = int(st.get("win_series") or 0)
    ls = int(st.get("loss_series") or 0)
    wg = int(st.get("win_games") or 0)
    lg = int(st.get("loss_games") or 0)
    wr_s = (ws + 1.0) / (ws + ls + 2.0) if (ws + ls) > 0 else 0.5
    wr_g = (wg + 1.5) / (wg + lg + 3.0) if (wg + lg) > 0 else wr_s
    wr = clamp(0.65 * wr_s + 0.35 * wr_g, 0.15, 0.85)
    return base_elo + 400.0 * math.log10(wr / (1.0 - wr))


def multi_division_pages(standings_rows) -> set[str]:
    """Pages that list more than one first place: several divisions/sections share
    one table, and the source has no column saying which team belongs to which."""
    places = defaultdict(int)
    for st in standings_rows or []:
        page = _norm_team(st.get("overview") or "")
        try:
            if int(str(st.get("place") or "").strip() or 0) == 1:
                places[page] += 1
        except (TypeError, ValueError):
            continue
    return {p for p, n in places.items() if n > 1}


def blend_h2h(p, h2h_n, h2h_wins, weight=0.15):
    if h2h_n < 3:
        return p, None
    rate = (h2h_wins + 1.0) / (h2h_n + 2.0)  # Laplace smoothing
    w = weight * min(h2h_n, 6) / 6.0
    return p * (1 - w) + rate * w, {"games": h2h_n, "team1_wins": h2h_wins, "weight": round(w, 3)}


def backtest(results, now, priors, days=30):
    """Honest out-of-sample check: fit on data before the window, score the last N days."""
    cut = now - timedelta(days=days)
    train = [r for r in results if r.get("winner") in (1, 2) and r["start_utc"] < utc_iso(cut)]
    rd = build_ratings(train, cut, priors=priors, half_life_days=365.0, k_base=24.0)
    ratings = rd["ratings"]
    n = 0
    ll = br = acc = 0.0
    for r in results:
        if r.get("winner") not in (1, 2):
            continue
        if not (utc_iso(cut) <= r["start_utc"] < utc_iso(now)):
            continue
        r1 = ratings.get(_norm_team(r["team1"]))
        r2 = ratings.get(_norm_team(r["team2"]))
        if r1 is None or r2 is None:
            continue
        p = clamp(prob_from_elo(r1, r2), 0.02, 0.98)
        y = 1.0 if r["winner"] == 1 else 0.0
        ll += -(y * math.log(p) + (1 - y) * math.log(1 - p))
        br += (p - y) ** 2
        acc += 1.0 if (p >= 0.5) == bool(y) else 0.0
        n += 1
    if not n:
        return None
    return {"window_days": days, "n": n, "log_loss": round(ll / n, 4),
            "brier": round(br / n, 4), "accuracy": round(acc / n, 4),
            "baseline_log_loss": 0.6931, "baseline_brier": 0.25}


def build_matches(hotspawn, leaguepedia, markets, aliases):
    now = now_utc()
    schedule_rows = leaguepedia.get("schedule") or []
    unscheduled_rows = leaguepedia.get("unscheduled") or []
    standings_rows = leaguepedia.get("standings") or []
    tournament_pages = aliases.get("tournament_pages") or {}

    # team -> modal competition over the last 365 days (used for tier priors)
    now_cut = now - timedelta(days=365)
    team_comps = defaultdict(Counter)
    for r in leaguepedia["results"]:
        try:
            when = datetime.fromisoformat(r["start_utc"].replace("Z", "+00:00"))
        except Exception:
            continue
        if when < now_cut:
            continue
        team_comps[_norm_team(r["team1"])][r["overview"]] += 1
        team_comps[_norm_team(r["team2"])][r["overview"]] += 1
    priors = {}
    for team, comps in team_comps.items():
        base = competition_base(comps.most_common(1)[0][0])
        if base:
            priors[team] = base

    rating_data = build_ratings(leaguepedia["results"], now, priors=priors)
    ratings = rating_data["ratings"]
    recent = rating_data["recent_games"]

    # Index current-season split standings by (overview, team) and by team
    standings_by_page_team: dict[tuple[str, str], dict] = {}
    standings_by_team: dict[str, dict] = {}
    for st in standings_rows:
        ov = str(st.get("overview") or "")
        tm = str(st.get("team") or "")
        played = int(st.get("win_series") or 0) + int(st.get("loss_series") or 0) + int(st.get("win_games") or 0) + int(st.get("loss_games") or 0)
        if not ov or not tm or played <= 0:
            continue
        standings_by_page_team[(_norm_team(ov), _norm_team(tm))] = st
        prev = standings_by_team.get(_norm_team(tm))
        if prev is None or played >= (int(prev.get("win_series") or 0) + int(prev.get("loss_series") or 0) + int(prev.get("win_games") or 0) + int(prev.get("loss_games") or 0)):
            standings_by_team[_norm_team(tm)] = st

    multi_div = multi_division_pages(standings_rows)

    lp_names = set()
    for r in leaguepedia["results"] + schedule_rows + unscheduled_rows:
        lp_names.add(str(r["team1"]))
        lp_names.add(str(r["team2"]))
    for st in standings_rows:
        if st.get("team"):
            lp_names.add(str(st["team"]))
    for t in leaguepedia.get("teams") or []:
        if t.get("Name") not in (None, ""):
            lp_names.add(str(t["Name"]))

    # Merge official Leaguepedia TeamRedirects only when the source name is not
    # already curated and the target is active in recent results or standings.
    curated = dict(aliases["hotspawn_to_leaguepedia"])
    curated_norms = {_norm_team(k) for k in curated}
    for src_name, dst_name in (leaguepedia.get("redirects") or {}).items():
        if _norm_team(src_name) in curated_norms:
            continue
        dst_norm = _norm_team(dst_name)
        if recent.get(dst_norm, 0) >= 1 or dst_norm in standings_by_team:
            curated[src_name] = dst_name

    resolver = Resolver(
        lp_names,
        curated,
        scoped_aliases=aliases.get("competition_scoped_aliases"),
    )

    # competition prior: median rating of rated teams in the same tournament page
    comp_teams = defaultdict(set)
    for r in leaguepedia["results"]:
        comp_teams[r["overview"]].add(_norm_team(r["team1"]))
        comp_teams[r["overview"]].add(_norm_team(r["team2"]))
    rated_values = [v for k, v in ratings.items() if recent.get(k, 0) >= 3]
    global_prior = median(rated_values) or 1500.0
    comp_prior = {}
    for page, teams in comp_teams.items():
        vals = [ratings[t] for t in teams if t in ratings and recent.get(t, 0) >= 3]
        if len(vals) >= 3:
            comp_prior[page] = median(vals)
        else:
            base = competition_base(page)
            if base:
                comp_prior[page] = base

    # Pre-match every Hotspawn fixture against Leaguepedia schedule so verified
    # BestOf values are available before series-vs-game market filtering runs.
    enriched_fixtures = []
    schedule_matches: dict[str, tuple[dict | None, str | None]] = {}
    for raw_f in hotspawn["fixtures"]:
        f = dict(raw_f)
        row, how = match_fixture_to_schedule(
            f, schedule_rows, unscheduled_rows=unscheduled_rows,
            resolver=resolver, tournament_pages=tournament_pages,
        )
        if f.get("best_of") is None and row and row.get("best_of") in (1, 2, 3, 5):
            f["best_of"] = int(row["best_of"])
        schedule_matches[str(f["id"])] = (row, how)
        enriched_fixtures.append(f)

    # ---- market matching (closest start time wins; ±36h) -----------------
    market_fixtures = defaultdict(list)
    market_unmatched = []
    for rec in markets.get("records") or []:
        rec_start = datetime.fromisoformat(rec["start_utc"].replace("Z", "+00:00"))
        src_aliases = aliases["market_aliases"].get(rec["source_key"], {})
        a_raw = src_aliases.get(rec["team_a"], rec["team_a"])
        b_raw = src_aliases.get(rec["team_b"], rec["team_b"])
        a_res = resolver.resolve(a_raw)
        b_res = resolver.resolve(b_raw)

        best_pair = None
        for f in enriched_fixtures:
            fstart = datetime.fromisoformat(f["start_utc"].replace("Z", "+00:00"))
            delta_h = abs((fstart - rec_start).total_seconds()) / 3600.0
            if delta_h > 36:
                continue
            tourn = f.get("tournament") or ""
            fk1 = resolver.resolve(f["team1"], tournament=tourn)
            fk2 = resolver.resolve(f["team2"], tournament=tourn)
            same_a = _side_match_score(a_raw, a_res, f["team1"], fk1)
            same_b = _side_match_score(b_raw, b_res, f["team2"], fk2)
            flip_a = _side_match_score(a_raw, a_res, f["team2"], fk2)
            flip_b = _side_match_score(b_raw, b_res, f["team1"], fk1)

            same_ok = same_a >= 0.86 and same_b >= 0.86
            flip_ok = flip_a >= 0.86 and flip_b >= 0.86
            if not (same_ok or flip_ok):
                continue

            market_note = f"{rec.get('note') or ''} {rec.get('competition') or ''}".lower()
            is_game_market = ((rec.get("raw") or {}).get("market_type") == "game"
                              or bool(re.search(r"\b(game|map)\s*\d", market_note)))
            if is_game_market and f.get("best_of") != 1:
                continue
            flip = (flip_a + flip_b) > (same_a + same_b)
            if best_pair is None or delta_h < best_pair[0]:
                best_pair = (delta_h, f, flip)

        if not best_pair:
            market_unmatched.append({"source": rec["source"], "teams": [rec["team_a"], rec["team_b"]],
                                     "start_utc": rec["start_utc"], "url": rec["url"]})
            continue
        delta_h, f, flip = best_pair
        raw_bo = (rec.get("raw") or {}).get("best_of")
        if f.get("best_of") is None and raw_bo in (1, 2, 3, 5) and (rec.get("raw") or {}).get("market_type") != "game":
            f["best_of"] = int(raw_bo)
        p1 = rec["prob_b"] if flip else rec["prob_a"]
        market_fixtures[f["id"]].append({
            "source": rec["source"], "source_key": rec["source_key"], "url": rec["url"],
            "prob_team1": p1, "prob_team2": round(1 - p1, 6),
            "decimal_team1": rec.get("decimal_b") if flip else rec.get("decimal_a"),
            "decimal_team2": rec.get("decimal_a") if flip else rec.get("decimal_b"),
            "note": rec.get("note"), "start_utc": rec["start_utc"],
            "start_delta_hours": round(delta_h, 1), "competition": rec.get("competition")})

    # ---- per-fixture probability -----------------------------------------
    WEIGHTS = {"pinnacle": 1.0, "unibet": 0.85, "bovada": 0.8, "polymarket": 0.7}
    out = []
    for f in enriched_fixtures:
        row, how = schedule_matches.get(str(f["id"]), (None, None))
        f = dict(f)
        t1, t2 = f["team1"], f["team2"]
        tourn = f.get("tournament") or ""
        k1, meta1 = resolver.resolve_with_meta(t1, tournament=tourn)
        k2, meta2 = resolver.resolve_with_meta(t2, tournament=tourn)
        if row:
            for n, disp in {(_norm_team(row["team1"]), row["team1"]), (_norm_team(row["team2"]), row["team2"])}:
                if n == _norm_team(t1) and not meta1:
                    k1 = resolver.resolve(disp, tournament=tourn) or k1
                if n == _norm_team(t2) and not meta2:
                    k2 = resolver.resolve(disp, tournament=tourn) or k2

        eff_page = (row["overview"] if row and row.get("overview") else None) or tournament_pages.get(tourn) or ""
        if row is None and eff_page:
            how = "tournament-page"

        n_k1 = _norm_team(k1) if k1 else _norm_team(t1)
        n_k2 = _norm_team(k2) if k2 else _norm_team(t2)
        r1 = ratings.get(n_k1) if k1 else None
        r2 = ratings.get(n_k2) if k2 else None
        g1 = recent.get(n_k1, 0) if k1 else 0
        g2 = recent.get(n_k2, 0) if k2 else 0

        st1 = standings_by_page_team.get((_norm_team(eff_page), n_k1)) if eff_page else None
        st2 = standings_by_page_team.get((_norm_team(eff_page), n_k2)) if eff_page else None
        if st1 is None:
            st1 = standings_by_team.get(n_k1)
        if st2 is None:
            st2 = standings_by_team.get(n_k2)

        comp1 = team_comps[n_k1].most_common(1)[0][0] if k1 and team_comps[n_k1] else (st1["overview"] if st1 else None)
        comp2 = team_comps[n_k2].most_common(1)[0][0] if k2 and team_comps[n_k2] else (st2["overview"] if st2 else None)
        base1 = priors.get(n_k1) or (competition_base(comp1) if comp1 else None)
        base2 = priors.get(n_k2) or (competition_base(comp2) if comp2 else None)
        cross_league = bool(base1 and base2 and abs(base1 - base2) >= 60 and
                            team_comps[n_k1].get(comp1, 0) >= 5 and
                            team_comps[n_k2].get(comp2, 0) >= 5)
        # The unrated side must be compared with a prior for ITS competition, not with
        # one median pooled across Worlds and third divisions.
        prior = (comp_prior.get(eff_page) or competition_base(eff_page)
                 or competition_base(f.get("tournament")) or competition_base(comp1)
                 or competition_base(comp2) or global_prior)
        if eff_page in comp_prior and comp_prior.get(eff_page) != competition_base(eff_page):
            prior_source = "competition median"
        elif competition_base(eff_page):
            prior_source = "competition tier prior"
        elif competition_base(f.get("tournament")):
            prior_source = "tournament tier prior"
        elif competition_base(comp1) or competition_base(comp2):
            prior_source = "team's competition tier prior"
        else:
            prior_source = "global median"

        flags = []
        for side_label, meta in ((t1, meta1), (t2, meta2)):
            if meta and meta.get("flag"):
                flags.append(meta["flag"])

        raw_recs = market_fixtures.get(f["id"], [])
        # Deduplicate external quotes per provider (closest start_delta_hours wins)
        # so one sportsbook's child boards can never outweigh independent books.
        by_book: dict[str, dict] = {}
        for r in raw_recs:
            sk = r["source_key"]
            if sk not in by_book or r.get("start_delta_hours", 999) < by_book[sk].get("start_delta_hours", 999):
                by_book[sk] = r
        recs = list(by_book.values())

        model = model_prob = model_method = None
        has_elo_1 = r1 is not None and g1 >= 1
        has_elo_2 = r2 is not None and g2 >= 1
        has_st_1 = st1 is not None and (int(st1.get("win_series") or 0) + int(st1.get("loss_series") or 0)) >= 1
        has_st_2 = st2 is not None and (int(st2.get("win_series") or 0) + int(st2.get("loss_series") or 0)) >= 1

        if has_elo_1 and has_elo_2:
            raw = prob_from_elo(r1, r2)
            shrink = min(g1, g2) / (min(g1, g2) + 8.0)
            p = 0.5 + (raw - 0.5) * shrink
            h2h = rating_data["h2h"].get(tuple(sorted((n_k1, n_k2))))
            h2h_info = None
            if h2h:
                first_is_k1 = tuple(sorted((n_k1, n_k2)))[0] == n_k1
                wins_k1 = h2h[0] if first_is_k1 else h2h[1]
                p, h2h_info = blend_h2h(p, sum(h2h), wins_k1)
            model_prob = p
            model_method = "MODEL_ELO" if min(g1, g2) >= 8 else "MODEL_ELO_THIN"
            model = {
                "elo_team1": round(r1), "elo_team2": round(r2),
                "canonical_team1": k1, "canonical_team2": k2,
                "games_team1_365d": g1, "games_team2_365d": g2,
                "shrink": round(shrink, 3), "h2h": h2h_info, "prior_used": None,
                "tournament_page": eff_page,
                "team1_recent_competition": comp1, "team2_recent_competition": comp2,
                "cross_league": cross_league,
                "team1_competition_base": round(base1 or prior),
                "team2_competition_base": round(base2 or prior),
            }
            if cross_league:
                flags.append("CROSS_LEAGUE_MODEL")
        elif (has_elo_1 or has_st_1) and (has_elo_2 or has_st_2):
            eff_r1 = r1 if has_elo_1 else _standings_elo(st1, prior)
            eff_r2 = r2 if has_elo_2 else _standings_elo(st2, prior)
            eff_g1 = g1 if has_elo_1 else (int(st1.get("win_series") or 0) + int(st1.get("loss_series") or 0))
            eff_g2 = g2 if has_elo_2 else (int(st2.get("win_series") or 0) + int(st2.get("loss_series") or 0))
            raw = prob_from_elo(eff_r1, eff_r2)
            shrink = min(eff_g1, eff_g2) / (min(eff_g1, eff_g2) + 8.0)
            model_prob = 0.5 + (raw - 0.5) * shrink
            if _norm_team(eff_page) in multi_div:
                # the page mixes divisions and does not say which team plays where:
                # the records are only weak evidence, so halve the edge
                model_prob = 0.5 + (model_prob - 0.5) * 0.5
                flags.append("MULTI_DIVISION_STANDINGS")
            model_method = "MODEL_STANDINGS"
            model = {
                "elo_team1": round(eff_r1), "elo_team2": round(eff_r2),
                "canonical_team1": k1, "canonical_team2": k2,
                "games_team1_365d": eff_g1, "games_team2_365d": eff_g2,
                "standings_team1": st1, "standings_team2": st2,
                "shrink": round(shrink, 3), "prior_used": "split standings",
                "tournament_page": eff_page,
                "team1_recent_competition": comp1, "team2_recent_competition": comp2,
                "cross_league": cross_league,
                "team1_competition_base": round(base1 or prior),
                "team2_competition_base": round(base2 or prior),
            }
            if cross_league:
                flags.append("CROSS_LEAGUE_MODEL")
        elif (has_elo_1 or has_st_1) or (has_elo_2 or has_st_2):
            known_k1 = bool(has_elo_1 or has_st_1)
            known_r = (r1 if has_elo_1 else _standings_elo(st1, prior)) if known_k1 else (r2 if has_elo_2 else _standings_elo(st2, prior))
            known_g = (g1 if has_elo_1 else int(st1.get("win_series") or 0) + int(st1.get("loss_series") or 0)) if known_k1 else (g2 if has_elo_2 else int(st2.get("win_series") or 0) + int(st2.get("loss_series") or 0))
            raw = prob_from_elo(known_r, prior) if known_k1 else prob_from_elo(prior, known_r)
            shrink = known_g / (known_g + 20.0)
            model_prob = 0.5 + (raw - 0.5) * shrink
            model_method = "MODEL_LEAGUE_PRIOR"
            model = {
                "elo_known": round(known_r), "elo_prior": round(prior),
                "canonical_team1": k1, "canonical_team2": k2,
                "known_side": "team1" if known_k1 else "team2",
                "games_known_365d": known_g, "shrink": round(shrink, 3),
                "prior_used": prior_source, "tournament_page": eff_page,
                "team1_recent_competition": comp1, "team2_recent_competition": comp2,
            }
            flags.append("ONE_TEAM_NO_HISTORY")
        elif not recs:
            flags.append("NO_TEAM_HISTORY")

        # ---- external market consensus
        market = None
        mconf = None
        if recs:
            recs.sort(key=lambda r: WEIGHTS.get(r["source_key"], 0.6), reverse=True)
            ps = [r["prob_team1"] for r in recs]
            w = [WEIGHTS.get(r["source_key"], 0.6) for r in recs]
            wmean = sum(pp * wi for pp, wi in zip(ps, w)) / sum(w)
            cons = median(ps) if len(ps) >= 3 else wmean
            dispersion = max(ps) - min(ps)
            spreads = [r.get("start_delta_hours", 0) for r in recs
                       if r["source_key"] in ("pinnacle", "unibet", "bovada")]
            market = {"sources": recs, "consensus_team1": round(cons, 4),
                      "weighted_mean_team1": round(wmean, 4),
                      "dispersion": round(dispersion, 4), "source_count": len(recs),
                      "time_spread_hours": round(max(spreads), 1) if spreads else None,
                      "cross_league": cross_league}
            if len(recs) >= 2 and dispersion <= 0.06:
                mconf = "High"
            elif len(recs) >= 2 and dispersion <= 0.10:
                mconf = "Medium"
            elif len(recs) == 1:
                mconf = "Medium"
            else:
                mconf = "Low"
            if dispersion > 0.10:
                flags.append("MARKET_DISAGREEMENT")
            if spreads and max(spreads) > 1.5:
                flags.append("START_TIME_DISAGREES_WITH_BOOKS")
            if model_prob is not None:
                market["model_team1"] = round(model_prob, 4)
                market["model_edge_team1"] = round(model_prob - cons, 4)

        if recs:
            p1 = market["consensus_team1"]
            method = "MARKET_CONSENSUS" if len(recs) >= 2 else "MARKET_SINGLE"
            confidence = mconf
        elif model_method:
            p1 = model_prob
            method = model_method
            if model_method == "MODEL_ELO":
                confidence = ("Low" if cross_league else
                              "High" if min(g1, g2) >= 15 and abs(r1 - r2) >= 60 else "Medium")
            elif model_method == "MODEL_STANDINGS":
                sample = min(
                    int((st1 or {}).get("win_series") or 0) + int((st1 or {}).get("loss_series") or 0)
                    if st1 else g1,
                    int((st2 or {}).get("win_series") or 0) + int((st2 or {}).get("loss_series") or 0)
                    if st2 else g2)
                confidence = "Low" if (_norm_team(eff_page) in multi_div or sample < 5) else "Medium"
            else:
                confidence = "Low"
        else:
            p1 = 0.5
            method = "UNRESOLVED"
            confidence = "None"
            flags.append("NO_VERIFIED_SIGNAL")

        p1 = clamp(p1, 0.02, 0.98)
        pick_team1 = p1 >= 0.5
        pick = t1 if pick_team1 else t2
        pick_prob = p1 if pick_team1 else 1 - p1

        if model_prob is not None and recs:
            market["model_note"] = ("Cross-league comparison; the model is anchored to competition "
                                    "tier priors, so the gap is indicative only." if cross_league else
                                    "Same-competition model comparison.")
            if abs(model_prob - market["consensus_team1"]) >= 0.08 and not cross_league:
                flags.append("MODEL_DISAGREES_WITH_MARKET")
        if not recs:
            flags.append("NO_EXTERNAL_MARKET")
        if g1 < 5 or g2 < 5:
            flags.append("THIN_HISTORY")
        if not f.get("hotspawn_url"):
            flags.append("NO_HOTSPAWN_MATCH_PAGE")
        if str(f.get("tier", "")).startswith("WAITING"):
            flags.append("TIER_UNVERIFIED")
        if model_method and not eff_page:
            # The team ratings still come from Leaguepedia's recorded results,
            # but no fixture-specific competition page was matched for this row.
            flags.append("GENERIC_RESULTS_SOURCE")
        if str(f.get("status") or "").lower() in ("cancelled", "canceled", "abandoned", "postponed"):
            flags.append("FIXTURE_CANCELLED_ON_FEED")
        if how == "unscheduled-pair":
            flags.append("LEAGUEPEDIA_TIME_TBD")
        elif how == "tournament-page":
            flags.append("FIXTURE_NOT_ON_LEAGUEPEDIA_SCHEDULE")
        if row and row.get("start_utc"):
            try:
                hs = datetime.fromisoformat(f["start_utc"].replace("Z", "+00:00"))
                ls = datetime.fromisoformat(row["start_utc"].replace("Z", "+00:00"))
                if abs((hs - ls).total_seconds()) > 1800:
                    flags.append("START_TIME_MISMATCH")
            except Exception:
                pass

        # sources for this row
        sources = [{"name": "Hotspawn fixture", "url": f.get("hotspawn_url") or f.get("source_lobby"),
                    "claim": "Teams, tournament, start time (fixture list only; never a probability input)."}]
        for r in recs:
            sources.append({"name": r["source"], "url": r["url"],
                            "claim": f"Two-way de-vigged line: {r['prob_team1']*100:.1f}% {t1}."})
        if eff_page:
            lp_url = "https://lol.fandom.com/wiki/" + eff_page.replace(" ", "_")
            claim_note = (f"Recorded results & schedule ({eff_page})." if row
                          else f"Verified tournament overview & standings ({eff_page}; pairing not yet on MatchSchedule).")
            sources.append({"name": "Leaguepedia tournament", "url": lp_url, "claim": claim_note})
        elif model_method:
            sources.append({"name": "Leaguepedia results",
                            "url": "https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule",
                            "claim": "Recorded match results used for the Elo model."})
        for meta in (meta1, meta2):
            if meta and meta.get("source_url"):
                u = meta["source_url"]
                if not any(s.get("url") == u for s in sources):
                    sources.append({"name": "Leaguepedia participant verification", "url": u,
                                    "claim": meta.get("note") or "Verified canonical participant."})

        evidence_bits = []
        if recs:
            names = ", ".join(sorted({r["source"] for r in recs}))
            evidence_bits.append(f"Market consensus from {names} ({len(recs)} independent book(s), "
                                 f"dispersion {market['dispersion']*100:.1f} pts).")
        if model_method:
            if model_method == "MODEL_STANDINGS":
                s1_txt = (f"{st1['win_series']}-{st1['loss_series']} series" if st1 else f"{g1} games")
                s2_txt = (f"{st2['win_series']}-{st2['loss_series']} series" if st2 else f"{g2} games")
                evidence_bits.append(f"Split standings + Elo {model['elo_team1']} vs {model['elo_team2']} "
                                     f"({s1_txt} vs {s2_txt} in {eff_page or 'split'}).")
            elif model.get("elo_team1") is not None and model.get("elo_team2") is not None:
                evidence_bits.append(f"Elo {model['elo_team1']} vs {model['elo_team2']} "
                                     f"({g1} / {g2} games in 365d; competition bases "
                                     f"{model['team1_competition_base']} / {model['team2_competition_base']}).")
            elif model.get("elo_known") is not None:
                evidence_bits.append(f"Only one side rated ({model['elo_known']}, {model['games_known_365d']} games); "
                                     f"other side uses {model['prior_used']} {model['elo_prior']}.")
        if row and row.get("start_utc") and "START_TIME_MISMATCH" in flags:
            evidence_bits.append(f"Leaguepedia lists start {row['start_utc']} (differs from Hotspawn feed).")
        for meta in (meta1, meta2):
            if meta and meta.get("note"):
                evidence_bits.append(meta["note"])
        if not evidence_bits:
            evidence_bits.append("No external market and no recorded history for either team.")

        # ---- per-row record of the official table actually used -----------------
        standings_block = None
        if st1 or st2:
            def _st(s):
                if not s:
                    return None
                ws, ls = s.get("win_series"), s.get("loss_series")
                return {"wins": ws, "losses": ls,
                        "win_games": s.get("win_games"), "loss_games": s.get("loss_games"),
                        "kind": "series" if (int(ws or 0) + int(ls or 0)) > 0 else "games",
                        "sample": int(ws or 0) + int(ls or 0) or int(s.get("win_games") or 0) + int(s.get("loss_games") or 0),
                        "page": s.get("overview")}
            page_name = (st1 or st2 or {}).get("overview") or eff_page
            standings_block = {
                "page": page_name,
                "url": "https://lol.fandom.com/wiki/" + page_name.replace(" ", "_") if page_name else None,
                "team1": _st(st1), "team2": _st(st2),
                "multi_division": bool(_norm_team(page_name) in multi_div) if page_name else False,
            }

        if method.startswith("MARKET"):
            why = f"Priced from {len(recs)} independent external line(s); the pick follows the market consensus."
        elif method == "MODEL_ELO":
            why = f"No external line. Elo from {g1}/{g2} recorded series in the last 365 days."
        elif method == "MODEL_ELO_THIN":
            why = (f"No external line. Elo from recorded series, but the thinner side has only "
                   f"{min(g1, g2)} series in 365 days, so the edge is shrunk toward 50%.")
        elif method == "MODEL_STANDINGS":
            bits = []
            for label, st, g in ((t1, st1, g1), (t2, st2, g2)):
                if st and (int(st.get("win_series") or 0) + int(st.get("loss_series") or 0)) > 0:
                    bits.append(f"{label} from its official {st.get('win_series')}-{st.get('loss_series')} record")
                elif st:
                    bits.append(f"{label} from its official game record {st.get('win_games')}-{st.get('loss_games')}")
                else:
                    bits.append(f"{label} from {g} recorded series")
            why = ("No external line. Line built from the official Leaguepedia standings "
                   f"({(st1 or st2 or {}).get('overview') or eff_page}): " + "; ".join(bits) + ".")
            if "MULTI_DIVISION_STANDINGS" in flags:
                why += (" That table combines several divisions, so the edge is halved and the row "
                        "is capped at low confidence.")
        elif method == "MODEL_LEAGUE_PRIOR":
            known_side = (model or {}).get("known_side")
            unknown = t2 if known_side == "team1" else t1
            why = (f"No external line and no series history or standings row for {unknown}. The "
                   f"{prior_source} ({round(prior)}) is substituted for that side and the edge is shrunk.")
        else:
            why = ("No external betting line, no recorded series and no standings row for either team. "
                   "The 50/50 is a labelled placeholder, not a pick.")

        out.append({
            **{k: f.get(k) for k in ("id", "team1", "team2", "tournament", "competition_id", "tier",
                                     "stage", "points", "best_of", "start_utc", "status",
                                     "hotspawn_url", "source_lobby", "crowd")},
            "standings": standings_block,
            "why": why,
            "source_url": (standings_block or {}).get("url") or (
                ("https://lol.fandom.com/wiki/" + eff_page.replace(" ", "_")) if eff_page else None),
            "leaguepedia_page": eff_page or None,
            "leaguepedia_url": ("https://lol.fandom.com/wiki/" + eff_page.replace(" ", "_")) if eff_page else None,
            "fixture_match": how,
            "prob_team1": round(p1, 4),
            "prob_team2": round(1 - p1, 4),
            "pick": pick,
            "pick_prob": round(pick_prob, 4),
            "method": method,
            "method_label": METHOD_LABELS.get(method, method),
            "confidence": confidence,
            "model": model,
            "market": market,
            "evidence": " ".join(evidence_bits),
            "flags": sorted(set(flags)),
            "sources": sources,
            "resolved": method != "UNRESOLVED",
        })

    out.sort(key=lambda m: (m["start_utc"], m["tournament"], m["team1"]))
    counts = Counter(m["method"] for m in out)
    resolved = sum(1 for m in out if m["resolved"])
    bt = backtest(leaguepedia["results"], now, priors)
    payload = {
        "generated_at": utc_iso(now),
        "model": {
            "matches_used": rating_data["matches_used"],
            "teams_rated": len(ratings),
            "teams_with_recent_games": sum(1 for v in recent.values() if v > 0),
            "half_life_days": 365, "k_base": 24,
            "competition_tier_priors": True,
            "competitions_with_prior": len(comp_prior),
            "global_prior": round(global_prior, 1),
            "backtest": bt,
            "top_ratings": [{"team": k, "elo": round(v), "games_365d": recent.get(k, 0)}
                            for k, v in sorted(ratings.items(), key=lambda kv: -kv[1])[:25]],
        },
        "market_unmatched": market_unmatched,
        "coverage": {
            "fixtures": len(out),
            "resolved": resolved,
            "unresolved": len(out) - resolved,
            "resolved_pct": round(100 * resolved / len(out), 1) if out else 0,
            "with_external_market": sum(1 for m in out if m["market"]),
            "with_model": sum(1 for m in out if m["method"].startswith("MODEL")),
            "with_team_specific_model": sum(
                1 for m in out if m["method"] in ("MODEL_ELO", "MODEL_ELO_THIN", "MODEL_STANDINGS")
            ),
            "with_prior_only": counts.get("MODEL_LEAGUE_PRIOR", 0),
            "with_standings_line": counts.get("MODEL_STANDINGS", 0),
            "published_picks": len(out),
            "both_market_and_model": sum(1 for m in out if m["market"] and m["model"]),
            "counts_by_method": dict(counts),
        },
        "matches": out,
    }
    return payload


def run(hotspawn, leaguepedia, markets, alias_path="data/aliases.json"):
    payload = build_matches(hotspawn, leaguepedia, markets, load_aliases(alias_path))
    write_json("data/cache/model.json", payload)
    log(f"model: {payload['coverage']}")
    return payload


if __name__ == "__main__":
    from lib_common import load_json as _l
    hs, lp, mk = _l("data/cache/hotspawn.json"), _l("data/cache/leaguepedia.json"), _l("data/cache/markets.json")
    if not (hs and lp and mk):
        raise SystemExit("run the fetchers first")
    run(hs, lp, mk)

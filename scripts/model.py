#!/usr/bin/env python3
"""Own-line model + market consensus.

No Hotspawn number is ever used as an input. Hotspawn supplies the fixture list
only. Probabilities come from:
  * external sportsbook / prediction-market prices (Pinnacle, Bovada, Polymarket),
  * our own Elo built from Leaguepedia recorded results, with a competition
    median prior when a team has no usable history.

The output is a per-fixture probability, a pick, a method, a confidence level and
an explicit list of source links for every row.
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher

from lib_common import (clamp, load_json, log, median, norm, now_utc, prob_from_elo,
                        utc_iso, write_json)

DEFAULT_ALIASES = {
    "hotspawn_to_leaguepedia": {
        "LOS": "LOS",
        "LØS": "LOS",
        "LYON": "LYON",
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
    },
    "market_aliases": {
        "pinnacle": {
            "Liquid": "Team Liquid",
            "Bilibili": "Bilibili Gaming",
            "Secret Whales": "Team Secret Whales",
            "Invictus": "Invictus Gaming",
            "Hanwha Life": "Hanwha Life Esports",
            "G2": "G2 Esports",
        },
        "bovada": {
            "Los Grandes": "LOS",
            "Team Secret": "Team Secret Whales",
            "Lyon Gaming": "LYON",
        },
        "polymarket": {},
    },
}

METHOD_LABELS = {
    "MARKET_CONSENSUS": "Market consensus (2+ sources)",
    "MARKET_SINGLE": "Single external market",
    "MODEL_ELO": "Own Elo model",
    "MODEL_ELO_THIN": "Own Elo model (thin history)",
    "MODEL_LEAGUE_PRIOR": "League/overall prior (no team history)",
    "UNRESOLVED": "Unresolved - no verified signal",
}


def sim(a: str, b: str) -> float:
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def contains(a: str, b: str) -> bool:
    na, nb = norm(a), norm(b)
    return bool(na and nb) and (na in nb or nb in na)


def load_aliases(path="data/aliases.json"):
    cfg = load_json(path, {}) or {}
    merged = {"hotspawn_to_leaguepedia": dict(DEFAULT_ALIASES["hotspawn_to_leaguepedia"]),
              "market_aliases": {k: dict(v) for k, v in DEFAULT_ALIASES["market_aliases"].items()}}
    for k, v in (cfg.get("hotspawn_to_leaguepedia") or {}).items():
        merged["hotspawn_to_leaguepedia"][k] = v
    for src, mapping in (cfg.get("market_aliases") or {}).items():
        merged["market_aliases"].setdefault(src, {}).update(mapping)
    return merged


# Competition strength priors -------------------------------------------------
# Pooling every league into one Elo pool without cross-play inflates teams that
# farm wins in weak or academy leagues. Each team is therefore anchored to a
# base rating for the tier of the competition it actually plays in (modal
# competition over the last 365 days). Tiers follow the official Riot ecosystem
# pyramid: international > top regional leagues > ERLs/second tiers > national
# and third divisions > academy/amateur. Documented in methodology.html.
_TIER_RULES = (
    ("academy", 1440), ("youth", 1440), ("rookie", 1440), ("university", 1400),
    ("qualifier", 1430), ("nexus tour", 1430), ("amateur", 1430),
    ("world championship", 1720), ("worlds", 1720), ("msi", 1720),
    ("first stand", 1720), ("asia masters", 1710),
    ("emea masters", 1640),
    ("lck cl", 1585), ("ldl", 1585), ("nacl", 1560),
    ("north american challengers", 1560), ("circuito desafiante", 1560),
    ("challengers", 1560),
    ("lck", 1690), ("lpl", 1690), ("lec", 1650), ("lcs", 1650), ("lta", 1630),
    ("cblol", 1625), ("lcp", 1615), ("pcs", 1600), ("vcs", 1595), ("ljl", 1580),
    ("lla", 1580), ("tcl", 1580), ("lco", 1570),
    ("prime league 1", 1560), ("lfl", 1550), ("nlc", 1545), ("ultraliga", 1540),
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
        ka, kb = norm(a), norm(b)
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


class Resolver:
    def __init__(self, names, aliases):
        self.names = sorted({str(n).strip() for n in names if str(n or "").strip()})
        self.by_norm = {norm(n): n for n in self.names}
        self.aliases = {norm(k): v for k, v in (aliases or {}).items()}

    def resolve(self, name):
        if not name:
            return None
        n = norm(name)
        if n in self.aliases:
            return self.by_norm.get(norm(self.aliases[n]), self.aliases[n])
        if n in self.by_norm:
            return self.by_norm[n]
        # containment (short market names such as "Liquid" -> "Team Liquid")
        cands = [x for x in self.names if contains(name, x)]
        if len(cands) == 1:
            return cands[0]
        if cands:
            cands.sort(key=lambda x: abs(len(norm(x)) - len(n)))
            return cands[0]
        best, score = None, 0.0
        for x in self.names:
            s = sim(name, x)
            if s > score:
                best, score = x, s
        return best if score >= 0.88 else None


def match_fixture_to_schedule(fixture, schedule_rows):
    """Find the Leaguepedia row for a Hotspawn fixture. Returns (row, how) or (None, reason)."""
    ft1, ft2 = fixture["team1"], fixture["team2"]
    start = datetime.fromisoformat(fixture["start_utc"].replace("Z", "+00:00"))
    best = None
    best_score = 0.0
    best_how = None
    for row in schedule_rows:
        try:
            when = datetime.fromisoformat(row["start_utc"].replace("Z", "+00:00"))
        except Exception:
            continue
        hours = abs((when - start).total_seconds()) / 3600.0
        if hours > 36:
            continue
        s1 = 1.0 if norm(row["team1"]) == norm(ft1) and norm(row["team2"]) == norm(ft2) else 0.0
        s2 = 1.0 if norm(row["team1"]) == norm(ft2) and norm(row["team2"]) == norm(ft1) else 0.0
        if s1 or s2:
            score = 100 - hours
            how = "exact-pair"
        else:
            f1 = max(sim(ft1, row["team1"]), sim(ft1, row["team2"]))
            f2 = max(sim(ft2, row["team1"]), sim(ft2, row["team2"]))
            if f1 < 0.84 or f2 < 0.84:
                continue
            score = (f1 + f2) * 50 - hours
            how = "fuzzy-pair"
        if score > best_score:
            best, best_score, best_how = row, score, how
    return best, best_how


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
        r1 = ratings.get(norm(r["team1"]))
        r2 = ratings.get(norm(r["team2"]))
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
        team_comps[norm(r["team1"])][r["overview"]] += 1
        team_comps[norm(r["team2"])][r["overview"]] += 1
    priors = {}
    for team, comps in team_comps.items():
        base = competition_base(comps.most_common(1)[0][0])
        if base:
            priors[team] = base

    rating_data = build_ratings(leaguepedia["results"], now, priors=priors)
    ratings = rating_data["ratings"]
    recent = rating_data["recent_games"]
    schedule_rows = leaguepedia.get("schedule") or []

    lp_names = set()
    for r in leaguepedia["results"] + schedule_rows:
        lp_names.add(str(r["team1"]))
        lp_names.add(str(r["team2"]))
    for t in leaguepedia.get("teams") or []:
        if t.get("Name") not in (None, ""):
            lp_names.add(str(t["Name"]))
    resolver = Resolver(lp_names, aliases["hotspawn_to_leaguepedia"])

    # competition prior: median rating of rated teams in the same tournament page
    comp_teams = defaultdict(set)
    for r in leaguepedia["results"]:
        comp_teams[r["overview"]].add(norm(r["team1"]))
        comp_teams[r["overview"]].add(norm(r["team2"]))
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

    # ---- market matching (closest start time wins; ±36h) -----------------
    market_fixtures = defaultdict(list)
    market_unmatched = []
    for rec in markets.get("records") or []:
        rec_start = datetime.fromisoformat(rec["start_utc"].replace("Z", "+00:00"))
        best_pair = None
        for f in hotspawn["fixtures"]:
            fstart = datetime.fromisoformat(f["start_utc"].replace("Z", "+00:00"))
            delta_h = abs((fstart - rec_start).total_seconds()) / 3600.0
            if delta_h > 36:
                continue
            src_aliases = aliases["market_aliases"].get(rec["source_key"], {})
            a_raw = src_aliases.get(rec["team_a"], rec["team_a"])
            b_raw = src_aliases.get(rec["team_b"], rec["team_b"])
            a = resolver.resolve(a_raw)
            b = resolver.resolve(b_raw)
            f1, f2 = f["team1"], f["team2"]
            pair_ok = ((norm(a) == norm(f1) and norm(b) == norm(f2)) or
                       (norm(a) == norm(f2) and norm(b) == norm(f1)) or
                       (contains(a_raw, f1) and contains(b_raw, f2)) or
                       (contains(a_raw, f2) and contains(b_raw, f1)))
            if not pair_ok:
                s1 = max(sim(a_raw, f1), sim(b_raw, f1))
                s2 = max(sim(a_raw, f2), sim(b_raw, f2))
                pair_ok = s1 >= 0.86 and s2 >= 0.86
            if not pair_ok:
                continue
            # A game-level market is not a series probability: only allow it on Bo1.
            # Belt and braces: detect it from the label too, so a stale cache or a
            # different feed cannot leak a Game-N price into a series row.
            market_note = f"{rec.get('note') or ''} {rec.get('competition') or ''}".lower()
            is_game_market = ((rec.get("raw") or {}).get("market_type") == "game"
                              or bool(re.search(r"\b(game|map)\s*\d", market_note)))
            if is_game_market and f.get("best_of") != 1:
                continue
            if best_pair is None or delta_h < best_pair[0]:
                best_pair = (delta_h, f)
        if not best_pair:
            market_unmatched.append({"source": rec["source"], "teams": [rec["team_a"], rec["team_b"]],
                                     "start_utc": rec["start_utc"], "url": rec["url"]})
            continue
        delta_h, f = best_pair
        src_aliases = aliases["market_aliases"].get(rec["source_key"], {})
        a_raw = src_aliases.get(rec["team_a"], rec["team_a"])
        b_raw = src_aliases.get(rec["team_b"], rec["team_b"])
        flip = (contains(a_raw, f["team2"]) and not contains(a_raw, f["team1"])) or (
            norm(a_raw) == norm(f["team2"]) and norm(b_raw) == norm(f["team1"]))
        p1 = rec["prob_b"] if flip else rec["prob_a"]
        market_fixtures[f["id"]].append({
            "source": rec["source"], "source_key": rec["source_key"], "url": rec["url"],
            "prob_team1": p1, "prob_team2": round(1 - p1, 6),
            "decimal_team1": rec.get("decimal_b") if flip else rec.get("decimal_a"),
            "decimal_team2": rec.get("decimal_a") if flip else rec.get("decimal_b"),
            "note": rec.get("note"), "start_utc": rec["start_utc"],
            "start_delta_hours": round(delta_h, 1), "competition": rec.get("competition")})

    # ---- per-fixture probability -----------------------------------------
    WEIGHTS = {"pinnacle": 1.0, "bovada": 0.8, "polymarket": 0.7}
    out = []
    for f in hotspawn["fixtures"]:
        row, how = match_fixture_to_schedule(f, schedule_rows)
        f = dict(f)
        t1, t2 = f["team1"], f["team2"]
        k1, k2 = resolver.resolve(t1), resolver.resolve(t2)
        if row:
            # prefer canonical Leaguepedia spellings from the matched row
            for n, disp in {(norm(row["team1"]), row["team1"]), (norm(row["team2"]), row["team2"])}:
                if n == norm(t1):
                    k1 = resolver.resolve(disp) or k1
                if n == norm(t2):
                    k2 = resolver.resolve(disp) or k2
        r1 = ratings.get(norm(k1)) if k1 else None
        r2 = ratings.get(norm(k2)) if k2 else None
        g1 = recent.get(norm(k1), 0) if k1 else 0
        g2 = recent.get(norm(k2), 0) if k2 else 0
        comp1 = team_comps[norm(k1)].most_common(1)[0][0] if k1 and team_comps[norm(k1)] else None
        comp2 = team_comps[norm(k2)].most_common(1)[0][0] if k2 and team_comps[norm(k2)] else None
        base1 = priors.get(norm(k1)) if k1 else None
        base2 = priors.get(norm(k2)) if k2 else None
        # "Cross-league" means a real strength-tier gap, not just two different
        # split names in the same division.
        cross_league = bool(base1 and base2 and abs(base1 - base2) >= 60 and
                            team_comps[norm(k1)].get(comp1, 0) >= 5 and
                            team_comps[norm(k2)].get(comp2, 0) >= 5)
        page = row["overview"] if row else ""
        prior = comp_prior.get(page) or competition_base(page) or global_prior
        prior_source = ("competition median" if page in comp_prior and comp_prior.get(page) != competition_base(page)
                        else "competition tier prior" if page else "global median")

        flags = []
        model = model_prob = model_method = None
        if r1 is not None and r2 is not None and g1 >= 3 and g2 >= 3:
            raw = prob_from_elo(r1, r2)
            shrink = min(g1, g2) / (min(g1, g2) + 8.0)
            p = 0.5 + (raw - 0.5) * shrink
            h2h = rating_data["h2h"].get(tuple(sorted((norm(k1), norm(k2)))))
            h2h_info = None
            if h2h:
                first_is_k1 = tuple(sorted((norm(k1), norm(k2))))[0] == norm(k1)
                wins_k1 = h2h[0] if first_is_k1 else h2h[1]
                p, h2h_info = blend_h2h(p, sum(h2h), wins_k1)
            model_prob = p
            model_method = "MODEL_ELO" if min(g1, g2) >= 8 else "MODEL_ELO_THIN"
            model = {"elo_team1": round(r1), "elo_team2": round(r2),
                     "games_team1_365d": g1, "games_team2_365d": g2,
                     "shrink": round(shrink, 3), "h2h": h2h_info, "prior_used": None,
                     "tournament_page": page,
                     "team1_recent_competition": comp1, "team2_recent_competition": comp2,
                     "cross_league": cross_league,
                     "team1_competition_base": round(priors.get(norm(k1), 1500)),
                     "team2_competition_base": round(priors.get(norm(k2), 1500))}
            if cross_league:
                flags.append("CROSS_LEAGUE_MODEL")
        elif (r1 is not None and g1 >= 3) or (r2 is not None and g2 >= 3):
            known_k1 = r1 is not None and g1 >= 3
            known_r = r1 if known_k1 else r2
            known_g = g1 if known_k1 else g2
            raw = prob_from_elo(known_r, prior) if known_k1 else prob_from_elo(prior, known_r)
            shrink = known_g / (known_g + 20.0)
            model_prob = 0.5 + (raw - 0.5) * shrink
            model_method = "MODEL_LEAGUE_PRIOR"
            model = {"elo_known": round(known_r), "elo_prior": round(prior),
                     "known_side": "team1" if known_k1 else "team2",
                     "games_known_365d": known_g, "shrink": round(shrink, 3),
                     "prior_used": prior_source, "tournament_page": page,
                     "team1_recent_competition": comp1, "team2_recent_competition": comp2}
            flags.append("ONE_TEAM_NO_HISTORY")
        else:
            flags.append("NO_TEAM_HISTORY")

        # ---- external market consensus
        recs = market_fixtures.get(f["id"], [])
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
                       if r["source_key"] in ("pinnacle", "bovada")]
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
        if row:
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
        if row:
            sources.append({"name": "Leaguepedia tournament",
                            "url": "https://lol.fandom.com/wiki/" + row["overview"].replace(" ", "_"),
                            "claim": f"Recorded results used for the Elo model ({row['overview']})."})
        elif model_method:
            sources.append({"name": "Leaguepedia results",
                            "url": "https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule",
                            "claim": "Recorded match results used for the Elo model."})

        evidence_bits = []
        if recs:
            names = ", ".join(sorted({r["source"] for r in recs}))
            evidence_bits.append(f"Market consensus from {names} ({len(recs)} line(s), "
                                 f"dispersion {market['dispersion']*100:.1f} pts).")
        if model_method:
            if model.get("elo_team1") is not None and model.get("elo_team2") is not None:
                evidence_bits.append(f"Elo {model['elo_team1']} vs {model['elo_team2']} "
                                     f"({g1} / {g2} games in 365d; competition bases "
                                     f"{model['team1_competition_base']} / {model['team2_competition_base']}).")
            elif model.get("elo_known") is not None:
                evidence_bits.append(f"Only one side rated ({model['elo_known']}, {model['games_known_365d']} games); "
                                     f"other side uses {model['prior_used']} {model['elo_prior']}.")
        if not evidence_bits:
            evidence_bits.append("No external market and no recorded history for either team.")

        out.append({
            **{k: f.get(k) for k in ("id", "team1", "team2", "tournament", "competition_id", "tier",
                                     "stage", "points", "best_of", "start_utc", "status",
                                     "hotspawn_url", "source_lobby", "crowd")},
            "leaguepedia_page": row["overview"] if row else None,
            "leaguepedia_url": ("https://lol.fandom.com/wiki/" + row["overview"].replace(" ", "_")) if row else None,
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
            "with_team_specific_model": sum(1 for m in out if m["method"] in ("MODEL_ELO", "MODEL_ELO_THIN")),
            "with_prior_only": counts.get("MODEL_LEAGUE_PRIOR", 0),
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

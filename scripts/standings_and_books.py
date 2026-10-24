"""Additional external sportsbook feeds, prop filters, and official standings math.

All sources here are strictly outside Hotspawn (Hotspawn is never used as a
probability source):
  * Kambi offering JSON API (Unibet / Paf / LeoVegas / BetRivers sportsbook network)
  * Pinnacle Arcadia main-match filter (drops child prop/special boards)
  * Leaguepedia Cargo Standings table client + smoothed Bradley-Terry line solver
  * Liquipedia MediaWiki API discovery probe (API-only, gzip, >=2.2s spacing, CC-BY-SA 3.0)
"""
from __future__ import annotations

import json
import math
import re
import time
import urllib.parse
from collections import Counter
from datetime import datetime, timezone

from lib_common import clamp, devig_two, fetch, get_json, log, norm, utc_iso

KAMBI_ENDPOINTS = (
    ("https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/"
     "esports/league_of_legends/all/all/matches.json?lang=en_GB&market=ZZ&useCombined=true"),
    ("https://eu-offering-api.kambicdn.com/offering/v2018/paf/listView/"
     "esports/league_of_legends/all/all/matches.json?lang=en_GB&market=ZZ&useCombined=true"),
)
KAMBI_PAGE = "https://www.unibet.com/betting/sports/filter/esports/league_of_legends"

LIQUIPEDIA_API = "https://liquipedia.net/leagueoflegends/api.php"
LIQUIPEDIA_PAGE = "https://liquipedia.net/leagueoflegends/api.php?action=query&meta=siteinfo&format=json"

PROP_SUFFIX_RE = re.compile(
    r"(\(\s*(?:kills?|towers?|turrets?|barons?|dragons?|inhibitors?|first\b[^)]*|map\s*\d+|game\s*\d+|handicap|total)\s*\))"
    r"|(\bcorrect\s+score\b)"
    r"|(\b\d+\s*,\s*[a-z0-9 .'-]+\s+\d+$)",
    re.I,
)


def is_pinnacle_main_matchup(matchup: dict) -> bool:
    """True only for main full-match moneyline boards, never child prop/special boards."""
    if not isinstance(matchup, dict):
        return False
    if matchup.get("parentId") is not None or matchup.get("parent"):
        return False
    if matchup.get("special"):
        return False
    mtype = str(matchup.get("type") or "matchup").strip().lower()
    if mtype != "matchup":
        return False
    units = str(matchup.get("units") or "regular").strip().lower()
    if units != "regular":
        return False
    parts = matchup.get("participants") or []
    if len(parts) != 2:
        return False
    for p in parts:
        pname = str((p or {}).get("name") or "")
        if not pname or PROP_SUFFIX_RE.search(pname):
            return False
    return True


def fetch_kambi() -> dict:
    """Fetch pre-match two-way League of Legends match odds from Kambi's public JSON CDN."""
    status = {
        "source": "Unibet (Kambi)",
        "key": "unibet",
        "url": KAMBI_PAGE,
        "status": "error",
        "count": 0,
    }
    data, last_resp, used = None, {}, None
    for url in KAMBI_ENDPOINTS:
        data, last_resp = get_json(url, timeout=30, retries=2)
        if isinstance(data, dict) and isinstance(data.get("events"), list):
            used = url
            break
        time.sleep(0.4)
    if not isinstance(data, dict) or not isinstance(data.get("events"), list):
        status["status"] = "unavailable"
        status["error"] = f"Kambi CDN HTTP {last_resp.get('status')} (no events array)"
        return {"status": status, "records": []}

    records = []
    comps = set()
    seen = set()
    for item in data.get("events") or []:
        ev = item.get("event") or {}
        if str(ev.get("state") or "").upper() == "STARTED":
            continue
        t_a = ev.get("homeName")
        t_b = ev.get("awayName")
        if not t_a or not t_b or PROP_SUFFIX_RE.search(str(t_a)) or PROP_SUFFIX_RE.search(str(t_b)):
            continue
        start_raw = ev.get("start")
        try:
            start_dt = datetime.fromisoformat(str(start_raw).replace("Z", "+00:00"))
        except Exception:
            continue
        comp = " / ".join(p.get("name", "") for p in (ev.get("path") or []) if p.get("name"))
        best_offer = None
        for bo in item.get("betOffers") or []:
            crit = str((bo.get("criterion") or {}).get("label") or "").lower()
            btype = str((bo.get("betOfferType") or {}).get("name") or "").lower()
            outs = bo.get("outcomes") or []
            if len(outs) != 2:
                continue
            if re.search(r"(map|game|kill|blood|tower|baron|dragon|handicap|total)", crit):
                continue
            if btype == "match" or crit in ("match odds", "match winner", "full time", "moneyline"):
                best_offer = bo
                break
        if not best_offer:
            continue
        outs = best_offer["outcomes"]
        da = (outs[0].get("odds") or 0) / 1000.0
        db = (outs[1].get("odds") or 0) / 1000.0
        dv = devig_two(da, db)
        if not dv:
            continue
        key = (norm(t_a), norm(t_b), utc_iso(start_dt)[:10])
        if key in seen:
            continue
        seen.add(key)
        if comp:
            comps.add(comp)
        pa, pb = clamp(dv[0]), clamp(dv[1])
        s = pa + pb
        records.append({
            "source": "Unibet",
            "source_key": "unibet",
            "competition": comp,
            "start_utc": utc_iso(start_dt),
            "team_a": outs[0].get("label") or t_a,
            "team_b": outs[1].get("label") or t_b,
            "prob_a": round(pa / s, 4),
            "prob_b": round(pb / s, 4),
            "decimal_a": round(da, 4),
            "decimal_b": round(db, 4),
            "url": KAMBI_PAGE,
            "note": f"Unibet (Kambi) match odds (event {ev.get('id')})",
            "raw": {"event_id": ev.get("id"), "criterion": (best_offer.get("criterion") or {}).get("label")},
        })
    status.update({
        "status": "ok" if records else "no_data",
        "count": len(records),
        "feed": used,
        "competitions": sorted(comps),
        "note": "Public Kambi sportsbook JSON feed (Unibet network); pre-match match odds only.",
    })
    return {"status": status, "records": records}


def fetch_leaguepedia_standings(pages: list[str], export_base: str = "https://lol.fandom.com/wiki/Special:CargoExport?",
                                sleep_s: float = 2.6) -> tuple[list[dict], list[dict]]:
    """Fetch official Leaguepedia Cargo `Standings` rows for active tournament pages."""
    clean_pages = sorted({p.strip() for p in pages if p and p.strip()})
    all_rows: list[dict] = []
    errors: list[dict] = []
    # Query in small batches of up to 6 pages using OR clauses to stay polite on rate limits
    for idx in range(0, len(clean_pages), 6):
        batch = clean_pages[idx:idx + 6]
        escaped = [p.replace("'", "''") for p in batch]
        where = " OR ".join(f"OverviewPage='{p}'" for p in escaped)
        params = {
            "tables": "Standings",
            "fields": "OverviewPage,Team,Place,WinSeries,LossSeries,TieSeries,WinGames,LossGames,N",
            "where": where,
            "limit": "500",
            "format": "json",
        }
        r = fetch(export_base + urllib.parse.urlencode(params), timeout=60, retries=3)
        time.sleep(sleep_s)
        if r["status"] != 200:
            errors.append({"batch": batch, "error": f"HTTP {r['status']}"})
            continue
        try:
            data = json.loads(r["text"])
        except Exception:
            errors.append({"batch": batch, "error": "non-JSON standings response"})
            continue
        if isinstance(data, list):
            for row in data:
                page = row.get("OverviewPage") or ""
                team = row.get("Team") or ""
                if not page or not team:
                    continue
                def _int(k):
                    v = row.get(k)
                    try:
                        return int(v) if v not in (None, "") else 0
                    except (TypeError, ValueError):
                        return 0
                all_rows.append({
                    "overview": page,
                    "team": str(team).strip(),
                    "place": str(row.get("Place") or ""),
                    "win_series": _int("WinSeries"),
                    "loss_series": _int("LossSeries"),
                    "tie_series": _int("TieSeries"),
                    "win_games": _int("WinGames"),
                    "loss_games": _int("LossGames"),
                })
    log(f"leaguepedia standings: {len(all_rows)} rows across {len(clean_pages)} pages ({len(errors)} errors)")
    return all_rows, errors


def build_standings_index(standings_rows: list[dict]) -> dict[tuple[str, str], dict]:
    """Index unambiguous non-empty standings records by (OverviewPage, norm(team)).

    Safety rules:
      * If the same (OverviewPage, norm(team)) appears multiple times (multi-division
        page sharing team names), mark ambiguous and DO NOT index it.
      * If a team has 0 completed series AND 0 completed games (0-0 start of split),
        DO NOT index it (0-0 is not evidence).
    """
    counts = Counter((r["overview"], norm(r["team"])) for r in (standings_rows or []) if r.get("overview") and r.get("team"))
    idx: dict[tuple[str, str], dict] = {}
    for r in standings_rows or []:
        key = (r.get("overview") or "", norm(r.get("team") or ""))
        if not key[0] or not key[1] or counts[key] > 1:
            continue
        n_series = int(r.get("win_series") or 0) + int(r.get("loss_series") or 0) + int(r.get("tie_series") or 0)
        n_games = int(r.get("win_games") or 0) + int(r.get("loss_games") or 0)
        if n_series == 0 and n_games == 0:
            continue
        idx[key] = r
    return idx


def standings_probability(rec1: dict | None, rec2: dict | None) -> tuple[float, dict] | tuple[None, None]:
    """Compute smoothed empirical-Bayes win probability from official division standings.

    Requires BOTH teams to have at least 1 completed match/game in the exact same
    OverviewPage. Never fabricates probabilities for 0-0 teams.
    """
    if not rec1 or not rec2:
        return None, None
    if rec1.get("overview") != rec2.get("overview"):
        return None, None

    def _strength(r: dict) -> tuple[float, float, str]:
        ws, ls, ts = int(r.get("win_series") or 0), int(r.get("loss_series") or 0), int(r.get("tie_series") or 0)
        wg, lg = int(r.get("win_games") or 0), int(r.get("loss_games") or 0)
        ns = ws + ls + ts
        ng = wg + lg
        if ns > 0:
            p_ser = (ws + 0.5 * ts + 2.0) / (ns + 4.0)
            if ng > 0:
                p_gam = (wg + 3.0) / (ng + 6.0)
                return 0.7 * p_ser + 0.3 * p_gam, float(ns), f"{ws}-{ls}" + (f"-{ts}" if ts else "")
            return p_ser, float(ns), f"{ws}-{ls}" + (f"-{ts}" if ts else "")
        p_gam = (wg + 3.0) / (ng + 6.0)
        return p_gam, float(ng) / 2.0, f"{wg}-{lg} games"

    s1, n1, lbl1 = _strength(rec1)
    s2, n2, lbl2 = _strength(rec2)
    o1 = s1 / max(1e-6, 1.0 - s1)
    o2 = s2 / max(1e-6, 1.0 - s2)
    raw_p1 = o1 / (o1 + o2)
    n_eff = min(n1, n2)
    shrink = n_eff / (n_eff + 3.0)
    p1 = clamp(0.5 + (raw_p1 - 0.5) * shrink, 0.05, 0.95)
    meta = {
        "tournament_page": rec1["overview"],
        "record_team1": lbl1,
        "record_team2": lbl2,
        "series_n_min": round(n_eff, 1),
        "shrink": round(shrink, 3),
    }
    return p1, meta


_LIQUIPEDIA_PREFIX_RULES: tuple[tuple[str, str], ...] = (
    ("worlds", "World_Championship/2026"),
    ("world championship", "World_Championship/2026"),
    ("prm ", "Prime_League"),
    ("prime league", "Prime_League"),
    ("arabian", "Arabian_League"),
    ("komplettligaen", "Komplettligaen"),
    ("lcp", "LCP/2027"),
    ("lgc", "Game_Changers"),
    ("game changers", "Game_Changers"),
    ("em ", "EMEA_Masters"),
    ("emea masters", "EMEA_Masters"),
)


def _normalise_liquipedia_prefixes(prefixes) -> list[str]:
    """Map raw tournament labels to deduplicated canonical Liquipedia page prefixes (max 8)."""
    out: list[str] = []
    seen: set[str] = set()
    for raw in prefixes or ():
        s = str(raw or "").strip()
        if not s:
            continue
        low = s.lower()
        mapped = None
        for needle, target in _LIQUIPEDIA_PREFIX_RULES:
            if needle in low:
                mapped = target
                break
        if mapped is None:
            # Keep explicit MediaWiki prefixes (e.g. Prime_League), otherwise take first title token
            if "_" in s or "/" in s:
                mapped = s.replace(" ", "_")
            else:
                continue
        if mapped not in seen:
            seen.add(mapped)
            out.append(mapped)
        if len(out) >= 8:
            break
    return out or ["World_Championship/2026", "Prime_League", "Arabian_League", "Komplettligaen"]


def probe_liquipedia_pages(prefixes: tuple[str, ...] = ("Prime_League", "World_Championship/2026", "Komplettligaen")) -> dict:
    """Compliant read-only check via Liquipedia's official MediaWiki API (CC-BY-SA 3.0).

    Strictly obeys https://liquipedia.net/api-terms-of-use:
      * MediaWiki api.php endpoint ONLY (never HTML scraping)
      * Accept-Encoding: gzip (handled by lib_common.fetch)
      * Custom contact User-Agent (LOLHOTSPAWN2 bot UA)
      * >= 2.2s spacing between requests
      * Deduplicated to <=8 canonical prefixes per run
    """
    norm_prefixes = _normalise_liquipedia_prefixes(prefixes)
    found = {}
    errors = []
    for pfx in norm_prefixes:
        params = urllib.parse.urlencode({
            "action": "query",
            "list": "allpages",
            "apprefix": pfx,
            "aplimit": "15",
            "format": "json",
        })
        r = fetch(f"{LIQUIPEDIA_API}?{params}", timeout=30, retries=2)
        time.sleep(2.2)
        if r["status"] != 200:
            errors.append(f"{pfx}: HTTP {r['status']}")
            continue
        try:
            body = json.loads(r["text"])
            pages = [x.get("title") for x in (body.get("query", {}).get("allpages") or []) if x.get("title")]
            if pages:
                found[pfx] = pages
        except Exception:
            errors.append(f"{pfx}: parse error")
    total = sum(len(v) for v in found.values())
    return {
        "name": "Liquipedia MediaWiki API (CC-BY-SA 3.0)",
        "url": LIQUIPEDIA_PAGE,
        "status": "ok" if total > 0 else ("degraded" if errors else "no_data"),
        "count": total,
        "pages": found,
        "note": ("Official MediaWiki api.php index (gzip, >=2.2s spacing; HTML never scraped; "
                 "CC-BY-SA 3.0 attribution on Methodology & Sources)."),
    }

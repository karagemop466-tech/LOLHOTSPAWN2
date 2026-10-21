#!/usr/bin/env python3
"""Diagnostic lab v3 - targeted: Hotspawn LoL subset, Pinnacle LoL, Leaguepedia export, Liquipedia gzip, Bovada/Rivalry.""
"""
import gzip, json, os, re, sys, time, traceback, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone

OUT = "data/diag"
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "LOLHOTSPAWN2-research/1.0 (https://github.com/karagemop466-tech/LOLHOTSPAWN2; contact via repo)",
      "Accept": "application/json,text/html;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.9"}
rep = {"generated_at": datetime.now(timezone.utc).isoformat()}
NOW = datetime.now(timezone.utc).timestamp()


def dump():
    json.dump(rep, open(os.path.join(OUT, "report3.json"), "w"), indent=1)


def fetch(url, headers=None, timeout=45):
    h = dict(UA)
    if headers:
        h.update(headers)
    try:
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            b = r.read()
            return {"status": r.status, "body": b, "ctype": r.headers.get("content-type", ""), "bytes": len(b), "enc": r.headers.get("content-encoding", "")}
    except urllib.error.HTTPError as e:
        b = b""
        try:
            b = e.read()
        except Exception:
            pass
        return {"status": e.code, "body": b, "ctype": e.headers.get("content-type", "") if e.headers else "", "bytes": len(b), "enc": ""}
    except Exception as e:
        return {"status": 0, "body": b"", "ctype": "", "bytes": 0, "err": repr(e)[:200], "enc": ""}


def dec(r):
    b = r["body"]
    if b[:2] == b"\x1f\x8b":
        try:
            b = gzip.decompress(b)
        except Exception:
            pass
    return b.decode("utf-8", "replace")


def jget(url, headers=None):
    r = fetch(url, headers)
    out = {"status": r["status"], "bytes": r["bytes"], "err": r.get("err")}
    if r["status"] == 200:
        try:
            out["json"] = json.loads(dec(r))
        except Exception as e:
            out["parse_err"] = repr(e)[:150]
            out["head"] = dec(r)[:300]
    else:
        out["head"] = dec(r)[:300]
    return out


def section(name, fn):
    try:
        fn()
    except Exception:
        rep.setdefault("errors", []).append({"section": name, "traceback": traceback.format_exc()[-2000:]})
    dump()
    print("section", name, "done", file=sys.stderr)


def s_fixtures():
    fx = jget("https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures")
    allfx = fx.get("json")
    if not isinstance(allfx, list):
        rep["fixtures_err"] = str(allfx)[:300]
        return
    lol = [x for x in allfx if (x.get("sport_alias") or "").lower() == "lol"]
    for x in lol:
        x["start_iso"] = datetime.fromtimestamp(int(x["scheduled_start_time"]) / 1000, timezone.utc).isoformat()
    fut = [x for x in lol if int(x["scheduled_start_time"]) / 1000 > NOW]
    rep["fixtures_lol"] = {"total": len(lol), "future": len(fut), "past": len(lol) - len(fut),
                           "comps_future": sorted(set(x["competition_name"] for x in fut)),
                           "earliest_future": min((x["start_iso"] for x in fut), default=None),
                           "latest_future": max((x["start_iso"] for x in fut), default=None),
                           "tiers_future": {t: sum(1 for x in fut if x["tier"] == t) for t in sorted(set(x["tier"] for x in fut))}}
    json.dump(fut, open(os.path.join(OUT, "lol_fixtures_future.json"), "w"), indent=0)
    # permalinks from lobby page
    r = fetch("https://play.hotspawn.com/lol-pickems")
    h = dec(r)
    m = re.search(r'<script[^>]*id="ng-state"[^>]*>(.*?)</script>', h, re.S)
    perma = {}
    if m:
        st = json.loads(m.group(1))
        for k, v in st.items():
            if isinstance(v, dict) and isinstance(v.get("b"), dict) and "permalinks" in v["b"]:
                perma = v["b"]["permalinks"]
    rep["fixtures_lol"]["lobby_rendered_cards"] = h.count("Who will win?")
    rep["fixtures_lol"]["permalinks"] = len(perma)
    rep["fixtures_lol"]["future_with_permalink"] = sum(1 for x in fut if str(x["id"]) in perma)
    json.dump(perma, open(os.path.join(OUT, "permalinks.json"), "w"))


section("fixtures", s_fixtures)


def s_pinnacle():
    PIN = {"x-api-key": "CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R", "Accept": "application/json"}
    lg = jget("https://guest.api.arcadia.pinnacle.com/0.1/sports/12/leagues", PIN)
    rep["pinnacle_leagues_12"] = lg if lg["status"] != 200 else [
        {"id": x.get("id"), "name": x.get("name"), "n": x.get("matchupCount")} for x in lg["json"]]
    if lg["status"] != 200 or not isinstance(lg.get("json"), list):
        return
    for L in [x for x in lg["json"] if "league of legends" in (x.get("name") or "").lower()]:
        lid = L["id"]
        mu = jget(f"https://guest.api.arcadia.pinnacle.com/0.1/leagues/{lid}/matchups", PIN)
        entry = {"league": L["name"], "status": mu["status"], "n": len(mu.get("json") or []) if isinstance(mu.get("json"), list) else None}
        if isinstance(mu.get("json"), list) and mu["json"]:
            entry["sample"] = mu["json"][0]
            mid = mu["json"][0]["id"]
            mk = jget(f"https://guest.api.arcadia.pinnacle.com/0.1/matchups/{mid}/markets/related/straight", PIN)
            entry["markets_status"] = mk["status"]
            entry["markets"] = (mk.get("json") or [])[:5] if isinstance(mk.get("json"), list) else mk.get("head")
        rep.setdefault("pinnacle_lol", {})[str(lid)] = entry


section("pinnacle", s_pinnacle)


def s_leaguepedia():
    LP = "https://lol.fandom.com/api.php"
    H = {"Accept-Encoding": "gzip", "User-Agent": "LOLHOTSPAWN2/2.0 (research; contact via GitHub repo) python-urllib"}
    rep["leaguepedia"] = {}
    # Space calls out; Cargo rate limits are strict on shared IPs.
    tests = [
        ("cargo_simple", {"action": "cargoquery", "format": "json", "formatversion": "2", "tables": "ScoreboardGames", "fields": "SG.Team1,SG.Team2,SG.Winner", "limit": "2"}),
        ("cargo_teamredirects2", {"action": "cargoquery", "format": "json", "formatversion": "2", "tables": "TeamRedirects", "fields": "AllName,Name", "limit": "2"}),
        ("cargo_schedule", {"action": "cargoquery", "format": "json", "formatversion": "2", "tables": "MatchSchedule", "fields": "MS.Team1,MS.Team2,MS.DateTime_UTC", "where": "MS.DateTime_UTC >= '2026-10-21'", "limit": "2"}),
    ]
    for name, p in tests:
        r = fetch(LP + "?" + urllib.parse.urlencode(p), H)
        rep["leaguepedia"][name] = {"status": r["status"], "bytes": r["bytes"], "head": dec(r)[:400]}
        time.sleep(4)
    exp = "https://lol.fandom.com/wiki/Special:CargoExport?" + urllib.parse.urlencode(
        {"tables": "ScoreboardGames", "fields": "Team1,Team2,Winner,DateTime_UTC,OverviewPage", "where": "DateTime_UTC >= '2025-09-01'", "limit": "100", "format": "json"})
    r = fetch(exp, H)
    rep["leaguepedia"]["cargo_export"] = {"status": r["status"], "bytes": r["bytes"], "head": dec(r)[:500]}


section("leaguepedia", s_leaguepedia)


def s_liquipedia():
    H = {"Accept-Encoding": "gzip", "User-Agent": "LOLHOTSPAWN2/2.0 (https://github.com/karagemop466-tech/LOLHOTSPAWN2; contact via repo)"}
    rep["liquipedia"] = {}
    for team in ["Absolved", "Good Chi", "Galions", "NTNUI Kometkameratene", "Team 300", "PRM 3rd Division 26-27 Fall"]:
        s = jget("https://liquipedia.net/leagueoflegends/api.php?" + urllib.parse.urlencode(
            {"action": "query", "list": "search", "srsearch": team, "format": "json", "srlimit": "3"}), H)
        hit = None
        if s["status"] == 200 and isinstance(s.get("json"), dict):
            hit = [(x["title"], re.sub(r"<[^>]+>", "", x.get("snippet", ""))[:110]) for x in s["json"].get("query", {}).get("search", [])]
        rep["liquipedia"][team] = {"status": s["status"], "hits": hit, "head": s.get("head") if s["status"] != 200 else None}
        time.sleep(2.5)
    pg = jget("https://liquipedia.net/leagueoflegends/api.php?" + urllib.parse.urlencode(
        {"action": "parse", "page": "Absolved", "prop": "text", "format": "json", "formatversion": "2"}), H)
    rep["liquipedia"]["Absolved_page_status"] = pg["status"]
    if pg["status"] == 200 and isinstance(pg.get("json"), dict):
        html = pg["json"].get("parse", {}).get("text", "") or ""
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
        rep["liquipedia"]["Absolved_page_len"] = len(html)
        rep["liquipedia"]["Absolved_text_sample"] = txt[:3000]
    else:
        rep["liquipedia"]["Absolved_page_head"] = pg.get("head")


section("liquipedia", s_liquipedia)


def s_books():
    rep["books"] = {}
    bov = [
        ("bovada_lol_coupon", "https://www.bovada.lv/services/sports/event/coupon/events/A/description/esports/league-of-legends?marketFilterId=def&preMatchOnly=true&lang=en"),
        ("bovada_lol_page", "https://www.bovada.lv/sports/esports/league-of-legends"),
    ]
    for n, u in bov:
        r = fetch(u)
        t = dec(r)
        rep["books"][n] = {"status": r["status"], "bytes": r["bytes"], "lol_mentions": len(re.findall(r"league of legends", t, re.I)),
                           "odds_mentions": len(re.findall(r"decimal|moneyline|price", t, re.I)), "head": t[:250]}
    riv_api = [
        "https://api.rivalry.com/api/v1/sport/league-of-legends/matches",
        "https://api.rivalry.com/api/v1/matches?sport=league-of-legends",
        "https://www.rivalry.com/api/v1/sport/league-of-legends/matches",
    ]
    for u in riv_api:
        r = fetch(u, {"Accept": "application/json", "Origin": "https://www.rivalry.com", "Referer": "https://www.rivalry.com/"})
        rep["books"]["rivalry:" + u.split("//")[1][:45]] = {"status": r["status"], "bytes": r["bytes"], "head": dec(r)[:200]}
    # bo3 correct filter attempts
    for u in ["https://api.bo3.gg/api/v1/matches?filter%5Bdisciplines%5D=lol&page%5Blimit%5D=3",
              "https://api.bo3.gg/api/v1/matches?filter%5Bgame%5D=league-of-legends&page%5Blimit%5D=3",
              "https://api.bo3.gg/api/v1/teams?filter%5Bname%5D=Absolved"]:
        r = fetch(u, {"Origin": "https://bo3.gg", "Referer": "https://bo3.gg/"})
        rep["books"]["bo3:" + u.split("?")[1][:45]] = {"status": r["status"], "bytes": r["bytes"], "head": dec(r)[:400]}
    mid = fetch("https://www.midnite.com/esports/league-of-legends")
    mt = dec(mid)
    rep["books"]["midnite"] = {"status": mid["status"], "bytes": mid["bytes"], "odds": len(re.findall(r"odds|price", mt, re.I)), "head": mt[:300]}


section("books", s_books)


def s_prediction():
    rep["prediction"] = {}
    r = jget("https://gamma-api.polymarket.com/events?tag_slug=league-of-legends&active=true&closed=false&limit=100")
    ev = r.get("json") if isinstance(r.get("json"), list) else []
    rep["prediction"]["polymarket_events"] = len(ev)
    rep["prediction"]["polymarket_match_events"] = [
        {"title": e.get("title"), "slug": e.get("slug"), "n_markets": len(e.get("markets") or []),
         "end": e.get("endDate")} for e in ev if re.search(r"\bvs\b|\bgame\b", e.get("title") or "", re.I)][:30]
    mf = jget("https://api.manifold.markets/v0/search-markets?term=league%20of%20legends&limit=20")
    if isinstance(mf.get("json"), list):
        rep["prediction"]["manifold"] = [{"q": x.get("question"), "prob": x.get("probability"), "vol": x.get("volume"), "close": x.get("closeTime")} for x in mf["json"]][:20]


section("prediction", s_prediction)
print("done", file=sys.stderr)

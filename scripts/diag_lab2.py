#!/usr/bin/env python3
"""Diagnostic lab v2 - odds/model source enumeration. Temporary."""
import gzip, json, os, re, sys, traceback, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone

OUT = "data/diag"
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "LOLHOTSPAWN2-research/1.0 (https://github.com/karagemop466-tech/LOLHOTSPAWN2; contact via repo)",
      "Accept": "application/json,text/html;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.9"}
rep = {"generated_at": datetime.now(timezone.utc).isoformat()}
NOW = datetime.now(timezone.utc).timestamp()


def dump():
    json.dump(rep, open(os.path.join(OUT, "report2.json"), "w"), indent=1)


def fetch(url, headers=None, timeout=40):
    h = dict(UA)
    if headers:
        h.update(headers)
    try:
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            b = r.read()
            return {"status": r.status, "body": b, "ctype": r.headers.get("content-type", ""), "bytes": len(b)}
    except urllib.error.HTTPError as e:
        b = b""
        try:
            b = e.read()
        except Exception:
            pass
        return {"status": e.code, "body": b, "ctype": e.headers.get("content-type", "") if e.headers else "", "bytes": len(b)}
    except Exception as e:
        return {"status": 0, "body": b"", "ctype": "", "bytes": 0, "err": repr(e)[:200]}


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
        rep.setdefault("errors", []).append({"section": name, "traceback": traceback.format_exc()[-2500:]})
    dump()
    print("section", name, "ok", file=sys.stderr)


# ------------------------------------------------ Hotspawn official fixtures API
def s_fixtures():
    fx = jget("https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures")
    d = {k: v for k, v in fx.items() if k != "json"}
    rep["hotspawn_fixtures_api"] = d
    if fx["status"] != 200:
        return
    data = fx["json"]
    d["root_type"] = type(data).__name__
    if isinstance(data, dict):
        d["root_keys"] = list(data.keys())
        for k in ("data", "fixtures", "items", "results"):
            if isinstance(data.get(k), list):
                data = data[k]
                break
    if not isinstance(data, list):
        d["unusable"] = str(data)[:300]
        return
    d["n"] = len(data)
    d["keys"] = sorted(data[0].keys()) if data and isinstance(data[0], dict) else None
    ts = []
    for x in data:
        try:
            ts.append(int(x.get("scheduled_start_time")) / 1000)
        except Exception:
            pass
    d["future"] = sum(1 for t in ts if t > NOW)
    d["past"] = sum(1 for t in ts if t <= NOW)
    d["earliest"] = datetime.fromtimestamp(min(ts), timezone.utc).isoformat() if ts else None
    d["latest"] = datetime.fromtimestamp(max(ts), timezone.utc).isoformat() if ts else None
    d["competitions"] = sorted(set(x.get("competition_name") for x in data))
    d["sample"] = data[0]
    d["past_sample"] = [{"id": x.get("id"), "t": datetime.fromtimestamp(int(x["scheduled_start_time"]) / 1000, timezone.utc).isoformat(),
                         "comp": x.get("competition_name"), "p": [x.get("participants0_name"), x.get("participants1_name")]}
                        for x in data if int(x["scheduled_start_time"]) / 1000 <= NOW][:12]


section("hotspawn_fixtures", s_fixtures)


# ------------------------------------------------ Pinnacle guest API
PIN = {"x-api-key": "CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R", "Accept": "application/json"}


def s_pinnacle():
    sports = jget("https://guest.api.arcadia.pinnacle.com/0.1/sports", PIN)
    rep["pinnacle_sports_status"] = sports["status"]
    if sports["status"] != 200 or not isinstance(sports.get("json"), list):
        rep["pinnacle_sports_head"] = sports.get("head")
        return
    rep["pinnacle_sports_with_matchups"] = [{"id": s["id"], "name": s["name"], "n": s.get("matchupCount")} for s in sports["json"] if s.get("matchupCount")]
    ids = [s["id"] for s in sports["json"] if "esport" in (s["name"] or "").lower()]
    rep["pinnacle_esport_sport_ids"] = ids
    rep["pinnacle_leagues"] = {}
    for sid in ids:
        lg = jget(f"https://guest.api.arcadia.pinnacle.com/0.1/sports/{sid}/leagues", PIN)
        if lg["status"] != 200 or not isinstance(lg.get("json"), list):
            rep["pinnacle_leagues"][sid] = {"status": lg["status"], "head": lg.get("head")}
            continue
        rep["pinnacle_leagues"][sid] = [{"id": x.get("id"), "name": x.get("name"), "matchups": x.get("matchupCount")} for x in lg["json"]]
        lol = [x for x in lg["json"] if "league of legends" in (x.get("name") or "").lower()]
        for L in lol[:4]:
            lid = L["id"]
            mu = jget(f"https://guest.api.arcadia.pinnacle.com/0.1/leagues/{lid}/matchups", PIN)
            m = {"league": L.get("name"), "status": mu["status"],
                 "n": len(mu.get("json") or []) if isinstance(mu.get("json"), list) else None}
            if isinstance(mu.get("json"), list) and mu["json"]:
                m["sample"] = mu["json"][0]
                mid = mu["json"][0].get("id")
                mk = jget(f"https://guest.api.arcadia.pinnacle.com/0.1/matchups/{mid}/markets/related/straight", PIN)
                m["markets_status"] = mk["status"]
                m["markets"] = (mk.get("json") or [])[:4] if isinstance(mk.get("json"), list) else mk.get("head")
            rep.setdefault("pinnacle_lol", {})[str(lid)] = m


section("pinnacle", s_pinnacle)


# ------------------------------------------------ Leaguepedia (capture errors)
def s_leaguepedia():
    LP = "https://lol.fandom.com/api.php"
    tests = {
        "cargo_simple": {"action": "cargoquery", "format": "json", "tables": "ScoreboardGames", "fields": "SG.Team1,SG.Team2,SG.Winner", "limit": "2"},
        "cargo_matchschedule": {"action": "cargoquery", "format": "json", "tables": "MatchSchedule", "fields": "MS.Team1,MS.Team2,MS.DateTime_UTC", "limit": "2"},
        "cargo_schedule_where": {"action": "cargoquery", "format": "json", "tables": "MatchSchedule", "fields": "MS.Team1,MS.Team2,MS.DateTime_UTC", "where": "MS.DateTime_UTC >= '2026-10-21'", "limit": "2"},
        "cargo_teamredirects": {"action": "cargoquery", "format": "json", "tables": "TeamRedirects", "fields": "TeamRedirects.AllName,TeamRedirects.Name", "limit": "2"},
        "cargo_tournamentresults": {"action": "cargoquery", "format": "json", "tables": "TournamentResults", "fields": "TournamentResults.Team,TournamentResults.Place", "limit": "2"},
        "query_siteinfo": {"action": "query", "format": "json", "meta": "siteinfo"},
        "cargoquery_noformat": {"action": "cargoquery", "tables": "ScoreboardGames", "fields": "SG.Team1", "limit": "1"},
    }
    rep["leaguepedia"] = {}
    for k, p in tests.items():
        r = fetch(LP + "?" + urllib.parse.urlencode(p))
        rep["leaguepedia"][k] = {"status": r["status"], "bytes": r["bytes"], "head": dec(r)[:500]}


section("leaguepedia", s_leaguepedia)


# ------------------------------------------------ Liquipedia
def s_liquipedia():
    rep["liquipedia"] = {}
    for team in ["Absolved", "Good Chi", "Galions", "NTNUI Kometkameratene", "Team 300"]:
        s = jget("https://liquipedia.net/leagueoflegends/api.php?" + urllib.parse.urlencode(
            {"action": "query", "list": "search", "srsearch": team, "format": "json", "srlimit": "3"}))
        hit = None
        if s["status"] == 200 and isinstance(s.get("json"), dict):
            hit = [(x["title"], re.sub(r"<[^>]+>", "", x.get("snippet", ""))[:90]) for x in s["json"].get("query", {}).get("search", [])]
        rep["liquipedia"][team] = {"status": s["status"], "hits": hit}
    pg = jget("https://liquipedia.net/leagueoflegends/api.php?" + urllib.parse.urlencode(
        {"action": "parse", "page": "Absolved", "prop": "text", "format": "json", "formatversion": "2"}))
    rep["liquipedia"]["Absolved_page_status"] = pg["status"]
    if pg["status"] == 200 and isinstance(pg.get("json"), dict):
        html = pg["json"].get("parse", {}).get("text", "") or ""
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
        rep["liquipedia"]["Absolved_page_len"] = len(html)
        rep["liquipedia"]["Absolved_text_sample"] = txt[:2500]
    else:
        rep["liquipedia"]["Absolved_page_head"] = pg.get("head")


section("liquipedia", s_liquipedia)


# ------------------------------------------------ bo3.gg / Rivalry / misc
def s_books():
    b3 = jget("https://api.bo3.gg/api/v1/matches?filter%5Bgame%5D=lol&page%5Blimit%5D=5", {"Origin": "https://bo3.gg", "Referer": "https://bo3.gg/"})
    rep["bo3"] = {k: v for k, v in b3.items() if k != "json"}
    if b3.get("json") is not None:
        rep["bo3"]["root_keys"] = list(b3["json"].keys()) if isinstance(b3["json"], dict) else "list"
        rep["bo3"]["sample"] = str(b3["json"])[:1500]
    riv = fetch("https://www.rivalry.com/lol", {"Accept": "text/html"})
    rtxt = dec(riv)
    rep["rivalry"] = {"status": riv["status"], "bytes": riv["bytes"], "has_next_data": "__NEXT_DATA__" in rtxt,
                      "odds_hits": len(re.findall(r"moneyline|decimalOdd|odds", rtxt, re.I)),
                      "match_links": len(set(re.findall(r"/esports-betting/league-of-legends/[^\"']+", rtxt))),
                      "head": rtxt[:200]}
    esp = fetch("https://www.esportspages.com/lol", {"Accept": "text/html"})
    etxt = dec(esp)
    rep["esportspages"] = {"status": esp["status"], "bytes": esp["bytes"], "odds_hits": len(re.findall(r"odds|moneyline", etxt, re.I)),
                           "has_json": "__NEXT_DATA__" in etxt, "head": etxt[:300]}


section("books", s_books)


def s_extra():
    extra = {
        "kalshi_series": "https://api.elections.kalshi.com/trade-api/v2/series?category=Esports",
        "manifold_search": "https://api.manifold.markets/v0/search-markets?term=league%20of%20legends&limit=10",
        "smarkets_lol": "https://smarkets.com/sport/esports/league-of-legends",
        "betfair_readonly": "https://www.betfair.com/www/sports/exchange/readonly/v1/bymarket?alt=json&currency=GBP&locale=en_GB&marketIds=1.1",
        "midnite_lol": "https://www.midnite.com/esports/league-of-legends",
        "pixelbet_lol": "https://pixel.bet/en/sport/esports/league-of-legends",
        "betway_esports": "https://www.betway.com/en/esports/league-of-legends",
        "unibet_lol": "https://www.unibet.com/betting/sports/filter/esports/league_of_legends",
        "bovada_lol": "https://www.bovada.lv/sports/esports/league-of-legends",
    }
    rep["extra"] = {}
    for k, u in extra.items():
        r = fetch(u)
        rep["extra"][k] = {"status": r["status"], "bytes": r["bytes"], "head": dec(r)[:200]}


section("extra", s_extra)
print("done", file=sys.stderr)

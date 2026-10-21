#!/usr/bin/env python3
"""Diagnostic lab v2 - odds/model source enumeration. Temporary."""
import gzip, json, os, re, sys, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone

OUT = "data/diag"
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "LOLHOTSPAWN2-research/1.0 (https://github.com/karagemop466-tech/LOLHOTSPAWN2; contact via repo)",
      "Accept": "application/json,text/html;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.9"}
rep = {"generated_at": datetime.now(timezone.utc).isoformat()}
NOW = datetime.now(timezone.utc).timestamp()


def fetch(url, headers=None, timeout=45):
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


# ------------------------------------------------ Hotspawn official fixtures API
fx = jget("https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures")
rep["hotspawn_fixtures_api"] = {k: v for k, v in fx.items() if k != "json"}
if fx["status"] == 200:
    data = fx["json"]
    if isinstance(data, dict):
        data = data.get("data") or data.get("fixtures") or data
    rep["hotspawn_fixtures_api"]["n"] = len(data) if isinstance(data, list) else None
    if isinstance(data, list):
        ts = [int(x["scheduled_start_time"]) / 1000 for x in data]
        rep["hotspawn_fixtures_api"].update({
            "future": sum(1 for t in ts if t > NOW), "past": sum(1 for t in ts if t <= NOW),
            "earliest": datetime.fromtimestamp(min(ts), timezone.utc).isoformat(),
            "latest": datetime.fromtimestamp(max(ts), timezone.utc).isoformat(),
            "competitions": sorted(set(x["competition_name"] for x in data)),
            "sample": data[0], "last": data[-1]})
        # do participant entries include per-match links? print all keys
        rep["hotspawn_fixtures_api"]["keys"] = sorted(data[0].keys())
        # past fixtures detail
        rep["hotspawn_fixtures_api"]["past_sample"] = [
            {"id": x["id"], "t": datetime.fromtimestamp(int(x["scheduled_start_time"]) / 1000, timezone.utc).isoformat(),
             "comp": x["competition_name"], "p": [x["participants0_name"], x["participants1_name"]]}
            for x in data if int(x["scheduled_start_time"]) / 1000 <= NOW][:10]

# ------------------------------------------------ Pinnacle guest API
PIN = {"x-api-key": "CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R", "Accept": "application/json"}
sports = jget("https://guest.api.arcadia.pinnacle.com/0.1/sports", PIN)
esport_ids = []
if sports["status"] == 200 and isinstance(sports.get("json"), list):
    rep["pinnacle_sports_with_matchups"] = [{"id": s["id"], "name": s["name"], "n": s.get("matchupCount")} for s in sports["json"] if s.get("matchupCount")]
    esport_ids = [s["id"] for s in sports["json"] if "esport" in s["name"].lower()]
    rep["pinnacle_esport_sport_ids"] = esport_ids
rep["pinnacle_leagues"] = {}
for sid in esport_ids:
    lg = jget(f"https://guest.api.arcadia.pinnacle.com/0.1/sports/{sid}/leagues", PIN)
    if lg["status"] == 200 and isinstance(lg.get("json"), list):
        rep["pinnacle_leagues"][sid] = [{"id": x.get("id"), "name": x.get("name"), "matchups": x.get("matchupCount")} for x in lg["json"]]
        lol = [x for x in lg["json"] if "league of legends" in (x.get("name") or "").lower()]
        for L in lol[:3]:
            lid = L["id"]
            mu = jget(f"https://guest.api.arcadia.pinnacle.com/0.1/leagues/{lid}/matchups", PIN)
            rep.setdefault("pinnacle_lol_matchups", {})[str(lid)] = {"league": L.get("name"), "status": mu["status"], "n": len(mu.get("json") or []) if isinstance(mu.get("json"), list) else None, "sample": (mu.get("json") or [])[:2] if isinstance(mu.get("json"), list) else mu.get("head")}
            if isinstance(mu.get("json"), list) and mu["json"]:
                mid = mu["json"][0].get("id")
                mk = jget(f"https://guest.api.arcadia.pinnacle.com/0.1/matchups/{mid}/markets/related/straight", PIN)
                rep.setdefault("pinnacle_markets", {})[str(mid)] = {"status": mk["status"], "sample": (mk.get("json") or [])[:3] if isinstance(mk.get("json"), list) else mk.get("head")}

# ------------------------------------------------ Leaguepedia (capture errors)
LP = "https://lol.fandom.com/api.php"
tests = {
 "cargo_simple": {"action": "cargoquery", "format": "json", "tables": "ScoreboardGames", "fields": "SG.Team1,SG.Team2,SG.Winner", "limit": "2"},
 "cargo_matchschedule": {"action": "cargoquery", "format": "json", "tables": "MatchSchedule", "fields": "MS.Team1,MS.Team2,MS.DateTime_UTC", "limit": "2"},
 "cargo_schedule_where": {"action": "cargoquery", "format": "json", "tables": "MatchSchedule", "fields": "MS.Team1,MS.Team2,MS.DateTime_UTC", "where": "MS.DateTime_UTC >= '2026-10-21'", "limit": "2"},
 "cargo_teamredirects": {"action": "cargoquery", "format": "json", "tables": "TeamRedirects", "fields": "TeamRedirects.AllName,TeamRedirects.Name", "limit": "2"},
 "cargo_tables": {"action": "cargoquery", "format": "json", "tables": "ScoreboardGames", "fields": "SG.Team1", "limit": "1", "offset": "0"},
 "query_siteinfo": {"action": "query", "format": "json", "meta": "siteinfo"},
 "cargoquery_noformat": {"action": "cargoquery", "tables": "ScoreboardGames", "fields": "SG.Team1", "limit": "1"},
}
rep["leaguepedia"] = {}
for k, p in tests.items():
    url = LP + "?" + urllib.parse.urlencode(p)
    r = fetch(url)
    rep["leaguepedia"][k] = {"status": r["status"], "bytes": r["bytes"], "head": dec(r)[:400]}

# ------------------------------------------------ Liquipedia: team page parse
rep["liquipedia"] = {}
for team in ["Absolved", "Good Chi", "Galions", "NTNUI Kometkameratene", "Team 300"]:
    s = jget("https://liquipedia.net/leagueoflegends/api.php?" + urllib.parse.urlencode(
        {"action": "query", "list": "search", "srsearch": team, "format": "json", "srlimit": "3"}))
    hit = None
    if s["status"] == 200:
        res = s["json"].get("query", {}).get("search", [])
        hit = [(x["title"], x.get("snippet", "")[:90]) for x in res]
    rep["liquipedia"][team] = {"status": s["status"], "hits": hit}
# parse a team page
pg = jget("https://liquipedia.net/leagueoflegends/api.php?" + urllib.parse.urlencode(
    {"action": "parse", "page": "Absolved", "prop": "text", "format": "json", "formatversion": "2"}))
if pg["status"] == 200:
    html = pg["json"].get("parse", {}).get("text", "") or ""
    txt = re.sub(r"<[^>]+>", " ", html)
    txt = re.sub(r"\s+", " ", txt)
    rep["liquipedia"]["Absolved_page_len"] = len(html)
    rep["liquipedia"]["Absolved_text_sample"] = txt[:1800]
else:
    rep["liquipedia"]["Absolved_page"] = {"status": pg["status"], "head": pg.get("head")}

# ------------------------------------------------ bo3.gg / Rivalry / others
b3 = jget("https://api.bo3.gg/api/v1/matches?filter%5Bgame%5D=lol&page%5Blimit%5D=5", {"Origin": "https://bo3.gg", "Referer": "https://bo3.gg/"})
rep["bo3"] = {k: v for k, v in b3.items() if k != "json"}
if b3.get("json") is not None:
    rep["bo3"]["keys"] = list(b3["json"].keys()) if isinstance(b3["json"], dict) else "list"
    rep["bo3"]["sample"] = str(b3["json"])[:1200]

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

extra = {
 "kalshi_series_search": "https://api.elections.kalshi.com/trade-api/v2/series?category=Esports",
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
    rep["extra"][k] = {"status": r["status"], "bytes": r["bytes"], "head": dec(r)[:180]}

json.dump(rep, open(os.path.join(OUT, "report2.json"), "w"), indent=1)
print("done", {k: (len(v) if hasattr(v, "__len__") else "") for k, v in rep.items()}, file=sys.stderr)

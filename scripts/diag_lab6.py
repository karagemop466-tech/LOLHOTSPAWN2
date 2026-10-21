#!/usr/bin/env python3
"""Diagnostic lab v6 - official league sites + standings for PRM3/Tunisian/4 Nations."""
import gzip, json, os, re, sys, time, traceback, urllib.request, urllib.parse, urllib.error

OUT = "data/diag"
UA = {"User-Agent": "LOLHOTSPAWN2-research/1.0 (https://github.com/karagemop466-tech/LOLHOTSPAWN2; contact via repo)",
      "Accept": "application/json,text/html;q=0.9,*/*;q=0.8", "Accept-Encoding": "gzip"}
rep = {}


def dump():
    json.dump(rep, open(os.path.join(OUT, "report6.json"), "w"), indent=1)


def fetch(url, headers=None, timeout=40):
    h = dict(UA)
    if headers:
        h.update(headers)
    try:
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"status": r.status, "body": r.read(), "bytes": 0}
    except urllib.error.HTTPError as e:
        b = b""
        try:
            b = e.read()
        except Exception:
            pass
        return {"status": e.code, "body": b, "bytes": len(b)}
    except Exception as e:
        return {"status": 0, "body": b"", "bytes": 0, "err": repr(e)[:160]}


def dec(r):
    b = r["body"]
    if b[:2] == b"\x1f\x8b":
        try:
            b = gzip.decompress(b)
        except Exception:
            pass
    return b.decode("utf-8", "replace")


def section(name, fn):
    try:
        fn()
    except Exception:
        rep.setdefault("errors", []).append({"section": name, "traceback": traceback.format_exc()[-1500:]})
    dump()
    print(name, "done", file=sys.stderr)


LPX = "https://lol.fandom.com/wiki/Special:CargoExport?"


def lp(params):
    r = fetch(LPX + urllib.parse.urlencode(params))
    return r, dec(r)


def s_standings():
    rep["standings"] = {}
    for label, page in [("prm3", "Prime League 3rd Division/2027 Season/Fall Split"),
                        ("prm2", "PRM 2nd Division 26-27 Fall"),
                        ("4nations", "4 Nations/2026 Season/Halloween Heist"),
                        ("rivals", "RIVALS LEAGUE/2026 Season/Season 2"),
                        ("komplett", "Komplettligaen/2026 Season/Autumn Split"),
                        ("tunisian", "Tunisian Super League/2026 Season")]:
        r, t = lp({"tables": "Standings", "fields": "OverviewPage,Team,Place,Wins,Losses,WinLoss,Points",
                   "where": f"OverviewPage LIKE '{page.split('/')[0]}%'", "limit": "100", "format": "json"})
        e = {"status": r["status"], "head": t[:150]}
        try:
            j = json.loads(t)
            e["n"] = len(j)
            e["sample"] = j[:4]
        except Exception as ex:
            e["err"] = repr(ex)[:100]
        rep["standings"][label] = e
        time.sleep(2)
    # tournament results (placements)
    r, t = lp({"tables": "TournamentResults", "fields": "OverviewPage,Team,Place,Prize,Phase",
               "where": "OverviewPage LIKE 'Prime League%' OR OverviewPage LIKE 'Tunisian%' OR OverviewPage LIKE '4 Nations%'",
               "limit": "100", "format": "json"})
    rep["tournament_results"] = {"status": r["status"], "head": t[:200]}
    try:
        j = json.loads(t)
        rep["tournament_results"]["n"] = len(j)
        rep["tournament_results"]["pages"] = sorted(set(x["OverviewPage"] for x in j))[:30]
    except Exception:
        pass


section("standings", s_standings)


def s_prm3_schedule():
    r, t = lp({"tables": "MatchSchedule", "fields": "Team1,Team2,DateTime_UTC,OverviewPage,BestOf,Tab",
               "where": "OverviewPage LIKE 'Prime League 3rd Division%'", "limit": "200", "format": "json"})
    e = {"status": r["status"], "head": t[:200]}
    try:
        j = json.loads(t)
        e["n"] = len(j)
        e["sample"] = j[:5]
        e["pages"] = sorted(set(x["OverviewPage"] for x in j))
        json.dump(j, open(os.path.join(OUT, "lp_prm3_schedule.json"), "w"))
    except Exception:
        pass
    rep["prm3_schedule"] = e
    r, t = lp({"tables": "MatchSchedule", "fields": "Team1,Team2,DateTime_UTC,OverviewPage,BestOf,Tab",
               "where": "OverviewPage LIKE 'Tunisian%'", "limit": "200", "format": "json"})
    e = {"status": r["status"], "head": t[:200]}
    try:
        j = json.loads(t)
        e["n"] = len(j)
        e["pages"] = sorted(set(x["OverviewPage"] for x in j))
        json.dump(j, open(os.path.join(OUT, "lp_tunisian_schedule.json"), "w"))
    except Exception:
        pass
    rep["tunisian_schedule"] = e


section("schedules", s_prm3_schedule)


def s_sites():
    sites = {
        "primeleague": "https://primeleague.gg/en/leagues",
        "primeleague_api": "https://primeleague.gg/api/v1/leagues",
        "4nations": "https://4nations.gg/",
        "rivals": "https://rivalsleague.gg/",
        "komplett": "https://komplettligaen.no/",
        "ligagg": "https://ligagg.com/",
        "tunisian": "https://tunisiansuperleague.com/",
        "tunisian2": "https://www.tunisiansuperleague.tn/",
        "lol_tn": "https://lol.tn/",
    }
    rep["sites"] = {}
    for k, u in sites.items():
        r = fetch(u)
        t = dec(r)
        rep["sites"][k] = {"status": r["status"], "bytes": r["bytes"], "title": (re.search(r"<title>(.*?)</title>", t, re.S).group(1)[:100] if re.search(r"<title>(.*?)</title>", t, re.S) else None),
                           "head": re.sub(r"\s+", " ", t)[:180]}


section("sites", s_sites)


def s_liq_pages():
    H = {"User-Agent": "LOLHOTSPAWN2/2.0 (https://github.com/karagemop466-tech/LOLHOTSPAWN2)"}
    rep["liq_pages"] = {}
    for prefix in ["Prime League", "4 Nations", "Tunisian", "RIVALS LEAGUE", "Komplettligaen"]:
        u = "https://liquipedia.net/leagueoflegends/api.php?" + urllib.parse.urlencode(
            {"action": "query", "list": "allpages", "apprefix": prefix, "aplimit": "60", "format": "json"})
        r = fetch(u, H)
        try:
            j = json.loads(dec(r))
            rep["liq_pages"][prefix] = [x["title"] for x in j.get("query", {}).get("allpages", [])]
        except Exception:
            rep["liq_pages"][prefix] = {"status": r["status"], "head": dec(r)[:150]}
        time.sleep(2.2)
    # full match-info blocks from Komplettligaen
    u = "https://liquipedia.net/leagueoflegends/api.php?" + urllib.parse.urlencode(
        {"action": "parse", "page": "Komplettligaen/2026/Autumn", "prop": "text", "format": "json", "formatversion": "2"})
    r = fetch(u, H)
    try:
        html = json.loads(dec(r)).get("parse", {}).get("text", "")
        i = html.find("match-info")
        rep["liq_matchinfo_block"] = html[i:i + 4500]
        # all timestamps + team names in match-info blocks
        blocks = re.findall(r'<div class="match-info match-info--[^"]+">(.*?)(?=<div class="match-info match-info--|</div></div></div>)', html, re.S)
        rep["liq_matchinfo_n"] = len(blocks)
        sample = []
        for b in blocks[:8]:
            ts = re.findall(r'data-timestamp="(\d+)"', b)
            teams = re.findall(r'title="([^"]+)"', b)
            scores = re.findall(r'match-info-score[^>]*>([^<]*)<', b)
            sample.append({"ts": ts[:1], "titles": teams[:6], "scores": scores[:4]})
        rep["liq_matchinfo_samples"] = sample
    except Exception as e:
        rep["liq_matchinfo_err"] = repr(e)[:200]


section("liq_pages", s_liq_pages)
print("done", file=sys.stderr)

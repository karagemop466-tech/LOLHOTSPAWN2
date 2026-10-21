#!/usr/bin/env python3
"""Diagnostic lab v7 - MatchSchedule scores + Riot official API."""
import gzip, json, os, re, sys, traceback, urllib.request, urllib.parse, urllib.error

OUT = "data/diag"
UA = {"User-Agent": "LOLHOTSPAWN2-research/1.0 (https://github.com/karagemop466-tech/LOLHOTSPAWN2; contact via repo)",
      "Accept": "application/json,text/html;q=0.9,*/*;q=0.8", "Accept-Encoding": "gzip"}
rep = {}


def dump():
    json.dump(rep, open(os.path.join(OUT, "report7.json"), "w"), indent=1)


def fetch(url, headers=None, timeout=40):
    h = dict(UA)
    if headers:
        h.update(headers)
    try:
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"status": r.status, "body": r.read()}
    except urllib.error.HTTPError as e:
        b = b""
        try:
            b = e.read()
        except Exception:
            pass
        return {"status": e.code, "body": b}
    except Exception as e:
        return {"status": 0, "body": b"", "err": repr(e)[:160]}


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


def s_scores():
    rep["matchschedule_scores"] = {}
    tests = {
        "prm3": "OverviewPage LIKE 'Prime League 3rd Division%'",
        "tunisian": "OverviewPage LIKE 'Tunisian Super League%'",
        "rivals": "OverviewPage LIKE 'RIVALS LEAGUE%'",
        "komplett": "OverviewPage LIKE 'Komplettligaen%'",
        "4nations": "OverviewPage LIKE '4 Nations%'",
        "prm2": "OverviewPage LIKE 'PRM 2nd Division%' OR OverviewPage LIKE 'Prime League 2nd Division%'",
    }
    for k, w in tests.items():
        r, t = lp({"tables": "MatchSchedule", "fields": "Team1,Team2,Team1Score,Team2Score,Winner,DateTime_UTC,OverviewPage,BestOf,Tab",
                   "where": w, "order_by": "DateTime_UTC DESC", "limit": "500", "format": "json"})
        e = {"status": r["status"], "head": t[:200]}
        try:
            j = json.loads(t)
            e["n"] = len(j)
            e["sample"] = j[:4]
            e["with_scores"] = sum(1 for x in j if x.get("Team1Score") not in (None, ""))
            json.dump(j, open(os.path.join(OUT, f"ms_{k}.json"), "w"))
        except Exception as ex:
            e["err"] = repr(ex)[:120]
        rep["matchschedule_scores"][k] = e


section("scores", s_scores)


def s_riot():
    H = {"x-api-key": "0TvQnueqKa5mxJntVWt0w4LpLssiF19a8wLoPLD", "Origin": "https://lolesports.com",
         "Referer": "https://lolesports.com/"}
    hosts = ["https://esports-api.lolesports.com/persisted/gw", "https://prod-relapi.ewp.gg/persisted/gw"]
    rep["riot"] = {}
    for h in hosts:
        for path in ["/getLeagues?hl=en-US", "/getSchedule?hl=en-US"]:
            r = fetch(h + path, H)
            e = {"status": r["status"], "len": len(r["body"])}
            try:
                j = json.loads(dec(r))
                if "getLeagues" in path:
                    leagues = j.get("data", {}).get("leagues", [])
                    e["n"] = len(leagues)
                    e["names"] = [x.get("name") for x in leagues][:10]
                    e["prime"] = [x for x in leagues if "prime" in (x.get("name") or "").lower() or "tunis" in (x.get("name") or "").lower()][:10]
                else:
                    ev = j.get("data", {}).get("schedule", {}).get("events", [])
                    e["n"] = len(ev)
                    e["sample"] = ev[:2]
            except Exception as ex:
                e["err"] = repr(ex)[:120]
                e["head"] = dec(r)[:200]
            rep["riot"][h.split("//")[1][:22] + path] = e


section("riot", s_riot)


def s_liq_wikitext():
    H = {"User-Agent": "LOLHOTSPAWN2/2.0 (https://github.com/karagemop466-tech/LOLHOTSPAWN2)"}
    u = "https://liquipedia.net/leagueoflegends/api.php?" + urllib.parse.urlencode(
        {"action": "parse", "page": "RIVALS LEAGUE/Season 2", "prop": "wikitext", "format": "json", "formatversion": "2"})
    r = fetch(u, H)
    try:
        wt = json.loads(dec(r)).get("parse", {}).get("wikitext", "")
        rep["rivals_wikitext_len"] = len(wt)
        rep["rivals_wikitext_sample"] = wt[:2500]
        rep["rivals_match_templates"] = wt.count("{{Match")
    except Exception as e:
        rep["rivals_wikitext_err"] = repr(e)[:150]


section("liq_wikitext", s_liq_wikitext)
print("done", file=sys.stderr)

#!/usr/bin/env python3
"""Diagnostic lab v4 - capture odds feeds + model inputs for local analysis."""
import gzip, json, os, re, sys, time, traceback, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone

OUT = "data/diag"
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "LOLHOTSPAWN2-research/1.0 (https://github.com/karagemop466-tech/LOLHOTSPAWN2; contact via repo)",
      "Accept": "application/json,text/html;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.9"}
rep = {"generated_at": datetime.now(timezone.utc).isoformat()}


def dump():
    json.dump(rep, open(os.path.join(OUT, "report4.json"), "w"), indent=1)


def fetch(url, headers=None, timeout=60):
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
        rep.setdefault("errors", []).append({"section": name, "traceback": traceback.format_exc()[-2000:]})
    dump()
    print("section", name, "done", file=sys.stderr)


PIN = {"x-api-key": "CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R", "Accept": "application/json"}


def s_pinnacle():
    out = []
    for lid in (9587, 225201):
        mu = jget(f"https://guest.api.arcadia.pinnacle.com/0.1/leagues/{lid}/matchups", PIN)
        if not isinstance(mu.get("json"), list):
            continue
        for m in mu["json"]:
            mk = jget(f"https://guest.api.arcadia.pinnacle.com/0.1/matchups/{m['id']}/markets/related/straight", PIN)
            ml = None
            if isinstance(mk.get("json"), list):
                for k in mk["json"]:
                    if k.get("type") == "moneyline" and k.get("period") == 0:
                        ml = k
                        break
                if ml is None and mk["json"]:
                    ml = mk["json"][0]
            out.append({"league_id": lid, "id": m.get("id"), "start": m.get("startTime"),
                        "teams": [p.get("name") for p in m.get("participants", [])],
                        "bestOf": m.get("bestOfX"), "moneyline": ml.get("prices") if ml else None})
            time.sleep(0.2)
    rep["pinnacle_lol"] = out
    json.dump(out, open(os.path.join(OUT, "pinnacle_lol.json"), "w"), indent=1)


section("pinnacle", s_pinnacle)


def s_bovada():
    urls = {
        "prematch": "https://www.bovada.lv/services/sports/event/coupon/events/A/description/esports/league-of-legends?marketFilterId=def&preMatchOnly=true&lang=en",
        "all": "https://www.bovada.lv/services/sports/event/coupon/events/A/description/esports/league-of-legends?marketFilterId=def&lang=en",
    }
    rep["bovada"] = {}
    for k, u in urls.items():
        r = jget(u, {"Accept": "application/json", "Referer": "https://www.bovada.lv/sports/esports/league-of-legends"})
        rep["bovada"][k] = {"status": r["status"], "bytes": r["bytes"], "head": r.get("head")}
        if isinstance(r.get("json"), list):
            json.dump(r["json"], open(os.path.join(OUT, f"bovada_{k}.json"), "w"), indent=1)
            rep["bovada"][k].update({"events": len(r["json"]), "sample": str(r["json"])[:1200]})


section("bovada", s_bovada)


def s_polymarket():
    events = []
    for u in ["https://gamma-api.polymarket.com/events?tag_slug=league-of-legends&active=true&closed=false&limit=100",
              "https://gamma-api.polymarket.com/events?tag_slug=league-of-legends&active=true&closed=false&limit=100&offset=100"]:
        r = jget(u)
        if isinstance(r.get("json"), list):
            events += r["json"]
    keep = []
    for e in events:
        mk = []
        for m in e.get("markets") or []:
            try:
                prices = json.loads(m.get("outcomePrices") or "[]")
                outs = json.loads(m.get("outcomes") or "[]")
            except Exception:
                continue
            mk.append({"q": m.get("question"), "outs": outs, "prices": prices, "closed": m.get("closed")})
        keep.append({"title": e.get("title"), "slug": e.get("slug"), "end": e.get("endDate"),
                     "markets": mk, "volume": e.get("volume")})
    rep["polymarket"] = {"events": len(events), "with_markets": len(keep)}
    json.dump(keep, open(os.path.join(OUT, "polymarket_lol.json"), "w"), indent=1)
    rep["polymarket"]["match_events"] = [k["title"] for k in keep if re.search(r"\bvs\b", k["title"] or "")][:80]


section("polymarket", s_polymarket)


def s_leaguepedia():
    H = {"Accept-Encoding": "gzip", "User-Agent": "LOLHOTSPAWN2/2.0 (research; contact via GitHub repo)"}
    base = "https://lol.fandom.com/wiki/Special:CargoExport?"
    tests = {}
    for name, params in {
        "sg_500": {"tables": "ScoreboardGames", "fields": "Team1,Team2,Winner,DateTime_UTC,OverviewPage,Tournament",
                   "where": "DateTime_UTC >= '2024-10-01'", "order_by": "DateTime_UTC ASC", "limit": "500", "format": "json"},
        "sg_5000": {"tables": "ScoreboardGames", "fields": "Team1,Team2,Winner,DateTime_UTC,OverviewPage,Tournament",
                    "where": "DateTime_UTC >= '2024-10-01'", "order_by": "DateTime_UTC ASC", "limit": "5000", "format": "json"},
        "redirects": {"tables": "TeamRedirects", "fields": "AllName,Name", "limit": "5000", "format": "json"},
        "schedule": {"tables": "MatchSchedule", "fields": "Team1,Team2,DateTime_UTC,OverviewPage,BestOf,Tab",
                     "where": "DateTime_UTC >= '2026-10-21'", "order_by": "DateTime_UTC ASC", "limit": "500", "format": "json"},
        "teams": {"tables": "Teams", "fields": "Name,OverviewPage,Location,Region", "limit": "5000", "format": "json"},
    }.items():
        r = fetch(base + urllib.parse.urlencode(params), H)
        body = dec(r)
        entry = {"status": r["status"], "bytes": r["bytes"], "head": body[:200]}
        try:
            j = json.loads(body)
            entry["n"] = len(j) if isinstance(j, list) else None
            if isinstance(j, list):
                entry["sample"] = j[:2]
                json.dump(j, open(os.path.join(OUT, f"lp_{name}.json"), "w"))
        except Exception as e:
            entry["err"] = repr(e)[:120]
        tests[name] = entry
        time.sleep(3)
    rep["leaguepedia"] = tests


section("leaguepedia", s_leaguepedia)


def s_liquipedia():
    H = {"Accept-Encoding": "gzip", "User-Agent": "LOLHOTSPAWN2/2.0 (https://github.com/karagemop466-tech/LOLHOTSPAWN2; contact via repo)"}
    rep["liquipedia"] = {}
    comps = ["4 Nations 2026 Halloween Heist", "PRM 3rd Division 26-27 Fall", "RIVALS LEAGUE Season 2",
             "Tunisian Super League 2026", "Komplettligaen 2026 Autumn", "PRM 2nd Division 26-27 Fall"]
    for c in comps:
        s = jget("https://liquipedia.net/leagueoflegends/api.php?" + urllib.parse.urlencode(
            {"action": "query", "list": "search", "srsearch": c, "format": "json", "srlimit": "4"}), H)
        hits = []
        if s["status"] == 200 and isinstance(s.get("json"), dict):
            hits = [x["title"] for x in s["json"].get("query", {}).get("search", [])]
        rep["liquipedia"][c] = {"search_status": s["status"], "hits": hits}
        time.sleep(2.5)
    # inspect structure of a team page's results + a tournament page
    for title, fname in [("Absolved", "team_absolved"), ("4 Nations/2026/Halloween Heist", "tour_4nations")]:
        pg = jget("https://liquipedia.net/leagueoflegends/api.php?" + urllib.parse.urlencode(
            {"action": "parse", "page": title, "prop": "text", "format": "json", "formatversion": "2"}), H)
        key = f"{fname}_status"
        rep["liquipedia"][key] = pg["status"]
        if pg["status"] == 200 and isinstance(pg.get("json"), dict):
            html = pg["json"].get("parse", {}).get("text", "") or ""
            rep["liquipedia"][fname + "_len"] = len(html)
            open(os.path.join(OUT, fname + ".html"), "w").write(html[:600000])
            i = html.find("match-info")
            rep["liquipedia"][fname + "_matchinfo_at"] = i
            if i > 0:
                rep["liquipedia"][fname + "_slice"] = re.sub(r"\s+", " ", html[max(0, i - 500):i + 2500])
        else:
            rep["liquipedia"][fname + "_head"] = pg.get("head")
        time.sleep(2.5)


section("liquipedia", s_liquipedia)
print("done", file=sys.stderr)

#!/usr/bin/env python3
"""Diagnostic lab (temporary, not used by the production pipeline).

Runs inside GitHub Actions (open internet) and writes a compact report to
data/diag/report.json + a few HTML slices, without dumping the 2 MB lobby.
"""
import gzip, json, os, re, sys, socket, urllib.request, urllib.parse, urllib.error, hashlib
from datetime import datetime, timezone

OUT = "data/diag"
os.makedirs(OUT, exist_ok=True)
UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36 LOLHOTSPAWN2-diag/1.0",
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
rep = {"generated_at": datetime.now(timezone.utc).isoformat(), "checks": [], "lobby": {}, "probes": {}}


def fetch(url, headers=None, timeout=45):
    h = dict(UA)
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            return {"status": r.status, "bytes": len(body), "body": body, "ctype": r.headers.get("content-type", "")}
    except urllib.error.HTTPError as e:
        body = b""
        try:
            body = e.read()
        except Exception:
            pass
        return {"status": e.code, "bytes": len(body), "body": body, "ctype": e.headers.get("content-type", "") if e.headers else "", "err": "HTTPError"}
    except Exception as e:
        return {"status": 0, "bytes": 0, "body": b"", "ctype": "", "err": repr(e)[:300]}


def check(name, url, headers=None, note=""):
    r = fetch(url, headers)
    entry = {"name": name, "url": url, "status": r["status"], "bytes": r["bytes"], "ctype": r["ctype"], "note": note}
    if r.get("err"):
        entry["err"] = r["err"]
    rep["checks"].append(entry)
    print(f"{name:42s} {r['status']:>4} {r['bytes']:>9} {r['ctype'][:40]}", file=sys.stderr)
    return r, entry


# ---------------------------------------------------------------- 1. Hotspawn
r, entry = check("hotspawn_lol_lobby", "https://play.hotspawn.com/lol-pickems")
html = r["body"].decode("utf-8", "replace") if r["body"] else ""
if html:
    open(os.path.join(OUT, "lobby_head.html"), "w").write(html[:200000])
    L = {}
    L["bytes"] = len(html)
    L["sha256"] = hashlib.sha256(html.encode()).hexdigest()[:16]
    for pat in ["Who will win?", "hotspawn.com/matches/", "View Match", "WAITING FOR INFORMATION",
                "Closing Soon", "Upcoming", "Locks in", "% picked", "Points available", "This week",
                "Load more", "Next", "Next.js", "__NEXT_DATA__", "data-page", "datetime=", "startTime",
                '"start_time"', "epoch", "Tier", "Stage", "Multiplier"]:
        L[pat] = html.count(pat)
    # script tags
    scripts = []
    for m in re.finditer(r"<script([^>]*)>", html):
        attrs = m.group(1)
        scripts.append(attrs.strip()[:180])
    L["script_tags"] = scripts[:40]
    L["script_count"] = len(scripts)
    # all script types / ids
    L["script_ids"] = sorted(set(re.findall(r'id="([^"]+)"', " ".join(scripts))))[:40]
    # json script blobs
    blobs = []
    for m in re.finditer(r'<script[^>]*type="application/(?:ld\+)?json"[^>]*>(.*?)</script>', html, re.S):
        blobs.append((len(m.group(1)), m.group(1)[:400]))
    L["json_blobs"] = blobs[:10]
    # find time-ish attributes
    L["time_attrs"] = list(dict.fromkeys(re.findall(r'<time[^>]*>', html)))[:10]
    L["date_attrs"] = list(dict.fromkeys(re.findall(r'data-(?:start|date|time|timestamp)[a-z-]*="[^"]{4,40}"', html)))[:20]
    L["iso_timestamps"] = list(dict.fromkeys(re.findall(r'20\d\d-\d\d-\d\dT\d\d:\d\d(?::\d\d)?(?:\.\d+)?Z?', html)))[:20]
    L["epoch13"] = list(dict.fromkeys(re.findall(r'\b17\d{11}\b|\b18\d{11}\b', html)))[:20]
    # card slice: from a match link back 1500 chars to forward 3500
    m = re.search(r'href="(https://www\.hotspawn\.com/matches/[^"]+)"', html)
    if m:
        i = max(0, m.start() - 1800)
        L["card_slice"] = html[i:m.start() + 4200]
        open(os.path.join(OUT, "card_slice.html"), "w").write(L["card_slice"])
    # team filter counts
    tiers = re.findall(r'All tiers\s*\((\d+)\)((?:\s*[A-Z][^(]*\(\d+\))+)', re.sub(r"<[^>]+>", " ", html))
    L["tier_filter_raw"] = tiers[:2]
    tour = re.search(r'All tournaments\s*\((\d+)\)', re.sub(r"<[^>]+>", " ", html))
    L["tournament_filter_total"] = tour.group(1) if tour else None
    # how many distinct match links
    L["match_links"] = len(set(re.findall(r'https://www\.hotspawn\.com/matches/[a-z0-9\-]+', html)))
    L["match_links_unique_ids"] = len(set(re.findall(r'https://www\.hotspawn\.com/matches/[a-z0-9\-]+?-(\d{6,})', html)))
    rep["lobby"] = L
    # gzip full page for one-off inspection (small enough)
    open(os.path.join(OUT, "lobby_full.html.gz"), "wb").write(gzip.compress(html.encode(), 9))
    print("lobby bytes", len(html), "match links", L["match_links"], file=sys.stderr)

# ------------------------------------------------- Leaguepedia / Liquipedia
LP = "https://lol.fandom.com/api.php"
q = urllib.parse.urlencode({"action": "cargoquery", "format": "json", "tables": "MatchSchedule",
                            "fields": "MS.Team1,MS.Team2,MS.DateTime_UTC,MS.OverviewPage,MS.BestOf,MS.Tab,MS.MatchDay",
                            "where": "MS.DateTime_UTC >= '2026-10-21' AND MS.DateTime_UTC <= '2026-11-05'",
                            "order_by": "MS.DateTime_UTC ASC", "limit": "500"})
r, e = check("leaguepedia_matchschedule", LP + "?" + q)
if r["status"] == 200:
    try:
        rows = json.loads(r["body"]).get("cargoquery", [])
        rep["leaguepedia_schedule"] = [x.get("title", x) for x in rows]
        rep["leaguepedia_schedule_n"] = len(rows)
    except Exception as ex:
        rep["leaguepedia_schedule_err"] = repr(ex)

q = urllib.parse.urlencode({"action": "cargoquery", "format": "json", "tables": "TeamRedirects",
                            "fields": "TR.AllName,TR.Name", "limit": "500"})
r, e = check("leaguepedia_teamredirects", LP + "?" + q)
if r["status"] == 200:
    try:
        traw = json.loads(r["body"]).get("cargoquery", [])
        rep["teamredirects_sample"] = [x.get("title", x) for x in traw[:5]]
        rep["teamredirects_n"] = len(traw)
    except Exception as ex:
        rep["teamredirects_err"] = repr(ex)

for name, url in [
    ("leaguepedia_scoreboardgames", LP + "?action=cargoquery&format=json&tables=ScoreboardGames&fields=SG.Team1,SG.Team2,SG.Winner,SG.DateTime_UTC&where=SG.DateTime_UTC%3E%3D%272025-10-01%27&limit=5"),
    ("liquipedia_api_siteinfo", "https://liquipedia.net/leagueoflegends/api.php?action=query&meta=siteinfo&format=json"),
    ("liquipedia_search_absolved", "https://liquipedia.net/leagueoflegends/api.php?action=query&list=search&srsearch=Absolved&format=json&srlimit=3"),
    ("liquipedia_lpdb_v3", "https://api.liquipedia.net/api/v3/match?wiki=leagueoflegends&limit=1"),
    ("riot_lolesports_schedule", "https://esports-api.lolesports.com/persisted/gw/getSchedule?hl=en-US"),
]:
    hdr = {"x-api-key": "0TvQnueqKa5mxJntVWt0w4LpLssiF19a8wLoPLD"} if "lolesports" in url else ({"Accept-Encoding": "gzip"} if "liquipedia" in url else None)
    r, e = check(name, url, hdr)
    if r["status"] in (200, 201) and r["bytes"]:
        try:
            j = json.loads(gzip.decompress(r["body"]) if r["body"][:2] == b"\x1f\x8b" else r["body"])
            if "lolesports" in url:
                ev = j.get("data", {}).get("schedule", {}).get("events", [])
                lol = [x for x in ev if (x.get("league") or {}).get("name") and (x.get("match") or {}).get("teams")]
                rep["riot_events"] = len(ev)
                rep["riot_sample"] = [{"league": (x["league"] or {}).get("name"), "start": x.get("startTime"),
                                       "teams": [t.get("name") for t in x["match"]["teams"]]} for x in lol[:8]]
            elif "liquipedia" in url:
                rep[name + "_keys"] = list(j.keys())[:10]
                rep[name + "_sample"] = str(j)[:600]
        except Exception as ex:
            rep[name + "_err"] = repr(ex)[:200]

# ---------------------------------------------------------------- 3. odds API probes
odds_probes = [
    ("polymarket_gamma_tag", "https://gamma-api.polymarket.com/events?tag_slug=league-of-legends&active=true&closed=false&limit=5"),
    ("pinnacle_guest_lol", "https://guest.api.arcadia.pinnacle.com/0.1/sports/15/leagues/2663/matchups",
     {"x-api-key": "CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R", "Accept": "application/json"}),
    ("pinnacle_guest_sports", "https://guest.api.arcadia.pinnacle.com/0.1/sports",
     {"x-api-key": "CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R", "Accept": "application/json"}),
    ("oddspapi_sports", "https://api.oddspapi.io/v4/sports"),
    ("oddspapi_lol_fixtures", "https://api.oddspapi.io/v4/fixtures?sportId=18"),
    ("theoddsapi_sports", "https://api.the-odds-api.com/v4/sports/?apiKey=demo"),
    ("betfair", "https://api.betfair.com/exchange/betting/rest/v1.0/listEventTypes/"),
    ("sofascore_esports", "https://api.sofascore.com/api/v1/sport/esports/scheduled-events/2026-10-22",
     {"Accept": "application/json", "Referer": "https://www.sofascore.com/"}),
    ("bo3gg_matches", "https://api.bo3.gg/api/v1/matches?filter%5Bgame%5D=lol&page%5Blimit%5D=5",
     {"Accept": "application/json", "Origin": "https://bo3.gg", "Referer": "https://bo3.gg/"}),
    ("betexplorer_lol", "https://www.betexplorer.com/lol/"),
    ("oddsportal_lol", "https://www.oddsportal.com/lol/"),
    ("esportspages_lol", "https://www.esportspages.com/lol"),
    ("rivalry_lol", "https://www.rivalry.com/lol"),
    ("ggbet_lol", "https://gg.bet/en/esports/lol"),
    ("thunderpick_lol", "https://thunderpick.io/esports/league-of-legends"),
    ("esports_api_lolesports", "https://esports-api.lolesports.com/persisted/gw/getLeagues?hl=en-US",
     {"x-api-key": "0TvQnueqKa5mxJntVWt0w4LpLssiF19a8wLoPLD"}),
]
for p in odds_probes:
    name, url = p[0], p[1]
    hdr = p[2] if len(p) > 2 else None
    r, e = check(name, url, hdr)
    if r["status"] == 200 and r["bytes"] and ("json" in r["ctype"] or r["body"][:1] in (b"{", b"[")):
        try:
            body = gzip.decompress(r["body"]) if r["body"][:2] == b"\x1f\x8b" else r["body"]
            j = json.loads(body)
            rep["probes"][name] = {"keys": list(j.keys())[:8] if isinstance(j, dict) else "list", "n": len(j) if isinstance(j, (list, dict)) else None,
                                   "sample": str(j)[:500]}
        except Exception as ex:
            rep["probes"][name] = {"parse_err": repr(ex)[:150], "head": r["body"][:200].decode("utf-8", "replace")}
    else:
        rep["probes"][name] = {"status": r["status"], "head": r["body"][:160].decode("utf-8", "replace")}

# --------------------------------------------- 4. team coverage probe (Leaguepedia)
try:
    picks = json.load(open("data/picks.json"))
    unresolved = [m for m in picks["matches"] if m["method"] == "UNRESOLVED"]
except Exception:
    unresolved = []
names = []
for m in unresolved:
    names += [m["team1"], m["team2"]]
names = list(dict.fromkeys(names))
rep["unresolved_team_names_n"] = len(names)
rep["unresolved_team_names"] = names[:400]
# how many appear anywhere in a 400-day pull of ScoreboardGames?
since = "2025-09-01 00:00:00"
found = {}
off = 0
allgames = []
for _ in range(14):
    q = urllib.parse.urlencode({"action": "cargoquery", "format": "json", "tables": "ScoreboardGames=SG",
                                "fields": "SG.Team1,SG.Team2,SG.Winner,SG.DateTime_UTC,SG.OverviewPage",
                                "where": f"SG.DateTime_UTC >= '{since}' AND SG.Winner IS NOT NULL",
                                "order_by": "SG.DateTime_UTC ASC", "limit": "500", "offset": str(off)})
    rr = fetch(LP + "?" + q)
    if rr["status"] != 200:
        break
    try:
        rows = json.loads(rr["body"]).get("cargoquery", [])
    except Exception:
        break
    if not rows:
        break
    for x in rows:
        t = x.get("title", x)
        allgames.append(t)
    off += 500
rep["leaguepedia_games_scanned"] = len(allgames)
norm = lambda s: re.sub(r"[^a-z0-9]", "", (s or "").lower())
seen = set()
for g in allgames:
    for k in ("Team1", "Team2"):
        if g.get(k):
            seen.add(norm(g[k]))
rep["leaguepedia_distinct_teamnames"] = len(seen)
hit = [n for n in names if norm(n) in seen]
rep["unresolved_names_with_lp_games"] = len(hit)
rep["unresolved_hits"] = hit[:200]
rep["unresolved_miss"] = [n for n in names if norm(n) not in seen][:200]

json.dump(rep, open(os.path.join(OUT, "report.json"), "w"), indent=1)
print("wrote", os.path.join(OUT, "report.json"), "checks", len(rep["checks"]), file=sys.stderr)

#!/usr/bin/env python3
"""Diagnostic lab v5 - Leaguepedia recent results coverage + Liquipedia bracket structure."""
import gzip, json, os, re, sys, time, traceback, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone

OUT = "data/diag"
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "LOLHOTSPAWN2-research/1.0 (https://github.com/karagemop466-tech/LOLHOTSPAWN2; contact via repo)",
      "Accept": "application/json,text/html;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.9",
      "Accept-Encoding": "gzip"}
rep = {"generated_at": datetime.now(timezone.utc).isoformat()}


def dump():
    json.dump(rep, open(os.path.join(OUT, "report5.json"), "w"), indent=1)


def fetch(url, headers=None, timeout=60):
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
        return {"status": 0, "body": b"", "bytes": 0, "err": repr(e)[:200]}


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
        rep.setdefault("errors", []).append({"section": name, "traceback": traceback.format_exc()[-2000:]})
    dump()
    print("section", name, "done", file=sys.stderr)


LPX = "https://lol.fandom.com/wiki/Special:CargoExport?"


def lp(params):
    r = fetch(LPX + urllib.parse.urlencode(params))
    return r, dec(r)


def s_recent():
    r, t = lp({"tables": "ScoreboardGames", "fields": "Team1,Team2,Winner,DateTime_UTC,OverviewPage,Tournament",
               "where": "DateTime_UTC >= '2026-07-01'", "order_by": "DateTime_UTC ASC", "limit": "5000", "format": "json"})
    rep["recent_status"] = r["status"]
    try:
        j = json.loads(t)
        json.dump(j, open(os.path.join(OUT, "lp_recent_sg.json"), "w"))
        import collections
        rep["recent_n"] = len(j)
        rep["recent_tournaments"] = collections.Counter(x["Tournament"] for x in j).most_common(60)
        rep["recent_max_date"] = max((x["DateTime UTC"] for x in j), default=None)
    except Exception as e:
        rep["recent_err"] = repr(e)[:200]
        rep["recent_head"] = t[:300]


section("recent", s_recent)


def s_leagues():
    rep["league_checks"] = {}
    for name in ["RIVALS%", "Komplettligaen%", "Prime League 3rd%", "Tunisian%", "4 Nations%", "LigaGG%", "LGC Rising%", "Arabian League 2nd%"]:
        r, t = lp({"tables": "ScoreboardGames", "fields": "Team1,Team2,Winner,DateTime_UTC,OverviewPage,Tournament",
                   "where": f"Tournament LIKE '{name}'", "order_by": "DateTime_UTC DESC", "limit": "5", "format": "json"})
        entry = {"status": r["status"], "head": t[:200]}
        try:
            j = json.loads(t)
            entry["n"] = len(j)
            entry["sample"] = j[:3]
        except Exception as e:
            entry["err"] = repr(e)[:100]
        rep["league_checks"][name] = entry
        time.sleep(2)


section("leagues", s_leagues)


def s_history():
    # 4 x 5000 rows, windowed by date, for the model
    windows = [("2024-10-01", "2025-04-01"), ("2025-04-01", "2025-10-01"),
               ("2025-10-01", "2026-04-01"), ("2026-04-01", "2026-10-22")]
    allrows = []
    rep["history_windows"] = []
    for a, b in windows:
        r, t = lp({"tables": "ScoreboardGames", "fields": "Team1,Team2,Winner,DateTime_UTC,OverviewPage,Tournament",
                   "where": f"DateTime_UTC >= '{a}' AND DateTime_UTC < '{b}'",
                   "order_by": "DateTime_UTC ASC", "limit": "5000", "format": "json"})
        try:
            j = json.loads(t)
            rep["history_windows"].append({"from": a, "to": b, "status": r["status"], "n": len(j),
                                           "first": j[0]["DateTime UTC"] if j else None, "last": j[-1]["DateTime UTC"] if j else None})
            allrows += j
        except Exception as e:
            rep["history_windows"].append({"from": a, "to": b, "status": r["status"], "err": repr(e)[:100], "head": t[:150]})
        time.sleep(3)
    json.dump(allrows, open(os.path.join(OUT, "lp_history_sg.json"), "w"))
    rep["history_total"] = len(allrows)


section("history", s_history)


def s_liquipedia():
    H = {"User-Agent": "LOLHOTSPAWN2/2.0 (https://github.com/karagemop466-tech/LOLHOTSPAWN2; contact via repo)"}
    rep["liquipedia"] = {}
    pages = ["RIVALS LEAGUE/Season 2", "Komplettligaen/2026/Autumn",
             "Prime League 3rd Division/2027 Season/Fall Split", "4 Nations/2026 Season/Halloween Heist",
             "Tunisian Super League/2026 Season"]
    for p in pages:
        u = "https://liquipedia.net/leagueoflegends/api.php?" + urllib.parse.urlencode(
            {"action": "parse", "page": p, "prop": "text", "format": "json", "formatversion": "2"})
        r = fetch(u, H)
        t = dec(r)
        entry = {"status": r["status"], "bytes": len(t)}
        try:
            j = json.loads(t)
            html = j.get("parse", {}).get("text", "") or ""
            entry["html_len"] = len(html)
            entry["classes"] = {c: html.count(c) for c in ["match-info", "brkts-match", "brkts-popup", "team-template-team-standard", "match-row", "wikitable"]}
            for marker in ["match-info", "brkts-match", "match-row", "wikitable"]:
                i = html.find(marker)
                if i > 0:
                    entry["slice"] = re.sub(r"\s+", " ", html[max(0, i - 300):i + 1800])
                    break
            open(os.path.join(OUT, "liq_" + re.sub(r"[^a-z0-9]+", "_", p.lower()) + ".html"), "w").write(html[:400000])
        except Exception as e:
            entry["err"] = repr(e)[:120]
            entry["head"] = t[:200]
        rep["liquipedia"][p] = entry
        time.sleep(2.5)


section("liquipedia", s_liquipedia)
print("done", file=sys.stderr)

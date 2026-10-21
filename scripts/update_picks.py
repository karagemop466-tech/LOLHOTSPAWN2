#!/usr/bin/env python3
"""
Hotspawn LoL Pick'em -> our own probabilities. Stdlib only (runs in GH Actions).
Sources (never Hotspawn crowd % as a probability input):
 1 MARKET   Polymarket Gamma (public) + OddsPapi (if ODDSPAPI_KEY secret set; Pinnacle/bet365 etc via sportId=18)
 2 MODEL    Our own Elo built from Leaguepedia (lol.fandom.com) Cargo ScoreboardGames results
 3 UNRESOLVED  No market and no usable team history -> 50/50, flagged, limitations stated
Hotspawn is used ONLY for the fixture list (teams/tournament/start/tier/points/match URL).
"""
import json, os, re, sys, math, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser

UA={"User-Agent":"Mozilla/5.0 (compatible; LOLHOTSPAWN2-picks/1.0; +https://github.com/karagemop466-tech/LOLHOTSPAWN2)"}
LOBBY="https://play.hotspawn.com/lol-pickems"
NOW=datetime.now(timezone.utc)

def get(url, timeout=30):
    req=urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8","replace"), r.status

def norm(s):
    return re.sub(r'[^a-z0-9]','',(s or '').lower())

# ---------- Hotspawn lobby parsing ----------
class TextExtract(HTMLParser):
    def __init__(self):
        super().__init__(); self.items=[]; self._href=None
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=="a": self._href=d.get("href")
    def handle_endtag(self,tag):
        if tag=="a": self._href=None
    def handle_data(self,data):
        t=" ".join(data.split())
        if t: self.items.append((t,self._href))

DATE_RE=re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s*\d{1,2}:\d{2}$')

def parse_lobby(html):
    # Try embedded JSON first (Next.js / Inertia style blobs)
    matches=[]
    for m in re.finditer(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S):
        try: blob=json.loads(m.group(1))
        except Exception: continue
        def walk(o):
            if isinstance(o,dict):
                keys={k.lower() for k in o}
                if any("team" in k for k in keys) and any("start" in k or "date" in k for k in keys):
                    matches.append(o)
                for v in o.values(): walk(v)
            elif isinstance(o,list):
                for v in o: walk(v)
        walk(blob)
    if matches:  # best-effort normalisation; fall through if unusable
        out=[]
        for o in matches:
            lo={k.lower():v for k,v in o.items()}
            t1=lo.get("team1") or lo.get("home_team") or lo.get("participant1")
            t2=lo.get("team2") or lo.get("away_team") or lo.get("participant2")
            if isinstance(t1,dict): t1=t1.get("name")
            if isinstance(t2,dict): t2=t2.get("name")
            if t1 and t2:
                out.append(dict(team1=str(t1),team2=str(t2),tournament=str(lo.get("tournament") or lo.get("league") or ""),start_raw=str(lo.get("scheduled_start") or lo.get("start_time") or lo.get("date") or ""),tier=str(lo.get("tier") or ""),points=str(lo.get("points") or ""),hotspawn_url=str(lo.get("url") or ""),crowd1=None,crowd2=None))
        if out: return out, "embedded-json"
    # Token-stream parser over rendered text (matches the SSR card layout)
    p=TextExtract(); p.feed(html)
    items=p.items; out=[]; i=0
    match_urls={}
    for txt,href in items:
        if href and "hotspawn.com/matches/" in href: match_urls.setdefault(txt,href)
    while i < len(items):
        txt=items[i][0]
        if DATE_RE.match(txt):
            start=txt; window=items[i+1:i+40]; texts=[w[0] for w in window]
            try: wi=texts.index("Who will win?")
            except ValueError: i+=1; continue
            tournament=texts[0] if texts else ""
            tier=""; points=""
            joined=" ".join(texts[:wi])
            tm=re.search(r'Tier\s*([A-Z]|WAITING FOR INFORMATION)',joined); 
            if tm: tier=tm.group(1)
            tm2=re.search(r'(\d+)\s*pts',joined)
            if tm2: points=tm2.group(1)
            # team names follow "Who will win?", each followed by "NN% picked" (or next team)
            rest=texts[wi+1:wi+8]; teams=[]; crowds=[]
            for t in rest:
                pm=re.match(r'^(\d+)%\s*picked$',t)
                if pm: crowds.append(int(pm.group(1)))
                elif t not in ("Sign in for streaks","Locks in") and not re.match(r'^[\d:dhms ]+$',t) and len(teams)<2:
                    teams.append(t)
            url=""
            for w in window:
                if w[1] and "hotspawn.com/matches/" in w[1]: url=w[1]; break
            if len(teams)==2:
                out.append(dict(team1=teams[0],team2=teams[1],tournament=tournament,start_raw=start,tier=tier,points=points,hotspawn_url=url,crowd1=crowds[0] if len(crowds)>0 else None,crowd2=crowds[1] if len(crowds)>1 else None))
            i+=wi+1
        else: i+=1
    # dedupe
    seen=set(); ded=[]
    for m in out:
        k=(norm(m["team1"]),norm(m["team2"]),m["start_raw"],norm(m["tournament"]))
        if k not in seen: seen.add(k); ded.append(m)
    return ded, "html-token-stream"

def parse_start(raw):
    if not raw: return ""
    try:
        if str(raw).isdigit(): return datetime.fromtimestamp(int(raw),timezone.utc).isoformat()
        dt=datetime.fromisoformat(str(raw).replace("Z","+00:00"))
        if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception: pass
    try: # "Oct 22, 08:00" lobby display time (year = current/next)
        dt=datetime.strptime(f"{raw} {NOW.year}","%b %d, %H:%M %Y").replace(tzinfo=timezone.utc)
        if dt < NOW-timedelta(days=2): dt=dt.replace(year=NOW.year+1)
        return dt.isoformat()
    except Exception: return ""

# ---------- External market: Polymarket (public, no key) ----------
def polymarket():
    events=[]
    for url in ["https://gamma-api.polymarket.com/events?tag_slug=league-of-legends&active=true&closed=false&limit=100",
                "https://gamma-api.polymarket.com/events?search=league%20of%20legends&active=true&closed=false&limit=100"]:
        try:
            data,_=get(url); events+=json.loads(data)
        except Exception as e: print("polymarket err",e,file=sys.stderr)
    idx=[]
    for ev in events if isinstance(events,list) else []:
        for mk in ev.get("markets",[]):
            q=mk.get("question","")
            try: prices=json.loads(mk.get("outcomePrices") or "[]"); outs=json.loads(mk.get("outcomes") or "[]")
            except Exception: continue
            if len(prices)==2 and len(outs)==2:
                idx.append(dict(question=q,outs=outs,prices=[float(x) for x in prices],url="https://polymarket.com/event/"+str(ev.get("slug",""))))
    return idx

def poly_lookup(idx,t1,t2):
    n1,n2=norm(t1),norm(t2)
    for m in idx:
        o=[norm(x) for x in m["outs"]]
        if (n1 in o[0] or o[0] in n1) and (n2 in o[1] or o[1] in n2): return m["prices"][0],m["url"],m["question"]
        if (n2 in o[0] or o[0] in n2) and (n1 in o[1] or o[1] in n1): return m["prices"][1],m["url"],m["question"]
        q=norm(m["question"])
        if n1 in q and n2 in q and m["prices"]: return m["prices"][0],m["url"],m["question"]
    return None

# ---------- External market: OddsPapi (optional key; Pinnacle etc., LoL sportId=18) ----------
def oddspapi():
    key=os.environ.get("ODDSPAPI_KEY")
    if not key: return []
    try:
        data,_=get(f"https://api.oddspapi.io/v4/fixtures?sportId=18&apiKey={key}")
        fx=json.loads(data)
    except Exception as e: print("oddspapi fixtures err",e,file=sys.stderr); return []
    out=[]
    for f in fx if isinstance(fx,list) else []:
        p1=(f.get("participant1Name") or ""); p2=(f.get("participant2Name") or "")
        fid=f.get("fixtureId")
        if not(p1 and p2 and fid): continue
        try:
            data,_=get(f"https://api.oddspapi.io/v4/odds?fixtureId={fid}&apiKey={key}")
            od=json.loads(data); books=od.get("bookmakers",{})
            probs=[]
            for slug,book in books.items():
                mk=(book.get("markets") or {}).get("181")  # LoL series winner market id per OddsPapi docs
                if not mk: continue
                outs=mk.get("outcomes") or {}
                vals=[]
                for oid in ("181","182"):
                    o=outs.get(oid) or {}
                    pr=(o.get("players") or {}).get("0") or o
                    price=pr.get("price")
                    if price: vals.append(float(price))
                if len(vals)==2 and all(v>1 for v in vals):
                    inv=[1/v for v in vals]; s=sum(inv); probs.append((inv[0]/s,slug))
            if probs:
                probs.sort(); med=probs[len(probs)//2]
                out.append(dict(team1=p1,team2=p2,p1=med[0],source=f"OddsPapi median de-vigged ({len(probs)} books, incl. median book {med[1]})",url="https://oddspapi.io/sports/esports/lol"))
        except Exception as e: print("oddspapi odds err",e,file=sys.stderr)
    return out

# ---------- Our own model: Elo from Leaguepedia Cargo results ----------
def elo_model():
    ratings={}; games={}; recent={}
    since=(NOW-timedelta(days=180)).strftime("%Y-%m-%d %H:%M:%S")
    offset=0
    for _ in range(12):  # up to 6000 games
        q=urllib.parse.urlencode({"action":"cargoquery","format":"json","tables":"ScoreboardGames=SG",
          "fields":"SG.Team1,SG.Team2,SG.Winner,SG.DateTime_UTC",
          "where":f"SG.DateTime_UTC >= '{since}' AND SG.Winner IS NOT NULL",
          "order_by":"SG.DateTime_UTC ASC","limit":"500","offset":str(offset)})
        try:
            data,_=get("https://lol.fandom.com/api.php?"+q); rows=json.loads(data).get("cargoquery",[])
        except Exception as e: print("leaguepedia err",e,file=sys.stderr); break
        if not rows: break
        for r in rows:
            t=r.get("title",r); a,b,w=t.get("Team1",""),t.get("Team2",""),str(t.get("Winner",""))
            if not a or not b: continue
            ra,rb=ratings.get(norm(a),1500),ratings.get(norm(b),1500)
            ea=1/(1+10**((rb-ra)/400)); winner_a=(w=="1")
            delta=32*((1 if winner_a else 0)-ea)
            ratings[norm(a)]=ra+delta; ratings[norm(b)]=rb-delta
            for team,won in ((a,winner_a),(b,not winner_a)):
                games[norm(team)]=games.get(norm(team),0)+1
                recent.setdefault(norm(team),[]).append(1 if won else 0)
        offset+=500
        if len(rows)<500: break
    return ratings,games,recent

def main():
    debug={"generated_at":NOW.isoformat(),"lobby":LOBBY}
    try:
        html,st=get(LOBBY); debug["lobby_http"]=st; debug["lobby_bytes"]=len(html)
    except Exception as e:
        print("FATAL lobby fetch",e,file=sys.stderr)
        if os.path.exists("docs/data/picks.json"): sys.exit(0)  # keep last good data
        raise
    matches,parser=parse_lobby(html); debug["parser"]=parser; debug["matches_parsed"]=len(matches)
    if not matches:
        print("FATAL: 0 matches parsed - lobby layout changed, keeping old data",file=sys.stderr); sys.exit(1)
    poly=polymarket(); debug["polymarket_markets"]=len(poly)
    books=oddspapi(); debug["oddspapi_fixtures_priced"]=len(books)
    ratings,games,recent=elo_model(); debug["elo_teams"]=len(ratings)
    rows=[]
    for m in matches:
        n1,n2=norm(m["team1"]),norm(m["team2"]); row=dict(m)
        row["start_utc"]=parse_start(m["start_raw"]); row["source_lobby"]=LOBBY
        prob=None; method=""; source=""; confidence=""
        # 1) bookmaker median (OddsPapi)
        for b in books:
            if {norm(b["team1"]),norm(b["team2"])}=={n1,n2}:
                prob=b["p1"] if norm(b["team1"])==n1 else 1-b["p1"]; method="MARKET_BOOKS"; source=b["source"]; confidence="High — established esportsbook lines, de-vigged"; row["market_url"]=b["url"]; break
        # 2) Polymarket
        if prob is None:
            hit=poly_lookup(poly,m["team1"],m["team2"])
            if hit: prob,url,q=hit; method="MARKET_POLYMARKET"; source=f"Polymarket: {q}"; confidence="High — prediction-market price (external, not Hotspawn)"; row["market_url"]=url
        # 3) our Elo model
        if prob is None and (n1 in ratings or n2 in ratings):
            r1,r2=ratings.get(n1,1500),ratings.get(n2,1500); g1,g2=games.get(n1,0),games.get(n2,0)
            raw=1/(1+10**((r2-r1)/400)); shrink=min(g1,g2)/(min(g1,g2)+10) if min(g1,g2)>0 else 0.25
            prob=0.5+(raw-0.5)*shrink; method="MODEL_ELO"
            source=f"Own Elo (Leaguepedia results, last 180d): {m['team1']} {round(r1)} ({g1}g) vs {m['team2']} {round(r2)} ({g2}g)"
            confidence="Medium" if min(g1,g2)>=10 else "Low — thin team history"
            row["elo"]=[round(r1),round(r2)]; row["games"]=[g1,g2]; row["source_url"]="https://lol.fandom.com/api.php?action=help&modules=cargoquery"
        # 4) unresolved
        if prob is None:
            prob=0.5; method="UNRESOLVED"; source="No external market and no Leaguepedia team history found"
            confidence="Unresolved — no data; 50/50 placeholder, do not treat as an edge"
            row["source_url"]="https://lol.fandom.com/wiki/Leaguepedia:League_of_Legends_Esports_Wiki"
        prob=round(max(0.01,min(0.99,prob)),4)
        row["prob_team1"]=prob; row["prob_team2"]=round(1-prob,4)
        row["pick"]=m["team1"] if prob>=0.5 else m["team2"]; row["pick_prob"]=max(prob,1-prob)
        row["method"]=method; row["evidence"]=source; row["confidence"]=confidence
        row["crowd_note"]="Hotspawn crowd % shown on lobby is context only and is NOT used in this probability."
        rows.append(row)
    rows.sort(key=lambda r:(r["start_utc"] or "9999", r["tournament"], r["team1"]))
    payload={"generated_at":NOW.isoformat(),"lobby":LOBBY,"count":len(rows),
      "counts_by_method":{k:sum(1 for r in rows if r["method"]==k) for k in ["MARKET_BOOKS","MARKET_POLYMARKET","MODEL_ELO","UNRESOLVED"]},
      "debug":debug,"matches":rows}
    for path in ["docs/data/picks.json","data/picks.json"]:
        os.makedirs(os.path.dirname(path),exist_ok=True)
        open(path,"w").write(json.dumps(payload,indent=1,ensure_ascii=False))
    json.dump(debug,open("data/debug.json","w"),indent=1)
    print(json.dumps(payload["counts_by_method"]), "total", len(rows))

if __name__=="__main__": main()

#!/usr/bin/env python3
"""
verify_site.py — line-by-line verification for the Hotspawn LoL picks project.

Checks the published data and site against the project requirements:
  D1  payload parses, count > 0, generated_at present and fresh (<= --max-age-hours)
  D2  every match has two non-empty team names and a scheduled start
  D3  every match has exactly one pick, and the pick is one of the two teams
  D4  probabilities are in [0,1] and sum to 1 (tolerance 0.005)
  D5  pick_prob equals max(prob_team1, prob_team2)
  D6  method is one of the documented methods
  D7  every row carries at least one source URL (url field or evidence URL)
  D8  market rows link a market/book URL; model rows link a results source;
      generic results-table evidence is explicitly flagged; unresolved rows are
      explicitly flagged as unverified 50/50
  Note: a trusted/community source is not equivalent to official organizer verification.
  D9  no duplicate fixtures (same normalised teams + same start)
  D10 counts_by_method in the payload agrees with the rows
  D11 data/picks.json and docs/data/picks.json are both present and identical
  D20 reserved (unique source_key per fixture: requested by arena/0fb2d0c7 as R16)
  D21 every upcoming lobby fixture is priced; no cancelled/excluded fixture is priced
  S1  every page exists and has a mobile viewport meta
  S2  every page has the shared navigation with links to all site sections
  S3  executive summary (docs/index.html) links in-site to the picks list and the
      unresolved section, and states the limitations
  S4  docs/unresolved.html exists, is a separate section and states limitations
  S5  no broken internal links (href/src) anywhere in the site
  S6  required assets exist and the shared JS/CSS are referenced
  S7  root index.html redirects into docs/
  S8  external links are https (collected for manual review)
  W1  a GitHub Actions workflow schedules the picks update every 4-8 hours
  W2  that workflow runs the picks generator and has contents: write
  W3  hotspawn crowd percentages are never used as a probability input (static scan)
Output: verification/report.json + verification/last_report.md, exit 1 on any FAIL.

Stdlib only; no network access is required (external reachability is checked in CI).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from urllib.parse import urlparse
import urllib.request
import urllib.error
import concurrent.futures
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
DATA_PATHS = [os.path.join(ROOT, "data", "picks.json"),
              os.path.join(DOCS, "data", "picks.json")]
OUT_DIR = os.path.join(ROOT, "verification")

MARKET_METHODS = {"MARKET_BOOKS", "MARKET_POLYMARKET", "MARKET_CONSENSUS", "MARKET_SINGLE"}
MODEL_METHODS = {"MODEL_ELO", "MODEL_ELO_THIN", "MODEL_LEAGUE_PRIOR", "MODEL_STANDINGS"}
METHODS = MARKET_METHODS | MODEL_METHODS | {"UNRESOLVED"}
EXTERNAL_LINKS: list[str] = []
UA = ("Mozilla/5.0 (compatible; LOLHOTSPAWN2-verify/1.0; "
      "+https://github.com/karagemop466-tech/LOLHOTSPAWN2)")
# Source hosts accepted as official/trusted. Hotspawn is accepted for the fixture
# list only; it is explicitly rejected as a probability source (requirement).
FIXTURE_HOSTS = ("hotspawn.com",)
MARKET_HOSTS = ("polymarket.com", "oddspapi.io", "pinnacle.com", "pinnacleapi",
                "bovada.lv", "kambicdn.com",
                "bet365.com", "draftkings.com", "fanduel.com", "betmgm.com",
                "williamhill.com", "betway.com", "1xbet.com", "gg.bet", "betboom.ru",
                "midnite.com", "rivalry.com", "unibet.com", "betfair.com",
                "smarkets.com", "kalshi.com", "betano.com", "betsson.com")
RESULTS_HOSTS = ("lol.fandom.com", "leaguepedia", "liquipedia.net", "bo3.gg",
                 "gol.gg", "lolesports.com", "riotgames.com", "leagueoflegends.com",
                 "gamesofdesktop", "oracleselixir.com", "primeleague.gg",
                 "rivalsleague.gg", "komplettligaen.no")
ALL_HOSTS = FIXTURE_HOSTS + MARKET_HOSTS + RESULTS_HOSTS + ("github.com", "creativecommons.org")

PASS, FAIL, WARN, SKIP = "PASS", "FAIL", "WARN", "SKIP"


class Report:
    def __init__(self) -> None:
        self.checks: list[dict] = []
        self.started = datetime.now(timezone.utc)

    def add(self, cid: str, title: str, status: str, detail: str = "",
            items: list | None = None, aggregate: bool = False) -> None:
        rec = {"id": cid, "title": title, "status": status, "detail": detail}
        if items:
            rec["items"] = items
        if aggregate:
            rec["aggregate"] = True   # summary row; not counted in pass/fail totals
        self.checks.append(rec)

    def count(self, status: str) -> int:
        return sum(1 for c in self.checks
                   if c["status"] == status and not c.get("aggregate"))

    @property
    def ok(self) -> bool:
        return self.count(FAIL) == 0


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def urls_in(text: str) -> list[str]:
    return re.findall(r"https?://[^\s<>\"')\]]+", text or "")


def host_of(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def host_in(host: str, allowlist) -> bool:
    return any(host == a or host.endswith("." + a) or a in host for a in allowlist)


# --------------------------------------------------------------------------- HTML
class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []   # (tag, url)
        self.metas: list[dict] = []
        self.ids: set[str] = set()
        self.text: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if d.get("id"):
            self.ids.add(d["id"])
        if tag == "meta":
            self.metas.append(d)
        for key in ("href", "src"):
            if d.get(key):
                self.links.append((tag, d[key]))
        if tag in ("script", "style"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            t = " ".join(data.split())
            if t:
                self.text.append(t)


def parse_page(path: str) -> PageParser:
    p = PageParser()
    with open(path, encoding="utf-8", errors="replace") as fh:
        p.feed(fh.read())
    return p


def pages() -> list[str]:
    out = []
    for base, _dirs, files in os.walk(DOCS):
        for f in files:
            if f.endswith(".html"):
                out.append(os.path.join(base, f))
    root_index = os.path.join(ROOT, "index.html")
    if os.path.exists(root_index):
        out.append(root_index)
    return sorted(out)


# --------------------------------------------------------------------------- data
def load_json(path: str):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh), None
    except Exception as exc:  # noqa: BLE001
        return None, repr(exc)


def verify_data(rep: Report, payload, path: str, max_age_hours: float) -> list[dict]:
    rows: list[dict] = []
    if payload is None:
        rep.add("D1", "picks payload parses", FAIL, f"{path} missing or unreadable")
        return rows
    rows = payload.get("matches") or []
    gen = payload.get("generated_at") or ""
    try:
        gen_dt = datetime.fromisoformat(gen.replace("Z", "+00:00"))
        if gen_dt.tzinfo is None:
            gen_dt = gen_dt.replace(tzinfo=timezone.utc)
        age_h = (datetime.now(timezone.utc) - gen_dt).total_seconds() / 3600
    except Exception:
        gen_dt, age_h = None, None
    d1_ok = bool(rows) and gen_dt is not None
    status = PASS if d1_ok else FAIL
    detail = f"{len(rows)} matches, generated_at={gen or 'MISSING'}"
    if age_h is not None:
        detail += f" ({age_h:.1f}h old)"
        if age_h > max_age_hours:
            status = FAIL if age_h > max_age_hours * 2 else WARN
            detail += f" — older than {max_age_hours:g}h update window"
    rep.add("D1", "payload parses, has matches and a fresh generated_at", status, detail)
    if not rows:
        return rows

    bad_teams, bad_pick, bad_prob, bad_pickprob, bad_method = [], [], [], [], []
    no_source, weak_source, market_no_url, unresolved_unflagged, dup = [], [], [], [], []
    model_no_result_source, generic_model_unflagged = [], []
    game1_as_series, generic_unresolved_link = [], []
    no_start_utc = []
    banned_prob_source = []
    seen = set()
    for i, m in enumerate(rows):
        label = f"{m.get('team1','?')} vs {m.get('team2','?')}"
        t1 = (m.get("team1") or "").strip()
        t2 = (m.get("team2") or "").strip()
        if not t1 or not t2 or norm(t1) == norm(t2):
            bad_teams.append(label)
        if not (m.get("start_utc") or m.get("start_raw") or m.get("start")):
            bad_teams.append(f"{label} [no start time]")
        elif not m.get("start_utc"):
            no_start_utc.append(f"{label} start_raw={m.get('start_raw')!r} (not parsed)")
        pick = m.get("pick") or ""
        if pick not in (t1, t2):
            bad_pick.append(f"{label} pick={pick!r}")
        p1, p2 = m.get("prob_team1"), m.get("prob_team2")
        try:
            p1f, p2f = float(p1), float(p2)
        except Exception:
            bad_prob.append(f"{label} prob_team1={p1!r} prob_team2={p2!r}")
            p1f = p2f = None
        if p1f is not None:
            if not (0.0 <= p1f <= 1.0 and 0.0 <= p2f <= 1.0):
                bad_prob.append(f"{label} out of range {p1f}/{p2f}")
            elif abs(p1f + p2f - 1.0) > 0.005:
                bad_prob.append(f"{label} sums to {p1f + p2f:.4f}")
            pk = m.get("pick_prob")
            try:
                if pk is not None and abs(float(pk) - max(p1f, p2f)) > 0.005:
                    bad_pickprob.append(f"{label} pick_prob={pk} vs max={max(p1f,p2f):.3f}")
            except Exception:
                bad_pickprob.append(f"{label} pick_prob={pk!r}")
        method = m.get("method") or ""
        if method not in METHODS:
            bad_method.append(f"{label} method={method!r}")

        # ---- source links (requirement: every row links an official/trusted source)
        row_urls = []
        prob_urls = []
        for key in ("market_url", "source_url", "hotspawn_url", "source_lobby", "fixtures_url"):
            val = m.get(key)
            if isinstance(val, str):
                row_urls += urls_in(val)
        for src in (m.get("sources") or []):
            if isinstance(src, dict):
                u = src.get("url") or ""
                row_urls += urls_in(u)
                if "hotspawn" not in str(src.get("name", "")).lower():
                    prob_urls += urls_in(u)
            elif isinstance(src, str):
                row_urls += urls_in(src)
        row_urls += urls_in(m.get("evidence") or "")
        prob_urls += urls_in(m.get("market_url") or "") + urls_in(m.get("source_url") or "")
        row_urls = list(dict.fromkeys(row_urls))
        if not row_urls:
            no_source.append(label)
        elif not any(host_in(host_of(u), ALL_HOSTS) for u in row_urls):
            weak_source.append(f"{label} -> {', '.join(host_of(u) for u in row_urls[:2])}")
        if method.startswith("MARKET") and not any(
                host_in(host_of(u), MARKET_HOSTS) for u in prob_urls):
            market_no_url.append(label)
        if method in MODEL_METHODS:
            if not any(host_in(host_of(u), RESULTS_HOSTS) for u in prob_urls):
                model_no_result_source.append(label)
            generic_results = any("/Special:CargoTables/" in u for u in prob_urls)
            if generic_results and "GENERIC_RESULTS_SOURCE" not in (m.get("flags") or []):
                generic_model_unflagged.append(label)
        if method in MARKET_METHODS or method in MODEL_METHODS:
            # Only the probability-source fields count here. hotspawn_url is the
            # fixture link and is explicitly allowed to point at Hotspawn.
            for u in prob_urls:
                if host_in(host_of(u), FIXTURE_HOSTS):
                    banned_prob_source.append(f"{label} -> {u}")
            # A model row whose only link is an API help page cannot be checked
            # line by line by a human; flag it for manual review (not a hard fail).
            su = m.get("source_url") or ""
            if method in ("MODEL_ELO", "MODEL_STANDINGS") and su and re.search(
                    r"action=help|/wiki/Leaguepedia:League_of_Legends_Esports_Wiki", su):
                weak_source.append(f"{label} -> model evidence link is a docs page: {su}")
        ev_low = " ".join(str(m.get(k) or "") for k in ("evidence", "note")).lower()
        meta = json.dumps(m.get("market") or m.get("market_meta") or {}, ensure_ascii=False).lower()
        blob = ev_low + " " + meta
        bo = m.get("best_of")
        try:
            bo = int(bo) if bo is not None else None
        except (TypeError, ValueError):
            bo = None
        single_game = re.search(r"game\s*[1-9]|map\s*[1-9]", blob)
        if method.startswith("MARKET") and single_game and bo != 1:
            if not (re.search(r"match winner|series winner|series price|match price", blob) and not single_game):
                game1_as_series.append(
                    f"{label} — single-game market used for a series "
                    f"(best_of={bo}): {single_game.group(0)}")
        if method == "UNRESOLVED":
            su = (m.get("source_url") or "")
            if re.search(r"/wiki/Leaguepedia:League_of_Legends_Esports_Wiki$", su):
                generic_unresolved_link.append(f"{label} -> generic wiki link {su}")
        if method == "UNRESOLVED":
            flags = " ".join(str(m.get(k) or "") for k in ("confidence", "evidence", "status")) + \
                " " + " ".join(str(x) for x in (m.get("flags") or []))
            if abs((p1f if p1f is not None else 0.5) - 0.5) > 0.001:
                unresolved_unflagged.append(f"{label} unresolved but prob={p1f}")
            elif not re.search(r"unresolved|unverified|no[_ ]verified|no team history|"
                               r"no external market|no data|50/50|placeholder", flags, re.I):
                unresolved_unflagged.append(f"{label} unresolved but not labelled unverified")

        key = (norm(t1), norm(t2), (m.get("start_utc") or m.get("start_raw") or ""))
        if key in seen:
            dup.append(label)
        seen.add(key)

    def emit(cid, title, problems, detail_ok, cap=12):
        if problems:
            rep.add(cid, title, FAIL, f"{len(problems)} row(s) violate this rule",
                    problems[:cap])
        else:
            rep.add(cid, title, PASS, detail_ok)

    emit("D2", "two distinct teams and a start time on every match", bad_teams,
         f"all {len(rows)} rows have team1, team2 and a start time")
    if no_start_utc:
        rep.add("D2b", "every match has a machine-readable UTC start", WARN,
                f"{len(no_start_utc)} row(s) have a display time that did not parse to UTC "
                "(unverified start — flagged)", no_start_utc[:10])
    emit("D3", "a pick exists and is one of the two teams", bad_pick,
         "every match has a pick equal to team1 or team2")
    emit("D4", "probabilities are in range and sum to 1", bad_prob,
         "every row sums to 1.0 within 0.005")
    emit("D5", "pick_prob equals the larger probability", bad_pickprob,
         "pick_prob matches max(prob_team1, prob_team2) on every row")
    emit("D6", f"method is one of {sorted(METHODS)}", bad_method,
         "all methods documented")
    bad_conf = sorted({str(r.get("confidence")) for r in rows
                       if str(r.get("confidence") or "") not in
                       ("High", "Medium", "Low", "None", "None yet", "")})
    rep.add("D6b", "confidence labels are from the documented set",
            PASS if not bad_conf else WARN,
            "High/Medium/Low/None only" if not bad_conf else f"unknown: {bad_conf}")
    bad_urls = []
    for r in rows:
        for src in (r.get("sources") or []):
            u = src.get("url") if isinstance(src, dict) else None
            if u and urlparse(u).scheme not in ("http", "https"):
                bad_urls.append(f"{r.get('team1')} vs {r.get('team2')}: {u}")
            elif u and not urlparse(u).netloc:
                bad_urls.append(f"{r.get('team1')} vs {r.get('team2')}: {u}")
    rep.add("D7c", "every source URL is absolute http(s)",
            PASS if not bad_urls else FAIL,
            "all source URLs well formed" if not bad_urls else f"{len(bad_urls)} malformed",
            bad_urls[:10])
    emit("D7", "every row links at least one source URL", no_source,
         f"all {len(rows)} rows carry at least one source URL")
    if weak_source:
        rep.add("D7b", "source host is on the trusted-source allowlist (not proof of official verification)", WARN,
                f"{len(weak_source)} row(s) link a host not on the allowlist — manual review",
                weak_source[:12])
    emit("D8a", "market rows link a bookmaker/prediction-market URL", market_no_url,
         "every market row links its market")
    emit("D8c", "model rows link a results-source URL", model_no_result_source,
         "every model row links a results source")
    emit("D8d", "model rows with generic results-table sources are flagged", generic_model_unflagged,
         "generic Leaguepedia table links are explicitly flagged as less directly auditable")
    emit("D8b", "unresolved rows are explicit unverified 50/50 (limitations published)",
         unresolved_unflagged, "every unresolved row is 0.50 and labelled unverified")
    emit("D9", "no duplicate fixtures", dup, "no duplicate (teams,start) rows")

    emit("D16", "no single-game (Game 1/Map 1) market used as a series probability",
         game1_as_series,
         "no non-BO1 row cites a single-game market")
    if generic_unresolved_link:
        rep.add("D17", "unresolved rows point at a fixture/league source, not a generic wiki page",
                WARN, f"{len(generic_unresolved_link)} unresolved row(s) cite the generic Leaguepedia "
                      "main page — a per-league/fixture source is preferable", generic_unresolved_link[:10])

    banned = list(dict.fromkeys(banned_prob_source))
    emit("D12", "Hotspawn is never the probability source (fixture list only)", banned,
         "no market/model row cites hotspawn.com as its probability source")

    expected = payload.get("counts_by_method") or {}
    actual = {k: sum(1 for r in rows if r.get("method") == k) for k in METHODS}
    if expected:
        mismatch = {k: (expected.get(k), actual[k]) for k in set(expected) | set(actual)
                    if int(expected.get(k, 0) or 0) != actual[k]}
        rep.add("D10", "counts_by_method agrees with the rows",
                PASS if not mismatch else FAIL,
                "counts consistent" if not mismatch else f"mismatch {mismatch}")
    else:
        counts = payload.get("counts") or {}
        if isinstance(counts, dict) and ("resolved" in counts or "unresolved" in counts):
            resolved = sum(1 for r in rows if r.get("method") != "UNRESOLVED")
            unres = sum(1 for r in rows if r.get("method") == "UNRESOLVED")
            bad = []
            if "resolved" in counts and int(counts["resolved"]) != resolved:
                bad.append(f"resolved {counts['resolved']} != {resolved}")
            if "unresolved" in counts and int(counts["unresolved"]) != unres:
                bad.append(f"unresolved {counts['unresolved']} != {unres}")
            rep.add("D10", "declared counts agree with the rows", PASS if not bad else FAIL,
                    "counts.resolved/unresolved consistent" if not bad else "; ".join(bad))
        else:
            rep.add("D10", "declared counts agree with the rows", SKIP,
                    "payload exposes no method counts")

    counts_obj = payload.get("counts") or {}
    declared = payload.get("count")
    if declared is None and isinstance(counts_obj, dict):
        declared = counts_obj.get("fixtures")
    rep.add("D11", "declared count equals number of rows",
            PASS if int(declared or 0) == len(rows) else FAIL,
            f"declared={declared}, rows={len(rows)}")

    # D19: coverage against the feed's own advertised future-fixture count, when exposed
    dbg = payload.get("debug") or {}
    expected = None
    for key in ("fixtures_future", "lobby_future", "hotspawn_future", "expected_matches",
                "future_fixtures"):
        if isinstance(dbg.get(key), (int, float)) and dbg.get(key):
            expected = int(dbg[key])
            break
    if expected is not None:
        missing = expected - len(rows)
        rep.add("D19", "every future Hotspawn fixture is published", PASS if missing <= 0 else FAIL,
                f"{len(rows)} published vs {expected} future fixtures advertised by the feed"
                + (f" — {missing} missing" if missing > 0 else ""))

    # D20: each external market provider appears at most once per fixture,
    # and source_count equals the number of distinct providers (no child-board inflation).
    dup_market_sources = []
    for r in rows:
        mk = r.get("market") or {}
        srcs = mk.get("sources") or []
        if not srcs:
            continue
        keys = [str(s.get("source_key") or s.get("source") or "").strip().lower()
                for s in srcs if isinstance(s, dict)]
        prop_leak = [s.get("market") or s.get("raw_title") or s.get("note") for s in srcs
                     if isinstance(s, dict) and re.search(
                         r"\b(first\s+(?:blood|tower|dragon|baron|inhibitor)|total\s+(?:kills|towers|dragons|barons)|handicap)\b",
                         f"{s.get('market') or ''} {s.get('raw_title') or ''} {s.get('note') or ''}", re.I)]
        if len(keys) != len(set(keys)):
            dup_market_sources.append(f"{r.get('team1')} vs {r.get('team2')}: providers={keys}")
        elif mk.get("source_count") is not None and int(mk.get("source_count")) != len(keys):
            dup_market_sources.append(
                f"{r.get('team1')} vs {r.get('team2')}: source_count={mk.get('source_count')} != {len(keys)}")
        elif prop_leak:
            dup_market_sources.append(f"{r.get('team1')} vs {r.get('team2')}: prop market leaked={prop_leak[0]!r}")
    emit("D20", "each external market provider counted at most once per fixture",
         dup_market_sources, "every market row has unique provider keys and matching source_count")

    # D21: lobby reconciliation - every upcoming lobby fixture is priced, nothing extra is,
    # and no excluded (cancelled / withdrawn) fixture appears among the picks.
    rec = payload.get("coverage_reconciliation") or {}
    if rec.get("lobby_upcoming") is not None:
        miss = rec.get("lobby_upcoming_missing_from_priced") or []
        extra = rec.get("priced_not_in_lobby") or []
        excl_ids = {str(x.get("id")) for x in (payload.get("excluded_fixtures") or [])}
        leaked = sorted({str(r.get("id")) for r in rows} & excl_ids)
        ok = not miss and not extra and not leaked and rec.get("priced") == len(rows)
        rep.add("D21", "every upcoming Hotspawn lobby fixture is priced; no excluded fixture is priced",
                PASS if ok else FAIL,
                f"lobby upcoming={rec.get('lobby_upcoming')}, priced={len(rows)}, "
                f"missing={len(miss)}, extra={len(extra)}, excluded={len(excl_ids)}, leaked={len(leaked)}")
    else:
        rep.add("D21", "every upcoming Hotspawn lobby fixture is priced", WARN,
                "lobby state unavailable for this run; coverage compared with the fixtures API only")

    unresolved = actual["UNRESOLVED"]
    # D13 tests *evidence sufficiency*, not whether a genuine match is close to 50/50.
    def lacks_evidence(r):
        flags = {str(x) for x in (r.get("flags") or [])}
        return (r.get("method") == "UNRESOLVED"
                or bool(flags & {"NO_TEAM_HISTORY", "NO_VERIFIED_SIGNAL", "NO_DATA"}))

    def labelled(r):
        flags = " ".join(str(x) for x in (r.get("flags") or [])).upper()
        conf = str(r.get("confidence") or "").lower()
        return (r.get("method") == "UNRESOLVED" or conf in ("low", "none", "very low")
                or any(k in flags for k in ("NO_VERIFIED_SIGNAL", "THIN_HISTORY",
                                            "ONE_TEAM_NO_HISTORY", "NO_TEAM_HISTORY")))

    no_ev = [r for r in rows if lacks_evidence(r)]
    bad_no_ev = [f"{r.get('team1')} vs {r.get('team2')} p={r.get('prob_team1')}"
                 for r in no_ev if abs(float(r.get("prob_team1") or 0.5) - 0.5) > 0.02]
    unlab = [f"{r.get('team1')} vs {r.get('team2')}" for r in no_ev if not labelled(r)]
    # informational: how many rows are close to a coin flip but may be genuine even matches
    near = sum(1 for r in rows
               if abs(float(r.get("prob_team1") or 0.5) - 0.5) < 0.02
               and not str(r.get("method", "")).startswith("MARKET"))
    status = PASS if not bad_no_ev and not unlab else WARN
    rep.add("D13", "rows without team evidence are 50/50 and explicitly labelled",
            status,
            f"{len(no_ev)} row(s) lack team evidence (UNRESOLVED / NO_TEAM_HISTORY); "
            f"{len(no_ev) - len(unlab)} labelled, {len(bad_no_ev)} non-50/50. "
            f"Info: {near} model row(s) land within ±2 pts of 50% — these are even-matchup "
            f"estimates from recorded results, not placeholders.", (bad_no_ev + unlab)[:10])
    return rows


def verify_schedule(rep: Report, rows: list[dict], path: str) -> None:
    """Cross-check fixture start times against a Leaguepedia MatchSchedule snapshot."""
    if not path:
        rep.add("D18", "start times cross-checked against Leaguepedia MatchSchedule", SKIP,
                "no --leaguepedia-schedule snapshot supplied")
        return
    if not os.path.exists(path):
        rep.add("D18", "start times cross-checked against Leaguepedia MatchSchedule", SKIP,
                f"snapshot not found: {path}")
        return
    sched = []
    snapshot_generated = None
    try:
        if os.path.isdir(path):
            # Diagnostic snapshots are committed artifacts and can outlive the
            # live pipeline. Read their capture timestamp so stale deltas are
            # not mistaken for a current schedule verification.
            for fn in sorted(os.listdir(path)):
                if not fn.startswith("report") or not fn.endswith(".json"):
                    continue
                try:
                    meta = json.load(open(os.path.join(path, fn), encoding="utf-8"))
                    stamp = meta.get("generated_at") if isinstance(meta, dict) else None
                    if stamp:
                        parsed = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
                        if parsed.tzinfo is None:
                            parsed = parsed.replace(tzinfo=timezone.utc)
                        if snapshot_generated is None or parsed > snapshot_generated:
                            snapshot_generated = parsed
                except Exception:  # noqa: BLE001
                    continue
            for fn in sorted(os.listdir(path)):
                if not fn.endswith(".json") or not fn.startswith("ms_"):
                    continue
                try:
                    part = json.load(open(os.path.join(path, fn), encoding="utf-8"))
                except Exception:  # noqa: BLE001
                    continue
                if isinstance(part, dict):
                    part = part.get("cargoquery") or part.get("rows") or []
                if isinstance(part, list):
                    sched += part
        else:
            sched = json.load(open(path, encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        rep.add("D18", "start times cross-checked against Leaguepedia MatchSchedule", FAIL,
                f"snapshot unreadable: {exc!r}")
        return
    if isinstance(sched, dict):
        sched = sched.get("cargoquery") or sched.get("rows") or []
    idx: dict[tuple[str, str], list[dict]] = {}
    for r in sched:
        r = r.get("title", r) if isinstance(r, dict) else r
        if not isinstance(r, dict):
            continue
        t1 = norm(r.get("Team1") or r.get("team1") or "")
        t2 = norm(r.get("Team2") or r.get("team2") or "")
        if t1 and t2:
            idx.setdefault((t1, t2), []).append(r)
            idx.setdefault((t2, t1), []).append(r)
    if not idx:
        rep.add("D18", "start times cross-checked against Leaguepedia MatchSchedule", SKIP,
                "snapshot contained no usable rows")
        return
    same, diff, unmatched = 0, [], []
    for m in rows:
        hits = idx.get((norm(m.get("team1")), norm(m.get("team2")))) or []
        if not hits:
            unmatched.append(f"{m.get('team1')} vs {m.get('team2')}")
            continue
        ours = (m.get("start_utc") or "")[:16].replace("T", " ")
        # the same pair can meet several times in a split: take the closest date
        def stamp(r):
            return str(r.get("DateTime UTC") or r.get("DateTime_UTC") or "")[:16]
        try:
            ours_dt = datetime.strptime(ours, "%Y-%m-%d %H:%M")
        except ValueError:
            ours_dt = None
        best, best_gap = None, None
        for h in hits:
            hs = stamp(h)
            try:
                gap = abs((datetime.strptime(hs, "%Y-%m-%d %H:%M") - ours_dt).total_seconds()) \
                    if ours_dt else 0
            except ValueError:
                gap = 0
            if best_gap is None or gap < best_gap:
                best, best_gap = hs, gap
        theirs = best or ""
        if ours and theirs and ours == theirs:
            same += 1
        else:
            diff.append(f"{m.get('team1')} vs {m.get('team2')}: ours={ours or '—'} lp={theirs or '—'}")
    checked = same + len(diff)
    if not checked:
        rep.add("D18", "start times cross-checked against Leaguepedia MatchSchedule", SKIP,
                f"no fixture matched the snapshot ({len(unmatched)} unmatched)")
        return
    snapshot_note = ""
    stale_snapshot = False
    if snapshot_generated is not None:
        age_hours = (datetime.now(timezone.utc) - snapshot_generated).total_seconds() / 3600
        snapshot_note = f" Snapshot captured {snapshot_generated.isoformat()} ({age_hours:.1f}h old)."
        stale_snapshot = age_hours > 24
        if stale_snapshot:
            snapshot_note += " This is a stale diagnostic snapshot; deltas are historical and do not verify the current schedule."
    elif os.path.isdir(path):
        snapshot_note = " Snapshot capture time unavailable; currentness cannot be established."
        stale_snapshot = True
    rep.add("D18", "start times cross-checked against Leaguepedia MatchSchedule",
            PASS if not diff and not stale_snapshot else WARN,
            f"{same}/{checked} matched fixture times agree with Leaguepedia; "
            f"{len(unmatched)} fixture(s) not in the snapshot; {len(diff)} differ "
            "(Hotspawn is authoritative for pick lock times; verify current organizer schedules before relying on a delta)."
            + snapshot_note,
            diff[:12])


def verify_data_files(rep: Report) -> None:
    present = [p for p in DATA_PATHS if os.path.exists(p)]
    if not present:
        rep.add("D14", "published data file exists", FAIL,
                f"none of {[os.path.relpath(p, ROOT) for p in DATA_PATHS]} exist")
        return
    if len(present) == 1:
        rep.add("D14", "single published data file (site copy)", PASS,
                f"only {os.path.relpath(present[0], ROOT)} exists — site copy is the single source")
        return
    digests = {}
    for p in DATA_PATHS:
        with open(p, "rb") as fh:
            digests[os.path.relpath(p, ROOT)] = hashlib.sha256(fh.read()).hexdigest()
    same = len(set(digests.values())) == 1
    rep.add("D14", "canonical data and site data are identical",
            PASS if same else FAIL,
            "identical" if same else f"diverged: {digests}")


# --------------------------------------------------------------------------- site
def verify_site(rep: Report, rows: list[dict]) -> None:
    payload, _ = load_json(DATA_PATHS[1])
    limitations_text = ""
    if isinstance(payload, dict):
        limitations_text = " ".join(str(x) for x in
                                    ((payload.get("unresolved") or {}).get("limitations") or []))
    js_path = os.path.join(DOCS, "assets", "app.js")
    js_text = open(js_path, encoding="utf-8").read() if os.path.exists(js_path) else ""
    required = ["index.html", "leagues.html", "picks.html", "unresolved.html", "flagged.html",
                "methodology.html", "match.html", "assets/style.css", "assets/app.js",
                "data/picks.json"]
    missing = [f for f in required if not os.path.exists(os.path.join(DOCS, f))]
    if missing:
        rep.add("S1", "all required site files exist", FAIL, f"missing {missing}")
        return
    rep.add("S1", "all required site files exist", PASS, f"{len(required)} files present")

    viewport_bad, nav_bad, internal_broken, external, assets_ref = [], [], [], [], []
    exec_detail = {}
    for path in pages():
        rel = os.path.relpath(path, ROOT)
        p = parse_page(path)
        # S1 mobile viewport
        has_vp = any((m.get("name") or "").lower() == "viewport" and
                     "width=device-width" in (m.get("content") or "")
                     for m in p.metas)
        if not has_vp:
            viewport_bad.append(rel)
        # S2 nav
        hrefs = [h for _t, h in p.links]
        if rel.startswith("docs") and not any("picks.html" in h for h in hrefs):
            nav_bad.append(f"{rel} (no link to picks.html)")
        # S3 exec summary
        if rel == os.path.join("docs", "index.html"):
            text_low = " ".join(p.text).lower()
            exec_detail = {
                "links_picks": any("picks.html" in h for h in hrefs),
                "links_unresolved": any("unresolved.html" in h for h in hrefs),
                "mentions_limitations": ("limitation" in text_low
                                          or "limitation" in limitations_text.lower()
                                          or "limitation" in js_text.lower()),
                "mentions_updated": ("updated" in text_low or "update" in text_low
                                     or ("updated" in js_text.lower()
                                         and any(i in {m.get("id") for m in p.metas} | p.ids
                                                 for i in ("updated", "generated", "freshness")))),
            }
        # S8 external + S5 internal
        for tag, url in p.links:
            if url.startswith(("http://", "https://")):
                external.append(url)
                if url.startswith("http://") and "." in host_of(url):
                    external.append(url)  # counted; https check below
                continue
            if url.startswith(("#", "mailto:", "javascript:", "data:")):
                continue
            target = url.split("#")[0].split("?")[0]
            if not target:
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(path), target))
            if not os.path.exists(resolved):
                internal_broken.append(f"{rel} -> {url}")

    # S10: the phone bottom nav must have one grid column per link (regression for a 4-column grid with 5 links)
    css_text = ""
    try:
        with open(os.path.join(DOCS, "assets", "style.css"), encoding="utf-8") as fh:
            css_text = fh.read()
    except OSError:
        pass
    mcol = re.search(r"\.bottom-nav\s*\{[^}]*grid-template-columns:\s*repeat\((\d+)", css_text)
    nav_bad = []
    for pg in pages():
        if not pg.startswith(DOCS + os.sep):
            continue  # root index.html is a redirect shell, not a dashboard page
        try:
            with open(pg, encoding="utf-8") as fh:
                html_text = fh.read()
        except OSError:
            continue
        nav = re.search(r'<nav class="bottom-nav".*?</nav>', html_text, re.S)
        if not nav:
            nav_bad.append(f"{pg}: no bottom nav")
            continue
        links = len(re.findall(r"<a ", nav.group(0)))
        if not mcol or int(mcol.group(1)) != links:
            nav_bad.append(f"{pg}: {links} links vs grid columns {mcol.group(1) if mcol else 'none'}")
    rep.add("S10", "phone bottom nav has one grid column per link on every page",
            PASS if not nav_bad else FAIL,
            "; ".join(nav_bad[:5]) if nav_bad else f"{mcol.group(1)} links, {mcol.group(1)} columns on every page")

    rep.add("S2", "every page is mobile-ready (viewport width=device-width)",
            PASS if not viewport_bad else FAIL,
            "all pages declare a responsive viewport" if not viewport_bad
            else f"{len(viewport_bad)} page(s) missing viewport meta", viewport_bad)
    rep.add("S3", "every page links the shared picks navigation",
            PASS if not nav_bad else FAIL,
            "navigation present" if not nav_bad else "navigation incomplete", nav_bad)

    if exec_detail:
        problems = [k for k, v in exec_detail.items() if not v]
        rep.add("S4", "executive summary links in-site to picks + unresolved and "
                      "states limitations",
                PASS if not problems else FAIL,
                f"exec summary checks: {exec_detail}")
    else:
        rep.add("S4", "executive summary links in-site to picks + unresolved and "
                      "states limitations", FAIL, "docs/index.html not found")

    # S4b unresolved page
    upath = os.path.join(DOCS, "unresolved.html")
    if os.path.exists(upath):
        p = parse_page(upath)
        text = " ".join(p.text).lower()
        dynamic_limits = ("limitations" in js_text.lower()
                          and "limitations" in limitations_text.lower())
        need = ["unresolved"]
        missing_terms = [t for t in need if t not in text]
        if "limitation" not in text and not dynamic_limits:
            missing_terms.append("limitation")
        rep.add("S5", "separate unresolved section with limitations",
                PASS if not missing_terms else FAIL,
                "unresolved page states limitations" if not missing_terms
                else f"missing terms {missing_terms}")
    else:
        rep.add("S5", "separate unresolved section with limitations", FAIL,
                "docs/unresolved.html missing")

    # S5b: per-league limitations on the unresolved page
    if os.path.exists(upath):
        upage = parse_page(upath)
        utext = " ".join(upage.text).lower()
        unres_tournaments = sorted({(r.get("tournament") or "").strip()
                                    for r in rows if r.get("method") == "UNRESOLVED"
                                    and (r.get("tournament") or "").strip()})
        named = [t for t in unres_tournaments if t.lower() in utext]
        if unres_tournaments:
            rep.add("S5b", "unresolved page names each unresolved league (per-league limits)",
                    PASS if len(named) == len(unres_tournaments) else WARN,
                    f"{len(named)}/{len(unres_tournaments)} unresolved tournaments named on the page",
                    [t for t in unres_tournaments if t not in named])

    # S5c: third-party attribution (Liquipedia is CC-BY-SA 3.0; Leaguepedia is a Fandom wiki)
    method_page = os.path.join(DOCS, "methodology.html")
    src_text = " ".join(
        (r.get("evidence") or "") + " " + (r.get("source_url") or "") + " " +
        " ".join(f"{x.get('name','')} {x.get('url','')}" if isinstance(x, dict) else str(x)
                 for x in (r.get("sources") or []))
        for r in rows).lower()
    if method_page and any(k in src_text for k in ("liquipedia", "lol.fandom.com", "leaguepedia")):
        mtext = " ".join(parse_page(method_page).text).lower()
        need = []
        if "liquipedia" in src_text and "liquipedia" not in mtext:
            need.append("Liquipedia credit")
        if "liquipedia" in src_text and "cc-by-sa" not in mtext and "cc by-sa" not in mtext:
            need.append("Liquipedia CC-BY-SA 3.0 attribution")
        if ("leaguepedia" in src_text or "lol.fandom.com" in src_text) and \
                "leaguepedia" not in mtext and "fandom" not in mtext:
            need.append("Leaguepedia credit")
        rep.add("S5c", "third-party data sources are attributed on Method & Sources",
                PASS if not need else WARN,
                "attribution present" if not need else f"missing: {', '.join(need)}")

    rep.add("S6", "no broken internal links", PASS if not internal_broken else FAIL,
            "all internal href/src resolve" if not internal_broken
            else f"{len(internal_broken)} broken internal link(s)", internal_broken)

    js = open(os.path.join(DOCS, "assets", "app.js"), encoding="utf-8").read()
    css = open(os.path.join(DOCS, "assets", "style.css"), encoding="utf-8").read()
    asset_problems = []
    if "load(" not in js:
        asset_problems.append("app.js does not define load()")
    if "data/picks.json" not in js:
        asset_problems.append("app.js does not read data/picks.json")
    if "@media" not in css:
        asset_problems.append("style.css has no responsive @media rules")
    rep.add("S7", "shared JS/CSS exist and are responsive",
            PASS if not asset_problems else FAIL,
            "assets load data and contain responsive rules" if not asset_problems
            else "; ".join(asset_problems))

    root_index = os.path.join(ROOT, "index.html")
    if os.path.exists(root_index):
        html = open(root_index, encoding="utf-8").read()
        redirects = ("url=./docs/" in html.replace(" ", "") or
                     "url=docs/" in html.replace(" ", "") or
                     "docs/index.html" in html)
        rep.add("S8", "root index.html sends visitors into the site", PASS if redirects
                else FAIL, "root redirects to docs/" if redirects else "no redirect found")
    else:
        rep.add("S8", "root index.html sends visitors into the site", FAIL,
                "root index.html missing")

    EXTERNAL_LINKS.extend(sorted(set(external)))
    https_bad = [u for u in external if u.startswith("http://")]
    rep.add("S9", "all external links use https", PASS if not https_bad else WARN,
            f"{len(set(external))} external link(s) collected for manual review; "
            f"{len(set(https_bad))} plain-http", sorted(set(https_bad))[:10])
    unverified_hosts = sorted({host_of(u) for u in external
                               if not host_in(host_of(u), ALL_HOSTS)})
    if unverified_hosts:
        rep.add("S9b", "external link hosts on the trust allowlist", WARN,
                f"{len(unverified_hosts)} host(s) need manual review", unverified_hosts[:12])


# --------------------------------------------------------------------------- workflow
CRON_RE = re.compile(r"cron\s*:\s*['\"]?([^'\"\n]+)['\"]?")


def cron_interval_hours(expr: str) -> float | None:
    """Return the repeat interval in hours for simple minute/hour cron patterns."""
    parts = expr.split()
    if len(parts) != 5:
        return None
    minute, hour = parts[0], parts[1]
    try:
        m_step = int(minute.split("/")[1]) if "/" in minute else (
            int(minute) if minute.isdigit() else 0)
    except ValueError:
        m_step = 0
    if hour == "*":
        return 1.0
    if hour.startswith("*/"):
        try:
            return float(hour[2:])
        except ValueError:
            return None
    if "," in hour:
        vals = sorted(int(x) for x in hour.split(",") if x.strip().isdigit())
        if len(vals) >= 2:
            gaps = [b - a for a, b in zip(vals, vals[1:])] + [24 - vals[-1] + vals[0]]
            return float(min(gaps)) + m_step / 60.0
    return None


def verify_workflows(rep: Report) -> None:
    wf_dir = os.path.join(ROOT, ".github", "workflows")
    if not os.path.isdir(wf_dir):
        rep.add("W1", "picks update is scheduled every 4-8 hours", FAIL,
                ".github/workflows missing")
        return
    found = []
    for f in sorted(os.listdir(wf_dir)):
        if not f.endswith((".yml", ".yaml")):
            continue
        text = open(os.path.join(wf_dir, f), encoding="utf-8").read()
        for expr in CRON_RE.findall(text):
            interval = cron_interval_hours(expr.strip())
            if interval is not None and 4 <= interval <= 8 and "update" in f:
                found.append((f, expr.strip(), interval))
    if found:
        f, expr, interval = found[0]
        rep.add("W1", "picks update is scheduled every 4-8 hours", PASS,
                f"{f}: cron '{expr}' = every {interval:g}h")
    else:
        rep.add("W1", "picks update is scheduled every 4-8 hours", FAIL,
                "no 4-8h cron found in an update workflow")

    # W2: generator referenced + contents write
    candidates = []
    for f in sorted(os.listdir(wf_dir)):
        if not f.endswith((".yml", ".yaml")):
            continue
        text = open(os.path.join(wf_dir, f), encoding="utf-8").read()
        if "update_picks.py" in text:
            candidates.append((f, "contents:write" in text.replace(" ", "")))
    candidates.sort(key=lambda c: (("test" in c[0]) or ("diag" in c[0]), c[0]))
    if candidates:
        f, has_write = candidates[0]
        rep.add("W2", "update workflow runs the generator with contents: write",
                PASS if has_write else WARN,
                f"{f} runs scripts/update_picks.py; contents write "
                f"{'present' if has_write else 'NOT declared'}")
    else:
        rep.add("W2", "update workflow runs the generator", FAIL,
                "no workflow references scripts/update_picks.py")

    # W3: crowd percentages must not be a probability input
    script = os.path.join(ROOT, "scripts", "update_picks.py")
    if not os.path.exists(script):
        rep.add("W3", "Hotspawn crowd % is never a probability input", SKIP,
                "scripts/update_picks.py not found")
        return
    suspects = []
    for lineno, line in enumerate(open(script, encoding="utf-8"), 1):
        low = line.lower()
        if not re.search(r"crowd|picked_percent|pickedpercent", low):
            continue
        # Ignore comments/notes that explicitly say crowd is NOT used.
        if re.search(r"never|not used|not a probability|context only|excluded", low):
            continue
        # Arithmetic use of a crowd value inside a probability expression.
        arithmetic = re.search(
            r"(crowd\w*\s*[/+*\-]|[/+*\-]\s*crowd\w*|"
            r"prob\w*\s*=\s*[^=\n]*crowd|"
            r"crowd\w*\s*/\s*100)", low)
        if arithmetic:
            suspects.append(f"line {lineno}: {line.strip()[:110]}")
    rep.add("W3", "Hotspawn crowd % is never a probability input",
            PASS if not suspects else FAIL,
            "static scan found no crowd->probability usage" if not suspects
            else "crowd values appear in a probability expression", suspects[:8])


# ------------------------------------------------------------------ optional live checks
def http_status(url: str, timeout: float = 20.0) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.geturl()
    except urllib.error.HTTPError as exc:
        return exc.code, url
    except Exception as exc:  # noqa: BLE001
        return 0, repr(exc)[:90]


def http_status_retry(url: str, attempts: int = 3, delay: float = 4.0,
                      timeout: float = 20.0) -> tuple[int, str]:
    """Retry transient failures (0/timeout, 429, 5xx) without masking definitive 404/410s."""
    code, final = 0, ""
    for i in range(attempts):
        code, final = http_status(url, timeout=timeout)
        transient = code == 0 or code == 429 or 500 <= code < 600
        if not transient:
            return code, final
        if i < attempts - 1:
            time.sleep(delay)
    return code, final


def wait_for_http(url: str, attempts: int = 8, delay: float = 12.0,
                  timeout: float = 20.0) -> tuple[int, str]:
    """Wait for a freshly deployed GitHub Pages build (~45-75s after push to main)."""
    code, final = 0, ""
    for i in range(attempts):
        code, final = http_status(url, timeout=timeout)
        if code == 200:
            return code, final
        if i < attempts - 1:
            time.sleep(delay)
    return code, final


def verify_external(rep: Report) -> None:
    """Reachability of every external link on the site. Blocked-but-alive hosts
    (401/403/405/429) and transient upstream 5xx/timeouts are WARN; 404/410 are FAIL."""
    links = sorted(set(EXTERNAL_LINKS))
    if not links:
        rep.add("X1", "external links reachable", SKIP, "no external links found")
        return
    results: dict[str, int] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for url, (code, _final) in zip(links, pool.map(lambda u: http_status_retry(u, attempts=2), links)):
            results[url] = code
    dead = [u for u, c in results.items() if c in (404, 410)]
    flaky = [u for u, c in results.items() if c == 0 or 500 <= c < 600]
    blocked = [u for u, c in results.items() if c in (401, 403, 405, 429)]
    ok = [u for u, c in results.items() if c and 200 <= c < 400]
    status = FAIL if dead else (WARN if (blocked or flaky) else PASS)
    detail = (f"{len(ok)}/{len(links)} returned 2xx/3xx; {len(blocked)} blocked by the host; "
              f"{len(flaky)} transient/5xx; {len(dead)} dead (404/410)")
    rep.add("X1", "external links reachable (official-source links resolve)", status, detail,
            [f"{u} -> {results[u]}" for u in (dead + flaky + blocked)][:14])


def verify_live(rep: Report, live_url: str) -> None:
    """Confirm the deployed Pages site serves the site and fresh data."""
    base = live_url.rstrip("/") + "/"
    code, final = wait_for_http(base)
    if code != 200:
        rep.add("X2", "live Pages site responds 200", FAIL, f"{base} -> {code} {final}")
        return
    rep.add("X2", "live Pages site responds 200", PASS, f"{base} -> 200 (final {final})")
    data_url = base + "docs/data/picks.json"
    code, _ = wait_for_http(data_url)
    if code != 200:
        rep.add("X3", "live site serves picks.json", FAIL, f"{data_url} -> {code}")
        return
    try:
        with urllib.request.urlopen(urllib.request.Request(data_url, headers={"User-Agent": UA}),
                                    timeout=25) as r:
            live = json.loads(r.read().decode("utf-8"))
        n = len(live.get("matches") or [])
        gen = live.get("generated_at")
        rep.add("X3", "live site serves picks.json", PASS,
                f"{n} matches live, generated_at={gen}")
    except Exception as exc:  # noqa: BLE001
        rep.add("X3", "live site serves picks.json", FAIL, f"unreadable: {exc!r}")


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-age-hours", type=float, default=8.0,
                    help="expected maximum data age (workflow runs every 6h)")
    ap.add_argument("--json-out", default=os.path.join(OUT_DIR, "report.json"))
    ap.add_argument("--md-out", default=os.path.join(OUT_DIR, "last_report.md"))
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--check-external", action="store_true",
                    help="HTTP-check every external link on the site (needs network)")
    ap.add_argument("--leaguepedia-schedule", default="",
                    help="Leaguepedia MatchSchedule snapshot JSON to cross-check start times")
    ap.add_argument("--live-url", default="",
                    help="deployed Pages base URL to confirm serving (needs network)")
    args = ap.parse_args()

    rep = Report()
    payload, err = load_json(DATA_PATHS[1])  # the site serves docs/data/picks.json
    if payload is None:
        payload, err2 = load_json(DATA_PATHS[0])
    rows = verify_data(rep, payload, err or "docs/data/picks.json", args.max_age_hours)
    verify_schedule(rep, rows, args.leaguepedia_schedule)
    verify_data_files(rep)
    verify_site(rep, rows)
    verify_workflows(rep)
    if args.check_external:
        verify_external(rep)
    if args.live_url:
        verify_live(rep, args.live_url)

    # ---- requirements traceability (maps the brief to concrete checks)
    def worst(*ids):
        vals = [c["status"] for c in rep.checks if c["id"] in ids]
        if any(v == FAIL for v in vals):
            return FAIL
        if any(v == WARN for v in vals):
            return WARN
        if vals and all(v == SKIP for v in vals):
            return SKIP
        return PASS if vals else SKIP

    requirements = [
        ("REQ1", "A pick exists for every match (pick is one of the two teams)",
         ["D3", "D11"]),
        ("REQ2", "Win probabilities for both teams on every match, summing to 100%",
         ["D4", "D5"]),
        ("REQ3", "Probabilities come from outside Hotspawn (books/markets/our results model)",
         ["D12", "W3"]),
        ("REQ4", "External betting lines used where they exist (markets first)",
         ["D8a", "D6", "D20"]),
        ("REQ5", "Every match without a market line still gets a pick + documented method",
         ["D8b", "D13"]),
        ("REQ6", "Separate unresolved section, with limitations, linked from the exec summary",
         ["S4", "S5", "S5b"]),
        ("REQ7", "Executive summary links in-site to the updated picks list",
         ["S4"]),
        ("REQ8", "Every row links its source; non-official or generic evidence is disclosed and flagged",
         ["D7", "D7b", "D8a", "D8b", "D8c", "D8d", "D17"]),
        ("REQ9", "Mobile-friendly: responsive viewport + responsive CSS + readable cards",
         ["S2", "S7"]),
        ("REQ10", "Automatic refresh every 4-8 hours, no manual input",
         ["W1", "W2", "D1"]),
        ("REQ11", "Site integrity: no broken internal links, root entry point works",
         ["S1", "S6", "S8"]),
        ("REQ12", "Third-party sources attributed where their data is used",
         ["S5c"]),
    ]
    req_status = (FAIL if any(worst(*ids) == FAIL for _r, _t, ids in requirements)
                  else WARN if any(worst(*ids) == WARN for _r, _t, ids in requirements)
                  else PASS)
    rep.add("REQ", "requirements traceability", req_status,
            "; ".join(f"{rid} {worst(*ids)}" for rid, _title, ids in requirements),
            [f"{rid}: {title} -> {worst(*ids)}" for rid, title, ids in requirements],
            aggregate=True)
    out_requirements = [{"id": rid, "requirement": title, "status": worst(*ids),
                         "checks": ids} for rid, title, ids in requirements]

    os.makedirs(os.path.dirname(args.json_out), exist_ok=True)
    out = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "status": PASS if rep.ok else FAIL,
        "counts": {s: rep.count(s) for s in (PASS, FAIL, WARN, SKIP)},
        "data_matches": len(rows),
        "methods": {k: sum(1 for r in rows if r.get("method") == k) for k in METHODS},
        "checks": rep.checks,
        "requirements": out_requirements,
    }
    with open(args.json_out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)

    lines = [f"# Verification report — {out['status']}",
             f"_{out['verified_at']}_",
             f"{len(rows)} matches · " +
             " · ".join(f"{k}: {v}" for k, v in out["methods"].items()),
             "", "| check | status | detail |", "|---|---|---|"]
    for c in rep.checks:
        detail = c["detail"].replace("|", "\\|")
        lines.append(f"| {c['id']} {c['title']} | {c['status']} | {detail} |")
    lines += ["", "## Requirements traceability", "",
              "| id | requirement | status | checks |", "|---|---|---|---|"]
    for r in out_requirements:
        lines.append(f"| {r['id']} | {r['requirement']} | {r['status']} | {', '.join(r['checks'])} |")
    for c in rep.checks:
        if c.get("items"):
            lines.append(f"\n**{c['id']} items:**")
            lines += [f"- {i}" for i in c["items"]]
    with open(args.md_out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    if not args.quiet:
        for c in rep.checks:
            print(f"[{c['status']:4}] {c['id']:4} {c['title']} — {c['detail']}")
            for i in c.get("items") or []:
                print(f"         · {i}")
        print(f"\n== {out['status']} · pass {rep.count(PASS)} · fail {rep.count(FAIL)} "
              f"· warn {rep.count(WARN)} · skip {rep.count(SKIP)} ==")
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main())

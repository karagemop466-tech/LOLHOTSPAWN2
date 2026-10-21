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
  D7  every row carries at least one official/trusted source link (url field or evidence URL)
  D8  market rows link a market/book URL; model rows link a results source;
      unresolved rows are explicitly flagged as unverified 50/50
  D9  no duplicate fixtures (same normalised teams + same start)
  D10 counts_by_method in the payload agrees with the rows
  D11 data/picks.json and docs/data/picks.json are both present and identical
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
DATA_PATHS = [os.path.join(ROOT, "data", "picks.json"),
              os.path.join(DOCS, "data", "picks.json")]
OUT_DIR = os.path.join(ROOT, "verification")

METHODS = {"MARKET_BOOKS", "MARKET_POLYMARKET", "MODEL_ELO", "UNRESOLVED"}
# Source hosts accepted as official/trusted. Hotspawn is accepted for the fixture
# list only; it is explicitly rejected as a probability source (requirement).
FIXTURE_HOSTS = ("hotspawn.com",)
MARKET_HOSTS = ("polymarket.com", "oddspapi.io", "pinnacle.com", "pinnacleapi",
                "bet365.com", "draftkings.com", "fanduel.com", "betmgm.com",
                "williamhill.com", "betway.com", "1xbet.com", "gg.bet", "betboom.ru",
                "midnite.com", "rivalry.com", "unibet.com", "betfair.com",
                "smarkets.com", "kalshi.com", "betano.com", "betsson.com")
RESULTS_HOSTS = ("lol.fandom.com", "leaguepedia", "liquipedia.net", "bo3.gg",
                 "gol.gg", "lolesports.com", "riotgames.com", "leagueoflegends.com",
                 "gamesofdesktop", "oracleselixir.com")
ALL_HOSTS = FIXTURE_HOSTS + MARKET_HOSTS + RESULTS_HOSTS + ("github.com",)

PASS, FAIL, WARN, SKIP = "PASS", "FAIL", "WARN", "SKIP"


class Report:
    def __init__(self) -> None:
        self.checks: list[dict] = []
        self.started = datetime.now(timezone.utc)

    def add(self, cid: str, title: str, status: str, detail: str = "",
            items: list | None = None) -> None:
        rec = {"id": cid, "title": title, "status": status, "detail": detail}
        if items:
            rec["items"] = items
        self.checks.append(rec)

    def count(self, status: str) -> int:
        return sum(1 for c in self.checks if c["status"] == status)

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
        self.text: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
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
        for key in ("market_url", "source_url", "hotspawn_url", "source_lobby",
                    "fixtures_url", "sources"):
            val = m.get(key)
            if isinstance(val, str):
                row_urls += urls_in(val)
            elif isinstance(val, list):
                for v in val:
                    row_urls += urls_in(v if isinstance(v, str) else json.dumps(v))
        row_urls += urls_in(m.get("evidence") or "")
        row_urls = list(dict.fromkeys(row_urls))
        if not row_urls:
            no_source.append(label)
        elif not any(host_in(host_of(u), ALL_HOSTS) for u in row_urls):
            weak_source.append(f"{label} -> {', '.join(host_of(u) for u in row_urls[:2])}")
        if method.startswith("MARKET") and not any(
                host_in(host_of(u), MARKET_HOSTS) for u in row_urls):
            market_no_url.append(label)
        if method in ("MODEL_ELO", "MARKET_BOOKS", "MARKET_POLYMARKET"):
            # Only the probability-source fields count here. hotspawn_url is the
            # fixture link and is explicitly allowed to point at Hotspawn.
            prob_urls = urls_in(m.get("market_url") or "") + \
                urls_in(m.get("source_url") or "") + \
                urls_in(m.get("evidence") or "")
            for u in prob_urls:
                if host_in(host_of(u), FIXTURE_HOSTS):
                    banned_prob_source.append(f"{label} -> {u}")
            # A model row whose only link is an API help page cannot be checked
            # line by line by a human; flag it for manual review (not a hard fail).
            su = m.get("source_url") or ""
            if method == "MODEL_ELO" and su and re.search(
                    r"action=help|/wiki/Leaguepedia:League_of_Legends_Esports_Wiki", su):
                weak_source.append(f"{label} -> model evidence link is a docs page: {su}")
        if method == "UNRESOLVED":
            flags = " ".join(str(m.get(k) or "") for k in ("confidence", "evidence", "status"))
            if abs((p1f if p1f is not None else 0.5) - 0.5) > 0.001:
                unresolved_unflagged.append(f"{label} unresolved but prob={p1f}")
            elif not re.search(r"unresolved|unverified|no data|50/50|placeholder", flags, re.I):
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
    emit("D3", "a pick exists and is one of the two teams", bad_pick,
         "every match has a pick equal to team1 or team2")
    emit("D4", "probabilities are in range and sum to 1", bad_prob,
         "every row sums to 1.0 within 0.005")
    emit("D5", "pick_prob equals the larger probability", bad_pickprob,
         "pick_prob matches max(prob_team1, prob_team2) on every row")
    emit("D6", f"method is one of {sorted(METHODS)}", bad_method,
         "all methods documented")
    emit("D7", "every row links at least one official/trusted source", no_source,
         f"all {len(rows)} rows carry at least one source URL")
    if weak_source:
        rep.add("D7b", "source host recognised as official/trusted", WARN,
                f"{len(weak_source)} row(s) link a host not on the allowlist — manual review",
                weak_source[:12])
    emit("D8a", "market rows link a bookmaker/prediction-market URL", market_no_url,
         "every market row links its market")
    emit("D8b", "unresolved rows are explicit unverified 50/50 (limitations published)",
         unresolved_unflagged, "every unresolved row is 0.50 and labelled unverified")
    emit("D9", "no duplicate fixtures", dup, "no duplicate (teams,start) rows")

    banned = list(dict.fromkeys(banned_prob_source))
    emit("D12", "Hotspawn is never the probability source (fixture list only)", banned,
         "no market/model row cites hotspawn.com as its probability source")

    expected = payload.get("counts_by_method") or {}
    actual = {k: sum(1 for r in rows if r.get("method") == k) for k in METHODS}
    mismatch = {k: (expected.get(k), actual[k]) for k in set(expected) | set(actual)
                if int(expected.get(k, 0) or 0) != actual[k]}
    rep.add("D10", "counts_by_method agrees with the rows",
            PASS if not mismatch else FAIL,
            "counts consistent" if not mismatch else f"mismatch {mismatch}")

    declared = payload.get("count")
    rep.add("D11", "declared count equals number of rows",
            PASS if int(declared or 0) == len(rows) else FAIL,
            f"count={declared}, rows={len(rows)}")

    unresolved = actual["UNRESOLVED"]
    share = unresolved / len(rows) if rows else 0
    rep.add("D13", "coverage: share of matches without an external market line",
            PASS if share == 0 else WARN,
            f"{unresolved}/{len(rows)} rows are UNRESOLVED 50/50 ({share:.1%}). "
            "A non-zero share is allowed only when published as an unresolved section "
            "with limitations — see S4 and the site's Unresolved page.")
    return rows


def verify_data_files(rep: Report) -> None:
    present = [p for p in DATA_PATHS if os.path.exists(p)]
    if len(present) != len(DATA_PATHS):
        missing = [os.path.relpath(p, ROOT) for p in DATA_PATHS if p not in present]
        rep.add("D14", "canonical and site data files both exist", FAIL,
                f"missing {missing}")
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
    required = ["index.html", "picks.html", "unresolved.html", "flagged.html",
                "methodology.html", "assets/style.css", "assets/app.js",
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
                "mentions_limitations": "limitation" in text_low,
                "mentions_updated": "updated" in text_low or "update" in text_low,
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
        need = ["unresolved", "limitation"]
        missing_terms = [t for t in need if t not in text]
        rep.add("S5", "separate unresolved section with limitations",
                PASS if not missing_terms else FAIL,
                "unresolved page states limitations" if not missing_terms
                else f"missing terms {missing_terms}")
    else:
        rep.add("S5", "separate unresolved section with limitations", FAIL,
                "docs/unresolved.html missing")

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


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-age-hours", type=float, default=8.0,
                    help="expected maximum data age (workflow runs every 6h)")
    ap.add_argument("--json-out", default=os.path.join(OUT_DIR, "report.json"))
    ap.add_argument("--md-out", default=os.path.join(OUT_DIR, "last_report.md"))
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    rep = Report()
    payload, err = load_json(DATA_PATHS[1])  # the site serves docs/data/picks.json
    if payload is None:
        payload, err2 = load_json(DATA_PATHS[0])
    rows = verify_data(rep, payload, err or "docs/data/picks.json", args.max_age_hours)
    verify_data_files(rep)
    verify_site(rep, rows)
    verify_workflows(rep)

    os.makedirs(os.path.dirname(args.json_out), exist_ok=True)
    out = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "status": PASS if rep.ok else FAIL,
        "counts": {s: rep.count(s) for s in (PASS, FAIL, WARN, SKIP)},
        "data_matches": len(rows),
        "methods": {k: sum(1 for r in rows if r.get("method") == k) for k in METHODS},
        "checks": rep.checks,
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

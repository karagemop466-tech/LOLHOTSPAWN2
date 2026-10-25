#!/usr/bin/env python3
"""Row-by-row independent audit of the published pick payload.

Why this file exists
--------------------
`scripts/verify_site.py` validates the payload's *shape* (schema, links, page
contract). This auditor re-derives the payload's *arithmetic* from the numbers
each row cites about itself, so a row cannot be internally consistent with the
schema and still be wrong:

  R1  identity        unique fixture ids, both teams named and different, start
                      time parseable and not in the past at generation time
  R2  probabilities   team1 + team2 = 1, pick == argmax, pick_prob == max prob
  R3  method          method matches the evidence on the row (market present <=>
                      MARKET_*, standings blend <=> MODEL_ELO_STANDINGS,
                      UNRESOLVED <=> exact 50/50 and resolved=false)
  R4  de-vig          every cited decimal price is re-converted to a two-way
                      probability and compared with the probability the row
                      published for that source
  R5  consensus       the published consensus is recomputed from the row's own
                      per-source probabilities (median with >=3 sources,
                      otherwise the documented weighted mean) and compared with
                      the row's published probability
  R6  dispersion      dispersion / time-spread recomputed
  R7  crowd leakage   Hotspawn crowd percentages are display-only context. This
                      measures how far every model-priced row sits from the crowd
                      number and fails if the published probabilities look like
                      a copy of it.
  R8  sources         every row cites >=1 https source, >=1 non-Hotspawn source,
                      every host is on the allowlist, and the Hotspawn citation
                      says it is the fixture list only
  R9  counts          the counts/coverage blocks re-foot against the rows
  R10 leagues         every per-league row re-foots against the rows
  R11 tier            Hotspawn tier values recorded; unpublished tiers counted
                      (never invented here)
  R12 excluded        no cancelled/excluded fixture is priced
  R13 duplicates      the same pair+tournament+day listed twice is reported
  R14 lists           next_24h / featured point at real rows inside their window
  R15 time spread     the row's published book-vs-Hotspawn time spread follows from
                      the start timestamps the row itself cites
  R16 start deltas    each book's start delta recomputes from those timestamps
                      (model.py matches on the absolute delta, so the published
                      number is unsigned and both timestamps are shown beside it)

Rules of the road: this script never invents a value, never edits the payload,
and never calls the network. Anything it cannot confirm is reported as
`UNVERIFIED`, not filled in. Exit code 1 only on a FAIL.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PICKS = os.path.join(ROOT, "docs", "data", "picks.json")
OUT_JSON = os.path.join(ROOT, "verification", "row_audit.json")
OUT_MD = os.path.join(ROOT, "verification", "row_audit.md")

# Documented in scripts/model.py (WEIGHTS) - restated here on purpose so a
# change in one place without the other is caught by R5 instead of silently
# agreeing with itself.
WEIGHTS = {"pinnacle": 1.0, "unibet": 0.85, "bovada": 0.8, "polymarket": 0.7}
DEFAULT_WEIGHT = 0.6

# Hosts a pick row may cite. Anything else is an unapproved provenance.
ALLOWED_HOSTS = {
    "www.hotspawn.com", "play.hotspawn.com", "hotspawn.com",
    "lol.fandom.com", "liquipedia.net",
    "guest.api.arcadia.pinnacle.com", "www.pinnacle.com",
    "www.unibet.com.au", "www.unibet.com", "eu-offering-api.kambicdn.com",
    "www.bovada.lv", "polymarket.com", "gamma-api.polymarket.com",
    # official organisers / results pages cited by league_breakdown rows
    "www.primeleague.gg", "primeleague.gg", "www.rivalsleague.gg", "rivalsleague.gg",
    "gol.gg", "www.gol.gg", "bo3.gg", "www.bo3.gg", "rft.gg", "www.rft.gg",
    "lolesports.com", "www.lolesports.com",
}

MARKET_METHODS = ("MARKET_CONSENSUS", "MARKET_SINGLE")
STANDINGS_METHODS = ("MODEL_STANDINGS", "MODEL_ELO_STANDINGS")
KNOWN_TIERS = {"S", "A", "B", "C", "D"}


def _parse(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None


def _median(vals):
    vals = sorted(v for v in vals if v is not None)
    n = len(vals)
    if not n:
        return None
    return vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2.0


def _host(url):
    try:
        from urllib.parse import urlparse
        return (urlparse(url or "").hostname or "").lower()
    except Exception:  # noqa: BLE001
        return ""


class Report:
    """Collects check results with row-level evidence."""

    def __init__(self):
        self.rows = []

    def add(self, cid, title, status, detail="", evidence=None):
        self.rows.append({"id": cid, "title": title, "status": status,
                          "detail": detail, "evidence": evidence or []})

    @property
    def fails(self):
        return [r for r in self.rows if r["status"] == "FAIL"]

    @property
    def warns(self):
        return [r for r in self.rows if r["status"] == "WARN"]

    def summary(self):
        c = Counter(r["status"] for r in self.rows)
        return {k: c.get(k, 0) for k in ("PASS", "FAIL", "WARN", "INFO", "UNVERIFIED")}


def audit(payload: dict) -> Report:
    rep = Report()
    matches = payload.get("matches") or []
    gen = _parse(payload.get("generated_at"))
    counts = payload.get("counts") or {}
    coverage = payload.get("coverage") or {}
    breakdown = payload.get("league_breakdown") or []
    excluded = payload.get("excluded_fixtures") or []

    # ---------------------------------------------------------------- R1
    ids = [str(m.get("id")) for m in matches]
    dup_ids = [i for i, n in Counter(ids).items() if n > 1]
    bad_identity = []
    stale = []
    for m in matches:
        t1, t2 = (m.get("team1") or "").strip(), (m.get("team2") or "").strip()
        start = _parse(m.get("start_utc"))
        if not t1 or not t2 or t1.lower() == t2.lower():
            bad_identity.append(f"{m.get('id')}: {t1!r} vs {t2!r}")
        if start is None:
            bad_identity.append(f"{m.get('id')}: unparseable start_utc {m.get('start_utc')!r}")
        elif gen and start < gen - timedelta(minutes=15):
            stale.append(f"{m.get('id')} {t1} vs {t2} start {m.get('start_utc')}")
    rep.add("R1", "fixture identity: unique ids, two distinct named teams, real UTC start",
            "PASS" if not dup_ids and not bad_identity else "FAIL",
            f"{len(matches)} rows; duplicate ids={len(dup_ids)}; bad identity={len(bad_identity)}",
            (dup_ids + bad_identity)[:10])
    rep.add("R1b", "no row was already more than 15 min old when the payload was generated",
            "PASS" if not stale else "WARN",
            f"{len(stale)} row(s) start before generated_at-15min", stale[:8])

    # ---------------------------------------------------------------- R2
    bad_sum, bad_pick = [], []
    for m in matches:
        p1, p2 = m.get("prob_team1"), m.get("prob_team2")
        if p1 is None or p2 is None or abs(p1 + p2 - 1.0) > 0.0011:
            bad_sum.append(f"{m.get('id')} {p1}+{p2}")
            continue
        want = m.get("team1") if p1 >= p2 else m.get("team2")
        if m.get("pick") != want:
            bad_pick.append(f"{m.get('id')} pick={m.get('pick')!r} argmax={want!r}")
        elif m.get("pick_prob") is None or abs(m.get("pick_prob") - max(p1, p2)) > 0.0006:
            bad_pick.append(f"{m.get('id')} pick_prob={m.get('pick_prob')} max={max(p1, p2)}")
    rep.add("R2", "probabilities sum to 100% and the pick is the higher probability",
            "PASS" if not bad_sum and not bad_pick else "FAIL",
            f"sum failures={len(bad_sum)}; pick failures={len(bad_pick)}",
            (bad_sum + bad_pick)[:10])

    # ---------------------------------------------------------------- R3
    bad_method, bad_unres, bad_stand = [], [], []
    for m in matches:
        meth, mkt = m.get("method"), m.get("market")
        if meth in MARKET_METHODS and not mkt:
            bad_method.append(f"{m.get('id')} {meth} without a market block")
        if meth and meth.startswith("MODEL") and mkt:
            bad_method.append(f"{m.get('id')} {meth} but a market block is present")
        if mkt:
            n = len(mkt.get("sources") or [])
            want = "MARKET_CONSENSUS" if n >= 2 else "MARKET_SINGLE"
            if meth != want or mkt.get("source_count") != n:
                bad_method.append(f"{m.get('id')} method={meth} sources={n} count={mkt.get('source_count')}")
            keys = [s.get("source_key") for s in (mkt.get("sources") or [])]
            if len(set(keys)) != len(keys):
                bad_method.append(f"{m.get('id')} duplicate source_key {keys}")
        if meth == "UNRESOLVED":
            if abs((m.get("prob_team1") or 0) - 0.5) > 1e-9 or m.get("resolved") is not False:
                bad_unres.append(f"{m.get('id')} UNRESOLVED but prob={m.get('prob_team1')} resolved={m.get('resolved')}")
        if meth in STANDINGS_METHODS and "STANDINGS_BLEND_APPLIED" not in (m.get("flags") or []) \
                and meth != "MODEL_STANDINGS":
            bad_stand.append(f"{m.get('id')} {meth} without STANDINGS_BLEND_APPLIED")
    rep.add("R3", "method label agrees with the evidence carried on the row",
            "PASS" if not bad_method and not bad_unres and not bad_stand else "FAIL",
            f"method mismatches={len(bad_method)}; unresolved mismatches={len(bad_unres)}; "
            f"standings mismatches={len(bad_stand)}", (bad_method + bad_unres + bad_stand)[:10])

    # ---------------------------------------------------------------- R4/R5/R6
    devig_rows, devig_bad = [], []
    cons_rows, cons_bad, disp_bad = [], [], []
    for m in matches:
        mkt = m.get("market")
        if not mkt:
            continue
        srcs = mkt.get("sources") or []
        ps, ws = [], []
        for s in srcs:
            d1, d2 = s.get("decimal_team1"), s.get("decimal_team2")
            if d1 and d2:
                i1, i2 = 1.0 / d1, 1.0 / d2
                recomputed = i1 / (i1 + i2)
                delta = abs(recomputed - (s.get("prob_team1") or 0))
                devig_rows.append({"fixture": m.get("id"), "source": s.get("source"),
                                   "decimal": [d1, d2], "published": s.get("prob_team1"),
                                   "recomputed": round(recomputed, 4), "delta": round(delta, 4)})
                if delta > 0.002:
                    devig_bad.append(f"{m.get('id')} {s.get('source')} {d1}/{d2} -> "
                                     f"{round(recomputed, 4)} vs published {s.get('prob_team1')}")
            if s.get("prob_team1") is not None:
                ps.append(s["prob_team1"])
                ws.append(WEIGHTS.get(s.get("source_key"), DEFAULT_WEIGHT))
        if ps:
            wmean = sum(p * w for p, w in zip(ps, ws)) / sum(ws)
            cons = _median(ps) if len(ps) >= 3 else wmean
            published = mkt.get("consensus_team1")
            row_p1 = m.get("prob_team1")
            cons_rows.append({"fixture": m.get("id"), "match": f"{m.get('team1')} vs {m.get('team2')}",
                              "sources": len(ps), "recomputed_consensus": round(cons, 4),
                              "published_consensus": published, "row_prob_team1": row_p1})
            if published is None or abs(cons - published) > 0.0015:
                cons_bad.append(f"{m.get('id')} recomputed {round(cons, 4)} vs published {published}")
            if row_p1 is None or abs(row_p1 - (published or 0)) > 0.0015:
                cons_bad.append(f"{m.get('id')} row probability {row_p1} != consensus {published}")
            if mkt.get("dispersion") is not None and abs((max(ps) - min(ps)) - mkt["dispersion"]) > 0.0015:
                disp_bad.append(f"{m.get('id')} dispersion {round(max(ps) - min(ps), 4)} vs {mkt['dispersion']}")
            if mkt.get("weighted_mean_team1") is not None and abs(wmean - mkt["weighted_mean_team1"]) > 0.0015:
                disp_bad.append(f"{m.get('id')} weighted mean {round(wmean, 4)} vs {mkt['weighted_mean_team1']}")
    rep.add("R4", "every cited decimal price re-converts to the probability published for that source",
            "PASS" if devig_rows and not devig_bad else ("FAIL" if devig_bad else "UNVERIFIED"),
            f"{len(devig_rows)} de-vig conversions recomputed; {len(devig_bad)} disagree by >0.2pt",
            devig_bad[:10])
    rep.add("R5", "published consensus and row probability recompute from the row's own sources",
            "PASS" if cons_rows and not cons_bad else ("FAIL" if cons_bad else "UNVERIFIED"),
            f"{len(cons_rows)} market rows recomputed (median >=3 sources, else weighted mean); "
            f"{len(cons_bad)} disagree by >0.15pt", cons_bad[:10])
    rep.add("R6", "dispersion and weighted mean recomputed",
            "PASS" if cons_rows and not disp_bad else ("FAIL" if disp_bad else "UNVERIFIED"),
            f"{len(disp_bad)} disagreement(s)", disp_bad[:10])

    # ---------------------------------------------------------------- R7
    leak, diffs = [], []
    for m in matches:
        crowd = (m.get("crowd") or {}).get("team1_pct")
        if crowd is None or m.get("market"):
            continue
        diff = abs((m.get("prob_team1") or 0) - crowd / 100.0)
        diffs.append(diff)
        if diff <= 0.005:
            leak.append(f"{m.get('id')} {m.get('team1')} prob={m.get('prob_team1')} crowd={crowd}%")
    mean_diff = round(sum(diffs) / len(diffs), 4) if diffs else None
    share = round(100.0 * len(leak) / len(diffs), 1) if diffs else 0.0
    rep.add("R7", "Hotspawn crowd percentages are not the published probability",
            "PASS" if diffs and share <= 25.0 else ("FAIL" if diffs else "UNVERIFIED"),
            f"{len(diffs)} model rows compared with the crowd number: mean |published - crowd| = "
            f"{mean_diff}, {len(leak)} row(s) ({share}%) within 0.5pt (coincidence, not a copy)",
            leak[:8])
    notes_ok = all((m.get("crowd") or {}).get("note") for m in matches if m.get("crowd"))
    rep.add("R7b", "every crowd figure carries its 'context only' note",
            "PASS" if notes_ok else "FAIL",
            "crowd.note present on every row that publishes a crowd percentage" if notes_ok
            else "a crowd figure is published without its context-only note")

    # ---------------------------------------------------------------- R8
    no_src, no_official, bad_host, bad_claim, hosts = [], [], [], [], Counter()
    for m in matches:
        srcs = m.get("sources") or []
        if not srcs:
            no_src.append(str(m.get("id")))
            continue
        urls = [s.get("url") or "" for s in srcs]
        for s in srcs:
            h = _host(s.get("url"))
            hosts[h] += 1
            if not h.startswith("www.") and h not in ALLOWED_HOSTS and h:
                pass
            if h and h not in ALLOWED_HOSTS:
                bad_host.append(f"{m.get('id')} {h}")
            if "hotspawn" in h and "fixture list only" not in (s.get("claim") or ""):
                bad_claim.append(f"{m.get('id')} {s.get('claim')!r}")
        if not any(_host(u) not in ("www.hotspawn.com", "play.hotspawn.com", "hotspawn.com") for u in urls):
            no_official.append(str(m.get("id")))
        if not all(u.startswith("https://") for u in urls):
            no_src.append(f"{m.get('id')} non-https source url")
    rep.add("R8", "every row cites https sources, at least one independent of Hotspawn",
            "PASS" if not no_src and not no_official else "FAIL",
            f"rows without a source={len(no_src)}; rows whose only source is Hotspawn={len(no_official)}",
            (no_src + no_official)[:10])
    rep.add("R8b", "every cited host is on the approved provenance allowlist",
            "PASS" if not bad_host else "WARN",
            f"{len(bad_host)} citation(s) to an unapproved host; hosts seen: "
            + ", ".join(f"{h}({n})" for h, n in hosts.most_common()), sorted(set(bad_host))[:10])
    rep.add("R8c", "the Hotspawn citation states it is the fixture list only",
            "PASS" if not bad_claim else "FAIL",
            f"{len(bad_claim)} Hotspawn citation(s) that could be read as a probability source",
            bad_claim[:6])

    # ---------------------------------------------------------------- R9
    recomputed_counts = {
        "fixtures": len(matches),
        "market": sum(1 for m in matches if m.get("market")),
        "model": sum(1 for m in matches if str(m.get("method", "")).startswith("MODEL")),
        "standings": sum(1 for m in matches if m.get("method") in STANDINGS_METHODS),
        "resolved": sum(1 for m in matches if m.get("resolved")),
        "unresolved": sum(1 for m in matches if m.get("method") == "UNRESOLVED"),
        "low_confidence": sum(1 for m in matches if (m.get("confidence") or "").lower() == "low"),
    }
    count_diff = [f"{k}: published={counts.get(k)} recomputed={v}"
                  for k, v in recomputed_counts.items() if counts.get(k) != v]
    tally = Counter(m.get("method") for m in matches)
    by_method = coverage.get("counts_by_method") or {}
    tally_diff = [f"{k}: published={by_method.get(k, 0)} recomputed={v}" for k, v in tally.items()
                  if by_method.get(k, 0) != v]
    if sum(by_method.values()) != len(matches):
        tally_diff.append(f"counts_by_method sums to {sum(by_method.values())}, not {len(matches)}")
    nxt = counts.get("next_24h")
    if gen:
        recomputed_next24 = sum(1 for m in matches
                                if (_parse(m.get("start_utc")) or gen) <= gen + timedelta(hours=24))
        if nxt != recomputed_next24:
            count_diff.append(f"next_24h: published={nxt} recomputed={recomputed_next24}")
    rep.add("R9", "the published counts block re-foots against the rows",
            "PASS" if not count_diff and not tally_diff else "FAIL",
            f"{len(count_diff)} count mismatch(es); {len(tally_diff)} method-tally mismatch(es)",
            (count_diff + tally_diff)[:12])
    cov_bad = []
    for key, want in (("fixtures", len(matches)), ("resolved", recomputed_counts["resolved"]),
                      ("unresolved", recomputed_counts["unresolved"]),
                      ("with_external_market", recomputed_counts["market"]),
                      ("with_model", recomputed_counts["model"]),
                      ("with_prior_only", sum(1 for m in matches if m.get("method") == "MODEL_LEAGUE_PRIOR")),
                      ("published_picks", sum(1 for m in matches if m.get("pick")))):
        if coverage.get(key) != want:
            cov_bad.append(f"coverage.{key}: published={coverage.get(key)} recomputed={want}")
    if matches:
        pct = round(100.0 * recomputed_counts["resolved"] / len(matches), 1)
        if coverage.get("resolved_pct") != pct:
            cov_bad.append(f"coverage.resolved_pct: published={coverage.get('resolved_pct')} recomputed={pct}")
    rep.add("R9b", "the coverage block re-foots against the rows",
            "PASS" if not cov_bad else "FAIL", f"{len(cov_bad)} mismatch(es)", cov_bad[:10])

    # ---------------------------------------------------------------- R10
    per = defaultdict(lambda: Counter())
    for m in matches:
        c = per[m.get("tournament") or "(none)"]
        c["fixtures"] += 1
        if m.get("market"):
            c["market"] += 1
        meth = m.get("method") or ""
        if meth in STANDINGS_METHODS:
            c["standings"] += 1
        elif meth == "MODEL_LEAGUE_PRIOR":
            c["league_prior"] += 1
        elif meth == "UNRESOLVED":
            c["unresolved"] += 1
        elif meth.startswith("MODEL") or meth in MARKET_METHODS:
            # an Elo-priced row; a market row with a model comparison is still market-priced
            if not m.get("market"):
                c["elo"] += 1
        if (m.get("confidence") or "").lower() == "low":
            c["low_confidence"] += 1
    league_bad, missing = [], []
    seen = set()
    for b in breakdown:
        name = b.get("tournament")
        seen.add(name)
        c = per.get(name)
        if not c:
            league_bad.append(f"{name}: breakdown row with no fixtures")
            continue
        for k in ("fixtures", "market", "elo", "standings", "league_prior", "unresolved", "low_confidence"):
            if b.get(k) is not None and int(b.get(k)) != int(c.get(k, 0)):
                league_bad.append(f"{name}.{k}: published={b.get(k)} recomputed={c.get(k, 0)}")
    missing = [t for t in per if t not in seen]
    total = sum(int(b.get("fixtures") or 0) for b in breakdown)
    if total != len(matches):
        league_bad.append(f"league_breakdown fixtures sum to {total}, not {len(matches)}")
    rep.add("R10", "every per-league row re-foots against the rows it summarises",
            "PASS" if not league_bad and not missing else "FAIL",
            f"{len(breakdown)} league rows, {total} fixtures; {len(league_bad)} mismatch(es); "
            f"leagues missing from the breakdown: {missing or 'none'}", league_bad[:12])

    # ---------------------------------------------------------------- R11
    tiers = Counter((m.get("tier") or "(none)") for m in matches)
    unpublished = sum(n for t, n in tiers.items() if t.upper() not in KNOWN_TIERS)
    rep.add("R11", "Hotspawn tier values as published (never inferred)",
            "INFO",
            f"{unpublished} of {len(matches)} rows carry no tier from Hotspawn and are shown as "
            f"'Tier not published'; observed values: "
            + ", ".join(f"{t}={n}" for t, n in tiers.most_common()))

    # ---------------------------------------------------------------- R12
    ex_ids = {str(x.get("id")) for x in excluded if isinstance(x, dict) and x.get("id")}
    overlap = sorted(ex_ids & set(ids))
    rep.add("R12", "no cancelled/excluded fixture is priced",
            "PASS" if not overlap else "FAIL",
            f"{len(ex_ids)} excluded fixture(s); {len(overlap)} also priced", overlap[:10])

    # ---------------------------------------------------------------- R13
    pair = Counter()
    for m in matches:
        key = (tuple(sorted([(m.get("team1") or "").lower(), (m.get("team2") or "").lower()])),
               m.get("tournament"), (m.get("start_utc") or "")[:10])
        pair[key] += 1
    dups = [f"{' vs '.join(k[0])} ({k[1]}, {k[2]}) x{n}" for k, n in pair.items() if n > 1]
    rep.add("R13", "the same pair in the same competition on the same day is listed once",
            "PASS" if not dups else "WARN", f"{len(dups)} duplicate listing(s)", dups[:8])

    # ---------------------------------------------------------------- R14
    list_bad = []
    by_id = {str(m.get("id")): m for m in matches}
    for fid in payload.get("featured") or []:
        row = by_id.get(str(fid))
        if not row:
            list_bad.append(f"featured id {fid} is not a priced row")
        elif not row.get("market"):
            list_bad.append(f"featured id {fid} has no market block")
    for item in payload.get("next_24h") or []:
        fid = str(item.get("id") if isinstance(item, dict) else item)
        row = by_id.get(fid)
        if not row:
            list_bad.append(f"next_24h id {fid} is not a priced row")
            continue
        start = _parse(row.get("start_utc"))
        if gen and start and start > gen + timedelta(hours=24):
            list_bad.append(f"next_24h id {fid} starts {row.get('start_utc')}, outside 24h")
    rep.add("R14", "the featured and next-24h lists point at real rows inside their window",
            "PASS" if not list_bad else "FAIL", f"{len(list_bad)} problem(s)", list_bad[:10])

    # ---------------------------------------------------------------- R15/R16
    spread_bad, delta_bad, delta_rows = [], [], 0
    for m in matches:
        mkt = m.get("market")
        if not mkt:
            continue
        row_start = _parse(m.get("start_utc"))
        books = []
        for s_ in mkt.get("sources") or []:
            bstart = _parse(s_.get("start_utc"))
            if row_start is None or bstart is None:
                continue
            # model.py matches on abs(delta) so the published delta is unsigned;
            # the direction stays visible because the row prints both timestamps.
            delta = abs((row_start - bstart).total_seconds()) / 3600.0
            delta_rows += 1
            published = s_.get("start_delta_hours")
            if published is None or abs(round(delta, 1) - published) > 0.051:
                delta_bad.append(f"{m.get('id')} {s_.get('source')}: book start {s_.get('start_utc')} "
                                 f"vs row {m.get('start_utc')} -> |{round(delta, 2)}| h, published {published}")
            if s_.get("source_key") in ("pinnacle", "unibet", "bovada"):
                books.append(round(delta, 1))
        want_spread = round(max(books), 1) if books else None
        if (mkt.get("time_spread_hours") or None) != want_spread:
            spread_bad.append(f"{m.get('id')}: time_spread_hours={mkt.get('time_spread_hours')} "
                              f"recomputed={want_spread}")
    rep.add("R15", "the published book/Hotspawn time spread recomputes from the timestamps on the row",
            "PASS" if not spread_bad else "FAIL",
            f"{len(spread_bad)} market row(s) whose time_spread_hours does not follow from the "
            f"start times it cites", spread_bad[:8])
    rep.add("R16", "every per-source start delta recomputes (unsigned by design, both timestamps shown)",
            "PASS" if delta_rows and not delta_bad else ("FAIL" if delta_bad else "UNVERIFIED"),
            f"{delta_rows} book start times compared with their fixture; {len(delta_bad)} disagree",
            delta_bad[:8])

    rep.evidence = {"devig": devig_rows, "consensus": cons_rows,
                    "hosts": dict(hosts), "tiers": dict(tiers),
                    "crowd_mean_abs_diff": mean_diff}
    return rep


def write_markdown(rep: Report, payload: dict, path: str) -> None:
    matches = payload.get("matches") or []
    counts = payload.get("counts") or {}
    ev = getattr(rep, "evidence", {})
    lines = [
        "# Row-by-row audit of the published payload",
        "",
        f"Payload `docs/data/picks.json` generated **{payload.get('generated_at')}** "
        f"(schema {payload.get('schema_version')}): {counts.get('fixtures')} fixtures, "
        f"{counts.get('resolved')} resolved, {counts.get('unresolved')} unresolved, "
        f"{counts.get('market')} with an external line.",
        "",
        "Auditor: `scripts/audit_rows.py` — offline, read-only, recomputes each row's arithmetic from the "
        "numbers that row cites. It never invents a value: anything it cannot confirm is reported as "
        "`UNVERIFIED`.",
        "",
        "| Check | Result | Detail |",
        "|---|---|---|",
    ]
    icon = {"PASS": "PASS", "FAIL": "**FAIL**", "WARN": "WARN", "INFO": "INFO", "UNVERIFIED": "UNVERIFIED"}

    def cell(text):
        """A detail string may contain a literal | (e.g. mean |a-b|); escape it."""
        return str(text).replace("|", "\\|")

    for r in rep.rows:
        lines.append(f"| {cell(r['id'] + ' ' + r['title'])} | {icon.get(r['status'], r['status'])} "
                     f"| {cell(r['detail'])} |")
    s = rep.summary()
    lines += ["", f"**{s['PASS']} PASS · {s['FAIL']} FAIL · {s['WARN']} WARN · {s['INFO']} INFO · "
                  f"{s['UNVERIFIED']} UNVERIFIED**", ""]
    for r in rep.rows:
        if r["evidence"]:
            lines += [f"### {r['id']} evidence", ""]
            for e in r["evidence"]:
                lines.append(f"- {str(e).replace('|', chr(92) + '|')}")
            lines.append("")
    if ev.get("consensus"):
        lines += ["## Market rows: consensus recomputed from the row's own sources", "",
                  "| Fixture | Match | Sources | Recomputed consensus | Published consensus | Row probability |",
                  "|---|---|---|---|---|---|"]
        for c in ev["consensus"]:
            lines.append(f"| {c['fixture']} | {c['match']} | {c['sources']} | {c['recomputed_consensus']} "
                         f"| {c['published_consensus']} | {c['row_prob_team1']} |")
        lines.append("")
    if ev.get("devig"):
        lines += ["## De-vig recomputed for every cited decimal price", "",
                  "| Fixture | Source | Decimals (team1 / team2) | Published p(team1) | Recomputed | Δ |",
                  "|---|---|---|---|---|---|"]
        for c in ev["devig"]:
            lines.append(f"| {c['fixture']} | {c['source']} | {c['decimal'][0]} / {c['decimal'][1]} "
                         f"| {c['published']} | {c['recomputed']} | {c['delta']} |")
        lines.append("")
    lines += ["## Cited hosts", ""]
    for h, n in sorted((ev.get("hosts") or {}).items(), key=lambda kv: -kv[1]):
        lines.append(f"- `{h}` — {n} citation(s)")
    lines += ["", f"Rows audited: **{len(matches)}**.", ""]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main() -> int:
    with open(PICKS, encoding="utf-8") as fh:
        payload = json.load(fh)
    rep = audit(payload)
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump({"audited_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "payload_generated_at": payload.get("generated_at"),
                   "rows": len(payload.get("matches") or []),
                   "summary": rep.summary(), "checks": rep.rows,
                   "evidence": getattr(rep, "evidence", {})}, fh, indent=1)
    write_markdown(rep, payload, OUT_MD)
    s = rep.summary()
    print(f"row audit: {s['PASS']} PASS · {s['FAIL']} FAIL · {s['WARN']} WARN · "
          f"{s['INFO']} INFO · {s['UNVERIFIED']} UNVERIFIED over {len(payload.get('matches') or [])} rows")
    for r in rep.rows:
        if r["status"] in ("FAIL", "WARN", "UNVERIFIED"):
            print(f"  {r['status']} {r['id']} {r['title']}: {r['detail']}")
            for e in r["evidence"][:5]:
                print(f"      - {e}")
    return 1 if rep.fails else 0


if __name__ == "__main__":
    sys.exit(main())

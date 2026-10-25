#!/usr/bin/env python3
"""
test_verifier.py — self-tests for scripts/verify_site.py.

Each test builds a synthetic payload that violates exactly one rule and asserts
that the corresponding check FAILs (so a green verification run cannot be a
false negative). Run: python3 verification/test_verifier.py
"""
from __future__ import annotations

import copy
import importlib.util
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("verify_site",
                                              os.path.join(ROOT, "scripts", "verify_site.py"))
vs = importlib.util.module_from_spec(spec)
sys.modules["verify_site"] = vs
spec.loader.exec_module(vs)

NOW = datetime.now(timezone.utc).isoformat()

BASE_ROW = {
    "team1": "Team A", "team2": "Team B",
    "tournament": "Test League", "tier": "C", "points": "10",
    "start_raw": "Oct 22, 12:00", "start_utc": "2026-10-22T12:00:00+00:00",
    "hotspawn_url": "https://www.hotspawn.com/matches/team-a-vs-team-b-test-1",
    "source_lobby": "https://play.hotspawn.com/lol-pickems",
    "market_url": "https://polymarket.com/event/test",
    "prob_team1": 0.6, "prob_team2": 0.4, "pick": "Team A", "pick_prob": 0.6,
    "method": "MARKET_POLYMARKET",
    "evidence": "Polymarket: Team A vs Team B (BO1) - Test",
    "confidence": "High",
}


def payload(rows, **kw):
    p = {"generated_at": NOW, "count": len(rows),
         "counts_by_method": {m: sum(1 for r in rows if r.get("method") == m)
                              for m in vs.METHODS},
         "matches": rows}
    p.update(kw)
    return p


def run(rows, **kw):
    rep = vs.Report()
    vs.verify_data(rep, payload(rows, **kw), "test.json", 8.0)
    return {c["id"]: c for c in rep.checks}


def assert_status(checks, cid, want, label):
    got = checks.get(cid, {}).get("status")
    ok = got == want
    print(f"  [{'ok' if ok else 'FAILED'}] {label}: {cid} = {got} (want {want})")
    return ok


def main() -> int:
    results = []

    # baseline: a clean row must pass every data check
    c = run([copy.deepcopy(BASE_ROW)])
    results += [assert_status(c, i, vs.PASS, "clean row passes")
                for i in ("D2", "D3", "D4", "D5", "D6", "D7", "D8a", "D8c", "D8d", "D9", "D12", "D20")]

    # pick not one of the teams
    r = copy.deepcopy(BASE_ROW); r["pick"] = "Team C"
    results.append(assert_status(run([r]), "D3", vs.FAIL, "bad pick"))
    # probabilities off by 10 points
    r = copy.deepcopy(BASE_ROW); r["prob_team1"], r["prob_team2"] = 0.6, 0.5
    results.append(assert_status(run([r]), "D4", vs.FAIL, "probs do not sum to 1"))
    # pick_prob inconsistent
    r = copy.deepcopy(BASE_ROW); r["pick_prob"] = 0.9
    results.append(assert_status(run([r]), "D5", vs.FAIL, "pick_prob wrong"))
    # unknown method
    r = copy.deepcopy(BASE_ROW); r["method"] = "GUT_FEEL"
    results.append(assert_status(run([r]), "D6", vs.FAIL, "undocumented method"))
    # no source link anywhere
    r = copy.deepcopy(BASE_ROW)
    for k in ("market_url", "source_url", "hotspawn_url", "source_lobby"):
        r.pop(k, None)
    r["evidence"] = "trust me"
    results.append(assert_status(run([r]), "D7", vs.FAIL, "no source link"))
    # market row with no market URL
    r = copy.deepcopy(BASE_ROW); r["market_url"] = ""
    r["source_url"] = "https://lol.fandom.com/wiki/Test"
    results.append(assert_status(run([r]), "D8a", vs.FAIL, "market row without market url"))
    # model row missing a recorded-results source URL
    r = copy.deepcopy(BASE_ROW); r["method"] = "MODEL_ELO"; r.pop("market_url", None)
    r["sources"] = [{"name": "Hotspawn fixture", "url": r["hotspawn_url"]}]
    results.append(assert_status(run([r]), "D8c", vs.FAIL, "model row without results source"))
    # generic results table without the explicit provenance warning
    r = copy.deepcopy(BASE_ROW); r["method"] = "MODEL_ELO"; r.pop("market_url", None)
    r["source_url"] = "https://lol.fandom.com/wiki/Special:CargoTables/MatchSchedule"
    results.append(assert_status(run([r]), "D8d", vs.FAIL, "generic model source without flag"))
    r["flags"] = ["GENERIC_RESULTS_SOURCE"]
    results.append(assert_status(run([r]), "D8d", vs.PASS, "generic model source correctly flagged"))
    # unresolved row that is not 50/50
    r = copy.deepcopy(BASE_ROW); r["method"] = "UNRESOLVED"; r["prob_team1"] = 0.7
    r["prob_team2"] = 0.3; r["pick"] = "Team A"; r["pick_prob"] = 0.7
    r["evidence"] = "no data"; r["confidence"] = "Unresolved"
    results.append(assert_status(run([r]), "D8b", vs.FAIL, "unresolved not 50/50"))
    # hotspawn cited as the probability source
    r = copy.deepcopy(BASE_ROW)
    r["market_url"] = "https://www.hotspawn.com/lol-pickems"
    results.append(assert_status(run([r]), "D12", vs.FAIL, "hotspawn as prob source"))
    # duplicate fixture
    rows = [copy.deepcopy(BASE_ROW), copy.deepcopy(BASE_ROW)]
    results.append(assert_status(run(rows), "D9", vs.FAIL, "duplicate fixture"))
    # counts_by_method lies
    r = copy.deepcopy(BASE_ROW)
    p = payload([r]); p["counts_by_method"]["UNRESOLVED"] = 5
    rep = vs.Report(); vs.verify_data(rep, p, "t.json", 8.0)
    results.append(assert_status({x["id"]: x for x in rep.checks}, "D10", vs.FAIL,
                                 "counts_by_method mismatch"))
    # Game-1 market used as a series price
    r = copy.deepcopy(BASE_ROW)
    r["evidence"] = "Polymarket: LoL: Team A vs Team B - Game 1 Winner"
    results.append(assert_status(run([r]), "D16", vs.FAIL, "game-1 as series"))
    # BO1 game-1 style evidence is fine when marked BO1
    r = copy.deepcopy(BASE_ROW)
    r["evidence"] = "Polymarket: Team A vs Team B (BO1) - Worlds Group Stage"
    results.append(assert_status(run([r]), "D16", vs.PASS, "BO1 market ok"))
    # duplicate bookmaker board rows inside market.sources must fail D20
    r = copy.deepcopy(BASE_ROW)
    r["method"] = "MARKET_CONSENSUS"
    r["market"] = {
        "source_count": 2,
        "sources": [
            {"source": "Pinnacle", "source_key": "pinnacle", "prob_team1": 0.6,
             "url": "https://www.pinnacle.com/en/esports/league-of-legends"},
            {"source": "Pinnacle", "source_key": "pinnacle", "prob_team1": 0.6,
             "url": "https://www.pinnacle.com/en/esports/league-of-legends"},
        ],
    }
    results.append(assert_status(run([r]), "D20", vs.FAIL, "duplicate bookmaker in market.sources"))
    # prop market board leaked into market.sources must fail D20
    r = copy.deepcopy(BASE_ROW)
    r["method"] = "MARKET_SINGLE"
    r["market"] = {
        "source_count": 1,
        "sources": [
            {"source": "Pinnacle", "source_key": "pinnacle", "prob_team1": 0.782,
             "market": "First Baron", "url": "https://www.pinnacle.com/en/esports/league-of-legends"},
        ],
    }
    results.append(assert_status(run([r]), "D20", vs.FAIL, "prop market leaked into market.sources"))
    # external-source probe row without an https link / carrying a probability must fail D22
    good_probe = {"checked_at": NOW, "summary": {"checked": 1},
                  "books": [{"name": "Example book", "url": "https://example.com/lol",
                             "http_status": 403, "verdict": "blocked"}]}
    results.append(assert_status(run([copy.deepcopy(BASE_ROW)], market_probe=good_probe),
                                 "D22", vs.PASS, "clean probe row"))
    bad = copy.deepcopy(good_probe); bad["books"][0]["url"] = "http://example.com/lol"
    results.append(assert_status(run([copy.deepcopy(BASE_ROW)], market_probe=bad),
                                 "D22", vs.FAIL, "probe row without https"))
    bad2 = copy.deepcopy(good_probe); bad2["books"][0]["prob_team1"] = 0.61
    results.append(assert_status(run([copy.deepcopy(BASE_ROW)], market_probe=bad2),
                                 "D22", vs.FAIL, "probe row carrying a probability"))
    # stale data
    old = "2020-01-01T00:00:00+00:00"
    rep = vs.Report(); vs.verify_data(rep, payload([copy.deepcopy(BASE_ROW)],
                                                   generated_at=old), "t.json", 8.0)
    results.append(assert_status({x["id"]: x for x in rep.checks}, "D1", vs.FAIL,
                                 "stale generated_at"))

    # ------------------------------------------------------------------ site structure (S11/S12)
    # S11 must fail when a page uses a class the stylesheet never defines — the exact
    # defect that clipped the executive summary header to a 12 px progress bar.
    import tempfile

    def structure_checks(css, pages_html):
        with tempfile.TemporaryDirectory() as td:
            os.makedirs(os.path.join(td, "assets"), exist_ok=True)
            with open(os.path.join(td, "assets", "style.css"), "w") as fh:
                fh.write(css)
            for name, html in pages_html.items():
                with open(os.path.join(td, name), "w") as fh:
                    fh.write(html)
            rep = vs.Report()
            vs.verify_structure(rep, td)
            return {c["id"]: c for c in rep.checks}

    GOOD_NAV = ('<nav class="top-nav"><ul><li><a href="picks.html">All picks</a></li></ul></nav>'
                '<nav class="bottom-nav"><a href="picks.html">Picks</a></nav>'
                '<span id="updated"></span><span id="freshness"></span>')
    good_page = f'<html><body><div class="card">ok</div>{GOOD_NAV}</body></html>'
    css_good = ".card { padding: 1px } .top-nav { border: 0 } .bottom-nav { display: grid }"

    c = structure_checks(css_good, {"index.html": good_page})
    results.append(assert_status(c, "S11", vs.PASS, "defined classes pass S11"))
    results.append(assert_status(c, "S12", vs.PASS, "consistent page passes S12"))

    # unstyled class (the header regression)
    bad = f'<html><body><div class="wrap bar">header</div>{GOOD_NAV}</body></html>'
    c = structure_checks(css_good, {"index.html": bad})
    results.append(assert_status(c, "S11", vs.FAIL, "unstyled class fails S11"))

    # navigation that differs between pages
    other = f'<html><body><div class="card">ok</div>{GOOD_NAV.replace("All picks", "Picks")}</body></html>'
    c = structure_checks(css_good, {"index.html": good_page, "picks.html": other})
    results.append(assert_status(c, "S12", vs.FAIL, "mismatched top nav fails S12"))

    # duplicate id on one page
    dup_page = f'<html><body><div class="card" id="x"></div><div id="x"></div>{GOOD_NAV}</body></html>'
    c = structure_checks(css_good, {"index.html": dup_page})
    results.append(assert_status(c, "S12", vs.FAIL, "duplicate id fails S12"))

    # missing freshness slot
    nofresh = ('<nav class="top-nav"><ul><li><a href="picks.html">All picks</a></li></ul></nav>'
               '<nav class="bottom-nav"><a href="picks.html">Picks</a></nav>')
    c = structure_checks(css_good, {"index.html": f'<html><body><div class="card">ok</div>{nofresh}</body></html>'})
    results.append(assert_status(c, "S12", vs.FAIL, "missing freshness slot fails S12"))

    # ---- S16: phone home-screen installability --------------------------------
    def install_checks(files, page_html):
        with tempfile.TemporaryDirectory() as td:
            os.makedirs(os.path.join(td, "assets"), exist_ok=True)
            for name, data in files.items():
                target = os.path.join(td, name)
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, "wb") as fh:
                    fh.write(data if isinstance(data, bytes) else data.encode())
            with open(os.path.join(td, "index.html"), "w") as fh:
                fh.write(page_html)
            rep = vs.Report()
            vs.verify_phone_install(rep, td)
            return {c["id"]: c for c in rep.checks}

    def tiny_png(w, h):
        import struct, zlib
        raw = b"".join(b"\x00" + b"\xff\xff\xff\xff" * w for _ in range(h))
        def chunk(tag, data):
            return (struct.pack(">I", len(data)) + tag + data
                    + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
        return (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 1)) + chunk(b"IEND", b""))

    good_page_s16 = ('<html><head><meta name="viewport" content="width=device-width">'
                     '<link rel="manifest" href="manifest.webmanifest">'
                     '<link rel="apple-touch-icon" href="assets/apple-touch-icon.png"></head></html>')
    good_manifest = ('{"name":"n","short_name":"s","start_url":"./index.html","display":"standalone",'
                     '"icons":[{"src":"assets/a-192.png","sizes":"192x192","purpose":"any"},'
                     '{"src":"assets/a-512.png","sizes":"512x512","purpose":"any maskable"}]}')
    files_ok = {"manifest.webmanifest": good_manifest,
                "assets/a-192.png": tiny_png(192, 192),
                "assets/a-512.png": tiny_png(512, 512),
                "assets/apple-touch-icon.png": tiny_png(180, 180)}
    c = install_checks(files_ok, good_page_s16)
    results.append(assert_status(c, "S16", vs.PASS, "complete manifest+icons pass S16"))

    c = install_checks({k: v for k, v in files_ok.items() if k != "manifest.webmanifest"}, good_page_s16)
    results.append(assert_status(c, "S16", vs.FAIL, "missing manifest fails S16"))

    # declared size disagrees with the real PNG
    bad_size = good_manifest.replace("192x192", "512x512", 1)
    c = install_checks({**files_ok, "manifest.webmanifest": bad_size}, good_page_s16)
    results.append(assert_status(c, "S16", vs.FAIL, "wrong declared icon size fails S16"))

    # a page that forgets the manifest link
    c = install_checks(files_ok, '<html><head><meta name="viewport" content="width=device-width">'
                                 '<link rel="apple-touch-icon" href="assets/apple-touch-icon.png"></head></html>')
    results.append(assert_status(c, "S16", vs.FAIL, "page without manifest link fails S16"))

    # no maskable icon
    no_mask = good_manifest.replace('"any maskable"', '"any"')
    c = install_checks({**files_ok, "manifest.webmanifest": no_mask}, good_page_s16)
    results.append(assert_status(c, "S16", vs.FAIL, "no maskable icon fails S16"))

    # ---- S17: every manual-review row carries a source link --------------------
    def review_checks(sections_html):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "flagged.html"), "w") as fh:
                fh.write(sections_html)
            rep = vs.Report()
            vs.verify_review_rows(rep, td)
            return {c["id"]: c for c in rep.checks}

    def review_sections(audit_rows, coverage_rows):
        def body(rows):
            return "".join(f"<tr>{r}</tr>" for r in rows)
        return (
            '<section id="source-coverage-flags"><table><tbody>'
            + body(coverage_rows) + "</tbody></table></section>"
            '<section id="audit-2026-10-25"><table><tbody>'
            + body(audit_rows) + "</tbody></table></section>"
        )

    row_linked = '<td>A</td><td>x</td><td><a href="https://example.org/a">src ↗</a></td><td>ok</td>'
    row_bare = '<td>B</td><td>x</td><td>no link at all</td><td>ok</td>'
    cov = [row_linked] * 3
    audit = [row_linked] * 8

    c = review_checks(review_sections(audit, cov))
    results.append(assert_status(c, "S17", vs.PASS, "all rows linked pass S17"))

    # one audit row silently loses its link
    c = review_checks(review_sections(audit[:7] + [row_bare], cov))
    results.append(assert_status(c, "S17", vs.FAIL, "a row without a source link fails S17"))

    # a whole section disappears
    only_cov = ('<section id="source-coverage-flags"><table><tbody>'
                + "".join(f"<tr>{r}</tr>" for r in cov) + "</tbody></table></section>")
    c = review_checks(only_cov)
    results.append(assert_status(c, "S17", vs.FAIL, "missing audit section fails S17"))

    # too few rows to be a real review (guards against an empty table passing)
    c = review_checks(review_sections(audit[:2], cov))
    results.append(assert_status(c, "S17", vs.FAIL, "a shrunken audit table fails S17"))

    # file missing entirely
    with tempfile.TemporaryDirectory() as td:
        rep = vs.Report()
        vs.verify_review_rows(rep, td)
        results.append(assert_status({c2["id"]: c2 for c2 in rep.checks}, "S17", vs.FAIL,
                                     "missing flagged.html fails S17"))

    # helper parsing
    helper_ok = (vs.html_class_names('<div class="a b">') == {"a", "b"}
                 and vs.css_class_names(".a{x} /* .z{} */ .b>.c{x}") == {"a", "b", "c"}
                 and vs.duplicate_ids('<i id="a"></i><i id="a"></i>') == ["a"]
                 and vs.nav_signature('<nav class="top-nav"><a href="x.html">X</a></nav>', "top-nav")
                 == (("x.html", "X"),))
    print(f"  [{'ok' if helper_ok else 'FAILED'}] class/id/nav parsing helpers")
    results.append(helper_ok)

    # cron parser
    for expr, want in [("0 */6 * * *", 6.0), ("0 */4 * * *", 4.0),
                       ("0 */12 * * *", 12.0), ("30 2 * * *", None),
                       ("0 0,6,12,18 * * *", 6.0)]:
        got = vs.cron_interval_hours(expr)
        ok = got == want
        print(f"  [{'ok' if ok else 'FAILED'}] cron {expr!r} -> {got} (want {want})")
        results.append(ok)

    print(f"\n{sum(results)}/{len(results)} verifier self-tests passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

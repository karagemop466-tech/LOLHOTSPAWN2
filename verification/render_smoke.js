#!/usr/bin/env node
/**
 * render_smoke.js — execute the real site JS against the real payload, head-less.
 *
 * jsdom has no layout engine, so this does not prove pixels. It proves the things
 * a static HTML/CSS contract cannot:
 *   - every page boots app.js with no uncaught exception / unhandled rejection
 *   - the header timestamp + freshness chip are actually populated on every page
 *   - the executive summary's "Where the picks are" counters and stat tiles fill in
 *   - the picks table renders one row per fixture, and the match page renders detail
 *   - the colour-theme button in the header is live: it flips <html data-theme>,
 *     swaps its icon/label and survives a reload (localStorage round-trip)
 *
 * Usage (needs jsdom; not vendored so the repo stays dependency-free):
 *   npm install --no-save jsdom@24 && node verification/render_smoke.js
 * Exit code 1 on any failed assertion.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { JSDOM, VirtualConsole } = require("jsdom");

const ROOT = path.resolve(__dirname, "..");
const DOCS = process.env.RENDER_SMOKE_DOCS || path.join(ROOT, "docs");
const PAYLOAD = JSON.parse(fs.readFileSync(path.join(DOCS, "data", "picks.json"), "utf8"));

const results = [];
function check(name, ok, detail) {
  results.push({ name, ok: !!ok, detail: ok ? "" : String(detail ?? "") });
}

async function boot(pageFile, { url = "", store = null } = {}) {
  const file = path.join(DOCS, pageFile);
  const html = fs.readFileSync(file, "utf8");
  const errors = [];
  const vc = new VirtualConsole();
  vc.on("jsdomError", (e) => errors.push(e.message));
  vc.on("error", (...a) => errors.push(a.join(" ")));

  const dom = new JSDOM(html, {
    url: `https://example.test/docs/${pageFile}${url}`,
    runScripts: "dangerously",
    resources: undefined,
    pretendToBeVisual: true,
    virtualConsole: vc,
  });

  const { window } = dom;
  // Serve data/picks.json from disk; everything else (no network) fails loudly.
  window.fetch = async (input) => {
    const target = String(input);
    if (target.endsWith("data/picks.json")) {
      return { ok: true, status: 200, json: async () => PAYLOAD };
    }
    throw new Error(`unexpected fetch ${target}`);
  };
  if (store) {
    for (const [k, v] of Object.entries(store)) window.localStorage.setItem(k, v);
  }
  // jsdom does not parse scripts injected before this point with `runScripts`,
  // so load app.js by hand in document order.
  window.eval(fs.readFileSync(path.join(DOCS, "assets", "app.js"), "utf8"));
  window.document.dispatchEvent(new window.Event("DOMContentLoaded", { bubbles: true }));
  await new Promise((r) => setTimeout(r, 250));
  return { dom, window, doc: window.document, errors };
}

function text(doc, sel) {
  const el = doc.querySelector(sel);
  return el ? el.textContent.trim() : null;
}

(async () => {
  const pages = ["index.html", "picks.html", "leagues.html", "unresolved.html",
    "flagged.html", "methodology.html", "match.html"];

  for (const page of pages) {
    const { window, doc, errors } = await boot(page, {
      url: page === "match.html" ? `?id=${encodeURIComponent(PAYLOAD.matches[0].id)}` : "",
    });
    check(`${page}: no JS errors`, errors.length === 0, errors.join(" | "));
    const updated = text(doc, "#updated");
    check(`${page}: header timestamp populated`, !!updated && !/Loading/.test(updated), updated);
    const fresh = text(doc, "#freshness");
    check(`${page}: freshness chip populated`, !!fresh && !/checking/.test(fresh), fresh);
    const toggle = doc.querySelector("#theme-toggle");
    check(`${page}: theme button present`, !!toggle);

    if (toggle) {
      const before = doc.documentElement.getAttribute("data-theme");
      toggle.dispatchEvent(new window.Event("click", { bubbles: true }));
      const after = doc.documentElement.getAttribute("data-theme");
      check(`${page}: theme button flips data-theme`, !!after && after !== before, `${before} -> ${after}`);
      const stored = window.localStorage.getItem("lolpicks-theme");
      check(`${page}: theme choice persisted`, stored === after, stored);
    }

    if (page === "index.html") {
      check("index: stat fixtures", text(doc, "#stat-fixtures") === String(PAYLOAD.matches.length),
        text(doc, "#stat-fixtures"));
      check("index: where-picks counter", text(doc, "#where-picks") === String(PAYLOAD.matches.length),
        text(doc, "#where-picks"));
      check("index: where-unresolved counter",
        text(doc, "#where-unresolved") === String(PAYLOAD.unresolved?.count ?? 0),
        text(doc, "#where-unresolved"));
      check("index: coverage bar filled", /width:/.test(doc.querySelector("#coverage-bar")?.innerHTML || ""));
      check("index: quick-picks table rows", doc.querySelectorAll("#quick-picks-body tr").length >= 1,
        doc.querySelectorAll("#quick-picks-body tr").length);
      check("index: starting-soon cards", doc.querySelectorAll("#next24 article.match").length >= 1,
        doc.querySelectorAll("#next24 article.match").length);
      check("index: per-competition rows", doc.querySelectorAll("#summary-leagues-body tr").length >= 1);
      check("index: unresolved summary rendered", /Unresolved picks/.test(text(doc, "#unresolved-summary") || ""));
      check("index: every quick row has a source link",
        Array.from(doc.querySelectorAll("#quick-picks-body tr")).every((tr) => tr.querySelector('a[href^="http"]')));
    }
    if (page === "picks.html") {
      check("picks: one row per fixture",
        doc.querySelectorAll("#picks-body tr").length === PAYLOAD.matches.length,
        `${doc.querySelectorAll("#picks-body tr").length} vs ${PAYLOAD.matches.length}`);
      check("picks: every row states a pick",
        Array.from(doc.querySelectorAll("#picks-body tr .pick-pill")).length === PAYLOAD.matches.length);
      check("picks: every row has an outbound source link",
        Array.from(doc.querySelectorAll("#picks-body tr")).every((tr) => tr.querySelector('a[href^="http"]')));
    }
    if (page === "unresolved.html") {
      check("unresolved: per-league limitation rows",
        doc.querySelectorAll("#league-limitations-body tr").length >= 1);
      check("unresolved: limitations list rendered", !/Loading/.test(text(doc, "#limitations") || "Loading"));
    }
    if (page === "flagged.html") {
      check("flagged: flag rows", doc.querySelectorAll("#flag-groups tr").length >= 1);
      check("flagged: every flagged row has a source link",
        Array.from(doc.querySelectorAll("#flagged-body tr")).every((tr) => tr.querySelector('a[href^="http"]')));
    }
    if (page === "methodology.html") {
      check("methodology: source status rows", doc.querySelectorAll("#sources-status tr").length >= 1);
      check("methodology: backtest rendered", /Log-loss/.test(text(doc, "#backtest") || ""));
    }
    if (page === "match.html") {
      check("match: detail rendered", /vs/.test(text(doc, "#match-detail") || ""));
      check("match: detail has source links",
        doc.querySelectorAll('#match-detail a[href^="http"]').length >= 1);
    }
    window.close();
  }

  // Reload with a stored preference: the saved theme must apply on first paint.
  const { doc } = await boot("picks.html", { store: { "lolpicks-theme": "dark" } });
  check("reload: stored theme applied without a click",
    doc.documentElement.getAttribute("data-theme") === "dark",
    doc.documentElement.getAttribute("data-theme"));

  const failed = results.filter((r) => !r.ok);
  const width = Math.max(...results.map((r) => r.name.length));
  for (const r of results) {
    if (!r.ok) console.log(`FAIL  ${r.name.padEnd(width)}  ${r.detail}`);
  }
  console.log(`${results.length - failed.length}/${results.length} render smoke checks passed`);
  process.exit(failed.length ? 1 : 0);
})().catch((e) => {
  console.error("render smoke crashed:", e);
  process.exit(1);
});

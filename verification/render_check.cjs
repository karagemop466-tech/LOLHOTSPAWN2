#!/usr/bin/env node
/**
 * render_check.cjs — execute the real site JavaScript against the real payload.
 *
 * The DOM-contract check proves that every id the JS looks for exists. This check
 * goes one step further: it loads each page in jsdom, runs docs/assets/app.js with
 * the committed docs/data/picks.json (as the browser would), and asserts that the
 * page actually renders its picks — rows/cards, counts, freshness text, the
 * "where the picks are" strip and the per-page tables — with no page error and no
 * error box. It also checks that the header container is not a fixed-height strip
 * (the regression that clipped the executive summary to 12 px).
 *
 * Usage:  node verification/render_check.cjs [--docs docs]
 * Needs jsdom (`npm i --no-save jsdom`). If jsdom is not installed the script
 * prints a SKIP line and exits 0 so it can never fail a pipeline for a missing
 * optional dev dependency.
 */
"use strict";

const fs = require("fs");
const path = require("path");

let JSDOM;
try {
  ({ JSDOM } = require("jsdom"));
} catch (err) {
  console.log("SKIP render_check: jsdom is not installed (npm i --no-save jsdom)");
  process.exit(0);
}

const args = process.argv.slice(2);
const docsArg = args.indexOf("--docs");
const DOCS = docsArg >= 0 ? args[docsArg + 1] : "docs";

const payloadPath = path.join(DOCS, "data/picks.json");
if (!fs.existsSync(payloadPath)) {
  console.log(`SKIP render_check: ${payloadPath} not found`);
  process.exit(0);
}
const payloadText = fs.readFileSync(payloadPath, "utf8");
const payload = JSON.parse(payloadText);
const appjs = fs.readFileSync(path.join(DOCS, "assets", "app.js"), "utf8");
const css = fs.readFileSync(path.join(DOCS, "assets", "style.css"), "utf8");
const firstId = (payload.matches || [])[0] ? String(payload.matches[0].id) : "";

// page -> checks. `expect` maps a CSS selector to the minimum number of nodes it
// must contain after the script runs; `text` maps an id to a non-empty value.
const PAGES = [
  {
    page: "index.html",
    expect: { "#quick-picks-body tr": 5, "#summary-leagues-body tr": 1, ".match": 3, "#starting-soon .match": 1 },
    text: ["picks-cta", "coverage-text", "updated", "freshness", "stat-fixtures", "soon-count", "unresolved-summary"],
    count: ["stat-fixtures"],
  },
  {
    page: "picks.html",
    expect: { "#picks-body tr": 20, "#countline": 1 },
    text: ["updated", "freshness", "countline"],
  },
  {
    page: "leagues.html",
    expect: { "#leagues-summary-body tr": 1, "#leagues-sections section": 1 },
    text: ["updated", "freshness"],
  },
  {
    page: "unresolved.html",
    expect: { "#league-limitations-body tr": 1 },
    text: ["updated", "freshness", "unresolved-counts", "reasons", "limitations"],
  },
  {
    page: "flagged.html",
    expect: { "#flag-groups tr": 1, "#flagged-body tr": 1, "#excluded-body tr": 1, "#bridges-body tr": 1 },
    text: ["updated", "freshness"],
  },
  {
    page: "methodology.html",
    expect: { "#sources-status tr": 1 },
    text: ["updated", "freshness"],
  },
  {
    page: "match.html",
    query: firstId ? `?id=${encodeURIComponent(firstId)}` : "",
    expect: { "#match-detail .match, #match-detail .detail-hero, #match-detail .card": 1 },
    text: ["updated", "freshness"],
  },
];

const errors = [];
function fail(msg) {
  errors.push(msg);
  console.log(`  [FAIL] ${msg}`);
}
function ok(msg) {
  console.log(`  [ok]   ${msg}`);
}

async function renderPage(spec) {
  const file = path.join(DOCS, spec.page);
  if (!fs.existsSync(file)) {
    fail(`${spec.page}: missing`);
    return;
  }
  // Inline the site script so it runs synchronously at DOMContentLoaded, exactly
  // like the deferred tag in the browser. split/join avoids `$$` replacement.
  const html = fs
    .readFileSync(file, "utf8")
    .split('<script src="assets/app.js" defer></script>')
    .join("<script>" + appjs + "</script>");
  const pageErrors = [];
  const dom = new JSDOM(html, {
    runScripts: "dangerously",
    pretendToBeVisual: true,
    url: `https://example.test/docs/${spec.page}${spec.query || ""}`,
    beforeParse(window) {
      window.fetch = async () => ({ ok: true, status: 200, json: async () => JSON.parse(payloadText) });
      window.addEventListener("error", (e) => pageErrors.push(String((e.error && e.error.stack) || e.message)));
    },
  });
  await new Promise((resolve) => setTimeout(resolve, 1200));
  const { document } = dom.window;

  if (pageErrors.length) {
    fail(`${spec.page}: script error — ${pageErrors[0].split("\n")[0]}`);
    return;
  }
  const errBox = (document.querySelector("#error-box") || {}).textContent || "";
  if (errBox.trim()) fail(`${spec.page}: error box shows "${errBox.trim().slice(0, 90)}"`);

  for (const [selector, min] of Object.entries(spec.expect || {})) {
    const n = document.querySelectorAll(selector).length;
    if (n < min) fail(`${spec.page}: ${selector} has ${n} node(s), expected >= ${min}`);
    else ok(`${spec.page}: ${selector} -> ${n}`);
  }
  for (const id of spec.text || []) {
    const el = document.getElementById(id);
    const text = el ? (el.textContent || "").trim() : "";
    if (!text || /^loading/i.test(text)) fail(`${spec.page}: #${id} not populated`);
  }
  for (const id of spec.count || []) {
    const el = document.getElementById(id);
    const text = el ? (el.textContent || "").trim() : "";
    if (!/^\d+$/.test(text)) fail(`${spec.page}: #${id} is not a number ("${text}")`);
  }
  const loading = Array.from(document.querySelectorAll(".loading")).filter((el) => !el.classList.contains("hidden"));
  if (loading.length) fail(`${spec.page}: ${loading.length} loading placeholder(s) still visible`);

  // header must not be a fixed-height strip (the 12 px .bar regression)
  const header = document.querySelector(".site-header .header-inner");
  if (!header) fail(`${spec.page}: no .header-inner (header not using the shared markup)`);
  else {
    const style = dom.window.getComputedStyle(header);
    const px = parseFloat(style.height);
    if (style.height !== "auto" && Number.isFinite(px) && px < 40) {
      fail(`${spec.page}: header height computes to ${style.height} (clipped)`);
    }
    if (style.overflow === "hidden" && Number.isFinite(px) && px < 60) {
      fail(`${spec.page}: header clips its content (overflow hidden, ${style.height})`);
    }
  }
  const navCurrent = document.querySelectorAll('.top-nav a[aria-current="page"]').length;
  if (navCurrent !== 1) fail(`${spec.page}: ${navCurrent} active primary-nav items (expected 1)`);
  dom.window.close();
}

(async () => {
  const data = payload;
  console.log(
    `render_check: ${data.matches ? data.matches.length : 0} fixtures, generated ${data.generated_at || "?"}, ` +
      `${PAGES.length} pages`
  );
  for (const spec of PAGES) {
    console.log(`\n${spec.page}${spec.query || ""}`);
    await renderPage(spec);
  }
  console.log(
    errors.length ? `\nRENDER CHECK FAILED — ${errors.length} problem(s)` : "\nRENDER CHECK PASS — all pages executed and rendered"
  );
  process.exit(errors.length ? 1 : 0);
})();

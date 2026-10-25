#!/usr/bin/env node
/**
 * mobile_render_390.cjs — render every published page in jsdom at a 390 px
 * viewport and assert what a phone visitor actually sees.
 *
 * jsdom has no layout engine, so this is not a pixel measurement: it asserts the
 * *content and controls* a phone reader depends on —
 *   - the executive summary links, in-site, to every picks list (findability)
 *   - the summary carries the separate unresolved + limitations section
 *   - every picks row/card shows the pick and both win probabilities
 *   - every row links its sources, and no element is wider than the viewport
 *   - the bottom navigation exposes the site sections on a phone
 *
 * The declared geometry (font sizes, tap targets, breakpoints) is checked by
 * verification/mobile_audit_390.py against style.css.
 *
 * Usage: node verification/mobile_render_390.cjs [--docs docs] [--quiet]
 * Exit 1 on any failure.
 */
"use strict";

const fs = require("fs");
const path = require("path");

const args = process.argv.slice(2);
const quiet = args.includes("--quiet");
const docsArg = args.indexOf("--docs");
const DOCS = path.resolve(docsArg >= 0 ? args[docsArg + 1] : path.join(__dirname, "..", "docs"));
const VIEWPORT = 390;
const PAGES = ["index.html", "picks.html", "leagues.html", "unresolved.html",
               "flagged.html", "methodology.html", "match.html"];

let JSDOM;
try {
  ({ JSDOM } = require("jsdom"));
} catch (e) {
  console.log("SKIP mobile_render_390: jsdom is not installed (npm install --no-save jsdom)");
  process.exit(0);
}

const results = [];
function check(name, ok, detail) {
  results.push({ name, ok: !!ok, detail });
  if (!quiet) console.log(`  [${ok ? "ok" : "FAIL"}] ${name}${detail ? ` — ${detail}` : ""}`);
  if (!ok) process.exitCode = 1;
}

const payload = JSON.parse(fs.readFileSync(path.join(DOCS, "data", "picks.json"), "utf8"));
let lastWindow = null;
const app = fs.readFileSync(path.join(DOCS, "assets", "app.js"), "utf8");

async function render(page) {
  const filePath = path.join(DOCS, page);
  const url = `https://picks.test/docs/${page}`;
  let html = fs.readFileSync(filePath, "utf8");
  const safeJs = app.replace(/<\/script>/g, "<\\/script>");
  // Inline the script (jsdom cannot fetch it over https, and file:// blocks
  // history.replaceState). A *function* replacement is required: app.js declares
  // `const $$`, and `$$` inside a replacement string means a literal `$`.
  html = html.replace(/<script src="assets\/app\.js" defer><\/script>/,
    () => `<script>${safeJs}</script>`);
  const { VirtualConsole } = require("jsdom");
  const virtualConsole = new VirtualConsole();
  const errors = [];
  virtualConsole.on("jsdomError", (e) => errors.push(String(e.message || e)));
  const dom = new JSDOM(html, {
    url, runScripts: "dangerously", pretendToBeVisual: true, virtualConsole,
    beforeParse(window) {
      window.fetch = async () => ({
        ok: true, status: 200,
        json: async () => JSON.parse(JSON.stringify(payload)),
      });
      window.__errors = errors;
      window.addEventListener("error", (e) => window.__errors.push(String(e.message || e)));
      window.addEventListener("unhandledrejection", (e) => window.__errors.push(String(e.reason)));
    },
  });
  await new Promise((resolve) => {
    if (dom.window.document.readyState === "complete") resolve();
    else dom.window.addEventListener("load", resolve);
  });
  await new Promise((r) => setTimeout(r, 80));   // app.js awaits fetch()
  return dom.window;
}

(async () => {
  console.log(`390 px phone audit (rendered) — viewport ${VIEWPORT}px, ${PAGES.length} pages`);

  // ---- executive summary: the picks must be findable in one or two taps ----
  const sum = (await render("index.html")).document;
  const hrefs = Array.from(sum.querySelectorAll("a[href]")).map((a) => a.getAttribute("href"));
  check("summary links in-site to the full picks list", hrefs.includes("picks.html"));
  check("summary links in-site to the next-24-hours picks list",
    hrefs.some((h) => (h || "").startsWith("picks.html?filter=next24")));
  check("summary links in-site to the by-league list", hrefs.includes("leagues.html"));
  check("summary links in-site to the unresolved & limitations list",
    hrefs.includes("unresolved.html"));
  check("summary has a full-width primary 'find every pick' button",
    !!sum.querySelector(".hero-actions .btn.primary.big"));
  const cards = sum.querySelectorAll("#picks-here .linkcard");
  check("'Where the updated picks are' card grid renders its destinations",
    cards.length >= 4, `${cards.length} cards`);
  check("every summary linkcard shows a live count",
    Array.from(sum.querySelectorAll(".linkcard .n"))
      .every((e) => (e.textContent || "").trim() !== "" && (e.textContent || "").trim() !== "—"));
  const unresSection = sum.querySelector("#unresolved-section");
  check("summary carries the separate unresolved + limitations section",
    !!unresSection && /limitation/i.test(unresSection.textContent || ""));
  check("summary links down to that section from the hero",
    hrefs.includes("#unresolved-section"));

  // ---- picks page: pick + both probabilities, source link, no overflow -----
  const picks = (await render("picks.html")).document;
  const rows = picks.querySelectorAll("#picks-body tr");
  check("picks page renders a row for every published fixture",
    rows.length === (payload.matches || []).length,
    `${rows.length} rows / ${(payload.matches || []).length} fixtures`);
  const bad = [];
  for (const tr of rows) {
    const txt = tr.textContent || "";
    if (!txt.includes("PICK:") || (txt.match(/%/g) || []).length < 2) bad.push(txt.slice(0, 60));
  }
  check("every picks row shows the pick and both win probabilities", bad.length === 0,
    bad.slice(0, 3).join(" | "));
  check("every picks row links at least one source",
    Array.from(rows).every((tr) => tr.querySelectorAll(".src-links a").length >= 1));
  const over = [];
  for (const el of picks.querySelectorAll("[style]")) {
    for (const m of (el.getAttribute("style") || "").matchAll(/(?:min-)?width\s*:\s*(\d+(?:\.\d+)?)px/g)) {
      if (parseFloat(m[1]) > VIEWPORT) over.push(`${el.tagName}.${el.className}=${m[0]}`);
    }
  }
  check(`no rendered element is wider than the ${VIEWPORT}px viewport`, over.length === 0,
    over.slice(0, 3).join(" | "));
  check("bottom navigation exposes the site sections on a phone",
    picks.querySelectorAll(".bottom-nav a").length >= 5,
    `${picks.querySelectorAll(".bottom-nav a").length} links`);

  // ---- unresolved page: limitations in words, per league -------------------
  const unres = (await render("unresolved.html")).document;
  const utext = (unres.querySelector("#main") || unres.body).textContent || "";
  check("unresolved page states the limitations in words",
    /limitation/i.test(utext) && /no external sportsbook/i.test(utext));
  check("unresolved page shows the per-league limits table",
    unres.querySelectorAll("table tr").length > 3);

  // ---- no page may throw or leave an error box populated -------------------
  for (const page of PAGES) {
    const win = await render(page);
    lastWindow = win;
    const doc = win.document;
    const win2 = lastWindow;
    const err = ((doc.querySelector("#error-box") || {}).textContent || "") +
      ((win2 && win2.__errors) ? win2.__errors.join(" | ") : "");
    check(`${page}: renders with no script error`, err.trim() === "", err.trim().slice(0, 120));
  }

  const failed = results.filter((r) => !r.ok);
  console.log(`\nMobile render audit: ${results.length - failed.length}/${results.length} passed` +
    (failed.length ? ` — ${failed.length} FAILED` : ""));
  failed.forEach((f) => console.log(`  - ${f.name}${f.detail ? ` (${f.detail})` : ""}`));
})().catch((err) => {
  console.error("mobile_render_390 crashed:", err);
  process.exit(1);
});

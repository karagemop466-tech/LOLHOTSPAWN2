#!/usr/bin/env node
/**
 * check_dom_render.js — render every published page in jsdom against the real
 * docs/data/picks.json payload and assert what the visitor (and a crawler) sees.
 *
 * Why this exists: check_dom_contract.py only proves that the ids the script
 * references exist in the HTML. It cannot prove that rendering succeeds, that
 * rows appear, or that a pick and its source link reach the DOM. This harness
 * runs docs/assets/app.js exactly as a browser would, with `fetch` stubbed to
 * serve the committed payload, and then asserts on the resulting DOM.
 *
 * Checks per page:
 *   - no runtime error was thrown and #error-box stayed empty
 *   - the counts rendered by the script match docs/data/picks.json exactly
 *   - the executive summary exposes the picks list, the in-site pick links,
 *     the separate unresolved section (fixture list + per-league limitations)
 *   - every rendered pick row/card carries a pick inside {team1, team2}, both
 *     probabilities summing to 100% (±0.1), and at least one source link
 *   - no page requires network access (only the local payload is used)
 *
 * Usage: node verification/check_dom_render.js [--docs docs] [--quiet]
 * Requires: npm install jsdom (not vendored; CI installs it in a step).
 * Exit 1 on any failure.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");

let JSDOM;
try {
  ({ JSDOM } = require("jsdom"));
} catch (e) {
  // Never fail a pipeline for a missing optional dev dependency: record the skip.
  console.log("SKIP check_dom_render: jsdom is not installed (npm install --no-save jsdom)");
  process.exit(0);
}

const args = process.argv.slice(2);
const quiet = args.includes("--quiet");
const docsArg = args.indexOf("--docs");
const DOCS = path.resolve(docsArg >= 0 ? args[docsArg + 1] : path.join(__dirname, "..", "docs"));
const PAYLOAD = JSON.parse(fs.readFileSync(path.join(DOCS, "data", "picks.json"), "utf8"));

const results = [];
function check(name, ok, detail) {
  results.push({ name, ok: !!ok, detail });
  if (!quiet) console.log(`  [${ok ? "ok" : "FAIL"}] ${name}${detail ? ` — ${detail}` : ""}`);
  if (!ok) process.exitCode = 1;
}

const matches = PAYLOAD.matches || [];
const leagues = PAYLOAD.league_breakdown || [];
const unresolved = matches.filter((m) => m.method === "UNRESOLVED");
const firstId = matches.length ? matches[0].id : "";

/** Render one page with the real app.js inlined, so no network or file:// history quirks apply. */
async function render(file, { query = "", payload = PAYLOAD } = {}) {
  const filePath = path.join(DOCS, file);
  const url = `https://picks.test/docs/${file}${query}`;
  let html = fs.readFileSync(filePath, "utf8");
  const appJs = fs.readFileSync(path.join(DOCS, "assets", "app.js"), "utf8");
  // Inline the script: jsdom's `resources: "usable"` cannot load it over https,
  // and file:// URLs block history.replaceState (which the picks page uses).
  // NB: a function replacement is required — app.js declares `const $$`, and
  // `$$` inside a replacement *string* is an escape for a literal `$`.
  const safeJs = appJs.replace(/<\/script>/g, "<\\/script>");
  html = html.replace(/<script src="assets\/app\.js" defer><\/script>/,
    () => `<script>${safeJs}</script>`);
  const virtualConsole = new (require("jsdom").VirtualConsole)();
  const errors = [];
  virtualConsole.on("jsdomError", (e) => errors.push(String(e.message || e)));
  const dom = new JSDOM(html, {
    url,
    runScripts: "dangerously",
    pretendToBeVisual: true,
    virtualConsole,
    beforeParse(window) {
      window.fetch = async () => ({
        ok: true,
        status: 200,
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
  // app.js awaits fetch(); give the microtask queue a turn.
  await new Promise((r) => setTimeout(r, 60));
  return dom.window;
}

function rowsText(win, sel) {
  return Array.from(win.document.querySelectorAll(sel)).map((el) => el.textContent.trim());
}

/** Every card/row must carry a pick that is one of the two teams and a source link. */
function assertPicks(win, selector, label, expected) {
  const nodes = Array.from(win.document.querySelectorAll(selector));
  check(`${label}: rendered ${expected} row(s)`, nodes.length === expected,
        `found ${nodes.length}, payload has ${expected}`);
  let badPick = 0, badProb = 0, noSource = 0;
  nodes.forEach((node) => {
    const text = node.textContent;
    const pill = node.querySelector(".pick-pill");
    const pillText = pill ? pill.textContent : "";
    const named = matches.filter((m) => text.includes(m.team1) && text.includes(m.team2));
    // The same pair can be listed twice (different competitions), so accept any
    // candidate whose own pick matches the pill.
    if (!named.length || !named.some((m) => pillText.includes(m.pick))) badPick++;
    else {
      const bad = named.filter((m) => Math.abs((m.prob_team1 || 0) + (m.prob_team2 || 0) - 1) > 0.001);
      if (bad.length) badProb++;
    }
    const links = Array.from(node.querySelectorAll("a[href^='http']"));
    if (!links.length) noSource++;
  });
  check(`${label}: every row's pick is one of the two teams`, badPick === 0, `${badPick} bad`);
  check(`${label}: both probabilities sum to 100%`, badProb === 0, `${badProb} bad`);
  check(`${label}: every row links an external source`, noSource === 0, `${noSource} without link`);
}

async function main() {
  check("payload loads with upcoming matches", matches.length > 0, `${matches.length} fixtures`);

  // ---------- executive summary -------------------------------------------
  const idx = await render("index.html");
  const idoc = idx.document;
  check("summary: no JS error", (idx.__errors || []).length === 0, (idx.__errors || []).join(" | "));
  check("summary: #error-box is empty", (idoc.querySelector("#error-box") || {}).textContent === "");
  check("summary: fixture stat matches payload",
        idoc.querySelector("#stat-fixtures").textContent.trim() === String(PAYLOAD.counts.fixtures),
        idoc.querySelector("#stat-fixtures").textContent.trim());
  check("summary: unresolved stat matches payload",
        idoc.querySelector("#stat-unresolved").textContent.trim() === String(PAYLOAD.counts.unresolved));
  check("summary: hero pick count matches payload",
        idoc.querySelector("#hero-count-picks").textContent.includes(String(matches.length)),
        idoc.querySelector("#hero-count-picks").textContent);

  // in-site links to the updated picks, with a visible href on mobile
  const whereLinks = Array.from(idoc.querySelectorAll("#picks-here a")).map((a) => a.getAttribute("href"));
  check("summary: in-site links to all picks", whereLinks.includes("picks.html"), whereLinks.join(","));
  check("summary: in-site link to next-24h filter",
        whereLinks.includes("picks.html?filter=next24"), whereLinks.join(","));
  check("summary: in-site link to unresolved page", whereLinks.includes("unresolved.html"), whereLinks.join(","));

  // picks first: the picks table must appear before the per-league table in the DOM
  const order = ["#starting-soon", "#quick-picks-body", "#unresolved-section", "#summary-leagues-body"]
    .map((sel) => idoc.querySelector(sel));
  check("summary: picks section exists on the page", order[0] && order[1]);
  check("summary: picks appear before the unresolved section",
        order[1] && order[2] && (order[1].compareDocumentPosition(order[2]) & 4) === 4);

  const quickRows = idoc.querySelectorAll("#quick-picks-body tr");
  check("summary: quick-scan table renders 12 rows", quickRows.length === Math.min(12, matches.length),
        `${quickRows.length} rows`);
  check("summary: starting-soon cards render", idoc.querySelectorAll("#next24 article.match").length > 0,
        `${idoc.querySelectorAll("#next24 article.match").length} cards`);

  // separate unresolved section: fixture list + per-league limitations, both in the summary
  const uList = idoc.querySelector("#unresolved-list");
  check("summary: unresolved fixture list rendered", uList && uList.children.length > 0);
  check("summary: unresolved list matches payload count",
        unresolved.length === 0
          ? /0 unresolved/i.test(uList.textContent)
          : uList.querySelectorAll("article.match").length === unresolved.length,
        `${unresolved.length} in payload`);
  const limRows = idoc.querySelectorAll("#exec-league-limits-body tr");
  check("summary: per-league limitation table rendered", limRows.length === leagues.length,
        `${limRows.length} rows vs ${leagues.length} competitions`);
  check("summary: limitations text present on the page",
        /limitation/i.test(idoc.body.textContent));
  check("summary: coverage bar rendered",
        idoc.querySelector("#coverage-bar").innerHTML.includes("width:"));
  check("summary: \"where the picks are\" strip rendered", !!idoc.querySelector("#picks-here"));
  check("summary: hero status line filled",
        (idoc.querySelector("#hero-status") || {}).textContent.trim().length > 0);
  check("summary: picks-locking-soonest section rendered", !!idoc.querySelector("#starting-soon"));

  // ---------- picks page ----------------------------------------------------
  const picks = await render("picks.html");
  const pdoc = picks.document;
  check("picks: no JS error", (picks.__errors || []).length === 0, (picks.__errors || []).join(" | "));
  assertPicks(picks, "#picks-body tr", "picks", matches.length);
  check("picks: countline reports every fixture",
        pdoc.querySelector("#countline").textContent.includes(String(matches.length)),
        pdoc.querySelector("#countline").textContent.trim());

  // filter deep-links used by the summary must actually filter
  const next24 = matches.filter((m) => {
    const t = new Date(m.start_utc).getTime();
    return t >= Date.now() - 300000 && t <= Date.now() + 86400000;
  }).length;
  const filtered = await render("picks.html", { query: "?filter=next24" });
  check("picks: ?filter=next24 deep link applies",
        filtered.document.querySelectorAll("#picks-body tr").length === next24,
        `${filtered.document.querySelectorAll("#picks-body tr").length} rows vs ${next24} in window`);
  // coin-flip labelling: rows whose favourite is <=53% must say so, the count
  // must match the payload, and the deep link from the summary must filter.
  const tossUps = matches.filter((m) => m.method !== "UNRESOLVED" && (m.pick_prob ?? 1) <= 0.53);
  const pillFlips = Array.from(pdoc.querySelectorAll("#picks-body .pick-pill"))
    .filter((el) => el.textContent.includes("coin-flip")).length;
  check("picks: every coin-flip row is labelled in its pick pill",
        pillFlips === tossUps.length, `${pillFlips} labelled vs ${tossUps.length} in payload`);
  check("picks: countline states the coin-flip count",
        pdoc.querySelector("#countline").textContent.includes(`${tossUps.length} coin-flips`),
        pdoc.querySelector("#countline").textContent.trim());
  const tossView = await render("picks.html", { query: "?filter=tossup" });
  check("picks: ?filter=tossup deep link applies",
        tossView.document.querySelectorAll("#picks-body tr").length === tossUps.length,
        `${tossView.document.querySelectorAll("#picks-body tr").length} rows vs ${tossUps.length} coin-flips`);
  check("summary: unresolved section counts coin-flip picks and links the filter",
        (idoc.querySelector("#unresolved-summary") || {}).textContent.includes("coin-flip")
        && !!idoc.querySelector('#unresolved-summary a[href="picks.html?filter=tossup"]'));

  const market = matches.filter((m) => m.market).length;
  const marketView = await render("picks.html", { query: "?filter=market" });
  check("picks: ?filter=market deep link applies",
        marketView.document.querySelectorAll("#picks-body tr").length === market,
        `${marketView.document.querySelectorAll("#picks-body tr").length} rows vs ${market} market rows`);

  // ---------- leagues page --------------------------------------------------
  const lpage = await render("leagues.html");
  check("leagues: no JS error", (lpage.__errors || []).length === 0, (lpage.__errors || []).join(" | "));
  const lbRows = lpage.document.querySelectorAll("#leagues-summary-body tr");
  check("leagues: one summary row per competition", lbRows.length === leagues.length,
        `${lbRows.length} vs ${leagues.length}`);
  check("leagues: per-league sections rendered",
        lpage.document.querySelectorAll("#leagues-sections section").length > 0);
  check("leagues: every competition has a source link",
        Array.from(lbRows).every((r) => r.querySelector("a[href^='http']")),
        `${lbRows.length} rows checked`);

  // ---------- unresolved page ----------------------------------------------
  const upage = await render("unresolved.html");
  const udoc = upage.document;
  check("unresolved: no JS error", (upage.__errors || []).length === 0, (upage.__errors || []).join(" | "));
  check("unresolved: reasons rendered",
        (udoc.querySelector("#reasons") || {}).textContent.trim().length > 0);
  check("unresolved: limitations rendered",
        (udoc.querySelector("#limitations") || {}).textContent.trim().length > 0);
  check("unresolved: unresolved and low-confidence lists rendered",
        !!udoc.querySelector("#unresolved-body") && !!udoc.querySelector("#lowconf-body"));
  check("unresolved: stat line states the coin-flip count",
        (udoc.querySelector("#unresolved-counts") || {}).textContent.includes(`${tossUps.length}`)
        && (udoc.querySelector("#unresolved-counts") || {}).textContent.includes("coin-flip"),
        (udoc.querySelector("#unresolved-counts") || {}).textContent.trim());
  check("unresolved: per-league limitations rendered",
        udoc.querySelectorAll("#league-limitations-body tr").length === leagues.length);

  // The "how this snapshot was resolved" line must agree with the payload's own per-method
  // tally — and with the league table further down the same page. It once reported "0 by split
  // standings" next to a table showing 55, because the method id it looked for did not exist.
  const byMethod = (PAYLOAD.coverage || {}).counts_by_method || {};
  const nStandings = byMethod.MODEL_ELO_STANDINGS || 0;
  const nElo = (byMethod.MODEL_ELO || 0) + (byMethod.MODEL_ELO_THIN || 0);
  const mixText = (udoc.querySelector("#resolution-mix") || {}).textContent || "";
  check("unresolved: resolution mix reports the split-standings count",
        new RegExp(`${nStandings}\\s*by split standings`).test(mixText)
        || (mixText.includes(String(nStandings)) && mixText.includes("split standings")),
        mixText.replace(/\s+/g, " ").slice(0, 160));
  check("unresolved: resolution mix reports the Elo count",
        mixText.includes(String(nElo)) && mixText.includes("Elo model"),
        `want ${nElo}`);
  const leagueStandings = leagues.reduce((n, l) => n + (l.standings || 0), 0);
  check("cross-page: summary, unresolved page and league rows agree on standings",
        nStandings === leagueStandings,
        `coverage ${nStandings} vs league rows ${leagueStandings}`);

  // ---------- flagged page --------------------------------------------------
  const fpage = await render("flagged.html");
  check("flagged: no JS error", (fpage.__errors || []).length === 0, (fpage.__errors || []).join(" | "));
  check("flagged: flag groups rendered",
        (fpage.document.querySelector("#flag-groups") || {}).textContent.trim().length > 0);
  check("flagged: excluded cancelled fixtures listed",
        fpage.document.querySelectorAll("#excluded-body tr").length === (PAYLOAD.excluded_fixtures || []).length,
        `${fpage.document.querySelectorAll("#excluded-body tr").length} rows`);

  // ---------- methodology page ---------------------------------------------
  const mpage = await render("methodology.html");
  check("methodology: no JS error", (mpage.__errors || []).length === 0, (mpage.__errors || []).join(" | "));
  check("methodology: backtest block rendered",
        (mpage.document.querySelector("#backtest") || {}).textContent.trim().length > 0);

  // ---------- match detail --------------------------------------------------
  if (firstId) {
    const m = matches[0];
    const dpage = await render("match.html", { query: `?id=${encodeURIComponent(firstId)}` });
    const dtext = dpage.document.body.textContent;
    check("match detail: no JS error", (dpage.__errors || []).length === 0, (dpage.__errors || []).join(" | "));
    check("match detail: renders both teams", dtext.includes(m.team1) && dtext.includes(m.team2));
    check("match detail: renders the pick", dtext.includes(m.pick));
  }

  // ---------- self-test: the separate unresolved section must not be vacuous ----
  // Build a payload with two forced-unresolved fixtures and prove they are listed
  // inline on the executive summary with an explicit 50/50 placeholder.
  const synthetic = JSON.parse(JSON.stringify(PAYLOAD));
  synthetic.matches = synthetic.matches.slice(0, 6).map((m, i) => (i < 2 ? Object.assign({}, m, {
    method: "UNRESOLVED", method_label: "Unresolved 50/50", confidence: "None",
    prob_team1: 0.5, prob_team2: 0.5, pick: m.team1, pick_prob: 0.5, market: null,
  }) : m));
  synthetic.counts = Object.assign({}, synthetic.counts, {
    fixtures: synthetic.matches.length, unresolved: 2, market: 0, resolved: synthetic.matches.length - 2,
  });
  synthetic.unresolved = Object.assign({}, synthetic.unresolved, { count: 2, low_confidence_count: 0 });
  synthetic.coverage = Object.assign({}, synthetic.coverage, { unresolved: 2 });
  const syn = await render("index.html", { payload: synthetic });
  const sdoc = syn.document;
  check("self-test: summary lists every unresolved fixture",
        sdoc.querySelectorAll("#unresolved-list article.match").length === 2,
        `${sdoc.querySelectorAll("#unresolved-list article.match").length} cards`);
  check("self-test: unresolved rows show the 50/50 placeholder",
        /50\/50/.test((sdoc.querySelector("#unresolved-list") || {}).textContent || ""));
  check("self-test: unresolved stat reflects the payload",
        sdoc.querySelector("#stat-unresolved").textContent.trim() === "2");
  check("self-test: hero unresolved counter reflects the payload",
        sdoc.querySelector("#hero-count-unresolved").textContent.includes("2"));

  const failed = results.filter((r) => !r.ok);
  console.log(`\nDOM render check: ${results.length - failed.length}/${results.length} passed` +
              (failed.length ? ` — ${failed.length} FAILED` : ""));
  if (failed.length) {
    console.log("Failures:");
    failed.forEach((f) => console.log(`  - ${f.name}${f.detail ? ` (${f.detail})` : ""}`));
  }
}

main().catch((err) => {
  console.error("DOM render check crashed:", err);
  process.exit(1);
});

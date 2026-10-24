#!/usr/bin/env node
/**
 * check_dom_render.js — render every site page against the published payload
 * and assert that each page actually produced its content.
 *
 * check_dom_contract.py proves the ids the shared JS looks up exist in the
 * HTML. This proves the opposite and complementary thing: that the JS, run
 * against the real docs/data/picks.json, actually fills those containers.
 * A page that renders but leaves its content containers empty (a silent
 * front-end regression) is caught here.
 *
 * Requires jsdom. Skips with exit code 0 (and a clear notice) when jsdom is
 * not installed, so the workflow stays green on a runner without it.
 */
"use strict";

const fs = require("fs");
const path = require("path");

const ROOT = path.dirname(__dirname);
const DOCS = path.join(ROOT, "docs");

const PAGES = ["index.html", "picks.html", "leagues.html", "unresolved.html",
               "flagged.html", "methodology.html"];

// Containers that must contain rendered content once app.js has run.
const REQUIRED = {
  "index.html": ["#stat-fixtures", "#coverage-text", "#next24", "#unresolved-summary",
                  "#featured", "#summary-leagues-body", "#quick-picks-body"],
  "picks.html": ["#picks-body", "#countline"],
  "leagues.html": ["#leagues-summary-body", "#leagues-sections"],
  "unresolved.html": ["#unresolved-body", "#lowconf-body",
                      "#league-limitations-body", "#limitations", "#reasons"],
  "flagged.html": ["#flagged-body", "#flag-groups"],
  "methodology.html": ["#backtest"],
};

let JSDOM;
let VirtualConsole;
try {
  ({ JSDOM, VirtualConsole } = require("jsdom"));
} catch (err) {
  console.log("SKIP: jsdom is not installed - DOM render check not run.");
  process.exit(0);
}

function loadPage(page) {
  const html = fs.readFileSync(path.join(DOCS, page), "utf8");
  const errors = [];
  const vc = new VirtualConsole();
  vc.on("jsdomError", (e) => errors.push(String((e && e.message) || e)));
  const dom = new JSDOM(html, {
    runScripts: "dangerously",
    url: `https://karagemop466-tech.github.io/LOLHOTSPAWN2/docs/${page}`,
    virtualConsole: vc,
    beforeParse(window) {
      window.fetch = async (u) => {
        const rel = String(u).replace(/^.*\/docs\//, "");
        const p = path.join(DOCS, rel);
        if (!fs.existsSync(p)) return { ok: false, status: 404, json: async () => ({}) };
        return { ok: true, status: 200, json: async () => JSON.parse(fs.readFileSync(p, "utf8")) };
      };
    },
  });
  const { window } = dom;
  window.eval(fs.readFileSync(path.join(DOCS, "assets", "app.js"), "utf8"));
  window.document.dispatchEvent(new window.Event("DOMContentLoaded", { bubbles: true }));
  return { dom, window, errors };
}

(async () => {
  let failures = 0;
  for (const page of PAGES) {
    const { dom, window, errors } = loadPage(page);
    await new Promise((r) => setTimeout(r, 700));
    const doc = window.document;
    // The trailing "main > .loading" block is the deliberate no-JS fallback;
    // only a live loading spinner means app.js did not finish.
    const liveLoading = [...doc.querySelectorAll(".loading")]
      .filter((e) => !e.parentElement || e.parentElement.tagName !== "MAIN").length;
    const empty = (REQUIRED[page] || []).filter((sel) => {
      const el = doc.querySelector(sel);
      return el && !el.innerHTML.trim();
    });
    const textLen = (doc.body.textContent || "").length;
    const ok = errors.length === 0 && liveLoading === 0 && empty.length === 0 && textLen > 500;
    if (!ok) failures++;
    console.log(`${ok ? "PASS" : "FAIL"} ${page.padEnd(16)} text=${String(textLen).padStart(6)}` +
                ` liveLoading=${liveLoading} empty=${JSON.stringify(empty)}` +
                (errors.length ? ` errors=${JSON.stringify(errors.slice(0, 2))}` : ""));
    dom.window.close();
  }
  console.log(`\n${failures === 0 ? "ALL PAGES RENDER CORRECTLY" : `${failures} PAGE(S) FAILED`}`);
  process.exit(failures ? 1 : 0);
})();

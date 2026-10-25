#!/usr/bin/env node
/** Real browser mobile layout/interaction audit. Optional developer dependencies:
 * npm i --no-save --no-package-lock playwright @sparticuz/chromium
 * Start: python3 -m http.server 8080 --bind 0.0.0.0
 * Run: node verification/check_mobile_browser.cjs [http://127.0.0.1:8080/docs/]
 * No browser binaries, screenshots, or npm dependencies are committed.
 */
const {chromium} = require('playwright');
const fs = require('node:fs');
const binaryModule = require('@sparticuz/chromium');
const binary = binaryModule.default || binaryModule;
const firstMatch = require('../docs/data/picks.json').matches[0];
const firstId = firstMatch.id;
const base = process.argv[2] || 'http://127.0.0.1:8080/docs/';
(async () => {
  // The npm-distributed Linux browser bundles NSS/NSPR for minimal environments.
  const libs = await binaryModule.inflate(require('path').resolve('node_modules/@sparticuz/chromium/bin/al2023.tar.br'));
  const browser = await chromium.launch({headless:true, executablePath:await binary.executablePath(), args:binary.args,
    env:{...process.env, LD_LIBRARY_PATH: `${libs}/lib:${process.env.LD_LIBRARY_PATH || ''}`}});
  const results = [];
  let failed = false;
  function check(name, ok, detail) {
    results.push({name, pass:!!ok, detail});
    console.log(`[${ok ? 'PASS' : 'FAIL'}] ${name}${detail ? ': '+detail : ''}`);
    if (!ok) failed = true;
  }
  try {
    for (const width of [320,390,768,1280]) {
      const context = await browser.newContext({viewport:{width,height:844},isMobile:width<768});
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      for (const file of ['index.html','picks.html','leagues.html','unresolved.html','flagged.html','methodology.html',`match.html?id=${encodeURIComponent(firstId)}`]) {
        await page.goto(base+file);
        await page.waitForFunction(() => document.querySelector('#updated')?.textContent !== 'Loading…');
        await page.evaluate(() => document.fonts.ready);
        const size = await page.evaluate(() => ({client:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth}));
        check(`${width}px ${file}: no document overflow`,size.scroll<=size.client+1,JSON.stringify(size));
        check(`${width}px ${file}: no load error`,(await page.locator('#error-box').textContent())==='');
        if (file==='index.html') {
          const link = page.locator('.hero-actions a[href="picks.html"]');
          const box = await link.boundingBox();
          check(`${width}px summary: primary picks button above fold`, box && box.y+box.height<784);
          check(`${width}px summary: primary touch target >=44px`,box && box.height>=44);
          await link.click();
          await page.waitForSelector('#picks-body tr');
          check(`${width}px summary: picks button opens populated list`, (await page.locator('#picks-body .pick-pill').count())>0);
          if (width===390 && process.env.MOBILE_SCREENSHOT) await page.screenshot({path:process.env.MOBILE_SCREENSHOT,fullPage:false});
        }
        if (file==='picks.html') {
          const all = await page.locator('#picks-body tr').count();
          await page.locator('#q').fill(firstMatch.team1);
          await page.waitForFunction(n => document.querySelectorAll('#picks-body tr').length < n, all);
          const found = await page.locator('#picks-body tr').count();
          check(`${width}px picks: team search narrows list`,found>0 && found<all,`${found}/${all}`);
        }
      }
      check(`${width}px: no browser JS errors`,errors.length===0,errors.join('; '));
      // Single-process serverless Chromium can exit when its last context closes.
      // Close all contexts with the browser after the final viewport instead.
    }
  } finally {await browser.close();}
  if (process.env.MOBILE_REPORT) fs.writeFileSync(process.env.MOBILE_REPORT,JSON.stringify({checked_at:new Date().toISOString(),base,results},null,2)+'\n');
  console.log(`Mobile browser audit: ${results.filter(r=>r.pass).length}/${results.length} passed`);
  process.exitCode = failed ? 1 : 0;
})().catch(e=>{console.error(e);process.exit(1)});

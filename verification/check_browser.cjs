#!/usr/bin/env node
/* Real CSS/layout regression audit, distinct from jsdom's DOM-only tests.
 * npm i --no-save --no-package-lock playwright-core @sparticuz/chromium jsdom
 * node verification/check_browser.cjs
 * Optional: CHROMIUM_PATH=/path/to/chromium; PREVIEW_URL=http://127.0.0.1:8000/
 * An ephemeral static server is started automatically unless PREVIEW_URL is set.
 * Browser packages/binaries are never committed.
 */
const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

async function main() {
  let executablePath = process.env.CHROMIUM_PATH;
  if (!executablePath) {
    const bundle = require('@sparticuz/chromium');
    // The sandbox is not Lambda, but lacks NSS. Extract only the bundled libs
    // locally; no apt install or extra host download is needed.
    if (process.platform === 'linux' && process.arch === 'x64') {
      const root = path.dirname(require.resolve('@sparticuz/chromium'));
      const libs = await bundle.inflate(path.resolve(root, '../bin/al2023.tar.br'));
      bundle.setupLambdaEnvironment(path.join(libs, 'lib'));
    }
    executablePath = await bundle.default.executablePath();
  }
  const browser = await chromium.launch({ executablePath, headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'] });
  const engine = browser.version();
  let server;
  let base = process.env.PREVIEW_URL;
  if (!base) {
    const root = path.resolve(__dirname, '../docs');
    server = require('http').createServer((req, res) => {
      const name = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
      const file = path.resolve(root, '.' + (name === '/' ? '/index.html' : name));
      if (!file.startsWith(root + path.sep)) { res.writeHead(403); res.end(); return; }
      fs.readFile(file, (error, content) => {
        if (error) { res.writeHead(404); res.end(); return; }
        const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json' };
        res.setHeader('Content-Type', mime[path.extname(file)] || 'application/octet-stream');
        res.end(content);
      });
    });
    await new Promise(resolve => server.listen(0, '0.0.0.0', resolve));
    base = `http://127.0.0.1:${server.address().port}/`;
  }
  const results = [];
  try {
    const payload = JSON.parse(fs.readFileSync(path.join(__dirname, '../docs/data/picks.json')));
    const match = payload.matches[0].id;
    for (const width of [320, 390, 768, 1280]) {
      const page = await browser.newPage({ viewport: { width, height: 844 } });
      for (const file of ['index.html', 'picks.html', 'leagues.html', 'unresolved.html', 'flagged.html', 'methodology.html', `match.html?id=${match}`]) {
        const errors = [];
        const recordError = e => errors.push(e.message);
        page.on('pageerror', recordError);
        const response = await page.goto(new URL(file, base).href);
        await page.waitForFunction(() => document.querySelector('#updated')?.textContent.includes('Updated'));
        const layout = await page.evaluate(() => ({
          scroll: document.documentElement.scrollWidth,
          loading: [...document.querySelectorAll('.loading')].filter(x => x.offsetHeight > 0).map(x => x.textContent),
          header: document.querySelector('header').getBoundingClientRect().height,
          minMobileNavHeight: Math.min(...[...document.querySelectorAll('.bottom-nav a')].map(a => a.getBoundingClientRect().height)),
        }));
        const pass = response.ok() && layout.scroll <= width && !errors.length && !layout.loading.length
          && layout.header > 40 && (width > 768 || layout.minMobileNavHeight >= 44);
        results.push({ width, path: file, ...layout, errors, pass });
        console.log(`${pass ? 'PASS' : 'FAIL'} ${width}px ${file} scrollWidth=${layout.scroll}`);
        page.off('pageerror', recordError);
      }
      await page.close();
    }
  } finally {
    await browser.close();
    if (server) await new Promise(resolve => server.close(resolve));
  }
  fs.writeFileSync(process.env.BROWSER_REPORT || path.join(__dirname, 'mobile-browser.json'), JSON.stringify({
    checked_at: new Date().toISOString(), engine: `Chromium ${engine} via Playwright`,
    scope: 'Actual CSS/layout and runtime audit, not a screen-reader or official source verification audit.',
    results,
  }, null, 2) + '\n');
  if (results.some(r => !r.pass)) process.exitCode = 1;
}
main().catch(e => { console.error(e); process.exitCode = 1; });

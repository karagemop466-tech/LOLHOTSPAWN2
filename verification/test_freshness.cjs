// Fail closed on bad timestamps; execute the real helper, not a test copy.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const app = fs.readFileSync('docs/assets/app.js', 'utf8');
const fn = app.match(/  function isFresh\(d\) \{[\s\S]*?\n  \}/)[0];
const fresh = vm.runInNewContext(`(${fn.trim()})`, { Date, Number });
const now = Date.now();
const iso = n => new Date(now + n * 3600000).toISOString();
const cases = [
  ['recent', {generated_at: iso(-1), stale_after_utc: iso(7)}, true],
  ['missing expiry', {generated_at: iso(-1)}, false],
  ['missing generation', {stale_after_utc: iso(7)}, false],
  ['invalid generation', {generated_at:'bad', stale_after_utc:iso(7)}, false],
  ['invalid expiry', {generated_at:iso(-1), stale_after_utc:'bad'}, false],
  ['expired', {generated_at:iso(-7), stale_after_utc:iso(-1)}, false],
  ['over eight hours despite deadline', {generated_at:iso(-9), stale_after_utc:iso(2)}, false],
  ['future generation', {generated_at:iso(1), stale_after_utc:iso(7)}, false],
  ['deadline before generation', {generated_at:iso(-1), stale_after_utc:iso(-2)}, false],
];
for (const [name, data, expected] of cases) {
  assert.equal(fresh(data), expected, name);
  console.log('PASS', name);
}
assert.ok(!app.includes('fixtures have a verified pick'));
assert.ok(app.includes('Recent snapshot · not live odds'));
console.log('PASS honest snapshot and estimate labels');

#!/usr/bin/env node
/* Manual "request indexing" helper.
 *
 * Prints the small set of match URLs whose content meaningfully changed, so you can submit
 * them by hand in Google Search Console. It deliberately does NOT call any indexing API and
 * does NOT resubmit the whole site: mass automated submission is the behaviour that got
 * BRYME's thin fixture pages ignored in the first place.
 *
 *   node scripts/request-indexing.js --since 2026-08-15
 *   node scripts/request-indexing.js --since 2026-08-15 --limit 10
 *
 * Google will find these on its own from sitemap.xml. Use this only for pages worth
 * nudging - a big fixture going live, or a result added to an already-indexed preview.
 */
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..');
const cfg = JSON.parse(fs.readFileSync(path.join(root, 'site.config.json'), 'utf8'));
const base = (cfg.siteUrl || '').replace(/\/$/, '');

const args = process.argv.slice(2);
const get = f => { const i = args.indexOf(f); return i > -1 ? args[i + 1] : undefined; };
const since = get('--since');
const limit = Number(get('--limit') || 25);
if (!since || !/^\d{4}-\d{2}-\d{2}$/.test(since)) {
  console.error('Usage: node scripts/request-indexing.js --since YYYY-MM-DD [--limit N]');
  process.exit(1);
}

const sm = fs.readFileSync(path.join(root, 'sitemap.xml'), 'utf8');
const entries = [...sm.matchAll(/<url><loc>([^<]+)<\/loc>(?:<lastmod>([^<]+)<\/lastmod>)?<\/url>/g)]
  .map(m => ({ url: m[1], lastmod: m[2] || null }))
  .filter(e => e.lastmod && e.lastmod >= since)
  .sort((a, b) => b.lastmod.localeCompare(a.lastmod));

if (!entries.length) {
  console.log(`No indexable pages changed on or after ${since}.`);
  process.exit(0);
}
console.log(`${entries.length} page(s) changed on or after ${since}. Showing ${Math.min(limit, entries.length)}.\n`);
entries.slice(0, limit).forEach(e => console.log(`  ${e.lastmod}  ${e.url}`));
if (entries.length > limit) console.log(`  ... and ${entries.length - limit} more`);

console.log(`
How to use this:
  1. Open Google Search Console for ${base || 'your property'}.
  2. Paste a URL into the URL Inspection tool.
  3. Choose "Request indexing" only if the page genuinely changed.

Do not submit every URL on this list every day. The sitemap already advertises the
lastmod dates above and normal recrawling will pick them up. Manual requests are for
pages where the delay actually matters.`);

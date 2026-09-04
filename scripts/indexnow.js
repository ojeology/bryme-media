#!/usr/bin/env node
/* Ping IndexNow with URLs that actually changed.
 *
 * IndexNow is an open protocol supported by Bing, Yandex and Seznam. It is free, has no
 * per-day cap, and no content-type restriction. Google does NOT participate, so this does
 * nothing for Google rankings - it is Bing and friends only.
 *
 *   node scripts/indexnow.js --since 2026-08-17          # dry run, shows what would be sent
 *   node scripts/indexnow.js --since 2026-08-17 --send   # actually submit
 *   node scripts/indexnow.js --url https://.../page/ --send
 *
 * URLs are taken from sitemap.xml lastmod, the same source request-indexing.js uses, so a
 * page is only ever submitted when its content genuinely changed.
 */
const fs = require('fs'), path = require('path'), https = require('https');
const root = path.resolve(__dirname, '..');
const cfg = JSON.parse(fs.readFileSync(path.join(root, 'site.config.json'), 'utf8'));
const base = (cfg.siteUrl || '').replace(/\/$/, '');
const host = base.replace(/^https?:\/\//, '');
const key = cfg.indexNowKey;

const args = process.argv.slice(2);
const get = f => { const i = args.indexOf(f); return i > -1 ? args[i + 1] : undefined; };
const has = f => args.includes(f);

if (!key) { console.error('No indexNowKey in site.config.json. Generate one first.'); process.exit(1); }
const keyFile = path.join(root, key + '.txt');
if (!fs.existsSync(keyFile)) { console.error(`Key file missing: /${key}.txt must be served from the site root.`); process.exit(1); }
if (fs.readFileSync(keyFile, 'utf8').trim() !== key) { console.error('Key file contents do not match the key.'); process.exit(1); }

let urls = [];

if (get('--paths')) {
  urls = get('--paths').split(',').map(s => s.trim()).filter(Boolean)
    .map(s => s.startsWith('http') ? s : base + (s.startsWith('/') ? s : '/' + s));
} else if (get('--url')) {
  urls = [get('--url')];
} else if (has('--all')) {
  const readSm = f => fs.existsSync(path.join(root, f)) ? fs.readFileSync(path.join(root, f), 'utf8') : '';
  const sm = readSm('sitemap.xml') + readSm('news-sitemap.xml');
  urls = [...sm.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => m[1]);
  urls = [...new Set(urls)];
} else {
  const since = get('--since');
  if (!since || !/^\d{4}-\d{2}-\d{2}$/.test(since)) {
    console.error('Usage: node scripts/indexnow.js --all [--send]  OR  --since YYYY-MM-DD [--send]  OR  --url <url> --send');
    process.exit(1);
  }
  const readSm = f => fs.existsSync(path.join(root, f)) ? fs.readFileSync(path.join(root, f), 'utf8') : '';
  const sm = readSm('sitemap.xml') + readSm('news-sitemap.xml');
  urls = [...sm.matchAll(/<url>\s*<loc>([^<]+)<\/loc>\s*(?:<lastmod>([^<]+)<\/lastmod>)?/g)]
    .filter(m => m[2] && m[2] >= since).map(m => m[1]);
  urls = [...new Set(urls)];
}

if (!urls.length) { console.log('Nothing changed on or after that date. Nothing to submit.'); process.exit(0); }
if (urls.length > 10000) { console.error('IndexNow accepts at most 10,000 URLs per request.'); process.exit(1); }

console.log(urls.length + ' URL(s) to submit to IndexNow (Bing / Yandex / Seznam)');
if (urls.length <= 30) urls.forEach(u => console.log('  ' + u));
else console.log('  (list omitted — ' + urls.length + ' URLs)');

if (!has('--send')) {
  console.log(`\nDry run. Add --send to actually submit.`);
  console.log(`Key file: ${base}/${key}.txt`);
  process.exit(0);
}

const payload = JSON.stringify({ host, key, keyLocation: `${base}/${key}.txt`, urlList: urls });
const req = https.request({
  hostname: 'api.indexnow.org', path: '/indexnow', method: 'POST',
  headers: { 'Content-Type': 'application/json; charset=utf-8', 'Content-Length': Buffer.byteLength(payload) }
}, res => {
  let body = '';
  res.on('data', d => body += d);
  res.on('end', () => {
    const ok = res.statusCode === 200 || res.statusCode === 202;
    console.log(`\nIndexNow responded ${res.statusCode}${body ? ': ' + body.slice(0, 200) : ''}`);
    if (ok) console.log('Accepted. Bing and the other participating engines will fetch these in their own time.');
    else if (res.statusCode === 403) console.log('403 usually means the key file is not reachable at the URL above. Check it is deployed.');
    else if (res.statusCode === 422) console.log('422 usually means a URL does not belong to the declared host.');
    process.exit(ok ? 0 : 1);
  });
});
req.on('error', e => { console.error('Request failed: ' + e.message); process.exit(1); });
req.write(payload);
req.end();

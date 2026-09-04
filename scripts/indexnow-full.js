#!/usr/bin/env node
/* One-shot IndexNow submission of the FULL sitemap URL list (Bing + Yandex + Seznam). */
const fs = require('fs'), path = require('path'), https = require('https');
const root = path.resolve(__dirname, '..');
const cfg = JSON.parse(fs.readFileSync(path.join(root, 'site.config.json'), 'utf8'));
const base = (cfg.siteUrl || '').replace(/\/$/, '');
const host = base.replace(/^https?:\/\//, '');
const key = cfg.indexNowKey;

function readUrls(file) {
  if (!fs.existsSync(path.join(root, file))) return [];
  const sm = fs.readFileSync(path.join(root, file), 'utf8');
  return [...sm.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => m[1]);
}

const urls = [...new Set([...readUrls('sitemap.xml'), ...readUrls('news-sitemap.xml')])];
console.log('URLs to submit:', urls.length);

const payload = {
  host,
  key,
  keyLocation: `${base}/${key}.txt`,
  urlList: urls,
};

const body = JSON.stringify(payload);
const req = https.request({
  hostname: 'api.indexnow.org',
  path: '/indexnow',
  method: 'POST',
  headers: { 'Content-Type': 'application/json; charset=utf-8', 'Content-Length': Buffer.byteLength(body) },
}, res => {
  let data = '';
  res.on('data', c => data += c);
  res.on('end', () => {
    console.log('HTTP', res.statusCode, data.slice(0, 300));
    if (res.statusCode === 200 || res.statusCode === 202) {
      console.log('SUCCESS: Bing (and partners) will crawl these URLs.');
    } else {
      console.log('CHECK: non-2xx response — see payload/body above.');
    }
  });
});
req.on('error', e => { console.error('ERROR', e.message); process.exit(1); });
req.write(body);
req.end();

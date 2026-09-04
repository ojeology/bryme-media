#!/usr/bin/env node
/* Static link integrity check for BRYME.
   Crawls every generated .html page (excluding legacy/) and verifies every
   internal href/src resolves to a real file. Prints a summary. */
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..');
const config = JSON.parse(fs.readFileSync(path.join(root, 'site.config.json'), 'utf8'));
const base = String(config.siteUrl).replace(/\/$/, '');

const files = [];
(function walk(dir) {
  if (dir.includes(path.join('legacy'))) return;
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p);
    else if (e.name.endsWith('.html')) files.push(p);
  }
})(root);

let checked = 0, broken = 0, skipped = 0;
const brokenList = [];
const hrefRe = /(?:href|src)="([^"]+)"/g;
for (const file of files) {
  const html = fs.readFileSync(file, 'utf8');
  const relRoot = path.relative(root, file).split(path.sep).slice(0, -1);
  let m;
  while ((m = hrefRe.exec(html))) {
    let raw = m[1];
    if (!raw || raw.startsWith('#') || raw.startsWith('mailto:') || raw.startsWith('tel:') || raw.startsWith('wa.me') || raw.startsWith('data:')) { skipped++; continue; }
    if (/^https?:\/\//i.test(raw)) {
      if (raw.startsWith(base)) raw = raw.slice(base.length);
      else { skipped++; continue; } // external link
    }
    checked++;
    let target;
    if (raw.startsWith('/')) target = path.join(root, raw);
    else target = path.resolve(path.join(root, ...relRoot), raw);
    target = target.split('#')[0].split('?')[0];
    if (!fs.existsSync(target)) { broken++; brokenList.push({ file: path.relative(root, file), link: raw }); }
  }
}
// sitemap + robots check
for (const p of ['sitemap.xml', 'robots.txt', 'assets/site.css', 'assets/site-app.js', 'manifest.webmanifest']) {
  if (!fs.existsSync(path.join(root, p))) { broken++; brokenList.push({ file: 'root', link: p }); }
}
console.log(`Checked ${checked} internal links across ${files.length} pages.`);
console.log(`Broken: ${broken}. Skipped (external/anchors): ${skipped}.`);
if (brokenList.length) {
  brokenList.slice(0, 40).forEach(b => console.log('  BROKEN:', b.file, '->', b.link));
}
process.exit(broken ? 1 : 0);

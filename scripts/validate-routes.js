#!/usr/bin/env node
/* Checks that generated same-site links point at files GitHub Pages can serve. */
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..');
const config = JSON.parse(fs.readFileSync(path.join(root, 'site.config.json')));
const base = config.siteUrl.replace(/\/$/, '');
const pages = [];
function walk(dir) { for (const entry of fs.readdirSync(dir, {withFileTypes:true})) { if (entry.name === '.git') continue; const full = path.join(dir, entry.name); if (entry.isDirectory()) walk(full); else if (entry.name === 'index.html' || entry.name === '404.html') pages.push(full); } }
walk(root);
const broken = [];
for (const page of pages) {
  // Dynamic search-result templates are JavaScript strings, not static anchor targets.
  const html = fs.readFileSync(page, 'utf8').replace(/<script[\s\S]*?<\/script>/gi, '');
  for (const href of html.matchAll(/href="([^"]+)"/g)) {
    const value = href[1];
    if (!value.startsWith(base + '/')) continue;
    const relative = value.slice(base.length + 1).replace(/\?.*$/, '');
    const destination = path.join(root, relative);
    if (!fs.existsSync(destination) && !fs.existsSync(path.join(destination, 'index.html'))) broken.push({page:path.relative(root,page), href:value});
  }
}
const report = { checkedPages:pages.length, brokenLinks:broken.length, records:broken };
fs.mkdirSync(path.join(root, 'reports'), {recursive:true});
fs.writeFileSync(path.join(root, 'reports', 'route-audit.json'), JSON.stringify(report, null, 2)+'\n');
if (broken.length) { console.error(`Found ${broken.length} broken generated internal links.`); process.exitCode = 1; } else console.log(`Validated ${pages.length} generated routes; no broken generated internal links.`);

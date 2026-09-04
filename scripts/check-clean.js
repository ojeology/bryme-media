#!/usr/bin/env node
/* Guard against shipping merge-conflict debris. Runs over source and generated output.
 * This exists because conflict markers landed inside a CSS template literal twice: the
 * JavaScript parsed fine, the build exited 0, and the markers went out in site.css. */
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..');
const MARKER = /^(<{7} |={7}$|>{7} )/m;
const targets = ['scripts', 'content', 'tests', 'docs', 'assets'];
let bad = [];
const walk = d => {
  for (const e of fs.readdirSync(d, {withFileTypes: true})) {
    const p = path.join(d, e.name);
    if (e.isDirectory()) { if (e.name !== '.git' && e.name !== 'node_modules') walk(p); continue; }
    if (!/\.(js|json|css|md|html)$/.test(e.name)) continue;
    const t = fs.readFileSync(p, 'utf8');
    if (MARKER.test(t)) bad.push(path.relative(root, p));
  }
};
targets.forEach(t => { const d = path.join(root, t); if (fs.existsSync(d)) walk(d); });
for (const f of ['index.html', 'sitemap.xml', 'robots.txt']) {
  const p = path.join(root, f);
  if (fs.existsSync(p) && MARKER.test(fs.readFileSync(p, 'utf8'))) bad.push(f);
}
if (bad.length) {
  console.error('MERGE CONFLICT DEBRIS in ' + bad.length + ' file(s):');
  bad.forEach(f => console.error('  - ' + f));
  process.exit(1);
}
console.log('No merge-conflict markers in source or generated output.');

#!/usr/bin/env node
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");
const MEDIA = new Set(["anime","article","articles","author","channels","entertainment","genre","genres","legacy","movie","movies","now","search","series","sports","topic","topics","trailers","trending","year","years","about","contact","privacy","terms","disclaimer","copyright","editorial-policy"]);
const failures = [];
let count = 0;
function walk(dir) {
  for (const e of fs.readdirSync(dir, {withFileTypes:true})) {
    if (e.name === ".git" || (dir === ROOT && e.name === "reports")) continue;
    const p = path.join(dir,e.name);
    if (e.isDirectory()) walk(p);
    else if (e.name.endsWith(".html")) check(p);
  }
}
function check(file) {
  count++;
  const s = fs.readFileSync(file,"utf8");
  const rel = path.relative(ROOT,file).replace(/\\/g,"/");
  if (/^google[^/]*\.html$/i.test(rel)) return;
  if (!/name=["']robots["'][^>]*content=["'][^"']*noindex/i.test(s) && !/content=["'][^"']*noindex[^"']*["'][^>]*name=["']robots/i.test(s)) failures.push(`${rel}: not noindex`);
  if (!/assets\/media-v2\.css/.test(s)) failures.push(`${rel}: media theme missing`);
  if (!/class=["'][^"']*media-bottom/.test(s)) failures.push(`${rel}: media bottom navigation missing`);
  if (!/\bid=["']main["']/.test(s)) failures.push(`${rel}: skip target missing`);
  if (/analytics\.js|n6wxm\.com|profitableratecpm|highperformanceformat/i.test(s)) failures.push(`${rel}: tracking or advertising reference`);
  if (/href=["']\/(?:jobs|make-money|tech)(?:\/|["'])/i.test(s)) failures.push(`${rel}: broken local link to main BRYME vertical`);
}
walk(ROOT);
for (const d of ["sports","movie","series","anime","article","assets","content","data","server"]) if (!fs.existsSync(path.join(ROOT,d))) failures.push(`required family missing: ${d}`);
for (const d of ["jobs","make-money","tech","miniapp"]) if (fs.existsSync(path.join(ROOT,d))) failures.push(`work-publication family leaked into media repo: ${d}`);
if (count < 3000) failures.push(`unexpectedly small archive: ${count} HTML files`);
const pkg = JSON.parse(fs.readFileSync(path.join(ROOT,"package.json"),"utf8"));
if (!pkg.scripts || !pkg.scripts.start) failures.push("start script missing");
if (failures.length) {
  console.error(`FAIL (${failures.length})`); failures.slice(0,100).forEach(x=>console.error("  - "+x)); process.exit(1);
}
console.log(JSON.stringify({ok:true, htmlFiles:count, indexable:0, theme:"forest-green", bottomNavigation:true},null,2));

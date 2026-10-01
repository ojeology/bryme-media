#!/usr/bin/env node
"use strict";
/* BRYME Media v3 "Watch Next" — sample integrity gate.
 *
 * Fails CI if the mass-upgrade architecture sample drifts:
 *   - every sample route exists and answers from the repository tree;
 *   - every sample page is noindex, v3-themed, has the bottom nav and #main;
 *   - authored copy stays above the thin-content floor;
 *   - pages ship no iframes (trailer facades only) and no ads/tracking;
 *   - every root-relative link in the sample resolves to a real file;
 *   - the hubs actually link to their collections.
 */
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");
const failures = [];
const fail = (m) => failures.push(m);

/* Authored-copy floors: single source of truth is content/niche-manifests.json
 * so the sample gate and the migration gate (scripts/audit-niche-readiness.js)
 * can never drift apart. Falls back to the same numbers if the manifest is
 * unreadable, so the gate still runs. */
let FLOORS = { rec: 350, explainer: 320, title: 280 };
try {
  const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, "content", "niche-manifests.json"), "utf8"));
  if (manifest && manifest.floors_words) FLOORS = manifest.floors_words;
} catch (e) {
  fail(`content/niche-manifests.json unreadable (${e.message}) — using fallback floors`);
}

const recs = [
  "shows-like-alice-in-borderland",
  "shows-like-squid-game",
  "movies-like-dune-part-two",
  "anime-like-solo-leveling",
];
const explainers = [
  "what-does-offside-mean",
  "how-does-var-work",
  "what-is-xg",
  "what-is-an-aggregate-score",
  "why-was-the-away-goals-rule-scrapped",
  "how-does-the-transfer-window-work",
  "how-is-a-knockout-tie-decided",
  "what-is-promotion-and-relegation",
];
const titlePages = [
  "movie/1917",
  "movie/dune-part-two",
  "series/alice-in-borderland",
  "series/squid-game",
  "anime/solo-leveling",
];

function read(rel) {
  const p = path.join(ROOT, rel);
  return fs.existsSync(p) ? fs.readFileSync(p, "utf8") : null;
}
function wordCount(htmlText) {
  const text = htmlText
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&[a-z#0-9]+;/gi, " ");
  return text.split(/\s+/).filter(Boolean).length;
}
function routeExists(href) {
  const clean = href.split("#")[0].split("?")[0];
  const rel = clean.replace(/^\//, "");
  if (!rel) return fs.existsSync(path.join(ROOT, "index.html"));
  const abs = path.join(ROOT, rel);
  return fs.existsSync(abs) || fs.existsSync(path.join(abs, "index.html"));
}
function checkLinks(rel, text) {
  const seen = new Set();
  for (const m of text.matchAll(/href="(\/[^"#]*)"/g)) {
    const href = m[1];
    if (seen.has(href)) continue;
    seen.add(href);
    if (!routeExists(href)) fail(`${rel}: broken internal link ${href}`);
  }
  return seen.size;
}

function checkSample(rel, { floor, require: reqClasses = [], minLinks = 3 }) {
  const text = read(rel);
  if (text === null) return fail(`${rel}: missing`);
  if (!/name=["']robots["'][^>]*noindex/i.test(text)) fail(`${rel}: not noindex`);
  if (!/assets\/media-v3\.css/.test(text)) fail(`${rel}: media-v3.css missing`);
  if (!/media-bottom/.test(text)) fail(`${rel}: bottom navigation missing`);
  if (!/\bid=["']main["']/.test(text)) fail(`${rel}: #main missing`);
  if (/analytics\.js|n6wxm\.com|profitableratecpm|highperformanceformat/i.test(text)) fail(`${rel}: tracking or advertising reference`);
  if (/<iframe/i.test(text)) fail(`${rel}: ships an iframe (facade-only rule)`);
  if (/youtube\.com\/embed/.test(text)) fail(`${rel}: direct embed URL in markup`);
  const words = wordCount(text);
  if (words < floor) fail(`${rel}: thin content (${words} words < ${floor})`);
  for (const cls of reqClasses) if (!text.includes(cls)) fail(`${rel}: expected component '${cls}' missing`);
  const linkCount = checkLinks(rel, text);
  if (linkCount < minLinks) fail(`${rel}: only ${linkCount} internal links (min ${minLinks})`);
  return words;
}

const summary = {};

/* hubs */
summary["/entertainment/"] = checkSample("entertainment/index.html", { floor: 100, require: ["v3-rail"], minLinks: 6 });
summary["/watch-next/"] = checkSample("watch-next/index.html", { floor: 100, require: ["v3-postcard"], minLinks: 5 });
summary["/sports/explainers/"] = checkSample("sports/explainers/index.html", { floor: 100, require: ["v3-postcard"], minLinks: 9 });

/* recommendation pages */
for (const slug of recs) {
  const rel = `watch-next/${slug}/index.html`;
  summary[`/watch-next/${slug}/`] = checkSample(rel, { floor: FLOORS.rec, require: ["v3-rec", "v3-trailer", "data-v3-play"], minLinks: 8 });
}
/* explainers */
for (const slug of explainers) {
  const rel = `sports/explainers/${slug}/index.html`;
  summary[`/sports/explainers/${slug}/`] = checkSample(rel, { floor: FLOORS.explainer, require: ["v3-answer", "v3-myths", "v3-faq"], minLinks: 5 });
}
/* upgraded title pages */
for (const rel of titlePages) {
  const file = `${rel}/index.html`;
  summary[`/${rel}/`] = checkSample(file, { floor: FLOORS.title, require: ["v3-title-poster", "v3-factlist"], minLinks: 5 });
  if (!/data-v3-play/.test(read(file) || "")) fail(`${file}: trailer facade missing`);
}

/* hub → collection link checks */
const wn = read("watch-next/index.html") || "";
for (const slug of recs) if (!wn.includes(`/watch-next/${slug}/`)) fail(`watch-next hub does not link ${slug}`);
const ex = read("sports/explainers/index.html") || "";
for (const slug of explainers) if (!ex.includes(`/sports/explainers/${slug}/`)) fail(`explainers hub does not link ${slug}`);

/* the sample must stay flat: no accidental mass generation beyond the approved sample */
const wnPages = fs.readdirSync(path.join(ROOT, "watch-next"), { withFileTypes: true })
  .filter((e) => e.isDirectory() && fs.existsSync(path.join(ROOT, "watch-next", e.name, "index.html"))).length;
if (wnPages > 12) fail(`watch-next has ${wnPages} pages — the approved sample is 4; get sign-off before scaling`);
const exPages = fs.readdirSync(path.join(ROOT, "sports", "explainers"), { withFileTypes: true })
  .filter((e) => e.isDirectory() && fs.existsSync(path.join(ROOT, "sports", "explainers", e.name, "index.html"))).length;
if (exPages > 16) fail(`sports/explainers has ${exPages} pages — the approved sample is 8; get sign-off before scaling`);

if (failures.length) {
  console.error(`FAIL (${failures.length})`);
  failures.slice(0, 100).forEach((x) => console.error("  - " + x));
  process.exit(1);
}
console.log(JSON.stringify({ ok: true, upgrade: "v3 watch-next sample", pages: summary }, null, 2));

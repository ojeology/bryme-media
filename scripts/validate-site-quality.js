#!/usr/bin/env node
/* Zero-dependency release gate for BRYME's Search, schema, data and privacy policy. */
"use strict";
const fs = require("fs");
const path = require("path");
const { URL } = require("url");

const ROOT = path.resolve(__dirname, "..");
const QUICK = process.argv.includes("--quick");
const failures = [];
const warnings = [];
const fail = (message) => failures.push(message);
const warn = (message) => warnings.push(message);
const read = (rel) => fs.readFileSync(path.join(ROOT, rel), "utf8");
const json = (rel) => JSON.parse(read(rel));
const allowDoc = json("content/index-allowlist.json");
const allow = new Set(allowDoc.routes);
const site = String(json("site.config.json").siteUrl).replace(/\/$/, "");
const verification = new Set([
  "google2ec8f794263d784f.html", "yandex_78fdd841f95fa2e1.html",
  "1740cdb82c02b9af13911b38c853e85d2f708322fa0c2c55.txt"
]);

function walk(dir, out) {
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    if ([".git", "node_modules", "reports"].includes(ent.name)) continue;
    const abs = path.join(dir, ent.name);
    if (ent.isDirectory()) walk(abs, out);
    else out.push(abs);
  }
  return out;
}
function rel(abs) { return path.relative(ROOT, abs).split(path.sep).join("/"); }
function routeFor(abs) {
  const r = rel(abs);
  if (r === "index.html") return "/";
  if (r.endsWith("/index.html")) return "/" + r.slice(0, -"index.html".length);
  return "/" + r;
}
function attrs(tag) {
  const out = {};
  const re = /([:\w-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))/g;
  let m;
  while ((m = re.exec(tag))) out[m[1].toLowerCase()] = m[2] ?? m[3] ?? m[4] ?? "";
  return out;
}
function metaContent(source, name) {
  for (const tag of source.match(/<meta\b[^>]*>/gi) || []) {
    const a = attrs(tag);
    if ((a.name || "").toLowerCase() === name.toLowerCase()) return a.content || "";
  }
  return "";
}
function canonical(source) {
  for (const tag of source.match(/<link\b[^>]*>/gi) || []) {
    const a = attrs(tag);
    if ((a.rel || "").toLowerCase().split(/\s+/).includes("canonical")) return a.href || "";
  }
  return "";
}
function normRoute(value) {
  if (value && typeof value === "object") value = value["@id"] || value.url || "";
  if (typeof value !== "string" || !value) return "";
  let p;
  try { p = new URL(value, site).pathname; } catch (_) { return ""; }
  p = p.replace(/\/{2,}/g, "/");
  return p === "/" ? "/" : p.replace(/\/+$/, "") + "/";
}
function visibleText(source) {
  return source
    .replace(/<script\b[\s\S]*?<\/script>/gi, " ")
    .replace(/<style\b[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/gi, " ").replace(/&amp;/gi, "&").replace(/&#39;|&apos;/gi, "'")
    .replace(/&quot;/gi, '"').replace(/\s+/g, " ").trim();
}
function jsonLd(source, fileRoute) {
  const entities = [];
  const re = /<script\b[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi;
  let m;
  while ((m = re.exec(source))) {
    let value;
    try { value = JSON.parse(m[1]); }
    catch (e) { fail(`${fileRoute}: invalid JSON-LD (${e.message})`); continue; }
    for (const item of Array.isArray(value) ? value : [value]) if (item && typeof item === "object") entities.push(item);
  }
  return entities;
}
function flattenSchema(node, out = []) {
  if (Array.isArray(node)) node.forEach(x => flattenSchema(x, out));
  else if (node && typeof node === "object") {
    if (node["@type"]) out.push(node);
    for (const value of Object.values(node)) if (value && typeof value === "object") flattenSchema(value, out);
  }
  return out;
}
function routeFile(route) {
  return path.join(ROOT, route === "/" ? "index.html" : route.replace(/^\//, "") + "index.html");
}

if (allow.size !== allowDoc.routes.length) fail("content/index-allowlist.json contains duplicate routes");
for (const route of allow) if (!fs.existsSync(routeFile(route))) fail(`Allowlisted route missing: ${route}`);

const allFiles = walk(ROOT, []);
const htmlFiles = allFiles.filter(f => f.toLowerCase().endsWith(".html"));
let indexableCount = 0;
let noindexCount = 0;
let sportsCount = 0;
let titleCount = 0;
const redirectSources = new Set(read("_redirects").split(/\r?\n/).map(x => x.trim()).filter(x => x && !x.startsWith("#")).map(x => normRoute(x.split(/\s+/)[0])));

for (const abs of htmlFiles) {
  const file = rel(abs);
  const route = routeFor(abs);
  const source = fs.readFileSync(abs, "utf8");
  const robots = metaContent(source, "robots").toLowerCase();
  const specialVerification = verification.has(file);
  const shouldIndex = allow.has(route);
  const isIndex = /(?:^|,)\s*index(?:\s*,|$)/.test(robots) && !robots.includes("noindex");
  const isNoindex = robots.includes("noindex");
  if (isIndex) indexableCount++;
  if (isNoindex) noindexCount++;
  if (shouldIndex && !isIndex) fail(`${route}: allowlisted but robots is ${JSON.stringify(robots)}`);
  if (!shouldIndex && !specialVerification && !isNoindex) fail(`${route}: outside allowlist without noindex`);

  if (shouldIndex) {
    if (/href=["']\/assets\/site\.css["']/i.test(source)) fail(`${route}: indexable page loads the 263 KB legacy stylesheet`);
    if (/src=["']\/assets\/site-app\.js["']/i.test(source)) fail(`${route}: indexable editorial page loads unnecessary client JS`);
    if (/\bshare-action\b/i.test(source)) fail(`${route}: indexable page exposes a JS-dependent share control`);
    const can = canonical(source);
    if (normRoute(can) !== normRoute(route)) fail(`${route}: canonical mismatch (${can || "missing"})`);
    const h1 = (source.match(/<h1\b/gi) || []).length;
    if (h1 !== 1) fail(`${route}: expected one H1, found ${h1}`);
    if (!/<html\b[^>]*\blang=["'][^"']+/i.test(source)) fail(`${route}: missing html lang`);
    if (!/<main\b/i.test(source)) fail(`${route}: missing main landmark`);
    if (!/<main\b[^>]*\bid=["']main["']/i.test(source)) fail(`${route}: main landmark lacks stable skip target`);
    if (!/<a\b[^>]*class=["'][^"']*skip-link[^"']*["'][^>]*href=["']#main["']/i.test(source)) fail(`${route}: missing keyboard skip link`);
    if (!/<title>[\s\S]*?<\/title>/i.test(source)) fail(`${route}: missing title`);
    if (!metaContent(source, "description")) fail(`${route}: missing meta description`);
    const ids = (source.match(/\bid=["'][^"']+["']/gi) || []).map(x => x.replace(/^.*?["']|["']$/g, ""));
    const dupIds = [...new Set(ids.filter((x, i) => ids.indexOf(x) !== i))];
    if (dupIds.length) fail(`${route}: duplicate IDs (${dupIds.slice(0, 4).join(", ")})`);
    for (const tag of source.match(/<img\b[^>]*>/gi) || []) if (!("alt" in attrs(tag))) fail(`${route}: image missing alt`);
  }

  const entities = jsonLd(source, route);
  const flat = flattenSchema(entities);
  if (flat.some(x => x["@type"] === "JobPosting")) fail(`${route}: unauthorized JobPosting schema`);
  if (shouldIndex) {
    const singleton = new Map();
    for (const entity of entities) {
      const type = entity["@type"];
      const group = ["Article", "NewsArticle", "BlogPosting"].includes(type) ? "Article" : type;
      if (["Article", "BreadcrumbList", "FAQPage"].includes(group)) singleton.set(group, (singleton.get(group) || 0) + 1);
      if (group === "Article") {
        const own = normRoute(entity.mainEntityOfPage || entity.url);
        if (own && own !== normRoute(route)) fail(`${route}: Article schema describes ${own}`);
        if (!entity.author) fail(`${route}: Article schema missing author`);
        if (!entity.datePublished || !entity.dateModified) fail(`${route}: Article schema missing dates`);
        const author = Array.isArray(entity.author) ? entity.author[0] : entity.author;
        const authorName = author && (author.name || "");
        const visible = visibleText(source);
        if (authorName && !visible.toLowerCase().includes(String(authorName).toLowerCase())) fail(`${route}: schema author is not visibly credited (${authorName})`);
        if (entity.datePublished && !visible.includes(String(entity.datePublished).slice(0, 10))) warn(`${route}: datePublished is not visibly printed`);
      }
      if (type === "BreadcrumbList") {
        const items = entity.itemListElement || [];
        const last = items.length && items[items.length - 1];
        const own = last && normRoute(last.item);
        if (own && own !== normRoute(route)) fail(`${route}: breadcrumb ends at ${own}`);
      }
      if (type === "FAQPage") {
        const visible = visibleText(source).toLowerCase();
        for (const q of entity.mainEntity || []) if (q.name && !visible.includes(String(q.name).toLowerCase())) fail(`${route}: FAQ question is not visible: ${q.name}`);
      }
    }
    for (const [type, count] of singleton) if (count > 1) fail(`${route}: duplicate ${type} schema (${count})`);
  }

  const titleRoute = /^\/(movie|series|anime)\/[^/]+\/$/.test(route);
  if (titleRoute) {
    titleCount++;
    for (const type of ["Movie", "TVSeries", "VideoObject", "Article"]) if (flat.some(x => x["@type"] === type)) fail(`${route}: contained title still publishes ${type} schema`);
    if (/data-nm-(?:my-list|rate)|\bWatch Now\b|class=["'][^"']*\bnm-(?:match|hd)\b/i.test(source)) fail(`${route}: unsupported title control remains`);
    if (/<iframe\b/i.test(source)) fail(`${route}: eager iframe remains on click-to-load title page`);
  }
  if (/class=["']svc-row["']/i.test(source)) fail(`${route}: generic provider button row remains`);
  if (route.startsWith("/sports/")) {
    sportsCount++;
    if (!isNoindex) fail(`${route}: sports route is not noindex`);
    if (!source.includes("Sports data paused.")) fail(`${route}: sports integrity notice missing`);
  }

  const externalScripts = (source.match(/<script\b[^>]*\bsrc=["']https?:\/\/[^"']+["'][^>]*>/gi) || []);
  for (const tag of externalScripts) {
    const src = attrs(tag).src || "";
    if (!(file === "miniapp/index.html" && src === "https://telegram.org/js/telegram-web-app.js")) fail(`${route}: unexpected external script ${src}`);
  }
  if (/googletagmanager\.com|google-analytics\.com|n6wxm\.com|libtl\.com\/sdk|monetag\.com/i.test(source)) fail(`${route}: active tracking/ad endpoint remains in HTML`);

  if (shouldIndex && !QUICK) {
    const attrRe = /\b(?:href|src)=["']([^"']+)["']/gi;
    let m;
    while ((m = attrRe.exec(source))) {
      const value = m[1];
      if (!value || /^(?:#|mailto:|tel:|javascript:|data:|https?:\/\/)/i.test(value)) continue;
      let local;
      try { local = new URL(value, site + route).pathname; } catch (_) { fail(`${route}: malformed local reference ${value}`); continue; }
      let target = path.join(ROOT, local.replace(/^\//, ""));
      let exists = fs.existsSync(target);
      if (exists && fs.statSync(target).isDirectory()) exists = fs.existsSync(path.join(target, "index.html"));
      if (!exists && !path.extname(local)) exists = fs.existsSync(path.join(target, "index.html"));
      if (!exists && !redirectSources.has(normRoute(local))) fail(`${route}: missing local target ${value}`);
    }
  }
}
if (indexableCount !== allow.size) fail(`Indexable HTML count ${indexableCount} does not equal allowlist ${allow.size}`);

/* Discovery files must be exact projections of the allowlist. */
const sitemap = read("sitemap.xml");
const sitemapRoutes = [...sitemap.matchAll(/<loc>(.*?)<\/loc>/g)].map(m => normRoute(m[1]));
if (sitemapRoutes.length !== allow.size) fail(`sitemap.xml has ${sitemapRoutes.length} URLs, expected ${allow.size}`);
for (const route of allow) if (!sitemapRoutes.includes(normRoute(route))) fail(`sitemap.xml missing ${route}`);
for (const route of sitemapRoutes) if (!allow.has(route)) fail(`sitemap.xml includes non-allowlisted ${route}`);
if (new Set(sitemapRoutes).size !== sitemapRoutes.length) fail("sitemap.xml contains duplicates");
const newsRoutes = [...read("news-sitemap.xml").matchAll(/<loc>(.*?)<\/loc>/g)].map(m => normRoute(m[1]));
for (const route of newsRoutes) if (!allow.has(route)) fail(`news-sitemap.xml includes non-allowlisted ${route}`);
const feedRoutes = [...read("feed.xml").matchAll(/<item>[\s\S]*?<link>(.*?)<\/link>/g)].map(m => normRoute(m[1]));
for (const route of feedRoutes) if (!allow.has(route)) fail(`feed.xml includes non-allowlisted ${route}`);
const robots = read("robots.txt");
if (!robots.includes(`Sitemap: ${site}/sitemap.xml`)) fail("robots.txt missing primary sitemap");
if (/Disallow:\s*\/(?:movie|series|anime|article|tech|make-money|jobs)/i.test(robots)) fail("robots.txt blocks crawlable noindex/content routes");

/* Data integrity and provenance. */
const jobs = json("content/jobs.json");
if (!Array.isArray(jobs.jobs) || jobs.jobs.length !== 13) fail(`Expected 13 verified jobs, found ${jobs.jobs && jobs.jobs.length}`);
const jobIds = new Set(), jobUrls = new Set();
for (const job of jobs.jobs || []) {
  for (const key of ["id", "employer", "title", "locationTextRaw", "workMode", "employmentType", "sourceUrl", "sourceSystem", "status", "verifiedAt", "notes"]) if (!(key in job) || job[key] === "") fail(`Job ${job.id || "?"}: missing ${key}`);
  if (job.status !== "open_when_checked") fail(`Job ${job.id}: unsupported status ${job.status}`);
  if (!/^https:\/\//.test(job.sourceUrl || "")) fail(`Job ${job.id}: sourceUrl must be HTTPS`);
  if (jobIds.has(job.id)) fail(`Duplicate job id ${job.id}`); jobIds.add(job.id);
  if (jobUrls.has(job.sourceUrl)) fail(`Duplicate job sourceUrl ${job.sourceUrl}`); jobUrls.add(job.sourceUrl);
}
const competitions = json("content/competitions.json");
let standingsRows = 0;
for (const comp of competitions.competitions || []) {
  let prior = null;
  for (const team of comp.teams || []) {
    standingsRows++;
    if (Number(team.gd) !== Number(team.gf) - Number(team.ga)) fail(`${comp.id}/${team.name}: GD ${team.gd} != GF ${team.gf} - GA ${team.ga}`);
    const key = [Number(team.pts), Number(team.gd), Number(team.gf)];
    if (prior && (key[0] > prior[0] || (key[0] === prior[0] && key[1] > prior[1]) || (key[0] === prior[0] && key[1] === prior[1] && key[2] > prior[2]))) fail(`${comp.id}: standings order is inconsistent near ${team.name}`);
    prior = key;
  }
}
if (standingsRows !== 132) fail(`Expected 132 standings rows, found ${standingsRows}`);
const movies = json("data/movies.json");
for (const movie of movies) {
  if (movie.runtime) {
    const mins = Number(String(movie.runtime).match(/\d+/)?.[0]);
    if (!mins || mins < 20 || mins > 400) fail(`${movie.slug}: implausible runtime ${movie.runtime}`);
  }
  if (movie.rating && movie.rating.value != null && !/BRYME/i.test(movie.rating.source || "")) fail(`${movie.slug}: rating source is not explicitly BRYME`);
  for (const key of ["metaSource", "castSource", "runtimeSource"]) {
    const src = movie[key];
    if (!src || !src.url) continue;
    if (/Wikipedia/i.test(src.name || "") && !/wikipedia\.org/i.test(src.url)) fail(`${movie.slug}: ${key} is mislabeled Wikipedia`);
    if (/Wikidata/i.test(src.name || "") && !/wikidata\.org/i.test(src.url)) fail(`${movie.slug}: ${key} is mislabeled Wikidata`);
  }
}
for (const [slug, runtime, sourceName] of [["oppenheimer", "180 min", "NBC Insider"], ["the-black-book", "124 min", "Nollywire"], ["the-invite", "107 min", "Apple TV official title page"]]) {
  const rec = movies.find(x => x.slug === slug);
  if (!rec || rec.runtime !== runtime) fail(`${slug}: expected corrected runtime ${runtime}`);
  if (!rec || !rec.runtimeSource || rec.runtimeSource.name !== sourceName) fail(`${slug}: corrected runtime source missing`);
}
const titleMetadata = read("content/title-metadata.json");
if (/imdb\.com/i.test(titleMetadata)) fail("content/title-metadata.json still uses IMDb as a metadata source");

/* Runtime code/deployment guarantees. */
for (const relPath of ["assets/analytics.js", "assets/site-app.js", "miniapp/ads.js"]) {
  const source = read(relPath);
  if (/googletagmanager\.com|google-analytics\.com|n6wxm\.com|libtl\.com\/sdk|monetag\.com/i.test(source)) fail(`${relPath}: tracking/ad endpoint remains`);
}
const appJs = read("assets/site-app.js");
if (/shouldAutoplay|[?#]play=1/.test(appJs)) fail("assets/site-app.js still contains URL-triggered autoplay");
const serverJs = read("server/server.js");
for (const marker of ["PUBLIC_HTML_DIRS", "PUBLIC_ROOT_FILES", "SECURITY_HEADERS", "content-security-policy", "GONE_ROUTES"]) if (!serverJs.includes(marker)) fail(`server/server.js missing hardening marker ${marker}`);
const workflow = read(".github/workflows/results-agent.yml");
if (/\|\|\s*true/.test(workflow.replace(/^\s*#.*$/gm, ""))) fail("results-agent workflow suppresses a failure with || true");
if (!fs.existsSync(path.join(ROOT, "render.yaml"))) fail("Root Render Blueprint missing");
const destructive = read("scripts/build-static-foundation.js");
if (!destructive.includes("ALLOW_DESTRUCTIVE_BUILD")) fail("Destructive legacy generator is not guarded");

if (warnings.length) {
  console.log(`WARNINGS (${warnings.length})`);
  warnings.slice(0, 40).forEach(x => console.log("  - " + x));
  if (warnings.length > 40) console.log(`  ... ${warnings.length - 40} more`);
}
if (failures.length) {
  console.error(`FAIL (${failures.length})`);
  failures.slice(0, 100).forEach(x => console.error("  - " + x));
  if (failures.length > 100) console.error(`  ... ${failures.length - 100} more`);
  process.exit(1);
}
console.log(JSON.stringify({
  ok: true,
  htmlFiles: htmlFiles.length,
  allowlisted: allow.size,
  indexable: indexableCount,
  noindex: noindexCount,
  titlePagesContained: titleCount,
  sportsPagesPaused: sportsCount,
  standingsRows,
  jobs: (jobs.jobs || []).length,
  sitemapUrls: sitemapRoutes.length,
  newsUrls: newsRoutes.length,
  rssItems: feedRoutes.length,
  mode: QUICK ? "quick" : "full"
}, null, 2));

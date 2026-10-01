#!/usr/bin/env node
"use strict";
/* BRYME Media — niche readiness audit (the staging → live migration gate).
 *
 * Owner directive (2026-10-01): work lands in bryme-media (staging); a niche
 * moves to nextclip (live) only when it is FULL and has NO THIN pages.
 * Approval of the sample does NOT trigger migration — only this gate does.
 *
 *   node scripts/audit-niche-readiness.js            # all niches, human output
 *   node scripts/audit-niche-readiness.js sports     # one niche
 *   node scripts/audit-niche-readiness.js --json     # machine output
 *   node scripts/audit-niche-readiness.js --strict   # exit 1 unless every audited niche is READY
 *
 * What each niche is measured on (config: content/niche-manifests.json):
 *   FULL    — rebuild set at its target and completely cross-linked
 *   NO THIN — every rebuild-set page clears its authored-copy floor
 *   LINKS   — every root-relative link resolves inside the staging tree
 */
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");

const args = process.argv.slice(2);
const jsonOut = args.includes("--json");
const strict = args.includes("--strict");
const nicheArg = args.find((a) => ["entertainment", "sports", "all"].includes(a)) || "all";

const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, "content", "niche-manifests.json"), "utf8"));
const FLOORS = manifest.floors_words;
const BY_SPORT = (manifest.niches.sports.targets.by_sport) || {};

/* slug -> sport, read from the authored batches so the audit reports coverage
 * per sport rather than only in total */
const SPORT_OF = {};
for (const f of fs.readdirSync(path.join(ROOT, "content"))) {
  if (!f.startsWith("upgrade-sports") || !f.endsWith(".json")) continue;
  const packs = JSON.parse(fs.readFileSync(path.join(ROOT, "content", f), "utf8")).explainers || [];
  for (const p of packs) SPORT_OF[p.slug] = p.sport || "general";
}

function read(rel) {
  const p = path.join(ROOT, rel);
  return fs.existsSync(p) ? fs.readFileSync(p, "utf8") : null;
}
function words(t) {
  return t
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&[a-z#0-9]+;/gi, " ")
    .split(/\s+/)
    .filter(Boolean).length;
}
function routeExists(href) {
  const clean = href.split("#")[0].split("?")[0];
  const rel = clean.replace(/^\//, "");
  if (!rel) return fs.existsSync(path.join(ROOT, "index.html"));
  const abs = path.join(ROOT, rel);
  return fs.existsSync(abs) || fs.existsSync(path.join(abs, "index.html"));
}
function dirsWithIndex(base) {
  const abs = path.join(ROOT, base);
  if (!fs.existsSync(abs)) return [];
  return fs
    .readdirSync(abs, { withFileTypes: true })
    .filter((e) => e.isDirectory() && fs.existsSync(path.join(abs, e.name, "index.html")))
    .map((e) => e.name)
    .sort();
}
function brokenLinksIn(rel, text) {
  const bad = new Set();
  for (const m of text.matchAll(/href="(\/[^"#]*)"/g)) {
    if (!routeExists(m[1])) bad.add(m[1]);
  }
  return [...bad];
}

/* ---------------------------------------------------------------- entertainment */
function auditEntertainment() {
  const recs = dirsWithIndex("watch-next");
  const thin = [];
  const linkIssues = [];
  const referenced = new Map(); // "dir/slug" -> slug
  let wordsMin = Infinity;
  let wordsMax = 0;

  for (const slug of recs) {
    const rel = `watch-next/${slug}/index.html`;
    const t = read(rel);
    if (!t) {
      linkIssues.push(`${rel} missing`);
      continue;
    }
    const w = words(t);
    wordsMin = Math.min(wordsMin, w);
    wordsMax = Math.max(wordsMax, w);
    if (w < FLOORS.rec) thin.push({ page: `/watch-next/${slug}/`, words: w, floor: FLOORS.rec });
    for (const m of t.matchAll(/href="\/(movie|series|anime)\/([a-z0-9-]+)\/"/g)) {
      referenced.set(`${m[1]}/${m[2]}`, m[2]);
    }
    for (const bad of brokenLinksIn(rel, t)) linkIssues.push(`${rel}: broken link ${bad}`);
  }

  const upgraded = [];
  const notUpgraded = [];
  for (const key of referenced.keys()) {
    const t = read(`${key}/index.html`);
    if (!t) notUpgraded.push(`${key} (page missing)`);
    else if (/v3-title-poster/.test(t)) upgraded.push(key);
    else notUpgraded.push(key);
  }

  const hub = read("watch-next/index.html") || "";
  const missingFromHub = recs.filter((s) => !hub.includes(`/watch-next/${s}/`));
  const entHub = read("entertainment/index.html");
  if (!entHub) linkIssues.push("entertainment/index.html missing");

  const target = manifest.niches.entertainment.targets.rec_lists;
  const full = recs.length >= target.value && notUpgraded.length === 0 && missingFromHub.length === 0;
  const noThin = thin.length === 0;

  return {
    niche: "entertainment",
    label: manifest.niches.entertainment.label,
    lists: recs.length,
    target: target.value,
    targetStatus: target.status,
    wordsMin: wordsMin === Infinity ? 0 : wordsMin,
    wordsMax,
    thin,
    titlesReferenced: referenced.size,
    titlesUpgraded: upgraded.length,
    notUpgraded,
    missingFromHub,
    linkIssues,
    full,
    noThin,
    ready: full && noThin && linkIssues.length === 0,
  };
}

/* ---------------------------------------------------------------- sports */
function auditSports() {
  const list = dirsWithIndex("sports/explainers");
  const thin = [];
  const linkIssues = [];
  const weakConcept = [];
  let wordsMin = Infinity;
  let wordsMax = 0;

  for (const slug of list) {
    const rel = `sports/explainers/${slug}/index.html`;
    const t = read(rel);
    if (!t) {
      linkIssues.push(`${rel} missing`);
      continue;
    }
    const w = words(t);
    wordsMin = Math.min(wordsMin, w);
    wordsMax = Math.max(wordsMax, w);
    if (w < FLOORS.explainer) thin.push({ page: `/sports/explainers/${slug}/`, words: w, floor: FLOORS.explainer });
    if (!/v3-answer/.test(t)) linkIssues.push(`${rel}: answer block missing`);
    const concept = t.match(/<div class="v3-concept">[\s\S]*?<ul>([\s\S]*?)<\/ul>/);
    const count = concept ? [...concept[1].matchAll(/href="\//g)].length : 0;
    if (count < 2) weakConcept.push(`/sports/explainers/${slug}/ → ${count} concept link(s)`);
    for (const bad of brokenLinksIn(rel, t)) linkIssues.push(`${rel}: broken link ${bad}`);
  }

  const hub = read("sports/explainers/index.html") || "";
  const missingFromHub = list.filter((s) => !hub.includes(`/sports/explainers/${s}/`));

  const bySport = {};
  for (const slug of list) {
    const sp = SPORT_OF[slug] || "general";
    bySport[sp] = (bySport[sp] || 0) + 1;
  }
  const sportGaps = Object.keys(BY_SPORT)
    .filter((sp) => (bySport[sp] || 0) < BY_SPORT[sp])
    .map((sp) => `${sp} ${bySport[sp] || 0}/${BY_SPORT[sp]}`);
  const sportRows = Object.keys(BY_SPORT).map((sp) => ({ sport: sp, have: bySport[sp] || 0, target: BY_SPORT[sp] }));

  const target = manifest.niches.sports.targets.explainers;
  const full = list.length >= target.value && missingFromHub.length === 0 && weakConcept.length === 0 && sportGaps.length === 0;
  const noThin = thin.length === 0;

  return {
    niche: "sports",
    label: manifest.niches.sports.label,
    explainers: list.length,
    target: target.value,
    bySport,
    sportRows,
    sportGaps,
    targetStatus: target.status,
    wordsMin: wordsMin === Infinity ? 0 : wordsMin,
    wordsMax,
    thin,
    weakConcept,
    missingFromHub,
    linkIssues,
    full,
    noThin,
    ready: full && noThin && linkIssues.length === 0,
  };
}

/* ---------------------------------------------------------------- report */
const results = [];
if (nicheArg === "all" || nicheArg === "entertainment") results.push(auditEntertainment());
if (nicheArg === "all" || nicheArg === "sports") results.push(auditSports());

const verdict = {
  rule: manifest.rule,
  floors_words: FLOORS,
  niches: results,
  allReady: results.every((r) => r.ready),
};

if (jsonOut) {
  console.log(JSON.stringify(verdict, null, 2));
} else {
  console.log("BRYME Media — niche readiness audit (staging → live gate)");
  console.log(`Rule: ${manifest.rule}\n`);
  for (const r of results) {
    console.log(`${r.niche.toUpperCase()} (${r.label.split("— ")[1] || r.label}) — ${r.ready ? "READY" : "NOT READY"}`);
    if (r.niche === "entertainment") {
      console.log(`  rec lists:       ${r.lists} / ${r.target} (${r.targetStatus})`);
      console.log(`  copy:            ${r.wordsMin}–${r.wordsMax} words/list (floor ${FLOORS.rec})`);
      console.log(`  thin pages:      ${r.thin.length === 0 ? "0 ✓" : r.thin.length + " ✗"}`);
      console.log(`  title coverage:  ${r.titlesUpgraded} / ${r.titlesReferenced} referenced titles upgraded`);
      if (r.notUpgraded.length) console.log(`  not upgraded:    ${r.notUpgraded.slice(0, 6).join(", ")}${r.notUpgraded.length > 6 ? ` (+${r.notUpgraded.length - 6} more)` : ""}`);
      console.log(`  hub links:       ${r.missingFromHub.length === 0 ? "complete ✓" : "missing " + r.missingFromHub.join(", ") + " ✗"}`);
    } else {
      console.log(`  explainers:      ${r.explainers} / ${r.target} (${r.targetStatus})`);
      if (r.sportRows && r.sportRows.length) {
        for (const row of r.sportRows) console.log(`    ${row.sport.padEnd(12)} ${row.have} / ${row.target}${row.have < row.target ? " ✗" : " ✓"}`);
      }
      console.log(`  copy:            ${r.wordsMin}–${r.wordsMax} words/page (floor ${FLOORS.explainer})`);
      console.log(`  thin pages:      ${r.thin.length === 0 ? "0 ✓" : r.thin.length + " ✗"}`);
      console.log(`  concept network: ${r.weakConcept.length === 0 ? "all pages ≥2 links ✓" : r.weakConcept.join("; ") + " ✗"}`);
      console.log(`  hub links:       ${r.missingFromHub.length === 0 ? "complete ✓" : "missing " + r.missingFromHub.join(", ") + " ✗"}`);
    }
    console.log(`  link integrity:  ${r.linkIssues.length === 0 ? "ok ✓" : r.linkIssues.length + " issue(s) ✗"}`);
    const remaining = [];
    if (r.lists !== undefined && r.lists < r.target) remaining.push(`build ${r.target - r.lists} more list(s)`);
    if (r.explainers !== undefined && r.explainers < r.target) remaining.push(`build ${r.target - r.explainers} more explainer(s)`);
    if (r.notUpgraded && r.notUpgraded.length) remaining.push(`upgrade ${r.notUpgraded.length} referenced title page(s)`);
    if (r.weakConcept && r.weakConcept.length) remaining.push(`fix concept links on ${r.weakConcept.length} page(s)`);
    if (r.sportGaps && r.sportGaps.length) remaining.push(`top up ${r.sportGaps.join(", ")}`);
    if (r.linkIssues.length) remaining.push("fix link issues");
    if (remaining.length) console.log(`  → remaining:     ${remaining.join("; ")}`);
    console.log("");
  }
  if (verdict.allReady) {
    console.log("VERDICT: gate green for all audited niches — migration still requires owner sign-off and an unfrozen live window.");
  } else {
    console.log("VERDICT: migration BLOCKED — niches above must reach FULL + NO THIN first.");
    console.log("(Live changes also remain frozen until the AdSense verdict — see the sitewide roadmap.)");
  }
}

if (strict && !verdict.allReady) process.exit(1);

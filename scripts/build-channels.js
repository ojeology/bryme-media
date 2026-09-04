#!/usr/bin/env node
/* BRYME legacy provider-channel containment.
 *
 * The former generator inferred Netflix/Prime/Crunchyroll/SonyLIV availability
 * from content type or genre. That was not provider data. These routes now
 * remain as noindex retirement notices so old links explain what changed.
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");
const labels = {
  trending: "Trending", latest: "Latest releases", netflix: "Netflix",
  prime: "Prime Video", sony: "SonyLIV", jio: "JioHotstar",
  crunchyroll: "Crunchyroll", kids: "Kids", mx: "MX Player"
};
function esc(s) { return String(s).replace(/[&<>\"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
for (const [slug, label] of Object.entries(labels)) {
  const route = `/channels/${slug}/`;
  const page = `<!doctype html><html lang="en-NG"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Legacy collection retired | BRYME</title><meta name="description" content="This legacy BRYME collection was retired because it did not represent verified provider availability."><meta name="robots" content="noindex,follow"><link rel="canonical" href="https://bryme.onrender.com${route}"><link rel="stylesheet" href="/assets/bryme-v2.css"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"></head><body><main id="main"><div class="wrap"><section class="page-hero"><p class="kicker"><span class="kicker-dot"></span>Collection retired</p><h1>${esc(label)} was not a verified availability page.</h1><p>BRYME removed this legacy collection from Search because it grouped titles by type or genre rather than confirmed, region-specific provider data.</p><div class="actions"><a class="btn" href="/articles/">Read original entertainment guides</a><a class="btn secondary" href="/">Return home</a></div></section></div></main></body></html>`;
  const out = path.join(ROOT, "channels", slug, "index.html");
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, page);
  console.log("retired", route);
}

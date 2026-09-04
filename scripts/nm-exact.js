#!/usr/bin/env node
/* NetMirror exact-match pass:
   1) desk-bar -> exact 9-pill NetMirror row (Trending, Latest Release,
      Netflix, Prime Video, JioHotstar, SonyLIV, Crunchyroll, Kids, MX Player)
   2) title pages -> floating Back / X bar over the detail hero
   3) homepage -> NetMirror search CTA card
   4) theme-color meta -> #0B0B0B */
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');

const PILLS = [
  ['/channels/trending/', 'tr', '🔥', 'Trending'],
  ['/channels/latest/', 'lr', '✨', 'Latest Release'],
  ['/channels/netflix/', 'n', 'N', 'Netflix'],
  ['/channels/prime/', 'pv', 'P', 'Prime Video'],
  ['/channels/sony/', 's', 'S', 'SonyLIV'],
  ['/channels/jio/', 'j', 'J', 'JioHotstar'],
  ['/channels/crunchyroll/', 'cr', 'C', 'Crunchyroll'],
  ['/channels/kids/', 'k', 'K', 'Kids'],
  ['/channels/mx/', 'm', 'M', 'MX Player'],
];

function routeOf(file) {
  const rel = path.relative(ROOT, file).split(path.sep).join('/');
  if (rel === 'index.html') return '/';
  if (rel.endsWith('/index.html')) return '/' + rel.slice(0, -'index.html'.length);
  return '/' + rel;
}
function activeHref(route) {
  if (route === '/' || route === '/trending' || route.startsWith('/trending/')) return '/channels/trending/';
  if (route.startsWith('/channels/trending')) return '/channels/trending/';
  if (route.startsWith('/channels/latest')) return '/channels/latest/';
  if (route.startsWith('/channels/netflix')) return '/channels/netflix/';
  if (route.startsWith('/channels/prime')) return '/channels/prime/';
  if (route.startsWith('/channels/sony')) return '/channels/sony/';
  if (route.startsWith('/channels/jio')) return '/channels/jio/';
  if (route.startsWith('/channels/mx')) return '/channels/mx/';
  if (route.startsWith('/channels/crunchyroll')) return '/channels/crunchyroll/';
  if (route.startsWith('/channels/kids')) return '/channels/kids/';
  return null;
}
function deskBar(route) {
  const active = activeHref(route);
  const links = PILLS.map(([href, key, glyph, label]) =>
    `<a class="dpill${href === active ? ' is-on' : ''}" href="${href}"><span class="plogo pl-${key}">${glyph}</span>${label}</a>`).join('');
  return `<nav class="desk-bar" aria-label="Browse channels"><div class="shell desk-bar-inner">${links}</div></nav>`;
}

const htmls = [];
(function walk(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name === '.git' || e.name === 'node_modules') continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p);
    else if (/\.html$/.test(e.name)) htmls.push(p);
  }
})(ROOT);

let pills = 0, heroBar = 0, cta = 0;
for (const file of htmls) {
  let s = fs.readFileSync(file, 'utf8');
  const route = routeOf(file);
  let changed = false;

  // 1) desk-bar -> exact pills (matches any existing desk-bar variant)
  const db = /<nav class="desk-bar"[^>]*><div class="shell desk-bar-inner">[\s\S]*?<\/div><\/nav>/;
  if (db.test(s)) {
    s = s.replace(db, deskBar(route));
    pills++; changed = true;
  }

  // 2) title pages -> Back / X bar
  if (/class="movie-hero/.test(s) && !s.includes('nm-hero-bar')) {
    s = s.replace(/(<section class="movie-hero[^"]*"[^>]*>)/,
      `$1<div class="nm-hero-bar"><a class="nm-back" href="#" onclick="history.back();return false" aria-label="Go back">‹ Back</a><a class="nm-x" href="/" aria-label="Close">✕</a></div>`);
    heroBar++; changed = true;
  }

  // 3) homepage -> search CTA
  if (route === '/' && !s.includes('nm-search-cta')) {
    const ctaHtml = `<section class="nm-search-cta"><div class="nm-search-cta-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg></div><h3>Can't find what you're looking for?</h3><p>Search any movie or show by name — instant results from the full BRYME catalogue.</p><a class="nm-btn nm-btn-primary" href="/search/">Search Now</a></section>\n`;
    s = s.replace('<nav class="mobile-nav">', ctaHtml + '<nav class="mobile-nav">');
    cta++; changed = true;
  }

  if (changed) fs.writeFileSync(file, s);
}
console.log(JSON.stringify({ pills, heroBar, cta, scanned: htmls.length }, null, 2));

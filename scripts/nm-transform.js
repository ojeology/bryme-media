#!/usr/bin/env node
/* NetMirror transform:
   A) desk-bar catalogue pills  -> channel pills (Trending/Netflix/Prime Video/Crunchyroll/Kids)
   B) mobile-nav               -> add Movies/Series/Anime links
   C) title pages              -> Watch Now + Trailer CTAs, % Match + HD chips,
                                  Cast carousel (initials avatars), Audio tabs,
                                  tp-loved header -> "More Like This"            */
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const esc = s => String(s == null ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

const htmls = [];
(function walk(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name === '.git' || e.name === 'node_modules') continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p);
    else if (/\.html$/.test(e.name)) htmls.push(p);
  }
})(ROOT);

function routeOf(file) {
  const rel = path.relative(ROOT, file).split(path.sep).join('/');
  if (rel === 'index.html') return '/';
  if (rel.endsWith('/index.html')) return '/' + rel.slice(0, -'index.html'.length);
  return '/' + rel;
}

function deskBar(route) {
  const pills = [
  ['/trending/', 'tr', '🔥', 'Trending'],
  ['/year/2026/', 'lr', '✨', 'Latest Release'],
  ['/channels/netflix/', 'n', 'N', 'Netflix'],
  ['/channels/prime-video/', 'pv', 'P', 'Prime Video'],
  ['/genre/indian/', 'j', 'J', 'JioHotstar'],
  ['/genre/indian/', 's', 'S', 'SonyLIV'],
  ['/channels/crunchyroll/', 'cr', 'C', 'Crunchyroll'],
  ['/channels/kids/', 'k', 'K', 'Kids'],
  ['/genre/indian/', 'm', 'M', 'MX Player'],
];
  let active = null;
  if (route === '/' || route === '/trending/' || route === '/trending') active = '/trending/';
  else if (route.startsWith('/channels/netflix')) active = '/channels/netflix/';
  else if (route.startsWith('/channels/prime-video')) active = '/channels/prime-video/';
  else if (route.startsWith('/channels/crunchyroll')) active = '/channels/crunchyroll/';
  else if (route.startsWith('/channels/kids')) active = '/channels/kids/';
  const links = pills.map(([href, key, glyph, label]) =>
    `<a class="dpill${href === active ? ' is-on' : ''}" href="${href}"><span class="plogo pl-${key}">${glyph}</span>${label}</a>`).join('');
  return `<nav class="desk-bar" aria-label="Browse channels"><div class="shell desk-bar-inner">${links}</div></nav>`;
}

function initials(name) {
  const parts = String(name).trim().split(/\s+/);
  const a = (parts[0] || '')[0] || '';
  const b = parts.length > 1 ? (parts[parts.length - 1][0] || '') : '';
  return (a + b).toUpperCase() || '?';
}

function extractCastAndLangs(html) {
  const m = html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/);
  if (!m) return { actors: [], langs: [] };
  try {
    const arr = JSON.parse(m[1]);
    const items = Array.isArray(arr) ? arr : [arr];
    const actors = [];
    let langs = [];
    for (const it of items) {
      if (!it || typeof it !== 'object') continue;
      if (Array.isArray(it.actor)) {
        for (const a of it.actor) {
          if (typeof a === 'string') actors.push(a);
          else if (a && typeof a === 'object' && a.name) actors.push(a.name);
        }
      }
      if (!langs.length && it.inLanguage) {
        const l = Array.isArray(it.inLanguage) ? it.inLanguage : [it.inLanguage];
        langs = l.map(x => (x && typeof x === 'object' ? x.name : String(x))).filter(Boolean);
      }
    }
    return { actors: actors.slice(0, 10), langs };
  } catch (e) {
    return { actors: [], langs: [] };
  }
}

let stats = { desk: 0, mnav: 0, detail: 0, badges: 0, morelike: 0 };

for (const file of htmls) {
  let s = fs.readFileSync(file, 'utf8');
  let changed = false;
  const route = routeOf(file);

  // A) desk-bar -> channel pills (only old markup)
  const oldDesk = /<nav class="desk-bar" aria-label="Catalogue"><div class="shell desk-bar-inner">[\s\S]*?<\/div><\/nav>/;
  if (oldDesk.test(s)) {
    s = s.replace(oldDesk, deskBar(route));
    stats.desk++; changed = true;
  }

  // B) mobile-nav: single tidy 6-item bar (Home/Entertain/Sports/Money/Tech/Search)
  const NAV6 = [
    ['/', '🏠', 'Home', '/'],
    ['/entertainment/', '🎬', 'Entertain', '/entertainment'],
    ['/sports/', '⚽', 'Sports', '/sports'],
    ['/make-money/', '💰', 'Money', '/make-money'],
    ['/tech/', '🤖', 'Tech', '/tech'],
    ['/search/', '🔍', 'Search', '/search'],
  ];
  const mnavRe = /<nav class="mobile-nav">[\s\S]*?<\/nav>/;
  if (mnavRe.test(s)) {
    const links = NAV6.map(function (n) {
      const active = (route === n[3] || route.startsWith(n[3] + '/')) ? ' class="active"' : '';
      return '<a href="' + n[0] + '"' + active + '><span class="mn-ico">' + n[1] + '</span>' + n[2] + '</a>';
    }).join('');
    s = s.replace(mnavRe, '<nav class="mobile-nav">' + links + '</nav>');
    stats.mnav++; changed = true;
  }
  // C) title-page NetMirror upgrades
  if (s.indexOf('class="movie-hero') > -1) {
    stats.detail++;
    const pair = /<a class="cta" href="#trailer">Watch trailer<\/a><a class="cta cta-ghost" href="#watch">Where to watch<\/a>/;
    if (pair.test(s)) {
      s = s.replace(pair,
        '<a class="cta nm-watch-now" href="#watch">▶ Watch Now</a><a class="cta cta-ghost nm-trailer" href="#trailer">▶ Trailer</a>');
      changed = true;
    } else {
      s = s.replace(/<a class="cta" href="#trailer">Watch trailer<\/a>/,
        '<a class="cta cta-ghost nm-trailer" href="#trailer">▶ Trailer</a>');
      s = s.replace(/<a class="cta cta-ghost" href="#watch">Where to watch<\/a>/,
        '<a class="cta nm-watch-now" href="#watch">▶ Watch Now</a>');
      changed = true;
    }
    // % Match + HD chips before the editorial badge
    const badgeRe = /(<div class="badges">)(<span class="badge" title="BRYME editorial score[^"]*">★ )(\d+(?:\.\d+)?)(\/10 · BRYME Editorial<\/span><\/div>)/;
    if (badgeRe.test(s)) {
      s = s.replace(badgeRe, (m, pre, badge, num, post) => {
        const pct = Math.round(parseFloat(num) * 10);
        return `${pre}<span class="badge nm-match">${pct}% Match</span><span class="badge nm-hd">HD</span>${badge}${num}${post}`;
      });
      stats.badges++; changed = true;
    }
    // Cast + Audio section after the movie-hero section
    const { actors, langs } = extractCastAndLangs(s);
    if (actors.length || langs.length) {
      const castHtml = actors.length
        ? `<div class="nm-extra-head">Cast</div><div class="nm-cast-row">${actors.map(n =>
            `<div class="nm-cast-item"><span class="nm-avatar">${esc(initials(n))}</span><b>${esc(n)}</b></div>`).join('')}</div>`
        : '';
      const langsList = langs.length ? langs : ['English'];
      const langHtml = `<div class="nm-extra-head">Audio</div><div class="nm-lang-tabs">${langsList.map((l, i) =>
        `<button type="button" class="nm-lang${i === 0 ? ' is-on' : ''}">${esc(l)}</button>`).join('')}</div>`;
      const extra = `<section class="nm-detail-extra"><div class="shell">${castHtml}${langHtml}</div></section>`;
      const hStart = s.indexOf('<section class="movie-hero');
      if (hStart > -1) {
        const hEnd = s.indexOf('</section>', hStart);
        if (hEnd > -1 && s.indexOf('nm-detail-extra') === -1) {
          s = s.slice(0, hEnd + '</section>'.length) + extra + s.slice(hEnd + '</section>'.length);
          changed = true;
        }
      }
    }
    // More Like This header
    const ml = /<h2>[^<]*If you like this[^<]*<\/h2>/;
    if (ml.test(s)) {
      s = s.replace(ml, '<h2>More Like This</h2>');
      stats.morelike++; changed = true;
    }
  }

  if (changed) fs.writeFileSync(file, s);
}

console.log(JSON.stringify(stats, null, 2));
console.log('files scanned:', htmls.length);

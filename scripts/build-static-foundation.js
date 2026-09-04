#!/usr/bin/env node
/* SAFETY GUARD: this legacy generator rewrites thousands of compiled pages.
 * Use scripts/build-focus-site.py plus scripts/apply-audit-remediation.py for
 * normal work. A deliberate migration must set ALLOW_DESTRUCTIVE_BUILD=1 and
 * review the resulting route-count diff before commit. */
if (process.env.ALLOW_DESTRUCTIVE_BUILD !== '1') {
  console.error('Refusing destructive legacy build. Set ALLOW_DESTRUCTIVE_BUILD=1 only for an explicitly reviewed migration.');
  process.exit(2);
}
/* Build indexable static movie, series, anime, genre, year and article pages.
   The legacy hash app (legacy/index.html) remains untouched.
   Frontend architecture: types are separated (/movies, /series, /anime),
   trending is a transparent editorial+algorithmic score, genres are per-type. */
const fs = require('fs'), path = require('path'), vm = require('vm');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'legacy', 'index.html'), 'utf8');
const script = html.match(/<script>\n([\s\S]*)<\/script>\s*<\/body>/)[1];
const dataSource = script.slice(0, script.indexOf('/* ============ HELPERS'));
const ctx = {};
vm.createContext(ctx);
vm.runInContext(dataSource, ctx, { timeout: 1000 });

const config = JSON.parse(fs.readFileSync(path.join(root, 'site.config.json'), 'utf8'));
const site = { name: config.siteName, url: String(config.siteUrl).replace(/\/$/, ''), description: config.siteDescription };
if (!/^https:\/\/[^\s]+$/i.test(site.url)) throw new Error('site.config.json requires an absolute https siteUrl.');
const CURRENT_YEAR = new Date().getFullYear();
const clean = v => String(v || '').replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
const slugify = v => clean(v).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const esc = v => String(v ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
/* Internal links are root-relative so the site works from any host (Render today,
   a custom domain later). absUrl() builds absolute production URLs where the web
   requires them (canonical, og:url, sitemap, robots, structured data). */
const url = p => {
  const q = String(p || '/');
  return q.charAt(0) === '/' ? q : '/' + q;
};
const absUrl = p => site.url + url(p);
/* Bing and schema.org reject relative URLs in JSON-LD. SVG is also a poor
   social/schema image (Facebook/Bing want jpg/png). Walk every graph we emit. */
const DEFAULT_SOCIAL = '/assets/bryme-card.png';
const SCHEMA_URL_KEYS = new Set(['url','image','item','mainEntityOfPage','sameAs','logo','contentUrl','thumbnailUrl','embedUrl','@id']);
function schemaAbsValue(v){
  if (typeof v !== 'string' || !v) return v;
  let out = v;
  if (out.startsWith('/') && !out.startsWith('//')) out = absUrl(out);
  if (/\.svg(\?|#|$)/i.test(out) && /\/assets\//.test(out)) out = absUrl(DEFAULT_SOCIAL);
  return out;
}
function normalizeSchema(node){
  if (Array.isArray(node)) return node.map(normalizeSchema);
  if (!node || typeof node !== 'object') return node;
  const out = {};
  for (const [k, v] of Object.entries(node)) {
    if (typeof v === 'string' && (SCHEMA_URL_KEYS.has(k) || /Url$|URL$/.test(k))) out[k] = schemaAbsValue(v);
    else out[k] = normalizeSchema(v);
  }
  return out;
}
function socialCardUrl(img){
  if (!img) return absUrl(DEFAULT_SOCIAL);
  const abs = /^https?:\/\//i.test(img) ? img : absUrl(img);
  if (/\.svg(\?|#|$)/i.test(abs)) return absUrl(DEFAULT_SOCIAL);
  return abs;
}
function socialMeta(img){
  const src = socialCardUrl(img);
  const isDefault = src.endsWith(DEFAULT_SOCIAL);
  const isYt = /ytimg\.com/.test(src);
  const type = /\.png(\?|#|$)/i.test(src) ? 'image/png' : 'image/jpeg';
  const w = isDefault ? 1200 : (isYt ? 480 : '');
  const h = isDefault ? 630 : (isYt ? 360 : '');
  return `<meta property="og:image" content="${esc(src)}"><meta property="og:image:type" content="${type}">${w ? `<meta property="og:image:width" content="${w}"><meta property="og:image:height" content="${h}">` : ''}<meta property="og:image:alt" content="${esc(site.name)}"><meta name="twitter:image" content="${esc(src)}"><meta name="twitter:image:alt" content="${esc(site.name)}">`;
}
const breadcrumbs = items => ({ '@context':'https://schema.org', '@type':'BreadcrumbList', itemListElement:items.map((item, index) => ({ '@type':'ListItem', position:index+1, name:item.name, item:absUrl(item.path) })) });
const normalizeYouTube = value => {
  const raw = String(value || '').trim();
  if (!raw) return null;
  if (/^[A-Za-z0-9_-]{11}$/.test(raw)) return raw;
  try {
    const parsed = new URL(raw);
    const host = parsed.hostname.replace(/^www\./, '');
    if (host === 'youtu.be') return /^[A-Za-z0-9_-]{11}$/.test(parsed.pathname.slice(1)) ? parsed.pathname.slice(1) : null;
    if (host.endsWith('youtube.com')) {
      const candidate = parsed.searchParams.get('v') || parsed.pathname.match(/\/(?:embed|shorts)\/([A-Za-z0-9_-]{11})/)?.[1];
      return candidate && /^[A-Za-z0-9_-]{11}$/.test(candidate) ? candidate : null;
    }
  } catch (e) {}
  return null;
};
const poster = m => m.poster || (m.youtubeId ? `https://i.ytimg.com/vi/${m.youtubeId}/hqdefault.jpg` : '');
const posterThumb = m => {
  const p = poster(m);
  return p ? String(p).replace('/hqdefault.jpg', '/mqdefault.jpg').replace('/sddefault.jpg', '/mqdefault.jpg') : '';
};

/* A title with neither a poster nor a trailer thumbnail used to render as bare text in a
   grey box, and shipped no og:image at all - so it had no card in Google or on social.
   We will not generate fake poster art for real films. Instead each of these gets a
   designed typographic card: the title set large on a colour derived from its own slug,
   so the grid looks curated rather than broken, and nobody could mistake it for artwork
   from the film. Written once per build to /assets/cards/<slug>.svg. */
const CARD_DIR = path.join(root, 'assets', 'cards');
const CARD_HUES = { movie: [12, 350], series: [214, 190], anime: [276, 320] };
function cardImage(m){
  const typeDir = m.typeDir || 'movie';
  const [h1, h2] = CARD_HUES[typeDir] || CARD_HUES.movie;
  let n = 0; for (const ch of (m.slug || '')) n = (n * 31 + ch.charCodeAt(0)) % 997;
  const a = (h1 + (n % 26) - 13 + 360) % 360, b = (h2 + (n % 18) - 9 + 360) % 360;
  const title = String(m.title || '').trim();
  /* wrap on words so long titles stay inside the card */
  const words = title.split(/\s+/); const lines = []; let cur = '';
  for (const w of words) {
    if ((cur + ' ' + w).trim().length > 15 && cur) { lines.push(cur); cur = w; } else { cur = (cur + ' ' + w).trim(); }
    if (lines.length === 4) break;
  }
  if (cur && lines.length < 4) lines.push(cur);
  const size = lines.length > 3 ? 46 : lines.length > 2 ? 54 : 64;
  const startY = 330 - ((lines.length - 1) * size * 0.62);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="600" height="900" viewBox="0 0 600 900" role="img" aria-label="${esc(title)}">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="hsl(${a},58%,26%)"/><stop offset="1" stop-color="hsl(${b},52%,13%)"/></linearGradient></defs>
<rect width="600" height="900" fill="url(#g)"/>
<rect x="26" y="26" width="548" height="848" fill="none" stroke="rgba(255,255,255,.16)" stroke-width="2" rx="18"/>
<text x="60" y="120" font-family="Georgia,serif" font-size="22" letter-spacing="6" fill="rgba(255,255,255,.62)">BRYME</text>
${lines.map((l, i) => `<text x="60" y="${startY + i * size * 1.16}" font-family="Georgia,serif" font-weight="700" font-size="${size}" fill="#fff">${esc(l)}</text>`).join('\n')}
<text x="60" y="800" font-family="Georgia,serif" font-size="26" fill="rgba(255,255,255,.72)">${esc(String(m.year || ''))}</text>
<text x="60" y="840" font-family="Georgia,serif" font-size="19" letter-spacing="3" fill="rgba(255,255,255,.5)">${esc(typeDir.toUpperCase())}</text>
</svg>`;
  if (!fs.existsSync(CARD_DIR)) fs.mkdirSync(CARD_DIR, { recursive: true });
  fs.writeFileSync(path.join(CARD_DIR, m.slug + '.svg'), svg);
  return '/assets/cards/' + m.slug + '.svg';
}
/* poster() for display: real poster, then trailer thumbnail, then the designed card */
const posterOrCard = m => poster(m) || cardImage(m);

const warnings = [];
const existing = new Set();
const movies = [...ctx.LIB, ...ctx.ANIME].map((raw, i) => {
  let slug = slugify(raw.title); if (existing.has(slug)) slug += '-' + raw.year; existing.add(slug);
  const isRich = raw.about || raw.teaser;
  const youtubeId = normalizeYouTube(raw.ytId);
  return {
    id: raw.id, title: clean(raw.title), slug, description: clean(raw.about || raw.teaser || ''), year: Number(raw.year) || null,
    genre: clean(raw.genre), country: null, language: null,
    poster: youtubeId ? `https://i.ytimg.com/vi/${youtubeId}/hqdefault.jpg` : null,
    backdrop: null,
    trailer: youtubeId ? `https://www.youtube.com/watch?v=${youtubeId}` : null, youtubeId,
    cast: [], legacyCastNotes: Array.isArray(ctx.CAST?.[raw.id]) ? ctx.CAST[raw.id].map(clean) : [], director: null, runtime: null,
    rating: raw.score == null ? null : { value: raw.score, source: 'BRYME editorial score' },
    status: 'published', createdAt: null, updatedAt: null, legacyType: raw.genre === 'Anime' ? 'legacy-anime' : (raw.genre === 'Series' ? 'legacy-series' : 'movie'), typeDir: raw.genre === 'Anime' ? 'anime' : (raw.genre === 'Series' ? 'series' : 'movie'),
    teaser: clean(raw.teaser || ''), facts: Array.isArray(raw.facts) ? raw.facts.map(clean) : [],
    watchLinks: Array.isArray(raw.links) ? raw.links.map(x => ({ name: clean(x.name), url: x.url })) : []
  };
});
const cataloguePath = path.join(root, 'content', 'catalogue.json');
if (fs.existsSync(cataloguePath)) {
  const additional = JSON.parse(fs.readFileSync(cataloguePath, 'utf8'));
  const ids = new Set(movies.map(m => m.id)), slugs = new Set(movies.map(m => m.slug));
  additional.forEach(record => {
    if (!record || record.status !== 'published') return;
    if (!record.id || !record.title || !record.slug || !record.description || !record.year || !record.genre) throw new Error(`Invalid catalogue record: ${record && record.id || 'unknown'}`);
    if (ids.has(record.id) || slugs.has(record.slug)) throw new Error(`Duplicate catalogue record: ${record.id}`);
    const youtubeId = normalizeYouTube(record.youtubeId || record.trailer);
    movies.push({ id:record.id, title:clean(record.title), slug:slugify(record.slug), description:clean(record.description), year:Number(record.year), genre:clean(record.genre), country:record.country||null, language:record.language||null, poster:record.poster||null, backdrop:record.backdrop||null, trailer:youtubeId?`https://www.youtube.com/watch?v=${youtubeId}`:null, youtubeId, cast:Array.isArray(record.cast)?record.cast:[], director:record.director||null, runtime:record.runtime||null, rating:record.rating||null, status:'published', createdAt:record.createdAt||null, updatedAt:record.updatedAt||null, legacyType: record.genre === 'Anime' ? 'legacy-anime' : (record.genre === 'Series' ? 'legacy-series' : 'movie'), typeDir: record.genre === 'Anime' ? 'anime' : (record.genre === 'Series' ? 'series' : 'movie'), teaser:clean(record.description), facts:[], watchLinks:[] });
    ids.add(record.id); slugs.add(record.slug);
  });
}

/* ------------------------------------------------------------------ */
/* Verified title metadata overlay (content/title-metadata.json)      */
/* ------------------------------------------------------------------ */
/* Director, cast, runtime, country and language sourced from Wikidata
   (CC0 structured data) by scripts/enrich-wikidata.py. The overlay only
   FILLS BLANKS — any value already present in the catalogue or in the
   legacy data wins, so editorial corrections are never overwritten.
   Each enriched record keeps the Wikidata id and Wikipedia link so the
   title page can say where the facts came from. */
const titleMetaPath = path.join(root, 'content', 'title-metadata.json');
let titleMeta = {};
if (fs.existsSync(titleMetaPath)) titleMeta = JSON.parse(fs.readFileSync(titleMetaPath, 'utf8'));
const titleEditorialsPath = path.join(root, 'content', 'title-editorials.json');
let TITLE_EDITORIALS = {};
if (fs.existsSync(titleEditorialsPath)) {
  try { TITLE_EDITORIALS = JSON.parse(fs.readFileSync(titleEditorialsPath, 'utf8')); } catch (e) { warnings.push('title-editorials.json unreadable'); }
}
if (TITLE_EDITORIALS._comment) delete TITLE_EDITORIALS._comment;
const editorialOf = m => (m && TITLE_EDITORIALS[m.slug]) || null;
let enrichedCount = 0;
movies.forEach(m => {
  const meta = titleMeta[m.id];
  if (!meta) return;
  let used = false;
  if (!m.director && meta.director) { m.director = clean(meta.director); used = true; }
  if ((!m.cast || !m.cast.length) && Array.isArray(meta.cast) && meta.cast.length) { m.cast = meta.cast.map(clean); used = true; }
  if (!m.runtime && meta.runtime) { m.runtime = clean(meta.runtime); used = true; }
  if (meta.runtimeSource && meta.runtimeSource.url) m.runtimeSource = meta.runtimeSource;
  if (!m.country && meta.country) { m.country = clean(meta.country); used = true; }
  if (!m.language && meta.language) { m.language = clean(meta.language); used = true; }
  /* Description is the ONE field the overlay may overwrite. The fact merge above only
     fills blanks because Wikidata must never clobber an editorial correction - but a
     description in the overlay IS the editorial correction, hand-written to replace a
     catalogue line that stopped too early. Facts fill gaps; prose is deliberate. */
  if (typeof meta.description === 'string' && meta.description.trim().length > 12) {
    m.description = clean(meta.description);
  }
  if (used && meta.source) { m.metaSource = meta.source; enrichedCount++; }
  if (m.cast && m.cast.length && meta.castSource) m.castSource = meta.castSource;
});

/* ------------------------------------------------------------------ */
/* Frontend enrichment (does NOT touch content/catalogue.json)        */
/* ------------------------------------------------------------------ */
const typeGenresPath = path.join(root, 'content', 'type-genres.json');
let typeGenres = {};
if (fs.existsSync(typeGenresPath)) typeGenres = JSON.parse(fs.readFileSync(typeGenresPath, 'utf8'));
/* ================================================================
   RANKINGS — three independent, editorially controlled concepts:
     🔥 TRENDING NOW  (content/rankings.json -> trending, per type)
     ⭐ POPULAR       (content/rankings.json -> popular, per type)
     👑 EDITOR'S PICKS (content/rankings.json -> editorPicks)
   Trending is NOT derived from scores/ratings/recency. Real traffic
   analytics can replace it later without changing this file's shape.
   ================================================================ */
const rankingsPath = path.join(root, 'content', 'rankings.json');
let rankings = {};
if (fs.existsSync(rankingsPath)) { try { rankings = JSON.parse(fs.readFileSync(rankingsPath, 'utf8')); } catch (e) { warnings.push('rankings.json unreadable'); } }
const slugIndex = new Map(movies.map(m => [m.slug, m]));
const TODAY = new Date().toISOString().slice(0, 10); // YYYY-MM-DD for trendingUntil expiry

const RANK_FIELDS = { trending: 'trendingRank', popular: 'popularRank', editorPicks: 'editorPickRank' };
function resolveRankList(entries, kind, typeDir) {
  const out = [];
  (entries || []).forEach(e => {
    if (!e || !e.slug) { warnings.push(`rankings.json: ${kind} entry missing slug`); return; }
    const rec = slugIndex.get(e.slug);
    if (!rec) { warnings.push(`rankings.json: ${kind} unknown slug "${e.slug}"`); return; }
    if (typeDir && rec.typeDir !== typeDir) warnings.push(`rankings.json: ${kind} type mismatch for "${e.slug}" (expected ${typeDir}, record is ${rec.typeDir})`);
    if (e.title && clean(e.title).toLowerCase() !== rec.title.toLowerCase()) warnings.push(`rankings.json: ${kind} title mismatch for "${e.slug}" (config says "${e.title}", catalogue says "${rec.title}")`);
    if (e.until && String(e.until) < TODAY) { warnings.push(`rankings.json: ${kind} "${e.slug}" expired (until ${e.until}) — excluded`); return; }
    const rankField = RANK_FIELDS[kind] || 'rank';
    out.push({ slug: e.slug, rank: Number(e[rankField] ?? e.rank) || out.length + 1, until: e.until || null, note: e.note || null, badge: e.badge || null });
  });
  out.sort((a, b) => a.rank - b.rank);
  return out;
}
const heroCfg = (rankings.hero && slugIndex.has(rankings.hero.slug)) ? rankings.hero : null;
const trendingCfg = { movie: resolveRankList(rankings.trending && rankings.trending.movie, 'trending', 'movie'), series: resolveRankList(rankings.trending && rankings.trending.series, 'trending', 'series'), anime: resolveRankList(rankings.trending && rankings.trending.anime, 'trending', 'anime') };
const popularCfg = { movie: resolveRankList(rankings.popular && rankings.popular.movie, 'popular', 'movie'), series: resolveRankList(rankings.popular && rankings.popular.series, 'popular', 'series'), anime: resolveRankList(rankings.popular && rankings.popular.anime, 'popular', 'anime') };
const editorCfg = resolveRankList(rankings.editorPicks, 'editorPicks', null);
const animeFilms = new Set((typeGenres.anime || {}).films || []);

const typeLabelOf = d => d === 'series' ? 'TV Series' : (d === 'anime' ? 'Anime' : 'Movie');
movies.forEach(m => {
  const tgs = (typeGenres[m.typeDir] || {})[m.slug];
  if (tgs && (!Array.isArray(tgs) || tgs.length === 0)) warnings.push(`type-genres.json: empty genres for ${m.slug}`);
  m.genres = Array.isArray(tgs) ? tgs.slice(0, 3) : [];
  m.typeLabel = typeLabelOf(m.typeDir);
  // Structured ranking fields (all editorial, deterministic)
  const tr = trendingCfg[m.typeDir].find(x => x.slug === m.slug);
  m.trending = !!tr;
  m.trendingRank = tr ? tr.rank : null;
  m.trendingUntil = tr ? tr.until : null;
  m.trendingNote = tr ? tr.note : null;
  m.trendingBadge = tr ? tr.badge : null;
  const pr = popularCfg[m.typeDir].find(x => x.slug === m.slug);
  m.popular = !!pr;
  m.popularRank = pr ? pr.rank : null;
  m.popularityScore = pr ? Math.max(1, 101 - pr.rank) : null;
  const ep = editorCfg.find(x => x.slug === m.slug);
  m.editorPick = !!ep;
  m.editorPickRank = ep ? ep.rank : null;
  m.editorPickNote = ep ? ep.note : null;
  m.isFeatured = !!(heroCfg && heroCfg.slug === m.slug);
  m.isNewRelease = !!m.year && m.year >= CURRENT_YEAR - 2;
});
if (heroCfg && !slugIndex.has(heroCfg.slug)) warnings.push('rankings.json: hero slug not found');

/* ------------------------------------------------------------------ */
/* Trailer system: multi-candidate verified trailers                   */
/* Priority: official-trailer > official-teaser > official-clip > fan-made > unavailable */
/* ------------------------------------------------------------------ */
// Raw IDs from catalogue.json + legacy (source of truth), written BEFORE any
// audit filtering so the audit can always re-verify every known video ID.
fs.mkdirSync(path.join(root, 'data'), {recursive:true});
fs.writeFileSync(path.join(root, 'data', 'trailer-sources.json'), JSON.stringify(movies.map(m => ({ slug: m.slug, title: m.title, youtubeIds: [m.youtubeId].filter(Boolean) })), null, 1) + '\n');
const TRAILER_PRIORITY = { 'official-trailer': 0, 'official-teaser': 1, 'official-clip': 2, 'fan-made': 3 };
const TRAILER_LABELS = {
  'official-trailer': 'Official Trailer',
  'official-teaser': 'Official Teaser',
  'official-clip': 'Official Clip',
  'fan-made': 'Community trailer'
};
const TRAILER_PATHS = {
  'official-trailer': '/movies/',
  'official-teaser': '/movies/',
  'official-clip': '/movies/',
  'fan-made': '/movies/'
};
let trailerAudit = {}, trailerOverrides = {};
const trailerAuditPath = path.join(root, 'content', 'trailer-audit.json');
if (fs.existsSync(trailerAuditPath)) { try { trailerAudit = JSON.parse(fs.readFileSync(trailerAuditPath, 'utf8')); } catch (e) { warnings.push('trailer-audit.json unreadable'); } }
const trailerOverridesPath = path.join(root, 'content', 'trailers.json');
if (fs.existsSync(trailerOverridesPath)) { try { trailerOverrides = JSON.parse(fs.readFileSync(trailerOverridesPath, 'utf8')); } catch (e) { warnings.push('trailers.json unreadable'); } }
const videoEditorialPath = path.join(root, 'content', 'video-editorial.json');
let VIDEO_EDITORIAL = {};
if (fs.existsSync(videoEditorialPath)) {
  try {
    const rawEd = JSON.parse(fs.readFileSync(videoEditorialPath, 'utf8'));
    VIDEO_EDITORIAL = (rawEd && rawEd.pages) ? rawEd.pages : (rawEd || {});
    if (VIDEO_EDITORIAL._comment) delete VIDEO_EDITORIAL._comment;
  } catch (e) { warnings.push('video-editorial.json unreadable'); }
}
function trailerEditorial(m, videoId){
  const extra = VIDEO_EDITORIAL[m && m.slug];
  if (!extra || extra.videoId !== videoId) return { caption: '', context: '', wrap: false };
  const caption = extra.figcaption ? `<figcaption>${esc(extra.figcaption)}</figcaption>` : '';
  const context = Array.isArray(extra.context) && extra.context.length
    ? `<div class="video-context">${extra.context.map(p => `<p>${esc(p)}</p>`).join('')}</div>` : '';
  return { caption, context, wrap: true };
}
const trailerStats = { official: 0, teaser: 0, clip: 0, fan: 0, missing: 0, broken: 0, brokenList: [] };
movies.forEach(m => {
  const auditRec = trailerAudit[m.slug] || {};
  const override = trailerOverrides[m.slug];
  const candidates = [];
  if (!(override && override.excludeTrailers)) {
    if (override && Array.isArray(override.candidates) && override.candidates.length) {
      override.candidates.forEach(c => {
        if (!c || !/^[A-Za-z0-9_-]{11}$/.test(c.videoId || '')) { warnings.push(`trailers.json: invalid videoId for ${m.slug}`); return; }
        candidates.push({ videoId: c.videoId, type: c.type || 'official-trailer', title: c.title || TRAILER_LABELS[c.type] || 'Trailer', source: c.source || 'YouTube', channel: c.channel || '', verified: !!c.verified, status: c.verified ? 'verified' : 'manual', lastChecked: c.lastChecked || null });
      });
    } else if (auditRec.videoId || (Array.isArray(auditRec.candidates) && auditRec.candidates.length)) {
      const srcList = (Array.isArray(auditRec.candidates) && auditRec.candidates.length) ? auditRec.candidates : [auditRec];
      srcList.forEach(ar => {
        if (!ar || !ar.videoId) return;
        const playable = ar.status === 'verified' || ar.status === 'community';
        candidates.push({
          videoId: ar.videoId,
          type: ar.status === 'community' ? 'fan-made' : (ar.type || 'official-trailer'),
          title: ar.status === 'community' ? 'Community trailer' : (TRAILER_LABELS[ar.type] || 'Trailer'),
          source: 'YouTube',
          channel: ar.channel || '',
          channelClass: ar.channelClass || null,
          verified: playable && ar.status !== 'community' ? true : (ar.status === 'community' ? false : false),
          status: ar.status || 'broken',
          videoTitle: ar.videoTitle || null,
          lastChecked: ar.lastChecked || null
        });
        if (!playable) {
          trailerStats.broken++;
          trailerStats.brokenList.push({ slug: m.slug, title: m.title, videoId: ar.videoId, status: ar.status, channel: ar.channel, videoTitle: ar.videoTitle, lastChecked: ar.lastChecked });
        }
      });
    }
  }
  candidates.sort((a, b) => (TRAILER_PRIORITY[a.type] ?? 9) - (TRAILER_PRIORITY[b.type] ?? 9));
  m.trailers = candidates;
  const playable = candidates.filter(c => c.verified || c.status === 'community' || c.status === 'manual');
  const primary = playable[0] || null;
  m.youtubeId = primary ? primary.videoId : null;
  m.trailer = primary ? `https://www.youtube.com/watch?v=${primary.videoId}` : null;
  m.poster = primary ? `https://i.ytimg.com/vi/${primary.videoId}/hqdefault.jpg` : null;
  m.trailerType = primary ? primary.type : null;
  m.trailerLabel = primary ? TRAILER_LABELS[primary.type] || primary.title : null;
  m.trailerChannel = primary ? primary.channel || '' : '';
  m.trailerVerified = primary ? !!primary.verified : false;
  m.trailerLastChecked = primary ? primary.lastChecked || null : null;
  if (!m.youtubeId) trailerStats.missing++;
  else if (m.trailerType === 'official-trailer') trailerStats.official++;
  else if (m.trailerType === 'official-teaser') trailerStats.teaser++;
  else if (m.trailerType === 'official-clip') trailerStats.clip++;
  else trailerStats.fan++;
});
const trailerAdminRows = movies.map(m => {
  let status = m.youtubeId ? (m.trailerType === 'fan-made' ? 'fan-made' : 'official') : 'none';
  if (!status || status === 'none') {
    const bad = (m.trailers || []).filter(t => !t.verified && t.status && t.status !== 'manual');
    if (bad.length) status = 'broken';
  }
  return {
    slug: m.slug, title: m.title, typeDir: m.typeDir,
    status,
    trailerType: m.trailerType || null,
    label: m.trailerLabel || null,
    videoId: m.youtubeId || null,
    channel: m.trailerChannel || null,
    verified: m.trailerVerified,
    lastChecked: m.trailerLastChecked || null,
    candidates: (m.trailers || []).map(t => ({ id: t.videoId, type: t.type, channel: t.channel || '', verified: !!t.verified, status: t.status || null }))
  };
});
const bySlug = slug => slugIndex.get(slug) || null;
const resolveList = cfg => cfg.map(x => bySlug(x.slug)).filter(Boolean);
const hero = heroCfg ? bySlug(heroCfg.slug) : movies.filter(m => m.typeDir === 'movie').sort((a,b) => (b.rating?.value||0) - (a.rating?.value||0))[0];

/* ================================================================
   HOMEPAGE HERO CAROUSEL + RECOMMENDATION ENGINE (client-side data)
   Hero slides are configured in content/homepage.json (slugs only —
   catalogue data is reused). Rec data is embedded for a no-backend
   similarity engine; the engine can be swapped for a real AI service
   later without changing the page structure.
   ================================================================ */
const homepageCfgPath = path.join(root, 'content', 'homepage.json');
let homepageCfg = {};
if (fs.existsSync(homepageCfgPath)) { try { homepageCfg = JSON.parse(fs.readFileSync(homepageCfgPath, 'utf8')); } catch (e) { warnings.push('homepage.json unreadable'); } }
const heroSlides = (homepageCfg.hero || []).map(item => {
  const rec = slugIndex.get(item.slug);
  if (!rec) { warnings.push(`homepage.json: unknown hero slug "${item.slug}" — excluded`); return null; }
  if (!rec.youtubeId || !rec.poster) { warnings.push(`homepage.json: hero "${item.slug}" has no verified trailer/poster — excluded`); return null; }
  return {
    slug: rec.slug, title: rec.title, typeDir: rec.typeDir, typeLabel: rec.typeLabel,
    year: rec.year, genres: rec.typeDir === 'movie' ? [rec.genre] : rec.genres,
    genreLabel: rec.typeDir === 'movie' ? rec.genre : ((rec.genres || [])[0] || rec.genre),
    poster: rec.poster, youtubeId: rec.youtubeId, trailer: rec.trailer,
    rating: (rec.rating && rec.rating.value != null) ? rec.rating.value : null,
    description: rec.description || rec.teaser || '', tagline: item.tagline || null,
    url: url('/' + rec.typeDir + '/' + rec.slug + '/')
  };
}).filter(Boolean).slice(0, 6);
if (!heroSlides.length) warnings.push('homepage.json: no valid hero slides configured — hero falls back to the rankings hero.');
const heroSlide = heroSlides[0] || hero;

// --- recommendation engine embedded data ---
const STOPWORDS = new Set(('the a an and or but of to in on for with from by is are was were his her their its it he she they you your we our as at be been being has have had not no so if than then that this these those when who which into after before about against between over under again once only own same such very just but what all can will would could should may might must do does did done get gets got go goes one two new now also much many more most some any other another each few both first last long great good big small high low old young man men woman women people world life time way thing things story stories series movie movies anime film films show shows watch watching watchlist making made make like likes love loves become becomes became find finds found take takes took keep keeps kept comes come came know knows known see sees saw say says said think thinks thought want wants need needs help helps start starts started end ends ended turn turns turned fight fights fought follow follows followed face faces faced bring brings brought leave leaves left return returns returned reveal reveals revealed discover discovers discovered experience experiences feel feels felt grow grows grew growing powerful power powers dead death deaths die dies died kill kills killed survive survives survived survival escape escapes escaped freedom dark darkest magic worlds years year episode episodes season seasons part parts final real really actually entire everything something nothing anything everyone someone nobody somebody ever never always still even though without within along around away back behind below beside beyond down during inside near off onto outside past since through throughout toward towards underneath until up upon via with according across almost amid among apart appear appears appeared approximately around asked asking became began begin begins begun being believe believes best better between both brief briefly came cannot cause causes certain certainly clearly could differ different differently doing done dont down downwards during each either else elsewhere enough etc every everybody everywhere except few for former formerly from further gave give given gives going got had happen happens hardly here how however immediately important in indeed instead into itself just least less lest let lets likely little look looked looking looks mainly many maybe meantime meanwhile might mine more moreover most mostly much must namely neither never nevertheless none nor normally not nothing nowhere obviously often oh ok okay old once ones only onto or other others otherwise ought our out over overall own per perhaps please plus possible presumably probably quite rather regardless relatively right said same saw saying says seem seemed seeming seems seen shall shortly showed shown shows significant significantly similar similarly since slightly so somebody somehow someone something sometimes somewhat somewhere soon specifically still stopped such suddenly suppose supposed than thee their theirs them themselves then thence there thereafter thereby therefore therein thereupon these they thick thin third this those though three through thru thus to together too took toward towards tried tries truly try trying twice under underneath unfortunately unless unlike unlikely until unto up upon us use used useful uses using usually various very via viz was way we well went were what whatever when whence whenever where whereafter whereas whereby wherein whereupon wherever whether which while whither who whoever whole whom whomever whose why will willing wish within without wonder would yet yours yourself yourselves').split(' '));
function descKeywords(text){
  if (!text) return [];
  const counts = {};
  String(text).toLowerCase().replace(/[^a-z0-9\s-]/g, ' ').split(/\s+/).forEach(w => {
    if (w.length >= 4 && !STOPWORDS.has(w)) counts[w] = (counts[w] || 0) + 1;
  });
  return Object.keys(counts).sort((a, b) => counts[b] - counts[a]).slice(0, 8);
}
const recItems = movies.filter(m => m.status === 'published').map(m => ({
  s: m.slug, t: m.title, y: m.year || null, ty: m.typeDir,
  g: m.typeDir === 'movie' ? [m.genre] : m.genres,
  p: m.poster,
  r: (m.rating && m.rating.value != null) ? m.rating.value : null,
  k: descKeywords(m.description || m.teaser).slice(0, 6)
}));
const homeRelationsPath = path.join(root, 'content', 'title-relationships.json');
let homeRelations = {};
if (fs.existsSync(homeRelationsPath)) { try { homeRelations = JSON.parse(fs.readFileSync(homeRelationsPath, 'utf8')); } catch (e) {} }
if (homeRelations._comment) delete homeRelations._comment;
const homePopular = ['movie', 'series', 'anime'].flatMap(td => (popularCfg[td] || []).map(x => x.slug)).slice(0, 9);
const recEmbed = JSON.stringify({ items: recItems, relations: homeRelations, popular: homePopular }).replace(/</g, '\\u003c');
fs.writeFileSync(path.join(root, 'data', 'rec-data.json'), JSON.stringify({ items: recItems, relations: homeRelations, popular: homePopular }));
// Trending: ONLY editorially flagged titles, ordered by trendingRank ASC.
// No scores, no recency, no random selection. Deterministic.
const trendingByType = {
  movie: resolveList(trendingCfg.movie),
  series: resolveList(trendingCfg.series),
  anime: resolveList(trendingCfg.anime)
};
const trendingList = [...trendingByType.movie, ...trendingByType.series, ...trendingByType.anime];
const popularByType = {
  movie: resolveList(popularCfg.movie),
  series: resolveList(popularCfg.series),
  anime: resolveList(popularCfg.anime)
};
const popularList = [...popularByType.movie, ...popularByType.series, ...popularByType.anime];
const editorPicksList = resolveList(editorCfg);
const newReleases = [...movies].sort((a,b) => ((b.year||0) - (a.year||0)) || a.title.localeCompare(b.title)).filter(m => m.isNewRelease);
const classics = movies.filter(m => m.year && m.year <= 2000).sort((a,b) => ((b.rating?.value||0) - (a.rating?.value||0)) || ((b.year||0) - (a.year||0)));
// Browse rows on the homepage: plain editorial-score ordering, NOT labelled
// as Trending/Popular — just a convenient way to keep exploring.
const sortPopular = (a,b) => ((b.rating?.value||0) - (a.rating?.value||0)) || ((b.year||0) - (a.year||0)) || a.title.localeCompare(b.title);
const sortNewest = (a,b) => ((b.year||0) - (a.year||0)) || a.title.localeCompare(b.title);
const sortAZ = (a,b) => a.title.localeCompare(b.title);

/* ------------------------------------------------------------------ */
/* Data outputs                                                       */
/* ------------------------------------------------------------------ */
fs.mkdirSync(path.join(root, 'data'), {recursive:true});
fs.mkdirSync(path.join(root, 'reports'), {recursive:true});
fs.writeFileSync(path.join(root, 'data/movies.json'), JSON.stringify(movies, null, 2)+'\n');
const youtubeAudit = movies.map(m => ({ id:m.id, title:m.title, youtubeId:m.youtubeId, status:m.youtubeId ? 'valid-id' : 'unavailable', watchUrl:m.trailer })).sort((a,b)=>a.status.localeCompare(b.status));
fs.writeFileSync(path.join(root, 'reports/youtube-audit.json'), JSON.stringify({ generatedAt:new Date().toISOString(), total:youtubeAudit.length, valid:youtubeAudit.filter(v=>v.status==='valid-id').length, unavailable:youtubeAudit.filter(v=>v.status==='unavailable').length, records:youtubeAudit }, null, 2)+'\n');
const trailerReport = {
  generatedAt: new Date().toISOString(),
  totalTitles: movies.length,
  officialTrailers: trailerStats.official,
  officialTeasers: trailerStats.teaser,
  officialClips: trailerStats.clip,
  fanMade: trailerStats.fan,
  titlesWithVerifiedTrailer: trailerStats.official + trailerStats.teaser + trailerStats.clip + trailerStats.fan,
  noCandidateAtAll: movies.filter(m => !(m.trailers || []).length).length,
  noVerifiedTrailer: trailerStats.missing,
  brokenUnavailable: trailerStats.broken,
  brokenList: trailerStats.brokenList,
  note: 'Counts reflect the primary (highest-priority) trailer per title. Fan-made videos are only used as a fallback and are labelled as community-created on the site. noVerifiedTrailer includes titles with broken/wrong candidates.'
};
fs.writeFileSync(path.join(root, 'reports', 'trailer-report.json'), JSON.stringify(trailerReport, null, 2) + '\n');
fs.writeFileSync(path.join(root, 'data', 'trailer-report.json'), JSON.stringify(trailerReport, null, 2) + '\n');
fs.writeFileSync(path.join(root, 'data', 'trailers.json'), JSON.stringify(trailerAdminRows, null, 2) + '\n');
fs.writeFileSync(path.join(root, 'data', 'trending.json'), JSON.stringify({ generatedAt:new Date().toISOString(), mode:'editorial-curation', note:'Trending Now is editorially curated (content/rankings.json). No live traffic data is claimed. When real analytics exist, Trending Score = recent engagement + growth rate + searches + clicks + recency can replace this list without changing the site architecture.', futureSignals:['pageViews','searches','cardClicks','trailerClicks','watchInteractions','favorites','shares','recentGrowth'], records:trendingList.map(m => ({ slug:m.slug, title:m.title, typeDir:m.typeDir, year:m.year, trendingRank:m.trendingRank, trendingUntil:m.trendingUntil })) }, null, 2)+'\n');

const legacyArticleCategories = { 'broke-internet':'Movie Facts', 'never-end':'Movie Recommendations', 'agent-kim':'Movie Explainers', 'korean-movies':'Movie Recommendations', 'vampire-horror':'Movie Facts' };
let articles = (ctx.ARTICLES || []).map(a => ({ id:a.id, slug:slugify(a.title), title:clean(a.title), description:clean(a.intro), category:legacyArticleCategories[a.id] || 'Editorial', tags:(a.tags||[]).map(clean), emoji:a.emoji || '', items:(a.items||[]).map(x=>({heading:clean(x.h), body:clean(x.p)})), relatedMovieSlugs:[], status:'archived', updatedAt:null, createdAt:null }));
const authoredEditorialPath = path.join(root, 'content', 'editorial.json');
if (fs.existsSync(authoredEditorialPath)) {
  const authoredEditorial = JSON.parse(fs.readFileSync(authoredEditorialPath, 'utf8'));
  authoredEditorial.forEach(a => articles.push({ id:a.id, slug:a.slug, title:clean(a.title), description:clean(a.excerpt), category:clean(a.category), tags:(a.tags||[]).map(clean), emoji:'', items:(a.content||[]).map(x=>({heading:clean(x.heading), body:clean(x.body)})), blocks:(a.blocks||[]).map(x=>({type:x.type||'paragraph', text:String(x.text||'')})), relatedMovieSlugs:a.relatedMovieSlugs||[], status:a.status||'draft', author:a.author||null, createdAt:a.publishedAt||null, updatedAt:a.updatedAt||null }));
}
articles = articles.filter(a => a.status === 'published');
fs.writeFileSync(path.join(root, 'data/articles.json'), JSON.stringify(articles, null, 2)+'\n');
const topicSourcePath = path.join(root, 'content', 'topics.json');
const topics = fs.existsSync(topicSourcePath) ? JSON.parse(fs.readFileSync(topicSourcePath, 'utf8')).filter(t => t.status === 'published') : [];
fs.writeFileSync(path.join(root, 'data/topics.json'), JSON.stringify(topics, null, 2)+'\n');
const searchIndex = { movies: movies.filter(m => m.status === 'published').map(m => ({type:m.typeDir||'movie',title:m.title,slug:m.slug,year:m.year,genre:m.genre,genres:m.genres,country:m.country,language:m.language,poster:m.poster,trailerStatus:m.youtubeId ? (m.trailerType === 'fan-made' ? 'fan-made' : 'official') : 'none'})), articles: articles.map(a => ({type:'article',title:a.title,slug:a.slug,description:a.description,category:a.category,tags:a.tags})), topics: topics.map(t => ({type:'topic',title:t.title,slug:t.slug,description:t.description})) };
fs.writeFileSync(path.join(root, 'data/search-index.json'), JSON.stringify(searchIndex)+'\n');

/* ------------------------------------------------------------------ */
/* Stylesheet                                                         */
/* ------------------------------------------------------------------ */
const css = `:root{--bg:#08090b;--panel:#111419;--line:#272b31;--text:#f4f5f6;--muted:#9aa1a9;--accent:#e94b2c;--gold:#e7bb5c;--movie:#e94b2c;--series:#4f8ef7;--anime:#b06ef7;--sports:#3ddc84;--memes:#ffd24a;--money:#e7bb5c;--tech:#4f8ef7;--ent:#e94b2c}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:inherit;text-decoration:none}img{max-width:100%}.shell{max-width:1180px;margin:auto;padding:0 20px}.top{position:sticky;top:0;z-index:40;background:rgba(8,9,11,.94);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}.top .shell{min-height:62px;display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{font-weight:900;letter-spacing:.1em;font-size:17px;white-space:nowrap}.brand b{color:var(--accent)}.topnav{display:flex;gap:16px;overflow-x:auto;font-size:13px;font-weight:700;color:var(--muted);scrollbar-width:none}.topnav::-webkit-scrollbar{display:none}.topnav a:hover{color:#fff}.topnav a.active{color:#fff}.nav-search{color:var(--gold)!important}.hero{padding:64px 0 40px;background:radial-gradient(600px 260px at 70% 0,rgba(233,75,44,.15),transparent 70%)}.eyebrow{color:var(--gold);font-size:12px;font-weight:800;letter-spacing:.14em;text-transform:uppercase}.hero h1{font-size:clamp(32px,6vw,60px);line-height:1.05;max-width:850px;margin:10px 0 14px}.lead{max-width:680px;color:var(--muted);font-size:17px}.section{padding:26px 0}.section h2{font-size:22px;margin:0 0 14px}.section-head{display:flex;align-items:end;justify-content:space-between;gap:16px;margin:0 0 14px}.section-head h2{font-size:clamp(21px,3vw,28px);margin:0;line-height:1.15}.section-head>a{font-size:12px;font-weight:800;color:var(--gold);white-space:nowrap}.section-note{font-size:12px;color:var(--muted);margin:-8px 0 14px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(148px,1fr));gap:16px}.grid-2{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px}.crumb{padding:22px 0 0;color:var(--muted);font-size:13px}.crumb a:hover{color:#fff}.poster{aspect-ratio:2/3;background:#171b20;border:1px solid var(--line);overflow:hidden;border-radius:4px;box-shadow:0 12px 28px rgba(0,0,0,.22);position:relative}.poster img{width:100%;height:100%;object-fit:cover;display:block}.placeholder{height:100%;display:grid;place-items:center;padding:16px;text-align:center;font-weight:800;font-size:13px;background:linear-gradient(145deg,#242b35,#0d0f13)}.tile{min-width:0;display:block;transition:transform .25s ease}.tile:hover{transform:translateY(-5px)}.tile h3{font-size:13.5px;margin:8px 0 0;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.6em}.tile-meta{display:flex;align-items:center;gap:6px;flex-wrap:wrap;font-size:11.5px;color:var(--muted);margin:4px 0 0}.tile-meta .sep{opacity:.5}.tile-rating{font-size:11px;color:var(--gold);margin:3px 0 0;font-weight:700}.type-badge{display:inline-block;font-size:9.5px;font-weight:900;letter-spacing:.07em;padding:2.5px 6px;border-radius:3px;line-height:1;text-transform:uppercase;color:#0a0b0d}.tb-movie{background:var(--movie)}.tb-series{background:var(--series)}.tb-anime{background:var(--anime)}.tb-sports{background:var(--sports)}.tb-memes{background:var(--memes);color:#14171d}.tb-money{background:var(--money);color:#14171d}.tb-tech{background:var(--tech)}.tb-ent{background:var(--ent)}.rank{position:absolute;top:6px;left:6px;z-index:2;background:rgba(8,9,11,.82);border:1px solid rgba(255,255,255,.25);color:#fff;font-size:11px;font-weight:900;min-width:22px;height:22px;border-radius:4px;display:grid;place-items:center;padding:0 4px}.rank.top{border-color:var(--gold);color:var(--gold)}.rail{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(148px,182px);overflow-x:auto;gap:14px;padding:2px 1px 14px;scroll-snap-type:x mandatory}.rail .tile{scroll-snap-align:start}.loadmore{display:block;margin:18px auto 0;background:transparent;border:1px solid var(--line);color:var(--text);font:inherit;font-weight:700;padding:11px 22px;border-radius:5px;cursor:pointer}.loadmore:hover{border-color:var(--accent);color:#fff}.count-line{font-size:12.5px;color:var(--muted);margin:0 0 14px}.filterbar{display:flex;flex-wrap:wrap;gap:10px;align-items:end;padding:16px;margin:0 0 22px;background:#101318;border:1px solid var(--line);border-radius:6px}.ffield{display:flex;flex-direction:column;gap:4px;font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}.ffield select{background:#171b20;color:var(--text);border:1px solid var(--line);border-radius:4px;font:inherit;font-size:13px;padding:8px 30px 8px 10px;max-width:190px}.fbtn{background:#171b20;border:1px solid var(--line);color:var(--muted);font:inherit;font-size:12.5px;font-weight:700;border-radius:4px;padding:8px 12px;cursor:pointer}.fbtn:hover{color:#fff;border-color:#444}.fbtn-clear{color:var(--gold)}.movie-hero{padding:34px 0 28px;display:grid;grid-template-columns:190px minmax(0,1fr);gap:28px}.movie-hero .poster{max-height:285px}.movie-hero h1{font-size:clamp(34px,6vw,58px);line-height:1.05;margin:8px 0}.badges{display:flex;flex-wrap:wrap;gap:7px}.badge{border:1px solid var(--line);color:var(--muted);padding:4px 9px;font-size:12px;border-radius:3px}.badge a:hover{color:#fff}.body{display:grid;grid-template-columns:minmax(0,1fr) 290px;gap:42px;padding:22px 0 60px}.prose h2{font-size:20px;margin:28px 0 8px}.prose p{color:#d9dde1}.aside{border-left:1px solid var(--line);padding-left:22px}.aside dt{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em;margin-top:16px}.aside dd{margin:3px 0}.cta{display:inline-block;background:var(--accent);padding:10px 15px;font-weight:800;margin-top:10px;border-radius:4px}.list{border-top:1px solid var(--line)}.row{display:flex;gap:14px;align-items:center;padding:14px 0;border-bottom:1px solid var(--line)}.row .thumb{height:64px;width:45px;background:#171b20;flex:none;border-radius:3px;overflow:hidden}.row .thumb img{height:100%;width:100%;object-fit:cover}.row b{display:block}.footer{border-top:1px solid var(--line);padding:28px 0 92px;color:var(--muted);font-size:13px}.footer-grid{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:26px;margin:0 0 20px}.footer-brand p{margin:10px 0 0;max-width:260px;font-size:12.5px;line-height:1.6}.footer-col{display:flex;flex-direction:column;gap:8px}.footer-col h4{font-size:11px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--text);margin:0 0 4px}.footer-col a{color:var(--muted);font-size:13px}.footer-col a:hover{color:#fff}.footer-note{margin:0 0 14px}@media(max-width:760px){.footer-grid{grid-template-columns:1fr 1fr;gap:18px}.footer-brand{grid-column:1/-1}}.footer .foot-links{display:flex;flex-wrap:wrap;gap:16px;margin:12px 0 18px;font-weight:700}.footer .foot-links a:hover{color:#fff}.footer small{display:block;max-width:720px;line-height:1.6;opacity:.75}.mobile-nav{display:none}@media(max-width:760px){.shell{padding:0 14px}.top .shell{min-height:56px;padding:0 14px}.topnav{display:none}.hero{padding:44px 0 26px}.movie-hero{grid-template-columns:108px minmax(0,1fr);gap:15px}.movie-hero .poster{max-height:162px}.body{display:block}.aside{border-left:0;border-top:1px solid var(--line);padding:16px 0;margin-top:28px}.grid{grid-template-columns:repeat(3,1fr);gap:10px}.rail{grid-auto-columns:128px;gap:10px}.tile h3{font-size:12px;min-height:2.7em}.tile-meta{font-size:10.5px}.filterbar{flex-wrap:nowrap;overflow-x:auto;padding:12px;gap:8px}.ffield select{max-width:150px}.section-head{flex-wrap:wrap}}`;
// Preserve the BRYME design layer (v2..v15) across rebuilds: it lives at the end of
// assets/site.css after the marker below. The base CSS written above would otherwise
// wipe it. Captured before overwrite, re-appended at the end of this build.
let BRYME_DESIGN_LAYER = '';
try {
  const _prev = fs.readFileSync(path.join(root, 'assets/site.css'), 'utf8');
  const _at = _prev.indexOf('BRYME v2');
  if (_at > -1) {
    const _start = _prev.lastIndexOf('/*', _at);
    BRYME_DESIGN_LAYER = (_start > -1 ? _prev.slice(_start) : _prev.slice(_at));
  }
} catch (e) {}
fs.mkdirSync(path.join(root,'assets'),{recursive:true});
fs.writeFileSync(path.join(root,'assets/site.css'), css + '\n' + '.sports-feature{position:relative;display:grid;place-items:center;min-height:390px;margin:0 -20px 10px;padding:42px 24px;overflow:hidden;text-align:center;background:radial-gradient(ellipse at 50% 110%,rgba(61,220,132,.32),transparent 47%),linear-gradient(135deg,#06140d 0%,#0c2016 48%,#080b0d 100%);border-bottom:1px solid rgba(61,220,132,.35);isolation:isolate}.sports-feature:before{content:"";position:absolute;inset:-35% -10% 0;background:repeating-linear-gradient(118deg,transparent 0 74px,rgba(255,255,255,.035) 75px 77px,transparent 78px 152px);transform:skewY(-5deg);z-index:-1}.sports-feature:after{content:"⚽";position:absolute;right:7%;bottom:-20px;font-size:clamp(170px,28vw,350px);line-height:1;color:rgba(255,255,255,.045);z-index:-1}.sports-feature-inner{max-width:760px}.sports-feature .eyebrow{color:#77e9a8}.sports-feature h1{font-size:clamp(38px,6vw,70px);line-height:1.02;letter-spacing:-.035em;margin:12px auto}.sports-feature p{max-width:610px;margin:0 auto;color:#c3d0c8;font-size:clamp(15px,2vw,18px);line-height:1.6}.sports-feature .cta{margin-top:24px;background:#3ddc84;color:#07120b;padding:12px 19px;border-radius:5px}.sports-feature .cta:hover{filter:brightness(1.08)}.sports-feature-meta{display:flex;justify-content:center;gap:10px;flex-wrap:wrap;margin-top:18px}.sports-feature-meta span{font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:#b9c9bf;border:1px solid rgba(255,255,255,.17);border-radius:20px;padding:5px 10px;background:rgba(4,12,8,.34)}@media(max-width:760px){.sports-feature{min-height:365px;margin:0 -14px 6px;padding:38px 18px}.sports-feature h1{font-size:40px}.sports-feature:after{right:-15px;font-size:230px}.sports-feature-meta{gap:7px}}\\n' + `/* Primary platform experience */
.home-hero{min-height:560px;display:flex;align-items:end;position:relative;isolation:isolate;background:#111820}.home-hero:before{content:"";position:absolute;inset:0;z-index:-2;background-image:var(--hero-image);background-size:cover;background-position:center;filter:saturate(.78) contrast(1.08)}.home-hero:after{content:"";position:absolute;inset:0;z-index:-1;background:linear-gradient(90deg,rgba(5,7,10,.96) 0%,rgba(5,7,10,.72) 42%,rgba(5,7,10,.18) 100%),linear-gradient(0deg,#08090b,transparent 52%)}.home-hero-inner{padding-top:120px;padding-bottom:64px;max-width:1180px;width:100%}.home-hero h1{font-size:clamp(42px,7vw,78px);line-height:.96;max-width:720px;margin:10px 0}.home-hero p{max-width:580px;color:#d2d6d9;font-size:16.5px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}.hero-facts{font-size:14px;color:#d3d7d9;display:flex;gap:8px;align-items:center;flex-wrap:wrap}.hero-actions{display:flex;gap:18px;align-items:center;margin-top:22px}.quiet-link{font-weight:750;color:#fff;border-bottom:1px solid rgba(255,255,255,.4);padding:9px 0}.home-main{padding-bottom:30px}.home-section{padding:30px 0}.home-section h2{font-size:clamp(21px,3vw,27px);margin:0}.genre-trio{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.genre-panel{background:#101318;border:1px solid var(--line);border-radius:6px;padding:18px}.genre-panel h3{font-size:15px;margin:0 0 12px;display:flex;align-items:center;gap:8px}.genre-panel .gp-count{font-size:11px;color:var(--muted);font-weight:700}.genre-chips{display:flex;flex-wrap:wrap;gap:7px}.genre-chips a{font-size:12px;font-weight:700;padding:6px 10px;border:1px solid var(--line);border-radius:20px;color:#d9dde1}.genre-chips a:hover{border-color:var(--accent);color:#fff}.genre-chips a b{color:var(--muted);font-weight:700;margin-left:3px}.editorial-row{display:grid;grid-template-columns:repeat(4,1fr);gap:18px}.editorial-card{display:block}.editorial-card .poster{aspect-ratio:16/10}.editorial-card h3{font-size:18px;margin:5px 0}.editorial-card span,.editorial-card p{font-size:12px;color:var(--muted)}.editorial-card p{margin:0}.story-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:#30343a}.story-grid a{min-height:225px;padding:22px;background:#111419;display:flex;flex-direction:column;align-items:flex-start}.story-grid a:hover{background:#191d23}.story-grid span{font-size:11px;font-weight:800;color:var(--gold);text-transform:uppercase;letter-spacing:.08em}.story-grid h3{font-size:21px;line-height:1.1;margin:10px 0}.story-grid p{font-size:13px;color:var(--muted);margin:0 0 14px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}.story-grid b{font-size:13px;margin-top:auto}.discover-cta{margin:40px 0 0;padding:40px;display:flex;align-items:center;justify-content:space-between;gap:30px;border-top:1px solid #353940;background:linear-gradient(90deg,#14171c,#0e1014)}.discover-cta p{color:var(--muted);max-width:480px}.discover-cta .cta{margin:0}.share-action{background:none;border:0;cursor:pointer;margin-left:14px;font:inherit}.article-hero .share-action{margin:16px 0 0}.article-hero{padding:70px 0 30px;max-width:820px}.article-hero h1{font-size:clamp(36px,6vw,60px);line-height:1.04;margin:10px 0}.article-meta{color:var(--muted);font-size:13px;margin-top:18px;display:flex;flex-wrap:wrap;align-items:center;gap:10px}.article-meta span+span:before{content:"\\00b7";margin-right:10px;opacity:.55}.article-body{max-width:760px;padding:28px 0 70px}.article-body h2{margin-top:38px;font-size:28px;line-height:1.16}.article-body p{font-size:18px;line-height:1.75;color:#d9dde1}.article-body blockquote{margin:24px 0;padding:4px 0 4px 22px;border-left:3px solid var(--gold);font-size:clamp(20px,3vw,27px);line-height:1.35;color:#fff}.article-source{font-size:13px!important;color:var(--gold)!important;font-weight:750;letter-spacing:.02em}.article-related{margin-top:56px;padding-top:28px;border-top:1px solid var(--line)}.article-related p{font-size:15px}.movie-hero{max-width:1180px;margin:0 auto;padding:64px 20px 40px;grid-template-columns:190px minmax(0,620px);align-items:end;min-height:470px;position:relative}.movie-hero:before{content:"";position:absolute;inset:0;z-index:-1;background:linear-gradient(90deg,#08090b 18%,rgba(8,9,11,.72) 55%,rgba(8,9,11,.95)),linear-gradient(0deg,#08090b,transparent),var(--movie-backdrop);background-size:cover;background-position:center}.movie-hero .poster{border-radius:4px}.movie-hero .lead{font-size:16px;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}.movie-hero h1{font-size:clamp(30px,5vw,52px)}.trailer-section{padding:0 20px 18px}.trailer-frame{position:relative;max-width:860px;aspect-ratio:16/9;background:#000;border-radius:6px;overflow:hidden;cursor:pointer;border:1px solid var(--line)}.trailer-frame img{width:100%;height:100%;object-fit:cover;opacity:.85}.trailer-frame iframe{width:100%;height:100%;border:0;display:block}.trailer-play{position:absolute;inset:0;margin:auto;width:74px;height:50px;border:0;border-radius:10px;background:rgba(233,75,44,.92);cursor:pointer;display:grid;place-items:center}.trailer-play:before{content:"";border-left:16px solid #fff;border-top:10px solid transparent;border-bottom:10px solid transparent;margin-left:4px}.trailer-play:hover{background:var(--accent)}.trailer-fallback{font-size:12.5px;color:var(--muted);margin:10px 0 0}.trailer-unavailable{padding:34px 18px;border:1px dashed var(--line);border-radius:6px;max-width:860px;text-align:center;color:var(--muted)}.trailer-unavailable b{display:block;color:var(--text);margin-bottom:4px}.searchbox{width:100%;max-width:640px;background:#101318;border:1px solid var(--line);border-radius:6px;color:var(--text);font:inherit;font-size:18px;padding:14px 16px;margin:14px 0}.searchbox:focus{outline:0;border-color:var(--accent)}.searchnote{color:var(--muted);font-size:13px;margin:0 0 18px}.search-tabs{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 18px}.stabs{background:#101318;border:1px solid var(--line);color:var(--muted);font:inherit;font-size:12.5px;font-weight:800;padding:8px 14px;border-radius:20px;cursor:pointer}.stabs.active{background:var(--accent);border-color:var(--accent);color:#fff}.search-group{grid-column:1/-1;font-size:12px;font-weight:900;letter-spacing:.1em;text-transform:uppercase;color:var(--gold);margin:14px 0 0;display:flex;align-items:center;gap:10px}.search-group:after{content:"";flex:1;height:1px;background:var(--line)}.trend-note{font-size:13px;color:var(--muted);background:#101318;border:1px solid var(--line);border-left:3px solid var(--gold);padding:14px 18px;border-radius:0 6px 6px 0;margin:0 0 26px}.trend-note code{color:var(--gold);font-size:12px}.boost-reason{font-size:11px;color:var(--muted);margin:3px 0 0}.score-pill{display:inline-flex;align-items:center;gap:4px;font-size:10.5px;font-weight:900;color:var(--gold);border:1px solid rgba(231,187,92,.4);border-radius:20px;padding:2px 8px}.mobile-nav{position:fixed;bottom:0;left:0;right:0;z-index:50;background:rgba(12,14,17,.97);backdrop-filter:blur(15px);border-top:1px solid #2a2e34;display:none;grid-auto-flow:column;grid-auto-columns:74px;overflow-x:auto;scrollbar-width:none;justify-content:start}.mobile-nav::-webkit-scrollbar{display:none}.mobile-nav a{text-align:center;padding:10px 2px 9px;color:#b6bdc5;font-size:10px;font-weight:800;line-height:1.2}.mobile-nav a:active,.mobile-nav a.active{color:#fff;background:#1a1e23}.mobile-nav .mn-ico{display:block;font-size:15px;margin-bottom:2px}@media(max-width:760px){body{padding-bottom:62px}.mobile-nav{display:grid}.home-hero{min-height:500px}.home-hero:after{background:linear-gradient(0deg,#08090b 0%,rgba(8,9,11,.86) 36%,rgba(8,9,11,.22) 100%)}.home-hero-inner{padding-top:170px;padding-bottom:36px}.home-hero h1{font-size:42px}.home-hero p{font-size:14.5px}.split-none{display:none}.editorial-row{grid-template-columns:repeat(2,1fr);gap:12px}.editorial-card .poster{aspect-ratio:1/1}.editorial-card p{font-size:13px;line-height:1.45;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.discover-cta{margin:30px -14px 0;padding:26px 14px;display:block}.discover-cta .cta{margin-top:12px}.genre-trio{grid-template-columns:1fr}.genre-panel h3{font-size:16px}.movie-hero{padding:110px 14px 24px;min-height:400px;grid-template-columns:100px minmax(0,1fr);gap:14px}.movie-hero .lead{font-size:14px;line-height:1.5;margin-top:6px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}.movie-hero .poster{max-height:150px}.trailer-section{padding:0 14px 14px}.story-grid{grid-template-columns:1fr}.story-grid a{min-height:170px}.article-hero{padding:44px 0 18px}.article-body{padding-top:16px}.article-body p{font-size:16px;line-height:1.7}.article-body h2{font-size:24px}}.trailer-section-inner{max-width:860px}.trailer-head{display:flex;align-items:center;gap:12px;margin:0 0 12px}.trailer-status{font-size:13px;font-weight:900;letter-spacing:.04em;padding:5px 12px;border-radius:20px;border:1px solid var(--line)}.trailer-status.t-ok{color:#3ddc84;border-color:rgba(61,220,132,.45)}.trailer-status.t-fan{color:#e7bb5c;border-color:rgba(231,187,92,.5)}.trailer-status.t-none{color:var(--muted)}.trailer-meta{font-size:12.5px;color:var(--muted);margin:10px 0 0}.trailer-verif-note{color:var(--gold);font-size:11px;margin-left:6px}.trailer-disclaimer{font-size:12.5px;color:#d9a441;background:rgba(231,187,92,.08);border:1px solid rgba(231,187,92,.3);padding:8px 12px;border-radius:5px;margin:10px 0 0}.trailer-error{border:1px dashed #b34a3a;background:rgba(179,74,58,.08);border-radius:6px;padding:18px 16px;margin:10px 0 0;color:var(--muted)}.trailer-error b{display:block;color:#ff8a75;margin-bottom:4px}.trailer-error-actions{display:flex;gap:18px;margin-top:10px}.trailer-alt{display:inline-block;margin-top:12px;background:transparent;border:1px solid var(--line);color:var(--text);font:inherit;font-size:13px;font-weight:700;padding:9px 16px;border-radius:5px;cursor:pointer}.trailer-alt:hover{border-color:var(--accent)}.trailer-retry{background:transparent;border:1px solid var(--line);color:var(--text);font:inherit;font-size:12.5px;font-weight:700;padding:7px 14px;border-radius:4px;cursor:pointer;margin-left:12px}.trailer-retry:hover{border-color:var(--accent)}.trailer-table{width:100%;border-collapse:collapse;font-size:13px}.trailer-table th,.trailer-table td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}.trailer-table th{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.08em}.tr-tag{display:inline-block;font-size:10px;font-weight:900;padding:2px 7px;border-radius:3px;letter-spacing:.05em}.tr-tag.ok{background:rgba(61,220,132,.15);color:#3ddc84}.tr-tag.fan{background:rgba(231,187,92,.15);color:#e7bb5c}.tr-tag.miss{background:rgba(154,161,169,.12);color:var(--muted)}.tr-tag.bad{background:rgba(179,74,58,.15);color:#ff8a75}.trailer-admin-filters{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 16px}.trailer-admin-filters select,.trailer-admin-filters input{background:#171b20;color:var(--text);border:1px solid var(--line);border-radius:4px;font:inherit;font-size:13px;padding:8px 12px}.legal-prose{max-width:760px;padding:10px 0 70px}.legal-prose h2{margin-top:34px}.legal-prose p{font-size:16px;line-height:1.75}@media(max-width:760px){.legal-prose p{font-size:15px}}.hero-carousel{position:relative;min-height:560px;background:#0d0f13;overflow:hidden;isolation:isolate}.hero-slides{position:absolute;inset:0}.hero-slide{position:absolute;inset:0;opacity:0;transform:scale(1.04);transition:opacity .8s ease,transform 8s linear;background-size:cover;background-position:center 28%;visibility:hidden}.hero-slide.is-active{opacity:1;transform:scale(1.08);visibility:visible;z-index:1}.hero-slide-shade{position:absolute;inset:0;background:linear-gradient(90deg,rgba(5,7,10,.97) 0%,rgba(5,7,10,.78) 40%,rgba(5,7,10,.25) 100%),linear-gradient(0deg,#08090b 0%,rgba(8,9,11,0) 55%)}.hero-slide-inner{position:relative;z-index:2;padding-top:120px;padding-bottom:64px;max-width:1180px;width:100%}.hero-slide-kicker{display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-size:13px;font-weight:800;color:#d3d7d9;letter-spacing:.06em;margin-bottom:12px}.hero-slide-kicker .dot{opacity:.35}.hero-slide h1{font-size:clamp(42px,7vw,78px);line-height:.96;max-width:760px;margin:0 0 10px}.hero-slide-rating{color:var(--gold);font-weight:800;font-size:14px;margin:0 0 10px}.hero-slide p{max-width:560px;color:#d2d6d9;font-size:16.5px;line-height:1.5;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}.hero-slide .hero-actions{margin-top:22px}.hero-video{position:absolute;inset:0;z-index:1}.hero-video iframe{width:100%;height:100%;border:0;display:block}.hero-ctrl{position:absolute;top:50%;transform:translateY(-50%);z-index:5;width:44px;height:44px;border-radius:50%;border:1px solid rgba(255,255,255,.25);background:rgba(8,9,11,.6);color:#fff;font-size:22px;line-height:1;cursor:pointer;display:grid;place-items:center;backdrop-filter:blur(4px)}.hero-ctrl:hover{background:rgba(8,9,11,.9);border-color:var(--accent)}.hero-prev{left:14px}.hero-next{right:14px}.hero-dots{position:absolute;bottom:18px;left:50%;transform:translateX(-50%);z-index:5;display:flex;gap:8px}.hero-dot{width:10px;height:10px;border-radius:50%;border:1px solid rgba(255,255,255,.5);background:transparent;padding:0;cursor:pointer}.hero-dot.is-active{background:var(--accent);border-color:var(--accent)}.hero-vctrl{position:absolute;right:14px;top:14px;z-index:5;width:40px;height:40px;border-radius:50%;border:1px solid rgba(255,255,255,.3);background:rgba(8,9,11,.65);color:#fff;font-size:16px;cursor:pointer;display:grid;place-items:center}.hero-pause{right:60px}.rec-section{padding:44px 0}.rec-inner{background:linear-gradient(135deg,#151922,#0e1014);border:1px solid var(--line);border-radius:10px;padding:34px 30px;display:grid;gap:18px}.rec-copy h2{font-size:clamp(26px,4vw,40px);margin:6px 0 6px}.rec-sub{color:var(--muted);font-size:15.5px;margin:0;max-width:560px}.rec-form{display:flex;gap:12px;flex-wrap:wrap}.rec-form input{flex:1 1 280px;background:#0d1013;border:1px solid var(--line);border-radius:6px;color:var(--text);font:inherit;font-size:16px;padding:15px 16px}.rec-form input:focus{outline:2px solid var(--accent);outline-offset:-1px}.rec-cta{font-size:15px;padding:15px 22px;margin:0}.rec-status{color:var(--muted);font-size:14px;min-height:0}.rec-suggest{position:relative;z-index:8;background:#101318;border:1px solid var(--line);border-radius:8px;margin-top:6px;overflow:hidden;max-height:280px;overflow-y:auto}.rec-suggest[hidden]{display:none}.rec-sug-item{display:flex;align-items:center;gap:12px;width:100%;background:none;border:0;border-bottom:1px solid var(--line);color:var(--text);font:inherit;text-align:left;padding:8px 12px;cursor:pointer}.rec-sug-item:last-child{border-bottom:0}.rec-sug-item:hover,.rec-sug-item:focus-visible{background:#1a1e25;outline:none}.rec-sug-item img{width:60px;height:45px;object-fit:cover;border-radius:4px;flex:none}.rec-sug-ph{width:60px;height:45px;flex:none;border-radius:4px;background:#1a1e25}.rec-sug-txt{display:flex;flex-direction:column;gap:2px;min-width:0}.rec-sug-txt b{font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.rec-sug-txt small{font-size:11px;color:var(--muted);font-weight:800;letter-spacing:.05em}.rec-results{margin-top:8px}.rec-results h3{font-size:clamp(19px,3vw,24px);margin:0 0 4px}.rec-reason{color:var(--muted);font-size:14px;margin:0 0 18px}.rec-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:16px}.rec-grid .tile .tile-meta{margin-top:4px}.rec-tag{display:inline-block;font-size:10.5px;font-weight:800;color:var(--gold);border:1px solid rgba(231,187,92,.35);border-radius:12px;padding:2px 8px;margin:5px 3px 0 0}.rec-actions{display:flex;gap:8px;margin-top:8px}.rec-actions a{font-size:11.5px;font-weight:800;padding:7px 10px;border-radius:4px}.rec-actions .ra-trailer{background:var(--accent);color:#fff}.rec-actions .ra-details{border:1px solid var(--line);color:var(--muted)}.rec-actions .ra-details:hover{color:#fff;border-color:var(--accent)}.rec-miss{background:#101318;border:1px dashed var(--line);border-radius:8px;padding:20px}.rec-miss b{display:block;font-size:17px;margin-bottom:4px}.rec-miss .rec-pop{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.rec-miss .rec-pop a{border:1px solid var(--line);padding:6px 12px;border-radius:20px;font-size:12.5px;font-weight:700}.brand-strip{padding:30px 0 6px}.brand-slogan{font-size:clamp(16px,2.6vw,22px);font-weight:800;letter-spacing:.02em;color:var(--text);margin:0 0 18px}.vchips{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}.vchip{position:relative;display:flex;flex-direction:column;gap:6px;padding:16px 18px;border:1px solid var(--line);border-radius:10px;background:linear-gradient(145deg,#14171d,#0e1014);overflow:hidden;transition:transform .2s,box-shadow .2s}.vchip:hover{transform:translateY(-3px);box-shadow:0 10px 26px rgba(0,0,0,.35)}.vchip:before{content:"";position:absolute;inset:0;opacity:.16;background:radial-gradient(200px 80px at 30% 0%,var(--vc,#fff),transparent 70%);pointer-events:none}.vchip-emoji{font-size:22px}.vchip-name{font-weight:900;font-size:14.5px}.vchip-tag{font-size:11.5px;color:var(--muted);line-height:1.45}.vchip-sports{--vc:#3ddc84}.vchip-memes{--vc:#ffd24a}.vchip-make-money{--vc:#e7bb5c}.vchip-tech{--vc:#4f8ef7}.vchip-entertainment{--vc:#e94b2c}.vhero{border-bottom:1px solid var(--line)}.vhero-sports{background:radial-gradient(500px 220px at 70% 0,rgba(61,220,132,.14),transparent 70%)}.vhero-memes{background:radial-gradient(500px 220px at 70% 0,rgba(255,210,74,.13),transparent 70%)}.vhero-make-money{background:radial-gradient(500px 220px at 70% 0,rgba(231,187,92,.14),transparent 70%)}.vhero-tech{background:radial-gradient(500px 220px at 70% 0,rgba(79,142,247,.15),transparent 70%)}.vcat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}.vcat{display:flex;flex-direction:column;gap:4px;padding:15px 17px;border:1px solid var(--line);border-radius:8px;background:#101318}.vcat:hover{border-color:var(--accent)}.vcat b{font-size:14.5px}.vcat span{font-size:12px;color:var(--muted);line-height:1.5}.vnote{border:1px solid var(--line);border-left:3px solid var(--gold);background:#101318;padding:12px 16px;border-radius:0 6px 6px 0;font-size:13px;color:var(--muted);line-height:1.6;max-width:820px}.vstate{border:1px dashed var(--line);border-radius:8px;padding:28px;text-align:center;color:var(--muted)}.sp-result{border:1px solid var(--line);border-left:3px solid #3ddc84;background:#101318;border-radius:0 8px 8px 0;padding:18px 20px;margin:14px 0}.sp-pill-ft{background:rgba(61,220,132,.15);color:#3ddc84;border-color:rgba(61,220,132,.45)}.sp-score{display:flex;align-items:center;gap:12px;flex-wrap:wrap;font-size:clamp(19px,3vw,25px);margin:10px 0 4px}.sp-score b{font-size:1.25em;font-variant-numeric:tabular-nums}.sp-score i{opacity:.45;font-style:normal}.sp-score span{color:#d9dde1}.sp-pens{font-size:13px;color:var(--gold);font-weight:700}.sp-result-meta{font-size:12.5px;color:var(--muted);margin:2px 0 0}.sp-scorers{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:14px 0 4px}.sp-scorers b{font-size:12.5px;color:var(--gold);text-transform:uppercase;letter-spacing:.05em}.sp-scorers ul{list-style:none;padding:0;margin:6px 0 0}.sp-scorers li{font-size:14px;padding:2px 0}.sp-scorers li span{color:var(--muted);font-size:12px}.sp-scorers .sp-none{color:var(--muted)}@media(max-width:600px){.sp-scorers{grid-template-columns:1fr}}.vstate b{display:block;font-size:17px;color:var(--text);margin-bottom:6px}
/* ==== BRYME SPORTS ==== */
.sp-pl-hero{padding:44px 0 8px}.sp-pl-hero h1{font-size:clamp(34px,6vw,64px);line-height:1.02;margin:8px 0}
.sp-hero{position:relative;margin:26px 0 10px;max-width:100%;overflow:hidden}.sp-hero-track{display:grid;grid-auto-flow:column;grid-auto-columns:calc((100% - 48px)/3);gap:16px;overflow-x:auto;scroll-snap-type:x mandatory;padding:4px 2px 18px;scrollbar-width:none;overscroll-behavior-x:contain;scrollbar-gutter:stable}.sp-hero-track::-webkit-scrollbar{display:none}.sp-hero-card{scroll-snap-align:start}
.sp-hero-card{position:relative;min-height:240px;display:flex;flex-direction:column;justify-content:flex-end;gap:8px;padding:22px;border-radius:12px;background:linear-gradient(150deg,#14241c,#0d1511 70%);border:1px solid rgba(61,220,132,.25);overflow:hidden;scroll-snap-align:start;transition:transform .2s,box-shadow .2s;isolation:isolate}.sp-hero-card:after{content:"";position:absolute;inset:0;z-index:-1;background-image:var(--card-img);background-size:cover;background-position:center;opacity:.28;transition:opacity .3s}.sp-hero-card:hover:after{opacity:.4}.sp-hero-card>*{position:relative;z-index:1;text-shadow:0 2px 8px rgba(0,0,0,.85)}.sp-hero-card:hover{transform:translateY(-4px);box-shadow:0 14px 30px rgba(0,0,0,.4)}.sp-hero-card:before{content:"";position:absolute;inset:0;opacity:.14;background:radial-gradient(240px 120px at 80% 0,rgba(61,220,132,.8),transparent 70%);pointer-events:none}.sp-hero-first{border-color:rgba(61,220,132,.55)}
.sp-hero-tag{font-size:10.5px;font-weight:900;letter-spacing:.1em;color:var(--sports);text-transform:uppercase}.sp-hero-card h3{font-size:clamp(17px,1.6vw,21px);line-height:1.2;margin:0}.sp-hero-card p{font-size:12.5px;color:var(--muted);line-height:1.5;margin:0;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.sp-hero-crests{display:flex;align-items:center;gap:7px}.sp-hero-crests img{width:26px;height:32px;object-fit:contain;filter:drop-shadow(0 2px 6px rgba(0,0,0,.6))}.sp-hero-crests b{color:var(--muted);font-size:10px;font-weight:800}.sp-hero-go{font-size:12px;font-weight:800;color:var(--sports)}
.sp-hero-arrow{position:absolute;top:40%;transform:translateY(-50%);z-index:3;width:38px;height:38px;border-radius:50%;border:1px solid rgba(255,255,255,.25);background:rgba(8,9,11,.7);color:#fff;font-size:20px;cursor:pointer;display:grid;place-items:center}.sp-hero-prev{left:2px}.sp-hero-next{right:2px}.sp-hero-arrow:hover{border-color:var(--sports)}
.sp-table-wrap{overflow-x:auto;margin:10px 0 26px;border:1px solid var(--line);border-radius:8px}.sp-table{width:100%;border-collapse:collapse;font-size:13px;min-width:640px}.sp-table th,.sp-table td{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left}.sp-table th{background:#101318;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.07em}.sp-table td{vertical-align:top}.sp-empty td{color:var(--muted);font-style:italic;padding:22px;line-height:1.6;text-align:center}
.sp-dir{font-size:17px;margin:22px 0 6px}.sp-st-conf,.sp-st-rep,.sp-st-rum{display:inline-block;font-size:11px;font-weight:800;padding:2px 9px;border-radius:12px;margin-right:6px}.sp-st-conf{background:rgba(61,220,132,.15);color:#3ddc84;border:1px solid rgba(61,220,132,.4)}.sp-st-rep{background:rgba(231,187,92,.12);color:#e7bb5c;border:1px solid rgba(231,187,92,.4)}.sp-st-rum{background:rgba(154,161,169,.12);color:var(--muted);border:1px solid rgba(154,161,169,.4)}
.sp-ed-label{display:inline-block;background:rgba(231,187,92,.12);color:#e7bb5c;border:1px solid rgba(231,187,92,.45);font-size:12px;font-weight:900;letter-spacing:.06em;padding:6px 14px;border-radius:20px;margin:10px 0}
.sp-article{max-width:820px;margin:0 auto;padding:10px 0 60px}.sp-article-head{padding:34px 0 24px}.sp-article-head h1{font-size:clamp(30px,5vw,52px);line-height:1.05;margin:10px 0}.sp-meta{display:flex;flex-wrap:wrap;gap:8px 18px;color:var(--muted);font-size:12.5px;margin-top:16px}
.sp-img{aspect-ratio:16/7;background:linear-gradient(145deg,#1a2026,#0d1013);border:1px dashed var(--line);border-radius:10px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;color:var(--muted);text-align:center;padding:20px}.sp-img span{font-weight:800;color:var(--text)}.sp-img small{font-size:11px}
.sp-body-placeholder{border:1px dashed var(--line);border-radius:10px;padding:30px;margin:18px 0;text-align:center}.sp-body-placeholder b{font-size:17px;display:block;margin-bottom:6px}.sp-body-placeholder p{color:var(--muted);font-size:14px;max-width:560px;margin:0 auto;line-height:1.6}
.sp-source{margin-top:30px;border:1px solid var(--line);border-radius:8px;padding:18px 20px;background:#101318}.sp-source h2{font-size:16px;margin:0 0 8px}.sp-source p{margin:6px 0;font-size:13.5px}.sp-source-note{font-size:12.5px;color:var(--muted);line-height:1.6;margin:8px 0 0}
.sp-related{margin-top:34px;padding-top:24px;border-top:1px solid var(--line)}.sp-related h2{font-size:18px;margin:0 0 14px}.sp-rel-grid{display:flex;flex-wrap:wrap;gap:10px}.sp-rel{border:1px solid var(--line);border-radius:20px;padding:8px 14px;font-size:12.5px;font-weight:700;color:#d9dde1}.sp-rel:hover{border-color:var(--sports);color:#fff}.sp-rel-static{color:var(--muted);cursor:default}
.sp-mc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px;margin:18px 0}.sp-mc-card{min-height:120px;border:1px dashed var(--line);border-radius:10px;padding:18px;display:flex;flex-direction:column;justify-content:flex-end;background:#101318}.sp-mc-card b{font-size:15px}.sp-mc-card p{font-size:12.5px;color:var(--muted);margin:4px 0 0;line-height:1.5}
.sp-live{display:flex;gap:14px;align-items:flex-start;background:linear-gradient(135deg,rgba(61,220,132,.1),rgba(61,220,132,.03));border:1px solid rgba(61,220,132,.35);border-radius:10px;padding:18px 20px;margin:6px 0 14px}.sp-live-dot{flex:none;width:12px;height:12px;border-radius:50%;background:#3ddc84;margin-top:5px;box-shadow:0 0 0 0 rgba(61,220,132,.6);animation:spPulse 2s infinite}@keyframes spPulse{0%{box-shadow:0 0 0 0 rgba(61,220,132,.55)}70%{box-shadow:0 0 0 9px rgba(61,220,132,0)}100%{box-shadow:0 0 0 0 rgba(61,220,132,0)}}.sp-live b{font-size:15px;letter-spacing:.04em}.sp-live p{margin:4px 0 0;font-size:13px;color:var(--muted);line-height:1.6}.sp-updated{font-size:12.5px;color:var(--gold);font-weight:800;margin:0 0 16px}.sp-truth{display:flex;gap:12px;align-items:flex-start;background:rgba(231,187,92,.06);border:1px solid rgba(231,187,92,.3);border-radius:10px;padding:14px 18px;margin:0 0 14px}.sp-truth b{color:var(--gold);font-size:13px;flex:none}.sp-legend-line{font-size:12.5px;color:var(--muted);margin:0 0 14px}.sp-mgr-club{display:flex;align-items:center;gap:10px}.sp-mgr-club img{flex:none}.sp-mgr-badge{display:inline-block;font-size:10.5px;font-weight:900;letter-spacing:.06em;padding:2px 8px;border-radius:12px;margin-right:8px}.sp-mgr-new{background:rgba(61,220,132,.15);color:#3ddc84;border:1px solid rgba(61,220,132,.4)}.sp-mgr-keep{background:rgba(154,161,169,.12);color:var(--muted);border:1px solid rgba(154,161,169,.35)}.sp-mgr-note{font-size:12px;color:var(--muted)}.sp-mgr-pending{color:var(--muted);font-style:italic}.sp-credits{font-size:11.5px;color:var(--muted);line-height:1.6;border:1px solid var(--line);border-left:3px solid var(--gold);background:#101318;padding:10px 14px;border-radius:0 6px 6px 0;margin:0 0 18px}.sp-truth p{margin:0;font-size:12.5px;color:var(--muted);line-height:1.6}.sp-freq-note{font-size:12.5px;color:var(--muted);margin:-8px 0 16px;font-style:italic}
.sp-club-nav{display:flex;flex-wrap:wrap;gap:7px;margin:0 0 22px}.sp-club-nav a{font-size:12px;font-weight:700;border:1px solid var(--line);border-radius:16px;padding:5px 11px;color:var(--muted)}.sp-club-nav a:hover{color:#fff;border-color:var(--sports)}
.sp-clubs{display:flex;flex-direction:column;gap:20px}.sp-club{border:1px solid var(--line);border-radius:12px;background:#101318;overflow:hidden}.sp-club-head{display:flex;gap:16px;align-items:center;padding:16px 20px;background:linear-gradient(90deg,#151a21,#101318)}.sp-club-head img{width:56px;height:67px;object-fit:contain;filter:drop-shadow(0 4px 10px rgba(0,0,0,.5))}.sp-club-head h2{font-size:22px;margin:0}.sp-club-man{font-size:13px;color:var(--muted);margin:3px 0 0}.sp-club-man b{color:var(--text)}.sp-club-cols{display:grid;grid-template-columns:1fr 1fr;gap:0}.sp-club-col{padding:6px 20px 18px}.sp-club-col h3{font-size:13px;font-weight:900;letter-spacing:.08em;text-transform:uppercase;color:var(--sports);margin:12px 0 8px}.sp-club-col+.sp-club-col{border-left:1px solid var(--line)}.sp-club .sp-table{min-width:0}.sp-club-notes{font-size:13px;color:#c9ced4;line-height:1.65;border-top:1px solid var(--line);padding:14px 20px;margin:0}.sp-club-notes b{color:var(--gold)}.sp-rumours{margin:0 20px 12px;border:1px dashed rgba(231,187,92,.4);border-radius:8px;padding:12px 16px;font-size:13px}.sp-rumours b{color:#e7bb5c;display:block;margin-bottom:6px}.sp-rumours p{margin:3px 0;color:var(--muted)}
.sp-window-note{margin:26px 0 0;font-size:13px;color:var(--muted);font-style:italic}.sp-signoff{margin:26px 0 8px;font-size:13px;color:var(--gold);font-weight:800}
.sp-mw{border:1px solid var(--line);border-radius:10px;background:#101318;margin:0 0 18px;overflow:hidden}.sp-mw-head{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px;padding:12px 18px;background:linear-gradient(90deg,#151a21,#101318);border-bottom:1px solid var(--line)}.sp-mw-head h2{font-size:17px;margin:0}.sp-mw-date{font-size:12px;color:var(--muted);font-weight:700}.sp-fixture{display:grid;grid-template-columns:1fr auto;gap:4px 18px;align-items:center;padding:11px 18px;border-bottom:1px solid var(--line)}.sp-fixture:last-child{border-bottom:0}.sp-fixture:hover{background:#161b22}.sp-fixt{display:flex;flex-wrap:wrap;align-items:center;gap:10px;font-size:14.5px;font-weight:700}.sp-fixt img{width:22px;height:27px;object-fit:contain;filter:drop-shadow(0 2px 5px rgba(0,0,0,.5))}.sp-fixt .sp-vs{color:var(--muted);font-weight:400;font-size:12px}.sp-fixt a{color:var(--text)}.sp-fixt a:hover{color:var(--sports)}.sp-fixt-info{display:flex;flex-wrap:wrap;align-items:center;gap:10px;font-size:12px;color:var(--muted)}.sp-fixt-day{font-weight:800;color:#c9ced4}.sp-fixt-time{font-weight:800;color:var(--text)}.sp-std{font-size:10px;color:var(--muted);font-weight:700}.sp-tv{font-size:10.5px;font-weight:900;letter-spacing:.04em;padding:2px 8px;border-radius:11px;background:rgba(79,142,247,.14);color:#7fb0ff;border:1px solid rgba(79,142,247,.35)}.sp-tv.tnt{background:rgba(233,75,44,.12);color:#ff9d8a;border-color:rgba(233,75,44,.35)}.sp-matchlink{font-size:12px;font-weight:800;color:var(--sports)}.sp-matchlink:hover{text-decoration:underline}.sp-mwnav{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 18px}.sp-mwnav a{font-size:11.5px;font-weight:800;border:1px solid var(--line);border-radius:14px;padding:4px 9px;color:var(--muted)}.sp-mwnav a:hover{color:#fff;border-color:var(--sports)}.sp-fix-legend{font-size:12px;color:var(--muted);line-height:1.7;border:1px dashed var(--line);border-radius:8px;padding:12px 16px;margin:0 0 20px}.sp-match-hero{display:flex;gap:20px;align-items:center;flex-wrap:wrap;margin:10px 0 22px;padding:22px 24px;border:1px solid var(--line);border-radius:12px;background:linear-gradient(90deg,#151a21,#101318)}.sp-match-hero img{width:64px;height:77px;object-fit:contain;filter:drop-shadow(0 4px 10px rgba(0,0,0,.5))}.sp-match-hero .sp-mh-vs{font-size:18px;color:var(--muted);font-weight:800}.sp-match-hero h1{font-size:clamp(24px,4vw,36px);margin:0;line-height:1.05}.sp-match-meta{display:flex;flex-wrap:wrap;gap:8px 18px;font-size:13px;color:var(--muted);margin:0 0 4px}.sp-match-meta b{color:var(--text)}.sp-pill{display:inline-block;font-size:11px;font-weight:900;letter-spacing:.05em;padding:3px 10px;border-radius:13px;background:rgba(61,220,132,.13);color:#3ddc84;border:1px solid rgba(61,220,132,.4);margin-right:6px}.sp-msec-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px;margin:14px 0 8px}.sp-msec{min-height:96px;border:1px dashed var(--line);border-radius:9px;padding:14px 16px;background:#0f1217;display:flex;flex-direction:column;gap:5px}.sp-msec b{font-size:13.5px;color:#d9dde1}.sp-msec p{font-size:12px;color:var(--muted);margin:0;line-height:1.5}.sp-msec .sp-pend{font-size:10.5px;font-weight:900;letter-spacing:.06em;color:var(--gold);text-transform:uppercase}.sp-mc-card.solid{border:1px solid var(--line);border-style:solid;background:linear-gradient(180deg,#14181f,#101318)}.sp-mc-card a.sp-mc-go{font-size:12px;font-weight:800;color:var(--sports);text-decoration:none;margin-top:8px}.sp-mc-card a.sp-mc-go:hover{text-decoration:underline}.sp-mc-crests{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:10px}.sp-mc-crests img{width:30px;height:36px;object-fit:contain;filter:drop-shadow(0 2px 6px rgba(0,0,0,.5))}.sp-mc-crests .sp-vs{color:var(--muted);font-size:11px;font-weight:800}
@media(max-width:760px){.sp-club-cols{grid-template-columns:1fr}.sp-club-col+.sp-club-col{border-left:0;border-top:1px solid var(--line)}.sp-club-head{padding:14px 16px}.sp-club-head h2{font-size:19px}.sp-club .sp-table{min-width:430px}.sp-live{padding:14px 16px}}
.sp-gw-sec{padding:16px 0;border-bottom:1px solid var(--line)}.sp-gw-sec h2{font-size:19px;margin:0 0 6px}.sp-empty-line{color:var(--muted);font-size:13.5px}
@media(max-width:1024px){.sp-hero-track{grid-auto-columns:calc((100% - 32px)/2)}}@media(min-width:1025px) and (max-width:1439px){.sp-hero{max-width:1180px;margin-left:auto;margin-right:auto}}
@media(max-width:640px){.sp-hero-track{grid-auto-columns:calc(100% - 40px)}.sp-hero-arrow{display:none}.sp-hero-card{min-height:200px}.sp-article-head h1{font-size:30px}}
@media(min-width:1440px){.sp-hero-track{grid-auto-columns:calc((100% - 64px)/5);grid-auto-flow:column}}
.visually-hidden{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}@media(max-width:760px){.hero-carousel{min-height:520px}.hero-slide-inner{padding-top:150px;padding-bottom:52px}.hero-slide h1{font-size:40px}.hero-slide p{font-size:14.5px}.hero-ctrl{width:40px;height:40px;font-size:19px}.hero-prev{left:8px}.hero-next{right:8px}.rec-inner{padding:26px 18px}.rec-cta{width:100%;text-align:center}}.hero-kicker{display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-size:12px;font-weight:800;color:var(--muted);letter-spacing:.05em;text-transform:uppercase;margin-bottom:10px}.hero-kicker .dot{opacity:.35}.cta-ghost{background:transparent;border:1px solid var(--accent);color:#fff}.cta-ghost:hover{background:var(--accent)}.take-card{margin-top:28px;border:1px solid var(--line);border-left:3px solid var(--gold);background:#101318;padding:18px 20px;border-radius:0 6px 6px 0}.take-card h3{font-size:19px;line-height:1.25;margin:6px 0}.take-card p{font-size:14px;color:var(--muted);margin:0 0 12px}.take-card .cta{margin:0}.sub-section{padding:8px 0 34px}.sub-section h2{font-size:clamp(20px,3vw,26px)}.sub-section .lead,.sub-section p.sec-note{font-size:13px;color:var(--muted);margin:0 0 14px}@media(max-width:760px){.hero-kicker{font-size:10.5px;gap:6px}.take-card{padding:15px 14px}.hero-actions .cta{min-height:44px;display:inline-flex;align-items:center}.story-grid-title{grid-template-columns:1fr}.story-grid-title a{min-height:150px}}`);
fs.appendFileSync(path.join(root,'assets/site.css'), `\n/* Verified metadata attribution */\n.meta-source{margin:10px 0 0;font-size:12px;line-height:1.55;color:#8b93a1}.meta-source a{color:#a9b3c2;text-decoration:underline;text-underline-offset:2px}.meta-source a:hover{color:#fff}\n`);
fs.appendFileSync(path.join(root,'assets/site.css'), `
/* ============================================================
   COLOUR & DEPTH LAYER
   Appended last so it layers over the base sheet without
   rewriting it. Adds the vertical colour identities, gradients
   and hover states across the site. Structure is untouched -
   this is presentation only.
   ============================================================ */
:root{
  --grad-brand:linear-gradient(115deg,#ff6a3d,#e94b2c 45%,#c2341c);
  --grad-gold:linear-gradient(115deg,#f7d489,#e7bb5c 50%,#c99a37);
  --grad-sports:linear-gradient(115deg,#4dffa0,#3ddc84 48%,#1fa862);
  --grad-money:linear-gradient(115deg,#ffd98a,#e7bb5c 48%,#b98f2f);
  --grad-tech:linear-gradient(115deg,#7fb0ff,#4f8ef7 48%,#2a63c9);
  --grad-ent:linear-gradient(115deg,#ff7d5c,#e94b2c 48%,#b8331b);
  --ring:0 0 0 1px rgba(255,255,255,.06);
}
/* page canvas: soft coloured light instead of flat black */
body{
  background:
    radial-gradient(1100px 520px at 12% -8%, rgba(233,75,44,.14), transparent 62%),
    radial-gradient(900px 460px at 88% 0%, rgba(79,142,247,.12), transparent 60%),
    radial-gradient(760px 420px at 50% 108%, rgba(61,220,132,.09), transparent 62%),
    var(--bg);
  background-attachment:fixed;
}
/* brand wordmark */
.brand,.logo,header .top b{letter-spacing:.02em}
.brand-grad,.footer-brand b{background:var(--grad-brand);-webkit-background-clip:text;background-clip:text;color:transparent}
/* primary action */
.cta{
  background:var(--grad-brand);border:0;color:#fff;border-radius:7px;
  box-shadow:0 6px 20px rgba(233,75,44,.28), var(--ring);
  transition:transform .18s ease, box-shadow .18s ease, filter .18s ease;
}
.cta:hover{transform:translateY(-2px);box-shadow:0 12px 30px rgba(233,75,44,.4), var(--ring);filter:saturate(1.08)}
.cta:active{transform:translateY(0)}
/* every section heading gets a coloured lead-in bar */
.section-head h2,.home-section h2,.section>h2,main h2,.brand-slogan{position:relative;padding-left:15px}
.section-head h2:before,.home-section h2:before,.section>h2:before,main h2:before,.brand-slogan:before{
  content:"";position:absolute;left:0;top:.16em;bottom:.16em;width:5px;border-radius:4px;background:var(--grad-brand);
}
.article-body h2:before,.legal-prose h2:before{background:var(--grad-gold)}
body[data-nav="sports"] main h2:before,body[data-nav="sports"] .section-head h2:before{background:var(--grad-sports)}
body[data-nav="make-money"] main h2:before{background:var(--grad-money)}
body[data-nav="tech"] main h2:before{background:var(--grad-tech)}
body[data-nav="sports"] .cta{background:var(--grad-sports);box-shadow:0 6px 20px rgba(61,220,132,.28),var(--ring);color:#06210f}
body[data-nav="tech"] .cta{background:var(--grad-tech);box-shadow:0 6px 20px rgba(79,142,247,.3),var(--ring)}
body[data-nav="make-money"] .cta{background:var(--grad-money);box-shadow:0 6px 20px rgba(231,187,92,.28),var(--ring);color:#2a1e05}
.section-head a{color:var(--gold);font-weight:800;font-size:13px}
.section-head a:hover{color:#fff}
/* big page titles pick up a warm gradient */
.hero h1,.vhero h1,.article-hero h1{
  background:linear-gradient(100deg,#ffffff 30%,#ffd9c9 62%,#ffb08e);
  -webkit-background-clip:text;background-clip:text;color:transparent;
}
.vhero-sports h1{background:linear-gradient(100deg,#ffffff 30%,#c9ffe3 62%,#6affab);-webkit-background-clip:text;background-clip:text}
.vhero-tech h1{background:linear-gradient(100deg,#ffffff 30%,#cfe0ff 62%,#8fb6ff);-webkit-background-clip:text;background-clip:text}
.vhero-make-money h1{background:linear-gradient(100deg,#ffffff 30%,#ffeec4 62%,#f5cd76);-webkit-background-clip:text;background-clip:text}
/* category cards: lit top edge, brighter surface, coloured lift */
.vcat{position:relative;overflow:hidden;background:linear-gradient(160deg,#181d26,#11151b);border-color:rgba(255,255,255,.1)}
.vcat:before{content:"";position:absolute;top:0;left:0;right:0;height:3px;background:var(--grad-brand);opacity:.9}
body[data-nav="sports"] .vcat:before{background:var(--grad-sports)}
body[data-nav="make-money"] .vcat:before{background:var(--grad-money)}
body[data-nav="tech"] .vcat:before{background:var(--grad-tech)}
body[data-nav="sports"] .prose a,body[data-nav="sports"] .sp-table a{color:#7dffb9}
body[data-nav="tech"] .prose a{color:#a8c8ff}
.vcat:hover{transform:translateY(-4px);border-color:rgba(255,255,255,.22);box-shadow:0 16px 34px rgba(0,0,0,.45)}
.vcat b{font-size:15px}
/* data tables read as content, not spreadsheets */
.sp-table thead th{background:linear-gradient(180deg,rgba(255,255,255,.06),transparent);color:#cfd5db;border-bottom-color:rgba(255,255,255,.14)}
.sp-table tbody tr:hover{background:rgba(255,255,255,.035)}
.sp-table a{color:#ffcaa8}.sp-table a:hover{color:#fff}
/* panels lift off the page */
.sp-msec,.genre-panel,.rec-miss{background:linear-gradient(160deg,#161b23,#0f1216)}
.sp-rel{background:linear-gradient(160deg,#171c24,#101318);transition:transform .16s ease,border-color .16s ease}
.sp-rel:hover{transform:translateY(-2px);border-color:rgba(255,255,255,.25)}
/* cards and tiles lift with light */
.tile:hover{transform:translateY(-5px)}
.tile .poster,.editorial-card .poster{transition:box-shadow .22s ease, filter .22s ease}
.tile:hover .poster,.editorial-card:hover .poster{box-shadow:0 16px 34px rgba(0,0,0,.55);filter:saturate(1.06) contrast(1.03)}
.vcat{background:linear-gradient(150deg,#141821,#0f1216);transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease}
.vcat:hover{transform:translateY(-3px);box-shadow:0 12px 26px rgba(0,0,0,.4)}
.story-grid a{transition:background .2s ease,transform .2s ease}
.story-grid a:hover{transform:translateY(-3px)}
/* vertical identity: colour the chips and hubs properly */
.vchip{border-color:rgba(255,255,255,.09)}
.vchip:before{opacity:.3}
.vchip-sports:hover{border-color:rgba(61,220,132,.55);box-shadow:0 12px 30px rgba(61,220,132,.16)}
.vchip-make-money:hover{border-color:rgba(231,187,92,.55);box-shadow:0 12px 30px rgba(231,187,92,.16)}
.vchip-tech:hover{border-color:rgba(79,142,247,.55);box-shadow:0 12px 30px rgba(79,142,247,.16)}
.vchip-entertainment:hover{border-color:rgba(233,75,44,.55);box-shadow:0 12px 30px rgba(233,75,44,.16)}
.vhero{position:relative;overflow:hidden}
.vhero:after{content:"";position:absolute;left:0;right:0;bottom:0;height:2px;opacity:.85}
.vhero-sports:after{background:var(--grad-sports)}
.vhero-make-money:after{background:var(--grad-money)}
.vhero-tech:after{background:var(--grad-tech)}
.vhero-sports{background:radial-gradient(620px 260px at 72% -10%,rgba(61,220,132,.22),transparent 68%)}
.vhero-make-money{background:radial-gradient(620px 260px at 72% -10%,rgba(231,187,92,.22),transparent 68%)}
.vhero-tech{background:radial-gradient(620px 260px at 72% -10%,rgba(79,142,247,.24),transparent 68%)}
/* eyebrows and pills */
.eyebrow{background:var(--grad-gold);-webkit-background-clip:text;background-clip:text;color:transparent;font-weight:900}
.vhero-sports .eyebrow{background:var(--grad-sports);-webkit-background-clip:text;background-clip:text}
.vhero-tech .eyebrow{background:var(--grad-tech);-webkit-background-clip:text;background-clip:text}
.genre-chips a:hover{background:rgba(233,75,44,.14);border-color:var(--accent);color:#fff}
.stabs.active{background:var(--grad-brand);border-color:transparent;box-shadow:0 4px 14px rgba(233,75,44,.3)}
.score-pill{background:rgba(231,187,92,.1)}
.sp-pill{background:rgba(255,255,255,.05)}
/* type accents on cards */
.tile-meta b,.card-type{color:var(--muted)}
/* navigation */
.topnav a{position:relative;transition:color .16s ease}
.topnav a:after{content:"";position:absolute;left:0;right:0;bottom:-6px;height:2px;border-radius:2px;background:var(--grad-brand);transform:scaleX(0);transition:transform .18s ease}
.topnav a:hover:after,.topnav a.active:after{transform:scaleX(1)}
.top{background:linear-gradient(180deg,rgba(10,12,15,.97),rgba(10,12,15,.82));border-bottom-color:rgba(255,255,255,.08)}
/* article reading experience */
.article-body h2{position:relative;padding-left:15px}
.article-body h2:before{content:"";position:absolute;left:0;top:.22em;bottom:.22em;width:3px;border-radius:3px;background:var(--grad-gold)}
.article-hero .eyebrow{letter-spacing:.1em}
.prose a{color:#ffb199;border-bottom:1px solid rgba(255,177,153,.35)}
.prose a:hover{color:#fff;border-bottom-color:#fff}
/* panels */
.vstate{background:linear-gradient(150deg,#12161c,#0e1114)}
.vnote,.trend-note{background:linear-gradient(90deg,rgba(231,187,92,.07),transparent 70%),#101318}
.sp-result{background:linear-gradient(90deg,rgba(61,220,132,.09),transparent 62%),#101318}
.rec-inner{background:linear-gradient(135deg,#181d27,#0e1014);box-shadow:0 20px 60px rgba(0,0,0,.35)}
/* footer */
.footer{position:relative;background:linear-gradient(180deg,#0b0d11,#08090b)}
.footer:before{content:"";position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#e94b2c,#e7bb5c 32%,#3ddc84 64%,#4f8ef7)}
.footer-col a:hover{color:#fff}
/* mobile bar */
.mobile-nav a.active{background:linear-gradient(180deg,rgba(233,75,44,.22),transparent)}
/* Back control: it is fixed-position, so keep it clear of the breadcrumb rather
   than letting it sit on top of the first line of text. */
body .bryme-back{top:auto;bottom:78px;left:14px;opacity:.92}
body .bryme-back:hover{opacity:1}
@media(min-width:761px){body .bryme-back{bottom:24px;left:18px}}
/* ---------- editorial layout variants ----------
   One tile component, four presentations. The wrapper class decides the
   shape, so curated order, counts and ranks are never altered by layout. */
.home-section{padding:44px 0}
.section-note{font-size:13px;color:var(--muted);margin:6px 0 0;max-width:640px}
.section-head{align-items:start}
.section-head>div{min-width:0}

/* Variants must undo the base rail's horizontal-scroll grid before laying out. */
.rail-lead,.rail-wall,.rail-chart,.rail-spread{
  grid-auto-flow:row;grid-auto-columns:auto;overflow-x:visible;
  scroll-snap-type:none;padding:2px 1px 4px;
}
.rail-lead .tile,.rail-wall .tile,.rail-chart .tile,.rail-spread .tile{scroll-snap-align:none}

/* LEAD - mosaic: one feature at 2x2, the rest fill around it.
   Works with any number of items, so a curated list is never truncated. */
.rail-lead{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;overflow:visible}
.rail-lead .tile{min-width:0}
.rail-lead .tile .poster{aspect-ratio:2/3}
.rail-lead .tile:first-child{grid-column:span 2;grid-row:span 2;display:flex;flex-direction:column}
.rail-lead .tile:first-child .poster{aspect-ratio:auto;flex:1;min-height:300px}
.rail-lead .tile:first-child .poster img{width:100%;height:100%;object-fit:cover}
.rail-lead .tile:first-child h3{font-size:clamp(20px,2.2vw,27px);line-height:1.15;margin-top:12px}
.rail-lead .tile:first-child .tile-meta{font-size:13px}
.rail-lead h3{font-size:14px;line-height:1.3}
.rail-lead .tile:not(:first-child) .tile-rating{display:none}
/* WALL - dense poster grid */
.rail-wall{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:16px;overflow:visible}
.rail-wall .tile{min-width:0}
.rail-wall .tile .poster{aspect-ratio:2/3}
.rail-wall h3{font-size:13.5px;line-height:1.3}
.rail-wall .tile-rating{display:none}

/* CHART - numbered two-column list */
.rail-chart{display:grid;grid-template-columns:1fr 1fr;gap:0 28px;counter-reset:ch;overflow:visible}
.rail-chart .tile{counter-increment:ch;display:grid;grid-template-columns:40px 48px minmax(0,1fr);gap:13px;align-items:center;padding:9px 6px;border-bottom:1px solid rgba(255,255,255,.055);border-radius:8px;transition:background .16s}
.rail-chart .tile:hover{background:rgba(255,255,255,.045)}
.rail-chart .tile:before{content:counter(ch);font-size:25px;font-weight:900;text-align:center;color:transparent;-webkit-text-stroke:1.4px rgba(255,255,255,.32);font-variant-numeric:tabular-nums}
.rail-chart .tile:nth-child(-n+3):before{-webkit-text-stroke:0;background:var(--grad-brand);-webkit-background-clip:text;background-clip:text}
.rail-chart .poster{width:48px;aspect-ratio:2/3;margin:0;border-radius:5px}
.rail-chart h3{font-size:15px;line-height:1.25;margin:0}
.rail-chart .tile-meta{font-size:11.5px}
.rail-chart .tile-rating{display:none}

/* SPREAD - equal-weight features, image behind the text */
.rail-spread{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;overflow:visible}
.rail-spread .tile{position:relative;min-height:300px;border-radius:12px;overflow:hidden;border:1px solid rgba(255,255,255,.09);display:flex;flex-direction:column;justify-content:flex-end;padding:18px}
.rail-spread .tile .poster{position:absolute;inset:0;margin:0;border-radius:0;aspect-ratio:auto;z-index:-2}
.rail-spread .tile .poster img{width:100%;height:100%;object-fit:cover}
.rail-spread .tile:after{content:"";position:absolute;inset:0;z-index:-1;background:linear-gradient(0deg,rgba(6,8,11,.985) 22%,rgba(6,8,11,.8) 52%,rgba(6,8,11,.35))}
.rail-spread h3{font-size:21px;line-height:1.16;margin:6px 0 4px}
.rail-spread .tile-meta,.rail-spread .tile-rating{position:relative}

@media(max-width:1080px){.rail-wall{grid-template-columns:repeat(4,minmax(0,1fr))}}
@media(max-width:980px){
  .rail-lead{grid-template-columns:repeat(2,minmax(0,1fr))}
  .rail-lead .tile:first-child .poster{min-height:210px}
  .rail-chart,.rail-spread{grid-template-columns:1fr}
}
@media(max-width:620px){.rail-wall{grid-template-columns:repeat(3,minmax(0,1fr));gap:11px}.home-section{padding:30px 0}}
/* ---------- match editorial workflow ---------- */
.sp-preview{margin:18px 0 0}
.sp-msec-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:12px}
.sp-msec{background:linear-gradient(160deg,#161b23,#0f1216);border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:15px 17px}
.sp-msec>b{display:block;font-size:11.5px;font-weight:900;letter-spacing:.09em;text-transform:uppercase;color:var(--gold);margin-bottom:7px}
.sp-msec p{margin:0 0 8px;font-size:14.5px;line-height:1.62;color:#d9dde1}
.sp-msec p:last-child{margin-bottom:0}
.sp-msec ul{margin:0;padding-left:18px;font-size:14px;line-height:1.6;color:#d9dde1}
/* an unconfirmed field is visibly a gap in the record, not filler */
.sp-msec-unknown{border-style:dashed;background:#0f1216}
.sp-msec-unknown>b{color:var(--muted)}
.sp-unknown{display:block;font-size:13.5px;line-height:1.6;color:var(--muted);font-style:italic}
/* empty match panel: one honest summary instead of repeated pending cards */
.sp-empty-panel{margin:22px 0 0;border:1px solid var(--line);border-left:3px solid var(--gold);border-radius:0 10px 10px 0;background:linear-gradient(160deg,#151a21,#0f1216);padding:20px 22px;max-width:860px}
.sp-empty-panel .sp-pend{display:inline-block;font-size:10.5px;font-weight:900;letter-spacing:.06em;color:var(--gold);text-transform:uppercase;margin-bottom:8px}
.sp-empty-panel b{display:block;font-size:17px;line-height:1.3;margin-bottom:8px}
.sp-empty-panel p{font-size:14.5px;line-height:1.62;color:#d9dde1;margin:0 0 8px}
.sp-empty-panel p.sp-empty-note{margin:0;font-size:13px;color:var(--muted)}
[data-theme="light"] .sp-empty-panel{background:#ffffff;border-color:var(--line)}
[data-theme="light"] .sp-empty-panel p{color:#2b333c}
[data-theme="light"] .sp-empty-panel p.sp-empty-note{color:#5a6572}
/* the preserved pre-match preview, once the match has been played */
.sp-preview-archived{margin-top:26px;padding-top:4px;border-top:1px solid var(--line)}
.sp-archive-note{background:linear-gradient(90deg,rgba(231,187,92,.09),transparent 70%);border:1px solid rgba(231,187,92,.28);border-left:3px solid var(--gold);border-radius:0 8px 8px 0;padding:13px 16px;margin:18px 0 14px}
.sp-archive-note b{display:block;font-size:14.5px;margin-bottom:3px}
.sp-archive-note p{margin:0;font-size:13px;color:var(--muted);line-height:1.6}
.sp-preview-archived .sp-msec{opacity:.86}
.sp-postmatch{margin-top:20px}
.sp-postmatch .sp-msec>b{color:#3ddc84}
@media(max-width:760px){.sp-msec-grid{grid-template-columns:1fr}}
/* ---------- clubs directory ---------- */
.cd-jumps{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 6px}
.cd-jump{font-size:12.5px;font-weight:800;text-transform:capitalize;padding:7px 13px;border:1px solid var(--line);border-radius:20px;color:#d9dde1;background:#101318}
.cd-jump:hover{border-color:var(--sports,#3ddc84);color:#fff}
.cd-count{font-size:12px;font-weight:700;color:var(--muted);margin-left:8px}
.cd-table{font-size:13.5px}
.cd-table td{vertical-align:middle}
.cd-table tbody tr:nth-child(even){background:rgba(255,255,255,.018)}
.cd-na{color:var(--muted);font-style:italic;font-size:12.5px}
.mp-card{position:relative}
.mp-when{display:block;font-size:11px;font-weight:900;letter-spacing:.08em;text-transform:uppercase;color:var(--gold);margin-bottom:2px}
.sec-previews .vcat b{font-size:16px;line-height:1.25;margin:2px 0 4px;display:block}
body[data-nav="sports"] .mp-when{color:#3ddc84}
.sp-artgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}
.sp-artcard{display:block;padding:16px 18px;border:1px solid var(--line);border-radius:14px;background:linear-gradient(160deg,rgba(61,220,132,.07),rgba(0,0,0,0));text-decoration:none;color:inherit;transition:border-color .18s,transform .18s}
.sp-artcard:hover{border-color:rgba(61,220,132,.5);transform:translateY(-2px)}
.sp-artcard-kicker{display:block;font-size:10px;font-weight:900;letter-spacing:.1em;text-transform:uppercase;color:#3ddc84;margin-bottom:6px}
.sp-artcard b{display:block;font-size:16px;line-height:1.3;margin-bottom:6px}
.sp-artcard span:not(.sp-artcard-kicker){display:block;font-size:13px;line-height:1.5;color:var(--muted)}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
`);
fs.appendFileSync(path.join(root,'assets/site.css'), `\n/* Persistent navigation control */\n.bryme-back{position:fixed;left:14px;top:74px;z-index:80;display:grid;place-items:center;width:34px;height:34px;border:1px solid rgba(255,255,255,.22);border-radius:50%;background:rgba(8,9,11,.88);backdrop-filter:blur(10px);color:#fff;font:900 21px/1 system-ui,sans-serif;padding:0;cursor:pointer;box-shadow:0 7px 22px rgba(0,0,0,.35)}.bryme-back:hover{border-color:var(--sports,#3ddc84);transform:translateX(-1px)}@media(max-width:760px){.bryme-back{left:10px;top:64px;width:32px;height:32px}}\n`);

/* UPGRADE LAYER appended in the build so it is never lost on rebuild */
fs.appendFileSync(path.join(root,'assets/site.css'), `
/* ============================================================
   UPGRADE LAYER — interactive controls, focus & LIGHT THEME.
   Appended last (after the platform sheet). Dark remains the
   default; the light theme flips the page canvas and content
   surfaces while the cinematic full-bleed banners (hero, movie
   hero, sports feature, footer, mobile bar) stay dark.
   ============================================================ */
html{color-scheme:dark}
[data-theme="light"]{color-scheme:light}
.theme-toggle{display:inline-grid;place-items:center;width:34px;height:34px;flex:none;border:1px solid var(--line);border-radius:50%;background:rgba(255,255,255,.04);color:var(--text);cursor:pointer;padding:0;transition:border-color .18s,color .18s,transform .18s}
.theme-toggle:hover{border-color:var(--accent);color:var(--accent);transform:rotate(20deg)}
.theme-toggle svg{display:block}
[data-theme="light"] .theme-toggle{background:#fff;color:#171b22}
[data-theme="light"] .theme-toggle:hover{color:var(--accent)}
#bryme-progress{position:fixed;top:0;left:0;height:3px;width:0;z-index:120;background:linear-gradient(90deg,#e94b2c,#e7bb5c,#3ddc84,#4f8ef7);box-shadow:0 0 8px rgba(233,75,44,.55);pointer-events:none}
.bryme-top{position:fixed;right:18px;bottom:84px;z-index:90;display:grid;place-items:center;width:42px;height:42px;border:1px solid rgba(255,255,255,.22);border-radius:50%;background:rgba(8,9,11,.85);backdrop-filter:blur(10px);color:#fff;cursor:pointer;padding:0;box-shadow:0 8px 24px rgba(0,0,0,.4);opacity:0;transform:translateY(12px);pointer-events:none;transition:opacity .22s,transform .22s,border-color .18s}
.bryme-top.is-visible{opacity:1;transform:translateY(0);pointer-events:auto}
.bryme-top:hover{border-color:var(--accent);color:var(--accent)}
.bryme-top svg{display:block}
[data-theme="light"] .bryme-top{background:rgba(255,255,255,.92);color:#171b22;border-color:rgba(20,30,44,.2)}
@media(min-width:761px){.bryme-top{bottom:30px}}
@media(max-width:760px){.bryme-top{bottom:78px}}
a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible,summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:3px}
[data-theme="light"] a:focus-visible,[data-theme="light"] button:focus-visible{outline-color:#c24427}
[data-theme="light"]{--bg:#f2f4f7;--panel:#ffffff;--line:#d7dbe2;--text:#161b22;--muted:#5a6572;--accent:#cf4424;--gold:#a86f14}
[data-theme="light"] body{background:radial-gradient(1100px 520px at 12% -8%, rgba(233,75,44,.06), transparent 60%),radial-gradient(900px 460px at 88% 0%, rgba(79,142,247,.06), transparent 58%),var(--bg);background-attachment:fixed}
[data-theme="light"] .top{background:rgba(255,255,255,.86);border-bottom-color:#dde1e7}
[data-theme="light"] .topnav a:hover,[data-theme="light"] .topnav a.active{color:#161b22}
[data-theme="light"] .nav-search{color:#a06b12!important}
[data-theme="light"] .hero h1,[data-theme="light"] .home-hero h1,[data-theme="light"] .article-hero h1{background:linear-gradient(100deg,#161b22 20%,#4a3b2e 70%);-webkit-background-clip:text;background-clip:text;color:transparent}
[data-theme="light"] .prose p,[data-theme="light"] .article-body p,[data-theme="light"] .sp-score span{color:#3a434e}
[data-theme="light"] .article-body blockquote{color:#2b333c}
[data-theme="light"] .prose a{color:#c24427;border-bottom-color:rgba(194,68,39,.35)}
[data-theme="light"] .prose a:hover{color:#8f2d16;border-bottom-color:#8f2d16}
[data-theme="light"] .crumb a:hover,[data-theme="light"] .badge a:hover,[data-theme="light"] .footer-col a:hover,[data-theme="light"] .genre-chips a:hover,[data-theme="light"] .sp-mwnav a:hover,[data-theme="light"] .sp-club-nav a:hover{color:#161b22}
[data-theme="light"] .genre-chips a{color:#2b333c}
[data-theme="light"] .genre-chips a:hover{color:#fff}
[data-theme="light"] .meta-source{color:#5a6572}
[data-theme="light"] .meta-source a{color:#3a434e}
[data-theme="light"] .meta-source a:hover{color:#161b22}
[data-theme="light"] .cta-ghost{color:#161b22;border-color:#cf4424}
[data-theme="light"] .cta-ghost:hover{color:#fff}
[data-theme="light"] .rail-chart .tile:before{-webkit-text-stroke:1.4px rgba(20,30,44,.35)}
[data-theme="light"] .rail-chart .tile:hover{background:rgba(20,30,44,.05)}
[data-theme="light"] .section-head a,[data-theme="light"] .tile-rating,[data-theme="light"] .mp-when{color:#a06b12}
[data-theme="light"] .searchbox,[data-theme="light"] .stabs,[data-theme="light"] .ffield select,[data-theme="light"] .rec-form input{background:#fff;border-color:var(--line);color:#161b22}
[data-theme="light"] .filterbar{background:#fff}
[data-theme="light"] .fbtn{background:#fff;color:#5a6572}
[data-theme="light"] .fbtn:hover{color:#161b22}
[data-theme="light"] .rec-inner,[data-theme="light"] .take-card,[data-theme="light"] .vcat,[data-theme="light"] .vchip,[data-theme="light"] .genre-panel,[data-theme="light"] .trend-note,[data-theme="light"] .vnote,[data-theme="light"] .vstate,[data-theme="light"] .sp-result,[data-theme="light"] .sp-credits,[data-theme="light"] .rec-suggest,[data-theme="light"] .rec-miss,[data-theme="light"] .story-grid a{background:#ffffff;border-color:var(--line)}
[data-theme="light"] .rec-inner{box-shadow:0 20px 60px rgba(20,30,44,.12)}
[data-theme="light"] .vcat:hover{box-shadow:0 12px 26px rgba(20,30,44,.14)}
[data-theme="light"] .vchip:hover{box-shadow:0 10px 26px rgba(20,30,44,.12)}
[data-theme="light"] .story-grid{background:#d7dbe2}
[data-theme="light"] .story-grid a:hover{background:#eef1f5}
[data-theme="light"] .discover-cta{background:linear-gradient(90deg,#ffffff,#eef1f5);border-top-color:#d7dbe2}
[data-theme="light"] .genre-chips a b{color:#5a6572}
[data-theme="light"] .rec-sug-item:hover,[data-theme="light"] .rec-sug-item:focus-visible{background:#eef1f5}
[data-theme="light"] .rec-sug-ph{background:#e3e7ec}
[data-theme="light"] .sp-msec,[data-theme="light"] .sp-club,[data-theme="light"] .sp-mw,[data-theme="light"] .sp-match-hero,[data-theme="light"] .sp-mc-card.solid{background:#ffffff;border-color:var(--line)}
[data-theme="light"] .sp-club-head,[data-theme="light"] .sp-mw-head{background:linear-gradient(90deg,#ffffff,#f1f4f8)}
[data-theme="light"] .sp-msec p,[data-theme="light"] .sp-msec b,[data-theme="light"] .sp-club-notes,[data-theme="light"] .sp-fixt-day{color:#2b333c}
[data-theme="light"] .sp-fixture:hover{background:#f3f6f9}
[data-theme="light"] .cd-jump{background:#fff;border-color:var(--line);color:#2b333c}
[data-theme="light"] .cd-jump:hover{color:#161b22}
[data-theme="light"] .sp-artcard{background:linear-gradient(160deg,rgba(61,220,132,.08),rgba(255,255,255,0))}
[data-theme="light"] .trailer-error{background:rgba(179,74,58,.06);border-color:#d9a09a}
[data-theme="light"] .trailer-error b{color:#b33a2a}
[data-theme="light"] .trailer-disclaimer{background:rgba(231,187,92,.16);border-color:rgba(196,150,45,.4);color:#7a5a10}
[data-theme="light"] .sp-pill{background:rgba(61,220,132,.14);color:#128a4e}
[data-theme="light"] .vhero p,[data-theme="light"] .vhero .lead,[data-theme="light"] .sports-feature p,[data-theme="light"] .home-hero p{color:#d2d6d9}
[data-theme="light"] .movie-hero h1,[data-theme="light"] .movie-hero p,[data-theme="light"] .movie-hero .lead{color:#fff}
[data-theme="light"] .movie-hero .badge{color:#d3d7d9}
[data-theme="light"] .hero-slide p,[data-theme="light"] .hero-slide-kicker{color:#d2d6d9}
[data-theme="light"] .mobile-nav{background:rgba(255,255,255,.97);border-top-color:#d7dbe2}
[data-theme="light"] .mobile-nav a{color:#5a6572}
[data-theme="light"] .mobile-nav a:active,[data-theme="light"] .mobile-nav a.active{color:#161b22;background:#eef1f5}
[data-theme="light"] .footer{background:linear-gradient(180deg,#0d1014,#08090b)}
/* Hero carousel: non-active slides use h2 (single h1 per page); keep them styled
   identically to the active h1 so the carousel visuals don't change. */
.hero-slide h2{font-size:clamp(42px,7vw,78px);line-height:.96;max-width:760px;margin:0 0 10px;font-weight:700;letter-spacing:0}
@media(max-width:760px){.hero-slide h2{font-size:40px}}
`);

fs.appendFileSync(path.join(root,'assets/site.css'), `
/* Writing Field Notes desk */
.wo-feature-card{border-color:rgba(231,187,92,.45)!important;background:linear-gradient(160deg,rgba(231,187,92,.12),#101318)!important}
.wo-banner{border:1px solid var(--line);border-left:3px solid var(--gold);background:#101318;padding:14px 16px;border-radius:0 8px 8px 0;margin:0 0 18px;max-width:820px}
.wo-banner b{display:block;margin-bottom:4px}
.wo-banner p{margin:0;color:var(--muted);font-size:14px;line-height:1.6}
.wo-how{padding:8px 0 10px;max-width:820px}
.wo-steps{margin:10px 0 16px;padding-left:20px}
.wo-steps li{margin:0 0 10px;color:#d9dde1;line-height:1.55}
.wo-filters{display:flex;flex-wrap:wrap;gap:12px;align-items:end;padding:14px 16px;margin:0 0 18px;background:#101318;border:1px solid var(--line);border-radius:8px}
.wo-filters label{display:flex;flex-direction:column;gap:4px;font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.wo-filters select{background:#171b20;color:var(--text);border:1px solid var(--line);border-radius:4px;font:inherit;font-size:13px;padding:8px 10px;min-width:160px}
.wo-count{margin:0;font-size:12.5px;color:var(--muted);font-weight:700;letter-spacing:0;text-transform:none}
.wo-grid{display:grid;gap:14px}
.wo-card{border:1px solid var(--line);border-radius:10px;background:linear-gradient(160deg,#161b23,#0f1216);padding:18px 18px 16px}
.wo-card-head{display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px;align-items:baseline}
.wo-card h3{margin:0;font-size:20px;line-height:1.2}
.wo-checked{font-size:12px;color:var(--gold);font-weight:800}
.wo-meta{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}
.wo-pay,.wo-contact,.wo-from,.wo-flag{font-size:11px;font-weight:800;letter-spacing:.04em;padding:3px 9px;border-radius:12px;border:1px solid var(--line)}
.wo-pay-paid{color:#3ddc84;border-color:rgba(61,220,132,.4);background:rgba(61,220,132,.1)}
.wo-pay-unpaid{color:#ff9d8a;border-color:rgba(233,75,44,.35);background:rgba(233,75,44,.08)}
.wo-pay-mixed,.wo-pay-unknown{color:var(--gold);border-color:rgba(231,187,92,.4)}
.wo-replied{color:#3ddc84;border-color:rgba(61,220,132,.4)}
.wo-no-reply,.wo-waiting{color:var(--gold);border-color:rgba(231,187,92,.4)}
.wo-not-contacted{color:var(--muted)}
.wo-tags{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px}
.wo-tag{font-size:11px;font-weight:700;border:1px solid var(--line);border-radius:12px;padding:2px 8px;color:#d9dde1}
.wo-card p{margin:0 0 8px;color:#d9dde1;font-size:15px;line-height:1.6}
.wo-unknowns,.wo-notfor,.wo-paynotes{font-size:13.5px!important;color:var(--muted)!important}
.wo-apply{display:inline-block;margin-top:6px;font-weight:800;font-size:13px;color:var(--gold)}
.wo-apply:hover{color:#fff}
.wo-pending{color:var(--muted);font-size:14px}
.wo-empty{margin-top:8px}
[data-theme="light"] .wo-card,[data-theme="light"] .wo-filters,[data-theme="light"] .wo-banner{background:#fff;border-color:var(--line)}
[data-theme="light"] .wo-card p{color:#2b333c}
[data-theme="light"] .wo-filters select{background:#fff;color:#161b22}
`);


fs.appendFileSync(path.join(root,'assets/site.css'), `
.mm-desk{margin:8px 0 28px;padding:22px 22px 18px;border:1px solid var(--line);border-radius:12px;background:linear-gradient(160deg,#161b23,#0f1216)}
.mm-desk h2{margin:18px 0 6px}
.mm-desk h2:first-child{margin-top:0}
.mm-desk-lead{color:var(--muted);font-size:14.5px;line-height:1.6;max-width:720px;margin:0 0 12px}
.mm-countries{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 8px}
.mm-country{background:#101318;border:1px solid var(--line);color:var(--text);font:inherit;font-size:13.5px;font-weight:700;padding:8px 14px;border-radius:20px;cursor:pointer}
.mm-country:hover{border-color:var(--gold)}
.mm-country.is-on{background:var(--grad-money);color:#2a1e05;border-color:transparent}
.mm-paths{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;margin:0 0 16px}
.mm-path{display:flex;flex-direction:column;gap:4px;padding:15px 17px;border:1px solid var(--line);border-radius:8px;background:#101318}
.mm-path.is-live{border-color:rgba(231,187,92,.45)}
.mm-path.is-live:hover{transform:translateY(-2px)}
.mm-path.is-later{opacity:.62;cursor:default}
.mm-path b{font-size:15px}
.mm-path span{font-size:12.5px;color:var(--muted);line-height:1.5}
.wo-inline-desk{padding:16px;margin:0 0 18px}
.wo-facts{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;margin:12px 0;padding:0}
.wo-facts div{border:1px solid var(--line);border-radius:8px;padding:10px 12px;background:rgba(0,0,0,.15)}
.wo-facts dt{font-size:10.5px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 4px}
.wo-facts dd{margin:0;font-size:13.5px;font-weight:700;line-height:1.4}
.wo-actions{display:flex;flex-wrap:wrap;gap:14px;margin-top:8px}
[data-theme="light"] .mm-desk,[data-theme="light"] .mm-path,[data-theme="light"] .mm-country,[data-theme="light"] .wo-facts div{background:#fff}
[data-theme="light"] .mm-country.is-on{color:#2a1e05}
`);


fs.appendFileSync(path.join(root,'assets/site.css'), `
/* ============================================================
   MOBILE POLISH LAYER
   Keep the site visual: rows of posters, 2-up cards.
   Do not flatten everything into a single column list.
   ============================================================ */
html,body{max-width:100%;overflow-x:clip}
.shell,.home-main,.hero-slide-inner,.movie-hero,.rec-inner,.mm-desk,.vcat,.tile,.wo-card{min-width:0}
input,select,textarea{font-size:16px}
.top-tools{display:flex;align-items:center;gap:8px;margin-left:auto;flex:none}
.header-search{display:none;font-size:12.5px;font-weight:800;color:var(--gold);border:1px solid var(--line);border-radius:16px;padding:6px 12px}
.header-search:hover{color:#fff;border-color:var(--accent)}
@media(max-width:760px){
  html{text-size-adjust:100%;-webkit-text-size-adjust:100%}
  body{padding-bottom:calc(64px + env(safe-area-inset-bottom,0px))}
  .shell{padding-left:16px;padding-right:16px}
  .top{padding-top:env(safe-area-inset-top,0px)}
  .top .shell{min-height:52px;padding:8px 16px;gap:10px}
  .brand{font-size:16px}
  .header-search{display:inline-flex;align-items:center;min-height:36px}
  .theme-toggle{width:36px;height:36px}
  .bryme-back{display:none}
  .mobile-nav{padding-bottom:env(safe-area-inset-bottom,0px);grid-auto-columns:minmax(52px,1fr);justify-content:stretch}
  .mobile-nav a{padding:8px 2px calc(8px + env(safe-area-inset-bottom,0px)/4);min-height:52px;display:flex;flex-direction:column;align-items:center;justify-content:center}
  .hero h1,.vhero h1,.article-hero h1,.home-hero h1{
    font-size:clamp(28px,8vw,38px);line-height:1.12;
    overflow-wrap:anywhere;max-width:100%
  }
  .hero-carousel .hero-slide h1,.hero-carousel .hero-slide h2{
    font-size:clamp(28px,8vw,38px)!important;line-height:1.1;color:#fff
  }
  .lead,.vhero .lead{font-size:15px;line-height:1.55}
  .hero-carousel{min-height:min(68svh,460px)}
  .hero-slide-inner{padding-top:92px;padding-bottom:52px}
  .hero-actions{flex-wrap:wrap;gap:10px;margin-top:16px}
  .hero-actions .cta,.hero-actions .cta-ghost{min-height:44px;padding:10px 16px}
  .hero-ctrl{width:34px;height:34px}
  /* Catalogue posters: 2-up, not a text list */
  .grid,.grid-2{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:12px!important}
  .tile h3{font-size:13px;min-height:2.5em}
  .poster img{width:100%;height:100%;object-fit:cover;object-position:center top}
  /* Homepage rails stay as sideways rows, like the desktop site */
  .rail-lead,.rail-wall,.rail-spread{
    display:grid!important;
    grid-auto-flow:column!important;
    grid-auto-columns:minmax(132px,40vw)!important;
    grid-template-columns:none!important;
    overflow-x:auto!important;
    overflow-y:hidden!important;
    scroll-snap-type:x mandatory;
    -webkit-overflow-scrolling:touch;
    padding:2px 0 14px;
    gap:12px!important
  }
  .rail-lead .tile,.rail-wall .tile,.rail-spread .tile{scroll-snap-align:start;min-width:0}
  .rail-lead .tile:first-child{grid-column:auto!important;grid-row:auto!important;display:block!important}
  .rail-lead .tile:first-child .poster{aspect-ratio:2/3!important;min-height:0!important;flex:none!important}
  .rail-lead .tile:first-child h3{font-size:13px!important;margin-top:8px}
  .rail-spread{grid-auto-columns:minmax(220px,78vw)!important}
  .rail-spread .tile{min-height:200px}
  .rail-chart{grid-template-columns:1fr!important}
  .rail-chart .tile{grid-template-columns:32px 44px minmax(0,1fr)}
  /* Cards: 2-up, not one long list */
  .vcat-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
  .vcat{padding:13px 13px}
  .vcat b{font-size:14px}
  .vcat span{font-size:12px}
  .vchips{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
  .editorial-row{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
  .genre-trio{grid-template-columns:1fr}
  .story-grid,.story-grid-title{grid-template-columns:1fr}
  .mm-desk{padding:16px 14px}
  .mm-paths{grid-template-columns:repeat(2,minmax(0,1fr))}
  .mm-country{min-height:40px}
  .wo-facts{grid-template-columns:1fr 1fr}
  .movie-hero{grid-template-columns:110px minmax(0,1fr)!important;gap:14px;padding:18px 16px 20px!important;min-height:0!important}
  .movie-hero .poster{max-height:165px!important}
  .body{display:block}
  .filterbar{flex-wrap:wrap!important;overflow:visible!important}
  .ffield select{max-width:100%}
  .rec-form{flex-direction:column}
  .rec-form input,.rec-cta{width:100%}
  .rec-inner{padding:20px 16px}
  .sp-table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;max-width:100%}
  .sp-table{min-width:520px}
  .sp-match-hero{padding:16px;gap:12px}
  .sp-match-hero h1{font-size:22px}
  .footer-grid{grid-template-columns:1fr 1fr;gap:16px}
  .discover-cta{margin-left:0;margin-right:0;padding:22px 16px}
  .cta,.cta-ghost,button.cta{min-height:44px}
}
@media(max-width:380px){
  .vchips{grid-template-columns:1fr}
  .mm-paths{grid-template-columns:1fr}
}
`);


fs.appendFileSync(path.join(root,'assets/site.css'), `
/* ============================================================
   TITLE PAGE — readable mini-editorial (movie / series / anime)
   Mobile first. Ads stay global; nothing here is an ad slot.
   ============================================================ */
.tp-page .movie-hero .lead{display:block;-webkit-line-clamp:unset;overflow:visible;font-size:16px;line-height:1.55;max-width:640px}
.tp-kicker-meta{display:flex;flex-wrap:wrap;gap:8px;align-items:center;color:#d3d7d9;font-size:13px;font-weight:700}
.tp-kicker-meta .dot{opacity:.4}
.hero-actions{flex-wrap:wrap;gap:10px 14px}
.hero-actions .cta,.hero-actions .cta-ghost{text-transform:none;letter-spacing:0;font-size:14px;font-weight:800;min-height:44px;display:inline-flex;align-items:center;margin-top:0}
.tp-watch{margin:28px 0;padding:18px;border:1px solid var(--line);border-radius:12px;background:linear-gradient(160deg,#161b23,#0f1216)}
.tp-watch h2{margin-top:0}
.tp-watch-intent{margin:28px 0 8px;padding:0}
.tp-watch-intent h2{margin-top:0}
.tp-watch-row{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0}
.tp-watch-btn{display:inline-flex;align-items:center;min-height:44px;padding:8px 14px;border:1px solid var(--line);border-radius:8px;font-weight:800;font-size:13.5px;background:#101318}
.tp-watch-btn:hover{border-color:var(--gold);color:#fff}
.tp-watch-note{font-size:13px;color:var(--muted);margin:10px 0 0;line-height:1.55}
.tp-why p,.tp-editorial p{font-size:16px;line-height:1.65}
.tp-next{margin:36px 0 8px;padding-top:22px;border-top:1px solid var(--line)}
.tp-next h3{font-size:16px;margin:16px 0 10px}
.tp-next-links{display:flex;flex-wrap:wrap;gap:10px;margin-top:12px}
.tp-next-links a{border:1px solid var(--line);border-radius:20px;padding:8px 14px;font-size:13px;font-weight:700}
.tp-next-links a:hover{border-color:var(--accent);color:#fff}
.aside dl > div{margin:0}
.tp-page .prose h2{font-size:22px;line-height:1.25}
.tp-page .prose p{font-size:16.5px;line-height:1.7}
@media(max-width:760px){
  .tp-watch{padding:14px}
  .tp-page .movie-hero .lead{font-size:14.5px}
  .grid.tp-related{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:12px!important}
  .tp-page .prose p{font-size:15.5px}
}
[data-theme="light"] .tp-watch{background:#fff}
[data-theme="light"] .tp-watch-btn{background:#fff;color:#161b22}
`);

/* ------------------------------------------------------------------ */
/* Shared markup helpers                                              */
/* ------------------------------------------------------------------ */
function image(m){
  const p = poster(m);
  if (p) return `<div class="poster"><img loading="lazy" width="480" height="360" src="${esc(p)}" alt="${esc(m.title)} poster"></div>`;
  return `<div class="poster"><img loading="lazy" width="600" height="900" src="${url(cardImage(m))}" alt="${esc(m.title)} — BRYME title card"></div>`;
}
function card(m, opts){
  opts = opts || {};
  const typeDir = m.typeDir || 'movie';
  const label = typeDir === 'series' ? 'SERIES' : (typeDir === 'anime' ? 'ANIME' : 'MOVIE');
  const genre = m.genreLabel || m.genre || '';
  const rating = m.rating && m.rating.value != null ? `<p class="tile-rating" title="BRYME editorial score">★ ${esc(String(m.rating.value))}/10 · Editorial</p>` : '';
  const rank = opts.rank ? `<span class="rank${opts.rank <= 3 ? ' top' : ''}">${opts.rank}</span>` : '';
  return `<a class="tile" href="${url('/' + typeDir + '/' + m.slug + '/')}"><div class="poster">${rank}${poster(m) ? `<img loading="lazy" decoding="async" width="320" height="180" src="${esc(poster(m) || posterThumb(m))}" alt="${esc(m.title)} trailer thumbnail">` : `<img loading="lazy" decoding="async" width="600" height="900" src="${url(cardImage(m))}" alt="${esc(m.title)} — BRYME title card">`}<span class="tile-play" aria-hidden="true"></span></div><h3>${esc(m.title)}</h3><div class="tile-meta"><span class="type-badge tb-${typeDir}">${label}</span><span>${esc(m.year || '')}</span>${genre ? `<span class="sep">·</span><span>${esc(genre)}</span>` : ''}</div>${rating}</a>`;
}
function progressiveGrid(items, initial){
  const shown = items.slice(0, initial), hidden = items.slice(initial);
  const hiddenHtml = hidden.map(m => `<div class="more-tile" hidden>${card(m)}</div>`).join('');
  const button = hidden.length ? `<button class="loadmore" type="button" data-load-more>Show more (${hidden.length} remaining)</button>` : '';
  return `<div class="grid" data-cards>${shown.map(m => card(m)).join('')}${hiddenHtml}</div>${button}`;
}
function articleRow(a){
  return `<a class="row" href="${url('/article/' + a.slug + '/')}"><div><b>${esc(a.title)}</b><span class="meta" style="font-size:12px;color:var(--muted)">${esc(a.category)} · ${esc(a.description.slice(0, 120))}</span></div></a>`;
}
function trailerSection(m){
  const tTitle = esc(m.title);
  if (!m.trailers || !m.trailers.length || !m.youtubeId) {
    return `<div class="trailer-section-inner"><div class="trailer-head"><span class="eyebrow">Trailer</span><span class="trailer-status t-none">🎬 Trailer unavailable</span></div><div class="trailer-unavailable"><b>Trailer unavailable</b><span>We couldn't find a suitable verified trailer for this title yet.</span></div></div>`;
  }
  const list = m.trailers.map(t => ({
    id: t.videoId,
    type: t.type,
    label: t.type === 'fan-made' ? 'Community trailer' : (TRAILER_LABELS[t.type] || 'Trailer'),
    channel: t.channel || '',
    videoTitle: t.videoTitle || null,
    verified: !!t.verified,
    watch: 'https://www.youtube.com/watch?v=' + t.videoId
  }));
  return `<div class="trailer-section-inner" data-trailer-box data-trailer-candidates="${esc(JSON.stringify(list))}" data-trailer-title="${tTitle}">${trailerBoxInner(m, 0)}</div>`;
}
function trailerBoxInner(m, idx){
  const t = m.trailers[idx];
  const isFan = t.type === 'fan-made';
  const dot = isFan ? '🟡' : '🟢';
  const badge = t.type === 'fan-made' ? 'Community trailer' : (TRAILER_LABELS[t.type] || 'Trailer');
  const disclaimer = isFan ? `<p class="trailer-disclaimer">This is a community-created video and is not an official trailer.</p>` : '';
  const sourceLine = t.channel ? `YouTube · via ${esc(t.channel)}` : 'YouTube';
  const verifiedNote = t.verified ? '' : `<span class="trailer-verif-note">(pending re-verification)</span>`;
  const altBtn = m.trailers.length > 1 ? `<button type="button" class="trailer-alt" data-trailer-alt>Try another trailer</button>` : '';
  const watch = 'https://www.youtube.com/watch?v=' + t.videoId;
  const ed = trailerEditorial(m, t.videoId);
  const frame = `<div class="trailer-frame" data-trailer-id="${t.videoId}"><img loading="lazy" src="https://i.ytimg.com/vi/${t.videoId}/hqdefault.jpg" alt="${esc(m.title)} trailer thumbnail"><button type="button" class="trailer-play">Play trailer</button></div><div class="trailer-controls" data-trailer-controls hidden><button type="button" class="cta" data-trailer-unmute>Unmute</button><a class="quiet-link" href="${esc(watch)}" target="_blank" rel="noopener">Watch on YouTube</a></div>`;
  const player = ed.wrap ? `<figure class="video-figure">${frame}${ed.caption}</figure>${ed.context}` : frame;
  return `<div class="trailer-head"><span class="eyebrow">Trailer</span><span class="trailer-status ${isFan ? 't-fan' : 't-ok'}">${dot} ${esc(badge)}</span></div>
  ${player}
  <p class="trailer-meta">${sourceLine}${verifiedNote}</p>${disclaimer}
  <div class="trailer-error" data-trailer-error hidden><b>Trailer currently unavailable.</b><span>This video could not be played right now.</span><span class="trailer-error-actions"><a class="quiet-link" data-trailer-watch href="${esc(watch)}" target="_blank" rel="noopener">Watch on YouTube</a><button type="button" class="trailer-retry" data-trailer-retry>Try again</button></span></div>
  <p class="trailer-fallback">If the embedded player is unavailable, <a href="${esc(watch)}" target="_blank" rel="noopener">watch the trailer on YouTube</a>.</p>${altBtn}`;
}
function pageScript(){
  return `<script>window.BRYME_BASE=''<\/script><script src="${url('/assets/site-app.js')}"><\/script>`;
}
/* Search-engine ownership verification. Codes live in site.config.json so a new
   engine is one config line, never a hand-edited HTML file that the next build
   would overwrite. Empty config -> no tags emitted at all. */
const VERIFY_TAGS = [
  site.bingVerification   ? `<meta name="msvalidate.01" content="${esc(site.bingVerification)}">` : '',
  site.googleVerification ? `<meta name="google-site-verification" content="${esc(site.googleVerification)}">` : '',
  site.yandexVerification ? `<meta name="yandex-verification" content="${esc(site.yandexVerification)}">` : ''
].join('');


function clipMeta(s, n){
  s = String(s || '').replace(/\s+/g, ' ').trim();
  if (s.length <= n) return s;
  const cut = s.slice(0, n);
  const sp = cut.lastIndexOf(' ');
  return (sp > n * 0.55 ? cut.slice(0, sp) : cut).replace(/[,;:.]+$/, '') + '…';
}
function pageTitle(raw){
  let t = String(raw || '').trim();
  t = t.replace(/\s*\|\s*BRYME\s*$/i, '').trim();
  const suffix = ' | ' + site.name;
  // Authored intent titles already carry an offer phrase after |. Do not clip them
  // back to 60 characters — that was eating "Where to Watch" / "Result & Analysis".
  if (t.includes('|')) return t + suffix;
  const budget = 70 - suffix.length;
  if (t.length > budget) t = clipMeta(t, budget);
  return t + suffix;
}
function pageDesc(raw){ return clipMeta(raw, 155); }


function legalServicesStrip(opts){
  opts = opts || {};
  const title = opts.title || 'Watch legally';
  const lead = opts.lead || 'BRYME does not host films or episodes. Confirm current, country-specific availability on a licensed service before subscribing.';
  // Do not render generic provider buttons: they looked like title availability
  // choices without a title-specific source. Verified links belong to each record.
  return `<section class="svc-strip"><div class="svc-copy"><h2>${esc(title)}</h2><p>${esc(lead)}</p></div></section>`;
}
function deskBar(o){
  const path = String(o.path || '');
  const active = String(o.activeNav || '');
  const on = /^(home|movies|series|anime|entertainment|genres)$/.test(active)
    || path === '/'
    || path === '/trending/' || path === '/search/' || path === '/genres/' || path === '/entertainment/'
    || path === '/movies/' || path === '/series/' || path === '/anime/'
    || /^\/(movie|series|anime|movies|trending|genres|search|entertainment|genre|year)\//.test(path);
  if (!on) return '';
  const items = [
    { href: '/trending/', on: path.indexOf('/trending/') === 0, label: 'Trending' },
    { href: '/movies/', on: path.indexOf('/movies/') === 0 || path.indexOf('/movie/') === 0 || path.indexOf('/year/') === 0, label: 'Movies' },
    { href: '/series/', on: path.indexOf('/series/') === 0, label: 'Series' },
    { href: '/anime/', on: path.indexOf('/anime/') === 0, label: 'Anime' },
    { href: '/genres/', on: path.indexOf('/genres/') === 0 || path.indexOf('/genre/') === 0, label: 'Genres' },
    { href: '/search/', on: path.indexOf('/search/') === 0, label: 'Search' }
  ];
  return `<nav class="desk-bar" aria-label="Catalogue"><div class="shell desk-bar-inner">${items.map(i => `<a href="${url(i.href)}"${i.on ? ' class="is-on"' : ''}>${i.label}</a>`).join('')}</div></nav>`;
}
function layout(o){

  const socialImage = socialMeta(o.image);
  const schema = o.schema ? `<script type="application/ld+json">${JSON.stringify(normalizeSchema(o.schema)).replace(/</g,'\\u003c')}<\/script>` : '';
  const active = o.activeNav || '';
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#08090b"><meta name="color-scheme" content="dark light"><link rel="icon" href="${url('/assets/favicon.svg')}" type="image/svg+xml"><link rel="icon" href="${url('/assets/favicon.png')}" type="image/png" sizes="32x32"><link rel="apple-touch-icon" href="${url('/assets/icons/apple-touch-icon.png')}"><link rel="manifest" href="${url('/manifest.webmanifest')}"><link rel="preconnect" href="https://i.ytimg.com" crossorigin><link rel="preconnect" href="https://www.youtube-nocookie.com" crossorigin><link rel="preconnect" href="https://www.youtube.com" crossorigin><title>${esc(pageTitle(o.title))}</title><meta name="description" content="${esc(pageDesc(o.description))}">${VERIFY_TAGS}${o.lcpImage?`<link rel="preload" as="image" href="${esc(o.lcpImage)}" fetchpriority="high">`:''}${o.noindex?'<meta name="robots" content="noindex,follow">':''}<link rel="canonical" href="${absUrl(o.canonical || o.path)}"><meta property="og:type" content="${esc(o.ogType || 'website')}"><meta property="og:site_name" content="${site.name}"><meta property="og:title" content="${esc(pageTitle(o.title))}"><meta property="og:description" content="${esc(pageDesc(o.description))}"><meta property="og:url" content="${absUrl(o.path)}">${socialImage}<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="${esc(pageTitle(o.title))}"><meta name="twitter:description" content="${esc(pageDesc(o.description))}"><link rel="stylesheet" href="${url('/assets/site.css')}">${schema}</head><body data-nav="${esc(o.activeNav || '')}"><header class="top"><div class="shell"><a class="brand" href="${url('/')}">BRY<b>ME</b></a><nav class="topnav"><a href="${url('/')}"${active==='home'?' class="active"':''}>Home</a><a href="${url('/entertainment/')}"${active==='entertainment'?' class="active"':''}>🎬 Entertainment</a><a href="${url('/sports/')}"${active==='sports'?' class="active"':''}>⚽ Sports</a><a href="${url('/make-money/')}"${active==='make-money'?' class="active"':''}>💰 Make Money</a><a href="${url('/tech/')}"${active==='tech'?' class="active"':''}>🤖 Tech &amp; AI</a><a class="nav-search" href="${url('/search/')}">Search</a></nav><div class="top-tools"><a class="header-search" href="${url('/search/')}" aria-label="Search">Search</a></div></div></header>${deskBar(o)}${o.body}<nav class="mobile-nav"><a href="${url('/')}"${active==='home'?' class="active"':''}><span class="mn-ico">🏠</span>Home</a><a href="${url('/entertainment/')}"${active==='entertainment'?' class="active"':''}><span class="mn-ico">🎬</span>Entertain</a><a href="${url('/sports/')}"${active==='sports'?' class="active"':''}><span class="mn-ico">⚽</span>Sports</a><a href="${url('/make-money/')}"${active==='make-money'?' class="active"':''}><span class="mn-ico">💰</span>Money</a><a href="${url('/tech/')}"${active==='tech'?' class="active"':''}><span class="mn-ico">🤖</span>Tech</a><a href="${url('/search/')}"><span class="mn-ico">🔍</span>Search</a></nav><footer class="footer"><div class="shell"><div class="footer-grid">
  <div class="footer-brand"><a class="brand" href="${url('/')}">BRY<b>ME</b></a><p>Discover what you love. Learn what you need. Find what's next.</p></div>
  <nav class="footer-col" aria-label="Explore"><h4>Verticals</h4><a href="${url('/entertainment/')}">🎬 Entertainment</a><a href="${url('/sports/')}">⚽ Sports</a><a href="${url('/make-money/')}">💰 Make Money</a><a href="${url('/tech/')}">🤖 Tech &amp; AI</a></nav>
  <nav class="footer-col" aria-label="Explore"><h4>Entertainment</h4><a href="${url('/trending/')}">What's Trending</a><a href="${url('/movies/')}">Movies</a><a href="${url('/series/')}">Series</a><a href="${url('/anime/')}">Anime</a><a href="${url('/articles/')}">Articles</a><a href="${url('/genres/')}">Genres</a></nav>
  <nav class="footer-col" aria-label="Information"><h4>Information</h4><a href="${url('/about/')}">About</a><a href="${url('/contact/')}">Contact</a><a href="${url('/editorial-policy/')}">Editorial Policy</a></nav>
  <nav class="footer-col" aria-label="Legal"><h4>Legal</h4><a href="${url('/privacy/')}">Privacy Policy</a><a href="${url('/terms/')}">Terms of Use</a><a href="${url('/disclaimer/')}">Disclaimer</a><a href="${url('/copyright/')}">Copyright / DMCA</a></nav>
</div>
<p class="footer-note">BRYME · Discover what you love. Learn what you need. Find what's next. Trailer links lead to YouTube and viewing links lead to third parties.<small>Trending Now is editorially curated by BRYME — it is not live traffic data. Popular and Editor's Picks are independent rankings. Real user analytics will replace trending once the site has enough traffic. · Build ${new Date().toISOString().slice(0, 16).replace('T', ' ')} UTC</small></div></footer>${pageScript()}</body></html>`;
}

/* ------------------------------------------------------------------ */
/* Pages                                                              */
/* ------------------------------------------------------------------ */
function write(dir, content){ const out = path.join(root, dir, 'index.html'); fs.mkdirSync(path.dirname(out), {recursive:true}); fs.writeFileSync(out, content); }
/* ================================================================
   EDITORIAL LAYOUT COMPONENTS
   The homepage was nine identical card rails stacked on top of each
   other, which reads as a template rather than a publication. These
   give each section its own shape: a lead story with supporting grid,
   a ranked chart, a poster wall, and a magazine spread. Same data,
   same links - different hierarchy.
   ================================================================ */
function clip(text, n){
  const t = String(text || '').trim();
  if (t.length <= n) return t;
  const cut = t.slice(0, n);
  const sp = cut.lastIndexOf(' ');
  return (sp > n * 0.6 ? cut.slice(0, sp) : cut).replace(/[,;:.\s]+$/, '') + '…';
}
function sectionHead(title, emoji, moreUrl, note, eyebrow){
  return `<div class="section-head"><div>${eyebrow ? `<div class="eyebrow">${esc(eyebrow)}</div>` : ''}<h2>${emoji ? emoji + ' ' : ''}${esc(title)}</h2>${note ? `<p class="section-note">${esc(note)}</p>` : ''}</div>${moreUrl ? `<a href="${url(moreUrl)}">View all</a>` : ''}</div>`;
}
/* One dominant story plus a supporting column - the standard editorial lead. */
function leadSection(title, emoji, items, moreUrl, note, eyebrow){
  if (!items || !items.length) return '';
  const [lead, ...rest] = items;
  const side = rest.slice(0, 4);
  const typeDir = m => m.typeDir || 'movie';
  const label = m => typeDir(m) === 'series' ? 'SERIES' : (typeDir(m) === 'anime' ? 'ANIME' : 'MOVIE');
  const art = m => poster(m);
  return `<section class="home-section lead-section"><div class="shell">${sectionHead(title, emoji, moreUrl, note, eyebrow)}
    <div class="lead-grid">
      <a class="lead-main" href="${url('/' + typeDir(lead) + '/' + lead.slug + '/')}">
        <div class="lead-art"><img src="${esc(art(lead))}" alt="${esc(lead.title)}" loading="lazy" width="760" height="428"></div>
        <div class="lead-copy"><span class="lead-tag">${label(lead)}${lead.year ? ' · ' + lead.year : ''}</span><h3>${esc(lead.title)}</h3>${lead.description ? `<p>${esc(clip(lead.description, 165))}</p>` : ''}${lead.rating && lead.rating.value != null ? `<span class="lead-score">★ ${esc(String(lead.rating.value))}/10 · Editorial</span>` : ''}</div>
      </a>
      <div class="lead-side">${side.map(m => `<a class="lead-item" href="${url('/' + typeDir(m) + '/' + m.slug + '/')}">
        <img src="${esc(art(m))}" alt="${esc(m.title)}" loading="lazy" width="112" height="64">
        <div><span>${label(m)}${m.year ? ' · ' + m.year : ''}</span><b>${esc(m.title)}</b></div></a>`).join('')}</div>
    </div></div></section>`;
}
/* A ranked chart - big numerals, compact rows, reads as a list not a carousel. */
function chartSection(title, emoji, items, moreUrl, note, eyebrow){
  if (!items || !items.length) return '';
  const rows = items.slice(0, 10);
  const typeDir = m => m.typeDir || 'movie';
  return `<section class="home-section chart-section"><div class="shell">${sectionHead(title, emoji, moreUrl, note, eyebrow)}
    <ol class="chart">${rows.map((m, i) => `<li><a href="${url('/' + typeDir(m) + '/' + m.slug + '/')}">
      <span class="chart-n">${i + 1}</span>
      <img src="${esc(poster(m))}" alt="${esc(m.title)}" loading="lazy" width="46" height="66">
      <span class="chart-t"><b>${esc(m.title)}</b><i>${(typeDir(m) === 'series' ? 'Series' : typeDir(m) === 'anime' ? 'Anime' : 'Movie')}${m.year ? ' · ' + m.year : ''}${m.genreLabel || m.genre ? ' · ' + esc(m.genreLabel || m.genre) : ''}</i></span>
      ${m.rating && m.rating.value != null ? `<span class="chart-s">★ ${esc(String(m.rating.value))}</span>` : ''}
    </a></li>`).join('')}</ol></div></section>`;
}
/* A dense poster wall - browsing, not reading. */
function wallSection(title, emoji, items, moreUrl, note, eyebrow, limit){
  if (!items || !items.length) return '';
  const typeDir = m => m.typeDir || 'movie';
  return `<section class="home-section wall-section"><div class="shell">${sectionHead(title, emoji, moreUrl, note, eyebrow)}
    <div class="wall">${items.slice(0, limit || 12).map(m => `<a class="wall-item" href="${url('/' + typeDir(m) + '/' + m.slug + '/')}">
      <img src="${esc(poster(m))}" alt="${esc(m.title)}" loading="lazy" width="200" height="286">
      <span class="wall-cap"><b>${esc(m.title)}</b><i>${m.year || ''}</i></span></a>`).join('')}</div></div></section>`;
}
/* Magazine spread - equal-weight feature cards with the image behind the text. */
function spreadSection(title, emoji, items, moreUrl, note, eyebrow){
  if (!items || !items.length) return '';
  const typeDir = m => m.typeDir || 'movie';
  return `<section class="home-section spread-section"><div class="shell">${sectionHead(title, emoji, moreUrl, note, eyebrow)}
    <div class="spread">${items.slice(0, 3).map(m => `<a class="spread-card" href="${url('/' + typeDir(m) + '/' + m.slug + '/')}" style="--sp-img:url('${esc(poster(m))}')">
      <span class="spread-tag">${typeDir(m) === 'series' ? 'SERIES' : typeDir(m) === 'anime' ? 'ANIME' : 'MOVIE'}${m.year ? ' · ' + m.year : ''}</span>
      <b>${esc(m.title)}</b>${m.description ? `<p>${esc(clip(m.description, 118))}</p>` : ''}</a>`).join('')}</div></div></section>`;
}

function railSection(title, emoji, items, moreUrl, note, opts){
  /* opts.variant changes only the wrapper class. Every section keeps the same
     <a class="tile"> markup and the full configured item list, so curated order,
     per-type ranks and counts stay intact - the layout differences are CSS. */
  const v = (opts && opts.variant) ? String(opts.variant) : '';
  const secClass = v ? ' sec-' + v : '';
  const variant = v ? ' rail-' + v : '';
  const eyebrow = (opts && opts.eyebrow) ? `<div class="eyebrow">${esc(opts.eyebrow)}</div>` : '';
  return `<section class="home-section${secClass}"><div class="shell"><div class="section-head"><div>${eyebrow}<h2>${emoji ? emoji + ' ' : ''}${esc(title)}</h2>${note ? `<p class="section-note">${esc(note)}</p>` : ''}</div>${moreUrl ? `<a href="${url(moreUrl)}">View all</a>` : ''}</div><div class="rail${variant}">${items.map((m,i) => card(m, {rank: opts && opts.ranked ? (opts.rankKey ? (m[opts.rankKey] || i + 1) : i + 1) : null})).join('')}</div></div></section>`;
}

/* ================================================================
   BRYME VERTICALS — Sports, Make Money, Tech & AI,
   plus the Entertainment hub. Foundation pages only: real structure,
   unique SEO, honest placeholder states. No fabricated content.
   ================================================================ */
const VERTICALS = [
  {
    dir: 'sports', emoji: '⚽', name: 'BRYME Sports', short: 'Sports', active: 'sports', accent: '#3ddc84',
    tagline: 'Football, covered properly: Premier League, Champions League, La Liga, Serie A, Bundesliga and Ligue 1.',
    desc: 'BRYME Sports is football. The Premier League, Champions League, La Liga, Serie A, Bundesliga, Ligue 1 and international football — with club histories, rivalry explainers, records, player profiles, match previews and reports. We cover one sport properly rather than several thinly.',
    note: 'Current reporting (previews, results, transfers) is always researched before publication. No result, transfer, injury, fixture or statistic is ever invented.',
    categories: [
      { slug: 'football', name: 'Football', desc: 'Premier League, Champions League, La Liga, Serie A, Bundesliga, Ligue 1, FPL and the global game.' },
      /* These six hubs existed as orphaned static pages that no build step regenerated: they were
         live, stuck on the placeholder notice and missing from the sitemap. Declaring them here puts
         them back under the build, so they list their articles and de-index themselves while empty. */
      { slug: 'champions-league', name: 'Champions League', desc: 'Europe\u2019s premier club competition: format, qualification, the knockout bracket and the nights that define it.' },
      { slug: 'records', name: 'Records', desc: 'Titles, streaks, milestones and the numbers behind the achievements.' },
      { slug: 'clubs', name: 'Clubs', desc: 'Club histories, identities, rivalries and how they are run.' },
      { slug: 'history', name: 'Football History', desc: 'Eras, turning points and the matches that changed the sport.' },
      { slug: 'international', name: 'International', desc: 'World Cup, continental championships and national-team football.' },
      { slug: 'players', name: 'Players', desc: 'Careers, playing styles and the athletes shaping the game.' }
    ]
  },
  {
    dir: 'make-money', emoji: '💰', name: 'BRYME Make Money', short: 'Make Money', active: 'make-money', accent: '#e7bb5c',
    tagline: 'Practical, honest guides to legitimate online income.',
    desc: 'BRYME Make Money covers practical and legitimate online-income topics: freelancing, remote work, AI-assisted work, microtasks, content creation, affiliate marketing, website monetization, digital products and online businesses.',
    note: 'No fake income claims. No guaranteed earnings. No fabricated statistics. Every guide distinguishes possible earnings, typical/observed earnings where reliable evidence exists, requirements, risks, fees, country availability and payment methods. Earnings always vary.',
    categories: [
      { slug: 'freelancing', name: 'Freelancing', desc: 'Starting and growing a freelance career.' },
      { slug: 'remote-work', name: 'Remote Work', desc: 'Finding and succeeding in remote jobs.' },
      { slug: 'ai-assisted-work', name: 'AI-Assisted Work', desc: 'Using AI tools to work faster and earn.' },
      { slug: 'online-services', name: 'Online Services', desc: 'Selling services online — from design to writing to support.' },
      { slug: 'microtasks', name: 'Microtasks', desc: 'Small tasks, realistic expectations, honest reviews.' },
      { slug: 'content-creation', name: 'Content Creation', desc: 'YouTube, TikTok, blogging and creator income.' },
      { slug: 'affiliate-marketing', name: 'Affiliate Marketing', desc: 'How affiliate marketing actually works.' },
      { slug: 'website-monetization', name: 'Website Monetization', desc: 'Turning a website into an income source.' },
      { slug: 'digital-products', name: 'Digital Products', desc: 'Creating and selling digital products.' },
      { slug: 'online-businesses', name: 'Online Businesses', desc: 'Small online business models explained.' },
      { slug: 'income-skills', name: 'Income Skills', desc: 'Skills that can generate income and how to learn them.' },
      { slug: 'platform-reviews', name: 'Platform Reviews', desc: 'Earning platforms reviewed honestly, with risks and fees.' },
      { slug: 'writing', name: 'Writing Opportunities', desc: 'Field notes on writing for websites: research, applications and what actually happened.' },
      { slug: 'beginner-guides', name: 'Beginner Guides', desc: 'Start here if you are new to online income.' }
    ]
  },
  {
    dir: 'tech', emoji: '🤖', name: 'BRYME Tech & AI', short: 'Tech & AI', active: 'tech', accent: '#4f8ef7',
    tagline: 'Practical technology: AI tools, apps, automation and useful websites.',
    desc: 'BRYME Tech & AI focuses on practical technology — what a tool can actually do for you — rather than generic tech news. AI tools and tutorials, ChatGPT assistants, Android apps, productivity, automation, beginner coding and website building.',
    note: 'Content is written for normal users in plain language. Highly technical topics are researched before publication; we do not pretend to be experts without doing the work.',
    categories: [
      { slug: 'ai-tools', name: 'AI Tools', desc: 'The most useful AI tools and what they actually do.' },
      { slug: 'ai-tutorials', name: 'AI Tutorials', desc: 'Step-by-step guides to getting real value from AI.' },
      { slug: 'ai-assistants', name: 'AI Assistants', desc: 'ChatGPT and AI assistants for everyday tasks.' },
      { slug: 'ai-image-video', name: 'AI Image & Video', desc: 'Generating images and video with AI.' },
      { slug: 'ai-coding', name: 'AI Coding', desc: 'Using AI to learn to code and code faster.' },
      { slug: 'useful-websites', name: 'Useful Websites', desc: 'Websites worth knowing about.' },
      { slug: 'android-apps', name: 'Android Apps', desc: 'Apps that make your phone more useful.' },
      { slug: 'productivity', name: 'Productivity', desc: 'Tools and habits that get things done.' },
      { slug: 'automation', name: 'Automation', desc: 'Letting software do the repetitive work.' },
      { slug: 'beginner-coding', name: 'Beginner Coding', desc: 'Learning to code from zero.' },
      { slug: 'developer-tools', name: 'Developer Tools', desc: 'Tools for people building software.' },
      { slug: 'website-building', name: 'Website Building', desc: 'Building websites without a degree in it.' },
      { slug: 'hosting', name: 'Hosting & Deployment', desc: 'Getting your website online.' },
      { slug: 'internet-tools', name: 'Internet Tools', desc: 'Everyday internet utilities explained.' },
      { slug: 'cybersecurity', name: 'Cybersecurity Awareness', desc: 'Staying safe online without the scare tactics.' },
      { slug: 'new-tech', name: 'New Technology', desc: 'New technology worth knowing about.' }
    ]
  }
];
searchIndex.verticals = [{ type:'entertainment', title:'BRYME Entertainment', slug:'entertainment', description:'Movies, TV series and anime with verified trailers and editorial articles.' }].concat(
  VERTICALS.flatMap(v => [{ type: v.dir, title: v.name, slug: v.dir, description: v.desc }].concat((v.categories || []).map(c => ({ type: v.dir, title: c.name, slug: v.dir + '/' + c.slug, description: c.desc }))))
);
searchIndex.verticals.push({ type:'make-money', title:'Writing Field Notes', slug:'make-money/writing', description:'I research websites, write to them, and publish what happened. A gig is not guaranteed.' });
fs.writeFileSync(path.join(root, 'data/search-index.json'), JSON.stringify(searchIndex)+'\n');
/* ================================================================
   VERTICAL ARTICLES — Make Money and Sports editorial.
   Published articles are rendered as real pages and listed on their
   category hub. A category with no published article keeps its honest
   placeholder but is marked noindex and kept out of the sitemap, so the
   site never submits empty pages to search engines. As soon as an
   article is published the hub becomes indexable again automatically.
   ================================================================ */
function loadVerticalArticles(file, key) {
  const f = path.join(root, 'content', file);
  if (!fs.existsSync(f)) return [];
  try {
    const raw = JSON.parse(fs.readFileSync(f, 'utf8'));
    const list = Array.isArray(raw) ? raw : (raw[key] || []);
    return list.filter(a => a && a.status === 'published');
  } catch (e) { return []; }
}
/* ================================================================
   AUTHORS — a byline is only a trust signal if it resolves to a real person.
   Bio content comes from content/authors.json and is supplied by the author;
   nothing here is generated or embellished. A byline with no matching record
   simply renders as plain text rather than linking nowhere.
   ================================================================ */
const AUTHORS = (() => {
  const f = path.join(root, 'content', 'authors.json');
  if (!fs.existsSync(f)) return new Map();
  try { return new Map(JSON.parse(fs.readFileSync(f, 'utf8')).map(a => [a.name, a])); }
  catch (e) { return new Map(); }
})();
const authorPath = a => '/author/' + a.slug + '/';
const authorLink = name => {
  const a = AUTHORS.get(name);
  return a ? `<a href="${url(authorPath(a))}" rel="author">${esc(name)}</a>` : esc(name);
};

/* Every vertical reads content/<dir>-articles.json, so adding a vertical needs no new code. */
const VERTICAL_ARTICLES = {};
const verticalArticleIndex = {};
/* article → category slug (explicit categorySlug wins; otherwise slugify the label) */
const articleCatSlug = a => slugify(a.categorySlug || a.category || '');
VERTICALS.forEach(v => {
  const list = loadVerticalArticles(v.dir + '-articles.json', 'articles');
  VERTICAL_ARTICLES[v.dir] = list;
  const idx = new Map();
  list.forEach(a => {
    const key = articleCatSlug(a);
    if (!idx.has(key)) idx.set(key, []);
    idx.get(key).push(a);
  });
  verticalArticleIndex[v.dir] = idx;
});
const moneyArticles = VERTICAL_ARTICLES['make-money'] || [];
const sportsArticlesPub = VERTICAL_ARTICLES.sports || [];
const articlePathFor = (dir, a) => '/' + dir + '/' + a.slug + '/';
/* An article slug must never collide with a category/section slug at the same level. */
VERTICALS.forEach(v => {
  const reserved = new Set(['articles'].concat((v.categories || []).map(c => c.slug)));
  if (v.dir === 'make-money') reserved.add('writing-opportunities');
  (v.dir === 'sports' ? sportsArticlesPub : v.dir === 'make-money' ? moneyArticles : []).forEach(a => {
    if (reserved.has(a.slug)) throw new Error(`Article slug "${a.slug}" collides with a ${v.dir} section slug. Rename the article slug in content/${v.dir === 'sports' ? 'sports' : 'make-money'}-articles.json.`);
  });
});

/* ---------- Shared editorial images (cinematic stills, no fake faces) ---------- */
const HERO_IMG = {
  'ballon-dor-race': '/assets/img/sports/hero-ballon-dor.jpg',
  'ballon-dor-2026-our-picks': '/assets/img/sports/hero-ballon-dor.jpg',
  'world-cup-2026-spain-champions': '/assets/img/sports/hero-world-cup.jpg',
  'premier-league-matchweek-1-guide': '/assets/img/sports/hero-matchweek.jpg',
  'arsenal-title-defence': '/assets/img/sports/hero-arsenal.jpg',
  'manchester-city-without-guardiola': '/assets/img/sports/hero-man-city-manager.jpg',
  'liverpools-next-chapter': '/assets/img/sports/hero-liverpool.jpg',
  'newly-promoted-clubs-approach': '/assets/img/sports/hero-premier-league.jpg',
  'five-matches-we-cannot-wait-to-watch': '/assets/img/sports/hero-matches.jpg',
  'champions-league-format-explained': '/assets/img/sports/hero-matches.jpg',
  'champions-league-records': '/assets/img/sports/hero-ballon-dor.jpg',
  'premier-league-2026-27-season-guide': '/assets/img/sports/hero-premier-league.jpg',
  'community-shield-2026-arsenal-manchester-city': '/assets/img/sports/hero-arsenal.jpg',
  'english-champions-since-1888': '/assets/img/sports/hero-premier-league.jpg',
  'beginners-guide-to-making-money-online': '/assets/img/money/hero-beginner.jpg',
  'freelance-platform-fees-explained': '/assets/img/money/hero-fees.jpg',
  'writing-field-notes-how-this-works': '/assets/img/money/hero-writing.jpg',
  'website-monetization-guide': '/assets/img/money/hero-beginner.jpg',
  'ai-assistant-data-training-settings': '/assets/img/tech/hero-privacy.jpg',
  'learning-to-code-on-a-phone-termux': '/assets/img/tech/hero-phone-code.jpg',
  'render-deployment-failures-what-they-taught-me': '/assets/img/tech/hero-deploy.jpg',
  'where-to-host-website-for-free': '/assets/img/tech/hero-hosting.jpg',
  'nigerian-thrillers-worth-your-time': '/assets/img/ent/hero-nollywood.jpg',
  'korean-cinema-starter-guide-rebuilt': '/assets/img/ent/hero-korean.jpg',
  'indian-cinema-first-five': '/assets/img/ent/hero-indian.jpg',
  'interstellar-ending-explained': '/assets/img/ent/hero-space.jpg',
  'movies-like-interstellar-guide': '/assets/img/ent/hero-space.jpg',
  'dune-sci-fi-epics-guide': '/assets/img/ent/hero-space.jpg',
  'christopher-nolan-movies-order': '/assets/img/ent/hero-space.jpg',
  'alien-franchise-in-order': '/assets/img/ent/hero-space.jpg',
  'movies-like-parasite': '/assets/img/ent/hero-korean.jpg',
  'squid-game-season-1-why-it-became-a-global-phenomenon': '/assets/img/ent/hero-survival.jpg',
  'alice-in-borderland-vs-squid-game': '/assets/img/ent/hero-survival.jpg',
  '10-shows-like-alice-in-borderland-you-should-watch-next': '/assets/img/ent/hero-survival.jpg',
  'breaking-bad-two-seasons-opinion': '/assets/img/ent/hero-series.jpg',
  'into-the-badlands-was-underrated': '/assets/img/ent/hero-series.jpg',
  'prison-break-season-1-watching-all-night': '/assets/img/ent/hero-series.jpg',
  'why-prison-break-season-1-is-still-one-of-the-best-tv-seasons': '/assets/img/ent/hero-series.jpg',
  'one-piece-vs-naruto': '/assets/img/ent/hero-anime.jpg',
  'solo-leveling-e-rank-to-s-rank': '/assets/img/ent/hero-anime.jpg',
  'was-eren-yeager-really-the-villain': '/assets/img/ent/hero-anime.jpg',
  '10-anime-like-solo-leveling-you-should-watch': '/assets/img/ent/hero-anime.jpg',
  'solo-leveling-vs-hunter-x-hunter-the-similarities-and-differences': '/assets/img/ent/hero-anime.jpg',
  'solo-leveling-from-e-rank-hunter-to-one-of-animes-most-powerful-characters': '/assets/img/ent/hero-anime.jpg'
};
const CAT_IMG = {
  'sports/football': '/assets/img/sports/hero-premier-league.jpg',
  'sports/champions-league': '/assets/img/sports/hero-matches.jpg',
  'sports/records': '/assets/img/sports/hero-ballon-dor.jpg',
  'sports/clubs': '/assets/img/sports/hero-arsenal.jpg',
  'sports/history': '/assets/img/sports/hero-premier-league.jpg',
  'sports/international': '/assets/img/sports/hero-world-cup.jpg',
  'sports/players': '/assets/img/sports/hero-ballon-dor.jpg',
  'sports/premier-league': '/assets/img/sports/hero-premier-league.jpg',
  'sports/la-liga': '/assets/img/sports/hero-la-liga.jpg',
  'sports/serie-a': '/assets/img/sports/hero-serie-a.jpg',
  'sports/bundesliga': '/assets/img/sports/hero-bundesliga.jpg',
  'sports/ligue-1': '/assets/img/sports/hero-ligue-1.jpg',
  'sports/fpl': '/assets/img/sports/hero-fpl.jpg',
  'sports/transfers': '/assets/img/sports/hero-man-city-manager.jpg',
  'make-money/freelancing': '/assets/img/money/hero-fees.jpg',
  'make-money/website-monetization': '/assets/img/money/hero-beginner.jpg',
  'make-money/content-creation': '/assets/img/money/hero-writing.jpg',
  'make-money/writing': '/assets/img/money/hero-writing.jpg',
  'tech/ai-tools': '/assets/img/tech/hero-privacy.jpg',
  'tech/ai-assistants': '/assets/img/tech/hero-privacy.jpg',
  'tech/beginner-coding': '/assets/img/tech/hero-phone-code.jpg',
  'tech/android-apps': '/assets/img/tech/hero-phone-code.jpg',
  'tech/developer-tools': '/assets/img/tech/hero-deploy.jpg',
  'tech/hosting': '/assets/img/tech/hero-hosting.jpg',
  'tech/website-building': '/assets/img/tech/hero-hosting.jpg',
  'hub/entertainment': '/assets/img/ent/hero-cinema.jpg',
  'hub/movies': '/assets/img/ent/hero-cinema.jpg',
  'hub/series': '/assets/img/ent/hero-series.jpg',
  'hub/anime': '/assets/img/ent/hero-anime.jpg',
  'hub/sports': '/assets/img/sports/hero-premier-league.jpg',
  'hub/make-money': '/assets/img/money/hero-writing.jpg',
  'hub/tech': '/assets/img/tech/hero-privacy.jpg',
  'hub/articles': '/assets/img/ent/hero-cinema.jpg'
};
const DIR_FALLBACK = {
  sports: '/assets/img/sports/hero-premier-league.jpg',
  'make-money': '/assets/img/money/hero-writing.jpg',
  tech: '/assets/img/tech/hero-privacy.jpg',
  entertainment: '/assets/img/ent/hero-cinema.jpg',
  article: '/assets/img/ent/hero-cinema.jpg'
};
function heroFor(slug, dir){
  if (slug && HERO_IMG[slug]) return HERO_IMG[slug];
  return DIR_FALLBACK[dir] || '/assets/img/ent/hero-cinema.jpg';
}
function catImg(key){ return CAT_IMG[key] || ''; }
function photoTile(href, title, desc, img){
  const style = img ? ` style="--card-img:url('${img}')"` : '';
  return `<a class="vcat${img ? ' vcat-photo' : ''}" href="${url(href)}"${style}><b>${esc(title)}</b><span>${esc(desc)}</span></a>`;
}
function storyPhoto(href, kicker, title, desc, img){
  const style = img ? ` style="--card-img:url('${img}')"` : '';
  return `<a class="story-photo" href="${url(href)}"${style}><span>${esc(kicker || '')}</span><h3>${esc(title)}</h3><p>${esc(String(desc || '').slice(0, 140))}</p><b>Read story</b></a>`;
}

const articleCard = (dir, a) => photoTile(articlePathFor(dir, a), a.title, a.excerpt || '', heroFor(a.slug, dir));

const EMPTY_HUB_PATHS = new Set();
const WRITING_EXTRA_PATHS = [];
const verticalChip = v => `<a class="vchip vchip-${v.dir}" href="${url('/' + v.dir + '/')}"><span class="vchip-emoji">${v.emoji}</span><span class="vchip-name">${esc(v.name)}</span><span class="vchip-tag">${esc(v.tagline)}</span></a>`;
/* Core category headers — the pages Googlebot should treat as the site’s
   spine. Used in-body (not only nav/footer) so crawl paths are obvious. */
const CORE_HUBS = [
  { id: 'entertainment', path: '/entertainment/', emoji: '🎬', name: 'Entertainment', tag: 'Movies, series, anime and articles', chip: 'entertainment' },
  { id: 'movies', path: '/movies/', emoji: '🎥', name: 'Movies', tag: 'Trailers and the movie catalogue', chip: 'entertainment' },
  { id: 'series', path: '/series/', emoji: '📺', name: 'TV Series', tag: 'Series catalogue', chip: 'entertainment' },
  { id: 'anime', path: '/anime/', emoji: '🍥', name: 'Anime', tag: 'Anime catalogue', chip: 'entertainment' },
  { id: 'sports', path: '/sports/', emoji: '⚽', name: 'Sports', tag: 'Football covered properly', chip: 'sports' },
  { id: 'make-money', path: '/make-money/', emoji: '💰', name: 'Make Money', tag: 'Verified writing markets and honest guides', chip: 'make-money' },
  { id: 'tech', path: '/tech/', emoji: '🤖', name: 'Tech & AI', tag: 'Practical tools and tutorials', chip: 'tech' }
];
function coreHubStrip(currentId, opts){
  opts = opts || {};
  const title = opts.title || 'Also on BRYME';
  const lead = opts.lead || 'The main sections of the site. Open the next one that matches what you came for.';
  const photoIds = opts.photos || [];
  const photos = photoIds.map((id, i) => {
    const h = CORE_HUBS.find(x => x.id === id);
    if (!h) return '';
    const img = catImg('hub/' + id) || '';
    return `<a class="hub-photo hub-photo-${h.chip}${i === 0 ? ' hub-photo-first' : ''}" href="${url(h.path)}"${img ? ` style="--card-img:url('${img}')"` : ''}><span>${esc(h.name)}</span><h3>${esc(h.tag)}</h3></a>`;
  }).join('');
  const photoSet = new Set(photoIds);
  const chips = CORE_HUBS.filter(h => h.id !== currentId && !photoSet.has(h.id)).map(h =>
    `<a class="vchip vchip-${h.chip}" href="${url(h.path)}"><span class="vchip-emoji">${h.emoji}</span><span class="vchip-name">${esc(h.name)}</span><span class="vchip-tag">${esc(h.tag)}</span></a>`
  ).join('');
  return `<section class="section core-hubs" data-core-hubs><div class="section-head"><h2>${esc(title)}</h2></div><p class="section-note">${esc(lead)}</p>${photos ? `<div class="hub-photos">${photos}</div>` : ''}${chips ? `<div class="vchips">${chips}</div>` : ''}</section>`;
}
function sendBar(path, title){
  const abs = absUrl(path);
  const text = title + ' — ' + abs;
  const wa = 'https://wa.me/?text=' + encodeURIComponent(text);
  return `<div class="send-bar" data-send-bar>
    <p>Send this page</p>
    <a class="send-wa" href="${esc(wa)}" target="_blank" rel="noopener">WhatsApp</a>
    <button type="button" class="quiet-link share-action" data-share-path="${esc(path)}" data-share-title="${esc(title)}">Copy link</button>
  </div>`;
}
const SENDABLE_META = {
  'shogun': { title: 'Shōgun (2024) | Cast, Trailer, Episodes & Where to Watch', desc: 'Shōgun (2024): FX series. Official trailer, billed cast, story, and how to find a legal stream. BRYME does not host episodes.' },
  'dune-part-two': { title: 'Dune: Part Two (2024) trailer & story', desc: 'What the film is, the official trailer, and legal viewing notes. Not a download page.' },
  'a-tribe-called-judah': { title: 'A Tribe Called Judah — Lagos film', desc: 'Funke Akindele’s Lagos family crime film: what it is, who it is for, and legal watch notes.' },
  'squid-game': { title: 'Squid Game (2021) story & what next', desc: 'What Squid Game is and what to open next on BRYME. No unofficial streams.' },
  'nigerian-thrillers-worth-your-time': { title: 'Five Nigerian thrillers to start with', desc: 'October 1, The Figurine, Brotherhood and more — a short BRYME starter, not a dump.' },
  'writing': { title: 'Writing gigs BRYME actually checked', desc: 'Official rates and doors. A gig is not guaranteed.' },
  'premier-league-matchweek-1-guide': { title: 'Premier League Matchweek 1 — confirmed fixtures', desc: 'The opening round, times and TV. No predictions.' },
  'arsenal-title-defence': { title: 'Arsenal’s title defence starts Friday', desc: 'Coventry at the Emirates. Community Shield already won. The league is not.' }
};
const MONEY_DESK = (() => {
  const fallback = {
    countries: [
      { id: 'nigeria', name: 'Nigeria' },
      { id: 'ghana', name: 'Ghana' },
      { id: 'kenya', name: 'Kenya' },
      { id: 'south-africa', name: 'South Africa' },
      { id: 'united-kingdom', name: 'United Kingdom' },
      { id: 'united-states', name: 'United States' },
      { id: 'other', name: 'Another country' }
    ],
    paths: [
      { id: 'writing', name: 'Writing', status: 'live', blurb: 'Publications I researched and wrote to. A gig is not guaranteed.' },
      { id: 'design', name: 'Design', status: 'later', blurb: 'Same format when I have first-hand notes.' },
      { id: 'video-editing', name: 'Video editing', status: 'later', blurb: 'Same format when I have first-hand notes.' },
      { id: 'virtual-assistance', name: 'Virtual assistance', status: 'later', blurb: 'Same format when I have first-hand notes.' }
    ]
  };
  const f = path.join(root, 'content', 'writing-opportunities.json');
  if (!fs.existsSync(f)) return fallback;
  try {
    const d = JSON.parse(fs.readFileSync(f, 'utf8'));
    return {
      countries: Array.isArray(d.countries) && d.countries.length ? d.countries : fallback.countries,
      paths: Array.isArray(d.paths) && d.paths.length ? d.paths : fallback.paths
    };
  } catch (e) { return fallback; }
})();
function moneyDeskHtml(){
  const countries = MONEY_DESK.countries.map(c =>
    `<button type="button" class="mm-country" data-mm-country="${esc(c.id)}" data-mm-country-name="${esc(c.name)}">${esc(c.name)}</button>`
  ).join('');
  const paths = MONEY_DESK.paths.map(p => {
    if (p.status === 'live') {
      return `<a class="mm-path is-live" data-mm-path="${esc(p.id)}" href="${url('/make-money/writing/')}"><b>${esc(p.name)}</b><span>${esc(p.blurb || '')}</span></a>`;
    }
    return `<div class="mm-path is-later"><b>${esc(p.name)}</b><span>Later — same research standard, not open yet.</span></div>`;
  }).join('');
  return `<section class="mm-desk" data-mm-desk>
    <h2>1. Your country</h2>
    <p class="mm-desk-lead">The catalogue you see next depends on where you write from. A site that only takes US writers will not be sold to Lagos as “open to everyone.”</p>
    <div class="mm-countries" role="group" aria-label="Choose your country">${countries}</div>
    <h2>2. What you want to do</h2>
    <p class="mm-desk-lead">Writing is open. Other paths use the same format when I have first-hand notes. I will not invent a catalogue to look busy.</p>
    <div class="mm-paths">${paths}</div>
    <div class="vnote">Nothing is guaranteed. A site can close submissions, ignore you, or stop paying. Every card is dated. If I do not know, the card says unknown.</div>
  </section>
  <script>
  (function(){
    var KEY = 'bryme-mm-country';
    var desk = document.querySelector('[data-mm-desk]');
    if (!desk) return;
    function qCountry(){ try { return new URLSearchParams(location.search).get('country') || ''; } catch (e) { return ''; } }
    var current = qCountry();
    try { if (!current) current = localStorage.getItem(KEY) || ''; } catch (e) {}
    function setCountry(id){
      current = id || '';
      try { if (id) localStorage.setItem(KEY, id); } catch (e) {}
      desk.querySelectorAll('[data-mm-country]').forEach(function(btn){
        btn.classList.toggle('is-on', btn.getAttribute('data-mm-country') === current);
      });
      desk.querySelectorAll('a[data-mm-path]').forEach(function(a){
        var base = a.getAttribute('href').split('?')[0];
        a.setAttribute('href', current ? base + '?country=' + encodeURIComponent(current) : base);
      });
    }
    desk.addEventListener('click', function(e){
      var btn = e.target.closest('[data-mm-country]');
      if (!btn) return;
      setCountry(btn.getAttribute('data-mm-country'));
    });
    setCountry(current);
  })();
  </script>`;
}


function verticalPage(v, category){
  const catPath = category ? '/' + v.dir + '/' + category.slug + '/' : '/' + v.dir + '/';
  const crumbs = [{name:'Home', path:'/'}, {name:v.name, path:'/' + v.dir + '/'}];
  if (category) crumbs.push({name:category.name, path:catPath});
  const catGrid = (v.dir === 'make-money' ? photoTile('/make-money/writing/', 'Writing Field Notes', 'I research websites, write to them, and publish what happened. A gig is not guaranteed.', catImg('make-money/writing')) : '') + (v.categories || []).map(c => photoTile('/' + v.dir + '/' + c.slug + '/', c.name, c.desc, catImg(v.dir + '/' + c.slug) || catImg('hub/' + v.dir))).join('') + (v.dir === 'make-money' ? photoTile('/make-money/beginners-guide-to-making-money-online/', 'Beginner’s Guide to Making Money Online', 'An honest, skill-first guide to avoiding shortcuts and building value.', heroFor('beginners-guide-to-making-money-online', 'make-money')) : '');
  const sportsEditorial = (() => { const f = path.join(root, 'content', 'sports-articles.json'); if (!fs.existsSync(f)) return []; try { return (JSON.parse(fs.readFileSync(f, 'utf8')).articles || []).filter(a => a.status === 'published'); } catch (_) { return []; } })();
  const sportsStoriesBlock = (v.dir === 'sports' && !category) ? `<section class="section"><div class="section-head"><h2>BRYME Sports Stories</h2><a href="${url('/sports/articles/')}">All stories</a></div>${sportsEditorial.length ? `<div class="story-grid">${sportsEditorial.slice(0, 8).map(a => storyPhoto(articlePathFor('sports', a), a.category || 'Sports', a.title, a.excerpt || '', heroFor(a.slug, 'sports'))).join('')}</div>` : `<div class="vstate"><b>Stories are being prepared</b><p>Drafts are researched and reviewed before publication. Published BRYME Sports stories will appear here.</p><a class="quiet-link" href="${url('/sports/articles/')}">Visit the Sports editorial desk</a></div>`}</section>` : '';
  const sportsFeature = (v.dir === 'sports' && category && category.slug === 'football') ? `<section class="sp-hero" aria-label="Featured BRYME Sports stories"><div class="sp-hero-track"><a class="sp-hero-card sp-hero-first" href="${url('/sports/premier-league-matchweek-1-guide/')}" style="--card-img:url('/assets/img/sports/hero-premier-league.jpg')"><span class="sp-hero-tag">Matchweek 1</span><h3>The opening round, confirmed</h3><p>Every Friday-to-Monday fixture, kick-off time and TV listing. No predictions.</p><span class="sp-hero-go">Read the briefing →</span></a><a class="sp-hero-card" href="${url('/sports/arsenal-title-defence/')}" style="--card-img:url('/assets/img/sports/hero-arsenal.jpg')"><span class="sp-hero-tag">Arsenal</span><h3>The title defence starts Friday</h3><p>Champions host Coventry. The Community Shield is already won. The league is not.</p><span class="sp-hero-go">Read the facts →</span></a><a class="sp-hero-card" href="${url('/sports/manchester-city-without-guardiola/')}" style="--card-img:url('/assets/img/sports/hero-man-city-manager.jpg')"><span class="sp-hero-tag">Manchester City</span><h3>After Guardiola: what is confirmed</h3><p>Maresca's appointment, the Community Shield, and Sunday against Bournemouth.</p><span class="sp-hero-go">Read what City announced →</span></a></div></section>` : '';
  /* ---- Clubs directory: the Clubs hub IS the reference page ----
     Built from content/club-history/*.json, where every club record already carries an
     official source. Capacities come from the fixture venue data where it exists.
     Honours totals are deliberately absent - the existing source policy withholds them
     until each club is reconciled against official honours lists, and inventing them
     here to fill a column would be exactly the wrong trade. */
  const clubsDirectory = (() => {
    if (!(v.dir === 'sports' && category && category.slug === 'clubs')) return '';
    const dir = path.join(root, 'content', 'club-history');
    if (!fs.existsSync(dir)) return '';
    const order = ['premier-league','la-liga','serie-a','bundesliga','ligue-1','eredivisie'];
    const capsFor = (lgSlug) => {
      const fname = lgSlug === 'premier-league' ? 'fixtures.json' : `fixtures-${lgSlug}.json`;
      const fp = path.join(root, 'content', fname);
      if (!fs.existsSync(fp)) return {};
      try { return (JSON.parse(fs.readFileSync(fp, 'utf8')).venues) || {}; } catch (e) { return {}; }
    };
    let total = 0, checked = null;
    const tables = order.map(lgSlug => {
      const fp = path.join(dir, lgSlug + '.json');
      if (!fs.existsSync(fp)) return '';
      let D; try { D = JSON.parse(fs.readFileSync(fp, 'utf8')); } catch (e) { return ''; }
      const clubs = (D.clubs || []).slice().sort((a, b) => String(a.name).localeCompare(String(b.name)));
      if (!clubs.length) return '';
      total += clubs.length;
      checked = checked || D.lastChecked;
      const caps = capsFor(lgSlug);
      const anyCap = clubs.some(c => caps[c.slug] && caps[c.slug].capacity);
      return `<h3 class="sp-dir" id="${esc(lgSlug)}">${esc(D.league || lgSlug)} <span class="cd-count">${clubs.length} clubs</span></h3>
      <div class="sp-table-wrap"><table class="sp-table cd-table"><thead><tr><th>Club</th><th>Founded</th><th>City</th><th>Stadium</th>${anyCap ? '<th>Capacity</th>' : ''}<th>Source</th></tr></thead><tbody>
      ${clubs.map(c => {
        const cap = caps[c.slug] && caps[c.slug].capacity;
        return `<tr><td><b>${esc(c.name)}</b></td><td>${esc(c.founded || '—')}</td><td>${esc(c.city || '—')}</td><td>${esc(c.stadium || '—')}</td>${anyCap ? `<td>${cap ? esc(Number(cap).toLocaleString('en-GB')) : '<span class="cd-na">not recorded</span>'}</td>` : ''}<td>${c.source ? `<a href="${esc(c.source)}" rel="nofollow noopener">official</a>` : '<span class="cd-na">—</span>'}</td></tr>`;
      }).join('')}
      </tbody></table></div>`;
    }).filter(Boolean).join('');
    const jump = order.filter(o => fs.existsSync(path.join(dir, o + '.json')))
      .map(o => `<a class="cd-jump" href="#${o}">${esc(o.replace(/-/g, ' '))}</a>`).join('');
    return `<section class="section">
      <div class="vnote">Founding year, home city and stadium for <b>${total} clubs</b> across six European leagues. Every row is backed by an official club source, linked in the last column. Last reconciled ${esc(checked || 'recently')}.</div>
      <div class="cd-jumps">${jump}</div>
      ${tables}
      <div class="sp-truth"><b>Why there is no honours column.</b><p>BRYME does not publish major-honours totals until each club has been reconciled against official club and competition honours lists. Trophy counts differ between sources depending on whether defunct competitions, shared titles and regional championships are included, and a table that quietly picks one interpretation is worse than no table. The column will appear when the reconciliation is done, not before.</p></div>
    </section>`;
  })();
  const footballHub = `<section class="section"><div class="vnote">Football is BRYME’s first fully built sports hub. Pick a competition or follow fixtures, FPL, transfers and the game’s biggest stories.</div><h2 style="margin:26px 0 14px">Football competitions</h2><div class="vcat-grid">${[['premier-league','Premier League','England’s top flight: fixtures, clubs, transfers and FPL.'],['champions-league','Champions League','Europe’s biggest club competition.'],['la-liga','La Liga','Spanish football: Real Madrid, Barcelona and beyond.'],['serie-a','Serie A','Italian football and its storied clubs.'],['bundesliga','Bundesliga','German football and its fan culture.'],['ligue-1','Ligue 1','French football, fixtures and clubs.'],['international','International football','National teams, tournaments and qualifiers.']].map(x => photoTile('/sports/' + x[0] + '/', x[1], x[2], catImg('sports/' + x[0]))).join('')}</div><h2 style="margin:30px 0 14px">Follow the game</h2><div class="vcat-grid">${[['fpl','Fantasy Premier League','Picks, captains and fixture-led decisions.'],['transfers','Transfers','Verified transfer coverage and market context.'],['players','Players','Profiles, careers and stories.'],['clubs','Clubs','Histories, identities and fan culture.'],['history','History','Historic moments and great eras.'],['records','Records','Goals, titles, appearances and numbers.']].map(x => photoTile('/sports/' + x[0] + '/', x[1], x[2], catImg('sports/' + x[0]))).join('')}</div></section>`;
  const sportsTeaserBlock = (v.dir === 'sports' && !category && VIDEO_EDITORIAL.sports && VIDEO_EDITORIAL.sports.videoId) ? (function(){
    const sv = VIDEO_EDITORIAL.sports;
    const cap = sv.figcaption ? `<figcaption>${esc(sv.figcaption)}</figcaption>` : '';
    const ctx = Array.isArray(sv.context) && sv.context.length ? `<div class="video-context">${sv.context.map(p => `<p>${esc(p)}</p>`).join('')}</div>` : '';
    return `<section class="section sports-teaser"><div class="section-head"><h2>Premier League 2026/27</h2></div><figure class="video-figure"><div class="trailer-frame" style="max-width:100%"><iframe src="https://www.youtube-nocookie.com/embed/${esc(sv.videoId)}" title="${esc(sv.name || 'Premier League 2026/27')}" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen loading="lazy" referrerpolicy="strict-origin-when-cross-origin"><\/iframe></div>${cap}</figure>${ctx}</section>`;
  }()) : '';
  const fixturesBlock = (v.dir === 'sports' && !category) ? '<section class="section"><div class="section-head"><h2>Fixtures &amp; Results 2026/27</h2></div><div class="vcat-grid">' + LEAGUE_FIX.map(lg => { const sum = leagueFixturesSummary(lg.slug); const tr = transferStats(lg.slug); const bits = ['All ' + sum.total + ' fixtures — dates, kickoffs & match pages']; if (tr.in + tr.out > 0) bits.push(tr.in + ' in / ' + tr.out + ' out tracked'); return '<a class="vcat" href="' + url('/sports/' + lg.slug + '/fixtures/') + '"><b>' + esc(lg.name) + '</b><span>' + esc(bits.join(' · ')) + '</span></a>'; }).join('') + '<a class="vcat" href="' + url('/sports/managers-2026-27/') + '"><b>Managers</b><span>Managers In &amp; Out — 2026/27</span></a></div></section>' : '';
  const defaultHeroImg = category ? (catImg(v.dir + '/' + category.slug) || catImg('hub/' + v.dir)) : catImg('hub/' + v.dir);
  const defaultHero = `<section class="hero vhero vhero-${v.dir}${defaultHeroImg ? ' vhero-photo' : ''}" data-vertical="${v.dir}"${defaultHeroImg ? ` style="--hero-img:url('${defaultHeroImg}')"` : ''}><div class="eyebrow">${v.emoji} ${category ? esc(v.name) + ' · ' + esc(category.name) : esc(v.name)}</div><h1>${esc(category ? category.name : v.name)}</h1><p class="lead">${esc(category ? category.desc : v.tagline)}</p></section>`;
  const sportsRootHero = (v.dir === 'sports' && !category) ? `<section class="sp-land" style="--sp-hero:url('/assets/img/sports/hero-landing.jpg')" aria-label="BRYME Sports"><div class="sp-land-bg" aria-hidden="true"></div><div class="sp-land-inner"><p class="sp-land-kicker"><i></i> BRYME Sports</p><h1>The season is on.</h1><p class="sp-land-lead">${esc(v.tagline)}</p><div class="sp-land-actions"><a class="cta" href="${url('/sports/premier-league/matches/')}">Match Centre</a><a class="cta-ghost" href="${url('/sports/premier-league/results/')}">Premier League results</a></div><nav class="sp-land-leagues" aria-label="Leagues"><a href="${url('/sports/premier-league/')}">Premier League</a><a href="${url('/sports/la-liga/')}">La Liga</a><a href="${url('/sports/serie-a/')}">Serie A</a><a href="${url('/sports/bundesliga/')}">Bundesliga</a><a href="${url('/sports/ligue-1/')}">Ligue 1</a><a href="${url('/sports/champions-league/')}">Champions League</a></nav></div></section>
    <section class="sp-hero" aria-label="Featured BRYME Sports stories"><div class="sp-hero-track">
      <a class="sp-hero-card sp-hero-first" href="${url('/sports/ballon-dor-race/')}" style="--card-img:url('/assets/img/sports/hero-ballon-dor.jpg')"><span class="sp-hero-tag">Ballon d'Or</span><h3>London, 26 October. The winner is not decided.</h3><p>The 70th ceremony is confirmed. Last year's winners are confirmed. This year's names are not.</p><span class="sp-hero-go">Read what UEFA announced →</span></a>
      <a class="sp-hero-card" href="${url('/sports/world-cup-2026-spain-champions/')}" style="--card-img:url('/assets/img/sports/hero-world-cup.jpg')"><span class="sp-hero-tag">World Cup 2026</span><h3>Spain are world champions</h3><p>Ferran Torres in the 106th minute at MetLife. The result, the format, and what it did to your league season.</p><span class="sp-hero-go">Read the final →</span></a>
      <a class="sp-hero-card" href="${url('/sports/premier-league-matchweek-1-guide/')}" style="--card-img:url('/assets/img/sports/hero-premier-league.jpg')"><span class="sp-hero-tag">Premier League</span><h3>The opening round, confirmed</h3><p>Every Friday-to-Monday fixture, kick-off time and TV listing. No predictions.</p><span class="sp-hero-go">Read the briefing →</span></a>
    </div></section>` : '';
  const techRootHero = (v.dir === 'tech' && !category) ? `<section class="sp-land tech-land" style="--sp-hero:url('/assets/img/tech/hero-landing.jpg')" aria-label="BRYME Tech &amp; AI"><div class="sp-land-bg" aria-hidden="true"></div><div class="sp-land-inner"><p class="sp-land-kicker"><i></i> BRYME Tech &amp; AI</p><h1>Practical tools. No theatre.</h1><p class="sp-land-lead">${esc(v.tagline)}</p><div class="sp-land-actions"><a class="cta" href="${url('/tech/where-to-host-website-for-free/')}">Where to host for free</a><a class="cta-ghost" href="${url('/tech/ai-assistant-data-training-settings/')}">AI privacy settings</a></div></div></section>
    <section class="sp-hero" aria-label="Featured BRYME Tech stories"><div class="sp-hero-track">
      <a class="sp-hero-card sp-hero-first tech-tint" href="${url('/tech/where-to-host-website-for-free/')}" style="--card-img:url('/assets/img/tech/hero-hosting.jpg')"><span class="sp-hero-tag">Hosting</span><h3>Where to host a website for free</h3><p>GitHub Pages, Cloudflare, Render, Vercel, Netlify. What their own docs actually say.</p><span class="sp-hero-go">Read what free means →</span></a>
      <a class="sp-hero-card tech-tint" href="${url('/tech/ai-assistant-data-training-settings/')}" style="--card-img:url('/assets/img/tech/hero-privacy.jpg')"><span class="sp-hero-tag">AI assistants</span><h3>What they actually do with your chats</h3><p>ChatGPT, Claude and Gemini each have a training toggle. Each one also has a way around it.</p><span class="sp-hero-go">Read the settings →</span></a>
      <a class="sp-hero-card tech-tint" href="${url('/tech/render-deployment-failures-what-they-taught-me/')}" style="--card-img:url('/assets/img/tech/hero-deploy.jpg')"><span class="sp-hero-tag">Deploy</span><h3>The site worked. The deploy didn't.</h3><p>Four real Render failures, including the package.json error on this site.</p><span class="sp-hero-go">Read the failures →</span></a>
    </div></section>` : '';
  const pageHero = sportsRootHero || techRootHero || (defaultHero + sportsFeature);
  const catArticles = category ? ((verticalArticleIndex[v.dir] && verticalArticleIndex[v.dir].get(category.slug)) || []) : [];
  const writingDeskBlock = (v.dir === 'make-money' && category && category.slug === 'writing')
    ? `<div class="wo-banner"><b>The live log is next door.</b><p>These are the articles about the series. Dated field notes — who I emailed, who replied, how they pay — live on <a href="${url('/make-money/writing/')}">Writing Field Notes</a>.</p></div>`
    : '';
  const catArticleBlock = catArticles.length
    ? `<div class="vcat-grid">${catArticles.map(a => articleCard(v.dir, a)).join('')}</div>`
    : '';
  const body = `<main class="shell"><div class="crumb"><a href="${url('/')}">Home</a> / ${category ? `<a href="${url('/' + v.dir + '/')}">${esc(v.name)}</a> / ${esc(category.name)}` : esc(v.name)}</div>${pageHero}<section class="section">${category ? (v.dir === 'sports' && category.slug === 'football' ? (footballHub + catArticleBlock) : (clubsDirectory ? (clubsDirectory + catArticleBlock) : (catArticles.length ? writingDeskBlock + catArticleBlock : (writingDeskBlock || `<div class="vstate"><b>${esc(category.name)} — foundation ready</b><p>This section is being built. Articles will appear here as they are researched and published.</p></div>`)))) : `${v.dir === 'make-money' ? moneyDeskHtml() : ''}<p class="lead" style="margin-bottom:18px">${esc(v.desc)}</p><div class="vnote">${esc(v.note)}</div><h2 style="margin:26px 0 14px">${v.dir === 'make-money' ? 'Guides already published' : 'Explore ' + esc(v.short)}</h2><div class="vcat-grid">${catGrid}</div>`}</section>${(v.dir === 'sports' && !category) ? livePreviewBlock(10) : ''}${sportsTeaserBlock}${fixturesBlock}${sportsStoriesBlock}${coreHubStrip(v.dir)}</main>`;
  const emptyHub = !!category && !catArticles.length && !clubsDirectory && !(v.dir === 'sports' && category.slug === 'football');
  if (emptyHub) EMPTY_HUB_PATHS.add(catPath);
  write(v.dir + (category ? '/' + category.slug : ''), layout({
    title: category ? `${category.name}` : v.name,
    description: category ? category.desc : (v.tagline || v.desc),
    noindex: emptyHub,
    path: catPath,
    activeNav: v.active,
    schema: (function(){
      const hubSchema = [{ '@context':'https://schema.org', '@type':'CollectionPage', name: category ? category.name : v.name, description: (category ? category.desc : v.desc), url: absUrl(catPath) }, breadcrumbs(crumbs)];
      if (v.dir === 'sports' && !category && VIDEO_EDITORIAL.sports && VIDEO_EDITORIAL.sports.videoId) {
        const sv = VIDEO_EDITORIAL.sports;
        const vo = { '@context':'https://schema.org', '@type':'VideoObject', name: sv.name, description: sv.description, thumbnailUrl: sv.thumbnailUrl, embedUrl: sv.embedUrl };
        if (sv.uploadDate) vo.uploadDate = sv.uploadDate;
        if (sv.channel) vo.publisher = { '@type':'Organization', name: sv.channel };
        hubSchema.push(vo);
      }
      return hubSchema;
    })(),
    body: body
  }));
}
/* ================================================================
   WEEKLY EDITORIAL WORKFLOW FOR MATCH PAGES
   ----------------------------------------------------------------
   The fixture database stays complete: every scheduled match keeps a
   page at its permanent URL. What changes is whether that page is an
   INDEXABLE EDITORIAL PAGE or a schedule entry.

   A fixture is written up roughly 3-5 days before kickoff. Adding an
   entry to content/match-editorial.json is what promotes it: the page
   gains the full preview, becomes indexable, and enters the sitemap
   with a lastmod. Without an entry it stays noindex and out of the
   sitemap, so thousands of unplayed fixtures are never submitted.

   After the match the SAME URL is updated - never a second URL. The
   result and post-match analysis go on top, and the pre-match preview
   is preserved below under its own heading so readers can see what
   BRYME expected and what actually happened.

   Nothing here invents team news. A field that is absent renders as an
   explicit "not confirmed" state.
   ================================================================ */
const EDITORIAL_WINDOW_DAYS = 5;   /* start writing this many days out */
const EDITORIAL_WINDOW_MIN  = 3;   /* page should be live by this many days out */
const BUILD_DAY = (process.env.BRYME_TODAY || new Date().toISOString().slice(0, 10));
const EDITORIAL = (() => {
  const f = path.join(root, 'content', 'match-editorial.json');
  if (!fs.existsSync(f)) return {};
  try { return JSON.parse(fs.readFileSync(f, 'utf8')); } catch (e) { return {}; }
})();
const PAGE_LASTMOD = new Map();     /* path -> YYYY-MM-DD for sitemap <lastmod> */
const EDITORIAL_FIELDS = ['overview','recentForm','headToHead','lastFiveMeetings','homeAwayForm',
  'keyPlayers','injuries','suspensions','expectedLineups','tacticalMatchup','historicalContext',
  'underdog','outlook','scorePrediction'];
function daysUntil(dateStr){
  if (!dateStr) return null;
  const a = Date.parse(dateStr + 'T00:00:00Z'), b = Date.parse(BUILD_DAY + 'T00:00:00Z');
  if (isNaN(a) || isNaN(b)) return null;
  return Math.round((a - b) / 86400000);
}
/* Sitemap <lastmod> and schema.org dates must be ISO 8601. Anything that is not a clean
   YYYY-MM-DD is dropped rather than emitted in a format crawlers will reject. */
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
const BAD_DATES = [];
function isoDate(v, where){
  if (!v) return null;
  const t = String(v).trim();
  if (ISO_DATE.test(t)) return t;
  BAD_DATES.push(`${where}: "${t}" is not YYYY-MM-DD`);
  return null;
}
function editorialFor(leagueSlug, matchSlug){
  const e = ((EDITORIAL[leagueSlug] || {})[matchSlug]);
  if (!e) return null;
  /* "meaningful content" gate: a stub with only dates must not go into the sitemap */
  const filled = EDITORIAL_FIELDS.filter(k => {
    const v = e[k];
    return Array.isArray(v) ? v.length > 0 : (typeof v === 'string' && v.trim().length > 12);
  });
  /* A post-match write-up counts as meaningful content in its own right. The gate exists
     to keep thin PREVIEWS out of the sitemap, but a page carrying a sourced result and a
     real analysis of it is not thin just because no preview preceded it - which is the case
     for any match played before BRYME started covering that league. Without this, the
     post-match block silently never rendered on those pages. */
  const pmFilled = e.postMatch
    ? Object.keys(e.postMatch).filter(k => k !== 'publishedAt' &&
        typeof e.postMatch[k] === 'string' && e.postMatch[k].trim().length > 12).length
    : 0;
  if (filled.length < 3 && pmFilled < 2) return null;
  return e;
}
const UNKNOWN = txt => `<span class="sp-unknown">${esc(txt)}</span>`;
function edRow(label, value, unknownNote){
  const has = Array.isArray(value) ? value.length : (typeof value === 'string' && value.trim());
  const body = !has ? UNKNOWN(unknownNote || 'Not confirmed at the time of writing.')
    : Array.isArray(value) ? `<ul>${value.map(x => `<li>${esc(x)}</li>`).join('')}</ul>`
    : String(value).split(/\n{2,}/).map(t => `<p>${esc(t.trim())}</p>`).join('');
  return `<div class="sp-msec${has ? '' : ' sp-msec-unknown'}"><b>${esc(label)}</b>${body}</div>`;
}
function previewBlock(e, opts){
  const past = !!(opts && opts.past);
  return `<section class="sp-preview${past ? ' sp-preview-archived' : ''}">
    ${past ? `<div class="sp-archive-note"><b>What BRYME said before kickoff</b><p>This preview was published on ${esc(e.publishedAt || 'an earlier date')} and is preserved unchanged. It is what we expected, not what happened.</p></div>` : ''}
    <div class="sp-msec-grid">
      ${edRow('Match overview', e.overview)}
      ${edRow('Recent form', e.recentForm)}
      ${edRow('Head-to-head record', e.headToHead)}
      ${edRow('Last five meetings', e.lastFiveMeetings)}
      ${edRow('Home & away form', e.homeAwayForm)}
      ${edRow('Key players', e.keyPlayers)}
      ${edRow('Injuries', e.injuries, 'No injury information confirmed by the clubs at the time of writing. BRYME does not publish unverified team news.')}
      ${edRow('Suspensions', e.suspensions, 'No suspensions confirmed at the time of writing.')}
      ${edRow('Expected lineups', e.expectedLineups, 'No lineup has been announced. Expected XIs are not published here as speculation.')}
      ${edRow('Tactical matchup', e.tacticalMatchup)}
      ${edRow('Historical context', e.historicalContext)}
      ${edRow('The case for the underdog', e.underdog)}
      ${edRow('BRYME editorial outlook', e.outlook)}
      ${edRow('BRYME editorial score prediction', e.scorePrediction)}
    </div>
    ${Array.isArray(e.sources) && e.sources.length ? `<p class="sp-source-note">Sources: ${e.sources.map(x => x.url ? `<a href="${esc(x.url)}" rel="nofollow noopener">${esc(x.name || x.url)}</a>` : esc(x.name || '')).join(' · ')}</p>` : ''}
  </section>`;
}
function postMatchBlock(pm){
  return `<section class="sp-postmatch">
    <h3 class="sp-dir">Post-match analysis</h3>
    <div class="sp-msec-grid">
      ${edRow('What actually happened', pm.whatHappened)}
      ${edRow('Tactical developments', pm.tacticalDevelopments)}
      ${edRow('Key performers', pm.keyPerformers)}
      ${edRow('Disappointing performers', pm.disappointing)}
      ${edRow('Against the pre-match prediction', pm.vsPrediction)}
      ${edRow('BRYME post-match analysis', pm.analysis)}
    </div>
  </section>`;
}

/* ================================================================
   LIVE MATCH PREVIEWS — internal linking.
   A page linked only from two deep listing pages is a page a crawler
   reaches late and rarely. These are the fixtures written up and worth
   surfacing, so they get linked from the homepage and the sports hub
   rather than being buried in the Match Centre. The list builds itself
   from the editorial store, so a fixture appears here the moment its
   preview is published and drops off once it is old news.
   ================================================================ */
const LIVE_PREVIEWS = (() => {
  const files = { 'premier-league':'fixtures.json', 'la-liga':'fixtures-la-liga.json',
    'serie-a':'fixtures-serie-a.json', 'bundesliga':'fixtures-bundesliga.json', 'ligue-1':'fixtures-ligue-1.json' };
  const out = [];
  for (const [lg, file] of Object.entries(files)) {
    const fp = path.join(root, 'content', file);
    if (!fs.existsSync(fp)) continue;
    let F; try { F = JSON.parse(fs.readFileSync(fp, 'utf8')); } catch (e) { continue; }
    (F.matchweeks || []).forEach(w => (w.matches || []).forEach(m => {
      const slug = m.id + '-vs-' + m.away;
      if (!editorialFor(lg, slug)) return;
      const d = daysUntil(m.date);
      if (d === null || d < -2) return;                 // drop once it is old news
      out.push({ lg, slug, league: F.league || lg, round: w.number, date: m.date,
        dayLabel: m.dayLabel, time: m.time, home: m.homeName, away: m.awayName, d,
        url: '/sports/' + lg + '/matches/' + slug + '/' });
    }));
  }
  return out.sort((a, b) => String(a.date).localeCompare(String(b.date)));
})();
function livePreviewBlock(limit){
  const items = LIVE_PREVIEWS.slice(0, limit || 10);
  if (!items.length) return '';
  return `<section class="home-section sec-previews"><div class="shell">
    <div class="section-head"><div><div class="eyebrow">Matchday ahead</div><h2>\u26bd Match previews</h2><p class="section-note">Form, head-to-head and BRYME's editorial prediction \u2014 published before kickoff, updated with the result afterwards.</p></div><a href="${url('/sports/premier-league/matches/')}">Match Centre</a></div>
    <div class="vcat-grid">${items.map(m => `<a class="vcat mp-card" href="${url(m.url)}">
      <span class="mp-when">${esc(m.dayLabel || m.date)}${m.time ? ' \u00b7 ' + esc(m.time) : ''}</span>
      <b>${esc(m.home)} v ${esc(m.away)}</b>
      <span>${esc(m.league)} \u00b7 Matchweek ${esc(String(m.round))} \u2014 preview, form and prediction</span></a>`).join('')}</div>
  </div></section>`;
}

/* ---------------- Homepage ---------------- */
const trendNow = trendingList.slice(0, 24); // the complete curated trending list
const popularMovies = popularByType.movie.slice(0, 12);
const popularSeries = popularByType.series.slice(0, 12);
const popularAnime = popularByType.anime.slice(0, 12);
const editorPicksNow = editorPicksList.slice(0, 8);
const freshNow = (newReleases.length >= 8 ? newReleases : movies.filter(m => m.year).sort(sortNewest)).slice(0, 12);
const browseMovies = movies.filter(m => m.typeDir === 'movie').sort(sortPopular).slice(0, 12);
const browseSeries = movies.filter(m => m.typeDir === 'series').sort(sortPopular).slice(0, 12);
const browseAnime = movies.filter(m => m.typeDir === 'anime').sort(sortPopular).slice(0, 12);
const latestArticles = articles.slice(-3).reverse();

function genreChips(list, baseDir, max){
  const map = new Map();
  list.forEach(m => {
    const names = m.typeDir === 'movie' ? [m.genre] : m.genres;
    names.forEach(n => { if (!n) return; const s = slugify(n); if (!map.has(s)) map.set(s, {name:n, count:0}); map.get(s).count++; });
  });
  const arr = [...map.values()].sort((a,b) => b.count - a.count).slice(0, max || 10);
  return arr.map(g => `<a href="${url('/' + baseDir + '/' + slugify(g.name) + '/')}">${esc(g.name)}<b>${g.count}</b></a>`).join('');
}
function heroSlideMarkup(m, idx){
  const kicker = `<span class="type-badge tb-${m.typeDir}">${m.typeLabel.toUpperCase()}</span>${m.year ? `<span>${m.year}</span>` : ''}${m.genreLabel ? `<span class="dot">·</span><span>${esc(m.genreLabel)}</span>` : ''}`;
  const rating = m.rating != null ? `<p class="hero-slide-rating">★ ${m.rating}/10 · BRYME Editorial</p>` : '';
  const desc = esc((m.tagline || m.description || '').slice(0, 200));
  /* SEO: a carousel should expose exactly one h1 (the active slide's title). The
     remaining slides use h2 with identical styling, so the page has a single
     top-level heading instead of one per slide. */
  const titleTag = idx === 0 ? 'h1' : 'h2';
  const posterSrc = m.poster || '';
  const bg = posterSrc ? ` style="background-image:url('${esc(posterSrc)}')"` : '';
  return `<div class="hero-slide${idx === 0 ? ' is-active' : ''}" data-slide data-video="${m.youtubeId}" data-title="${esc(m.title)}" data-url="${m.url}" data-poster="${esc(posterSrc)}"${bg}><div class="hero-slide-shade"></div><div class="shell hero-slide-inner"><div class="hero-slide-kicker">${kicker}</div><${titleTag}>${esc(m.title)}</${titleTag}>${rating}<p>${desc}</p><div class="hero-actions"><button type="button" class="cta hero-watch" data-hero-watch>▶ Watch Trailer</button><a class="cta cta-ghost" href="${m.url}">View Details</a></div></div></div>`;
}
const heroEmbed = JSON.stringify(heroSlides.map(m => ({ t: m.title, ty: m.typeLabel, td: m.typeDir, y: m.year, g: m.genreLabel, r: m.rating, v: m.youtubeId, p: m.poster, d: (m.tagline || m.description || '').slice(0, 200), u: m.url }))).replace(/</g, '\u003c');
write('', layout({
  title: 'Movies, TV Series & Anime',
  description: 'Discover what to watch on BRYME: 630+ movies, TV series and anime with verified trailers, editorial guides, plus sports, money and tech & AI coverage.',
  path: '/', image: poster(heroSlide), lcpImage: poster(heroSlide), activeNav: 'home',
  schema: [{ '@context':'https://schema.org', '@type':'WebSite', name:site.name, url:absUrl('/'), description:site.description, publisher:{ '@type':'Organization', name:site.name, url:absUrl('/'), logo:absUrl('/assets/icons/icon-512.png') } }, { '@context':'https://schema.org', '@type':'CollectionPage', name:'Movies, TV Series & Anime', description:'Discover what to watch on BRYME: 630+ movies, TV series and anime with verified trailers, editorial guides, plus sports, money and tech & AI coverage.', url:absUrl('/') }],
  body: `<main>
  <section class="hero-carousel" data-hero role="region" aria-roledescription="carousel" aria-label="Featured titles" data-interval="8000">
    <div class="hero-slides">${heroSlides.map(heroSlideMarkup).join('')}</div>
    <button type="button" class="hero-ctrl hero-prev" data-hero-prev aria-label="Previous featured title">&#8249;</button>
    <button type="button" class="hero-ctrl hero-next" data-hero-next aria-label="Next featured title">&#8250;</button>
    <div class="hero-dots" data-hero-dots role="tablist" aria-label="Featured title slides">${heroSlides.map((m, i) => `<button type="button" class="hero-dot${i === 0 ? ' is-active' : ''}" data-hero-dot="${i}" role="tab" aria-label="${esc(m.title)}" aria-selected="${i === 0}"></button>`).join('')}</div>
    <button type="button" class="hero-vctrl hero-mute" data-hero-mute aria-label="Unmute trailer" hidden>&#128263;</button>
    <button type="button" class="hero-vctrl hero-pause" data-hero-pause aria-label="Pause rotation" hidden>&#9208;</button>
    <div class="hero-video" data-hero-video hidden></div>
  </section>
    <div class="home-main">
  <section class="home-section brand-strip"><div class="shell"><p class="brand-slogan">Discover what you love. Learn what you need. Find what's next.</p>${coreHubStrip('home', { title: 'Explore BRYME', lead: 'Start with a section, then follow the titles and guides inside it.', photos: ['entertainment','sports','make-money','tech'] }).replace('<section class="section core-hubs" data-core-hubs>', '<section class="core-hubs" data-core-hubs>')}</div></section>
  <section class="home-section rec-section" id="recommend">
    <div class="shell rec-inner">
      <div class="rec-copy"><div class="eyebrow">Personalised discovery</div><h2>DON'T KNOW WHAT TO WATCH?</h2><p class="rec-sub">Tell us one movie or series you loved. We'll find your next watch.</p></div>
      <form class="rec-form" data-rec-form><label class="visually-hidden" for="rec-input">Enter a movie or series you loved</label><input id="rec-input" data-rec-input type="text" autocomplete="off" placeholder="Enter a movie or series you loved..." aria-label="Enter a movie or series you loved"><button type="submit" class="cta rec-cta">&#10024; RECOMMEND FOR ME</button></form>
      <div class="rec-status" data-rec-status aria-live="polite"></div>
      <div class="rec-results" data-rec-results aria-live="polite"></div>
    </div>
  </section>
  ${railSection("What's Trending", '🔥', trendNow.slice(0, 10), '/trending/', 'Curated by the BRYME editorial team — not live traffic data. Ranked per content type.', {ranked:true, rankKey:'trendingRank'})}
  ${railSection('Popular Movies', '⭐', popularMovies.slice(0, 8), '/movies/', 'Evergreen movie favourites, editorially ranked.', {variant:'lead', eyebrow:'Film'})}
  ${railSection('Popular Series', '⭐', popularSeries.slice(0, 8), '/series/', 'Evergreen TV series favourites, editorially ranked.', {variant:'lead', eyebrow:'Television'})}
  ${railSection('Popular Anime', '⭐', popularAnime.slice(0, 8), '/anime/', 'Evergreen anime favourites, editorially ranked.', {variant:'wall', eyebrow:'Animation'})}
  ${railSection('Editor\'s Picks', '👑', editorPicksNow.slice(0, 6), '/trending/#editors-picks', 'Hand-picked by the BRYME editorial desk — separate from trending and popularity.', {variant:'spread', eyebrow:'From the desk'})}
  ${railSection('New Releases', '🆕', freshNow.slice(0, 8), '/trending/#new-releases', 'Newest verified release years — old classics are never re-labelled as new.', {eyebrow:'Just added'})}
  ${railSection('Movies', '🎬', browseMovies.slice(0, 8), '/movies/', 'Keep exploring the movie catalogue.', {variant:'wall', eyebrow:'Browse'})}
  ${railSection('Series', '📺', browseSeries.slice(0, 8), '/series/', 'Keep exploring the series catalogue.', {variant:'chart', eyebrow:'Browse'})}
  ${railSection('Anime', '🍥', browseAnime.slice(0, 8), '/anime/', 'Keep exploring the anime catalogue.', {variant:'chart', eyebrow:'Browse'})}
  ${livePreviewBlock(24)}
  <section class="home-section"><div class="shell"><div class="section-head"><h2>🎭 Browse by genre</h2><a href="${url('/genres/')}">All genres</a></div><div class="genre-trio"><div class="genre-panel"><h3>🎬 Movie genres <span class="gp-count">${movies.filter(m=>m.typeDir==='movie').length} films</span></h3><div class="genre-chips">${genreChips(movies.filter(m=>m.typeDir==='movie'), 'movies', 9)}</div></div><div class="genre-panel"><h3>📺 Series genres <span class="gp-count">${movies.filter(m=>m.typeDir==='series').length} shows</span></h3><div class="genre-chips">${genreChips(movies.filter(m=>m.typeDir==='series'), 'series', 9)}</div></div><div class="genre-panel"><h3>🍥 Anime genres <span class="gp-count">${movies.filter(m=>m.typeDir==='anime').length} titles</span></h3><div class="genre-chips">${genreChips(movies.filter(m=>m.typeDir==='anime'), 'anime', 9)}</div></div></div></div></section>
  <section class="home-section"><div class="shell"><div class="section-head"><div><div class="eyebrow">From the editorial desk</div><h2>📰 Latest articles</h2></div><a href="${url('/articles/')}">All stories</a></div><div class="story-grid">${latestArticles.map(a => storyPhoto('/article/' + a.slug + '/', a.category, a.title, a.description || '', heroFor(a.slug, 'entertainment'))).join('')}</div></div></section>
  ${legalServicesStrip({ title: 'Watch on a licensed service', lead: 'BRYME is a discovery site. Trailers are official YouTube embeds. To watch a film or series, open a licensed service — we do not host the title.' })}
  <section class="discover-cta"><div><div class="eyebrow">Full catalogue</div><h2>Pick a lane: Movies, Series or Anime.</h2><p>Each section is strictly filtered to its own content type. No mixed-up walls of posters.</p></div><a class="cta" href="${url('/search/')}">Search everything</a></div></section></div></main><script id="hero-data" type="application/json">${heroEmbed}</script>`
}));


/* ---------------- League fixtures (all five leagues) ---------------- */
const LEAGUE_FIXTURE_FILES = {
  'premier-league': 'fixtures.json',
  'la-liga': 'fixtures-la-liga.json',
  'serie-a': 'fixtures-serie-a.json',
  'bundesliga': 'fixtures-bundesliga.json',
  'ligue-1': 'fixtures-ligue-1.json'
};
const LEAGUE_FIX = [
  { slug:'premier-league', name:'Premier League', roundLabel:'Matchweek', tz:'Europe/London', timeSuffix:'UK',
    stdSlot:'<b>(std)</b> marks the Premier League\'s standard slot — 15:00 on weekend/Bank Holiday dates and 20:00 midweek — where no specific time was published. ',
    crest:id=>url('/assets/img/sports/pl/'+id+'.svg'), alt:(id,name)=> name + ' official club crest' },
  { slug:'la-liga', name:'La Liga', roundLabel:'Jornada', tz:'Europe/Madrid', timeSuffix:null,
    crest:id=>url('/assets/img/sports/ll/'+(LL_NAME[id]||id)+'.png'), alt:(id,name)=> name + ' official club crest' },
  { slug:'serie-a', name:'Serie A', roundLabel:'Giornata', tz:'Europe/Rome', timeSuffix:null,
    crest:id=>url('/assets/img/sports/sa/'+id+(id==='lazio'?'.png':'.svg')), alt:(id,name)=> name + ' official club crest' },
  { slug:'bundesliga', name:'Bundesliga', roundLabel:'Spieltag', tz:'Europe/Berlin', timeSuffix:null,
    crest:id=> id==='hamburg' ? url('/assets/img/sports/club-hamburg.svg') : url('/assets/img/sports/bl/'+id+'.svg'),
    alt:(id,name)=> id==='hamburg' ? 'Abstract crest for '+name+' — BRYME-generated illustration' : name + ' official club crest' },
  { slug:'ligue-1', name:'Ligue 1', roundLabel:'Journée', tz:'Europe/Paris', timeSuffix:null,
    crest:id=>url('/assets/img/sports/l1/'+id+'.webp'), alt:(id,name)=> name + ' official club crest' }
];
const LEAGUE_FIXTURES_DATA = {};
const LEAGUE_MATCH_PATHS = [];
const UNPLAYED_MATCH_PATHS = new Set();
function loadLeagueFixtures(slug){
  if (LEAGUE_FIXTURES_DATA[slug]) return LEAGUE_FIXTURES_DATA[slug];
  const file = LEAGUE_FIXTURE_FILES[slug];
  try { LEAGUE_FIXTURES_DATA[slug] = JSON.parse(fs.readFileSync(path.join(root, 'content', file), 'utf8')); }
  catch (e) { warnings.push(file + ' unreadable'); LEAGUE_FIXTURES_DATA[slug] = { matchweeks: [], venues: {} }; }
  return LEAGUE_FIXTURES_DATA[slug];
}
/* ---- REAL per-league stats for the hub cards ----
   Pulls only verified data already in the repo: the official fixture list, the
   sourced results file, the editorial match analysis, and the transfer trackers.
   Every number shown is computed, never invented. Used to replace the generic
   "Completed results" / "transfer tracker" one-liners with real counts. */
const TRANSFER_FILES = { 'premier-league':'pl-transfers.json', 'la-liga':'league-transfers.json', 'serie-a':'league-transfers.json', 'bundesliga':'league-transfers.json', 'ligue-1':'league-transfers.json' };
function transferStats(slug){
  const out = { in:0, out:0, confirmed:0, managerNew:0 };
  const file = TRANSFER_FILES[slug];
  if (!file) return out;
  try {
    const d = JSON.parse(fs.readFileSync(path.join(root, 'content', file), 'utf8'));
    let clubs = (file === 'pl-transfers.json') ? (d.clubs || []) : (((d.leagues || []).find(l => l.id === slug) || {}).clubs || []);
    clubs.forEach(c => {
      (c.playersIn || []).forEach(x => { out.in++; if (/confirmed/i.test(x.type || '')) out.confirmed++; });
      (c.playersOut || []).forEach(x => { out.out++; if (/confirmed/i.test(x.type || '')) out.confirmed++; });
      if (c.managerNote && /new/i.test(c.managerNote)) out.managerNew++;
    });
  } catch (e) {}
  return out;
}
function leagueFixturesSummary(slug){
  const F = loadLeagueFixtures(slug);
  const total = (F.matchweeks || []).reduce((n, w) => n + w.matches.length, 0);
  const rounds = (F.matchweeks || []).length;
  return { total, rounds };
}
function resultCountFor(slug){
  const r = (RESULTS[slug] || {});
  const n = Object.keys(r).filter(k => !k.startsWith('_')).length;
  if (n > 0) return n + (n === 1 ? ' verified result' : ' verified results');
  const F = loadLeagueFixtures(slug);
  const first = (F.matchweeks || [])[0] && (F.matchweeks[0].matches || [])[0];
  return first ? 'Season starts ' + esc(first.dayLabel || 'soon') + ' — no results yet' : 'No matches played yet';
}
function transferBlurb(slug, leagueName){
  const tr = transferStats(slug);
  const parts = [];
  if (tr.in > 0) parts.push(tr.in + ' in / ' + tr.out + ' out tracked');
  if (tr.confirmed > 0) parts.push(tr.confirmed + ' confirmed');
  return parts.length ? esc(parts.join(' · ')) : esc(leagueName + ' transfer tracker');
}
function managerBlurb(slug, season){
  const tr = transferStats(slug);
  if (tr.managerNew > 0) return tr.managerNew + ' new manager' + (tr.managerNew === 1 ? '' : 's') + ' confirmed — ' + season;
  return 'Managers In &amp; Out — ' + esc(season);
}

for (const v of VERTICALS) {
  verticalPage(v, null);
  (v.categories || []).forEach(c => verticalPage(v, c));
}

function buildWritingOpportunities(){
  const file = path.join(root, 'content', 'writing-opportunities.json');
  let data = { updatedAt: TODAY, writerBase: 'Nigeria', title: 'Writing catalogue', tagline: '', youtubeVideoUrl: null, opportunities: [], countries: MONEY_DESK.countries, paths: MONEY_DESK.paths };
  if (fs.existsSync(file)) {
    try { data = Object.assign(data, JSON.parse(fs.readFileSync(file, 'utf8'))); }
    catch (e) { warnings.push('writing-opportunities.json unreadable'); }
  }
  const PAY = new Set(['paid', 'unpaid', 'mixed', 'unknown']);
  const ISO = /^\d{4}-\d{2}-\d{2}$/;
  const daysBetween = (a, b) => {
    const A = Date.parse(String(a) + 'T00:00:00Z'), B = Date.parse(String(b) + 'T00:00:00Z');
    if (isNaN(A) || isNaN(B)) return null;
    return Math.round((B - A) / 86400000);
  };
  const published = [];
  (Array.isArray(data.opportunities) ? data.opportunities : []).forEach((o, idx) => {
    if (!o || o.status !== 'published') return;
    const label = o.slug || o.name || ('row ' + idx);
    if (!o.name || !o.slug) { warnings.push('writing-opportunities: dropped ' + label + ' — missing name/slug'); return; }
    if (!o.siteUrl && !o.applyUrl) { warnings.push('writing-opportunities: dropped ' + label + ' — no siteUrl or applyUrl'); return; }
    if (!o.lastChecked || !ISO.test(String(o.lastChecked))) { warnings.push('writing-opportunities: dropped ' + label + ' — lastChecked must be YYYY-MM-DD'); return; }
    if (!o.writerCountry) { warnings.push('writing-opportunities: dropped ' + label + ' — writerCountry required'); return; }
    const substance = [o.notes, o.whatTheyWant, o.payNotes, o.guidelines, o.howToSubmit].some(v => {
      if (Array.isArray(v)) return v.join(' ').trim().length > 20;
      return typeof v === 'string' && v.trim().length > 20;
    }) || o.contacted === true;
    if (!substance) { warnings.push('writing-opportunities: dropped ' + label + ' — no notes, brief or contact'); return; }
    const claimedOutcome = o.replied != null || o.gotPaid === true || o.landedGig === true || o.replyDays != null;
    if (claimedOutcome && o.contacted !== true) { warnings.push('writing-opportunities: dropped ' + label + ' — reply/pay claimed without contacted:true'); return; }
    if (o.payStatus && !PAY.has(o.payStatus)) { warnings.push('writing-opportunities: dropped ' + label + ' — payStatus must be paid|unpaid|mixed|unknown'); return; }
    published.push(o);
  });
  published.sort((a, b) => String(b.lastChecked).localeCompare(String(a.lastChecked)) || String(a.name).localeCompare(String(b.name)));

  const niches = [...new Set(published.flatMap(o => Array.isArray(o.niches) ? o.niches : (o.niche ? [o.niche] : [])))].sort();
  const payLabel = s => s === 'paid' ? 'Pays (as stated)' : s === 'unpaid' ? 'Does not pay' : s === 'mixed' ? 'Sometimes pays' : 'Pay unknown';

  const replyFact = o => {
    if (o.contacted !== true) return { key: 'unknown', label: 'Reply unknown — I have not written to them' };
    if (o.replied === true && o.contactedOn && o.repliedOn) {
      const n = daysBetween(o.contactedOn, o.repliedOn);
      return { key: 'replied', label: n != null ? 'Replied in ' + n + ' day' + (n === 1 ? '' : 's') + ' (my application)' : 'Replied (my application)' };
    }
    if (o.replied === true) return { key: 'replied', label: o.repliedOn ? 'Replied ' + o.repliedOn + ' (my application)' : 'Replied (my application)' };
    if (o.replied === false) {
      const n = o.contactedOn ? daysBetween(o.contactedOn, o.lastChecked || TODAY) : null;
      return { key: 'no-reply', label: n != null ? 'No reply after ' + n + ' day' + (n === 1 ? '' : 's') + ' (my application)' : 'No reply (my application)' };
    }
    return { key: 'waiting', label: o.contactedOn ? 'Waiting since ' + o.contactedOn : 'Contacted — waiting' };
  };

  const yn = (v, yes, no, unk) => v === true ? yes : v === false ? no : unk;

  const policyFor = (o, countryName) => {
    if (!countryName) return 'unknown';
    const policy = o.countryPolicy && typeof o.countryPolicy === 'object' ? o.countryPolicy : null;
    if (policy && policy[countryName]) return policy[countryName];
    if (Array.isArray(o.countriesAccepted) && o.countriesAccepted.map(String).some(x => x.toLowerCase() === countryName.toLowerCase())) return 'accepted';
    if (Array.isArray(o.countriesRejected) && o.countriesRejected.map(String).some(x => x.toLowerCase() === countryName.toLowerCase())) return 'rejected';
    return 'unknown';
  };

  const listBlock = (title, value) => {
    if (!value) return '';
    if (Array.isArray(value) && value.length) return `<h3>${esc(title)}</h3><ol>${value.map(x => `<li>${esc(x)}</li>`).join('')}</ol>`;
    if (typeof value === 'string' && value.trim()) return `<h3>${esc(title)}</h3>` + String(value).split(/\n{2,}/).map(t => `<p>${esc(t.trim())}</p>`).join('');
    return '';
  };

  const facts = (o) => {
    const reply = replyFact(o);
    const open = yn(o.submissionsOpen, 'Open when last checked', 'Closed when last checked', 'Unknown');
    const articles = yn(o.acceptsArticles, 'Yes', 'No', 'Unknown');
    return `<dl class="wo-facts">
      <div><dt>Accepts articles</dt><dd>${esc(articles)}</dd></div>
      <div><dt>Submissions</dt><dd>${esc(open)}${o.submissionsCheckedOn || o.lastChecked ? ' · checked ' + esc(o.submissionsCheckedOn || o.lastChecked) : ''}</dd></div>
      <div><dt>Pay</dt><dd>${esc(payLabel(o.payStatus || 'unknown'))}</dd></div>
      <div><dt>Reply</dt><dd class="wo-${reply.key}">${esc(reply.label)}</dd></div>
      <div data-wo-country-cell><dt>Your country</dt><dd data-wo-country-verdict>Unknown until you pick a country</dd></div>
    </dl>`;
  };

  const card = o => {
    const reply = replyFact(o);
    const tags = (Array.isArray(o.niches) ? o.niches : (o.niche ? [o.niche] : [])).map(n => `<span class="wo-tag">${esc(n)}</span>`).join('');
    const apply = o.applyUrl
      ? `<a class="wo-apply" href="${esc(o.applyUrl)}" rel="nofollow noopener" target="_blank">How they ask you to submit</a>`
      : (o.siteUrl ? `<a class="wo-apply" href="${esc(o.siteUrl)}" rel="nofollow noopener" target="_blank">Visit site</a>` : '');
    const policyJson = esc(JSON.stringify(o.countryPolicy || {}));
    const accepted = esc(JSON.stringify(o.countriesAccepted || []));
    const rejected = esc(JSON.stringify(o.countriesRejected || []));
    return `<article class="wo-card" data-niches="${esc((Array.isArray(o.niches) ? o.niches : []).join(','))}" data-contact="${reply.key}" data-policy="${policyJson}" data-accepted="${accepted}" data-rejected="${rejected}">
      <header class="wo-card-head"><h3><a href="${url('/make-money/writing-opportunities/' + o.slug + '/')}">${esc(o.name)}</a></h3><span class="wo-checked">Last checked ${esc(o.lastChecked)}</span></header>
      ${tags ? `<div class="wo-tags">${tags}</div>` : ''}
      ${facts(o)}
      ${o.whatTheyWant ? `<p>${esc(o.whatTheyWant)}</p>` : ''}
      ${o.whoItsNotFor ? `<p class="wo-notfor"><b>Skip if:</b> ${esc(o.whoItsNotFor)}</p>` : ''}
      <p class="wo-actions">${apply} <a class="wo-apply" href="${url('/make-money/writing-opportunities/' + o.slug + '/')}">Full guide</a></p>
    </article>`;
  };

  const countryStrip = `<div class="mm-desk wo-inline-desk" data-mm-desk data-mm-desk-compact>
    <p class="mm-desk-lead"><b>Country.</b> Pick yours. Cards that reject it drop out. Unknown stays visible — I will not pretend I know.</p>
    <div class="mm-countries" role="group" aria-label="Choose your country">${(data.countries || MONEY_DESK.countries).map(c => `<button type="button" class="mm-country" data-mm-country="${esc(c.id)}" data-mm-country-name="${esc(c.name)}">${esc(c.name)}</button>`).join('')}</div>
  </div>`;

  const filterBar = published.length ? `<div class="wo-filters" data-wo-filters>
    <label>Niche <select data-wo-niche><option value="">All niches</option>${niches.map(n => `<option value="${esc(n)}">${esc(n)}</option>`).join('')}</select></label>
    <label>Reply <select data-wo-contact><option value="">Any</option><option value="replied">Replied to me</option><option value="no-reply">No reply</option><option value="waiting">Waiting</option><option value="unknown">Not contacted</option></select></label>
    <button type="button" class="fbtn" data-wo-clear>Clear filters</button>
    <p class="wo-count" data-wo-count></p>
  </div>` : '';

  const empty = `<div class="vstate wo-empty"><b>No sites in the catalogue yet</b><p data-wo-empty-copy>I have not published a dated site. When I research one and write to them, the card will appear here — including if they never reply. I will not invent a reply time or “actively hiring” badge to fill this space.</p></div>`;

  const how = `<section class="wo-how">
    <h2>What each card is allowed to say</h2>
    <ol class="wo-steps">
      <li><b>Accepts articles / submissions open.</b> Only from their current write-for-us page, dated.</li>
      <li><b>Pay.</b> Only what they published or told me. Not a rate from another blog.</li>
      <li><b>Your country.</b> Accepted, rejected, or unknown. Unknown is the default.</li>
      <li><b>Reply time.</b> Only from my own application: “replied in X days” or “no reply after X days”. Never a guessed average.</li>
    </ol>
    <div class="vnote">Writing can pay. Landing a gig is not promised. Guidelines change. Re-check their page before you send anything.</div>
  </section>`;

  const yt = data.youtubeVideoUrl
    ? `<section class="wo-video"><h2>Latest video</h2><p><a href="${esc(data.youtubeVideoUrl)}" rel="noopener" target="_blank">${esc(data.youtubeVideoTitle || 'Watch on YouTube')}</a></p></section>`
    : `<section class="wo-video"><h2>YouTube</h2><p class="wo-pending">No video is linked yet. When the first one goes up it will sit here.</p></section>`;

  const guideLink = url('/make-money/writing-field-notes-how-this-works/');
  const crumbs = [
    { name: 'Home', path: '/' },
    { name: 'BRYME Make Money', path: '/make-money/' },
    { name: 'Writing catalogue', path: '/make-money/writing-opportunities/' }
  ];
  const desc = 'A catalogue of websites I researched for writers. Filter by country. See whether they accept articles, if submissions were open when I checked, whether they pay, and how I applied. A gig is not guaranteed.';
  const body = `<main class="shell wo-page"><div class="crumb"><a href="${url('/')}">Home</a> / <a href="${url('/make-money/')}">BRYME Make Money</a> / Writing</div>
    <section class="hero vhero vhero-make-money"><div class="eyebrow">💰 BRYME Make Money · Writing</div>
      <h1>${esc(data.title || 'Writing catalogue')}</h1>
      <p class="lead">${esc(data.tagline || 'Pick your country. Then see sites I actually researched. A gig is not guaranteed.')}</p>
    </section>
    ${countryStrip}
    ${how}
    <section class="section">
      <div class="section-head"><h2>The catalogue</h2></div>
      <p class="section-note">${published.length ? published.length + ' published site' + (published.length === 1 ? '' : 's') + ' · last file update ' + esc(data.updatedAt || TODAY) : 'Empty on purpose until a site is researched and dated.'}</p>
      ${filterBar}
      <div class="wo-grid" data-wo-grid>${published.length ? published.map(card).join('') : empty}</div>
    </section>
    ${yt}
    <section class="section"><div class="section-head"><h2>Read the rulebook</h2></div>
      <div class="vcat-grid">
        <a class="vcat" href="${guideLink}"><b>How this series works</b><span>What I log, what I refuse to invent, and why this beats buying a script.</span></a>
        <a class="vcat" href="${url('/make-money/beginners-guide-to-making-money-online/')}"><b>Beginner’s guide to making money online</b><span>The skill-first piece this series sits on top of.</span></a>
      </div>
    </section>
    ${coreHubStrip('make-money')}
  </main>
  <script>
  (function(){
    var KEY = 'bryme-mm-country';
    var desk = document.querySelector('[data-mm-desk]');
    var grid = document.querySelector('[data-wo-grid]');
    var countries = ${JSON.stringify((data.countries || []).map(c => ({id:c.id, name:c.name}))).replace(/</g, '\\\\u003c')};
    function qCountry(){ try { return new URLSearchParams(location.search).get('country') || ''; } catch (e) { return ''; } }
    function saved(){ try { return localStorage.getItem(KEY) || ''; } catch (e) { return ''; } }
    function nameOf(id){ var hit = countries.filter(function(c){ return c.id === id; })[0]; return hit ? hit.name : ''; }
    var current = qCountry() || saved();
    function verdict(card, countryName){
      if (!countryName) return 'unknown';
      try {
        var policy = JSON.parse(card.getAttribute('data-policy') || '{}');
        if (policy[countryName]) return policy[countryName];
        var acc = JSON.parse(card.getAttribute('data-accepted') || '[]');
        var rej = JSON.parse(card.getAttribute('data-rejected') || '[]');
        var low = countryName.toLowerCase();
        if (acc.some(function(x){ return String(x).toLowerCase() === low; })) return 'accepted';
        if (rej.some(function(x){ return String(x).toLowerCase() === low; })) return 'rejected';
      } catch (e) {}
      return 'unknown';
    }
    function paintCountry(){
      if (desk) {
        desk.querySelectorAll('[data-mm-country]').forEach(function(btn){
          btn.classList.toggle('is-on', btn.getAttribute('data-mm-country') === current);
        });
      }
      var countryName = nameOf(current);
      try { if (current) localStorage.setItem(KEY, current); } catch (e) {}
      if (grid) {
        grid.querySelectorAll('.wo-card').forEach(function(card){
          var v = verdict(card, countryName);
          card.setAttribute('data-country-verdict', v);
          var dd = card.querySelector('[data-wo-country-verdict]');
          if (dd) {
            dd.textContent = !countryName ? 'Pick a country above' : (v === 'accepted' ? 'Accepts ' + countryName + ' (as logged)' : v === 'rejected' ? 'Does not accept ' + countryName + ' (as logged)' : 'Unknown for ' + countryName);
          }
        });
      }
      var emptyCopy = document.querySelector('[data-wo-empty-copy]');
      if (emptyCopy && countryName) {
        emptyCopy.textContent = 'I have not published a dated site for ' + countryName + ' yet. When I research one and write to them, it will appear here. I will not invent a reply time to fill this space.';
      }
      applyFilters();
    }
    var root = document.querySelector('[data-wo-filters]');
    var niche = root && root.querySelector('[data-wo-niche]');
    var contact = root && root.querySelector('[data-wo-contact]');
    var count = root && root.querySelector('[data-wo-count]');
    function applyFilters(){
      if (!grid) return;
      var cards = Array.prototype.slice.call(grid.querySelectorAll('.wo-card'));
      var n = niche && niche.value;
      var k = contact && contact.value;
      var shown = 0;
      cards.forEach(function(card){
        var ok = true;
        if (card.getAttribute('data-country-verdict') === 'rejected') ok = false;
        if (n && (',' + (card.getAttribute('data-niches') || '') + ',').indexOf(',' + n + ',') === -1) ok = false;
        if (k && card.getAttribute('data-contact') !== k) ok = false;
        card.hidden = !ok;
        if (ok) shown++;
      });
      if (count) count.textContent = cards.length ? (shown + ' of ' + cards.length + ' sites') : '';
    }
    if (desk) desk.addEventListener('click', function(e){
      var btn = e.target.closest('[data-mm-country]');
      if (!btn) return;
      current = btn.getAttribute('data-mm-country');
      try {
        var u = new URL(location.href);
        u.searchParams.set('country', current);
        history.replaceState({}, '', u.toString());
      } catch (err) {}
      paintCountry();
    });
    if (root) {
      root.addEventListener('change', applyFilters);
      var clear = root.querySelector('[data-wo-clear]');
      if (clear) clear.addEventListener('click', function(){
        if (niche) niche.value = '';
        if (contact) contact.value = '';
        applyFilters();
      });
    }
    paintCountry();
  })();
  <\/script>`;

  const pagePath = '/make-money/writing-opportunities/';
  write('make-money/writing-opportunities', layout({
    title: (data.title || 'Writing catalogue') + ' – sites I actually researched',
    description: desc,
    path: pagePath,
    activeNav: 'make-money',
    schema: [
      { '@context': 'https://schema.org', '@type': 'CollectionPage', name: data.title || 'Writing catalogue', description: desc, url: absUrl(pagePath) },
      breadcrumbs(crumbs)
    ],
    body
  }));

  published.forEach(o => {
    const reply = replyFact(o);
    const detailPath = '/make-money/writing-opportunities/' + o.slug + '/';
    WRITING_EXTRA_PATHS.push(detailPath);
    if (ISO.test(String(o.lastChecked))) PAGE_LASTMOD.set(detailPath, o.lastChecked);
    const sourceBlock = Array.isArray(o.sources) && o.sources.length
      ? `<section class="sp-source"><h2>Sources</h2><p>${o.sources.map(src =>
          src.url ? `<a href="${esc(src.url)}" rel="nofollow noopener">${esc(src.name || src.url)}</a>` : esc(src.name || src)
        ).join(' · ')}</p><p class="sp-source-note">Checked ${esc(o.lastChecked)}. Their rules can change — confirm on their page before you send work.</p></section>`
      : '';
    const dCrumbs = crumbs.concat([{ name: o.name, path: detailPath }]);
    const dBody = `<main class="shell wo-page"><div class="crumb"><a href="${url('/')}">Home</a> / <a href="${url('/make-money/')}">BRYME Make Money</a> / <a href="${url(pagePath)}">Writing</a> / ${esc(o.name)}</div>
      <section class="article-hero"><div class="eyebrow">Writing catalogue</div>
        <h1>${esc(o.name)}</h1>
        <p class="lead">${esc(o.whatTheyWant || o.notes || 'A publication I researched for writers. Nothing here is a guarantee.')}</p>
        <div class="article-meta"><span>Last checked ${esc(o.lastChecked)}</span><span>Logged from ${esc(o.writerCountry)}</span></div>
      </section>
      <article class="prose article-body">
        ${facts(o)}
        ${o.payNotes ? `<h2>Pay</h2><p>${esc(o.payNotes)}</p>` : ''}
        ${listBlock('Write-up guidelines', o.guidelines)}
        ${listBlock('How to submit', o.howToSubmit)}
        ${o.notes ? `<h2>What I did</h2><p>${esc(o.notes)}</p>` : ''}
        ${o.whoItsNotFor ? `<h2>Skip this if</h2><p>${esc(o.whoItsNotFor)}</p>` : ''}
        ${Array.isArray(o.unknowns) && o.unknowns.length ? `<h2>Still unknown</h2><ul>${o.unknowns.map(u => `<li>${esc(u)}</li>`).join('')}</ul>` : ''}
        <div class="vnote">A gig is not guaranteed. This is a dated field note, not a hiring promise.</div>
        ${o.applyUrl ? `<p><a class="cta" href="${esc(o.applyUrl)}" rel="nofollow noopener" target="_blank">Their submit page</a></p>` : ''}
      </article>
      ${sourceBlock}
      <section class="section"><a class="quiet-link" href="${url(pagePath)}">← Back to the writing catalogue</a></section>
    </main>`;
    write('make-money/writing-opportunities/' + o.slug, layout({
      title: o.name + ' – writing guide',
      description: (o.whatTheyWant || o.notes || ('How to submit to ' + o.name + '. Dated. A gig is not guaranteed.')).slice(0, 158),
      path: detailPath,
      activeNav: 'make-money',
      schema: [{ '@context':'https://schema.org', '@type':'Article', headline: o.name, dateModified: o.lastChecked, description: o.whatTheyWant || undefined }, breadcrumbs(dCrumbs)],
      body: dBody
    }));
  });
}


buildWritingOpportunities();
require('./build-opportunity-catalog')({
  fs, path, root, esc, url, absUrl, layout, write, breadcrumbs,
  TODAY, PAGE_LASTMOD, WRITING_EXTRA_PATHS, warnings, VERTICALS, verticalChip, coreHubStrip, sendBar, SENDABLE_META, site
});


// Entertainment hub — the existing mature section, presented under BRYME Entertainment
write('entertainment', layout({
  title: 'BRYME Entertainment – Movies, TV Series & Anime',
  description: 'BRYME Entertainment: 630+ movies, TV series and anime with verified trailers, editorial articles and curated recommendations.',
  path: '/entertainment/', activeNav: 'entertainment',
  schema: [{ '@context':'https://schema.org', '@type':'CollectionPage', name:'BRYME Entertainment', description:'Movies, TV series and anime discovery on BRYME.', url:url('/entertainment/') }, breadcrumbs([{name:'Home', path:'/'}, {name:'BRYME Entertainment', path:'/entertainment/'}])],
  body: `<main class="shell"><section class="ent-feature ent-feature-photo" style="--hero-img:url('/assets/img/ent/hero-cinema.jpg')"><div class="ent-feature-inner"><div class="eyebrow">🎬 BRYME Entertainment</div><h1>Movies, series &amp; anime worth your time.</h1><p>Browse 630+ titles with verified trailers, editorial articles and curated recommendations — all in one place.</p></div></section>
    <section class="sp-hero" aria-label="Featured BRYME Entertainment stories"><div class="sp-hero-track">
      <a class="sp-hero-card sp-hero-first ent-tint" href="${url('/article/nigerian-thrillers-worth-your-time/')}" style="--card-img:url('/assets/img/ent/hero-nollywood.jpg')"><span class="sp-hero-tag">Nigeria</span><h3>Five Nigerian thrillers to start with</h3><p>October 1, The Figurine, Brotherhood and two more. A short list, not a dump.</p><span class="sp-hero-go">Read the guide →</span></a>
      <a class="sp-hero-card ent-tint" href="${url('/article/squid-game-season-1-why-it-became-a-global-phenomenon/')}" style="--card-img:url('/assets/img/ent/hero-survival.jpg')"><span class="sp-hero-tag">Series</span><h3>Why Squid Game travelled</h3><p>The first season, the hook, and why it is still the show people name.</p><span class="sp-hero-go">Read the piece →</span></a>
      <a class="sp-hero-card ent-tint" href="${url('/article/korean-cinema-starter-guide-rebuilt/')}" style="--card-img:url('/assets/img/ent/hero-korean.jpg')"><span class="sp-hero-tag">Korean cinema</span><h3>A starter guide by mood</h3><p>Not a dump of every Palme d'Or. A route through films already on BRYME.</p><span class="sp-hero-go">Open the guide →</span></a>
    </div></section>
  <section class="section"><div class="grid-2" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:14px">${[['Movies','/movies/','🎬','hub/movies'],['Series','/series/','📺','hub/series'],['Anime','/anime/','🍥','hub/anime'],['Articles','/articles/','📰','hub/articles'],['Genres','/genres/','🎭','hub/entertainment'],['Years','/years/','🗓️','hub/entertainment'],['Trending & Picks','/trending/','🔥','hub/entertainment'],['Topics','/topics/','🧭','hub/entertainment']].map(x => photoTile(x[1], x[2] + ' ' + x[0], 'Explore the ' + x[0].toLowerCase() + ' section', catImg(x[3]))).join('')}</div></section>
  <section class="section"><div class="section-head"><h2>🔥 What's Trending</h2><a href="${url('/trending/')}">View all</a></div><div class="rail">${trendNow.slice(0, 10).map(card).join('')}</div></section>
  <section class="section"><div class="section-head"><h2>⭐ Popular Movies</h2><a href="${url('/movies/')}">All movies</a></div><div class="rail">${popularMovies.slice(0, 10).map(card).join('')}</div></section>
  <section class="section"><div class="section-head"><h2>⭐ Popular Series</h2><a href="${url('/series/')}">All series</a></div><div class="rail">${popularSeries.slice(0, 10).map(card).join('')}</div></section>
  <section class="section"><div class="section-head"><h2>⭐ Popular Anime</h2><a href="${url('/anime/')}">All anime</a></div><div class="rail">${popularAnime.slice(0, 10).map(card).join('')}</div></section>
  <section class="section"><div class="section-head"><h2>Start here</h2><a href="${url('/articles/')}">All stories</a></div>
  <p class="section-note">These are existing BRYME pieces — not new URLs dumped for a crawler.</p>
  <div class="story-grid">${['nigerian-thrillers-worth-your-time','korean-cinema-starter-guide-rebuilt','dune-sci-fi-epics-guide','christopher-nolan-movies-order','squid-game-season-1-why-it-became-a-global-phenomenon','10-anime-like-solo-leveling-you-should-watch'].map(slug => articles.find(a => a.slug === slug)).filter(Boolean).map(a => storyPhoto('/article/' + a.slug + '/', a.category, a.title, a.description || '', heroFor(a.slug, 'entertainment'))).join('')}</div></section>
  <section class="section"><div class="section-head"><h2>📰 Latest articles</h2><a href="${url('/articles/')}">All stories</a></div><div class="story-grid">${latestArticles.map(a => storyPhoto('/article/' + a.slug + '/', a.category, a.title, a.description || '', heroFor(a.slug, 'entertainment'))).join('')}</div></section>
  ${coreHubStrip('entertainment')}</main>`
}));

/* WhatsApp / YouTube send landing — one URL for Status and video descriptions. */
(function writeNowPage(){
  const picks = [
    { slug: 'a-tribe-called-judah', type: 'movie', kicker: 'Lagos · film', blurb: 'A mother, five sons, and a city that will not wait. Start here if you are sending to people in Nigeria.' },
    { slug: 'dune-part-two', type: 'movie', kicker: 'Sci-fi · trailer', blurb: 'What the film is, the official trailer, and legal watch notes. Not a download page.' },
    { slug: 'squid-game', type: 'series', kicker: 'Series', blurb: 'The survival show everyone already names — plus what to open next on BRYME.' },
    { href: '/article/nigerian-thrillers-worth-your-time/', title: 'Five Nigerian thrillers to start with', kicker: 'Guide', blurb: 'October 1, The Figurine, Brotherhood and two more. A short list, not a dump.' },
    { href: '/make-money/writing/', title: 'Writing markets we actually checked', kicker: 'Make Money', blurb: 'Official rates and doors. A gig is not guaranteed. This is the YouTube end-card link.' }
  ];
  const cards = picks.map(p => {
    if (p.slug) {
      const rec = slugIndex.get(p.slug);
      if (!rec) return '';
      const href = '/' + rec.typeDir + '/' + rec.slug + '/';
      return `<a class="now-card" href="${url(href)}"><span class="oc-editor-kicker">${esc(p.kicker)}</span><b>${esc(rec.title)}</b><span>${esc(p.blurb)}</span><span class="now-go">Open →</span></a>`;
    }
    return `<a class="now-card" href="${url(p.href)}"><span class="oc-editor-kicker">${esc(p.kicker)}</span><b>${esc(p.title)}</b><span>${esc(p.blurb)}</span><span class="now-go">Open →</span></a>`;
  }).join('');
  const ytCopy = `What to open on BRYME:\nhttps://bryme.onrender.com/now/\n\nWriting markets I actually checked:\nhttps://bryme.onrender.com/make-money/writing/\n\nA gig is not guaranteed.`;
  const waCopy = `Five pages on BRYME worth opening:\nhttps://bryme.onrender.com/now/`;
  write('now', layout({
    title: 'Send BRYME — five pages worth opening',
    description: 'One link for WhatsApp Status or a YouTube description: five BRYME pages worth opening. Trailers, legal watch notes, and writing markets we checked. A gig is not guaranteed.',
    path: '/now/',
    activeNav: 'home',
    schema: [{ '@context':'https://schema.org', '@type':'CollectionPage', name:'Send BRYME', url: absUrl('/now/') }, breadcrumbs([{name:'Home', path:'/'}, {name:'Send BRYME', path:'/now/'}])],
    body: `<main class="shell">
      <div class="crumb"><a href="${url('/')}">Home</a> / Send</div>
      <section class="hero"><div class="eyebrow">WhatsApp · YouTube</div>
        <h1>Send this. Then pick one.</h1>
        <p class="lead">Five pages on BRYME worth a Status or a video description. Trailers, legal viewing notes, and writing markets we actually checked. Nothing here is a download. A gig is not guaranteed.</p>
        ${sendBar('/now/', 'Five pages on BRYME worth opening')}
      </section>
      <section class="section"><div class="section-head"><h2>The five</h2></div>
        <div class="now-grid">${cards}</div>
      </section>
      <section class="section" id="youtube"><div class="section-head"><h2>If you came from YouTube</h2></div>
        <p class="section-note">The video is about the process. The living list is the writing catalogue. Paste this in the description and pin it.</p>
        <pre class="now-copy">${esc(ytCopy)}</pre>
        <p><a class="cta" href="${url('/make-money/writing/')}">Open writing markets</a>
        <a class="quiet-link" href="${url('/make-money/writing-field-notes-how-this-works/')}">How the notes work</a></p>
      </section>
      <section class="section"><div class="section-head"><h2>WhatsApp caption</h2></div>
        <pre class="now-copy">${esc(waCopy)}</pre>
      </section>
      ${coreHubStrip('home', { title: 'Or browse a section', lead: 'If you would rather wander than send one card.' })}
    </main>`
  }));
})();

/* ================================================================
   BRYME SPORTS — hero carousel, transfers, managers, editorial
   table, FPL, match centre, fixtures/results, article placeholders.
   Structure first, content later. No fabricated data.
   ================================================================ */
const sportsCfgPath = path.join(root, 'content', 'sports.json');
let sportsCfg = {};
if (fs.existsSync(sportsCfgPath)) { try { sportsCfg = JSON.parse(fs.readFileSync(sportsCfgPath, 'utf8')); } catch (e) { warnings.push('sports.json unreadable'); } }
const S = sportsCfg || {};
const SEASON = S.season || '2026/27';
const MW = S.matchweek || 1;
const mwLabel = 'Matchweek ' + MW;

/* --- image placeholder system: alt/credit/source/license-capable --- */
function sportImgPlaceholder(alt, credit){
  return `<div class="sp-img" role="img" aria-label="${esc(alt)}"><span>${esc(alt)}</span>${credit ? `<small>Image: ${esc(credit)}</small>` : '<small>Image placeholder — licensed/reusable image to be added</small>'}</div>`;
}
/* --- article placeholder page (full structure, body pending) --- */
function sportArticlePlaceholder(art){
  const route = art.route;
  const crumbs = [{name:'Home', path:'/'}, {name:'BRYME Sports', path:'/sports/'}, {name:art.title, path:'/' + route + '/'}];
  const schema = [
    { '@context':'https://schema.org', '@type':'Article', headline: art.title, description: art.excerpt,
      mainEntityOfPage: url('/' + route + '/'), publisher: { '@type':'Organization', name: site.name } },
    breadcrumbs(crumbs)
  ];
  const related = (art.related || []).map(r => `<a class="sp-rel" href="${url('/sports/' + r + '/')}">${esc(r.split('/').pop().replace(/-/g, ' '))}</a>`).join('');
  const body = `<main class="shell">
    <div class="crumb"><a href="${url('/')}">Home</a> / <a href="${url('/sports/')}">BRYME Sports</a> / ${esc(art.title)}</div>
    <article class="sp-article">
      <header class="sp-article-head"><div class="eyebrow">⚽ BRYME Sports · ${esc(art.category)}</div><h1>${esc(art.title)}</h1>
        <p class="lead">${esc(art.excerpt)}</p>
        <div class="sp-meta"><span>By BRYME Sports Editorial</span><span>Published: when the article is finalised</span><span>Last updated: —</span></div>
      </header>
      ${sportImgPlaceholder(art.title + ' — hero image', null)}
      <div class="sp-body-placeholder">
        <b>Article body — coming soon</b>
        <p>This page is a structured placeholder. The full article will be researched, written in BRYME's own editorial voice and published here. Facts, quotes, statistics and lineups are never invented.</p>
      </div>
      <section class="sp-source"><h2>Source</h2><p><b>Source:</b> [Source Name]</p><p><b>Original report:</b> [Link]</p><p class="sp-source-note">Information on this page is rewritten in BRYME's own original editorial voice, never copied. External selections and claims are always identified with their source.</p></section>
      ${related ? `<section class="sp-related"><h2>Related reading</h2><div class="sp-rel-grid">${related}</div></section>` : ''}
    </article></main>`;
  /* A placeholder is a structured shell, not a finished article. Indexing an empty
     "when the article is finalised" page invites Google/Bing "Crawled - currently not
     indexed" and reads as thin. Keep it reachable for visitors but noindex,follow and
     out of the sitemap until real editorial content replaces the placeholder. */
  write('sports/' + route, layout({ title: art.title + ' | BRYME Sports', description: art.excerpt, path: '/sports/' + route + '/', activeNav: 'sports', noindex: true, schema, body }));
}
/* --- transfer page: structured table, legend, empty state --- */
function transferPage(league){
  const crumbs = [{name:'Home', path:'/'}, {name:'BRYME Sports', path:'/sports/'}, {name:'Transfers', path:'/sports/transfers/'}, {name:league.title, path:'/sports/transfers/' + league.id + '-2026-27/'}];
  const legend = `<span class="sp-st-conf">${esc(S.transfers.legend.confirmed)}</span><span class="sp-st-rep">${esc(S.transfers.legend.reported)}</span><span class="sp-st-rum">${esc(S.transfers.legend.rumoured)}</span>`;
  const empty = `<tr class="sp-empty"><td colspan="6">No verified ${esc(league.name)} transfers listed yet. Entries appear here only when confirmed by clubs or reported by credible outlets — with the source shown. Rumours are never presented as confirmed.</td></tr>`;
  const row = (dir) => `<h3 class="sp-dir">${dir === 'in' ? '⬇ Transfer In' : '⬆ Transfer Out'}</h3><div class="sp-table-wrap"><table class="sp-table"><thead><tr><th>Player</th><th>From</th><th>To</th><th>Status</th><th>Date</th><th>Source</th></tr></thead><tbody>${empty}</tbody></table></div>`;
  const body = `<main class="shell"><div class="crumb"><a href="${url('/')}">Home</a> / <a href="${url('/sports/')}">BRYME Sports</a> / <a href="${url('/sports/transfers/')}">Transfers</a> / ${esc(league.title)}</div>
    <section class="hero"><div class="eyebrow">⚽ Transfers · ${esc(league.name)}</div><h1>${esc(league.title)}</h1><p class="lead">Structured transfer tracker for ${esc(league.name)}. Status legend: ${legend}.</p></section>
    <div class="vnote">${esc(S.transfers.disclaimer)}</div>
    ${row('in')}${row('out')}
    <section class="sp-related"><h2>Other leagues</h2><div class="sp-rel-grid">${S.transfers.leagues.filter(l => l.id !== league.id).map(l => `<a class="sp-rel" href="${url('/sports/transfers/' + l.id + '-2026-27/')}">${esc(l.name)} Transfers</a>`).join('')}</div></section>
    <section class="sp-related"><h2>Related</h2><div class="sp-rel-grid"><a class="sp-rel" href="${url('/sports/managers-2026-27/')}">Managers In &amp; Out</a><a class="sp-rel" href="${url('/sports/premier-league/matchweek-1-preview/')}">Matchweek ${MW} Preview</a></div></section></main>`;
  write('sports/transfers/' + league.id + '-2026-27', layout({ title: league.title + ' | BRYME Sports', description: 'Structured ' + league.name + ' transfer tracker for ' + SEASON + ' — confirmed, reported and rumoured deals, each with a source.', path: '/sports/transfers/' + league.id + '-2026-27/', activeNav: 'sports', schema: [{ '@context':'https://schema.org', '@type':'CollectionPage', name: league.title, url: absUrl('/sports/transfers/' + league.id + '-2026-27/') }, breadcrumbs(crumbs)], body }));
}
/* --- transfers hub --- */
function transfersHub(){
  const crumbs = [{name:'Home', path:'/'}, {name:'BRYME Sports', path:'/sports/'}, {name:'Transfers', path:'/sports/transfers/'}];
  const body = `<main class="shell"><div class="crumb"><a href="${url('/')}">Home</a> / <a href="${url('/sports/')}">BRYME Sports</a> / Transfers</div>
    <section class="hero"><div class="eyebrow">⚽ Transfers</div><h1>Transfer trackers ${SEASON}</h1><p class="lead">League-by-league transfer trackers. Every deal is labelled Confirmed, Reported or Rumoured — never presented as more than the source supports.</p></section>
    <div class="vnote">${esc(S.transfers.disclaimer)}</div>
    <section class="section"><div class="vcat-grid">${S.transfers.leagues.map(l => { const tr = transferStats(l.id); const bits = ['Transfers ' + SEASON]; if (tr.in + tr.out > 0) bits.push(tr.in + ' in / ' + tr.out + ' out'); if (tr.confirmed > 0) bits.push(tr.confirmed + ' confirmed'); return `<a class="vcat" href="${url('/sports/transfers/' + l.id + '-2026-27/')}"><b>${esc(l.name)}</b><span>${esc(bits.join(' · '))}</span></a>`; }).join('')}<a class="vcat" href="${url('/sports/managers-2026-27/')}"><b>Managers</b><span>Managers In &amp; Out — ${SEASON}</span></a></div></section></main>`;
  write('sports/transfers', layout({ title: 'Transfers ' + SEASON + ' | BRYME Sports', description: 'League-by-league football transfer trackers for ' + SEASON + ' — Premier League, La Liga, Serie A, Bundesliga and Ligue 1, each deal labelled and sourced.', path: '/sports/transfers/', activeNav: 'sports', schema: [{ '@context':'https://schema.org', '@type':'CollectionPage', name: 'Transfers ' + SEASON, url: absUrl('/sports/transfers/') }, breadcrumbs(crumbs)], body }));
}
/* --- managers page (real data from the transfer trackers) --- */
function managersPage(){
  const crumbs = [{name:'Home', path:'/'}, {name:'BRYME Sports', path:'/sports/'}, {name:'Managers', path:'/sports/managers-2026-27/'}];
  // Gather manager data from the five league trackers
  const allClubs = [];
  const plPath2 = path.join(root, 'content', 'pl-transfers.json');
  if (fs.existsSync(plPath2)) {
    try {
      const pl2 = JSON.parse(fs.readFileSync(plPath2, 'utf8'));
      (pl2.clubs || []).forEach(c => allClubs.push({ league: 'Premier League', name: c.name, id: c.id, manager: c.manager, note: c.managerNote }));
    } catch (e) { warnings.push('pl-transfers.json unreadable (managers)'); }
  }
  const lgPath2 = path.join(root, 'content', 'league-transfers.json');
  if (fs.existsSync(lgPath2)) {
    try {
      const lg2 = JSON.parse(fs.readFileSync(lgPath2, 'utf8'));
      (lg2.leagues || []).forEach(lg => (lg.clubs || []).forEach(c => allClubs.push({ league: lg.name, name: c.name, id: c.id, manager: c.manager, note: c.managerNote })));
    } catch (e) { warnings.push('league-transfers.json unreadable (managers)'); }
  }
  const leagueOrder = ['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1'];
  const byLeague = {};
  allClubs.forEach(c => { (byLeague[c.league] = byLeague[c.league] || []).push(c); });
  const managerCrest = (league, id) => {
    const lgId = { 'Premier League':'premier-league', 'La Liga':'la-liga', 'Serie A':'serie-a', 'Bundesliga':'bundesliga', 'Ligue 1':'ligue-1' }[league];
    if (lgId === 'premier-league') return url('/assets/img/sports/pl/' + id + '.svg');
    if (lgId === 'la-liga') return url('/assets/img/sports/ll/' + (LL_NAME[id] || id) + '.png');
    if (lgId === 'bundesliga') return id === 'hamburg' ? url('/assets/img/sports/club-' + id + '.svg') : url('/assets/img/sports/bl/' + id + '.svg');
    if (lgId === 'ligue-1') return url('/assets/img/sports/l1/' + id + '.webp');
    if (lgId === 'serie-a') return url('/assets/img/sports/sa/' + id + (id === 'lazio' ? '.png' : '.svg'));
    return url('/assets/img/sports/club-' + id + '.svg');
  };
  const badge = note => {
    const n = (note || '').toLowerCase();
    if (/^new/.test(n)) return '<span class="sp-mgr-badge sp-mgr-new">NEW</span>';
    if (/no change/.test(n)) return '<span class="sp-mgr-badge sp-mgr-keep">No change</span>';
    return '';
  };
  const leagueBlocks = leagueOrder.filter(l => byLeague[l]).map(lg => {
    const rows = byLeague[lg].map(c => {
      const lgId = { 'Premier League':'premier-league', 'La Liga':'la-liga', 'Serie A':'serie-a', 'Bundesliga':'bundesliga', 'Ligue 1':'ligue-1' }[lg];
      const official = lg === 'Premier League' || lg === 'Serie A' || (['La Liga','Bundesliga','Ligue 1'].includes(lg) && c.id !== 'hamburg');
      return `<tr><td class="sp-mgr-club"><img src="${managerCrest(lg, c.id)}" alt="${official ? esc(c.name) + ' official club crest' : 'Abstract crest for ' + esc(c.name) + ' — BRYME-generated illustration'}" width="28" height="34" loading="lazy"><b>${esc(c.name)}</b></td><td>${c.manager ? '<b>' + esc(c.manager) + '</b>' : '<span class="sp-mgr-pending">Pending verification</span>'}</td><td>${badge(c.note)} <span class="sp-mgr-note">${esc(c.note || '')}</span></td></tr>`;
    }).join('');
    return `<h3 class="sp-dir">${esc(lg)}</h3><div class="sp-table-wrap"><table class="sp-table"><thead><tr><th>Club</th><th>Manager</th><th>Status / note</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  }).join('');
  const note = 'Managerial changes are only listed once confirmed by the clubs or widely reported by credible outlets. Sources are always shown on the league transfer trackers.';
  const body = `<main class="shell"><div class="crumb"><a href="${url('/')}">Home</a> / <a href="${url('/sports/')}">BRYME Sports</a> / Managers</div>
    <section class="hero"><div class="eyebrow">⚽ Managers</div><h1>${esc(S.managers.title)}</h1><p class="lead">${esc(note)}</p></section>
    <p class="sp-updated">Last updated: ${esc('13 August 2026')}</p>
    <div class="sp-credits"><b>Premier League club crests</b> © Copyright The Football Association Premier League Limited, 2016, used under the Premier League Logo Site media licence for editorial reporting. BRYME Sports is not affiliated with, endorsed or sponsored by the Premier League or any club. Crests for La Liga (LaLiga), Serie A, Bundesliga (DFL) and Ligue 1 (LFP) clubs are © their respective clubs, retrieved from official league/club websites and Wikimedia Commons, and used solely for editorial reporting. Only Hamburger SV still shows a BRYME-generated abstract illustration.</div>
    <div class="sp-legend-line">${leagueOrder.filter(l => byLeague[l]).map(l => `<span class="sp-st-conf">${esc(l)}</span>`).join(' ')}</div>
    ${leagueBlocks}
    <section class="sp-related"><h2>Related</h2><div class="sp-rel-grid"><a class="sp-rel" href="${url('/sports/transfers/')}">Transfer trackers</a><a class="sp-rel" href="${url('/sports/premier-league/matchweek-1-preview/')}">Matchweek ${MW} Preview</a></div></section></main>`;
  write('sports/managers-2026-27', layout({ title: S.managers.title + ' | BRYME Sports', description: note, path: '/sports/managers-2026-27/', activeNav: 'sports', schema: [{ '@context':'https://schema.org', '@type':'CollectionPage', name: S.managers.title, url: absUrl('/sports/managers-2026-27/') }, breadcrumbs(crumbs)], body }));
}
/* --- editorial prediction table --- */
function editorialTablePage(){
  const crumbs = [{name:'Home', path:'/'}, {name:'BRYME Sports', path:'/sports/'}, {name:'Premier League', path:'/sports/premier-league/'}, {name:'Table Prediction', path:'/sports/premier-league/table/'}];
  const body = `<main class="shell"><div class="crumb"><a href="${url('/')}">Home</a> / <a href="${url('/sports/')}">BRYME Sports</a> / <a href="${url('/sports/premier-league/')}">Premier League</a> / Table Prediction</div>
    <section class="hero"><div class="eyebrow">⚽ Premier League · Editorial</div><h1>${esc(S.editorialTable.title)}</h1><div class="sp-ed-label">${esc(S.editorialTable.label)}</div><p class="lead">${esc(S.editorialTable.note)}</p></section>
    <div class="sp-table-wrap"><table class="sp-table sp-table-pred"><thead><tr>${S.editorialTable.columns.map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead><tbody><tr class="sp-empty"><td colspan="7">The editorial prediction table will appear here once the BRYME Sports editorial team finalises it for ${mwLabel}. Predictions are never presented as guarantees or as the official table.</td></tr></tbody></table></div>
    <p class="sp-source-note">After the gameweek is completed, this component can be replaced with the official Premier League table.</p>
    <section class="sp-related"><h2>Related</h2><div class="sp-rel-grid"><a class="sp-rel" href="${url('/sports/premier-league/fixtures/')}">Fixtures</a><a class="sp-rel" href="${url('/sports/premier-league/results/')}">Results</a><a class="sp-rel" href="${url('/sports/premier-league/matchweek-1-preview/')}">Matchweek ${MW}</a></div></section></main>`;
  /* The editorial prediction table is still an empty placeholder. Indexing an empty
     table invites "Crawled - currently not indexed", so keep it noindex,follow and out
     of the sitemap until the prediction table is actually finalised. */
  write('sports/premier-league/table', layout({ title: S.editorialTable.title + ' | BRYME Sports', description: S.editorialTable.label + ' — ' + S.editorialTable.note, path: '/sports/premier-league/table/', activeNav: 'sports', noindex: true, schema: [{ '@context':'https://schema.org', '@type':'CollectionPage', name: S.editorialTable.title, url: absUrl('/sports/premier-league/table/') }, breadcrumbs(crumbs)], body }));
}
/* --- FPL hub --- */
function fplHub(){
  const crumbs = [{name:'Home', path:'/'}, {name:'BRYME Sports', path:'/sports/'}, {name:'Fantasy Premier League', path:'/sports/fpl/'}];
  const body = `<main class="shell"><div class="crumb"><a href="${url('/')}">Home</a> / <a href="${url('/sports/')}">BRYME Sports</a> / Fantasy Premier League</div>
    <section class="hero"><div class="eyebrow">⚽ Fantasy Premier League</div><h1>${esc(S.fpl.title)}</h1><p class="lead">${esc(S.fpl.desc)}</p></section>
    <section class="section"><div class="vcat-grid">${S.fpl.sections.map(s => `<a class="vcat" href="${url('/sports/fpl/gameweek-' + MW + '/#' + s.id + '/')}"><b>${esc(s.name)}</b><span>Gameweek ${MW} section</span></a>`).join('')}<a class="vcat" href="${url('/sports/fpl/gameweek-' + MW + '-players-to-watch/')}"><b>Gameweek ${MW} Players to Watch</b><span>Popular picks, differentials, captaincy</span></a></div></section>
    <section class="sp-related"><h2>Related</h2><div class="sp-rel-grid"><a class="sp-rel" href="${url('/sports/premier-league/matchweek-1-preview/')}">Matchweek ${MW} Preview</a><a class="sp-rel" href="${url('/sports/premier-league/injuries-matchweek-1/')}">Injury Report</a></div></section></main>`;
  write('sports/fpl', layout({ title: 'Fantasy Premier League | BRYME Sports', description: S.fpl.desc, path: '/sports/fpl/', activeNav: 'sports', schema: [{ '@context':'https://schema.org', '@type':'CollectionPage', name: 'Fantasy Premier League', url: absUrl('/sports/fpl/') }, breadcrumbs(crumbs)], body }));
  // gameweek hub
  const gwBody = `<main class="shell"><div class="crumb"><a href="${url('/')}">Home</a> / <a href="${url('/sports/')}">BRYME Sports</a> / <a href="${url('/sports/fpl/')}">FPL</a> / Gameweek ${MW}</div>
    <section class="hero"><div class="eyebrow">⚽ FPL · Gameweek ${MW}</div><h1>FPL Gameweek ${MW}</h1><p class="lead">Gameweek-by-gameweek FPL content. Each section below fills with researched, sourced content.</p></section>
    <section class="section">${S.fpl.sections.map(s => `<div class="sp-gw-sec" id="${s.id}"><h2>${esc(s.name)}</h2><p class="sp-empty-line">Content for this section is being prepared. No picks, predictions or difficulty ratings are shown before they are researched and sourced.</p></div>`).join('')}</section>
    <section class="sp-related"><h2>Related</h2><div class="sp-rel-grid"><a class="sp-rel" href="${url('/sports/fpl/gameweek-' + MW + '-players-to-watch/')}">Players to Watch</a><a class="sp-rel" href="${url('/sports/premier-league/matchweek-1-preview/')}">Matchweek ${MW} Preview</a></div></section></main>`;
  /* Every FPL section is still an empty "being prepared" shell until the editorial
     team writes researched picks. Indexing 8 empty sections reads as thin, so the
     gameweek hub stays reachable for visitors but noindex,follow and out of the
     sitemap until at least one section carries real content. */
  const fplGwEmpty = S.fpl.sections.length > 0 && gwBody.includes('sp-empty-line');
  write('sports/fpl/gameweek-' + MW, layout({ title: 'FPL Gameweek ' + MW + ' | BRYME Sports', description: 'Fantasy Premier League Gameweek ' + MW + ' — players to watch, picks, captaincy and fixture difficulty.', path: '/sports/fpl/gameweek-' + MW + '/', activeNav: 'sports', noindex: fplGwEmpty, schema: [{ '@context':'https://schema.org', '@type':'CollectionPage', name: 'FPL Gameweek ' + MW, url: absUrl('/sports/fpl/gameweek-' + MW + '/') }, breadcrumbs([{name:'Home', path:'/'}, {name:'BRYME Sports', path:'/sports/'}, {name:'FPL', path:'/sports/fpl/'}, {name:'Gameweek ' + MW, path:'/sports/fpl/gameweek-' + MW + '/'}])], body: gwBody }));
}
/* --- fixtures / results --- */
function euDstOffset(dateISO){
  // returns UTC offset hours for the league's local time on that date: +1 (CET) / +2 (CEST)
  const y = Number(dateISO.slice(0, 4));
  let start = new Date(Date.UTC(y, 2, 31)); while (start.getUTCDay() !== 0) start.setUTCDate(start.getUTCDate() - 1);
  let end = new Date(Date.UTC(y, 9, 31)); while (end.getUTCDay() !== 0) end.setUTCDate(end.getUTCDate() - 1);
  const t = Date.parse(dateISO + 'T12:00:00Z');
  return (t >= start.getTime() && t < end.getTime()) ? 2 : 1;
}
function leagueTimeInfo(lg, m){
  // returns { display, wat } for a match kickoff
  if (!m.time) return { display: '<span class="sp-fixt-time">Time TBC</span>', wat: '' };
  if (lg.slug === 'premier-league' && !m.timePublished) {
    return { display: `<span class="sp-fixt-time">${esc(m.time)} UK</span><span class="sp-std"> · std</span>`, wat: '' };
  }
  let offset;
  if (lg.slug === 'premier-league') {
    offset = euDstOffset(m.date) - 1; // BST +1 / GMT 0
  } else {
    offset = euDstOffset(m.date); // CEST +2 / CET +1
  }
  const tzSuffix = lg.timeSuffix || (offset === 2 ? 'CEST' : 'CET');
  let wat = '';
  if (offset !== 1) { // WAT = UTC+1; show when it differs from league-local time
    const [h, mn] = m.time.split(':').map(Number);
    let w = h + 1 - offset; if (w < 0) w += 24; if (w >= 24) w -= 24;
    wat = `<span class="sp-std"> · ${String(w).padStart(2, '0')}:${String(mn).padStart(2, '0')} WAT</span>`;
  }
  return { display: `<span class="sp-fixt-time">${esc(m.time)} ${tzSuffix}</span>`, wat };
}
function fixtureRowFor(lg, m){
  const t = leagueTimeInfo(lg, m);
  const tv = m.tv ? `<span class="sp-tv${(m.tv || '').toLowerCase().indexOf('tnt') > -1 ? ' tnt' : ''}">${esc(m.tv)}</span>` : '';
  const dayM = (m.dayLabel || '').match(/^(\w+)\s+(\d{1,2})\s+(\w+)(?:\s+(\d{4}))?/);
  const day = dayM ? esc(dayM[1] + ' ' + dayM[2] + ' ' + dayM[3]) + `<span class="sp-std">${esc(dayM[4] ? ' ' + dayM[4] : '')}</span>` : esc(m.dayLabel || m.date);
  const urlM = '/sports/' + lg.slug + '/matches/' + m.id + '-vs-' + m.away + '/';
  return `<div class="sp-fixture" aria-label="${esc(m.homeName)} v ${esc(m.awayName)}">
      <div class="sp-fixt"><span class="sp-fixt-day">${day}</span><img src="${lg.crest(m.id)}" alt="" width="22" height="27" loading="lazy"><a href="${url(urlM)}">${esc(m.homeName)}</a><span class="sp-vs">v</span><img src="${lg.crest(m.away)}" alt="" width="22" height="27" loading="lazy"><a href="${url(urlM)}">${esc(m.awayName)}</a></div>
      <div class="sp-fixt-info">${t.display}${t.wat}${tv}<a class="sp-matchlink" href="${url(urlM)}">Match page →</a></div>
    </div>`;
}
function fixturesResults(){
  for (const lg of LEAGUE_FIX) {
    const F = loadLeagueFixtures(lg.slug);
    const mwBlocks = (F.matchweeks || []).map(w => {
      const days = [...new Set(w.matches.map(m => m.dayLabel))];
      return `<section class="sp-mw" id="mw-${w.number}"><div class="sp-mw-head"><h2>${esc(lg.roundLabel)} ${w.number}</h2><span class="sp-mw-date">${esc(days.join(' · '))}</span></div>${w.matches.map(m => fixtureRowFor(lg, m)).join('')}</section>`;
    }).join('');
    const total = (F.matchweeks || []).reduce((n, w) => n + w.matches.length, 0);
    const crumb = [{name:'Home', path:'/'}, {name:'BRYME Sports', path:'/sports/'}, {name:F.league, path:'/sports/' + lg.slug + '/'}, {name:'Fixtures', path:'/sports/' + lg.slug + '/fixtures/'}];
    const hasTbc = (F.matchweeks || []).some(w => w.matches.some(m => !m.time));
    const body = `<main class="shell"><div class="crumb"><a href="${url('/')}">Home</a> / <a href="${url('/sports/')}">BRYME Sports</a> / <a href="${url('/sports/' + lg.slug + '/')}">${esc(F.league)}</a> / Fixtures</div>
      <section class="hero"><div class="eyebrow">⚽ ${esc(F.league)} · Fixtures</div><h1>${esc(F.league)} Fixtures ${esc(F.season)}</h1><p class="lead">All ${total} fixtures of the ${esc(F.season)} ${esc(F.league)} season. ${F.source ? esc(F.source) : ''} Dates and kick-off times are shown exactly as published — nothing is invented.</p></section>
      <p class="sp-updated">Last updated: ${esc(F.lastUpdated || 'Pending verification')}</p>
      <div class="sp-truth"><b>Truth first.</b><p>This is the official fixture list as published for the ${esc(F.season)} ${esc(F.league)} season. ${F.subjectToChange ? esc(F.subjectToChange) : ''}</p></div>
      <div class="sp-fix-legend">${lg.stdSlot || ''}${hasTbc ? '<b>Time TBC</b> means the league has not yet published the kick-off time for that match — it appears here as soon as it is officially confirmed. ' : ''}${F.kickoffNote ? esc(F.kickoffNote) : ''}</div>
      <nav class="sp-mwnav" aria-label="Jump to round">${(F.matchweeks || []).map(w => `<a href="#mw-${w.number}">${esc(lg.roundLabel.slice(0, 2))} ${w.number}</a>`).join('')}</nav>
      ${mwBlocks}
      ${(F.footnotes && F.footnotes.length) ? `<div class="sp-fix-legend"><b>Fixture notes</b><br>${F.footnotes.map(n => '• ' + esc(n)).join('<br>')}</div>` : ''}
      <section class="sp-source"><h2>Source</h2><p><b>Source:</b> ${esc(F.source || 'Official league fixture release')}${F.sourceUrl ? ` — <a href="${esc(F.sourceUrl)}" rel="nofollow noopener">${esc(new URL(F.sourceUrl).hostname)}</a>` : ''}</p><p class="sp-source-note">Fixtures are summarised in BRYME's own words from official publications. Dates, kick-off times and venues are only listed as published; changes announced officially are reflected as soon as BRYME verifies them. Results are never shown before a match is played.</p></section>
      <section class="sp-related"><h2>Related</h2><div class="sp-rel-grid"><a class="sp-rel" href="${url('/sports/' + lg.slug + '/results/')}">Results</a><a class="sp-rel" href="${url('/sports/' + lg.slug + '/matches/')}">Match Centre</a><a class="sp-rel" href="${url('/sports/transfers/' + lg.slug + '-2026-27/')}">Transfers</a><a class="sp-rel" href="${url('/sports/')}">BRYME Sports</a></div></section></main>`;
    write('sports/' + lg.slug + '/fixtures', layout({ title: `${F.league} Fixtures ${F.season}: All ${total} Matches`, description: `Complete ${F.league} ${F.season} fixture list — all ${total} matches across ${(F.matchweeks || []).length} rounds with dates and kick-off times from the official release. Nothing invented.`, path: '/sports/' + lg.slug + '/fixtures/', activeNav: 'sports', schema: [{ '@context':'https://schema.org', '@type':'CollectionPage', name: `${F.league} Fixtures ${F.season}`, description: `All ${total} ${F.league} ${F.season} fixtures as published.`, url: absUrl('/sports/' + lg.slug + '/fixtures/') }, breadcrumbs(crumb)], body }));

    // ---- results page (honest empty state + next round preview) ----
    const mw1 = (F.matchweeks && F.matchweeks[0] && F.matchweeks[0].matches) || [];
    const nextBlock = mw1.length ? `<h3 class="sp-dir">Upcoming — ${esc(lg.roundLabel)} 1 (${esc([...new Set(mw1.map(m => m.dayLabel))].join(' · '))})</h3><div class="sp-table-wrap"><table class="sp-table"><thead><tr><th>Date</th><th>Fixture</th><th>Kickoff</th><th>TV</th></tr></thead><tbody>${mw1.map(m => `<tr><td>${esc(m.dayLabel)}</td><td><b>${esc(m.homeName)}</b> v <b>${esc(m.awayName)}</b></td><td>${m.time ? esc(m.time + (lg.timeSuffix || ' local')) : 'TBC'}</td><td>${esc(m.tv || '—')}</td></tr>`).join('')}</tbody></table></div>` : '';
    const crumbR = [{name:'Home', path:'/'}, {name:'BRYME Sports', path:'/sports/'}, {name:F.league, path:'/sports/' + lg.slug + '/'}, {name:'Results', path:'/sports/' + lg.slug + '/results/'}];
    const bodyR = `<main class="shell"><div class="crumb"><a href="${url('/')}">Home</a> / <a href="${url('/sports/')}">BRYME Sports</a> / <a href="${url('/sports/' + lg.slug + '/')}">${esc(F.league)}</a> / Results</div>
      <section class="hero"><div class="eyebrow">⚽ ${esc(F.league)} · Results</div><h1>${esc(F.league)} Results ${esc(F.season)}</h1><p class="lead">Completed ${esc(F.league)} match results. Results appear only after matches are actually played and officially confirmed — never predicted or assumed.</p></section>
      <p class="sp-updated">Last updated: ${esc(F.lastUpdated || 'Pending verification')}</p>
      ${(() => {
        /* Played matches, newest round first. Driven entirely by content/results.json,
           so this page fills itself in as results are added - no separate edit needed. */
        const rows = [];
        (F.matchweeks || []).forEach(w => w.matches.forEach(m => {
          const r = resultFor(lg.slug, m.id + '-vs-' + m.away);
          if (r) rows.push({ w, m, r });
        }));
        if (!rows.length) return `<div class="vstate"><b>No matches played yet</b><p>The ${esc(F.season)} ${esc(F.league)} season ${(F.matchweeks && F.matchweeks[0] && F.matchweeks[0].matches[0]) ? 'starts ' + esc(F.matchweeks[0].matches[0].dayLabel) : 'has not started'} — so as of ${esc(F.lastUpdated || 'today')} no league fixtures have been played and there are no results to show. When matches are played, the official result and match data are added here after full-time — verified only.</p></div>`;
        rows.reverse();
        return `<h3 class="sp-dir">Results — ${rows.length} match${rows.length === 1 ? '' : 'es'} played</h3>
        <div class="sp-table-wrap"><table class="sp-table"><thead><tr><th>Round</th><th>Match</th><th>Score</th><th>Source</th></tr></thead><tbody>${rows.map(({w, m, r}) => `<tr><td>${esc(lg.roundLabel)} ${w.number}</td><td><a href="${url('/sports/' + lg.slug + '/matches/' + m.id + '-vs-' + m.away + '/')}">${esc(m.homeName)} v ${esc(m.awayName)}</a></td><td><b>${r.homeScore}&ndash;${r.awayScore}</b>${r.status && r.status !== 'FT' ? ` <span class="sp-pens">${esc(r.status)}</span>` : ''}</td><td><a href="${esc(r.source.url)}" rel="nofollow noopener">${esc(r.source.name || 'source')}</a></td></tr>`).join('')}</tbody></table></div>`;
      })()}
      ${nextBlock}
      <div class="sp-truth"><b>Truth first.</b><p>BRYME never publishes a result, scoreline or scorer before a match is played and the outcome is confirmed by the club or official league channels. If a result cannot be verified, it is not shown.</p></div>
      <section class="sp-related"><h2>Related</h2><div class="sp-rel-grid"><a class="sp-rel" href="${url('/sports/' + lg.slug + '/fixtures/')}">Fixtures</a><a class="sp-rel" href="${url('/sports/' + lg.slug + '/matches/')}">Match Centre</a><a class="sp-rel" href="${url('/sports/transfers/' + lg.slug + '-2026-27/')}">Transfers</a></div></section></main>`;
    write('sports/' + lg.slug + '/results', layout({ title: `${F.league} Results ${F.season}`, description: `${F.league} ${F.season} results — only official, verified match results after matches are played. No results are predicted or assumed.`, path: '/sports/' + lg.slug + '/results/', activeNav: 'sports', schema: [{ '@context':'https://schema.org', '@type':'CollectionPage', name: `${F.league} Results ${F.season}`, url: absUrl('/sports/' + lg.slug + '/results/') }, breadcrumbs(crumbR)], body: bodyR }));
  }
}

/* --- match centre + per-match pages (all five leagues) --- */
const MW1_REVIEW_PATH = path.join(root, 'content', 'premier-league-matchweek-1-analysis.json');
const MW1_REVIEW = fs.existsSync(MW1_REVIEW_PATH) ? JSON.parse(fs.readFileSync(MW1_REVIEW_PATH, 'utf8')).matches || {} : {};
/* ================================================================
   MATCH RESULTS — content/results.json is the single source of truth for
   what has actually been played. A fixture with no entry here is unplayed:
   it renders as a fixture, stays noindex and stays out of the sitemap.
   The moment a sourced result is added the page gains real content and
   becomes indexable automatically.

   A result is only published if it carries a source with a url. An
   unsourced result is refused and reported, never rendered - the site
   must never show a scoreline it cannot attribute.
   ================================================================ */
const RESULTS = (() => {
  const f = path.join(root, 'content', 'results.json');
  if (!fs.existsSync(f)) return {};
  try { return JSON.parse(fs.readFileSync(f, 'utf8')); } catch (e) { return {}; }
})();
const REJECTED_RESULTS = [];
function resultFor(leagueSlug, matchSlug){
  const r = ((RESULTS[leagueSlug] || {})[matchSlug]);
  if (!r) return null;
  const scored = Number.isInteger(r.homeScore) && Number.isInteger(r.awayScore);
  const sourced = r.source && r.source.url;
  if (!scored || !sourced) {
    REJECTED_RESULTS.push(`${leagueSlug}/${matchSlug}: ${!scored ? 'homeScore/awayScore must be integers' : 'missing source.url'}`);
    return null;
  }
  return r;
}
function resultBlock(m, r){
  const st = esc(r.status || 'FT');
  const pens = r.status === 'FT (pens)' && r.penalties ? ` <span class="sp-pens">(${esc(r.penalties)} on penalties)</span>` : '';
  const goals = Array.isArray(r.scorers) && r.scorers.length
    ? `<div class="sp-scorers"><div><b>${esc(m.homeName)}</b><ul>${r.scorers.filter(g => g.team === 'home').map(g => `<li>${esc(g.player)}${g.minute ? ` <span>${esc(String(g.minute))}'</span>` : ''}</li>`).join('') || '<li class="sp-none">—</li>'}</ul></div><div><b>${esc(m.awayName)}</b><ul>${r.scorers.filter(g => g.team === 'away').map(g => `<li>${esc(g.player)}${g.minute ? ` <span>${esc(String(g.minute))}'</span>` : ''}</li>`).join('') || '<li class="sp-none">—</li>'}</ul></div></div>`
    : '';
  const extra = [r.attendance ? `Attendance ${esc(String(r.attendance))}` : '', r.playedOn ? `Played ${esc(r.playedOn)}` : ''].filter(Boolean).join(' · ');
  return `<div class="sp-result"><span class="sp-pill sp-pill-ft">${st}</span>
    <div class="sp-score"><span>${esc(m.homeName)}</span><b>${r.homeScore}</b><i>&ndash;</i><b>${r.awayScore}</b><span>${esc(m.awayName)}</span></div>${pens}
    ${extra ? `<p class="sp-result-meta">${extra}</p>` : ''}${goals}
    <p class="sp-source-note">Result confirmed via <a href="${esc(r.source.url)}" rel="nofollow noopener">${esc(r.source.name || r.source.url)}</a>${r.verifiedOn ? ` · checked ${esc(r.verifiedOn)}` : ''}.</p></div>`;
}

/* Match pages can point at BRYME articles that genuinely bear on the fixture - a
   manager's first game, a promoted club's route up. Declared per fixture in
   match-editorial.json as "relatedArticles": ["<slug>"], resolved against the published
   sports articles so a typo or an unpublished draft produces nothing rather than a 404. */
/* --- Empty (un-played, not-yet-researched) match page panel ---
   Instead of printing 16 near-identical "Pending verification" cards (which made
   the page read as a repeated template and bloated the HTML that a crawler has to
   chew through), an un-researched fixture gets ONE honest panel: it confirms the
   fixture facts BRYME actually knows from the official calendar and says plainly
   that analysis will be added with verified data. Factual, non-repetitive, and
   it will no longer bury genuinely-researched pages under template noise. */
function emptyMatchPanel(m, lg, F, t, v){
  const known = [];
  if (m.dayLabel) known.push(`<b>Date:</b> ${esc(m.dayLabel)}`);
  if (m.time) known.push(`<b>Kickoff:</b> ${esc(t.display.replace(/<[^>]+>/g, ''))}`);
  if (m.tv) known.push(`<b>TV:</b> ${esc(m.tv)}`);
  if (v && v.name) known.push(`<b>Venue:</b> ${esc(v.name)}`);
  return `<div class="sp-empty-panel">
    <span class="sp-pend">Analysis in progress</span>
    <b>This fixture is scheduled, not yet covered.</b>
    <p>BRYME will research ${esc(m.homeName)} v ${esc(m.awayName)} before kickoff and fill this page with verified data only — form, head-to-head, team news, lineups and a prediction — never predicted or fabricated. Until then, the officially published details are: ${known.length ? known.join(' · ') : 'date to be confirmed by the league'}.</p>
    <p class="sp-empty-note">Match result and post-match analysis appear only after full-time, once the outcome is officially confirmed.</p>
  </div>`;
}
function relatedArticleCards(ed){
  if (!ed || !Array.isArray(ed.relatedArticles) || !ed.relatedArticles.length) return '';
  const pool = (VERTICAL_ARTICLES.sports || []).filter(a => a.status === 'published');
  const cards = ed.relatedArticles.map(slug => {
    const a = pool.find(x => x.slug === slug);
    if (!a) return '';
    return `<a class="sp-artcard" href="${url(articlePathFor('sports', a))}">
      <span class="sp-artcard-kicker">BRYME analysis</span>
      <b>${esc(a.title)}</b>
      ${a.description ? `<span>${esc(clip(a.description, 130))}</span>` : ''}</a>`;
  }).filter(Boolean).join('');
  if (!cards) return '';
  return `<section class="sp-related sp-artrel"><h2>Related reading</h2><div class="sp-artgrid">${cards}</div></section>`;
}

function matchCentre(){
  for (const lg of LEAGUE_FIX) {
    const F = loadLeagueFixtures(lg.slug);
    const venueOf = (m) => {
      const v = (F.venues || {})[m.id] || {};
      const name = m.venue || v.name || null;
      const cap = v.capacity;
      return { name, cap };
    };
    const slug = m => m.id + '-vs-' + m.away;
    const matchUrl = m => '/sports/' + lg.slug + '/matches/' + slug(m) + '/';
    // --- per-match pages ---
    (F.matchweeks || []).forEach(w => w.matches.forEach(m => {
      const v = venueOf(m);
      const RES = resultFor(lg.slug, slug(m));
      const matchPlayed = !!RES;
      const ED = editorialFor(lg.slug, slug(m));
      /* Indexable once it is a real editorial page (preview written) or the match has a
         sourced result. Otherwise it stays a schedule entry: noindex, no sitemap. */
      const isEditorial = !!(ED || RES);
      if (!isEditorial) UNPLAYED_MATCH_PATHS.add(matchUrl(m));
      const datePublished = isoDate((ED && ED.publishedAt) || (RES && RES.playedOn), matchUrl(m) + ' datePublished');
      const dateModified = isoDate((RES && (RES.verifiedOn || RES.playedOn))
        || (ED && ED.postMatch && ED.postMatch.publishedAt)
        || (ED && (ED.updatedAt || ED.publishedAt)), matchUrl(m) + ' dateModified');
      if (isEditorial && dateModified) PAGE_LASTMOD.set(matchUrl(m), dateModified);
      const t = leagueTimeInfo(lg, m);
      let sections = (S.matchCentre.matchPageSections || []).map(s => {
        const isPost = /result after the game|post-match/i.test(s);
        return `<div class="sp-msec"><span class="sp-pend">${isPost ? 'After full-time' : 'Pending verification'}</span><b>${esc(s)}</b><p>${isPost ? 'This section is written after the match, once the result is officially confirmed.' : 'Filled in with verified data only — never predicted or fabricated.'}</p></div>`;
      }).join('');
      const reviewKey = m.id + '-vs-' + m.away;
      const review = MW1_REVIEW[reviewKey];
      if (review) {
        const base = [['Match overview',review.overview],['Recent form',review.form],['Head-to-head record','Historical and head-to-head context is included in the supplied editorial review and requires final source checking before publication.'],['Last five meetings','Recent-meeting context requires official-record verification before publication.'],['Home/away form','Home and away form context is included in the supplied editorial review and is subject to final verification.'],['Key players',review.context],['Injuries',review.injuries],['Suspensions','None reported in the supplied 14 August snapshot; reconfirm before kick-off.'],['Expected lineups','Provisional only. Recheck official team news before kick-off.'],['Tactical matchup',review.tactics],['Historical context',review.context],['Underdog discussion',review.context],['BRYME editorial outlook',review.outlook],['Editorial score prediction','BRYME editorial prediction: ' + review.prediction],['Match result after the game','Pending — complete only after the officially confirmed result.'],['Post-match analysis','Pending — complete with verified information after the match.']];
        sections = base.map(x => { const post = /result after the game|post-match/i.test(x[0]); return `<div class="sp-msec"><span class="sp-pend">${post ? 'After full-time' : 'Editorial review · 14 Aug 2026'}</span><b>${esc(x[0])}</b><p>${esc(x[1])}</p></div>`; }).join('');
      }
      const crumbs = [{name:'Home', path:'/'}, {name:'BRYME Sports', path:'/sports/'}, {name:F.league, path:'/sports/' + lg.slug + '/'}, {name:'Match Centre', path:'/sports/' + lg.slug + '/matches/'}, {name:m.homeName + ' v ' + m.awayName, path: matchUrl(m)}];
      const body = `<main class="shell"><div class="crumb"><a href="${url('/')}">Home</a> / <a href="${url('/sports/')}">BRYME Sports</a> / <a href="${url('/sports/' + lg.slug + '/')}">${esc(F.league)}</a> / <a href="${url('/sports/' + lg.slug + '/matches/')}">Match Centre</a> / ${esc(m.homeName)} v ${esc(m.awayName)}</div>
        <section class="hero"><div class="eyebrow">⚽ ${esc(F.league)} ${esc(F.season)} · ${esc(lg.roundLabel)} ${w.number}</div><span class="visually-hidden">${esc(m.homeName)} v ${esc(m.awayName)}</span></section>
        <div class="sp-match-hero"><img src="${lg.crest(m.id)}" alt="${lg.alt(m.id, m.homeName)}" width="64" height="77"><span class="sp-mh-vs">v</span><img src="${lg.crest(m.away)}" alt="${lg.alt(m.away, m.awayName)}" width="64" height="77"><div>${RES ? `<span class="sp-pill sp-pill-ft">${esc(RES.status || 'FT')} ${RES.homeScore}&ndash;${RES.awayScore}</span>` : `<span class="sp-pill">Upcoming — not yet played</span>`}<h1 style="margin-top:6px">${esc(m.homeName)} v ${esc(m.awayName)}</h1><p class="sp-match-meta"><span><b>Date:</b> ${esc(m.dayLabel)}</span><span><b>Kickoff:</b> ${m.time ? esc(t.display.replace(/<[^>]+>/g, '')) + (t.wat ? esc(t.wat.replace(/<[^>]+>/g, '')) : '') : 'TBC — announced closer to the round'}</span>${m.tv ? `<span><b>TV:</b> ${esc(m.tv)}</span>` : ''}<span><b>Venue:</b> ${esc(v.name || 'TBC')}${v.cap ? ' · ' + esc(Number(v.cap).toLocaleString('en-GB')) : ''}</span></p>${m.note ? `<p class="sp-match-meta" style="margin-top:6px"><b>Note:</b> ${esc(m.note)}</p>` : ''}</div></div>
        ${RES ? resultBlock(m, RES) : (ED ? '' : `<div class="sp-truth"><b>Truth first.</b><p>This match has not been played yet — there is no result, scoreline, lineup or statistic to report. Pre-match research below is an editorial review snapshot from 14 August 2026. Team news and expected lineups are provisional and must be rechecked close to kickoff. Match result and post-match analysis remain blank until official confirmation.</p></div>`)}
        ${(!RES && ED) ? `<div class="sp-truth"><b>Preview — not yet played.</b><p>This match has not been played. Everything below is pre-match editorial published on ${esc(ED.publishedAt || '')}; there is no result, lineup or statistic to report yet. Team news is only shown where a club or official source has confirmed it.</p></div>` : ''}
        ${(RES && ED && ED.postMatch) ? postMatchBlock(ED.postMatch) : ''}
        ${ED ? previewBlock(ED, {past: !!RES}) : ''}
        ${ED ? '' : emptyMatchPanel(m, lg, F, t, v)}
        ${relatedArticleCards(ED)}
        <section class="sp-related"><h2>Related</h2><div class="sp-rel-grid"><a class="sp-rel" href="${url('/sports/' + lg.slug + '/fixtures/')}">Fixtures</a><a class="sp-rel" href="${url('/sports/' + lg.slug + '/results/')}">Results</a><a class="sp-rel" href="${url('/sports/' + lg.slug + '/matches/')}">Match Centre</a><a class="sp-rel" href="${url('/sports/')}">BRYME Sports</a></div></section></main>`;
      let startDate;
      const off = lg.slug === 'premier-league' ? (euDstOffset(m.date) - 1) : euDstOffset(m.date);
      if (m.time) {
        startDate = m.date + 'T' + m.time + ':00' + (off === 2 ? '+02:00' : off === 1 ? '+01:00' : '+00:00');
      } else {
        startDate = m.date;
      }
      /* A fixture that has not been played has no result, lineup or statistic to report: ~366 words
         of which all but roughly one sentence is template shared with every other fixture page.
         Submitting ~1,750 of those to Google buries the pages that do carry unique content and
         invites "Crawled - currently not indexed" across the whole site. So an unplayed fixture is
         kept for readers (kickoff time, venue, pre-match notes) but marked noindex,follow and left
         out of sitemap.xml. It becomes indexable automatically once it carries a real result. */
      write('sports/' + lg.slug + '/matches/' + slug(m), layout({
        noindex: !isEditorial,
        title: RES
          ? `${m.homeName} ${RES.homeScore}-${RES.awayScore} ${m.awayName} — Result & Analysis · ${F.league} ${F.season}`
          : (ED ? `${m.homeName} v ${m.awayName} — Preview, Form & Prediction · ${lg.roundLabel} ${w.number} · ${F.league}`
                : `${m.homeName} v ${m.awayName} — ${lg.roundLabel} ${w.number} · ${F.league} ${F.season}`),
        description: RES
          ? `${m.homeName} ${RES.homeScore}-${RES.awayScore} ${m.awayName}: full-time result, goalscorers and BRYME post-match analysis from ${F.league} ${lg.roundLabel} ${w.number}, ${F.season}.`
          : (ED ? `${m.homeName} v ${m.awayName} preview: form, head-to-head, tactical matchup and BRYME's editorial prediction for ${F.league} ${lg.roundLabel} ${w.number}${m.time ? `, kick-off ${m.time}` : ''}.`
                : `${m.homeName} v ${m.awayName}, ${F.season} ${F.league} ${lg.roundLabel} ${w.number} — ${m.dayLabel}${m.time ? ', ' + m.time + ' local' : ', kickoff TBC'}${v.name ? ' at ' + v.name : ''}. Match analysis sections appear once verified; no results are predicted.`),
        path: matchUrl(m), activeNav: 'sports',
        schema: (() => {
          const ev = [{ '@context':'https://schema.org', '@type':'SportsEvent', name: m.homeName + ' v ' + m.awayName, startDate, eventStatus: 'https://schema.org/EventScheduled', eventAttendanceMode: 'https://schema.org/OfflineEventAttendanceMode', location: v.name ? { '@type':'Place', name: v.name } : undefined, homeTeam: { '@type':'SportsTeam', name: m.homeName }, awayTeam: { '@type':'SportsTeam', name: m.awayName }, url: absUrl(matchUrl(m)) }, breadcrumbs(crumbs)];
          const sportsEvent = ev[0];
          if (RES) {
            sportsEvent.eventStatus = 'https://schema.org/EventScheduled';
            sportsEvent.homeTeam = { '@type':'SportsTeam', name: m.homeName };
            sportsEvent.awayTeam = { '@type':'SportsTeam', name: m.awayName };
          }
          if (isEditorial) {
            /* the editorial write-up itself, so datePublished/dateModified are expressed */
            ev.push({
              '@context':'https://schema.org', '@type':'Article',
              headline: RES ? `${m.homeName} ${RES.homeScore}-${RES.awayScore} ${m.awayName}: result and analysis`
                            : `${m.homeName} v ${m.awayName}: preview and prediction`,
              datePublished: datePublished || undefined,
              dateModified: dateModified || datePublished || undefined,
              author: { '@type':'Organization', name: 'BRYME Sports' },
              publisher: { '@type':'Organization', name: site.name },
              mainEntityOfPage: absUrl(matchUrl(m)),
              articleSection: F.league
            });
          }
          return ev;
        })(),
        body
      }));
      LEAGUE_MATCH_PATHS.push(matchUrl(m));
    }));
    // --- match centre hub ---
    const mw1 = (F.matchweeks && F.matchweeks[0]) || { number: 1, matches: [] };
    const heroImg = url('/assets/img/sports/hero-' + lg.slug + '.jpg');
    const cards = mw1.matches.map((m, i) => {
      const t = leagueTimeInfo(lg, m);
      const timeStr = m.time ? esc(t.display.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()) : 'Time TBC';
      const tv = m.tv ? ' · ' + esc(m.tv) : '';
      return `<a class="sp-hero-card${i === 0 ? ' sp-hero-first' : ''}" href="${url(matchUrl(m))}" style="--card-img:url('${heroImg}')">
        <span class="sp-hero-crests"><img src="${lg.crest(m.id)}" alt="" width="26" height="32" loading="lazy"><b>v</b><img src="${lg.crest(m.away)}" alt="" width="26" height="32" loading="lazy"></span>
        <span class="sp-hero-tag">${esc(lg.roundLabel)} ${mw1.number} · ${timeStr}</span>
        <h3>${esc(m.homeName)} v ${esc(m.awayName)}</h3>
        <p>${esc(m.dayLabel)}${tv}</p>
        <span class="sp-hero-go">Match page →</span>
      </a>`;
    }).join('');
    const crumbs = [{name:'Home', path:'/'}, {name:'BRYME Sports', path:'/sports/'}, {name:F.league, path:'/sports/' + lg.slug + '/'}, {name:'Match Centre', path:'/sports/' + lg.slug + '/matches/'}];
    const total = (F.matchweeks || []).reduce((n, w) => n + w.matches.length, 0);
    const body = `<main class="shell"><div class="crumb"><a href="${url('/')}">Home</a> / <a href="${url('/sports/')}">BRYME Sports</a> / <a href="${url('/sports/' + lg.slug + '/')}">${esc(F.league)}</a> / Match Centre</div>
      <section class="hero"><div class="eyebrow">⚽ ${esc(F.league)} · Match Centre</div><h1>${esc(F.league)} ${esc(lg.roundLabel)} ${mw1.number}</h1><p class="lead">${esc(lg.roundLabel)} ${mw1.number} fixtures with dates and kick-off times from the official ${esc(F.league)} calendar. Every one of the ${total} matches in the ${esc(F.season)} season has its own match page.</p></section>
      <p class="sp-updated">Last updated: ${esc(F.lastUpdated || 'Pending verification')}</p>
      <div class="sp-truth"><b>Truth first.</b><p>Every fixture has its own match page with the officially published date${(F.matchweeks || []).some(w => w.matches.some(x => x.time)) ? ' and kick-off time' : ''}. Match analysis sections (lineups, injuries, form, result, post-match) are filled in only with verified data — never predicted or fabricated.</p></div>
      <h3 class="sp-dir">${esc(lg.roundLabel)} ${mw1.number} — ${esc([...new Set(mw1.matches.map(x => x.dayLabel))].join(' · '))}</h3>
      <section class="sp-hero" aria-label="${esc(F.league)} ${esc(lg.roundLabel)} ${mw1.number} fixtures"><div class="sp-hero-track">${cards}</div><button type="button" class="sp-hero-arrow sp-hero-prev" data-sp-hero-prev aria-label="Previous card">‹</button><button type="button" class="sp-hero-arrow sp-hero-next" data-sp-hero-next aria-label="Next card">›</button></section>
      <p class="sp-freq-note">Looking for the whole season? See <a href="${url('/sports/' + lg.slug + '/fixtures/')}">all ${total} fixtures across ${(F.matchweeks || []).length} rounds</a>.</p>
      <section class="sp-related"><h2>Match page sections</h2><p class="sp-source-note">Every match gets its own analysis page at /sports/${lg.slug}/matches/[team-a]-vs-[team-b]/ with:</p><div class="sp-rel-grid">${S.matchCentre.matchPageSections.map(s => `<span class="sp-rel sp-rel-static">${esc(s)}</span>`).join('')}</div></section>
      <section class="sp-related"><h2>Related</h2><div class="sp-rel-grid"><a class="sp-rel" href="${url('/sports/' + lg.slug + '/fixtures/')}">Fixtures</a><a class="sp-rel" href="${url('/sports/' + lg.slug + '/results/')}">Results</a><a class="sp-rel" href="${url('/sports/transfers/' + lg.slug + '-2026-27/')}">Transfers</a><a class="sp-rel" href="${url('/sports/')}">BRYME Sports</a></div></section></main>`;
    write('sports/' + lg.slug + '/matches', layout({ title: `${F.league} ${lg.roundLabel} ${mw1.number}`, description: `${F.league} ${lg.roundLabel} ${mw1.number} — fixtures, kick-off times and match pages. All ${total} matches of the ${F.season} season have their own page; analysis sections fill in with verified data only.`, path: '/sports/' + lg.slug + '/matches/', activeNav: 'sports', schema: [{ '@context':'https://schema.org', '@type':'CollectionPage', name: `${F.league} ${lg.roundLabel} ${mw1.number}`, url: absUrl('/sports/' + lg.slug + '/matches/') }, breadcrumbs(crumbs)], body }));
  }
}

/* --- PL hub: hero carousel + links --- */
function plHub(){
  const heroCards = (S.hero.cards || []).map((c, i) => `<a class="sp-hero-card${i === 0 ? ' sp-hero-first' : ''}" href="${url(c.route + '/')}" style="--card-img:url('${url('/assets/img/sports/' + (c.img || 'hero-matchweek.jpg'))}')"><span class="sp-hero-tag">${esc(c.tag)}</span><h3>${esc(c.title)}</h3><p>${esc(c.desc)}</p><span class="sp-hero-go">Read →</span></a>`).join('');
  const crumbs = [{name:'Home', path:'/'}, {name:'BRYME Sports', path:'/sports/'}, {name:'Premier League', path:'/sports/premier-league/'}];
  const body = `<main class="shell"><div class="crumb"><a href="${url('/')}">Home</a> / <a href="${url('/sports/')}">BRYME Sports</a> / Premier League</div>
    <section class="sp-pl-hero"><div class="eyebrow">⚽ Premier League · ${SEASON}</div><h1>${esc(S.hero.kicker)}</h1><p class="lead">${esc(S.hero.subtitle)}</p></section>
    <section class="sp-hero" aria-label="Premier League matchweek ${MW} highlights"><div class="sp-hero-track">${heroCards}</div><button type="button" class="sp-hero-arrow sp-hero-prev" data-sp-hero-prev aria-label="Previous card">‹</button><button type="button" class="sp-hero-arrow sp-hero-next" data-sp-hero-next aria-label="Next card">›</button></section>
    <section class="section"><div class="section-head"><h2>Matchweek ${MW} hub</h2></div><div class="vcat-grid">
      <a class="vcat" href="${url('/sports/premier-league/matches/')}"><b>Match Centre</b><span>Matchweek ${MW} fixtures and match analysis</span></a>
      <a class="vcat" href="${url('/sports/premier-league/fixtures/')}"><b>Fixtures</b><span>${leagueFixturesSummary('premier-league').total} fixtures across ${leagueFixturesSummary('premier-league').rounds} rounds — dates &amp; kickoffs</span></a>
      <a class="vcat" href="${url('/sports/premier-league/results/')}"><b>Results</b><span>${resultCountFor('premier-league')}</span></a>
      <a class="vcat" href="${url('/sports/premier-league/table/')}"><b>Table</b><span>Editorial prediction + official table later</span></a>
      <a class="vcat" href="${url('/sports/fpl/')}"><b>FPL</b><span>Fantasy Premier League coverage</span></a>
      <a class="vcat" href="${url('/sports/transfers/premier-league-2026-27/')}"><b>Transfers</b><span>${transferBlurb('premier-league', 'Premier League')}</span></a>
    </div></section>
    <section class="sp-related"><h2>Related</h2><div class="sp-rel-grid"><a class="sp-rel" href="${url('/sports/transfers/')}">All transfer trackers</a><a class="sp-rel" href="${url('/sports/managers-2026-27/')}">Managers In &amp; Out</a><a class="sp-rel" href="${url('/sports/')}">BRYME Sports</a></div></section></main>`;
  write('sports/premier-league', layout({ title: 'Premier League ' + SEASON + ' | BRYME Sports', description: S.hero.kicker + ' — ' + S.hero.subtitle + ' Matchweek ' + MW + ' previews, transfers, FPL, injuries, fixtures, results and the BRYME editorial table prediction.', path: '/sports/premier-league/', activeNav: 'sports', schema: [{ '@context':'https://schema.org', '@type':'CollectionPage', name: 'Premier League ' + SEASON, url: absUrl('/sports/premier-league/') }, breadcrumbs(crumbs)], body }));
}
/* --- league hub pages (La Liga, Serie A, Bundesliga, Ligue 1) — PL-style hero fixture cards --- */
function leagueHub(){
  for (const lg of LEAGUE_FIX.filter(l => l.slug !== 'premier-league')) {
    const F = loadLeagueFixtures(lg.slug);
    const mw1 = (F.matchweeks && F.matchweeks[0]) || { number: 1, matches: [] };
    const heroImg = url('/assets/img/sports/hero-' + lg.slug + '.jpg');
    const card = (m, i) => {
      const t = leagueTimeInfo(lg, m);
      const urlM = '/sports/' + lg.slug + '/matches/' + m.id + '-vs-' + m.away + '/';
      const timeStr = m.time ? esc(t.display.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()) : 'Time TBC';
      const tv = m.tv ? ' · ' + esc(m.tv) : '';
      return `<a class="sp-hero-card${i === 0 ? ' sp-hero-first' : ''}" href="${url(urlM)}" style="--card-img:url('${heroImg}')">
        <span class="sp-hero-crests"><img src="${lg.crest(m.id)}" alt="" width="26" height="32" loading="lazy"><b>v</b><img src="${lg.crest(m.away)}" alt="" width="26" height="32" loading="lazy"></span>
        <span class="sp-hero-tag">${esc(lg.roundLabel)} ${mw1.number} · ${timeStr}</span>
        <h3>${esc(m.homeName)} v ${esc(m.awayName)}</h3>
        <p>${esc(m.dayLabel)}${m.venue ? ' · ' + esc(m.venue) : ''}${tv}</p>
        <span class="sp-hero-go">Match page →</span>
      </a>`;
    };
    const cards = mw1.matches.map(card).join('');
    const total = (F.matchweeks || []).reduce((n, w) => n + w.matches.length, 0);
    const rounds = (F.matchweeks || []).length;
    const kicker = F.league + ' ' + F.season;
    const subtitle = F.league + ' ' + F.season + ' — all ' + total + ' fixtures across ' + rounds + ' rounds from the official calendar. Every match has its own page with the officially published date' + ((F.matchweeks || []).some(w => w.matches.some(x => x.time)) ? ' and kick-off time' : '') + '.';
    const crumbs = [{name:'Home', path:'/'}, {name:'BRYME Sports', path:'/sports/'}, {name:F.league, path:'/sports/' + lg.slug + '/'}];
    const body = `<main class="shell"><div class="crumb"><a href="${url('/')}">Home</a> / <a href="${url('/sports/')}">BRYME Sports</a> / ${esc(F.league)}</div>
      <section class="sp-pl-hero"><div class="eyebrow">⚽ ${esc(F.league)} · ${esc(F.season)}</div><h1>${esc(kicker)}</h1><p class="lead">${esc(subtitle)}</p></section>
      <section class="sp-hero" aria-label="${esc(F.league)} ${esc(lg.roundLabel)} ${mw1.number} fixtures"><div class="sp-hero-track">${cards}</div><button type="button" class="sp-hero-arrow sp-hero-prev" data-sp-hero-prev aria-label="Previous card">‹</button><button type="button" class="sp-hero-arrow sp-hero-next" data-sp-hero-next aria-label="Next card">›</button></section>
      <section class="section"><div class="section-head"><h2>${esc(lg.roundLabel)} ${mw1.number} hub</h2></div><div class="vcat-grid">
        <a class="vcat" href="${url('/sports/' + lg.slug + '/matches/')}"><b>Match Centre</b><span>${esc(lg.roundLabel)} ${mw1.number} fixtures and match analysis</span></a>
        <a class="vcat" href="${url('/sports/' + lg.slug + '/fixtures/')}"><b>Fixtures</b><span>All ${total} fixtures — dates, kickoffs &amp; match pages</span></a>
        <a class="vcat" href="${url('/sports/' + lg.slug + '/results/')}"><b>Results</b><span>${resultCountFor(lg.slug)}</span></a>
        <a class="vcat" href="${url('/sports/transfers/' + lg.slug + '-2026-27/')}"><b>Transfers</b><span>${transferBlurb(lg.slug, F.league)}</span></a>
        <a class="vcat" href="${url('/sports/managers-2026-27/')}"><b>Managers</b><span>${managerBlurb(lg.slug, F.season)}</span></a>
      </div></section>
      <section class="sp-related"><h2>Related</h2><div class="sp-rel-grid"><a class="sp-rel" href="${url('/sports/transfers/')}">All transfer trackers</a><a class="sp-rel" href="${url('/sports/managers-2026-27/')}">Managers In &amp; Out</a><a class="sp-rel" href="${url('/sports/')}">BRYME Sports</a></div></section></main>`;
    write('sports/' + lg.slug, layout({
      title: `${F.league} ${F.season}`,
      description: `${kicker} — ${F.league} ${F.season} ${lg.roundLabel} ${mw1.number} fixtures, ${total} matches across ${rounds} rounds, transfers, results and match pages from the official calendar.`,
      path: '/sports/' + lg.slug + '/', activeNav: 'sports',
      schema: [{ '@context':'https://schema.org', '@type':'CollectionPage', name: `${F.league} ${F.season}`, url: absUrl('/sports/' + lg.slug + '/') }, breadcrumbs(crumbs)],
      body
    }));
  }
}

/* --- full Premier League transfer tracker (20 clubs) --- */
function buildPlTransferTracker(){
  const plPath = path.join(root, 'content', 'pl-transfers.json');
  let pl = {};
  if (fs.existsSync(plPath)) { try { pl = JSON.parse(fs.readFileSync(plPath, 'utf8')); } catch (e) { warnings.push('pl-transfers.json unreadable'); } }
  const imgUrl = id => url('/assets/img/sports/pl/' + id + '.svg');
  const statusBadge = t => t === 'Loan' ? 'sp-st-conf' : (t === 'Free' ? 'sp-st-rep' : (t === 'Released' || t === 'Retired' || t === 'Departed' ? 'sp-st-rum' : 'sp-st-conf'));
  const statusLabel = t => t === 'Confirmed' ? 'Confirmed' : t;
  const rows = list => list.length ? list.map(r => `<tr><td><b>${esc(r.player)}</b></td><td>${esc(r.from || r.to || '—')}</td><td>${esc(r.detail)}</td><td><span class="${statusBadge(r.type)}">${esc(statusLabel(r.type))}</span></td></tr>`).join('')
    : `<tr class="sp-empty"><td colspan="4">No confirmed ${esc('')}transfers listed yet — nothing is added before it is officially confirmed.</td></tr>`;
  const clubCard = c => `<article class="sp-club" id="${esc(c.id)}">
    <header class="sp-club-head"><img src="${imgUrl(c.id)}" alt="${esc(c.name)} official club crest" width="64" height="77" loading="lazy"><div><h2>${esc(c.name)}</h2><p class="sp-club-man">Manager: <b>${esc(c.manager)}</b> · ${esc(c.managerNote)}</p></div></header>
    <div class="sp-club-cols">
      <div class="sp-club-col"><h3>Players In</h3><div class="sp-table-wrap"><table class="sp-table"><thead><tr><th>Player</th><th>From</th><th>Transfer type / fee</th><th>Status</th></tr></thead><tbody>${rows(c.playersIn)}</tbody></table></div></div>
      <div class="sp-club-col"><h3>Players Out</h3><div class="sp-table-wrap"><table class="sp-table"><thead><tr><th>Player</th><th>To</th><th>Transfer type / fee</th><th>Status</th></tr></thead><tbody>${rows(c.playersOut)}</tbody></table></div></div>
    </div>
    ${(c.rumours && c.rumours.length) ? `<div class="sp-rumours"><b>Rumour / Reported interest — not confirmed</b>${c.rumours.map(r => `<p>${esc(r)}</p>`).join('')}</div>` : ''}
    ${c.notes ? `<p class="sp-club-notes"><b>Transfer notes.</b> ${esc(c.notes)}</p>` : ''}
  </article>`;
  const crumbs = [{name:'Home', path:'/'}, {name:'BRYME Sports', path:'/sports/'}, {name:'Transfers', path:'/sports/transfers/'}, {name:'Premier League Transfers 2026/27', path:'/sports/transfers/premier-league-2026-27/'}];
  const body = `<main class="shell"><div class="crumb"><a href="${url('/')}">Home</a> / <a href="${url('/sports/')}">BRYME Sports</a> / <a href="${url('/sports/transfers/')}">Transfers</a> / Premier League</div>
    <section class="hero"><div class="eyebrow">⚽ BRYME Sports · Transfers</div><h1>Premier League Transfers ${esc(pl.windowClose ? '2026/27' : '')}</h1></section>
    <div class="sp-live"><span class="sp-live-dot"></span><div><b>LIVE TRANSFER WINDOW</b><p>Premier League 2026/27 Transfers — All Clubs. This page shows the transfers completed by each Premier League club as they stand right now. The transfer window is still open, so players may move clubs, deals may be completed, and squad information may change before the transfer window closes${pl.windowClose ? ' (' + esc(pl.windowClose) + ')' : ''}. BRYME will continue updating this page as new transfers are confirmed.</p></div></div>
    <p class="sp-updated">Last updated: ${esc(pl.lastUpdated || '—')}</p>
    <div class="sp-credits"><b>Club crests</b> © Copyright The Football Association Premier League Limited, 2016. Used under the Premier League Logo Site media licence by BRYME Sports as an editorial sports publication. Crests may be resized for editorial presentation but not altered. BRYME Sports is an independent publication and is not affiliated with, endorsed or sponsored by the Premier League or any club. Other clubs' crests shown here are BRYME-generated abstract illustrations.</div>
    <p class="sp-freq-note">Transfer information changes frequently. This list is updated as new information becomes available and may not include breaking or unannounced developments.</p>
    <nav class="sp-club-nav" aria-label="Jump to club">${(pl.clubs || []).map(c => `<a href="#${esc(c.id)}">${esc(c.name.replace(' &amp; Hove Albion', '').replace('Hotspur', ''))}</a>`).join('')}</nav>
    <div class="sp-clubs">${(pl.clubs || []).map(clubCard).join('')}</div>
    <p class="sp-window-note">Transfer window still open: this page will be updated as new deals are officially confirmed.</p>
    <section class="sp-source"><h2>Sources</h2><p>${(pl.sources || []).map(esc).join(' · ')}</p><p class="sp-source-note">Transfer information is summarised in BRYME's own words. Where an external report is used, the source is named. Rumours are never presented as confirmed transfers.</p></section>
    <p class="sp-signoff">BRYME Sports — Discover what you love, learn what you need, and find what's next.</p></main>`;
  write('sports/transfers/premier-league-2026-27', layout({
    title: 'Premier League 2026/27 Transfers: All 20 Clubs, Players In & Out',
    description: 'Track every confirmed Premier League 2026/27 transfer. See players joining and leaving all 20 clubs, managers, major deals and the latest transfer updates.',
    path: '/sports/transfers/premier-league-2026-27/', activeNav: 'sports',
    schema: [{ '@context':'https://schema.org', '@type':'CollectionPage', name: 'Premier League 2026/27 Transfers', description: 'Confirmed Premier League transfers for the 2026/27 season, all 20 clubs.', url: absUrl('/sports/transfers/premier-league-2026-27/') }, breadcrumbs(crumbs)],
    body
  }));
}
/* --- league transfer trackers (La Liga, Serie A, Bundesliga, Ligue 1) ---
   TRUTH-FIRST: nothing is listed until officially confirmed by a club or
   widely reported by credible outlets. Club shells are placeholders for
   verified data; the 2026/27 club composition must be confirmed. */
/* Official crest constants shared by league trackers + managers page */
const LL_NAME = { 'atletico-madrid':'atletico', 'athletic-bilbao':'athletic', 'real-betis':'betis', 'celta-vigo':'celta', 'rayo-vallecano':'rayo', 'deportivo':'deportivo', 'racing':'racing' };
const SA_OFFICIAL = ['inter','milan','juventus','napoli','roma','lazio','atalanta','bologna','fiorentina','como','genoa','sassuolo','udinese','lecce','parma','frosinone','torino','monza','venezia','cagliari'];
function buildLeagueTrackers(){
  const pathLg = path.join(root, 'content', 'league-transfers.json');
  let lgData = { leagues: [] };
  if (fs.existsSync(pathLg)) { try { lgData = JSON.parse(fs.readFileSync(pathLg, 'utf8')); } catch (e) { warnings.push('league-transfers.json unreadable'); } }
  function crestUrl(league, id){
    if (league === 'la-liga') return url('/assets/img/sports/ll/' + (LL_NAME[id] || id) + '.png');
    if (league === 'bundesliga') {
      if (id === 'hamburg') return url('/assets/img/sports/club-' + id + '.svg');
      return url('/assets/img/sports/bl/' + id + '.svg');
    }
    if (league === 'ligue-1') return url('/assets/img/sports/l1/' + id + '.webp');
    if (league === 'serie-a') {
      return url('/assets/img/sports/sa/' + id + (id === 'lazio' ? '.png' : '.svg'));
    }
    return url('/assets/img/sports/club-' + id + '.svg');
  }
  function crestAlt(league, id, name){
    if (league === 'bundesliga' && id === 'hamburg') return 'Abstract crest for ' + name + ' — BRYME-generated illustration';
    return league === 'premier-league' || ['la-liga','bundesliga','ligue-1'].includes(league) || league === 'serie-a'
      ? name + ' official club crest' : 'Abstract crest for ' + name + ' — BRYME-generated illustration';
  }
  const CREDIT_LINES = {
    'premier-league': '<b>Club crests</b> © Copyright The Football Association Premier League Limited, 2016, used under the Premier League Logo Site media licence for editorial reporting. BRYME Sports is an independent publication, not affiliated with, endorsed or sponsored by the Premier League or any club.',
    'la-liga': '<b>Club shields</b> © the respective clubs and LaLiga, obtained from the official LaLiga website (files.laliga.es) and used solely for editorial reporting on BRYME Sports. BRYME Sports is not affiliated with, endorsed or sponsored by LaLiga or any club.',
    'bundesliga': '<b>Club crests</b> © the respective clubs and the DFL, obtained from the official bundesliga.com website and used solely for editorial reporting on BRYME Sports. BRYME Sports is not affiliated with, endorsed or sponsored by the DFL/Bundesliga or any club. Crests may be resized for editorial presentation but are not altered.',
    'ligue-1': '<b>Club crests</b> © the respective clubs and the LFP, obtained from the official ligue1.com website (official marks) and used solely for editorial reporting on BRYME Sports. BRYME Sports is not affiliated with, endorsed or sponsored by the LFP/Ligue 1 or any club.',
    'serie-a': '<b>Club crests</b> © the respective clubs, retrieved from Wikimedia Commons (Wikipedia) and official club websites, and used solely for editorial reporting on BRYME Sports. BRYME Sports is not affiliated with, endorsed or sponsored by Lega Serie A or any club.'
  };
  const imgUrl = id => url('/assets/img/sports/club-' + id + '.svg');
  const statusBadge = t => t === 'Loan' ? 'sp-st-conf' : (t === 'Free' ? 'sp-st-rep' : (t === 'Released' || t === 'Retired' || t === 'Departed' ? 'sp-st-rum' : 'sp-st-conf'));
  const statusLabel = t => t === 'Confirmed' ? 'Confirmed' : t;
  const rows = (list, kind) => list && list.length ? list.map(r => `<tr><td><b>${esc(r.player)}</b></td><td>${esc(r.from || r.to || '—')}</td><td>${esc(r.detail || '—')}</td><td><span class="${statusBadge(r.type)}">${esc(statusLabel(r.type))}</span></td></tr>`).join('')
    : `<tr class="sp-empty"><td colspan="4">No confirmed ${esc(kind)} listed yet — BRYME only lists transfers that are officially confirmed by a club or widely reported by credible outlets. Nothing is invented to fill this table.</td></tr>`;
  const clubCard = (c, lgId) => `<article class="sp-club" id="${esc(c.id)}">
    <header class="sp-club-head"><img src="${crestUrl(lgId, c.id)}" alt="${crestAlt(lgId, c.id, c.name)}" width="64" height="77" loading="lazy"><div><h2>${esc(c.name)}</h2><p class="sp-club-man">Manager: <b>${esc(c.manager || 'Pending verification')}</b>${c.managerNote ? ' · ' + esc(c.managerNote) : ''}</p></div></header>
    <div class="sp-club-cols">
      <div class="sp-club-col"><h3>Players In</h3><div class="sp-table-wrap"><table class="sp-table"><thead><tr><th>Player</th><th>From</th><th>Transfer type / fee</th><th>Status</th></tr></thead><tbody>${rows(c.playersIn, 'arrivals')}</tbody></table></div></div>
      <div class="sp-club-col"><h3>Players Out</h3><div class="sp-table-wrap"><table class="sp-table"><thead><tr><th>Player</th><th>To</th><th>Transfer type / fee</th><th>Status</th></tr></thead><tbody>${rows(c.playersOut, 'departures')}</tbody></table></div></div>
    </div>
    ${(c.rumours && c.rumours.length) ? `<div class="sp-rumours"><b>Rumour / Reported interest — not confirmed</b>${c.rumours.map(r => `<p>${esc(r)}</p>`).join('')}</div>` : ''}
    ${c.notes ? `<p class="sp-club-notes"><b>Transfer notes.</b> ${esc(c.notes)}</p>` : ''}
  </article>`;
  for (const lg of lgData.leagues || []) {
    const crumbs = [{name:'Home', path:'/'}, {name:'BRYME Sports', path:'/sports/'}, {name:'Transfers', path:'/sports/transfers/'}, {name:lg.name + ' Transfers 2026/27', path:'/sports/transfers/' + lg.id + '-2026-27/'}];
    const body = `<main class="shell"><div class="crumb"><a href="${url('/')}">Home</a> / <a href="${url('/sports/')}">BRYME Sports</a> / <a href="${url('/sports/transfers/')}">Transfers</a> / ${esc(lg.name)}</div>
      <section class="hero"><div class="eyebrow">⚽ BRYME Sports · Transfers</div><h1>${esc(lg.name)} Transfers 2026/27</h1></section>
      <div class="sp-live"><span class="sp-live-dot"></span><div><b>LIVE TRANSFER WINDOW</b><p>${esc(lg.name)} 2026/27 Transfers — All Clubs. This page shows the transfers completed by each club as they stand right now. The transfer window is still open, so players may move clubs, deals may be completed, and squad information may change before the transfer window closes. BRYME will continue updating this page as new transfers are confirmed.</p></div></div>
      <div class="sp-truth"><b>Truth first — nothing fabricated.</b><p>BRYME only lists transfers that are officially confirmed by the club or widely reported by credible outlets, with the source shown. Rumours are never presented as confirmed. If a transfer is uncertain, it is left out until it can be verified.</p></div>
      <p class="sp-legend-line">Status legend: <span class="sp-st-conf">Confirmed</span><span class="sp-st-rep">Loan · Free</span><span class="sp-st-rum">Released · Retired · Departed</span><span class="sp-st-rum">Rumour (never in confirmed tables)</span></p>
      <p class="sp-updated">Last updated: ${esc(lg.lastUpdated || 'Pending verification')}</p>
      ${lg.leagueNote ? `<div class="vnote" style="margin:0 0 14px">${esc(lg.leagueNote)}</div>` : ''}
      <p class="sp-freq-note">Transfer information changes frequently. This list is updated as new information becomes available and may not include breaking or unannounced developments.${lg.compositionVerified ? '' : ' Club list: based on the most recent completed season — the 2026/27 line-up (promoted/relegated clubs) must be verified before publishing.'}</p>
      <nav class="sp-club-nav" aria-label="Jump to club">${(lg.clubs || []).map(c => `<a href="#${esc(c.id)}">${esc(c.name.replace(' &amp; Hove Albion', '').replace('Hotspur', ''))}</a>`).join('')}</nav>
      <div class="sp-clubs">${(lg.clubs || []).map(c => clubCard(c, lg.id)).join('')}</div>
      <div class="sp-credits">${CREDIT_LINES[lg.id] || ''}</div>
      <p class="sp-window-note">Transfer window still open: this page will be updated as new deals are officially confirmed.</p>
      <section class="sp-source"><h2>Sources</h2><p>${(lg.sources || []).map(esc).join(' · ')}</p><p class="sp-source-note">Transfer information is summarised in BRYME's own words. Where an external report is used, the source is named. Rumours are never presented as confirmed transfers.</p></section>
      <section class="sp-related"><h2>Related</h2><div class="sp-rel-grid"><a class="sp-rel" href="${url('/sports/' + lg.id + '/fixtures/')}">Fixtures</a><a class="sp-rel" href="${url('/sports/' + lg.id + '/results/')}">Results</a><a class="sp-rel" href="${url('/sports/' + lg.id + '/matches/')}">Match Centre</a><a class="sp-rel" href="${url('/sports/managers-2026-27/')}">Managers</a></div></section>
      <p class="sp-signoff">BRYME Sports — Discover what you love, learn what you need, and find what's next.</p></main>`;
    write('sports/transfers/' + lg.id + '-2026-27', layout({
      title: lg.name + ' Transfers 2026/27: All Clubs, Players In & Out',
      description: 'Track every confirmed ' + lg.name + ' 2026/27 transfer. See players joining and leaving clubs, managers, major deals and the latest transfer updates. Only officially confirmed deals are listed.',
      path: '/sports/transfers/' + lg.id + '-2026-27/', activeNav: 'sports',
      schema: [{ '@context':'https://schema.org', '@type':'CollectionPage', name: lg.name + ' Transfers 2026/27', description: 'Confirmed ' + lg.name + ' transfers for the 2026/27 season, all clubs.', url: absUrl('/sports/transfers/' + lg.id + '-2026-27/') }, breadcrumbs(crumbs)],
      body
    }));
  }
}
/* --- execute --- */
(S.articlePlaceholders || []).forEach(sportArticlePlaceholder);
buildPlTransferTracker(); buildLeagueTrackers();
transfersHub(); managersPage(); editorialTablePage(); fplHub(); fixturesResults(); matchCentre(); plHub(); leagueHub();
// cleanup any stray non-prefixed sports pages (from earlier builds)
for (const stray of ['premier-league', 'fpl']) {
  if (fs.existsSync(path.join(root, stray)) && !['premier-league', 'fpl'].includes(stray)) {}
}
const sportsExtraPaths = [];
const PLACEHOLDER_SPORTS_PATHS = new Set();
/* Empty placeholders stay out of the sitemap: the editorial prediction table (empty
   until finalised) and the FPL gameweek hub (currently all sections are "being
   prepared"). Both remain reachable but noindex until real content is written. */
PLACEHOLDER_SPORTS_PATHS.add('/sports/premier-league/table/');
PLACEHOLDER_SPORTS_PATHS.add('/sports/fpl/gameweek-' + MW + '/');
['sports/transfers', 'sports/managers-2026-27', 'sports/fpl'].forEach(p => sportsExtraPaths.push('/' + p + '/'));
['premier-league','la-liga','serie-a','bundesliga','ligue-1'].forEach(slug => ['fixtures','results','matches'].forEach(pp => sportsExtraPaths.push('/sports/' + slug + '/' + pp + '/')));
['premier-league','la-liga','serie-a','bundesliga','ligue-1'].forEach(slug => sportsExtraPaths.push('/sports/' + slug + '/'));
/* Placeholder articles stay out of the sitemap (they are noindexed until written). */
(S.articlePlaceholders || []).forEach(a => PLACEHOLDER_SPORTS_PATHS.add('/sports/' + a.route + '/'));
(S.hero.cards || []).forEach(c => sportsExtraPaths.push(c.route + '/'));
S.transfers.leagues.forEach(l => sportsExtraPaths.push('/sports/transfers/' + l.id + '-2026-27/'));

/* ---------------- Type category pages (/movies/, /series/, /anime/) ---------------- */
const typeConfig = [
  { dir:'movie', pageDir:'movies', label:'Movies', title:'Movies – Discover Popular & Trending Movies', desc:n => `Browse ${n}+ films — Hollywood, Nollywood, Korean, Indian, anime films and more — with trailers, genres, years, countries and languages. Strictly movies, no series or anime mixed in.`, activeNav:'movies', seoNote:'Movie catalogue' },
  { dir:'series', pageDir:'series', label:'TV Series', title:'TV Series – Discover Popular & Trending Series', desc:n => `Browse ${n}+ TV series — American, British, Korean, African and more — with trailers, genres, years and countries. Strictly series, no movies or anime mixed in.`, activeNav:'series', seoNote:'Series catalogue' },
  { dir:'anime', pageDir:'anime', label:'Anime', title:'Anime – Discover Popular Anime, New Releases & Classics', desc:n => `Browse ${n}+ anime series and films — shonen classics, isekai, Studio Ghibli and the latest seasons — with trailers, genres and years. Strictly anime.`, activeNav:'anime', seoNote:'Anime catalogue' }
];
for (const t of typeConfig) {
  const list = movies.filter(m => m.typeDir === t.dir).sort(sortPopular);
  const tDesc = t.desc(list.length);
  const genreMapT = new Map();
  list.forEach(m => {
    const names = m.typeDir === 'movie' ? [m.genre] : m.genres;
    names.forEach(n => { if (!n) return; const s = slugify(n); if (!genreMapT.has(s)) genreMapT.set(s, {name:n, count:0}); genreMapT.get(s).count++; });
  });
  const years = [...new Set(list.map(m => m.year).filter(Boolean))].sort((a,b) => b - a);
  const countries = [...new Set(list.map(m => m.country).filter(Boolean))].sort();
  const languages = [...new Set(list.map(m => m.language).filter(Boolean))].sort();
  const embed = list.map(m => ({ s:m.slug, t:m.title, y:m.year||null, g:m.genreLabel || m.genre || '', gs:m.typeDir === 'movie' ? [m.genre] : m.genres, c:m.country||'', l:m.language||'', r:m.rating && m.rating.value != null ? m.rating.value : null, p:poster(m) }));
  const select = (id, label, options, placeholder) => `<div class="ffield"><label for="${id}">${label}</label><select id="${id}"><option value="">${placeholder}</option>${options.map(o => `<option value="${esc(o)}">${esc(o)}</option>`).join('')}</select></div>`;
  const filterBar = `<div class="filterbar" data-filterbar data-type="${t.dir}">
    <div class="ffield"><label for="f-sort">Sort</label><select id="f-sort"><option value="popular">Popular (Editorial score)</option><option value="newest">Newest</option><option value="az">A–Z</option></select></div>
    ${select('f-genre', 'Genre', [...genreMapT.values()].sort((a,b) => b.count - a.count).map(g => g.name), 'All genres')}
    ${select('f-year', 'Year', years, 'All years')}
    ${select('f-country', 'Country', countries, 'All countries')}
    ${select('f-language', 'Language', languages, 'All languages')}
    <button type="button" class="fbtn fbtn-clear" data-clear>Clear filters</button>
  </div>`;
  const json = JSON.stringify({ type:t.dir, typeLabel:t.label, items:embed }).replace(/</g, '\\u003c');
  write(t.pageDir, layout({
    title: t.title,
    description: tDesc,
    path: '/' + t.pageDir + '/',
    activeNav: t.activeNav,
    image: list[0] ? posterOrCard(list[0]) : undefined,
    schema: [{ '@context':'https://schema.org', '@type':'CollectionPage', name:t.label + ' on BRYME', description:tDesc, url:url('/' + t.pageDir + '/') }, breadcrumbs([{name:'Home', path:'/'}, {name:t.label, path:'/' + t.pageDir + '/'}])],
    body: `<main class="shell"><section class="cat-feature" style="--hero-img:url('${t.dir === 'movie' ? '/assets/img/ent/hero-cinema.jpg' : (t.dir === 'series' ? '/assets/img/ent/hero-series.jpg' : '/assets/img/ent/hero-anime.jpg')}')"><div class="eyebrow">${t.seoNote}</div><h1>${esc(t.label)}</h1><p class="lead">${esc(tDesc)}</p></section>${coreHubStrip(t.pageDir === 'movies' ? 'movies' : t.dir, { title: 'Also on BRYME', lead: 'From here you can jump to series, anime, football, money guides or tech — or stay and browse this catalogue.' })}${t.dir === 'movie' ? `<section class="section"><div class="section-head"><h2>Start with these</h2></div><p class="section-note">Flagship pages with a full BRYME write-up — open one, then follow related titles.</p><div class="rail">${['dune-part-two','interstellar','parasite','oppenheimer','black-panther','a-tribe-called-judah','93-days','october-1'].map(s => slugIndex.get(s)).filter(Boolean).map(card).join('')}</div></section>` : ''}<section class="section"><h2>Browse ${esc(t.label.toLowerCase())}</h2>${filterBar}<p class="count-line" data-count>${list.length} ${t.label.toLowerCase()} in the catalogue</p>${progressiveGrid(list, 40)}</section><script id="catalogue-data" type="application/json">${json}<\/script></main>`
  }));
}

/* ---------------- Per-type genre pages ---------------- */
/* A listing with fewer than this many items adds nothing over its parent page:
   noindexed and kept out of the sitemap until it fills up. Self-healing. */
const THIN_ARCHIVE_MIN = 3;            // below this an archive is noindexed and left out of the sitemap
const thinArchive = list => (list || []).length < THIN_ARCHIVE_MIN;
const THIN_LISTING_PATHS = new Set();
const genreIndexByType = { movie: new Map(), series: new Map(), anime: new Map() };
for (const t of typeConfig) {
  const list = movies.filter(m => m.typeDir === t.dir);
  const map = genreIndexByType[t.dir];
  list.forEach(m => {
    const names = m.typeDir === 'movie' ? [m.genre] : m.genres;
    names.forEach(n => { if (!n) return; const s = slugify(n); if (!map.has(s)) map.set(s, {name:n, items:[]}); map.get(s).items.push(m); });
  });
  const titleSlugs = new Set(list.map(m => m.slug));
  for (const [s, g] of map) {
    if (titleSlugs.has(s)) { warnings.push(`genre page /${t.dir}/${s}/ collides with a title page slug — skipped`); continue; }
    const items = [...g.items].sort(sortPopular);
    const genreLabel = t.dir === 'movie' ? 'movies' : (t.dir === 'series' ? 'series' : 'anime');
    if (thinArchive(items)) THIN_LISTING_PATHS.add(`/${t.pageDir}/${s}/`);
    write(`${t.pageDir}/${s}`, layout({
      noindex: thinArchive(items),
      title: `${g.name} ${genreLabel} – Browse & Discover`,
      description: `Explore ${g.name.toLowerCase()} ${genreLabel} in the BRYME catalogue: trailers, years, countries and editorial information. ${items.length} ${genreLabel} in this collection.`,
      path: `/${t.pageDir}/${s}/`,
      activeNav: t.activeNav, image: items[0] ? posterOrCard(items[0]) : undefined,
      schema: [{ '@context':'https://schema.org', '@type':'CollectionPage', name:`${g.name} ${genreLabel}`, description:`${g.name} ${genreLabel} on BRYME.`, url:url(`/${t.pageDir}/${s}/`) }, breadcrumbs([{name:'Home', path:'/'}, {name:t.label, path:'/' + t.pageDir + '/'}, {name:g.name, path:`/${t.pageDir}/${s}/`}])],
      body: `<main class="shell"><div class="crumb"><a href="${url('/genres/')}">Genres</a> / <a href="${url('/' + t.pageDir + '/')}">${esc(t.label)}</a> / ${esc(g.name)}</div><section class="hero"><div class="eyebrow">${esc(t.label)} genre</div><h1>${esc(g.name)} ${esc(genreLabel)}</h1><p class="lead">${items.length} ${genreLabel} in this collection — strictly ${esc(t.label.toLowerCase())}, nothing else mixed in.</p></section><section class="section">${progressiveGrid(items, 36)}</section></main>`
    }));
  }
}

/* ---------------- Genres hub ---------------- */
const genreHubPanels = typeConfig.map(t => {
  const list = movies.filter(m => m.typeDir === t.dir);
  const map = genreIndexByType[t.dir];
  const chips = [...map.values()].sort((a,b) => b.items.length - a.items.length)
    .map(g => `<a href="${url('/' + t.pageDir + '/' + slugify(g.name) + '/')}">${esc(g.name)}<b>${g.items.length}</b></a>`).join('');
  return `<div class="genre-panel"><h3>${t.dir === 'movie' ? '🎬' : (t.dir === 'series' ? '📺' : '🍥')} ${esc(t.label)} genres <span class="gp-count">${list.length} ${t.label.toLowerCase()}</span></h3><div class="genre-chips">${chips}</div></div>`;
}).join('');
write('genres', layout({
  title: 'Genres – Movie, Series & Anime categories',
  description: 'Browse BRYME genres with strict content-type separation: movie genres, TV series genres and anime genres each have their own category pages.',
  path: '/genres/', activeNav: 'genres',
  schema: [{ '@context':'https://schema.org', '@type':'CollectionPage', name:'BRYME genres', url:url('/genres/') }],
  body: `<main class="shell"><section class="hero"><div class="eyebrow">Browse by category</div><h1>Genres, separated by type.</h1><p class="lead">Every genre page is scoped to a single content type — movie genres never contain series, and anime genres never contain movies.</p></section><section class="section"><div class="genre-trio">${genreHubPanels}</div></section><section class="section"><h2>Legacy movie genre pages</h2><p class="lead">The original genre routes remain available: <a class="quiet-link" href="${url('/genre/action/')}">Action</a>, <a class="quiet-link" href="${url('/genre/horror/')}">Horror</a>, <a class="quiet-link" href="${url('/genre/sci-fi/')}">Sci-Fi</a> and <a class="quiet-link" href="${url('/genre/comedy/')}">Comedy</a>.</p></section></main>`
}));

/* ---------------- Legacy /genre/ pages (movie-only, canonical to /movies/{genre}/) ---------------- */
for (const [s, g] of genreIndexByType.movie) {
  if (!fs.existsSync(path.join(root, 'genre', s))) continue;
  const items = [...g.items].sort(sortPopular);
  write(`genre/${s}`, layout({
    title: `${g.name} movies – Browse & Discover`,
    description: `Explore ${g.name.toLowerCase()} movies in the BRYME catalogue: trailers, years and editorial information.`,
    path: `/genre/${s}/`, canonical: `/movies/${s}/`, activeNav: 'movies',
    schema: { '@context':'https://schema.org', '@type':'CollectionPage', name:`${g.name} movies`, url:url(`/genre/${s}/`) },
    body: `<main class="shell"><div class="crumb"><a href="${url('/genres/')}">Genres</a> / ${esc(g.name)}</div><section class="hero"><div class="eyebrow">Genre</div><h1>${esc(g.name)} movies</h1><p class="lead">A curated selection from the existing BRYME movie catalogue. The canonical version of this page lives at <a class="quiet-link" href="${url('/movies/' + s + '/')}">${esc(g.name)} movies</a>.</p></section><section class="section">${progressiveGrid(items, 36)}</section></main>`
  }));
}
// Stale mixed-content legacy genre pages (no inbound links) are removed,
// plus any artifacts wrongly generated under the singular /movie/ dir.
for (const stale of ['genre/anime', 'genre/series', 'movie/index.html']) {
  if (fs.existsSync(path.join(root, stale))) { fs.rmSync(path.join(root, stale), {recursive:true, force:true}); warnings.push(`removed stale mixed-content page ${stale}/`); }
}
for (const s of genreIndexByType.movie.keys()) {
  const wrong = path.join(root, 'movie', s);
  if (fs.existsSync(wrong)) { fs.rmSync(wrong, {recursive:true, force:true}); warnings.push(`removed mis-placed genre page movie/${s}/ (now at movies/${s}/)`); }
}

/* ---------------- Years (per content type) ---------------- */
const yearMap = new Map();        // movies  -> /year/{y}/
const seriesYearMap = new Map();  // series  -> /series/{y}/
const animeYearMap = new Map();   // anime   -> /anime/{y}/
movies.forEach(m => {
  if (!m.year) return;
  const map = m.typeDir === 'movie' ? yearMap : (m.typeDir === 'series' ? seriesYearMap : animeYearMap);
  if (!map.has(m.year)) map.set(m.year, []);
  map.get(m.year).push(m);
});
const yearChip = (map, base, label) => [...map.keys()].sort((a, b) => b - a)
  .map(y => `<a href="${url('/' + base + '/' + y + '/')}">${y} <b>${map.get(y).length}</b></a>`).join('');
write('years', layout({
  title: 'Browse by year — Movies, Series & Anime',
  description: 'Browse BRYME years with strict content-type separation: movies by year, TV series by year and anime by year each have their own index.',
  path: '/years/', activeNav: 'years',
  body: `<main class="shell"><section class="hero"><div class="eyebrow">Browse by year</div><h1>Years, separated by type.</h1><p class="lead">Series and anime are never mixed into the movie year index. Each type has its own year pages.</p></section><section class="section"><div class="genre-trio"><div class="genre-panel"><h3>🎬 Movies <span class="gp-count">${yearMap.size} years</span></h3><div class="genre-chips">${yearChip(yearMap, 'year', 'movies')}</div></div><div class="genre-panel"><h3>📺 Series <span class="gp-count">${seriesYearMap.size} years</span></h3><div class="genre-chips">${yearChip(seriesYearMap, 'series', 'series')}</div></div><div class="genre-panel"><h3>🍥 Anime <span class="gp-count">${animeYearMap.size} years</span></h3><div class="genre-chips">${yearChip(animeYearMap, 'anime', 'anime')}</div></div></div></section></main>`
}));
for (const [year, list] of yearMap) write(`year/${year}`, layout({
  title: `Movies from ${year}`, description: `Explore movies from ${year} in the BRYME catalogue.`, path: `/year/${year}/`, noindex: thinArchive(list), activeNav: 'movies', image: list[0] ? poster(list[0]) : undefined,
  body: `<main class="shell"><div class="crumb"><a href="${url('/years/')}">Years</a> / <a href="${url('/movies/')}">Movies</a> / ${year}</div><section class="hero"><div class="eyebrow">Year · Movies</div><h1>Movies from ${year}</h1></section><section class="section">${progressiveGrid(list, 36)}</section></main>`
}));
for (const [year, list] of seriesYearMap) write(`series/${year}`, layout({
  title: `Series from ${year}`, description: `Explore TV series from ${year} in the BRYME catalogue.`, path: `/series/${year}/`, noindex: thinArchive(list), activeNav: 'series', image: list[0] ? poster(list[0]) : undefined,
  body: `<main class="shell"><div class="crumb"><a href="${url('/years/')}">Years</a> / <a href="${url('/series/')}">Series</a> / ${year}</div><section class="hero"><div class="eyebrow">Year · Series</div><h1>Series from ${year}</h1></section><section class="section">${progressiveGrid(list, 36)}</section></main>`
}));
for (const [year, list] of animeYearMap) write(`anime/${year}`, layout({
  title: `Anime from ${year}`, description: `Explore anime from ${year} in the BRYME catalogue.`, path: `/anime/${year}/`, noindex: thinArchive(list), activeNav: 'anime', image: list[0] ? poster(list[0]) : undefined,
  body: `<main class="shell"><div class="crumb"><a href="${url('/years/')}">Years</a> / <a href="${url('/anime/')}">Anime</a> / ${year}</div><section class="hero"><div class="eyebrow">Year · Anime</div><h1>Anime from ${year}</h1></section><section class="section">${progressiveGrid(list, 36)}</section></main>`
}));

/* ---------------- Rankings hub (/trending/) ---------------- */
function trendLabel(m){
  const b = String(m.trendingBadge || '').toLowerCase();
  if (b === 'viral') return { cls: 'tl-watch', text: '👀 Viral' };
  if (b === 'hot') return { cls: 'tl-hot', text: '🔥 Hot' };
  if (b === 'rising') return { cls: 'tl-rise', text: '📈 Rising' };
  if (b === 'new') return { cls: 'tl-new', text: '🆕 New' };
  if (b === 'global') return { cls: 'tl-rise', text: '🌍 Global' };
  if (b === 'regional') return { cls: 'tl-rise', text: '🌍 Regional' };
  if (m.trending && m.trendingRank != null && m.trendingRank <= 3) return { cls: 'tl-hot', text: '🔥 Hot' };
  if (m.trending && m.trendingRank != null && m.trendingRank <= 7) return { cls: 'tl-rise', text: '📈 Rising' };
  if (m.trending) return { cls: 'tl-watch', text: '👀 On the list' };
  if (m.isNewRelease) return { cls: 'tl-new', text: '🆕 New' };
  return null;
}
function trendCard(m, opts){
  opts = opts || {};
  const typeDir = m.typeDir || 'movie';
  const label = typeDir === 'series' ? 'SERIES' : (typeDir === 'anime' ? 'ANIME' : 'MOVIE');
  const genre = (typeDir === 'movie' ? m.genre : ((m.genres || [])[0] || m.genre || '')) || '';
  const blurb = clipMeta(m.description || m.teaser || '', 150);
  const lab = trendLabel(m);
  const pageHref = url('/' + typeDir + '/' + m.slug + '/');
  const thumb = poster(m) || posterThumb(m);
  const img = thumb
    ? `<img loading="lazy" decoding="async" width="160" height="90" src="${esc(thumb)}" alt="${esc(m.title)} poster">`
    : `<img loading="lazy" decoding="async" width="160" height="240" src="${url(cardImage(m))}" alt="${esc(m.title)} — BRYME title card">`;
  const rank = opts.rank ? `<span class="trend-rank">${opts.rank}</span>` : '';
  const trailer = m.youtubeId
    ? `<a class="trend-go" href="${pageHref}#trailer">Trailer</a>`
    : `<span class="trend-none">No trailer on BRYME yet</span>`;
  const note = (opts.note || m.trendingNote) ? `<p class="trend-why">${esc(opts.note || m.trendingNote)}</p>` : '';
  return `<article class="trend-card"><a class="trend-poster" href="${pageHref}">${rank}${img}</a><div class="trend-body"><div class="trend-kicker"><span class="type-badge tb-${typeDir}">${label}</span>${lab ? `<span class="trend-lab ${lab.cls}">${lab.text}</span>` : ''}${m.year ? `<span>${m.year}</span>` : ''}${genre ? `<span class="sep">·</span><span>${esc(genre)}</span>` : ''}</div><h3><a href="${pageHref}">${esc(m.title)}</a></h3>${blurb ? `<p class="trend-blurb">${esc(blurb)}</p>` : ''}${note}<div class="trend-actions"><a class="cta" href="${pageHref}">View on BRYME</a>${trailer}</div></div></article>`;
}
function itemListSchema(name, items){
  return {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name,
    itemListOrder: 'https://schema.org/ItemListOrderAscending',
    numberOfItems: items.length,
    itemListElement: items.map((m, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      url: absUrl('/' + (m.typeDir || 'movie') + '/' + m.slug + '/'),
      name: m.title
    }))
  };
}
const trendTopMovie = trendingByType.movie.slice(0, 24);
const trendTopSeries = trendingByType.series.slice(0, 24);
const trendTopAnime = trendingByType.anime.slice(0, 24);
const popularTop = [...popularByType.movie, ...popularByType.series, ...popularByType.anime].slice(0, 36);
const editorTop = editorPicksList.slice(0, 12);
const newTop = (newReleases.length >= 8 ? newReleases : movies.filter(m => m.year).sort(sortNewest)).slice(0, 24);
const classicTop = classics.slice(0, 24);
const nollywoodTop = movies.filter(m => /nigeria/i.test(String(m.country || '')))
  .sort((a, b) => ((b.year || 0) - (a.year || 0)) || a.title.localeCompare(b.title))
  .slice(0, 12);
const indiaNow = movies.filter(m => (m.typeDir || 'movie') === 'movie' && /india/i.test(String(m.country || '')) && m.year === CURRENT_YEAR)
  .sort((a, b) => a.title.localeCompare(b.title));
const chinaNow = movies.filter(m => (m.typeDir || 'movie') === 'movie' && /china/i.test(String(m.country || '')) && m.year === CURRENT_YEAR)
  .sort((a, b) => a.title.localeCompare(b.title));
const koreaNow = movies.filter(m => (m.typeDir || 'movie') === 'movie' && /korea/i.test(String(m.country || '')) && m.year === CURRENT_YEAR)
  .sort((a, b) => a.title.localeCompare(b.title));
const trendTrailers = trendingList.filter(m => m.youtubeId);
const trendSlugSet = new Set(trendingList.map(m => m.slug));
const trendStories = articles.filter(a => (a.relatedMovieSlugs || []).some(s => trendSlugSet.has(s))).slice(0, 6);
write('trending', layout({
  title: 'Trending, Popular, Editor\'s Picks & New Releases',
  description: 'BRYME\'s editorial rankings: trending (curated per content type), popular, editor\'s picks, new releases and classics. No fake view counts.',
  path: '/trending/', activeNav: 'trending',
  schema: [
    { '@context':'https://schema.org', '@type':'CollectionPage', name:'Trending & Popular on BRYME', url:url('/trending/') },
    breadcrumbs([{name:'Home', path:'/'}, {name:"What's Trending", path:'/trending/'}]),
    itemListSchema('What\'s Trending — Movies', trendTopMovie),
    itemListSchema('What\'s Trending — TV series', trendTopSeries),
    itemListSchema('What\'s Trending — Anime', trendTopAnime)
  ],
  body: `<main class="shell trend-page"><section class="hero"><div class="eyebrow">Discovery desk</div><h1>What's Trending</h1><p class="lead">Movies, series and anime the BRYME desk is pointing to right now — then Nollywood on this site, verified trailers, and the older lists (popular, editor's picks, new, classics). This is not a live TikTok or Google Trends feed.</p></section>
  <nav class="trend-jump" aria-label="What's Trending"><a href="#movies">🎬 Movies</a><a href="#series">📺 TV series</a><a href="#anime">🍥 Anime</a><a href="#nollywood">🇳🇬 Nollywood</a>${indiaNow.length >= 2 ? '<a href="#india">🇮🇳 India</a>' : ''}${chinaNow.length >= 2 ? '<a href="#china">🇨🇳 China</a>' : ''}${koreaNow.length >= 2 ? '<a href="#korea">🇰🇷 Korea</a>' : ''}<a href="#trailers">🎞️ Trailers</a><a href="#editors-picks">👑 Editor's picks</a></nav>
  <div class="trend-note"><b style="color:var(--text)">How these labels work.</b><br>🔥 Hot, 📈 Rising, 👀 Viral, 🌍 Regional/Global and 🆕 New are <b>editorial labels</b> on BRYME's list (content/rankings.json) — not search volume, not TikTok, not a made-up percentage score. A title is on this page because an editor put it here. Country shelves below only appear when there are enough current titles to fill them. When BRYME has real analytics, this desk can switch to engagement + growth without changing the URL.</div>
  <section class="section" id="movies"><div class="section-head"><h2>🎬 Movies</h2><a href="${url('/movies/')}">All movies</a></div><p class="section-note">${trendTopMovie.length} titles on the current editorial movie list.</p><div class="trend-list">${trendTopMovie.map(m => trendCard(m, {rank: m.trendingRank})).join('') || '<p style="color:var(--muted)">No trending movies configured yet.</p>'}</div></section>
  <section class="section" id="series"><div class="section-head"><h2>📺 TV series</h2><a href="${url('/series/')}">All series</a></div><p class="section-note">${trendTopSeries.length} titles on the current editorial series list.</p><div class="trend-list">${trendTopSeries.map(m => trendCard(m, {rank: m.trendingRank})).join('') || '<p style="color:var(--muted)">No trending series configured yet.</p>'}</div></section>
  <section class="section" id="anime"><div class="section-head"><h2>🍥 Anime</h2><a href="${url('/anime/')}">All anime</a></div><p class="section-note">${trendTopAnime.length} titles on the current editorial anime list.</p><div class="trend-list">${trendTopAnime.map(m => trendCard(m, {rank: m.trendingRank})).join('') || '<p style="color:var(--muted)">No trending anime configured yet.</p>'}</div></section>
  <section class="section" id="nollywood"><div class="section-head"><h2>🇳🇬 Nollywood on BRYME</h2><a href="${url('/movies/')}">Movies catalogue</a></div><p class="section-note">Nigerian titles already in the catalogue, newest first. This is a shelf on BRYME — not a claim that these films are trending on TikTok.</p><div class="trend-list">${nollywoodTop.map(m => trendCard(m)).join('') || '<p style="color:var(--muted)">No Nigerian titles in the catalogue yet.</p>'}</div></section>
  ${indiaNow.length >= 2 ? `<section class="section" id="india"><div class="section-head"><h2>🇮🇳 India right now</h2><a href="${url('/movies/')}">Movies catalogue</a></div><p class="section-note">${indiaNow.length} Indian films from ${CURRENT_YEAR} already on BRYME. This is a shelf, not a new country URL, and not a national box-office chart.</p><div class="trend-list">${indiaNow.map(m => trendCard(m)).join('')}</div></section>` : ''}
  ${chinaNow.length >= 2 ? `<section class="section" id="china"><div class="section-head"><h2>🇨🇳 China right now</h2><a href="${url('/movies/')}">Movies catalogue</a></div><p class="section-note">${chinaNow.length} Chinese films from ${CURRENT_YEAR} on BRYME. Shown only because there is enough to fill a shelf.</p><div class="trend-list">${chinaNow.map(m => trendCard(m)).join('')}</div></section>` : ''}
  ${koreaNow.length >= 2 ? `<section class="section" id="korea"><div class="section-head"><h2>🇰🇷 Korea right now</h2><a href="${url('/movies/')}">Movies catalogue</a></div><p class="section-note">${koreaNow.length} Korean films from ${CURRENT_YEAR} on BRYME. Shown only because there is enough to fill a shelf.</p><div class="trend-list">${koreaNow.map(m => trendCard(m)).join('')}</div></section>` : ''}
  <section class="section" id="trailers"><div class="section-head"><h2>🎞️ Trailers on this list</h2></div><p class="section-note">Verified YouTube trailers for titles on What's Trending. BRYME does not host the files. Play is on the title page.</p><div class="trend-list">${trendTrailers.map(m => trendCard(m, {rank: m.trendingRank})).join('') || '<p style="color:var(--muted)">No verified trailers on the current list.</p>'}</div></section>
  ${trendStories.length ? `<section class="section" id="reading"><div class="section-head"><h2>Related BRYME stories</h2><a href="${url('/articles/')}">All stories</a></div><p class="section-note">Existing articles that already point at titles on this desk — not new pages spun up for a crawler.</p><div class="story-grid">${trendStories.map(a => storyPhoto('/article/' + a.slug + '/', a.category, a.title, a.description || '', heroFor(a.slug, 'entertainment'))).join('')}</div></section>` : ''}
  <section class="section" id="editors-picks"><div class="section-head"><h2>👑 Editor's Picks</h2></div><p class="section-note">Personal recommendations from the BRYME desk — independent of the lists above.</p><div class="grid grid-2">${editorTop.map(m => card(m)).join('') || '<p style="color:var(--muted)">No editor\'s picks configured yet.</p>'}</div></section>
  <section class="section"><div class="section-head"><h2>⭐ Popular</h2></div><p class="section-note">Evergreen favourites, editorially ranked per content type.</p><div class="grid">${popularTop.map(card).join('')}</div></section>
  <section class="section" id="new-releases"><div class="section-head"><h2>🆕 New Releases</h2></div><p class="section-note">Newest verified release years (${CURRENT_YEAR - 2}–${CURRENT_YEAR}). Older titles are never re-labelled as new.</p><div class="grid">${newTop.map(card).join('')}</div></section>
  <section class="section" id="classics"><div class="section-head"><h2>🎞️ Classics</h2></div><p class="section-note">Titles from 2000 and earlier, ranked by editorial score.</p><div class="grid">${classicTop.map(card).join('')}</div></section>
  <section class="tp-next"><h2>Keep exploring</h2><p>Stay on BRYME — these are real sections, not download buttons.</p><div class="tp-next-links"><a href="${url('/movies/')}">Movies</a><a href="${url('/series/')}">TV series</a><a href="${url('/anime/')}">Anime</a><a href="${url('/entertainment/')}">Entertainment</a><a href="${url('/articles/')}">Stories</a></div></section></main>`
}));

/* ---------------- Search ---------------- */
const searchEmbed = JSON.stringify({ movies: searchIndex.movies, articles: searchIndex.articles, topics: searchIndex.topics, verticals: searchIndex.verticals || [] }).replace(/</g, '\\u003c');
write('search', layout({
  title: 'Search Movies, TV Series & Anime',
  description: 'Search across BRYME — movies, TV series, anime, sports, memes, money guides and tech — every result is labelled with its vertical.',
  path: '/search/', noindex: false,
  body: `<main class="shell"><section class="hero"><div class="eyebrow">Global search</div><h1>What are you looking for?</h1><p class="lead">Search movies, TV series, anime, sports, memes, money guides and tech & AI. Every result shows its vertical.</p></section><section class="section"><input class="searchbox" id="search-q" autocomplete="off" placeholder="Try Dune, Breaking Bad, One Piece, Horror, 2024…"><p class="searchnote" id="search-status"></p><div class="search-tabs" id="search-tabs"><button type="button" class="stabs active" data-tab="all">All</button><button type="button" class="stabs" data-tab="movie">🎬 Movies</button><button type="button" class="stabs" data-tab="series">📺 Series</button><button type="button" class="stabs" data-tab="anime">🍥 Anime</button><button type="button" class="stabs" data-tab="article">📰 Articles</button></div><div class="grid" id="search-results"></div></section><script id="search-data" type="application/json">${searchEmbed}<\/script></main>`
}));

/* ---------------- Title pages ---------------- */
function relatedArticlesFor(m){
  if (!m.relatedMovieSlugs) return [];
  return (m.relatedMovieSlugs || []).map(slug => articles.find(a => a.slug === slug)).filter(Boolean).slice(0, 3);
}
articles.forEach(a => a.relatedMovieSlugs = a.relatedMovieSlugs || []);
const articleToMovies = new Map();
articles.forEach(a => { (a.relatedMovieSlugs || []).forEach(slug => { const m = slugIndex.get(slug); if (m) { if (!articleToMovies.has(m.slug)) articleToMovies.set(m.slug, []); articleToMovies.get(m.slug).push(a); } }); });

/* ================================================================
   TITLE PAGES — premium individual pages
   Related-title algorithm (deterministic):
   manual editorial relationship (+100) + shared genres + same era
   (±3 years) + editorial rating. Same type always required.
   ================================================================ */
const titleRelationsPath = path.join(root, 'content', 'title-relationships.json');
let titleRelations = {};
if (fs.existsSync(titleRelationsPath)) {
  try { titleRelations = JSON.parse(fs.readFileSync(titleRelationsPath, 'utf8')); } catch (e) { warnings.push('title-relationships.json unreadable'); }
}
// Normalise manual relationships: titleRelations[slug] may be a plain array
// (legacy) or { relatedTitles: [...] } — the spec's optional relatedTitles form.
const REL = {};
for (const [from, val] of Object.entries(titleRelations)) {
  if (from === '_comment') continue;
  if (!slugIndex.has(from)) { warnings.push(`title-relationships.json: unknown key slug "${from}"`); continue; }
  const list = Array.isArray(val) ? val : (val && Array.isArray(val.relatedTitles) ? val.relatedTitles : []);
  if (!Array.isArray(val) && !(val && Array.isArray(val.relatedTitles))) warnings.push(`title-relationships.json: invalid value for "${from}"`);
  REL[from] = list;
  list.forEach(t => { if (!slugIndex.has(t)) warnings.push(`title-relationships.json: unknown related slug "${t}" (from ${from})`); });
}
// Distinctive genres carry more signal than generic ones (Survival vs Action).
const COMMON_GENRES = new Set(['action', 'adventure', 'comedy', 'drama', 'fantasy', 'sci-fi', 'thriller', 'romance', 'crime', 'horror', 'animation', 'family']);
const DISTINCTIVE_WEIGHT = 6, COMMON_WEIGHT = 2;
function genreWeight(g) { return COMMON_GENRES.has(slugify(g)) ? COMMON_WEIGHT : DISTINCTIVE_WEIGHT; }
function listedGenres(m){
  if ((m.typeDir || 'movie') === 'movie') return [m.genre].filter(Boolean);
  return (m.genres || []).filter(Boolean);
}
function countryTokens(s){
  return String(s || '').split(/[;,/]/).map(x => x.trim().toLowerCase()).filter(Boolean);
}
function nameList(s){
  return String(s || '').split(';').map(x => x.trim()).filter(Boolean);
}
function primaryCountry(m){
  const parts = String(m.country || '').split(/[;,]/).map(s => s.trim()).filter(Boolean);
  if (!parts.length) return '';
  if (parts.length <= 2) return parts.join(', ');
  /* Wikidata often dumps every filming location. Prefer a real production
     country; otherwise say nothing rather than "Hungary" for Dune. */
  const hints = ['Nigeria','United States','United Kingdom','India','South Korea','Japan','France','Canada','Australia','Germany','Brazil','Mexico','China','Hong Kong','Ireland','Italy','Spain','South Africa'];
  for (const h of hints) {
    const hit = parts.find(p => p.toLowerCase() === h.toLowerCase());
    if (hit) return hit;
  }
  return '';
}
function detailsCountry(m){
  const parts = String(m.country || '').split(/[;,]/).map(s => s.trim()).filter(Boolean);
  if (!parts.length) return '';
  if (parts.length <= 2) return parts.join(', ');
  return primaryCountry(m) + ' (co-production)';
}
function runtimeLabel(m){
  const mins = parseInt(String(m.runtime || '').replace(/[^0-9]/g, ''), 10);
  return mins > 0 ? mins + ' min' : '';
}
function genrePath(m, g){
  const typeDir = m.typeDir || 'movie';
  const base = typeDir === 'movie' ? 'movies' : typeDir;
  return '/' + base + '/' + slugify(g) + '/';
}
const LEGAL_WATCH_HOSTS = new Set([
  'netflix.com','primevideo.com','amazon.com','amazon.co.uk','amazon.de',
  'disneyplus.com','tv.apple.com','itunes.apple.com','play.google.com',
  'youtube.com','m.youtube.com','youtu.be','max.com','play.hbomax.com',
  'hulu.com','paramountplus.com','peacocktv.com','showmax.com','irokotv.com',
  'tubitv.com','crunchyroll.com','mubi.com','curiositystream.com','plex.tv',
  'watch.plex.tv','justwatch.com'
]);
function isLegalWatchUrl(raw){
  try {
    const u = new URL(String(raw || ''));
    if (u.protocol !== 'https:') return false;
    if (/torrent|magnet|putlocker|fmovies|123movie|soap2day|nkiri|netnaija|fzmovies|mobiletvshows|zippyshare/i.test(u.href)) return false;
    const host = u.hostname.replace(/^www\./, '').toLowerCase();
    return LEGAL_WATCH_HOSTS.has(host);
  } catch (e) { return false; }
}
function watchLinkLabel(link){
  const name = clean(link.name || 'platform');
  let isSearch = false;
  try {
    const u = new URL(link.url);
    isSearch = /\/search/i.test(u.pathname) || u.searchParams.has('q');
  } catch (e) {}
  return (isSearch ? 'Search ' : 'Check ') + name;
}
const WATCH_GUIDANCE = (() => {
  const f = path.join(root, 'content', 'watch-guidance.json');
  if (!fs.existsSync(f)) return {};
  try { return JSON.parse(fs.readFileSync(f, 'utf8')); } catch (e) { return {}; }
})();
function whereToWatchBlock(m){
  /* Do not emit generic Netflix/Crunchyroll chips. That fabricates availability
     even with a disclaimer and is why "Shōgun watch" cannot trust this page. */
  const g = (WATCH_GUIDANCE[m.slug] && typeof WATCH_GUIDANCE[m.slug] === 'object' && WATCH_GUIDANCE[m.slug].originalNetwork)
    ? WATCH_GUIDANCE[m.slug] : null;
  const links = (m.watchLinks || []).filter(l => l && l.url && isLegalWatchUrl(l.url));
  const note = '<p class="tp-watch-note">A “Check” or “Search” link opens an official service. It is not a promise the title is on that service in your country today. BRYME does not host films or episodes. These links are not advertisements.</p>';
  const host = `<p>BRYME is not a streaming site and does not host ${esc(m.title)}.</p>`;
  let network = '';
  if (g) {
    const article = /^[AEIOU]/i.test(g.originalNetwork) ? 'an' : 'a';
    const label = (m.typeDir === 'series') ? 'original series' : 'title';
    const lead = g.lead || 'That tells you which licensed family to search first. Rights move by country and date.';
    network = `<p>${esc(m.title)} is ${article} ${esc(g.originalNetwork)} ${label}. ${esc(lead)}</p>`;
  }
  const how = `<p>To find a legal copy: search “${esc(m.title)}” in the licensed apps available in your country and confirm the title page on the service itself before paying or starting a trial. Skip unofficial “free watch” sites — they are not listed here.</p>`;
  const check = (g && Array.isArray(g.check) ? g.check : [])
    .filter(c => c && c.name && c.url)
    .map(c => `<a class="tp-watch-btn" href="${esc(c.url)}" rel="nofollow noopener" target="_blank">Check ${esc(c.name)}</a>`);
  const search = links.map(l => `<a class="tp-watch-btn" href="${esc(l.url)}" rel="nofollow noopener" target="_blank">${esc(watchLinkLabel(l))}</a>`);
  const btns = check.concat(search);
  const row = btns.length ? `<div class="tp-watch-row">${btns.join('')}</div>` : '';
  return `<section class="tp-watch" id="watch"><h2>Where to watch legally</h2>${host}${network}${how}${row}${note}</section>`;
}
function nowTalkingBlock(m){
  const ed = editorialOf(m);
  if (ed && Array.isArray(ed.now) && ed.now.length) {
    return `<section class="tp-now" id="trending-now"><h2>🔥 Why it's trending</h2>${ed.now.map(p => `<p>${esc(p)}</p>`).join('')}</section>`;
  }
  if (m.trending) {
    return `<section class="tp-now" id="trending-now"><h2>🔥 Why it's trending</h2><p>${esc(m.title)} is on BRYME's current What's Trending list. That list is editorial — not TikTok, not a live search-volume score.</p></section>`;
  }
  return '';
}
function verdictBlock(m){
  const ed = editorialOf(m);
  const score = (m.rating && m.rating.value != null) ? m.rating.value : null;
  const line = (ed && Array.isArray(ed.why) && ed.why[0]) ? ed.why[0] : '';
  if (score == null && !line) return '';
  const scoreHtml = score != null
    ? `<p class="tp-verdict-score">★ ${esc(String(score))}/10</p><p class="tp-verdict-note">BRYME editorial opinion — not IMDb, Rotten Tomatoes, or a live audience score.</p>`
    : '';
  const lineHtml = line ? `<p>${esc(line)}</p>` : '';
  return `<section class="tp-verdict" id="verdict"><h2>⭐ BRYME Quick Take</h2>${scoreHtml}${lineHtml}</section>`;
}
function lovedHeading(m){
  const noun = (m.typeDir === 'series') ? 'series' : (m.typeDir === 'anime' ? 'anime' : 'movie');
  const g = (listedGenres(m)[0] || '');
  const c = String(m.country || '');
  if (m.slug === 'niu-lai') return "If you like this, check these unusual animated movies";
  if (/korea/i.test(c) && /thriller|horror/i.test(g)) return 'If you like this Korean thriller, check these out';
  if ((m.typeDir || '') === 'anime') return 'If you like this anime, check these out';
  if (/nigeria/i.test(c)) return 'If you like this Nollywood title, check these out';
  if (/india/i.test(c) && (m.typeDir || 'movie') === 'movie') return 'If you like this Indian film, check these out';
  if (g) return 'If you like this ' + g.toLowerCase() + ' ' + noun + ', check these out';
  return 'If you like ' + m.title + ', check these out';
}
function recReason(from, to){
  const fg = listedGenres(from), tg = listedGenres(to);
  const shared = fg.filter(g => tg.includes(g));
  const fd = nameList(from.director), td = nameList(to.director).map(x => x.toLowerCase());
  const sameDir = fd.find(d => td.includes(d.toLowerCase()));
  if (sameDir) return 'Same director: ' + sameDir + '.';
  const fc = countryTokens(from.country), tc = countryTokens(to.country);
  const sameC = fc.find(c => tc.includes(c));
  if ((from.typeDir || 'movie') === 'anime' && (to.typeDir || 'movie') === 'anime') {
    if (shared[0]) return 'Another ' + shared[0].toLowerCase() + ' anime on BRYME.';
    return 'Another anime title on BRYME.';
  }
  if (sameC && shared[0]) return sameC.replace(/\b\w/g, ch => ch.toUpperCase()) + ' ' + shared[0].toLowerCase() + ' — same lane.';
  if (shared[0]) return 'Also listed as ' + shared[0].toLowerCase() + ' on BRYME.';
  if (sameC) return 'Also from ' + sameC.replace(/\b\w/g, ch => ch.toUpperCase()) + '.';
  if (from.language && to.language && from.language === to.language) return 'Same language (' + from.language + ').';
  if (from.year && to.year && Math.abs(from.year - to.year) <= 3) return 'From the same period (' + to.year + ').';
  return 'Next on BRYME if ' + from.title + ' is the kind of thing you want.';
}
function lovedPick(m, related){
  const srcG = listedGenres(m)[0];
  const ranked = (related || []).slice();
  if (srcG) {
    ranked.sort((a, b) => {
      const ag = listedGenres(a).includes(srcG) ? 1 : 0;
      const bg = listedGenres(b).includes(srcG) ? 1 : 0;
      return bg - ag;
    });
  }
  return ranked.slice(0, 5);
}
function lovedBlock(m, related){
  const five = lovedPick(m, related);
  if (!five.length) return '';
  const noun = (m.typeDir === 'series') ? 'series' : (m.typeDir === 'anime' ? 'anime' : 'movies');
  const explore = (m.typeDir === 'series') ? '/trending/#series' : (m.typeDir === 'anime' ? '/trending/#anime' : '/trending/#movies');
  const cards = five.map(x => {
    const img = poster(x) || url(cardImage(x));
    const g = listedGenres(x)[0] || (x.typeDir === 'anime' ? 'Anime' : (x.typeDir === 'series' ? 'Series' : 'Movie'));
    const href = url('/' + (x.typeDir || 'movie') + '/' + x.slug + '/');
    return `<a class="tp-loved-card" href="${href}"><img loading="lazy" decoding="async" width="320" height="180" src="${esc(img)}" alt="${esc(x.title)} thumbnail"><span><b>${esc(x.title)}</b><em>${esc(g)}${x.year ? ' · ' + x.year : ''}</em><small>${esc(recReason(m, x))}</small></span></a>`;
  }).join('');
  return `<section class="tp-loved tp-loved-under" id="loved"><h2>🍿 ${esc(lovedHeading(m))}</h2><p class="tp-loved-lead">If you like this, check these out. It sits under the trailer so it does not cover the player.</p><div class="tp-loved-list">${cards}</div><p class="tp-loved-more">Didn't find your next ${esc(noun === 'movies' ? 'movie' : noun)}? <a href="${url(explore)}">Explore What's Trending →</a></p></section>`;
}
function whyYouMightLikeBlock(m, related){
  const ed = editorialOf(m);
  if (ed && Array.isArray(ed.why) && ed.why.length) {
    return `<section class="tp-why"><h2>Why you might like it</h2>${ed.why.map(b => `<p>${esc(b)}</p>`).join('')}</section>`;
  }
  const bits = [];
  const gs = listedGenres(m);
  if (gs.length) bits.push('BRYME lists ' + m.title + ' as ' + gs.join(' / ').toLowerCase() + '.');
  const dirs = nameList(m.director);
  if (dirs.length) bits.push('It was directed by ' + dirs.slice(0, 2).join(' and ') + '.');
  if (m.cast && m.cast.length) bits.push('The billed cast includes ' + m.cast.slice(0, 3).join(', ') + '.');
  if (m.editorPick) bits.push('It is on BRYME\'s Editor\'s Picks.');
  if (related[0]) {
    const more = related.slice(0, 2).map(x => x.title);
    bits.push('If this is the lane you want, ' + more.join(' and ') + (more.length > 1 ? ' are' : ' is') + ' next on BRYME.');
  }
  if (bits.length < 2) return '';
  return `<section class="tp-why"><h2>Why you might like it</h2>${bits.map(b => `<p>${esc(b)}</p>`).join('')}</section>`;
}
function keepExploringBlock(m, relatedArticles, yearPath){
  const topicsHere = (typeof topics !== 'undefined' ? topics : []).filter(t => (t.movieSlugs || []).includes(m.slug));
  const gs = listedGenres(m);
  const links = [];
  const noun = (m.typeDir === 'series') ? 'series' : (m.typeDir === 'anime' ? 'anime' : 'movies');
  if (gs[0]) links.push(`<a href="${url(genrePath(m, gs[0]))}">More ${esc(gs[0])} ${noun}</a>`);
  if (m.year && yearPath) links.push(`<a href="${url(yearPath)}">${esc(String(m.year))} index</a>`);
  topicsHere.forEach(t => links.push(`<a href="${url('/topic/' + t.slug + '/')}">${esc(t.title)}</a>`));
  links.push(`<a href="${url('/articles/')}">BRYME guides</a>`);
  return `<section class="tp-next"><h2>Keep exploring</h2><p>Finished reading? Stay on BRYME — these are related pages, not download buttons.</p><div class="tp-next-links">${links.join('')}</div></section>`;
}
function articlesAboutTitle(m){
  const title = String(m.title || '').toLowerCase();
  const short = title.replace(/:.*/, '').trim();
  return (articleToMovies.get(m.slug) || []).filter(a => {
    const slugs = a.relatedMovieSlugs || [];
    if (slugs[0] === m.slug) return true;
    const hay = (a.title + ' ' + (a.description || '')).toLowerCase();
    return (title && hay.indexOf(title) > -1) || (short.length > 3 && hay.indexOf(short) > -1);
  }).slice(0, 3);
}
function relatedFor(m) {
  const typeDir = m.typeDir || 'movie';
  const manual = new Set(REL[m.slug] || []);
  const mGenres = listedGenres(m);
  const mCountries = countryTokens(m.country);
  const mDirectors = nameList(m.director).map(d => d.toLowerCase());
  const scored = movies
    .filter(x => x.id !== m.id && (x.typeDir || 'movie') === typeDir)
    .map(x => {
      let score = 0;
      if (manual.has(x.slug)) score += 100;
      const xGenres = listedGenres(x);
      for (const g of mGenres) if (xGenres.includes(g)) score += genreWeight(g);
      const xCountries = countryTokens(x.country);
      if (xCountries.some(c => mCountries.includes(c))) score += 4;
      const xDirectors = nameList(x.director).map(d => d.toLowerCase());
      if (xDirectors.some(d => mDirectors.includes(d))) score += 12;
      if (x.language && m.language && x.language === m.language) score += 1;
      if (x.year && m.year && Math.abs(x.year - m.year) <= 3) score += 1;
      if (x.rating && x.rating.value != null) score += x.rating.value / 10;
      return { x, score };
    })
    .filter(r => r.score >= 2)
    .sort((a, b) => (b.score - a.score) || ((b.x.rating?.value || 0) - (a.x.rating?.value || 0)) || ((b.x.year || 0) - (a.x.year || 0)) || a.x.title.localeCompare(b.x.title));
  const seen = new Set();
  const out = [];
  for (const r of scored) {
    const key = r.x.title.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(r.x);
    if (out.length === 6) break;
  }
  return out;
}
/* Seasons (series/anime only, optional) — architecture for future season data.
   Source: content/seasons.json (or a future catalogue field). Nothing is
   invented; if no seasons are recorded, no Seasons section is rendered. */
const seasonsPath = path.join(root, 'content', 'seasons.json');
let seasonsData = {};
if (fs.existsSync(seasonsPath)) {
  try { seasonsData = JSON.parse(fs.readFileSync(seasonsPath, 'utf8')); } catch (e) { warnings.push('seasons.json unreadable'); }
}
movies.forEach(m => {
  let seasons = seasonsData[m.slug] || [];
  if (!Array.isArray(seasons)) seasons = [];
  seasons = seasons.filter(x => x && typeof x === 'object').map(x => ({
    seasonNumber: Number(x.seasonNumber) || null,
    title: x.title ? clean(x.title) : null,
    year: Number(x.year) || null,
    episodeCount: Number(x.episodeCount) || null
  })).filter(x => x.seasonNumber != null);
  m.seasons = (m.typeDir === 'movie') ? [] : seasons;
  m.numberOfSeasons = m.seasons.length || null;
  m.numberOfEpisodes = m.seasons.reduce((sum, x) => sum + (x.episodeCount || 0), 0) || null;
});

/* ---- fact-derived prose for thin title pages ----
   Many title pages carry only a short one-line teaser, which reads as thin to a
   reader and a crawler. The metadata overlay (Wikidata/Wikipedia) already holds
   verified facts for most titles — director, cast, year, genre, country,
   language, runtime. This helper turns those verified facts into a short,
   factual "At a glance" paragraph. It assembles ONLY facts already on the
   record; it never invents plot, opinions, or ratings. If a longer in-house
   synopsis (longDescription) exists it takes precedence and this is skipped. */
function factBlurb(m){
  const isMovie = m.typeDir === 'movie';
  const noun = isMovie ? 'film' : (m.typeDir === 'anime' ? 'anime' : 'series');
  const sentences = [];
  const genres = listedGenres(m).map(g => g.toLowerCase()).filter(Boolean);
  const genreTxt = genres.length > 1 ? genres.slice(0, -1).join(', ') + ' and ' + genres[genres.length - 1] : (genres[0] || '');
  const dirs = nameList(m.director);
  const dirTxt = dirs.length > 1 ? dirs.slice(0, -1).join(', ') + ' and ' + dirs[dirs.length - 1] : (dirs[0] || '');
  const ident = [];
  if (genreTxt) ident.push(genreTxt + ' ' + noun);
  if (dirTxt) ident.push('directed by ' + dirTxt);
  if (m.year) ident.push('released in ' + m.year);
  if (ident.length) {
    const firstWord = (genres[0] || '').replace(/^\(/,'');
    const useAn = /^[aeiou]/i.test(firstWord) && !/^uni|^eu|^one/.test(firstWord);
    const prefix = genreTxt ? (useAn ? ' is an ' : ' is a ') : ' is ';
    let s = m.title + prefix + ident.join(', ');
    s = s.replace(', and released in', ' and released in').replace(', released in', ' and released in').replace(', directed by', ' directed by');
    sentences.push(s + '.');
  }
  const origin = [];
  const originCountry = primaryCountry(m);
  if (originCountry) origin.push('from ' + originCountry);
  if (m.language && String(m.language).toLowerCase() !== 'english') origin.push('spoken in ' + m.language);
  if (origin.length) sentences.push('It comes ' + origin.join(', ') + '.');
  const castTxt = (m.cast && m.cast.length) ? m.cast.slice(0, 4).join(', ') : null;
  if (castTxt) sentences.push('The cast includes ' + castTxt + '.');
  if (m.runtime) { const mins = parseInt(String(m.runtime).replace(/[^0-9]/g, ''), 10); if (mins > 0) sentences.push('The ' + noun + ' runs about ' + mins + ' minutes.'); }
  if (sentences.length) return sentences.join(' ');
  if (castTxt) return 'The cast of ' + m.title + ' includes ' + castTxt + '.';
  return '';
}

for (const m of movies) {
  const typeDir = m.typeDir || 'movie';
  const label = m.typeLabel;
  const schemaType = typeDir === 'series' ? 'TVSeries' : (typeDir === 'anime' ? (animeFilms.has(m.slug) ? 'Movie' : 'TVSeries') : 'Movie');
  const typeWord = typeDir === 'series' ? 'Series Overview' : (typeDir === 'anime' ? 'Anime Overview' : 'Movie Overview');
  const seoTitle = m.year ? `${m.title} (${m.year})` : m.title;
  const genreText = listedGenres(m)[0] || '';
  const seoDesc = `${m.title}${m.year ? ' (' + m.year + ')' : ''} — ${m.typeLabel.toLowerCase()}${genreText ? ' ' + genreText.toLowerCase() : ''} on BRYME. Trailer, story and legal viewing options.`;
  const relatedArts = (articleToMovies.get(m.slug) || []).slice(0, 2);
  const schema = { '@context':'https://schema.org', '@type':schemaType, name:m.title, description:m.description || m.teaser || undefined, dateCreated:m.year ? String(m.year) : undefined, genre:genreText || undefined, sameAs:m.trailer || undefined, image: posterOrCard(m) || undefined };
  if (primaryCountry(m)) schema.countryOfOrigin = primaryCountry(m);
  if (m.language) schema.inLanguage = m.language;
  /* Verified credits (Wikidata/Wikipedia overlay) — only emitted when real. */
  if (m.director) {
    const directors = nameList(m.director);
    if (directors.length) schema.director = directors.map(name => ({ '@type':'Person', name }));
  }
  if (m.cast && m.cast.length) schema.actor = m.cast.map(name => ({ '@type':'Person', name }));
  if (m.runtime) {
    const mins = parseInt(String(m.runtime).replace(/[^0-9]/g, ''), 10);
    if (mins > 0) schema.duration = `PT${mins}M`;
  }
  if (schemaType === 'TVSeries' && m.year) schema.startDate = String(m.year);
  if (schemaType === 'TVSeries' && m.numberOfSeasons) schema.numberOfSeasons = m.numberOfSeasons;
  if (schemaType === 'TVSeries' && m.numberOfEpisodes) schema.numberOfEpisodes = m.numberOfEpisodes;
  if (relatedArts.length) schema.about = relatedArts.map(a => ({ '@type':'Article', name:a.title, url:url('/article/' + a.slug + '/') }));
  Object.keys(schema).forEach(k => schema[k] === undefined && delete schema[k]);
  const pagePath = `/${typeDir}/${m.slug}/`;
  schema.url = pagePath;
  const yearPath = m.year ? (typeDir === 'movie' ? '/year/' + m.year + '/' : '/' + typeDir + '/' + m.year + '/') : '';
  const yearLabel = m.year ? (typeDir === 'movie' ? m.year + ' movies' : (typeDir === 'series' ? m.year + ' series' : m.year + ' anime')) : null;
  const listLabel = label === 'TV Series' ? 'TV Series' : (label === 'Anime' ? 'Anime' : 'Movies');
  const listPath = '/' + (typeDir === 'movie' ? 'movies' : typeDir) + '/';
  const crumbs = [{name:'Home', path:'/'}, {name: listLabel, path: listPath}];
  if (genreText) crumbs.push({name: genreText, path: genrePath(m, genreText)});
  const schemaList = [schema, breadcrumbs(crumbs)];
  // VideoObject structured data is emitted ONLY when the primary trailer is a
  // verified official video whose title we actually know from oEmbed. No
  // fabricated upload dates, durations or creators.
  if (m.trailers.length && m.trailerType && m.trailerType !== 'fan-made' && m.trailerVerified) {
    const t0 = m.trailers[0];
    const extra = VIDEO_EDITORIAL[m.slug];
    const match = !!(extra && extra.videoId === t0.videoId);
    const vo = { '@context':'https://schema.org', '@type':'VideoObject', name: (match && extra.name) || t0.videoTitle || (m.title + ' official trailer'), description: (match && extra.description) || ('Official trailer for ' + m.title + '.'), thumbnailUrl: (match && extra.thumbnailUrl) || ('https://i.ytimg.com/vi/' + t0.videoId + '/hqdefault.jpg'), embedUrl: 'https://www.youtube-nocookie.com/embed/' + t0.videoId };
    if (match && extra.uploadDate) vo.uploadDate = extra.uploadDate;
    if (t0.channel) vo.publisher = { '@type':'Organization', name: t0.channel };
    // Google Video rich results require uploadDate. Do not emit a VideoObject
    // we cannot date — an incomplete block is a validation error, not a rich result.
    if (vo.uploadDate) schemaList.push(vo);
  }
  crumbs.push({name:m.title, path:pagePath});
  const related = relatedFor(m);
  const relatedArticles = articlesAboutTitle(m);
  write(`${typeDir}/${m.slug}`, layout({
    title: (SENDABLE_META[m.slug] && SENDABLE_META[m.slug].title) || seoTitle,
    description: (SENDABLE_META[m.slug] && SENDABLE_META[m.slug].desc) || ((m.description || '').length >= 80 ? (m.description || seoDesc) : seoDesc),
    path: pagePath,
    activeNav: typeDir === 'movie' ? 'movies' : (typeDir === 'series' ? 'series' : 'anime'),
    schema: schemaList,
    image: posterOrCard(m),   /* designed card when there is no poster or trailer thumbnail */
    body: `<main class="shell tp-page" data-video-landing><div class="crumb"><a href="${url('/')}">Home</a> / <a href="${url(listPath)}">${esc(listLabel)}</a>${genreText ? ` / <a href="${url(genrePath(m, genreText))}">${esc(genreText)}</a>` : ''} / ${esc(m.title)}</div>
  <section class="shell trailer-section" id="trailer">${trailerSection(m)}</section>
  <section class="movie-hero movie-hero-compact" style="--movie-backdrop:url('${esc(poster(m))}')">
    ${image(m)}
    <div>
      <div class="hero-kicker tp-kicker-meta"><span class="type-badge tb-${typeDir}">${typeDir === 'series' ? 'SERIES' : (typeDir === 'anime' ? 'ANIME' : 'MOVIE')}</span>${m.year ? `<span>${m.year}</span>` : ''}${genreText ? `<span class="dot">·</span><span>${esc(genreText)}</span>` : ''}${runtimeLabel(m) ? `<span class="dot">·</span><span>${esc(runtimeLabel(m))}</span>` : ''}${primaryCountry(m) ? `<span class="dot">·</span><span>${esc(primaryCountry(m))}</span>` : ''}</div>
      <h1>${esc(m.title)}</h1>
      <div class="badges">${m.rating && m.rating.value != null ? `<span class="badge" title="BRYME editorial score — not IMDb, Rotten Tomatoes or audience ratings">★ ${esc(String(m.rating.value))}/10 · BRYME Editorial</span>` : ''}${m.trending ? `<span class="badge" title="Editorially curated — not live traffic data">🔥 Trending #${m.trendingRank}</span>` : ''}${m.popular ? `<span class="badge" title="Editorial popular pick">⭐ Popular</span>` : ''}${m.editorPick ? `<span class="badge" title="BRYME editor's recommendation">👑 Editor's Pick</span>` : ''}</div>
      ${(() => {
        const ed = editorialOf(m);
        const hook = (ed && ed.hook) || ((m.teaser && m.description && m.teaser.trim() && m.teaser.trim() !== m.description.trim()) ? m.teaser.trim() : (m.description || m.teaser || '').trim());
        return hook ? `<p class="lead">${esc(hook)}</p>` : '';
      })()}
      <div class="hero-actions">${m.youtubeId ? `<a class="cta" href="#trailer">Watch trailer</a>` : ''}<a class="cta cta-ghost" href="#watch">Where to watch</a>${related.length ? `<a class="quiet-link" href="#loved">More like this</a>` : ''}${relatedArticles.length ? `<a class="cta cta-ghost" href="${url('/article/' + relatedArticles[0].slug + '/')}">Read BRYME story</a>` : ''}<button class="quiet-link share-action" type="button" data-share-path="${pagePath}" data-share-title="${esc(m.title)}">Share</button></div>
      ${SENDABLE_META[m.slug] ? sendBar(pagePath, SENDABLE_META[m.slug].title || m.title) : ''}
    </div>
  </section>
  ${lovedBlock(m, related)}
  <section class="body">
    <article class="prose">
      ${nowTalkingBlock(m)}
      ${verdictBlock(m)}
      ${(() => {
        const ed = editorialOf(m);
        if (ed && ed.summary) return `<h2>Quick summary</h2><p>${esc(ed.summary)}</p>`;
        const hook = (m.teaser && m.description && m.teaser.trim() && m.teaser.trim() !== m.description.trim()) ? m.teaser.trim() : '';
        const full = (m.description || '').trim();
        if (hook && full && full !== hook) return `<h2>Quick summary</h2><p>${esc(full)}</p>`;
        return '';
      })()}
      ${(() => {
        const ed = editorialOf(m);
        const long = m.longDescription || m.synopsis || m.about || '';
        const fb = factBlurb(m);
        const parts = [];
        if (ed && Array.isArray(ed.about)) ed.about.forEach(p => parts.push(`<p>${esc(p)}</p>`));
        else if (fb) parts.push(`<p>${esc(fb)}</p>`);
        if (long && long.trim() && long.trim() !== (m.description || '').trim()) {
          long.trim().split(/\n{2,}/).forEach(t => parts.push(`<p>${esc(t.trim())}</p>`));
        }
        if (!parts.length) return '';
        return `<h2>What ${esc(m.title)} is about</h2>` + parts.join('');
      })()}
      ${whyYouMightLikeBlock(m, related)}
      ${relatedArticles.length ? `<section class="tp-editorial"><h2>BRYME editorial</h2><p>Only real BRYME pieces are listed here. This is not a generated review and not a claim that BRYME watched the title on your behalf.</p><div class="story-grid story-grid-title">${relatedArticles.map(a => `<a href="${url('/article/' + a.slug + '/')}"><span>${esc(a.category)}</span><h3>${esc(a.title)}</h3><p>${esc((a.description || '').slice(0, 140))}</p><b>Read article</b></a>`).join('')}</div></section>` : ''}
      ${related.length ? `<div class="grid tp-related" hidden>${related.map(card).join('')}</div>` : ''}
      <div class="tp-boring" id="details-more">
      ${m.facts.length ? `<h2>Notes</h2><ul>${m.facts.map(f => `<li>${esc(f)}</li>`).join('')}</ul>` : ''}
      ${(typeDir !== 'movie' && m.seasons.length) ? `<h2>Seasons</h2><div class="list">${m.seasons.map(x => `<div class="row"><div><b>${esc(x.title || ('Season ' + x.seasonNumber))}</b><span class="meta" style="font-size:12px;color:var(--muted)">${x.year ? x.year + ' · ' : ''}${x.episodeCount ? x.episodeCount + ' episodes' : 'episode count unavailable'}</span></div></div>`).join('')}</div>` : ''}
      ${whereToWatchBlock(m)}
      ${keepExploringBlock(m, relatedArticles, yearPath)}
      </div>
    </article>
    <aside class="aside">
      <h2>Details</h2>
      <dl>
        <div><dt>Title</dt><dd>${esc(m.title)}</dd></div>
        <div><dt>Type</dt><dd>${esc(label)}</dd></div>
        ${m.year ? `<div><dt>Year</dt><dd>${m.year}</dd></div>` : ''}
        ${genreText ? `<div><dt>Genre</dt><dd>${listedGenres(m).map(g => `<a href="${url(genrePath(m, g))}">${esc(g)}</a>`).join(', ')}</dd></div>` : ''}
        ${detailsCountry(m) ? `<div><dt>Country</dt><dd>${esc(detailsCountry(m))}</dd></div>` : ''}
        ${m.language ? `<div><dt>Language</dt><dd>${esc(m.language)}</dd></div>` : ''}
        ${m.runtime ? `<div><dt>Runtime</dt><dd>${esc(m.runtime)}</dd></div>` : ''}
        ${m.director ? `<div><dt>Director</dt><dd>${esc(m.director)}</dd></div>` : ''}
        ${m.cast && m.cast.length ? `<div><dt>Cast</dt><dd>${m.cast.map(esc).join('; ')}</dd></div>` : ''}
        ${yearPath ? `<div><dt>Year index</dt><dd><a href="${url(yearPath)}">${esc(yearLabel)}</a></dd></div>` : ''}
        ${m.trending ? `<div><dt>Trending</dt><dd>🔥 #${m.trendingRank} (editorially curated)${m.trendingUntil ? ` · until ${m.trendingUntil}` : ''}</dd></div>` : ''}
        ${m.popular ? `<div><dt>Popular</dt><dd>⭐ #${m.popularRank} (editorial popular pick)</dd></div>` : ''}
        ${m.editorPick ? `<div><dt>Editor's Pick</dt><dd>👑 #${m.editorPickRank}${m.editorPickNote ? ` — ${esc(m.editorPickNote)}` : ''}</dd></div>` : ''}
      </dl>
      ${m.metaSource ? `<p class="meta-source">${m.runtimeSource ? 'Director, country and language' : 'Director, runtime, country and language'} from <a href="${esc(m.metaSource.url)}" rel="nofollow noopener">${esc(m.metaSource.name || 'Wikidata')}</a>${m.castSource && m.castSource.url ? `; billed cast from <a href="${esc(m.castSource.url)}" rel="nofollow noopener">${esc(m.castSource.name || 'Wikipedia')}</a>` : ''}${m.metaSource.retrieved ? ` · retrieved ${esc(m.metaSource.retrieved)}` : ''}.${m.runtimeSource ? ` Runtime checked against <a href="${esc(m.runtimeSource.url)}" rel="nofollow noopener">${esc(m.runtimeSource.name || 'source')}</a>${m.runtimeSource.retrieved ? ` on ${esc(m.runtimeSource.retrieved)}` : ''}.` : ''} BRYME's synopsis and editorial score are written in-house.</p>` : ''}
    </aside>
  </section></main>`
  }));
  if (typeDir !== 'movie') {
    write(`movie/${m.slug}`, layout({
      title: `${m.title} has moved`,
      description: `This ${m.typeLabel.toLowerCase()} page has moved. Continue to ${m.title} on BRYME.`,
      path: `/movie/${m.slug}/`, canonical: pagePath, noindex: true, image: poster(m),
      body: `<main class="shell"><section class="hero"><div class="eyebrow">Moved</div><h1>${esc(m.title)} has moved</h1><p class="lead">This title now lives on its ${esc(m.typeLabel.toLowerCase())} page.</p><p><a class="cta" href="${url(pagePath)}">Continue to ${esc(m.title)}</a></p></section></main><meta http-equiv="refresh" content="0;url=${url(pagePath)}">`
    }));
  }
}

/* ---------------- Articles & topics ---------------- */
function linkedEsc(raw) {
  const parts = String(raw || '').split(/(\{(?:film|article):[a-z0-9-]+\})/i);
  return parts.map(part => {
    const m = part.match(/^\{(film|article):([a-z0-9-]+)\}$/i);
    if (!m) return esc(part);
    const kind = m[1].toLowerCase(), slug = m[2];
    if (kind === 'article') {
      const a = articles.find(x => x.slug === slug);
      if (!a) return esc(slug);
      return `<a href="${url('/article/' + a.slug + '/')}">${esc(a.title)}</a>`;
    }
    const rec = slugIndex.get(slug);
    if (!rec) return esc(slug);
    return `<a href="${url('/' + (rec.typeDir || 'movie') + '/' + rec.slug + '/')}">${esc(rec.title)}</a>`;
  }).join('');
}
function articleBlocks(article) {
  if (article.blocks && article.blocks.length) return article.blocks.map(block => {
    const text = linkedEsc(block.text);
    if (block.type === 'heading') return `<h2>${esc(block.text)}</h2>`;
    if (block.type === 'quote') return `<blockquote>${text}</blockquote>`;
    if (block.type === 'source') return `<p class="article-source">${text}</p>`;
    return `<p>${text}</p>`;
  }).join('');
  return (article.items || []).map(item => {
    const paras = String(item.body || '').split(/\n\n+/).map(p => `<p>${linkedEsc(p.trim())}</p>`).join('');
    return `<h2>${esc(item.heading)}</h2>` + paras;
  }).join('');
}
function articleWordCount(article) {
  const text = article.blocks && article.blocks.length ? article.blocks.map(b => b.text).join(' ') : (article.items || []).map(i => i.heading + ' ' + i.body).join(' ');
  return text.trim().split(/\s+/).filter(Boolean).length;
}
write('articles', layout({
  title: 'Editorial – Movie, Series & Anime guides',
  description: 'Original editorial from BRYME: movie lists, explainers and guides that link back to the catalogue.',
  path: '/articles/', activeNav: 'articles',
  body: `<main class="shell"><section class="ent-feature ent-feature-photo" style="--hero-img:url('/assets/img/ent/hero-cinema.jpg')"><div class="ent-feature-inner"><div class="eyebrow">Editorial</div><h1>Stories behind the screen.</h1><p>Original guides and lists — separate from the catalogue, and always linking back to the movies, series and anime they talk about.</p></div></section><section class="section"><div class="story-grid">${articles.map(a => storyPhoto('/article/' + a.slug + '/', a.category, a.title, a.description || '', heroFor(a.slug, 'entertainment'))).join('')}</div></section></main>`
}));
for (const a of articles) {
  const relatedMovies = (a.relatedMovieSlugs || []).map(slug => slugIndex.get(slug)).filter(Boolean);
  const relatedStories = articles.filter(x => x.slug !== a.slug && (x.category === a.category || x.tags.some(t => a.tags.includes(t)))).slice(0, 3);
  const schema = { '@context':'https://schema.org', '@type':'Article', headline:a.title, description:a.description, mainEntityOfPage:url(`/article/${a.slug}/`), publisher:{'@type':'Organization', name:site.name} };
  if (a.author) schema.author = { '@type': 'Person', name: a.author };
  write(`article/${a.slug}`, layout({
    title: (SENDABLE_META[a.slug] && SENDABLE_META[a.slug].title) || a.title,
    description: (SENDABLE_META[a.slug] && SENDABLE_META[a.slug].desc) || a.description,
    path: `/article/${a.slug}/`, activeNav: 'articles', ogType: 'article',
    schema: [schema, breadcrumbs([{name:'Home', path:'/'}, {name:'Articles', path:'/articles/'}, {name:a.title, path:`/article/${a.slug}/`}])],
    image: heroFor(a.slug, 'entertainment'),
    body: `<main class="shell"><div class="crumb"><a href="${url('/articles/')}">Editorial</a> / ${esc(a.title)}</div><section class="article-hero article-hero-photo" style="--hero-img:url('${heroFor(a.slug, 'entertainment')}')"><div class="eyebrow">${esc(a.category)}</div><h1>${esc(a.title)}</h1><p class="lead">${esc(a.description)}</p><div class="article-meta">${a.author ? 'By ' + esc(a.author) + ' · ' : ''}Editorial guide · ${a.createdAt ? 'Published ' + esc(a.createdAt) + ' · ' : ''}${a.updatedAt ? 'Last updated ' + esc(a.updatedAt) + ' · ' : ''}Reading time: about ${Math.max(2, Math.ceil(articleWordCount(a) / 220))} minutes</div>${SENDABLE_META[a.slug] ? sendBar("/article/" + a.slug + "/", SENDABLE_META[a.slug].title || a.title) : `<button class="quiet-link share-action" type="button" data-share-path="/article/${a.slug}/" data-share-title="${esc(a.title)}">Share</button>`}</section><article class="prose article-body">${articleBlocks(a)}<section class="article-related"><h2>Related titles</h2>${relatedMovies.length ? `<div class="grid">${relatedMovies.map(card).join('')}</div>` : '<p>Related titles will be added when there is a useful match.</p>'}<h2>Keep reading</h2>${relatedStories.length ? `<div class="list">${relatedStories.map(articleRow).join('')}</div>` : ''}</section></article></main>`
  }));
}
write('topics', layout({
  title: 'Topics – focused collections',
  description: 'Explore focused movie, series and anime collections on BRYME.', path: '/topics/',
  body: `<main class="shell"><section class="hero"><div class="eyebrow">Explore by topic</div><h1>Collections with a point of view.</h1><p class="lead">Focused routes through the catalogue and related editorial reading.</p></section><section class="section"><div class="story-grid">${topics.map(t => `<a href="${url('/topic/' + t.slug + '/')}"><span>Topic</span><h3>${esc(t.title)}</h3><p>${esc(t.description)}</p><b>Explore collection</b></a>`).join('') || '<p>No topic collections are published yet.</p>'}</div></section></main>`
}));
for (const topic of topics) {
  const topicMovies = (topic.movieSlugs || []).map(slug => slugIndex.get(slug)).filter(Boolean);
  const topicArticles = (topic.articleSlugs || []).map(slug => articles.find(a => a.slug === slug)).filter(Boolean);
  write(`topic/${topic.slug}`, layout({
    title: topic.title, description: topic.description, path: `/topic/${topic.slug}/`,
    schema: { '@context':'https://schema.org', '@type':'CollectionPage', name:topic.title, description:topic.description, url:url(`/topic/${topic.slug}/`) },
    body: `<main class="shell"><div class="crumb"><a href="${url('/topics/')}">Topics</a> / ${esc(topic.title)}</div><section class="hero"><div class="eyebrow">Topic collection</div><h1>${esc(topic.title)}</h1><p class="lead">${esc(topic.description)}</p></section><section class="section"><h2>Featured titles</h2><div class="grid">${topicMovies.map(card).join('')}</div></section><section class="section"><h2>Related reading</h2>${topicArticles.length ? `<div class="list">${topicArticles.map(articleRow).join('')}</div>` : '<p>Related editorial reading will be added when useful.</p>'}</section></main>`
  }));
}
const articleCategoryMap = new Map();
articles.forEach(a => { const s = slugify(a.category); if (!articleCategoryMap.has(s)) articleCategoryMap.set(s, {name:a.category, articles:[]}); articleCategoryMap.get(s).articles.push(a); });
for (const [slug, category] of articleCategoryMap) {
  const catCount = (category.items || category.articles || []).length;
  if (catCount < THIN_ARCHIVE_MIN) THIN_LISTING_PATHS.add(`/articles/${slug}/`);
  write(`articles/${slug}`, layout({
  noindex: catCount < THIN_ARCHIVE_MIN,
  title: `${category.name} articles`, description: `Original ${category.name.toLowerCase()} guides from BRYME.`, path: `/articles/${slug}/`, activeNav: 'articles',
  body: `<main class="shell"><section class="hero"><div class="eyebrow">Editorial category</div><h1>${esc(category.name)}</h1><p class="lead">Useful guides and original editorial reading.</p></section><section class="section"><div class="list">${category.articles.map(articleRow).join('')}</div></section></main>`
}));
}

/* ---------------- Trailer admin audit page ---------------- */
const trailerAdminJson = JSON.stringify(trailerAdminRows).replace(/</g, '\\u003c');
const trailerAdminFilters = `<div class="trailer-admin-filters"><select id="ta-filter"><option value="">All trailer states</option><option value="official">Official trailers</option><option value="fan-made">Community/fan-made trailers</option><option value="broken">Broken / wrong / unverifiable</option><option value="none">No trailer</option></select><input id="ta-q" placeholder="Search title or slug…" autocomplete="off"></div>`;
write('trailers', layout({
  title: 'Trailer status audit',
  description: "Internal trailer audit for BRYME: every title\u2019s trailer state, source channel and verification date.",
  path: '/trailers/', noindex: true,
  body: `<main class="shell"><section class="hero"><div class="eyebrow">Internal audit</div><h1>Trailer status</h1><p class="lead">Every title's trailer state — official, community fallback or none — with channel and last-check date. Editing is done via content/trailers.json (see scripts/trailer_admin.py); this page is read-only.</p></section><section class="section">${trailerAdminFilters}<div class="trailer-table-wrap" style="overflow-x:auto"><table class="trailer-table"><thead><tr><th>Title</th><th>State</th><th>Type</th><th>Video ID</th><th>Channel</th><th>Verified</th><th>Last checked</th></tr></thead><tbody id="ta-body"></tbody></table></div></section><script id="trailer-admin-data" type="application/json">${trailerAdminJson}<\/script></main>`
}));
/* ================================================================
   TRUST / LEGAL PAGES — About, Contact, Privacy, Terms, Disclaimer,
   Copyright/DMCA, Editorial Policy. Indexable, footer-linked only.
   ================================================================ */
function legalBody(sections){
  return sections.map(sec =>
    sec.h ? `<h2>${esc(sec.h)}</h2>` + (sec.p ? sec.p.map(p => `<p>${p}</p>`).join('') : '')
          : (sec.p ? sec.p.map(p => `<p>${p}</p>`).join('') : '')
  ).join('');
}
const LEGAL_CONTACT_EMAIL = 'Sodiqibrahim03@gmail.com';
const LEGAL_WHATSAPP = '0815 643 0614';
const legalPages = [
  {
    dir: 'about', schemaType: 'AboutPage',
    title: 'About BRYME – Entertainment Discovery Platform',
    description: 'What BRYME is: an entertainment discovery platform for movies, TV series and anime — with trailers, editorial guides and curated recommendations.',
    hero: 'About BRYME', eyebrow: 'About', lead: 'An entertainment discovery platform for movies, TV series and anime.',
    sections: [
      { h: 'What BRYME is', p: ['BRYME is an entertainment discovery website focused on movies, TV series and anime. It helps visitors find titles worth watching by combining a curated catalogue, verified trailer links and original editorial articles.', 'The site is built around discovery: browse by content type, genre, year or country; search across the catalogue; read personal, opinionated articles; and watch official trailers where they are available.'] },
      { h: 'What you will find here', p: ['Movies, TV series and anime with clean title pages that include synopses, key details (year, country, language, genre), related titles and editorial links when they exist.', 'Trailers are linked or embedded from external platforms such as YouTube. BRYME does not host video files and does not claim ownership of third-party trailers, posters or clips unless explicitly stated.', 'Editorial articles are written by BRYME and reflect the personal opinions of their authors.'] },
      { h: 'Who is behind BRYME', p: ['BRYME is created and edited by its founder as an independent entertainment discovery project. Editorial articles are published under the author name shown on each article.'] },
      { h: 'A note on trailers and images', p: ['Trailer thumbnails and embedded players come from YouTube (using YouTube\'s privacy-enhanced domain for embeds). Availability of any trailer is controlled by the external platform and the uploader, not by BRYME. If a trailer becomes unavailable, the site shows a clean \u201cTrailer unavailable\u201d state instead of a broken player.'] }
    ]
  },
  {
    dir: 'contact', schemaType: 'ContactPage',
    title: 'Contact BRYME – Report Issues & Send Feedback',
    description: 'Contact BRYME about incorrect information, trailer or link issues, copyright concerns or general feedback.',
    hero: 'Contact BRYME', eyebrow: 'Contact', lead: 'Questions, corrections, feedback — we want to hear from you.',
    sections: [
      { h: 'Email', p: [LEGAL_CONTACT_EMAIL] },
      { h: 'WhatsApp', p: [LEGAL_WHATSAPP + ' — fastest reply'] },
      { h: 'What to contact us about', p: ['Incorrect or outdated information on any title page.', 'Broken trailer links or trailers that have become unavailable.', 'Copyright concerns (see the Copyright / DMCA page for the full procedure).', 'General feedback, suggestions or questions about the site.'] },
      { h: 'How to make reporting easier', p: ['When reporting an issue, include the exact page URL and a short description of the problem. For copyright matters, please follow the reporting procedure on the Copyright / DMCA page.'] }
    ]
  },
  {
    dir: 'privacy', schemaType: 'WebPage',
    title: 'Privacy Policy – BRYME',
    description: 'BRYME privacy policy: what information is collected, how it is used, external services, cookies, analytics status and your rights.',
    hero: 'Privacy Policy', eyebrow: 'Legal', lead: 'Clear and honest information about privacy on BRYME.',
    sections: [
      { h: 'Information you provide voluntarily', p: ['If you contact BRYME by email or WhatsApp, you voluntarily provide the information contained in your message (such as your email address and the content of your enquiry). BRYME uses that information only to respond to you.'] },
      { h: 'Information collected automatically', p: ['BRYME is hosted on Render. Like most hosts, Render and its CDN may process standard technical data (such as IP addresses and request logs) as part of operating the service. BRYME itself does not run analytics tracking on its pages.'] },
      { h: 'Cookies and local storage', p: ['BRYME uses local storage for preferences you choose on the site (for example theme and the Make Money country filter). A short-lived local record is also used so the interruptive ad is not shown on every page. We do not build a personal profile from that data. Advertising partners may set their own cookies or similar identifiers — see Advertising below.'] },
      { h: 'Analytics', p: ['BRYME does not currently use Google Analytics or any other analytics service. If analytics is introduced in the future, this policy will be updated to describe it.'] },
      { h: 'External services and YouTube', p: ['Trailers are embedded from YouTube using the privacy-enhanced youtube-nocookie.com domain. When you play a trailer, YouTube\'s own privacy policy and cookie practices apply. BRYME has no control over YouTube\'s data handling.', 'Links to third-party websites (such as streaming platforms) leave BRYME; those websites have their own privacy policies.'] },
      { h: 'Advertising', p: ['BRYME does not currently load third-party advertising. Advertising will not be reintroduced until the privacy policy, consent controls and published ad experience accurately describe the deployed behavior.'] },
      { h: 'How information may be used', p: ['Information you send us is used to respond to your enquiry, improve the website and address reported issues. BRYME does not sell personal information.'] },
      { h: 'Data retention', p: ['Correspondence is kept only as long as needed to handle the enquiry. BRYME does not maintain user accounts or store visitor profiles.'] },
      { h: 'Your rights', p: ['You may contact BRYME at any time to ask what information we hold about you, to request correction or deletion, or to ask questions about this policy.'] },
      { h: 'Policy updates', p: ['This policy may be updated as the website evolves. Changes will be reflected on this page.'] },
      { h: 'Contact', p: ['Questions about privacy can be sent to ' + LEGAL_CONTACT_EMAIL + '.'] }
    ]
  },
  {
    dir: 'terms', schemaType: 'WebPage',
    title: 'Terms of Use – BRYME',
    description: 'The terms governing your use of BRYME: acceptable use, content, external links, intellectual property and liability.',
    hero: 'Terms of Use', eyebrow: 'Legal', lead: 'The rules for using BRYME.',
    sections: [
      { h: 'Acceptable use', p: ['Use BRYME for lawful, personal, non-commercial discovery purposes. Do not attempt to disrupt the website, scrape it at scale, or use it in any way that could damage or overload the service.'] },
      { h: 'Website content', p: ['Catalogue descriptions, articles and editorial content are provided for entertainment and discovery purposes. Editorial articles reflect the personal opinions of their authors and are clearly opinionated where relevant.'] },
      { h: 'External links and embedded content', p: ['BRYME links to and embeds content from external platforms such as YouTube and third-party streaming services. BRYME does not control those platforms, their content, their availability or their policies.'] },
      { h: 'Accuracy limitations', p: ['While BRYME aims for accuracy, catalogue information, synopses, years, genres and trailer availability may contain errors or become outdated. Information should be verified independently before relying on it.'] },
      { h: 'Intellectual property', p: ['BRYME does not claim ownership of third-party trailers, posters, film footage or other copyrighted material belonging to studios, distributors or rights holders. All trademarks and copyrighted works belong to their respective owners.', 'Original BRYME editorial text and site content are the property of BRYME unless stated otherwise.'] },
      { h: 'User responsibilities', p: ['Users are responsible for how they use the information on the site and for their own decisions about what to watch and where to watch it.'] },
      { h: 'Availability', p: ['BRYME is provided as a static website hosted on Render. Availability depends on the hosting service and is provided on a best-effort basis without guarantee of uninterrupted access.'] },
      { h: 'Changes to the service', p: ['BRYME may change, add or remove features, content and pages at any time. These terms may also be updated; continued use of the site after changes means you accept the updated terms.'] },
      { h: 'Limitation of liability', p: ['BRYME is provided \u201cas is\u201d. To the maximum extent permitted by law, BRYME and its operator are not liable for any loss arising from the use of the site, reliance on its content, or the unavailability of third-party trailers or links.'] },
      { h: 'Contact', p: ['Questions about these terms can be sent to ' + LEGAL_CONTACT_EMAIL + '.'] }
    ]
  },
  {
    dir: 'disclaimer', schemaType: 'WebPage',
    title: 'Disclaimer – BRYME',
    description: 'BRYME disclaimer: an entertainment discovery platform; information may change, trailers are controlled by external platforms.',
    hero: 'Disclaimer', eyebrow: 'Legal', lead: 'Please read this before relying on anything you find here.',
    sections: [
      { h: 'Discovery platform', p: ['BRYME is an entertainment discovery and information platform. It helps visitors find movies, TV series and anime worth watching. It is not a streaming service and does not host video content.'] },
      { h: 'Information accuracy', p: ['Information on BRYME — including synopses, years, genres, countries and editorial claims — is provided in good faith but may contain errors or become outdated. Verify important information independently.'] },
      { h: 'Trailer availability', p: ['Trailers are provided by external platforms such as YouTube. Those platforms and their uploaders control the videos: a trailer can be removed, made private or restricted at any time. BRYME does not guarantee that any trailer will remain available, embeddable or playable.'] },
      { h: 'Third-party websites', p: ['Links to external websites lead away from BRYME. Those websites have their own terms, privacy policies and content. BRYME is not responsible for them.'] },
      { h: 'Editorial opinions', p: ['Articles on BRYME express the personal opinions of their authors. Rankings and recommendations are subjective unless explicitly stated otherwise.'] },
      { h: 'Advertising', p: ['BRYME does not currently load third-party ads. Any future advertising must be disclosed in the privacy policy and kept separate from editorial content.'] },
      { h: 'No professional advice', p: ['Nothing on BRYME constitutes professional, financial, legal or any other form of professional advice.'] }
    ]
  },
  {
    dir: 'copyright', schemaType: 'WebPage',
    title: 'Copyright & DMCA – BRYME',
    description: 'BRYME copyright notice and reporting procedure for rights holders concerned about potentially infringing material.',
    hero: 'Copyright / DMCA', eyebrow: 'Legal', lead: 'BRYME respects the rights of copyright owners.',
    sections: [
      { h: 'Our position', p: ['BRYME does not host video files, movies or television content. Trailers are linked or embedded from external platforms such as YouTube, and thumbnails are YouTube\'s generated preview images. BRYME does not claim ownership of third-party posters, trailers, screenshots or other copyrighted material — those belong to their respective owners.'] },
      { h: 'Reporting potentially infringing material', p: ['If you are a rights holder and believe material on BRYME infringes your copyright, contact us with the following information:', '1. The exact URL(s) on BRYME where the material appears.', '2. Identification of the copyrighted work you believe is affected.', '3. Your relationship to the material (for example, rights holder or authorized representative).', '4. Contact details so we can reply to you.'] },
      { h: 'How to report', p: ['Send reports to ' + LEGAL_CONTACT_EMAIL + '. Every legitimate report will be reviewed, and material that is found to infringe will be removed or corrected promptly.'] },
      { h: 'What happens next', p: ['BRYME reviews each report on its merits. Where a trailer or thumbnail is hosted by a third party such as YouTube, we may also point you to that platform\'s own reporting tools, since they control the underlying content.'] }
    ]
  },
  {
    dir: 'editorial-policy', schemaType: 'WebPage',
    title: 'Editorial Policy – BRYME',
    description: 'How BRYME articles are written: entertainment-focused, opinionated where labelled, fact-checked, correctable and transparent about sponsored content.',
    hero: 'Editorial Policy', eyebrow: 'Information', lead: 'How BRYME writes and publishes its articles.',
    sections: [
      { h: 'Purpose', p: ['BRYME articles are written for entertainment and discovery purposes: to help readers find something worth watching, understand why a title works, and compare options. They are not academic reviews and not objective buyer-style rankings unless explicitly stated.'] },
      { h: 'Opinions are subjective', p: ['Many articles are opinionated. Authors share personal views — which series gripped them, which anime they prefer and why. These opinions belong to the author and are presented as opinions, not universal facts.'] },
      { h: 'Facts and sources', p: ['Where articles state factual information — release years, episode counts, plot basics — BRYME aims for accuracy and checks facts against reliable sources. External sources may be referenced where appropriate. If a specific fact cannot be verified, it is not invented.'] },
      { h: 'Distinguishing opinion from fact', p: ['BRYME tries to keep the distinction clear: descriptive information (what a series is about, when it aired) is presented as information, while judgments (whether it is good, which one is better) are presented as the author\'s opinion.'] },
      { h: 'Corrections', p: ['When errors are discovered — in facts, links or metadata — BRYME will correct them as soon as practical. Readers are encouraged to report errors via the Contact page.'] },
      { h: 'Sponsored content and advertising', p: ['BRYME does not currently load third-party advertising and does not sell article placements as news. If a future piece is sponsored or paid, it will be clearly labelled and kept separate from independent editorial decisions.'] }
    ]
  }
];
for (const page of legalPages) {
  const schema = [
    { '@context':'https://schema.org', '@type': page.schemaType, name: page.hero, description: page.description, url: absUrl('/' + page.dir + '/') },
    breadcrumbs([{ name:'Home', path:'/' }, { name: page.hero, path: '/' + page.dir + '/' }])
  ];
  write(page.dir, layout({
    title: page.title,
    description: page.description,
    path: '/' + page.dir + '/',
    schema,
    body: `<main class="shell"><div class="crumb"><a href="${url('/')}">Home</a> / ${esc(page.hero)}</div><section class="hero"><div class="eyebrow">${esc(page.eyebrow)}</div><h1>${esc(page.hero)}</h1><p class="lead">${esc(page.lead)}</p></section><article class="prose legal-prose">${legalBody(page.sections)}</article></main>`
  }));
}

/* ================================================================
   VERTICAL ARTICLE PAGES — Make Money / Sports editorial.
   Rendered from content/*-articles.json so the JSON is the single source
   of truth. Only 'published' articles are rendered here; drafts stay out
   of the public site entirely.
   ================================================================ */
function renderVerticalArticle(dir, verticalName, a) {
  const pagePath = articlePathFor(dir, a);
  const cat = (VERTICALS.find(v => v.dir === dir)?.categories || []).find(c => c.slug === articleCatSlug(a));
  const crumbs = [{ name: 'Home', path: '/' }, { name: verticalName, path: '/' + dir + '/' }];
  if (cat) crumbs.push({ name: cat.name, path: '/' + dir + '/' + cat.slug + '/' });
  crumbs.push({ name: a.title, path: pagePath });

  const sections = (a.content || []).map(sec => {
    if (!sec) return '';
    const heading = sec.heading ? `<h2>${esc(sec.heading)}</h2>` : '';
    const paras = String(sec.body || sec.text || '')
      .split(/\n{2,}/)
      .filter(Boolean)
      .map(t => `<p>${esc(t.trim())}</p>`)
      .join('');
    const bullets = Array.isArray(sec.points) && sec.points.length
      ? `<ul>${sec.points.map(pt => `<li>${esc(pt)}</li>`).join('')}</ul>` : '';
    return heading + paras + bullets;
  }).join('');

  const sourceBlock = Array.isArray(a.sources) && a.sources.length
    ? `<section class="sp-source"><h2>Sources</h2><p>${a.sources.map(src =>
        src.url ? `<a href="${esc(src.url)}" rel="nofollow noopener">${esc(src.name || src.url)}</a>` : esc(src.name || src)
      ).join(' · ')}</p><p class="sp-source-note">Figures were checked against the sources above${a.sourcesCheckedOn ? ` on ${esc(a.sourcesCheckedOn)}` : ''}. Published terms change — confirm on the provider's own site before relying on them.</p></section>`
    : '';

  const related = (verticalArticleIndex[dir].get(articleCatSlug(a)) || []).filter(x => x.slug !== a.slug).slice(0, 3);
  const relatedBlock = related.length
    ? `<section class="section"><div class="section-head"><h2>More in ${esc(cat ? cat.name : verticalName)}</h2></div><div class="vcat-grid">${related.map(x => articleCard(dir, x)).join('')}</div></section>`
    : '';

  const updated = a.updatedAt && a.updatedAt !== a.publishedAt ? ` · updated ${esc(a.updatedAt)}` : '';
  const send = SENDABLE_META[a.slug] ? sendBar(pagePath, SENDABLE_META[a.slug].title || a.title) : '';
  const heroImg = heroFor(a.slug, dir);
  const yt = a.youtube && /^[A-Za-z0-9_-]{11}$/.test(a.youtube.videoId || '') ? a.youtube : null;
  const videoBlock = yt ? (function () {
    const watch = 'https://www.youtube.com/watch?v=' + yt.videoId;
    const candidates = JSON.stringify([{ id: yt.videoId, type: 'official-clip', label: 'Official highlights', channel: yt.channel || '', verified: true, watch }]);
    const cap = yt.caption ? `<p class="trailer-meta">${esc(yt.caption)}</p>` : `<p class="trailer-meta">YouTube · via ${esc(yt.channel || 'official channel')}. BRYME does not host the file.</p>`;
    return `<section class="shell trailer-section" id="video" data-video-landing><div class="trailer-section-inner" data-trailer-box data-trailer-candidates="${esc(candidates)}" data-trailer-title="${esc(a.title)}"><div class="trailer-head"><span class="eyebrow">Video</span><span class="trailer-status t-ok">🟢 Official highlights</span></div><div class="trailer-frame" data-trailer-id="${yt.videoId}"><img loading="lazy" src="https://i.ytimg.com/vi/${yt.videoId}/hqdefault.jpg" alt="${esc(a.title)} video thumbnail"><button type="button" class="trailer-play">Play video</button></div><div class="trailer-controls" data-trailer-controls hidden><button type="button" class="cta" data-trailer-unmute>Unmute</button><a class="quiet-link" href="${esc(watch)}" target="_blank" rel="noopener">Watch on YouTube</a></div>${cap}<p class="trailer-fallback">If the embedded player is unavailable, <a href="${esc(watch)}" target="_blank" rel="noopener">watch on YouTube</a>.</p></div></section>`;
  })() : '';
  const nextSlugs = Array.isArray(a.nextOnBryme) ? a.nextOnBryme : [];
  const nextItems = nextSlugs.map(s => (VERTICAL_ARTICLES[dir] || []).find(x => x.slug === s)).filter(Boolean);
  const nextBlock = nextItems.length ? `<section class="tp-loved tp-loved-under" id="next"><h2>If you like this, check these out</h2><p class="tp-loved-lead">Under the clip, not on top of it. These pages continue the same story.</p><div class="tp-loved-list">${nextItems.map(x => `<a class="tp-loved-card" href="${url(articlePathFor(dir, x))}"><span><b>${esc(x.title)}</b><em>${esc(x.category || verticalName)}</em><small>${esc((x.excerpt || '').slice(0, 140))}</small></span></a>`).join('')}</div></section>` : '';
  const hero = `<section class="article-hero article-hero-photo" style="--hero-img:url('${heroImg}')"><div class="eyebrow">${esc(cat ? cat.name : verticalName)}</div><h1>${esc(a.title)}</h1>${a.excerpt ? `<p class="lead">${esc(a.excerpt)}</p>` : ''}<div class="article-meta">${a.author ? `<span>${authorLink(a.author)}</span>` : ''}${a.publishedAt ? `<span>${esc(a.publishedAt)}${updated}</span>` : ''}${a.readingTime ? `<span>${esc(a.readingTime)}</span>` : ''}</div>${send}</section>`;
  const crumb = `<div class="crumb">${crumbs.slice(0, -1).map(c => `<a href="${url(c.path)}">${esc(c.name)}</a>`).join(' / ')} / ${esc(a.title)}</div>`;
  const body = videoBlock
    ? `<main class="shell" data-video-landing>${crumb}
  ${videoBlock}
  ${nextBlock}
  ${hero}
  <article class="prose article-body">${sections}</article>
  ${sourceBlock}${relatedBlock}</main>`
    : `<main class="shell">${crumb}
  ${hero}
  <article class="prose article-body">${sections}${nextBlock}</article>
  ${sourceBlock}${relatedBlock}</main>`;

  const schemaList = [{
      '@context': 'https://schema.org', '@type': 'Article',
      headline: a.title,
      description: a.excerpt || undefined,
      datePublished: a.publishedAt || undefined,
      dateModified: a.updatedAt || a.publishedAt || undefined,
      author: (() => {
        const rec = AUTHORS.get(a.author);
        if (rec) return { '@type': 'Person', name: rec.name, url: absUrl(authorPath(rec)), jobTitle: rec.role || undefined, knowsAbout: rec.knowsAbout || undefined };
        return { '@type': a.author && /\s/.test(a.author) ? 'Person' : 'Organization', name: a.author || 'BRYME Editorial' };
      })(),
      publisher: { '@type': 'Organization', name: site.name },
      mainEntityOfPage: absUrl(pagePath),
      articleSection: cat ? cat.name : verticalName,
      image: absUrl(heroImg)
    }, breadcrumbs(crumbs)];
    if (yt) {
      const vo = { '@context':'https://schema.org', '@type':'VideoObject', name: yt.name || a.title, description: yt.description || a.excerpt || a.title, thumbnailUrl: 'https://i.ytimg.com/vi/' + yt.videoId + '/hqdefault.jpg', embedUrl: 'https://www.youtube-nocookie.com/embed/' + yt.videoId };
      if (yt.uploadDate) vo.uploadDate = yt.uploadDate;
      if (yt.channel) vo.publisher = { '@type':'Organization', name: yt.channel };
      if (vo.uploadDate) schemaList.push(vo);
    }
  write(dir + '/' + a.slug, layout({
    title: a.seoTitle || a.title,
    description: a.excerpt || `${a.title} — ${verticalName} on BRYME.`,
    path: pagePath,
    activeNav: dir,
    ogType: 'article',
    image: heroImg,
    schema: schemaList,
    body
  }));
}
VERTICALS.forEach(v => (VERTICAL_ARTICLES[v.dir] || []).forEach(a => renderVerticalArticle(v.dir, v.name, a)));

/* ---------------- Author pages ---------------- */
const AUTHOR_PATHS = [];
AUTHORS.forEach(a => {
  const written = VERTICALS.flatMap(v => (VERTICAL_ARTICLES[v.dir] || [])
    .filter(x => x.author === a.name)
    .map(x => ({ art: x, dir: v.dir, vertical: v.name })));
  const crumbs = [{ name: 'Home', path: '/' }, { name: 'Authors', path: '/' }, { name: a.name, path: authorPath(a) }];
  const body = `<main class="shell"><div class="crumb"><a href="${url('/')}">Home</a> / ${esc(a.name)}</div>
  <section class="article-hero"><div class="eyebrow">${esc(a.role || 'Writer')}</div><h1>${esc(a.name)}</h1>${a.summary ? `<p class="lead">${esc(a.summary)}</p>` : ''}</section>
  <article class="prose article-body">${(a.bio || []).map(t => `<p>${esc(t)}</p>`).join('')}
  ${a.knowsAbout && a.knowsAbout.length ? `<h2>Works with</h2><p>${a.knowsAbout.map(esc).join(' · ')}</p>` : ''}
  ${a.contact ? `<h2>Contact</h2><p>${esc(a.contact)}</p>` : ''}</article>
  ${written.length ? `<section class="section"><div class="section-head"><h2>Articles by ${esc(a.name)}</h2></div><div class="vcat-grid">${written.map(w => articleCard(w.dir, w.art)).join('')}</div></section>` : ''}
  </main>`;
  write('author/' + a.slug, layout({
    title: `${a.name} — ${a.role || 'Writer'}`,
    description: a.summary || `${a.name} writes for ${site.name}.`,
    path: authorPath(a),
    schema: [{
      '@context': 'https://schema.org', '@type': 'ProfilePage',
      mainEntity: {
        '@type': 'Person', name: a.name, url: absUrl(authorPath(a)),
        jobTitle: a.role || undefined,
        description: (a.bio || []).join(' ') || undefined,
        knowsAbout: a.knowsAbout || undefined,
        worksFor: { '@type': 'Organization', name: site.name }
      }
    }, breadcrumbs(crumbs)],
    body
  }));
  AUTHOR_PATHS.push(authorPath(a));
});

/* ================================================================
   NEWS SITEMAP — Google News discovery for time-sensitive football.
   Built to Google's documented rules: articles from the last two days
   only, max 1,000 entries, the same file updated rather than replaced.
   Evergreen guides are deliberately excluded — a news sitemap listing
   explainers that are not news is the fastest way to have it ignored.
   An empty file is valid and expected between publishing runs.
   ================================================================ */
const NEWS_WINDOW_DAYS = 2;
const newsItems = [];
(() => {
  const withinWindow = (d) => {
    const iso = isoDate(d, 'news sitemap');
    if (!iso) return false;
    const days = -daysUntil(iso);          // days since publication
    return days !== null && days >= 0 && days <= NEWS_WINDOW_DAYS;
  };
  /* 1. Sports articles, but ONLY those explicitly marked newsworthy.
        An article has to opt in with "newsworthy": true. Evergreen explainers -
        how the Champions League format works, all-time records - are reference
        material, not news, and a news sitemap padded with them is one Google
        learns to distrust. Opt-in rather than opt-out so the default is safe. */
  (VERTICAL_ARTICLES.sports || []).forEach(a => {
    if (a.newsworthy !== true) return;
    const d = a.publishedAt;
    if (withinWindow(d)) newsItems.push({ path: articlePathFor('sports', a), title: a.title, date: d });
  });
  /* 2. Match pages that became editorial pages, or gained a result, inside the window. */
  const files = { 'premier-league':'fixtures.json', 'la-liga':'fixtures-la-liga.json',
    'serie-a':'fixtures-serie-a.json', 'bundesliga':'fixtures-bundesliga.json', 'ligue-1':'fixtures-ligue-1.json' };
  for (const [lg, file] of Object.entries(files)) {
    const fp = path.join(root, 'content', file);
    if (!fs.existsSync(fp)) continue;
    let F; try { F = JSON.parse(fs.readFileSync(fp, 'utf8')); } catch (e) { continue; }
    (F.matchweeks || []).forEach(w => (w.matches || []).forEach(m => {
      const slug = m.id + '-vs-' + m.away;
      const ed = editorialFor(lg, slug);
      const res = resultFor(lg, slug);
      if (!ed && !res) return;
      /* the date this became news: the result if there is one, else the preview */
      const d = (res && (res.verifiedOn || res.playedOn))
             || (ed && ed.postMatch && ed.postMatch.publishedAt)
             || (ed && (ed.updatedAt || ed.publishedAt));
      if (!withinWindow(d)) return;
      const title = res
        ? `${m.homeName} ${res.homeScore}-${res.awayScore} ${m.awayName}: result and analysis`
        : `${m.homeName} v ${m.awayName}: preview, form and prediction`;
      newsItems.push({ path: '/sports/' + lg + '/matches/' + slug + '/', title, date: d });
    }));
  }
})();
const newsCapped = newsItems.slice(0, 1000);   // Google's documented limit
const newsXml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n${newsCapped.map(n => `  <url>
    <loc>${absUrl(n.path)}</loc>
    <news:news>
      <news:publication>
        <news:name>${esc(site.name)}</news:name>
        <news:language>en</news:language>
      </news:publication>
      <news:publication_date>${esc(n.date)}</news:publication_date>
      <news:title>${esc(n.title)}</news:title>
    </news:news>
  </url>`).join('\n')}\n</urlset>\n`;
fs.writeFileSync(path.join(root, 'news-sitemap.xml'), newsXml);

/* ---------------- 404, sitemap, robots ---------------- */
const genrePaths = typeConfig.flatMap(t => [...genreIndexByType[t.dir].keys()].map(s => `/${t.pageDir}/${s}/`));
const legalPaths = legalPages.map(p => '/' + p.dir + '/');
const verticalPaths = ['/entertainment/','/sports/articles/']
  .concat(VERTICALS.flatMap(v => ['/' + v.dir + '/'].concat((v.categories || []).map(c => '/' + v.dir + '/' + c.slug + '/'))))
  .concat(WRITING_EXTRA_PATHS)
  .filter(p => !EMPTY_HUB_PATHS.has(p));
/* Published vertical articles are real, indexable pages. */
const verticalArticlePaths = VERTICALS.flatMap(v => (VERTICAL_ARTICLES[v.dir] || []).map(a => articlePathFor(v.dir, a)));
const paths = ['/','/now/','/movies/','/series/','/anime/','/trending/','/genres/','/years/','/topics/','/articles/', ...legalPaths, ...AUTHOR_PATHS, ...verticalPaths, ...verticalArticlePaths, ...sportsExtraPaths.filter(p => !PLACEHOLDER_SPORTS_PATHS.has(p)), ...LEAGUE_MATCH_PATHS.filter(p => !UNPLAYED_MATCH_PATHS.has(p)), ...genrePaths.filter(p => !THIN_LISTING_PATHS.has(p)), ...movies.map(m => `/${m.typeDir || 'movie'}/${m.slug}/`), ...[...yearMap].filter(([,l]) => !thinArchive(l)).map(([y]) => `/year/${y}/`), ...[...seriesYearMap].filter(([,l]) => !thinArchive(l)).map(([y]) => `/series/${y}/`), ...[...animeYearMap].filter(([,l]) => !thinArchive(l)).map(([y]) => `/anime/${y}/`), ...articles.map(a => `/article/${a.slug}/`), ...topics.map(t => `/topic/${t.slug}/`), ...[...articleCategoryMap.keys()].map(s => `/articles/${s}/`).filter(p => !THIN_LISTING_PATHS.has(p))];
fs.writeFileSync(path.join(root, '404.html'), layout({
  title: 'Page not found', description: 'This page is not available on BRYME.', path: '/404.html', noindex: true,
  body: `<main class="shell"><section class="hero"><div class="eyebrow">404</div><h1>Looks like this one disappeared.</h1><p class="lead">Try searching the catalogue, or browse a single content type.</p><p><a class="cta" href="${url('/search/')}">Search everything</a> <a class="quiet-link" href="${url('/movies/')}">Movies</a> <a class="quiet-link" href="${url('/series/')}">Series</a> <a class="quiet-link" href="${url('/anime/')}">Anime</a> <a class="quiet-link" href="${url('/articles/')}">Latest articles</a></p></section></main>`
}));
if (fs.existsSync(path.join(root, '404'))) { fs.rmSync(path.join(root, '404'), {recursive:true, force:true}); }
const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${[...new Set(paths)].map(p => `  <url><loc>${absUrl(p)}</loc>${PAGE_LASTMOD.has(p) ? `<lastmod>${PAGE_LASTMOD.get(p)}</lastmod>` : ''}</url>`).join('\n')}\n</urlset>\n`;
fs.writeFileSync(path.join(root, 'sitemap.xml'), xml);
fs.writeFileSync(path.join(root, 'robots.txt'), `User-agent: *\nAllow: /\nSitemap: ${absUrl('/sitemap.xml')}\nSitemap: ${absUrl('/news-sitemap.xml')}\n`);

/* ---------------- Catalogue report ---------------- */
const typeCounts = { movie:0, series:0, anime:0 };
movies.forEach(m => { typeCounts[m.typeDir] = (typeCounts[m.typeDir] || 0) + 1; });
const unknown = movies.filter(m => !m.typeDir || !['movie','series','anime'].includes(m.typeDir));
const report = [
  '# BRYME catalogue & frontend report',
  '',
  `Generated: ${new Date().toISOString()}`,
  '',
  '## Catalogue',
  `- Total titles: **${movies.length}**`,
  `- Movies: **${typeCounts.movie}**`,
  `- Series: **${typeCounts.series}**`,
  `- Anime: **${typeCounts.anime}**`,
  `- Unclassified / ambiguous type: **${unknown.length}**`,
  `- With verified trailers: **${youtubeAudit.filter(v => v.status === 'valid-id').length}**`,
  `- Without trailers: **${youtubeAudit.filter(v => v.status === 'unavailable').length}**`,
  `- With editorial ratings: **${movies.filter(m => m.rating && m.rating.value != null).length}**`,
  `- With country data: **${movies.filter(m => m.country).length}** / language: **${movies.filter(m => m.language).length}**`,
  '',
  '## Genre coverage (per type)',
  `- Movie genres: ${[...genreIndexByType.movie.keys()].map(s => `\`${s}\` (${genreIndexByType.movie.get(s).items.length})`).join(', ')}`,
  `- Series genres: ${[...genreIndexByType.series.keys()].map(s => `\`${s}\` (${genreIndexByType.series.get(s).items.length})`).join(', ')}`,
  `- Anime genres: ${[...genreIndexByType.anime.keys()].map(s => `\`${s}\` (${genreIndexByType.anime.get(s).items.length})`).join(', ')}`,
  '',
  '## Routes',
  `- Title pages: ${movies.length}`,
  `- Category pages: /movies/, /series/, /anime/`,
  `- Per-type genre pages: ${genrePaths.length}`,
  `- Indexable URLs in sitemap: **${[...new Set(paths)].length}**`,
  '',
  '## Rankings (editorially curated)',
  `- Trending Now: ${trendingList.length} titles (${trendingByType.movie.length} movies / ${trendingByType.series.length} series / ${trendingByType.anime.length} anime), ranked by trendingRank ASC from content/rankings.json`,
  `- Popular: ${popularList.length} titles (${popularByType.movie.length} movies / ${popularByType.series.length} series / ${popularByType.anime.length} anime), independent of trending`,
  `- Editor's Picks: ${editorPicksList.length} titles, independent of trending/popular`,
  `- Featured hero: ${hero ? hero.title : 'none'}`,
  `- Deterministic: same catalogue + same rankings.json always produces the same lists (no random, no score-based trending)`,
  `- Future: Trending Score = recent engagement + growth rate + searches + clicks + recency, once real analytics exist`,
  '',
  '## Trailer system',
  `- Official trailers: **${trailerStats.official}**`,
  `- Official teasers: **${trailerStats.teaser}**`,
  `- Official clips: **${trailerStats.clip}**`,
  `- Community/fan-made fallbacks (labelled): **${trailerStats.fan}**`,
  `- No verified trailer: **${trailerStats.missing}**`,
  `- Broken/unavailable detected: **${trailerStats.broken}**` + (trailerStats.brokenList.length ? '\n- Broken: ' + trailerStats.brokenList.map(b => b.title + ' (' + b.videoId + ') [' + b.status + ']').join('; ') : ''),
  '- Priority: official-trailer > official-teaser > official-clip > fan-made > unavailable',
  '- Fan-made videos are labelled "Community trailer" with a disclaimer; never "Official Trailer".',
  '',
  '## Editorial config',
  `- Featured hero: ${hero ? hero.title : 'none'} (content/rankings.json)`,
  ''
].join('\n');
fs.writeFileSync(path.join(root, 'reports', 'catalogue-report.md'), report);

fs.appendFileSync(path.join(root,'assets/site.css'), `

/* ============================================================
   LIGHT MODE READABILITY
   Last layer. White mode was flipping --text/--muted to dark
   while many cards stayed black, so boxes became unreadable.
   Content cards go light. Cinematic banners stay dark but
   their type is locked to light colours.
   ============================================================ */
.send-bar{display:flex;flex-wrap:wrap;align-items:center;gap:10px 14px;margin:16px 0 0;padding:12px 14px;border:1px solid var(--line);border-radius:10px;background:#101318}
.send-bar p{margin:0;font-size:13px;font-weight:800;color:var(--muted)}
.send-wa{display:inline-flex;align-items:center;min-height:40px;padding:8px 14px;border-radius:8px;background:#25d366;color:#06210f;font-weight:800;font-size:13.5px}
.send-wa:hover{filter:brightness(1.06);color:#06210f}
[data-theme="light"] .send-bar{background:#fff;border-color:var(--line)}
[data-theme="light"] .send-bar p{color:#5a6572}

/* Content cards that were still black */
[data-theme="light"] .sp-source,
[data-theme="light"] .sp-mc-card,
[data-theme="light"] .sp-body-placeholder,
[data-theme="light"] .sp-img,
[data-theme="light"] .sp-rel,
[data-theme="light"] .sp-fix-legend,
[data-theme="light"] .sp-rumours,
[data-theme="light"] .sp-archive-note,
[data-theme="light"] .sp-live,
[data-theme="light"] .sp-truth,
[data-theme="light"] .oc-card,
[data-theme="light"] .oc-filters,
[data-theme="light"] .oc-editor,
[data-theme="light"] .oc-official,
[data-theme="light"] .oc-facts div,
[data-theme="light"] .mm-cat,
[data-theme="light"] .mm-country-q,
[data-theme="light"] .wo-feature-card,
[data-theme="light"] .wo-banner,
[data-theme="light"] .wo-card,
[data-theme="light"] .wo-filters,
[data-theme="light"] .tp-watch,
[data-theme="light"] .tp-watch-btn,
[data-theme="light"] .tp-next-links a,
[data-theme="light"] .sa-card,
[data-theme="light"] .sa-empty,
[data-theme="light"] .sa-draft,
[data-theme="light"] .filterbar,
[data-theme="light"] .take-card,
[data-theme="light"] .vcat,
[data-theme="light"] .vchip,
[data-theme="light"] .genre-panel,
[data-theme="light"] .mm-desk,
[data-theme="light"] .mm-path,
[data-theme="light"] .mm-country{
  background:#fff !important;
  border-color:var(--line) !important;
  color:#161b22;
}
[data-theme="light"] .wo-feature-card{
  background:linear-gradient(160deg,rgba(231,187,92,.16),#fff) !important;
}
[data-theme="light"] .sp-artcard{
  background:linear-gradient(160deg,rgba(61,220,132,.10),#fff) !important;
}

/* Hardcoded pale text sitting on now-white cards */
[data-theme="light"] .wo-steps li,
[data-theme="light"] .wo-tag,
[data-theme="light"] .wo-card p,
[data-theme="light"] .wo-banner p,
[data-theme="light"] .sp-rel,
[data-theme="light"] .sp-rel-static,
[data-theme="light"] .sp-source p,
[data-theme="light"] .sp-source h2,
[data-theme="light"] .sp-source-note,
[data-theme="light"] .sp-mc-card b,
[data-theme="light"] .sp-mc-card p,
[data-theme="light"] .sp-club-notes,
[data-theme="light"] .sp-fixt-day,
[data-theme="light"] .sp-msec p,
[data-theme="light"] .sp-msec b,
[data-theme="light"] .sp-msec ul,
[data-theme="light"] .cd-jump,
[data-theme="light"] .oc-card h3,
[data-theme="light"] .oc-facts dd,
[data-theme="light"] .mm-cat b,
[data-theme="light"] .mm-path b,
[data-theme="light"] .vcat b,
[data-theme="light"] .prose li,
[data-theme="light"] .legal-prose p,
[data-theme="light"] .article-body li{
  color:#2b333c;
}
[data-theme="light"] .wo-tag,
[data-theme="light"] .oc-pub,
[data-theme="light"] .mm-cat span,
[data-theme="light"] .mm-path span,
[data-theme="light"] .vcat span,
[data-theme="light"] .vchip-tag,
[data-theme="light"] .sp-source-note,
[data-theme="light"] .oc-disclaimer,
[data-theme="light"] .oc-note{
  color:#5a6572;
}
[data-theme="light"] .sp-table th{
  background:#f1f4f8;
  color:#5a6572;
}
[data-theme="light"] .sp-table a,
[data-theme="light"] body[data-nav="sports"] .sp-table a{
  color:#c24427;
}
[data-theme="light"] .sp-table a:hover{color:#8f2d16}
[data-theme="light"] .quiet-link{color:#161b22;border-bottom-color:rgba(22,27,34,.35)}
[data-theme="light"] .section-head a:hover,
[data-theme="light"] .wo-apply:hover,
[data-theme="light"] .header-search:hover,
[data-theme="light"] .loadmore:hover,
[data-theme="light"] .sp-rel:hover,
[data-theme="light"] .tp-next-links a:hover,
[data-theme="light"] .tp-watch-btn:hover{
  color:#161b22;
}
[data-theme="light"] .genre-chips a:hover{color:#161b22;background:#f3f6f9}

/* Cinematic surfaces stay dark — lock type to light so flipped
   --text/--muted cannot turn them into black-on-black boxes */
[data-theme="light"] .footer,
[data-theme="light"] .footer p,
[data-theme="light"] .footer small,
[data-theme="light"] .footer-col a,
[data-theme="light"] .footer .foot-links a{
  color:#c5cbd2;
}
[data-theme="light"] .footer-col h4,
[data-theme="light"] .footer-brand b{
  color:#f4f5f6;
  background:none;
  -webkit-background-clip:unset;
  background-clip:unset;
}
[data-theme="light"] .footer-col a:hover,
[data-theme="light"] .footer .foot-links a:hover{color:#fff}

[data-theme="light"] .sp-hero-card,
[data-theme="light"] .sp-hero-card h3{color:#f4f5f6}
[data-theme="light"] .sp-hero-card p{color:#d5e4da}
[data-theme="light"] .sp-hero-tag,
[data-theme="light"] .sp-hero-go{color:#7dffb9}
[data-theme="light"] .sp-hero-crests b{color:#c5d0c8}

[data-theme="light"] .sports-feature h1,
[data-theme="light"] .sports-feature .eyebrow{
  background:none;
  -webkit-background-clip:unset;
  background-clip:unset;
  color:#fff;
}
[data-theme="light"] .sports-feature p{color:#c3d0c8}
[data-theme="light"] .home-hero .quiet-link,
[data-theme="light"] .movie-hero .quiet-link,
[data-theme="light"] .hero-slide .quiet-link,
[data-theme="light"] .sports-feature .quiet-link{color:#fff;border-bottom-color:rgba(255,255,255,.4)}

[data-theme="light"] .vhero h1{
  background:linear-gradient(100deg,#161b22 20%,#4a3b2e 70%);
  -webkit-background-clip:text;
  background-clip:text;
  color:transparent;
}
[data-theme="light"] .vhero-sports h1{
  background:linear-gradient(100deg,#0b3d24 10%,#128a4e 70%);
  -webkit-background-clip:text;
  background-clip:text;
}
[data-theme="light"] .vhero p,
[data-theme="light"] .vhero .lead{color:#5a6572}

[data-theme="light"] .poster{background:#e7ebf0}
[data-theme="light"] .placeholder{background:linear-gradient(145deg,#e9edf2,#d7dbe2);color:#161b22}
`);


fs.appendFileSync(path.join(root,'assets/site.css'), `

/* ============================================================
   MOBILE COMPACTNESS
   Last visual pass. Desktop is unchanged. Only phones/small
   screens: shrink oversized icons, buttons, headings, nav and
   padding so more of the same design fits on one screen.
   ============================================================ */
@media (max-width: 760px) {
  /* Header + tools */
  .top .shell { min-height: 46px; padding: 6px 12px; gap: 8px; }
  .brand { font-size: 15px; letter-spacing: .08em; }
  .header-search { min-height: 32px; padding: 4px 10px; font-size: 12px; }
  .theme-toggle { width: 32px; height: 32px; }
  .theme-toggle svg, .bryme-top svg { width: 15px; height: 15px; }
  .bryme-top { width: 34px; height: 34px; right: 12px; bottom: 62px; }
  .shell { padding-left: 12px; padding-right: 12px; }

  /* Bottom nav: slimmer, icons still tappable */
  body { padding-bottom: calc(54px + env(safe-area-inset-bottom, 0px)); }
  .mobile-nav { grid-auto-columns: minmax(0, 1fr); }
  .mobile-nav a {
    min-height: 46px;
    padding: 5px 1px calc(5px + env(safe-area-inset-bottom, 0px) / 4);
    font-size: 9.5px;
    gap: 1px;
  }
  .mobile-nav .mn-ico { font-size: 13px; margin-bottom: 0; line-height: 1; }

  /* Headings: slightly smaller, still a title */
  .hero h1,
  .vhero h1,
  .article-hero h1,
  .home-hero h1,
  .sp-pl-hero h1,
  .sp-article-head h1 {
    font-size: clamp(22px, 6.6vw, 30px) !important;
    line-height: 1.15 !important;
    margin: 6px 0 8px;
  }
  .hero-carousel .hero-slide h1,
  .hero-carousel .hero-slide h2 {
    font-size: clamp(22px, 6.6vw, 30px) !important;
    line-height: 1.12 !important;
    margin: 0 0 6px;
  }
  .sports-feature h1 { font-size: 26px !important; margin: 6px auto 8px; }
  .section-head h2,
  .home-section h2,
  .section > h2,
  .section h2 { font-size: 18px; }
  .rec-copy h2 { font-size: 20px; margin: 2px 0 4px; }
  .article-body h2,
  .tp-page .prose h2,
  .legal-prose h2 { font-size: 18px; margin-top: 22px; }
  .wo-card h3,
  .oc-card h3 { font-size: 16px; }
  .story-grid h3 { font-size: 16px; margin: 6px 0; }
  .editorial-card h3 { font-size: 14.5px; }
  .take-card h3 { font-size: 16px; }
  .movie-hero h1 { font-size: clamp(22px, 6.4vw, 28px) !important; margin: 4px 0 6px; }

  /* Body copy: a notch tighter, still readable */
  .lead, .vhero .lead { font-size: 14px; line-height: 1.5; }
  .hero-slide p, .home-hero p { font-size: 13.5px; }
  .article-body p { font-size: 15.5px; line-height: 1.6; }
  .tp-page .prose p { font-size: 15px; line-height: 1.6; }

  /* Section / page padding */
  .hero { padding: 20px 0 14px; }
  .vhero, .sp-pl-hero { padding: 16px 0 6px; }
  .section { padding: 14px 0; }
  .home-section { padding: 16px 0 !important; }
  .rec-section { padding: 16px 0; }
  .brand-strip { padding: 12px 0 4px; }
  .sub-section { padding: 4px 0 16px; }
  .article-hero { padding: 18px 0 10px; }
  .article-body { padding: 10px 0 36px; }
  .legal-prose { padding: 6px 0 36px; }
  .crumb { padding: 10px 0 0; font-size: 12px; }
  .body { padding: 12px 0 32px; }
  .section-head { gap: 8px; margin: 0 0 8px; }
  .section-note { margin: 2px 0 8px; }
  .count-line { margin: 0 0 8px; }
  .home-main { padding-bottom: 16px; }

  /* Heroes: stop eating the first screen */
  .hero-carousel {
    min-height: min(52svh, 340px) !important;
  }
  .hero-slide-inner {
    padding-top: 58px !important;
    padding-bottom: 28px !important;
  }
  .home-hero { min-height: 320px; }
  .home-hero-inner { padding-top: 64px; padding-bottom: 24px; }
  .sports-feature {
    min-height: 220px !important;
    padding: 22px 14px !important;
    margin: 0 -12px 4px;
  }
  .sports-feature:after { font-size: 110px !important; right: -8px; bottom: -28px; }
  .sports-feature p { font-size: 13.5px; line-height: 1.45; }
  .sports-feature .cta { margin-top: 12px; }
  .sports-feature-meta { margin-top: 10px; }
  .movie-hero {
    grid-template-columns: 88px minmax(0, 1fr) !important;
    gap: 10px !important;
    padding: 12px 12px 14px !important;
    min-height: 0 !important;
  }
  .movie-hero .poster { max-height: 132px !important; }
  .trailer-section { padding: 0 12px 10px; }

  /* Icons / controls that were bulky */
  .vchip-emoji { font-size: 16px; line-height: 1; }
  .trailer-play { width: 52px; height: 36px; border-radius: 8px; }
  .trailer-play:before { border-left-width: 12px; border-top-width: 7px; border-bottom-width: 7px; }
  .hero-ctrl { width: 30px; height: 30px; font-size: 16px; }
  .hero-vctrl { width: 30px; height: 30px; font-size: 13px; top: 10px; right: 10px; }
  .hero-pause { right: 46px; }
  .hero-dots { bottom: 10px; gap: 6px; }
  .hero-dot { width: 7px; height: 7px; }
  .rank { min-width: 18px; height: 18px; font-size: 10px; top: 4px; left: 4px; }
  .sp-club-head img { width: 40px; height: 48px; }
  .sp-match-hero img { width: 40px; height: 48px; }
  .sp-hero-crests img { width: 22px; height: 26px; }
  .sp-mc-crests img { width: 24px; height: 28px; }
  .sp-fixt img { width: 18px; height: 22px; }
  .genre-panel h3 { font-size: 14px; gap: 6px; }

  /* Buttons: smaller, still easy to tap */
  .cta,
  .cta-ghost,
  button.cta,
  .hero-actions .cta,
  .hero-actions .cta-ghost {
    min-height: 36px !important;
    padding: 7px 12px !important;
    font-size: 13px;
    margin-top: 0;
  }
  .loadmore { padding: 8px 16px; margin: 12px auto 0; font-size: 13.5px; }
  .rec-cta { padding: 10px 16px; font-size: 14px; min-height: 40px; }
  .rec-form input { padding: 10px 12px; }
  .searchbox { padding: 10px 12px; margin: 8px 0; font-size: 16px; }
  .stabs { padding: 6px 10px; font-size: 12px; }
  .send-wa { min-height: 34px; padding: 6px 12px; font-size: 13px; }
  .send-bar { margin: 10px 0 0; padding: 8px 10px; gap: 8px 10px; }
  .tp-watch-btn { min-height: 36px; padding: 6px 12px; font-size: 13px; }
  .fbtn { padding: 6px 10px; }
  .mm-country { min-height: 34px; padding: 6px 11px; font-size: 13px; }
  .header-search { min-height: 32px; }

  /* Cards and containers */
  .vchip { padding: 10px 11px; gap: 3px; border-radius: 8px; }
  .vchip-name { font-size: 13.5px; }
  .vchip-tag { font-size: 11px; }
  .vchips { gap: 8px; }
  .vcat { padding: 10px 11px; }
  .vcat b { font-size: 13.5px; }
  .vcat-grid { gap: 8px; }
  .oc-card { padding: 12px 12px 10px; border-radius: 10px; }
  .oc-filters { padding: 10px; margin: 0 0 12px; }
  .oc-search-wrap input { padding: 9px 10px; }
  .oc-facts { margin: 8px 0; gap: 6px; }
  .wo-card { padding: 12px 12px 10px; }
  .wo-filters { padding: 10px 12px; margin: 0 0 12px; gap: 8px; }
  .wo-banner { padding: 10px 12px; margin: 0 0 12px; }
  .mm-desk { padding: 12px; margin: 4px 0 16px; }
  .mm-cat { padding: 11px; min-height: 88px; }
  .mm-path { padding: 11px 12px; }
  .story-grid a,
  .story-grid-title a { min-height: 118px !important; padding: 14px; }
  .sp-hero-card { min-height: 148px !important; padding: 14px; gap: 5px; }
  .sp-hero { margin: 14px 0 6px; }
  .sp-artcard { padding: 12px 13px; }
  .sp-artcard b { font-size: 14.5px; }
  .take-card { margin-top: 14px; padding: 12px; }
  .tp-watch { margin: 16px 0; padding: 12px; }
  .tp-next { margin: 22px 0 6px; padding-top: 14px; }
  .rec-inner { padding: 14px 12px; gap: 12px; }
  .filterbar { padding: 10px; margin: 0 0 12px; gap: 8px; }
  .genre-panel { padding: 12px; }
  .discover-cta { padding: 16px 12px; margin: 18px 0 0; }
  .sp-match-hero { padding: 12px; gap: 10px; }
  .sp-live { padding: 12px; gap: 10px; }
  .sp-source { padding: 12px 14px; margin-top: 18px; }
  .sp-club-head { padding: 10px 12px; gap: 10px; }
  .sp-empty-panel { padding: 14px; }
  .sp-mc-card { min-height: 96px; padding: 12px; }
  .sp-msec { padding: 12px; min-height: 0; }
  .row { padding: 10px 0; gap: 10px; }

  /* Poster rails: a bit denser, still a row */
  .grid, .grid-2 { gap: 8px !important; }
  .rail { grid-auto-columns: 112px; gap: 8px; padding-bottom: 10px; }
  .rail-lead,
  .rail-wall,
  .rail-spread {
    grid-auto-columns: minmax(112px, 34vw) !important;
    gap: 8px !important;
    padding-bottom: 10px;
  }
  .rail-spread { grid-auto-columns: minmax(200px, 72vw) !important; }
  .rail-spread .tile { min-height: 168px; padding: 12px; }
  .tile h3 { font-size: 12px; margin-top: 6px; min-height: 2.4em; }
  .editorial-row { gap: 8px; }

  /* Footer */
  .footer { padding: 18px 0 72px; }
  .footer-grid { gap: 12px; margin: 0 0 12px; }
  .footer .foot-links { gap: 12px; margin: 8px 0 12px; }

  /* Misc gaps */
  .hero-actions { gap: 8px; margin-top: 10px; }
  .badges { gap: 5px; }
  .search-tabs { margin: 0 0 12px; }
  .article-meta { margin-top: 10px; }
  .article-related { margin-top: 28px; padding-top: 16px; }

  /* Nationality picker / send landing */
  .mm-onboard { margin: 0 auto 16px; }
  .mm-onboard h1 { font-size: clamp(22px, 6.4vw, 28px); margin: 6px 0 8px; }
  .mm-country-q { padding: 10px 12px; margin: 0 0 10px; }
  .mm-country-list { max-height: 240px; gap: 6px; }
  .now-grid { display: grid; gap: 8px; margin: 12px 0; }
  .now-card { display: flex; flex-direction: column; gap: 4px; padding: 12px; border: 1px solid var(--line); border-radius: 10px; }
  .now-card b { font-size: 15px; line-height: 1.25; }
  .now-card > span { font-size: 13px; line-height: 1.45; }
  .now-card .now-go { font-size: 12.5px; font-weight: 800; color: var(--gold); }
  .now-copy { font-size: 12.5px; padding: 10px; overflow-x: auto; max-width: 100%; }
}

@media (max-width: 380px) {
  .hero-carousel { min-height: min(48svh, 300px) !important; }
  .sports-feature { min-height: 196px !important; }
  .movie-hero { grid-template-columns: 76px minmax(0, 1fr) !important; }
  .movie-hero .poster { max-height: 114px !important; }
}
`);

fs.appendFileSync(path.join(root,'assets/site.css'), `

/* ============================================================
   LIGHT MODE INPUTS + FIRST-VISIT DESK HINT
   Type / Payment / Word-count selects stayed #0d1013 in white
   mode. First-visit mobile notice is not an ad.
   ============================================================ */
[data-theme="light"] .oc-filters select,
[data-theme="light"] .oc-search-wrap input,
[data-theme="light"] .oc-filters select option,
[data-theme="light"] .wo-filters select,
[data-theme="light"] .wo-filters select option,
[data-theme="light"] .ffield select,
[data-theme="light"] .ffield select option,
[data-theme="light"] .mm-country-q,
[data-theme="light"] .oc-search-wrap input:focus,
[data-theme="light"] .oc-filters select:focus{
  background:#fff !important;
  color:#161b22 !important;
  border-color:var(--line) !important;
  color-scheme:light;
}
[data-theme="light"] .oc-facts div,
[data-theme="light"] .wo-facts div{
  background:#fff !important;
  color:#161b22;
}
[data-theme="light"] .oc-facts dt,
[data-theme="light"] .wo-facts dt{color:#5a6572}
[data-theme="light"] .oc-facts dd,
[data-theme="light"] .wo-facts dd{color:#161b22}

.desk-hint{
  /* Parked overlay. Recs now live under the embed as .tp-loved-under. */
  display:none !important;
}
.desk-hint-card{
  width:100%;max-width:420px;
  background:#111419;border:1px solid var(--line);
  border-radius:14px;padding:16px 16px 14px;
  color:#f4f5f6;box-shadow:0 18px 40px rgba(0,0,0,.35);
}
.desk-hint-card h2{font-size:18px;line-height:1.25;margin:0 0 8px;color:#fff}
.desk-hint-card p{font-size:14px;line-height:1.55;margin:0 0 10px;color:#c5cbd2}
.desk-hint-card .cta{margin:4px 0 0;min-height:40px;padding:8px 14px;font-size:14px}
[data-theme="light"] .desk-hint{background:rgba(22,27,34,.35)}
[data-theme="light"] .desk-hint-card{background:#fff;border-color:var(--line);color:#161b22}
[data-theme="light"] .desk-hint-card h2{color:#161b22}
[data-theme="light"] .desk-hint-card p{color:#5a6572}
@media(min-width:761px){
  .desk-hint{display:none !important}
}
`);

fs.appendFileSync(path.join(root,'assets/site.css'), `

/* ============================================================
   HUB FEATURE BANNERS — Make Money + Tech
   Same shape as .sports-feature. Cards reuse .sp-hero-card
   with gold / blue tints. Desktop sports cards unchanged.
   ============================================================ */
.mm-feature,.tech-feature{
  position:relative;display:grid;place-items:center;min-height:320px;
  margin:0 -20px 10px;padding:36px 24px;overflow:hidden;text-align:center;
  isolation:isolate;border-bottom:1px solid var(--line)
}
.mm-feature{
  background:radial-gradient(ellipse at 50% 110%,rgba(231,187,92,.30),transparent 47%),linear-gradient(135deg,#1a1408 0%,#20180c 48%,#080b0d 100%);
  border-bottom-color:rgba(231,187,92,.35)
}
.tech-feature{
  background:radial-gradient(ellipse at 50% 110%,rgba(79,142,247,.30),transparent 47%),linear-gradient(135deg,#071018 0%,#0c1624 48%,#080b0d 100%);
  border-bottom-color:rgba(79,142,247,.35)
}
.mm-feature:before,.tech-feature:before{
  content:"";position:absolute;inset:-35% -10% 0;
  background:repeating-linear-gradient(118deg,transparent 0 74px,rgba(255,255,255,.035) 75px 77px,transparent 78px 152px);
  transform:skewY(-5deg);z-index:-1
}
.mm-feature:after{content:"💰";position:absolute;right:7%;bottom:-20px;font-size:clamp(140px,24vw,300px);line-height:1;color:rgba(255,255,255,.05);z-index:-1}
.tech-feature:after{content:"🤖";position:absolute;right:7%;bottom:-20px;font-size:clamp(140px,24vw,300px);line-height:1;color:rgba(255,255,255,.05);z-index:-1}
.mm-feature h1,.tech-feature h1{font-size:clamp(32px,5.5vw,58px);line-height:1.02;letter-spacing:-.03em;margin:10px auto;color:#fff}
.mm-feature p,.tech-feature p{max-width:610px;margin:0 auto;font-size:clamp(15px,2vw,17px);line-height:1.55}
.mm-feature p{color:#e6d7b4}
.tech-feature p{color:#c5d4ea}
.mm-feature .eyebrow{color:#f0d48a}
.tech-feature .eyebrow{color:#9ec0ff}

.sp-hero-card.mm-tint{background:linear-gradient(150deg,#241c12,#14100c 70%);border-color:rgba(231,187,92,.28)}
.sp-hero-card.mm-tint:before{background:radial-gradient(240px 120px at 80% 0,rgba(231,187,92,.75),transparent 70%)}
.sp-hero-card.mm-tint .sp-hero-tag,
.sp-hero-card.mm-tint .sp-hero-go{color:#e7bb5c}
.sp-hero-card.tech-tint{background:linear-gradient(150deg,#121a28,#0c1018 70%);border-color:rgba(79,142,247,.28)}
.sp-hero-card.tech-tint:before{background:radial-gradient(240px 120px at 80% 0,rgba(79,142,247,.75),transparent 70%)}
.sp-hero-card.tech-tint .sp-hero-tag,
.sp-hero-card.tech-tint .sp-hero-go{color:#7fb0ff}

[data-theme="light"] .mm-feature h1,
[data-theme="light"] .mm-feature .eyebrow,
[data-theme="light"] .tech-feature h1,
[data-theme="light"] .tech-feature .eyebrow{
  background:none;-webkit-background-clip:unset;background-clip:unset;color:#fff
}
[data-theme="light"] .mm-feature p{color:#e6d7b4}
[data-theme="light"] .tech-feature p{color:#c5d4ea}

@media(max-width:760px){
  .mm-feature,.tech-feature{min-height:210px;margin:0 -12px 4px;padding:22px 14px}
  .mm-feature h1,.tech-feature h1{font-size:26px;margin:6px auto 8px}
  .mm-feature:after,.tech-feature:after{font-size:110px;right:-8px;bottom:-28px}
  .mm-feature p,.tech-feature p{font-size:13.5px;line-height:1.45}
}
`);
fs.appendFileSync(path.join(root,'assets/site.css'), `

/* ============================================================
   MORE IMAGES — photo tiles, article heroes, hub photos,
   entertainment / catalogue banners. Desktop sports cards
   keep their existing size. Mobile compactness only below 760.
   ============================================================ */
.vcat-photo{
  position:relative;isolation:isolate;overflow:hidden;min-height:148px;
  color:#f4f5f6;border-color:rgba(255,255,255,.12);background:#101318
}
.vcat-photo:before{
  content:"";position:absolute;inset:0;z-index:-1;
  background-image:linear-gradient(180deg,rgba(8,9,11,.18),rgba(8,9,11,.86)),var(--card-img);
  background-size:cover;background-position:center
}
.vcat-photo b,.vcat-photo span{position:relative;z-index:1;text-shadow:0 1px 8px rgba(0,0,0,.75)}
.vcat-photo span{color:#d5dbe0}
.vcat-photo:hover{transform:translateY(-2px)}

.story-grid a.story-photo,
a.story-photo{
  position:relative;isolation:isolate;overflow:hidden;min-height:230px;
  color:#f4f5f6;background:#111419;display:flex;flex-direction:column;align-items:flex-start;
  padding:22px
}
a.story-photo:before{
  content:"";position:absolute;inset:0;z-index:0;
  background-image:linear-gradient(180deg,rgba(8,9,11,.12) 0%,rgba(8,9,11,.88) 100%),var(--card-img);
  background-size:cover;background-position:center
}
a.story-photo > *{position:relative;z-index:1;text-shadow:0 1px 8px rgba(0,0,0,.8)}
a.story-photo span{color:#e7bb5c}
a.story-photo h3{color:#fff}
a.story-photo p{color:#d5dbe0}
a.story-photo b{color:#fff}
a.story-photo:hover{filter:brightness(1.06)}

.hub-photos{
  display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0 8px
}
.hub-photo{
  position:relative;isolation:isolate;overflow:hidden;min-height:188px;
  border-radius:12px;padding:18px;display:flex;flex-direction:column;justify-content:flex-end;
  border:1px solid rgba(255,255,255,.12);color:#fff
}
.hub-photo:before{
  content:"";position:absolute;inset:0;z-index:0;
  background-image:linear-gradient(180deg,rgba(8,9,11,.1),rgba(8,9,11,.88)),var(--card-img);
  background-size:cover;background-position:center
}
.hub-photo > *{position:relative;z-index:1;text-shadow:0 2px 10px rgba(0,0,0,.85)}
.hub-photo span{font-size:11px;font-weight:900;letter-spacing:.1em;text-transform:uppercase;color:#e7bb5c}
.hub-photo h3{font-size:18px;line-height:1.2;margin:6px 0 0;color:#fff}
.hub-photo-sports span{color:#7dffb9}
.hub-photo-make-money span{color:#e7bb5c}
.hub-photo-tech span{color:#9ec0ff}
.hub-photo-entertainment span{color:#ffb08e}
.hub-photo:hover{transform:translateY(-3px);box-shadow:0 12px 28px rgba(0,0,0,.35)}

.ent-feature{
  position:relative;display:grid;place-items:center;min-height:320px;
  margin:0 -20px 10px;padding:36px 24px;overflow:hidden;text-align:center;
  isolation:isolate;border-bottom:1px solid rgba(233,75,44,.35);
  background:radial-gradient(ellipse at 50% 110%,rgba(233,75,44,.28),transparent 47%),linear-gradient(135deg,#1a0c0a 0%,#180e0c 48%,#080b0d 100%)
}
.ent-feature.ent-feature-photo:before,
.mm-feature.mm-feature-photo:before,
.cat-feature:before,
.vhero-photo:before,
.article-hero-photo:before{
  content:"";position:absolute;inset:0;z-index:-2;
  background-image:var(--hero-img);background-size:cover;background-position:center
}
.ent-feature.ent-feature-photo:after,
.mm-feature.mm-feature-photo:after,
.cat-feature:after{
  content:"";position:absolute;inset:0;z-index:-1;
  background:linear-gradient(180deg,rgba(8,9,11,.25),rgba(8,9,11,.78))
}
.ent-feature-inner{max-width:760px}
.ent-feature .eyebrow{color:#ffb08e}
.ent-feature h1{font-size:clamp(32px,5.5vw,58px);line-height:1.02;letter-spacing:-.03em;margin:10px auto;color:#fff}
.ent-feature p{max-width:610px;margin:0 auto;font-size:clamp(15px,2vw,17px);line-height:1.55;color:#f0d4c8}

.sp-hero-card.ent-tint{background:linear-gradient(150deg,#241412,#140e0c 70%);border-color:rgba(233,75,44,.28)}
.sp-hero-card.ent-tint:before{background:radial-gradient(240px 120px at 80% 0,rgba(233,75,44,.75),transparent 70%)}
.sp-hero-card.ent-tint .sp-hero-tag,
.sp-hero-card.ent-tint .sp-hero-go{color:#ffb08e}

.cat-feature{
  position:relative;display:grid;place-items:end start;min-height:240px;
  margin:0 -20px 10px;padding:42px 24px 28px;overflow:hidden;isolation:isolate;
  border-bottom:1px solid var(--line);color:#fff
}
.cat-feature h1{font-size:clamp(32px,5vw,56px);line-height:1.04;margin:8px 0;color:#fff}
.cat-feature .lead,.cat-feature p{max-width:640px;color:#e6e8ea}
.cat-feature .eyebrow{color:#ffb08e}

.mm-feature.mm-feature-photo{background:#1a1408}
.mm-feature.mm-feature-photo .eyebrow,
.mm-feature.mm-feature-photo h1,
.mm-feature.mm-feature-photo p{position:relative;z-index:1}

.vhero-photo{position:relative;isolation:isolate;overflow:hidden;min-height:210px}
.vhero-photo:after{
  content:"";position:absolute;inset:0;z-index:-1;
  background:linear-gradient(100deg,rgba(8,9,11,.82),rgba(8,9,11,.45) 70%,rgba(8,9,11,.7))
}
.vhero-photo h1,.vhero-photo .lead,.vhero-photo .eyebrow{position:relative;z-index:1}

.article-hero-photo{
  position:relative;isolation:isolate;overflow:hidden;
  max-width:none;margin:8px -20px 0;padding:92px 20px 34px;min-height:320px;
  display:flex;flex-direction:column;justify-content:flex-end
}
.article-hero-photo:after{
  content:"";position:absolute;inset:0;z-index:-1;
  background:linear-gradient(180deg,rgba(8,9,11,.12) 0%,rgba(8,9,11,.55) 48%,rgba(8,9,11,.94) 100%)
}
.article-hero-photo h1{
  background:none;-webkit-background-clip:unset;background-clip:unset;color:#fff;max-width:820px
}
.article-hero-photo .lead{color:#e6e8ea;max-width:760px}
.article-hero-photo .eyebrow,
.article-hero-photo .article-meta{color:#d5dbe0}
.article-hero-photo .article-meta a{color:#fff}

.sa-card.sa-card-photo{
  position:relative;isolation:isolate;overflow:hidden;color:#f4f5f6;min-height:210px
}
.sa-card.sa-card-photo:before{
  content:"";position:absolute;inset:0;z-index:0;
  background-image:linear-gradient(180deg,rgba(8,9,11,.15),rgba(8,9,11,.9)),var(--card-img);
  background-size:cover;background-position:center
}
.sa-card.sa-card-photo > *{position:relative;z-index:1}

[data-theme="light"] .ent-feature h1,
[data-theme="light"] .ent-feature .eyebrow,
[data-theme="light"] .cat-feature h1,
[data-theme="light"] .cat-feature .eyebrow,
[data-theme="light"] .article-hero-photo h1,
[data-theme="light"] .hub-photo h3,
[data-theme="light"] .vcat-photo b,
[data-theme="light"] a.story-photo h3{
  background:none;-webkit-background-clip:unset;background-clip:unset;color:#fff
}
[data-theme="light"] .ent-feature p,
[data-theme="light"] .cat-feature .lead,
[data-theme="light"] .article-hero-photo .lead,
[data-theme="light"] .vcat-photo span,
[data-theme="light"] a.story-photo p{color:#e6e8ea}

@media(max-width:760px){
  .hub-photos{grid-template-columns:1fr 1fr;gap:8px;margin:12px 0 4px}
  .hub-photo{min-height:132px;padding:12px;border-radius:10px}
  .hub-photo h3{font-size:14px}
  .ent-feature,.cat-feature{min-height:190px;margin:0 -12px 4px;padding:22px 14px}
  .ent-feature h1,.cat-feature h1{font-size:26px}
  .article-hero-photo{min-height:220px;padding:56px 14px 20px;margin:4px -12px 0}
  .vcat-photo{min-height:120px}
  a.story-photo{min-height:170px;padding:16px}
}

`);
fs.appendFileSync(path.join(root,'assets/site.css'), `

/* ============================================================
   INSTALLED-APP LANDSCAPE
   The PWA used to lock portrait. Phones in landscape are often
   wider than 760px, so desktop CSS (560px heroes, no bottom nav)
   ran in a ~390px-tall window. This only matches short screens.
   Desktop monitors are unchanged.
   ============================================================ */
@media (orientation: landscape) and (max-height: 540px) {
  body { padding-bottom: 50px; }
  .mobile-nav { display: grid !important; }
  .topnav { display: none !important; }
  .top .shell { min-height: 42px; padding: 4px 12px; gap: 10px; }
  .hero-carousel,
  .home-hero { min-height: 220px; max-height: 100dvh; }
  .hero-slide-inner,
  .home-hero-inner { padding-top: 52px; padding-bottom: 18px; }
  .hero-carousel h1,
  .hero-slide h1,
  .hero-slide h2,
  .home-hero h1 { font-size: 26px; }
  .sports-feature,
  .mm-feature,
  .tech-feature,
  .ent-feature,
  .cat-feature { min-height: 150px; padding: 16px 20px; }
  .article-hero-photo { min-height: 160px; padding: 36px 16px 14px; }
  .movie-hero { min-height: 240px; padding-top: 48px; padding-bottom: 16px; }
  .sp-hero-card { min-height: 120px !important; }
  .hub-photos { grid-template-columns: repeat(4, 1fr); }
  .hub-photo { min-height: 110px; padding: 10px; }
}

`);
fs.appendFileSync(path.join(root,'assets/site.css'), `
/* homepage performance / mobile overflow — desktop look unchanged */
html,body{overflow-x:clip}
.tile img{content-visibility:auto}
.hero-video iframe{width:100%;height:100%;border:0;position:absolute;inset:0}
`);

fs.appendFileSync(path.join(root,'assets/site.css'), `
/* video figure / figcaption — target embed pages; desktop layout unchanged */
.video-figure{margin:0 0 8px;max-width:860px}
.video-figure .trailer-frame{max-width:100%}
.video-figure figcaption{font-size:13.5px;line-height:1.5;color:var(--muted);margin:10px 0 0}
.video-context{max-width:760px;margin:14px 0 8px}
.video-context p{font-size:16px;line-height:1.7;color:#d9dde1;margin:0 0 12px}
.sports-teaser .video-figure{max-width:100%}
[data-theme="light"] .video-context p{color:#2b333c}
[data-theme="light"] .video-figure figcaption{color:#5a6572}
@media(max-width:760px){
  .video-context p{font-size:15px;line-height:1.6}
  .video-figure figcaption{font-size:13px}
}
`);


fs.appendFileSync(path.join(root,'assets/site.css'), `
/* What's Trending desk — /trending/ only. Poster-first, no extra JS. */
.trend-jump{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 18px}
.trend-jump a{font-size:13px;font-weight:800;border:1px solid var(--line);border-radius:20px;padding:8px 12px;background:#101318;color:#d9dde1}
.trend-jump a:hover{border-color:var(--accent);color:#fff}
.trend-list{display:flex;flex-direction:column;gap:12px}
.trend-card{display:grid;grid-template-columns:120px minmax(0,1fr);gap:16px;padding:14px;border:1px solid var(--line);border-radius:12px;background:linear-gradient(160deg,#161b23,#0f1216)}
.trend-poster{position:relative;display:block;aspect-ratio:16/9;overflow:hidden;border-radius:8px;background:#171b20}
.trend-poster img{width:100%;height:100%;object-fit:cover}
.trend-rank{position:absolute;top:6px;left:6px;z-index:1;min-width:22px;height:22px;display:grid;place-items:center;font-size:11px;font-weight:900;border-radius:4px;background:rgba(8,9,11,.82);border:1px solid rgba(255,255,255,.25)}
.trend-kicker{display:flex;flex-wrap:wrap;gap:6px 8px;align-items:center;font-size:12px;color:var(--muted);font-weight:700}
.trend-kicker .sep{opacity:.45}
.trend-lab{font-size:10.5px;font-weight:900;letter-spacing:.04em;padding:2px 8px;border-radius:12px;border:1px solid var(--line)}
.tl-hot{color:#ff8a75;border-color:rgba(233,75,44,.45);background:rgba(233,75,44,.1)}
.tl-rise{color:#e7bb5c;border-color:rgba(231,187,92,.45);background:rgba(231,187,92,.1)}
.tl-watch{color:#9ec0ff;border-color:rgba(79,142,247,.35);background:rgba(79,142,247,.1)}
.tl-new{color:#7dffb9;border-color:rgba(61,220,132,.4);background:rgba(61,220,132,.1)}
.trend-body h3{margin:6px 0 4px;font-size:20px;line-height:1.2}
.trend-body h3 a:hover{color:var(--gold)}
.trend-blurb{margin:0 0 8px;font-size:14.5px;line-height:1.55;color:#d9dde1}
.trend-why{margin:0 0 8px;font-size:13px;color:var(--gold);line-height:1.45}
.trend-actions{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.trend-actions .cta{margin-top:0;min-height:36px;padding:8px 12px;font-size:13px}
.trend-go{font-size:13px;font-weight:800;color:var(--gold)}
.trend-go:hover{color:#fff}
.trend-none{font-size:12px;color:var(--muted)}
[data-theme="light"] .trend-card,[data-theme="light"] .trend-jump a{background:#fff;border-color:var(--line)}
[data-theme="light"] .trend-blurb{color:#2b333c}
[data-theme="light"] .trend-jump a{color:#2b333c}
@media(max-width:760px){
  .trend-card{grid-template-columns:96px minmax(0,1fr);gap:10px;padding:10px}
  .trend-body h3{font-size:16px}
  .trend-blurb{font-size:13.5px}
  .trend-jump{flex-wrap:nowrap;overflow-x:auto;-webkit-overflow-scrolling:touch;padding-bottom:6px}
  .trend-jump a{flex:none}
}
`);


fs.appendFileSync(path.join(root,'assets/site.css'), `
/* post-watch CTA + desktop details stick — not an ad, not on mobile overlay nav */
.trailer-frame{position:relative}
.bryme-afterwatch{position:absolute;inset:0;z-index:4;display:flex;flex-direction:column;justify-content:flex-end;gap:8px;padding:16px;background:linear-gradient(0deg,rgba(8,9,11,.96) 18%,rgba(8,9,11,.72));color:#fff}
.bryme-afterwatch .aw-kicker{margin:0;font-size:11px;font-weight:900;letter-spacing:.08em;text-transform:uppercase;color:#e7bb5c}
.bryme-afterwatch b{font-size:18px;line-height:1.2}
.aw-sub{margin:4px 0 0;font-size:12px;color:#c5cbd2}
.aw-links{display:flex;flex-wrap:wrap;gap:8px}
.aw-links a{border:1px solid rgba(255,255,255,.25);border-radius:16px;padding:6px 10px;font-size:12.5px;font-weight:700}
.aw-links a:hover{border-color:#e7bb5c;color:#fff}
.aw-actions{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:6px}
.aw-actions .cta,.aw-actions .cta-ghost{margin-top:0;min-height:36px;padding:8px 12px;font-size:13px}
.aw-actions .quiet-link{color:#fff;border-bottom-color:rgba(255,255,255,.4)}
@media(min-width:761px){
  .tp-page .body .aside{position:sticky;top:74px;align-self:start}
}
@media(max-width:760px){
  .bryme-afterwatch{padding:12px}
  .bryme-afterwatch b{font-size:16px}
}
[data-theme="light"] .bryme-afterwatch{background:linear-gradient(0deg,rgba(8,9,11,.96) 18%,rgba(8,9,11,.72));color:#fff}
`);


fs.appendFileSync(path.join(root,'assets/site.css'), `
/* static heroes + visible card photos — desktop layout width unchanged */
.home-hero-static{position:relative;background:#0d0f13}
.home-hero-feature{position:relative;min-height:560px;background-size:cover;background-position:center 28%;overflow:hidden;isolation:isolate}
.home-hero-feature .hero-slide-inner{position:relative;z-index:2;padding-top:120px;padding-bottom:48px;max-width:1180px}
.home-hero-feature h1{font-size:clamp(42px,7vw,78px);line-height:.96;max-width:760px;margin:0 0 10px}
.home-hero-feature p{max-width:560px;color:#d2d6d9;font-size:16.5px;line-height:1.5}
.home-hero-feature .hero-video{position:absolute;inset:0;z-index:1}
.home-hero-feature .hero-video iframe{width:100%;height:100%;border:0;display:block}
.home-hero-picks{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;padding:16px 0 8px}
.home-hero-pick{display:flex;flex-direction:column;gap:8px;color:inherit;text-decoration:none;min-width:0}
.home-hero-pick img{width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:8px;background:#171b20;display:block;border:1px solid var(--line)}
.home-hero-pick b{font-size:13px;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.home-hero-pick.is-current img{outline:2px solid var(--accent);outline-offset:2px}
.sp-hero-track{display:grid !important;grid-template-columns:repeat(3,minmax(0,1fr)) !important;grid-auto-flow:row !important;grid-auto-columns:unset !important;overflow:visible !important;scroll-snap-type:none !important}
.sp-hero-arrow,[data-sp-hero-prev],[data-sp-hero-next]{display:none !important}
.sp-hero-card{
  background-image:linear-gradient(180deg,rgba(8,9,11,.25),rgba(8,9,11,.82)),var(--card-img) !important;
  background-size:cover !important;
  background-position:center !important;
}
.sp-hero-card:after{opacity:0 !important}
.sp-hero-card > *{position:relative;z-index:1}
.vcat-photo{
  background-image:linear-gradient(180deg,rgba(8,9,11,.18),rgba(8,9,11,.86)),var(--card-img) !important;
  background-size:cover !important;
  background-position:center !important;
}
.vcat-photo:before{z-index:0 !important}
.tile .poster img,.trend-poster img{background:#171b20}
@media (max-width: 760px) {
  .home-hero-feature{min-height:min(52svh,340px)}
  .home-hero-feature .hero-slide-inner{padding-top:72px;padding-bottom:28px}
  .home-hero-picks{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
  .sp-hero-track{grid-template-columns:1fr !important;gap:12px !important}
  .sp-hero-card{min-height:180px}
}
`);

fs.appendFileSync(path.join(root,'assets/site.css'), `
/* mobile fit: 375/390 — desktop from 761px unchanged */
@media (max-width: 760px) {
  .trailer-frame, .video-figure, .trailer-section-inner { width: 100%; max-width: 100%; }
  .trailer-frame iframe { width: 100%; height: 100%; }
  .trend-card, .trend-list, .trend-jump { max-width: 100%; }
  .movie-hero, .home-hero, .hero-carousel { max-width: 100%; }
  .tp-page .movie-hero { overflow: hidden; }
}
`);


fs.appendFileSync(path.join(root,'assets/site.css'), `
/* video landing: recs under the embed, compact identity, boring bits last */
.tp-page .movie-hero,
.tp-page .movie-hero-compact{
  min-height:0 !important;
  padding:14px 0 10px !important;
  align-items:center;
}
.tp-page .movie-hero:before{opacity:.45}
.tp-loved-under{
  margin:8px 0 18px;
  padding:14px;
  border:1px solid var(--line);
  border-radius:14px;
  background:#111419;
  max-width:860px;
  box-shadow:0 10px 28px rgba(0,0,0,.22);
}
.tp-loved-under h2{font-size:18px;line-height:1.25;margin:0 0 6px;color:#fff}
.tp-loved-lead{font-size:13px;color:var(--muted);margin:0 0 10px;line-height:1.5}
.tp-loved-list{display:grid;gap:8px}
.tp-loved-card{
  display:grid;
  grid-template-columns:96px minmax(0,1fr);
  gap:10px;
  align-items:center;
  padding:8px;
  border:1px solid var(--line);
  border-radius:10px;
  background:#0e1014;
  color:inherit;
  text-decoration:none;
  min-width:0;
}
.tp-loved-card:hover{border-color:var(--gold)}
.tp-loved-card img{width:96px;height:54px;object-fit:cover;border-radius:6px;background:#171b20;display:block}
.tp-loved-card b{display:block;font-size:14px;line-height:1.25}
.tp-loved-card em{display:block;font-style:normal;font-size:11px;color:var(--gold);font-weight:800;margin-top:2px}
.tp-loved-card small{display:block;font-size:12px;color:var(--muted);line-height:1.4;margin-top:2px}
.tp-loved-more{font-size:13px;margin:10px 0 0}
.tp-now,.tp-verdict{max-width:760px}
.tp-verdict-score{font-size:22px;font-weight:900;color:var(--gold);margin:0 0 4px}
.tp-verdict-note{font-size:12.5px;color:var(--muted);margin:0 0 10px}
.tp-boring{margin-top:28px;padding-top:20px;border-top:1px solid var(--line)}
[data-video-landing] .article-hero-photo{min-height:160px;padding-top:28px}
[data-theme="light"] .tp-loved-under{background:#fff;border-color:var(--line)}
[data-theme="light"] .tp-loved-under h2{color:#161b22}
[data-theme="light"] .tp-loved-card{background:#fff;color:#161b22}
[data-theme="light"] .tp-loved-card small{color:#5a6572}
@media (min-width:761px){
  .tp-page .movie-hero-compact{grid-template-columns:110px minmax(0,1fr);gap:18px}
  .tp-loved-list{grid-template-columns:1fr 1fr}
}
@media (max-width:760px){
  .tp-loved-under{padding:12px;margin:6px 0 14px}
  .tp-loved-card{grid-template-columns:72px minmax(0,1fr);gap:8px}
  .tp-loved-card img{width:72px;height:42px}
  .tp-loved-under h2{font-size:16px}
}
`);


fs.appendFileSync(path.join(root,'assets/site.css'), `
/* BRYME cinematic catalogue — own design system, 16:9 cards, desk bar */
:root{
  --radius:10px;
  --card-gap:12px;
  --shade:linear-gradient(180deg,rgba(8,9,11,0) 42%,rgba(8,9,11,.88) 100%);
}
.desk-bar{
  position:sticky;top:62px;z-index:35;
  background:rgba(8,9,11,.92);
  backdrop-filter:blur(12px);
  border-bottom:1px solid var(--line);
}
.desk-bar-inner{
  display:flex;gap:8px;overflow-x:auto;scrollbar-width:none;
  padding:8px 0;
}
.desk-bar-inner::-webkit-scrollbar{display:none}
.desk-bar a{
  flex:none;
  font-size:12.5px;font-weight:800;
  letter-spacing:.04em;
  padding:7px 14px;
  border:1px solid var(--line);
  border-radius:999px;
  color:var(--muted);
  background:#101318;
}
.desk-bar a:hover{color:#fff;border-color:#555}
.desk-bar a.is-on{
  color:#fff;
  background:var(--accent);
  border-color:var(--accent);
}
.top{z-index:40}
.poster{
  aspect-ratio:16/9 !important;
  border-radius:var(--radius);
  overflow:hidden;
  border:1px solid var(--line);
  background:#0d1014;
}
.movie-hero .poster,
.movie-hero-compact .poster{
  aspect-ratio:2/3 !important;
}
.tile{transition:transform .22s ease, filter .22s ease}
.tile:hover{transform:translateY(-4px) scale(1.02);filter:brightness(1.05)}
.tile .poster{position:relative}
.tile .poster img{width:100%;height:100%;object-fit:cover;display:block}
.tile-play{
  position:absolute;left:50%;top:50%;
  width:46px;height:46px;margin:-23px 0 0 -23px;
  border-radius:50%;
  background:rgba(233,75,44,.94);
  opacity:0;
  transform:scale(.9);
  transition:opacity .2s, transform .2s;
  z-index:2;
  pointer-events:none;
  box-shadow:0 10px 24px rgba(0,0,0,.4);
}
.tile-play:before{
  content:"";
  position:absolute;left:18px;top:14px;
  border-left:14px solid #fff;
  border-top:9px solid transparent;
  border-bottom:9px solid transparent;
}
.tile:hover .tile-play{opacity:1;transform:scale(1)}
.tile .poster:after{
  content:"";
  position:absolute;inset:0;
  background:var(--shade);
  pointer-events:none;
  z-index:1;
}
.tile h3{font-size:13.5px;margin:8px 0 0;line-height:1.3}
.grid{
  grid-template-columns:repeat(auto-fill,minmax(180px,1fr));
  gap:16px 12px;
}
.rail,
.rail-lead,.rail-wall,.rail-chart,.rail-spread{
  display:grid !important;
  grid-auto-flow:column !important;
  grid-auto-columns:minmax(210px,240px) !important;
  overflow-x:auto !important;
  gap:12px !important;
  padding:4px 1px 16px !important;
  scroll-snap-type:x mandatory;
}
.rail .tile,.rail-lead .tile,.rail-wall .tile,.rail-chart .tile,.rail-spread .tile{
  scroll-snap-align:start;
}
.rail-lead .tile .poster,
.rail-wall .tile .poster,
.rail-chart .tile .poster,
.rail-spread .tile .poster{aspect-ratio:16/9 !important}
.svc-strip{
  margin:8px 0 28px;
  padding:18px;
  border:1px solid var(--line);
  border-radius:14px;
  background:linear-gradient(160deg,#141820,#0e1014);
}
.svc-copy h2{margin:0 0 6px;font-size:18px}
.svc-copy p{margin:0 0 12px;color:var(--muted);font-size:13.5px;line-height:1.55;max-width:720px}
.svc-row{display:flex;flex-wrap:wrap;gap:8px}
.svc-chip{
  display:inline-flex;align-items:center;
  min-height:40px;padding:8px 14px;
  border:1px solid var(--line);
  border-radius:999px;
  font-size:13px;font-weight:800;
  background:#101318;
}
.svc-chip:hover{border-color:var(--gold);color:#fff}
.tp-watch .svc-row{margin:12px 0 4px}
.tp-loved-under{max-width:100%}
.tp-loved-list{
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(180px,1fr));
  gap:12px;
}
.tp-loved-card{
  display:flex;
  flex-direction:column;
  gap:8px;
  padding:0;
  background:transparent;
  border:0;
  align-items:stretch;
}
.tp-loved-card img{
  width:100%;height:auto;
  aspect-ratio:16/9;
  object-fit:cover;
  border-radius:var(--radius);
  border:1px solid var(--line);
}
.tp-loved-card span{padding:0 2px 6px}
.cta{border-radius:8px}
.trailer-frame{border-radius:12px}
.hero-carousel{border-radius:0}
@media (min-width:761px){
  .desk-bar{top:62px}
  .grid{grid-template-columns:repeat(auto-fill,minmax(190px,1fr))}
}
@media (max-width:760px){
  .desk-bar{top:56px}
  .desk-bar a{padding:6px 12px;font-size:12px}
  .grid{grid-template-columns:repeat(2,minmax(0,1fr)) !important;gap:10px !important}
  .rail,.rail-lead,.rail-wall,.rail-chart,.rail-spread{
    grid-auto-columns:minmax(196px,70vw) !important;
    gap:10px !important;
  }
  .svc-strip{padding:14px}
  .tile:hover{transform:none;filter:none}
  .tile-play{opacity:.9;transform:scale(1);width:36px;height:36px;margin:-18px 0 0 -18px}
  .tile-play:before{left:14px;top:11px;border-left:11px solid #fff;border-top:7px solid transparent;border-bottom:7px solid transparent}
}
@media (prefers-reduced-motion:reduce){
  .tile,.tile-play,.hero-slide{transition:none !important}
}
[data-theme="light"] .desk-bar{background:rgba(244,245,247,.94)}
[data-theme="light"] .desk-bar a{background:#fff;color:#5a6572}
[data-theme="light"] .desk-bar a.is-on{background:var(--accent);color:#fff;border-color:var(--accent)}
[data-theme="light"] .svc-strip,[data-theme="light"] .svc-chip{background:#fff;color:#161b22}
`);

if (warnings.length) {
  console.log('WARNINGS:');
  warnings.forEach(w => console.log('  - ' + w));
}
if (BAD_DATES.length) {
  console.error('\nNON-ISO DATES (dropped from sitemap/structured data):');
  BAD_DATES.forEach(d => console.error('  - ' + d));
  process.exitCode = 1;
}
if (REJECTED_RESULTS.length) {
  console.error('\nREFUSED to publish ' + REJECTED_RESULTS.length + ' result(s) - every result needs integer scores and a source.url:');
  REJECTED_RESULTS.forEach(r => console.error('  - ' + r));
  process.exitCode = 1;
}
if (BRYME_DESIGN_LAYER) {
  fs.appendFileSync(path.join(root, 'assets/site.css'), '\n' + BRYME_DESIGN_LAYER + '\n');
}

console.log(`Built ${movies.length} normalized catalogue records (${typeCounts.movie} movies / ${typeCounts.series} series / ${typeCounts.anime} anime), ${articles.length} articles and ${[...new Set(paths)].length} indexable URLs.`);

#!/usr/bin/env node
/* Produces an editorial and SEO readiness report from the public static data. */
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..');
const movies = JSON.parse(fs.readFileSync(path.join(root, 'data/movies.json')));
const articles = JSON.parse(fs.readFileSync(path.join(root, 'data/articles.json')));
const topics = JSON.parse(fs.readFileSync(path.join(root, 'data/topics.json')));
const status = movie => {
  const essentials = [movie.title, movie.slug, movie.year, movie.genre, movie.description, movie.poster, movie.youtubeId];
  const count = essentials.filter(Boolean).length;
  return count === essentials.length ? 'COMPLETE' : count >= 5 ? 'PARTIAL' : 'MISSING';
};
const groups = { COMPLETE: [], PARTIAL: [], MISSING: [] };
movies.forEach(m => groups[status(m)].push(m));
const weak = movies.filter(m => !m.description || m.description.length < 110 || !m.poster || !m.youtubeId);
const lines = [
  '# BRYME content and SEO readiness audit', '',
  `Generated: ${new Date().toISOString().slice(0, 10)}`, '',
  '## Catalogue coverage', '',
  `- Movies audited: **${movies.length}**`,
  `- COMPLETE metadata: **${groups.COMPLETE.length}**`,
  `- PARTIAL metadata: **${groups.PARTIAL.length}**`,
  `- MISSING metadata: **${groups.MISSING.length}**`,
  `- Movies requiring editorial/media attention: **${weak.length}**`, '',
  'Complete means the currently available title, slug, year, genre, description, temporary poster source, and YouTube ID are present. It does not mean that unavailable cast, director, country, language, runtime, or backdrop data has been invented.', '',
  '## Editorial inventory', '',
  `- Published articles: **${articles.length}**`,
  `- Published topic hubs: **${topics.length}**`,
  `- Article categories: **${[...new Set(articles.map(a => a.category))].join(', ')}**`, '',
  '## Priority movie enrichment queue', '',
  'The following records should be reviewed first because their descriptions are short or key temporary media is unavailable. Improve only from original editorial work or verified, attributable information.', '',
  ...weak.slice(0, 30).map(m => `- [ ] **${m.title}** (${m.year || 'year unavailable'}) — ${m.genre || 'genre unavailable'}`), '',
  '## Publishing checks', '',
  '- Confirm claims against reliable primary/official sources before adding factual metadata.',
  '- Add publication or update dates only when known and meaningful.',
  '- Add a licensed/official cover image when rights are clear; do not scrape artwork.',
  '- Keep unpublished drafts out of the generated public data, search index and sitemap.', ''
];
fs.mkdirSync(path.join(root, 'reports'), { recursive: true });
fs.writeFileSync(path.join(root, 'reports', 'content-seo-audit.md'), lines.join('\n'));
console.log(`Audited ${movies.length} movies; ${weak.length} are in the enrichment queue.`);

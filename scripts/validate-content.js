#!/usr/bin/env node
/* Fails the static build before drafts, duplicate slugs or incomplete content become public. */
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..');
const fail = message => { console.error(`Content validation failed: ${message}`); process.exitCode = 1; };
const read = file => JSON.parse(fs.readFileSync(path.join(root, file), 'utf8'));
const unique = (items, label) => {
  const seen = new Set();
  items.forEach(item => { if (!item.slug) fail(`${label} has a missing slug`); else if (seen.has(item.slug)) fail(`duplicate ${label} slug: ${item.slug}`); else seen.add(item.slug); });
};
const movies = read('data/movies.json');
const articles = read('data/articles.json');
const topics = read('data/topics.json');
unique(movies, 'movie'); unique(articles, 'article'); unique(topics, 'topic');
movies.forEach(m => { if (m.status !== 'published' || !m.title || !m.description || !m.year || !m.genre) fail(`movie ${m.id} is incomplete or not published`); });
articles.forEach(a => { const hasItems = Array.isArray(a.items) && a.items.length; const hasBlocks = Array.isArray(a.blocks) && a.blocks.length; if (a.status !== 'published' || !a.title || !a.description || !a.category || (!hasItems && !hasBlocks)) fail(`article ${a.id} is incomplete or not published`); });
topics.forEach(t => { if (t.status !== 'published' || !t.title || !t.description || !Array.isArray(t.movieSlugs) || !t.movieSlugs.length) fail(`topic ${t.id} is incomplete or not published`); });
if (!process.exitCode) console.log(`Validated ${movies.length} published movies, ${articles.length} published articles and ${topics.length} published topics.`);

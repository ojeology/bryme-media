#!/usr/bin/env node
/* Validate content/results.json against the fixture lists.
 * Fails if a result is unattributable, malformed, or points at a fixture that does not exist.
 * Run: node scripts/validate-results.js
 */
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..');
const FIXTURE_FILES = {
  'premier-league': 'fixtures.json', 'la-liga': 'fixtures-la-liga.json',
  'serie-a': 'fixtures-serie-a.json', 'bundesliga': 'fixtures-bundesliga.json',
  'ligue-1': 'fixtures-ligue-1.json'
};
const RESULTS = JSON.parse(fs.readFileSync(path.join(root, 'content', 'results.json'), 'utf8'));

let checked = 0, problems = [];
for (const [league, file] of Object.entries(FIXTURE_FILES)) {
  const entries = RESULTS[league] || {};
  const fp = path.join(root, 'content', file);
  if (!fs.existsSync(fp)) { if (Object.keys(entries).length) problems.push(`${league}: results exist but ${file} is missing`); continue; }
  const F = JSON.parse(fs.readFileSync(fp, 'utf8'));
  const valid = new Set();
  (F.matchweeks || []).forEach(w => w.matches.forEach(m => valid.add(m.id + '-vs-' + m.away)));

  for (const [slug, r] of Object.entries(entries)) {
    checked++;
    const at = `${league}/${slug}`;
    if (!valid.has(slug)) problems.push(`${at}: no such fixture in ${file}`);
    if (!Number.isInteger(r.homeScore) || !Number.isInteger(r.awayScore)) problems.push(`${at}: homeScore/awayScore must be integers`);
    if (r.homeScore < 0 || r.awayScore < 0) problems.push(`${at}: negative score`);
    if (!r.source || !r.source.url) problems.push(`${at}: missing source.url — a result must be attributable`);
    else if (!/^https?:\/\//.test(r.source.url)) problems.push(`${at}: source.url is not a URL`);
    if (r.status && !['FT', 'AET', 'FT (pens)'].includes(r.status)) problems.push(`${at}: unexpected status "${r.status}"`);
    if (r.status === 'FT (pens)' && !r.penalties) problems.push(`${at}: status is "FT (pens)" but no penalties score given`);
    if (r.playedOn && !/^\d{4}-\d{2}-\d{2}$/.test(r.playedOn)) problems.push(`${at}: playedOn must be YYYY-MM-DD`);
    (r.scorers || []).forEach((g, i) => {
      if (!['home', 'away'].includes(g.team)) problems.push(`${at}: scorer ${i} has team "${g.team}", expected home/away`);
      if (!g.player) problems.push(`${at}: scorer ${i} has no player name`);
    });
  }
}

if (problems.length) {
  console.error(`Validated ${checked} result(s); ${problems.length} problem(s):`);
  problems.forEach(p => console.error('  - ' + p));
  process.exit(1);
}
console.log(`Validated ${checked} match result(s) across ${Object.keys(FIXTURE_FILES).length} leagues; all reference real fixtures and carry a source.`);

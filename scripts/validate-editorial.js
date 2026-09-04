#!/usr/bin/env node
/* Validate content/match-editorial.json against the fixture database.
 * Run: node scripts/validate-editorial.js
 */
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..');
const FIXTURES = {
  'premier-league': 'fixtures.json', 'la-liga': 'fixtures-la-liga.json',
  'serie-a': 'fixtures-serie-a.json', 'bundesliga': 'fixtures-bundesliga.json',
  'ligue-1': 'fixtures-ligue-1.json'
};
const ISO = /^\d{4}-\d{2}-\d{2}$/;
const FIELDS = ['overview','recentForm','headToHead','lastFiveMeetings','homeAwayForm','keyPlayers',
  'injuries','suspensions','expectedLineups','tacticalMatchup','historicalContext','underdog','outlook','scorePrediction'];
const PM_FIELDS = ['whatHappened','tacticalDevelopments','keyPerformers','disappointing','vsPrediction','analysis'];

const ED = JSON.parse(fs.readFileSync(path.join(root, 'content/match-editorial.json'), 'utf8'));
const RESULTS = fs.existsSync(path.join(root, 'content/results.json'))
  ? JSON.parse(fs.readFileSync(path.join(root, 'content/results.json'), 'utf8')) : {};

let checked = 0, live = 0, problems = [], warnings = [];
for (const [league, file] of Object.entries(FIXTURES)) {
  const entries = ED[league];
  if (entries === undefined) { problems.push(`results/editorial: missing "${league}" bucket in match-editorial.json`); continue; }
  const fp = path.join(root, 'content', file);
  if (!fs.existsSync(fp)) { if (Object.keys(entries).length) problems.push(`${league}: editorial exists but ${file} is missing`); continue; }
  const F = JSON.parse(fs.readFileSync(fp, 'utf8'));
  const valid = new Map();
  (F.matchweeks || []).forEach(w => (w.matches || []).forEach(m => valid.set(m.id + '-vs-' + m.away, m)));

  for (const [slug, e] of Object.entries(entries)) {
    checked++;
    const at = `${league}/${slug}`;
    if (!valid.has(slug)) { problems.push(`${at}: no such fixture in ${file} - a preview must map to a real fixture, and to exactly one URL`); continue; }
    if (!e.publishedAt) problems.push(`${at}: publishedAt is required (it becomes datePublished)`);
    else if (!ISO.test(e.publishedAt)) problems.push(`${at}: publishedAt "${e.publishedAt}" must be YYYY-MM-DD`);
    if (e.updatedAt && !ISO.test(e.updatedAt)) problems.push(`${at}: updatedAt "${e.updatedAt}" must be YYYY-MM-DD`);
    if (e.updatedAt && e.publishedAt && e.updatedAt < e.publishedAt) problems.push(`${at}: updatedAt is before publishedAt`);

    const filled = FIELDS.filter(k => {
      const v = e[k];
      return Array.isArray(v) ? v.length > 0 : (typeof v === 'string' && v.trim().length > 12);
    });
    if (filled.length >= 3) live++;
    else warnings.push(`${at}: only ${filled.length} populated field(s) - stays noindex until it has at least 3`);

    for (const k of Object.keys(e)) {
      if (!FIELDS.includes(k) && !['publishedAt','updatedAt','sources','sourcesCheckedOn','postMatch','migratedFrom', 'retrospective'].includes(k))
        warnings.push(`${at}: unrecognised field "${k}"`);
    }
    (e.sources || []).forEach((sx, i) => {
      if (!sx || !sx.url || !/^https?:\/\//.test(sx.url)) problems.push(`${at}: source ${i} needs a http(s) url`);
    });

    if (e.postMatch) {
      const pm = e.postMatch;
      const res = (RESULTS[league] || {})[slug];
      if (!res) problems.push(`${at}: has postMatch analysis but no recorded result - add the result first so the score is sourced`);
      if (pm.publishedAt && !ISO.test(pm.publishedAt)) problems.push(`${at}: postMatch.publishedAt must be YYYY-MM-DD`);
      if (pm.publishedAt && e.publishedAt && pm.publishedAt < e.publishedAt) problems.push(`${at}: postMatch is dated before the preview`);
      const pmFilled = PM_FIELDS.filter(k => typeof pm[k] === 'string' && pm[k].trim().length > 12);
      if (!pmFilled.length) warnings.push(`${at}: postMatch present but empty`);
      for (const k of Object.keys(pm)) if (!PM_FIELDS.includes(k) && k !== 'publishedAt') warnings.push(`${at}: unrecognised postMatch field "${k}"`);
      /* History preservation: after a match, the preview must still be there.
         The exception is a fixture BRYME never previewed - a match played before we
         covered that league at all. Those are written up retrospectively and there is
         no history to preserve. They must say so explicitly with "retrospective": true,
         so that the flag is a deliberate editorial statement rather than a way to
         quietly skip the check on a fixture we did preview and then overwrote. */
      if (filled.length < 3 && !e.retrospective) {
        problems.push(`${at}: post-match update must not remove the pre-match preview` +
          ` (if this match was never previewed, mark the entry "retrospective": true)`);
      }
      if (e.retrospective && filled.length >= 3) {
        warnings.push(`${at}: marked retrospective but has a full preview - remove the flag`);
      }
    }
  }
}

warnings.forEach(w => console.warn('  warning: ' + w));
if (problems.length) {
  console.error(`\nValidated ${checked} editorial entr(ies); ${problems.length} problem(s):`);
  problems.forEach(p => console.error('  - ' + p));
  process.exit(1);
}
console.log(`Validated ${checked} editorial entr(ies) across ${Object.keys(FIXTURES).length} leagues; ${live} are live/indexable, all map to real fixtures with ISO dates.`);

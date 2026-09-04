#!/usr/bin/env node
/* Add a match result to content/results.json.
 *
 *   node scripts/add-result.js --league premier-league --match arsenal-vs-coventry \
 *        --score 2-1 --source-name "Premier League" --source-url "https://www.premierleague.com/..." \
 *        [--status "FT"] [--played 2026-08-21] [--attendance 60000] \
 *        [--scorer "home:Saka:23"] [--scorer "away:Wright:71"]
 *
 * Refuses to write unless the fixture exists and a source URL is supplied.
 * List what is still unplayed:  node scripts/add-result.js --league premier-league --list
 */
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..');
const FIXTURE_FILES = {
  'premier-league': 'fixtures.json', 'la-liga': 'fixtures-la-liga.json',
  'serie-a': 'fixtures-serie-a.json', 'bundesliga': 'fixtures-bundesliga.json',
  'ligue-1': 'fixtures-ligue-1.json'
};

const args = process.argv.slice(2);
const get = (flag) => { const i = args.indexOf(flag); return i > -1 ? args[i + 1] : undefined; };
const all = (flag) => args.reduce((a, x, i) => (x === flag ? a.concat(args[i + 1]) : a), []);
const has = (flag) => args.includes(flag);

const league = get('--league');
if (!league || !FIXTURE_FILES[league]) {
  console.error('--league must be one of: ' + Object.keys(FIXTURE_FILES).join(', '));
  process.exit(1);
}

const F = JSON.parse(fs.readFileSync(path.join(root, 'content', FIXTURE_FILES[league]), 'utf8'));
const fixtures = new Map();
(F.matchweeks || []).forEach(w => w.matches.forEach(m =>
  fixtures.set(m.id + '-vs-' + m.away, { round: w.number, home: m.homeName, away: m.awayName, date: m.date })));

const resultsPath = path.join(root, 'content', 'results.json');
const RESULTS = JSON.parse(fs.readFileSync(resultsPath, 'utf8'));
RESULTS[league] = RESULTS[league] || {};

if (has('--list')) {
  const done = new Set(Object.keys(RESULTS[league]));
  const todo = [...fixtures.entries()].filter(([k]) => !done.has(k));
  console.log(`${league}: ${done.size} played, ${todo.length} still to come\n`);
  todo.slice(0, Number(get('--limit') || 12)).forEach(([k, f]) =>
    console.log(`  ${f.date}  ${String(f.home + ' v ' + f.away).padEnd(44)} ${k}`));
  process.exit(0);
}

const match = get('--match');
const score = get('--score');
const sourceUrl = get('--source-url');
const sourceName = get('--source-name');

const fail = (msg) => { console.error('REFUSED: ' + msg); process.exit(1); };
if (!match) fail('--match is required (e.g. arsenal-vs-coventry). Use --list to see the slugs.');
if (!fixtures.has(match)) fail(`no fixture "${match}" in ${league}. Use --list to see valid slugs.`);
if (!score || !/^\d+-\d+$/.test(score)) fail('--score must look like 2-1');
if (!sourceUrl || !/^https?:\/\//.test(sourceUrl)) fail('--source-url is required and must be a URL. BRYME does not publish a scoreline it cannot attribute.');

const [homeScore, awayScore] = score.split('-').map(Number);
const scorers = all('--scorer').filter(Boolean).map(sp => {
  const [team, player, minute] = String(sp).split(':');
  if (!['home', 'away'].includes(team) || !player) fail(`--scorer must be team:player[:minute], got "${sp}"`);
  return minute ? { team, player, minute } : { team, player };
});

const entry = { homeScore, awayScore, status: get('--status') || 'FT' };
if (get('--penalties')) entry.penalties = get('--penalties');
if (get('--played')) entry.playedOn = get('--played');
if (get('--attendance')) entry.attendance = Number(get('--attendance'));
if (scorers.length) entry.scorers = scorers;
entry.source = { name: sourceName || new URL(sourceUrl).hostname.replace(/^www\./, ''), url: sourceUrl };
entry.verifiedOn = get('--verified') || new Date().toISOString().slice(0, 10);

const f = fixtures.get(match);
const existed = !!RESULTS[league][match];
RESULTS[league][match] = entry;
fs.writeFileSync(resultsPath, JSON.stringify(RESULTS, null, 2) + '\n');

console.log(`${existed ? 'Updated' : 'Added'}: ${f.home} ${homeScore}-${awayScore} ${f.away} (${entry.status}, round ${f.round})`);
console.log(`Source: ${entry.source.name} — ${entry.source.url}`);
console.log('\nNow rebuild so the page and sitemap pick it up:');
console.log('  node scripts/build-static-foundation.js');

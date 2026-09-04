#!/usr/bin/env node
/* BRYME weekly editorial queue.
 *
 * Shows which fixtures are entering the 3-5 day editorial window and still have no
 * preview, so the week's work is a list rather than a guess.
 *
 *   node scripts/editorial-queue.js                 # next 5 days, all leagues
 *   node scripts/editorial-queue.js --days 7
 *   node scripts/editorial-queue.js --league premier-league
 *   node scripts/editorial-queue.js --overdue       # inside 3 days and still unwritten
 *   node scripts/editorial-queue.js --played        # finished but no result recorded
 *   node scripts/editorial-queue.js --today 2026-08-18   # pretend it is this date
 *
 * Writing a preview = add an entry to content/match-editorial.json, then rebuild.
 */
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..');
const FIXTURES = {
  'premier-league': 'fixtures.json', 'la-liga': 'fixtures-la-liga.json',
  'serie-a': 'fixtures-serie-a.json', 'bundesliga': 'fixtures-bundesliga.json',
  'ligue-1': 'fixtures-ligue-1.json'
};
const WINDOW_OPEN = 5, WINDOW_DUE = 3;

const args = process.argv.slice(2);
const get = f => { const i = args.indexOf(f); return i > -1 ? args[i + 1] : undefined; };
const has = f => args.includes(f);
const TODAY = get('--today') || new Date().toISOString().slice(0, 10);
const DAYS = Number(get('--days') || WINDOW_OPEN);
const onlyLeague = get('--league');

const readJson = p => JSON.parse(fs.readFileSync(p, 'utf8'));
const EDITORIAL = fs.existsSync(path.join(root, 'content/match-editorial.json'))
  ? readJson(path.join(root, 'content/match-editorial.json')) : {};
const RESULTS = fs.existsSync(path.join(root, 'content/results.json'))
  ? readJson(path.join(root, 'content/results.json')) : {};
const FIELDS = ['overview','recentForm','headToHead','lastFiveMeetings','homeAwayForm','keyPlayers',
  'injuries','suspensions','expectedLineups','tacticalMatchup','historicalContext','underdog','outlook','scorePrediction'];
const filled = e => !e ? 0 : FIELDS.filter(k => {
  const v = e[k];
  return Array.isArray(v) ? v.length > 0 : (typeof v === 'string' && v.trim().length > 12);
}).length;
const days = d => Math.round((Date.parse(d + 'T00:00:00Z') - Date.parse(TODAY + 'T00:00:00Z')) / 86400000);

const rows = [];
for (const [league, file] of Object.entries(FIXTURES)) {
  if (onlyLeague && league !== onlyLeague) continue;
  const fp = path.join(root, 'content', file);
  if (!fs.existsSync(fp)) continue;
  const F = readJson(fp);
  (F.matchweeks || []).forEach(w => (w.matches || []).forEach(m => {
    const slug = m.id + '-vs-' + m.away;
    const d = days(m.date);
    rows.push({
      league, slug, round: w.number, date: m.date, d,
      label: `${m.homeName} v ${m.awayName}`,
      ed: (EDITORIAL[league] || {})[slug],
      res: (RESULTS[league] || {})[slug]
    });
  }));
}

const pad = (s, n) => String(s).padEnd(n).slice(0, n);
const show = (list, title, hint) => {
  console.log(`\n${title} (${list.length})`);
  if (!list.length) { console.log('  nothing'); return; }
  if (hint) console.log(`  ${hint}`);
  list.sort((a, b) => a.date.localeCompare(b.date) || a.league.localeCompare(b.league));
  list.forEach(r => console.log(
    `  ${r.date}  ${r.d >= 0 ? 'T-' + String(r.d).padStart(2) : 'T+' + String(-r.d).padStart(2)}  ${pad(r.league, 15)} ${pad(r.label, 40)} ${r.slug}`));
};

if (has('--played')) {
  show(rows.filter(r => r.d < 0 && !r.res), 'PLAYED, NO RESULT RECORDED',
    'add with: node scripts/add-result.js --league <l> --match <slug> --score X-Y --source-url ...');
} else if (has('--overdue')) {
  show(rows.filter(r => r.d >= 0 && r.d < WINDOW_DUE && filled(r.ed) < 3),
    `OVERDUE - kicks off within ${WINDOW_DUE} days, still no preview`,
    'these should already be live and crawlable');
} else {
  const win = rows.filter(r => r.d >= 0 && r.d <= DAYS);
  show(win.filter(r => filled(r.ed) < 3), `TO WRITE - kickoff within ${DAYS} days, no preview yet`,
    'add an entry to content/match-editorial.json, then rebuild');
  show(win.filter(r => filled(r.ed) >= 3), `ALREADY LIVE - preview published, indexable`);
  const late = rows.filter(r => r.d >= 0 && r.d < WINDOW_DUE && filled(r.ed) < 3);
  if (late.length) console.log(`\n!! ${late.length} fixture(s) inside the ${WINDOW_DUE}-day mark with no preview. Run --overdue.`);
  const unrec = rows.filter(r => r.d < 0 && !r.res);
  if (unrec.length) console.log(`!! ${unrec.length} played fixture(s) with no result recorded. Run --played.`);
  console.log(`\nToday: ${TODAY}. Window opens T-${WINDOW_OPEN}, page should be live by T-${WINDOW_DUE}.`);
}

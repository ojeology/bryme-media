#!/usr/bin/env node
/* BRYME — ESPN public API -> content/competitions.json
   Top-five competitions for the Mini App sports section:
   standings + recent scores (last 5 days) + fixtures (next 7 days).
   Champions League included (uefa.champions league phase, 36 teams).
   Agent-safe: a competition that fails to fetch/validate is skipped;
   if nothing validates, the existing file is kept untouched. */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "content", "competitions.json");

const COMPETITIONS = [
  { id: "premier-league",   code: "eng.1",          name: "Premier League",   flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿" },
  { id: "la-liga",          code: "esp.1",          name: "La Liga",          flag: "🇪🇸" },
  { id: "serie-a",          code: "ita.1",          name: "Serie A",          flag: "🇮🇹" },
  { id: "bundesliga",       code: "ger.1",          name: "Bundesliga",       flag: "🇩🇪" },
  { id: "ligue-1",          code: "fra.1",          name: "Ligue 1",          flag: "🇫🇷" },
  { id: "champions-league", code: "uefa.champions", name: "Champions League", flag: "🇪🇺" }
];

const DAY = 86400000;
function ymd(d) { return d.toISOString().slice(0, 10).replace(/-/g, ""); }
function iso(d) { return d.toISOString().slice(0, 10); }
function statMap(entry) { const m = {}; (entry.stats || []).forEach((s) => { m[s.name] = s; }); return m; }
function num(v) { const n = Number(v); return Number.isFinite(n) ? n : 0; }
function logo(team) { return (team.logos && team.logos[0] && team.logos[0].href) || ""; }
function short(team) { return team.shortDisplayName || team.abbreviation || team.displayName || "?"; }

async function getJson(url) {
  const r = await fetch(url, { headers: { "user-agent": "bryme-agent/1.0" }, signal: AbortSignal.timeout(20000) });
  if (!r.ok) throw new Error("HTTP " + r.status + " " + url.slice(-40));
  return r.json();
}

async function fetchStandings(c) {
  const d = await getJson("https://site.api.espn.com/apis/v2/sports/soccer/" + c.code + "/standings");
  const entries = d && d.children && d.children[0] && d.children[0].standings && d.children[0].standings.entries;
  if (!Array.isArray(entries) || entries.length < 6) throw new Error(c.id + " thin standings");
  const teams = entries.map((e) => {
    const s = statMap(e); const team = e.team || {};
    const gf = num((s.pointsFor || {}).displayValue ?? (s.pointsFor || {}).summary);
    const ga = num((s.pointsAgainst || {}).displayValue ?? (s.pointsAgainst || {}).summary);
    return {
      name: team.displayName || "?",
      short: short(team),
      logo: logo(team),
      p: num((s.gamesPlayed || {}).displayValue ?? (s.gamesPlayed || {}).summary),
      w: num((s.wins || {}).displayValue ?? (s.wins || {}).summary),
      d: num((s.ties || {}).displayValue ?? (s.ties || {}).summary),
      l: num((s.losses || {}).displayValue ?? (s.losses || {}).summary),
      gf,
      ga,
      // Derive goal difference from the same goals-for/against values we publish.
      // ESPN's pointDifferential summary has been absent/zero for soccer feeds.
      gd: String(gf - ga),
      pts: num((s.points || {}).displayValue ?? (s.points || {}).summary)
    };
  }).filter((t) => t.name !== "?")
    .sort((a, b) => b.pts - a.pts || num(b.gd) - num(a.gd) || b.gf - a.gf || a.name.localeCompare(b.name));
  if (teams.length < 6) throw new Error(c.id + " too few valid teams");
  teams.forEach((t, i) => { t.pos = i + 1; });
  return teams;
}

function eventRow(ev) {
  const comp = ev.competitions && ev.competitions[0];
  if (!comp || !Array.isArray(comp.competitors) || comp.competitors.length !== 2) return null;
  let h = null, a = null;
  comp.competitors.forEach((x) => { if (x.homeAway === "home") h = x; else if (x.homeAway === "away") a = x; });
  if (!h || !a) return null;
  const row = {
    date: iso(new Date(ev.date)),
    home: h.team.displayName, hshort: short(h.team), hlogo: logo(h.team),
    away: a.team.displayName, ashort: short(a.team), alogo: logo(a.team)
  };
  const st = ev.status && ev.status.type || {};
  if (st.state === "post") {
    /* ESPN returns score either as plain string or {displayValue} — handle both. */
    const sv = (x) => (x.score && typeof x.score === "object" ? num(x.score.displayValue) : num(x.score));
    row.hs = sv(h); row.as = sv(a);
    row.status = "FT";
  } else {
    row.time = (ev.date || "").slice(11, 16);
    row.status = st.detail || "Scheduled";
  }
  return row;
}

async function fetchBoard(c, from, to) {
  const d = await getJson("https://site.api.espn.com/apis/site/v2/sports/soccer/" + c.code +
    "/scoreboard?dates=" + ymd(from) + "-" + ymd(to) + "&limit=100");
  const evs = Array.isArray(d.events) ? d.events : [];
  return evs.map(eventRow).filter(Boolean);
}

async function fetchScorers(c) {
  const d = await getJson("https://site.api.espn.com/apis/site/v2/sports/soccer/" + c.code + "/statistics");
  const stats = Array.isArray(d.stats) ? d.stats : [];
  const goals = stats.filter((s) => s.name === "goalsLeaders")[0];
  const leaders = goals && Array.isArray(goals.leaders) ? goals.leaders : [];
  return leaders.slice(0, 10).map((l) => {
    const a = l.athlete || {};
    const apps = (a.statistics || []).filter((s) => s.name === "appearances")[0];
    return {
      name: a.displayName || "?",
      team: (a.team && (a.team.abbreviation || a.team.shortDisplayName)) || "",
      logo: (a.team && a.team.logos && a.team.logos[0] && a.team.logos[0].href) || "",
      goals: num(l.value),
      apps: num(apps && (apps.displayValue ?? apps.value))
    };
  }).filter((x) => x.name !== "?");
}

(async () => {
  const now = new Date();
  const past = new Date(now.getTime() - 5 * DAY);
  const future = new Date(now.getTime() + 7 * DAY);
  const out = [];
  for (const c of COMPETITIONS) {
    try {
      const teams = await fetchStandings(c);
      const board = await fetchBoard(c, past, future);
      /* scoreboard events don't carry logos — backfill from standings by team name */
      const logoBy = {};
      teams.forEach((t) => { if (t.logo) logoBy[t.name] = t.logo; });
      board.forEach((r) => {
        if (!r.hlogo && logoBy[r.home]) r.hlogo = logoBy[r.home];
        if (!r.alogo && logoBy[r.away]) r.alogo = logoBy[r.away];
      });
      const scores = board.filter((r) => r.status === "FT").slice(-14).reverse();
      const fixtures = board.filter((r) => r.status !== "FT").slice(0, 14);
      let scorers = [];
      try { scorers = await fetchScorers(c); } catch (e) { console.log("     scorers unavailable:", e.message); }
      out.push({ id: c.id, name: c.name, flag: c.flag, teams, scores, fixtures, scorers });
      console.log("ok  ", c.id, "(" + teams.length + " teams, " + scores.length + " scores, " + fixtures.length + " fixtures, " + scorers.length + " scorers)");
    } catch (e) { console.log("skip", c.id, "-", e.message); }
  }
  if (!out.length) {
    if (fs.existsSync(OUT)) { console.log("no data — keeping existing file"); process.exit(0); }
    console.error("no data at all"); process.exit(1);
  }
  fs.writeFileSync(OUT, JSON.stringify({ builtAt: new Date().toISOString(), competitions: out }, null, 1) + "\n");
  console.log("wrote", path.relative(ROOT, OUT), "—", out.length, "competitions");
})().catch((e) => { console.error(e.message); process.exit(1); });

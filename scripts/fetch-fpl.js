#!/usr/bin/env node
/* Official Fantasy Premier League API -> content/fpl.json
   Player points only. Nothing invented. */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "content", "fpl.json");
const BASE = "https://fantasy.premierleague.com/api";

const POS = { 1: "GKP", 2: "DEF", 3: "MID", 4: "FWD" };

async function getJson(url) {
  const r = await fetch(url, {
    headers: { "user-agent": "Mozilla/5.0 (compatible; BRYME/1.0)", accept: "application/json" },
    signal: AbortSignal.timeout(25000)
  });
  if (!r.ok) throw new Error("HTTP " + r.status + " " + url);
  return r.json();
}

function playerRow(el, teams, extra) {
  const t = teams[el.team] || {};
  return Object.assign({
    id: el.id,
    name: el.web_name,
    team: t.short || "",
    teamName: t.name || "",
    pos: POS[el.element_type] || "",
    price: Math.round(el.now_cost) / 10,
    total: el.total_points || 0,
    gw: el.event_points || 0,
    g: el.goals_scored || 0,
    a: el.assists || 0,
    sel: el.selected_by_percent || ""
  }, extra || {});
}

function liveRow(el, live, teams) {
  const st = (live && live.stats) || {};
  const t = teams[el.team] || {};
  return {
    id: el.id,
    name: el.web_name,
    team: t.short || "",
    teamName: t.name || "",
    pos: POS[el.element_type] || "",
    pts: st.total_points || 0,
    min: st.minutes || 0,
    g: st.goals_scored || 0,
    a: st.assists || 0,
    bonus: st.bonus || 0,
    cs: st.clean_sheets || 0,
    total: el.total_points || 0
  };
}

(async () => {
  const boot = await getJson(BASE + "/bootstrap-static/");
  const fixtures = await getJson(BASE + "/fixtures/");
  const teams = {};
  (boot.teams || []).forEach((t) => {
    teams[t.id] = { name: t.name, short: t.short_name };
  });
  const events = (boot.events || []).map((e) => ({
    id: e.id,
    name: e.name,
    deadline: e.deadline_time,
    finished: !!e.finished,
    isCurrent: !!e.is_current,
    isNext: !!e.is_next,
    average: e.average_entry_score || 0,
    highest: e.highest_score || 0
  }));
  const current = events.find((e) => e.isCurrent) || events.find((e) => e.finished);
  const next = events.find((e) => e.isNext);
  const previous = events.filter((e) => e.finished).slice(-2);

  const wantGw = new Set();
  previous.forEach((e) => wantGw.add(e.id));
  if (current) wantGw.add(current.id);
  if (next) wantGw.add(next.id);

  const byGw = {};
  for (const id of wantGw) {
    byGw[id] = { fixtures: [], players: [] };
  }

  (fixtures || []).forEach((f) => {
    const gw = f.event;
    if (!byGw[gw]) return;
    const h = teams[f.team_h] || {};
    const a = teams[f.team_a] || {};
    byGw[gw].fixtures.push({
      kickoff: f.kickoff_time,
      home: h.name, hshort: h.short,
      away: a.name, ashort: a.short,
      hs: f.team_h_score,
      as: f.team_a_score,
      finished: !!f.finished
    });
  });

  const els = {};
  (boot.elements || []).forEach((el) => { els[el.id] = el; });

  for (const id of wantGw) {
    const ev = events.find((e) => e.id === id);
    if (!ev || !ev.finished) continue;
    try {
      const live = await getJson(BASE + "/event/" + id + "/live/");
      const rows = (live.elements || []).map((x) => {
        const el = els[x.id];
        if (!el) return null;
        return liveRow(el, x, teams);
      }).filter((r) => r && r.pts > 0)
        .sort((a, b) => b.pts - a.pts || b.total - a.total || a.name.localeCompare(b.name))
        .slice(0, 60);
      byGw[id].players = rows;
      console.log("ok  GW" + id, rows.length, "players with points");
    } catch (e) {
      console.log("skip live GW" + id, e.message);
    }
  }

  const season = (boot.elements || [])
    .map((el) => playerRow(el, teams))
    .filter((p) => p.total > 0)
    .sort((a, b) => b.total - a.total || b.gw - a.gw || a.name.localeCompare(b.name))
    .slice(0, 50);

  const out = {
    builtAt: new Date().toISOString(),
    source: "https://fantasy.premierleague.com/",
    current: current ? current.id : 0,
    next: next ? next.id : 0,
    events,
    gameweeks: byGw,
    season
  };
  fs.writeFileSync(OUT, JSON.stringify(out) + "\n");
  console.log("wrote", path.relative(ROOT, OUT), "current GW" + out.current, "next GW" + out.next);
})().catch((e) => { console.error(e.message); process.exit(1); });

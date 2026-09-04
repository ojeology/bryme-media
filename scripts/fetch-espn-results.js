#!/usr/bin/env node
/* BRYME auto-scores — ESPN public API -> content/results.json.
   Never overwrites; validates pairings against fixtures. Dry: --dry */
const fs = require("fs");
const path = require("path");
const root = path.resolve(__dirname, "..");
const LEAGUES = {
  "premier-league": { file: "fixtures.json", code: "eng.1" },
  "la-liga": { file: "fixtures-la-liga.json", code: "esp.1" },
  "serie-a": { file: "fixtures-serie-a.json", code: "ita.1" },
  "bundesliga": { file: "fixtures-bundesliga.json", code: "ger.1" },
  "ligue-1": { file: "fixtures-ligue-1.json", code: "fra.1" }
};
const ALIASES = {
  "internazionale": "inter", "inter milan": "inter", "as roma": "roma",
  "marseille": "olympique de marseille", "paris saint germain": "psg", "paris sg": "psg",
  "deportivo la coruna": "coruna", "deportivo de la coruna": "coruna", "deportivo": "coruna",
  "atalanta bc": "atalanta", "ac milan": "milan", "athletic club": "athletic bilbao",
  "rayo": "rayo vallecano", "spurs": "tottenham", "tottenham hotspur": "tottenham",
  "manchester city": "man city", "manchester united": "man utd", "newcastle": "newcastle united",
  "brighton and hove albion": "brighton", "brighton hove albion": "brighton", "brighton hove": "brighton",
  "wolves": "wolverhampton", "nottm forest": "nottingham forest", "west ham united": "west ham",
  "leicester city": "leicester", "rc lens": "lens", "ogc nice": "nice", "fc lorient": "lorient",
  "stade brestois": "brest", "stade brestois 29": "brest", "toulouse fc": "toulouse",
  "angers sco": "angers", "lille osc": "lille", "lille losc": "lille", "rc strasbourg": "strasbourg",
  "strasbourg alsace": "strasbourg", "le mans fc": "le mans", "aj auxerre": "auxerre",
  "lyon": "olympique lyonnais", "estac troyes": "troyes", "rennes": "stade rennais",
  "hull": "hull city", "coventry": "coventry city", "ac monza": "monza",
  "1 fc union berlin": "union berlin", "fc union berlin": "union berlin",
  "fc cologne": "1 fc koln", "cologne": "1 fc koln", "1 fc koln": "1 fc koln",
  "hamburg sv": "hamburger sv", "hamburger sv": "hamburger sv",
  "sc paderborn 07": "paderborn", "paderborn 07": "paderborn", "sc paderborn": "paderborn",
  "mainz": "mainz 05", "fsv mainz 05": "mainz 05", "fsv mainz": "mainz 05",
  "tsg 1899 hoffenheim": "tsg hoffenheim", "1899 hoffenheim": "tsg hoffenheim",
  "borussia dortmund": "borussia dortmund"
};
const DENY = new Set(["ligue-1/rennes-vs-psg"]);
const STRIP = /^(as|ac|sc|rc|ogc|aj|fc|usc|ss|calcio|club|deportivo de la|the)\s+/i;
function norm(name) {
  let n = name.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/&/g, "and").replace(/[^a-z0-9 ]/g, " ").replace(/\s+/g, " ").trim();
  if (ALIASES[n]) return ALIASES[n];
  let s = n.replace(STRIP, "").replace(/\s+(fc|cf|afc|bk|sk)\b/g, "").trim();
  if (ALIASES[s]) return ALIASES[s];
  return s;
}
function iso(d) { return d.toISOString().slice(0, 10); }

const fsx = require("fs");
const pathx = require("path");
const LABELS = {
  "premier-league": ["Premier League", "/sports/premier-league/", "Matchweek"],
  "serie-a": ["Serie A", "/sports/serie-a/", "Matchday"],
  "la-liga": ["La Liga", "/sports/la-liga/", "Jornada"],
  "bundesliga": ["Bundesliga", "/sports/bundesliga/", "Matchday"],
  "ligue-1": ["Ligue 1", "/sports/ligue-1/", "Matchday"]
};
function escx(t) { return String(t == null ? "" : t).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
function buildReport(lg, mid, r, homeName, awayName, mw) {
  const L = LABELS[lg];
  const score = r.homeScore + "-" + r.awayScore;
  const date = r.playedOn || "";
  const dir = pathx.join(root, "sports", lg, "reports", mid);
  fsx.mkdirSync(dir, { recursive: true });
  const sc = (r.scorers || []).map(s => "<tr><td>" + (s.team === "home" ? "Home" : "Away") + "</td><td>" + escx(s.player) + "</td><td>" + escx(s.minute) + "</td></tr>").join("");
  const title = escx(homeName) + " " + score + " " + escx(awayName) + ": Result & Scorers | BRYME";
  const desc = escx(homeName) + " " + score + " " + escx(awayName) + " (" + date + ") - full-time result, goalscorers and verified source from " + L[0] + " 2026/27.";
  const page = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + title + '</title><meta name="description" content="' + desc + '"><link rel="canonical" href="https://bryme.onrender.com/sports/' + lg + '/reports/' + mid + '/"><link rel="stylesheet" href="/assets/site.css"><script src="/assets/analytics.js" async></script></head><body data-nav="sports" class="spx"><header class="top"><div class="shell"><a class="brand" href="/">BRY<b>ME</b></a><nav class="topnav"><a href="/">Home</a><a href="/entertainment/">🎬 Entertainment</a><a href="/sports/" class="active">⚽ Sports</a><a href="/make-money/">💰 Make Money</a><a href="/tech/">🤖 Tech &amp; AI</a><a class="nav-search" href="/search/">Search</a></nav><div class="top-tools"><a class="header-search" href="/search/" aria-label="Search">Search</a></div></div></header><main class="shell"><div class="crumb"><a href="/">Home</a> / <a href="/sports/">BRYME Sports</a> / <a href="' + L[1] + '">' + L[0] + '</a> / ' + escx(homeName) + ' v ' + escx(awayName) + '</div><section class="article-hero"><div class="eyebrow">' + L[0] + ' · ' + L[2] + ' ' + mw + '</div><h1>' + escx(homeName) + ' ' + score + ' ' + escx(awayName) + '</h1><p class="lead">' + desc + '</p><div class="article-meta"><span>BRYME Sports</span><span>' + date + '</span></div></section><article class="prose article-body"><div class="sp-table-wrap"><table class="sp-table"><tbody><tr><td><b>' + escx(homeName) + '</b></td><td><b>' + r.homeScore + '</b></td><td rowspan="2" style="text-align:center"><b>FT</b></td></tr><tr><td><b>' + escx(awayName) + '</b></td><td><b>' + r.awayScore + '</b></td></tr></tbody></table></div>' + (sc ? '<h2>Goals</h2><div class="sp-table-wrap"><table class="sp-table"><thead><tr><th>Team</th><th>Scorer</th><th>Minute</th></tr></thead><tbody>' + sc + '</tbody></table></div>' : '') + '<p>Played ' + date + '. <a href="' + (r.source && r.source.url ? r.source.url : "https://www.espn.com/soccer/") + '" rel="nofollow noopener" target="_blank">Verified source</a>.</p><p>More: <a href="/sports/' + lg + '/matches/' + mid + '/">Full match page</a> · <a href="' + L[1] + 'table/">Table</a> · <a href="' + L[1] + 'top-scorers/">Top scorers</a>.</p></article></main><nav class="mobile-nav"><a href="/"><span class="mn-ico">🏠</span>Home</a><a href="/entertainment/"><span class="mn-ico">🎬</span>Entertain</a><a href="/sports/" class="active"><span class="mn-ico">⚽</span>Sports</a><a href="/make-money/"><span class="mn-ico">💰</span>Money</a><a href="/tech/"><span class="mn-ico">🤖</span>Tech</a><a href="/search/"><span class="mn-ico">🔍</span>Search</a></nav><footer class="footer"><div class="shell"><div class="footer-grid"><div class="footer-brand"><a class="brand" href="/">BRY<b>ME</b></a><p>Discover what you love. Learn what you need. Find what&rsquo;s next.</p></div><nav class="footer-col" aria-label="Verticals"><h3>Verticals</h3><a href="/entertainment/">🎬 Entertainment</a><a href="/sports/">⚽ Sports</a><a href="/make-money/">💰 Make Money</a><a href="/tech/">🤖 Tech &amp; AI</a></nav><nav class="footer-col" aria-label="Information"><h3>Information</h3><a href="/about/">About</a><a href="/contact/">Contact</a><a href="/editorial-policy/">Editorial Policy</a></nav><nav class="footer-col" aria-label="Legal"><h3>Legal</h3><a href="/privacy/">Privacy Policy</a><a href="/terms/">Terms of Use</a><a href="/disclaimer/">Disclaimer</a><a href="/copyright/">Copyright / DMCA</a></nav></div><p class="footer-note">BRYME · Discover what you love. Learn what you need. Find what&rsquo;s next.</p></div></footer><script>window.BRYME_BASE=\'\'</script><script src="/assets/site-app.js"></script><script src="/assets/sports-engine.js"></script></body></html>';
  fsx.writeFileSync(pathx.join(dir, "index.html"), page);
  const sm = pathx.join(root, "sitemap.xml");
  let smx = fsx.readFileSync(sm, "utf8");
  const u = "https://bryme.onrender.com/sports/" + lg + "/reports/" + mid + "/";
  if (smx.indexOf(u) === -1) {
    smx = smx.replace("</urlset>", "<url><loc>" + u + "</loc><lastmod>" + date + "</lastmod></url>\n</urlset>");
    fsx.writeFileSync(sm, smx);
  }
}

(async () => {
  const dry = process.argv.includes("--dry");
  const resultsPath = path.join(root, "content/results.json");
  const results = JSON.parse(fs.readFileSync(resultsPath, "utf8"));
  const days = [];
  const now = new Date();
  for (let i = 4; i >= 0; i--) { const d = new Date(now); d.setUTCDate(d.getUTCDate() - i); days.push(iso(d)); }
  let added = 0, skipped = 0, unmatched = 0;
  const report = [];
  for (const [lg, cfg] of Object.entries(LEAGUES)) {
    const fx = JSON.parse(fs.readFileSync(path.join(root, "content", cfg.file), "utf8"));
    const validPairs = new Set();
    fx.matchweeks.forEach(w => w.matches.forEach(m => validPairs.add(`${m.id}-vs-${m.away}`)));
    const byNorm = {};
    fx.matchweeks.forEach(w => w.matches.forEach(m => {
      const h = norm(m.homeName), a = norm(m.awayName);
      byNorm[h] = byNorm[h] || {};
      byNorm[h].homeId = m.id; byNorm[h].homeName = m.homeName;
      byNorm[a] = byNorm[a] || {};
      byNorm[a].awayId = m.away; byNorm[a].awayName = m.awayName;
    }));
    for (const day of days) {
      let json;
      try {
        const r = await fetch(`https://site.api.espn.com/apis/site/v2/sports/soccer/${cfg.code}/scoreboard?dates=${day.replace(/-/g, "")}`);
        json = await r.json();
      } catch (e) { report.push(`FETCH-FAIL ${lg} ${day}: ${e.message}`); continue; }
      for (const ev of (json.events || [])) {
        const comp = ev.competitions && ev.competitions[0];
        if (!comp) continue;
        const home = comp.competitors.find(c => c.homeAway === "home");
        const away = comp.competitors.find(c => c.homeAway === "away");
        if (!home || !away) continue;
        if (!ev.status || !ev.status.type || ev.status.type.state !== "post") continue;
        const h = byNorm[norm(home.team.displayName)];
        const a = byNorm[norm(away.team.displayName)];
        if (!h || !a || !h.homeId || !a.awayId) {
          unmatched++;
          report.push(`UNMATCHED ${lg}: ${home.team.displayName} v ${away.team.displayName} (${day})`);
          continue;
        }
        const key = `${h.homeId}-vs-${a.awayId}`;
        if (DENY.has(lg + "/" + key)) { skipped++; continue; }
        if (!validPairs.has(key)) {
          unmatched++;
          report.push(`NO-FIXTURE ${lg}: -> ${key} (${day})`);
          continue;
        }
        results[lg] = results[lg] || {};
        if (results[lg][key]) { skipped++; continue; }
        let mwNum = "1";
        try {
          const w = fx.matchweeks.find(w => w.matches.some(m => (m.id + "-vs-" + m.away) === key));
          if (w) mwNum = String(w.number);
        } catch (e) {}
        const homeNorm = norm(home.team.displayName);
        const scorers = [];
        for (const d of (comp.details || [])) {
          if (!d.type || !/goal|penalty|own goal/i.test(d.type.text || "")) continue;
          const who = (d.athletesInvolved || [])[0];
          if (!who) continue;
          const tn = (d.team && (d.team.displayName || d.team.name)) || d.teamDisplayName;
          if (!tn) continue;
          scorers.push({
            team: norm(tn) === homeNorm ? "home" : "away",
            player: who.displayName || who.shortName || "",
            minute: String((d.clock && d.clock.displayValue) || "").replace(/\s/g, "")
          });
        }
        if (!scorers.length) {
          try {
            const smr = await fetch(`https://site.api.espn.com/apis/site/v2/sports/soccer/${cfg.code}/summary?event=${ev.id}`);
            const sm = await smr.json();
            for (const k of (sm.keyEvents || [])) {
              if (!k.scoringPlay || !k.participants || !k.participants[0] || !k.team) continue;
              scorers.push({
                team: norm(k.team.displayName) === homeNorm ? "home" : "away",
                player: k.participants[0].athlete.displayName || k.participants[0].athlete.shortName || "",
                minute: String((k.clock && k.clock.displayValue) || "").replace(/\s/g, "")
              });
            }
          } catch (e) {}
        }
        const link = (ev.links || []).find(l => /espn\.com/.test(l.href || ""));
        results[lg][key] = {
          homeScore: parseInt(home.score, 10) || 0,
          awayScore: parseInt(away.score, 10) || 0,
          status: "FT",
          playedOn: day,
          source: { name: "ESPN", url: (link && link.href) || "https://www.espn.com/soccer/" }
        };
        if (scorers.length) results[lg][key].scorers = scorers;
        added++;
        if (!dry) { try { buildReport(lg, key, results[lg][key], h.homeName, a.awayName, mwNum); } catch (e) { report.push("REPORT-FAIL " + key + ": " + e.message); } }
        report.push(`ADDED ${lg}: ${h.homeName} ${home.score}-${away.score} ${a.awayName} => ${key} (${day})`);
      }
    }
  }
  console.log(report.join("\n"));
  console.log(`\nsummary: ${added} added, ${skipped} already known, ${unmatched} unmatched`);
  if (dry || added === 0) { console.log(added === 0 ? "no changes" : "dry run — not writing"); process.exit(0); }
  fs.writeFileSync(resultsPath, JSON.stringify(results, null, 2) + "\n");
  try {
    const FIXF = {"premier-league":"fixtures.json","la-liga":"fixtures-la-liga.json","serie-a":"fixtures-serie-a.json","bundesliga":"fixtures-bundesliga.json","ligue-1":"fixtures-ligue-1.json"};
    const feed = { v: 1, leagues: {}, results: {} };
    for (const [lg2, f2] of Object.entries(FIXF)) {
      const fx2 = JSON.parse(fs.readFileSync(path.join(root, "content", f2), "utf8"));
      feed.leagues[lg2] = [];
      fx2.matchweeks.forEach(w => w.matches.forEach(m => feed.leagues[lg2].push([m.id, m.away, m.homeName, m.awayName, m.date, m.time || ""])));
      feed.results[lg2] = results[lg2] || {};
    }
    fs.writeFileSync(path.join(root, "content", "sports-feed.json"), JSON.stringify(feed));
    console.log("sports-feed.json refreshed");
  } catch (e) { console.log("feed refresh failed: " + e.message); }
  console.log("results.json updated");
})();

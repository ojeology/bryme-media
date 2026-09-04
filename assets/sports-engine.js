/* BRYME Match Engine v3 — boards + tables + scorers + team widgets + LIVE scores.
   Containers:
     <div data-sp-engine>…fallback…</div>                       all-league board
     <div data-sp-engine data-sp-league="premier-league">       one league
     <div data-sp-engine data-sp-table="premier-league">        live standings
     <div data-sp-engine data-sp-scorers="premier-league">      live top scorers
     <div data-sp-engine data-sp-team="premier-league/man-city"> form + position
   LIVE: on matchdays, today's cards poll ESPN directly in the browser. */
(function () {
  "use strict";
  var LEAGUES = {
    "premier-league": { label: "Premier League", file: "fixtures.json", crest: "pl", code: "eng.1" },
    "serie-a": { label: "Serie A", file: "fixtures-serie-a.json", crest: "club", code: "ita.1" },
    "la-liga": { label: "La Liga", file: "fixtures-la-liga.json", crest: "club", code: "esp.1" },
    "bundesliga": { label: "Bundesliga", file: "fixtures-bundesliga.json", crest: "club", code: "ger.1" },
    "ligue-1": { label: "Ligue 1", file: "fixtures-ligue-1.json", crest: "club", code: "fra.1" }
  };
  var ALIAS = {
    "internazionale":"inter","inter milan":"inter","as roma":"roma","marseille":"olympique de marseille",
    "paris saint germain":"psg","deportivo la coruna":"coruna","deportivo de la coruna":"coruna","deportivo":"coruna",
    "atalanta bc":"atalanta","ac milan":"milan","athletic club":"athletic bilbao","rayo":"rayo vallecano",
    "spurs":"tottenham","tottenham hotspur":"tottenham","manchester city":"man city","manchester united":"man utd",
    "newcastle":"newcastle united","brighton and hove albion":"brighton","brighton hove albion":"brighton","brighton hove":"brighton",
    "wolves":"wolverhampton","nottm forest":"nottingham forest","west ham united":"west ham","leicester city":"leicester",
    "rc lens":"lens","ogc nice":"nice","fc lorient":"lorient","stade brestois":"brest","stade brestois 29":"brest",
    "toulouse fc":"toulouse","angers sco":"angers","lille osc":"lille","lille losc":"lille","rc strasbourg":"strasbourg",
    "strasbourg alsace":"strasbourg","le mans fc":"le mans","aj auxerre":"auxerre","lyon":"olympique lyonnais",
    "estac troyes":"troyes","rennes":"stade rennais","hull":"hull city","coventry":"coventry city","ac monza":"monza"
  };
  var STRIP = /^(as|ac|sc|rc|ogc|aj|fc|usc|ss|calcio|club|deportivo de la|the)\s+/i;
  function norm(name) {
    var n = String(name).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .replace(/&/g, "and").replace(/[^a-z0-9 ]/g, " ").replace(/\s+/g, " ").trim();
    if (ALIAS[n]) return ALIAS[n];
    var s = n.replace(STRIP, "").replace(/\s+(fc|cf|afc|bk|sk)\b/g, "").trim();
    if (ALIAS[s]) return ALIAS[s];
    return s;
  }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function todayStr() { var d = new Date(); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); }
  function niceDate(iso) { var p = iso.split("-"); return new Date(+p[0], +p[1] - 1, +p[2]).toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" }); }
  /* Real club badges (downloaded from ESPN) preferred for every league;
     falls back to the existing local crest, then hides, so nothing breaks. */
  function crest(lg, id) {
    return "/assets/img/sports/badges/" + id + ".png";
  }
  function crestFallback(lg, id) {
    var dir = LEAGUES[lg].crest === "pl" ? "/assets/img/sports/pl/" : "/assets/img/sports/";
    return dir + (LEAGUES[lg].crest === "pl" ? id : "club-" + id) + ".svg";
  }
  /* reusable crest <img> with badge → svg → hide fallback chain */
  function crestImg(lg, id, sz) {
    if (!id) return "";
    if (!sz) sz = 18;
    return '<img src="' + crest(lg, id) + '" data-fb="' + crestFallback(lg, id) + '" alt="" width="' + sz +
      '" height="' + sz + '" loading="lazy" decoding="async" onerror="if(this.dataset.fb){this.src=this.dataset.fb;this.dataset.fb=\'\';}else{this.style.display=\'none\';}">';
  }
  /* name → id index so any surface showing a club name can show its badge */
  var TEAMIDX = {};
  function crestImgFor(name, sz) {
    var t = TEAMIDX[norm(name)];
    return t ? crestImg(t.lg, t.id, sz) : "";
  }

  function card(lg, m, r, key) {
    var url = "/sports/" + lg + "/matches/" + m.id + "-vs-" + m.away + "/";
    var pill = r ? '<span class="sp-sc-pill ft">FT</span>' : '<span class="sp-sc-pill">' + esc(m.time || "TBC") + "</span>";
    var hn = r ? r.homeScore : "\u2013", an = r ? r.awayScore : "\u2013";
    return '<a class="sp-scorecard" href="' + url + '" data-mk="' + esc(key || "") + '"><div class="sp-sc-top">' + pill +
      '<span class="sp-sc-lg">' + LEAGUES[lg].label + '</span><span class="sp-sc-go">' + (r ? "Result \u2192" : "Preview \u2192") + "</span></div><div>" +
      '<div class="sp-sc-row"><div class="sp-sc-club"><img src="' + crest(lg, m.id) + '" data-fb="' + crestFallback(lg, m.id) + '" alt="" width="32" height="32" loading="lazy" decoding="async" onerror="if(this.dataset.fb){this.src=this.dataset.fb;this.dataset.fb=\'\';}else{this.style.display=\'none\';}"><span>' + esc(m.homeName) + '</span></div><b class="sp-sc-num">' + hn + "</b></div>" +
      '<div class="sp-sc-row"><div class="sp-sc-club"><img src="' + crest(lg, m.away) + '" data-fb="' + crestFallback(lg, m.away) + '" alt="" width="32" height="32" loading="lazy" decoding="async" onerror="if(this.dataset.fb){this.src=this.dataset.fb;this.dataset.fb=\'\';}else{this.style.display=\'none\';}"><span>' + esc(m.awayName) + '</span></div><b class="sp-sc-num">' + an + "</b></div></div></a>";
  }
  function group(lg, items, results) {
    var cards = items.map(function (m) { var k = lg + "/" + m.id + "-vs-" + m.away; return card(lg, m, results[k], k); }).join("");
    var head = '<div class="sp-lg sp-lg-' + lg + '" style="--lg-img:url(\'/assets/img/sports/hero-' + lg + '-md.jpg\')"><div class="sp-lg-head"><b>' + LEAGUES[lg].label + '</b><a href="/sports/' + lg + '/matches/">Open \u2192</a></div>';
    // ALWAYS rail — duplicate content for seamless auto-scroll loop
    return head + '<div class="sp-score-rail"><div class="sp-rail-track">' + cards + cards + "</div></div></div>";
  }
  function computeTable(lg, matches, results) {
    var T = {};
    matches.forEach(function (m) {
      T[m.id] = T[m.id] || { id: m.id, name: m.homeName, p: 0, w: 0, d: 0, l: 0, gf: 0, ga: 0, pts: 0, form: [] };
      T[m.away] = T[m.away] || { id: m.away, name: m.awayName, p: 0, w: 0, d: 0, l: 0, gf: 0, ga: 0, pts: 0, form: [] };
      var r = results[lg + "/" + m.id + "-vs-" + m.away];
      if (!r) return;
      var res = r.homeScore > r.awayScore ? "W" : r.homeScore < r.awayScore ? "L" : "D";
      var resA = res === "W" ? "L" : res === "L" ? "W" : "D";
      [[m.id, r.homeScore, r.awayScore, res], [m.away, r.awayScore, r.homeScore, resA]].forEach(function (x) {
        var t = T[x[0]]; t.p++; t.gf += x[1]; t.ga += x[2];
        if (x[3] === "W") { t.w++; t.pts += 3; } else if (x[3] === "D") { t.d++; } else { t.l++; }
        t.form.push(x[3] + "|" + r.playedOn);
      });
    });
    return Object.keys(T).map(function (id) { return T[id]; })
      .sort(function (a, b) { return b.pts - a.pts || (b.gf - b.ga) - (a.gf - a.ga) || b.gf - a.gf || (a.name < b.name ? -1 : 1); })
      .map(function (t, i) { t.pos = i + 1; t.form.sort(function (a, b) { return a.split("|")[1] < b.split("|")[1] ? -1 : 1; }); return t; });
  }
  var ZONES = {
    "premier-league": { cl: 4, el: 5, rel: 3 },
    "la-liga":        { cl: 4, el: 6, rel: 3 },
    "serie-a":        { cl: 4, el: 6, rel: 3 },
    "bundesliga":     { cl: 4, el: 5, rel: 2 },
    "ligue-1":        { cl: 3, el: 4, rel: 2 }
  };
  function renderTable(lg, matches, results) {
    var z = ZONES[lg] || { cl: 4, el: 6, rel: 3 };
    var relStart = 21 - (z.rel || 3) + (lg === "bundesliga" || lg === "ligue-1" ? 2 : 0);
    var n = lg === "bundesliga" || lg === "ligue-1" ? 18 : 20;
    var rows = computeTable(lg, matches, results).map(function (x) {
      var cls = x.pos <= z.cl ? " class=\"zcl\"" : x.pos <= z.el ? " class=\"zeu\"" : x.pos > n - (z.rel || 3) ? " class=\"zre\"" : "";
      var dots = x.form.slice(-5).map(function (f) {
        var r = f.split("|")[0];
        var col = r === "W" ? "#2e9e5b" : r === "D" ? "#5d6672" : "#d84343";
        return '<span class="sp-form-d" style="background:' + col + '">' + r + "</span>";
      }).join("");
      return "<tr" + cls + "><td>" + x.pos + '</td><td class="sp-td-team">' + crestImg(lg, x.id, 18) + "<b>" + esc(x.name) + "</b></td><td>" + dots + "</td><td>" + x.p + "</td><td>" + x.w +
        "</td><td>" + x.d + "</td><td>" + x.l + "</td><td>" + x.gf + ":" + x.ga + "</td><td>" +
        (x.gf - x.ga > 0 ? "+" : "") + (x.gf - x.ga) + "</td><td><b>" + x.pts + "</b></td></tr>";
    }).join("");
    return '<div class="sp-table-wrap"><table class="sp-table"><thead><tr><th>#</th><th>Team</th><th>Form</th><th>P</th><th>W</th><th>D</th><th>L</th><th>Goals</th><th>GD</th><th>Pts</th></tr></thead><tbody>' + rows + '</tbody></table></div><p class="sp-zone-legend"><i style="background:#2f6b3a"></i>Champions League&nbsp;&nbsp;<i style="background:#7a5b1e"></i>Europa&nbsp;&nbsp;<i style="background:#8e2020"></i>Relegation</p><p class="sp-result-meta">Live standings — recomputed from verified results on every visit.</p>';
  }
  function renderScorers(lg, matches, results) {
    
    var G = {};
    matches.forEach(function (m) {
      var r = results[lg + "/" + m.id + "-vs-" + m.away];
      if (!r || !r.scorers) return;
      r.scorers.forEach(function (s) {
        if (!s.player) return;
        var teamName = s.team === "home" ? m.homeName : m.awayName;
        G[s.player] = G[s.player] || { player: s.player, team: teamName, goals: 0 };
        G[s.player].goals++;
      });
    });
    var list = Object.keys(G).map(function (k) { return G[k]; })
      .sort(function (a, b) { return b.goals - a.goals || (a.player < b.player ? -1 : 1); }).slice(0, 20);
    if (!list.length) return '<p class="sp-result-meta">No goals recorded yet this season — updates automatically as matches are verified.</p>';
    var rows = list.map(function (x, i) {
      return "<tr><td>" + (i + 1) + "</td><td><b>" + esc(x.player) + "</b></td><td class=\"sp-td-team\">" + crestImgFor(x.team, 16) + esc(x.team) + "</td><td><b>" + x.goals + "</b></td></tr>";
    }).join("");
    return '<div class="sp-table-wrap"><table class="sp-table"><thead><tr><th>#</th><th>Player</th><th>Club</th><th>Goals</th></tr></thead><tbody>' + rows + '</tbody></table></div><p class="sp-result-meta">Live list — every verified scorer counted automatically.</p>';
  }
  function renderTeam(lg, teamId, matches, results) {
    var table = computeTable(lg, matches, results);
    var me = table.find(function (t) { return t.id === teamId; });
    if (!me) return "";
    var dots = me.form.slice(-5).map(function (f) {
      var r = f.split("|")[0];
      var col = r === "W" ? "#2e9e5b" : r === "D" ? "#8b93a1" : "#d84343";
      return '<span style="display:inline-block;width:22px;height:22px;line-height:22px;text-align:center;border-radius:50%;background:' + col + ';color:#fff;font-weight:800;font-size:12px;margin-right:5px">' + r + '</span>';
    }).join("");
    var next = null;
    matches.forEach(function (m) {
      if (results[lg + "/" + m.id + "-vs-" + m.away]) return;
      if (m.id === teamId || m.away === teamId) {
        if (!next || m.date < next.m.date) next = { m: m };
      }
    });
    var nextHtml = next
      ? 'Next: <b>' + esc(next.m.id === teamId ? next.m.awayName + " (H)" : next.m.homeName + " (A)") + "</b> · " + esc(next.m.date) + (next.m.time ? " · " + esc(next.m.time) : "")
      : "No upcoming fixture recorded yet.";
    return '<div class="sp-lg" style="margin:14px 0"><div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center">' +
      '<span style="background:#111419;border:1px solid #272b31;border-radius:20px;padding:6px 14px;font-weight:800">' + LEAGUES[lg].label + ' position: <b>' + me.pos + '</b> · ' + me.pts + ' pts</span>' +
      '<span style="background:#111419;border:1px solid #272b31;border-radius:20px;padding:6px 14px">Form: ' + (dots || "—") + "</span>" +
      '<span style="background:#111419;border:1px solid #272b31;border-radius:20px;padding:6px 14px">' + nextHtml + "</span></div></div>";
  }

  function abbr(name) {
    var w = String(name).replace(/[^A-Za-z ]/g, "").split(/\s+/).filter(Boolean);
    if (w.length >= 3) return (w[0][0] + w[1][0] + w[2][0]).toUpperCase();
    if (w.length === 2) return (w[0].slice(0, 2) + w[1][0]).toUpperCase();
    return String(name).slice(0, 3).toUpperCase();
  }
  function renderTicker(data, lgFilter) {
    /* Smart ticker — tight loop, high signal:
       1) today's matches, 2) the 6 freshest results,
       3) the next 3 fixtures with kickoff day. Never more than 10 chips. */
    var played = [], upcoming = [], today = [];
    var todayStr0 = todayStr();
    data.leagues.forEach(function (L) {
      if (lgFilter && L.lg !== lgFilter) return;
      L.ms.forEach(function (m) {
        var k = L.lg + "/" + m.id + "-vs-" + m.away;
        var r = data.results[k];
        if (m.date === todayStr0) today.push({ lg: L.lg, m: m, r: r });
        else if (r) played.push({ lg: L.lg, m: m, r: r });
        else if (m.date > todayStr0) upcoming.push({ lg: L.lg, m: m });
      });
    });
    played.sort(function (a, b) { return b.r.playedOn < a.r.playedOn ? -1 : b.r.playedOn > a.r.playedOn ? 1 : 0; });
    upcoming.sort(function (a, b) { return a.m.date < b.m.date ? -1 : a.m.date > b.m.date ? 1 : 0; });
    var DAYS = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
    function day(iso) { var p = iso.split("-"); return DAYS[new Date(+p[0], +p[1] - 1, +p[2]).getDay()]; }
    function item(x) {
      return '<span class="tk">' + crestImg(x.lg, x.m.id, 16) + '<b>' + abbr(x.m.homeName) + " " +
        x.r.homeScore + "\u2013" + x.r.awayScore + " " + abbr(x.m.awayName) + "</b><i>FT</i>" + crestImg(x.lg, x.m.away, 16) + "</span>";
    }
    function itemUp(x) {
      return '<span class="tk tk-up">' + crestImg(x.lg, x.m.id, 16) + "<b>" + abbr(x.m.homeName) +
        " v " + abbr(x.m.awayName) + "</b><i>" + day(x.m.date) + " " + esc(x.m.time || "") + "</i>" + crestImg(x.lg, x.m.away, 16) + "</span>";
    }
    var list = today.slice(0, 3).map(function (x) {
      return x.r ? item(x) : itemUp({ lg: x.lg, m: x.m });
    });
    list = list.concat(played.slice(0, 6).map(item), upcoming.slice(0, 3).map(itemUp));
    if (!list.length) list = upcoming.slice(0, 8).map(itemUp);
    var half = list.join("");
    return '<div class="tk-track">' + half + half + "</div>";
  }

  function renderMini(kind, lg, data) {
      if (kind === "scorers" && !lg) {
        var GA = {};
        data.leagues.forEach(function (L2) {
          L2.ms.forEach(function (m) {
            var r = data.results[L2.lg + "/" + m.id + "-vs-" + m.away];
            if (!r || !r.scorers) return;
            r.scorers.forEach(function (sc) {
              if (!sc.player) return;
              GA[sc.player] = GA[sc.player] || { t: sc.team === "home" ? m.homeName : m.awayName, g: 0 };
              GA[sc.player].g++;
            });
          });
        });
        var listA = Object.keys(GA).map(function (k) { GA[k].p = k; return GA[k]; })
          .sort(function (a, b) { return b.g - a.g; }).slice(0, 5);
        return '<table class="sp-table"><tbody>' + listA.map(function (x) {
          return '<tr><td><b>' + esc(x.p) + '</b></td><td class="sp-td-team">' + crestImgFor(x.t, 16) + esc(x.t) + '</td><td><b>' + x.g + '</b></td></tr>';
        }).join("") + '</tbody></table>';
      }
      var L = data.leagues.find(function (x) { return x.lg === lg; });
      if (!L) return "";
      if (kind === "table") {
        var rows = computeTable(lg, L.ms, data.results).slice(0, 5).map(function (x) {
          var cls = x.pos <= (ZONES[lg] || {cl:4}).cl ? "zcl" : x.pos <= (ZONES[lg] || {el:6}).el ? "zeu" : "";
          return '<tr class="' + cls + '"><td>' + x.pos + '</td><td class="sp-td-team">' + crestImg(lg, x.id, 16) + '<b>' + esc(x.name) + '</b></td><td><b>' + x.pts + '</b></td></tr>';
        }).join("");
        return '<table class="sp-table"><tbody>' + rows + '</tbody></table>';
      }
      if (kind === "scorers") {
        var G = {};
        L.ms.forEach(function (m) {
          var r = data.results[lg + "/" + m.id + "-vs-" + m.away];
          if (!r || !r.scorers) return;
          r.scorers.forEach(function (sc) {
            if (!sc.player) return;
            G[sc.player] = G[sc.player] || { t: sc.team === "home" ? m.homeName : m.awayName, g: 0 };
            G[sc.player].g++;
          });
        });
        var list = Object.keys(G).map(function (k) { G[k].p = k; return G[k]; })
          .sort(function (a, b) { return b.g - a.g; }).slice(0, 5);
        if (!list.length) return '<p class="sp-result-meta">No goals yet — fills automatically.</p>';
        return '<table class="sp-table"><tbody>' + list.map(function (x) {
          return '<tr><td><b>' + esc(x.p) + '</b></td><td class="sp-td-team">' + crestImgFor(x.t, 16) + esc(x.t) + '</td><td><b>' + x.g + '</b></td></tr>';
        }).join("") + '</tbody></table>';
      }
      if (kind === "reports") {
        var played = [];
        L.ms.forEach(function (m) {
          var r = data.results[lg + "/" + m.id + "-vs-" + m.away];
          if (r) played.push({ m: m, r: r });
        });
        played.sort(function (a, b) { return b.r.playedOn < a.r.playedOn ? -1 : 1; });
        return played.slice(0, 4).map(function (x) {
          return '<a class="sp-rep" href="/sports/' + lg + '/reports/' + x.m.id + '-vs-' + x.m.away + '/">' +
            esc(x.m.homeName) + ' ' + x.r.homeScore + '\u2013' + x.r.awayScore + ' ' + esc(x.m.awayName) +
            '<i>' + esc(x.r.playedOn) + '</i></a>';
        }).join("") || '<p class="sp-result-meta">No reports yet.</p>';
      }
      return "";
    }

  function renderMiniReportsAll(data) {
    var played = [];
    data.leagues.forEach(function (L) {
      L.ms.forEach(function (m) {
        var r = data.results[L.lg + "/" + m.id + "-vs-" + m.away];
        if (r) played.push({ lg: L.lg, m: m, r: r });
      });
    });
    played.sort(function (a, b) { return b.r.playedOn < a.r.playedOn ? -1 : 1; });
    return played.slice(0, 5).map(function (x) {
      return '<a class="sp-rep" href="/sports/' + x.lg + '/reports/' + x.m.id + '-vs-' + x.m.away + '/">' +
        crestImg(x.lg, x.m.id, 22) +
        '<span class="sp-rep-mid"><b>' + esc(x.m.homeName) + ' ' + x.r.homeScore + '\u2013' + x.r.awayScore + ' ' + esc(x.m.awayName) + '</b>' +
        '<em>' + LEAGUES[x.lg].label + ' \u00b7 ' + esc(x.r.playedOn) + '</em></span>' +
        crestImg(x.lg, x.m.away, 22) + '</a>';
    }).join("") || '<p class="sp-result-meta">No reports yet.</p>';
  }

  var DATA = null;
  var OFFICIAL = null;

  function load() {
    if (DATA) return DATA;
    DATA = fetch("/content/sports-feed.json").then(function (r) { return r.json(); }).then(function (fd) {
      var res = {};
      var leagues = [];
      Object.keys(fd.leagues || {}).forEach(function (lg) {
        var ms = (fd.leagues[lg] || []).map(function (a) {
          return { id: a[0], away: a[1], homeName: a[2], awayName: a[3], date: a[4], time: a[5] };
        });
        leagues.push({ lg: lg, ms: ms });
        ms.forEach(function (m) {
          TEAMIDX[norm(m.homeName)] = { lg: lg, id: m.id };
          TEAMIDX[norm(m.awayName)] = { lg: lg, id: m.away };
        });
        var r2 = (fd.results && fd.results[lg]) || {};
        Object.keys(r2).forEach(function (k) { res[lg + "/" + k] = r2[k]; });
      });
      return { results: res, leagues: leagues };
    }).catch(function () { return null; });
    return DATA;
  }

  function fetchJson(url, ms) {
    var opts = { cache: "no-cache", headers: { accept: "application/json" } };
    try { if (ms && window.AbortSignal && AbortSignal.timeout) opts.signal = AbortSignal.timeout(ms); } catch (e) {}
    return fetch(url, opts).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
  }

  function loadOfficial() {
    if (OFFICIAL) return Promise.resolve(OFFICIAL);
    return fetchJson("/content/competitions.json", 8000).then(function (file) {
      if (file && file.competitions && file.competitions.length) OFFICIAL = file;
      return OFFICIAL;
    });
  }

  function findComp(official, id) {
    if (!official || !official.competitions) return null;
    for (var i = 0; i < official.competitions.length; i++) {
      if (official.competitions[i].id === id) return official.competitions[i];
    }
    return null;
  }

  function applyOfficial(data, official) {
    if (!data || !official) return;
    (official.competitions || []).forEach(function (c) {
      (c.scores || []).forEach(function (s) {
        data.leagues.forEach(function (L) {
          if (c.id !== "champions-league" && L.lg !== c.id) return;
          L.ms.forEach(function (m) {
            if (norm(m.homeName) !== norm(s.home) || norm(m.awayName) !== norm(s.away)) return;
            var k = L.lg + "/" + m.id + "-vs-" + m.away;
            data.results[k] = {
              homeScore: s.hs, awayScore: s.as, playedOn: s.date,
              source: { name: "ESPN", url: "https://www.espn.com/soccer/" }
            };
          });
        });
      });
    });
  }

  function logoImg(url, sz) {
    if (!url) return "";
    return '<img src="' + esc(url) + '" alt="" width="' + (sz || 18) + '" height="' + (sz || 18) + '" loading="lazy" decoding="async" onerror="this.style.display=\'none\'">';
  }

  function renderOfficialTable(lg, comp) {
    var z = ZONES[lg] || { cl: 4, el: 6, rel: 3 };
    var n = (comp.teams || []).length || 20;
    var rows = (comp.teams || []).map(function (x) {
      var cls = x.pos <= z.cl ? " class=\"zcl\"" : x.pos <= z.el ? " class=\"zeu\"" : x.pos > n - (z.rel || 3) ? " class=\"zre\"" : "";
      var tid = TEAMIDX[norm(x.name)];
      var badge = tid ? crestImg(tid.lg, tid.id, 18) : logoImg(x.logo, 18);
      return "<tr" + cls + "><td>" + x.pos + '</td><td class="sp-td-team">' + badge + "<b>" + esc(x.name) + "</b></td><td></td><td>" + x.p + "</td><td>" + x.w +
        "</td><td>" + x.d + "</td><td>" + x.l + "</td><td>" + x.gf + ":" + x.ga + "</td><td>" +
        esc(x.gd) + "</td><td><b>" + x.pts + "</b></td></tr>";
    }).join("");
    var when = officialStamp(OFFICIAL);
    return '<div class="sp-table-wrap"><table class="sp-table"><thead><tr><th>#</th><th>Team</th><th>Form</th><th>P</th><th>W</th><th>D</th><th>L</th><th>Goals</th><th>GD</th><th>Pts</th></tr></thead><tbody>' + rows + '</tbody></table></div><p class="sp-zone-legend"><i style="background:#2f6b3a"></i>Champions League&nbsp;&nbsp;<i style="background:#7a5b1e"></i>Europa&nbsp;&nbsp;<i style="background:#8e2020"></i>Relegation</p><p class="sp-result-meta">Live table' + (when ? " · updated " + when : "") + ".</p>";
  }

  function renderOfficialScorers(list, limit) {
    var rows = (list || []).slice(0, limit || 5).map(function (x, i) {
      return "<tr><td>" + (i + 1) + "</td><td><b>" + esc(x.name) + "</b></td><td class=\"sp-td-team\">" + logoImg(x.logo, 16) + esc(x.team || "") + "</td><td><b>" + x.goals + "</b></td></tr>";
    }).join("");
    if (!rows) return "";
    return '<table class="sp-table"><tbody>' + rows + "</tbody></table>";
  }

  function renderOfficialTicker(official, lgFilter) {
    var chips = [];
    (official.competitions || []).forEach(function (c) {
      if (lgFilter && c.id !== lgFilter) return;
      (c.scores || []).forEach(function (s) {
        chips.push('<span class="tk">' + logoImg(s.hlogo, 16) + "<b>" + esc(s.hshort) + " " + s.hs + "\u2013" + s.as + " " + esc(s.ashort) + "</b><i>FT</i>" + logoImg(s.alogo, 16) + "</span>");
      });
    });
    if (!chips.length) return "";
    var half = chips.join("");
    return '<div class="tk-track">' + half + half + "</div>";
  }

  function renderHomeScores(official) {
    var cards = [];
    (official.competitions || []).forEach(function (c) {
      (c.scores || []).slice(0, 6).forEach(function (s) {
        var href = "/sports/#" + c.id;
        cards.push('<a class="mp-card hl-score" href="' + href + '"><span class="mp-when">FT · ' + esc(c.name) + " · " + esc(s.date) + "</span><b>" + esc(s.home) + " " + s.hs + "\u2013" + s.as + " " + esc(s.away) + "</b><span>Full time</span></a>");
      });
    });
    if (!cards.length) return "";
    return '<div class="mp-sub"><div class="mp-sub-head"><span class="mp-sub-dot"></span>Live scores</div><div class="mp-rail">' + cards.join("") + "</div></div>";
  }

  function officialStamp(d) {
    if (!d || !d.builtAt) return "";
    var t = new Date(d.builtAt);
    if (isNaN(t.getTime())) return "";
    return t.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
  }

  function boot() {
    var nodes = document.querySelectorAll("[data-sp-engine]");
    if (!nodes.length) return;
    Promise.all([load(), loadOfficial()]).then(function (pair) {
      var data = pair[0];
      var official = pair[1];
      if (!data) data = { results: {}, leagues: [] };
      if (official) applyOfficial(data, official);
      var today = todayStr();
      var liveLeagues = {};
      nodes.forEach(function (el) {
        if (el.hasAttribute("data-sp-official-scores")) {
          if (official) {
            el.innerHTML = renderHomeScores(official);
            el.setAttribute("data-sp-live", "1");
          }
          return;
        }
        var mini = el.getAttribute("data-sp-mini");
        if (mini) {
          var mlg = el.getAttribute("data-sp-league");
          if (mini === "scorers") {
            var olist = [];
            if (official) {
              (official.competitions || []).forEach(function (c) {
                if (mlg && c.id !== mlg) return;
                (c.scorers || []).forEach(function (s) { olist.push(s); });
              });
              olist.sort(function (a, b) { return (b.goals || 0) - (a.goals || 0); });
            }
            var scored = olist.length ? renderOfficialScorers(olist, 5) : renderMini(mini, mlg, data);
            if (scored) { el.innerHTML = scored; el.setAttribute("data-sp-live", "1"); }
            return;
          }
          if (mini === "table" && mlg && official) {
            var ocMini = findComp(official, mlg);
            if (ocMini && ocMini.teams && ocMini.teams.length) {
              var z = ZONES[mlg] || { cl: 4, el: 6 };
              var rowsM = ocMini.teams.slice(0, 5).map(function (x) {
                var cls = x.pos <= z.cl ? "zcl" : x.pos <= z.el ? "zeu" : "";
                var tid = TEAMIDX[norm(x.name)];
                var badge = tid ? crestImg(tid.lg, tid.id, 16) : logoImg(x.logo, 16);
                return '<tr class="' + cls + '"><td>' + x.pos + '</td><td class="sp-td-team">' + badge + "<b>" + esc(x.name) + "</b></td><td><b>" + x.pts + "</b></td></tr>";
              }).join("");
              el.innerHTML = '<table class="sp-table"><tbody>' + rowsM + "</tbody></table>";
              el.setAttribute("data-sp-live", "1");
              return;
            }
          }
          if (mini === "reports" && !mlg) {
            el.innerHTML = renderMiniReportsAll(data);
            el.setAttribute("data-sp-live", "1");
          } else if (mini === "scorers" || (mlg && LEAGUES[mlg])) {
            el.innerHTML = renderMini(mini, mlg, data);
            el.setAttribute("data-sp-live", "1");
          }
          return;
        }
        if (el.hasAttribute("data-sp-ticker")) {
          var tick = official ? renderOfficialTicker(official, el.getAttribute("data-sp-league")) : "";
          el.innerHTML = tick || renderTicker(data, el.getAttribute("data-sp-league"));
          el.setAttribute("data-sp-live", "1");
          return;
        }
        var lgFilter = el.getAttribute("data-sp-league");
        var lgTable = el.getAttribute("data-sp-table");
        var lgScorers = el.getAttribute("data-sp-scorers");
        var teamAttr = el.getAttribute("data-sp-team");
        if (lgTable && LEAGUES[lgTable]) {
          var oc = official ? findComp(official, lgTable) : null;
          if (oc && oc.teams && oc.teams.length) {
            el.innerHTML = renderOfficialTable(lgTable, oc);
            el.setAttribute("data-sp-live", "1");
            return;
          }
          var LT = data.leagues.find(function (x) { return x.lg === lgTable; });
          if (LT) { el.innerHTML = renderTable(lgTable, LT.ms, data.results); el.setAttribute("data-sp-live", "1"); }
          return;
        }
        if (lgScorers && LEAGUES[lgScorers]) {
          var ocS = official ? findComp(official, lgScorers) : null;
          if (ocS && ocS.scorers && ocS.scorers.length) {
            el.innerHTML = '<div class="sp-table-wrap">' + renderOfficialScorers(ocS.scorers, 20) + '</div><p class="sp-result-meta">Live list.</p>';
            el.setAttribute("data-sp-live", "1");
            return;
          }
          var LS = data.leagues.find(function (x) { return x.lg === lgScorers; });
          if (LS) { el.innerHTML = renderScorers(lgScorers, LS.ms, data.results); el.setAttribute("data-sp-live", "1"); }
          return;
        }
        if (teamAttr) {
          var parts = teamAttr.split("/");
          var LTm = data.leagues.find(function (x) { return x.lg === parts[0]; });
          if (LTm) {
            var html = renderTeam(parts[0], parts[1], LTm.ms, data.results);
            if (html) { el.innerHTML = html; el.setAttribute("data-sp-live", "1"); }
          }
          return;
        }
        var played = [], upcoming = [], todays = [];
        data.leagues.forEach(function (L) {
          if (lgFilter && L.lg !== lgFilter) return;
          L.ms.forEach(function (m) {
            var r = data.results[L.lg + "/" + m.id + "-vs-" + m.away];
            if (m.date === today) { todays.push({ lg: L.lg, m: m }); liveLeagues[L.lg] = true; }
            else if (r) played.push({ lg: L.lg, m: m });
            else if (m.date > today) upcoming.push({ lg: L.lg, m: m });
          });
        });
        function byD(a, b) { return a.m.date < b.m.date ? -1 : a.m.date > b.m.date ? 1 : 0; }
        played.sort(function (a, b) { return -byD(a, b); }); upcoming.sort(byD);
        played = played.slice(0, lgFilter ? 5 : 4); upcoming = upcoming.slice(0, lgFilter ? 5 : 4);
        function section(title, arr, withDate) {
          if (!arr.length) return "";
          var html = '<div class="sp-board-head"><div><div class="eyebrow">Scores</div><h2>' + title + "</h2></div>";
          if (withDate && arr[0].m.date) html += '<span class="sp-board-date">' + esc(niceDate(arr[0].m.date)) + "</span>";
          html += "</div>";
          /* FLAT board: one rail per section — every card carries its own league tag */
          var cards = arr.map(function (b) {
            var k = b.lg + "/" + b.m.id + "-vs-" + b.m.away;
            return card(b.lg, b.m, data.results[k], k);
          }).join("");
          html += '<div class="sp-score-rail"><div class="sp-rail-track">' + cards + cards + "</div></div>";
          return html;
        }
        var out = section("Today", todays, false);
        out += section("Latest results", played, true);
        out += section("Next up", upcoming, true);
        if (out) { el.innerHTML = out; el.setAttribute("data-sp-live", "1"); }
      });
      document.querySelectorAll("[data-sp-date]").forEach(function (s) { s.textContent = niceDate(today); });
      initRails();
      var liveKeys = Object.keys(liveLeagues);
      if (liveKeys.length) pollLive(liveKeys);
    }).catch(function () {});
  }

  /* LIVE: poll ESPN directly for in-play scores on today's cards */
  function pollLive(leagues) {
    function tick() {
      if (document.hidden) return;
      leagues.forEach(function (lg) {
        fetch("https://site.api.espn.com/apis/site/v2/sports/soccer/" + LEAGUES[lg].code + "/scoreboard", { cache: "no-cache" })
          .then(function (r) { return r.json(); })
          .then(function (j) {
            (j.events || []).forEach(function (ev) {
              var comp = ev.competitions && ev.competitions[0];
              if (!comp) return;
              var home = comp.competitors.find(function (c) { return c.homeAway === "home"; });
              var away = comp.competitors.find(function (c) { return c.homeAway === "away"; });
              if (!home || !away) return;
              var key = lg + "/" + norm(home.team.displayName) + "-vs-" + norm(away.team.displayName);
              /* our ids are already normalized short forms, so this usually matches directly */
              var el = document.querySelector('[data-mk="' + key + '"]');
              var elAlt = null;
              if (!el) {
                document.querySelectorAll("[data-mk]").forEach(function (c) {
                  var k = c.getAttribute("data-mk");
                  if (k.indexOf(lg + "/") === 0 && k.split("-vs-")[0] === lg + "/" + norm(home.team.displayName) && k.split("-vs-")[1] === norm(away.team.displayName)) elAlt = c;
                });
                el = elAlt;
              }
              if (!el) return;
              var pill = el.querySelector(".sp-sc-pill");
              var nums = el.querySelectorAll(".sp-sc-num");
              if (ev.status.type.state === "in") {
                var min = (ev.status.displayClock || "LIVE").toString();
                if (pill) { pill.textContent = "LIVE " + min; pill.classList.add("sp-live"); }
                if (nums.length === 2) { nums[0].textContent = home.score; nums[1].textContent = away.score; }
              } else if (ev.status.type.state === "post") {
                if (pill && pill.textContent.indexOf("FT") === -1) {
                  pill.textContent = "FT"; pill.classList.remove("sp-live");
                  if (nums.length === 2) { nums[0].textContent = home.score; nums[1].textContent = away.score; }
                }
              }
            });
          }).catch(function () {});
      });
    }
    tick();
    setInterval(tick, 60000);
  }

  function initRails() {
    document.querySelectorAll(".sp-score-rail, .sp-art-rail").forEach(function (rail) {
      if (rail.getAttribute("data-rail-go")) return;
      rail.setAttribute("data-rail-go", "1");
      var track = rail.querySelector(".sp-rail-track, .sp-art-track");
      if (!track) return;
      var pos = 0;
      var paused = false;
      var resumeTimer = null;
      var animId = null;
      function pause() {
        paused = true;
        if (resumeTimer) clearTimeout(resumeTimer);
        resumeTimer = setTimeout(function () { paused = false; }, 3000);
      }
      // AUTO-SCROLL: CSS transform (bulletproof — works everywhere)
      function tick() {
        if (!paused && !document.hidden) {
          var w = track.scrollWidth || track.offsetWidth;
          var half = w / 2;
          if (half > 100) {
            pos += 0.5;
            if (pos >= half) pos = 0;
            track.style.transform = "translateX(" + (-pos) + "px)";
          }
        }
        animId = requestAnimationFrame(tick);
      }
      animId = requestAnimationFrame(tick);
      rail.style.overflow = "hidden";
      rail.style.cursor = "grab";
      rail.style.touchAction = "pan-y";
      rail.style.userSelect = "none";
      rail.style.webkitUserSelect = "none";
      // MANUAL DRAG
      var dragging = false, startX = 0, startPos = 0, moved = false;
      rail.addEventListener("pointerdown", function (e) {
        dragging = true; moved = false;
        startX = e.clientX; startPos = pos;
        rail.style.cursor = "grabbing";
        pause();
      });
      document.addEventListener("pointermove", function (e) {
        if (!dragging) return;
        var dx = e.clientX - startX;
        if (Math.abs(dx) > 3) moved = true;
        pos = startPos - dx;
        if (pos < 0) pos = 0;
        track.style.transform = "translateX(" + (-pos) + "px)";
      });
      document.addEventListener("pointerup", function () {
        if (!dragging) return;
        dragging = false;
        rail.style.cursor = "grab";
        pause();
      });
      rail.addEventListener("touchstart", function () { pause(); }, { passive: true });
      rail.addEventListener("wheel", function () { pause(); }, { passive: true });
      rail.addEventListener("click", function (e) {
        if (moved) { e.preventDefault(); e.stopPropagation(); moved = false; }
      }, true);
    });
  }
  var bootDone = false;
  function bootSafe() { if (bootDone) return; bootDone = true; boot(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", bootSafe);
  else if (window.requestIdleCallback) window.requestIdleCallback(bootSafe, { timeout: 1200 });
  else setTimeout(bootSafe, 60);
})();

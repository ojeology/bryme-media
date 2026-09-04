/* Club page — played scores + next fixtures. No comics. */
(function () {
  "use strict";
  var view = document.getElementById("tm-app");
  if (!view) return;
  var league = view.getAttribute("data-league");
  var teamId = view.getAttribute("data-id");
  var teamName = view.getAttribute("data-name") || "";

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function norm(s) {
    return String(s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .replace(/&/g, "and").replace(/[^a-z0-9]+/g, "");
  }
  function sameTeam(a, b) { return norm(a) === norm(b); }

  function scoreCard(s) {
    return '<div class="sp-score"><div class="tm">' + esc(s.home) + '</div><div class="num">' +
      s.hs + "–" + s.as + '</div><div class="tm away">' + esc(s.away) + '</div>' +
      '<div class="when">FT · ' + esc(s.date) + "</div></div>";
  }
  function fixtCard(f) {
    return '<div class="sp-fixt"><div class="when">' + esc(f.date) + (f.time ? " · " + esc(f.time) : "") +
      '</div><div class="teams">' + esc(f.home) + " <i>vs</i> " + esc(f.away) + "</div></div>";
  }

  function keyOf(hid, aid) { return hid + "-vs-" + aid; }

  Promise.all([
    fetch("/content/sports-feed.json", { cache: "no-cache" }).then(function (r) { return r.ok ? r.json() : null; }),
    fetch("/content/competitions.json", { cache: "no-cache" }).then(function (r) { return r.ok ? r.json() : null; })
  ]).then(function (pair) {
    var feed = pair[0] || { leagues: {}, results: {} };
    var official = pair[1];
    var rows = (feed.leagues && feed.leagues[league]) || [];
    var res = (feed.results && feed.results[league]) || {};
    var played = [];
    var next = [];
    var seen = {};

    rows.forEach(function (r) {
      var hid = r[0], aid = r[1], hn = r[2], an = r[3], date = r[4], time = r[5];
      if (hid !== teamId && aid !== teamId) return;
      var sc = res[keyOf(hid, aid)];
      if (sc && (sc.status === "FT" || sc.homeScore != null)) {
        var item = { date: sc.playedOn || date, home: hn, away: an, hs: sc.homeScore, as: sc.awayScore };
        played.push(item);
        seen[norm(hn) + norm(an) + item.date] = 1;
      } else {
        next.push({ date: date, time: time || "", home: hn, away: an });
      }
    });

    if (official && official.competitions) {
      var comp = null;
      official.competitions.forEach(function (c) { if (c.id === league) comp = c; });
      if (comp) {
        (comp.scores || []).forEach(function (s) {
          if (!sameTeam(s.home, teamName) && !sameTeam(s.away, teamName)) return;
          var k = norm(s.home) + norm(s.away) + s.date;
          if (seen[k]) return;
          played.push({ date: s.date, home: s.home, away: s.away, hs: s.hs, as: s.as });
          seen[k] = 1;
        });
        (comp.fixtures || []).forEach(function (f) {
          if (!sameTeam(f.home, teamName) && !sameTeam(f.away, teamName)) return;
          var already = next.some(function (x) { return x.date === f.date && sameTeam(x.home, f.home); });
          if (!already) next.push({ date: f.date, time: f.time || "", home: f.home, away: f.away });
        });
      }
    }

    played.sort(function (a, b) { return a.date < b.date ? 1 : a.date > b.date ? -1 : 0; });
    next.sort(function (a, b) { return a.date < b.date ? -1 : a.date > b.date ? 1 : 0; });
    next = next.slice(0, 6);

    var html = "";
    html += '<p class="sp-kick">Played</p>';
    html += played.length ? played.map(scoreCard).join("") : '<p class="sp-empty">No played scores yet.</p>';
    html += '<p class="sp-kick">Next</p>';
    html += next.length ? next.map(fixtCard).join("") : '<p class="sp-empty">No upcoming fixtures listed.</p>';
    html += '<div class="sp-more"><a href="/sports/#' + esc(league) + '">Table &amp; scores</a></div>';
    document.getElementById("tm-body").innerHTML = html;
  }).catch(function () {
    var el = document.getElementById("tm-body");
    if (el) el.innerHTML = '<p class="sp-empty">Scores could not load. Open the league table instead.</p>';
  });
})();

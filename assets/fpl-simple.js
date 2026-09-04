/* Official FPL points — table, next fixtures, season. */
(function () {
  "use strict";
  var view = document.getElementById("fpl-app");
  if (!view) return;
  var DATA = null;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function uk(iso) {
    if (!iso) return "";
    var d = new Date(iso);
    if (isNaN(d.getTime())) return "";
    return d.toLocaleString("en-GB", {
      timeZone: "Europe/London",
      weekday: "short",
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit"
    });
  }
  function ev(id) {
    var list = (DATA && DATA.events) || [];
    for (var i = 0; i < list.length; i++) if (list[i].id === id) return list[i];
    return null;
  }
  function gw(id) {
    return (DATA && DATA.gameweeks && DATA.gameweeks[id]) || { fixtures: [], players: [] };
  }

  function pointsHtml(id) {
    var e = ev(id);
    var g = gw(id);
    if (!e) return '<p class="sp-empty">No gameweek data.</p>';
    var head = "<h2>" + esc(e.name) + (e.finished ? " — done" : "") + "</h2>";
    if (e.finished && (e.average || e.highest)) {
      head += '<p class="sp-easy-sub">Average ' + e.average + " pts · Highest " + e.highest + " pts. Official FPL points.</p>";
    } else if (!e.finished) {
      head += '<p class="sp-easy-sub">Deadline ' + uk(e.deadline) + " UK. Points appear after full time.</p>";
    }
    var rows = (g.players || []).map(function (p, i) {
      var why = [];
      if (p.g) why.push(p.g + "g");
      if (p.a) why.push(p.a + "a");
      if (p.bonus) why.push(p.bonus + " bonus");
      return '<div class="sp-tbl-r fpl-r"><i>' + (i + 1) + "</i><span>" + esc(p.name) +
        ' <em class="fpl-why">' + esc(p.team) + (why.length ? " · " + why.join(" ") : "") +
        "</em></span><b>" + esc(p.pos) + "</b><em>" + p.pts + "</em><b>" + p.total + "</b></div>";
    }).join("");
    if (!rows) {
      return head + '<p class="sp-empty">No points yet for this gameweek.</p>';
    }
    return head +
      '<div class="sp-tbl"><div class="sp-tbl-r fpl-r"><i>#</i><span>Player</span><b>Pos</b><em>GW</em><b>Tot</b></div>' +
      rows + "</div>";
  }

  function fixturesHtml(id) {
    var e = ev(id);
    var g = gw(id);
    if (!e) return '<p class="sp-empty">No fixtures.</p>';
    var head = "<h2>" + esc(e.name) + "</h2>" +
      '<p class="sp-easy-sub">Deadline ' + uk(e.deadline) + " UK.</p>";
    var list = (g.fixtures || []).map(function (f) {
      var score = f.finished && f.hs != null
        ? "<b>" + f.hs + "–" + f.as + "</b>"
        : "<i>vs</i>";
      return '<div class="sp-fixt"><div class="when">' + esc(uk(f.kickoff)) +
        '</div><div class="teams">' + esc(f.hshort || f.home) + " " + score + " " +
        esc(f.ashort || f.away) + "</div></div>";
    }).join("");
    return head + (list || '<p class="sp-empty">Fixtures appear when FPL publishes them.</p>');
  }

  function seasonHtml() {
    var list = (DATA && DATA.season) || [];
    var rows = list.map(function (p, i) {
      return '<div class="sp-tbl-r fpl-r"><i>' + (i + 1) + "</i><span>" + esc(p.name) +
        ' <em class="fpl-why">' + esc(p.team) + "</em></span><b>" + esc(p.pos) +
        "</b><em>" + p.gw + "</em><b>" + p.total + "</b></div>";
    }).join("");
    return "<h2>Season</h2>" +
      '<p class="sp-easy-sub">Total FPL points so far.</p>' +
      '<div class="sp-tbl"><div class="sp-tbl-r fpl-r"><i>#</i><span>Player</span><b>Pos</b><em>GW</em><b>Tot</b></div>' +
      rows + "</div>";
  }

  function pane(tab) {
    var forced = parseInt(view.getAttribute("data-gw") || "0", 10);
    if (tab === "season") return seasonHtml();
    if (tab === "next") return fixturesHtml(DATA.next || forced || 3);
    var id = forced || DATA.current || 2;
    return pointsHtml(id);
  }

  function render(tab) {
    var forced = parseInt(view.getAttribute("data-gw") || "0", 10);
    var cur = DATA.current || 2;
    var nxt = DATA.next || 3;
    if (!tab) {
      tab = view.getAttribute("data-tab") || "points";
    }
    if (forced && tab === "points") {
      var fe = ev(forced);
      if (fe && !fe.finished) tab = "next";
    }
    var tabs = [
      ["points", "GW" + (forced || cur) + " points"],
      ["next", "GW" + nxt + " next"],
      ["season", "Season"]
    ];
    var box = document.getElementById("fpl-body");
    var curE = ev(forced || cur);
    var nextE = ev(nxt);
    var sub = "Official player points from Fantasy Premier League.";
    if (nextE && !nextE.finished) sub = "Gameweek " + nxt + " deadline: " + uk(nextE.deadline) + " UK.";
    else if (curE && curE.finished) sub = esc(curE.name) + " is done. Official points below.";
    box.innerHTML =
      '<div class="sp-seg">' + tabs.map(function (t) {
        return '<button type="button" data-tab="' + t[0] + '"' + (t[0] === tab ? ' class="on"' : "") + ">" + t[1] + "</button>";
      }).join("") + "</div>" +
      '<p class="sp-easy-sub" id="fpl-sub">' + sub + "</p>" +
      '<div id="fpl-pane">' + pane(tab) + "</div>";
    box.querySelector(".sp-seg").onclick = function (e) {
      var b = e.target.closest("button[data-tab]");
      if (!b) return;
      render(b.getAttribute("data-tab"));
    };
  }

  fetch("/content/fpl.json", { cache: "no-cache" })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      DATA = d;
      if (!DATA) {
        document.getElementById("fpl-body").innerHTML = '<p class="sp-empty">Could not load FPL points.</p>';
        return;
      }
      render();
    })
    .catch(function () {
      var el = document.getElementById("fpl-body");
      if (el) el.innerHTML = '<p class="sp-empty">Could not load FPL points.</p>';
    });
})();

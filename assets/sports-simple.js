/* Simple sports — table, scores, fixtures, scorers. */
(function () {
  "use strict";
  var DATA = null;
  var view = document.getElementById("sp-app");
  if (!view) return;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function img(url) {
    if (!url) return "";
    return '<img src="' + esc(url) + '" alt="" width="20" height="20" loading="lazy">';
  }
  function find(id) {
    var list = (DATA && DATA.competitions) || [];
    for (var i = 0; i < list.length; i++) if (list[i].id === id) return list[i];
    return null;
  }
  function lineFor(c) {
    if (c.fixtures && c.fixtures[0]) {
      var f = c.fixtures[0];
      return "Next: " + f.hshort + " vs " + f.ashort + " · " + f.date;
    }
    if (c.scores && c.scores[0]) {
      var s = c.scores[0];
      return s.hshort + " " + s.hs + "–" + s.as + " " + s.ashort;
    }
    return "Season starting";
  }
  function isSubpage() {
    return !!view.getAttribute("data-lg");
  }

  function renderHome() {
    if (isSubpage()) {
      location.href = "/sports/";
      return;
    }
    var leagues = document.getElementById("sp-leagues");
    var box = document.getElementById("sp-comp");
    var head = document.getElementById("sp-home-head");
    if (leagues) leagues.hidden = false;
    if (box) box.hidden = true;
    if (head) head.hidden = false;
    if (history.replaceState) history.replaceState(null, "", location.pathname);
  }

  function tableHtml(c) {
    if (!c.teams || !c.teams.length) return '<p class="sp-empty">Table fills when matches are played.</p>';
    var rows = c.teams.map(function (t) {
      return '<div class="sp-tbl-r' + (t.pos <= 4 ? " ucl" : "") + '"><i>' + t.pos + "</i><span>" +
        img(t.logo) + esc(t.short || t.name) + "</span><b>" + t.p + "</b><b>" + t.w + "-" + t.d + "-" + t.l +
        "</b><b>" + esc(t.gd) + "</b><em>" + t.pts + "</em></div>";
    }).join("");
    return '<div class="sp-tbl"><div class="sp-tbl-r"><i>#</i><span>Club</span><b>P</b><b>W-D-L</b><b>GD</b><em>Pts</em></div>' + rows + "</div>";
  }
  function scoresHtml(c) {
    if (!c.scores || !c.scores.length) return '<p class="sp-empty">No recent results yet.</p>';
    return c.scores.map(function (s) {
      return '<div class="sp-score"><div class="tm">' + img(s.hlogo) + esc(s.hshort) + '</div><div class="num">' +
        s.hs + "–" + s.as + '</div><div class="tm away">' + esc(s.ashort) + img(s.alogo) + '</div><div class="when">FT · ' +
        esc(s.date) + "</div></div>";
    }).join("");
  }
  function fixturesHtml(c) {
    if (!c.fixtures || !c.fixtures.length) return '<p class="sp-empty">No upcoming fixtures in the next week.</p>';
    return c.fixtures.map(function (f) {
      return '<div class="sp-fixt"><div class="when">' + esc(f.date) + (f.time ? " · " + esc(f.time) : "") +
        '</div><div class="teams">' + img(f.hlogo) + esc(f.hshort) + " <i>vs</i> " + esc(f.ashort) + img(f.alogo) + "</div></div>";
    }).join("");
  }
  function scorersHtml(c) {
    if (!c.scorers || !c.scorers.length) return '<p class="sp-empty">Top scorers appear after goals are recorded.</p>';
    return c.scorers.map(function (s, i) {
      return '<div class="sp-fixt"><div class="when">#' + (i + 1) + " · " + s.goals + " goal" + (s.goals === 1 ? "" : "s") +
        '</div><div class="teams">' + img(s.logo) + esc(s.name) + " <i>" + esc(s.team || "") + "</i></div></div>";
    }).join("");
  }

  function pane(c, tab) {
    if (tab === "scores") return scoresHtml(c);
    if (tab === "fixtures") return fixturesHtml(c);
    if (tab === "scorers") return scorersHtml(c);
    return tableHtml(c);
  }

  function openComp(id, tab) {
    var c = find(id);
    if (!c) return;
    tab = tab || (c.scores && c.scores.length ? "scores" : "table");
    var leagues = document.getElementById("sp-leagues");
    if (leagues) leagues.hidden = true;
    var head = document.getElementById("sp-home-head");
    if (head) head.hidden = true;
    var box = document.getElementById("sp-comp");
    if (!box) return;
    box.hidden = false;
    var tabs = [
      ["table", "Table"],
      ["scores", "Scores"],
      ["fixtures", "Fixtures"],
      ["scorers", "Scorers"]
    ];
    box.innerHTML =
      '<button class="sp-easy-back" type="button" id="sp-back">← All leagues</button>' +
      "<h1>" + esc(c.flag || "") + " " + esc(c.name) + "</h1>" +
      '<p class="sp-easy-sub">Tap a tab. Table, scores, fixtures, scorers.</p>' +
      '<div class="sp-seg">' + tabs.map(function (t) {
        return '<button type="button" data-tab="' + t[0] + '"' + (t[0] === tab ? ' class="on"' : "") + ">" + t[1] + "</button>";
      }).join("") + "</div>" +
      '<div id="sp-pane">' + pane(c, tab) + "</div>";
    document.getElementById("sp-back").onclick = function () { renderHome(); };
    box.querySelector(".sp-seg").onclick = function (e) {
      var b = e.target.closest("button[data-tab]");
      if (!b) return;
      box.querySelectorAll(".sp-seg button").forEach(function (x) { x.classList.toggle("on", x === b); });
      document.getElementById("sp-pane").innerHTML = pane(c, b.getAttribute("data-tab"));
    };
    if (!isSubpage() && history.replaceState) history.replaceState(null, "", "#" + id);
  }

  function fillLeagues() {
    var host = document.getElementById("sp-league-list");
    if (!host || !DATA) return;
    host.innerHTML = (DATA.competitions || []).map(function (c) {
      var f = c.fixtures && c.fixtures[0];
      var s = c.scores && c.scores[0];
      var strip = "";
      if (s) {
        strip = '<div class="sp-lg-strip">' + img(s.hlogo) + "<b>" + s.hs + "–" + s.as + "</b>" + img(s.alogo) + "</div>";
      } else if (f) {
        strip = '<div class="sp-lg-strip">' + img(f.hlogo) + "<i>vs</i>" + img(f.alogo) + "</div>";
      }
      return '<a class="sp-lg" href="#' + esc(c.id) + '" data-id="' + esc(c.id) + '">' +
        '<div class="sp-lg-top">' + esc(c.flag || "") + " " + esc(c.name) + "<span>Open →</span></div>" +
        strip +
        '<p class="sp-lg-next">' + esc(lineFor(c)) + "</p></a>";
    }).join("");
    host.onclick = function (e) {
      var a = e.target.closest("a[data-id]");
      if (!a) return;
      e.preventDefault();
      openComp(a.getAttribute("data-id"));
    };
  }

  function boot() {
    var forced = view.getAttribute("data-lg");
    var tab = view.getAttribute("data-tab");
    if (forced && find(forced)) {
      openComp(forced, tab);
      return;
    }
    var id = (location.hash || "").replace(/^#/, "");
    if (id && find(id)) openComp(id);
    else renderHome();
  }

  fetch("/content/competitions.json", { cache: "no-cache" })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      DATA = d;
      fillLeagues();
      boot();
    })
    .catch(function () {});
  window.addEventListener("hashchange", function () {
    if (isSubpage()) return;
    boot();
  });
})();

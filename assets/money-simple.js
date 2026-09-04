/* Make Money — country + simple lists. */
(function () {
  "use strict";
  var KEY = "bryme-nationality";
  var POP = ["NG", "GH", "KE", "ZA", "UG", "TZ", "EG", "IN", "PH", "PK", "GB", "US", "CA", "AU"];
  var view = document.getElementById("mm-app");
  if (!view) return;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function loadNat() {
    try { return JSON.parse(localStorage.getItem(KEY) || "null"); } catch (e) { return null; }
  }
  function saveNat(n) {
    try { localStorage.setItem(KEY, JSON.stringify(n)); } catch (e) {}
  }
  function byId(list, id) {
    for (var i = 0; i < list.length; i++) if (list[i].id === id) return list[i];
    return null;
  }
  function ok(item, nat) {
    if (!nat) return true;
    var ex = item.excludes || [];
    if (ex.indexOf(nat.id) !== -1) return false;
    if (item.open || item.mode === "open") return true;
    var inc = item.countries || [];
    var regs = item.regions || [];
    if (inc.length && inc.indexOf(nat.id) !== -1) return true;
    if (regs.length && regs.indexOf(nat.region) !== -1) return true;
    if (item.diaspora) return true;
    if (inc.length || regs.length) return false;
    return true;
  }

  var COUNTRIES = [];
  var ITEMS = [];
  var nat = loadNat();
  var src = view.getAttribute("data-src");

  function renderCountry() {
    var box = document.getElementById("mm-nat");
    if (!box) return;
    var q = (document.getElementById("mm-q") && document.getElementById("mm-q").value) || "";
    var status = document.getElementById("mm-nat-status");
    if (status) {
      status.textContent = nat
        ? "Showing listings for " + nat.name + ". Type another country to change."
        : "Type your country. We hide listings that do not take you.";
    }
    var chips = document.getElementById("mm-chips");
    if (chips) {
      chips.innerHTML = POP.map(function (id) {
        var c = byId(COUNTRIES, id);
        if (!c) return "";
        return '<button type="button" data-id="' + esc(c.id) + '"' + (nat && nat.id === c.id ? ' class="on"' : "") + ">" + esc(c.name) + "</button>";
      }).join("");
    }
    var sug = document.getElementById("mm-suggest");
    if (sug) {
      var f = q.trim().toLowerCase();
      if (!f) { sug.innerHTML = ""; return; }
      var hits = COUNTRIES.filter(function (c) {
        return c.name.toLowerCase().indexOf(f) === 0 || c.name.toLowerCase().indexOf(f) !== -1 || c.id.toLowerCase() === f;
      }).slice(0, 8);
      sug.innerHTML = hits.map(function (c) {
        return '<button type="button" data-id="' + esc(c.id) + '">' + esc(c.name) + "</button>";
      }).join("");
    }
  }

  function renderList() {
    var host = document.getElementById("mm-list");
    if (!host) return;
    var shown = ITEMS.filter(function (it) { return ok(it, nat); });
    var hidden = ITEMS.length - shown.length;
    var count = document.getElementById("mm-count");
    if (count) {
      count.textContent = nat
        ? shown.length + " of " + ITEMS.length + " for " + nat.name + (hidden ? " · " + hidden + " hidden" : "")
        : ITEMS.length + " listings. Pick a country to hide ones that exclude you.";
    }
    host.innerHTML = shown.map(function (it) {
      var href = it.url || "#";
      var ext = /^https?:/i.test(href);
      return '<a class="mm-row" href="' + esc(href) + '"' + (ext ? ' target="_blank" rel="nofollow noopener"' : "") + ">" +
        "<b>" + esc(it.name) + "</b>" +
        "<span>" + esc(it.title || it.excerpt || "") + "</span>" +
        (it.pay ? "<em>" + esc(it.pay) + "</em>" : "") +
        "</a>";
    }).join("") || '<p class="sp-empty">Nothing left for this country. Try another, or clear the country.</p>';
  }

  function pick(id) {
    var c = byId(COUNTRIES, id);
    if (!c) return;
    nat = { id: c.id, name: c.name, region: c.region };
    saveNat(nat);
    var q = document.getElementById("mm-q");
    if (q) q.value = "";
    renderCountry();
    renderList();
  }

  view.addEventListener("click", function (e) {
    var b = e.target.closest("[data-id]");
    if (!b || !view.contains(b)) return;
    pick(b.getAttribute("data-id"));
  });
  var qEl = document.getElementById("mm-q");
  if (qEl) {
    qEl.addEventListener("input", renderCountry);
    qEl.addEventListener("keydown", function (e) {
      if (e.key !== "Enter") return;
      e.preventDefault();
      var first = document.querySelector("#mm-suggest [data-id], #mm-chips [data-id]");
      if (first) pick(first.getAttribute("data-id"));
    });
  }

  var jobs = [fetch("/content/countries.json", { cache: "no-cache" }).then(function (r) { return r.ok ? r.json() : []; })];
  if (src) {
    jobs.push(fetch(src, { cache: "no-cache" }).then(function (r) { return r.ok ? r.json() : { items: [] }; }));
  } else {
    jobs.push(Promise.resolve({ items: [] }));
  }
  Promise.all(jobs).then(function (pair) {
    COUNTRIES = pair[0] || [];
    ITEMS = (pair[1] && pair[1].items) || [];
    if (nat && nat.id && !nat.region) {
      var c = byId(COUNTRIES, nat.id);
      if (c) nat = c;
    }
    renderCountry();
    renderList();
  }).catch(function () {
    var host = document.getElementById("mm-list");
    if (host) host.innerHTML = '<p class="sp-empty">Listings could not load.</p>';
  });
})();

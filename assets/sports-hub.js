/* ==========================================================================
   BRYME SPORTS DESK v2 — page runtime (loaded only on /sports/)
   --------------------------------------------------------------------------
   Small and deliberate. The data layer (sports-engine.js) is untouched.
   This file only handles:
     · league table tabs — click, keyboard (arrows/Home/End), URL hash
   Everything else is CSS.
   ========================================================================== */
(function () {
  "use strict";

  function initTabs(root) {
    var tabs = Array.prototype.slice.call(root.querySelectorAll(".bsd-tab"));
    if (!tabs.length) return;
    var panels = tabs.map(function (t) {
      return document.getElementById(t.getAttribute("aria-controls"));
    });

    function select(tab, focus) {
      tabs.forEach(function (t, i) {
        var on = t === tab;
        t.setAttribute("aria-selected", on ? "true" : "false");
        t.tabIndex = on ? 0 : -1;
        if (panels[i]) panels[i].hidden = !on;
      });
      if (focus !== false) tab.focus();
      if (history.replaceState) history.replaceState(null, "", "#" + tab.getAttribute("data-tab"));
    }

    tabs.forEach(function (t, i) {
      t.addEventListener("click", function () { select(t); });
      t.addEventListener("keydown", function (e) {
        var n = null;
        if (e.key === "ArrowRight") n = tabs[(i + 1) % tabs.length];
        else if (e.key === "ArrowLeft") n = tabs[(i - 1 + tabs.length) % tabs.length];
        else if (e.key === "Home") n = tabs[0];
        else if (e.key === "End") n = tabs[tabs.length - 1];
        if (n) { e.preventDefault(); select(n); }
      });
    });

    /* restore from URL hash (#la-liga etc.) */
    var hash = (location.hash || "").replace("#", "");
    var initial = tabs.filter(function (t) { return t.getAttribute("data-tab") === hash; })[0];
    if (initial) select(initial, false);
  }

  function boot() {
    document.querySelectorAll("[data-tabs]").forEach(initTabs);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();

/* BRYME Media v3 — tiny progressive-enhancement layer.
   No dependencies, no tracking, no network calls of its own.
   1) Trailer facade: pages ship zero iframes; the privacy-enhanced
      youtube-nocookie player is created only after an explicit play action.
   2) Keep the mobile bottom bar's active item in sync with body[data-nav]. */
(function () {
  "use strict";

  /* 1) click-to-play trailer facade */
  document.addEventListener("click", function (e) {
    var btn = e.target && e.target.closest ? e.target.closest("[data-v3-play]") : null;
    if (!btn) return;
    var box = btn.closest(".v3-trailer");
    var id = btn.getAttribute("data-v3-play");
    if (!box || !id) return;
    var frame = document.createElement("iframe");
    frame.setAttribute("src", "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(id) + "?autoplay=1&rel=0&modestbranding=1");
    frame.setAttribute("title", btn.getAttribute("data-v3-title") || "Trailer");
    frame.setAttribute("allow", "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share");
    frame.setAttribute("allowfullscreen", "");
    frame.setAttribute("loading", "lazy");
    frame.setAttribute("referrerpolicy", "strict-origin-when-cross-origin");
    box.classList.add("is-playing");
    box.appendChild(frame);
    frame.focus();
  });

  /* 2) mark the mobile-bar item that matches the current section */
  try {
    var nav = document.body ? document.body.getAttribute("data-nav") : null;
    if (nav) {
      var link = document.querySelector('.mobile-nav a[data-sec="' + nav + '"]');
      if (link) link.setAttribute("aria-current", "page");
    }
  } catch (err) { /* enhancement only — never break the page */ }
})();

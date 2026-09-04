/* BRYME contained legacy interactions.
 * Search-eligible editorial pages are static and do not load this file.
 * No analytics, advertising, automatic playback, storage or service-worker code.
 */
(function () {
  'use strict';
  var originals = typeof WeakMap === 'function' ? new WeakMap() : null;

  function boxFor(node) {
    return (node && node.closest && node.closest('[data-trailer-box]')) || document.querySelector('[data-trailer-box]');
  }
  function candidate(box) {
    var frame = box && box.querySelector('[data-trailer-id]');
    var id = frame && frame.getAttribute('data-trailer-id');
    var watch = '';
    try {
      var rows = JSON.parse(box.getAttribute('data-trailer-candidates') || '[]');
      var row = rows.find(function (x) { return x && /^[A-Za-z0-9_-]{11}$/.test(x.id || ''); });
      if (row) { id = row.id; watch = row.watch || ''; }
    } catch (e) {}
    return /^[A-Za-z0-9_-]{11}$/.test(id || '') ? { id: id, watch: watch } : null;
  }
  function showError(box, item) {
    var error = box && box.querySelector('[data-trailer-error]');
    if (!error) return;
    error.hidden = false;
    var watch = error.querySelector('[data-trailer-watch]');
    if (watch && item && item.watch) watch.href = item.watch;
  }
  function play(box) {
    var frame = box && box.querySelector('[data-trailer-id]');
    var item = candidate(box);
    if (!frame || !item) { showError(box, item); return; }
    if (originals && !originals.has(frame)) originals.set(frame, frame.innerHTML);
    var error = box.querySelector('[data-trailer-error]');
    if (error) error.hidden = true;
    var iframe = document.createElement('iframe');
    iframe.src = 'https://www.youtube-nocookie.com/embed/' + item.id + '?rel=0&modestbranding=1&playsinline=1&enablejsapi=1&autoplay=1';
    iframe.title = (box.getAttribute('data-trailer-title') || 'Title') + ' trailer';
    iframe.allow = 'autoplay; encrypted-media; picture-in-picture';
    iframe.allowFullscreen = true;
    iframe.referrerPolicy = 'strict-origin-when-cross-origin';
    frame.replaceChildren(iframe);
    frame.hidden = false;
    var controls = box.querySelector('[data-trailer-controls]');
    if (controls) controls.hidden = false;
  }
  function reset(box) {
    var frame = box && box.querySelector('[data-trailer-id]');
    if (!frame) return;
    var saved = originals && originals.get(frame);
    if (saved) frame.innerHTML = saved;
    var controls = box.querySelector('[data-trailer-controls]');
    if (controls) controls.hidden = true;
  }
  function command(box, name) {
    var iframe = box && box.querySelector('iframe');
    if (!iframe || !iframe.contentWindow) return;
    iframe.contentWindow.postMessage(JSON.stringify({ event: 'command', func: name, args: [] }), '*');
  }
  function share(control) {
    var url = new URL(control.getAttribute('data-share-path') || location.pathname, location.origin).href;
    var title = control.getAttribute('data-share-title') || document.title;
    if (navigator.share) { navigator.share({ title: title, url: url }).catch(function () {}); return; }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(function () {
        var old = control.textContent; control.textContent = 'Link copied';
        setTimeout(function () { control.textContent = old; }, 1600);
      }).catch(function () {});
    }
  }

  document.addEventListener('click', function (event) {
    var control = event.target.closest && event.target.closest('.trailer-play,.nm-watch-now,.nm-trailer,[data-trailer-unmute],[data-trailer-retry],[data-trailer-close],.nm-tab,.nm-share,.share-action,.nm-back');
    if (!control) return;
    if (control.matches('.trailer-play,.nm-watch-now,.nm-trailer')) {
      event.preventDefault(); play(boxFor(control));
    } else if (control.matches('[data-trailer-unmute]')) {
      event.preventDefault(); command(boxFor(control), 'unMute'); command(boxFor(control), 'playVideo'); control.hidden = true;
    } else if (control.matches('[data-trailer-retry]')) {
      event.preventDefault(); reset(boxFor(control)); play(boxFor(control));
    } else if (control.matches('[data-trailer-close]')) {
      event.preventDefault(); reset(boxFor(control));
    } else if (control.matches('.nm-tab')) {
      event.preventDefault();
      document.querySelectorAll('.nm-tab').forEach(function (x) { x.classList.toggle('is-on', x === control); });
      var name = control.getAttribute('data-nm-tab');
      document.querySelectorAll('.nm-panel').forEach(function (x) { x.classList.toggle('is-on', x.id === 'nm-' + name); });
    } else if (control.matches('.nm-share,.share-action')) {
      event.preventDefault(); share(control);
    } else if (control.matches('.nm-back')) {
      event.preventDefault();
      if (history.length > 1 && document.referrer && new URL(document.referrer).origin === location.origin) history.back();
      else location.href = '/';
    }
  });
})();

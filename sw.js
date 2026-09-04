/* BRYME no longer installs an offline cache while the focused site is rebuilt. */
self.addEventListener('install', function () { self.skipWaiting(); });
self.addEventListener('activate', function (event) {
  event.waitUntil(Promise.all([
    caches.keys().then(function (names) { return Promise.all(names.map(function (name) { return caches.delete(name); })); }),
    self.registration.unregister(),
    self.clients.claim()
  ]));
});

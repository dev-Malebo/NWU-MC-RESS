// Minimal service worker so the site can be installed
self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  // Network-first for now — just enough for installability
  event.respondWith(fetch(event.request));
});

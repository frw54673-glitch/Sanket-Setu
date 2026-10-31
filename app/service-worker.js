const CACHE_NAME = 'sanket-setu-shell-v5';
const SHELL = [
  '/',
  '/assets/sanket-setu-mark.svg',
  '/assets/sanket-setu-polish.css?v=6',
  '/assets/sanket-setu-walkthrough-poster.jpg',
  '/assets/sanket-setu-walkthrough.vtt',
  '/assets/sanket-setu-walkthrough-hi.vtt',
  '/manifest.webmanifest',
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(key => key.startsWith('sanket-setu-') && key !== CACHE_NAME)
      .map(key => caches.delete(key))
  )));
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== self.location.origin) return;
  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).then(response => {
      if (response.ok) caches.open(CACHE_NAME).then(cache => cache.put('/', response.clone()));
      return response;
    }).catch(async () => (await caches.match('/')) || Response.error()));
    return;
  }
  if (url.pathname.endsWith('.mp4')) return;
  event.respondWith(caches.match(request).then(cached => cached || fetch(request).then(response => {
    if (response.ok) caches.open(CACHE_NAME).then(cache => cache.put(request, response.clone()));
    return response;
  })));
});


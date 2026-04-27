/**
 * ONTO Agent · Service Worker v1.1
 *
 * Strategy:
 *   - App shell cached on install (offline splash works)
 *   - Network-first for HTML (always latest UI)
 *   - Cache-first for static assets (icons, fonts, manifest)
 *   - API calls pass through untouched (never cache AI responses)
 *
 * Cache versioning: bump CACHE_NAME on UI release to force refresh.
 *
 * v1.5: institute voice cleanup - removed SaaS reward tiers from donation modal
 */

const CACHE_NAME = 'onto-agent-v1.5';

const APP_SHELL = [
  '/agent/',
  '/agent/index.html',
  '/agent/manifest.json',
  '/agent/favicon.ico',
  '/agent/favicon-32.png',
  '/agent/icons/icon-192.png',
  '/agent/icons/icon-512.png',
  '/agent/icons/maskable-icon-512.png',
];

// ─── install: prime cache with app shell ─────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL).catch(() => {}))
      .then(() => self.skipWaiting())
  );
});

// ─── activate: drop old caches ───────────────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((names) => Promise.all(
        names.filter((n) => n !== CACHE_NAME).map((n) => caches.delete(n))
      ))
      .then(() => self.clients.claim())
  );
});

// ─── fetch: route by request type ────────────────────────────────
self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Skip non-GET
  if (req.method !== 'GET') return;

  // Skip cross-origin (API, Google Fonts) — let network handle
  if (url.origin !== self.location.origin) return;

  // Skip API paths even if same-origin
  if (url.pathname.startsWith('/v1/')) return;

  // HTML: network-first (always fresh UI)
  if (req.mode === 'navigate' || req.destination === 'document') {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE_NAME).then((c) => c.put(req, copy)).catch(() => {});
          return res;
        })
        .catch(() => caches.match(req).then((hit) => hit || caches.match('/agent/')))
    );
    return;
  }

  // Static assets: cache-first
  event.respondWith(
    caches.match(req).then((hit) => {
      if (hit) return hit;
      return fetch(req).then((res) => {
        if (res && res.status === 200 && res.type === 'basic') {
          const copy = res.clone();
          caches.open(CACHE_NAME).then((c) => c.put(req, copy)).catch(() => {});
        }
        return res;
      }).catch(() => hit);
    })
  );
});

// ─── message: allow manual cache clear from app ──────────────────
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    caches.delete(CACHE_NAME);
  }
});

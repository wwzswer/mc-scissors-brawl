/* =========================================================================
   方块猜拳战场 · Service Worker
   目标：装成 App 之后断网也能开局（单机全在本地跑），联机接口永不缓存
   策略：
     · 页面导航        network-first（3.5s 超时）→ 失败回缓存 → 再失败回离线壳
     · 同源静态资源    stale-while-revalidate（先给缓存，后台更新）
     · /api/*          直接放行，绝不拦截、绝不缓存（联机房间必须实时）
     · 跨域请求        直接放行
   发版：改动 index.html 后把 VERSION 加一，旧缓存会在 activate 时清掉
   ========================================================================= */
const VERSION = 'mc-brawl-v1.6.0-2';
const CORE = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icon-192.png',
  './icon-512.png',
  './icon-maskable-512.png',
  './apple-touch-icon-180.png',
];

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(VERSION);
    /* 逐个装，个别文件 404 不至于让整个安装失败 */
    await Promise.all(CORE.map(u =>
      fetch(u, { cache: 'reload' }).then(r => {
        if (r && (r.ok || r.type === 'opaque')) return cache.put(u, r);
      }).catch(() => {})
    ));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

self.addEventListener('message', event => {
  const data = event.data || {};
  if (data.type === 'SKIP_WAITING') self.skipWaiting();
  if (data.type === 'VERSION') event.source && event.source.postMessage({ type: 'VERSION', version: VERSION });
});

function timeout(ms){
  return new Promise(resolve => setTimeout(() => resolve(null), ms));
}

async function networkFirst(request){
  const cache = await caches.open(VERSION);
  try{
    const res = await Promise.race([fetch(request), timeout(3500).then(r => r || Promise.reject(new Error('timeout')))]);
    if (res && res.ok) cache.put(request, res.clone()).catch(() => {});
    return res;
  }catch(err){
    const hit = await cache.match(request) || await cache.match('./index.html') || await cache.match('./');
    if (hit) return hit;
    return new Response(
      '<!doctype html><meta charset="utf-8"><title>离线</title>' +
      '<body style="background:#0e1116;color:#e8ecf5;font-family:system-ui;padding:40px;line-height:1.9">' +
      '<h2>离线，而且本地缓存里没有页面</h2>' +
      '<p>先把 <code>start-server.cmd</code> 跑起来，用 <code>http://127.0.0.1:8787</code> 打开一次，之后就能离线开局了。</p>' +
      '</body>',
      { status: 200, headers: { 'Content-Type': 'text/html; charset=utf-8' } }
    );
  }
}

async function staleWhileRevalidate(request){
  const cache = await caches.open(VERSION);
  const hit = await cache.match(request);
  const fetching = fetch(request).then(res => {
    if (res && res.ok) cache.put(request, res.clone()).catch(() => {});
    return res;
  }).catch(() => null);
  if (hit){
    fetching.catch(() => {});
    return hit;
  }
  const res = await fetching;
  return res || new Response('', { status: 504, statusText: 'offline' });
}

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  let url;
  try{ url = new URL(req.url); }catch(e){ return; }
  if (url.origin !== self.location.origin) return;            /* 第三方资源不插手 */
  if (url.pathname.startsWith('/api/')) return;               /* 联机接口：绝不缓存 */

  const isHTML = req.mode === 'navigate' || (req.headers.get('accept') || '').includes('text/html');
  event.respondWith(isHTML ? networkFirst(req) : staleWhileRevalidate(req));
});

const CACHE = "nexo-v0.5";
const ARCHIVOS = ["./", "./index.html", "./callback.html", "./styles.css", "./app.js", "./manifest.webmanifest", "./icono.svg", "./icono-192.png", "./icono-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ARCHIVOS)));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((claves) =>
      Promise.all(claves.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("message", (e) => {
  if (e.data === "actualizar") {
    caches.keys().then((claves) => Promise.all(claves.map((k) => caches.delete(k))));
    self.skipWaiting();
  }
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  let url;
  try { url = new URL(e.request.url); } catch { return; }
  if (url.origin !== location.origin) return;
  e.respondWith(
    fetch(e.request)
      .then((respuesta) => {
        const copia = respuesta.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copia));
        return respuesta;
      })
      .catch(() => caches.match(e.request).then((r) => r || caches.match("./")))
  );
});

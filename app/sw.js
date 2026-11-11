const CACHE = "astral-v0.1";
const ARCHIVOS = ["./", "./index.html", "./styles.css", "./app.js", "./manifest.webmanifest", "./icono.svg"];

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

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET" || new URL(e.request.url).pathname.startsWith("/servidores") || new URL(e.request.url).pathname.startsWith("/auth")) {
    return;
  }
  e.respondWith(
    caches.match(e.request).then((respuesta) => respuesta || fetch(e.request))
  );
});

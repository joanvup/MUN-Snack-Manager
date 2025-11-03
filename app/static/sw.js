// Definimos un nombre y versión para nuestro caché
const CACHE_NAME = 'mun-snack-manager-v1';
// Lista de archivos que queremos cachear (el "esqueleto" de la app)
const urlsToCache = [
  '/', // La ruta raíz (que redirige al login o al escaner)
  '/operador/escaner', // La página principal de escaneo
  '/static/manifest.json', // El manifiesto
  'https://cdn.tailwindcss.com', // El CSS de Tailwind
  'https://unpkg.com/html5-qrcode@2.0.9/dist/html5-qrcode.min.js' // La librería del escaner
];

// Evento 'install': Se dispara cuando el service worker se instala.
self.addEventListener('install', event => {
  // Esperamos hasta que el caché esté abierto y todos los archivos estén guardados.
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Cache abierto');
        return cache.addAll(urlsToCache);
      })
  );
});

// Evento 'activate': Se dispara después de la instalación y se usa para limpiar cachés antiguos.
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            // Si el caché no está en nuestra lista blanca, lo borramos.
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Evento 'fetch': Se dispara cada vez que la app hace una petición de red (pide un archivo, una imagen, etc.).
self.addEventListener('fetch', event => {
  event.respondWith(
    // Buscamos la respuesta en el caché primero.
    caches.match(event.request)
      .then(response => {
        // Si la encontramos en el caché, la devolvemos.
        if (response) {
          return response;
        }
        // Si no, hacemos la petición a la red como siempre.
        return fetch(event.request);
      })
  );
});
/**
 * Variante del Worker que sirve el sitio desde archivos empaquetados en el
 * propio script (src/static.gen.js), sin el servicio de estáticos de
 * Cloudflare. Misma lógica de formulario que src/worker.js.
 */
import site from './worker.js';
import FILES from './static.gen.js';

const SECURITY = {
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
  'X-Frame-Options': 'SAMEORIGIN',
};

const cache = new Map();
function body(path) {
  if (!cache.has(path)) {
    const bin = atob(FILES[path][1]);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    cache.set(path, bytes);
  }
  return cache.get(path);
}

function respond(path, status = 200) {
  const headers = new Headers(SECURITY);
  headers.set('Content-Type', FILES[path][0]);
  headers.set('Cache-Control', path.startsWith('/assets/') ? 'public, max-age=31536000, immutable' : 'public, max-age=0, must-revalidate');
  return new Response(body(path), { status, headers });
}

const embedded = {
  async fetch(request) {
    const url = new URL(request.url);
    let p = decodeURIComponent(url.pathname);
    if (request.method !== 'GET' && request.method !== 'HEAD') return new Response('Method Not Allowed', { status: 405 });
    if (FILES[p]) return respond(p);
    if (p.endsWith('/') && FILES[p + 'index.html']) return respond(p + 'index.html');
    if (!p.endsWith('/') && FILES[p + '/index.html']) {
      url.pathname = p + '/';
      return Response.redirect(url.toString(), 308);
    }
    if (p.endsWith('/index.html') && FILES[p]) return respond(p);
    return respond('/404.html', 404);
  },
};

export default {
  async fetch(request, env, ctx) {
    const res = await site.fetch(request, { ...env, ASSETS: embedded }, ctx);
    // La versión de prueba en workers.dev no debe aparecer en buscadores
    if (new URL(request.url).hostname.endsWith('.workers.dev')) {
      const out = new Response(res.body, res);
      out.headers.set('X-Robots-Tag', 'noindex, nofollow');
      return out;
    }
    return res;
  },
};

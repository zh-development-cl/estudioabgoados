/**
 * Abogados Remates Judiciales · Worker de Cloudflare
 *
 * Sirve el sitio estático (carpeta public/) y recibe el formulario de contacto
 * en POST /api/contacto. Cada contacto se guarda en la base D1 (buzón único
 * para todas las páginas del grupo) y, si está configurado, se avisa por correo
 * con Brevo.
 *
 * Variables (wrangler.jsonc o panel de Cloudflare):
 *   NOTIFY_TO      correos que reciben el aviso, separados por coma
 *   NOTIFY_FROM    remitente verificado en Brevo
 *   SITE_NAME      nombre del sitio de origen (para distinguirlo en el buzón)
 * Secreto (wrangler secret put BREVO_API_KEY):
 *   BREVO_API_KEY  clave de la API de Brevo; sin ella solo se guarda en D1
 */

const MAX = { nombre: 120, telefono: 40, email: 160, perfil: 40, mensaje: 3000, pagina: 200 };
const PERFILES = new Set(['Persona', 'Inversionista', 'Empresa o fondo']);

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === '/api/contacto') {
      if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: { Allow: 'POST' } });
      if (request.method !== 'POST') return json({ ok: false, error: 'method' }, 405);
      return contacto(request, env, ctx);
    }
    return env.ASSETS.fetch(request);
  },
};

async function contacto(request, env, ctx) {
  // Solo aceptamos envíos desde el propio sitio
  const origin = request.headers.get('Origin');
  if (origin && new URL(origin).host !== new URL(request.url).host) return json({ ok: false, error: 'origin' }, 403);

  let data;
  try {
    const type = request.headers.get('Content-Type') || '';
    data = type.includes('application/json') ? await request.json() : Object.fromEntries(await request.formData());
  } catch {
    return json({ ok: false, error: 'formato' }, 400);
  }

  // Campo trampa para bots: si viene lleno, respondemos «ok» sin guardar nada
  if (clean(data.web)) return json({ ok: true });

  const c = {};
  for (const k of Object.keys(MAX)) c[k] = clean(data[k]).slice(0, MAX[k]);
  if (!PERFILES.has(c.perfil)) c.perfil = 'Persona';
  if (!c.nombre || !c.mensaje) return json({ ok: false, error: 'faltan datos' }, 422);
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(c.email)) return json({ ok: false, error: 'correo' }, 422);
  if (c.telefono.replace(/\D/g, '').length < 8) return json({ ok: false, error: 'teléfono' }, 422);

  const sitio = env.SITE_NAME || new URL(request.url).host;
  const ip = request.headers.get('CF-Connecting-IP') || '';
  const pais = (request.cf && request.cf.country) || '';

  try {
    await env.DB.prepare(
      `INSERT INTO contactos (creado, sitio, pagina, nombre, telefono, email, perfil, mensaje, ip, pais)
       VALUES (datetime('now'), ?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)`
    ).bind(sitio, c.pagina, c.nombre, c.telefono, c.email, c.perfil, c.mensaje, ip, pais).run();
  } catch (err) {
    console.error('D1', err);
    return json({ ok: false, error: 'guardar' }, 500);
  }

  if (env.BREVO_API_KEY && env.NOTIFY_TO && env.NOTIFY_FROM) ctx.waitUntil(notify(env, sitio, c));
  return json({ ok: true });
}

async function notify(env, sitio, c) {
  const to = env.NOTIFY_TO.split(',').map(e => ({ email: e.trim() })).filter(e => e.email);
  const rows = [
    ['Sitio', sitio], ['Nombre', c.nombre], ['Teléfono', c.telefono], ['Correo', c.email],
    ['Perfil', c.perfil], ['Página', c.pagina], ['Mensaje', c.mensaje],
  ];
  const html = `<table cellpadding="6" style="font-family:Arial,sans-serif;font-size:14px;border-collapse:collapse">${
    rows.map(([k, v]) => `<tr><td style="color:#6A6F89;vertical-align:top">${k}</td><td style="color:#171C36;white-space:pre-wrap">${escapeHtml(v)}</td></tr>`).join('')
  }</table>`;
  try {
    const res = await fetch('https://api.brevo.com/v3/smtp/email', {
      method: 'POST',
      headers: { 'api-key': env.BREVO_API_KEY, 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({
        sender: { email: env.NOTIFY_FROM, name: sitio },
        to,
        replyTo: { email: c.email, name: c.nombre },
        subject: `Nuevo contacto · ${sitio} · ${c.nombre}`,
        htmlContent: html,
      }),
    });
    if (!res.ok) console.error('Brevo', res.status, await res.text());
  } catch (err) {
    console.error('Brevo', err);
  }
}

function clean(v) {
  return typeof v === 'string' ? v.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '').trim() : '';
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
  });
}

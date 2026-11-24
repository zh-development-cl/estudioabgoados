# abogadosrematesjudiciales.cl

Sitio de **Abogados Remates Judiciales**. Es estático (HTML, CSS y JS sin frameworks) y se publica en Cloudflare Workers, donde además un Worker recibe el formulario de contacto y lo guarda en una base D1 que sirve de buzón único para los sitios del grupo.

## Estructura

| Ruta | Qué es |
|---|---|
| `public/` | El sitio que se publica. Las páginas HTML se generan; no editarlas a mano. |
| `public/assets/site.css`, `site.js` | Estilos y comportamiento, incluida la animación de entrada. |
| `tools/site.json` | Teléfono, WhatsApp, dirección y dominio. |
| `tools/build_site.py` | Contenido y plantillas de las páginas, datos estructurados, sitemap, `robots.txt` y `llms.txt`. |
| `tools/build_assets.py` | Logos, íconos, imagen para redes y el plano de la portada, a partir de `brand/remates-judiciales/build.py`. |
| `src/worker.js` | Recibe `POST /api/contacto`, lo guarda en D1 y avisa por correo si Brevo está configurado. |
| `schema.sql` | Tabla `contactos` del buzón único. |
| `wrangler.jsonc` | Configuración de Cloudflare. |

## Comandos

```bash
npm install
```

```bash
npm run build
```

Para verlo en local (usa una copia de la configuración con una base de prueba):

```bash
npx wrangler d1 execute buzon-contactos --local --config wrangler.dev.jsonc --file schema.sql
```

```bash
npx wrangler dev --config wrangler.dev.jsonc
```

## Publicar

El token de Cloudflare necesita, además de Zone y DNS, los permisos **Workers Scripts · Edit** y **D1 · Edit** a nivel de cuenta.

1. Crear la base y copiar su `database_id` en `wrangler.jsonc`:

```bash
npx wrangler d1 create buzon-contactos
```

2. Crear la tabla en la base real:

```bash
npx wrangler d1 execute buzon-contactos --remote --file schema.sql
```

3. Publicar. Las rutas `custom_domain` conectan el sitio a `abogadosrematesjudiciales.cl` y `www`:

```bash
npx wrangler deploy
```

4. Opcional, aviso por correo de cada contacto: definir `NOTIFY_TO` y `NOTIFY_FROM` en `wrangler.jsonc` y guardar la clave de Brevo:

```bash
npx wrangler secret put BREVO_API_KEY
```

## Publicar desde un entorno con proxy

Si el despliegue normal falla al subir los archivos (`workers/assets/upload -> 401`), es porque un proxy reemplaza el encabezado Authorization. En ese caso se empaqueta el sitio dentro del Worker y se publica con la variante `wrangler.embed.jsonc`:

```bash
python3 tools/embed_static.py
```

```bash
npx wrangler deploy --config wrangler.embed.jsonc
```

La versión de prueba queda en https://abogadosrematesjudiciales.zhdevelopment.workers.dev y responde `noindex` para que no aparezca en buscadores.

## Antes de publicar, confirmar con el cliente

- Número de WhatsApp y teléfono propios de la marca (hoy usa el de administración de Cáceres & Camiruaga).
- Correo que recibe los avisos de contacto.
- Textos del equipo, fotos de cada persona y cifras que quieran mostrar.
- Respuestas de las preguntas frecuentes y la guía: son generales y deben revisarlas los abogados.
- Concepto de logo elegido. El sitio usa la R de martillo; para cambiarlo basta regenerar con `npm run build`.

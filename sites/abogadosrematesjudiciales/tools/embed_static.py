"""Empaqueta public/ dentro de un módulo JS para publicar el sitio sin el
servicio de archivos estáticos de Cloudflare (útil cuando el despliegue se hace
detrás de un proxy que reemplaza el encabezado Authorization).

Uso:  python3 sites/abogadosrematesjudiciales/tools/embed_static.py
Genera src/static.gen.js (no se versiona).
"""
import base64
import json
import mimetypes
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
PUB = os.path.join(SITE, "public")
OUT = os.path.join(SITE, "src", "static.gen.js")

TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".svg": "image/svg+xml", ".png": "image/png", ".woff2": "font/woff2", ".json": "application/json",
         ".xml": "application/xml; charset=utf-8", ".txt": "text/plain; charset=utf-8",
         ".webmanifest": "application/manifest+json"}
SKIP = {"_headers"}

files = {}
for root, _, names in os.walk(PUB):
    for n in names:
        if n in SKIP or n.startswith("."):
            continue
        p = os.path.join(root, n)
        rel = "/" + os.path.relpath(p, PUB).replace(os.sep, "/")
        ext = os.path.splitext(n)[1].lower()
        ctype = TYPES.get(ext) or mimetypes.guess_type(n)[0] or "application/octet-stream"
        files[rel] = [ctype, base64.b64encode(open(p, "rb").read()).decode()]

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("// Generado por tools/embed_static.py. No editar.\nexport default ")
    json.dump(files, fh, separators=(",", ":"))
    fh.write(";\n")
print(f"{len(files)} archivos, {os.path.getsize(OUT) // 1024} KB en {OUT}")

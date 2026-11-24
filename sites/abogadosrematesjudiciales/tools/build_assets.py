"""Genera los recursos gráficos del sitio a partir de la marca:
logos, piezas de la animación inicial, íconos, imagen para redes y el plano
de fondo de la portada.

Uso:  python3 sites/abogadosrematesjudiciales/tools/build_assets.py
Requiere lo mismo que brand/remates-judiciales/build.py, más Chromium vía
Playwright (node) para rasterizar los PNG.
"""
import json
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(SITE))
sys.path.insert(0, os.path.join(ROOT, "brand", "remates-judiciales"))

import build as brand  # noqa: E402
from build import NAVY, bbox, d_of, minus, place, rrect, union  # noqa: E402

PUB = os.path.join(SITE, "public")
IMG = os.path.join(PUB, "assets", "img")
ACC = brand.ACCENTS["verde"][0]
ACC_L = brand.ACCENTS["verde"][1]


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def mark_parts():
    """La R de martillo separada en letra y cabeza del martillo (alto 100)."""
    m = brand.mark_r(100.0, parts=True)
    return m["letter"], m["head"], m["w"], m["h"]


def svg_doc(view, body, title=None, extra=""):
    t = f"<title>{title}</title>" if title else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view}"{extra}>{t}{body}</svg>')


def build_logos():
    files = {
        "logo-horizontal.svg": brand.r_horizontal("color"),
        "logo-horizontal-negativo.svg": brand.r_horizontal("negativo"),
        "logo-vertical.svg": brand.r_vertical("color"),
        "simbolo.svg": brand.symbol("r", "color"),
        "simbolo-negativo.svg": brand.symbol("r", "negativo"),
        "sello.svg": brand.r_sello("color"),
        "sello-negativo.svg": brand.r_sello("negativo"),
    }
    for name, content in files.items():
        write(os.path.join(IMG, name), content)


def build_intro():
    """Piezas para la animación: letra y cabeza por separado, con el mismo
    viewBox, más la línea base que se abre con el golpe."""
    letter, head, w, h = mark_parts()
    data = {
        "viewBox": f"-4 -4 {w + 8:.2f} {h + 8:.2f}",
        "letter": d_of(letter),
        "head": d_of(head),
        "w": round(w, 2),
        "h": round(h, 2),
        # punto de impacto: centro de la cabeza sobre la base
        "impact": [round((bbox([head])[0] + bbox([head])[2]) / 2, 2), round(bbox([head])[3], 2)],
    }
    write(os.path.join(SITE, "tools", "intro-parts.json"), json.dumps(data))
    return data


def build_icons():
    fav = brand.avatar("r")
    write(os.path.join(PUB, "favicon.svg"), fav)
    write(os.path.join(IMG, "avatar.svg"), fav)
    return fav


def build_plan():
    """Plano de manzanas y lotes para el fondo de la portada (líneas finas)."""
    rnd = random.Random(7)
    W, H = 1600, 1000
    paths, lots = [], []
    x = -40
    while x < W:
        bw = rnd.choice([180, 210, 240, 260])
        y = -30
        while y < H:
            bh = rnd.choice([150, 170, 200, 230])
            street = 22
            bx, by, bw2, bh2 = x + street / 2, y + street / 2, bw - street, bh - street
            paths.append(f"M{bx:.0f} {by:.0f}h{bw2:.0f}v{bh2:.0f}h{-bw2:.0f}Z")
            # subdivisión en lotes
            n = rnd.choice([3, 4, 5])
            if rnd.random() < 0.5:
                step = bw2 / n
                for i in range(1, n):
                    paths.append(f"M{bx + i * step:.1f} {by:.0f}v{bh2 * rnd.choice([0.5, 1]):.0f}")
                paths.append(f"M{bx:.0f} {by + bh2 / 2:.0f}h{bw2:.0f}")
                cell = (bx + step * rnd.randrange(n), by + (0 if rnd.random() < .5 else bh2 / 2), step, bh2 / 2)
            else:
                step = bh2 / n
                for i in range(1, n):
                    paths.append(f"M{bx:.0f} {by + i * step:.1f}h{bw2:.0f}")
                cell = (bx, by + step * rnd.randrange(n), bw2, step)
            if rnd.random() < 0.09:
                lots.append(cell)
            y += bh
        x += bw
    lines = "".join(f'<path d="{d}" pathLength="1"/>' for d in paths)
    hl = "".join(f'<rect x="{c[0]:.1f}" y="{c[1]:.1f}" width="{c[2]:.1f}" height="{c[3]:.1f}"/>' for c in lots)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" aria-hidden="true">'
           f'<g class="plan-lines" fill="none" stroke="currentColor" stroke-width="1">{lines}</g>'
           f'<g class="plan-lots">{hl}</g></svg>')
    write(os.path.join(SITE, "tools", "plan.svg"), svg)
    return svg


def rasterize():
    """PNG para íconos y la imagen de redes sociales, con Chromium."""
    fav = open(os.path.join(PUB, "favicon.svg"), encoding="utf-8").read()
    logo_neg = brand.r_horizontal("negativo")
    sello = brand.r_sello("negativo")
    og = f"""<!doctype html><html><head><meta charset="utf-8"><style>
    @font-face{{font-family:M;src:url(file://{PUB}/assets/fonts/montserrat-500.woff2)}}
    body{{margin:0;width:1200px;height:630px;background:{NAVY};display:flex;align-items:center;justify-content:space-between;padding:0 96px;box-sizing:border-box;font-family:M}}
    .l{{width:640px}} .s{{width:250px;opacity:.95}} .k{{position:absolute;left:96px;bottom:70px;color:#C9CDDD;letter-spacing:.32em;font-size:17px}}
    .bar{{position:absolute;left:96px;bottom:110px;width:60px;height:3px;background:{ACC_L}}}
    </style></head><body><div class="l">{logo_neg}</div><div class="s">{sello}</div>
    <div class="bar"></div><div class="k">SANTIAGO · CHILE</div></body></html>"""
    jobs = [
        ("og.png", og, 1200, 630),
        ("apple-touch-icon.png", f'<html><body style="margin:0;width:180px;height:180px">{fav}</body></html>', 180, 180),
        ("icon-512.png", f'<html><body style="margin:0;width:512px;height:512px">{fav}</body></html>', 512, 512),
        ("icon-192.png", f'<html><body style="margin:0;width:192px;height:192px">{fav}</body></html>', 192, 192),
        ("favicon-32.png", f'<html><body style="margin:0;width:32px;height:32px">{fav}</body></html>', 32, 32),
    ]
    tmp = os.path.join(SITE, "tools", ".raster")
    os.makedirs(tmp, exist_ok=True)
    specs = []
    for name, html, w, h in jobs:
        html = html.replace("<svg ", '<svg style="display:block;width:100%;height:100%" ', 1) if name != "og.png" else html
        p = os.path.join(tmp, name + ".html")
        write(p, html)
        out = os.path.join(PUB if name != "og.png" else IMG, name)
        specs.append({"src": p, "out": out, "w": w, "h": h})
    js = """
const { chromium } = require('playwright');
(async () => {
  const specs = JSON.parse(process.argv[2]);
  const b = await chromium.launch();
  for (const s of specs) {
    const p = await b.newPage({ viewport: { width: s.w, height: s.h }, deviceScaleFactor: 1 });
    await p.goto('file://' + s.src); await p.waitForTimeout(150);
    await p.screenshot({ path: s.out, omitBackground: false });
    await p.close();
  }
  await b.close();
})();
"""
    jsp = os.path.join(tmp, "r.js")
    write(jsp, js)
    subprocess.run(["node", jsp, json.dumps(specs)], check=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)


if __name__ == "__main__":
    build_logos()
    build_icons()
    build_intro()
    build_plan()
    rasterize()
    print("recursos generados")

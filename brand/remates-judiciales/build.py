"""Genera los logos propuestos para Abogados Remates Judiciales (SVG con texto
convertido a trazos) y la página de propuesta.

Uso:  python3 brand/remates-judiciales/build.py
Requiere: fonttools, brotli, pillow.
"""
import base64
import io
import os

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BRAND = os.path.dirname(HERE)

NAVY = "#222B53"   # azul compartido por las marcas del grupo
GREY = "#6E6D6D"   # gris del texto secundario en los logos actuales
GOLD = "#EAB350"   # acento de Cáceres & Camiruaga
TERRA = "#DB7545"  # acento de Inversiones Cáceres

# Acentos candidatos para la marca nueva: (sobre blanco, sobre azul)
ACCENTS = {
    "verde": ("#1F7A6B", "#5CC2AE"),
    "burdeos": ("#8C2F3C", "#E08D99"),
    "acero": ("#3A6EA5", "#8DB4DC"),
}


def num(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


class Face:
    def __init__(self, path):
        self.font = TTFont(path)
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upm = self.font["head"].unitsPerEm

    def glyph(self, ch):
        return self.glyphs[self.cmap[ord(ch)]]

    def width(self, text, size, track=0.0):
        s = size / self.upm
        return sum(self.glyph(c).width for c in text) * s + track * size * (len(text) - 1)

    def bounds(self, ch, size):
        pen = BoundsPen(self.glyphs)
        self.glyph(ch).draw(pen)
        s = size / self.upm
        x0, y0, x1, y1 = pen.bounds
        return x0 * s, y0 * s, x1 * s, y1 * s

    def path(self, text, size, x, y, track=0.0, anchor="start"):
        """Texto como trazos. (x, y) es la línea base; devuelve (d, ancho)."""
        w = self.width(text, size, track)
        if anchor == "middle":
            x -= w / 2
        elif anchor == "end":
            x -= w
        s = size / self.upm
        out = []
        for c in text:
            g = self.glyph(c)
            pen = SVGPathPen(self.glyphs, ntos=num)
            g.draw(TransformPen(pen, (s, 0, 0, -s, x, y)))
            cmds = pen.getCommands()
            if cmds:
                out.append(cmds)
            x += g.width * s + track * size
        return "".join(out), w

    def fit_track(self, text, size, target):
        """Espaciado (en em) para que el texto mida `target` de ancho."""
        return (target - self.width(text, size)) / (size * (len(text) - 1))

    def fit_size(self, text, target, track):
        return target / self.width(text, 1.0, track)


SERIF = Face(os.path.join(HERE, "fonts", "texgyrepagella-regular.otf"))
SANS = Face(os.path.join(HERE, "fonts", "montserrat-latin-400-normal.woff2"))
SANS_M = Face(os.path.join(HERE, "fonts", "montserrat-latin-500-normal.woff2"))


def palette(mode, accent):
    on_white, on_navy = ACCENTS[accent]
    if mode == "color":
        return dict(fg=NAVY, sub=GREY, acc=on_white, bg="#FFFFFF", band=on_white)
    if mode == "negativo":
        return dict(fg="#FFFFFF", sub="#C9CDDD", acc=on_navy, bg=NAVY, band=on_navy)
    if mode == "mono":
        return dict(fg="#111111", sub="#111111", acc="#111111", bg="#FFFFFF", band="#FFFFFF")
    raise ValueError(mode)


def svg(w, h, body, title):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {num(w)} {num(h)}" '
        f'role="img" aria-label="{title}"><title>{title}</title>{body}</svg>'
    )


def p(d, fill, extra=""):
    return f'<path d="{d}" fill="{fill}"{extra}/>'


def rect(x, y, w, h, fill, rx=0, extra=""):
    r = f' rx="{num(rx)}"' if rx else ""
    return f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}"{r} fill="{fill}"{extra}/>'


# ---------------------------------------------------------------- símbolos

def monogram_rj(c, size=150.0):
    """R y J superpuestas, como las CC e IC del grupo. Devuelve (body, w, h)."""
    rx0, _, rx1, rcap = SERIF.bounds("R", size)
    jx0, jy0, jx1, _ = SERIF.bounds("J", size)
    pad = size * 0.04
    base = pad + rcap                      # línea base de la R
    r_x = pad - rx0
    j_drop = size * 0.11                   # la J baja respecto de la R
    j_x = r_x + rx1 - size * 0.20 - jx0    # la J muerde la pata de la R
    j_base = base + j_drop
    d_r, _ = SERIF.path("R", size, r_x, base)
    d_j, _ = SERIF.path("J", size, j_x, j_base)
    halo = f' stroke="{c["bg"]}" stroke-width="{num(size * 0.05)}" stroke-linejoin="round" paint-order="stroke"'
    body = p(d_r, c["fg"]) + p(d_j, c["acc"], halo)
    w = j_x + jx1 + pad
    h = j_base - jy0 + pad
    return body, w, h


def gavel(c, s=1.0, ox=0.0, oy=0.0):
    """Martillo de remate sobre su base. Caja de 100 x 100 a escala 1."""
    g = (
        f'<g transform="translate({num(ox)} {num(oy)}) scale({num(s)})">'
        '<g transform="rotate(-40 44 46)">'
        + rect(15, 26, 58, 28, c["fg"], 4.5)
        + rect(22.5, 26, 5.5, 28, c["band"])
        + rect(60, 26, 5.5, 28, c["band"])
        + rect(39.5, 54, 9, 44, c["fg"], 4.5)
        + "</g>"
        + rect(44, 88.5, 52, 8.5, c["acc"], 4.25)
        + "</g>"
    )
    return g


# ---------------------------------------------------------------- lockups

def bars_abogados(c, cx, base, size=13.5, track=0.42):
    """« | ABOGADOS | » con barras de acento, igual que el logo del estudio."""
    d, w = SANS.path("ABOGADOS", size, cx, base, track, "middle")
    cap = size * 0.70
    gap = size * 0.95
    bar_w = size * 0.11
    top = base - cap - size * 0.38
    bh = cap + size * 0.76
    return (
        p(d, c["sub"])
        + rect(cx - w / 2 - gap - bar_w, top, bar_w, bh, c["acc"])
        + rect(cx + w / 2 + gap, top, bar_w, bh, c["acc"])
    ), w + 2 * (gap + bar_w)


def logo_a(mode="color", accent="verde"):
    """A · Monograma: el más cercano a la familia."""
    c = palette(mode, accent)
    mono, mw, mh = monogram_rj(c, 132)
    size, track = 31.0, 0.24
    tw = SERIF.width("REMATES JUDICIALES", size, track)
    W = tw + 24
    cx = W / 2
    y_text = mh + 44
    d, _ = SERIF.path("REMATES JUDICIALES", size, cx, y_text, track, "middle")
    sub, _ = bars_abogados(c, cx, y_text + 33)
    body = f'<g transform="translate({num(cx - mw / 2)} 0)">{mono}</g>' + p(d, c["fg"]) + sub
    return svg(W, y_text + 33 + 16, body, "Abogados Remates Judiciales")


def logo_b(mode="color", accent="verde"):
    """B · Martillo: símbolo propio, lectura inmediata."""
    c = palette(mode, accent)
    icon = 92.0
    x_rule = icon + 18
    x_text = x_rule + 20
    size, track = 31.0, 0.20
    d1, w1 = SERIF.path("REMATES JUDICIALES", size, x_text, 47, track)
    d2, _ = SANS_M.path("ABOGADOS", 12.5, x_text + 1, 74, 0.46)
    body = (
        gavel(c, icon / 100.0, 0, 0)
        + rect(x_rule, 12, 1.2, 70, c["sub"], 0, ' opacity="0.55"')
        + p(d1, c["fg"])
        + p(d2, c["sub"])
    )
    return svg(x_text + w1 + 6, icon + 2, body, "Abogados Remates Judiciales")


def logo_c(mode="color", accent="verde"):
    """C · Tipográfico: bloque de tres líneas del mismo ancho."""
    c = palette(mode, accent)
    x = 4.0
    size1, track1 = 70.0, 0.10
    w = SERIF.width("REMATES", size1, track1)
    size2 = SERIF.fit_size("JUDICIALES", w, track1)
    cap1 = SERIF.bounds("R", size1)[3]
    cap2 = SERIF.bounds("J", size2)[3]
    y1 = 6 + cap1
    y2 = y1 + 24 + cap2
    y_sub = y2 + 34
    d1, _ = SERIF.path("REMATES", size1, x, y1, track1)
    d2, _ = SERIF.path("JUDICIALES", size2, x, y2, track1)
    size3 = 14.0
    d3, w3 = SANS_M.path("ABOGADOS", size3, x + 1, y_sub, 0.46)
    # la línea de acento ocupa el ancho que deja la palabra
    x_rule = x + w3 + 20
    body = (
        p(d1, c["fg"])
        + p(d2, c["fg"])
        + p(d3, c["sub"])
        + rect(x_rule, y_sub - 6.4, x + w - x_rule - 2, 2.6, c["acc"])
    )
    return svg(w + 8, y_sub + 10, body, "Abogados Remates Judiciales")


def icon_a(mode="color", accent="verde"):
    c = palette(mode, accent)
    mono, mw, mh = monogram_rj(c, 150)
    side = max(mw, mh) + 24
    body = f'<g transform="translate({num((side - mw) / 2)} {num((side - mh) / 2)})">{mono}</g>'
    return svg(side, side, body, "Remates Judiciales")


def icon_b(mode="color", accent="verde"):
    c = palette(mode, accent)
    return svg(108, 108, gavel(c, 1.0, 3, 2), "Remates Judiciales")


def icon_c(mode="negativo", accent="verde"):
    """Avatar: RJ en caja azul con línea de acento (redes y WhatsApp)."""
    c = palette(mode, accent)
    side = 120.0
    size, track = 58.0, 0.06
    cap = SERIF.bounds("R", size)[3]
    base = 28 + cap
    d, w = SERIF.path("RJ", size, side / 2, base, track, "middle")
    body = (
        rect(0, 0, side, side, c["bg"], 18)
        + p(d, c["fg"])
        + rect(side / 2 - w / 2 + 2, base + 16, 40, 3.6, c["acc"])
    )
    return svg(side, side, body, "Remates Judiciales")


def endorsement(mode="color", accent="verde"):
    """Logo B con la línea de respaldo del estudio."""
    c = palette(mode, accent)
    inner = logo_b(mode, accent)
    vb = inner.split('viewBox="0 0 ')[1].split('"')[0].split()
    w, h = float(vb[0]), float(vb[1])
    body = inner.split("</title>")[1].rsplit("</svg>", 1)[0]
    d1, w1 = SANS_M.path("CON EL RESPALDO DE", 8.6, 0, 0, 0.30)
    d2, w2 = SERIF.path("CÁCERES & CAMIRUAGA", 13.0, 0, 0, 0.20)
    y = h + 28
    x = 130.0
    line = (
        rect(x, h + 6, w - x - 6, 0.8, c["sub"], 0, ' opacity="0.45"')
        + f'<g transform="translate({num(x)} {num(y)})">{p(d1, c["sub"])}</g>'
        + f'<g transform="translate({num(x + w1 + 10)} {num(y + 0.6)})">{p(d2, c["fg"])}</g>'
    )
    del w2
    return svg(w, y + 10, body + line, "Abogados Remates Judiciales, con el respaldo de Cáceres & Camiruaga")


# ---------------------------------------------------------------- salida

def data_uri(rel, max_w):
    im = Image.open(os.path.join(BRAND, rel)).convert("RGBA")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def main():
    out = os.path.join(HERE, "logos")
    os.makedirs(out, exist_ok=True)
    files = {}
    for key, fn in (("a", logo_a), ("b", logo_b), ("c", logo_c)):
        for mode in ("color", "negativo", "mono"):
            files[f"{key}-{mode}"] = fn(mode)
    files["a-icono"] = icon_a()
    files["b-icono"] = icon_b()
    files["c-icono"] = icon_c()
    files["b-con-respaldo"] = endorsement()
    for name, content in files.items():
        with open(os.path.join(out, f"remates-judiciales-{name}.svg"), "w", encoding="utf-8") as fh:
            fh.write(content)

    slots = dict(files)
    slots["a-icono-neg"] = icon_a("negativo")
    slots["b-icono-neg"] = icon_b("negativo")
    for acc in ACCENTS:
        slots[f"b-color-{acc}"] = logo_b("color", acc)
        slots[f"b-negativo-{acc}"] = logo_b("negativo", acc)
    slots["img-cc"] = data_uri("caceres-camiruaga/logo-1-color.png", 900)
    slots["img-cc-mono"] = data_uri("caceres-camiruaga/logo-3-monograma-color.png", 260)
    slots["img-ic"] = data_uri("inversiones-caceres/logo-2-color.png", 900)

    with open(os.path.join(HERE, "propuesta.template.html"), encoding="utf-8") as fh:
        html = fh.read()
    for key, value in slots.items():
        html = html.replace("{{" + key + "}}", value)
    if "{{" in html:
        missing = sorted({html[i + 2:html.index("}}", i)] for i in range(len(html)) if html.startswith("{{", i)})
        raise SystemExit(f"Faltan valores en la plantilla: {missing}")
    with open(os.path.join(HERE, "propuesta.html"), "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"{len(files)} logos y propuesta.html generados")


if __name__ == "__main__":
    main()

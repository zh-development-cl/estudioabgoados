"""Genera los logos propuestos para Abogados Remates Judiciales y la página
de propuesta. Todo el texto de los logos queda convertido a trazos.

Uso:  python3 brand/remates-judiciales/build.py
Requiere: fonttools, brotli, uharfbuzz, skia-pathops, pillow.
"""
import base64
import glob
import io
import math
import os
from functools import reduce

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from pathops import Path, PathOp, op
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BRAND = os.path.dirname(HERE)

NAVY = "#222B53"   # azul compartido por las marcas del grupo
GREY = "#6E6D6D"   # gris del texto secundario en los logos actuales

# Acentos candidatos para la marca nueva: (sobre blanco, sobre azul)
ACCENTS = {
    "verde": ("#1F7A6B", "#5CC2AE"),
    "burdeos": ("#8C2F3C", "#E08D99"),
    "acero": ("#3A6EA5", "#8DB4DC"),
}
NAME = "Abogados Remates Judiciales"


# ------------------------------------------------------------ geometría

K = 0.5522847498


def num(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def rrect(x, y, w, h, r=0.0):
    p = Path()
    if r <= 0:
        p.moveTo(x, y); p.lineTo(x + w, y); p.lineTo(x + w, y + h); p.lineTo(x, y + h); p.close()
        return p
    k = r * K
    p.moveTo(x + r, y)
    p.lineTo(x + w - r, y); p.cubicTo(x + w - r + k, y, x + w, y + r - k, x + w, y + r)
    p.lineTo(x + w, y + h - r); p.cubicTo(x + w, y + h - r + k, x + w - r + k, y + h, x + w - r, y + h)
    p.lineTo(x + r, y + h); p.cubicTo(x + r - k, y + h, x, y + h - r + k, x, y + h - r)
    p.lineTo(x, y + r); p.cubicTo(x, y + r - k, x + r - k, y, x + r, y)
    p.close()
    return p


def circle(cx, cy, r):
    k = r * K
    p = Path()
    p.moveTo(cx + r, cy)
    p.cubicTo(cx + r, cy + k, cx + k, cy + r, cx, cy + r)
    p.cubicTo(cx - k, cy + r, cx - r, cy + k, cx - r, cy)
    p.cubicTo(cx - r, cy - k, cx - k, cy - r, cx, cy - r)
    p.cubicTo(cx + k, cy - r, cx + r, cy - k, cx + r, cy)
    p.close()
    return p


def union(*paths):
    return reduce(lambda a, c: op(a, c, PathOp.UNION), paths)


def minus(a, *others):
    return reduce(lambda x, c: op(x, c, PathOp.DIFFERENCE), others, a)


def inter(a, c):
    return op(a, c, PathOp.INTERSECTION)


def affine(p, a=1.0, b=0.0, c=0.0, d=1.0, e=0.0, f=0.0):
    return p.transform(a, b, c, d, e, f)


def rotate(p, deg):
    t = math.radians(deg)
    return affine(p, math.cos(t), math.sin(t), -math.sin(t), math.cos(t))


def place(p, x, y, s=1.0):
    return affine(p, s, 0, 0, s, x, y)


def d_of(p):
    pen = SVGPathPen(None, ntos=num)
    p.draw(pen)
    return pen.getCommands()


def bbox(paths):
    bs = [p.bounds for p in paths]
    return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))


# ------------------------------------------------------------ tipografía

class Face:
    """Fuente con kerning real (HarfBuzz) y salida como trazos."""

    def __init__(self, path):
        self.font = TTFont(path)
        self.glyphs = self.font.getGlyphSet()
        self.order = self.font.getGlyphOrder()
        self.upm = self.font["head"].unitsPerEm
        raw = TTFont(path)
        raw.flavor = None
        buf = io.BytesIO()
        raw.save(buf)
        self.hb = hb.Font(hb.Face(buf.getvalue()))

    def shape(self, text, smcp=False):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"kern": True, "liga": False, "smcp": smcp})
        return [(self.order[i.codepoint], pos.x_advance) for i, pos in zip(buf.glyph_infos, buf.glyph_positions)]

    def width(self, text, size, track=0.0, smcp=False):
        s = size / self.upm
        return sum(adv for _, adv in self.shape(text, smcp)) * s + track * size * (len(text) - 1)

    def cap(self, size):
        return self.font["OS/2"].sCapHeight * size / self.upm

    def text(self, text, size, x, y, track=0.0, anchor="start", smcp=False):
        """Texto como Path. (x, y) es la línea base. Devuelve (path, ancho)."""
        w = self.width(text, size, track, smcp)
        if anchor == "middle":
            x -= w / 2
        elif anchor == "end":
            x -= w
        s = size / self.upm
        out = Path()
        for name, adv in self.shape(text, smcp):
            self.glyphs[name].draw(TransformPen(out.getPen(), (s, 0, 0, -s, x, y)))
            x += adv * s + track * size
        return out, w

    def glyph(self, ch):
        """Glifo en unidades de fuente, con el eje y hacia abajo y la línea base en 0."""
        name = self.font.getBestCmap()[ord(ch)]
        out = Path()
        self.glyphs[name].draw(TransformPen(out.getPen(), (1, 0, 0, -1, 0, 0)))
        return out


SERIF = Face(os.path.join(HERE, "fonts", "texgyrepagella-regular.otf"))
SANS = Face(os.path.join(HERE, "fonts", "montserrat-latin-500-normal.woff2"))


# ------------------------------------------------------------ símbolos

def period(size, x_after):
    """Punto final en color: un círculo apoyado en la línea base, tras la última letra."""
    r = size * 0.08
    return circle(x_after + size * 0.05 + r, -r, r)


def gavel_head(cx, length, h, cap_w, cap_h, gap, base=0.0):
    """Cabeza de martillo de perfil, con la base plana en y = `base`: un cuerpo y
    dos extremos más altos, redondeados solo arriba, como un tambor."""
    x0, x1 = cx - length / 2, cx + length / 2
    rad = min(cap_w, cap_h) * 0.45

    def cap(x):  # esquinas de arriba redondeadas, base recta
        return union(rrect(x, base - cap_h, cap_w, cap_h, rad),
                     rrect(x, base - cap_h / 2, cap_w, cap_h / 2))

    body = rrect(x0 + cap_w + gap, base - h, length - 2 * (cap_w + gap), h)
    return union(body, cap(x0), cap(x1 - cap_w))


def mark_r(height=100.0):
    """La R de martillo: el asta de la R es el mango y su pie, la cabeza de un
    martillo de remate. Un solo color. La base del martillo queda a la misma
    altura que el pie de la pata inclinada.

    Devuelve la letra con su borde superior en y = 0, lista para ubicar.
    """
    g = SERIF.glyph("R")
    base = bbox([g])[3]                      # pie de la pata, con su leve sobrepaso
    length, h, cap_w, cap_h, gap = 292.0, 52.0, 40.0, 62.0, 8.0
    stem_center = 168.5                      # centro del asta de la R de Pagella
    # La pata inclinada termina recta en la línea de base, sin el pie curvo, para
    # que el único «pie» de la letra sea el martillo. Bordes medidos en Pagella:
    # a 100 unidades de altura la pata va de x 451,1 a 572,3 y baja con
    # pendientes de 0,745 (borde izquierdo) y 0,767 (borde derecho).
    def leg_x(y_up, x100, slope):
        return x100 + (100 - y_up) * slope
    leg = Path()
    pen = leg.getPen()
    pen.moveTo((leg_x(101, 451.1, 0.745), -101))
    pen.lineTo((leg_x(101, 572.3, 0.767), -101))
    pen.lineTo((leg_x(-base, 572.3, 0.767), base))
    pen.lineTo((leg_x(-base, 451.1, 0.745), base))
    pen.closePath()
    g = union(minus(g, rrect(420, -100, 400, 120)), leg)
    # el asta baja hasta meterse un poco en la cabeza, para que no quede ranura
    letter = minus(g, rrect(0, base - h + 2, 330, h + 20))
    letter = union(letter, gavel_head(stem_center, length, h, cap_w, cap_h, gap, base))
    x0, y0, x1, y1 = bbox([letter])
    s = height / (y1 - y0)
    letter = place(letter, -x0 * s, -y0 * s, s)
    return {"main": letter, "accent": Path(), "w": (x1 - x0) * s, "h": height}


def arc_text(face, text, size, radius, center_deg, track=0.0, bottom=False):
    """Texto sobre un círculo de centro (0, 0). center_deg: 90 arriba, 270 abajo.
    Arriba la base mira al centro; abajo el texto queda derecho."""
    shaped = face.shape(text)
    s = size / face.upm
    steps = [adv * s + track * size for _, adv in shaped]
    span = (sum(steps) - track * size) / radius
    th = math.radians(center_deg) + (-span / 2 if bottom else span / 2)
    out = Path()
    for (name, adv), step in zip(shaped, steps):
        w = adv * s
        mid = th + (w / 2) / radius if bottom else th - (w / 2) / radius
        g = Path()
        face.glyphs[name].draw(TransformPen(g.getPen(), (s, 0, 0, -s, -w / 2, 0)))
        ct, st = math.cos(mid), math.sin(mid)
        px, py = radius * ct, -radius * st
        m = (-st, -ct, ct, -st, px, py) if bottom else (st, ct, -ct, st, px, py)
        g.transform(*m).draw(out.getPen())
        th = th + step / radius if bottom else th - step / radius
    return out


def mark_punto(height=100.0):
    """R con punto final: el ícono del concepto «Punto final»."""
    size = height / 0.692
    letter, w = SERIF.text("R", size, 0, height)
    dot = place(period(size, w), 0, height)
    x0, y0, x1, y1 = bbox([letter, dot])
    letter, dot = place(letter, -x0, -y0), place(dot, -x0, -y0)
    return {"main": letter, "accent": dot, "w": x1 - x0, "h": y1 - y0}


MARKS = {"punto": mark_punto, "r": mark_r}


# ------------------------------------------------------------ armado

def palette(mode, accent):
    on_white, on_navy = ACCENTS[accent]
    if mode == "color":
        return dict(fg=NAVY, sub=GREY, acc=on_white, bg="#FFFFFF", rule="#B9BED0")
    if mode == "negativo":
        return dict(fg="#FFFFFF", sub="#C9CDDD", acc=on_navy, bg=NAVY, rule="#5A6290")
    if mode == "mono":
        return dict(fg="#111111", sub="#111111", acc="#111111", bg="#FFFFFF", rule="#111111")
    raise ValueError(mode)


class Art:
    """Lienzo mínimo: acumula trazos por color y entrega un SVG ajustado."""

    def __init__(self):
        self.items = []

    def add(self, path, fill, opacity=None):
        if not list(path.contours):
            return
        self.items.append((path, fill, opacity))

    def svg(self, pad=0.0, title=NAME, bg=None, radius=0.0, box=None):
        x0, y0, x1, y1 = box or bbox([p for p, _, _ in self.items])
        x0 -= pad; y0 -= pad; x1 += pad; y1 += pad
        w, h = x1 - x0, y1 - y0
        body = ""
        if bg:
            rx = f' rx="{num(radius)}"' if radius else ""
            body += f'<rect x="{num(x0)}" y="{num(y0)}" width="{num(w)}" height="{num(h)}"{rx} fill="{bg}"/>'
        for p, fill, opacity in self.items:
            o = f' opacity="{opacity}"' if opacity else ""
            body += f'<path d="{d_of(p)}" fill="{fill}"{o}/>'
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{num(x0)} {num(y0)} {num(w)} {num(h)}" '
            f'role="img" aria-label="{title}"><title>{title}</title>{body}</svg>'
        )


SUB_SIZE, SUB_TRACK = 13.0, 0.55     # «ABOGADOS»


def endorsement(art, c, x, y, right):
    art.add(rrect(x, y - 22, right - x, 0.8), c["rule"])
    e1, _ = SANS.text("CON EL RESPALDO DE", 7.6, x, y, 0.3)
    e2, _ = SERIF.text("CÁCERES & CAMIRUAGA", 11.6, x, y + 17, 0.2)
    art.add(e1, c["sub"]); art.add(e2, c["fg"])


def punto_principal(mode="color", accent="verde", endorsed=False):
    """«Remates / Judiciales.» en dos líneas, con «ABOGADOS» debajo. Versión principal."""
    c = palette(mode, accent)
    size, lead = 72.0, 78.0
    art = Art()
    l1, _ = SERIF.text("Remates", size, 0, 0, 0.02)
    l2, w2 = SERIF.text("Judiciales", size, 0, lead, 0.02)
    art.add(l1, c["fg"]); art.add(l2, c["fg"])
    art.add(place(period(size, w2), 0, lead), c["acc"])
    sub, _ = SANS.text("ABOGADOS", 15.0, 2, lead + 44, 0.5)
    art.add(sub, c["sub"])
    if endorsed:
        endorsement(art, c, 2, lead + 42 + 44, w2 + 0.3 * size)
    return art.svg(pad=3)


def punto_horizontal(mode="color", accent="verde"):
    """«Remates Judiciales.» en una línea, para encabezados angostos."""
    c = palette(mode, accent)
    size = 60.0
    art = Art()
    t, w = SERIF.text("Remates Judiciales", size, 0, 0, 0.0)
    art.add(t, c["fg"])
    art.add(period(size, w), c["acc"])
    sub, _ = SANS.text("ABOGADOS", 15.5, 2, 38, 0.5)
    art.add(sub, c["sub"])
    return art.svg(pad=3)


def r_horizontal(mode="color", accent="verde", endorsed=False):
    """R de martillo, línea divisoria, nombre en versalitas y «ABOGADOS» con una
    línea corta de acento. Versión principal del concepto."""
    c = palette(mode, accent)
    m = mark_r(150.0)
    art = Art()
    art.add(m["main"], c["fg"])
    x_rule = m["w"] + 24
    art.add(rrect(x_rule, 4, 1.4, 146), c["rule"])
    x = x_rule + 26
    size = 64.0
    l1, w1 = SERIF.text("Remates", size, x, 56, 0.04, smcp=True)
    l2, w2 = SERIF.text("Judiciales", size, x, 114, 0.04, smcp=True)
    art.add(l1, c["fg"]); art.add(l2, c["fg"])
    art.add(rrect(x + 2, 145.2, 34, 2.6), c["acc"])
    sub, _ = SANS.text("ABOGADOS", SUB_SIZE, x + 50, 151, SUB_TRACK)
    art.add(sub, c["sub"])
    if endorsed:
        endorsement(art, c, x + 2, 150 + 44, x + max(w1, w2))
    return art.svg(pad=3)


def r_insignia(accent="verde"):
    """La R blanca dentro de un cuadro azul, con el nombre al lado."""
    c = palette("color", accent)
    side = 160.0
    m = mark_r(92.0)
    art = Art()
    art.add(rrect(0, 0, side, side, 14), NAVY)
    art.add(place(m["main"], (side - m["w"]) / 2 + 2, (side - m["h"]) / 2), "#FFFFFF")
    x = side + 30
    size = 62.0
    l1, _ = SERIF.text("Remates", size, x, 60, 0.04, smcp=True)
    l2, _ = SERIF.text("Judiciales", size, x, 117, 0.04, smcp=True)
    art.add(l1, c["fg"]); art.add(l2, c["fg"])
    art.add(rrect(x + 2, 149.2, 34, 2.6), c["acc"])
    sub, _ = SANS.text("ABOGADOS", SUB_SIZE, x + 50, 155, SUB_TRACK)
    art.add(sub, c["sub"])
    return art.svg(pad=3)


def r_vertical(mode="color", accent="verde"):
    """R de martillo arriba y el nombre en versalitas centrado."""
    c = palette(mode, accent)
    m = mark_r(136.0)
    size = 52.0
    w = SERIF.width("Remates Judiciales", size, 0.06, smcp=True)
    cx = w / 2
    art = Art()
    art.add(place(m["main"], cx - m["w"] / 2 + 4, 0), c["fg"])
    y = m["h"] + 60
    t, _ = SERIF.text("Remates Judiciales", size, cx, y, 0.06, "middle", smcp=True)
    art.add(t, c["fg"])
    sub, ws = SANS.text("ABOGADOS", SUB_SIZE, cx, y + 34, SUB_TRACK, "middle")
    art.add(sub, c["sub"])
    cap = SANS.cap(SUB_SIZE)
    for bx in (cx - ws / 2 - 40, cx + ws / 2 + 14):
        art.add(rrect(bx, y + 34 - cap / 2 - 1.3, 26, 2.6), c["acc"])
    return art.svg(pad=3)


def r_sello(mode="color", accent="verde"):
    """Sello circular: para documentos, firmas de correo y presentaciones."""
    c = palette(mode, accent)
    R0 = 150.0
    art = Art()
    art.add(minus(circle(0, 0, R0), circle(0, 0, R0 - 3.2)), c["fg"])
    art.add(minus(circle(0, 0, R0 - 44), circle(0, 0, R0 - 45.6)), c["fg"])
    art.add(arc_text(SANS, "REMATES JUDICIALES", 15.5, R0 - 29, 90, 0.34), c["fg"])
    art.add(arc_text(SANS, "ABOGADOS", 15.5, R0 - 16, 270, 0.5, bottom=True), c["fg"])
    m = mark_r(124.0)
    art.add(place(m["main"], -m["w"] / 2 + 4, -m["h"] / 2 - 2), c["fg"])
    art.add(union(circle(-(R0 - 22), 6, 3.2), circle(R0 - 22, 6, 3.2)), c["acc"])
    return art.svg(pad=2, title="Remates Judiciales · Abogados")


def symbol(kind, mode="color", accent="verde"):
    c = palette(mode, accent)
    m = MARKS[kind](100.0)
    art = Art()
    art.add(m["main"], c["fg"])
    art.add(m["accent"], c["acc"])
    return art.svg(pad=2)


def avatar(kind, accent="verde", shape="square"):
    """Ícono para redes, WhatsApp y pestaña del navegador."""
    c = palette("negativo", accent)
    side = 200.0
    target = {"punto": 98.0, "r": 108.0}[kind]
    m = MARKS[kind](target)
    x = (side - m["w"]) / 2
    y = (side - m["h"]) / 2
    if kind == "punto":
        x -= 3
    art = Art()
    art.add(circle(side / 2, side / 2, side / 2) if shape == "circle" else rrect(0, 0, side, side, 44), c["bg"])
    art.add(place(m["main"], x, y), c["fg"])
    art.add(place(m["accent"], x, y), c["acc"])
    return art.svg(box=(0, 0, side, side), title="Remates Judiciales")


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
    for old in glob.glob(os.path.join(out, "*.svg")):
        os.remove(old)

    files = {}
    for mode in ("color", "negativo", "mono"):
        files[f"punto-principal-{mode}"] = punto_principal(mode)
        files[f"punto-horizontal-{mode}"] = punto_horizontal(mode)
        files[f"r-horizontal-{mode}"] = r_horizontal(mode)
        files[f"r-vertical-{mode}"] = r_vertical(mode)
        files[f"r-sello-{mode}"] = r_sello(mode)
        for kind in MARKS:
            files[f"{kind}-simbolo-{mode}"] = symbol(kind, mode)
    for kind in MARKS:
        files[f"{kind}-avatar"] = avatar(kind)
        files[f"{kind}-avatar-circular"] = avatar(kind, shape="circle")
    files["punto-principal-con-respaldo"] = punto_principal(endorsed=True)
    files["r-horizontal-con-respaldo"] = r_horizontal(endorsed=True)
    files["r-insignia"] = r_insignia()
    for name, content in files.items():
        with open(os.path.join(out, f"remates-judiciales-{name}.svg"), "w", encoding="utf-8") as fh:
            fh.write(content)

    slots = dict(files)
    for acc in ACCENTS:
        slots[f"punto-principal-color-{acc}"] = punto_principal("color", acc)
        slots[f"r-horizontal-color-{acc}"] = r_horizontal("color", acc)
    slots["img-cc"] = data_uri("caceres-camiruaga/logo-1-color.png", 900)
    slots["img-cc-mono"] = data_uri("caceres-camiruaga/logo-3-monograma-color.png", 360)
    slots["img-ic"] = data_uri("inversiones-caceres/logo-2-color.png", 900)
    slots["img-ic-mono"] = data_uri("inversiones-caceres/logo-3-monograma-color.png", 360)
    ref = os.path.join(HERE, "referencias", "estudios.png")
    if os.path.exists(ref):
        slots["img-ref-estudios"] = data_uri("remates-judiciales/referencias/estudios.png", 870)

    with open(os.path.join(HERE, "propuesta.template.html"), encoding="utf-8") as fh:
        html = fh.read()
    for key in sorted(slots, key=len, reverse=True):
        html = html.replace("{{" + key + "}}", slots[key])
    if "{{" in html:
        i = html.index("{{")
        raise SystemExit(f"Falta un valor en la plantilla: {html[i:html.index('}}', i) + 2]}")
    with open(os.path.join(HERE, "propuesta.html"), "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"{len(files)} logos y propuesta.html generados")


if __name__ == "__main__":
    main()

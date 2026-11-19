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

    def shape(self, text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"kern": True, "liga": False})
        return [(self.order[i.codepoint], pos.x_advance) for i, pos in zip(buf.glyph_infos, buf.glyph_positions)]

    def width(self, text, size, track=0.0):
        s = size / self.upm
        return sum(adv for _, adv in self.shape(text)) * s + track * size * (len(text) - 1)

    def cap(self, size):
        return self.font["OS/2"].sCapHeight * size / self.upm

    def text(self, text, size, x, y, track=0.0, anchor="start"):
        """Texto como Path. (x, y) es la línea base. Devuelve (path, ancho)."""
        w = self.width(text, size, track)
        if anchor == "middle":
            x -= w / 2
        elif anchor == "end":
            x -= w
        s = size / self.upm
        out = Path()
        for name, adv in self.shape(text):
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

def mark_r(height=100.0):
    """La R que remata: la pata de la R es el mango de un martillo de remate.

    Devuelve las piezas con la R apoyada en y = `height` (línea base) y su
    borde superior en y = 0; la cabeza del martillo baja un poco de la base.
    """
    g = SERIF.glyph("R")
    # La pata de la R de Pagella: eje y ángulo medidos sobre el propio glifo.
    theta = math.atan2(200.0, 151.0)
    ax, ay = 436.5, -200.0
    ca, sa = math.cos(theta), math.sin(theta)

    def local(p):  # marco local: x a lo largo de la pata, y transversal
        return affine(p, ca, sa, -sa, ca, ax, ay)

    length, thick = 292.0, 122.0      # cabeza: largo (transversal) y grosor
    cap, gap, inset = 50.0, 10.0, 7.0
    drop = 55.0                       # cuánto baja la cabeza de la línea base
    t0 = (200.0 + drop - (length / 2) * ca) / sa - thick
    # Se corta la pata original donde empieza la cabeza; el pie del asta no se toca.
    beyond = inter(local(rrect(t0 + inset + 1, -500, 1200, 1000)), rrect(300, -600, 1200, 1200))
    letter = minus(g, beyond)
    head = union(
        rrect(t0, -length / 2, thick, cap, 10),
        rrect(t0, length / 2 - cap, thick, cap, 10),
        rrect(t0 + inset, -length / 2 + cap + gap, thick - 2 * inset, length - 2 * (cap + gap), 3),
    )
    head = local(head)
    cap_h = 692.0
    s = height / cap_h
    x0 = bbox([letter])[0]
    letter = place(letter, -x0 * s, height, s)
    head = place(head, -x0 * s, height, s)
    x_min, y_min, x_max, y_max = bbox([letter, head])
    return {"main": letter, "accent": head, "w": x_max, "h": y_max, "base": height}


def mark_key(height=100.0):
    """El martillo que entrega la llave: un martillo cuyo mango termina en llave."""
    hw, hh, cap, gap = 84.0, 36.0, 14.0, 3.6
    sw, shaft = 10.0, 68.0
    top = hh / 2
    end = top + shaft
    head = union(
        rrect(-hw / 2, -hh / 2, cap, hh, 3),
        rrect(hw / 2 - cap, -hh / 2, cap, hh, 3),
        rrect(-hw / 2 + cap + gap, -hh / 2 + 1.5, hw - 2 * (cap + gap), hh - 3, 1.2),
    )
    body = union(
        head,
        rrect(-sw / 2 - 3.5, top - 1.5, sw + 7, 7.5, 1.2),
        rrect(-sw / 2, top, sw, shaft - sw / 2),
        rrect(-sw / 2, end - sw, sw, sw, sw / 2),
    )
    teeth = union(
        rrect(-sw / 2 - 17, end - 34, 18, 10, 1),
        rrect(-sw / 2 - 12, end - 19, 13, 10, 1),
    )
    body, teeth = rotate(body, -45), rotate(teeth, -45)
    x0, y0, x1, y1 = bbox([body, teeth])
    s = height / (y1 - y0)
    body = place(body, -x0 * s, -y0 * s, s)
    teeth = place(teeth, -x0 * s, -y0 * s, s)
    return {"main": body, "accent": teeth, "w": (x1 - x0) * s, "h": height, "base": height}


MARKS = {"r": mark_r, "llave": mark_key}


# ------------------------------------------------------------ armado

def palette(mode, accent):
    on_white, on_navy = ACCENTS[accent]
    if mode == "color":
        return dict(fg=NAVY, sub=GREY, acc=on_white, bg="#FFFFFF")
    if mode == "negativo":
        return dict(fg="#FFFFFF", sub="#C9CDDD", acc=on_navy, bg=NAVY)
    if mode == "mono":
        return dict(fg="#111111", sub="#111111", acc="#111111", bg="#FFFFFF")
    raise ValueError(mode)


class Art:
    """Lienzo mínimo: acumula trazos por color y entrega un SVG ajustado."""

    def __init__(self):
        self.items = []

    def add(self, path, fill, opacity=None):
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


def symbol(kind, mode="color", accent="verde"):
    c = palette(mode, accent)
    m = MARKS[kind](100.0)
    art = Art()
    art.add(m["main"], c["fg"])
    art.add(m["accent"], c["acc"])
    return art.svg(pad=2)


def horizontal(kind, mode="color", accent="verde", endorsed=False):
    """Símbolo a la izquierda y el nombre en dos líneas, como el logo de inversiones."""
    c = palette(mode, accent)
    m = MARKS[kind](100.0)
    art = Art()
    art.add(m["main"], c["fg"])
    art.add(m["accent"], c["acc"])
    x_rule = m["w"] + 17
    art.add(rrect(x_rule, 0, 1.1, 100), c["sub"], 0.5)
    x = x_rule + 19
    size, track = 33.0, 0.2
    cap = SERIF.cap(size)
    l1, w1 = SERIF.text("REMATES", size, x, cap, track)
    l2, w2 = SERIF.text("JUDICIALES", size, x, cap * 2 + 15.5, track)
    art.add(l1, c["fg"]); art.add(l2, c["fg"])
    y_rule = cap * 2 + 15.5 + 14
    art.add(rrect(x + 1, y_rule, 30, 2.2), c["acc"])
    sub, _ = SANS.text("ABOGADOS", 12.4, x + 1, 100, 0.46)
    art.add(sub, c["sub"])
    if endorsed:
        y = 100 + 36
        right = x + max(w1, w2)
        art.add(rrect(x + 1, y - 20, right - x - 1, 0.8), c["sub"], 0.45)
        e1, we = SANS.text("CON EL RESPALDO DE", 7.4, x + 1, y, 0.3)
        e2, _ = SERIF.text("CÁCERES & CAMIRUAGA", 11.4, x + 1, y + 17, 0.2)
        art.add(e1, c["sub"]); art.add(e2, c["fg"])
        del we
    return art.svg(pad=3)


def vertical(kind, mode="color", accent="verde"):
    """Símbolo arriba, nombre en una línea y «| ABOGADOS |», como el logo del estudio."""
    c = palette(mode, accent)
    m = MARKS[kind](112.0)
    size, track = 29.0, 0.24
    w = SERIF.width("REMATES JUDICIALES", size, track)
    cx = w / 2
    art = Art()
    art.add(place(m["main"], cx - m["w"] / 2, 0), c["fg"])
    art.add(place(m["accent"], cx - m["w"] / 2, 0), c["acc"])
    y = m["h"] + 46
    name, _ = SERIF.text("REMATES JUDICIALES", size, cx, y, track, "middle")
    art.add(name, c["fg"])
    sub_size = 12.6
    y2 = y + 31
    sub, ws = SANS.text("ABOGADOS", sub_size, cx, y2, 0.44, "middle")
    art.add(sub, c["sub"])
    cap = SANS.cap(sub_size)
    bar_h = cap + 9.5
    for bx in (cx - ws / 2 - 13.5, cx + ws / 2 + 12):
        art.add(rrect(bx, y2 - cap - 4.75, 1.5, bar_h), c["acc"])
    return art.svg(pad=3)


def avatar(kind, accent="verde", shape="square"):
    """Ícono para redes, WhatsApp y pestaña del navegador."""
    c = palette("negativo", accent)
    side = 200.0
    target = 104.0 if kind == "r" else 118.0
    m = MARKS[kind](target)
    x = (side - m["w"]) / 2
    y = (side - m["h"]) / 2
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
    for kind in MARKS:
        for mode in ("color", "negativo", "mono"):
            files[f"{kind}-simbolo-{mode}"] = symbol(kind, mode)
            files[f"{kind}-horizontal-{mode}"] = horizontal(kind, mode)
            files[f"{kind}-vertical-{mode}"] = vertical(kind, mode)
        files[f"{kind}-avatar"] = avatar(kind)
        files[f"{kind}-avatar-circular"] = avatar(kind, shape="circle")
    files["r-horizontal-con-respaldo"] = horizontal("r", endorsed=True)
    for name, content in files.items():
        with open(os.path.join(out, f"remates-judiciales-{name}.svg"), "w", encoding="utf-8") as fh:
            fh.write(content)

    slots = dict(files)
    for acc in ACCENTS:
        slots[f"r-horizontal-color-{acc}"] = horizontal("r", "color", acc)
        slots[f"r-avatar-{acc}"] = avatar("r", acc)
    slots["img-cc"] = data_uri("caceres-camiruaga/logo-1-color.png", 900)
    slots["img-cc-mono"] = data_uri("caceres-camiruaga/logo-3-monograma-color.png", 360)
    slots["img-ic"] = data_uri("inversiones-caceres/logo-2-color.png", 900)
    slots["img-ic-mono"] = data_uri("inversiones-caceres/logo-3-monograma-color.png", 360)

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

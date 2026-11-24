"""Arma las páginas del sitio en public/: HTML, datos estructurados, sitemap,
robots.txt y llms.txt.

Uso:  python3 sites/abogadosrematesjudiciales/tools/build_site.py
(Antes, una vez: tools/build_assets.py para logos, íconos y el plano.)
"""
import html
import json
import os
import re
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
PUB = os.path.join(SITE, "public")
CFG = json.load(open(os.path.join(HERE, "site.json"), encoding="utf-8"))
INTRO = json.load(open(os.path.join(HERE, "intro-parts.json"), encoding="utf-8"))
PLAN = open(os.path.join(HERE, "plan.svg"), encoding="utf-8").read()
TODAY = date.today().isoformat()
D = CFG["dominio"]
ASSET_V = "1"   # súbelo al cambiar CSS o JS para renovar la caché

# ------------------------------------------------------------------ íconos

ICO = {
    "arrow": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M4 12h15M13 6l6 6-6 6"/></svg>',
    "wa": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2.2a9.7 9.7 0 0 0-8.4 14.6L2.3 21.8l5.1-1.3A9.7 9.7 0 1 0 12 2.2Zm0 17.7a8 8 0 0 1-4.1-1.1l-.3-.2-3 .8.8-2.9-.2-.3A8 8 0 1 1 12 19.9Zm4.4-6c-.2-.1-1.4-.7-1.7-.8-.2-.1-.4-.1-.5.1l-.8.9c-.1.2-.3.2-.5.1a6.6 6.6 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.5-.4h-.5a.9.9 0 0 0-.7.3 2.8 2.8 0 0 0-.9 2.1 4.9 4.9 0 0 0 1 2.6 11.2 11.2 0 0 0 4.3 3.8c1.6.7 2.2.7 3 .6a2.6 2.6 0 0 0 1.7-1.2 2.1 2.1 0 0 0 .2-1.2c-.1-.1-.2-.2-.5-.3Z"/></svg>',
    "phone": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A17 17 0 0 1 3 5a2 2 0 0 1 2-2Z"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M12 21s-7-6.2-7-12a7 7 0 0 1 14 0c0 5.8-7 12-7 12Z"/><circle cx="12" cy="9" r="2.5"/></svg>',
    "check": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="m8 12.5 2.7 2.7L16.5 9"/></svg>',
    "home": '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M7 22 24 8l17 14"/><path d="M11 19v20h26V19"/><path d="M20 39V28h8v11"/></svg>',
    "chart": '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M7 40h34"/><path d="M11 33l9-9 7 6 13-14"/><path d="M33 16h7v7"/></svg>',
    "build": '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M9 40V12l16-5v33M25 18l14 4v18M6 40h36"/><path d="M14 16v2M19 15v2M14 23v2M19 22v2M14 30v2M19 29v2M30 26v2M34 27v2M30 32v2M34 33v2"/></svg>',
}

# ------------------------------------------------------------------ marco común


def esc(s):
    return html.escape(s, quote=True)


def wa_link(text="Hola, quiero evaluar una propiedad en remate judicial."):
    from urllib.parse import quote
    return f"https://wa.me/{CFG['whatsapp']}?text={quote(text)}"


def head(title, desc, path, jsonld, og_type="website"):
    url = D + path
    ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in jsonld)
    return f"""<!doctype html>
<html lang="es-CL">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="theme-color" content="#222B53">
<meta property="og:type" content="{og_type}">
<meta property="og:locale" content="es_CL">
<meta property="og:site_name" content="{esc(CFG['nombre'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{D}/assets/img/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(CFG['nombre'])}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="preload" href="/assets/fonts/pagella-regular.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/montserrat-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/site.css?v={ASSET_V}">
<script>try{{if(!sessionStorage.getItem('arj-intro')&&!matchMedia('(prefers-reduced-motion: reduce)').matches&&document.documentElement.dataset.intro==='1')document.documentElement.classList.add('play-intro')}}catch(e){{}}</script>
{ld}
</head>"""


def intro_html():
    return f"""<div class="intro" aria-hidden="true">
  <div class="half top"></div><div class="half bot"></div>
  <div class="seam"></div><div class="ring"></div>
  <div class="stage"><svg viewBox="{INTRO['viewBox']}"><g class="mark"><path class="letter" d="{INTRO['letter']}"/><path class="head" d="{INTRO['head']}"/></g></svg></div>
  <div class="word"><b>Remates Judiciales</b><span>ABOGADOS</span></div>
  <div class="skip-hint">Toque para saltar</div>
</div>"""


NAV = [("/#servicios", "Servicios"), ("/#proceso", "Cómo trabajamos"), ("/#equipo", "Equipo"),
       ("/guia-remate-judicial/", "Guía"), ("/#preguntas", "Preguntas")]


def header():
    links = "".join(f'<a href="{h}">{t}</a>' for h, t in NAV)
    return f"""<a class="skip" href="#contenido">Ir al contenido</a>
<header class="site-head">
  <div class="wrap bar">
    <a class="brand" href="/" aria-label="{esc(CFG['nombre'])}, inicio">
      <img class="neg" src="/assets/img/logo-horizontal-negativo.svg" alt="" width="214" height="78">
      <img class="pos" src="/assets/img/logo-horizontal.svg" alt="" width="214" height="78">
    </a>
    <nav class="nav" id="menu" aria-label="Principal">{links}<a class="btn" href="/#contacto">Contacto</a></nav>
    <button class="menu-btn" aria-controls="menu" aria-expanded="false" aria-label="Abrir menú"><span></span><span></span><span></span></button>
  </div>
</header>"""


def footer():
    year = date.today().year
    return f"""<footer class="site-foot">
  <div class="wrap">
    <div class="foot-grid">
      <div>
        <img src="/assets/img/logo-horizontal-negativo.svg" alt="{esc(CFG['nombre'])}" width="220" height="80" loading="lazy">
        <p>Abogados especialistas en remates judiciales de inmuebles en Chile. Asesoría legal desde la revisión del expediente hasta la entrega de la propiedad.</p>
      </div>
      <div><h2 class="fh">Servicios</h2><ul>
        <li><a href="/#servicios">Análisis de remates</a></li>
        <li><a href="/#servicios">Estudio de títulos</a></li>
        <li><a href="/#servicios">Representación en la subasta</a></li>
        <li><a href="/#servicios">Inscripción y entrega</a></li>
      </ul></div>
      <div><h2 class="fh">Recursos</h2><ul>
        <li><a href="/guia-remate-judicial/">Guía: cómo comprar en remate</a></li>
        <li><a href="/#preguntas">Preguntas frecuentes</a></li>
        <li><a href="{CFG['estudio_aliado_url']}" rel="noopener">{esc(CFG['estudio_aliado'])}</a></li>
      </ul></div>
      <div><h2 class="fh">Contacto</h2><ul>
        <li><a href="tel:{CFG['telefono_href']}">{esc(CFG['telefono'])}</a></li>
        <li><a href="{wa_link()}" rel="noopener">WhatsApp</a></li>
        <li><a href="{CFG['mapa']}" rel="noopener">{esc(CFG['direccion'])}, {esc(CFG['comuna'])}</a></li>
      </ul></div>
    </div>
    <div class="foot-legal">
      <span>© {year} {esc(CFG['nombre'])}. Todos los derechos reservados.</span>
      <span><a href="/privacidad/">Política de privacidad</a></span>
    </div>
  </div>
</footer>
<a class="wa" href="{wa_link()}" rel="noopener" aria-label="Escribir por WhatsApp">{ICO['wa']}</a>
<script src="/assets/site.js?v={ASSET_V}" defer></script>"""


def page(path, title, desc, body, jsonld, intro=False, og_type="website"):
    attr = ' data-intro="1"' if intro else ""
    doc = head(title, desc, path, jsonld, og_type).replace('<html lang="es-CL">', f'<html lang="es-CL"{attr}>')
    doc += "\n<body>\n" + (intro_html() if intro else "") + header() + f'\n<main id="contenido">\n{body}\n</main>\n' + footer() + "\n</body>\n</html>\n"
    out = os.path.join(PUB, path.strip("/"), "index.html") if path != "/" else os.path.join(PUB, "index.html")
    if path.endswith(".html"):
        out = os.path.join(PUB, path.strip("/"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(doc)


# ------------------------------------------------------------------ contenido

SERVICES = [
    ("Análisis de la oportunidad", "Revisamos el expediente judicial, las bases del remate, el precio mínimo, la garantía y las condiciones de participación. Antes de ofrecer, usted sabe exactamente qué está comprando."),
    ("Estudio de títulos y gravámenes", "Analizamos la historia de la propiedad en el Conservador de Bienes Raíces: hipotecas, embargos, prohibiciones y otras cargas, y qué deudas pueden seguir al inmueble."),
    ("Estrategia y representación en la subasta", "Definimos con usted una postura máxima razonable, preparamos la garantía y lo representamos en la audiencia, presencial o por videoconferencia."),
    ("Adjudicación y escrituración", "Gestionamos la consignación del saldo dentro del plazo, el acta de remate y su reducción a escritura pública."),
    ("Inscripción y alzamientos", "Inscribimos el dominio a su nombre en el Conservador de Bienes Raíces y tramitamos el alzamiento de los gravámenes que correspondan."),
    ("Entrega material del inmueble", "Si la propiedad está ocupada, solicitamos al tribunal su entrega y la seguimos hasta que usted tenga las llaves."),
]

RISKS = [
    ("Deudas y gravámenes", "Hipotecas, embargos o prohibiciones que no siempre se alzan solos, y deudas que pueden seguir a la propiedad."),
    ("Propiedad ocupada", "Ocupantes que no entregan el inmueble, con plazos y costos que cambian el negocio."),
    ("Vicios del juicio o del título", "Errores en el procedimiento o en la historia registral que pueden poner en riesgo la adjudicación."),
    ("Plazos y garantías", "Una garantía mal rendida o un saldo fuera de plazo pueden significar perder el dinero depositado."),
]

STEPS = [
    ("Evaluación", "Nos envía el remate que le interesa y revisamos expediente, bases y títulos."),
    ("Informe y estrategia", "Le entregamos por escrito los riesgos, los costos y una postura recomendada."),
    ("Subasta", "Preparamos la garantía y lo representamos en la audiencia."),
    ("Adjudicación", "Consignamos el saldo y firmamos la escritura de adjudicación."),
    ("Inscripción y entrega", "Inscribimos a su nombre y gestionamos la entrega del inmueble."),
]

WHO = [
    ("home", "Personas que buscan su propiedad", "Para quienes quieren comprar una vivienda bajo el valor de mercado, con la seguridad de no equivocarse en su primera compra en remate.",
     ["Revisión completa antes de ofrecer", "Acompañamiento en la audiencia", "Gestión hasta la entrega de llaves"]),
    ("chart", "Inversionistas", "Para quienes compran propiedades como inversión y necesitan analizar oportunidades con rapidez y criterio legal.",
     ["Análisis de varias oportunidades", "Estimación de riesgos, plazos y costos", "Acompañamiento post adjudicación"]),
    ("build", "Empresas y fondos", "Para empresas y fondos de inversión que participan en remates de forma recurrente y requieren un equipo especializado.",
     ["Asesoría continua", "Estructuración de la compra", "Gestión de cartera de adjudicaciones"]),
]

PLEDGES = [
    ("Decide con información, por escrito", "Antes de cada remate le entregamos un análisis con los riesgos y los costos. Nada se decide de palabra."),
    ("Nunca manejamos su dinero", "La garantía y el saldo se depositan directamente a la orden del tribunal, a su nombre."),
    ("Un abogado responsable de su caso", "Sabe quién lleva su remate y puede preguntarle en cualquier momento cómo va."),
]

TEAM = [
    ("FC", "Felipe Cáceres Carreño", "Socio fundador", "Abogado de la Universidad Central de Chile y magíster en Derecho Inmobiliario y Registral. Juez partidor ante la Corte de Apelaciones de Santiago. Inició su carrera en estudios de títulos en el Conservador de Bienes Raíces de San Miguel."),
    ("JC", "José Pablo Camiruaga Zamorano", "Abogado · Gerente legal", "Dirige la estrategia legal de los casos y la coordinación con el estudio Cáceres & Camiruaga."),
    ("GF", "Giselle Farías Zenteno", "Abogada coordinadora", "Coordina la tramitación judicial de los remates y las adjudicaciones hasta su inscripción."),
    ("DF", "Denise Fonseca Cañete", "Abogada asociada", "Acompaña a inversionistas en la búsqueda, análisis y adjudicación de oportunidades."),
]

FAQ = [
    ("¿Qué es un remate judicial?",
     ["Es la venta pública de un bien, ordenada por un tribunal, normalmente dentro de un juicio en que se cobra una deuda. Con lo que se obtiene se paga al acreedor.",
      "La propiedad se adjudica a quien ofrece el mayor precio sobre el mínimo fijado en las bases del remate."]),
    ("¿Cualquier persona puede participar en un remate?",
     ["Sí. Pueden participar personas y empresas, siempre que cumplan las bases: rendir la garantía exigida y, cuando el remate es por videoconferencia, inscribirse previamente según lo que indique el tribunal."]),
    ("¿Cuánto hay que dejar de garantía?",
     ["La fijan las bases de cada remate. Con frecuencia es un porcentaje del precio mínimo, y se rinde en la forma que ellas indiquen, por ejemplo con un vale vista a la orden del tribunal.",
      "Si no se adjudica la propiedad, la garantía se devuelve. Si se adjudica y no se paga el saldo a tiempo, se puede perder."]),
    ("¿Se puede comprar en remate con crédito hipotecario?",
     ["Es posible en algunos casos, pero los plazos para pagar el saldo suelen ser cortos. Por eso el financiamiento debe estar conversado con el banco antes de ofrecer. Revisamos las bases para ver si su caso es viable."]),
    ("¿La propiedad queda libre de deudas?",
     ["No siempre. Algunos gravámenes se alzan con la adjudicación, pero otras deudas, como contribuciones o gastos comunes, pueden seguir a la propiedad. Las revisamos antes de que usted ofrezca."]),
    ("¿Qué pasa si la propiedad está ocupada?",
     ["Quien se adjudica la propiedad puede pedir al tribunal su entrega material, y si los ocupantes no la entregan, solicitar el auxilio de la fuerza pública. Lo evaluamos antes del remate, porque afecta los plazos y los costos."]),
    ("¿Cuánto demora todo el proceso?",
     ["Depende del tribunal, del Conservador de Bienes Raíces y de si la propiedad está ocupada. Desde la subasta hasta la inscripción suelen pasar varios meses. Le damos una estimación para su caso desde la primera evaluación."]),
    ("¿Cuánto cuesta la asesoría?",
     ["Cotizamos cada caso según el tipo de propiedad y su complejidad. Envíenos los datos del remate que le interesa y le respondemos con una propuesta."]),
]


def faq_html():
    items = "".join(
        f'<details class="reveal" style="--i:{i}"><summary>{esc(q)}<i aria-hidden="true"></i></summary><div class="ans">{"".join(f"<p>{esc(p)}</p>" for p in a)}</div></details>'
        for i, (q, a) in enumerate(FAQ))
    return f'<div class="faq-list">{items}</div>'


def contact_form():
    return f"""<form class="lead-form reveal" action="/api/contacto" method="post" novalidate>
  <div class="fgrid">
    <div class="field"><label for="f-nombre">Nombre</label><input id="f-nombre" name="nombre" autocomplete="name" required maxlength="120"></div>
    <div class="field"><label for="f-tel">Teléfono</label><input id="f-tel" name="telefono" type="tel" autocomplete="tel" required maxlength="40" placeholder="+56 9"></div>
    <div class="field full"><label for="f-email">Correo electrónico</label><input id="f-email" name="email" type="email" autocomplete="email" required maxlength="160"></div>
    <div class="field full"><fieldset><legend>Usted es</legend><div class="chips">
      <label><input type="radio" name="perfil" value="Persona" checked><span>Persona</span></label>
      <label><input type="radio" name="perfil" value="Inversionista"><span>Inversionista</span></label>
      <label><input type="radio" name="perfil" value="Empresa o fondo"><span>Empresa o fondo</span></label>
    </div></fieldset></div>
    <div class="field full"><label for="f-msg">¿Qué remate o propiedad le interesa?</label><textarea id="f-msg" name="mensaje" required maxlength="3000" placeholder="Comuna, tribunal, rol de la causa o el enlace del aviso, si lo tiene."></textarea></div>
    <div class="hp" aria-hidden="true"><label for="f-web">No completar</label><input id="f-web" name="web" tabindex="-1" autocomplete="off"></div>
    <p class="form-msg" role="status" aria-live="polite"></p>
  </div>
  <div class="form-foot">
    <small>Al enviar acepta nuestra <a href="/privacidad/">política de privacidad</a>. Sus datos solo se usan para responderle.</small>
    <button class="btn" type="submit">Enviar consulta {ICO['arrow']}</button>
  </div>
</form>"""


def org_jsonld():
    return {
        "@context": "https://schema.org",
        "@type": "LegalService",
        "@id": D + "/#organizacion",
        "name": CFG["nombre"],
        "alternateName": CFG["nombre_corto"],
        "url": D + "/",
        "logo": D + "/icon-512.png",
        "image": D + "/assets/img/og.png",
        "description": "Abogados especialistas en remates judiciales de inmuebles en Chile: análisis del expediente y de los títulos, representación en la subasta, adjudicación, inscripción y entrega de la propiedad.",
        "telephone": CFG["telefono"],
        "address": {"@type": "PostalAddress", "streetAddress": CFG["direccion"], "addressLocality": CFG["comuna"],
                    "addressRegion": CFG["region"], "addressCountry": CFG["pais"]},
        "areaServed": {"@type": "Country", "name": "Chile"},
        "knowsAbout": ["Remates judiciales", "Derecho inmobiliario", "Estudio de títulos", "Juicio ejecutivo", "Inscripción en el Conservador de Bienes Raíces"],
        "founder": {"@type": "Person", "name": "Felipe Cáceres Carreño", "jobTitle": "Socio fundador",
                    "alumniOf": "Universidad Central de Chile"},
        "employee": [{"@type": "Person", "name": n, "jobTitle": r} for _, n, r, _ in TEAM],
        "parentOrganization": {"@type": "LegalService", "name": CFG["estudio_aliado"], "url": CFG["estudio_aliado_url"]},
        "contactPoint": {"@type": "ContactPoint", "telephone": CFG["telefono"], "contactType": "customer service",
                         "areaServed": "CL", "availableLanguage": "es"},
    }


def home():
    services = "".join(
        f'<div class="service reveal" style="--i:{i % 3}"><span class="n">{i + 1:02d}</span><h3>{esc(t)}</h3><p>{esc(d)}</p></div>'
        for i, (t, d) in enumerate(SERVICES))
    risks = "".join(
        f'<div class="risk reveal" style="--i:{i}"><span class="n">{i + 1:02d}</span><h3>{esc(t)}</h3><p>{esc(d)}</p></div>'
        for i, (t, d) in enumerate(RISKS))
    steps = "".join(f'<li style="--i:{i}"><div><h3>{esc(t)}</h3><p>{esc(d)}</p></div></li>' for i, (t, d) in enumerate(STEPS))
    who = "".join(
        f'<article class="reveal" style="--i:{i}"><div class="ico">{ICO[ic]}</div><h3>{esc(t)}</h3><p>{esc(d)}</p><ul>{"".join(f"<li>{esc(x)}</li>" for x in items)}</ul></article>'
        for i, (ic, t, d, items) in enumerate(WHO))
    pledges = "".join(f'<li class="reveal" style="--i:{i}">{ICO["check"]}<div><b>{esc(t)}</b><span>{esc(d)}</span></div></li>' for i, (t, d) in enumerate(PLEDGES))
    team = "".join(
        f'<article class="person reveal" style="--i:{i}"><div class="ph" aria-hidden="true">{ini}</div><div class="tx"><h3>{esc(n)}</h3><p class="role">{esc(r)}</p><p>{esc(b)}</p></div></article>'
        for i, (ini, n, r, b) in enumerate(TEAM))

    body = f"""
<section class="hero on-dark" aria-labelledby="hero-title">
  <div class="plan">{PLAN}</div>
  <div class="wrap">
    <div class="hero-grid">
      <div>
        <p class="kicker rise" style="--i:0">Abogados especialistas en remates judiciales</p>
        <h1 id="hero-title" class="rise" style="--i:1">Compre en remate judicial con un abogado <em>de su lado.</em></h1>
        <p class="lead rise" style="--i:2">Revisamos el expediente, los títulos y los riesgos antes de que usted ofrezca. Lo representamos en la subasta y lo acompañamos hasta inscribir la propiedad a su nombre y recibir las llaves.</p>
        <div class="ctas rise" style="--i:3">
          <a class="btn" href="#contacto">Evaluar una propiedad {ICO['arrow']}</a>
          <a class="btn ghost" href="{wa_link()}" rel="noopener">{ICO['wa']} WhatsApp</a>
        </div>
      </div>
      <aside class="hero-aside rise" style="--i:4">
        <p><b>Del expediente a las llaves.</b>Un solo equipo legal en todas las etapas del remate.</p>
        <p><b>Con el respaldo de {esc(CFG['estudio_aliado'])}.</b>Estudio especializado en derecho civil, inmobiliario y comercial.</p>
      </aside>
    </div>
    <div class="hero-strip rise" style="--i:5">
      <div><b>Análisis</b>Expediente, bases y títulos</div>
      <div><b>Subasta</b>Presencial o por videoconferencia</div>
      <div><b>Adjudicación</b>Saldo, acta y escritura</div>
      <div><b>Entrega</b>Inscripción y llaves</div>
    </div>
  </div>
  <div class="scroll-cue" aria-hidden="true"></div>
</section>

<section class="sec" aria-labelledby="riesgo">
  <div class="wrap">
    <div class="sec-head">
      <div><p class="kicker reveal">Por qué un abogado</p><h2 id="riesgo" class="reveal" style="--i:1">El precio mínimo no cuenta toda la historia.</h2></div>
      <p class="lead reveal" style="--i:2">Un remate puede ser una muy buena oportunidad. Pero lo que define si conviene está en el expediente y en los títulos, no en el aviso.</p>
    </div>
    <div class="risks">{risks}</div>
  </div>
</section>

<section class="sec dark on-dark" id="servicios" aria-labelledby="servicios-t">
  <div class="wrap">
    <div class="sec-head">
      <div><p class="kicker reveal">Servicios</p><h2 id="servicios-t" class="reveal" style="--i:1">Todo el remate, en manos de un solo equipo.</h2></div>
      <p class="lead reveal" style="--i:2">Desde la primera revisión hasta que la propiedad queda inscrita a su nombre. Puede contratarnos para todo el proceso o para una etapa específica.</p>
    </div>
    <div class="services">{services}</div>
  </div>
</section>

<section class="sec" id="proceso" aria-labelledby="proceso-t">
  <div class="wrap">
    <div class="sec-head">
      <div><p class="kicker reveal">Cómo trabajamos</p><h2 id="proceso-t" class="reveal" style="--i:1">Cinco pasos, sin sorpresas.</h2></div>
      <p class="lead reveal" style="--i:2">Cada etapa tiene un responsable y usted sabe en todo momento en qué está su remate.</p>
    </div>
    <ol class="steps"><span class="bar-fill" aria-hidden="true"></span>{steps}</ol>
  </div>
</section>

<section class="sec white" aria-labelledby="quien-t">
  <div class="wrap">
    <div class="sec-head">
      <div><p class="kicker reveal">Para quién</p><h2 id="quien-t" class="reveal" style="--i:1">Asesoría a la medida de cada comprador.</h2></div>
      <p class="lead reveal" style="--i:2">Acompañamos tanto a quien compra su primera propiedad en remate como a inversionistas y fondos que participan con frecuencia.</p>
    </div>
    <div class="who">{who}</div>
  </div>
</section>

<section class="sec dark on-dark" aria-labelledby="confianza-t">
  <div class="wrap trust">
    <div class="seal reveal"><img src="/assets/img/sello-negativo.svg" alt="" width="360" height="360" loading="lazy"></div>
    <div>
      <p class="kicker reveal">Transparencia</p>
      <h2 id="confianza-t" class="reveal" style="--i:1">Remates claros, de principio a fin.</h2>
      <p class="lead reveal" style="--i:2;margin-top:22px">Sabemos que muchas personas desconfían de los remates. Por eso trabajamos con reglas simples que usted puede verificar.</p>
      <ul class="pledges">{pledges}</ul>
    </div>
  </div>
</section>

<section class="sec" id="equipo" aria-labelledby="equipo-t">
  <div class="wrap">
    <div class="sec-head">
      <div><p class="kicker reveal">Equipo</p><h2 id="equipo-t" class="reveal" style="--i:1">Abogados dedicados al derecho inmobiliario.</h2></div>
      <p class="lead reveal" style="--i:2">Un equipo con experiencia en estudios de títulos, litigación civil y tramitación de remates.</p>
    </div>
    <div class="team">{team}</div>
    <div class="alliance reveal">
      <p><b>Alianza con {esc(CFG['estudio_aliado'])}.</b> Para todo lo que va más allá del remate, como litigios civiles y comerciales, particiones o regularizaciones, trabajamos junto a este estudio especializado en derecho civil, inmobiliario y comercial.</p>
      <a class="link" href="{CFG['estudio_aliado_url']}" rel="noopener">Conocer el estudio {ICO['arrow']}</a>
    </div>
  </div>
</section>

<section class="sec white" id="preguntas" aria-labelledby="faq-t">
  <div class="wrap faq-grid">
    <div class="faq-side">
      <p class="kicker reveal">Preguntas frecuentes</p>
      <h2 id="faq-t" class="reveal" style="--i:1">Lo que conviene saber antes de un remate.</h2>
      <p class="lead reveal" style="--i:2;margin:22px 0 30px">Si quiere el detalle de cada etapa, revise nuestra guía paso a paso.</p>
      <a class="link reveal" style="--i:3" href="/guia-remate-judicial/">Leer la guía {ICO['arrow']}</a>
    </div>
    {faq_html()}
  </div>
</section>

<section class="sec dark on-dark" id="contacto" aria-labelledby="contacto-t">
  <div class="wrap contact">
    <div>
      <p class="kicker reveal">Contacto</p>
      <h2 id="contacto-t" class="reveal" style="--i:1">Cuéntenos qué remate le interesa.</h2>
      <p class="lead reveal" style="--i:2;margin-top:22px">Revisamos su caso y le respondemos con una evaluación inicial y una propuesta de trabajo.</p>
      <div class="contact-info">
        <a class="reveal" href="{wa_link()}" rel="noopener"><span class="ci">{ICO['wa']}</span><span><b>WhatsApp</b>La forma más rápida de contactarnos</span></a>
        <a class="reveal" style="--i:1" href="tel:{CFG['telefono_href']}"><span class="ci">{ICO['phone']}</span><span><b>{esc(CFG['telefono'])}</b>Lunes a viernes</span></a>
        <a class="reveal" style="--i:2" href="{CFG['mapa']}" rel="noopener"><span class="ci">{ICO['pin']}</span><span><b>{esc(CFG['direccion'])}</b>{esc(CFG['comuna'])}, Chile</span></a>
      </div>
    </div>
    {contact_form()}
  </div>
</section>
"""
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": " ".join(a)}} for q, a in FAQ]}
    site_ld = {"@context": "https://schema.org", "@type": "WebSite", "name": CFG["nombre"], "url": D + "/", "inLanguage": "es-CL",
               "publisher": {"@id": D + "/#organizacion"}}
    page("/", "Abogados Remates Judiciales | Asesoría para comprar en remate",
         "Abogados especialistas en remates judiciales en Chile. Revisamos expediente y títulos, lo representamos en la subasta y lo acompañamos hasta la entrega.",
         body, [org_jsonld(), site_ld, faq_ld], intro=True)


GUIDE = [
    ("buscar", "1. Encontrar el remate", [
        "Los remates judiciales se publican en avisos en diarios y en el sitio del Poder Judicial, con la fecha, el tribunal, la causa (rol), la propiedad y el precio mínimo.",
        "Antes de entusiasmarse con el precio, anote el tribunal y el rol de la causa: con esos datos se revisa el expediente."]),
    ("expediente", "2. Revisar el expediente y las bases", [
        "Las bases del remate fijan el precio mínimo, la garantía que hay que rendir, la forma de pago del saldo y sus plazos. El expediente muestra cómo se ha llevado el juicio.",
        "Errores en las notificaciones, en la tasación o en la publicación de los avisos pueden afectar la adjudicación. Por eso conviene que lo revise un abogado."]),
    ("titulos", "3. Estudiar los títulos y las deudas", [
        "En el Conservador de Bienes Raíces se revisa quién es el dueño, la historia de la propiedad y las hipotecas, embargos y prohibiciones vigentes.",
        "También hay que averiguar las deudas que pueden seguir al inmueble, como contribuciones o gastos comunes en un edificio o condominio."]),
    ("visita", "4. Conocer la propiedad y su ocupación", [
        "Normalmente no es posible recorrer el interior, pero sí verificar el entorno, el estado exterior y si la propiedad está ocupada.",
        "Si está ocupada, hay que prever el tiempo y el costo de pedir su entrega al tribunal."]),
    ("garantia", "5. Preparar la garantía y el financiamiento", [
        "Para participar se rinde la garantía que exigen las bases, en la forma que ellas indiquen, por ejemplo con un vale vista a la orden del tribunal.",
        "Si piensa financiar con un crédito, converse con su banco antes: los plazos para pagar el saldo suelen ser cortos."]),
    ("subasta", "6. Participar en la subasta", [
        "El remate se realiza en la fecha y hora fijadas, en el tribunal o por videoconferencia, según lo disponga el tribunal. Para los remates por videoconferencia, normalmente hay que inscribirse con anticipación.",
        "Conviene llegar con una postura máxima definida de antemano, para no pagar de más en el calor de la puja."]),
    ("adjudicacion", "7. Pagar el saldo y firmar la escritura", [
        "Quien se adjudica la propiedad debe pagar el saldo del precio dentro del plazo de las bases. Luego se firma el acta de remate y se reduce a escritura pública.",
        "Si el saldo no se paga a tiempo, se arriesga la garantía."]),
    ("inscripcion", "8. Inscribir y recibir la propiedad", [
        "Con la escritura se inscribe el dominio a su nombre en el Conservador de Bienes Raíces y se alzan los gravámenes que correspondan.",
        "Si la propiedad está ocupada, se solicita al tribunal su entrega material, con auxilio de la fuerza pública si es necesario."]),
]


def guide():
    toc = "".join(f'<li><a href="#{sid}">{esc(t[3:])}</a></li>' for sid, t, _ in GUIDE)
    secs = "".join(f'<h2 id="{sid}">{esc(t)}</h2>' + "".join(f"<p>{esc(p)}</p>" for p in ps) for sid, t, ps in GUIDE)
    body = f"""
<section class="page-hero on-dark">
  <div class="plan">{PLAN}</div>
  <div class="wrap" style="position:relative">
    <ol class="crumbs"><li><a href="/">Inicio</a></li><li>Guía</li></ol>
    <p class="kicker">Guía práctica</p>
    <h1>Cómo comprar una propiedad en remate judicial en Chile</h1>
    <p class="lead">Las ocho etapas de un remate, desde que encuentra el aviso hasta que recibe las llaves, y en qué fijarse en cada una.</p>
  </div>
</section>
<section class="sec">
  <div class="wrap article-grid">
    <aside><nav class="toc" aria-label="Índice"><h2 class="fh">En esta guía</h2><ol>{toc}</ol></nav></aside>
    <article class="prose">
      <p class="lead">Comprar en remate puede ser una forma de acceder a una propiedad bajo su valor de mercado. A cambio, exige revisar con cuidado aspectos que en una compraventa normal resuelve el vendedor.</p>
      {secs}
      <div class="note"><b>Importante.</b> Esta guía es informativa y general. Cada remate tiene sus propias bases y cada propiedad su propia historia, por lo que conviene revisar su caso con un abogado antes de ofrecer.</div>
      <p><a class="btn" href="/#contacto">Evaluar un remate {ICO['arrow']}</a></p>
    </article>
  </div>
</section>
"""
    art = {"@context": "https://schema.org", "@type": "Article", "headline": "Cómo comprar una propiedad en remate judicial en Chile",
           "description": "Guía paso a paso para comprar una propiedad en remate judicial en Chile: expediente, títulos, garantía, subasta, adjudicación, inscripción y entrega.",
           "inLanguage": "es-CL", "author": {"@id": D + "/#organizacion"}, "publisher": {"@id": D + "/#organizacion"},
           "mainEntityOfPage": D + "/guia-remate-judicial/", "image": D + "/assets/img/og.png", "dateModified": TODAY}
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Inicio", "item": D + "/"},
        {"@type": "ListItem", "position": 2, "name": "Guía para comprar en remate judicial", "item": D + "/guia-remate-judicial/"}]}
    page("/guia-remate-judicial/", "Cómo comprar en remate judicial en Chile: guía paso a paso",
         "Guía para comprar en remate judicial en Chile: expediente, títulos, garantía, subasta, pago del saldo, inscripción y entrega de la propiedad.",
         body, [org_jsonld(), art, crumbs], og_type="article")


def privacy():
    body = f"""
<section class="page-hero on-dark"><div class="wrap"><ol class="crumbs"><li><a href="/">Inicio</a></li><li>Privacidad</li></ol><h1>Política de privacidad</h1></div></section>
<section class="sec"><div class="wrap"><article class="prose">
<p>En {esc(CFG['nombre'])} usamos los datos que nos entrega en el formulario de contacto o por WhatsApp (nombre, teléfono, correo y el detalle de su consulta) solo para responder su consulta y, si lo solicita, prestarle nuestros servicios.</p>
<p>No vendemos ni cedemos sus datos a terceros. Pueden tener acceso a ellos los abogados del equipo y los proveedores tecnológicos que usamos para operar este sitio, siempre con ese único fin.</p>
<p>Puede pedir en cualquier momento que actualicemos o eliminemos sus datos escribiéndonos por los medios de contacto de este sitio, conforme a la Ley N.º 19.628 sobre protección de la vida privada.</p>
<p>Este sitio no usa cookies de seguimiento publicitario.</p>
</article></div></section>"""
    page("/privacidad/", f"Política de privacidad | {CFG['nombre']}", f"Cómo usa {CFG['nombre']} los datos que nos entrega en el formulario de contacto.",
         body, [org_jsonld()])


def not_found():
    body = """
<section class="page-hero on-dark" style="min-height:70vh"><div class="wrap"><p class="kicker">Error 404</p><h1>Esta página no existe.</h1>
<p class="lead">Puede volver al inicio o escribirnos directamente.</p><p style="margin-top:32px"><a class="btn" href="/">Volver al inicio</a></p></div></section>"""
    page("/404.html", f"Página no encontrada | {CFG['nombre']}", "La página que busca no existe.", body, [])
    p = os.path.join(PUB, "404.html")
    s = open(p, encoding="utf-8").read().replace('<meta name="robots" content="index, follow, max-image-preview:large">', '<meta name="robots" content="noindex">')
    open(p, "w", encoding="utf-8").write(s)


def extras():
    urls = [("/", "1.0"), ("/guia-remate-judicial/", "0.8"), ("/privacidad/", "0.2")]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
        f"  <url><loc>{D}{u}</loc><lastmod>{TODAY}</lastmod><priority>{p}</priority></url>\n" for u, p in urls) + "</urlset>\n"
    open(os.path.join(PUB, "sitemap.xml"), "w", encoding="utf-8").write(sm)
    open(os.path.join(PUB, "robots.txt"), "w", encoding="utf-8").write(f"User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: {D}/sitemap.xml\n")
    faq_txt = "\n".join(f"- {q} {' '.join(a)}" for q, a in FAQ)
    services_txt = "\n".join(f"- {t}: {d}" for t, d in SERVICES)
    llms = f"""# {CFG['nombre']}

> Abogados especialistas en remates judiciales de inmuebles en Chile. Asesoran a personas, inversionistas, empresas y fondos en todo el proceso: análisis del expediente y de las bases, estudio de títulos y deudas, representación en la subasta, adjudicación, escrituración, inscripción en el Conservador de Bienes Raíces y entrega material de la propiedad. Oficina en {CFG['direccion']}, {CFG['comuna']}, Chile. Trabajan en alianza con {CFG['estudio_aliado']} ({CFG['estudio_aliado_url']}).

## Servicios
{services_txt}

## Equipo
""" + "\n".join(f"- {n}, {r}." for _, n, r, _ in TEAM) + f"""

## Páginas
- [Inicio]({D}/): servicios, forma de trabajo, equipo, preguntas frecuentes y contacto.
- [Guía: cómo comprar una propiedad en remate judicial en Chile]({D}/guia-remate-judicial/)

## Preguntas frecuentes
{faq_txt}

## Contacto
- Teléfono y WhatsApp: {CFG['telefono']}
- Dirección: {CFG['direccion']}, {CFG['comuna']}, Chile
- Formulario: {D}/#contacto
"""
    open(os.path.join(PUB, "llms.txt"), "w", encoding="utf-8").write(llms)
    manifest = {"name": CFG["nombre"], "short_name": CFG["nombre_corto"], "start_url": "/", "display": "standalone",
                "background_color": "#222B53", "theme_color": "#222B53", "lang": "es-CL",
                "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
                          {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}]}
    open(os.path.join(PUB, "site.webmanifest"), "w", encoding="utf-8").write(json.dumps(manifest, ensure_ascii=False, indent=2))
    headers = """/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  X-Frame-Options: SAMEORIGIN
/assets/*
  Cache-Control: public, max-age=31536000, immutable
"""
    open(os.path.join(PUB, "_headers"), "w", encoding="utf-8").write(headers)


if __name__ == "__main__":
    home()
    guide()
    privacy()
    not_found()
    extras()
    n = sum(1 for _, _, fs in os.walk(PUB) for f in fs if f.endswith(".html"))
    print(f"{n} páginas generadas en {PUB}")

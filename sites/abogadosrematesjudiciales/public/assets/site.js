/* Abogados Remates Judiciales · comportamiento del sitio */
(() => {
  const root = document.documentElement;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- animación de entrada ---------- */
  const intro = document.querySelector('.intro');
  const markReady = () => { if (!root.classList.contains('ready')) root.classList.add('ready'); };

  if (intro && root.classList.contains('play-intro')) {
    // El golpe del martillo cae en el centro de la cabeza: la línea y la onda nacen ahí
    const head = intro.querySelector('.head');
    const placeImpact = () => {
      const r = head.getBoundingClientRect();
      const x = ((r.left + r.width / 2) / window.innerWidth) * 100;
      intro.style.setProperty('--ix', x.toFixed(2) + '%');
    };
    requestAnimationFrame(placeImpact);
    let done = false;
    const finish = () => {
      if (done) return; done = true;
      root.classList.add('intro-out');
      setTimeout(markReady, 250);
      setTimeout(() => { root.classList.remove('play-intro', 'intro-out'); intro.remove(); }, 1300);
    };
    try { sessionStorage.setItem('arj-intro', '1'); } catch (e) { /* sin almacenamiento: no pasa nada */ }
    const timer = setTimeout(finish, 2300);
    const skip = () => { clearTimeout(timer); finish(); };
    intro.addEventListener('click', skip);
    window.addEventListener('keydown', e => { if (e.key === 'Escape' || e.key === 'Enter' || e.key === ' ') skip(); }, { once: true });
  } else {
    requestAnimationFrame(markReady);
  }

  /* ---------- plano de la portada: cada línea se dibuja con un pequeño desfase ---------- */
  document.querySelectorAll('.plan-lines path').forEach((p, i) => p.style.setProperty('--d', String((i * 37) % 1400)));
  document.querySelectorAll('.plan-lots rect').forEach((r, i) => r.style.setProperty('--d', String(i * 160)));

  /* ---------- encabezado ---------- */
  const head = document.querySelector('.site-head');
  const hero = document.querySelector('.hero, .page-hero');
  const wa = document.querySelector('.wa');
  let lastY = window.scrollY;
  const onScroll = () => {
    const y = window.scrollY;
    const limit = hero ? hero.offsetHeight - 90 : 40;
    head.classList.toggle('solid', y > 40);
    head.classList.toggle('hide', y > limit && y > lastY + 4 && !document.querySelector('.nav.open'));
    if (y < lastY - 4) head.classList.remove('hide');
    if (wa) wa.classList.toggle('show', y > window.innerHeight * 0.6);
    lastY = y;
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- menú en el teléfono ---------- */
  const btn = document.querySelector('.menu-btn');
  const nav = document.querySelector('.nav');
  if (btn && nav) {
    const toggle = open => {
      nav.classList.toggle('open', open);
      btn.setAttribute('aria-expanded', String(open));
      document.body.style.overflow = open ? 'hidden' : '';
    };
    btn.addEventListener('click', () => toggle(!nav.classList.contains('open')));
    nav.querySelectorAll('a').forEach(a => a.addEventListener('click', () => toggle(false)));
    window.addEventListener('keydown', e => { if (e.key === 'Escape') toggle(false); });
  }

  /* ---------- aparición al hacer scroll ---------- */
  const targets = document.querySelectorAll('.reveal, .line-in, .steps');
  if ('IntersectionObserver' in window && !reduce) {
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.08 });
    targets.forEach(t => io.observe(t));
  } else {
    targets.forEach(t => t.classList.add('in'));
  }

  /* ---------- índice de la guía ---------- */
  const tocLinks = document.querySelectorAll('.toc a');
  if (tocLinks.length && 'IntersectionObserver' in window) {
    const map = new Map([...tocLinks].map(a => [a.getAttribute('href').slice(1), a]));
    const io2 = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) { tocLinks.forEach(a => a.classList.remove('on')); const a = map.get(e.target.id); if (a) a.classList.add('on'); }
      });
    }, { rootMargin: '-20% 0px -70% 0px' });
    map.forEach((_, id) => { const el = document.getElementById(id); if (el) io2.observe(el); });
  }

  /* ---------- formulario de contacto ---------- */
  const form = document.querySelector('form.lead-form');
  if (form) {
    const msg = form.querySelector('.form-msg');
    const send = form.querySelector('button[type="submit"]');
    const show = (kind, text) => { msg.className = 'form-msg ' + kind; msg.textContent = text; };
    form.addEventListener('submit', async e => {
      e.preventDefault();
      if (!form.reportValidity()) return;
      const data = Object.fromEntries(new FormData(form).entries());
      data.pagina = location.pathname;
      send.disabled = true;
      show('', '');
      try {
        const res = await fetch(form.action, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        const out = await res.json().catch(() => ({}));
        if (!res.ok || !out.ok) throw new Error(out.error || 'error');
        form.reset();
        show('ok', 'Recibimos su mensaje. Un abogado del equipo lo contactará a la brevedad.');
      } catch (err) {
        show('err', 'No pudimos enviar el mensaje. Escríbanos por WhatsApp o inténtelo de nuevo en unos minutos.');
      } finally {
        send.disabled = false;
      }
    });
  }
})();

/* Taj Elite — shared behaviour for every page:
   header, mobile menu, action dock, reveal-on-scroll, palette picker, smooth scroll,
   plus two small components other pages call: Taj.tabs() and Taj.ba(). */
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const htmlEl = document.documentElement;

  /* header + dock */
  const hdr = $('#hdr'), dock = $('#dock');
  const onScroll = () => {
    const y = scrollY;
    hdr && hdr.classList.toggle('scrolled', y > 40);
    dock && dock.classList.toggle('show', y > innerHeight * 0.6);
  };
  addEventListener('scroll', onScroll, { passive: true }); onScroll();

  /* mobile menu */
  const nav = $('#nav'), mb = $('#menuBtn');
  if (nav && mb) {
    mb.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      mb.setAttribute('aria-expanded', open);
      mb.setAttribute('aria-label', open ? 'إغلاق القائمة' : 'فتح القائمة');
      document.body.style.overflow = open ? 'hidden' : '';
      window.__lenis && (open ? __lenis.stop() : __lenis.start());
    });
    nav.addEventListener('click', e => { if (e.target.closest('a') && nav.classList.contains('open')) mb.click(); });
    addEventListener('keydown', e => { if (e.key === 'Escape' && nav.classList.contains('open')) { mb.click(); mb.focus(); } });
  }

  /* reveal */
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
  }), { rootMargin: '0px 0px -10% 0px' });
  $$('.rv-in').forEach(el => io.observe(el));

  /* accessible tabs */
  function tabs(list, onSelect) {
    const ts = $$('[role=tab]', list);
    const select = (t, focus) => {
      ts.forEach(x => { const on = x === t; x.setAttribute('aria-selected', on); x.tabIndex = on ? 0 : -1; });
      if (focus) t.focus();
      onSelect(t);
    };
    ts.forEach((t, i) => {
      t.addEventListener('click', () => select(t));
      t.addEventListener('keydown', e => {
        const d = { ArrowLeft: 1, ArrowRight: -1, Home: -i, End: ts.length - 1 - i }[e.key];   // RTL
        if (d === undefined) return;
        e.preventDefault(); select(ts[(i + d + ts.length) % ts.length], true);
      });
    });
  }

  /* before / after comparison: root contains .ba (with #-less hooks) and a .thumbs list */
  function ba(root, key, count, base = '/assets/img/cases/') {
    const box = $('.ba', root), range = $('input', box), A = $('.after', box), B = $('.before', box), thumbs = $('.thumbs', root);
    const setPos = v => box.style.setProperty('--pos', v + '%');
    const src = (k, i, w) => `${base}${k}-${i}-${w}.webp`;
    if (!range.dataset.bound) { range.addEventListener('input', () => setPos(range.value)); range.dataset.bound = 1; }
    function show(i) {
      A.src = src(key, i, 'after'); B.src = src(key, i, 'before');
      $$('button', thumbs).forEach((b, n) => b.setAttribute('aria-pressed', n + 1 === i));
      range.value = 50; setPos(50);
    }
    thumbs.innerHTML = '';
    for (let i = 1; i <= count; i++) {
      const b = document.createElement('button');
      b.type = 'button'; b.setAttribute('aria-label', `الحالة ${i}`);
      b.innerHTML = `<img src="${src(key, i, 'after')}" width="425" height="228" loading="lazy" alt="">`;
      b.addEventListener('click', () => show(i));
      thumbs.append(b);
    }
    show(1);
  }
  $$('[data-ba]').forEach(r => { const [k, n] = r.dataset.ba.split(':'); ba(r, k, +n); });

  /* palette picker */
  const tBtn = $('#themeBtn'), tPop = $('#themePop');
  if (tBtn && tPop) {
    const tOpts = $$('[role=radio]', tPop), metaTheme = $('meta[name=theme-color]');
    const applyTheme = (t, animate) => {
      if (animate && !reduced) { htmlEl.classList.add('theming'); setTimeout(() => htmlEl.classList.remove('theming'), 700); }
      htmlEl.dataset.theme = t;
      tOpts.forEach(o => { const on = o.dataset.t === t; o.setAttribute('aria-checked', on); o.tabIndex = on ? 0 : -1; });
      if (metaTheme) metaTheme.content = getComputedStyle(htmlEl).getPropertyValue('--deep').trim();
      document.dispatchEvent(new CustomEvent('tajtheme', { detail: t }));
      try { localStorage.setItem('taj-theme', t); } catch {}
    };
    const setPop = open => {
      tPop.classList.toggle('open', open);
      tBtn.setAttribute('aria-expanded', open);
      if (open) (tOpts.find(o => o.getAttribute('aria-checked') === 'true') || tOpts[0]).focus();
    };
    tBtn.addEventListener('click', () => setPop(!tPop.classList.contains('open')));
    tOpts.forEach((o, i) => {
      o.addEventListener('click', () => applyTheme(o.dataset.t, true));
      o.addEventListener('keydown', e => {
        const d = { ArrowDown: 1, ArrowUp: -1 }[e.key];
        if (d) { e.preventDefault(); const n = tOpts[(i + d + tOpts.length) % tOpts.length]; n.focus(); applyTheme(n.dataset.t, true); }
      });
    });
    document.addEventListener('click', e => { if (!e.target.closest('.theme')) setPop(false); });
    addEventListener('keydown', e => { if (e.key === 'Escape' && tPop.classList.contains('open')) { setPop(false); tBtn.focus(); } });
    applyTheme(htmlEl.dataset.theme || 'teal', false);
  }

  /* smooth, weighted scrolling on desktop (touch keeps native momentum) */
  if (!reduced && matchMedia('(pointer: fine)').matches) {
    const sc = document.createElement('script');
    sc.src = 'https://cdn.jsdelivr.net/npm/lenis@1.1.13/dist/lenis.min.js';
    sc.onload = () => {
      const lenis = new Lenis({ lerp: 0.085, wheelMultiplier: 0.95 });
      window.__lenis = lenis;
      const raf = t => { lenis.raf(t); requestAnimationFrame(raf); };
      requestAnimationFrame(raf);
      document.addEventListener('click', e => {
        const a = e.target.closest('a[href^="#"]');
        if (!a || a.getAttribute('href').length < 2) return;
        const t = document.querySelector(a.getAttribute('href'));
        if (!t) return;
        e.preventDefault();
        lenis.scrollTo(t, { offset: t.id === 'top' ? 0 : -80, duration: 1.4 });
      });
    };
    document.head.append(sc);
  }

  /* map: click-to-load keeps Google's 500KB+ off the page until asked for */
  const mapBtn = $('#mapBtn');
  mapBtn && mapBtn.addEventListener('click', () => {
    $('#map').innerHTML = '<iframe title="موقع مجمع تاج إيليت على الخريطة" src="https://www.google.com/maps?q=24.59286,46.758461&z=16&output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>';
  });

  /* reviews: one featured quote at a time; auto-advances while visible,
     pauses on hover/focus, stops for good once the visitor picks a review */
  $$('[data-reviews]').forEach(root => {
    const qs = $$('.rvx-q', root), dots = $$('.rvx-dot', root), stage = $('.rvx-stage', root);
    if (qs.length < 2) return;
    const MS = 7000;
    let i = 0, timer = 0, picked = false, visible = false, held = false;
    root.style.setProperty('--rvx-ms', MS + 'ms');
    const running = () => !reduced && !picked && visible && !held;
    function tick() {
      clearTimeout(timer);
      root.classList.remove('playing');
      if (!running()) return;
      void root.offsetWidth;                 // restart the progress bar animation
      root.classList.add('playing');
      timer = setTimeout(() => show(i + 1), MS);
    }
    function show(n) {
      i = (n + qs.length) % qs.length;
      qs.forEach((q, k) => { q.classList.toggle('on', k === i); q.setAttribute('aria-hidden', k !== i); });
      dots.forEach((d, k) => d.setAttribute('aria-pressed', k === i));
      tick();
    }
    dots.forEach((d, k) => d.addEventListener('click', () => {
      picked = true; stage.setAttribute('aria-live', 'polite'); show(k);
    }));
    root.addEventListener('mouseenter', () => { held = true; tick(); });
    root.addEventListener('mouseleave', () => { held = false; tick(); });
    root.addEventListener('focusin', () => { held = true; tick(); });
    root.addEventListener('focusout', e => { if (!root.contains(e.relatedTarget)) { held = false; tick(); } });
    new IntersectionObserver(([e]) => { visible = e.isIntersecting; tick(); }, { threshold: 0.35 }).observe(root);
  });

  /* offer countdowns: "ends in N days" in correct Arabic; expired offers remove themselves */
  const days = n => n === 1 ? 'يوم واحد' : n === 2 ? 'يومين' : n <= 10 ? `${n} أيام` : `${n} يومًا`;
  $$('[data-ends]').forEach(el => {
    const end = new Date(el.dataset.ends + 'T23:59:59+03:00');            // Riyadh time
    const left = Math.ceil((end - Date.now()) / 864e5);
    if (left < 1 && end < Date.now()) {
      const card = el.closest('[data-offer]'); card && card.remove(); return;
    }
    if (left <= 1) el.textContent = 'ينتهي العرض اليوم';
    else if (left <= 45) el.textContent = `ينتهي العرض خلال ${days(left)}`;
  });
  const offersSec = $('#offers');
  if (offersSec && !$('[data-offer]', offersSec)) { offersSec.hidden = true; $$('.promo, a[href$="#offers"]').forEach(a => a.remove()); }

  $$('.yr').forEach(el => el.textContent = new Date().getFullYear());

  window.Taj = { $, $$, reduced, tabs, ba };
})();

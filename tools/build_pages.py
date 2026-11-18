# -*- coding: utf-8 -*-
"""Builds every inner page of the Taj Elite site from tools/content.py.

    python tools/build_pages.py

Header, footer, icon sprite and mobile dock are copied from index.html, so they stay
identical everywhere. Each page is written to /<slug>/index.html, keeping the old
site's URLs (and their search rankings).
"""
import os, re, json, html
from urllib.parse import quote
from content import (DEPTS, DOCTORS, SERVICES, DOCTOR_PAGES, ARTICLES, REDIRECTS,
                     CARD_IMG, CARD_ORDER, SHORT, OFFERS, OFFERS_SAMPLE, PAYMENTS)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://taj-elite.com"
PHONE_TEL = "+966598957544"
WA_NUM = "966598957544"
E = html.escape
BY_SLUG = {s["slug"]: s for s in SERVICES}
OFFER_BY_SLUG = {o["slug"]: o for o in OFFERS}
MONTHS = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
INDEX_PATH = os.path.join(ROOT, "index.html")

SPRITE = HEADER = FOOTER = DOCK = ""

def load_shell():
    """Copy header/footer/sprite/dock from index.html so every page matches it."""
    global SPRITE, HEADER, FOOTER, DOCK
    index = open(INDEX_PATH, encoding="utf-8").read()
    def cut(start, end_marker):
        a = index.index(start)
        return index[a:index.index(end_marker, a) + len(end_marker)]
    SPRITE = cut('<svg width="0" height="0"', "</svg>")
    HEADER = cut('<header class="hdr"', "</header>")
    FOOTER = cut('<footer class="foot">', "</footer>")
    DOCK = cut('<div class="dock"', "</div>")
    # on inner pages, in-page anchors point back to the home page
    HEADER = HEADER.replace('href="#top"', 'href="/"')
    HEADER = re.sub(r'href="#(\w+)"', r'href="/#\1"', HEADER)

def img_dims(path):
    if path.startswith("cases/"): return 425, 228
    if "derma" in path: return 720, 960
    if path.startswith("dr-"): return 640, 640
    return 720, 480

def money(n):
    return f"{n:,}"

def date_ar(iso):
    y, m, d = map(int, iso.split("-"))
    return f"{d} {MONTHS[m - 1]}"

# ---------------------------------------------------------------- image cards
def tcards(slugs, cls="tcards"):
    items = []
    for s in slugs:
        x = BY_SLUG[s]; img = CARD_IMG[s]; w, h = img_dims(img)
        items.append(f'<li><a class="tcard" href="/{s}/"><span class="tc-img"><img src="/assets/img/{img}" width="{w}" height="{h}" loading="lazy" decoding="async" alt=""></span>'
                     f'<h3>{E(x["name"])}{icon("arrow")}</h3><p>{E(SHORT[s])}</p></a></li>')
    return f'<ul class="{cls}">' + "".join(items) + "</ul>"

def text_rows(slugs):
    rows = "".join(f'<li><a href="/{s}/"><h3>{E(BY_SLUG[s]["name"])}</h3><p>{E(SHORT[s])}</p>{icon("arrow")}</a></li>' for s in slugs)
    return f'<ul class="svc">{rows}</ul>'

# ---------------------------------------------------------------- offers (sales)
def offer_wa(o):
    return wa(f'مرحبًا، أرغب بحجز عرض {o["title"]} ({money(o["now"])} ريال) في تاج إيليت.')

def offer_card(o):
    w, h = img_dims(o["img"])
    off = round((o["was"] - o["now"]) / o["was"] * 100)
    inc = "".join(f"<li>{E(i)}</li>" for i in o["includes"])
    badge = f'<span class="of-badge">{E(o["badge"])}</span>' if o.get("badge") else ""
    return f'''<article class="offer rv-in" data-offer>
      <div class="of-img"><img src="/assets/img/{o["img"]}" width="{w}" height="{h}" loading="lazy" decoding="async" alt="">{badge}<span class="of-off">خصم {off}%</span></div>
      <div class="of-body">
        <h3>{E(o["title"])}</h3>
        <ul class="of-inc">{inc}</ul>
        <div class="of-price"><b>{money(o["now"])}</b><span>ريال</span><s>{money(o["was"])} ريال</s><small>{E(o["unit"])}</small></div>
        <p class="of-ends"><svg class="ico" viewBox="0 0 24 24"><circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 2M9 2h6"/></svg><span data-ends="{o["ends"]}">ينتهي العرض {date_ar(o["ends"])}</span></p>
        <div class="of-actions">
          <a class="btn" href="{offer_wa(o)}" target="_blank" rel="noopener">{icon("chat")}احجز العرض</a>
          <a class="of-more" href="/{o["slug"]}/">تفاصيل العلاج</a>
        </div>
      </div>
    </article>'''

def offers_section():
    pays = "".join(f"<span>{E(p)}</span>" for p in PAYMENTS)
    note = ('<p class="sample-note">الأسعار المعروضة أمثلة لعرض التصميم، وتُستبدل بعروض العيادة المعتمدة قبل الإطلاق.</p>'
            if OFFERS_SAMPLE else "")
    ld = {"@context": "https://schema.org", "@type": "OfferCatalog", "name": "عروض تاج إيليت",
          "itemListElement": [{"@type": "Offer", "name": o["title"], "price": o["now"], "priceCurrency": "SAR",
                               "validThrough": o["ends"], "url": f'{SITE}/{o["slug"]}/'} for o in OFFERS]}
    ld_tag = "" if OFFERS_SAMPLE else f'\n<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    return f'''<section class="offers dark" id="offers" aria-labelledby="h-offers">
  <div class="wrap">
    <div class="of-head">
      <div class="sec-head rv-in">
        <span class="eyebrow">العروض</span>
        <h2 id="h-offers">عروض لفترة محدودة</h2>
        <p>أسعار واضحة تشمل ما تحتاجه فعلًا. احجز العرض على واتساب ويؤكد فريق الاستقبال موعدك.</p>
      </div>
    </div>
    <div class="offer-grid">{"".join(offer_card(o) for o in OFFERS)}</div>
    <div class="pay"><b>طرق الدفع</b>{pays}</div>
    {note}
  </div>
</section>{ld_tag}'''

def promo_pill():
    if not OFFERS: return ""
    o = OFFERS[0]
    return (f'<a class="promo" href="#offers" data-offer><b>{E(o.get("badge") or "عرض")}</b>'
            f'<span>{E(o["title"])} بـ {money(o["now"])} ريال</span><svg class="ico"><use href="#i-arrow"/></svg></a>')

def svc_offer_box(slug):
    o = OFFER_BY_SLUG.get(slug)
    if not o: return ""
    return (f'<a class="svc-offer" href="{offer_wa(o)}" target="_blank" rel="noopener" data-offer><b>عرض حالي</b>'
            f'<span><strong>{money(o["now"])} ريال</strong> بدل <s>{money(o["was"])}</s> · {E(o["unit"])}</span>'
            f'<span class="ends" data-ends="{o["ends"]}">ينتهي {date_ar(o["ends"])}</span></a>')

def inject_index():
    s = open(INDEX_PATH, encoding="utf-8").read()
    def put(name, html_):
        nonlocal s
        pat = re.compile(rf"<!--{re.escape(name)}-->.*?<!--/{re.escape(name)}-->", re.S)
        assert pat.search(s), name
        s = pat.sub(lambda m: f"<!--{name}-->{html_}<!--/{name}-->", s, count=1)
    put("PROMO", promo_pill())
    # homepage treatments stay as a text list (image cards are used on inner pages only)
    put("CARDS:surg", text_rows(CARD_ORDER["surg"]))
    put("CARDS:cos", text_rows(CARD_ORDER["cos"]))
    put("OFFERS", offers_section())
    open(INDEX_PATH, "w", encoding="utf-8").write(s)

def wa(text):
    return f"https://wa.me/{WA_NUM}?text={quote(text)}"

def icon(name):
    return f'<svg class="ico"><use href="#i-{name}"/></svg>'

def head(title, desc, path, extra_ld=()):
    ld = "".join(f'\n<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in extra_ld)
    return f'''<!doctype html>
<html lang="ar" dir="rtl" data-theme="stone">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<meta name="theme-color" content="#1D1A17">
<script>try{{var t=localStorage.getItem("taj-theme");if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
<link rel="canonical" href="{SITE}{path}">
<meta property="og:type" content="website">
<meta property="og:locale" content="ar_SA">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:image" content="{SITE}/assets/img/facade-960.webp">
<link rel="icon" type="image/png" href="/assets/img/favicon-64.png">
<link rel="apple-touch-icon" href="/assets/img/icon-180.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600&family=Reem+Kufi:wght@500;600;700&display=swap">
<link rel="stylesheet" href="/assets/css/site.css">{ld}
</head>
<body>
<script>document.documentElement.classList.add('js')</script>
{SPRITE}
<a class="skip" href="#main">تخطَّ إلى المحتوى</a>
{HEADER}
<main id="main">
'''

def tail():
    return f'''
</main>
{FOOTER}
{DOCK}
<script src="/assets/js/site.js"></script>
</body>
</html>
'''

def crumbs(items):
    out = ['<nav class="crumbs" aria-label="مسار الصفحة">']
    for i, (label, href) in enumerate(items):
        if i: out.append('<span aria-hidden="true">/</span>')
        out.append(f'<a href="{href}">{E(label)}</a>' if href else f'<span aria-current="page">{E(label)}</span>')
    out.append("</nav>")
    return "".join(out)

def breadcrumb_ld(items, path):
    els = []
    for i, (label, href) in enumerate(items, 1):
        els.append({"@type": "ListItem", "position": i, "name": label, "item": SITE + (href or path)})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": els}

def faq_ld(faq):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}

def doc_chip(key):
    d = DOCTORS[key]
    return (f'<a class="doc-chip" href="/{d["slug"]}/"><img src="/assets/img/{d["img"]}" width="46" height="46" alt="" loading="lazy">'
            f'<span><small>{E(d["role"])}</small><b>{E(d["name"])}</b></span></a>')

def hero(crumb_items, h1, lede, img, img_alt, wa_text, chip="", offer=""):
    return f'''<section class="page-hero dark">
  <div class="wrap ph-grid">
    <div>
      {crumbs(crumb_items)}
      <h1>{E(h1)}</h1>
      <p class="lede">{E(lede)}</p>
      <div class="cta">
        <a class="btn" href="{wa(wa_text)}" target="_blank" rel="noopener">{icon("chat")}احجز استشارة</a>
        <a class="btn ghost" href="tel:{PHONE_TEL}">{icon("phone")}<span dir="ltr">059 895 7544</span></a>
      </div>
      {offer}
      {chip}
    </div>
    <div class="ph-arch"><div class="fr"><img src="/assets/img/{img}" width="720" height="480" alt="{E(img_alt)}" fetchpriority="high"></div></div>
  </div>
</section>'''

class Sections:
    """Alternates section backgrounds automatically, whatever sections a page has."""
    def __init__(self): self.n = 0
    def open(self, extra=""):
        cls = "pg-sec alt" if self.n % 2 else "pg-sec"
        self.n += 1
        return f'<section class="{cls}"{extra}>'

def checks(items):
    return '<ul class="checks">' + "".join(f"<li>{E(x)}</li>" for x in items) + "</ul>"

def svc_rows(slugs):
    rows = []
    for s in slugs:
        x = BY_SLUG[s]
        rows.append(f'<li><a href="/{s}/"><h3>{E(x["name"])}</h3><p>{E(x["lede"].split("،")[0].split(".")[0])}.</p>{icon("arrow")}</a></li>')
    return '<ul class="svc">' + "".join(rows) + "</ul>"

def cases_block(sec, spec, title="حالات حقيقية من المجمع"):
    k = spec.split(":")[0]
    return f'''{sec.open()}
  <div class="wrap cases">
    <div data-ba="{spec}">
      <div class="ba" style="--pos:50%">
        <img class="after" src="/assets/img/cases/{k}-1-after.webp" width="425" height="228" loading="lazy" decoding="async" alt="بعد العلاج">
        <img class="before" src="/assets/img/cases/{k}-1-before.webp" width="425" height="228" loading="lazy" decoding="async" alt="قبل العلاج">
        <span class="tag a">بعد</span><span class="tag b">قبل</span>
        <input type="range" min="0" max="100" value="50" dir="ltr" aria-label="اسحب للمقارنة بين قبل العلاج وبعده">
        <span class="handle" aria-hidden="true"></span>
      </div>
      <div class="thumbs" aria-label="اختر حالة"></div>
    </div>
    <div class="case-copy rv-in">
      <span class="eyebrow">قبل وبعد</span>
      <h2>{E(title)}</h2>
      <p>صور حقيقية لمراجعين عولجوا في تاج إيليت. اسحب الخط لترى الفرق.</p>
      <p class="note">تختلف النتائج من شخص لآخر حسب الحالة.</p>
    </div>
  </div>
</section>'''

def faq_block(sec, faq, title):
    items = "".join(f'<details><summary>{E(q)}{icon("plus")}</summary><p>{E(a)}</p></details>' for q, a in faq)
    return f'''{sec.open(' id="faq"')}
  <div class="wrap faq">
    <div class="sec-head rv-in"><span class="eyebrow">أسئلة شائعة</span><h2>{E(title)}</h2>
      <p>لم تجد سؤالك؟ أرسله لنا على واتساب ويرد عليك فريق الاستقبال.</p></div>
    <div>{items}</div>
  </div>
</section>'''

def cta_band(wa_text, title="جاهز للخطوة الأولى؟"):
    return f'''<section class="cta-band dark">
  <div class="wrap">
    <h2>{E(title)}</h2>
    <p>أرسل لنا على واتساب، ويتواصل معك فريق الاستقبال لتأكيد موعد الاستشارة.</p>
    <div class="cta">
      <a class="btn" href="{wa(wa_text)}" target="_blank" rel="noopener">{icon("chat")}احجز عبر واتساب</a>
      <a class="btn ghost" href="tel:{PHONE_TEL}">{icon("phone")}<span dir="ltr">059 895 7544</span></a>
    </div>
    <p class="addr">جنوب الرياض، حي الشباب، العزيزية — بجوار فندق أرجان بارك</p>
  </div>
</section>'''

def write(slug, content):
    d = os.path.join(ROOT, slug)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(content)

# ---------------------------------------------------------------- treatments
def service_page(s):
    path = f'/{s["slug"]}/'
    dept = DEPTS[s["dept"]]
    trail = [("الرئيسية", "/"), (dept, "/#treatments"), (s["name"], None)]
    wa_text = f'مرحبًا، أرغب بحجز استشارة لـ{s["name"]} في تاج إيليت.'
    sec = Sections()
    out = [head(s["title"], s["desc"], path, [breadcrumb_ld(trail, path), faq_ld(s["faq"])])]
    out.append(hero(trail, s["name"], s["lede"], s["img"], f'{s["name"]} في مجمع تاج إيليت', wa_text,
                    doc_chip(s["doctor"]) if s.get("doctor") else "", svc_offer_box(s["slug"])))

    # what it is (+ who it suits)
    body = "".join(f"<p>{E(p)}</p>" for p in s["what"])
    if s.get("for"):
        if s.get("for_h"): body += f'<h3>{E(s["for_h"])}</h3>'
        body += checks(s["for"])
    out.append(f'''{sec.open()}
  <div class="wrap split">
    <div class="rv-in"><span class="eyebrow">{E(dept)}</span><h2>{E(s["what_h"])}</h2></div>
    <div class="prose">{body}</div>
  </div>
</section>''')

    if s.get("steps"):
        lis = "".join(f"<li><h3>{E(t)}</h3><p>{E(d)}</p></li>" for t, d in s["steps"])
        out.append(f'''{sec.open()}
  <div class="wrap">
    <div class="sec-head rv-in"><span class="eyebrow">مراحل العلاج</span><h2>{E(s.get("steps_h") or "خطوة بخطوة")}</h2></div>
    <ol class="process">{lis}</ol>
  </div>
</section>''')

    if s.get("features"):
        cards = "".join(f'<article class="feature rv-in"><h3>{E(t)}</h3><p>{E(d)}</p></article>' for t, d in s["features"])
        out.append(f'{sec.open()}<div class="wrap"><div class="features">{cards}</div></div></section>')

    out.append(f'''{sec.open()}
  <div class="wrap split">
    <div class="rv-in"><span class="eyebrow">لماذا تاج إيليت</span><h2>{E(s.get("why_h") or "ما يميز " + s["name"] + " لدينا")}</h2></div>
    {checks(s["why"])}
  </div>
</section>''')

    if s.get("cases"):
        out.append(cases_block(sec, s["cases"]))

    out.append(faq_block(sec, s["faq"], f'عن {s["name"]}'))

    out.append(f'''{sec.open()}
  <div class="wrap">
    <div class="sec-head rv-in"><span class="eyebrow">علاجات ذات صلة</span><h2>قد يهمك أيضًا</h2></div>
    {tcards(s["related"], "tcards three")}
  </div>
</section>''')
    out.append(cta_band(wa_text))
    out.append(tail())
    write(s["slug"], "\n".join(out))

# ---------------------------------------------------------------- doctors
def doctor_page(p):
    d = DOCTORS[p["key"]]
    path = f'/{d["slug"]}/'
    trail = [("الرئيسية", "/"), ("الأطباء", "/#doctors"), (d["name"], None)]
    wa_text = f'مرحبًا، أرغب بحجز استشارة مع {d["name"]} في تاج إيليت.'
    person = {"@context": "https://schema.org", "@type": "Physician", "name": d["name"], "medicalSpecialty": "Dentistry",
              "description": p["desc"], "image": f'{SITE}/assets/img/{d["img"]}', "worksFor": {"@type": "Dentist", "name": "Taj Elite Dental Clinics"}}
    sec = Sections()
    out = [head(p["title"], p["desc"], path, [breadcrumb_ld(trail, path), person])]
    out.append(f'''<section class="page-hero dark">
  <div class="wrap ph-grid">
    <div>
      {crumbs(trail)}
      <h1>{E(d["name"])}</h1>
      <p class="lede"><b style="color:var(--on-deep);font-weight:600">{E(d["role"])}</b> · {E(p["exp"])}<br>{E(p["lede"])}</p>
      <div class="cta">
        <a class="btn" href="{wa(wa_text)}" target="_blank" rel="noopener">{icon("chat")}احجز مع {E(d["name"])}</a>
        <a class="btn ghost" href="tel:{PHONE_TEL}">{icon("phone")}<span dir="ltr">059 895 7544</span></a>
      </div>
    </div>
    <div class="ph-arch"><div class="fr"><img src="/assets/img/{d["img"]}" width="640" height="640" alt="{E(d["name"])}" style="object-position:30% 20%" fetchpriority="high"></div></div>
  </div>
</section>''')
    about = "".join(f"<p>{E(x)}</p>" for x in p["about"])
    out.append(f'''{sec.open()}
  <div class="wrap split">
    <div class="rv-in"><span class="eyebrow">نبذة</span><h2>عن {E(d["name"])}</h2></div>
    <div class="prose">{about}<h3>مجالات الخبرة</h3>{checks(p["areas"])}</div>
  </div>
</section>''')
    out.append(f'''{sec.open()}
  <div class="wrap">
    <div class="sec-head rv-in"><span class="eyebrow">العلاجات</span><h2>علاجات يجريها {E(d["name"])}</h2></div>
    {tcards(p["services"])}
  </div>
</section>''')
    if p.get("cases"):
        out.append(cases_block(sec, p["cases"], f'حالات {d["name"]}'))
    if p.get("reviews"):
        cards = "".join(f'<article class="rv"><div class="stars" aria-label="٥ من ٥">★★★★★</div><blockquote>{E(t)}</blockquote>'
                        f'<footer><b>{E(n)}</b><span>مراجعة Google</span></footer></article>' for n, t in p["reviews"])
        out.append(f'''<section class="reviews dark">
  <div class="wrap">
    <div class="sec-head rv-in"><span class="eyebrow">آراء المراجعين</span><h2>بكلماتهم، كما كتبوها على Google</h2></div>
    <div class="rv-track" tabindex="0" aria-label="مراجعات المراجعين، مرّر أفقيًا">{cards}</div>
    <p class="rv-src">مراجعات منشورة على صفحة المجمع في خرائط Google، منقولة كما هي مع تصحيح إملائي بسيط.</p>
  </div>
</section>''')
    out.append(cta_band(wa_text, f'احجز استشارتك مع {d["name"]}'))
    out.append(tail())
    write(d["slug"], "\n".join(out))

# ---------------------------------------------------------------- articles
def news_page():
    path = "/news/"
    trail = [("الرئيسية", "/"), ("المقالات", None)]
    cards = []
    for title, iso, label, excerpt, href in ARTICLES:
        go = "احجز استشارة" if href.startswith("/#") else "اقرأ عن العلاج"
        t = f'<time datetime="{iso}">{E(label)}</time>' if iso else '<span class="tag">مقال</span>'
        cards.append(f'<a class="post rv-in" href="{href}">{t}<h2>{E(title)}</h2><p>{E(excerpt)}</p><span class="go">{go}{icon("arrow")}</span></a>')
    out = [head("مقالات طب الأسنان والتجميل | تاج إيليت", "مقالات عن زراعة الأسنان وتجميلها والتقويم والجلدية من مجمع تاج إيليت في جنوب الرياض.", path,
                [breadcrumb_ld(trail, path)])]
    out.append(f'''<section class="page-hero dark">
  <div class="wrap">
    {crumbs(trail)}
    <h1>المقالات</h1>
    <p class="lede">إجابات واضحة عن العلاجات التي نقدمها، لتعرف خياراتك قبل زيارتك.</p>
  </div>
</section>
<section class="pg-sec"><div class="wrap"><div class="posts">{"".join(cards)}</div></div></section>''')
    out.append(cta_band("مرحبًا، لدي سؤال عن العلاج في تاج إيليت.", "عندك سؤال عن حالتك؟"))
    out.append(tail())
    write("news", "\n".join(out))

# ---------------------------------------------------------------- old URLs
def redirect_stub(slug, target):
    write(slug, f'''<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8">
<title>تاج إيليت</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="{SITE}{target}">
<meta http-equiv="refresh" content="0; url={target}">
<script>location.replace({json.dumps(target)})</script>
</head><body><p><a href="{target}">انتقل إلى الصفحة</a></p></body></html>
''')

if __name__ == "__main__":
    inject_index()      # homepage: promo pill, treatment image cards, offers section
    load_shell()        # then copy the (updated) header/footer to every inner page
    for s in SERVICES: service_page(s)
    for p in DOCTOR_PAGES: doctor_page(p)
    news_page()
    for slug, target in REDIRECTS.items(): redirect_stub(slug, target)
    # sitemap for search engines
    urls = ["/"] + [f'/{s["slug"]}/' for s in SERVICES] + [f'/{DOCTORS[p["key"]]["slug"]}/' for p in DOCTOR_PAGES] + ["/news/"]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + \
         "".join(f"  <url><loc>{SITE}{u}</loc></url>\n" for u in urls) + "</urlset>\n"
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(sm)
    print(f"built {len(SERVICES)} treatment pages, {len(DOCTOR_PAGES)} doctor pages, news, {len(REDIRECTS)} redirects, sitemap")

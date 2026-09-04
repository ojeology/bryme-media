#!/usr/bin/env python3
"""BRYME v18 · Clean Netflix-style deep-link page rebuild.
Landing via a video link now shows:
  1) FULL-SCREEN TRAILER at the very top — nothing above it.
  2) Below: only relevant info — title, meta, languages, synopsis, cast,
     Play/Trailer buttons, icon actions, More-Like-This / More-Details tabs,
     and editorial content (if present). No duplicate poster/thumbnail below.
Rebuilds <main> from scratch, extracting the pieces that exist."""
import json, os, re, sys, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def esc(s): return H.escape(str(s), quote=True)

def parse_ld(s):
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
    if not m: return {}
    try:
        d = json.loads(m.group(1))
    except Exception:
        return {}
    items = d if isinstance(d, list) else [d]
    for it in items:
        if isinstance(it, dict) and it.get('@type') in ('Movie', 'TVSeries', 'Anime'):
            return it
    return {}

def detail_rows(ld):
    rows = []
    d = ld.get('director')
    if isinstance(d, list):
        d = ', '.join(x.get('name', '') if isinstance(x, dict) else str(x) for x in d)
    if d: rows.append(('Director', d))
    a = ld.get('actor') or []
    names = []
    for x in a:
        if isinstance(x, str): names.append(x)
        elif isinstance(x, dict) and x.get('name'): names.append(x['name'])
    if names: rows.append(('Cast', ', '.join(names[:12])))
    g = ld.get('genre')
    if g: rows.append(('Genres', ', '.join(g) if isinstance(g, list) else str(g)))
    dur = ld.get('duration')
    if dur:
        m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', dur)
        if m:
            h, mi = m.group(1), m.group(2)
            rows.append(('Runtime', (h + 'h ' if h else '') + (mi + 'm' if mi else '')))
    lang = ld.get('inLanguage')
    if lang:
        rows.append(('Audio', lang if isinstance(lang, str) else ', '.join(x.get('name','') if isinstance(x,dict) else str(x) for x in (lang if isinstance(lang,list) else [lang]))))
    if ld.get('dateCreated'): rows.append(('Year', str(ld['dateCreated'])))
    return rows

def rebuild(path):
    s = open(path, encoding='utf-8').read()
    orig = s
    # Never turn a type-mismatch redirect stub back into a full title page.
    # Those /movie/<series-or-anime-slug>/ copies must stay noindex + refresh.
    if 'has moved' in s.lower() and ('noindex' in s or 'http-equiv="refresh"' in s):
        return False
    norm = path.replace('\\', '/')
    if '/movie/' in norm:
        slug = os.path.basename(os.path.dirname(path))
        if os.path.exists(os.path.join(ROOT, 'series', slug, 'index.html')) or os.path.exists(os.path.join(ROOT, 'anime', slug, 'index.html')):
            return False
    td = 'series' if '/series/' in path else 'anime' if '/anime/' in path else 'movie'
    type_label = 'SERIES' if td == 'series' else 'ANIME' if td == 'anime' else 'FILM'
    i = s.find('<main'); j = s.find('</main>')
    if i < 0 or j < 0: return False
    body = s[i:j+len('</main>')]
    inner = s[i+len('<main class="shell tp-page">'):j] if '<main class="shell tp-page">' in s else s[i+len('<main'):j]

    # ---- extract pieces ----
    def grab(pat, text, flags=re.S):
        m = re.search(pat, text, flags)
        return m.group(0) if m else ''

    def balance(html):
        # repair tag imbalance left by earlier transforms (v17 displaced closes)
        while html.count('</div>') > html.count('<div'):
            idx = html.rfind('</div>')
            if idx < 0: break
            html = html[:idx] + html[idx + len('</div>'):]
        while html.count('</section>') < html.count('<section'):
            html = html.rstrip() + '</section>'
        return html

    crumb = grab(r'<div class="crumb">.*?</div>', inner)
    hero_bar = grab(r'<div class="nm-hero-bar">.*?</div>', inner)
    # copy the whole trailer box (data-trailer-box wrapper) so the play handler wires up
    tsec = grab(r'<section class="[^"]*trailer-section[^"]*"[^>]*>.*?</section>', inner)
    trailer_box = ''
    if tsec:
        trailer_box = tsec
        trailer_box = re.sub(r'</?section[^>]*>', '', trailer_box).strip()
    trailer_frame = grab(r'<div class="trailer-frame"[^>]*>.*?</div>', inner)

    # title block from movie-hero
    hero_sec = grab(r'<section class="movie-hero[^"]*"[^>]*>.*?</section>', inner)
    tb = hero_sec
    tb = re.sub(r'<div class="nm-hero-bar">.*?</div>', '', tb, flags=re.S)
    tb = re.sub(r'<button[^>]*class="[^"]*nm-play-overlay[^"]*"[^>]*>.*?</button>', '', tb, flags=re.S)
    tb = re.sub(r'<div class="poster">.*?</div>', '', tb, flags=re.S)
    tb = re.sub(r'<div class="nm-icon-actions">.*?</div>', '', tb, flags=re.S)
    tb = re.sub(r'</?section[^>]*>', '', tb)
    tb = tb.strip()
    if tb.startswith('<div>') and tb.rstrip().endswith('</div>'):
        tb = tb[5:-6].strip()
    # keep only kicker/h1/badges/lead/hero-actions; drop quiet-links (clutter)
    kicker = grab(r'<div class="hero-kicker[^"]*"[^>]*>.*?</div>', tb)
    h1 = grab(r'<h1>.*?</h1>', tb)
    badges = grab(r'<div class="badges">.*?</div>', tb)
    leads = ''.join(grab(r'<p class="lead"[^>]*>.*?</p>', tb))
    actions = grab(r'<div class="hero-actions">.*?</div>', tb)
    # actions: keep only the 2 cta links
    ctas = re.findall(r'<a class="cta[^"]*"[^>]*>.*?</a>', actions, re.S)
    actions_html = '<div class="hero-actions">' + ''.join(ctas) + '</div>' if ctas else actions

    # languages + cast from nm-detail-extra
    extra = grab(r'<section class="nm-detail-extra">.*?</section>', inner)
    langs = grab(r'<div class="nm-lang-tabs">.*?</div>', extra)
    cast = grab(r'<div class="nm-cast-row">.*?</div>', extra)

    icons = grab(r'<div class="nm-icon-actions">.*?</div>', inner)
    if not icons:
        sh = re.search(r'data-share-path="([^"]+)"', s)
        share_path = sh.group(1) if sh else '/' + td + '/' + (path.split('/')[-2] if '/' in path else '') + '/'
        title = re.sub(r'<[^>]+>', '', h1).strip() if h1 else ''
        icons = ('<div class="nm-icon-actions">'
                 '<button type="button" class="nm-icon-action" data-nm-my-list><svg viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg><span>My List</span></button>'
                 '<button type="button" class="nm-icon-action" data-nm-rate><svg viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg><span>Rate</span></button>'
                 '<button type="button" class="nm-icon-action nm-share" data-share-path="' + esc(share_path) + '" data-share-title="' + esc(title) + '"><svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg><span>Share</span></button>'
                 '</div>')

    # More-Like-This list + editorial from the (messy) tabs region
    ml_open = '<div class="nm-panel is-on" id="nm-ml">'
    md_open = '<div class="nm-panel" id="nm-md">'
    mi = inner.find(ml_open); mdi = inner.find(md_open)
    loved_list = ''
    editorial = ''
    if mi > -1 and mdi > -1:
        region = inner[mi + len(ml_open):mdi]
        loved_list = balance(grab(r'<div class="tp-loved-list">.*?</div>', region))
        tl = region.find('<section class="tp-loved')
        if tl > -1:
            sec_end = region.find('</section>', tl)
            if sec_end > -1:
                after = region[sec_end + len('</section>'):]
                last_div = after.rfind('</div>')
                editorial = balance((after[:last_div] if last_div > -1 else after).strip())
    else:
        # clean (pre-v17) input: tp-loved + editorial sit directly in main
        loved_list = balance(grab(r'<div class="tp-loved-list">.*?</div>', inner))
        tl = inner.find('<section class="tp-loved')
        if tl > -1:
            sec_end = inner.find('</section>', tl)
            if sec_end > -1:
                editorial = balance(inner[sec_end + len('</section>'):].strip())

    # More-Details rows from JSON-LD
    ld = parse_ld(s)
    rows = detail_rows(ld)
    rows_html = ''.join(
        f'<div class="nm-detail-row"><div class="nm-detail-label">{esc(k)}</div><div class="nm-detail-value">{esc(v)}</div></div>'
        for k, v in rows) if rows else '<p class="nm-detail-empty">More details coming soon.</p>'

    # ---- rebuild ----
    if trailer_box or trailer_frame:
        embed = trailer_box or trailer_frame
        video_hero = ('<section class="nm-video-hero">' + hero_bar +
                      '<div class="nm-trailer-embed">' + embed + '</div></section>')
    else:
        video_hero = ''

    tabs = ('<div class="nm-tabs"><div class="nm-tabbar">'
            '<button type="button" class="nm-tab is-on" data-nm-tab="ml">More Like This</button>'
            '<button type="button" class="nm-tab" data-nm-tab="md">More Details</button></div>'
            '<div class="nm-panel is-on" id="nm-ml">' + (loved_list or '<p class="nm-detail-empty">More titles coming soon.</p>') + '</div>'
            '<div class="nm-panel" id="nm-md"><div class="nm-details-list">' + rows_html + '</div></div></div>')

    inner_bits = [
        '<div class="nm-brandline"><span class="nm-bn">BRY</span><span class="nm-bt">' + type_label + '</span></div>',
        h1,
        badges,
        leads,
        actions_html,
    ]
    if langs:
        inner_bits.append('<div class="nm-lang-row">' + langs + '</div>')
    if cast:
        inner_bits.append('<div class="nm-cast-row-wrap">' + cast + '</div>')
    if icons:
        inner_bits.append(icons)
    inner_bits.append(tabs)
    if editorial:
        inner_bits.append('<div class="nm-editorial">' + editorial + '</div>')

    body_inner = '\n    '.join(b for b in inner_bits if b)
    new_main = ('<main class="tp-page">' +
                video_hero +
                '<div class="nm-body"><div class="nm-body-inner">' +
                (('<div class="nm-crumb">' + crumb + '</div>') if crumb else '') +
                body_inner +
                '</div></div></main>')
    # self-balance: pad any missing closes so the page is always valid
    for tag, op, cl in (('div', '<div', '</div>'), ('section', '<section', '</section>')):
        need = new_main.count(op) - new_main.count(cl)
        if need > 0:
            new_main = new_main[:new_main.rfind('</main>')] + (cl * need) + '</main>'
    s = s[:i] + new_main + s[j+len('</main>'):]
    if s != orig:
        open(path, 'w', encoding='utf-8').write(s)
        return True
    return False

if __name__ == '__main__':
    n = 0; skipped = []
    for td in ('movie', 'series', 'anime'):
        for root, dirs, files in os.walk(os.path.join(ROOT, td)):
            if 'index.html' in files:
                p = os.path.join(root, 'index.html')
                try:
                    if rebuild(p): n += 1
                except Exception as e:
                    skipped.append((p, str(e)))
    print('rebuilt pages:', n)
    if skipped:
        print('skipped/errors:', len(skipped))
        for p, e in skipped[:10]: print('  ', p, e)

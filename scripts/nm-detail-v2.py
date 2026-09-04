#!/usr/bin/env python3
"""BRYME v17 · Netflix-style title-page landing (WhatsApp/Bing deep-link view).
Restyles every movie/series/anime page to the supplied Netflix reference:
full-bleed hero + play overlay, meta row (% match · year · age · runtime · HD),
languages, Play button (NO download), synopsis + cast, icon actions,
More Like This / More Details tabs. Missing data fields are simply omitted."""
import json, os, re, sys, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def esc(s): return H.escape(str(s), quote=True)

POSTERS = {}
try:
    POSTERS = json.load(open(os.path.join(ROOT, 'data/posters.json')))
except Exception:
    pass
def slug_of(path):
    parts = path.replace('\\', '/').split('/')
    # .../movie/<slug>/index.html or .../series/<slug>/index.html
    for i, p in enumerate(parts):
        if p in ('movie', 'series', 'anime') and i + 1 < len(parts):
            return parts[i + 1]
    return None

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
    if names: rows.append(('Cast', ', '.join(names[:10])))
    g = ld.get('genre')
    if g: rows.append(('Genres', ', '.join(g) if isinstance(g, list) else str(g)))
    dur = ld.get('duration')
    if dur:
        m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', dur)
        if m:
            h, mi = m.group(1), m.group(2)
            rows.append(('Runtime', (h + 'h ' if h else '') + (mi + 'm' if mi else '')))
    lang = ld.get('inLanguage')
    if lang: rows.append(('Audio', lang if isinstance(lang, str) else ', '.join(x.get('name','') if isinstance(x,dict) else str(x) for x in (lang if isinstance(lang,list) else [lang]))))
    if ld.get('dateCreated'): rows.append(('Year', str(ld['dateCreated'])))
    return rows

def upgrade(path):
    s = open(path, encoding='utf-8').read()
    orig = s
    slug = slug_of(path)
    poster_url = POSTERS.get(slug) or ''
    # 1) fix mangled double-src posters + set the authoritative poster url
    def fix_src(m):
        cur = m.group(1)
        if 'hqdefault.jpg' in cur and cur.count('hqdefault.jpg') > 1:
            cur = cur[:cur.index('hqdefault.jpg') + len('hqdefault.jpg')]
        return 'src="' + (poster_url or cur) + '"'
    s = re.sub(r'src="([^"]*?)"', fix_src, s, count=1)
    # 2) hero backdrop: use the poster url when placeholder/missing
    m = re.search(r'(<section class="movie-hero[^"]*" style="--movie-backdrop:url\(\')([^\']*?)(\'\)")', s)
    if m and ('placeholder' in m.group(2) or 'hqdefault.jpg' == m.group(2)) and poster_url:
        s = s[:m.start(2)] + poster_url + s[m.end(2):]
    ld = parse_ld(s)
    td = 'series' if '/series/' in path else 'anime' if '/anime/' in path else 'movie'
    type_label = 'SERIES' if td == 'series' else 'ANIME' if td == 'anime' else 'FILM'

    # 3) play overlay into the hero
    if 'nm-play-overlay' not in s:
        play = ('<button type="button" class="nm-play-overlay" onclick="var t=document.getElementById(\'trailer\');'
                'if(t){t.scrollIntoView({behavior:\'smooth\'});}else{var w=document.querySelector(\'[data-hero-watch]\');if(w)w.click();}"'
                ' aria-label="Play trailer"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></button>')
        # insert right after <section class="movie-hero ...">
        m = re.search(r'(<section class="movie-hero[^"]*"[^>]*>)', s)
        if m:
            s = s[:m.end()] + play + s[m.end():]

    # 4) icon actions after hero-actions close
    if 'nm-icon-actions' not in s:
        icons = ('<div class="nm-icon-actions">'
                 '<button type="button" class="nm-icon-action" data-nm-my-list><svg viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg><span>My List</span></button>'
                 '<button type="button" class="nm-icon-action" data-nm-rate><svg viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg><span>Rate</span></button>'
                 '<button type="button" class="nm-icon-action nm-share" data-share-path="' + (re.search(r"data-share-path=\"([^\"]+)\"", s) or [None, '/'])[1] + '" data-share-title="' + esc((re.search(r'<h1>([^<]+)</h1>', s) or [None, ''])[1]) + '"><svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg><span>Share</span></button>'
                 '</div>')
        m = re.search(r'(</div>\s*</section>\s*<section class="nm-detail-extra")', s)
        if not m:
            m = re.search(r'(</section>\s*<section class="shell trailer-section")', s)
        if m:
            s = s[:m.start()] + icons + s[m.start():]

    # 5) Tabs: wrap tp-loved into More Like This + add More Details tab
    if 'nm-tabs' not in s:
        m = re.search(r'(<section class="tp-loved[^"]*"[^>]*>)', s)
        if m:
            tab_start = ('<div class="nm-tabs"><div class="nm-tabbar">'
                         '<button type="button" class="nm-tab is-on" data-nm-tab="ml">More Like This</button>'
                         '<button type="button" class="nm-tab" data-nm-tab="md">More Details</button></div>')
            # more-like panel wraps the tp-loved section content
            ml_panel = '<div class="nm-panel is-on" id="nm-ml">'
            # details panel
            rows = detail_rows(ld)
            rows_html = ''.join(
                f'<div class="nm-detail-row"><div class="nm-detail-label">{esc(k)}</div><div class="nm-detail-value">{esc(v)}</div></div>'
                for k, v in rows) if rows else '<p class="nm-detail-empty">More details coming soon.</p>'
            md_panel = ('</div><div class="nm-panel" id="nm-md">'
                        '<div class="nm-details-list">' + rows_html + '</div>')
            s = s[:m.start()] + tab_start + ml_panel + s[m.start():]
            # close panels + tabs after tp-loved section closes
            m2 = re.search(r'(</section>\s*</main>)', s)
            if m2:
                s = s[:m2.start()] + md_panel + '</div></div>' + s[m2.start():]

    if s != orig:
        open(path, 'w', encoding='utf-8').write(s)
        return True
    return False

if __name__ == '__main__':
    n = 0
    for td in ('movie', 'series', 'anime'):
        for root, dirs, files in os.walk(os.path.join(ROOT, td)):
            if 'index.html' in files:
                p = os.path.join(root, 'index.html')
                if upgrade(p): n += 1
    print('upgraded pages:', n)

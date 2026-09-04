#!/usr/bin/env python3
"""Posterize the BRYME catalog.
Poster source order: data/movies.json poster > official trailer thumbnail
(https://i.ytimg.com/vi/<vid>/hqdefault.jpg) > local assets/posters/<slug>.jpg > gradient monogram.
Writes data/posters.json, updates title pages, and rebuilds /entertainment/ cards."""
import json, os, re, sys, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from nm_catalog import CATALOG, unique

def esc(s): return H.escape(str(s), quote=True)

uniq = unique()  # slug -> (title, td, rating, year, cert)
movies = json.load(open(os.path.join(ROOT, 'data/movies.json')))
items = movies if isinstance(movies, list) else movies.get('movies', [])
by = {x.get('slug'): x for x in items if isinstance(x, dict)}
emb = json.load(open(os.path.join(ROOT, 'scripts/embeds.json')))

POSTERS = {}
for slug, (title, td, rating, year, cert) in uniq.items():
    rec = by.get(slug) or {}
    # Priority: committed real poster > data poster (if not a yt thumb) > yt thumb fallback
    local = next((e for e in ('.jpg', '.png', '.webp') if os.path.exists(os.path.join(ROOT, 'assets', 'posters', slug + e))), None)
    if local:
        POSTERS[slug] = f'/assets/posters/{slug}{local}'
    elif rec.get('poster') and 'i.ytimg.com' not in rec['poster']:
        POSTERS[slug] = rec['poster']
    elif emb.get(slug):
        POSTERS[slug] = f'https://i.ytimg.com/vi/{emb[slug]}/hqdefault.jpg'
    # else: leave out -> gradient monogram fallback

json.dump(POSTERS, open(os.path.join(ROOT, 'data', 'posters.json'), 'w'), indent=1)
print('posters mapped:', len(POSTERS), '/', len(uniq))

def poster_html(slug, title):
    url = POSTERS.get(slug)
    if url:
        return (f'<img loading="lazy" decoding="async" width="480" height="360" src="{esc(url)}" '
                f'alt="{esc(title)} poster">')
    return None

# ---- update title pages: swap placeholder poster for real img ----
updated = 0
for slug, (title, td, rating, year, cert) in uniq.items():
    p = os.path.join(ROOT, td, slug, 'index.html')
    if not os.path.exists(p):
        continue
    s = open(p, encoding='utf-8').read()
    if POSTERS.get(slug) and '<img loading="lazy" decoding="async" width="480" height="360" src="' not in s:
        # replace <div class="placeholder" ...>...</div> inside <div class="poster"> with an img
        ph = re.search(r'(<div class="poster">)(<div class="placeholder"[^>]*>.*?</div>)(</div>)', s, re.S)
        if ph:
            img = poster_html(slug, title)
            if img:
                s = s[:ph.start(2)] + img + s[ph.end(2):]
                open(p, 'w', encoding='utf-8').write(s)
                updated += 1
print('title pages posterized:', updated)

# ---- rebuild /entertainment/ cards with posters ----
def card(slug, title, td, rating, year, cert, t10_rank=None):
    tb = 'tb-series' if td == 'series' else 'tb-anime' if td == 'anime' else 'tb-movie'
    tlabel = 'SERIES' if td == 'series' else 'ANIME' if td == 'anime' else 'MOVIE'
    url = POSTERS.get(slug)
    if url:
        img = f'<img loading="lazy" decoding="async" width="480" height="360" src="{esc(url)}" alt="{esc(title)} poster">'
    else:
        img = f'<div class="placeholder" style="background:#1a1a2e;color:#fff;font-size:28px;font-weight:800">{esc((title.strip().split()[0][0] if title.strip() else "?").upper())}</div>'
    rank = f'<span class="rank top">{t10_rank}</span>' if t10_rank else ''
    badge = f'<span class="type-badge {tb}">{tlabel}</span>'
    rat = f'<p class="tile-rating" title="BRYME editorial score">\u2605 {rating}</p>' if rating else ''
    return (f'<a class="tile" href="/{td}/{slug}/"><div class="poster">{img}{rank}<span class="tile-play" aria-hidden="true"></span>{badge}</div>'
            f'<h3>{esc(title)}</h3><div class="tile-meta"><span>{year}</span><span class="sep">\u00b7</span><span>{esc(tlabel.title())}</span></div>{rat}</a>')

def build_ent():
    rows = []
    for h2, entries in CATALOG.items():
        t10 = h2.startswith('\U0001f525')
        cards = ''.join(card(slug, title, td, rating, year, cert, (i + 1) if t10 else None)
                        for i, (title, slug, td, rating, year, cert) in enumerate(entries))
        cls = 'rail rail-t10' if t10 else 'rail'
        rows.append(f'<section class="home-section"><div class="shell"><div class="section-head"><div><h2>{esc(h2)}</h2></div></div>'
                    f'<div class="{cls}">{cards}</div></div></section>')
    ent = os.path.join(ROOT, 'entertainment', 'index.html')
    s = open(ent, encoding='utf-8').read()
    # replace the whole <main>...</main> block
    m = re.search(r'<main[^>]*>.*?</main>', s, re.S)
    if not m:
        print('ERR: no <main> in entertainment'); return
    cta = ('<section class="nm-search-cta"><div class="nm-search-cta-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg></div>'
           '<h3>Can\'t find what you\'re looking for?</h3><p>Search any movie or show by name — instant results from the full BRYME catalogue.</p>'
           '<a class="nm-btn nm-btn-primary" href="/search/">Search Now</a></section>')
    # preserve hero section
    hero = re.search(r'<section class="hero-carousel".*?</section>', s, re.S).group(0)
    new_main = '<main class="ent">' + hero + ''.join(rows) + cta + '</main>'
    s = s[:m.start()] + new_main + s[m.end():]
    open(ent, 'w', encoding='utf-8').write(s)
    print('entertainment rebuilt with', len(uniq), 'unique titles')

if __name__ == '__main__':
    build_ent()

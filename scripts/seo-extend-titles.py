#!/usr/bin/env python3
"""BRYME SEO extension — apply the pilot's intent-aware <title> pattern across the
wider catalogue. Tiered by what the page ACTUALLY contains (never claims "Cast" or
"Where to Watch" on pages lacking them). Meta descriptions are left untouched here
to avoid near-duplicate endings across hundreds of pages (brief §14)."""
import json, os, re, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def esc(s): return H.escape(str(s), quote=True)

movies = json.load(open(os.path.join(ROOT, 'data/movies.json')))

done = 0
skipped = 0
for m in movies:
    slug = m.get('slug') or m.get('id')
    tdir = m.get('typeDir') or ('series' if m.get('legacyType') == 'legacy-series' else 'anime' if m.get('legacyType') == 'legacy-anime' else 'movie')
    if not slug: continue
    p = os.path.join(ROOT, tdir, slug, 'index.html')
    if not os.path.exists(p): continue
    html = open(p, encoding='utf-8').read()

    # skip pages already carrying an intent title
    t = re.search(r'<title>(.*?)</title>', html, re.S)
    if not t: continue
    cur = H.unescape(t.group(1)).strip()
    if 'Where to Watch' in cur or 'Cast' in cur:
        skipped += 1
        continue

    # what does this page actually have?
    has_t = 'data-trailer-box' in html
    has_c = 'nm-cast-item' in html
    has_w = 'id="watch"' in html or 'tp-watch' in html or 'where to watch legally' in html.lower()

    title = H.unescape(re.sub(r'\s*\|\s*BRYME\s*$', '', cur)).strip()
    year = ''
    ym = re.search(r'\((\d{4})\)', title)
    if ym:
        year = ym.group(1)
        title = title[:ym.start()].strip()

    if has_t and has_c and has_w:
        offer = 'Cast, Trailer, Episodes & Where to Watch' if tdir == 'series' else ('Trailer, Cast & Where to Watch' if tdir == 'anime' else 'Cast, Trailer & Where to Watch')
    elif has_t and has_w:
        offer = 'Trailer & Where to Watch'
    elif has_t and has_c:
        offer = 'Cast & Trailer'
    elif has_t:
        offer = 'Trailer'
    elif has_c:
        offer = 'Cast & Story'
    else:
        offer = 'Overview'

    new_title = f"{title} ({year})" if year else title
    new_title += f" | {offer} | BRYME"

    html2 = re.sub(r'<title>.*?</title>', f'<title>{esc(new_title)}</title>', html, count=1, flags=re.S)
    html2 = re.sub(r'<meta property="og:title" content="[^"]*"', f'<meta property="og:title" content="{esc(new_title)}"', html2, count=1)
    html2 = re.sub(r'<meta name="twitter:title" content="[^"]*"', f'<meta name="twitter:title" content="{esc(new_title)}"', html2, count=1)
    if html2 != html:
        open(p, 'w', encoding='utf-8').write(html2)
        done += 1

print(f"title-optimized: {done} pages | already optimized: {skipped}")

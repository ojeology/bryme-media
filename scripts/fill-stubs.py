#!/usr/bin/env python3
"""BRYME · fill the 155 'has moved' stubs with full v18 content.

Every stub is a legacy movie/<slug> duplicate of a full series/<slug> or
anime/<slug> page. This builds a complete Netflix-style deep-link page from
data/movies.json + scripts/embeds.json, keeps the canonical pointing at the
sibling (no duplicate-content signal), and removes noindex.
"""
import json, os, re, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def esc(s): return H.escape(str(s), quote=True)
def unesc(s): return H.unescape(str(s))

SITE = 'https://bryme.onrender.com'
movies = json.load(open(os.path.join(ROOT, 'data/movies.json')))
embeds = json.load(open(os.path.join(ROOT, 'scripts/embeds.json')))
posters = json.load(open(os.path.join(ROOT, 'data/posters.json')))
by_id = {m['id']: m for m in movies}
by_slug = {m.get('slug'): m for m in movies if m.get('slug')}

def sibling_type(path):
    """derive the real type (series/anime/movie) from the stub's canonical target"""
    html = open(path, encoding='utf-8').read()
    m = re.search(r'<link rel="canonical" href="https://bryme\.onrender\.com/([^/"]+)/', html)
    t = m.group(1) if m else None
    return t if t in ('movie', 'series', 'anime') else 'movie'

def find_stubs():
    stubs = []
    for root in ('movie', 'series', 'anime'):
        for slug in os.listdir(os.path.join(ROOT, root)):
            p = os.path.join(ROOT, root, slug, 'index.html')
            if os.path.exists(p) and 'has moved' in open(p, encoding='utf-8').read():
                stubs.append((root, slug))
    return stubs

def poster_for(slug):
    if slug in posters:
        v = posters[slug]
        return v if v.startswith('http') else SITE + v
    for ext in ('jpg', 'png', 'webp', 'jpeg'):
        if os.path.exists(os.path.join(ROOT, f'assets/posters/{slug}.{ext}')):
            return f'{SITE}/assets/posters/{slug}.{ext}'
    return None

def yt_thumb(vid): return f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg'

def sibling_data(slug, type_dir):
    """copy description from the full sibling page (series/ or anime/ etc.)"""
    for root in ('series', 'anime', 'movie'):
        p = os.path.join(ROOT, root, slug, 'index.html')
        if not os.path.exists(p): continue
        html = open(p, encoding='utf-8').read()
        if 'has moved' in html: continue
        ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        if ld:
            try:
                d = json.loads(ld.group(1))
                items = d if isinstance(d, list) else [d]
                for it in items:
                    if isinstance(it, dict) and it.get('@type') in ('Movie', 'TVSeries'):
                        return it
            except Exception:
                pass
    return {}

def genre_link(genre, type_dir):
    prefix = type_dir if type_dir in ('movie', 'series', 'anime') else 'movies'
    if prefix == 'movie':
        prefix = 'movies'
    return f'/{prefix}/{genre.lower().replace(" ", "-")}/'

def build(record, slug, type_dir, live_yt):
    title = record.get('title') or slug.replace('-', ' ').title()
    year = record.get('year') or ''
    genres = record.get('genres') or []
    if not genres and record.get('genre'):
        genres = [record['genre']]
    genre_str = genres[0] if genres else 'Film'
    cast = record.get('cast') or []
    director = record.get('director') or ''
    if isinstance(director, str):
        directors = [d.strip() for d in director.split(';') if d.strip()]
    else:
        directors = director
    desc = record.get('description') or record.get('teaser') or ''
    lang = record.get('language') or ''
    country = record.get('country') or ''
    rating = record.get('rating')
    trending = record.get('trending') or False
    popular = record.get('popular') or False
    edpick = record.get('editorPick') or False
    ednote = record.get('editorPickNote') or ''

    # sibling for description fallback + canonical type
    sib = sibling_data(slug, type_dir)
    if not desc:
        desc = sib.get('description') or ''
    if not desc:
        desc = f'{title} — synopsis, official trailer and watch links on BRYME.'
    # clean multi-sentence desc to lead (keep as is; it is a full synopsis)
    lead = re.sub(r'\s+', ' ', desc).strip()

    # type
    if type_dir == 'series': ld_type, label = 'TVSeries', 'SERIES'
    elif type_dir == 'anime': ld_type, label = 'TVSeries', 'ANIME'
    else: ld_type, label = 'Movie', 'FILM'
    bread = 'Series' if type_dir == 'series' else 'Anime' if type_dir == 'anime' else 'Movies'
    crumb_top = f'/series/' if type_dir == 'series' else f'/anime/' if type_dir == 'anime' else '/movies/'
    crumb_genre = genre_link(genre_str, type_dir) if genres else crumb_top

    # poster
    poster = poster_for(slug) or (yt_thumb(live_yt) if live_yt else f'{SITE}/assets/bryme-card.png')
    og_w, og_h = (480, 360) if live_yt else (1200, 630)
    img_type = 'image/jpeg'

    # ---- trailer hero ----
    if live_yt:
        trailer_box = (
            '<div class="trailer-section-inner" data-trailer-box '
            f'data-trailer-candidates="[{esc(json.dumps({"id": live_yt, "type": "official-trailer", "label": "Official Trailer", "channel": "YouTube", "verified": True, "watch": f"https://www.youtube.com/watch?v={live_yt}"}))}]" '
            f'data-trailer-title="{esc(title)}">'
            '<div class="trailer-head"><span class="eyebrow">Trailer</span><span class="trailer-status t-ok">🟢 Official Trailer</span></div>'
            f'<div class="trailer-frame" data-trailer-id="{live_yt}"><img loading="lazy" src="{yt_thumb(live_yt)}" alt="{esc(title)} trailer thumbnail"><button type="button" class="trailer-play">Play trailer</button></div>'
            '<div class="trailer-controls" data-trailer-controls hidden><button type="button" class="cta" data-trailer-unmute>Unmute</button>'
            f'<a class="quiet-link" href="https://www.youtube.com/watch?v={live_yt}" target="_blank" rel="noopener">Watch on YouTube</a></div>'
            f'<p class="trailer-meta">YouTube</p>'
            '<div class="trailer-error" data-trailer-error hidden><b>Trailer currently unavailable.</b><span>This video could not be played right now.</span>'
            '<span class="trailer-error-actions"><a class="quiet-link" data-trailer-watch href="https://www.youtube.com/watch?v=' + live_yt + '" target="_blank" rel="noopener">Watch on YouTube</a>'
            '<button type="button" class="trailer-retry" data-trailer-retry>Try again</button></span></div>'
            f'<p class="trailer-fallback">If the embedded player is unavailable, <a href="https://www.youtube.com/watch?v={live_yt}" target="_blank" rel="noopener">watch the trailer on YouTube</a>.</p></div>'
        )
        video_hero = ('<section class="nm-video-hero"><div class="nm-hero-bar">'
                      '<a class="nm-back" href="#" onclick="history.back();return false" aria-label="Go back">‹ Back</a>'
                      '<a class="nm-x" href="/" aria-label="Close">✕</a></div>'
                      '<div class="nm-trailer-embed">' + trailer_box + '</div></section>')
    else:
        video_hero = ('<section class="nm-video-hero"><div class="nm-hero-bar">'
                      '<a class="nm-back" href="#" onclick="history.back();return false" aria-label="Go back">‹ Back</a>'
                      '<a class="nm-x" href="/" aria-label="Close">✕</a></div>'
                      '<div class="nm-trailer-embed"><div class="trailer-section-inner"><div class="trailer-head">'
                      '<span class="eyebrow">Trailer</span><span class="trailer-status t-none">🎬 Trailer unavailable</span></div>'
                      '<div class="trailer-unavailable"><b>Trailer unavailable</b><span>We couldn\'t find a suitable verified trailer for this title yet.</span></div>'
                      '</div></div></section>')

    # ---- badges ----
    badges = []
    if rating:
        badges.append(f'<span class="badge" title="BRYME editorial score — not IMDb, Rotten Tomatoes or audience ratings">★ {rating}/10 · BRYME Editorial</span>')
    if trending:
        badges.append('<span class="badge" title="Editorial trending pick">🔥 Trending</span>')
    if popular:
        badges.append('<span class="badge" title="Editorial popular pick">⭐ Popular</span>')
    if edpick:
        badges.append(f'<span class="badge" title="Editorial pick">{esc(ednote or "⭐ Editor\'s Pick")}</span>')
    badges_html = f'<div class="badges">{"".join(badges)}</div>' if badges else '<div class="badges"></div>'

    # ---- actions ----
    actions = '<a class="cta nm-watch-now" href="#watch">▶ Watch Now</a>'
    if live_yt:
        actions += '<a class="cta cta-ghost nm-trailer" href="#trailer">▶ Trailer</a>'
    actions_html = f'<div class="hero-actions">{actions}</div>'

    # ---- languages ----
    langs = ''
    if lang:
        langs = f'<div class="nm-lang-row"><div class="nm-lang-tabs"><button type="button" class="nm-lang is-on">{esc(lang)}</button></div></div>'

    # ---- cast ----
    cast_html = ''
    if cast:
        items = []
        for name in cast[:12]:
            initials = ''.join(w[0] for w in name.split()[:2]).upper() if name else ''
            items.append(f'<div class="nm-cast-item"><span class="nm-avatar">{esc(initials)}</span><b>{esc(name)}</b></div>')
        cast_html = f'<div class="nm-cast-row-wrap"><div class="nm-cast-row">{"".join(items)}</div></div>'

    # ---- icon actions ----
    icons = ('<div class="nm-icon-actions">'
             '<button type="button" class="nm-icon-action" data-nm-my-list><svg viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg><span>My List</span></button>'
             '<button type="button" class="nm-icon-action" data-nm-rate><svg viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg><span>Rate</span></button>'
             f'<button type="button" class="nm-icon-action nm-share" data-share-path="/{type_dir}/{slug}/" data-share-title="{esc(title)}"><svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg><span>Share</span></button>'
             '</div>')

    # ---- More Like This (same genres) ----
    related = []
    for m in movies:
        if m.get('slug') == slug: continue
        mg = m.get('genres') or []
        if genres and set(genres) & set(mg):
            related.append(m)
        if len(related) >= 8: break
    loved = []
    for m in related[:6]:
        rslug = m.get('slug')
        rdir = m.get('typeDir') or ('series' if m.get('legacyType') == 'legacy-series' else 'anime' if m.get('legacyType') == 'legacy-anime' else 'movie')
        if not os.path.exists(os.path.join(ROOT, rdir, rslug or '', 'index.html')):
            rdir = next((r for r in ('movie','series','anime') if os.path.exists(os.path.join(ROOT, r, rslug or '', 'index.html'))), 'movie')
        rposter = poster_for(rslug) or (yt_thumb(embeds.get(rslug, '')) if embeds.get(rslug) else f'{SITE}/assets/bryme-card.png')
        rtitle = m.get('title') or rslug.replace('-',' ').title()
        rg = (m.get('genres') or [m.get('genre')] or ['Film'])[0]
        ry = m.get('year') or ''
        loved.append(
            f'<a class="tp-loved-card" href="/{rdir}/{rslug}/">'
            f'<img loading="lazy" decoding="async" width="320" height="180" src="{rposter}" alt="{esc(rtitle)} thumbnail">'
            f'<span><b>{esc(rtitle)}</b><em>{esc(rg)} · {ry}</em><small>{esc(country)} {esc(rg)} — same lane.</small></span></a>'
        )
    loved_html = f'<div class="tp-loved-list">{"".join(loved)}</div>' if loved else '<p class="nm-detail-empty">More titles coming soon.</p>'

    # ---- More Details ----
    rows = []
    if directors: rows.append(('Director', ', '.join(directors[:6])))
    if cast: rows.append(('Cast', ', '.join(cast[:12])))
    if genres: rows.append(('Genres', ', '.join(genres)))
    if country: rows.append(('Country', country))
    if lang: rows.append(('Audio', lang))
    if year: rows.append(('Year', str(year)))
    rows_html = ''.join(f'<div class="nm-detail-row"><div class="nm-detail-label">{esc(k)}</div><div class="nm-detail-value">{esc(v)}</div></div>' for k, v in rows)
    rows_html = rows_html or '<p class="nm-detail-empty">More details coming soon.</p>'

    # ---- editorial ----
    editorial = ''
    if len(lead) > 140:
        editorial = ('<div class="nm-editorial"><section>'
                     f'<p>{esc(lead)}</p>'
                     f'<p>{esc(title)} is featured on BRYME with its verified trailer and the basics you need before you watch — cast, creators, genres and where to find it legally.</p>'
                     '</section></div>')

    tabs = ('<div class="nm-tabs"><div class="nm-tabbar">'
            '<button type="button" class="nm-tab is-on" data-nm-tab="ml">More Like This</button>'
            '<button type="button" class="nm-tab" data-nm-tab="md">More Details</button></div>'
            f'<div class="nm-panel is-on" id="nm-ml">{loved_html}</div>'
            f'<div class="nm-panel" id="nm-md"><div class="nm-details-list">{rows_html}</div></div></div>')

    crumb = f'<div class="nm-crumb"><div class="crumb"><a href="/">Home</a> / <a href="{crumb_top}">{bread}</a> / <a href="{crumb_genre}">{esc(genre_str)}</a> / {esc(title)}</div></div>'

    inner_bits = [
        '<div class="nm-brandline"><span class="nm-bn">BRY</span><span class="nm-bt">' + label + '</span></div>',
        f'<h1>{esc(title)}</h1>',
        badges_html,
        f'<p class="lead">{esc(lead[:300])}</p>',
        actions_html,
    ]
    if langs: inner_bits.append(langs)
    if cast_html: inner_bits.append(cast_html)
    inner_bits.append(icons)
    inner_bits.append(tabs)
    if editorial: inner_bits.append(editorial)

    body_inner = '\n    '.join(b for b in inner_bits if b)
    new_main = ('<main class="tp-page">' + video_hero +
                '<div class="nm-body"><div class="nm-body-inner">' + crumb + body_inner +
                '</div></div></main>')

    # ---- SEO head ----
    seo_title = f'{title} ({year}) | BRYME' if year else f'{title} | BRYME'
    meta_desc = lead[:158]
    canonical_target = None  # canonical stays pointing at the sibling (set in file)
    ld_actor = [{'@type': 'Person', 'name': n} for n in cast[:8]]
    ld_director = [{'@type': 'Person', 'name': d} for d in (directors[:4] if isinstance(directors, list) else [])]
    ld = [{
        '@context': 'https://schema.org', '@type': ld_type,
        'name': title, 'description': lead,
        'dateCreated': str(year) if year else None,
        'genre': genre_str,
        'image': poster,
        'url': f'{SITE}/{type_dir}/{slug}/',
    }]
    if country: ld[0]['countryOfOrigin'] = country
    if lang: ld[0]['inLanguage'] = lang
    if ld_director: ld[0]['director'] = ld_director
    if ld_actor: ld[0]['actor'] = ld_actor
    ld = [d for d in ld if d]
    ld.append({'@context': 'https://schema.org', '@type': 'BreadcrumbList',
               'itemListElement': [
                   {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': f'{SITE}/'},
                   {'@type': 'ListItem', 'position': 2, 'name': bread, 'item': f'{SITE}{crumb_top}'},
                   {'@type': 'ListItem', 'position': 3, 'name': title, 'item': f'{SITE}/{type_dir}/{slug}/'}]})
    # VideoObject omitted unless a verified uploadDate exists (Google required field).

    return {
        'title': seo_title, 'meta_desc': meta_desc, 'poster': poster,
        'og_w': og_w, 'og_h': og_h, 'img_type': img_type,
        'new_main': new_main, 'ld': json.dumps(ld, ensure_ascii=False),
    }

def apply(path, data, slug, type_dir):
    s = open(path, encoding='utf-8').read()
    orig = s
    # title
    s = re.sub(r'<title>.*?</title>', f'<title>{esc(data["title"])}</title>', s, count=1, flags=re.S)
    # meta description
    s = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{esc(data["meta_desc"])}"', s, count=1)
    # remove noindex
    s = re.sub(r'<meta name="robots" content="noindex[^"]*">', '', s, count=1)
    # remove the old instant-refresh redirect to the sibling
    s = re.sub(r'<meta http-equiv="refresh"[^>]*>', '', s, count=1)
    # canonical — keep pointing at sibling (already in file)
    # og:title / og:description / twitter
    s = re.sub(r'<meta property="og:title" content="[^"]*"', f'<meta property="og:title" content="{esc(data["title"])}"', s, count=1)
    s = re.sub(r'<meta property="og:description" content="[^"]*"', f'<meta property="og:description" content="{esc(data["meta_desc"])}"', s, count=1)
    s = re.sub(r'<meta name="twitter:title" content="[^"]*"', f'<meta name="twitter:title" content="{esc(data["title"])}"', s, count=1)
    s = re.sub(r'<meta name="twitter:description" content="[^"]*"', f'<meta name="twitter:description" content="{esc(data["meta_desc"])}"', s, count=1)
    # og:image
    s = re.sub(r'<meta property="og:image" content="[^"]*"', f'<meta property="og:image" content="{data["poster"]}"', s, count=1)
    s = re.sub(r'<meta name="twitter:image" content="[^"]*"', f'<meta name="twitter:image" content="{data["poster"]}"', s, count=1)
    s = re.sub(r'<meta property="og:image:type" content="[^"]*"', f'<meta property="og:image:type" content="{data["img_type"]}"', s, count=1)
    s = re.sub(r'<meta property="og:image:width" content="\d+"', f'<meta property="og:image:width" content="{data["og_w"]}"', s, count=1)
    s = re.sub(r'<meta property="og:image:height" content="\d+"', f'<meta property="og:image:height" content="{data["og_h"]}"', s, count=1)
    # JSON-LD: replace existing block or insert before </head>
    ld_tag = f'<script type="application/ld+json">{data["ld"]}</script>'
    if '<script type="application/ld+json">' in s:
        s = re.sub(r'<script type="application/ld\+json">.*?</script>', ld_tag, s, count=1, flags=re.S)
    else:
        s = s.replace('</head>', ld_tag + '</head>', 1)
    # main
    i = s.find('<main'); j = s.find('</main>')
    if i < 0 or j < 0:
        raise ValueError('no <main>')
    s = s[:i] + data['new_main'] + s[j + len('</main>'):]
    if s != orig:
        open(path, 'w', encoding='utf-8').write(s)
        return True
    return False

def build_ld_only(record, slug, type_dir, live_yt, title, lead, poster):
    """JSON-LD only (for backfilling pages that render fine but lack schema)"""
    year = record.get('year') or ''
    genres = record.get('genres') or []
    if not genres and record.get('genre'):
        genres = [record['genre']]
    genre_str = genres[0] if genres else 'Film'
    cast = record.get('cast') or []
    director = record.get('director') or ''
    directors = [d.strip() for d in director.split(';') if d.strip()] if isinstance(director, str) else director
    lang = record.get('language') or ''
    country = record.get('country') or ''
    ld_type = 'TVSeries' if type_dir in ('series', 'anime') else 'Movie'
    bread = 'Series' if type_dir == 'series' else 'Anime' if type_dir == 'anime' else 'Movies'
    crumb_top = f'/{type_dir}/' if type_dir in ('series', 'anime') else '/movies/'
    ld = [{
        '@context': 'https://schema.org', '@type': ld_type,
        'name': title, 'description': lead,
        'dateCreated': str(year) if year else None,
        'genre': genre_str, 'image': poster,
        'url': f'{SITE}/{type_dir}/{slug}/',
    }]
    if country: ld[0]['countryOfOrigin'] = country
    if lang: ld[0]['inLanguage'] = lang
    if directors: ld[0]['director'] = [{'@type': 'Person', 'name': d} for d in directors[:4]]
    if cast: ld[0]['actor'] = [{'@type': 'Person', 'name': n} for n in cast[:8]]
    ld = [d for d in ld if d]
    ld.append({'@context': 'https://schema.org', '@type': 'BreadcrumbList',
               'itemListElement': [
                   {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': f'{SITE}/'},
                   {'@type': 'ListItem', 'position': 2, 'name': bread, 'item': f'{SITE}{crumb_top}'},
                   {'@type': 'ListItem', 'position': 3, 'name': title, 'item': f'{SITE}/{type_dir}/{slug}/'}]})
    # VideoObject omitted unless a verified uploadDate exists (Google required field).
    return json.dumps(ld, ensure_ascii=False)

def backfill_ld():
    """add JSON-LD to full pages that render fine but lack schema markup"""
    n = ok = 0
    for root in ('movie', 'series', 'anime'):
        for slug in os.listdir(os.path.join(ROOT, root)):
            p = os.path.join(ROOT, root, slug, 'index.html')
            if not os.path.exists(p): continue
            html = open(p, encoding='utf-8').read()
            if 'has moved' in html or 'application/ld+json' in html: continue
            if 'data-trailer-box' not in html and 'nm-video-hero' not in html: continue
            n += 1
            try:
                record = by_id.get(slug) or by_slug.get(slug) or {}
                h1 = re.search(r'<h1>(.*?)</h1>', html, re.S)
                title = re.sub(r'<[^>]+>', '', h1.group(1)).strip() if h1 else (record.get('title') or slug.replace('-', ' ').title())
                lead = re.search(r'<p class="lead"[^>]*>(.*?)</p>', html, re.S)
                lead_txt = re.sub(r'<[^>]+>', '', lead.group(1)).strip() if lead else (record.get('description') or '')
                img = re.search(r'<meta property="og:image" content="([^"]+)"', html)
                poster = img.group(1) if img else poster_for(slug) or f'{SITE}/assets/bryme-card.png'
                live_yt = embeds.get(slug) or ''
                ld = build_ld_only(record, slug, root, live_yt, title, lead_txt, poster)
                s2 = html.replace('</head>', f'<script type="application/ld+json">{ld}</script></head>', 1)
                if s2 != html:
                    open(p, 'w', encoding='utf-8').write(s2)
                    ok += 1
            except Exception as e:
                print('  ', p, str(e)[:60])
    print(f'backfill scanned {n}, added ld to {ok}')

def find_unavailable():
    """pages currently showing the 'trailer unavailable' hero"""
    out = []
    for root in ('movie', 'series', 'anime'):
        for slug in os.listdir(os.path.join(ROOT, root)):
            p = os.path.join(ROOT, root, slug, 'index.html')
            if os.path.exists(p):
                html = open(p, encoding='utf-8').read()
                if 'trailer-unavailable' in html and 'has moved' not in html:
                    out.append((root, slug))
    return out

def upgrade_unavailable():
    """rebuild pages that have trailer-unavailable but now have a verified embed"""
    n = ok = 0
    failed = []
    for root, slug in find_unavailable():
        n += 1
        p = os.path.join(ROOT, root, slug, 'index.html')
        try:
            if not embeds.get(slug):
                continue
            tdir = sibling_type(p) if root != 'movie' or True else root
            m = re.search(r'<link rel="canonical" href="https://bryme\.onrender\.com/([^/"]+)/', open(p, encoding='utf-8').read())
            if m and m.group(1) in ('movie', 'series', 'anime'):
                tdir = m.group(1)
            record = by_id.get(slug) or by_slug.get(slug)
            if not record:
                sib = sibling_data(slug, tdir)
                record = {'title': slug.replace('-', ' ').title(), 'year': sib.get('dateCreated'),
                          'genres': [sib.get('genre')] if sib.get('genre') else [],
                          'description': sib.get('description'), 'cast': [], 'director': '',
                          'language': sib.get('inLanguage'), 'country': sib.get('countryOfOrigin')}
            data = build(record, slug, tdir, embeds.get(slug))
            if apply(p, data, slug, tdir):
                ok += 1
        except Exception as e:
            failed.append((p, str(e)))
    print(f'upgrade scanned {n}, rebuilt {ok}')
    if failed:
        for p, e in failed[:10]: print('  ', p, e)
    return ok

if __name__ == '__main__':
    import sys
    if '--upgrade' in sys.argv:
        upgrade_unavailable()
        sys.exit(0)
    if '--backfill-ld' in sys.argv:
        backfill_ld()
        sys.exit(0)
    n = ok = 0
    failed = []
    for root, slug in find_stubs():
        n += 1
        p = os.path.join(ROOT, root, slug, 'index.html')   # the stub path (movie/…)
        try:
            # real type from canonical (stubs live in movie/ but point at series|anime)
            tdir = sibling_type(p)
            record = by_id.get(slug) or by_slug.get(slug)
            if not record:
                # fall back to sibling JSON-LD
                sib = sibling_data(slug, root)
                record = {'title': slug.replace('-', ' ').title(), 'year': sib.get('dateCreated'),
                          'genres': [sib.get('genre')] if sib.get('genre') else [],
                          'description': sib.get('description'), 'cast': [], 'director': '',
                          'language': sib.get('inLanguage'), 'country': sib.get('countryOfOrigin')}
            live_yt = embeds.get(slug) or ''
            if not live_yt:
                yt = record.get('youtubeId') or (record.get('trailer') or '').split('v=')[-1]
                if yt and len(yt) == 11: live_yt = yt
            data = build(record, slug, tdir, live_yt)
            if apply(p, data, slug, tdir):
                ok += 1
            else:
                failed.append((p, 'no change'))
        except Exception as e:
            failed.append((p, str(e)))
    print(f'processed {n} stubs, rebuilt {ok}')
    if failed:
        print('failed:', len(failed))
        for p, e in failed[:15]:
            print('  ', p, e)

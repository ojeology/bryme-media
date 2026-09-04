#!/usr/bin/env python3
"""BRYME v10 · Build /entertainment/ from the full NetMirror catalog.
1) Ensure a real title page exists for every catalog title.
2) Rebuild the entertainment page: hero + all 17 rows, FULL-WIDTH RECTANGULAR cards.
3) Cards link to real pages; posters from data/movies.json when available,
   gradient monograms otherwise. Hero + title pages stay embed-ready."""
import json, os, re, sys, html as H

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nm_catalog import CATALOG, unique

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def rd(p): return open(os.path.join(ROOT, p), encoding='utf-8').read()
def wr(p, s):
    full = os.path.join(ROOT, p)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w', encoding='utf-8').write(s)
def esc(s): return H.escape(str(s), quote=True)

data = json.load(open(os.path.join(ROOT, 'data/movies.json')))
items = data if isinstance(data, list) else data.get('movies', [])
BY = {}
for it in items:
    if isinstance(it, dict) and it.get('slug'):
        BY[it['slug']] = it

UNIQ = unique()  # slug -> (title, td, rating, year, cert)

# ---------------- gradient seeds ----------------
def seed(slug):
    n = abs(hash(slug)) % 7
    pal = [('26,26,62','42,42,94'), ('46,10,10','94,26,26'), ('10,46,26','26,94,58'),
           ('46,42,10','94,74,26'), ('10,26,46','26,58,94'), ('46,10,42','94,26,82'),
           ('30,30,30','60,60,60')]
    a, b = pal[n]
    return f'linear-gradient(135deg,rgb({a}),rgb({b}))'

def initials(title):
    p = title.strip().split()
    return ((p[0][0] if p else '') + (p[-1][0] if len(p) > 1 else '')).upper()

# ---------------- ensure pages ----------------
def ensure_pages():
    created = 0
    for slug, (title, td, rating, year, cert) in UNIQ.items():
        loc = f'{td}/{slug}/index.html'
        if os.path.exists(loc):
            continue
        rec = BY.get(slug) or {}
        poster = rec.get('poster')
        yt = rec.get('youtubeId') or (rec.get('trailers') or [{}])[0].get('videoId')
        if rec.get('title') and (rec.get('poster') or yt):
            # full record exists in data but page missing -> build rich page
            _rich_page(slug, rec)
            created += 1
            continue
        _min_page(slug, title, td, rating, year, cert, poster)
        created += 1
    return created

# reuse the same shell pieces as build-missing-movies
TMPL = rd('movie/1917/index.html')
HEAD_PREFIX = TMPL[:TMPL.index('<title>')] + '<title>'
HEADER = re.search(r'<header class="top">.*?</header>', TMPL, re.S).group(0)
PILLS = [
 ['/channels/trending/','tr','🔥','Trending'],['/channels/latest/','lr','✨','Latest Release'],
 ['/channels/netflix/','n','N','Netflix'],['/channels/prime/','pv','P','Prime Video'],
 ['/channels/sony/','s','S','SonyLIV'],['/channels/jio/','j','J','JioHotstar'],
 ['/channels/crunchyroll/','cr','C','Crunchyroll'],['/channels/kids/','k','K','Kids'],['/channels/mx/','m','M','MX Player']]
DESK = ('<nav class="desk-bar" aria-label="Browse channels"><div class="shell desk-bar-inner">'
        + ''.join(f'<a class="dpill" href="{href}"><span class="plogo pl-{key}">{glyph}</span>{label}</a>' for href,key,glyph,label in PILLS)
        + '</div></nav>')
MNAV = ('<nav class="mobile-nav"><a href="/"><span class="mn-ico">\U0001f3e0</span>Home</a>'
        '<a href="/entertainment/" class="active"><span class="mn-ico">\U0001f3ac</span>Entertain</a>'
        '<a href="/sports/"><span class="mn-ico">\u26bd</span>Sports</a>'
        '<a href="/make-money/"><span class="mn-ico">\U0001f4b0</span>Money</a>'
        '<a href="/tech/"><span class="mn-ico">\U0001f916</span>Tech</a>'
        '<a href="/search/"><span class="mn-ico">\U0001f50d</span>Search</a></nav>')
TAIL = rd('movies/index.html')
FOOTER = TAIL[TAIL.find('<footer'):]

def _shell(title, desc, body, data_nav='home'):
    head = (HEAD_PREFIX + title + '</title>\n'
            f'<meta name="description" content="{esc(desc)}">\n'
            f'<link rel="canonical" href="https://bryme.onrender.com/{data_nav if data_nav!="home" else ""}">\n'
            '<meta property="og:type" content="website"><meta property="og:site_name" content="BRYME">\n'
            f'<meta property="og:title" content="{esc(title)}">\n'
            f'<meta property="og:description" content="{esc(desc)}">\n'
            '<link rel="stylesheet" href="/assets/site.css"></head>')
    scripts = '<script>window.BRYME_BASE=\'\'</script><script src="/assets/site-app.js"></script>'
    return head + f'<body data-nav="{data_nav}">' + HEADER + DESK + body + MNAV + FOOTER + scripts + '</body></html>'

def _min_page(slug, title, td, rating, year, cert, poster):
    tb = 'tb-series' if td == 'series' else 'tb-anime' if td == 'anime' else 'tb-movie'
    tlabel = 'SERIES' if td == 'series' else 'ANIME' if td == 'anime' else 'MOVIE'
    url = f'https://bryme.onrender.com/{td}/{slug}/'
    img = (f'<div class="poster"><img loading="lazy" decoding="async" width="320" height="180" src="{esc(poster)}" alt="{esc(title)} poster"></div>'
           if poster else f'<div class="poster"><div class="placeholder" style="background:{seed(slug)};color:#fff;font-size:34px;font-weight:800">{esc(initials(title))}</div></div>')
    badges = ''
    if rating:
        badges += f'<span class="badge nm-match">{round(rating*10)}% Match</span>'
    badges += '<span class="badge nm-hd">HD</span>'
    if cert:
        badges += f'<span class="badge" title="Age rating">{esc(cert)}</span>'
    body = (f'<main class="shell tp-page"><section class="movie-hero movie-hero-compact" '
            f'style="--movie-backdrop:url(\'{esc(poster) if poster else "https://i.ytimg.com/vi/placeholder/hqdefault.jpg"}\')">'
            f'{img}<div><div class="hero-kicker tp-kicker-meta"><span class="type-badge {tb}">{tlabel}</span>'
            f'<span>{year}</span><span class="dot">·</span><span>{esc(td.title())}</span></div>'
            f'<h1>{esc(title)}</h1><div class="badges">{badges}</div>'
            f'<div class="hero-actions"><a class="cta nm-watch-now" href="#watch">\u25b6 Watch Now</a>'
            f'<a class="cta cta-ghost nm-trailer" href="#trailer">\u25b6 Trailer</a></div></div></section>'
            f'<section class="shell trailer-section" id="trailer"><div class="trailer-unavailable"><b>Trailer currently unavailable.</b>'
            f'<span>The official trailer for {esc(title)} will appear here once it is verified.</span></div></section>'
            f'<section class="tp-loved tp-loved-under" id="loved"><h2>More Like This</h2><p class="tp-loved-lead">Explore more titles in the BRYME catalogue.</p><div class="tp-loved-list"></div></section></main>')
    wr(f'{td}/{slug}/index.html', _shell(f'{esc(title)} ({year}) – Overview, Trailer &amp; BRYME', f'{title} — synopsis, official trailer and watch links on BRYME.', body))

def _rich_page(slug, rec):
    td = rec.get('typeDir', 'movie')
    title = rec.get('title', slug); year = rec.get('year', ''); genre = rec.get('genre', '')
    poster = rec.get('poster')
    yt = rec.get('youtubeId') or (rec.get('trailers') or [{}])[0].get('videoId')
    rating = (rec.get('rating') or {}).get('value')
    url = f'https://bryme.onrender.com/{td}/{slug}/'
    tb = 'tb-series' if td == 'series' else 'tb-anime' if td == 'anime' else 'tb-movie'
    tlabel = 'SERIES' if td == 'series' else 'ANIME' if td == 'anime' else 'MOVIE'
    img = (f'<div class="poster"><img loading="lazy" decoding="async" width="320" height="180" src="{esc(poster)}" alt="{esc(title)} poster"></div>'
           if poster else f'<div class="poster"><div class="placeholder" style="background:{seed(slug)};color:#fff;font-size:34px;font-weight:800">{esc(initials(title))}</div></div>')
    badges = ''
    if rating:
        badges += f'<span class="badge nm-match">{round(rating*10)}% Match</span>'
    badges += '<span class="badge nm-hd">HD</span>'
    trailer = ''
    if yt:
        trailer = (f'<section class="shell trailer-section" id="trailer"><div class="trailer-section-inner" data-trailer-box '
                   f"data-trailer-candidates='[{{\"id\":\"{yt}\",\"type\":\"official-trailer\",\"label\":\"Official Trailer\",\"channel\":\"YouTube\",\"verified\":true,\"watch\":\"https://www.youtube.com/watch?v={yt}\"}}]' "
                   f'data-trailer-title="{esc(title)}"><div class="trailer-head"><span class="eyebrow">Trailer</span>'
                   f'<span class="trailer-status t-ok">\U0001f7e2 Official Trailer</span></div>'
                   f'<div class="trailer-frame" data-trailer-id="{yt}"><img loading="lazy" src="https://i.ytimg.com/vi/{yt}/hqdefault.jpg" alt="{esc(title)} trailer thumbnail">'
                   f'<button type="button" class="trailer-play">Play trailer</button></div>'
                   f'<div class="trailer-controls" data-trailer-controls hidden><button type="button" class="cta" data-trailer-unmute>Unmute</button>'
                   f'<a class="quiet-link" href="https://www.youtube.com/watch?v={yt}" target="_blank" rel="noopener">Watch on YouTube</a></div>'
                   f'<p class="trailer-meta">YouTube \u00b7 Official trailer</p>'
                   f'<div class="trailer-error" data-trailer-error hidden><b>Trailer currently unavailable.</b>'
                   f'<span class="trailer-error-actions"><a class="quiet-link" data-trailer-watch target="_blank" rel="noopener">Watch on YouTube</a>'
                   f'<button type="button" class="trailer-retry" data-trailer-retry>Try again</button></span></div></div></section>')
    else:
        trailer = (f'<section class="shell trailer-section" id="trailer"><div class="trailer-unavailable"><b>Trailer currently unavailable.</b>'
                   f'<span>The official trailer for {esc(title)} will appear here once it is verified.</span></div></section>')
    cast = (rec.get('cast') or [])[:8]
    cast_html = ''
    if cast:
        cast_html = ('<section class="nm-detail-extra"><div class="shell"><div class="nm-extra-head">Cast</div><div class="nm-cast-row">'
                     + ''.join(f'<div class="nm-cast-item"><span class="nm-avatar">{esc(initials(n))}</span><b>{esc(n)}</b></div>' for n in cast)
                     + '</div></div></section>')
    body = (f'<main class="shell tp-page"><section class="movie-hero movie-hero-compact" '
            f'style="--movie-backdrop:url(\'{esc(poster) if poster else "https://i.ytimg.com/vi/placeholder/hqdefault.jpg"}\')">'
            f'{img}<div><div class="hero-kicker tp-kicker-meta"><span class="type-badge {tb}">{tlabel}</span>'
            f'<span>{year}</span><span class="dot">\u00b7</span><span>{esc(genre)}</span></div>'
            f'<h1>{esc(title)}</h1><div class="badges">{badges}</div>'
            f'<div class="hero-actions"><a class="cta nm-watch-now" href="#watch">\u25b6 Watch Now</a>'
            f'<a class="cta cta-ghost nm-trailer" href="#trailer">\u25b6 Trailer</a></div></div></section>'
            + trailer + cast_html
            + f'<section class="tp-loved tp-loved-under" id="loved"><h2>More Like This</h2><p class="tp-loved-lead">Explore more titles in the BRYME catalogue.</p><div class="tp-loved-list"></div></section></main>')
    wr(f'{td}/{slug}/index.html', _shell(f'{esc(title)} ({year}) – Overview, Trailer &amp; BRYME', f'{title} — synopsis, official trailer and watch links on BRYME.', body))

# ---------------- entertainment page ----------------
def ent_card(slug, title, td, rating, year, cert, t10_rank=None, is_series_badge=True):
    tb = 'tb-series' if td == 'series' else 'tb-anime' if td == 'anime' else 'tb-movie'
    tlabel = 'SERIES' if td == 'series' else 'ANIME' if td == 'anime' else 'MOVIE'
    rec = BY.get(slug) or {}
    poster = rec.get('poster')
    if poster:
        img = f'<img loading="lazy" decoding="async" width="640" height="360" src="{esc(poster)}" alt="{esc(title)} poster">'
    else:
        img = f'<div class="placeholder" style="background:{seed(slug)};color:#fff;font-size:26px;font-weight:800">{esc(initials(title))}</div>'
    rank = f'<span class="rank top">{t10_rank}</span>' if t10_rank else ''
    badge = f'<span class="type-badge {tb}">{tlabel}</span>' if is_series_badge else ''
    rat = f'<p class="tile-rating" title="BRYME editorial score">\u2605 {rating}</p>' if rating else ''
    return (f'<a class="tile" href="/{td}/{slug}/"><div class="poster">{img}{rank}<span class="tile-play" aria-hidden="true"></span>{badge}</div>'
            f'<h3>{esc(title)}</h3><div class="tile-meta"><span>{year}</span><span class="sep">\u00b7</span><span>{esc(tlabel.title())}</span></div>{rat}</a>')

def ent_row(h2, entries, t10=False):
    cards = []
    for i, (title, slug, td, rating, year, cert) in enumerate(entries):
        cards.append(ent_card(slug, title, td, rating, year, cert, (i + 1) if t10 else None))
    cls = 'rail rail-t10' if t10 else 'rail'
    return (f'<section class="home-section"><div class="shell"><div class="section-head"><div><h2>{esc(h2)}</h2></div></div>'
            f'<div class="{cls}">{"".join(cards)}</div></div></section>')

def build_ent():
    rows = []
    for h2, entries in CATALOG.items():
        rows.append(ent_row(h2, entries, t10=(h2.startswith('🔥'))))
    hero = _hero()
    cta = ('<section class="nm-search-cta"><div class="nm-search-cta-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg></div>'
           '<h3>Can\'t find what you\'re looking for?</h3><p>Search any movie or show by name — instant results from the full BRYME catalogue.</p>'
           '<a class="nm-btn nm-btn-primary" href="/search/">Search Now</a></section>')
    body = '<main class="ent">' + hero + ''.join(rows) + cta + '</main>'
    desc = ('The BRYME Entertainment hub — Top 10 Today, trending, latest releases, Bollywood, South Indian hits, '
            'Indian originals, Hollywood, action, drama, comedy, thrillers, sci-fi, romance, horror, animation & family, and coming soon.')
    wr('entertainment/index.html', _shell('Entertainment — Movies, Series &amp; Anime | BRYME', desc, body, 'ent'))
    return body

def _hero():
    slides = [
        ('Project Hail Mary', 'project-hail-mary', 'movie', 8.7, 2026, 'U/A 13+', '26,26,62', '42,42,94', False,
         'Science teacher Ryland Grace wakes up on a spaceship light years from home with no recollection of who he is or how he got there.'),
        ('SWAPPED', 'swapped', 'movie', 8.9, 2026, 'U/A 7+', '45,80,22', '74,122,32', True,
         'A small woodland creature and a majestic bird, two natural sworn enemies of the Valley, must work together to survive.'),
        ('The Shawshank Redemption', 'the-shawshank-redemption', 'movie', 8.7, 1994, 'U', '61,40,23', '90,58,32', False,
         'Imprisoned in the 1940s for the double murder of his wife and her lover, upstanding banker Andy Dufresne begins a new life at Shawshank prison.'),
    ]
    out = []
    for i, (t, slug, td, rating, year, age, a, b, gold, desc) in enumerate(slides):
        act = ' is-active' if i == 0 else ''
        tb = 'tb-series' if td == 'series' else 'tb-movie'
        tlabel = 'SERIES' if td == 'series' else 'MOVIE'
        goldcls = ' nm-hero-title-gold' if gold else ''
        out.append(
            f'<div class="hero-slide{act}" data-slide data-title="{esc(t)}" data-url="/{td}/{slug}/" data-age="{esc(age)}" '
            f'style="background-image:linear-gradient(to bottom,rgba(0,0,0,.3),#0B0B0B),linear-gradient(135deg,rgb({a}),rgb({b}))">'
            f'<div class="hero-slide-shade"></div><div class="shell hero-slide-inner"><div class="hero-trend-tag">\U0001f525 TRENDING NOW</div>'
            f'<div class="hero-slide-kicker"><span class="type-badge {tb}">{tlabel}</span><span class="chip-hd">HD</span>'
            f'<span>{year}</span><span class="dot">\u00b7</span><span>{esc(tlabel.title())}</span></div>'
            f'<h1 class="{goldcls}">{esc(t)}</h1><p class="hero-slide-rating">\u2605 {rating}/10</p>'
            f'<p>{esc(desc)}</p><div class="hero-actions"><button type="button" class="cta hero-watch" data-hero-watch>\u25b6 Watch Now</button>'
            f'<a class="cta cta-ghost" href="/{td}/{slug}/">More Info</a></div></div></div>')
    return ('<section class="hero-carousel" data-hero role="region" aria-roledescription="carousel" aria-label="Featured titles" data-interval="5000">'
            '<div class="hero-slides">' + ''.join(out) + '</div>'
            '<button type="button" class="hero-ctrl hero-prev" data-hero-prev aria-label="Previous featured title">&#8249;</button>'
            '<button type="button" class="hero-ctrl hero-next" data-hero-next aria-label="Next featured title">&#8250;</button>'
            '<div class="hero-dots" data-hero-dots role="tablist" aria-label="Featured title slides">'
            + ''.join(f'<button type="button" class="hero-dot{" is-active" if i==0 else ""}" data-hero-dot="{i}" role="tab" aria-label="{esc(t[0])}" aria-selected="{str(i==0).lower()}"></button>' for i, t in enumerate(slides))
            + '</div><button type="button" class="hero-vctrl hero-mute" data-hero-mute aria-label="Unmute trailer" hidden>&#128263;</button>'
            '<button type="button" class="hero-vctrl hero-pause" data-hero-pause aria-label="Pause rotation" hidden>&#9208;</button>'
            '<div class="hero-video" data-hero-video hidden></div></section>')

if __name__ == '__main__':
    n = ensure_pages()
    build_ent()
    print('pages ensured:', n)
    print('unique titles:', len(UNIQ))
    print('rows:', len(CATALOG))
    print('total cards:', sum(len(v) for v in CATALOG.values()))

#!/usr/bin/env python3
"""BRYME v9 · /entertainment/ rebuilt to match the NetMirror reference EXACTLY:
same rows, same movie names, same card anatomy (140px 2:3 posters, SERIES badge
top-left, star rating top-right, title below), hero with 3 slides, search CTA,
and the 6-item bottom nav. Cards link to real BRYME title pages."""
import json, os, re, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def rd(p): return open(os.path.join(ROOT, p), encoding='utf-8').read()
def wr(p, s): open(os.path.join(ROOT, p), 'w', encoding='utf-8').write(s)
def esc(s): return H.escape(str(s), quote=True)

data = json.load(open(os.path.join(ROOT, 'data/movies.json')))
items = data if isinstance(data, list) else data.get('movies', [])
BY = {}
for it in items:
    if isinstance(it, dict) and it.get('slug'):
        BY[it['slug']] = it

# ---------- reference card data: (title, slug, typeDir, rating, year, typeLabel) ----------
C = {
 'Reacher': ('reacher','series',8.1,2022,'Series'),
 'The Traitors': ('the-traitors','series',5.7,2024,'Series'),
 'Spider-Man: Brand New Day': ('spider-man-brand-new-day','movie',7.9,2026,'Movie'),
 'Adaalat': ('adaalat','series',7.7,2024,'Series'),
 'Lanterns': ('lanterns','series',8.1,2026,'Series'),
 'Toy Story 5': ('toy-story-5','movie',8.0,2026,'Movie'),
 'The Odyssey': ('the-odyssey-2026','movie',8.0,2026,'Movie'),
 'Silo': ('silo','series',8.2,2023,'Series'),
 'Superman': ('superman-2025','movie',7.3,2025,'Movie'),
 'Avatar: Fire and Ash': ('avatar-fire-and-ash','movie',7.6,2025,'Movie'),
 'Zootopia 2': ('zootopia-2','movie',7.7,2025,'Movie'),
 'Demon Slayer': ('demon-slayer-infinity-castle','movie',7.7,2025,'Movie'),
 'Kalki 2898-AD': ('kalki-2898-ad','movie',6.4,2024,'Movie'),
 'Pushpa 2': ('pushpa-2','movie',6.3,2024,'Movie'),
 'Deadpool & Wolverine': ('deadpool-wolverine','movie',7.6,2024,'Movie'),
 'Inside Out 2': ('inside-out-2','movie',7.5,2024,'Movie'),
 'Dhurandhar': ('dhurandhar','movie',7.1,2025,'Movie'),
 'Stree 2': ('stree-2','movie',6.6,2024,'Movie'),
 'Singham Again': ('singham-again','movie',5.0,2024,'Movie'),
 'RRR': ('rrr','movie',7.7,2022,'Movie'),
 'Lioness': ('lioness','series',8.1,2023,'Series'),
 'House of the Dragon': ('house-of-the-dragon','series',8.4,2022,'Series'),
 'Minions & Monsters': ('minions-monsters','movie',7.5,2026,'Movie'),
 'Colony': ('colony-2026','movie',8.1,2026,'Movie'),
 'Obsession': ('obsession-2026','movie',8.2,2026,'Movie'),
 'Backrooms': ('backrooms','movie',7.1,2026,'Movie'),
 'Avatar Aang': ('avatar-aang-2026','movie',9.2,2026,'Movie'),
 'Mutiny': ('mutiny-2026','movie',6.9,2026,'Movie'),
 'Avengers: Doomsday': ('avengers-doomsday','movie',None,2026,'Movie'),
 'Project Hail Mary': ('project-hail-mary','movie',8.7,2026,'Movie'),
 'SWAPPED': ('swapped','movie',8.9,2026,'Movie'),
 'The Shawshank Redemption': ('the-shawshank-redemption','movie',8.7,1994,'Movie'),
}
# reference gradient poster seeds per title (used when no real poster)
GRAD = {
 'Reacher':'#1a0a2e,#4a1a6e','The Traitors':'#2e0a0a,#6e1a1a','Spider-Man: Brand New Day':'#0a1a2e,#1a3a6e',
 'Adaalat':'#1a2e0a,#3a6e1a','Lanterns':'#1a2e1a,#2a4e2a','Toy Story 5':'#2e1a0a,#6e3a1a',
 'The Odyssey':'#0a1a2e,#1a3a5e','Silo':'#1a1a1a,#3a3a3a','Superman':'#0a0a2e,#1a1a6e',
 'Avatar: Fire and Ash':'#0a2e1a,#1a6e3a','Zootopia 2':'#2e1a0a,#6e3a1a','Demon Slayer':'#2e0a0a,#6e1a1a',
 'Kalki 2898-AD':'#1a1a0a,#4a4a1a','Pushpa 2':'#1a0a0a,#4a1a1a','Deadpool & Wolverine':'#2e0a1a,#6e1a3a',
 'Inside Out 2':'#0a1a2e,#1a3a6e','Dhurandhar':'#0a0a0a,#2a2a2a','Stree 2':'#1a0a2e,#3a1a6e',
 'Singham Again':'#0a1a0a,#1a3a1a','RRR':'#2e1a0a,#5e3a1a','Lioness':'#1a0a0a,#3a1a1a',
 'House of the Dragon':'#0a0a1a,#1a1a3a','Minions & Monsters':'#2e2a0a,#5e4a1a','Colony':'#0a1a1a,#1a3a3a',
 'Obsession':'#0a0a0a,#1a1a1a','Backrooms':'#1a1a0a,#2a2a1a','Avatar Aang':'#0a1a2e,#1a3a5e',
 'Mutiny':'#0a1a2e,#1a3a4e','Avengers: Doomsday':'#1a0a0a,#3a1a1a',
 'Project Hail Mary':'#1a1a3e,#2a2a5e','SWAPPED':'#2d5016,#4a7a20','The Shawshank Redemption':'#3d2817,#5a3a20',
}

def initials(title):
    p = title.strip().split()
    return ((p[0][0] if p else '') + (p[-1][0] if len(p) > 1 else '')).upper()

def poster_for(title, slug):
    rec = BY.get(slug)
    if rec and rec.get('poster'):
        return (f'<img loading="lazy" decoding="async" width="320" height="180" src="{esc(rec["poster"])}" '
                f'alt="{esc(title)} poster">')
    g = GRAD.get(title, '#1a1a1a,#2a2a2a')
    return (f'<div class="placeholder" style="background:linear-gradient(135deg,{g});color:#fff;'
            f'font-size:30px;font-weight:800">{esc(initials(title))}</div>')

def card(title):
    slug, td, rating, year, tlabel = C[title]
    tb = 'tb-series' if td == 'series' else 'tb-movie'
    badge = f'<span class="type-badge {tb}">{tlabel.upper()}</span>' if tlabel == 'Series' else ''
    rat = f'<p class="tile-rating" title="BRYME editorial score">{rating}</p>' if rating else ''
    return (f'<a class="tile" href="/{td}/{slug}/"><div class="poster">{poster_for(title, slug)}'
            f'<span class="tile-play" aria-hidden="true"></span></div><h3>{esc(title)}</h3>'
            f'<div class="tile-meta"><span class="type-badge {tb}">{tlabel.upper()}</span><span>{year}</span></div>{rat}</a>')

def top10_card(i, title):
    slug, td, rating, year, tlabel = C[title]
    tb = 'tb-series' if td == 'series' else 'tb-movie'
    return (f'<a class="tile" href="/{td}/{slug}/"><div class="poster">{poster_for(title, slug)}'
            f'<span class="tile-play" aria-hidden="true"></span><span class="rank top">{i}</span></div>'
            f'<h3>{esc(title)}</h3><div class="tile-meta"><span class="type-badge {tb}">{tlabel.upper()}</span></div></a>')

def row(h2, titles, note=None, t10=False):
    cls = 'rail rail-t10' if t10 else 'rail'
    cards = ''.join(top10_card(i+1, t) for i, t in enumerate(titles)) if t10 else ''.join(card(t) for t in titles)
    note_html = f'<p class="section-note">{esc(note)}</p>' if note else ''
    return (f'<section class="home-section"><div class="shell"><div class="section-head"><div><h2>{esc(h2)}</h2>{note_html}</div></div>'
            f'<div class="{cls}">{cards}</div></div></section>')

# ---------- ROWS exactly as in the reference ----------
ROWS = [
    ('🔥 Top 10 Today', ['Reacher','The Traitors','Spider-Man: Brand New Day','Adaalat'], None, True),
    ('Trending Now', ['Lanterns','Toy Story 5','The Odyssey','Reacher','Silo'], None, False),
    ('Latest Release', ['Superman','Avatar: Fire and Ash','Zootopia 2','Demon Slayer'], None, False),
    ('Hot New Releases', ['Kalki 2898-AD','Pushpa 2','Deadpool & Wolverine','Inside Out 2'], None, False),
    ('Bollywood', ['Dhurandhar','Stree 2','Singham Again'], None, False),
    ('South Indian Hits', ['Kalki 2898-AD','Pushpa 2','RRR'], None, False),
    ('Drama Series', ['Lioness','House of the Dragon','Lanterns'], None, False),
    ('Comedy', ['Toy Story 5','Minions & Monsters','Deadpool & Wolverine'], None, False),
    ('Horror', ['Colony','Obsession','Backrooms'], None, False),
    ('Animation & Family', ['Toy Story 5','Avatar Aang','Demon Slayer'], None, False),
    ('Trending Globally — Coming Soon', ['Mutiny','Spider-Man: Brand New Day','Avengers: Doomsday'], None, False),
]
BODY = ''.join(row(h, ts, n, t) for h, ts, n, t in ROWS)

# ---------- HERO (3 slides, exact reference) ----------
HERO_META = {
 'Project Hail Mary': ('U/A 13+', False, 'Science teacher Ryland Grace wakes up on a spaceship light years from home with no recollection of who he is or how he got there.'),
 'SWAPPED': ('U/A 7+', True, 'A small woodland creature and a majestic bird, two natural sworn enemies of the Valley, must work together to survive.'),
 'The Shawshank Redemption': ('U', False, 'Imprisoned in the 1940s for the double murder of his wife and her lover, upstanding banker Andy Dufresne begins a new life at Shawshank prison.'),
}
def slide(title, active):
    slug, td, rating, year, tlabel = C[title]
    age, gold, desc = HERO_META[title]
    tb = 'tb-series' if td == 'series' else 'tb-movie'
    g = GRAD[title]
    act = ' is-active' if active else ''
    return (f'<div class="hero-slide{act}" data-slide data-title="{esc(title)}" data-url="/{td}/{slug}/" '
            f'data-age="{esc(age)}" style="background-image:linear-gradient(to bottom,rgba(0,0,0,.3),#0B0B0B),'
            f'linear-gradient(135deg,{g})">'
            f'<div class="hero-slide-shade"></div>'
            f'<div class="shell hero-slide-inner"><div class="hero-trend-tag">🔥 TRENDING NOW</div>'
            f'<div class="hero-slide-kicker"><span class="type-badge {tb}">{tlabel.upper()}</span>'
            f'<span class="chip-hd">HD</span><span>{year}</span><span class="dot">·</span><span>{tlabel}</span></div>'
            f'<h1 class="{"nm-hero-title-gold" if gold else ""}">{esc(title)}</h1>'
            f'<p class="hero-slide-rating">★ {rating}/10</p>'
            f'<p>{esc(desc)}</p>'
            f'<div class="hero-actions"><button type="button" class="cta hero-watch" data-hero-watch>▶ Watch Now</button>'
            f'<a class="cta cta-ghost" href="/{td}/{slug}/">More Info</a></div></div></div>')

HERO = ('<section class="hero-carousel" data-hero role="region" aria-roledescription="carousel" '
        'aria-label="Featured titles" data-interval="5000"><div class="hero-slides">'
        + slide('Project Hail Mary', True) + slide('SWAPPED', False) + slide('The Shawshank Redemption', False)
        + '</div><button type="button" class="hero-ctrl hero-prev" data-hero-prev aria-label="Previous featured title">&#8249;</button>'
        '<button type="button" class="hero-ctrl hero-next" data-hero-next aria-label="Next featured title">&#8250;</button>'
        '<div class="hero-dots" data-hero-dots role="tablist" aria-label="Featured title slides">'
        + ''.join(f'<button type="button" class="hero-dot{" is-active" if i==0 else ""}" data-hero-dot="{i}" role="tab" aria-label="{esc(t)}" aria-selected="{str(i==0).lower()}"></button>' for i,t in enumerate(['Project Hail Mary','SWAPPED','The Shawshank Redemption']))
        + '</div><button type="button" class="hero-vctrl hero-mute" data-hero-mute aria-label="Unmute trailer" hidden>&#128263;</button>'
        '<button type="button" class="hero-vctrl hero-pause" data-hero-pause aria-label="Pause rotation" hidden>&#9208;</button>'
        '<div class="hero-video" data-hero-video hidden></div></section>')

# ---------- SEARCH CTA ----------
CTA = ('<section class="nm-search-cta"><div class="nm-search-cta-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg></div>'
       '<h3>Can\'t find what you\'re looking for?</h3><p>Search any movie or show by name — instant results from the full BRYME catalogue.</p>'
       '<a class="nm-btn nm-btn-primary" href="/search/">Search Now</a></section>')

# ---------- shell ----------
tmpl = rd('movies/index.html')
headPrefix = tmpl[:tmpl.index('<title>')] + '<title>'
header = re.search(r'<header class="top">.*?</header>', tmpl, re.S).group(0)
tail = tmpl[tmpl.find('<nav class="mobile-nav">'):]
PILLS = [
 ['/channels/trending/','tr','🔥','Trending'],['/channels/latest/','lr','✨','Latest Release'],
 ['/channels/netflix/','n','N','Netflix'],['/channels/prime/','pv','P','Prime Video'],
 ['/channels/sony/','s','S','SonyLIV'],['/channels/jio/','j','J','JioHotstar'],
 ['/channels/crunchyroll/','cr','C','Crunchyroll'],['/channels/kids/','k','K','Kids'],['/channels/mx/','m','M','MX Player']]
desk = ('<nav class="desk-bar" aria-label="Browse channels"><div class="shell desk-bar-inner">'
        + ''.join(f'<a class="dpill{" is-on" if href=="/channels/trending/" else ""}" href="{href}"><span class="plogo pl-{key}">{glyph}</span>{label}</a>' for href,key,glyph,label in PILLS)
        + '</div></nav>')

title = 'Entertainment — Movies, Series &amp; Anime | BRYME'
desc = ('The Netflix-style BRYME Entertainment hub — hero carousel, Top 10 Today, trending, latest releases, '
        'Bollywood, South Indian hits, drama, comedy, horror, animation & family, and coming-soon titles with verified trailers.')
head = (headPrefix + title + '</title>\n'
        f'<meta name="description" content="{desc}">\n'
        '<link rel="canonical" href="https://bryme.onrender.com/entertainment/">\n'
        '<meta property="og:type" content="website"><meta property="og:site_name" content="BRYME">\n'
        '<meta property="og:title" content="Entertainment — Movies, Series &amp; Anime">\n'
        f'<meta property="og:description" content="{desc}">\n'
        '<meta property="og:url" content="https://bryme.onrender.com/entertainment/">\n'
        '<link rel="stylesheet" href="/assets/site.css"></head>')

mnav = ('<nav class="mobile-nav"><a href="/"><span class="mn-ico">\U0001f3e0</span>Home</a>'
        '<a href="/entertainment/" class="active"><span class="mn-ico">\U0001f3ac</span>Entertain</a>'
        '<a href="/sports/"><span class="mn-ico">\u26bd</span>Sports</a>'
        '<a href="/make-money/"><span class="mn-ico">\U0001f4b0</span>Money</a>'
        '<a href="/tech/"><span class="mn-ico">\U0001f916</span>Tech</a>'
        '<a href="/search/"><span class="mn-ico">\U0001f50d</span>Search</a></nav>')
footer = tail[tail.find('<footer'):]
out = head + '<body data-nav="ent">' + header + desk + '<main>' + HERO + BODY + CTA + '</main>' + mnav + footer
wr('entertainment/index.html', out)
print('entertainment rebuilt, bytes:', len(out))

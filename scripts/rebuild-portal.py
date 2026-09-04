#!/usr/bin/env python3
"""BRYME v8 · Rebuild homepage (portal for ALL content) + entertainment (NetMirror experience).
- Home: portal hero, 4 vertical hubs, "Now on Entertainment" rail, matchday, money/tech panels,
  recommendation box, articles, services strip, search CTA.
- Entertainment: NetMirror hero carousel + Top 10 + Popular rails + category grid + editorial
  stories + genre chips + articles (kept), with the same shell (header/pills/footer)."""
import re, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def rd(p): return open(os.path.join(ROOT, p), encoding='utf-8').read()
def wr(p, s): open(os.path.join(ROOT, p), 'w', encoding='utf-8').write(s)

home = rd('index.html')
ent = rd('entertainment/index.html')

def extract_section(html, marker, tag=None):
    i = html.find(marker)
    if i < 0: raise SystemExit(f'marker not found: {marker}')
    st = html.rfind('<section', 0, i)
    if st < 0: raise SystemExit(f'no section for: {marker}')
    en = html.find('</section>', st) + len('</section>')
    return html[st:en]

def extract_tag(html, open_tag, close_tag):
    i = html.find(open_tag)
    if i < 0: raise SystemExit(f'tag not found: {open_tag}')
    j = html.find(close_tag, i) + len(close_tag)
    return html[i:j]

# ---- extract pieces from home ----
HERO = extract_section(home, 'hero-carousel')
T10 = extract_section(home, 'Top 10 Today')
POP_M = extract_section(home, 'Popular Movies')
POP_S = extract_section(home, 'Popular Series')
POP_A = extract_section(home, 'Popular Anime')
MATCH = extract_section(home, 'Match previews')
GENRE = extract_section(home, 'Browse by genre')
ART = extract_section(home, 'Latest articles')
SVC = extract_section(home, 'svc-strip')
REC = extract_section(home, 'data-rec-input')
CTA = extract_section(home, 'nm-search-cta')
HEADER = extract_tag(home, '<header class="top">', '</header>')
DESKBAR = extract_tag(home, '<nav class="desk-bar"', '</nav>')
TAIL = home[home.find('<nav class="mobile-nav">'):]
# head prefix (through </head>) for home — we'll swap <title> + description
home_head_end = home.find('</head>') + len('</head>')
HEAD_HOME = home[:home_head_end]
ENT_HEAD_END = ent.find('</head>') + len('</head>')
HEAD_ENT = ent[:ENT_HEAD_END]

# ---- extract pieces from entertainment ----
CATGRID = extract_section(ent, 'vcat-photo')
STORIES = extract_section(ent, 'sp-hero-track')
START_HERE = extract_section(ent, 'Start here')
ENT_ART = extract_section(ent, 'Latest articles')
ENT_TAIL = ent[ent.find('<nav class="mobile-nav">'):]
ENT_BODY_OPEN = ent[ent.find('<body'):ent.find('>', ent.find('<body')) + 1]

# ---- data for the "Now on Entertainment" rail ----
data = json.load(open(os.path.join(ROOT, 'data/movies.json')))
items = data if isinstance(data, list) else data.get('movies', [])
def tile(it):
    td = it.get('typeDir', 'movie')
    tb = {'movie': 'tb-movie', 'series': 'tb-series', 'anime': 'tb-anime'}.get(td, 'tb-movie')
    typ = {'movie': 'MOVIE', 'series': 'SERIES', 'anime': 'ANIME'}.get(td, 'MOVIE')
    poster = it.get('poster')
    img = (f'<img loading="lazy" decoding="async" width="320" height="180" src="{poster}" alt="{it["title"]} thumbnail">'
           if poster else '<div class="placeholder">No image</div>')
    rating = it.get('rating', {}).get('value')
    rat = f'<p class="tile-rating" title="BRYME editorial score">{rating}/10</p>' if rating else ''
    return (f'<a class="tile" href="/{td}/{it["slug"]}/"><div class="poster">{img}<span class="tile-play" aria-hidden="true"></span></div>'
            f'<h3>{it["title"]}</h3><div class="tile-meta"><span class="type-badge {tb}">{typ}</span><span>{it.get("year","")}</span><span class="sep">·</span><span>{it.get("genre","")}</span></div>{rat}</a>')

pool = [x for x in items if x.get('status') != 'draft' and x.get('poster') and x.get('typeDir') in ('movie','series','anime')]
pool.sort(key=lambda x: (x.get('rating') or {}).get('value') or 0, reverse=True)
NOW_ENT_RAIL = '<div class="rail">' + ''.join(tile(x) for x in pool[:16]) + '</div>'

def esc(s): return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

# ---- build: MOBILE NAV (6 items) ----
def mobile_nav(active):
    links = [('/', '🏠', 'Home'), ('/entertainment/', '🎬', 'Entertain'), ('/sports/', '⚽', 'Sports'),
             ('/make-money/', '💰', 'Money'), ('/tech/', '🤖', 'Tech'), ('/search/', '🔍', 'Search')]
    return '<nav class="mobile-nav">' + ''.join(
        f'<a href="{h}"{" class=\"active\"" if h == active else ""}><span class="mn-ico">{i}</span>{l}</a>'
        for h, i, l in links) + '</nav>'

def footer_from(tail):
    i = tail.find('<footer')
    return tail[i:]

FOOTER = footer_from(TAIL)

# ---- build: PORTAL HERO ----
PORTAL_HERO = f'''<section class="portal-hero">
  <div class="shell portal-hero-inner">
    <div class="eyebrow">BRYME · One hub, four lanes</div>
    <h1>Discover what you love.<br>Learn what you need.<br><span>Find what&rsquo;s next.</span></h1>
    <p class="portal-sub">Movies, TV &amp; anime with verified trailers — plus sports, practical money guides and tech &amp; AI. All in one place.</p>
    <form class="portal-search" action="/search/" method="get" role="search">
      <input type="search" name="q" placeholder="Search movies, series, sports, guides…" aria-label="Search BRYME" autocomplete="off">
      <button type="submit">Search</button>
    </form>
    <div class="portal-quick">
      <a href="/entertainment/"><span class="plogo pl-n">🎬</span>Watch</a>
      <a href="/sports/"><span class="plogo pl-s">⚽</span>Sports</a>
      <a href="/make-money/"><span class="plogo pl-m">💰</span>Make Money</a>
      <a href="/tech/"><span class="plogo pl-t">🤖</span>Tech &amp; AI</a>
    </div>
  </div>
</section>'''

# ---- build: VERTICAL HUBS ----
def hub(href, img, emoji, name, tag, glow):
    return (f'<a class="hub-card" href="{href}" style="--hub-img:url(\'{img}\');--hub-glow:{glow}">'
            f'<div class="hub-card-inner"><span class="hub-emoji">{emoji}</span><b>{name}</b>'
            f'<p>{tag}</p><span class="hub-go">Explore &rarr;</span></div></a>')

HUBS = ('<section class="hub-row"><div class="shell">'
        '<div class="section-head"><div><div class="eyebrow">Everything on BRYME</div><h2>Pick a lane</h2></div></div>'
        '<div class="hub-grid">'
        + hub('/entertainment/', '/assets/img/ent/hero-cinema.jpg', '🎬', 'Entertainment', 'Movies, series & anime with verified trailers.', 'rgba(229,9,20,.35)')
        + hub('/sports/', '/assets/img/sports/hero-premier-league.jpg', '⚽', 'Sports', 'Previews, results, tables & transfer stories.', 'rgba(61,220,132,.3)')
        + hub('/make-money/', '/assets/img/money/hero-writing.jpg', '💰', 'Make Money', 'Legitimate online opportunities, filtered to you.', 'rgba(245,197,24,.3)')
        + hub('/tech/', '/assets/img/tech/hero-hosting.jpg', '🤖', 'Tech & AI', 'Practical tools and no-nonsense explainers.', 'rgba(79,142,247,.3)')
        + '</div></div></section>')

# ---- build: MONEY + TECH panels ----
MONEY_TECH = f'''<section class="home-section duo-wrap"><div class="shell"><div class="duo-grid">
  <div class="panel-card pc-money">
    <div class="panel-head"><span class="panel-ico">💰</span><div><h2>Make Money</h2><p>Fresh, verified online opportunities.</p></div><a href="/make-money/">All guides</a></div>
    <div class="panel-links">
      <a href="/make-money/beginners-guide-to-making-money-online/">Beginners guide to making money online</a>
      <a href="/make-money/freelance-platform-fees-explained/">Freelance platform fees, explained</a>
      <a href="/make-money/website-monetization-guide/">Website monetization guide</a>
      <a href="/make-money/writing/">Writing opportunities hub</a>
    </div>
  </div>
  <div class="panel-card pc-tech">
    <div class="panel-head"><span class="panel-ico">🤖</span><div><h2>Tech &amp; AI</h2><p>Practical tools. No theatre.</p></div><a href="/tech/">All articles</a></div>
    <div class="panel-links">
      <a href="/tech/ai-assistants/">AI assistants, compared for real work</a>
      <a href="/tech/ai-assistant-data-training-settings/">What &ldquo;train on your data&rdquo; actually means</a>
      <a href="/articles/">All BRYME stories</a>
    </div>
  </div>
</div></div></section>'''

# ---- build: HOME ----
NEW_TITLE_HOME = 'BRYME — Movies, Sports, Money &amp; Tech | Discover what\'s next'
home_head = re.sub(r'<title>.*?</title>', f'<title>{NEW_TITLE_HOME}</title>', HEAD_HOME, count=1)
home_head = re.sub(r'(<meta name="description" content=")[^"]*(")', r'\1Discover what you love. Learn what you need. Find what\'s next — movies, series, anime with verified trailers, sports coverage, practical money guides and tech & AI, all on BRYME.\2', home_head, count=1)

home_body = (
    '<main>'
    + PORTAL_HERO + HUBS
    + '<section class="home-section"><div class="shell"><div class="section-head"><div><div class="eyebrow">Entertainment</div><h2>Now on Entertainment</h2><p class="section-note">Top-rated movies, series &amp; anime — full Netflix-style experience with trailers.</p></div><a href="/entertainment/">Open Entertainment</a></div>'
    + NOW_ENT_RAIL + '</div></section>'
    + MATCH + MONEY_TECH + REC + ART + SVC + CTA
    + '</main>'
)
home_new = home_head + '<body data-nav="home">' + HEADER + DESKBAR + home_body + mobile_nav('/') + FOOTER + home[home.rfind('<script>'):]
# keep the trailing scripts from original home
home_tail_scripts = home[home.find('<script>window.BRYME_BASE'):]
home_new = home_head + '<body data-nav="home">' + HEADER + DESKBAR + home_body + mobile_nav('/') + FOOTER + home_tail_scripts
wr('index.html', home_new)

# ---- build: ENTERTAINMENT ----
NEW_TITLE_ENT = 'Entertainment — Movies, Series &amp; Anime | BRYME'
ent_head = re.sub(r'<title>.*?</title>', f'<title>{NEW_TITLE_ENT}</title>', HEAD_ENT, count=1)
ent_head = re.sub(r'(<meta name="description" content=")[^"]*(")', r'\1The Netflix-style BRYME Entertainment hub — hero carousel, Top 10 Today, popular movies, series & anime with verified trailers, editorial guides and more.\2', ent_head, count=1)

# wrap shell-less sections so they stay inside the 1180px container under a full-width <main>
def wrap_shell(sec):
    i = sec.find('>')
    return sec[:i + 1] + '<div class="shell">' + sec[i + 1:] + '</div>'
CATGRID_S = wrap_shell(CATGRID)
STORIES_S = wrap_shell(STORIES)

ent_body = (
    '<main>'
    + HERO + T10 + POP_M + POP_S + POP_A + CATGRID_S + STORIES_S + GENRE + START_HERE + ENT_ART + SVC
    + '</main>'
)
ent_tail_scripts = ent[ent.find('<script>window.BRYME_BASE'):]
ent_new = ent_head + '<body data-nav="ent">' + HEADER + DESKBAR + ent_body + mobile_nav('/entertainment/') + FOOTER + ent_tail_scripts
wr('entertainment/index.html', ent_new)

print('home bytes:', len(home_new), '| ent bytes:', len(ent_new))
print('HOME sections:', re.findall(r'<section class="([a-z-]+)"', home_body)[:14])
print('ENT sections:', re.findall(r'<section class="([a-z-]+)"', ent_body)[:14])
print('OK')

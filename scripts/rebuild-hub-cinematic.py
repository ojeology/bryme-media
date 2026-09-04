#!/usr/bin/env python3
"""BRYME Sports Hub — cinematic glass rebuild.
Rebuilds /sports/index.html keeping EVERY existing route, data container,
live engine, content block, semantic link and SEO mark. This is a purely
presentation-layer upgrade scoped to body.shub (new CSS/JS files).
"""
import re, os, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sports", "index.html")

# ---- source page (original, read from git HEAD so the build is reproducible) ----
src = (subprocess.check_output(["git", "show", "HEAD:sports/index.html"], cwd=ROOT)
       .decode("utf-8").replace("\\r\\n", "\\n"))

# ---- extract reusable fragments straight from the original ----
def extract(html, start_marker, end_marker):
    i = html.find(start_marker)
    if i < 0:
        raise ValueError("marker not found: " + start_marker[:40])
    j = html.find(end_marker, i)
    if j < 0:
        raise ValueError("end marker not found: " + end_marker[:40])
    if end_marker:
        j = j + len(end_marker)
    return html[i:j]

# top stories art rail (engine-managed)
ARTRAIL = extract(src, '<div class="sp-art-rail">', '</div></div>')
# stories grid (the real story-photo cards) — reuse the inner section only,
# dropping the sh-sec wrapper (the build wraps it again) so tags stay balanced
STORIES = extract(src, '<section class="section"><div class="shell">\n  <div class="section-head"><h2>BRYME Sports Stories</h2>', '</section>')
# use optimized background variants for the story cards (lighter payload)
STORIES = re.sub(r"--card-img:url\('/assets/img/sports/(hero-[a-z-]+)\.jpg'\)",
                 r"--card-img:url('/assets/img/sports/\1-md.jpg')", STORIES)
# live engine board + side dashboards (the whole sp-layout grid)
BOARD = extract(src, '<section class="sp-board"', '</aside></div>')
# season video section
VIDEO = extract(src, '<!-- ============ SEASON VIDEO ============ -->', '</section>')
# "everything else on BRYME" core hubs
COREHUBS = extract(src, '<!-- ============ EVERYTHING ELSE ON BRYME ============ -->', '</section>')
# FAQ
FAQ = extract(src, '<!-- ============ FAQ ============ -->', '</section>')

html = src  # the build reads fragments out of the original above

# ---- head (verbatim, plus hub stylesheet + preloads) ----
head = html[:html.find("</head>")]
head = head.replace('rel="stylesheet" href="/assets/site.css"',
    'rel="stylesheet" href="/assets/site.css">\n<link rel="stylesheet" href="/assets/sports-hub.css">')
# preload hero photography used by the cinematic background & hero
head = head.replace('fetchpriority="high">',
    'fetchpriority="high">\n<link rel="preload" as="image" href="/assets/img/sports/hero-premier-league.jpg" fetchpriority="high">')

# ---- body prefix (verbatim) + cinematic background layer ----
bodyprefix = html[html.find("<body"):html.find('<main class="sp-desk">')]
bodyprefix = bodyprefix.replace('class="spx"', 'class="spx shub"')
bodyprefix = bodyprefix.replace("</header>",
    '</header>\n'
    '<div class="sh-bg" aria-hidden="true">\n'
    '  <div class="sh-bg-photo"></div>\n'
    '  <div class="sh-bg-veil"></div>\n'
    '  <div class="sh-bg-vignette"></div>\n'
    '  <div class="sh-bg-noise"></div>\n'
    '</div>')

# ---- tail (mobile-nav + footer + scripts), add hub script ----
tail = html[html.find("</main>"):]
tail = tail.replace('src="/assets/sports-engine.js"',
    'src="/assets/sports-engine.js"></script><script src="/assets/sports-hub.js" defer>')

# ---------------------------------------------------------------- main ----
def carousel_nav():
    return ('<button class="sh-car-nav prev" type="button" aria-label="Previous">'
            '<svg viewBox="0 0 24 24" fill="none"><path d="M15 5l-7 7 7 7" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg></button>'
            '<button class="sh-car-nav next" type="button" aria-label="Next">'
            '<svg viewBox="0 0 24 24" fill="none"><path d="M9 5l7 7-7 7" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg></button>')

comic_cards = [
    dict(href="/sports/premier-league/teams/arsenal/", img="arsenal-coventry-mw1/ac-01.jpg",
         title="Arsenal open the title defence", meta="Arsenal v Coventry · MW1",
         hook="Champions dey open the defence — three nil, rout confirmed!"),
    dict(href="/sports/premier-league/teams/manchester-city/", img="mancity-bournemouth-mw1/mc-01.jpg",
         title="City's new era begins at the Etihad", meta="Man City v Bournemouth · MW1",
         hook="New season. New manager. New assignment."),
    dict(href="/sports/premier-league/teams/brentford/", img="brentford-tottenham-mw1/bc-01.jpg",
         title="West London stays Bees", meta="Brentford v Tottenham · MW1",
         hook="London derby — who go cry? West London na Bees own!"),
    dict(href="/sports/premier-league/teams/newcastle-united/", img="newcastle-liverpool-mw1/nl-01.jpg",
         title="Toon rise against the Reds", meta="Newcastle v Liverpool · MW1",
         hook="Newcastle dey rise, but Liverpool no go lie down!"),
    dict(href="/sports/premier-league/teams/hull/", img="hull-united-mw1/01.jpg",
         title="The Tigers are back in the big league", meta="Hull v Man United · MW1",
         hook="Nine years don done — Tigers return, MKM don turn mad house!"),
    dict(href="/sports/la-liga/teams/espanyol/", img="real-espanyol-mw1/re-01.jpg",
         title="The kings find a way again", meta="Real Madrid v Espanyol · MW1",
         hook="Underdogs dey host the kings — but the kings find a way again!"),
]
comics = "".join(
    '<a class="sh-comic" href="%s"><div class="sh-comic-media">'
    '<img src="/assets/img/sports/comics/%s-md.jpg" '
    'srcset="/assets/img/sports/comics/%s-md.jpg 720w, /assets/img/sports/comics/%s.jpg 1408w" '
    'sizes="(max-width:520px) 270px, 330px" alt="%s football comic" width="640" height="360" '
    'loading="lazy" decoding="async"><div class="sh-comic-shade"></div></div>'
    '<span class="sh-comic-tag">Match Comic</span>'
    '<div class="sh-comic-body"><div class="sh-comic-meta"><em>Original artwork</em><span>·</span>%s</div>'
    '<h3 class="sh-comic-title">%s</h3><p class="sh-comic-hook">%s</p></div>'
    '<span class="sh-comic-play"><svg viewBox="0 0 24 24" fill="none"><path d="M8 5v14l11-7z" fill="currentColor"/></svg></span></a>'
    % (c["href"], c["img"][:-4], c["img"][:-4], c["img"][:-4], c["title"], c["meta"], c["title"], c["hook"]) for c in comic_cards
)

transfer_cards = [
    dict(href="/sports/transfers/premier-league-2026-27/", title="Premier League", sub="All 20 clubs — confirmed in &amp; out."),
    dict(href="/sports/transfers/la-liga-2026-27/", title="La Liga", sub="Real, Barça and the rest of the desk."),
    dict(href="/sports/transfers/serie-a-2026-27/", title="Serie A", sub="Milan, Inter, Juve and the chasing pack."),
    dict(href="/sports/transfers/bundesliga-2026-27/", title="Bundesliga", sub="Bayern, Leverkusen and the news from Germany."),
    dict(href="/sports/transfers/ligue-1-2026-27/", title="Ligue 1", sub="Paris, Marseille and the French window."),
    dict(href="/sports/articles/premier-league-transfer-tracker-august-2026/", title="Transfer tracker", sub="Every big done deal — August 2026."),
]
transfers = "".join(
    '<a class="sh-transfer" href="%s"><span class="sh-transfer-em"><i></i>Live transfer window</span>'
    '<b>%s</b><span>%s</span><span class="sh-transfer-foot">Open the desk →</span></a>'
    % (t["href"], t["title"], t["sub"]) for t in transfer_cards
)

cat_links = [
    ("Premier League", "/sports/premier-league/", ""),
    ("La Liga", "/sports/la-liga/", ""),
    ("Champions League", "/sports/champions-league/", "UCL"),
    ("Serie A", "/sports/serie-a/", ""),
    ("Bundesliga", "/sports/bundesliga/", ""),
    ("Ligue 1", "/sports/ligue-1/", ""),
    ("International", "/sports/international/", ""),
    ("Transfers", "/sports/transfers/", "LIVE"),
    ("Football Comics", "/sports/comics/", ""),
    ("Clubs", "/sports/clubs/", ""),
    ("Players", "/sports/players/", ""),
    ("Records", "/sports/records/", ""),
]
cats = "".join(
    '<a class="sh-cat" href="%s">%s%s</a>' % (h, n, ('<span class="sh-cat-badge">%s</span>' % b) if b else "")
    for (n, h, b) in cat_links
)

# the engine-managed "Top stories" rail (verbatim content)
art_rail = ARTRAIL

main = ('<main class="sp-desk">\n'
        '<!-- ============ CINEMATIC HERO ============ -->\n'
        '<section class="sh-hero" aria-labelledby="sh-hero-title">\n'
        '  <div class="sh-hero-photo alt" aria-hidden="true"></div>\n'
        '  <div class="sh-hero-veil" aria-hidden="true"></div>\n'
        '  <div class="sh-hero-in">\n'
        '    <span class="sh-hero-kick"><i></i>Matchday &middot; <span data-sp-date>Live desk</span></span>\n'
        '    <h1 id="sh-hero-title" class="sh-hero-title">BRYME <span class="sh-title-s">SPORTS</span></h1>\n'
        '    <p class="sh-hero-copy">The world&rsquo;s game, covered properly. Top-five leagues, sourced results, '
        'instant tables, transfer desks and original match comics &mdash; a serious football platform.</p>\n'
        '    <div class="sh-hero-fact"><span><b>5</b> Leagues</span><span><b>45</b> Results</span>'
        '<span><b>117</b> Goals</span><span class="sh-hero-fact"><i class="sh-live-dot"></i> Live on matchdays</span></div>\n'
        '    <div class="sh-hero-cta">\n'
        '      <a class="sh-btn sh-btn-primary" href="/sports/premier-league/matches/">Explore matches '
        '<svg viewBox="0 0 24 24" fill="none"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></a>\n'
        '      <a class="sh-btn sh-btn-glass" href="/sports/comics/">Watch the comics</a>\n'
        '      <a class="sh-btn sh-btn-glass" href="/sports/transfers/">Transfer desk</a>\n'
        '    </div>\n'
        '  </div>\n'
        '</section>\n'

        '<!-- ============ CATEGORY NAV (horizontal) ============ -->\n'
        '<nav class="sh-cats" aria-label="Sports categories"><div class="sh-cats-in"><div class="sh-cats-scroll">'
        + cats + '</div></div></nav>\n'

        '<!-- ============ LIVE TICKER (engine) ============ -->\n'
        '<div class="shell"><div class="sp-ticker" aria-label="Latest results"><div data-sp-engine data-sp-ticker>'
        '<div class="tk-track"><span class="tk"><em>Premier League</em><b>MCI 2&ndash;1 BOU</b><i>FT</i></span>'
        '<span class="tk"><em>Premier League</em><b>BHA 4&ndash;0 AVL</b><i>FT</i></span>'
        '<span class="tk"><em>Premier League</em><b>NEW 2&ndash;2 LIV</b><i>FT</i></span>'
        '<span class="tk"><em>Serie A</em><b>ROM 4&ndash;0 FIO</b><i>FT</i></span>'
        '<span class="tk"><em>La Liga</em><b>ELC 0&ndash;5 BAR</b><i>FT</i></span></div>'
        '</div></div></div>\n'

        '<!-- ============ TOP STORIES (engine rail) ============ -->\n'
        '<section class="sh-sec" aria-label="Top stories">\n'
        '  <div class="sh-sec-head"><div><span class="sh-sec-kick">Editorial</span>'
        '<h2 class="sh-sec-title">Top stories</h2></div>'
        '<a class="sh-sec-more" href="/sports/articles/">All stories</a></div>\n'
        + art_rail + '\n'
        '</section>\n'

        '<!-- ============ LIVE / UPCOMING MATCHES (live engine) ============ -->\n'
        '<section class="sh-sec" aria-label="Live match board">\n'
        '  <div class="sh-sec-head"><div><span class="sh-sec-kick"><i class="sh-live-dot"></i> Live desk</span>'
        '<h2 class="sh-sec-title">The board &mdash; live scores</h2>'
        '<p class="sh-sec-sub">Sourced results and live scoreboxes, refreshed automatically on matchdays.</p></div>'
        '<a class="sh-sec-more" href="/sports/premier-league/table/">Full table</a></div>\n'
        + '<div class="sp-layout shell"><div class="sp-main">' + BOARD + '\n'
        '</section>\n'

        '<!-- ============ FOOTBALL COMICS ============ -->\n'
        '<section class="sh-sec" aria-label="Football comics">\n'
        '  <div class="sh-sec-head"><div><span class="sh-sec-kick">Original artwork</span>'
        '<h2 class="sh-sec-title">Football comics</h2>'
        '<p class="sh-sec-sub">Match stories drawn as cinematic comics &mdash; sourced scores, no official artwork.</p></div>'
        '<a class="sh-sec-more" href="/sports/comics/">All comics</a></div>\n'
        '  <div class="sh-car"><div class="sh-car-view" tabindex="0"><div class="sh-car-track">'
        + comics + '</div></div>' + carousel_nav() + '</div>\n'
        '</section>\n'

        '<!-- ============ FEATURED ============ -->\n'
        '<section class="sh-sec" aria-label="Featured stories">\n'
        '  <div class="sh-sec-head"><div><span class="sh-sec-kick">On the desk</span>'
        '<h2 class="sh-sec-title">Featured</h2></div>'
        '<a class="sh-sec-more" href="/sports/articles/">All stories</a></div>\n'
        '<div class="sh-comp-grid">'
        '<a class="sh-story" href="/sports/world-cup-2026-spain-champions/" style="--card-img:url(\'/assets/img/sports/hero-world-cup-md.jpg\')"><span class="sh-story-em">World Cup 2026</span><h3>Spain are world champions</h3><p>Ferran Torres in the 106th minute at MetLife.</p><span class="sh-story-cta">Read the story &rarr;</span></a>'
        '<a class="sh-story" href="/sports/ballon-dor-race/" style="--card-img:url(\'/assets/img/sports/hero-ballon-dor-md.jpg\')"><span class="sh-story-em">Ballon d&rsquo;Or</span><h3>London, 26 October. The winner is not decided.</h3><p>The 70th ceremony is confirmed. Last year&rsquo;s winners are confirmed. This year&rsquo;s names are not.</p><span class="sh-story-cta">Read the story &rarr;</span></a>'
        '<a class="sh-story" href="/sports/premier-league-matchweek-1-guide/" style="--card-img:url(\'/assets/img/sports/hero-matchweek-md.jpg\')"><span class="sh-story-em">Premier League</span><h3>Matchweek 2: fixtures &amp; picks</h3><p>Every Friday-to-Monday fixture, kick-off and TV listing.</p><span class="sh-story-cta">Read the story &rarr;</span></a>'
        '<a class="sh-story" href="/sports/manchester-city-without-guardiola/" style="--card-img:url(\'/assets/img/sports/hero-man-city-manager-md.jpg\')"><span class="sh-story-em">Football</span><h3>Manchester City after Guardiola</h3><p>Ten years, four titles and a new manager. What is officially confirmed.</p><span class="sh-story-cta">Read the story &rarr;</span></a>'
        '</div>\n'
        '</section>\n'

        '<!-- ============ COMPETITIONS ============ -->\n'
        '<section class="sh-sec" aria-label="Competitions">\n'
        '  <div class="sh-sec-head"><div><span class="sh-sec-kick">Competitions</span>'
        '<h2 class="sh-sec-title">Pick a league</h2></div></div>\n'
        '<div class="sh-comp-grid">'
        '<a class="sh-comp sh-comp-wide" href="/sports/premier-league/" style="--card-img:url(\'/assets/img/sports/hero-premier-league-md.jpg\')"><em>England</em><b>Premier League</b><span>A full desk: fixtures, sourced results, FPL, transfers, clubs and match pages.</span></a>'
        '<a class="sh-comp" href="/sports/champions-league/" style="--card-img:url(\'/assets/img/sports/hero-ucl-md.jpg\')"><em>Europe</em><b>Champions League</b><span>Format, brackets and the nights that define the competition.</span></a>'
        '<a class="sh-comp" href="/sports/la-liga/" style="--card-img:url(\'/assets/img/sports/hero-la-liga-md.jpg\')"><em>Spain</em><b>La Liga</b><span>380 fixtures, match pages and the transfer desk.</span></a>'
        '<a class="sh-comp" href="/sports/serie-a/" style="--card-img:url(\'/assets/img/sports/hero-serie-a-md.jpg\')"><em>Italy</em><b>Serie A</b><span>The opening weeks, clubs and confirmed business.</span></a>'
        '<a class="sh-comp" href="/sports/bundesliga/" style="--card-img:url(\'/assets/img/sports/hero-bundesliga-md.jpg\')"><em>Germany</em><b>Bundesliga</b><span>306 fixtures and the 2026/27 tracker.</span></a>'
        '<a class="sh-comp" href="/sports/ligue-1/" style="--card-img:url(\'/assets/img/sports/hero-ligue-1-md.jpg\')"><em>France</em><b>Ligue 1</b><span>Paris, Marseille and the rest of the calendar.</span></a>'
        '</div>\n'
        '</section>\n'

        '<!-- ============ LATEST STORIES ============ -->\n'
        + '<div class="sh-sec">' + STORIES + '</div>\n'

        '<!-- ============ TRANSFERS ============ -->\n'
        '<section class="sh-sec" aria-label="Transfers">\n'
        '  <div class="sh-sec-head"><div><span class="sh-sec-kick"><i class="sh-live-dot"></i> Window</span>'
        '<h2 class="sh-sec-title">Transfer desks</h2>'
        '<p class="sh-sec-sub">Every confirmed deal, tracked by league as the window stays open.</p></div>'
        '<a class="sh-sec-more" href="/sports/transfers/">All transfers</a></div>\n'
        '  <div class="sh-car"><div class="sh-car-view" tabindex="0"><div class="sh-car-track">'
        + transfers + '</div></div>' + carousel_nav() + '</div>\n'
        '</section>\n'

        '<!-- ============ FIXTURES ============ -->\n'
        '<section class="sh-sec" aria-label="Fixtures and results">\n'
        '  <div class="sh-sec-head"><div><span class="sh-sec-kick">Calendar</span>'
        '<h2 class="sh-sec-title">Fixtures &amp; results 2026/27</h2></div>'
        '<a class="sh-sec-more" href="/sports/premier-league/fixtures/">All fixtures</a></div>\n'
        '<div class="sh-linkgrid">'
        '<a class="sh-linkcard" href="/sports/premier-league/fixtures/"><b>Premier League</b><span>All 380 fixtures &mdash; dates, kick-offs &amp; match pages.</span></a>'
        '<a class="sh-linkcard" href="/sports/la-liga/fixtures/"><b>La Liga</b><span>All 380 fixtures &mdash; dates, kick-offs &amp; match pages.</span></a>'
        '<a class="sh-linkcard" href="/sports/serie-a/fixtures/"><b>Serie A</b><span>All 380 fixtures &mdash; dates, kick-offs &amp; match pages.</span></a>'
        '<a class="sh-linkcard" href="/sports/bundesliga/fixtures/"><b>Bundesliga</b><span>All 306 fixtures &mdash; dates, kick-offs &amp; match pages.</span></a>'
        '<a class="sh-linkcard" href="/sports/ligue-1/fixtures/"><b>Ligue 1</b><span>All 306 fixtures &mdash; dates, kick-offs &amp; match pages.</span></a>'
        '<a class="sh-linkcard" href="/sports/managers-2026-27/"><b>Managers</b><span>Managers in &amp; out &mdash; 2026/27.</span></a>'
        '</div>\n'
        '</section>\n'

        '<!-- ============ EXPLORE ============ -->\n'
        '<section class="sh-sec" aria-label="Explore the desk">\n'
        '  <div class="sh-sec-head"><div><span class="sh-sec-kick">More from the desk</span>'
        '<h2 class="sh-sec-title">Explore</h2>'
        '<p class="sh-sec-sub">Club histories, rivalry explainers, records, player profiles, previews and reports.</p></div></div>\n'
        '<div class="sh-comp-grid">'
        '<a class="sh-comp" href="/sports/records/" style="--card-img:url(\'/assets/img/sports/hero-ballon-dor-md.jpg\')"><em>Numbers</em><b>Records</b><span>Titles, streaks, milestones and the numbers behind the achievements.</span></a>'
        '<a class="sh-comp" href="/sports/teams/" style="--card-img:url(\'/assets/img/sports/hero-arsenal-md.jpg\')"><em>Clubs</em><b>Clubs by league</b><span>Every top-five club, filed under its own league.</span></a>'
        '<a class="sh-comp" href="/sports/clubs/" style="--card-img:url(\'/assets/img/sports/hero-arsenal-md.jpg\')"><em>Directory</em><b>Clubs</b><span>Club histories, identities, rivalries and how they are run.</span></a>'
        '<a class="sh-comp" href="/sports/history/" style="--card-img:url(\'/assets/img/sports/hero-matches-md.jpg\')"><em>Archive</em><b>Football history</b><span>Eras, turning points and the matches that changed the sport.</span></a>'
        '<a class="sh-comp" href="/sports/international/" style="--card-img:url(\'/assets/img/sports/hero-world-cup-md.jpg\')"><em>Nations</em><b>International</b><span>World Cup, continental championships and national-team football.</span></a>'
        '<a class="sh-comp" href="/sports/players/" style="--card-img:url(\'/assets/img/sports/hero-ballon-dor-md.jpg\')"><em>People</em><b>Players</b><span>Careers, styles and the athletes shaping the game.</span></a>'
        '</div>\n'
        '</section>\n'

        '<!-- ============ SEASON VIDEO ============ -->\n'
        + VIDEO + '\n\n'

        '<!-- ============ EVERYTHING ELSE ON BRYME ============ -->\n'
        + COREHUBS + '\n\n'

        '<!-- ============ FAQ ============ -->\n'
        + FAQ + '\n')

out = head + "</head>\n" + bodyprefix + main + tail
open(SRC, "w", encoding="utf-8").write(out)
print("WROTE", os.path.getsize(SRC), "bytes")
print("engine containers:", out.count("data-sp-engine"), "| sports-hub.css:", "sports-hub.css" in out)
# sanity: count preserved links
import re as _re
print("unique hrefs:", len(set(_re.findall(r'href="([^"]*)"', out))))

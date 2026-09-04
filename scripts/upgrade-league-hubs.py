#!/usr/bin/env python3
"""Give each league hub the same cinematic landing as /sports/."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

LEAGUES = {
    'premier-league': {
        'kicker': 'England · 2026/27',
        'h1': 'The Premier League is here.',
        'lead': 'Matchweek 1 is live. Sourced results only. Fixtures, FPL, transfers and the clubs that came up.',
        'img': '/assets/img/sports/hero-premier-league.jpg',
        'cta': ('/sports/premier-league/matches/', 'Match Centre'),
        'ghost': ('/sports/premier-league/results/', 'Results'),
        'chips': [
            ('/sports/teams/', 'Team pages'),
            ('/sports/premier-league/fixtures/', 'Fixtures'),
            ('/sports/premier-league/results/', 'Results'),
            ('/sports/fpl/', 'FPL'),
            ('/sports/transfers/premier-league-2026-27/', 'Transfers'),
        ],
        'tiles': [
            ('wide', '/sports/premier-league/matches/', 'hero-matchweek.jpg', 'Now', 'Match Centre', 'Matchweek 1 fixtures, previews and sourced results.'),
            ('', '/sports/premier-league/fixtures/', 'hero-premier-league.jpg', 'Calendar', 'Fixtures', 'All 380 fixtures across 38 rounds — dates and kick-offs.'),
            ('', '/sports/premier-league/results/', 'hero-matches.jpg', 'Scores', 'Results', 'Verified full-time scores only. Nothing invented.'),
            ('', '/sports/fpl/', 'hero-fpl.jpg', 'Fantasy', 'FPL', 'Gameweek coverage, picks and captaincy talk — sourced.'),
            ('', '/sports/transfers/premier-league-2026-27/', 'hero-breakout.jpg', 'Business', 'Transfers', '87 in / 72 out tracked · 115 confirmed.'),
            ('', '/sports/premier-league/table/', 'hero-ballon-dor.jpg', 'Table', 'Table', 'Editorial prediction now. Official table when the league publishes one.'),
        ],
    },
    'la-liga': {
        'kicker': 'Spain · 2026/27',
        'h1': 'La Liga 2026/27.',
        'lead': '380 fixtures, match pages and a transfer desk. Results only after they are official.',
        'img': '/assets/img/sports/hero-la-liga.jpg',
        'cta': ('/sports/la-liga/matches/', 'Match Centre'),
        'ghost': ('/sports/la-liga/results/', 'Results'),
        'chips': [
            ('/sports/teams/', 'Team pages'),
            ('/sports/la-liga/fixtures/', 'Fixtures'),
            ('/sports/la-liga/results/', 'Results'),
            ('/sports/transfers/la-liga-2026-27/', 'Transfers'),
        ],
        'tiles': [
            ('wide', '/sports/la-liga/matches/', 'hero-la-liga.jpg', 'Now', 'Match Centre', 'Jornada 1 fixtures and match analysis.'),
            ('', '/sports/la-liga/fixtures/', 'hero-la-liga.jpg', 'Calendar', 'Fixtures', 'All 380 fixtures — dates, kick-offs and match pages.'),
            ('', '/sports/la-liga/results/', 'hero-matches.jpg', 'Scores', 'Results', '7 verified results. Nothing assumed.'),
            ('', '/sports/transfers/la-liga-2026-27/', 'hero-breakout.jpg', 'Business', 'Transfers', '48 in / 41 out tracked · 61 confirmed.'),
            ('', '/sports/managers-2026-27/', 'hero-man-city-manager.jpg', 'Dugout', 'Managers', '8 new managers confirmed for 2026/27.'),
        ],
    },
    'serie-a': {
        'kicker': 'Italy · 2026/27',
        'h1': 'Serie A 2026/27.',
        'lead': 'Giornata 1 is underway. Match pages first. Results only when they are official.',
        'img': '/assets/img/sports/hero-serie-a.jpg',
        'cta': ('/sports/serie-a/matches/', 'Match Centre'),
        'ghost': ('/sports/serie-a/fixtures/', 'Fixtures'),
        'chips': [
            ('/sports/teams/', 'Team pages'),
            ('/sports/serie-a/results/', 'Results'),
            ('/sports/transfers/serie-a-2026-27/', 'Transfers'),
        ],
        'tiles': [
            ('wide', '/sports/serie-a/matches/', 'hero-serie-a.jpg', 'Now', 'Match Centre', 'Giornata 1 fixtures and match analysis.'),
            ('', '/sports/serie-a/fixtures/', 'hero-serie-a.jpg', 'Calendar', 'Fixtures', 'All 380 fixtures — dates, kick-offs and match pages.'),
            ('', '/sports/serie-a/results/', 'hero-matches.jpg', 'Scores', 'Results', 'Season just opened — no invented scores.'),
            ('', '/sports/transfers/serie-a-2026-27/', 'hero-breakout.jpg', 'Business', 'Transfers', '18 in / 16 out tracked · 28 confirmed.'),
            ('', '/sports/managers-2026-27/', 'hero-man-city-manager.jpg', 'Dugout', 'Managers', '11 new managers confirmed for 2026/27.'),
        ],
    },
    'bundesliga': {
        'kicker': 'Germany · 2026/27',
        'h1': 'Bundesliga 2026/27.',
        'lead': 'Spieltag 1 starts Friday 28 August. The calendar is up. Scores wait until they are played.',
        'img': '/assets/img/sports/hero-bundesliga.jpg',
        'cta': ('/sports/bundesliga/matches/', 'Match Centre'),
        'ghost': ('/sports/bundesliga/fixtures/', 'Fixtures'),
        'chips': [
            ('/sports/bundesliga/results/', 'Results'),
            ('/sports/transfers/bundesliga-2026-27/', 'Transfers'),
        ],
        'tiles': [
            ('wide', '/sports/bundesliga/matches/', 'hero-bundesliga.jpg', 'Now', 'Match Centre', 'Spieltag 1 fixtures and match analysis.'),
            ('', '/sports/bundesliga/fixtures/', 'hero-bundesliga.jpg', 'Calendar', 'Fixtures', 'All 306 fixtures — dates, kick-offs and match pages.'),
            ('', '/sports/bundesliga/results/', 'hero-matches.jpg', 'Scores', 'Results', 'Season starts 28 August — no results yet.'),
            ('', '/sports/transfers/bundesliga-2026-27/', 'hero-breakout.jpg', 'Business', 'Transfers', '23 in / 18 out tracked · 33 confirmed.'),
            ('', '/sports/managers-2026-27/', 'hero-man-city-manager.jpg', 'Dugout', 'Managers', '5 new managers confirmed for 2026/27.'),
        ],
    },
    'ligue-1': {
        'kicker': 'France · 2026/27',
        'h1': 'Ligue 1 2026/27.',
        'lead': 'Journée 1 is on. Marseille 4–0 Strasbourg is locked. Everything else waits for a source.',
        'img': '/assets/img/sports/hero-ligue-1.jpg',
        'cta': ('/sports/ligue-1/matches/', 'Match Centre'),
        'ghost': ('/sports/ligue-1/results/', 'Results'),
        'chips': [
            ('/sports/ligue-1/fixtures/', 'Fixtures'),
            ('/sports/transfers/ligue-1-2026-27/', 'Transfers'),
        ],
        'tiles': [
            ('wide', '/sports/ligue-1/matches/', 'hero-ligue-1.jpg', 'Now', 'Match Centre', 'Journée 1 fixtures and match analysis.'),
            ('', '/sports/ligue-1/fixtures/', 'hero-ligue-1.jpg', 'Calendar', 'Fixtures', 'All 306 fixtures — dates, kick-offs and match pages.'),
            ('', '/sports/ligue-1/results/', 'hero-matches.jpg', 'Scores', 'Results', '1 verified result — Marseille 4–0 Strasbourg.'),
            ('', '/sports/transfers/ligue-1-2026-27/', 'hero-breakout.jpg', 'Business', 'Transfers', '31 in / 16 out tracked · 42 confirmed.'),
            ('', '/sports/managers-2026-27/', 'hero-man-city-manager.jpg', 'Dugout', 'Managers', '12 new managers confirmed for 2026/27.'),
        ],
    },
}


def land(meta):
    chips = ''.join(f'<a href="{h}">{n}</a>' for h, n in meta['chips'])
    tiles = []
    for kind, href, img, em, b, span in meta['tiles']:
        wide = ' sp-comp-wide' if kind == 'wide' else ''
        tiles.append(
            f'<a class="sp-comp-card{wide}" href="{href}" style="--card-img:url(\'/assets/img/sports/{img}\')">'
            f'<em>{em}</em><b>{b}</b><span>{span}</span></a>'
        )
    return (
        f'<section class="sp-land" style="--sp-hero:url(\'{meta["img"]}\')" aria-label="{meta["h1"]}">'
        f'<div class="sp-land-bg" aria-hidden="true"></div>'
        f'<div class="sp-land-inner">'
        f'<p class="sp-land-kicker"><i></i> {meta["kicker"]}</p>'
        f'<h1>{meta["h1"]}</h1>'
        f'<p class="sp-land-lead">{meta["lead"]}</p>'
        f'<div class="sp-land-actions">'
        f'<a class="cta" href="{meta["cta"][0]}">{meta["cta"][1]}</a>'
        f'<a class="cta-ghost" href="{meta["ghost"][0]}">{meta["ghost"][1]}</a>'
        f'</div>'
        f'<nav class="sp-land-leagues">{chips}<a href="/sports/">All sports</a></nav>'
        f'</div></section>'
        f'<section class="sp-comp"><div class="shell">'
        f'<div class="section-head"><div><div class="eyebrow">This league</div><h2>Pick a desk</h2></div></div>'
        f'<div class="sp-comp-grid">{"".join(tiles)}</div></div></section>'
    )


def upgrade_league(slug, meta):
    page = ROOT / 'sports' / slug / 'index.html'
    raw = page.read_text(encoding='utf-8')
    i, j = raw.find('<main'), raw.find('</main>')
    head, main, tail = raw[:i], raw[i:j + 7], raw[j + 7:]
    # drop crumb + old text hero
    main = re.sub(r'<main class="shell">\s*<div class="crumb">.*?</div>\s*', '<main class="sp-desk">', main, count=1, flags=re.S)
    main = re.sub(r'<section class="sp-pl-hero">.*?</section>\s*', '', main, count=1, flags=re.S)
    # drop the plain vcat hub (keep the fixture carousel + related)
    main = re.sub(r'<section class="section"><div class="section-head"><h2>.*?</h2></div><div class="vcat-grid">.*?</div></section>\s*', '', main, count=1, flags=re.S)
    insert_at = main.find('<section')
    if insert_at < 0:
        raise SystemExit(f'no section in {slug}')
    main = main[:insert_at] + land(meta) + main[insert_at:]
    if meta['img'] not in head:
        head = head.replace('</head>', f'<link rel="preload" as="image" href="{meta["img"]}" fetchpriority="high"></head>', 1)
    page.write_text(head + main + tail, encoding='utf-8')
    print('upgraded', slug, page.stat().st_size)


def upgrade_ucl():
    page = ROOT / 'sports' / 'champions-league' / 'index.html'
    raw = page.read_text(encoding='utf-8')
    i, j = raw.find('<main'), raw.find('</main>')
    head, main, tail = raw[:i], raw[i:j + 7], raw[j + 7:]
    also = re.search(r'<section class="section core-hubs".*?</section>', main, re.S)
    also_html = also.group(0) if also else ''
    new = '''<main class="sp-desk">
<section class="sp-land" style="--sp-hero:url('/assets/img/sports/hero-ucl.jpg')" aria-label="Champions League">
  <div class="sp-land-bg" aria-hidden="true"></div>
  <div class="sp-land-inner">
    <p class="sp-land-kicker"><i></i> Europe</p>
    <h1>Champions League.</h1>
    <p class="sp-land-lead">The group stage is gone. One 36-team table, eight league-phase games, then the nights that define the competition.</p>
    <div class="sp-land-actions">
      <a class="cta" href="/sports/champions-league-format-explained/">How it works now</a>
      <a class="cta-ghost" href="/sports/">Back to Sports</a>
    </div>
  </div>
</section>
<section class="sp-comp"><div class="shell">
  <div class="sp-comp-grid">
    <a class="sp-comp-card sp-comp-wide" href="/sports/champions-league-format-explained/" style="--card-img:url('/assets/img/sports/hero-ucl.jpg')"><em>Format</em><b>How the Champions League actually works now</b><span>The group stage is gone. One 36-team table, eight league-phase games.</span></a>
    <a class="sp-comp-card" href="/sports/records/" style="--card-img:url('/assets/img/sports/hero-ballon-dor.jpg')"><em>Numbers</em><b>Records</b><span>Titles, streaks and the nights that set them.</span></a>
    <a class="sp-comp-card" href="/sports/premier-league/" style="--card-img:url('/assets/img/sports/hero-premier-league.jpg')"><em>England</em><b>Premier League</b><span>The domestic desk those European nights sit on.</span></a>
    <a class="sp-comp-card" href="/sports/la-liga/" style="--card-img:url('/assets/img/sports/hero-la-liga.jpg')"><em>Spain</em><b>La Liga</b><span>Madrid, Barcelona and the rest of the Spanish calendar.</span></a>
    <a class="sp-comp-card" href="/sports/serie-a/" style="--card-img:url('/assets/img/sports/hero-serie-a.jpg')"><em>Italy</em><b>Serie A</b><span>The Italian clubs heading into Europe.</span></a>
  </div>
</div></section>
'''
    if also_html:
        new += '<div class="shell">' + also_html + '</div>\n</main>'
    else:
        new += '</main>'
    if 'hero-ucl.jpg' not in head:
        head = head.replace('</head>', '<link rel="preload" as="image" href="/assets/img/sports/hero-ucl.jpg" fetchpriority="high"></head>', 1)
    page.write_text(head + new + tail, encoding='utf-8')
    print('upgraded champions-league', page.stat().st_size)


def upgrade_home():
    page = ROOT / 'index.html'
    t = page.read_text(encoding='utf-8')
    t = t.replace("url('/assets/img/sports/hero-premier-league.jpg')", "url('/assets/img/sports/hero-landing.jpg')")
    t = t.replace("url('/assets/img/money/hero-writing.jpg')", "url('/assets/img/money/hero-landing.jpg')")
    t = t.replace("url('/assets/img/tech/hero-hosting.jpg')", "url('/assets/img/tech/hero-landing.jpg')")
    t = t.replace(
        '<p>Previews, results, tables & transfer stories.</p>',
        '<p>Night-stadium desk: sourced scores, five leagues, no invented results.</p>',
    )
    page.write_text(t, encoding='utf-8')
    print('home hub images updated')


if __name__ == '__main__':
    for slug, meta in LEAGUES.items():
        upgrade_league(slug, meta)
    upgrade_ucl()
    upgrade_home()

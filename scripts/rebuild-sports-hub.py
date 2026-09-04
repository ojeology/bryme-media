#!/usr/bin/env python3
"""Rebuild /sports/ landing page with the v2 night-stadium hub.

Surgical: keeps the existing <head> + footer/nav shell. Does not invent scores. Sunday 23 Aug board is previews until a sourced FT exists.
"""
from pathlib import Path
import html as H
import re

ROOT = Path(__file__).resolve().parents[1]


def esc(s):
    return H.escape(str(s), quote=True)


def card(href, home, away, home_crest, away_crest, status, home_score=None, away_score=None, go='Open →'):
    ft = status == 'FT'
    pill_cls = 'ft' if ft else 'ko'
    pill = 'FT' if ft else status
    hs = esc(home_score) if home_score is not None else '<span class="sp-sc-num muted">–</span>'
    aws = esc(away_score) if away_score is not None else '<span class="sp-sc-num muted">–</span>'
    if home_score is not None:
        hs = f'<b class="sp-sc-num">{esc(home_score)}</b>'
    if away_score is not None:
        aws = f'<b class="sp-sc-num">{esc(away_score)}</b>'
    return (
        f'<a class="sp-scorecard" href="{esc(href)}">'
        f'<div class="sp-sc-top"><span class="sp-sc-pill {pill_cls}">{esc(pill)}</span>'
        f'<span class="sp-sc-go">{esc(go)}</span></div>'
        f'<div>'
        f'<div class="sp-sc-row"><div class="sp-sc-club"><img src="{esc(home_crest)}" alt="" width="32" height="32">'
        f'<span>{esc(home)}</span></div>{hs}</div>'
        f'<div class="sp-sc-row"><div class="sp-sc-club"><img src="{esc(away_crest)}" alt="" width="32" height="32">'
        f'<span>{esc(away)}</span></div>{aws}</div>'
        f'</div></a>'
    )


PL = '/assets/img/sports/pl/'
LL = '/assets/img/sports/ll/'
SA = '/assets/img/sports/sa/'
L1 = '/assets/img/sports/l1/'

# Sunday 23 Aug — previews only until FT is sourced
pl_today = ''.join([
    card('/sports/premier-league/matches/brighton-vs-aston-villa/', 'Brighton', 'Aston Villa',
         PL + 'brighton.svg', PL + 'aston-villa.svg', '14:00', None, None, 'Preview →'),
    card('/sports/premier-league/matches/man-city-vs-bournemouth/', 'Man City', 'Bournemouth',
         PL + 'man-city.svg', PL + 'bournemouth.svg', '14:00', None, None, 'Preview →'),
    card('/sports/premier-league/matches/newcastle-vs-liverpool/', 'Newcastle', 'Liverpool',
         PL + 'newcastle.svg', PL + 'liverpool.svg', '16:30', None, None, 'Preview →'),
])

ll_today = ''.join([
    card('/sports/la-liga/matches/atletico-madrid-vs-villarreal/', 'Atlético', 'Villarreal',
         LL + 'atletico.png', LL + 'villarreal.png', '17:00', None, None, 'Preview →'),
    card('/sports/la-liga/matches/getafe-vs-racing/', 'Getafe', 'Racing',
         LL + 'getafe.png', LL + 'racing.png', '19:30', None, None, 'Preview →'),
    card('/sports/la-liga/matches/elche-vs-barcelona/', 'Elche', 'Barcelona',
         LL + 'elche.png', LL + 'barcelona.png', '21:30', None, None, 'Preview →'),
])

sa_today = ''.join([
    card('/sports/serie-a/matches/frosinone-vs-juventus/', 'Frosinone', 'Juventus',
         SA + 'frosinone.svg', SA + 'juventus.svg', '18:30', None, None, 'Preview →'),
    card('/sports/serie-a/matches/venezia-vs-lecce/', 'Venezia', 'Lecce',
         SA + 'venezia.svg', SA + 'lecce.svg', '18:30', None, None, 'Preview →'),
    card('/sports/serie-a/matches/atalanta-vs-sassuolo/', 'Atalanta', 'Sassuolo',
         SA + 'atalanta.svg', SA + 'sassuolo.svg', '20:45', None, None, 'Preview →'),
    card('/sports/serie-a/matches/torino-vs-milan/', 'Torino', 'AC Milan',
         SA + 'torino.svg', SA + 'milan.svg', '20:45', None, None, 'Preview →'),
])

l1_today = ''.join([
    card('/sports/ligue-1/matches/angers-vs-lille/', 'Angers SCO', 'Lille',
         L1 + 'angers.webp', L1 + 'lille.webp', '15:00', None, None, 'Preview →'),
    card('/sports/ligue-1/matches/le-havre-vs-monaco/', 'Le Havre', 'Monaco',
         L1 + 'le-havre.webp', L1 + 'monaco.webp', '17:15', None, None, 'Preview →'),
    card('/sports/ligue-1/matches/psg-vs-rennes/', 'PSG', 'Rennes',
         L1 + 'psg.webp', L1 + 'rennes.webp', '20:45', None, None, 'Preview →'),
])

pl_yday = ''.join([
    card('/sports/premier-league/matches/hull-vs-man-united/', 'Hull City', 'Manchester United',
         PL + 'hull.svg', PL + 'man-united.svg', 'FT', 2, 0, 'Result →'),
    card('/sports/premier-league/matches/everton-vs-crystal-palace/', 'Everton', 'Crystal Palace',
         PL + 'everton.svg', PL + 'crystal-palace.svg', 'FT', 2, 0, 'Result →'),
    card('/sports/premier-league/matches/ipswich-vs-sunderland/', 'Ipswich Town', 'Sunderland',
         PL + 'ipswich.svg', PL + 'sunderland.svg', 'FT', 2, 1, 'Result →'),
    card('/sports/premier-league/matches/nottingham-forest-vs-leeds/', 'Nott\'m Forest', 'Leeds United',
         PL + 'nottingham-forest.svg', PL + 'leeds.svg', 'FT', 0, 1, 'Result →'),
    card('/sports/premier-league/matches/brentford-vs-tottenham/', 'Brentford', 'Tottenham',
         PL + 'brentford.svg', PL + 'tottenham.svg', 'FT', 3, 0, 'Result →'),
])


MAIN = f'''<main class="sp-desk">
<section class="sp-land" style="--sp-hero:url('/assets/img/sports/hero-landing.jpg')" aria-label="BRYME Sports">
  <div class="sp-land-bg" aria-hidden="true"></div>
  <div class="sp-land-inner">
    <p class="sp-land-kicker"><i></i> Matchday · Sunday 23 August 2026</p>
    <h1>Sunday is live.</h1>
    <p class="sp-land-lead">Brighton–Villa and City–Bournemouth at 14:00. Newcastle–Liverpool at 16:30. Previews until full-time is sourced. Saturday’s scores stay on the desk below.</p>
    <div class="sp-land-actions">
      <a class="cta" href="/sports/premier-league/matches/">Match Centre</a>
      <a class="cta-ghost" href="/sports/premier-league/results/">Premier League results</a>
    </div>
    <nav class="sp-land-leagues" aria-label="Leagues">
      <a href="/sports/premier-league/">Premier League</a>
      <a href="/sports/la-liga/">La Liga</a>
      <a href="/sports/serie-a/">Serie A</a>
      <a href="/sports/bundesliga/">Bundesliga</a>
      <a href="/sports/ligue-1/">Ligue 1</a>
      <a href="/sports/champions-league/">Champions League</a>
    </nav>
  </div>
</section>

<section class="sp-board" aria-label="Sunday's board">
  <div class="shell">
    <div class="sp-board-head">
      <div><div class="eyebrow">Live desk</div><h2>Sunday's board</h2></div>
      <span class="sp-board-date">23 August 2026 · previews until FT is sourced</span>
    </div>

    <div class="sp-lg">
      <div class="sp-lg-head"><b>Premier League</b><a href="/sports/premier-league/matches/">Match Centre →</a></div>
      <div class="sp-score-grid">{pl_today}</div>
    </div>
    <div class="sp-lg">
      <div class="sp-lg-head"><b>La Liga</b><a href="/sports/la-liga/fixtures/">Fixtures →</a></div>
      <div class="sp-score-grid">{ll_today}</div>
    </div>
    <div class="sp-lg">
      <div class="sp-lg-head"><b>Serie A</b><a href="/sports/serie-a/fixtures/">Fixtures →</a></div>
      <div class="sp-score-grid">{sa_today}</div>
    </div>
    <div class="sp-lg">
      <div class="sp-lg-head"><b>Ligue 1</b><a href="/sports/ligue-1/fixtures/">Fixtures →</a></div>
      <div class="sp-score-grid">{l1_today}</div>
    </div>
    <div class="sp-lg">
      <div class="sp-lg-head"><b>Bundesliga</b><a href="/sports/bundesliga/fixtures/">Fixtures →</a></div>
      <p class="sp-empty">No Bundesliga fixtures today. Spieltag 1 starts Friday 28 August.</p>
    </div>

    <div class="sp-lg">
      <div class="sp-lg-head"><b>Yesterday — Saturday 22 Aug</b><a href="/sports/premier-league/results/">All results →</a></div>
      <div class="sp-score-grid">{pl_yday}</div>
    </div>

    <div class="sp-lg sp-desk-previews">
      <div class="sp-lg-head"><b>Matchday previews</b><a href="/sports/premier-league/matches/">Match Centre →</a></div>
      <p class="sp-desk-note">Published before kickoff. A score appears here only after it is sourced.</p>
      <div class="sp-prev-grid">
        <a class="sp-prev" href="/sports/premier-league/matches/brighton-vs-aston-villa/"><em>Sun 23 Aug · 14:00</em><b>Brighton v Aston Villa</b><span>Premier League · preview</span></a>
        <a class="sp-prev" href="/sports/premier-league/matches/man-city-vs-bournemouth/"><em>Sun 23 Aug · 14:00</em><b>Manchester City v Bournemouth</b><span>Premier League · preview</span></a>
        <a class="sp-prev" href="/sports/premier-league/matches/newcastle-vs-liverpool/"><em>Sun 23 Aug · 16:30</em><b>Newcastle v Liverpool</b><span>Premier League · preview</span></a>
        <a class="sp-prev" href="/sports/la-liga/matches/elche-vs-barcelona/"><em>Sun 23 Aug · 21:30</em><b>Elche v Barcelona</b><span>La Liga · preview</span></a>
        <a class="sp-prev" href="/sports/serie-a/matches/torino-vs-milan/"><em>Sun 23 Aug · 20:45</em><b>Torino v AC Milan</b><span>Serie A · preview</span></a>
        <a class="sp-prev" href="/sports/ligue-1/matches/psg-vs-rennes/"><em>Sun 23 Aug · 20:45</em><b>PSG v Rennes</b><span>Ligue 1 · preview</span></a>
        <a class="sp-prev" href="/sports/premier-league/matches/fulham-vs-chelsea/"><em>Mon 24 Aug · 20:00</em><b>Fulham v Chelsea</b><span>Premier League · tomorrow</span></a>
        <a class="sp-prev" href="/sports/premier-league/matches/brentford-vs-tottenham/"><em>Sat 22 Aug · 17:30</em><b>Brentford 3–0 Tottenham</b><span>Premier League · result locked</span></a>
      </div>
    </div>
  </div>
</section>

<section class="sp-comp">
  <div class="shell">
    <div class="section-head"><div><div class="eyebrow">Competitions</div><h2>Pick a league</h2></div></div>
    <div class="sp-comp-grid">
      <a class="sp-comp-card sp-comp-wide" href="/sports/premier-league/" style="--card-img:url('/assets/img/sports/hero-premier-league.jpg')">
        <em>England</em><b>Premier League</b><span>The English game in one desk: fixtures, sourced results, FPL, transfers, clubs and Matchweek 1 pages.</span>
      </a>
      <a class="sp-comp-card" href="/sports/champions-league/" style="--card-img:url('/assets/img/sports/hero-ucl.jpg')">
        <em>Europe</em><b>Champions League</b><span>Format, qualification, the knockout bracket and the nights that define the competition.</span>
      </a>
      <a class="sp-comp-card" href="/sports/la-liga/" style="--card-img:url('/assets/img/sports/hero-la-liga.jpg')">
        <em>Spain</em><b>La Liga</b><span>380 fixtures, match pages and the transfer desk.</span>
      </a>
      <a class="sp-comp-card" href="/sports/serie-a/" style="--card-img:url('/assets/img/sports/hero-serie-a.jpg')">
        <em>Italy</em><b>Serie A</b><span>The opening weeks, clubs and confirmed business.</span>
      </a>
      <a class="sp-comp-card" href="/sports/bundesliga/" style="--card-img:url('/assets/img/sports/hero-bundesliga.jpg')">
        <em>Germany</em><b>Bundesliga</b><span>306 fixtures and the 2026/27 tracker.</span>
      </a>
      <a class="sp-comp-card" href="/sports/ligue-1/" style="--card-img:url('/assets/img/sports/hero-ligue-1.jpg')">
        <em>France</em><b>Ligue 1</b><span>Paris, Marseille and the rest of the calendar.</span>
      </a>
    </div>
  </div>
</section>

<section class="sp-feat" aria-label="Featured stories">
  <div class="shell">
    <div class="section-head"><div><div class="eyebrow">On the desk</div><h2>Featured</h2></div><a href="/sports/articles/">All stories</a></div>
    <div class="sp-feat-grid">
      <a class="sp-feat-main" href="/sports/ballon-dor-race/" style="--card-img:url('/assets/img/sports/hero-ballon-dor.jpg')">
        <span class="tag">Ballon d'Or</span>
        <h2>London, 26 October. The winner is not decided.</h2>
        <p>The 70th ceremony is confirmed. Last year's winners are confirmed. This year's names are not.</p>
      </a>
      <div class="sp-feat-side">
        <a href="/sports/world-cup-2026-spain-champions/" style="--card-img:url('/assets/img/sports/hero-world-cup.jpg')">
          <span class="tag">World Cup 2026</span>
          <h3>Spain are world champions</h3>
          <p>Ferran Torres in the 106th minute at MetLife.</p>
        </a>
        <a href="/sports/premier-league-matchweek-1-guide/" style="--card-img:url('/assets/img/sports/hero-matchweek.jpg')">
          <span class="tag">Premier League</span>
          <h3>The opening round, confirmed</h3>
          <p>Every Friday-to-Monday fixture, kick-off and TV listing.</p>
        </a>
      </div>
    </div>
  </div>
</section>

<section class="sp-comp sp-explore">
  <div class="shell">
    <p class="lead" style="margin-bottom:18px">BRYME Sports is football. Club histories, rivalry explainers, records, player profiles, match previews and reports. We cover one sport properly rather than several thinly.</p>
    <div class="vnote">Current reporting (previews, results, transfers) is always researched before publication. No result, transfer, injury, fixture or statistic is ever invented.</div>
    <div class="section-head" style="margin-top:26px"><div><div class="eyebrow">More from the desk</div><h2>Explore</h2></div></div>
    <div class="sp-explore-grid">
      <a class="sp-comp-card" href="/sports/records/" style="--card-img:url('/assets/img/sports/hero-ballon-dor.jpg')"><em>Numbers</em><b>Records</b><span>Titles, streaks, milestones and the numbers behind the achievements.</span></a>
      <a class="sp-comp-card" href="/sports/teams/" style="--card-img:url('/assets/img/sports/hero-arsenal.jpg')"><em>Clubs</em><b>Clubs by league</b><span>Every top-five club, filed under its own league.</span></a>
      <a class="sp-comp-card" href="/sports/clubs/" style="--card-img:url('/assets/img/sports/hero-arsenal.jpg')"><em>Directory</em><b>Clubs</b><span>Club histories, identities, rivalries and how they are run.</span></a>
      <a class="sp-comp-card" href="/sports/history/" style="--card-img:url('/assets/img/sports/hero-matches.jpg')"><em>Archive</em><b>Football History</b><span>Eras, turning points and the matches that changed the sport.</span></a>
      <a class="sp-comp-card" href="/sports/international/" style="--card-img:url('/assets/img/sports/hero-world-cup.jpg')"><em>Nations</em><b>International</b><span>World Cup, continental championships and national-team football.</span></a>
      <a class="sp-comp-card" href="/sports/players/" style="--card-img:url('/assets/img/sports/hero-ballon-dor.jpg')"><em>People</em><b>Players</b><span>Careers, playing styles and the athletes shaping the game.</span></a>
    </div>
  </div>
</section>


<section class="section sports-teaser sp-video"><div class="shell">
  <div class="section-head"><h2>Premier League 2026/27</h2></div>
  <figure class="video-figure"><div class="trailer-frame" style="max-width:100%"><iframe src="https://www.youtube-nocookie.com/embed/nx8rgJrmSFY" title="PREMIER LEAGUE 2026/27 🔥 | THE WAIT IS OVER | OFFICIAL TRAILER ⚽🔥" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen loading="lazy" referrerpolicy="strict-origin-when-cross-origin"></iframe></div><figcaption>A third-party YouTube season clip from the channel Azar_kattumulla — not a Premier League Productions video.</figcaption></figure>
  <div class="video-context"><p>The player on this hub is a YouTube embed. The uploader is Azar_kattumulla. YouTube showed the clip as premiered on 11 August 2026. BRYME does not host the file, did not edit it, and does not run that channel. The uploader’s packaging uses the word official; the channel is not the Premier League’s own YouTube account, so do not read this as a league announcement.</p><p>It is here because this page is the front door to BRYME’s 2026/27 football desk — fixtures, match pages, and transfer trackers. A season-themed clip lets you stay on the hub instead of bouncing out for a video. It is not a source for kick-off times, tables, injuries, or signings. When BRYME publishes those, they come from club or league pages and are labelled.</p></div>
</div></section>

<section class="section"><div class="shell">
  <div class="section-head"><h2>Fixtures &amp; Results 2026/27</h2></div>
  <div class="vcat-grid">
    <a class="vcat" href="/sports/premier-league/fixtures/"><b>Premier League</b><span>All 380 fixtures — dates, kickoffs &amp; match pages</span></a>
    <a class="vcat" href="/sports/la-liga/fixtures/"><b>La Liga</b><span>All 380 fixtures — dates, kickoffs &amp; match pages</span></a>
    <a class="vcat" href="/sports/serie-a/fixtures/"><b>Serie A</b><span>All 380 fixtures — dates, kickoffs &amp; match pages</span></a>
    <a class="vcat" href="/sports/bundesliga/fixtures/"><b>Bundesliga</b><span>All 306 fixtures — dates, kickoffs &amp; match pages</span></a>
    <a class="vcat" href="/sports/ligue-1/fixtures/"><b>Ligue 1</b><span>All 306 fixtures — dates, kickoffs &amp; match pages</span></a>
    <a class="vcat" href="/sports/managers-2026-27/"><b>Managers</b><span>Managers In &amp; Out — 2026/27</span></a>
  </div>
</div></section>

<section class="section"><div class="shell">
  <div class="section-head"><h2>BRYME Sports Stories</h2><a href="/sports/articles/">All stories</a></div>
  <div class="story-grid">
    <a class="story-photo" href="/sports/arsenal-title-defence/" style="--card-img:url('/assets/img/sports/hero-arsenal.jpg')"><span>Football</span><h3>Arsenal's Title Defence Starts Friday Against Coventry</h3><p>Arsenal host Coventry on Friday to begin the defence of their first Premier League title since 2004. The Community Shield is already won.</p><b>Read story</b></a>
    <a class="story-photo" href="/sports/ballon-dor-race/" style="--card-img:url('/assets/img/sports/hero-ballon-dor.jpg')"><span>Players</span><h3>Ballon d'Or 2026: London, 26 October. The winner is not decided.</h3><p>UEFA and France Football have put the 70th Ballon d'Or in London on 26 October 2026.</p><b>Read story</b></a>
    <a class="story-photo" href="/sports/ballon-dor-2026-our-picks/" style="--card-img:url('/assets/img/sports/hero-ballon-dor.jpg')"><span>Players</span><h3>Who Is Leading the 2026 Ballon d'Or Race? Our Picks</h3><p>This is our assessment, not an official Ballon d'Or ranking. Only one player can win.</p><b>Read story</b></a>
    <a class="story-photo" href="/sports/newly-promoted-clubs-approach/" style="--card-img:url('/assets/img/sports/hero-premier-league.jpg')"><span>Football</span><h3>Coventry, Ipswich and Hull: The Three Clubs Back in the Premier League</h3><p>How they came up, their opening fixtures, and what this page will track.</p><b>Read story</b></a>
    <a class="story-photo" href="/sports/manchester-city-without-guardiola/" style="--card-img:url('/assets/img/sports/hero-man-city-manager.jpg')"><span>Football</span><h3>Manchester City After Guardiola: What Is Officially Confirmed</h3><p>Pep Guardiola stepped down after ten years. Enzo Maresca is the new manager.</p><b>Read story</b></a>
    <a class="story-photo" href="/sports/liverpools-next-chapter/" style="--card-img:url('/assets/img/sports/hero-liverpool.jpg')"><span>Football</span><h3>Liverpool Under Andoni Iraola: What the Club Has Confirmed</h3><p>Liverpool appointed Andoni Iraola on 4 June. His first Premier League match is at Newcastle on Sunday.</p><b>Read story</b></a>
    <a class="story-photo" href="/sports/premier-league-matchweek-1-guide/" style="--card-img:url('/assets/img/sports/hero-matchweek.jpg')"><span>Football</span><h3>Premier League Matchweek 1: The Opening Round, Confirmed</h3><p>Champions Arsenal host Coventry on Friday 21 August. The full opening round, with kick-off times and TV listings.</p><b>Read story</b></a>
    <a class="story-photo" href="/sports/five-matches-we-cannot-wait-to-watch/" style="--card-img:url('/assets/img/sports/hero-matches.jpg')"><span>Football</span><h3>Five Opening-Weekend Matches, and Why They Matter</h3><p>Arsenal–Coventry, Hull–United, City–Bournemouth, Newcastle–Liverpool and Fulham–Chelsea.</p><b>Read story</b></a>
  </div>
</div></section>

<section class="section core-hubs" data-core-hubs><div class="shell">
  <div class="section-head"><h2>Also on BRYME</h2></div>
  <p class="section-note">The main sections of the site. Open the next one that matches what you came for.</p>
  <div class="vchips">
    <a class="vchip vchip-entertainment" href="/entertainment/"><span class="vchip-emoji">🎬</span><span class="vchip-name">Entertainment</span><span class="vchip-tag">Movies, series, anime and articles</span></a>
    <a class="vchip vchip-entertainment" href="/movies/"><span class="vchip-emoji">🎥</span><span class="vchip-name">Movies</span><span class="vchip-tag">Trailers and the movie catalogue</span></a>
    <a class="vchip vchip-make-money" href="/make-money/"><span class="vchip-emoji">💰</span><span class="vchip-name">Make Money</span><span class="vchip-tag">Verified writing markets and honest guides</span></a>
    <a class="vchip vchip-tech" href="/tech/"><span class="vchip-emoji">🤖</span><span class="vchip-name">Tech &amp; AI</span><span class="vchip-tag">Practical tools and tutorials</span></a>
  </div>
</div></section>
</main>'''


def build():
    page = ROOT / 'sports' / 'index.html'
    raw = page.read_text(encoding='utf-8')
    i = raw.find('<main')
    j = raw.find('</main>')
    if i < 0 or j < 0:
        raise SystemExit('could not find main in sports/index.html')
    head, tail = raw[:i], raw[j + len('</main>'):]
    head = re.sub(
        r'<link rel="preload" as="image" href="[^"]*" fetchpriority="high">',
        '<link rel="preload" as="image" href="/assets/img/sports/hero-landing.jpg" fetchpriority="high">',
        head,
        count=1,
    )
    if 'hero-landing.jpg' not in head:
        head = head.replace(
            '</head>',
            '<link rel="preload" as="image" href="/assets/img/sports/hero-landing.jpg" fetchpriority="high"></head>',
            1,
        )
    # Tighten the sports hub title/description slightly — still honest, still the same URL.
    head = re.sub(
        r'<title>.*?</title>',
        '<title>BRYME Sports — Football Covered Properly | BRYME</title>',
        head,
        count=1,
        flags=re.S,
    )
    desc = 'Football covered properly: Premier League results and previews, Champions League, La Liga, Serie A, Bundesliga and Ligue 1. Sourced scores only.'
    head = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{esc(desc)}"', head, count=1)
    head = re.sub(r'<meta property="og:title" content="[^"]*"', '<meta property="og:title" content="BRYME Sports — Football Covered Properly | BRYME"', head, count=1)
    head = re.sub(r'<meta property="og:description" content="[^"]*"', f'<meta property="og:description" content="{esc(desc)}"', head, count=1)
    head = re.sub(r'<meta name="twitter:title" content="[^"]*"', '<meta name="twitter:title" content="BRYME Sports — Football Covered Properly | BRYME"', head, count=1)
    head = re.sub(r'<meta name="twitter:description" content="[^"]*"', f'<meta name="twitter:description" content="{esc(desc)}"', head, count=1)
    out = head + MAIN + tail
    page.write_text(out, encoding='utf-8')
    print('sports hub rebuilt', len(out), 'scorecards', out.count('sp-scorecard'))


if __name__ == '__main__':
    build()

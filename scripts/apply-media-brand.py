#!/usr/bin/env python3
"""Apply the BRYME Media v3 shell without changing archived editorial bodies.

v3 ("Watch Next") upgrade:
  * new header / mobile navigation / footer (cinematic identity, section accents);
  * every page loads assets/media-v3.css + assets/media-v3.js instead of media-v2.css;
  * the homepage is rebuilt as the discovery front door (Watch Next rails,
    football explainers, the desks);
  * link/image/tracking hygiene from v2 is kept unchanged.

The script is idempotent: running it twice must not change a single byte
(CI enforces this with `git diff --exit-code`)."""
from pathlib import Path
import html
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://bryme-media.onrender.com"
MEDIA_DIRS = {
    "anime", "article", "articles", "author", "channels", "entertainment",
    "genre", "genres", "legacy", "movie", "movies", "now", "search",
    "series", "sports", "topic", "topics", "trailers", "trending", "watch-next",
    "year", "years",
}
BRAND = 'BRY<b>ME</b> <span class="bm-tag">MEDIA</span>'
HEADER = ('<a class="skip-link" href="#main">Skip to content</a>'
          '<header class="top media-top v3-top"><div class="shell">'
          f'<a class="brand" href="/" aria-label="BRYME Media home">{BRAND}</a>'
          '<nav class="topnav" aria-label="Primary">'
          '<a data-sec="sports" href="/sports/">Sports</a>'
          '<a data-sec="watch-next" href="/watch-next/">Watch Next</a>'
          '<a data-sec="movies" href="/movies/">Movies</a>'
          '<a data-sec="series" href="/series/">Series</a>'
          '<a data-sec="anime" href="/anime/">Anime</a>'
          '<a data-sec="read" href="/articles/">Read</a>'
          '<a data-sec="about" href="/about/">About</a>'
          '</nav><div class="top-tools"><a class="header-search" href="/search/">Search</a></div>'
          '</div></header>')
MOBILE = ('<nav class="mobile-nav media-bottom v3-bottom" aria-label="Primary mobile">'
          '<a data-sec="home" href="/"><span class="mn-ico">⌂</span>Home</a>'
          '<a data-sec="sports" href="/sports/"><span class="mn-ico">◆</span>Sports</a>'
          '<a data-sec="watch-next" href="/watch-next/"><span class="mn-ico">▶</span>Watch</a>'
          '<a data-sec="movies" href="/movies/"><span class="mn-ico">▣</span>Movies</a>'
          '<a data-sec="series" href="/series/"><span class="mn-ico">◇</span>Series</a>'
          '<a data-sec="anime" href="/anime/"><span class="mn-ico">✦</span>Anime</a>'
          '</nav>')
FOOTER = ('<footer class="footer v3-footer"><div class="shell"><div class="footer-grid">'
          f'<div class="footer-brand"><a class="brand" href="/">{BRAND}</a>'
          '<p>Independent sports and entertainment pages, maintained outside BRYME\'s '
          'work-and-opportunities publication — now being rebuilt around recommendations, '
          'explainers and genuinely useful title pages.</p></div>'
          '<div class="footer-col"><h4>Watch</h4>'
          '<a href="/watch-next/">Watch Next lists</a>'
          '<a href="/entertainment/">Entertainment hub</a>'
          '<a href="/movies/">Films</a><a href="/series/">Series</a><a href="/anime/">Anime</a></div>'
          '<div class="footer-col"><h4>Read &amp; explore</h4>'
          '<a href="/articles/">Original articles</a>'
          '<a href="/sports/explainers/">Football explainers</a>'
          '<a href="/sports/">Sports desk</a>'
          '<a href="/author/ibrahim-sodiq/">Author</a>'
          '<a href="/search/">Search the archive</a></div>'
          '<div class="footer-col"><h4>Trust</h4>'
          '<a href="/about/">About</a><a href="/editorial-policy/">Editorial policy</a>'
          '<a href="/privacy/">Privacy</a><a href="/terms/">Terms</a>'
          '<a href="/contact/">Contact</a></div>'
          '</div><p class="footer-note">Staging preview of the BRYME Media rebuild — every page is '
          'deliberately noindexed and the preview is not submitted to search. Archived sports data '
          'must not be treated as current. Advertising and analytics are disabled.</p>'
          '<small>© 2026 BRYME Media · QA preview for the Sports &amp; Entertainment rebuild.</small>'
          '</div></footer>')


def route_for(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html": return "/"
    if rel.endswith("/index.html"): return "/" + rel[:-10]
    return "/" + rel


def noindex(text: str) -> str:
    tag = '<meta name="robots" content="noindex,follow">'
    if re.search(r'<meta\b[^>]*name=["\']robots["\'][^>]*>', text, re.I):
        return re.sub(r'<meta\b[^>]*name=["\']robots["\'][^>]*>', tag, text, count=1, flags=re.I)
    return re.sub(r'(<head\b[^>]*>)', r'\1' + tag, text, count=1, flags=re.I)


def patch(path: Path) -> bool:
    route = route_for(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    before = text
    text = re.sub(r'<script\b[^>]*(?:analytics|n6wxm|profitableratecpm|highperformanceformat)[^>]*>.*?</script>', '', text, flags=re.I | re.S)
    text = re.sub(r'(?:<a\b[^>]*class=["\']skip-link["\'][^>]*>.*?</a>)?<header\b[^>]*class=["\'][^"\']*\btop\b[^"\']*["\'][^>]*>.*?</header>', HEADER, text, count=1, flags=re.I | re.S)
    if '<header class="top media-top v3-top">' not in text:
        text = re.sub(r'(<body\b[^>]*>)', r'\1' + HEADER, text, count=1, flags=re.I)
    text = re.sub(r'<nav\b[^>]*class=["\'][^"\']*\bmobile-nav\b[^"\']*["\'][^>]*>.*?</nav>', MOBILE, text, count=1, flags=re.I | re.S)
    if 'class="mobile-nav media-bottom v3-bottom"' not in text:
        text = re.sub(r'(</main>)', r'\1' + MOBILE, text, count=1, flags=re.I)
    text = re.sub(r'<footer\b[^>]*class=["\'][^"\']*\bfooter\b[^"\']*["\'][^>]*>.*?</footer>', FOOTER, text, count=1, flags=re.I | re.S)
    if '<footer class="footer v3-footer">' not in text:
        text = text.replace('</body>', FOOTER + '</body>', 1)
    text = re.sub(r'<main(?![^>]*\bid=)([^>]*)>', r'<main id="main"\1>', text, count=1, flags=re.I)
    if '<main' not in text:
        text = re.sub(r'(<body\b[^>]*>)', r'\1<main id="main">', text, count=1, flags=re.I).replace('</body>', '</main></body>', 1)
    elif not re.search(r'\bid=["\']main["\']', text, re.I):
        text = re.sub(r'(<main\b)', r'<span id="main" tabindex="-1"></span>\1', text, count=1, flags=re.I)
    text = noindex(text)
    # v3 theme swap: retire media-v2.css everywhere, make sure the v3 pair is present exactly once.
    text = text.replace('href="/assets/media-v2.css"', 'href="/assets/media-v3.css"')
    text = text.replace("href='/assets/media-v2.css'", "href='/assets/media-v3.css'")
    if '/assets/media-v3.css' not in text:
        text = text.replace('</head>', '<link rel="stylesheet" href="/assets/media-v3.css"></head>', 1)
    if '/assets/media-v3.js' not in text:
        text = text.replace('</head>', '<script src="/assets/media-v3.js" defer></script></head>', 1)
    # The migration target is deliberately noindex until its final host is active.
    text = re.sub(r'https://bryme\.onrender\.com(?=[/"\'])', BASE, text)
    # Cross-publication links must remain explicit rather than becoming broken local paths.
    text = re.sub(r'href=["\']/jobs/[^"\']*["\']', 'href="https://bryme.onrender.com/jobs/"', text)
    text = re.sub(r'href=["\']/make-money/[^"\']*["\']', 'href="https://bryme.onrender.com/opportunities/"', text)
    text = re.sub(r'href=["\']/tech/[^"\']*["\']', 'href="https://bryme.onrender.com/guides/"', text)
    if text != before:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def page(title: str, description: str, route: str, heading: str, body: str) -> str:
    return f'''<!doctype html><html lang="en-NG"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><title>{html.escape(title)} | BRYME Media</title><meta name="description" content="{html.escape(description)}"><link rel="canonical" href="{BASE}{route}"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/bryme-v2.css"><link rel="stylesheet" href="/assets/media-v3.css"><script src="/assets/media-v3.js" defer></script></head><body>{HEADER}<main id="main"><div class="wrap"><nav class="breadcrumb"><a href="/">Home</a> / {html.escape(heading)}</nav><section class="page-hero"><p class="kicker"><span class="kicker-dot"></span>BRYME Media</p><h1>{html.escape(heading)}</h1><div class="prose">{body}</div></section></div></main>{MOBILE}{FOOTER}</body></html>'''


def rail_card(href: str, art: str, title: str, blurb: str, meta: str) -> str:
    return (f'<a class="card" href="{href}"><span class="card-art" style="background-image:url(\'{art}\')">'
            '<span class="card-play" aria-hidden="true">▶</span></span>'
            f'<span class="card-body"><h3>{html.escape(title)}</h3><p>{html.escape(blurb)}</p>'
            f'<span class="card-meta">{html.escape(meta)}</span></span></a>')


def write_pages() -> None:
    yt = lambda vid: f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg'
    watch_cards = "".join([
        rail_card("/watch-next/shows-like-alice-in-borderland/", yt("49_44FFKZ1M"),
                  "Shows Like Alice in Borderland",
                  "Five survival dramas — and exactly why each one fits.", "5 picks · Watch Next"),
        rail_card("/watch-next/shows-like-squid-game/", yt("oqxAJKy0ii4"),
                  "Shows Like Squid Game",
                  "Pressure-cooker dramas where the real game is the group.", "5 picks · Watch Next"),
        rail_card("/watch-next/movies-like-dune-part-two/", yt("PAV9YN5TEVg"),
                  "Movies Like Dune: Part Two",
                  "For the scale, the patience and the sound.", "5 picks · Watch Next"),
        rail_card("/watch-next/anime-like-solo-leveling/", yt("YvGSK8mIlt8"),
                  "Anime Like Solo Leveling",
                  "The leveling, the escalation, the power fantasy done right.", "5 picks · Watch Next"),
    ])
    explainer_cards = "".join([
        rail_card("/sports/explainers/what-does-offside-mean/", "", "What does offside mean?",
                  "The three-part test, in plain English.", "Football laws"),
        rail_card("/sports/explainers/how-does-var-work/", "", "How does VAR actually work?",
                  "The four categories — and what VAR cannot touch.", "Football technology"),
        rail_card("/sports/explainers/what-is-xg/", "", "What is xG?",
                  "Chance quality, explained without the maths degree.", "Football numbers"),
        rail_card("/sports/explainers/what-is-an-aggregate-score/", "", "Aggregate scores, explained",
                  "How two-legged ties really add up.", "Knockout football"),
    ]).replace('style="background-image:url(\'\')"', 'style="background:linear-gradient(135deg,#14352c,#0e1526)"')
    home = ('<!doctype html><html lang="en-NG"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="robots" content="noindex,follow">'
            '<title>BRYME Media | Sports explained, screen culture, what to watch next</title>'
            '<meta name="description" content="BRYME Media is the independent home of BRYME sports and entertainment: football explainers, recommendation lists and upgraded title pages — previewed here first.">'
            f'<link rel="canonical" href="{BASE}/">'
            '<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">'
            '<link rel="stylesheet" href="/assets/bryme-v2.css">'
            '<link rel="stylesheet" href="/assets/media-v3.css">'
            '<script src="/assets/media-v3.js" defer></script></head>'
            f'<body data-nav="home">{HEADER}<main id="main" class="v3-main">'
            '<section class="v3-hero"><div class="wrap">'
            '<p class="v3-kicker"><i></i>Independent media · Rebuild preview</p>'
            '<h1 class="v3-display">Sports stories. Screen culture. <em>What to watch next.</em></h1>'
            '<p class="v3-lede">BRYME Media is the separate home for BRYME\'s sports and entertainment work — '
            'rebuilt around three questions people actually ask: what does this football rule mean, what should I watch after this, and what is worth my evening.</p>'
            '<div class="v3-actions"><a class="v3-btn" href="/watch-next/">Browse Watch Next</a>'
            '<a class="v3-btn ghost" href="/sports/explainers/">Football explainers</a>'
            '<a class="v3-btn ghost" href="/entertainment/">Entertainment hub</a></div>'
            '</div></section>'
            '<section class="v3-sec"><div class="wrap"><div class="v3-sec-head"><h2>Watch Next — start here</h2>'
            '<a class="v3-more" href="/watch-next/">All lists →</a></div>'
            f'<div class="v3-rail">{watch_cards}</div></div></section>'
            '<section class="v3-sec" style="padding-top:0"><div class="wrap"><div class="v3-sec-head"><h2>Football, explained</h2>'
            '<a class="v3-more" href="/sports/explainers/">All explainers →</a></div>'
            f'<div class="v3-rail">{explainer_cards}</div>'
            '<div class="v3-note" style="margin-top:18px"><b>House rule:</b> archived sports pages carry old results and must never be read as current tables, fixtures or advice.</div>'
            '</div></section>'
            '<section class="v3-sec" style="padding-top:0;border-top:1px solid var(--bm-line)"><div class="wrap">'
            '<div class="v3-sec-head"><h2>The desks</h2><span class="v3-count">preserved archive · being rebuilt desk by desk</span></div>'
            '<div class="v3-grid">'
            + rail_card("/entertainment/", "", "Entertainment", "Recommendation lists and title pages with trailers and real context.", "Watch Next")
            + rail_card("/sports/", "", "Sports", "The preserved football archive — match pages, clubs and explainers.", "Sports desk")
            + rail_card("/movies/", "", "Films", "The full film catalogue from the archive.", "Movies")
            + rail_card("/articles/", "", "Read", "Original entertainment writing and guides.", "Articles")
            + '</div>'
            '<div class="v3-callout" style="margin-top:28px"><h3>What this preview is</h3>'
            '<p>The staging environment for the BRYME Media rebuild: a reviewed sample of the new architecture on top of '
            'the preserved sports and entertainment archive. Every page is deliberately noindexed while structures are tested; '
            'nothing here is final until it is approved for migration to the live publication.</p></div>'
            '</div></section></main>' + MOBILE + FOOTER + '</body></html>')
    home = home.replace('style="background-image:url(\'\')"', 'style="background:linear-gradient(135deg,#14352c,#0e1526)"')
    (ROOT / 'index.html').write_text(home, encoding='utf-8')
    pages = {
        'about': ('About', 'About the separate BRYME sports and entertainment archive.', '<p>BRYME Media is the independent home for sports and entertainment pages moved out of BRYME’s work publication. It is maintained separately so each publication can have a clear purpose.</p><h2>Current status</h2><p>This repository is a migration archive in active rebuild. Pages are excluded from Search until source rights, factual freshness, routing and the final domain are approved.</p>'),
        'contact': ('Contact', 'Contact BRYME Media about corrections and rights.', '<p>Use the project owner’s established BRYME contact channel for factual corrections, rights questions or removal requests. Include the exact page URL and the material concerned.</p>'),
        'privacy': ('Privacy', 'Privacy information for BRYME Media.', '<p>BRYME Media does not currently load advertising or analytics. Trailer thumbnails may be requested from YouTube; the privacy-enhanced embedded player is created only after an explicit play action.</p><h2>No accounts</h2><p>The archive does not collect account profiles, applications or payment information.</p>'),
        'terms': ('Terms', 'Terms for use of the BRYME Media archive.', '<p>Material is provided for information and commentary. Sports information may be archived and must not be relied on as a current score, fixture or table.</p><h2>Third-party material</h2><p>Names and trademarks belong to their owners. Embedded trailers and outbound sources remain governed by their respective services.</p>'),
        'disclaimer': ('Disclaimer', 'Important limitations of BRYME Media pages.', '<p>BRYME Media does not host films, streams or betting services. Trailer availability does not establish where a title is legally available in a particular country.</p><p>Archived sports pages are not current advice and are not betting recommendations.</p>'),
        'copyright': ('Copyright', 'Copyright and rights contact information.', '<p>Original BRYME writing is protected by copyright. Third-party names, marks, trailers and source material remain the property of their respective owners.</p><p>For a rights concern, provide the exact URL and enough information to identify the material.</p>'),
        'editorial-policy': ('Editorial policy', 'Editorial and source standards for BRYME Media.', '<p>Original commentary must be separated from factual claims. Material facts require visible provenance, and corrections should be recorded rather than silently hidden.</p><h2>Sports status</h2><p>Automated sports publication remains paused until source rights and a reliable verification process are approved.</p>'),
    }
    for slug, (heading, desc, body) in pages.items():
        target = ROOT / slug / 'index.html'; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page(heading, desc, f'/{slug}/', heading, body), encoding='utf-8')


if __name__ == '__main__':
    changed = 0
    for file in sorted(ROOT.rglob('*.html')):
        if '.git' not in file.parts and patch(file): changed += 1
    write_pages()
    print(f'v3 shell: patched {changed} archived HTML files and rebuilt the home + static pages')

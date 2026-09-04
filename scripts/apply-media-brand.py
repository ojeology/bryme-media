#!/usr/bin/env python3
"""Apply the BRYME Media shell without changing archived editorial bodies."""
from pathlib import Path
import html
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://bryme-media.onrender.com"
MEDIA_DIRS = {
    "anime", "article", "articles", "author", "channels", "entertainment",
    "genre", "genres", "legacy", "movie", "movies", "now", "search",
    "series", "sports", "topic", "topics", "trailers", "trending", "year", "years",
}
HEADER = '''<a class="skip-link" href="#main">Skip to content</a><header class="top media-top"><div class="shell"><a class="brand" href="/" aria-label="BRYME Media home">BRY<b>ME</b> <span>MEDIA</span></a><nav class="topnav" aria-label="Primary"><a href="/sports/">Sports</a><a href="/movies/">Movies</a><a href="/series/">Series</a><a href="/anime/">Anime</a><a href="/articles/">Read</a><a href="/about/">About</a></nav><div class="top-tools"><a class="header-search" href="/sports/">Sports</a></div></div></header>'''
MOBILE = '''<nav class="mobile-nav media-bottom" aria-label="Primary mobile"><a href="/"><span class="mn-ico">⌂</span>Home</a><a href="/sports/"><span class="mn-ico">◆</span>Sports</a><a href="/movies/"><span class="mn-ico">▶</span>Movies</a><a href="/series/"><span class="mn-ico">▣</span>Series</a><a href="/anime/"><span class="mn-ico">◇</span>Anime</a><a href="/articles/"><span class="mn-ico">✦</span>Read</a></nav>'''
FOOTER = '''<footer class="footer media-footer"><div class="shell"><div class="footer-grid"><div class="footer-brand"><a class="brand" href="/">BRY<b>ME</b> MEDIA</a><p>Independent sports and entertainment pages preserved outside BRYME's work-and-opportunities publication.</p></div><div class="footer-col"><h4>Explore</h4><a href="/sports/">Sports</a><a href="/movies/">Movies</a><a href="/series/">Series</a><a href="/anime/">Anime</a></div><div class="footer-col"><h4>Editorial</h4><a href="/articles/">Original articles</a><a href="/editorial-policy/">Editorial policy</a><a href="/author/ibrahim-sodiq/">Author</a></div><div class="footer-col"><h4>Trust</h4><a href="/about/">About</a><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a><a href="/contact/">Contact</a></div></div><p class="footer-note">Sports data is archived and must not be treated as current until its source and update process are approved.</p><small>© 2026 BRYME Media · Advertising and analytics are disabled.</small></div></footer>'''


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
    if '<header class="top media-top">' not in text:
        text = re.sub(r'(<body\b[^>]*>)', r'\1' + HEADER, text, count=1, flags=re.I)
    text = re.sub(r'<nav\b[^>]*class=["\'][^"\']*\bmobile-nav\b[^"\']*["\'][^>]*>.*?</nav>', MOBILE, text, count=1, flags=re.I | re.S)
    if 'class="mobile-nav media-bottom"' not in text:
        text = re.sub(r'(</main>)', r'\1' + MOBILE, text, count=1, flags=re.I)
    text = re.sub(r'<footer\b[^>]*class=["\'][^"\']*\bfooter\b[^"\']*["\'][^>]*>.*?</footer>', FOOTER, text, count=1, flags=re.I | re.S)
    if '<footer class="footer media-footer">' not in text:
        text = text.replace('</body>', FOOTER + '</body>', 1)
    text = re.sub(r'<main(?![^>]*\bid=)([^>]*)>', r'<main id="main"\1>', text, count=1, flags=re.I)
    if '<main' not in text:
        text = re.sub(r'(<body\b[^>]*>)', r'\1<main id="main">', text, count=1, flags=re.I).replace('</body>', '</main></body>', 1)
    elif not re.search(r'\bid=["\']main["\']', text, re.I):
        text = re.sub(r'(<main\b)', r'<span id="main" tabindex="-1"></span>\1', text, count=1, flags=re.I)
    text = noindex(text)
    if '/assets/media-v2.css' not in text:
        text = text.replace('</head>', '<link rel="stylesheet" href="/assets/media-v2.css"></head>', 1)
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
    return f'''<!doctype html><html lang="en-NG"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><title>{html.escape(title)} | BRYME Media</title><meta name="description" content="{html.escape(description)}"><link rel="canonical" href="{BASE}{route}"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/bryme-v2.css"><link rel="stylesheet" href="/assets/media-v2.css"></head><body>{HEADER}<main id="main"><div class="wrap"><nav class="breadcrumb"><a href="/">Home</a> / {html.escape(heading)}</nav><section class="page-hero"><p class="kicker"><span class="kicker-dot"></span>BRYME Media</p><h1>{html.escape(heading)}</h1><div class="prose">{body}</div></section></div></main>{MOBILE}{FOOTER}</body></html>'''


def write_pages() -> None:
    home = '''<!doctype html><html lang="en-NG"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><title>BRYME Media | Sports and entertainment archive</title><meta name="description" content="BRYME Media preserves BRYME sports, movie, series, anime and original entertainment pages during their move to an independent publication."><link rel="canonical" href="https://bryme-media.onrender.com/"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/bryme-v2.css"><link rel="stylesheet" href="/assets/media-v2.css"></head><body>''' + HEADER + '''<main id="main"><section class="media-hero"><div class="wrap"><p class="kicker"><span class="kicker-dot"></span>Independent media archive</p><h1>Sports stories. Screen culture. <em>One separate home.</em></h1><p>BRYME Media preserves the sports and entertainment work moved out of BRYME's jobs and opportunities publication. The archive remains outside Search until its data rights, freshness and final domain are approved.</p><div class="actions"><a class="btn" href="/sports/">Explore sports</a><a class="btn secondary" href="/articles/">Read original articles</a></div></div></section><section class="section"><div class="wrap"><div class="card-grid"><a class="path-card" href="/sports/"><span class="card-num">SPORTS</span><h3>Match pages and stories</h3><p>Preserved with visible archive warnings while the source process is rebuilt.</p></a><a class="path-card" href="/movies/"><span class="card-num">MOVIES</span><h3>Movie discovery</h3><p>Trailers, title notes and related original guides.</p></a><a class="path-card" href="/series/"><span class="card-num">SERIES</span><h3>Series discovery</h3><p>Series pages and editorial pathways.</p></a><a class="path-card" href="/anime/"><span class="card-num">ANIME</span><h3>Anime discovery</h3><p>Anime pages, trailers and comparisons.</p></a></div></div></section></main>''' + MOBILE + FOOTER + '''</body></html>'''
    (ROOT / 'index.html').write_text(home, encoding='utf-8')
    pages = {
        'about': ('About', 'About the separate BRYME sports and entertainment archive.', '<p>BRYME Media is the independent home for sports and entertainment pages moved out of BRYME’s work publication. It is maintained separately so each publication can have a clear purpose.</p><h2>Current status</h2><p>This repository is a migration archive. Pages are excluded from Search until source rights, factual freshness, routing and the final domain are approved.</p>'),
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
    print(f'branded {changed} archived HTML files and rebuilt migration pages')

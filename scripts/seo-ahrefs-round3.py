#!/usr/bin/env python3
"""Finish remaining Ahrefs items that are real and safe to touch."""
from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://bryme.onrender.com"


def set_meta_desc(html: str, new: str) -> str:
    new = new.replace('"', "&quot;")
    html = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{new}"', html, count=1)
    html = re.sub(r'<meta property="og:description" content="[^"]*"', f'<meta property="og:description" content="{new}"', html, count=1)
    html = re.sub(r'<meta name="twitter:description" content="[^"]*"', f'<meta name="twitter:description" content="{new}"', html, count=1)
    return html


def main():
    stats = {}

    # --- movies hub: chips to every canonical genre folder ---
    movies = ROOT / "movies" / "index.html"
    mt = movies.read_text(encoding="utf-8")
    chips = (
        '<nav class="genre-chips" aria-label="Movie genres">'
        '<a href="/movies/action/">Action</a>'
        '<a href="/movies/comedy/">Comedy</a>'
        '<a href="/movies/crime/">Crime</a>'
        '<a href="/movies/drama/">Drama</a>'
        '<a href="/movies/fantasy/">Fantasy</a>'
        '<a href="/movies/horror/">Horror</a>'
        '<a href="/movies/romance/">Romance</a>'
        '<a href="/movies/sci-fi/">Sci-Fi</a>'
        '<a href="/movies/superhero/">Superhero</a>'
        '<a href="/movies/thriller/">Thriller</a>'
        '<a href="/movies/war/">War</a>'
        '<a href="/movies/western/">Western</a>'
        '<a href="/movies/animation/">Animation</a>'
        '<a href="/movies/chinese/">Chinese</a>'
        '<a href="/movies/french/">French</a>'
        '<a href="/movies/german/">German</a>'
        '<a href="/movies/indian/">Indian</a>'
        '<a href="/movies/korean/">Korean</a>'
        '<a href="/movies/nigerian/">Nigerian</a>'
        '<a href="/genre/musical/">Musical</a>'
        '<a href="/anime/">Anime</a>'
        "</nav>"
    )
    if 'aria-label="Movie genres"' not in mt:
        mt = re.sub(r'<nav class="genre-chips"[^>]*>.*?</nav>', chips, mt, count=1, flags=re.S)
        if 'aria-label="Movie genres"' not in mt:
            mt = mt.replace("</main>", chips + "</main>", 1)
        movies.write_text(mt, encoding="utf-8")
        stats["movies_genre_chips"] = True
    else:
        stats["movies_genre_chips"] = "already"

    # --- articles hub: link the two orphan collections ---
    art = ROOT / "articles" / "index.html"
    at = art.read_text(encoding="utf-8")
    block = (
        '<section class="section"><div class="section-head"><h2>Guides by type</h2></div>'
        '<div class="vcat-grid">'
        '<a class="vcat" href="/articles/movie-guides/"><b>Movie guides</b>'
        "<span>Editorial movie explainers and watch-next lists.</span></a>"
        '<a class="vcat" href="/articles/tv-series-opinion/"><b>TV series opinion</b>'
        "<span>First-person series pieces, not a recap mill.</span></a>"
        '<a class="vcat" href="/article/interstellar-ending-explained/"><b>Interstellar ending</b>'
        "<span>The tesseract, Murph, and why Cooper leaves.</span></a>"
        "</div></section>"
    )
    if "/articles/movie-guides/" not in at:
        at = at.replace("</main>", block + "</main>", 1)
        art.write_text(at, encoding="utf-8")
        stats["articles_hub_links"] = True
    else:
        stats["articles_hub_links"] = "already"

    for rel, desc in (
        ("articles/movie-guides/index.html", "Original BRYME movie guides: endings, watch-next lists and how we pick titles."),
        ("articles/tv-series-opinion/index.html", "First-person BRYME pieces on TV series — opinions, not episode recaps."),
        ("topics/index.html", "Focused routes through movies, series and anime already in the BRYME catalogue."),
        ("now/index.html", "Five BRYME pages worth sending someone — movies, football, money and tech."),
    ):
        p = ROOT / rel
        if not p.exists():
            continue
        html = p.read_text(encoding="utf-8")
        html = set_meta_desc(html, desc)
        p.write_text(html, encoding="utf-8")
    stats["collection_desc"] = 4

    # --- homepage: /now/ ---
    home = ROOT / "index.html"
    ht = home.read_text(encoding="utf-8")
    if "/now/" not in ht:
        ht = ht.replace(
            '<a href="/articles/">All BRYME stories</a>',
            '<a href="/now/">Five pages worth sending</a>\n      <a href="/articles/">Editorial stories</a>',
        )
        # entertainment panel may not have that string
        if "/now/" not in ht:
            ht = ht.replace(
                '<a href="/entertainment/">🎬 Entertainment</a>',
                '<a href="/entertainment/">🎬 Entertainment</a>',
                1,
            )
            # add into tech panel leftover
            ht = ht.replace(
                '<a href="/tech/where-to-host-website-for-free/">Where to host a website for free</a>',
                '<a href="/tech/where-to-host-website-for-free/">Where to host a website for free</a>\n      <a href="/now/">Five pages worth sending</a>',
                1,
            )
        home.write_text(ht, encoding="utf-8")
        stats["home_now"] = "/now/" in home.read_text(encoding="utf-8")

    # --- make-money landing cards ---
    mm = ROOT / "make-money" / "index.html"
    mmt = mm.read_text(encoding="utf-8")
    extra = (
        '      <a class="sp-comp-card" href="/make-money/content-creation/" style="--card-img:url(\'/assets/img/money/hero-writing.jpg\')">\n'
        "        <em>Create</em><b>Content creation</b><span>Writing markets and the process. No invented YouTube rates.</span>\n"
        "      </a>\n"
        '      <a class="sp-comp-card" href="/make-money/income-skills/" style="--card-img:url(\'/assets/img/money/hero-beginner.jpg\')">\n'
        "        <em>Skills</em><b>Income skills</b><span>Writing, coding and the beginner guide. No fake hourly rates.</span>\n"
        "      </a>\n"
        '      <a class="sp-comp-card" href="/make-money/ai-assisted-work/" style="--card-img:url(\'/assets/img/tech/hero-privacy.jpg\')">\n'
        "        <em>AI</em><b>AI-assisted work</b><span>Many paying markets here ban AI. Read that before you paste a draft.</span>\n"
        "      </a>\n"
    )
    if "/make-money/content-creation/" not in mmt:
        mmt = mmt.replace(
            '<a class="sp-comp-card" href="/make-money/platform-reviews/"',
            extra + '      <a class="sp-comp-card" href="/make-money/platform-reviews/"',
            1,
        )
        mm.write_text(mmt, encoding="utf-8")
        stats["mm_hub_cards"] = True

    # --- tech + sports short descriptions ---
    DESCS = {
        "tech/ai-assistants/index.html": "ChatGPT, Claude, Gemini, Arena and DeepSeek — what each official page actually says, plus the privacy settings.",
        "tech/ai-image-video/index.html": "Pixlr, Photopea and Affinity: sourced image tools. Not a Midjourney clone list.",
        "tech/ai-tutorials/index.html": "Start with AI privacy settings and coding on a phone. No prompt-pack shop.",
        "tech/android-apps/index.html": "Termux, Lyra, Bitwarden and Signal — Android tools with a sourced BRYME page.",
        "tech/beginner-coding/index.html": "Learning to code from zero on an Android phone with Termux: what broke and what fixed it.",
        "tech/cybersecurity/index.html": "Bitwarden’s free vault and what ChatGPT, Claude and Gemini do with your chats.",
        "tech/developer-tools/index.html": "Free hosting docs, Render deploy failures from this site, and Termux on a phone.",
        "tech/hosting/index.html": "Where to host a website for free — GitHub Pages, Cloudflare, Render, Vercel, Netlify.",
        "tech/internet-tools/index.html": "Browser tools we sourced: Photopea, Polotno and Bitwarden. Not a utilities dump.",
        "sports/clubs/index.html": "Club histories, identities and rivalries. No invented transfers or squad lists.",
        "sports/history/index.html": "Eras and turning points in football, written from confirmed records.",
        "sports/international/index.html": "World Cup, continental championships and national-team football on BRYME.",
        "sports/players/index.html": "Player careers and the Ballon d’Or race — assessment labelled as ours.",
        "sports/records/index.html": "Titles, streaks and Champions League records, with the awkward ones included.",
    }
    n = 0
    for rel, desc in DESCS.items():
        p = ROOT / rel
        if not p.exists():
            continue
        p.write_text(set_meta_desc(p.read_text(encoding="utf-8"), desc), encoding="utf-8")
        n += 1
    stats["hub_descs"] = n

    # --- series short generic descriptions ---
    series_n = 0
    for p in (ROOT / "series").glob("*/index.html"):
        if p.parent.name.isdigit():
            continue
        html = p.read_text(encoding="utf-8")
        if "noindex" in html[:4000]:
            continue
        dm = re.search(r'<meta name="description" content="([^"]*)"', html)
        if not dm or len(dm.group(1)) >= 70:
            continue
        if "synopsis, official trailer" not in dm.group(1) and "watch the official trailer" not in dm.group(1) and len(dm.group(1)) >= 50:
            # already specific-ish but short — expand from title/year
            pass
        h1 = re.search(r"<h1>([^<]+)</h1>", html)
        year = re.search(r"Year</div><div class=\"nm-detail-value\">([^<]+)", html)
        genre = re.search(r"Genres</div><div class=\"nm-detail-value\">([^<]+)", html)
        title = unescape(h1.group(1)).strip() if h1 else p.parent.name.replace("-", " ").title()
        y = year.group(1).strip() if year else ""
        g = genre.group(1).strip().split(",")[0] if genre else "series"
        if y:
            new = f"{title} ({y}) — {g} series. Official trailer, cast basics and related titles on BRYME."
        else:
            new = f"{title} — {g} series. Official trailer and the basics on BRYME."
        if len(new) > 155:
            new = new[:155].rsplit(" ", 1)[0] + "…"
        p.write_text(set_meta_desc(html, new), encoding="utf-8")
        series_n += 1
    stats["series_descs"] = series_n

    # --- visible lead on thin year archives ---
    year_leads = 0
    for folder in (ROOT / "year", ROOT / "movies", ROOT / "series", ROOT / "anime"):
        if not folder.exists():
            continue
        for p in folder.glob("*/index.html"):
            if not p.parent.name.isdigit():
                continue
            html = p.read_text(encoding="utf-8")
            if "noindex" in html[:4000] or 'class="year-lead"' in html:
                continue
            titles = re.findall(r"<h3>([^<]+)</h3>", html)
            if not titles:
                continue
            listed = ", ".join(titles[:6])
            more = f" and {len(titles) - 6} more" if len(titles) > 6 else ""
            lead = f'<p class="lead year-lead">On this page: {listed}{more}.</p>'
            html = html.replace("</h1></section>", f"</h1>{lead}</section>", 1)
            if 'class="year-lead"' in html:
                p.write_text(html, encoding="utf-8")
                year_leads += 1
    stats["year_leads"] = year_leads

    # --- sports hub crest alts (empty → team name) ---
    sp = ROOT / "sports" / "index.html"
    st = sp.read_text(encoding="utf-8")

    def crest_alt(m):
        block = m.group(0)
        if 'alt=""' not in block:
            return block
        name = re.search(r"<span>([^<]+)</span>", block)
        if not name:
            return block
        return block.replace('alt=""', f'alt="{name.group(1)} crest"', 1)

    st2 = re.sub(r'<div class="sp-sc-club">.*?</div>', crest_alt, st, flags=re.S)
    if st2 != st:
        sp.write_text(st2, encoding="utf-8")
        stats["sports_crest_alts"] = st2.count(" crest")
    else:
        stats["sports_crest_alts"] = 0

    # --- sports ItemList of today's preview URLs (no fake scores) ---
    st = Path(ROOT / "sports" / "index.html").read_text(encoding="utf-8")
    if '"@type":"ItemList"' not in st:
        hrefs = re.findall(r'href="(/sports/[^"]+/matches/[^"]+/)"', st)
        # unique, keep order, today previews first
        seen = []
        for h in hrefs:
            if h not in seen:
                seen.append(h)
        items = []
        for i, h in enumerate(seen[:12], 1):
            items.append(
                {"@type": "ListItem", "position": i, "url": SITE + h}
            )
        lst = {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": "Sunday 23 August 2026 match pages on BRYME",
            "itemListElement": items,
        }
        blob = json.dumps(lst, ensure_ascii=False, separators=(",", ":"))
        st = st.replace("</script>", "," + blob + "]", 1)
        # that might break if first script isn't an array. Safer insert new script.
        # revert naive replace — do properly
        st = Path(ROOT / "sports" / "index.html").read_text(encoding="utf-8")
        st = st.replace(
            "</head>",
            f'<script type="application/ld+json">{blob}</script></head>',
            1,
        )
        Path(ROOT / "sports" / "index.html").write_text(st, encoding="utf-8")
        stats["sports_itemlist"] = len(items)

    # --- IndexNow: support --urls-file / git names ---
    idx = ROOT / "scripts" / "indexnow.js"
    js = idx.read_text(encoding="utf-8")
    if "--paths" not in js:
        extra = r'''
if (get('--paths')) {
  urls = get('--paths').split(',').map(s => s.trim()).filter(Boolean)
    .map(s => s.startsWith('http') ? s : base + (s.startsWith('/') ? s : '/' + s));
} else if (get('--url')) {
'''
        js = js.replace("if (get('--url')) {\n  urls = [get('--url')];", extra + "  urls = [get('--url')];")
        idx.write_text(js, encoding="utf-8")
        stats["indexnow_paths"] = True

    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()

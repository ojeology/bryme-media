#!/usr/bin/env python3
"""Ahrefs technical SEO cleanup — template-level, no fabricated facts.

1. Drop VideoObject blocks that lack uploadDate (Google required property).
2. Rebuild sitemap.xml from on-disk indexable, self-canonical pages.
3. Complete missing og:url / og:image / Twitter cards on indexable pages.
4. Shorten titles over 70 characters without dropping the film/series name.
5. One H1 on the entertainment carousel.
6. Repair broken /movies/{genre}/ crumbs to real destinations.
"""
from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://bryme.onrender.com"
CARD = SITE + "/assets/bryme-card.png"

GENRE_FIX = {
    "/movies/anime/": "/anime/",
    "/movies/musical/": "/genre/musical/",
    "/movies/music/": "/genre/musical/",
    "/movies/mystery/": "/movies/thriller/",
    "/movies/adventure/": "/movies/action/",
    "/movies/sports/": "/movies/",
    "/movies/shonen/": "/anime/",
}


def page_url(p: Path) -> str:
    rel = "/" + str(p.parent.relative_to(ROOT)).replace("\\", "/")
    if rel.endswith("/."):
        rel = ""
    if rel == "/.":
        rel = ""
    return (rel if rel != "/" else "") + "/"


def walk_html():
    for p in ROOT.rglob("index.html"):
        if any(x in p.parts for x in (".git", "reports", "node_modules", "__pycache__")):
            continue
        yield p


def strip_bad_video_object(html: str) -> tuple[str, int]:
    n = 0

    def fix(m):
        nonlocal n
        raw = m.group(1)
        try:
            data = json.loads(raw)
        except Exception:
            return m.group(0)
        items = data if isinstance(data, list) else [data]
        kept = []
        for it in items:
            if isinstance(it, dict) and it.get("@type") == "VideoObject" and not it.get("uploadDate"):
                n += 1
                continue
            kept.append(it)
        if not kept:
            return ""
        out = kept if isinstance(data, list) else kept[0]
        return '<script type="application/ld+json">' + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "</script>"

    html2 = re.sub(r'<script type="application/ld\+json">(.*?)</script>', fix, html, flags=re.S)
    return html2, n


def shorten_title(title: str) -> str:
    t = unescape(title)
    t = t.replace("&amp;", "&")
    if len(t) <= 70:
        return title
    t = t.replace(" | Cast, Trailer, Episodes & Where to Watch | BRYME", " | Cast & Trailer | BRYME")
    t = t.replace(" | Cast, Trailer & Where to Watch | BRYME", " | Cast & Trailer | BRYME")
    t = t.replace(" | Cast, Trailer, Story & Where to Watch | BRYME", " | Cast & Trailer | BRYME")
    if len(t) > 70:
        t = re.sub(r"\s*\|\s*Cast & Trailer\s*\|\s*BRYME$", " | BRYME", t)
    if len(t) > 70:
        # keep name + year + brand
        m = re.match(r"^(.*?\(\d{4}\))", t)
        if m:
            t = m.group(1) + " | BRYME"
    return t


def ensure_social(html: str, url: str) -> str:
    head_end = html.find("</head>")
    if head_end < 0:
        return html
    head = html[:head_end]
    title_m = re.search(r"<title>(.*?)</title>", head, re.S)
    title = re.sub(r"\s+", " ", unescape(title_m.group(1))).strip() if title_m else "BRYME"
    desc_m = re.search(r'<meta name="description" content="([^"]*)"', head)
    desc = desc_m.group(1) if desc_m else title
    img_m = re.search(r'<meta property="og:image" content="([^"]*)"', head)
    img = img_m.group(1) if img_m else CARD
    if "property=\"og:url\"" not in head and ">meta property=\"og:url\"" not in head:
        head += f'<meta property="og:url" content="{SITE}{url}">'
    if "property=\"og:image\"" not in head:
        head += f'<meta property="og:image" content="{img}">'
    if "twitter:card" not in head:
        head += (
            '<meta name="twitter:card" content="summary_large_image">'
            f'<meta name="twitter:title" content="{title}">'
            f'<meta name="twitter:description" content="{desc}">'
            f'<meta name="twitter:image" content="{img}">'
        )
    # fix double-escaped og title
    head = head.replace("&amp;amp;", "&amp;")
    return head + html[head_end:]


def rebuild_sitemap():
    urls = []
    for p in walk_html():
        text = p.read_text(encoding="utf-8", errors="ignore")
        head = text[:5000]
        if "noindex" in head:
            continue
        url = page_url(p)
        can = re.search(r'rel="canonical" href="([^"]+)"', head)
        if can:
            dest = can.group(1).replace(SITE, "")
            if dest.rstrip("/") != url.rstrip("/") and dest.rstrip("/") + "/" != url:
                # non-canonical — keep out
                continue
        last = re.search(r"<lastmod>([^<]+)</lastmod>", text)  # rarely in html
        urls.append((url, None))
    # unique, stable order
    seen = set()
    ordered = []
    for u, lm in urls:
        key = SITE + (u if u.startswith("/") else "/" + u)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(key)
    ordered.sort()
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in ordered)
        + "</urlset>\n"
    )
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")
    return len(ordered)


def main():
    vo_removed = 0
    social_fixed = 0
    titles_fixed = 0
    crumbs_fixed = 0
    pages = 0

    for p in walk_html():
        html = p.read_text(encoding="utf-8")
        orig = html
        html, n = strip_bad_video_object(html)
        vo_removed += n
        url = page_url(p)
        indexable = "noindex" not in html[:4000]
        if indexable:
            before = html
            html = ensure_social(html, url)
            if html != before:
                social_fixed += 1
            tm = re.search(r"<title>(.*?)</title>", html, re.S)
            if tm:
                raw = tm.group(1)
                new = shorten_title(raw)
                if new != raw:
                    html = html.replace(f"<title>{raw}</title>", f"<title>{new}</title>", 1)
                    # keep og/twitter in sync when they used the long title
                    html = html.replace(f'content="{raw}"', f'content="{new}"')
                    titles_fixed += 1
        for bad, good in GENRE_FIX.items():
            if bad in html:
                html = html.replace(bad, good)
                crumbs_fixed += 1
        if html != orig:
            p.write_text(html, encoding="utf-8")
            pages += 1

    # Entertainment: one H1 — keep the first slide, demote the rest
    ent = ROOT / "entertainment" / "index.html"
    et = ent.read_text(encoding="utf-8")
    first = True

    def demote(m):
        nonlocal first
        if first:
            first = False
            return m.group(0)
        return m.group(0).replace("<h1>", "<h2>", 1).replace("</h1>", "</h2>", 1)

    et2 = re.sub(r"<h1>.*?</h1>", demote, et, flags=re.S)
    if et2 != et:
        ent.write_text(et2, encoding="utf-8")
        print("entertainment H1 demoted")

    sm = rebuild_sitemap()

    # _redirects for the broken genre paths
    redir = ROOT / "_redirects"
    existing = redir.read_text(encoding="utf-8") if redir.exists() else ""
    extra = ["# Broken genre crumbs → real catalogue destinations\n"]
    for bad, good in GENRE_FIX.items():
        line = f"{bad}  {good}  301\n"
        if line not in existing:
            extra.append(line)
    if len(extra) > 1:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        redir.write_text(existing + "".join(extra), encoding="utf-8")

    # movies hub: link real genre directories that were orphaned
    movies = ROOT / "movies" / "index.html"
    if movies.exists():
        mt = movies.read_text(encoding="utf-8")
        if "/genre/musical/" not in mt:
            block = (
                '<nav class="genre-chips" aria-label="More genres">'
                '<a href="/genre/musical/">Musical</a>'
                '<a href="/genre/korean/">Korean</a>'
                '<a href="/genre/indian/">Indian</a>'
                '<a href="/genre/nigerian/">Nigerian</a>'
                '<a href="/genre/animation/">Animation</a>'
                '<a href="/anime/">Anime</a>'
                "</nav>"
            )
            mt = mt.replace("</main>", block + "</main>", 1)
            movies.write_text(mt, encoding="utf-8")
            print("movies hub genre links added")

    print(
        json.dumps(
            {
                "pages_rewritten": pages,
                "videoobject_removed": vo_removed,
                "social_fixed": social_fixed,
                "titles_shortened": titles_fixed,
                "genre_crumb_rewrites": crumbs_fixed,
                "sitemap_urls": sm,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

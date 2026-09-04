#!/usr/bin/env python3
"""Restore /movie/<slug>/ copies of series and anime titles as noindex redirect stubs.

The build already writes these stubs (canonical + noindex + meta refresh). A later
layout pass turned them back into full title pages and they leaked into sitemap.xml.
Existing URLs are preserved; they now point at the canonical type URL.
"""
import html as H
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://bryme.onrender.com"

GENRE_DIRS = {
    "action", "adventure", "animation", "comedy", "crime", "drama", "family",
    "fantasy", "historical", "horror", "isekai", "mecha", "music", "mystery",
    "political", "psychological", "romance", "sci-fi", "shonen", "slice-of-life",
    "sports", "superhero", "supernatural", "survival", "thriller", "war",
}


def listing_name(d):
    return {n for n in os.listdir(os.path.join(ROOT, d))
            if os.path.isdir(os.path.join(ROOT, d, n))
            and n != "index.html"
            and not re.fullmatch(r"\d{4}", n)
            and n not in GENRE_DIRS}


def page_title(path):
    html = open(path, encoding="utf-8").read()
    m = re.search(r"<h1>(.*?)</h1>", html, re.S)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    if m:
        t = H.unescape(re.sub(r"<[^>]+>", "", m.group(1)))
        return re.sub(r"\s*\|\s*.*$", "", t).strip()
    return os.path.basename(os.path.dirname(path))


def stub(title, dest, label):
    t = H.escape(title)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{t} has moved | BRYME</title><meta name="description" content="This {H.escape(label)} page has moved. Continue to {t} on BRYME."><meta name="robots" content="noindex,follow"><link rel="canonical" href="{SITE}{dest}"><meta http-equiv="refresh" content="0;url={dest}"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/site.css"></head><body><header class="top"><div class="shell"><a class="brand" href="/">BRY<b>ME</b></a></div></header><main class="shell"><section class="hero"><div class="eyebrow">Moved</div><h1>{t} has moved</h1><p class="lead">This title now lives on its {H.escape(label)} page.</p><p><a class="cta" href="{dest}">Continue to {t}</a></p></section></main></body></html>
"""


def main():
    series = listing_name("series")
    anime = listing_name("anime")
    restored = []
    for slug in sorted(series | anime):
        src = os.path.join(ROOT, "movie", slug, "index.html")
        if not os.path.exists(src):
            continue
        if slug in series:
            dest, label = f"/series/{slug}/", "TV series"
        else:
            dest, label = f"/anime/{slug}/", "anime"
        title = page_title(src)
        # Prefer the canonical page's H1 when the movie copy is a stub already
        canon = os.path.join(ROOT, dest.strip("/"), "index.html")
        if os.path.exists(canon):
            title = page_title(canon) or title
        os.makedirs(os.path.dirname(src), exist_ok=True)
        open(src, "w", encoding="utf-8").write(stub(title, dest, label))
        restored.append((f"/movie/{slug}/", dest))

    # sitemap: drop redirected / noindex URLs
    sm_path = os.path.join(ROOT, "sitemap.xml")
    sm = open(sm_path, encoding="utf-8").read()
    drop = {SITE + old for old, _ in restored}
    kept, removed = [], 0
    for block in re.findall(r"  <url>.*?</url>\n?", sm, re.S):
        loc = re.search(r"<loc>([^<]+)</loc>", block)
        if loc and loc.group(1) in drop:
            removed += 1
            continue
        kept.append(block if block.endswith("\n") else block + "\n")
    head = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    open(sm_path, "w", encoding="utf-8").write(head + "".join(kept) + "</urlset>\n")

    # Render/Netlify-style redirects (HTML refresh remains the static fallback)
    lines = ["# Type-mismatch title URLs → canonical type. Do not delete these paths."]
    for old, dest in restored:
        lines.append(f"{old}  {dest}  301")
    open(os.path.join(ROOT, "_redirects"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

    print(f"restored {len(restored)} redirect stubs")
    print(f"removed {removed} sitemap URLs")
    print(f"wrote _redirects ({len(restored)} rules)")


if __name__ == "__main__":
    main()

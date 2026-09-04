#!/usr/bin/env python3
"""Pilot-page content pass for the Movie SEO brief.

Does not add pages, change URLs, or invent streaming availability.
Updates the existing 29 pilot title pages:
  - unique meta description (word-boundary, what the page actually offers)
  - honest where-to-watch block (no generic Netflix/Crunchyroll chips)
  - "Watch Now" CTA → "Where to watch"
  - billed cast row (not only the first name)
  - Shōgun case-study copy for the watch-intent gap
"""
import html as H
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def esc(s):
    return H.escape(str(s), quote=True)


def clip(s, n=155):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    if len(s) <= n:
        return s
    cut = s[:n]
    sp = cut.rfind(" ")
    return (cut[:sp] if sp > n * 0.55 else cut).rstrip(" ,;:.") + "…"


def initials(name):
    parts = [p for p in re.sub(r"[()]", " ", name).split() if p and p[0].isalpha()]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


GUIDANCE = json.load(open(os.path.join(ROOT, "content", "watch-guidance.json")))
MOVIES = {m["slug"]: m for m in json.load(open(os.path.join(ROOT, "data", "movies.json")))}

PILOT = [
    {"path": "series/shogun", "slug": "shogun"},
    {"path": "movie/spider-man-no-way-home", "slug": "spider-man-no-way-home"},
    {"path": "movie/deadpool-wolverine", "slug": "deadpool-wolverine"},
    {"path": "movie/thor-ragnarok", "slug": "thor-ragnarok"},
    {"path": "movie/avengers-infinity-war", "slug": "avengers-infinity-war"},
    {"path": "movie/28-years-later", "slug": "28-years-later"},
    {"path": "movie/gladiator-ii", "slug": "gladiator-ii"},
    {"path": "series/house-of-the-dragon", "slug": "house-of-the-dragon"},
    {"path": "movie/inside-out-2", "slug": "inside-out-2"},
    {"path": "movie/jawan", "slug": "jawan"},
    {"path": "movie/jurassic-world-rebirth", "slug": "jurassic-world-rebirth"},
    {"path": "movie/rrr", "slug": "rrr"},
    {"path": "series/silo", "slug": "silo"},
    {"path": "movie/superman-2025", "slug": "superman-2025"},
    {"path": "series/ted-lasso", "slug": "ted-lasso"},
    {"path": "movie/the-substance", "slug": "the-substance"},
    {"path": "movie/twisters", "slug": "twisters"},
    {"path": "movie/coco", "slug": "coco"},
    {"path": "movie/the-wild-robot", "slug": "the-wild-robot"},
    {"path": "movie/spider-man-brand-new-day", "slug": "spider-man-brand-new-day"},
    {"path": "movie/toy-story-5", "slug": "toy-story-5"},
    {"path": "movie/the-end-of-oak-street", "slug": "the-end-of-oak-street"},
    {"path": "movie/the-notebook", "slug": "the-notebook"},
    {"path": "anime/your-name", "slug": "your-name"},
    {"path": "anime/spirited-away", "slug": "spirited-away"},
    {"path": "movie/back-to-the-future", "slug": "back-to-the-future"},
    {"path": "series/game-of-thrones", "slug": "game-of-thrones"},
    {"path": "movie/insidious", "slug": "insidious"},
    {"path": "series/the-walking-dead", "slug": "the-walking-dead"},
]


def meta_for(m, g):
    title, year, kind = m["title"], m.get("year"), m.get("typeDir")
    noun = "series" if kind == "series" else ("anime" if kind == "anime" else "film")
    if m["slug"] == "shogun":
        return "Shōgun (2024): FX series. Official trailer, billed cast, story, and how to find a legal stream. BRYME does not host episodes."
    if g and g.get("originalNetwork") and kind == "series":
        return clip(f"{title} ({year}) is {g['originalNetwork']}'s {noun}. Official trailer, billed cast, story, and how to find a legal stream. BRYME does not host episodes.")
    if g and g.get("originalNetwork"):
        return clip(f"{title} ({year}) — {g['originalNetwork']} {noun}. Official trailer, billed cast, story, and how to find a legal copy. BRYME does not host the film.")
    if kind == "series":
        return clip(f"{title} ({year}) TV series: official trailer, billed cast, story, and how to find a legal stream. BRYME does not host episodes.")
    if kind == "anime":
        return clip(f"{title} ({year}) anime: official trailer, billed cast, story, and how to find a legal stream. BRYME does not host the title.")
    return clip(f"{title} ({year}): official trailer, billed cast, story, and how to find a legal copy. BRYME does not host the film.")


def watch_block(m, g):
    title = m["title"]
    kind = m.get("typeDir")
    host_word = "episodes" if kind == "series" else "this title"
    parts = [
        f'<section class="tp-watch" id="watch"><h2>Where to watch legally</h2>',
        f"<p>BRYME is not a streaming site and does not host {esc(title)}.</p>",
    ]
    if g and g.get("originalNetwork"):
        article = "an" if re.match(r"^[AEIOU]", g["originalNetwork"]) else "a"
        label = "original series" if kind == "series" else ("title" if kind == "anime" else "title")
        lead = g.get("lead") or "That tells you which licensed family to search first. Rights move by country and date."
        parts.append(f"<p>{esc(title)} is {article} {esc(g['originalNetwork'])} {label}. {esc(lead)}</p>")
    parts.append(
        f"<p>To find a legal copy: search “{esc(title)}” in the licensed apps available in your country "
        "and confirm the title page on the service itself before paying or starting a trial. "
        "Skip unofficial “free watch” sites — they are not listed here.</p>"
    )
    checks = (g or {}).get("check") or []
    btns = []
    for c in checks:
        if c.get("name") and c.get("url"):
            btns.append(
                f'<a class="tp-watch-btn" href="{esc(c["url"])}" rel="nofollow noopener" target="_blank">Check {esc(c["name"])}</a>'
            )
    for link in m.get("watchLinks") or []:
        url = link.get("url") or ""
        if not url.startswith("https://"):
            continue
        name = link.get("name") or "service"
        is_search = "/search" in url or "q=" in url
        label = ("Search " if is_search else "Check ") + name
        btns.append(
            f'<a class="tp-watch-btn" href="{esc(url)}" rel="nofollow noopener" target="_blank">{esc(label)}</a>'
        )
    if btns:
        parts.append('<div class="tp-watch-row">' + "".join(btns) + "</div>")
    parts.append(
        '<p class="tp-watch-note">A “Check” or “Search” link opens an official service. '
        "It is not a promise the title is on that service in your country today. "
        f"BRYME does not host {host_word}. These links are not advertisements.</p></section>"
    )
    return "".join(parts)


def shogun_extra():
    return (
        '<section class="tp-watch-intent" id="find-legally">'
        "<h2>How to find Shōgun legally</h2>"
        "<p>People searching “Shōgun watch” usually want a licensed stream, not another recap. "
        "BRYME cannot play the series. This page is here so you can confirm what it is, "
        "watch the official FX trailer, see the billed cast, and know which family of services to search.</p>"
        "<p>Shōgun is an FX original. In many territories FX originals have been carried on "
        "Hulu and Disney+. That has been widely reported; it is still not a live catalogue row. "
        "Open the licensed app you actually have, search the title, and only continue if the "
        "service’s own title page lists it for your country.</p>"
        "<p>If no licensed service in your country offers it right now, wait or use a legal storefront. "
        "Unofficial “free full episode” sites are not listed here.</p>"
        "</section>"
    )


def set_attr(html, tag_re, new_val):
    return re.sub(tag_re, lambda _m: _m.group(0).split("content=", 1)[0] + f'content="{esc(new_val)}"', html, count=1)


def apply(path, slug):
    fp = os.path.join(ROOT, path, "index.html")
    if not os.path.exists(fp):
        print("MISSING", path)
        return False
    m = MOVIES.get(slug)
    if not m:
        print("NO DATA", slug)
        return False
    g = GUIDANCE.get(slug) if isinstance(GUIDANCE.get(slug), dict) else None
    html = open(fp, encoding="utf-8").read()
    orig = html
    meta = meta_for(m, g)

    html = re.sub(
        r'<meta name="description" content="[^"]*"',
        f'<meta name="description" content="{esc(meta)}"',
        html,
        count=1,
    )
    html = re.sub(
        r'<meta property="og:description" content="[^"]*"',
        f'<meta property="og:description" content="{esc(meta)}"',
        html,
        count=1,
    )
    html = re.sub(
        r'<meta name="twitter:description" content="[^"]*"',
        f'<meta name="twitter:description" content="{esc(meta)}"',
        html,
        count=1,
    )

    html = html.replace(
        'class="cta nm-watch-now" href="#watch">▶ Watch Now</a>',
        'class="cta nm-watch-now" href="#watch">Where to watch</a>',
    )
    html = html.replace('href="#watch">Watch Now</a>', 'href="#watch">Where to watch</a>')

    block = watch_block(m, g)
    if slug == "shogun" and 'id="find-legally"' not in html:
        block = shogun_extra() + block
    if re.search(r'<section class="tp-watch" id="watch">.*?</section>', html, re.S):
        html = re.sub(r'<section class="tp-watch" id="watch">.*?</section>', block, html, count=1, flags=re.S)
    else:
        html = html.replace('<section class="tp-next">', block + '<section class="tp-next">', 1)

    cast = m.get("cast") or []
    if cast:
        items = "".join(
            f'<div class="nm-cast-item"><span class="nm-avatar">{esc(initials(n))}</span><b>{esc(n)}</b></div>'
            for n in cast[:8]
        )
        new_row = f'<div class="nm-cast-row">{items}</div>'
        html = re.sub(r'<div class="nm-cast-row">.*?</div>', new_row, html, count=1, flags=re.S)

    if html != orig:
        open(fp, "w", encoding="utf-8").write(html)
        return True
    return False


def main():
    n = 0
    for p in PILOT:
        if apply(p["path"], p["slug"]):
            n += 1
            print("updated", p["path"])
        else:
            print("unchanged", p["path"])
    print(f"pilot content updated: {n}/{len(PILOT)}")


if __name__ == "__main__":
    main()

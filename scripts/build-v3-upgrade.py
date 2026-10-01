#!/usr/bin/env python3
"""BRYME Media v3 "Watch Next" — architecture sample generator.

Builds the new content types of the mass-upgrade drop from the authored packs
(content/upgrade-entertainment.json, content/upgrade-sports.json) plus the
archive's own datasets (movies, trailers, posters, recommendations):

  /entertainment/                     cinematic discovery hub (rebuild)
  /watch-next/                        recommendation index
  /watch-next/<slug>/                 4 recommendation pages
  /sports/explainers/                 explainer index
  /sports/explainers/<slug>/          8 question-led explainers
  /<movie|series|anime>/<slug>/       5 title pages upgraded in place

Deterministic and idempotent: no timestamps, fixed ordering, byte-stable
output. The v3 shell (scripts/apply-media-brand.py) runs after this and adds
header/footer/mobile chrome where missing. Internal links emitted here are
verified against the filesystem (and the routes generated in this same run)
before the script exits.
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://bryme-media.onrender.com"
DIR_FOR_TYPE = {"movie": "movie", "series": "series", "anime": "anime"}
TYPE_LABEL = {"movie": "Film", "series": "Series", "anime": "Anime"}
HUB_FOR_DIR = {"movie": "/movies/", "series": "/series/", "anime": "/anime/"}

# ---------------------------------------------------------------- data loading

def load_json(rel: str):
    with open(ROOT / rel, encoding="utf-8") as fh:
        return json.load(fh)

MOVIES = {m["slug"]: m for m in load_json("data/movies.json") if m.get("slug")}
TRAILERS = {t["slug"]: t for t in load_json("data/trailers.json") if t.get("slug")}
POSTERS = load_json("data/posters.json")
REC_DATA = load_json("data/rec-data.json")
REC_ITEMS = {i["s"]: i for i in REC_DATA.get("items", [])}

ENT = load_json("content/upgrade-entertainment.json")

# The sports library is authored in batches so each drop stays reviewable.
# Merge them into one ordered list; slugs must stay unique across batches.
SPORTS_BATCHES = [
    "content/upgrade-sports.json",
    "content/upgrade-sports-batch2a.json",
    "content/upgrade-sports-batch2b.json",
    "content/upgrade-sports-batch3a.json",
]
_EXPLAINERS: list = []
_seen_slugs: set[str] = set()
for _batch in SPORTS_BATCHES:
    for _pack in load_json(_batch)["explainers"]:
        if _pack["slug"] in _seen_slugs:
            raise SystemExit(f"duplicate explainer slug across batches: {_pack['slug']}")
        _seen_slugs.add(_pack["slug"])
        _EXPLAINERS.append(_pack)
SPORTS = {"explainers": _EXPLAINERS}

GENERATED_ROUTES: set[str] = set()
LINK_ERRORS: list[str] = []

# ---------------------------------------------------------------- small helpers

def esc(text) -> str:
    return html.escape(str(text), quote=True)

def clip(text: str, limit: int = 155) -> str:
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0] + "…"

def trailer_id(slug: str) -> str | None:
    entry = TRAILERS.get(slug)
    return entry.get("videoId") if entry else None

def art_for(slug: str) -> str:
    local = POSTERS.get(slug)
    if local:
        return local
    vid = trailer_id(slug)
    if vid:
        return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
    return "/assets/cards/placeholder.jpg"

def title_page(slug: str) -> str | None:
    movie = MOVIES.get(slug)
    if not movie:
        return None
    directory = DIR_FOR_TYPE.get(movie.get("typeDir") or movie.get("legacyType") or "", None)
    if not directory:
        item = REC_ITEMS.get(slug)
        directory = DIR_FOR_TYPE.get((item or {}).get("ty", ""))
    if not directory:
        return None
    return f"/{directory}/{slug}/"

def display_title(slug: str) -> str:
    item = REC_ITEMS.get(slug)
    if item:
        return item["t"]
    movie = MOVIES.get(slug)
    return movie["title"] if movie else slug.replace("-", " ").title()

def display_year(slug: str) -> str:
    item = REC_ITEMS.get(slug)
    if item and item.get("y"):
        return str(item["y"])
    movie = MOVIES.get(slug)
    return str(movie.get("year") or "")

def display_type(slug: str) -> str:
    item = REC_ITEMS.get(slug)
    if item:
        return item.get("ty", "")
    movie = MOVIES.get(slug)
    return movie.get("typeDir") or ""

def route_exists(href: str) -> bool:
    clean = href.split("#", 1)[0].split("?", 1)[0]
    if clean in GENERATED_ROUTES:
        return True
    rel = clean.strip("/")
    if not rel:
        return (ROOT / "index.html").is_file()
    if rel.startswith("assets/"):
        return (ROOT / rel).is_file()
    return (ROOT / rel / "index.html").is_file() or (ROOT / rel).is_file()

def href_for(slug: str) -> str:
    """Best real URL for a title: dataset type first, then disk truth."""
    movie = MOVIES.get(slug)
    candidates = []
    if movie:
        directory = DIR_FOR_TYPE.get(movie.get("typeDir") or movie.get("legacyType") or "")
        if directory:
            candidates.append(f"/{directory}/{slug}/")
    item = REC_ITEMS.get(slug)
    if item and item.get("ty") in DIR_FOR_TYPE:
        candidates.append(f"/{DIR_FOR_TYPE[item['ty']]}/{slug}/")
    for directory in ("movie", "series", "anime"):
        candidates.append(f"/{directory}/{slug}/")
    for candidate in candidates:
        if route_exists(candidate):
            return candidate
    raise SystemExit(f"FATAL: no title page found for '{slug}' (tried {candidates})")

def check_links(pages: dict[str, str]) -> None:
    """Every root-relative href in generated pages must resolve."""
    import re
    for route, body in pages.items():
        for href in re.findall(r'href="(/[^"#]*)', body):
            if not route_exists(href):
                LINK_ERRORS.append(f"{route}: broken internal link {href}")
    if LINK_ERRORS:
        print("FATAL: broken internal links in v3 sample:", file=sys.stderr)
        for item in LINK_ERRORS:
            print("  -", item, file=sys.stderr)
        sys.exit(1)

# ---------------------------------------------------------------- page shell

def crumbs(items: list[tuple[str, str | None]]) -> str:
    parts = []
    for label, href in items:
        if href:
            parts.append(f'<li><a href="{href}">{esc(label)}</a></li>')
        else:
            parts.append(f'<li aria-current="page">{esc(label)}</li>')
    return '<ul class="v3-crumbs">' + "".join(parts) + "</ul>"

def head(*, title: str, description: str, route: str, nav: str) -> str:
    canonical = BASE + route
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="robots" content="noindex,follow"><title>{esc(title)} | BRYME Media</title><meta name="description" content="{esc(clip(description))}"><link rel="canonical" href="{canonical}"><meta property="og:type" content="website"><meta property="og:site_name" content="BRYME Media"><meta property="og:title" content="{esc(title)} | BRYME Media"><meta property="og:description" content="{esc(clip(description))}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{esc(BASE + '/assets/bryme-card.png')}"><meta name="twitter:card" content="summary_large_image"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/bryme-v2.css"><link rel="stylesheet" href="/assets/media-v3.css"><script src="/assets/media-v3.js" defer></script></head><body data-nav="{nav}"><main id="main" class="v3-main">'''

FOOT = "</main></body></html>"

def trailer_facade(video_id: str, label: str, caption: str) -> str:
    return f'''<div class="v3-trailer"><img src="https://i.ytimg.com/vi/{esc(video_id)}/hqdefault.jpg" alt="" loading="lazy" width="480" height="360"><button class="v3-play" type="button" data-v3-play="{esc(video_id)}" data-v3-title="{esc(label)}" aria-label="Play {esc(label)}"><span class="v3-play-btn">▶ Play trailer</span></button><span class="v3-trailer-caption"><span>{esc(caption)}</span><span>click to load the player</span></span></div>'''

def card(*, href: str, art: str, title: str, blurb: str, meta: str, poster: bool = False, play: bool = False) -> str:
    play_html = '<span class="card-play" aria-hidden="true">▶</span>' if play else ""
    return f'''<a class="card{" poster" if poster else ""}" href="{href}"><span class="card-art" style="background-image:url('{esc(art)}')">{play_html}</span><span class="card-body"><h3>{esc(title)}</h3><p>{esc(blurb)}</p><span class="card-meta">{esc(meta)}</span></span></a>'''

# ---------------------------------------------------------------- templates

def recommendation_page(pack: dict) -> str:
    subject = pack["subject"]
    subject_href = href_for(subject)
    vid = trailer_id(subject)
    subject_title = display_title(subject)
    subject_year = display_year(subject)

    rec_blocks = []
    for rec in pack["recs"]:
        slug = rec["slug"]
        href = href_for(slug)
        reason = rec["reason"]
        parts = [
            f'<article class="v3-rec"><div class="v3-rec-head">',
            f'<span class="v3-rec-art" style="background-image:url(\'{esc(art_for(slug))}\')" role="img" aria-label=""></span>',
            f'<div class="v3-rec-copy"><span class="v3-tag coral">{esc(TYPE_LABEL.get(display_type(slug), "Title"))} · {esc(display_year(slug))}</span>',
            f'<h3>{esc(display_title(slug))}</h3><p class="v3-rec-why">{esc(reason)}</p>',
            f'<p class="v3-rec-links"><a href="{href}">{esc(rec.get("bryme", display_title(slug) + " on BRYME"))} →</a></p>',
            "</div></div></article>",
        ]
        rec_blocks.append("".join(parts))

    faq = "".join(
        f'<details><summary>{esc(q["q"])}</summary><p>{esc(q["a"])}</p></details>'
        for q in pack.get("faq", [])
    )

    related = "".join(
        card(
            href=f"/watch-next/{slug}/",
            art=art_for(ENT_REC_BY_SLUG[slug]["subject"]),
            title=ENT_REC_BY_SLUG[slug]["title"],
            blurb=clip(ENT_REC_BY_SLUG[slug]["lede"], 120),
            meta="Watch Next",
        )
        for slug in pack.get("related", [])
        if slug in ENT_REC_BY_SLUG
    )

    return "".join([
        head(
            title=pack["title"],
            description=pack["lede"],
            route=f"/watch-next/{pack['slug']}/",
            nav="watch-next",
        ),
        f'''<section class="v3-hero"><div class="wrap">{crumbs([("Home", "/"), ("Watch Next", "/watch-next/"), (pack["title"], None)])}<p class="v3-kicker"><i></i>Watch Next · Recommendation</p><h1 class="v3-display">{esc(pack["title"])}</h1><p class="v3-lede">{esc(pack["lede"])}</p></div></section>''',
        '<section class="v3-sec"><div class="wrap">',
        '<div class="v3-sec-head"><h2>The starting point</h2><a class="v3-more" href="' + subject_href + '">' + esc(subject_title) + " on BRYME →</a></div>",
        f'<p class="v3-count" style="margin:0 0 16px">{esc(subject_title)} · {esc(subject_year)} · you are here because you finished it — and the list below is what to watch next.</p>',
    ] + [
        (trailer_facade(vid, f"{subject_title} trailer", f"{subject_title} — official trailer") if vid else "")
    ] + [
        f'<p class="v3-media-note">The player loads only when you press play — the page itself ships no YouTube iframes.</p>',
        '<div class="v3-prose" style="margin-top:26px">',
        "".join(f"<p>{esc(p)}</p>" for p in pack["intro"]),
        f'</div><div class="v3-callout"><h3>Who this list is for</h3><p>{esc(pack["audience"])}</p></div>',
        "</div></section>",
        '<section class="v3-sec" style="padding-top:0"><div class="wrap">',
        f'<div class="v3-sec-head"><h2>The list — {len(pack["recs"])} to queue next</h2><span class="v3-count">each pick links to its BRYME title page</span></div>',
        '<div class="v3-collection">' + "".join(rec_blocks) + "</div>",
        f'<div class="v3-callout" style="margin-top:26px"><h3>How to watch</h3><p>{esc(pack["viewing"])}</p></div>',
        "</div></section>",
        ('<section class="v3-sec v3-sec-tight" style="border-top:1px solid var(--bm-line)"><div class="wrap"><div class="v3-sec-head"><h2>Related lists</h2><a class="v3-more" href="/watch-next/">All Watch Next lists →</a></div><div class="v3-rail">' + related + "</div></div></section>") if related else "",
        (f'<section class="v3-sec"><div class="wrap"><div class="v3-sec-head"><h2>Questions, quickly</h2></div><div class="v3-faq">{faq}</div></div></section>') if faq else "",
        (f'<section class="v3-sec v3-sec-tight"><div class="wrap"><div class="v3-callout"><h3>Staging preview</h3><p>This page is part of the BRYME Media rebuild preview. It is deliberately noindexed and not published for search; copy may change before the structure is approved for migration.</p></div></div></section>'),
        FOOT,
    ])

def title_page_v3(pack: dict) -> str:
    slug, directory = pack["slug"], pack["dir"]
    movie = MOVIES.get(slug, {})
    vid = trailer_id(slug)
    year = display_year(slug)
    label = TYPE_LABEL.get(display_type(slug), "Title")
    href = f"/{directory}/{slug}/"
    cast = [c for c in (movie.get("cast") or []) if c][:4]
    country = (movie.get("country") or "").split(";")[0].strip()
    genres = movie.get("genres") or ([movie.get("genre")] if movie.get("genre") else [])
    facts = [f"<li><b>Year</b> {esc(year)}</li>"]
    if country:
        facts.append(f"<li><b>Country</b> {esc(country)}</li>")
    if movie.get("director"):
        facts.append(f"<li><b>Director</b> {esc(movie['director'])}</li>")
    if movie.get("runtime"):
        facts.append(f"<li><b>Runtime</b> {esc(movie['runtime'])}</li>")
    if cast:
        facts.append(f"<li><b>Starring</b> {esc(', '.join(cast))}</li>")
    if genres:
        facts.append(f"<li><b>Genre</b> {esc(', '.join(str(g) for g in genres[:3]))}</li>")

    related = "".join(
        card(
            href=href_for(other),
            art=art_for(other),
            title=display_title(other),
            blurb=clip(MOVIES.get(other, {}).get("description") or (REC_ITEMS.get(other) or {}).get("t") or "", 110),
            meta=f"{TYPE_LABEL.get(display_type(other), 'Title')} · {display_year(other)}",
            play=True,
        )
        for other in pack.get("relatedTitles", [])
    )
    backlink = pack.get("backlink")
    back_html = ""
    if backlink and backlink in ENT_REC_BY_SLUG:
        back_html = f'<div class="v3-callout"><h3>Featured in a Watch Next list</h3><p>This title is one of the picks in <a href="/watch-next/{backlink}/">{esc(ENT_REC_BY_SLUG[backlink]["title"])}</a> — see why it made the list and what to pair it with.</p></div>'

    return "".join([
        head(title=f"{pack['title']} — trailer, details and what to watch next", description=f"{pack['intro'][0]}", route=href, nav=display_type(slug) or "movies"),
        f'''<section class="v3-hero"><div class="wrap">{crumbs([("Home", "/"), (("Films" if label == "Film" else "Anime" if label == "Anime" else "Series"), HUB_FOR_DIR[directory]), (pack["title"], None)])}<div class="v3-title-head"><div class="v3-title-poster" style="background-image:url('{esc(art_for(slug))}')" role="img" aria-label="{esc(pack["title"])} artwork"></div><div class="v3-title-copy"><p class="v3-kicker"><i></i>{esc(label)} · BRYME Media</p><h1 class="v3-display">{esc(pack["title"])}</h1><ul class="v3-factlist">{"".join(facts)}</ul></div></div></div></section>''',
        (f'<section class="v3-sec v3-sec-tight"><div class="wrap">{trailer_facade(vid, pack["title"] + " trailer", pack["title"] + " — official trailer")}<p class="v3-media-note">Privacy-enhanced player, loaded only on click.</p></div></section>') if vid else "",
        '<section class="v3-sec" style="padding-top:0"><div class="wrap"><div class="v3-prose">',
        "".join(f"<p>{esc(p)}</p>" for p in pack["intro"]),
        f'<h2>Why it is worth your evening</h2><p>{esc(pack["why"])}</p>',
        f'<h2>How to watch it</h2><p>{esc(pack["viewing"])}</p>',
        "</div>", back_html,
        "</div></section>",
        (f'<section class="v3-sec v3-sec-tight" style="border-top:1px solid var(--bm-line)"><div class="wrap"><div class="v3-sec-head"><h2>Watch next after this</h2><span class="v3-count">hand-picked, not algorithmic</span></div><div class="v3-rail">{related}</div></div></section>') if related else "",
        FOOT,
    ])

def explainer_page(pack: dict, siblings: list[dict]) -> str:
    slug = pack["slug"]
    myths = "".join(
        f'<li><b>{esc(m["belief"])}</b> {esc(m["reality"])}</li>' for m in pack.get("myths", [])
    )
    concepts = "".join(
        f'<li><a href="{esc(c["href"])}">{esc(c["label"])}</a><span>{esc(c["note"])}</span></li>'
        for c in pack.get("concepts", [])
    )
    faq = "".join(
        f'<details><summary>{esc(q["q"])}</summary><p>{esc(q["a"])}</p></details>'
        for q in pack.get("faq", [])
    )
    more = "".join(
        card(href=f"/sports/explainers/{s['slug']}/", art="/assets/cards/placeholder.jpg", title=s["short"], blurb=clip(s["answer"], 120), meta="Sports explainer")
        for s in siblings
    )

    return "".join([
        head(title=pack["question"], description=pack["answer"], route=f"/sports/explainers/{slug}/", nav="sports"),
        f'''<section class="v3-hero v3-hero-slim"><div class="wrap">{crumbs([("Home", "/"), ("Sports", "/sports/"), ("Explainers", "/sports/explainers/"), (pack["short"], None)])}<p class="v3-kicker"><i></i>{esc(pack["kicker"])}</p><h1 class="v3-display">{esc(pack["question"])}</h1></div></section>''',
        f'<section class="v3-sec-tight"><div class="wrap"><div class="v3-answer"><h2>The short answer</h2><p>{esc(pack["answer"])}</p></div></div></section>',
        '<section class="v3-sec" style="padding-top:8px"><div class="wrap"><div class="v3-prose">',
        "".join(f"<p>{esc(p)}</p>" for p in pack["explain"]),
        '</div>',
        (f'<div class="v3-callout"><h3>In practice</h3><p>{esc(pack["example"])}</p></div>') if pack.get("example") else "",
        (f'<div class="v3-callout"><h3>Common misunderstandings</h3><ul class="v3-myths">{myths}</ul></div>') if myths else "",
        (f'<div class="v3-concept"><h3>Where this connects</h3><ul>{concepts}</ul></div>') if concepts else "",
        (f'<div class="v3-faq" style="margin-top:26px"><h2 style="font-size:20px;margin:0 0 14px">Quick questions</h2>{faq}</div>') if faq else "",
        "</div></section>",
        (f'<section class="v3-sec v3-sec-tight" style="border-top:1px solid var(--bm-line)"><div class="wrap"><div class="v3-sec-head"><h2>Keep reading</h2><a class="v3-more" href="/sports/explainers/">All explainers →</a></div><div class="v3-rail">{more}</div></div></section>') if more else "",
        FOOT,
    ])

def watch_next_hub() -> str:
    posts = "".join(
        f'''<a class="v3-postcard" href="/watch-next/{esc(pack["slug"])}/"><span class="v3-postcard-art" style="background-image:url('{esc(art_for(pack["subject"]))}')"></span><span class="v3-postcard-copy"><span class="v3-tag coral">Recommendation</span><h3>{esc(pack["title"])}</h3><p>{esc(clip(pack["lede"], 200))}</p><span class="v3-postcard-meta">{len(pack["recs"])} picks · {esc(display_title(pack["subject"]))}</span></span></a>'''
        for pack in ENT["recommendations"]
    )
    return "".join([
        head(title="Watch Next — what to watch after what you just finished", description="BRYME's recommendation desk: every list starts from a title you loved and explains why each next pick fits.", route="/watch-next/", nav="watch-next"),
        '''<section class="v3-hero"><div class="wrap">''' + crumbs([("Home", "/"), ("Watch Next", None)]) + '''<p class="v3-kicker"><i></i>Recommendation desk</p><h1 class="v3-display">You finished something. <em>Here is what is next.</em></h1><p class="v3-lede">Every list starts from one title and explains — in plain language — why each pick belongs. No 'because our algorithm says so': each recommendation links straight to that title's BRYME page.</p></div></section>''',
        '<section class="v3-sec"><div class="wrap"><div class="v3-collection">' + posts + "</div>",
        '<div class="v3-callout" style="margin-top:28px"><h3>How Watch Next grows</h3><p>This desk currently holds a reviewed sample. Once the structure is approved, the same format extends across the catalogue — starting with the titles people finish most often.</p></div>',
        "</div></section>",
        FOOT,
    ])

def explainers_hub() -> str:
    # Group the library by theme so a visitor browsing for a rule lands in the
    # right neighbourhood instead of scrolling one long alphabetical list.
    groups: dict[str, list] = {}
    for p in SPORTS["explainers"]:
        groups.setdefault(p["kicker"], []).append(p)

    sections = []
    for group, packs in groups.items():
        posts = "".join(
            f'''<a class="v3-postcard" href="/sports/explainers/{esc(p["slug"])}/"><span class="v3-postcard-art plain"></span><span class="v3-postcard-copy"><span class="v3-tag lime">{esc(group)}</span><h3>{esc(p["question"])}</h3><p>{esc(clip(p["answer"], 200))}</p><span class="v3-postcard-meta">{esc(p["short"])}</span></span></a>'''
            for p in packs
        )
        sections.append(
            f'<div class="v3-sec-head" style="margin-top:30px"><h2>{esc(group)}</h2><span class="v3-count">{len(packs)} question{"s" if len(packs) != 1 else ""}</span></div><div class="v3-collection">{posts}</div>'
        )

    total = len(SPORTS["explainers"])
    return "".join([
        head(title="Football rules explained — the complete question library", description="BRYME's football rules library: every question answered straight, then explained properly with worked examples and the myths that cause most arguments.", route="/sports/explainers/", nav="sports"),
        '''<section class="v3-hero"><div class="wrap">''' + crumbs([("Home", "/"), ("Sports", "/sports/"), ("Explainers", None)]) + f'''<p class="v3-kicker"><i></i>Sports desk · Rules library</p><h1 class="v3-display">We are not a livescore. <em>We break down the rules.</em></h1><p class="v3-lede">{total} evergreen football questions answered — offside, handball, cards, tiebreakers, how competitions actually work. Straight answer first, then the full explanation.</p></div></section>''',
        '<section class="v3-sec"><div class="wrap">' + "".join(sections),
        '<div class="v3-callout" style="margin-top:28px"><h3>A network, not a list</h3><p>Each explainer links to the concepts it depends on, so one question naturally leads to the next — offside leads to VAR, VAR leads to when a goal is a goal, and so on. Every page here is evergreen: it answers the same question in 2026 as it will in 2036.</p></div>',
        "</div></section>",
        FOOT,
    ])

def entertainment_hub() -> str:
    rails = "".join(
        card(
            href=f"/watch-next/{pack['slug']}/",
            art=art_for(pack["subject"]),
            title=pack["title"],
            blurb=clip(pack["lede"], 120),
            meta=f"{len(pack['recs'])} picks · Watch Next",
            play=True,
        )
        for pack in ENT["recommendations"]
    )
    titles = "".join(
        card(
            href=f"/{t['dir']}/{t['slug']}/",
            art=art_for(t["slug"]),
            title=t["title"],
            blurb=clip(t["intro"][0], 110),
            meta=f"{TYPE_LABEL.get(t['dir'], 'Title')} · {display_year(t['slug'])}",
            play=True,
        )
        for t in ENT["titles"]
    )
    return "".join([
        head(title="Entertainment — find what to watch next", description="Movies, series and anime discovery from BRYME: recommendation lists, upgraded title pages and the full archive.", route="/entertainment/", nav="entertainment"),
        '''<section class="v3-hero"><div class="wrap">''' + crumbs([("Home", "/"), ("Entertainment", None)]) + '''<p class="v3-kicker"><i></i>BRYME Media · Entertainment</p><h1 class="v3-display">I loved this. <em>What do I watch next?</em></h1><p class="v3-lede">That question is the whole desk. Recommendation lists you can actually follow, title pages worth reading, and the full film & television archive underneath.</p><div class="v3-actions"><a class="v3-btn" href="/watch-next/">Browse Watch Next lists</a><a class="v3-btn ghost" href="#title-pages">Title pages</a></div></div></section>''',
        '<section class="v3-sec"><div class="wrap"><div class="v3-sec-head"><h2>Recommendation lists</h2><a class="v3-more" href="/watch-next/">All lists →</a></div><div class="v3-rail">' + rails + "</div></div></section>",
        '<section class="v3-sec" id="title-pages" style="padding-top:0"><div class="wrap"><div class="v3-sec-head"><h2>Title pages, upgraded</h2><span class="v3-count">trailer, facts, why it is worth watching</span></div><div class="v3-rail">' + titles + "</div></div></section>",
        '''<section class="v3-sec" style="padding-top:0;border-top:1px solid var(--bm-line)"><div class="wrap"><div class="v3-sec-head"><h2>The archive</h2><span class="v3-count">preserved catalogue — being rebuilt desk by desk</span></div><div class="v3-grid">'''
        + card(href="/movies/", art="/assets/bryme-card.png", title="Films archive", blurb="The full preserved film catalogue, filterable by genre.", meta="Movies")
        + card(href="/series/", art="/assets/bryme-card.png", title="Series archive", blurb="TV and streaming series pages from the archive.", meta="Series")
        + card(href="/anime/", art="/assets/bryme-card.png", title="Anime archive", blurb="Anime titles and discovery routes.", meta="Anime")
        + card(href="/articles/", art="/assets/bryme-card.png", title="Original articles", blurb="BRYME's entertainment writing and guides.", meta="Read")
        + '</div><div class="v3-callout" style="margin-top:28px"><h3>Rebuild in progress</h3><p>This is the staging preview of the Entertainment rebuild: a reviewed sample of the new architecture on top of the preserved archive. Pages here are noindexed, and nothing on this desk is final until the structure is approved for the live site.</p></div></div></section>',
        FOOT,
    ])

# ---------------------------------------------------------------- main

ENT_REC_BY_SLUG = {p["slug"]: p for p in ENT["recommendations"]}

def main() -> None:
    pages: dict[str, str] = {}

    # register generated routes first so intra-sample links resolve
    pages["/entertainment/"] = entertainment_hub()
    pages["/watch-next/"] = watch_next_hub()
    pages["/sports/explainers/"] = explainers_hub()
    for pack in ENT["recommendations"]:
        pages[f"/watch-next/{pack['slug']}/"] = ""  # placeholder for link resolution
    for pack in SPORTS["explainers"]:
        pages[f"/sports/explainers/{pack['slug']}/"] = ""
    for pack in ENT["titles"]:
        pages[f"/{pack['dir']}/{pack['slug']}/"] = ""
    GENERATED_ROUTES.update(pages)

    # now render for real
    pages["/entertainment/"] = entertainment_hub()
    pages["/watch-next/"] = watch_next_hub()
    pages["/sports/explainers/"] = explainers_hub()
    for pack in ENT["recommendations"]:
        pages[f"/watch-next/{pack['slug']}/"] = recommendation_page(pack)
    explainer_list = SPORTS["explainers"]
    for index, pack in enumerate(explainer_list):
        siblings = [explainer_list[(index + step) % len(explainer_list)] for step in (1, 2, 3)]
        pages[f"/sports/explainers/{pack['slug']}/"] = explainer_page(pack, siblings)
    for pack in ENT["titles"]:
        pages[f"/{pack['dir']}/{pack['slug']}/"] = title_page_v3(pack)

    check_links(pages)

    written = 0
    for route, body in sorted(pages.items()):
        rel = route.strip("/")
        target = ROOT / rel / "index.html" if rel else ROOT / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        written += 1
    print(
        f"v3 upgrade sample: {written} pages written "
        f"({len(ENT['recommendations'])} rec lists, {len(SPORTS['explainers'])} explainers, "
        f"{len(ENT['titles'])} title pages, 3 hubs)"
    )

if __name__ == "__main__":
    main()

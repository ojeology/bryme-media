#!/usr/bin/env python3
"""Upgrade existing extra movie URLs with verified credits + original copy.

Does not create new slugs. Does not invent streaming availability.
Duplicates of catalogue titles become noindex redirects.
"""
import html as H
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://bryme.onrender.com"


def esc(s):
    return H.escape(str(s), quote=True)


def initials(name):
    parts = [p for p in re.sub(r"[()]", " ", name).split() if p and p[0].isalpha()]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def clip(s, n=155):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    if len(s) <= n:
        return s
    cut = s[:n]
    sp = cut.rfind(" ")
    return (cut[:sp] if sp > n * 0.55 else cut).rstrip(" ,;:.") + "…"


def exists(slug):
    for d in ("movie", "series", "anime"):
        if os.path.isfile(os.path.join(ROOT, d, slug, "index.html")):
            return d
    return None


def stub(title, dest):
    t = esc(title)
    return (
        f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{t} has moved | BRYME</title>"
        f'<meta name="description" content="This title now lives at its canonical BRYME page.">'
        f'<meta name="robots" content="noindex,follow">'
        f'<link rel="canonical" href="{SITE}{dest}">'
        f'<meta http-equiv="refresh" content="0;url={dest}">'
        f'<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">'
        f'<link rel="stylesheet" href="/assets/site.css"></head><body>'
        f'<header class="top"><div class="shell"><a class="brand" href="/">BRY<b>ME</b></a></div></header>'
        f'<main class="shell"><section class="hero"><div class="eyebrow">Moved</div>'
        f"<h1>{t} has moved</h1>"
        f'<p class="lead">Continue on the main BRYME title page.</p>'
        f'<p><a class="cta" href="{dest}">Continue to {t}</a></p>'
        f"</section></main></body></html>\n"
    )


def watch_block(rec):
    title = rec["title"]
    studio = rec.get("studio")
    bits = [
        '<section class="tp-watch" id="watch"><h2>Where to watch legally</h2>',
        f"<p>BRYME is not a streaming site and does not host {esc(title)}.</p>",
    ]
    if studio:
        bits.append(
            f"<p>{esc(title)} is a {esc(studio)} title. That tells you which licensed family to search first. "
            "Rights move by country and date — this is not a live catalogue listing.</p>"
        )
    bits.append(
        f"<p>To find a legal copy: search “{esc(title)}” in the licensed apps available in your country "
        "and confirm the title page on the service itself before paying or starting a trial. "
        "Skip unofficial “free watch” sites — they are not listed here.</p>"
    )
    bits.append(
        '<p class="tp-watch-note">BRYME does not host films. These notes are not advertisements '
        "and are not a promise the title is on any named service today.</p></section>"
    )
    return "".join(bits)


def related_cards(rec):
    cards = []
    movies = {m["slug"]: m for m in json.load(open(os.path.join(ROOT, "data", "movies.json")))}
    for slug in rec.get("related") or []:
        d = exists(slug)
        if not d:
            continue
        m = movies.get(slug) or {}
        title = m.get("title") or slug.replace("-", " ").title()
        year = m.get("year") or ""
        genre = (m.get("genres") or [m.get("genre")] or ["Film"])[0] or "Film"
        yt = m.get("youtubeId")
        img = f"https://i.ytimg.com/vi/{yt}/hqdefault.jpg" if yt else "/assets/bryme-card.png"
        cards.append(
            f'<a class="tp-loved-card" href="/{d}/{slug}/">'
            f'<img loading="lazy" decoding="async" width="320" height="180" src="{esc(img)}" alt="{esc(title)} thumbnail">'
            f"<span><b>{esc(title)}</b><em>{esc(genre)}{(' · ' + str(year)) if year else ''}</em>"
            f"<small>Next on BRYME if {esc(rec['title'])} is the lane you want.</small></span></a>"
        )
        if len(cards) >= 5:
            break
    return "".join(cards)


def build_main(rec):
    slug = rec["slug"]
    title = rec["title"]
    year = rec["year"]
    yt = rec["youtubeId"]
    cast = rec.get("cast") or []
    genres = rec.get("genres") or [rec.get("genre") or "Film"]
    genre = genres[0]
    dirs = [d.strip() for d in str(rec.get("director") or "").split(";") if d.strip()]
    lead = rec["description"]
    thumb = f"https://i.ytimg.com/vi/{yt}/hqdefault.jpg"
    watch = f"https://www.youtube.com/watch?v={yt}"
    cast_items = "".join(
        f'<div class="nm-cast-item"><span class="nm-avatar">{esc(initials(n))}</span><b>{esc(n)}</b></div>'
        for n in cast[:8]
    )
    rows = []
    if dirs:
        rows.append(("Director", ", ".join(dirs)))
    if cast:
        rows.append(("Cast", ", ".join(cast[:10])))
    rows.append(("Genres", ", ".join(genres)))
    if rec.get("runtime"):
        rows.append(("Runtime", rec["runtime"]))
    if rec.get("language"):
        rows.append(("Audio", rec["language"]))
    rows.append(("Year", str(year)))
    if rec.get("country"):
        rows.append(("Country", rec["country"]))
    rows_html = "".join(
        f'<div class="nm-detail-row"><div class="nm-detail-label">{esc(k)}</div>'
        f'<div class="nm-detail-value">{esc(v)}</div></div>'
        for k, v in rows
    )
    loved = related_cards(rec)
    wiki = rec.get("wikipedia") or ""
    source = (
        f'<p class="meta-source">Billed cast and director from '
        f'<a href="{esc(wiki)}" rel="nofollow noopener">Wikipedia</a> infobox · retrieved 2026-08-22. '
        "BRYME’s synopsis is written in-house.</p>"
        if wiki
        else ""
    )
    about = (
        f"<h2>What {esc(title)} is about</h2><p>{esc(lead)}</p>"
        f"<p>{esc(title)} ({year}) is listed on BRYME with the official trailer, billed cast"
        f"{(' and director ' + esc(dirs[0])) if dirs else ''} — not as a stream we host.</p>"
    )
    return f"""<main class="tp-page"><section class="nm-video-hero"><div class="nm-hero-bar"><a class="nm-back" href="#" onclick="history.back();return false" aria-label="Go back">‹ Back</a><a class="nm-x" href="/" aria-label="Close">✕</a></div><div class="nm-trailer-embed"><div class="trailer-section-inner" data-trailer-box data-trailer-candidates="[{esc(json.dumps({"id": yt, "type": "official-trailer", "label": "Official Trailer", "channel": "YouTube", "verified": True, "watch": watch}))}]" data-trailer-title="{esc(title)}"><div class="trailer-head"><span class="eyebrow">Trailer</span><span class="trailer-status t-ok">🟢 Official Trailer</span></div>
  <div class="trailer-frame" data-trailer-id="{yt}"><img loading="lazy" src="{thumb}" alt="{esc(title)} trailer thumbnail"><button type="button" class="trailer-play">Play trailer</button></div><div class="trailer-controls" data-trailer-controls hidden><button type="button" class="cta" data-trailer-unmute>Unmute</button><a class="quiet-link" href="{watch}" target="_blank" rel="noopener">Watch on YouTube</a></div>
  <p class="trailer-meta">YouTube</p>
  <div class="trailer-error" data-trailer-error hidden><b>Trailer currently unavailable.</b><span>This video could not be played right now.</span><span class="trailer-error-actions"><a class="quiet-link" data-trailer-watch href="{watch}" target="_blank" rel="noopener">Watch on YouTube</a><button type="button" class="trailer-retry" data-trailer-retry>Try again</button></span></div>
  <p class="trailer-fallback">If the embedded player is unavailable, <a href="{watch}" target="_blank" rel="noopener">watch the trailer on YouTube</a>.</p></div></div></section><div class="nm-body"><div class="nm-body-inner"><div class="nm-crumb"><div class="crumb"><a href="/">Home</a> / <a href="/movies/">Movies</a> / <a href="/movies/{esc(genre.lower().replace(" ", "-"))}/">{esc(genre)}</a> / {esc(title)}</div></div><div class="nm-brandline"><span class="nm-bn">BRY</span><span class="nm-bt">FILM</span></div>
    <h1>{esc(title)}</h1>
    <div class="badges"></div>
    <p class="lead">{esc(lead)}</p>
    <div class="hero-actions"><a class="cta nm-watch-now" href="#watch">Where to watch</a><a class="cta cta-ghost nm-trailer" href="#trailer">▶ Trailer</a></div>
    {f'<div class="nm-lang-row"><div class="nm-lang-tabs"><button type="button" class="nm-lang is-on">{esc(rec.get("language"))}</button></div></div>' if rec.get("language") else ""}
    {f'<div class="nm-cast-row-wrap"><div class="nm-cast-row">{cast_items}</div></div>' if cast_items else ""}
    <div class="nm-icon-actions"><button type="button" class="nm-icon-action" data-nm-my-list><svg viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg><span>My List</span></button><button type="button" class="nm-icon-action" data-nm-rate><svg viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg><span>Rate</span></button><button type="button" class="nm-icon-action nm-share" data-share-path="/movie/{slug}/" data-share-title="{esc(title)}"><svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg><span>Share</span></button></div>
    <div class="nm-tabs"><div class="nm-tabbar"><button type="button" class="nm-tab is-on" data-nm-tab="ml">More Like This</button><button type="button" class="nm-tab" data-nm-tab="md">More Details</button></div><div class="nm-panel is-on" id="nm-ml">{('<div class="tp-loved-list">' + loved + "</div>") if loved else '<p class="nm-detail-empty">More titles coming soon.</p>'}</div><div class="nm-panel" id="nm-md"><div class="nm-details-list">{rows_html}</div></div></div>
    <div class="nm-editorial"><section class="body"><article class="prose">
      {about}
      {watch_block(rec)}
      <section class="tp-next"><h2>Keep exploring</h2><p>Stay on BRYME — these are related pages, not download buttons.</p><div class="tp-next-links"><a href="/movies/{esc(genre.lower().replace(" ", "-"))}/">More {esc(genre)} movies</a><a href="/year/{year}/">{year} index</a><a href="/articles/">BRYME guides</a></div></section>
    </article>
    <aside class="aside"><h2>Details</h2><dl>
      <div><dt>Title</dt><dd>{esc(title)}</dd></div>
      <div><dt>Type</dt><dd>Movie</dd></div>
      <div><dt>Year</dt><dd>{year}</dd></div>
      <div><dt>Genre</dt><dd>{esc(", ".join(genres))}</dd></div>
      {f"<div><dt>Director</dt><dd>{esc('; '.join(dirs))}</dd></div>" if dirs else ""}
      {f"<div><dt>Cast</dt><dd>{esc('; '.join(cast))}</dd></div>" if cast else ""}
      {f"<div><dt>Runtime</dt><dd>{esc(rec['runtime'])}</dd></div>" if rec.get("runtime") else ""}
    </dl>{source}</aside>
    </section></div></div></div></div></main>"""


def apply_page(rec):
    path = os.path.join(ROOT, "movie", rec["slug"], "index.html")
    if not os.path.isfile(path):
        print("MISSING", rec["slug"])
        return False
    html = open(path, encoding="utf-8").read()
    # keep one clean document: cut any duplicated trailing html
    html = re.split(r"</html>", html, maxsplit=1)[0] + "</html>"
    title = f"{rec['title']} ({rec['year']}) | Cast, Trailer & Where to Watch | BRYME"
    meta = clip(
        f"{rec['title']} ({rec['year']}): official trailer, billed cast, story, and how to find a legal copy. BRYME does not host the film."
    )
    url = f"{SITE}/movie/{rec['slug']}/"
    thumb = f"https://i.ytimg.com/vi/{rec['youtubeId']}/hqdefault.jpg"
    html = re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", html, count=1, flags=re.S)
    html = re.sub(
        r'<meta name="description" content="[^"]*"',
        f'<meta name="description" content="{esc(meta)}"',
        html,
        count=1,
    )
    html = re.sub(r'<meta name="robots" content="[^"]*"\s*/?>', "", html)
    html = re.sub(
        r'<link rel="canonical" href="[^"]*"\s*/?>',
        f'<link rel="canonical" href="{url}">',
        html,
        count=1,
    )
    html = re.sub(
        r'<meta property="og:title" content="[^"]*"',
        f'<meta property="og:title" content="{esc(title)}"',
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
        r'<meta property="og:url" content="[^"]*"',
        f'<meta property="og:url" content="{url}"',
        html,
        count=1,
    )
    html = re.sub(
        r'<meta property="og:image" content="[^"]*"',
        f'<meta property="og:image" content="{thumb}"',
        html,
        count=1,
    )
    html = re.sub(
        r'<meta name="twitter:title" content="[^"]*"',
        f'<meta name="twitter:title" content="{esc(title)}"',
        html,
        count=1,
    )
    html = re.sub(
        r'<meta name="twitter:description" content="[^"]*"',
        f'<meta name="twitter:description" content="{esc(meta)}"',
        html,
        count=1,
    )
    dirs = [d.strip() for d in str(rec.get("director") or "").split(";") if d.strip()]
    ld = [
        {
            "@context": "https://schema.org",
            "@type": "Movie",
            "name": rec["title"],
            "description": rec["description"],
            "dateCreated": str(rec["year"]),
            "genre": rec.get("genre") or "Film",
            "image": thumb,
            "url": url,
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Movies", "item": SITE + "/movies/"},
                {"@type": "ListItem", "position": 3, "name": rec["title"], "item": url},
            ],
        },

    ]
    if rec.get("country"):
        ld[0]["countryOfOrigin"] = rec["country"]
    if rec.get("language"):
        ld[0]["inLanguage"] = rec["language"]
    if dirs:
        ld[0]["director"] = [{"@type": "Person", "name": d} for d in dirs]
    if rec.get("cast"):
        ld[0]["actor"] = [{"@type": "Person", "name": n} for n in rec["cast"][:8]]
    ld_tag = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>"
    if "application/ld+json" in html:
        html = re.sub(
            r'<script type="application/ld\+json">.*?</script>',
            ld_tag,
            html,
            count=1,
            flags=re.S,
        )
    else:
        html = html.replace("</head>", ld_tag + "</head>", 1)
    i, j = html.find("<main"), html.find("</main>")
    if i < 0 or j < 0:
        print("NO MAIN", rec["slug"])
        return False
    html = html[:i] + build_main(rec) + html[j + len("</main>") :]
    open(path, "w", encoding="utf-8").write(html)
    return True


def patch_catalogue(item):
    slug = item["slug"]
    d = exists(slug)
    if not d:
        print("NO CATALOGUE PAGE", slug)
        return False
    path = os.path.join(ROOT, d, slug, "index.html")
    html = open(path, encoding="utf-8").read()
    orig = html
    cast = item.get("cast") or []
    if cast and "nm-cast-item" not in html:
        items = "".join(
            f'<div class="nm-cast-item"><span class="nm-avatar">{esc(initials(n))}</span><b>{esc(n)}</b></div>'
            for n in cast[:8]
        )
        row = f'<div class="nm-cast-row-wrap"><div class="nm-cast-row">{items}</div></div>'
        html = html.replace('<div class="nm-icon-actions">', row + '<div class="nm-icon-actions">', 1)
    # details panel
    if cast and "nm-detail-label\">Cast<" not in html and "nm-details-list" in html:
        row = (
            '<div class="nm-detail-row"><div class="nm-detail-label">Cast</div>'
            f'<div class="nm-detail-value">{esc(", ".join(cast[:10]))}</div></div>'
        )
        if item.get("director") and "nm-detail-label\">Director<" not in html:
            row = (
                '<div class="nm-detail-row"><div class="nm-detail-label">Director</div>'
                f'<div class="nm-detail-value">{esc(item["director"])}</div></div>'
            ) + row
        html = html.replace('<div class="nm-details-list">', '<div class="nm-details-list">' + row, 1)
    if html != orig:
        open(path, "w", encoding="utf-8").write(html)
        return True
    return False


def persist(found):
    movies = json.load(open(os.path.join(ROOT, "data", "movies.json")))
    by = {m["slug"]: m for m in movies}
    for rec in found["titles"]:
        if rec["slug"] in by:
            m = by[rec["slug"]]
            if not m.get("cast"):
                m["cast"] = rec["cast"]
            if not m.get("director"):
                m["director"] = rec["director"]
            if not m.get("runtime"):
                m["runtime"] = rec.get("runtime")
            continue
        movies.append(
            {
                "id": rec["slug"],
                "title": rec["title"],
                "slug": rec["slug"],
                "description": rec["description"],
                "year": rec["year"],
                "genre": rec.get("genre") or "Film",
                "country": rec.get("country"),
                "language": rec.get("language"),
                "poster": f"https://i.ytimg.com/vi/{rec['youtubeId']}/hqdefault.jpg",
                "backdrop": None,
                "trailer": f"https://www.youtube.com/watch?v={rec['youtubeId']}",
                "youtubeId": rec["youtubeId"],
                "cast": rec.get("cast") or [],
                "director": rec.get("director"),
                "runtime": rec.get("runtime"),
                "rating": None,
                "status": "published",
                "createdAt": None,
                "updatedAt": "2026-08-22",
                "legacyType": "movie",
                "typeDir": "movie",
                "teaser": rec["description"],
                "facts": [],
                "watchLinks": [],
                "genres": rec.get("genres") or [],
                "typeLabel": "Movie",
                "trending": False,
                "popular": False,
                "editorPick": False,
                "isFeatured": False,
                "isNewRelease": False,
                "trailers": [
                    {
                        "videoId": rec["youtubeId"],
                        "type": "official-trailer",
                        "title": "Official Trailer",
                        "source": "YouTube",
                        "verified": True,
                        "status": "verified",
                    }
                ],
                "trailerType": "official-trailer",
                "trailerVerified": True,
                "castSource": {
                    "name": "Wikipedia",
                    "url": rec.get("wikipedia"),
                    "field": "infobox starring",
                    "retrieved": "2026-08-22",
                },
            }
        )
    for item in found["catalogueCast"]:
        if item["slug"] in by:
            m = by[item["slug"]]
            if not m.get("cast"):
                m["cast"] = item["cast"]
            if not m.get("director"):
                m["director"] = item["director"]
            if not m.get("runtime"):
                m["runtime"] = item.get("runtime")
    json.dump(movies, open(os.path.join(ROOT, "data", "movies.json"), "w"), ensure_ascii=False, indent=2)
    overlay_path = os.path.join(ROOT, "content", "title-metadata.json")
    overlay = json.load(open(overlay_path))
    for rec in found["titles"] + found["catalogueCast"]:
        slug = rec["slug"]
        cur = overlay.get(slug) or {}
        cur.setdefault("title", rec.get("title"))
        cur.setdefault("year", rec.get("year"))
        if rec.get("director") and not cur.get("director"):
            cur["director"] = rec["director"]
        if rec.get("cast") and not cur.get("cast"):
            cur["cast"] = rec["cast"]
        if rec.get("runtime") and not cur.get("runtime"):
            cur["runtime"] = rec["runtime"]
        if rec.get("wikipedia"):
            cur.setdefault("source", {"name": "Wikipedia", "url": rec["wikipedia"], "retrieved": "2026-08-22"})
            cur.setdefault(
                "castSource",
                {"name": "Wikipedia", "url": rec["wikipedia"], "field": "infobox starring", "retrieved": "2026-08-22"},
            )
        overlay[slug] = cur
    json.dump(overlay, open(overlay_path, "w"), ensure_ascii=False, indent=2)
    print("persisted movies.json + title-metadata.json")


def sitemap_add(urls):
    path = os.path.join(ROOT, "sitemap.xml")
    sm = open(path, encoding="utf-8").read()
    added = 0
    insert_at = sm.rfind("</urlset>")
    extra = ""
    for u in urls:
        loc = SITE + u
        if loc in sm:
            continue
        extra += f"  <url><loc>{loc}</loc></url>\n"
        added += 1
    if extra:
        sm = sm[:insert_at] + extra + sm[insert_at:]
        open(path, "w", encoding="utf-8").write(sm)
    print("sitemap added", added)


def sitemap_drop(urls):
    path = os.path.join(ROOT, "sitemap.xml")
    sm = open(path, encoding="utf-8").read()
    drop = {SITE + u for u in urls}
    kept, removed = [], 0
    for block in re.findall(r"  <url>.*?</url>\n?", sm, re.S):
        loc = re.search(r"<loc>([^<]+)</loc>", block)
        if loc and loc.group(1) in drop:
            removed += 1
            continue
        kept.append(block if block.endswith("\n") else block + "\n")
    head = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    open(path, "w", encoding="utf-8").write(head + "".join(kept) + "</urlset>\n")
    print("sitemap removed", removed)


def main():
    found = json.load(open(os.path.join(ROOT, "content", "found-movies.json")))
    n = 0
    for rec in found["titles"]:
        if apply_page(rec):
            n += 1
            print("upgraded", rec["slug"])
    print("upgraded extras", n)
    c = 0
    for item in found["catalogueCast"]:
        if patch_catalogue(item):
            c += 1
            print("cast patched", item["slug"])
    print("catalogue patches", c)
    dests = []
    for old, dest in found["redirects"]:
        slug = old.strip("/").split("/")[-1]
        path = os.path.join(ROOT, "movie", slug, "index.html")
        title = slug.replace("-", " ").title()
        dest_page = os.path.join(ROOT, dest.strip("/"), "index.html")
        if os.path.isfile(dest_page):
            h1 = re.search(r"<h1>(.*?)</h1>", open(dest_page, encoding="utf-8").read(), re.S)
            if h1:
                title = re.sub(r"<[^>]+>", "", h1.group(1)).strip()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf-8").write(stub(title, dest))
        dests.append(old)
        print("redirect", old, "->", dest)
        # _redirects append
    redir_path = os.path.join(ROOT, "_redirects")
    existing = open(redir_path, encoding="utf-8").read() if os.path.isfile(redir_path) else ""
    with open(redir_path, "a", encoding="utf-8") as f:
        if not existing.endswith("\n"):
            f.write("\n")
        f.write("# Same-title extra slugs → catalogue canonical\n")
        for old, dest in found["redirects"]:
            line = f"{old}  {dest}  301\n"
            if line not in existing:
                f.write(line)
    persist(found)
    sitemap_add([f"/movie/{r['slug']}/" for r in found["titles"]])
    sitemap_drop(dests)


if __name__ == "__main__":
    main()

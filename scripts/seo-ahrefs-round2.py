#!/usr/bin/env python3
"""Ahrefs round 2 — only remaining genuine issues. No fabricated schema."""
from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://bryme.onrender.com"
SKIP = {".git", "reports", "node_modules", "__pycache__", ".arena"}

# shorter slug → keep (official title slug)
DUP_MOVIES = {
    "baahubali": "baahubali-the-beginning",
    "everything-everywhere": "everything-everywhere-all-at-once",
    "grand-budapest": "the-grand-budapest-hotel",
    "half-yellow-sun": "half-of-a-yellow-sun",
    "living-in-bondage": "living-in-bondage-breaking-free",
    "mi-final-reckoning": "mission-impossible-the-final-reckoning",
    "spider-verse-2": "spider-man-across-spider-verse",
}

ANIME_TVSERIES = {
    "dandadan",
    "fullmetal-alchemist-brotherhood",
    "kuroko-basketball",
    "slam-dunk",
    "toradora",
    "violet-evergarden",
}


def walk_html():
    for p in ROOT.rglob("index.html"):
        if any(x in p.parts for x in SKIP):
            continue
        yield p


def page_url(p: Path) -> str:
    rel = "/" + str(p.parent.relative_to(ROOT)).replace("\\", "/")
    if rel.endswith("/."):
        rel = rel[:-2]
    if rel in ("/.", "/."):
        rel = ""
    return (rel if rel != "/" else "") + "/"


def patch_jsonld_anime(html: str) -> tuple[str, int]:
    n = 0

    def fix(m):
        nonlocal n
        raw = m.group(1)
        try:
            data = json.loads(raw)
        except Exception:
            return m.group(0)
        items = data if isinstance(data, list) else [data]
        changed = False
        for it in items:
            if isinstance(it, dict) and it.get("@type") == "Anime":
                it["@type"] = "TVSeries"
                n += 1
                changed = True
        if not changed:
            return m.group(0)
        out = items if isinstance(data, list) else items[0]
        return '<script type="application/ld+json">' + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "</script>"

    return re.sub(r'<script type="application/ld\+json">(.*?)</script>', fix, html, flags=re.S), n


def noindex_alias(html: str, keep_url: str) -> str:
    head_end = html.find("</head>")
    if head_end < 0:
        return html
    head = html[:head_end]
    if 'name="robots"' in head:
        head = re.sub(
            r'<meta name="robots" content="[^"]*">',
            '<meta name="robots" content="noindex,follow">',
            head,
            count=1,
        )
    else:
        head += '<meta name="robots" content="noindex,follow">'
    if 'rel="canonical"' in head:
        head = re.sub(
            r'<link rel="canonical" href="[^"]*">',
            f'<link rel="canonical" href="{keep_url}">',
            head,
            count=1,
        )
    else:
        head += f'<link rel="canonical" href="{keep_url}">'
    if 'property="og:url"' in head:
        head = re.sub(
            r'<meta property="og:url" content="[^"]*"',
            f'<meta property="og:url" content="{keep_url}"',
            head,
            count=1,
        )
    return head + html[head_end:]


def trim_desc(desc: str, limit: int = 155) -> str:
    desc = unescape(desc)
    if len(desc) <= limit:
        return desc
    return desc[:limit].rsplit(" ", 1)[0].rstrip(".,;:") + "…"


def set_meta_desc(html: str, new: str) -> str:
    html = re.sub(
        r'<meta name="description" content="[^"]*"',
        f'<meta name="description" content="{new}"',
        html,
        count=1,
    )
    html = re.sub(
        r'<meta property="og:description" content="[^"]*"',
        f'<meta property="og:description" content="{new}"',
        html,
        count=1,
    )
    html = re.sub(
        r'<meta name="twitter:description" content="[^"]*"',
        f'<meta name="twitter:description" content="{new}"',
        html,
        count=1,
    )
    return html


def year_desc(html: str, url: str) -> str | None:
    titles = re.findall(r"<h3>([^<]+)</h3>", html)
    if not titles:
        titles = re.findall(r"<b>([^<]+)</b>", html)
    n = len(titles)
    m = re.search(r"/(?:movies|series|anime|year)/(\d{4})/", url)
    year = m.group(1) if m else None
    if not year:
        return None
    kind = "titles"
    if "/series/" in url:
        kind = "series"
    elif "/anime/" in url:
        kind = "anime"
    elif "/movies/" in url or url.startswith("/year/"):
        kind = "movies"
    extra = ""
    if titles:
        shown = ", ".join(titles[:3])
        extra = f", including {shown}"
    if n:
        return f"Browse {n} {kind} from {year} in the BRYME catalogue{extra}."
    return f"Browse {kind} from {year} in the BRYME catalogue."


def rebuild_sitemap() -> int:
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
                continue
        urls.append(SITE + url)
    urls = sorted(set(urls))
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls)
        + "</urlset>\n"
    )
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")
    return len(urls)


def prune_news() -> int:
    path = ROOT / "news-sitemap.xml"
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8")
    # keep publication_date on or after 2026-08-22 (last two calendar days from 23 Aug)
    kept = []
    chunks = re.split(r"(?=<url>)", text)
    header = chunks[0]
    n_drop = 0
    body = []
    for ch in chunks[1:]:
        dm = re.search(r"<news:publication_date>([^<]+)</news:publication_date>", ch)
        if dm and dm.group(1) < "2026-08-22":
            n_drop += 1
            continue
        body.append(ch if ch.endswith("\n") else ch)
    if n_drop:
        # rebuild well-formed
        urls = re.findall(r"<url>.*?</url>", "".join(body), flags=re.S)
        out = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'
        )
        for u in urls:
            out += "  " + u.strip() + "\n"
        out += "</urlset>\n"
        path.write_text(out, encoding="utf-8")
    return n_drop


def fix_fill_stubs_template():
    p = ROOT / "scripts" / "fill-stubs.py"
    t = p.read_text(encoding="utf-8")
    orig = t
    t = t.replace("elif type_dir == 'anime': ld_type, label = 'Anime', 'ANIME'", "elif type_dir == 'anime': ld_type, label = 'TVSeries', 'ANIME'")
    t = t.replace("ld_type = 'TVSeries' if type_dir == 'series' else 'Anime' if type_dir == 'anime' else 'Movie'", "ld_type = 'TVSeries' if type_dir in ('series', 'anime') else 'Movie'")
    t = t.replace("it.get('@type') in ('Movie', 'TVSeries', 'Anime')", "it.get('@type') in ('Movie', 'TVSeries')")
    # do not emit VideoObject without uploadDate
    t = t.replace(
        "    if live_yt:\n        ld.append({'@context': 'https://schema.org', '@type': 'VideoObject',\n                   'name': f'{title} — Official Trailer', 'description': f'Official trailer for {title}.',\n                   'thumbnailUrl': yt_thumb(live_yt), 'embedUrl': f'https://www.youtube-nocookie.com/embed/{live_yt}',\n                   'publisher': {'@type': 'Organization', 'name': 'YouTube'}})",
        "    # VideoObject omitted unless a verified uploadDate exists (Google required field).",
    )
    if t != orig:
        p.write_text(t, encoding="utf-8")
        return True
    return False


def main():
    stats = {
        "anime_schema_fixed": 0,
        "dup_aliases_noindexed": 0,
        "internal_alias_rewrites": 0,
        "year_desc_updated": 0,
        "long_desc_trimmed": 0,
        "news_dropped": 0,
        "redirects_added": 0,
    }

    # 1. Anime @type on the six pages
    for slug in ANIME_TVSERIES:
        p = ROOT / "anime" / slug / "index.html"
        if not p.exists():
            continue
        html = p.read_text(encoding="utf-8")
        html2, n = patch_jsonld_anime(html)
        if n:
            p.write_text(html2, encoding="utf-8")
            stats["anime_schema_fixed"] += n

    # 2. Duplicate movie aliases
    redir_path = ROOT / "_redirects"
    redir = redir_path.read_text(encoding="utf-8") if redir_path.exists() else ""
    extra_redir = []
    for alias, keep in DUP_MOVIES.items():
        ap = ROOT / "movie" / alias / "index.html"
        if not ap.exists():
            continue
        html = ap.read_text(encoding="utf-8")
        keep_url = f"{SITE}/movie/{keep}/"
        html2 = noindex_alias(html, keep_url)
        if html2 != html:
            ap.write_text(html2, encoding="utf-8")
            stats["dup_aliases_noindexed"] += 1
        line = f"/movie/{alias}/  /movie/{keep}/  301\n"
        if line not in redir:
            extra_redir.append(line)

    if extra_redir:
        if redir and not redir.endswith("\n"):
            redir += "\n"
        redir_path.write_text(redir + "# Duplicate title slugs → canonical slug\n" + "".join(extra_redir), encoding="utf-8")
        stats["redirects_added"] = len(extra_redir)

    # rewrite internal hrefs to aliases (not the alias page itself)
    alias_hrefs = {f"/movie/{a}/": f"/movie/{k}/" for a, k in DUP_MOVIES.items()}
    for p in walk_html():
        # don't rewrite the alias file's own path mentions in crumbs unnecessarily — do rewrite nav links
        html = p.read_text(encoding="utf-8")
        orig = html
        for bad, good in alias_hrefs.items():
            if p.parent.name == bad.strip("/").split("/")[-1] and p.parent.parent.name == "movie":
                continue
            html = html.replace(f'href="{bad}"', f'href="{good}"')
        if html != orig:
            p.write_text(html, encoding="utf-8")
            stats["internal_alias_rewrites"] += 1

    # 3. Year / type-year short descriptions
    for p in walk_html():
        url = page_url(p)
        if not re.search(r"/(year|movies|series|anime)/\d{4}/", url):
            continue
        html = p.read_text(encoding="utf-8")
        if "noindex" in html[:4000]:
            continue
        dm = re.search(r'<meta name="description" content="([^"]*)"', html)
        if not dm or len(dm.group(1)) >= 70:
            continue
        new = year_desc(html, url)
        if new and new != dm.group(1):
            p.write_text(set_meta_desc(html, new.replace('"', "&quot;")), encoding="utf-8")
            stats["year_desc_updated"] += 1

    # 4. Three long money descriptions
    for rel in (
        "make-money/coding/index.html",
        "make-money/make-money-online-nigeria/index.html",
        "make-money/remote-work/index.html",
    ):
        p = ROOT / rel
        html = p.read_text(encoding="utf-8")
        dm = re.search(r'<meta name="description" content="([^"]*)"', html)
        if dm and len(dm.group(1)) > 160:
            p.write_text(set_meta_desc(html, trim_desc(dm.group(1))), encoding="utf-8")
            stats["long_desc_trimmed"] += 1

    stats["news_dropped"] = prune_news()
    stats["fill_stubs_template"] = fix_fill_stubs_template()
    stats["sitemap_urls"] = rebuild_sitemap()

    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()

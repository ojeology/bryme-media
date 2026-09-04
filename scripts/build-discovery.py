#!/usr/bin/env python3
"""Build robots, XML sitemaps and RSS from BRYME's explicit Search policy."""
from __future__ import annotations

import datetime as dt
import email.utils
import html
import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = str(json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))["siteUrl"]).rstrip("/")
POLICY = json.loads((ROOT / "content/index-allowlist.json").read_text(encoding="utf-8"))
ROUTES = list(dict.fromkeys(POLICY["routes"]))
REVIEWED = dt.date.fromisoformat(POLICY["reviewedAt"])
NEWS_POLICY = json.loads((ROOT / "content/news-allowlist.json").read_text(encoding="utf-8"))
NEWS_ROUTES = set(NEWS_POLICY["routes"])


def route_file(route: str) -> Path:
    return ROOT / ("index.html" if route == "/" else route.strip("/") + "/index.html")


def norm_path(value: object) -> str:
    if isinstance(value, dict):
        value = value.get("@id") or value.get("url") or ""
    if not isinstance(value, str) or not value:
        return ""
    p = re.sub(r"/+", "/", urlsplit(value).path or "/")
    return "/" if p == "/" else p.rstrip("/") + "/"


class MetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.in_title = False
        self.in_jsonld = False
        self.json_parts: list[str] = []
        self.json_blocks: list[str] = []
        self.description = ""
        self.robots = ""
        self.canonical = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag.lower() == "title":
            self.in_title = True
        elif tag.lower() == "meta":
            if a.get("name", "").lower() == "description":
                self.description = a.get("content", "").strip()
            elif a.get("name", "").lower() == "robots":
                self.robots = a.get("content", "").strip().lower()
        elif tag.lower() == "link" and a.get("rel", "").lower() == "canonical":
            self.canonical = a.get("href", "").strip()
        elif tag.lower() == "script" and a.get("type", "").lower() == "application/ld+json":
            self.in_jsonld = True
            self.json_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False
        elif tag.lower() == "script" and self.in_jsonld:
            self.in_jsonld = False
            self.json_blocks.append("".join(self.json_parts).strip())
            self.json_parts = []

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.in_jsonld:
            self.json_parts.append(data)

    @property
    def title(self) -> str:
        return re.sub(r"\s+", " ", "".join(self.title_parts)).strip()


def read_page(route: str) -> dict:
    path = route_file(route)
    if not path.is_file():
        raise RuntimeError(f"Allowlisted route has no HTML file: {route}")
    parser = MetadataParser()
    parser.feed(path.read_text(encoding="utf-8"))
    if "noindex" in parser.robots or "index" not in parser.robots:
        raise RuntimeError(f"Allowlisted route is not index,follow: {route} ({parser.robots!r})")
    if norm_path(parser.canonical) != norm_path(route):
        raise RuntimeError(f"Canonical mismatch for {route}: {parser.canonical!r}")
    entities: list[dict] = []
    for raw in parser.json_blocks:
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON-LD on {route}: {exc}") from exc
        for obj in value if isinstance(value, list) else [value]:
            if isinstance(obj, dict):
                entities.append(obj)
    article = None
    for obj in entities:
        if obj.get("@type") in {"Article", "NewsArticle", "BlogPosting"}:
            own = norm_path(obj.get("mainEntityOfPage") or obj.get("url"))
            if not own or own == norm_path(route):
                article = obj
                break
    published = str((article or {}).get("datePublished") or "")[:10]
    modified = str((article or {}).get("dateModified") or published or POLICY["reviewedAt"])[:10]
    for label, value in (("datePublished", published), ("dateModified", modified)):
        if value:
            try:
                parsed = dt.date.fromisoformat(value)
            except ValueError as exc:
                raise RuntimeError(f"Invalid {label} on {route}: {value!r}") from exc
            if parsed > REVIEWED:
                raise RuntimeError(f"Future {label} on {route}: {value}")
    return {
        "route": route,
        "url": SITE + route,
        "title": parser.title.removesuffix(" | BRYME").strip(),
        "description": parser.description,
        "article": article,
        "published": published,
        "modified": modified,
    }


def xml_escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def rss_date(value: str) -> str:
    day = dt.date.fromisoformat(value)
    stamp = dt.datetime.combine(day, dt.time(12, 0), tzinfo=dt.timezone.utc)
    return email.utils.format_datetime(stamp)


def build() -> None:
    if len(ROUTES) != len(set(ROUTES)):
        raise RuntimeError("Duplicate routes in index allowlist")
    pages = [read_page(route) for route in ROUTES]

    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += "\n".join(
        f"  <url><loc>{xml_escape(page['url'])}</loc><lastmod>{xml_escape(page['modified'])}</lastmod></url>"
        for page in pages
    )
    sitemap += "\n</urlset>\n"
    (ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    cutoff = REVIEWED - dt.timedelta(days=2)
    by_route = {page["route"]: page for page in pages}
    unknown_news = NEWS_ROUTES - set(by_route)
    if unknown_news:
        raise RuntimeError(f"News routes are not Search-allowlisted: {sorted(unknown_news)}")
    news_pages = []
    for route in sorted(NEWS_ROUTES):
        page = by_route[route]
        if not page["article"] or not page["published"]:
            raise RuntimeError(f"News route lacks Article/datePublished: {route}")
        date = dt.date.fromisoformat(page["published"])
        if cutoff <= date <= REVIEWED:
            news_pages.append(page)
    news = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'
    news += "\n".join(
        "  <url><loc>{url}</loc><news:news><news:publication><news:name>BRYME</news:name>"
        "<news:language>en</news:language></news:publication><news:publication_date>{date}</news:publication_date>"
        "<news:title>{title}</news:title></news:news></url>".format(
            url=xml_escape(page["url"]), date=xml_escape(page["published"]), title=xml_escape(page["title"])
        ) for page in news_pages[:1000]
    )
    news += "\n</urlset>\n"
    (ROOT / "news-sitemap.xml").write_text(news, encoding="utf-8")

    feed_pages = [page for page in pages if page["article"] and page["published"]]
    feed_pages.sort(key=lambda page: (page["published"], page["route"] == "/jobs/verified-2026-09-04/"), reverse=True)
    rss = '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>\n'
    rss += f"  <title>BRYME — verified work, practical tech and original guides</title><link>{SITE}/</link>"
    rss += "<description>Primary-source jobs, practical technology and original entertainment guides from BRYME.</description>"
    rss += f'<language>en-ng</language><lastBuildDate>{rss_date(POLICY["reviewedAt"])}</lastBuildDate>'
    rss += f'<atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>\n'
    for page in feed_pages[:30]:
        rss += "  <item><title>{title}</title><link>{url}</link><guid isPermaLink=\"true\">{url}</guid>".format(
            title=xml_escape(page["title"]), url=xml_escape(page["url"])
        )
        rss += f"<pubDate>{rss_date(page['published'])}</pubDate><description>{xml_escape(page['description'])}</description></item>\n"
    rss += "</channel></rss>\n"
    (ROOT / "feed.xml").write_text(rss, encoding="utf-8")

    robots = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /api/\n"
        "Disallow: /admin/\n"
        "Disallow: /telegram/\n\n"
        f"Sitemap: {SITE}/sitemap.xml\n"
        f"Sitemap: {SITE}/news-sitemap.xml\n"
    )
    (ROOT / "robots.txt").write_text(robots, encoding="utf-8")

    for name in ("sitemap.xml", "news-sitemap.xml", "feed.xml"):
        ET.parse(ROOT / name)
    print(json.dumps({"sitemap_urls": len(pages), "news_urls": len(news_pages), "rss_items": min(30, len(feed_pages))}, indent=2))


if __name__ == "__main__":
    build()

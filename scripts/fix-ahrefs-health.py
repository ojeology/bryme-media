#!/usr/bin/env python3
"""Fix Ahrefs health: sitemap, short/long descriptions, OG/Twitter, orphans."""
from __future__ import annotations

import json
import re
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = "https://bryme.onrender.com"
SKIP = {"server", "miniapp", "legacy", "docs", "scripts", "node_modules", ".git"}
CARD = "https://bryme.onrender.com/assets/bryme-card.png"


class Head(HTMLParser):
    def __init__(self):
        super().__init__()
        self.desc = None
        self.canon = None
        self.robots = None
        self.title = ""
        self.og = {}
        self.tw = {}
        self._t = False

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "meta":
            name = (d.get("name") or d.get("property") or "").lower()
            c = d.get("content") or ""
            if name == "description":
                self.desc = c
            elif name == "robots":
                self.robots = c
            elif name.startswith("og:"):
                self.og[name] = c
            elif name.startswith("twitter:"):
                self.tw[name] = c
        elif tag == "link" and d.get("rel") == "canonical":
            self.canon = d.get("href")
        elif tag == "title":
            self._t = True

    def handle_data(self, data):
        if self._t:
            self.title += data

    def handle_endtag(self, tag):
        if tag == "title":
            self._t = False


def html_files():
    for p in ROOT.rglob("*.html"):
        if set(p.relative_to(ROOT).parts) & SKIP:
            continue
        yield p


def url_for(p: Path) -> str:
    rel = p.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[:-10]
    return "/" + rel


def parse(t: str) -> Head:
    h = Head()
    try:
        h.feed(t)
    except Exception:
        pass
    return h


def clip(s: str, n: int = 155) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) <= n:
        return s
    s = s[: n - 1]
    if " " in s:
        s = s.rsplit(" ", 1)[0]
    return s.rstrip(".,;:") + "…"


def pad(desc: str, title: str, url: str) -> str:
    d = re.sub(r"\s+", " ", (desc or "").strip())
    if 120 <= len(d) <= 160:
        return d
    if len(d) > 160:
        return clip(d, 155)
    tail = {
        "/sports/": " Sourced football scores, tables and fixtures on BRYME. We do not invent results.",
        "/make-money/": " Checked against official pages. BRYME does not promise you will be hired or paid.",
        "/tech/": " Practical tools in plain language. We check official pages, not rumour posts.",
        "/movie/": " Trailer, story and legal viewing options on BRYME. We do not host the film.",
        "/series/": " Trailer, story and legal viewing options on BRYME. We do not host the show.",
        "/anime/": " Trailer, story and legal viewing options on BRYME. We do not host the title.",
        "/article/": " A BRYME editorial guide. Discovery only — we do not host films or shows.",
    }
    extra = " Discover movies, sports, money guides and tech on BRYME."
    for prefix, text in tail.items():
        if url.startswith(prefix):
            extra = text
            break
    if not d:
        d = re.sub(r"\s*\|\s*BRYME.*$", "", title or "BRYME").strip()
    out = d
    if extra.strip() not in out:
        out = (out + extra).strip()
    if len(out) < 120:
        out = (out + " Updated 2026.").strip()
    return clip(out, 155) if len(out) > 160 else out


def set_meta(html: str, name: str, content: str, attr: str = "name") -> str:
    """Insert or replace a meta tag in <head>."""
    content = content.replace('"', "&quot;")
    pat = re.compile(
        rf'<meta\s+[^>]*{attr}=["\']{re.escape(name)}["\'][^>]*>',
        re.I,
    )
    tag = f'<meta {attr}="{name}" content="{content}">'
    if pat.search(html):
        return pat.sub(tag, html, count=1)
    # also property/name swapped
    if "</title>" in html:
        return html.replace("</title>", "</title>\n" + tag, 1)
    return html


def ensure_social(html: str, title: str, desc: str, url: str) -> str:
    h = parse(html)
    page_url = h.canon or (HOST + url)
    img = h.og.get("og:image") or CARD
    title_plain = re.sub(r"\s*\|\s*BRYME.*$", "", title).strip() or title
    if not h.og.get("og:title"):
        html = set_meta(html, "og:title", title_plain, "property")
    if not h.og.get("og:description"):
        html = set_meta(html, "og:description", desc, "property")
    if not h.og.get("og:url"):
        html = set_meta(html, "og:url", page_url, "property")
    if not h.og.get("og:image"):
        html = set_meta(html, "og:image", img, "property")
    if not h.og.get("og:type"):
        html = set_meta(html, "og:type", "website", "property")
    if not h.tw.get("twitter:card"):
        html = set_meta(html, "twitter:card", "summary_large_image")
    if not h.tw.get("twitter:title"):
        html = set_meta(html, "twitter:title", title_plain)
    if not h.tw.get("twitter:description"):
        html = set_meta(html, "twitter:description", desc)
    if not h.tw.get("twitter:image"):
        html = set_meta(html, "twitter:image", img)
    return html


def replace_desc(html: str, new: str) -> str:
    new_esc = new.replace('"', "&quot;")
    pat = re.compile(
        r'(<meta\s+[^>]*name=["\']description["\'][^>]*content=["\'])(.*?)(["\'][^>]*>)',
        re.I | re.S,
    )
    if pat.search(html):
        return pat.sub(rf"\g<1>{new_esc}\3", html, count=1)
    pat2 = re.compile(
        r'(<meta\s+[^>]*content=["\'])(.*?)(["\'][^>]*name=["\']description["\'][^>]*>)',
        re.I | re.S,
    )
    if pat2.search(html):
        return pat2.sub(rf"\g<1>{new_esc}\3", html, count=1)
    return set_meta(html, "description", new)


def bake_money_lists() -> None:
    mapping = {
        ROOT / "make-money" / "writing" / "index.html": ROOT / "content" / "money-writing.json",
        ROOT / "make-money" / "remote-work" / "index.html": ROOT / "content" / "money-remote.json",
        ROOT / "make-money" / "coding" / "index.html": ROOT / "content" / "money-coding.json",
    }
    for page, js in mapping.items():
        items = json.loads(js.read_text())["items"]
        rows = []
        for it in items:
            href = it.get("url") or "#"
            name = escape(it.get("name") or "")
            title = escape(it.get("title") or "")
            pay = escape(it.get("pay") or "")
            ext = ' target="_blank" rel="nofollow noopener"' if href.startswith("http") else ""
            rows.append(
                f'<a class="mm-row" href="{escape(href)}"{ext}><b>{name}</b>'
                f"<span>{title}</span>"
                + (f"<em>{pay}</em>" if pay else "")
                + "</a>"
            )
        html = page.read_text(encoding="utf-8")
        html = html.replace(
            '<div id="mm-list"><p class="sp-empty">Loading…</p></div>',
            '<div id="mm-list">\n' + "\n".join(rows) + "\n</div>",
        )
        page.write_text(html, encoding="utf-8")
        print("baked", page.relative_to(ROOT), len(rows))


def link_sports() -> None:
    p = ROOT / "sports" / "index.html"
    t = p.read_text(encoding="utf-8")
    extra = """
    <p class="sp-kick">Leagues</p>
    <div class="sp-more">
      <a href="/sports/premier-league/">Premier League</a>
      <a href="/sports/la-liga/">La Liga</a>
      <a href="/sports/serie-a/">Serie A</a>
      <a href="/sports/bundesliga/">Bundesliga</a>
      <a href="/sports/ligue-1/">Ligue 1</a>
      <a href="/sports/champions-league/">Champions League</a>
    </div>
    <p class="sp-kick">More</p>
    <div class="sp-more">
      <a href="/sports/football/">Football</a>
      <a href="/sports/history/">History</a>
      <a href="/sports/records/">Records</a>
      <a href="/sports/international/">International</a>
      <a href="/sports/clubs/">Clubs</a>
      <a href="/sports/players/">Players</a>
    </div>
"""
    # recent results
    feed = json.loads((ROOT / "content" / "sports-feed.json").read_text())
    links = []
    for lg, res in (feed.get("results") or {}).items():
        for key, val in list(res.items())[:8]:
            if not val or val.get("homeScore") is None:
                continue
            href = f"/sports/{lg}/matches/{key}/"
            links.append(f'<a class="sp-story" href="{href}"><b>{escape(key.replace("-", " "))}</b><span>FT {val.get("homeScore")}–{val.get("awayScore")}</span></a>')
    if links:
        extra += '    <p class="sp-kick">Recent results</p>\n    ' + "\n    ".join(links[:24]) + "\n"
    if 'href="/sports/premier-league/"' not in t:
        t = t.replace(
            '    <p class="sp-kick">News</p>',
            extra + '    <p class="sp-kick">News</p>',
            1,
        )
        p.write_text(t, encoding="utf-8")
        print("sports hub links added", len(links[:24]))


def link_tech() -> None:
    p = ROOT / "tech" / "index.html"
    t = p.read_text(encoding="utf-8")
    if 'href="/tech/ai-tools/"' in t:
        return
    block = """
  <p class="sp-kick">Topics</p>
  <div class="sp-more">
    <a href="/tech/ai-tools/">AI tools</a>
    <a href="/tech/app-alternatives/">App alternatives</a>
    <a href="/tech/hosting/">Hosting</a>
    <a href="/tech/android-apps/">Android</a>
    <a href="/tech/cybersecurity/">Security</a>
    <a href="/tech/useful-websites/">Useful sites</a>
  </div>
"""
    t = t.replace("  <p class=\"sp-kick\">AI</p>", block + "  <p class=\"sp-kick\">AI</p>", 1)
    p.write_text(t, encoding="utf-8")
    print("tech topics linked")


def fix_sitemap() -> None:
    p = ROOT / "sitemap.xml"
    t = p.read_text(encoding="utf-8")
    t2 = re.sub(r"\s*<url><loc>https://bryme.onrender.com/sports/comics/</loc>.*?</url>", "", t)
    if t2 != t:
        p.write_text(t2, encoding="utf-8")
        print("removed comics from sitemap")
    else:
        print("comics already out of sitemap" if "/sports/comics/" not in t else "comics still in sitemap (pattern miss)")


def fix_robots() -> None:
    p = ROOT / "robots.txt"
    p.write_text(
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /miniapp/\n"
        "Disallow: /404.html\n"
        "Disallow: /server/\n"
        "\n"
        "User-agent: Googlebot\n"
        "Allow: /\n"
        "\n"
        "User-agent: AdsBot-Google\n"
        "Allow: /\n"
        "\n"
        "Sitemap: https://bryme.onrender.com/sitemap.xml\n"
        "Sitemap: https://bryme.onrender.com/news-sitemap.xml\n",
        encoding="utf-8",
    )
    print("robots.txt refreshed")


def fix_meta() -> None:
    n_desc = n_og = 0
    for p in html_files():
        t = p.read_text(encoding="utf-8")
        h = parse(t)
        url = url_for(p)
        ni = h.robots and "noindex" in h.robots.lower()
        if ni:
            continue
        desc = h.desc or ""
        title = (h.title or "").strip()
        new = pad(desc, title, url)
        changed = False
        if new != desc:
            t = replace_desc(t, new)
            desc = new
            changed = True
            n_desc += 1
        t2 = ensure_social(t, title, desc, url)
        if t2 != t:
            n_og += 1
            t = t2
            changed = True
        if changed:
            p.write_text(t, encoding="utf-8")
    print("descriptions updated", n_desc, "social tags", n_og)


def main() -> None:
    fix_robots()
    fix_sitemap()
    bake_money_lists()
    link_sports()
    link_tech()
    fix_meta()


if __name__ == "__main__":
    main()

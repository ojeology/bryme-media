#!/usr/bin/env python3
"""Contain empty title stubs that were published without synopsis, cast, or details.

Does not delete URLs. Sets a self-canonical, noindex,follow, and drops them from
the sitemap so they cannot keep pointing at the homepage.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://bryme.onrender.com"
LIST = os.path.join(ROOT, "reports", "empty-title-stubs.txt")


def main():
    urls = [ln.strip() for ln in open(LIST, encoding="utf-8") if ln.strip().startswith("/")]
    n = 0
    for url in urls:
        rel = url.strip("/") + "/index.html"
        fp = os.path.join(ROOT, rel)
        if not os.path.isfile(fp):
            print("MISSING", url)
            continue
        html = open(fp, encoding="utf-8").read()
        orig = html
        self = SITE + url
        html = re.sub(
            r'<link rel="canonical" href="[^"]*"\s*/?>',
            f'<link rel="canonical" href="{self}">',
            html,
            count=1,
        )
        if 'name="robots"' in html:
            html = re.sub(
                r'<meta name="robots" content="[^"]*"\s*/?>',
                '<meta name="robots" content="noindex,follow">',
                html,
                count=1,
            )
        else:
            html = html.replace(
                '<link rel="canonical"',
                '<meta name="robots" content="noindex,follow"><link rel="canonical"',
                1,
            )
        html = re.sub(
            r'<meta property="og:url" content="[^"]*"',
            f'<meta property="og:url" content="{self}"',
            html,
            count=1,
        )
        if html != orig:
            open(fp, "w", encoding="utf-8").write(html)
            n += 1
            print("contained", url)

    sm_path = os.path.join(ROOT, "sitemap.xml")
    sm = open(sm_path, encoding="utf-8").read()
    drop = {SITE + u for u in urls}
    kept, removed = [], 0
    for block in re.findall(r"  <url>.*?</url>\n?", sm, re.S):
        loc = re.search(r"<loc>([^<]+)</loc>", block)
        if loc and loc.group(1) in drop:
            removed += 1
            continue
        kept.append(block if block.endswith("\n") else block + "\n")
    head = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    open(sm_path, "w", encoding="utf-8").write(head + "".join(kept) + "</urlset>\n")
    print(f"updated {n} stubs; removed {removed} sitemap URLs")


if __name__ == "__main__":
    main()

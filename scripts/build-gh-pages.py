#!/usr/bin/env python3
"""Build a GitHub-Pages-safe copy of the BRYME Media archive into dist/.

GitHub Pages serves this project site under a URL prefix
(https://ojeology.github.io/bryme-media/), but the archive was written for a
domain root: internal links, stylesheets, fetch() paths and canonical URLs are
absolute ("/assets/...", "https://bryme-media.onrender.com/..."). This script
copies the static tree and rewrites those references for the Pages prefix so
the preview works. The source tree is never modified.

Indexing safeguards (house rule: staging must never become an accidental
Google index):
  * every copied page keeps — or gets — <meta name="robots" content="noindex,follow">
    and the script FAILS if any published .html lacks noindex;
  * dist/robots.txt disallows everything (secondary signal only: crawlers read
    the host-level ojeology.github.io/robots.txt, so the meta tag is the real
    protection);
  * no sitemap is published (the source sitemap.xml is an empty urlset and is
    deliberately not copied);
  * canonical/og URLs are repointed from the dead bryme-media.onrender.com
    host to the Pages preview URL, so nothing references a 404 host;
  * stale search-engine verification token files are not published.

Run:  python3 scripts/build-gh-pages.py
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
BASE = "/bryme-media"  # project-page path prefix; matches the repo name
PAGES_ORIGIN = "https://ojeology.github.io"
DEAD_HOST = "https://bryme-media.onrender.com"

# Directories that are part of the published static site.
COPY_DIRS = [
    "about", "anime", "article", "articles", "assets", "author", "channels",
    "contact", "content", "copyright", "data", "disclaimer", "editorial-policy",
    "entertainment", "genre", "genres", "legacy", "movie", "movies", "now",
    "privacy", "search", "series", "sports", "terms", "topic", "topics",
    "trailers", "trending", "year", "years",
]
# Root files that are part of the published static site.
COPY_FILES = ["404.html", "index.html", "favicon.ico", "manifest.webmanifest", "feed.xml"]

# Deliberately NOT published: server/, scripts/, docs/, content sources for the
# node server, package.json, render.yaml, README.md, sitemap.xml,
# news-sitemap.xml, sw.js (a service worker on a shared github.io host would
# only add stale-cache risk to a QA preview), and the stale verification
# token files (google*.html, yandex*.html) which belong to the live domain.

# Path roots that may appear at the start of an absolute reference. Anything
# starting with "/<one of these>" gets the Pages prefix. A bare "/" is left
# alone except in the webmanifest (start_url/scope), so generic JS string
# logic is not corrupted.
ROOTS = sorted(set(COPY_DIRS) | {"sw.js", "favicon.ico", "manifest.webmanifest", "feed.xml", "404.html"})
ROOTS_ALT = "|".join(re.escape(r) for r in ROOTS)

# "/assets/...", '/movie/...', "/sw.js" — quoted absolute paths in JS/JSON/CSS-ish text
RE_QUOTED_PATH = re.compile(r"""(["'])/(%s)(?=["'/?.#])""" % ROOTS_ALT)
# href="/...", src="/...", action="/...", data-src="/...", data-share-path="/..."
RE_ATTR_PATH = re.compile(r"""\b(href|src|data-src|data-poster|data-href|data-share-path|data-url|poster|action)\s*=\s*"/(%s)(?=["/?.#])""" % ROOTS_ALT)
# content="/..." on meta tags (e.g. og:image given as a path)
RE_META_CONTENT_PATH = re.compile(r"""\bcontent\s*=\s*"/(%s)(?=["/?.#])""" % ROOTS_ALT)
# url(/...) or url('/...') inside CSS or inline styles — the quote is preserved
RE_CSS_URL = re.compile(r"""url\(\s*(['"])?/(%s)(?=['")/?.#])""" % ROOTS_ALT)
# @import "/..." or @import '/...'
RE_CSS_IMPORT = re.compile(r"""@import\s+(['"])/(%s)(?=['"/?.#])""" % ROOTS_ALT)

RE_DEAD_HOST = re.compile(re.escape(DEAD_HOST) + r"(?=[/\"'?)\s<]|$)")
RE_DEAD_HOST_BARE = re.compile(r"(?<![\w.])bryme-media\.onrender\.com")

RE_NOINDEX = re.compile(r"name=[\"']robots[\"'][^>]*noindex|noindex[^>]*name=[\"']robots[\"']", re.I)
RE_HEAD_OPEN = re.compile(r"<head[^>]*>", re.I)

TEXT_SUFFIXES = {".html", ".htm", ".css", ".js", ".json", ".xml", ".webmanifest", ".svg", ".txt", ".webmanifest"}

stats = {"copied": 0, "rewritten": 0, "host_fixes": 0, "noindex_injected": 0, "html": 0}


def prefix_paths(text: str) -> tuple[str, int]:
    """Add the Pages prefix to absolute internal references."""
    n = 0
    # quoted paths (JS/JSON)
    text, c = RE_QUOTED_PATH.subn(lambda m: f'{m.group(1)}{BASE}/{m.group(2)}', text)
    n += c
    # html attributes
    text, c = RE_ATTR_PATH.subn(lambda m: f'{m.group(1)}="{BASE}/{m.group(2)}', text)
    n += c
    # meta content paths
    text, c = RE_META_CONTENT_PATH.subn(lambda m: f'content="{BASE}/{m.group(1)}', text)
    n += c
    # css url() and @import (quote preserved)
    text, c = RE_CSS_URL.subn(lambda m: f'url({m.group(1) or ""}{BASE}/{m.group(2)}', text)
    n += c
    text, c = RE_CSS_IMPORT.subn(lambda m: f'@import {m.group(1)}{BASE}/{m.group(2)}', text)
    n += c
    return text, n


def fix_host(text: str) -> tuple[str, int]:
    """Repoint the dead onrender canonical host at the Pages preview URL."""
    text, c1 = RE_DEAD_HOST.subn(PAGES_ORIGIN + BASE, text)
    text, c2 = RE_DEAD_HOST_BARE.subn("ojeology.github.io" + BASE, text)
    return text, c1 + c2


def fix_manifest(text: str) -> str:
    """start_url/scope/id must live under the prefix or the PWA scope is wrong."""
    for key in ("start_url", "scope", "id"):
        text = re.sub(r'("%s"\s*:\s*")/(")' % key, rf"\1{BASE}/\2", text)
    return text


def ensure_noindex(text: str, path: Path) -> str:
    if RE_NOINDEX.search(text):
        return text
    m = RE_HEAD_OPEN.search(text)
    if not m:
        print(f"FATAL: {path} has no <head> and no noindex — cannot publish safely", file=sys.stderr)
        sys.exit(1)
    stats["noindex_injected"] += 1
    return text[: m.end()] + '<meta name="robots" content="noindex,follow">' + text[m.end():]


def transform(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() in TEXT_SUFFIXES:
        text = src.read_text(encoding="utf-8", errors="surrogateescape")
        text, n = prefix_paths(text)
        text, h = fix_host(text)
        if src.name == "manifest.webmanifest":
            text = fix_manifest(text)
        if src.suffix.lower() in (".html", ".htm"):
            stats["html"] += 1
            text = ensure_noindex(text, src)
        dst.write_text(text, encoding="utf-8", errors="surrogateescape")
        if n or h:
            stats["rewritten"] += 1
        stats["host_fixes"] += h
    else:
        shutil.copy2(src, dst)
    stats["copied"] += 1


def main() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    for d in COPY_DIRS:
        src_dir = ROOT / d
        if not src_dir.is_dir():
            continue
        for f in sorted(src_dir.rglob("*")):
            if f.is_file():
                transform(f, DIST / d / f.relative_to(src_dir))

    for f in COPY_FILES:
        src_f = ROOT / f
        if src_f.is_file():
            transform(src_f, DIST / f)

    # secondary indexing safeguard (see module docstring re: host-level robots)
    (DIST / "robots.txt").write_text(
        "# BRYME Media staging preview — not for search indexing.\n"
        "# Crawlers read the host-level robots.txt (ojeology.github.io/robots.txt),\n"
        "# so this file is a secondary signal only. The binding protection is the\n"
        '# <meta name="robots" content="noindex,follow"> tag on every page,\n'
        "# which scripts/build-gh-pages.py enforces at build time.\n"
        "User-agent: *\nDisallow: /\n",
        encoding="utf-8",
    )

    # Hard gate: nothing publishes without noindex.
    missing = [p for p in DIST.rglob("*.html") if not RE_NOINDEX.search(p.read_text(encoding="utf-8", errors="surrogateescape"))]
    if missing:
        print(f"FATAL: {len(missing)} pages lack noindex, e.g. {missing[:3]}", file=sys.stderr)
        sys.exit(1)

    print(
        f"gh-pages build: {stats['copied']} files copied, {stats['html']} html pages "
        f"(all noindex), {stats['rewritten']} files path-rewritten, "
        f"{stats['host_fixes']} dead-host references repointed, "
        f"{stats['noindex_injected']} noindex tags injected -> dist/"
    )


if __name__ == "__main__":
    main()

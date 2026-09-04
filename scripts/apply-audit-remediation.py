#!/usr/bin/env python3
"""Apply the controlled 2026-09-04 audit containment pass.

Unlike the historical foundation generator, this script does not invent or
regenerate content. It makes narrow, idempotent policy/UX transformations:
explicit index allowlisting, honest controls, source-first navigation,
structured-data containment, and visible sports/archive warnings.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ALLOW = set(json.loads((ROOT / "content/index-allowlist.json").read_text(encoding="utf-8"))["routes"])
STAMP = "2026-09-04"

LEGACY_HEADER = '''<a class="skip-link" href="#main">Skip to content</a><header class="top"><div class="shell"><a class="brand" href="/" aria-label="BRYME home">BRY<b>ME</b></a><nav class="topnav" aria-label="Primary"><a href="/">Home</a><a href="/jobs/">Jobs</a><a href="/make-money/">Opportunities</a><a href="/tech/">Practical Tech</a><a href="/articles/">Watch &amp; Read</a><a class="nav-search" href="/about/">About</a></nav><div class="top-tools"><a class="header-search" href="/jobs/" aria-label="Verified jobs">Jobs</a></div></div></header>'''
LEGACY_MOBILE = '''<nav class="mobile-nav" aria-label="Primary mobile"><a href="/"><span class="mn-ico">⌂</span>Home</a><a href="/jobs/"><span class="mn-ico">✓</span>Jobs</a><a href="/make-money/"><span class="mn-ico">↗</span>Work</a><a href="/tech/"><span class="mn-ico">◈</span>Tech</a><a href="/articles/"><span class="mn-ico">◇</span>Read</a><a href="/about/"><span class="mn-ico">i</span>About</a></nav>'''
LEGACY_FOOTER = '''<footer class="footer"><div class="shell"><div class="footer-grid"><div class="footer-brand"><a class="brand" href="/">BRY<b>ME</b></a><p>Verified opportunities and practical technology for Nigerians and Africa-based applicants. Primary sources and human check dates come first.</p></div><div class="footer-col"><h4>Use BRYME</h4><a href="/jobs/">Verified jobs</a><a href="/make-money/">Opportunities</a><a href="/tech/">Practical tech</a><a href="/articles/">Watch &amp; Read</a></div><div class="footer-col"><h4>Trust</h4><a href="/jobs/methodology/">Verification method</a><a href="/editorial-policy/">Editorial policy</a><a href="/corrections/">Corrections</a><a href="/contact/">Contact</a></div><div class="footer-col"><h4>Legal</h4><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a><a href="/disclaimer/">Disclaimer</a><a href="/copyright/">Copyright</a></div></div><p class="footer-note">BRYME does not accept job applications or guarantee availability, interviews, tasks or earnings.</p><small>© 2026 BRYME · Third-party advertising and analytics are disabled during the quality rebuild.</small></div></footer>'''
SPORTS_NOTICE = '''<aside class="integrity-notice" role="note"><b>Sports data paused.</b> This archived page is excluded from Search while BRYME repairs its data pipeline and verifies source rights. Do not rely on it for a current score, table or fixture.</aside>'''
CSS_PATCH = r'''
/* AUDIT-REMEDIATION-2026-09-04: honesty, navigation and accessibility */
body:has(main.tp-page) .top{display:block!important}
body:has(main.tp-page){padding-top:0!important}
.skip-link{position:fixed;z-index:1000;top:8px;left:8px;transform:translateY(-150%);padding:10px 14px;border-radius:8px;background:#c7f36b;color:#07100d;font-weight:900}
.skip-link:focus{transform:none}
.desk-bar{display:none!important}
.nm-match,.nm-hd,.tile-rating,[data-nm-my-list],[data-nm-rate]{display:none!important}
.topnav{font-size:13.5px}
.mobile-nav a{font-size:11.5px;min-height:52px}
.integrity-notice{position:relative;z-index:5;margin:12px auto;padding:13px 18px;max-width:1180px;border:1px solid rgba(255,190,100,.38);border-radius:8px;background:#281b0d;color:#f3d7ad;font-size:13px;line-height:1.5}
.integrity-notice b{color:#ffd08a}
@media(max-width:760px){.integrity-notice{margin:8px 12px}.topnav{display:none}}
'''

SCRIPT_RE = re.compile(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.I | re.S)


def route_for(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[:-10]
    return "/" + rel


def first_git_date(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    try:
        out = subprocess.check_output(
            ["git", "log", "--diff-filter=A", "--follow", "--format=%ad", "--date=short", "--", rel],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL,
        ).strip().splitlines()
        return out[-1] if out else STAMP
    except Exception:
        return STAMP


def ensure_robots(text: str, indexable: bool) -> str:
    desired = "index,follow" if indexable else "noindex,follow"
    pattern = re.compile(r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*["\']\s*/?>', re.I)
    tag = f'<meta name="robots" content="{desired}">'
    if pattern.search(text):
        return pattern.sub(tag, text, count=1)
    head = re.search(r'<head\b[^>]*>', text, re.I)
    if head:
        return text[:head.end()] + tag + text[head.end():]
    return text


def patch_article_object(obj: dict, path: Path, text: str) -> None:
    if obj.get("@type") != "Article":
        return
    visible = re.search(r'Last updated\s*(?:</?[^>]+>\s*)?(\d{4}-\d{2}-\d{2})', text, re.I)
    modified = visible.group(1) if visible else obj.get("dateModified") or STAMP
    published = obj.get("datePublished") or first_git_date(path)
    obj["datePublished"] = published
    obj["dateModified"] = modified
    if not obj.get("author"):
        if re.search(r'By\s+Ibrahim\s+Sodiq', text, re.I):
            obj["author"] = {"@type": "Person", "name": "Ibrahim Sodiq", "url": "https://bryme.onrender.com/author/ibrahim-sodiq/"}
        else:
            obj["author"] = {"@type": "Organization", "name": "BRYME Editorial Desk", "url": "https://bryme.onrender.com/editorial-policy/"}
    if not obj.get("publisher"):
        obj["publisher"] = {"@type": "Organization", "name": "BRYME", "url": "https://bryme.onrender.com/"}


def walk_patch(obj: object, path: Path, text: str, title_route: bool) -> object | None:
    if isinstance(obj, list):
        kept = []
        for item in obj:
            patched = walk_patch(item, path, text, title_route)
            if patched is not None:
                kept.append(patched)
        return kept
    if not isinstance(obj, dict):
        return obj
    typ = obj.get("@type")
    if title_route and typ in {"VideoObject", "Movie", "TVSeries", "Article"}:
        return None
    if typ in {"Movie", "TVSeries"} and isinstance(obj.get("sameAs"), str) and "youtu" in obj["sameAs"]:
        obj.pop("sameAs", None)
    if typ == "Article":
        patch_article_object(obj, path, text)
    if "@graph" in obj and isinstance(obj["@graph"], list):
        obj["@graph"] = [x for x in (walk_patch(x, path, text, title_route) for x in obj["@graph"]) if x is not None]
    return obj


def patch_schema(text: str, path: Path, route: str) -> str:
    title_route = bool(re.match(r'^/(movie|series|anime)/[^/]+/$', route))
    if not title_route and route not in ALLOW:
        return text

    def repl(match: re.Match[str]) -> str:
        raw = match.group(1).strip()
        try:
            data = json.loads(raw)
        except Exception:
            return match.group(0)
        data = walk_patch(data, path, text, title_route)
        if data in (None, [], {}):
            return ""
        return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>"

    return SCRIPT_RE.sub(repl, text)


def normalized_schema_path(value: object) -> str:
    if isinstance(value, dict):
        value = value.get("@id") or value.get("url") or ""
    if not isinstance(value, str) or not value:
        return ""
    path = urlsplit(value).path or "/"
    path = re.sub(r'/+', '/', path)
    return "/" if path == "/" else path.rstrip("/") + "/"


def clean_allowlisted_schema(text: str, route: str) -> str:
    """Drop copied/mismatched JSON-LD and singleton duplicates.

    A historical enhancement pass injected another page's Article, breadcrumb
    and FAQ blocks into four URLs. Structured data must describe visible content
    on the current canonical route, not merely be syntactically valid.
    """
    if route not in ALLOW:
        return text
    visible_markup = SCRIPT_RE.sub("", text)
    visible_text = re.sub(r'<[^>]+>', ' ', html.unescape(visible_markup))
    visible_text = re.sub(r'\s+', ' ', visible_text).casefold()
    expected = normalized_schema_path(route)
    seen: set[str] = set()

    def repl(match: re.Match[str]) -> str:
        try:
            data = json.loads(match.group(1).strip())
        except Exception:
            return match.group(0)
        was_list = isinstance(data, list)
        entities = data if was_list else [data]
        kept: list[object] = []
        for entity in entities:
            if not isinstance(entity, dict):
                kept.append(entity)
                continue
            typ = entity.get("@type")
            group = "Article" if typ in {"Article", "NewsArticle", "BlogPosting"} else typ
            invalid = False
            if group == "Article":
                own = normalized_schema_path(entity.get("mainEntityOfPage") or entity.get("url"))
                invalid = bool(own and own != expected)
            elif typ == "BreadcrumbList":
                items = entity.get("itemListElement") or []
                last = items[-1] if items and isinstance(items[-1], dict) else {}
                own = normalized_schema_path(last.get("item"))
                invalid = bool(own and own != expected)
            elif typ == "FAQPage":
                questions = [
                    str(q.get("name") or "").strip().casefold()
                    for q in (entity.get("mainEntity") or []) if isinstance(q, dict)
                ]
                invalid = bool(questions and any(q and q not in visible_text for q in questions))
            if invalid:
                continue
            if group in {"Article", "BreadcrumbList", "FAQPage"}:
                if group in seen:
                    continue
                seen.add(str(group))
            kept.append(entity)
        if not kept:
            return ""
        out: object = kept if was_list or len(kept) != 1 else kept[0]
        return '<script type="application/ld+json">' + json.dumps(out, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>"

    return SCRIPT_RE.sub(repl, text)


def patch_visible_article_date(text: str, route: str) -> str:
    if route not in ALLOW:
        return text
    published = ""
    expected = normalized_schema_path(route)
    for match in SCRIPT_RE.finditer(text):
        try:
            data = json.loads(match.group(1).strip())
        except Exception:
            continue
        for entity in data if isinstance(data, list) else [data]:
            if not isinstance(entity, dict) or entity.get("@type") not in {"Article", "NewsArticle", "BlogPosting"}:
                continue
            own = normalized_schema_path(entity.get("mainEntityOfPage") or entity.get("url"))
            if own and own != expected:
                continue
            published = str(entity.get("datePublished") or "")[:10]
            break
        if published:
            break
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', published):
        return text
    visible_markup = SCRIPT_RE.sub("", text)
    visible_text = re.sub(r'<[^>]+>', ' ', visible_markup)
    if published in html.unescape(visible_text):
        return text
    # Preserve each template's metadata row when it exists.
    text2, n = re.subn(
        r'(<div\b[^>]*class="[^"]*\barticle-meta\b[^"]*"[^>]*>)',
        rf'\1<span>Published {published}</span>', text, count=1, flags=re.I,
    )
    if n:
        return text2
    text2, n = re.subn(
        r'(<p\b[^>]*class="[^"]*\bchecked-line\b[^"]*"[^>]*>)',
        rf'\1Published {published} · ', text, count=1, flags=re.I,
    )
    if n:
        return text2
    return re.sub(
        r'(</h1>)',
        rf'\1<p class="article-byline"><time datetime="{published}">Published {published}</time></p>',
        text, count=1, flags=re.I,
    )


def patch_visible_article_byline(text: str, route: str) -> str:
    if not route.startswith("/article/") or re.search(r'By\s+Ibrahim\s+Sodiq', text, re.I):
        return text
    # Ignore JSON-LD when checking whether the byline is visibly present.
    visible_markup = SCRIPT_RE.sub("", text)
    if re.search(r'By\s+BRYME\s+Editorial\s+Desk', visible_markup, re.I):
        return text
    # Most article templates expose this exact metadata sequence.
    text2, n = re.subn(r'(Editorial guide\s*·\s*Last updated)', r'By BRYME Editorial Desk · \1', text, count=1, flags=re.I)
    if n:
        return text2
    # Fallback: add a transparent byline directly after the first H1.
    return re.sub(r'(</h1>)', r'\1<p class="article-byline">By BRYME Editorial Desk</p>', text, count=1, flags=re.I)


def patch_allowlisted_performance(text: str, route: str) -> str:
    """Keep Search-eligible editorial pages lean and useful without client JS."""
    if route not in ALLOW:
        return text
    text = text.replace('href="/assets/site.css"', 'href="/assets/content-v2.css"')
    text = re.sub(r'<link\b[^>]*rel=["\']manifest["\'][^>]*>', '', text, flags=re.I)
    text = re.sub(r'<script>\s*window\.BRYME_BASE\s*=\s*[\'\"][^<]*?</script>', '', text, flags=re.I)
    text = re.sub(r'<script\s+src="/assets/site-app\.js"[^>]*></script>', '', text, flags=re.I)
    text = re.sub(r'<button\b[^>]*\bshare-action\b[^>]*>.*?</button>', '', text, flags=re.I | re.S)
    return text


def patch_common(text: str, path: Path, route: str) -> str:
    # No tracking tags or speculative preconnections in static HTML.
    text = re.sub(r'<script\b[^>]*src=["\']/assets/analytics\.js["\'][^>]*>\s*</script>', '', text, flags=re.I)
    text = re.sub(r'<link\b[^>]*rel=["\']preconnect["\'][^>]*youtu[^>]*>', '', text, flags=re.I)
    text = patch_allowlisted_performance(text, route)

    # Replace old global navigation and remove misleading provider navigation.
    text = re.sub(r'(?:<a\b[^>]*class="skip-link"[^>]*>.*?</a>)?<header class="top">.*?</header>', LEGACY_HEADER, text, count=1, flags=re.I | re.S)
    text = re.sub(r'<main(?![^>]*\bid=)([^>]*)>', r'<main id="main"\1>', text, count=1, flags=re.I)
    text = re.sub(r'<nav class="desk-bar".*?</nav>', '', text, flags=re.I | re.S)
    text = re.sub(r'<nav class="mobile-nav".*?</nav>', LEGACY_MOBILE, text, count=1, flags=re.I | re.S)
    text = re.sub(r'<footer class="footer">.*?</footer>', LEGACY_FOOTER, text, count=1, flags=re.I | re.S)

    # Remove non-functional and unsupported title-page UI.
    text = re.sub(r'\s+onclick="history\.back\(\);return false"', '', text, flags=re.I)
    text = re.sub(r'<button\b[^>]*data-nm-(?:my-list|rate)[^>]*>.*?</button>', '', text, flags=re.I | re.S)
    text = re.sub(r'<a\b[^>]*class="[^"]*\bnm-trailer\b[^"]*"[^>]*>.*?</a>', '', text, flags=re.I | re.S)
    text = re.sub(r'(<a\b[^>]*class="[^"]*\bnm-watch-now\b[^"]*"[^>]*>).*?(</a>)', r'\1▶ Play trailer\2', text, flags=re.I | re.S)
    text = re.sub(r'<[^>]+class="[^"]*\b(?:nm-match|nm-hd|tile-rating)\b[^"]*"[^>]*>.*?</[^>]+>', '', text, flags=re.I | re.S)
    # Generic provider chips looked like availability choices despite the fine
    # print. Keep only title-specific, clearly labelled official search links.
    text = re.sub(r'<div\s+class="svc-row"[^>]*>.*?</div>', '', text, flags=re.I | re.S)

    text = patch_schema(text, path, route)
    text = clean_allowlisted_schema(text, route)
    text = patch_visible_article_date(text, route)
    text = patch_visible_article_byline(text, route)
    text = ensure_robots(text, route in ALLOW)

    if route.startswith("/sports/") and "Sports data paused." not in text:
        body = re.search(r'<body\b[^>]*>', text, re.I)
        if body:
            text = text[:body.end()] + SPORTS_NOTICE + text[body.end():]
    return text


def retired_page(label: str, route: str) -> str:
    safe = html.escape(label)
    return f'''<!doctype html><html lang="en-NG"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Legacy collection retired | BRYME</title><meta name="description" content="This legacy BRYME collection was retired because it did not represent verified provider availability."><meta name="robots" content="noindex,follow"><link rel="canonical" href="https://bryme.onrender.com{route}"><link rel="stylesheet" href="/assets/bryme-v2.css"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"></head><body><main id="main"><div class="wrap"><section class="page-hero"><p class="kicker"><span class="kicker-dot"></span>Collection retired</p><h1>{safe} was not a verified availability page.</h1><p>BRYME removed this legacy collection from Search because it grouped titles by type or genre rather than confirmed, region-specific provider data.</p><div class="actions"><a class="btn" href="/articles/">Read original entertainment guides</a><a class="btn secondary" href="/">Return home</a></div></section></div></main></body></html>'''


def paused_search_page() -> str:
    return '''<!doctype html><html lang="en-NG"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Browse BRYME | Focused sections</title><meta name="description" content="Browse BRYME verified jobs, opportunities, practical technology and original entertainment editorial."><meta name="robots" content="noindex,follow"><link rel="canonical" href="https://bryme.onrender.com/search/"><link rel="stylesheet" href="/assets/bryme-v2.css"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"></head><body><main id="main"><div class="wrap"><section class="page-hero"><p class="kicker"><span class="kicker-dot"></span>Browse BRYME</p><h1>Search is being rebuilt around the useful parts.</h1><p>The old search shipped the entire catalogue into one page. Use the focused sections while a lighter search index is built.</p></section><section class="section"><div class="card-grid"><a class="path-card" href="/jobs/"><span class="card-num">JOBS</span><h3>Verified roles</h3><p>Exact employer and ATS links.</p><span class="card-link">Open jobs →</span></a><a class="path-card" href="/tech/"><span class="card-num">TECH</span><h3>Practical guides</h3><p>Task-first technology help.</p><span class="card-link">Open tech →</span></a><a class="path-card" href="/articles/"><span class="card-num">READ</span><h3>Entertainment editorial</h3><p>Original recommendations and opinion.</p><span class="card-link">Open articles →</span></a></div></section></div></main></body></html>'''


def apply(check: bool = False) -> Counter:
    stats: Counter = Counter()
    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts or "reports" in path.parts:
            continue
        route = route_for(path)
        before = path.read_text(encoding="utf-8", errors="replace")
        after = patch_common(before, path, route)
        if before != after:
            stats["html_changed"] += 1
            if not check:
                path.write_text(after, encoding="utf-8")
    labels = {
        "trending": "Trending", "latest": "Latest releases", "netflix": "Netflix",
        "prime": "Prime Video", "sony": "SonyLIV", "jio": "JioHotstar",
        "crunchyroll": "Crunchyroll", "kids": "Kids", "mx": "MX Player",
    }
    for slug, label in labels.items():
        path = ROOT / "channels" / slug / "index.html"
        out = retired_page(label, f"/channels/{slug}/")
        if not path.exists() or path.read_text(encoding="utf-8", errors="replace") != out:
            stats["channel_pages_retired"] += 1
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(out, encoding="utf-8")
    search_path = ROOT / "search/index.html"
    search_out = paused_search_page()
    if search_path.read_text(encoding="utf-8", errors="replace") != search_out:
        stats["search_page_replaced"] += 1
        if not check:
            search_path.write_text(search_out, encoding="utf-8")
    css = ROOT / "assets/site.css"
    css_text = css.read_text(encoding="utf-8")
    marker = "/* AUDIT-REMEDIATION-2026-09-04:"
    base_css = css_text.split(marker, 1)[0].rstrip()
    desired_css = base_css + "\n" + CSS_PATCH.strip() + "\n"
    if css_text != desired_css:
        stats["css_patch_updated"] += 1
        if not check:
            css.write_text(desired_css, encoding="utf-8")
    if not check:
        report = {"appliedAt": STAMP, "indexAllowlistCount": len(ALLOW), **stats}
        (ROOT / "reports/remediation-apply-summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="report whether rerunning would change files")
    args = parser.parse_args()
    result = apply(check=args.check)
    print(json.dumps(dict(result), indent=2))
    if args.check and result:
        raise SystemExit(1)

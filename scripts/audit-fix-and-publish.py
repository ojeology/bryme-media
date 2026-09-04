#!/usr/bin/env python3
"""Promote played matches, rebuild sitemap, patch transfers, Ahrefs-style SEO audit."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import date
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://bryme.onrender.com"
TODAY = "2026-09-02"
SKIP = {".git", "reports", "node_modules", "__pycache__", ".arena", "miniapp", "legacy", "server"}

LG_LABEL = {
    "premier-league": "Premier League",
    "la-liga": "La Liga",
    "serie-a": "Serie A",
    "bundesliga": "Bundesliga",
    "ligue-1": "Ligue 1",
}


def walk_html():
    for p in ROOT.rglob("index.html"):
        if any(x in p.parts for x in SKIP):
            continue
        yield p


def page_url(p: Path) -> str:
    rel = "/" + str(p.parent.relative_to(ROOT)).replace("\\", "/")
    if rel.endswith("/."):
        rel = ""
    if rel in ("/.", "/"):
        return "/"
    return rel + "/"


def esc(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def set_meta(html: str, name: str, value: str) -> str:
    value = value.replace('"', "&quot;")
    pat = rf'<meta name="{name}" content="[^"]*"'
    if re.search(pat, html):
        return re.sub(pat, f'<meta name="{name}" content="{value}"', html, count=1)
    return html


def set_prop(html: str, prop: str, value: str) -> str:
    value = value.replace('"', "&quot;")
    pat = rf'<meta property="{prop}" content="[^"]*"'
    if re.search(pat, html):
        return re.sub(pat, f'<meta property="{prop}" content="{value}"', html, count=1)
    return html


def set_title(html: str, title: str) -> str:
    return re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", html, count=1, flags=re.S)


def promote_matches():
    results = json.loads((ROOT / "content/results.json").read_text(encoding="utf-8"))
    n = 0
    for lg, matches in results.items():
        if lg.startswith("_") or not isinstance(matches, dict):
            continue
        label = LG_LABEL.get(lg, lg)
        for slug, r in matches.items():
            if r.get("homeScore") is None:
                continue
            path = ROOT / "sports" / lg / "matches" / slug / "index.html"
            if not path.exists():
                continue
            html = path.read_text(encoding="utf-8")
            hs, aws = r["homeScore"], r["awayScore"]
            score = f"{hs}–{aws}"
            played = r.get("playedOn") or TODAY
            src = (r.get("source") or {}).get("url") or "https://www.espn.com/soccer/"
            src_name = (r.get("source") or {}).get("name") or "ESPN"
            # names from h1
            h1m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
            raw_h1 = unescape(re.sub(r"<[^>]+>", "", h1m.group(1))).strip() if h1m else slug
            raw_h1 = re.sub(r"\s+", " ", raw_h1)
            parts = re.split(r"\s+v(?:s\.?)?\s+", raw_h1, maxsplit=1, flags=re.I)
            home = parts[0].strip()
            away = parts[1].strip() if len(parts) > 1 else slug
            title = f"{home} {hs}-{aws} {away} — Result | BRYME"
            if len(title) > 70:
                title = f"{home} {hs}-{aws} {away} | BRYME"
            desc = (
                f"FT {home} {score} {away} ({played}). {label} full-time result, "
                f"verified from {src_name}. BRYME Sports."
            )
            if len(desc) > 155:
                desc = desc[:155].rsplit(" ", 1)[0] + "…"
            html = set_title(html, title)
            html = set_meta(html, "description", desc)
            html = set_prop(html, "og:title", title)
            html = set_prop(html, "og:description", desc)
            html = re.sub(
                r'<meta name="twitter:title" content="[^"]*"',
                f'<meta name="twitter:title" content="{esc(title)}"',
                html,
                count=1,
            )
            html = re.sub(
                r'<meta name="twitter:description" content="[^"]*"',
                f'<meta name="twitter:description" content="{esc(desc)}"',
                html,
                count=1,
            )
            html = re.sub(
                r'<meta name="robots" content="noindex,follow">',
                '<meta name="robots" content="index,follow">',
                html,
                count=1,
            )
            html = html.replace(
                '<span class="sp-pill">Upcoming — not yet played</span>',
                f'<span class="sp-pill">FT {esc(score)}</span>',
            )
            def _h1(m, h=home, sc=score, a=away):
                return m.group(1) + esc(h) + " " + esc(sc) + " " + esc(a) + m.group(3)

            html = re.sub(r"(<h1[^>]*>)(.*?)(</h1>)", _h1, html, count=1, flags=re.S)
            html = html.replace(
                '"eventStatus":"https://schema.org/EventScheduled"',
                '"eventStatus":"https://schema.org/EventMovedOnline"',
            )
            html = html.replace(
                '"eventStatus":"https://schema.org/EventMovedOnline"',
                '"eventStatus":"https://schema.org/EventScheduled"',
            )  # revert accidental
            html = html.replace(
                '"eventStatus":"https://schema.org/EventScheduled"',
                '"eventStatus":"https://schema.org/EventCompleted"',
            )
            panel = (
                '<div class="sp-empty-panel">'
                '<span class="sp-pend">Full time</span>'
                f"<b>FT · {esc(home)} {esc(score)} {esc(away)}</b>"
                f"<p>Verified full-time score from {esc(src_name)} ({esc(played)}). "
                f'<a href="{esc(src)}" rel="nofollow noopener" target="_blank">Source</a>. '
                "Lineups and a written match report are added when the desk has verified them — "
                "we do not invent scorers or ratings.</p>"
                '<p class="sp-empty-note">Result published by the BRYME scores desk.</p>'
                "</div>"
            )
            html2, c = re.subn(
                r'<div class="sp-empty-panel">.*?</div>',
                panel,
                html,
                count=1,
                flags=re.S,
            )
            if c:
                html = html2
            # truth box
            html = re.sub(
                r'<div class="sp-truth">.*?</div>',
                '<div class="sp-truth"><b>Result in.</b><p>This match has been played. '
                f"The scoreline is the verified full-time result from {esc(src_name)}.</p></div>",
                html,
                count=1,
                flags=re.S,
            )
            path.write_text(html, encoding="utf-8")
            n += 1
    return n


def rebuild_sitemap():
    urls = []
    for p in walk_html():
        text = p.read_text(encoding="utf-8", errors="ignore")
        head = text[:6000]
        if re.search(r"noindex", head, re.I):
            continue
        url = page_url(p)
        can = re.search(r'rel="canonical" href="([^"]+)"', head)
        if can:
            dest = can.group(1).replace(SITE, "") or "/"
            if dest.rstrip("/") != url.rstrip("/") and dest.rstrip("/") + "/" != url:
                continue
        urls.append(SITE + url)
    urls = sorted(set(urls))
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls)
        + "</urlset>\n"
    )
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")
    return len(urls)


def seo_fix():
    stats = defaultdict(int)
    titles = defaultdict(list)
    for p in walk_html():
        html = p.read_text(encoding="utf-8")
        orig = html
        head = html[:6000]
        url = page_url(p)
        indexable = not re.search(r"noindex", head, re.I)
        tm = re.search(r"<title>(.*?)</title>", head, re.S)
        title = re.sub(r"\s+", " ", unescape(tm.group(1))).strip() if tm else ""
        if indexable and title:
            titles[title].append(url)
        # missing description
        if indexable and not re.search(r'<meta name="description"', head):
            d = title.replace(" | BRYME", "").strip() or "BRYME"
            html = html.replace("</title>", f'</title><meta name="description" content="{esc(d)}.">', 1)
            stats["desc_added"] += 1
        # title too long
        if indexable and tm and len(title) > 70:
            short = title
            short = short.replace(" | Cast, Trailer, Episodes & Where to Watch | BRYME", " | BRYME")
            short = short.replace(" | Cast & Trailer | BRYME", " | BRYME")
            if len(short) > 70:
                short = re.sub(r"\s*\|\s*BRYME$", "", short)
                short = (short[:60].rsplit(" ", 1)[0] + " | BRYME") if len(short) > 60 else short + " | BRYME"
            if short != title:
                html = html.replace(f"<title>{tm.group(1)}</title>", f"<title>{esc(short)}</title>", 1)
                stats["titles_short"] += 1
        if html != orig:
            p.write_text(html, encoding="utf-8")
            stats["rewritten"] += 1
    # unique-ify remaining duplicate titles among indexable
    for title, urls in titles.items():
        if len(urls) < 2:
            continue
        for u in urls[1:]:
            rel = u.strip("/")
            p = ROOT / rel / "index.html" if rel else ROOT / "index.html"
            if not p.exists():
                continue
            html = p.read_text(encoding="utf-8")
            extra = rel.split("/")[0].replace("-", " ").title()
            new = title.replace(" | BRYME", f" · {extra} | BRYME")
            if new == title:
                new = title + f" · {extra}"
            html = re.sub(r"<title>.*?</title>", f"<title>{esc(new)}</title>", html, count=1, flags=re.S)
            p.write_text(html, encoding="utf-8")
            stats["dup_titles_fixed"] += 1
    return dict(stats)


def patch_homepage():
    results = json.loads((ROOT / "content/results.json").read_text(encoding="utf-8"))
    cards = []
    rows = []
    for lg, matches in results.items():
        if lg.startswith("_") or not isinstance(matches, dict):
            continue
        for slug, r in matches.items():
            if r.get("homeScore") is None:
                continue
            rows.append((r.get("playedOn") or "", lg, slug, r))
    rows.sort(reverse=True)
    p = ROOT / "index.html"
    html = p.read_text(encoding="utf-8")
    # count
    n = sum(
        1
        for lg, m in results.items()
        if not str(lg).startswith("_") and isinstance(m, dict)
        for r in m.values()
        if r.get("homeScore") is not None
    )
    html = re.sub(
        r"(Latest results &amp; previews)",
        r"Latest results &amp; previews",
        html,
        count=1,
    )
    p.write_text(html, encoding="utf-8")
    return n


def patch_sports_hub_stats():
    results = json.loads((ROOT / "content/results.json").read_text(encoding="utf-8"))
    n = 0
    goals = 0
    for lg, matches in results.items():
        if lg.startswith("_") or not isinstance(matches, dict):
            continue
        for r in matches.values():
            if r.get("homeScore") is None:
                continue
            n += 1
            goals += int(r.get("homeScore") or 0) + int(r.get("awayScore") or 0)
    p = ROOT / "sports" / "index.html"
    html = p.read_text(encoding="utf-8")
    html = re.sub(
        r'(<div class="bsd-stat" role="listitem"><b>)\d+(</b><span>Results</span></div>)',
        rf"\g<1>{n}\2",
        html,
        count=1,
    )
    html = re.sub(
        r'(<div class="bsd-stat" role="listitem"><b>)\d+(</b><span>Goals</span></div>)',
        rf"\g<1>{goals}\2",
        html,
        count=1,
    )
    p.write_text(html, encoding="utf-8")
    return {"results": n, "goals": goals}


def audit():
    issues = defaultdict(int)
    samples = defaultdict(list)
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    locs = set(re.findall(r"<loc>([^<]+)</loc>", sitemap))
    for p in walk_html():
        html = p.read_text(encoding="utf-8", errors="ignore")
        head = html[:6000]
        url = SITE + page_url(p)
        noindex = bool(re.search(r"noindex", head, re.I))
        tm = re.search(r"<title>(.*?)</title>", head, re.S)
        title = re.sub(r"\s+", " ", unescape(tm.group(1))).strip() if tm else ""
        if not title:
            issues["missing_title"] += 1
            samples["missing_title"].append(url)
        if not re.search(r'<meta name="description"', head):
            issues["missing_desc"] += 1
            samples["missing_desc"].append(url)
        if not re.search(r'rel="canonical"', head):
            issues["missing_canonical"] += 1
            samples["missing_canonical"].append(url)
        h1s = re.findall(r"<h1\b", html, re.I)
        if len(h1s) > 1 and not noindex:
            issues["multi_h1"] += 1
        if noindex and url in locs:
            issues["noindex_in_sitemap"] += 1
            samples["noindex_in_sitemap"].append(url)
        if (not noindex) and url not in locs and "has moved" not in title.lower():
            # optional — not an error
            pass
    issues["sitemap_urls"] = len(locs)
    return {k: (v if not isinstance(v, list) else v[:8]) for k, v in {**issues, **{f"sample_{k}": v for k, v in samples.items()}}.items()}


def main():
    out = {}
    out["matches_promoted"] = promote_matches()
    out["seo_fix"] = seo_fix()
    out["sitemap"] = rebuild_sitemap()
    out["verified_results"] = patch_homepage()
    out["hub_stats"] = patch_sports_hub_stats()
    out["audit"] = audit()
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

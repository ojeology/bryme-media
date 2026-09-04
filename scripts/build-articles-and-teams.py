#!/usr/bin/env python3
"""One Articles page + team pages with played scores. Comics removed."""
from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPORTS = ROOT / "sports"

LEAGUES = {
    "premier-league": "Premier League",
    "la-liga": "La Liga",
    "serie-a": "Serie A",
    "bundesliga": "Bundesliga",
    "ligue-1": "Ligue 1",
}

SKIP_DIRS = {
    "articles", "premier-league", "la-liga", "serie-a", "bundesliga", "ligue-1",
    "champions-league", "fpl", "transfers", "comics", "clubs", "teams",
    "football", "history", "records", "international", "players",
}


def text(html: str, pat: str) -> str:
    m = re.search(pat, html, re.I | re.S)
    if not m:
        return ""
    return re.sub(r"<[^>]+>", "", m.group(1)).replace("&amp;", "&").replace("&nbsp;", " ").strip()


def replace_main(html: str, new_main: str) -> str:
    m = re.search(r"<main\b[^>]*>", html)
    n = html.find("</main>")
    if not m or n < 0:
        return html
    return html[: m.start()] + new_main + html[n + 7 :]


def ensure_css_js(html: str, js: str | None) -> str:
    if "sports-simple.css" not in html and 'href="/assets/site.css"' in html:
        html = html.replace(
            '<link rel="stylesheet" href="/assets/site.css">',
            '<link rel="stylesheet" href="/assets/site.css">\n<link rel="stylesheet" href="/assets/sports-simple.css">',
            1,
        )
    html = re.sub(r'\s*<script src="/assets/comic-carousel.js"></script>', "", html)
    if js and js not in html:
        html = html.replace("</body>", f'<script src="{js}"></script>\n</body>', 1)
    return html


def collect_articles() -> list[tuple[str, str, str]]:
    items: list[tuple[str, str, str]] = []
    seen_titles: set[str] = set()

    def add(href: str, title: str, desc: str) -> None:
        key = re.sub(r"[^a-z0-9]+", "", title.lower())
        if not title or key in seen_titles:
            return
        seen_titles.add(key)
        items.append((href, title, desc))

    # /sports/articles/* first
    for p in sorted((SPORTS / "articles").glob("*/index.html")):
        html = p.read_text(encoding="utf-8", errors="ignore")
        title = text(html, r"<h1[^>]*>(.*?)</h1>") or text(html, r"<title>(.*?)</title>")
        title = re.sub(r"\s*\|\s*BRYME.*$", "", title).strip()
        desc = text(html, r'<meta name="description" content="(.*?)">')
        add(f"/sports/articles/{p.parent.name}/", title, desc)

    for p in sorted(SPORTS.iterdir()):
        if not p.is_dir() or p.name in SKIP_DIRS:
            continue
        f = p / "index.html"
        if not f.exists():
            continue
        html = f.read_text(encoding="utf-8", errors="ignore")
        title = text(html, r"<h1[^>]*>(.*?)</h1>") or text(html, r"<title>(.*?)</title>")
        title = re.sub(r"\s*\|\s*BRYME.*$", "", title).strip()
        desc = text(html, r'<meta name="description" content="(.*?)">')
        add(f"/sports/{p.name}/", title, desc)

    prefer = [
        "premier-league-transfer-tracker-august-2026",
        "premier-league-matchweek-2-preview",
        "where-to-watch-premier-league-in-nigeria",
        "premier-league-2026-27-season-guide",
    ]
    rank = {k: i for i, k in enumerate(prefer)}

    def sort_key(it: tuple[str, str, str]) -> tuple[int, str]:
        slug = it[0].rstrip("/").split("/")[-1]
        return (rank.get(slug, 50), it[1].lower())

    items.sort(key=sort_key)
    return items


HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#08090b">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="https://bryme.onrender.com/assets/bryme-card.png">
<link rel="stylesheet" href="/assets/site.css">
<link rel="stylesheet" href="/assets/sports-simple.css">
<script src="/assets/analytics.js" async></script>
</head>
<body data-nav="sports">
<header class="top"><div class="shell"><a class="brand" href="/">BRY<b>ME</b></a>
<nav class="topnav"><a href="/">Home</a><a href="/entertainment/">🎬 Entertainment</a><a href="/sports/" class="active">⚽ Sports</a><a href="/make-money/">💰 Make Money</a><a href="/tech/">🤖 Tech &amp; AI</a><a class="nav-search" href="/search/">Search</a></nav>
</div></header>
"""

FOOT = """
<nav class="mobile-nav"><a href="/"><span class="mn-ico">🏠</span>Home</a><a href="/entertainment/"><span class="mn-ico">🎬</span>Entertain</a><a href="/sports/" class="active"><span class="mn-ico">⚽</span>Sports</a><a href="/make-money/"><span class="mn-ico">💰</span>Money</a><a href="/tech/"><span class="mn-ico">🤖</span>Tech</a><a href="/search/"><span class="mn-ico">🔍</span>Search</a></nav>
<footer class="footer"><div class="shell"><p class="footer-note">BRYME · Scores are sourced. We do not invent results.</p></div></footer>
<script>window.BRYME_BASE=''</script>
<script src="/assets/site-app.js"></script>
{extra}
</body>
</html>
"""


def write_page(path: Path, title: str, desc: str, canonical: str, main: str, extra: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        HEAD.format(title=escape(title), desc=escape(desc), canonical=canonical)
        + main
        + FOOT.format(extra=extra),
        encoding="utf-8",
    )


def write_articles(items: list[tuple[str, str, str]]) -> None:
    cards = []
    for href, title, desc in items:
        line = escape(desc[:140]) if desc else ""
        cards.append(
            f'<a class="sp-story" href="{escape(href)}"><b>{escape(title)}</b>'
            + (f"<span>{line}</span>" if line else "")
            + "</a>"
        )
    main = (
        '<main class="shell sp-easy">\n'
        '  <a class="sp-easy-back" href="/sports/">← Sports</a>\n'
        "  <h1>Articles</h1>\n"
        '  <p class="sp-easy-sub">Every sports story on BRYME, in one place.</p>\n'
        + "\n".join(cards)
        + "\n</main>"
    )
    write_page(
        SPORTS / "articles" / "index.html",
        "Articles | BRYME Sports",
        "Every BRYME sports story in one place — transfers, matchweeks, FPL notes and guides.",
        "https://bryme.onrender.com/sports/articles/",
        main,
    )


def last_score_line(feed: dict, team_id: str, league: str) -> str:
    rows = (feed.get("leagues") or {}).get(league) or []
    res = (feed.get("results") or {}).get(league) or {}
    best = None
    for r in rows:
        hid, aid, hn, an, date = r[0], r[1], r[2], r[3], r[4]
        if hid != team_id and aid != team_id:
            continue
        sc = res.get(f"{hid}-vs-{aid}")
        if not sc or sc.get("homeScore") is None:
            continue
        if best is None or date > best[0]:
            best = (date, f"{hn} {sc['homeScore']}–{sc['awayScore']} {an}")
    return best[1] if best else "No played score yet"


def write_team_hubs(teams: list[dict], feed: dict) -> None:
    league_cards = []
    for slug, name in LEAGUES.items():
        league_cards.append(
            f'<a class="sp-lg" href="/sports/{slug}/teams/"><div class="sp-lg-top">{escape(name)}'
            f'<span>Open →</span></div><p class="sp-lg-next">Clubs and played scores</p></a>'
        )
    hub_main = (
        '<main class="shell sp-easy">\n'
        '  <a class="sp-easy-back" href="/sports/">← Sports</a>\n'
        "  <h1>Teams</h1>\n"
        '  <p class="sp-easy-sub">Tap a league, then a club. Played scores on every page.</p>\n'
        + "\n".join(league_cards)
        + "\n</main>"
    )
    write_page(
        SPORTS / "teams" / "index.html",
        "Teams | BRYME Sports",
        "Club pages with played scores and upcoming fixtures. Tap a league.",
        "https://bryme.onrender.com/sports/teams/",
        hub_main,
    )
    # old comics URL becomes Teams
    write_page(
        SPORTS / "comics" / "index.html",
        "Teams | BRYME Sports",
        "Club pages with played scores and upcoming fixtures.",
        "https://bryme.onrender.com/sports/teams/",
        hub_main,
    )

    by_lg: dict[str, list[dict]] = {}
    for t in teams:
        by_lg.setdefault(t["league"], []).append(t)
    for slug, name in LEAGUES.items():
        cards = []
        for t in sorted(by_lg.get(slug, []), key=lambda x: x["name"]):
            last = last_score_line(feed, t["id"], slug)
            cards.append(
                f'<a class="sp-lg" href="/sports/{slug}/teams/{t["slug"]}/">'
                f'<div class="sp-lg-top">{escape(t["name"])}<span>Open →</span></div>'
                f'<p class="sp-lg-next">{escape(last)}</p></a>'
            )
        main = (
            '<main class="shell sp-easy">\n'
            '  <a class="sp-easy-back" href="/sports/teams/">← Teams</a>\n'
            f"  <h1>{escape(name)}</h1>\n"
            '  <p class="sp-easy-sub">Tap a club for played scores.</p>\n'
            + "\n".join(cards)
            + "\n</main>"
        )
        write_page(
            SPORTS / slug / "teams" / "index.html",
            f"{name} clubs | BRYME",
            f"{name} club pages with played scores.",
            f"https://bryme.onrender.com/sports/{slug}/teams/",
            main,
        )


def rewrite_team_pages(teams: list[dict]) -> int:
    n = 0
    for t in teams:
        p = SPORTS / t["league"] / "teams" / t["slug"] / "index.html"
        if not p.exists():
            continue
        html = p.read_text(encoding="utf-8")
        name = t["name"]
        lg = LEAGUES.get(t["league"], t["league"])
        main = (
            f'<main class="shell sp-easy" id="tm-app" data-league="{t["league"]}" '
            f'data-id="{t["id"]}" data-name="{escape(name)}">\n'
            f'  <a class="sp-easy-back" href="/sports/{t["league"]}/teams/">← {escape(lg)}</a>\n'
            f"  <h1>{escape(name)}</h1>\n"
            f'  <p class="sp-easy-sub">{escape(lg)}. Played scores and next fixtures.</p>\n'
            f'  <div id="tm-body"><p class="sp-empty">Loading scores…</p></div>\n'
            f"</main>"
        )
        html = replace_main(html, main)
        html = ensure_css_js(html, "/assets/team-simple.js")
        html = re.sub(r'\s*<script src="/assets/sports-engine.js"[^>]*></script>', "", html)
        html = html.replace("Comics only on the big clubs.", "")
        html = html.replace("BRYME Match Comic", "")
        # keep canonical; light title tweak if it's the old comic title
        html = re.sub(
            r"<title>[^<]*</title>",
            f"<title>{escape(name)} — scores | BRYME</title>",
            html,
            count=1,
        )
        p.write_text(html, encoding="utf-8")
        n += 1
    return n


def patch_sports_landing() -> None:
    p = SPORTS / "index.html"
    html = p.read_text(encoding="utf-8")
    html = html.replace(
        """    <p class="sp-kick">Also here</p>
    <div class="sp-more">
      <a href="/sports/transfers/">Transfers</a>
      <a href="/sports/comics/">Comics</a>
      <a href="/sports/fpl/">FPL</a>
    </div>

    <p class="sp-kick">Stories</p>
    <a class="sp-story" href="/sports/articles/premier-league-transfer-tracker-august-2026/"><b>Deadline day: the window is shut</b><span>Fernández to City, and the other done deals</span></a>
    <a class="sp-story" href="/sports/articles/premier-league-matchweek-2-preview/"><b>Matchweek 2 preview</b><span>Fixtures and kick-off times</span></a>
    <a class="sp-story" href="/sports/articles/where-to-watch-premier-league-in-nigeria/"><b>Where to watch the Premier League in Nigeria</b><span>Viewer guide</span></a>
    <a class="sp-story" href="/sports/premier-league-2026-27-season-guide/"><b>Premier League 2026/27 dates</b><span>Season guide</span></a>""",
        """    <p class="sp-kick">Also here</p>
    <div class="sp-more">
      <a href="/sports/transfers/">Transfers</a>
      <a href="/sports/teams/">Teams</a>
      <a href="/sports/fpl/">FPL</a>
      <a href="/sports/articles/">Articles</a>
    </div>""",
    )
    p.write_text(html, encoding="utf-8")


def strip_comic_links() -> int:
    n = 0
    for p in SPORTS.rglob("*.html"):
        html = p.read_text(encoding="utf-8", errors="ignore")
        new = html.replace("/sports/comics/", "/sports/teams/")
        new = new.replace(">Comics<", ">Teams<")
        new = new.replace("Match comic", "Team page")
        new = re.sub(r'\s*<script src="/assets/comic-carousel.js"></script>', "", new)
        if new != html:
            p.write_text(new, encoding="utf-8")
            n += 1
    return n


def main() -> None:
    teams = json.loads((ROOT / "content" / "teams.json").read_text())["teams"]
    feed = json.loads((ROOT / "content" / "sports-feed.json").read_text())
    items = collect_articles()
    write_articles(items)
    write_team_hubs(teams, feed)
    n = rewrite_team_pages(teams)
    patch_sports_landing()
    c = strip_comic_links()
    print(f"articles {len(items)}; team pages {n}; comic-link files {c}")


if __name__ == "__main__":
    main()

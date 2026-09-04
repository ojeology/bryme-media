#!/usr/bin/env python3
"""Make remaining sports pages match the simple hub: table / scores / fixtures / scorers."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPORTS = ROOT / "sports"

LEAGUES = {
    "premier-league": "Premier League",
    "la-liga": "La Liga",
    "serie-a": "Serie A",
    "bundesliga": "Bundesliga",
    "ligue-1": "Ligue 1",
    "champions-league": "Champions League",
}

TAB_FOR = {
    "table": "table",
    "fixtures": "fixtures",
    "results": "scores",
    "top-scorers": "scorers",
    "matches": "scores",
}

SPX_BACK = re.compile(r'<a class="spx-back-btn"[^>]*>.*?</a>', re.S)
SP_TABS = re.compile(r'<nav class="sp-tabs"[^>]*>.*?</nav>', re.S)
CRUMB = re.compile(r'<div class="crumb">.*?</div>', re.S)
TD_CRUMB = re.compile(r'<div class="td-crumb">.*?</div>', re.S)
TRUTH = re.compile(r'<div class="sp-truth">.*?</div>', re.S)
JUMP = re.compile(r'<p class="tp-match-jump">.*?</p>', re.S)
EMPTY_HERO = re.compile(
    r'<section class="hero">\s*<div class="eyebrow">[^<]*</div>\s*'
    r'<span class="visually-hidden">[^<]*</span>\s*</section>',
    re.S,
)
DESK_WORDS = (
    ("Open the Premier League desk", "Open Premier League"),
    ("Night-stadium desk", "Scores and tables"),
    ("the BRYME sports desk", "BRYME Sports"),
    ("from the scores desk", "full time"),
    ("Latest from the scores desk", "Full time"),
    ("Sports desk", "Sports"),
    ("live desk", "scores"),
    ("Live desk", "Scores"),
    ("editorial desk", "stories"),
    ("From the editorial desk", "Stories"),
)


def replace_main(html: str, new_main: str) -> str:
    m = re.search(r"<main\b[^>]*>", html)
    n = html.find("</main>")
    if not m or n < 0:
        return html
    return html[: m.start()] + new_main + html[n + 7 :]


def ensure_simple(html: str) -> str:
    if "sports-simple.css" not in html and 'href="/assets/site.css"' in html:
        html = html.replace(
            '<link rel="stylesheet" href="/assets/site.css">',
            '<link rel="stylesheet" href="/assets/site.css">\n<link rel="stylesheet" href="/assets/sports-simple.css">',
            1,
        )
    if "sports-simple.js" not in html:
        html = html.replace(
            "</body>",
            '<script src="/assets/sports-simple.js"></script>\n</body>',
            1,
        )
    return html


def strip_chrome(html: str) -> str:
    html = SPX_BACK.sub("", html)
    html = SP_TABS.sub("", html)
    html = CRUMB.sub("", html)
    html = TD_CRUMB.sub("", html)
    html = JUMP.sub("", html)
    html = EMPTY_HERO.sub("", html)
    # Only drop the old "Truth first" newspaper box, not FPL notes that reuse the class
    html = re.sub(
        r'<div class="sp-truth"><b>Truth first\.</b>.*?</div>',
        "",
        html,
        flags=re.S,
    )
    html = html.replace(' class="team-desk"', "")
    html = html.replace(" class=\"team-desk\"", "")
    for old, new in DESK_WORDS:
        html = html.replace(old, new)
    html = re.sub(
        r'<section class="bsd-sec"[^>]*>.*?</section>',
        "",
        html,
        flags=re.S,
    )
    return html


def league_app_main(slug: str, tab: str) -> str:
    name = LEAGUES.get(slug, slug)
    return (
        f'<main class="shell sp-easy" id="sp-app" data-lg="{slug}" data-tab="{tab}">\n'
        f'  <div id="sp-leagues" hidden></div>\n'
        f'  <div id="sp-comp"></div>\n'
        f'  <noscript><p><a class="sp-easy-back" href="/sports/#{slug}">← {name}</a></p></noscript>\n'
        f"</main>"
    )


def rewrite_league_data_pages() -> int:
    n = 0
    for slug in LEAGUES:
        base = SPORTS / slug
        if not base.is_dir():
            continue
        for folder, tab in TAB_FOR.items():
            p = base / folder / "index.html"
            if not p.exists():
                continue
            html = p.read_text(encoding="utf-8")
            html = strip_chrome(html)
            html = replace_main(html, league_app_main(slug, tab))
            html = ensure_simple(html)
            html = re.sub(r'\s*<script src="/assets/sports-engine.js"[^>]*></script>', "", html)
            p.write_text(html, encoding="utf-8")
            n += 1
    return n


def simplify_empty_match(html: str, slug: str) -> str:
    name = LEAGUES.get(slug, "Sports")
    hm = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    title = re.sub(r"<[^>]+>", "", hm.group(1)).strip() if hm else "Match"
    dm = re.search(r"<b>Date:</b>\s*([^<]+)", html)
    km = re.search(r"<b>Kickoff:</b>\s*([^<]+)", html)
    bits = []
    if dm:
        bits.append(dm.group(1).strip())
    if km:
        bits.append(km.group(1).strip())
    when = " · ".join(bits) if bits else "Date to be confirmed"
    main = (
        f'<main class="shell sp-easy">\n'
        f'  <a class="sp-easy-back" href="/sports/#{slug}">← {name}</a>\n'
        f"  <h1>{title}</h1>\n"
        f'  <p class="sp-easy-sub">{when}</p>\n'
        f'  <p class="sp-empty">Not played yet. The score shows here after full time.</p>\n'
        f'  <div class="sp-more"><a href="/sports/#{slug}">Scores &amp; table</a></div>\n'
        f"</main>"
    )
    html = replace_main(html, main)
    return ensure_simple(html)


def walk_matches() -> tuple[int, int]:
    empty = filled = 0
    for p in SPORTS.glob("*/matches/*/index.html"):
        slug = p.parts[-4]
        html = p.read_text(encoding="utf-8")
        is_empty = "noindex" in html and (
            "not been played" in html or "Upcoming — not yet played" in html or "Upcoming &mdash; not yet played" in html
        )
        if is_empty:
            html = simplify_empty_match(html, slug)
            empty += 1
        else:
            html = strip_chrome(html)
            html = ensure_simple(html)
            filled += 1
        p.write_text(html, encoding="utf-8")
    return empty, filled


def simple_hub(title: str, sub: str, cards: list[tuple[str, str, str]]) -> str:
    items = []
    for href, label, next_line in cards:
        extra = f'<p class="sp-lg-next">{next_line}</p>' if next_line else ""
        items.append(
            f'<a class="sp-lg" href="{href}"><div class="sp-lg-top">{label}<span>Open →</span></div>{extra}</a>'
        )
    return (
        '<main class="shell sp-easy">\n'
        '  <a class="sp-easy-back" href="/sports/">← Sports</a>\n'
        f"  <h1>{title}</h1>\n"
        f'  <p class="sp-easy-sub">{sub}</p>\n'
        + "\n".join(items)
        + "\n</main>"
    )


def rewrite_named_hubs() -> int:
    league_cards = [
        ("/sports/#premier-league", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League", "Table, scores, fixtures"),
        ("/sports/#la-liga", "🇪🇸 La Liga", "Table, scores, fixtures"),
        ("/sports/#serie-a", "🇮🇹 Serie A", "Table, scores, fixtures"),
        ("/sports/#bundesliga", "🇩🇪 Bundesliga", "Table, scores, fixtures"),
        ("/sports/#ligue-1", "🇫🇷 Ligue 1", "Table, scores, fixtures"),
        ("/sports/#champions-league", "🇪🇺 Champions League", "Scores and fixtures"),
    ]
    hubs = {
        "football": ("Football", "Tap a league.", league_cards),
        "clubs": ("Clubs", "Pick a league, then open the table.", league_cards),
        "teams": ("Teams", "Pick a league, then open the table.", league_cards),
        "players": ("Players", "Top scorers live on each league screen.", league_cards),
        "history": (
            "History",
            "Stories and records.",
            [
                ("/sports/english-champions-since-1888/", "English champions since 1888", ""),
                ("/sports/champions-league-records/", "Champions League records", ""),
                ("/sports/", "Scores", ""),
            ],
        ),
        "records": (
            "Records",
            "A few lists. Scores stay on Sports.",
            [
                ("/sports/english-champions-since-1888/", "English champions since 1888", ""),
                ("/sports/champions-league-records/", "Champions League records", ""),
                ("/sports/", "Scores", ""),
            ],
        ),
        "international": (
            "International",
            "World Cup and the big leagues.",
            [
                ("/sports/world-cup-2026-spain-champions/", "World Cup 2026", "Spain are champions"),
                ("/sports/", "League scores", ""),
            ],
        ),
        "comics": (
            "Comics",
            "Match stories drawn as comics. Scores are real. No club badges.",
            [
                ("/sports/premier-league/teams/hull/", "Hull 2–0 United", "Match comic"),
                ("/sports/premier-league/teams/arsenal/", "Arsenal 3–0 Coventry", "Match comic"),
                ("/sports/premier-league/teams/brentford/", "Brentford 3–0 Tottenham", "Match comic"),
                ("/sports/premier-league/teams/manchester-city/", "City v Bournemouth", "Match comic"),
                ("/sports/premier-league/teams/newcastle-united/", "Newcastle v Liverpool", "Match comic"),
                ("/sports/", "Scores", ""),
            ],
        ),
    }
    n = 0
    for slug, (title, sub, cards) in hubs.items():
        p = SPORTS / slug / "index.html"
        if not p.exists():
            continue
        html = p.read_text(encoding="utf-8")
        html = replace_main(html, simple_hub(title, sub, cards))
        html = ensure_simple(html)
        html = strip_chrome(html)
        p.write_text(html, encoding="utf-8")
        n += 1
    return n


def strip_all_sports() -> int:
    n = 0
    for p in SPORTS.rglob("index.html"):
        html = p.read_text(encoding="utf-8")
        new = strip_chrome(html)
        new = ensure_simple(new) if "sports/" in str(p.relative_to(ROOT)) else new
        if new != html:
            p.write_text(new, encoding="utf-8")
            n += 1
    return n


def main() -> None:
    data_n = rewrite_league_data_pages()
    empty, filled = walk_matches()
    hubs = rewrite_named_hubs()
    rest = strip_all_sports()
    print(
        f"league data pages {data_n}; empty matches {empty}; "
        f"played matches {filled}; hubs {hubs}; chrome-stripped {rest}"
    )


if __name__ == "__main__":
    main()

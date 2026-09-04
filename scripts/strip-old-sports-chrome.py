#!/usr/bin/env python3
"""Remove Sports Desk v2 ticker/rail from every sports page. Keep the simple layout."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPORTS = ROOT / "sports"

CHROME = re.compile(
    r'<div class="bsd-chrome" data-bsd-chrome>.*?</nav>\s*</div>\s*',
    re.S,
)

LEAGUE_HUBS = {
    "premier-league": ("🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League", "/sports/#premier-league"),
    "la-liga": ("🇪🇸 La Liga", "/sports/#la-liga"),
    "serie-a": ("🇮🇹 Serie A", "/sports/#serie-a"),
    "bundesliga": ("🇩🇪 Bundesliga", "/sports/#bundesliga"),
    "ligue-1": ("🇫🇷 Ligue 1", "/sports/#ligue-1"),
    "champions-league": ("🇪🇺 Champions League", "/sports/#champions-league"),
}


def strip(html: str) -> str:
    html = CHROME.sub("", html)
    html = html.replace('\n<link rel="stylesheet" href="/assets/sports-hub.css">', "")
    html = html.replace('<link rel="stylesheet" href="/assets/sports-hub.css">', "")
    html = html.replace('\n<link rel="stylesheet" href="/assets/sports-skin.css">', "")
    html = html.replace('<link rel="stylesheet" href="/assets/sports-skin.css">', "")
    html = html.replace(' class="spx"', "")
    if "sports-simple.css" not in html and 'href="/assets/site.css"' in html:
        html = html.replace(
            '<link rel="stylesheet" href="/assets/site.css">',
            '<link rel="stylesheet" href="/assets/site.css">\n<link rel="stylesheet" href="/assets/sports-simple.css">',
            1,
        )
    # drop engine if it was only feeding the ticker
    if "data-sp-engine" not in html:
        html = re.sub(r'\s*<script src="/assets/sports-engine.js"></script>', "", html)
        html = re.sub(r'\s*<script src="/assets/sports-hub.js"[^>]*></script>', "", html)
    return html


def add_back(html: str, href: str, label: str) -> str:
    if "sp-easy-back" in html:
        return html
    html = html.replace('<main class="shell">', '<main class="shell sp-easy">', 1)
    html = html.replace('<main class="shell sp-pro">', '<main class="shell sp-easy">', 1)
    html = html.replace('<main class="shell sp-pro"', '<main class="shell sp-easy"', 1)
    m = re.search(r"<main[^>]*>", html)
    if not m:
        return html
    return html[: m.end()] + f'\n  <a class="sp-easy-back" href="{href}">{label}</a>\n' + html[m.end():]


def league_main(name: str, hash_url: str, slug: str) -> str:
    extra = ""
    if slug != "champions-league":
        extra = (
            f'<a class="sp-lg" href="/sports/{slug}/matches/"><div class="sp-lg-top">Match centre<span>Open →</span></div></a>\n'
            f'<a class="sp-lg" href="/sports/transfers/{slug}-2026-27/"><div class="sp-lg-top">Transfers<span>Open →</span></div></a>\n'
        )
    return f"""  <a class="sp-easy-back" href="/sports/">← Sports</a>
  <h1>{name}</h1>
  <p class="sp-easy-sub">Table, scores and fixtures — same screen as Sports.</p>
  <a class="sp-lg" href="{hash_url}"><div class="sp-lg-top">Scores &amp; table<span>Open →</span></div></a>
{extra}  <div class="sp-more"><a href="/sports/">All leagues</a></div>
"""


def rewrite_league_hub(p: Path, slug: str) -> None:
    html = strip(p.read_text(encoding="utf-8"))
    name, href = LEAGUE_HUBS[slug]
    m = re.search(r"<main[^>]*>", html)
    n = html.find("</main>")
    if not m or n < 0:
        p.write_text(html, encoding="utf-8")
        return
    html = html[: m.end()] + "\n" + league_main(name, href, slug) + html[n:]
    # keep simple css
    if "sports-simple.css" not in html:
        html = html.replace(
            '<link rel="stylesheet" href="/assets/site.css">',
            '<link rel="stylesheet" href="/assets/site.css">\n<link rel="stylesheet" href="/assets/sports-simple.css">',
            1,
        )
    p.write_text(html, encoding="utf-8")


def main() -> None:
    n = 0
    for p in SPORTS.rglob("index.html"):
        rel = p.relative_to(SPORTS).as_posix()
        if rel == "index.html":
            continue
        parts = rel.split("/")
        # league hub
        if len(parts) == 2 and parts[0] in LEAGUE_HUBS and parts[1] == "index.html":
            rewrite_league_hub(p, parts[0])
            n += 1
            continue
        html = p.read_text(encoding="utf-8")
        if "data-bsd-chrome" not in html and "sports-hub.css" not in html:
            continue
        html = strip(html)
        back, label = "/sports/", "← Sports"
        if parts[0] in LEAGUE_HUBS:
            if "matches" in parts:
                back, label = f"/sports/{parts[0]}/", "← " + LEAGUE_HUBS[parts[0]][0].split(" ", 1)[-1]
            elif "teams" in parts:
                back, label = f"/sports/{parts[0]}/", "← Teams"
            else:
                back, label = "/sports/", "← Sports"
        elif parts[0] == "articles":
            back, label = "/sports/", "← Sports"
        elif parts[0] == "fpl":
            back, label = "/sports/fpl/", "← FPL"
        elif parts[0] == "transfers":
            back, label = "/sports/transfers/", "← Transfers"
        html = add_back(html, back, label)
        p.write_text(html, encoding="utf-8")
        n += 1
    print("updated", n)


if __name__ == "__main__":
    main()

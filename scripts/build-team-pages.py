#!/usr/bin/env python3
"""BRYME league team pages.

Canonical URL:

    /sports/{league}/teams/{slug}/

Every club in the five-league fixture files gets a page.
Matchweek comics are only written for the big clubs flagged in COMIC_TEAMS.

    python3 scripts/build-team-pages.py
"""
from __future__ import annotations

import html as H
import json
import re
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://bryme.onrender.com"
TODAY = date(2026, 8, 23)

FIXTURE_FILES = {
    "premier-league": "fixtures.json",
    "la-liga": "fixtures-la-liga.json",
    "serie-a": "fixtures-serie-a.json",
    "bundesliga": "fixtures-bundesliga.json",
    "ligue-1": "fixtures-ligue-1.json",
}
LEAGUE_NAME = {
    "premier-league": "Premier League",
    "la-liga": "La Liga",
    "serie-a": "Serie A",
    "bundesliga": "Bundesliga",
    "ligue-1": "Ligue 1",
}
LEAGUE_ORDER = ["premier-league", "la-liga", "serie-a", "bundesliga", "ligue-1"]

# Pretty public slugs. Everything else uses the fixture id.
PRETTY = {
    "man-united": "manchester-united",
    "man-city": "manchester-city",
    "newcastle": "newcastle-united",
    "inter": "inter-milan",
    "milan": "ac-milan",
    "bayern": "bayern-munich",
    "dortmund": "borussia-dortmund",
    "leverkusen": "bayer-leverkusen",
    "leipzig": "rb-leipzig",
    "psg": "paris-saint-germain",
    "gladbach": "borussia-monchengladbach",
    "koln": "fc-koln",
    "athletic-bilbao": "athletic-club",
}

COMIC_TEAMS = {
    "man-united", "man-city", "liverpool", "arsenal", "chelsea", "tottenham",
    "newcastle", "aston-villa", "real-madrid", "barcelona", "atletico-madrid",
    "inter", "milan", "juventus", "napoli", "roma", "bayern", "dortmund",
    "leverkusen", "leipzig", "psg", "marseille", "lyon", "monaco",
}

RELATED = {
    "arsenal": [
        ("/sports/arsenal-title-defence/", "Arsenal's title defence"),
        ("/sports/community-shield-2026-arsenal-manchester-city/", "Community Shield 2026"),
        ("/sports/premier-league-matchweek-1-guide/", "Premier League Matchweek 1 guide"),
    ],
    "man-city": [
        ("/sports/manchester-city-without-guardiola/", "Manchester City after Guardiola"),
        ("/sports/community-shield-2026-arsenal-manchester-city/", "Community Shield 2026"),
    ],
    "liverpool": [
        ("/sports/liverpools-next-chapter/", "Liverpool under Andoni Iraola"),
        ("/sports/five-matches-we-cannot-wait-to-watch/", "Five opening-weekend matches"),
    ],
    "man-united": [
        ("/sports/newly-promoted-clubs-approach/", "Hull, Coventry and Ipswich: the promoted clubs"),
        ("/sports/premier-league-matchweek-1-guide/", "Premier League Matchweek 1 guide"),
    ],
}

COLORS = {
    "arsenal": "#EF0107", "aston-villa": "#670E36", "bournemouth": "#DA291C",
    "brentford": "#E30613", "brighton": "#0057B8", "chelsea": "#034694",
    "coventry": "#77BBFF", "crystal-palace": "#C4122E", "everton": "#003399",
    "fulham": "#9AA0A6", "hull": "#F5A12D", "ipswich": "#3A64A8",
    "leeds": "#FFCD00", "liverpool": "#C8102E", "man-city": "#6CABDD",
    "man-united": "#DA291C", "newcastle": "#241F20", "nottingham-forest": "#DD0000",
    "sunderland": "#EB172B", "tottenham": "#132257",
    "alaves": "#004FA3", "athletic-bilbao": "#EE2523", "atletico-madrid": "#CB3524",
    "barcelona": "#A50044", "celta-vigo": "#8AC3EE", "deportivo": "#1D57A5",
    "elche": "#007A33", "espanyol": "#1E6BB8", "getafe": "#004FA3",
    "levante": "#9B1B30", "malaga": "#2B6CB0", "osasuna": "#D11241",
    "racing": "#007A33", "rayo-vallecano": "#E30613", "real-betis": "#00954C",
    "real-madrid": "#FEBE10", "real-sociedad": "#0067B1", "sevilla": "#D4A017",
    "valencia": "#EE3524", "villarreal": "#FFE14D",
    "atalanta": "#1E71B8", "bologna": "#1A1A6C", "cagliari": "#AE1218",
    "como": "#1B3A6B", "fiorentina": "#482E92", "frosinone": "#0066B3",
    "genoa": "#AD1919", "inter": "#010E80", "juventus": "#111111",
    "lazio": "#87D8F7", "lecce": "#F7E017", "milan": "#FB090B",
    "monza": "#C8102E", "napoli": "#12A0D7", "parma": "#FFD200",
    "roma": "#8E1F2F", "sassuolo": "#00A651", "torino": "#8B1E1E",
    "udinese": "#111111", "venezia": "#F07E13",
    "augsburg": "#BA3733", "bayern": "#DC052D", "dortmund": "#FDE100",
    "elversberg": "#E30613", "frankfurt": "#E1000F", "freiburg": "#E30613",
    "gladbach": "#111111", "hamburg": "#1C63B7", "hoffenheim": "#1C63B7",
    "koln": "#ED1C24", "leipzig": "#DD0741", "leverkusen": "#E32221",
    "mainz": "#C4122E", "paderborn": "#005CA9", "schalke": "#004D9D",
    "stuttgart": "#E30613", "union-berlin": "#EB1923", "werder": "#1A9F4B",
    "angers": "#111111", "auxerre": "#1B4FA3", "brest": "#D21034",
    "le-havre": "#78B7E7", "le-mans": "#E30613", "lens": "#E30613",
    "lille": "#E01A22", "lorient": "#F07E13", "lyon": "#002F6C",
    "marseille": "#2FAEE0", "monaco": "#E31B23", "nice": "#D21034",
    "paris-fc": "#0033A0", "psg": "#004170", "rennes": "#E30613",
    "strasbourg": "#1B4FA3", "toulouse": "#503291", "troyes": "#1B4FA3",
}

LL_CREST = {
    "alaves": "alaves.png", "athletic-bilbao": "athletic.png",
    "atletico-madrid": "atletico.png", "barcelona": "barcelona.png",
    "celta-vigo": "celta.png", "deportivo": "deportivo.png", "elche": "elche.png",
    "espanyol": "espanyol.png", "getafe": "getafe.png", "levante": "levante.png",
    "malaga": "malaga.png", "osasuna": "osasuna.png", "racing": "racing.png",
    "rayo-vallecano": "rayo.png", "real-betis": "betis.png",
    "real-madrid": "real-madrid.png", "real-sociedad": "real-sociedad.png",
    "sevilla": "sevilla.png", "valencia": "valencia.png", "villarreal": "villarreal.png",
}

HEADER = (
    '<header class="top"><div class="shell"><a class="brand" href="/">BRY<b>ME</b></a>'
    '<nav class="topnav"><a href="/">Home</a><a href="/entertainment/">🎬 Entertainment</a>'
    '<a href="/sports/" class="active">⚽ Sports</a><a href="/make-money/">💰 Make Money</a>'
    '<a href="/tech/">🤖 Tech &amp; AI</a><a class="nav-search" href="/search/">Search</a></nav>'
    '<div class="top-tools"><a class="header-search" href="/search/" aria-label="Search">Search</a>'
    "</div></div></header>"
)
FOOTER = """<nav class="mobile-nav"><a href="/"><span class="mn-ico">🏠</span>Home</a><a href="/entertainment/"><span class="mn-ico">🎬</span>Entertain</a><a href="/sports/" class="active"><span class="mn-ico">⚽</span>Sports</a><a href="/make-money/"><span class="mn-ico">💰</span>Money</a><a href="/tech/"><span class="mn-ico">🤖</span>Tech</a><a href="/search/"><span class="mn-ico">🔍</span>Search</a></nav><footer class="footer"><div class="shell"><div class="footer-grid">
  <div class="footer-brand"><a class="brand" href="/">BRY<b>ME</b></a><p>Discover what you love. Learn what you need. Find what's next.</p></div>
  <nav class="footer-col" aria-label="Explore"><h3>Verticals</h3><a href="/entertainment/">🎬 Entertainment</a><a href="/sports/">⚽ Sports</a><a href="/make-money/">💰 Make Money</a><a href="/tech/">🤖 Tech &amp; AI</a></nav>
  <nav class="footer-col" aria-label="Explore"><h3>Entertainment</h3><a href="/trending/">What's Trending</a><a href="/movies/">Movies</a><a href="/series/">Series</a><a href="/anime/">Anime</a><a href="/articles/">Articles</a><a href="/genres/">Genres</a></nav>
  <nav class="footer-col" aria-label="Information"><h3>Information</h3><a href="/about/">About</a><a href="/contact/">Contact</a><a href="/editorial-policy/">Editorial Policy</a></nav>
  <nav class="footer-col" aria-label="Legal"><h3>Legal</h3><a href="/privacy/">Privacy Policy</a><a href="/terms/">Terms of Use</a><a href="/disclaimer/">Disclaimer</a><a href="/copyright/">Copyright / DMCA</a></nav>
</div>
<p class="footer-note">BRYME · Discover what you love. Learn what you need. Find what's next.<small>Team pages live under each league. Comics only on the big clubs. · 2026-08-23</small></div></footer><script>window.BRYME_BASE=''</script><script src="/assets/site-app.js"></script>"""


def esc(s) -> str:
    return H.escape("" if s is None else str(s), quote=True)


def load_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def slug_of(team_id: str) -> str:
    return PRETTY.get(team_id, team_id)


def team_href(league: str, team_id: str) -> str:
    return f"/sports/{league}/teams/{slug_of(team_id)}/"


def league_teams_href(league: str) -> str:
    return f"/sports/{league}/teams/"


def crest_for(league: str, team_id: str) -> str:
    if league == "premier-league":
        return f"/assets/img/sports/pl/{team_id}.svg"
    if league == "la-liga":
        return f"/assets/img/sports/ll/{LL_CREST.get(team_id, team_id + '.png')}"
    if league == "serie-a":
        ext = ".png" if team_id == "lazio" else ".svg"
        return f"/assets/img/sports/sa/{team_id}{ext}"
    if league == "ligue-1":
        return f"/assets/img/sports/l1/{team_id}.webp"
    p = ROOT / f"assets/img/sports/bl/{team_id}.svg"
    if p.exists():
        return f"/assets/img/sports/bl/{team_id}.svg"
    alt = ROOT / f"assets/img/sports/club-{team_id}.svg"
    if alt.exists():
        return f"/assets/img/sports/club-{team_id}.svg"
    return f"/assets/img/sports/bl/{team_id}.svg"


def parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def season_date(raw: str | None, mw: int | None) -> date | None:
    d = parse_date(raw)
    if not d:
        return None
    if d.year == 2026 and d.month <= 6 and (mw or 0) >= 19:
        try:
            return d.replace(year=2027)
        except ValueError:
            return d
    return d


def fmt_date(s: str | None, mw: int | None = None) -> str:
    d = season_date(s, mw) if mw is not None else parse_date(s)
    if not d:
        return "Date TBC"
    return d.strftime("%a %-d %b %Y")


def fmt_time(t) -> str:
    return f"{t} UK" if t else "TBC"


def match_slug(home_id: str, away_id: str) -> str:
    return f"{home_id}-vs-{away_id}"


def match_href(league: str, home_id: str, away_id: str) -> str:
    return f"/sports/{league}/matches/{match_slug(home_id, away_id)}/"


def empty_row() -> dict:
    return {"p": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "gd": 0, "pts": 0, "form": []}


def apply_result(table: dict, home: str, away: str, hs: int, as_: int):
    for tid in (home, away):
        table.setdefault(tid, empty_row())
    table[home]["p"] += 1
    table[away]["p"] += 1
    table[home]["gf"] += hs
    table[home]["ga"] += as_
    table[away]["gf"] += as_
    table[away]["ga"] += hs
    table[home]["gd"] = table[home]["gf"] - table[home]["ga"]
    table[away]["gd"] = table[away]["gf"] - table[away]["ga"]
    if hs > as_:
        table[home]["w"] += 1
        table[away]["l"] += 1
        table[home]["pts"] += 3
        table[home]["form"].append("W")
        table[away]["form"].append("L")
    elif hs < as_:
        table[away]["w"] += 1
        table[home]["l"] += 1
        table[away]["pts"] += 3
        table[home]["form"].append("L")
        table[away]["form"].append("W")
    else:
        table[home]["d"] += 1
        table[away]["d"] += 1
        table[home]["pts"] += 1
        table[away]["pts"] += 1
        table[home]["form"].append("D")
        table[away]["form"].append("D")


def standings_for(league: str, fixtures: dict, results: dict) -> tuple[dict, list[str]]:
    table, names = {}, {}
    for mw in fixtures.get("matchweeks", []):
        for m in mw.get("matches", []):
            table.setdefault(m["id"], empty_row())
            table.setdefault(m["away"], empty_row())
            names[m["id"]] = m.get("homeName") or m["id"]
            names[m["away"]] = m.get("awayName") or names.get(m["away"], m["away"])
    dated = []
    for slug, r in (results.get(league) or {}).items():
        if "-vs-" not in slug:
            continue
        home, away = slug.split("-vs-", 1)
        dated.append((r.get("playedOn") or "", home, away, r))
    dated.sort(key=lambda x: x[0])
    for _, home, away, r in dated:
        apply_result(table, home, away, int(r["homeScore"]), int(r["awayScore"]))
    ranked = sorted(
        table.keys(),
        key=lambda tid: (-table[tid]["pts"], -table[tid]["gd"], -table[tid]["gf"], names.get(tid, tid)),
    )
    return table, ranked


def collect_team_matches(team_id: str, fixtures: dict, results: dict, league: str) -> list[dict]:
    out = []
    league_results = results.get(league) or {}
    venues = fixtures.get("venues") or {}
    for mw in fixtures.get("matchweeks", []):
        num = mw.get("number")
        for m in mw.get("matches", []):
            if m["id"] != team_id and m["away"] != team_id:
                continue
            slug = match_slug(m["id"], m["away"])
            res = league_results.get(slug)
            home = m["id"] == team_id
            row = {
                "mw": num,
                "homeId": m["id"],
                "awayId": m["away"],
                "homeName": m["homeName"],
                "awayName": m["awayName"],
                "date": m.get("date"),
                "time": m.get("time"),
                "venue": (m.get("venue") or (venues.get(m["id"]) or {}).get("name") or ""),
                "slug": slug,
                "href": match_href(league, m["id"], m["away"]),
                "home": home,
                "oppId": m["away"] if home else m["id"],
                "oppName": m["awayName"] if home else m["homeName"],
                "result": None,
            }
            if res and "homeScore" in res and "awayScore" in res:
                hs, aws = int(res["homeScore"]), int(res["awayScore"])
                if hs > aws:
                    wdl_h, wdl_a = "W", "L"
                elif hs < aws:
                    wdl_h, wdl_a = "L", "W"
                else:
                    wdl_h = wdl_a = "D"
                row["result"] = {
                    "hs": hs, "as": aws,
                    "status": res.get("status") or "FT",
                    "playedOn": res.get("playedOn") or m.get("date"),
                    "wdl": wdl_h if home else wdl_a,
                }
            out.append(row)
    out.sort(key=lambda r: (r["mw"] or 99, r["date"] or "9999", r["time"] or "99:99"))
    return out


def pick_next(upcoming: list[dict]) -> dict | None:
    future = [
        m for m in upcoming
        if season_date(m.get("date"), m.get("mw"))
        and season_date(m.get("date"), m.get("mw")) >= TODAY
    ]
    if future:
        return min(future, key=lambda m: (season_date(m.get("date"), m.get("mw")) or date(9999, 1, 1), m.get("time") or ""))
    return upcoming[0] if upcoming else None


def pick_prev(completed: list[dict]) -> dict | None:
    if not completed:
        return None
    return max(completed, key=lambda m: (m["result"].get("playedOn") or m.get("date") or "", m.get("time") or ""))


def form_html(letters: list[str]) -> str:
    if not letters:
        return '<span>No sourced result yet</span>'
    bits = [f'<span class="td-pill td-pill-{ch.lower()}">{esc(ch)}</span>' for ch in letters[-5:]]
    return '<span class="td-pills">' + "".join(bits) + "</span>"


def gd_txt(n: int) -> str:
    return f"+{n}" if n > 0 else str(n)


def page_head(title: str, desc: str, url: str, extra_ld: list) -> str:
    t, d, u = esc(title), esc(desc), esc(url)
    ld = json.dumps(extra_ld, ensure_ascii=False, separators=(",", ":"))
    return (
        f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        f'<meta name="theme-color" content="#08090b"><meta name="color-scheme" content="dark light">'
        f'<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">'
        f'<link rel="icon" href="/assets/favicon.png" type="image/png" sizes="32x32">'
        f'<link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png">'
        f'<link rel="manifest" href="/manifest.webmanifest">'
        f'<title>{t}</title><meta name="description" content="{d}">'
        f'<link rel="canonical" href="{u}">'
        f'<meta property="og:type" content="website"><meta property="og:site_name" content="BRYME">'
        f'<meta property="og:title" content="{t}"><meta property="og:description" content="{d}">'
        f'<meta property="og:url" content="{u}">'
        f'<meta property="og:image" content="https://bryme.onrender.com/assets/bryme-card.png">'
        f'<meta property="og:image:type" content="image/png"><meta property="og:image:width" content="1200">'
        f'<meta property="og:image:height" content="630"><meta property="og:image:alt" content="BRYME">'
        f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{t}">'
        f'<meta name="twitter:description" content="{d}">'
        f'<meta name="twitter:image" content="https://bryme.onrender.com/assets/bryme-card.png">'
        f'<meta name="twitter:image:alt" content="BRYME">'
        f'<link rel="stylesheet" href="/assets/site.css">'
        f'<script type="application/ld+json">{ld}</script></head>'
    )


def build_registry(fixtures_by_league: dict) -> list[dict]:
    hist = {}
    for lg in LEAGUE_ORDER:
        data = load_json(f"content/club-history/{lg}.json")
        for c in data["clubs"]:
            hist[(lg, c["slug"])] = c
    teams = []
    for lg, fx in fixtures_by_league.items():
        names = {}
        for mw in fx.get("matchweeks", []):
            for m in mw.get("matches", []):
                names[m["id"]] = m.get("homeName") or names.get(m["id"], m["id"])
                names[m["away"]] = m.get("awayName") or names.get(m["away"], m["away"])
        for tid, name in sorted(names.items(), key=lambda kv: kv[1]):
            rec = hist.get((lg, tid), {})
            teams.append({
                "id": tid,
                "slug": slug_of(tid),
                "name": rec.get("name") or name,
                "shortName": (rec.get("name") or name),
                "league": lg,
                "leagueName": LEAGUE_NAME[lg],
                "crest": crest_for(lg, tid),
                "color": COLORS.get(tid, "#3ddc84"),
                "founded": rec.get("founded") or "",
                "city": rec.get("city") or "",
                "stadium": rec.get("stadium") or "",
                "historySource": rec.get("source") or "",
                "comics": tid in COMIC_TEAMS,
                "related": RELATED.get(tid, []),
            })
    return teams


def story_for(team: dict, match: dict, comics: dict) -> dict | None:
    if not match.get("result") or not team.get("comics"):
        return None
    for s in comics.get("stories") or []:
        if s.get("teamId") == team["id"] and s.get("matchSlug") == match["slug"]:
            return s
    r = match["result"]
    line = f"{match['homeName']} {r['hs']}–{r['as']} {match['awayName']}"
    mood = "celebrate" if r["wdl"] == "W" else ("concede" if r["wdl"] == "L" else "kickoff")
    return {
        "headline": f"Matchweek {match['mw']} is in the book",
        "resultLine": line,
        "panels": [
            {"art": "arrival", "title": "Before kickoff",
             "caption": f"{match['homeName']} against {match['awayName']}.",
             "bubble": "Get the points. Then go home."},
            {"art": mood, "title": "The match",
             "caption": f"Final score {line}. Scorers only appear when BRYME has them sourced.",
             "bubble": "That's the number on the board."},
            {"art": "table", "title": "Full time",
             "caption": f"{r['status']} {line}.",
             "bubble": "File it. Next week is a different comic."},
        ],
    }


def render_panels(story: dict, art: dict) -> str:
    bits = ['<ol class="mwc-panels">']
    for i, p in enumerate(story.get("panels") or [], 1):
        src = art.get(p.get("art") or "", art.get("kickoff", ""))
        bubble = p.get("bubble") or ""
        bubble_html = f'<p class="mwc-bubble"><span>{esc(bubble)}</span></p>' if bubble else ""
        bits.append(
            f'<li class="mwc-panel"><figure>'
            f'<img src="{esc(src)}" alt="{esc(p.get("title") or f"Panel {i}")}" width="1200" height="669" loading="lazy" decoding="async">'
            f'<figcaption><b>Panel {i}: {esc(p.get("title") or "")}</b>'
            f'<span>{esc(p.get("caption") or "")}</span></figcaption></figure>{bubble_html}</li>'
        )
    bits.append("</ol>")
    return "".join(bits)


def render_awaiting(art: dict, match: dict | None, mw: int) -> str:
    src = art.get("awaiting", "")
    if match:
        body = (
            f"<p>Matchweek {mw} has not been locked. Next listed fixture: "
            f"<a href=\"{esc(match['href'])}\">{esc(match['homeName'])} vs {esc(match['awayName'])}</a> "
            f"({esc(fmt_date(match['date'], match.get('mw')))} · {esc(fmt_time(match['time']))}). "
            f"The comic is written after a sourced full-time result.</p>"
        )
    else:
        body = f"<p>Matchweek {mw} has not been played.</p>"
    return (
        f'<div class="mwc-await"><img src="{esc(src)}" alt="Empty night pitch, awaiting the next BRYME matchweek comic" width="1200" height="669" loading="lazy" decoding="async">'
        f'<div><p class="eyebrow">Awaiting matchweek {mw}</p>{body}</div></div>'
    )


def ticket(kind: str, match: dict | None, league: str) -> str:
    if not match:
        return (
            f'<div class="td-ticket"><div><small>{esc(kind)}</small>'
            f'<p class="td-ticket-empty">Nothing sourced yet.</p></div></div>'
        )
    if match.get("result"):
        r = match["result"]
        score = f"{match['homeName']} {r['hs']}–{r['as']} {match['awayName']}"
        meta = f"{fmt_date(r.get('playedOn') or match['date'], match.get('mw'))} · {r['wdl']}"
    else:
        score = f"{match['homeName']} vs {match['awayName']}"
        meta = f"{fmt_date(match['date'], match.get('mw'))} · {fmt_time(match['time'])} · {'Home' if match['home'] else 'Away'}"
    return (
        f'<a class="td-ticket" href="{esc(match["href"])}">'
        f'<img src="{esc(crest_for(league, match["oppId"]))}" alt="{esc(match["oppName"])} crest" width="44" height="44">'
        f'<div><small>{esc(kind)}</small><b>{esc(score)}</b><span>{esc(meta)}</span></div></a>'
    )


def match_card(m: dict, league: str, by_id: dict) -> str:
    opp = by_id.get(m["oppId"])
    opp_name = m["oppName"]
    if opp:
        opp_html = f'<a href="{esc(team_href(opp["league"], opp["id"]))}">{esc(opp_name)}</a>'
    else:
        opp_html = esc(opp_name)
    ha = "Home" if m["home"] else "Away"
    if m.get("result"):
        r = m["result"]
        score = f"{r['hs']}–{r['as']}"
        status = r["status"]
    else:
        score = "Preview"
        status = "Today" if parse_date(m.get("date")) == TODAY else fmt_time(m.get("time"))
    return (
        f'<a class="td-match" href="{esc(m["href"])}">'
        f'<div class="td-match-date"><b>{esc(fmt_date(m["date"], m.get("mw")))}</b>MW {esc(m["mw"])}</div>'
        f'<div class="td-match-who"><img src="{esc(crest_for(league, m["oppId"]))}" alt="" width="32" height="32">'
        f'<div><strong>{opp_html}</strong><i>{ha} · {esc(LEAGUE_NAME[league])}</i></div></div>'
        f'<div class="td-match-score"><small>{esc(status)}</small>{esc(score)}</div></a>'
    )


def render_team_page(team: dict, ctx: dict) -> str:
    matches = ctx["matches"]
    table, ranked, comics, by_id, teams = ctx["table"], ctx["ranked"], ctx["comics"], ctx["by_id"], ctx["teams"]
    art = comics.get("art") or {}
    league = team["league"]
    stats = table.get(team["id"], empty_row())
    pos = ranked.index(team["id"]) + 1 if team["id"] in ranked else None
    completed = [m for m in matches if m.get("result")]
    upcoming_raw = [m for m in matches if not m.get("result")]
    upcoming = sorted(
        upcoming_raw,
        key=lambda m: (season_date(m.get("date"), m.get("mw")) or date(9999, 1, 1), m.get("time") or ""),
    )
    next_m, prev_m = pick_next(upcoming_raw), pick_prev(completed)

    title = f"{team['name']} Fixtures & Results | {team['leagueName']} | BRYME"
    desc = (
        f"{team['name']} fixtures, results, next match and recent form in the "
        f"{team['leagueName']} 2026/27 season."
    )
    if team.get("comics"):
        title = f"{team['name']} Fixtures, Results & Matchweek Stories | BRYME"
        desc += " Plus BRYME matchweek comics."
    url = SITE + team_href(league, team["id"])
    blurb = (
        f"{team['name']} are a {team['leagueName']} club"
        + (f" from {team['city']}" if team.get("city") else "")
        + "."
    )
    if team.get("founded") and team.get("stadium"):
        blurb += f" Founded in {team['founded']}, they play at {team['stadium']}."
    page_ld = [
        {"@context": "https://schema.org", "@type": "WebPage", "name": title.replace(" | BRYME", ""),
         "description": desc, "url": url,
         "isPartOf": {"@type": "WebSite", "name": "BRYME", "url": SITE + "/"}},
        {"@context": "https://schema.org", "@type": "SportsTeam", "name": team["name"], "sport": "Soccer",
         "url": url, "logo": SITE + team["crest"],
         "memberOf": {"@type": "SportsOrganization", "name": team["leagueName"],
                      "url": f"{SITE}/sports/{league}/"}},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "BRYME Sports", "item": SITE + "/sports/"},
            {"@type": "ListItem", "position": 3, "name": team["leagueName"], "item": f"{SITE}/sports/{league}/"},
            {"@type": "ListItem", "position": 4, "name": f"{team['leagueName']} teams",
             "item": SITE + league_teams_href(league)},
            {"@type": "ListItem", "position": 5, "name": team["name"], "item": url},
        ]},
    ]
    if next_m:
        page_ld.append({
            "@context": "https://schema.org", "@type": "SportsEvent",
            "name": f"{next_m['homeName']} v {next_m['awayName']}", "sport": "Soccer",
            "startDate": f"{next_m['date']}T{(next_m['time'] or '15:00')}:00",
            "eventStatus": "https://schema.org/EventScheduled",
            "homeTeam": {"@type": "SportsTeam", "name": next_m["homeName"]},
            "awayTeam": {"@type": "SportsTeam", "name": next_m["awayName"]},
            "url": SITE + next_m["href"],
        })

    sourced_n = sum(1 for tid in table if table[tid]["p"] > 0)
    games = sum(s["p"] for s in table.values()) // 2
    pos_note = (
        f"BRYME table from {games} sourced full-time results across {sourced_n} clubs. "
        f"Sunday 23 August matches stay as previews until a source URL exists. "
        f"Not an official {team['leagueName']} table."
    )
    src_link = ""
    if team.get("historySource"):
        src_link = f'<a href="{esc(team["historySource"])}" rel="nofollow noopener">Club history source ↗</a>'

    hero = f"""
<section class="td-hero" style="--td:{esc(team['color'])}">
  <div class="td-hero-top">
    <img class="td-crest" src="{esc(team['crest'])}" alt="{esc(team['name'])} crest" width="108" height="108">
    <div>
      <p class="td-kicker">{esc(team['leagueName'])} · 2026/27</p>
      <h1>{esc(team['name'])}</h1>
      <p class="td-where">{esc(' · '.join(x for x in [team.get('city'), team.get('stadium'), ('Founded ' + team['founded']) if team.get('founded') else ''] if x))}</p>
      <p class="td-blurb">{esc(blurb)}{src_link}</p>
    </div>
  </div>
  <div class="td-tickets">{ticket("Next match", next_m, league)}{ticket("Last result", prev_m, league)}</div>
</section>"""

    overview = f"""
<section class="td-season" id="season">
  <div class="td-season-head"><div><p class="eyebrow">This season</p><h2>2026/27 so far</h2></div>
  <a href="/sports/{esc(league)}/">Open the {esc(team['leagueName'])} desk</a></div>
  <p class="td-note">{esc(pos_note)}</p>
  <div class="td-statgrid">
    <div class="td-stat"><b>{stats['p']}</b><em>Played</em></div>
    <div class="td-stat"><b>{stats['w']}-{stats['d']}-{stats['l']}</b><em>W-D-L</em></div>
    <div class="td-stat"><b>{esc(gd_txt(stats['gd']))}</b><em>Goal difference</em></div>
    <div class="td-stat"><b>{stats['pts']}</b><em>Points</em></div>
    <div class="td-stat"><b>{esc(pos or '—')}</b><em>Position</em></div>
  </div>
  <p class="td-form">Form {form_html(stats['form'])}</p>
</section>"""

    chronicles = ""
    if team.get("comics"):
        mws, first = [], {}
        for m in matches:
            if m["mw"] not in first:
                first[m["mw"]] = m
                mws.append(m["mw"])
        carousel = mws[:6]
        current = (prev_m or next_m or matches[0])["mw"] if matches else 1
        cards, stories_html, archive = [], [], []
        for mw in carousel:
            group = [m for m in matches if m["mw"] == mw]
            done = [m for m in group if m.get("result")]
            story = story_for(team, done[-1], comics) if done else None
            is_cur = mw == current
            if done:
                last = done[-1]
                label = last["result"]
                sub = f"{last['homeName']} {label['hs']}–{label['as']} {last['awayName']}"
            elif group:
                sub = f"{group[0]['homeName']} vs {group[0]['awayName']}"
            else:
                sub = "Awaiting"
            state = "complete" if done else "awaiting"
            cards.append(
                f'<button type="button" class="mwc-card{" is-current" if is_cur else ""}" data-mwc-card="{mw}" aria-pressed="{"true" if is_cur else "false"}">'
                f'<span class="mwc-card-kicker">Matchweek {mw}</span>'
                f'<span class="mwc-card-state mwc-{state}">{"Complete" if done else "Awaiting"}</span>'
                f'<span class="mwc-card-sub">{esc(sub)}</span></button>'
            )
            if story:
                stories_html.append(
                    f'<article class="mwc-story{" is-active" if is_cur else ""}" data-mwc-story="{mw}" id="mw-{mw}">'
                    f'<header class="mwc-story-head"><p class="eyebrow">Matchweek {mw} complete</p>'
                    f"<h3>{esc(story.get('headline') or f'Matchweek {mw}')}</h3>"
                    f'<p class="mwc-resultline">{esc(story.get("resultLine") or sub)}</p>'
                    f'<p class="mwc-jump">Match report: <a href="{esc(done[-1]["href"])}">{esc(done[-1]["homeName"])} vs {esc(done[-1]["awayName"])}</a>'
                    f'{(" · <a href=\"" + esc(story.get("comicUrl")) + "\">Open the BRYME Football Comic</a>") if story.get("comicUrl") else ""}'
                    f"</p></header>"
                    f'{render_panels(story, art)}</article>'
                )
                archive.append(
                    f'<li><a href="#mw-{mw}"><b>Matchweek {mw}</b><span>{esc(story.get("resultLine") or sub)}</span><em>Read comic</em></a></li>'
                )
            else:
                stories_html.append(
                    f'<article class="mwc-story{" is-active" if is_cur else ""}" data-mwc-story="{mw}" id="mw-{mw}">'
                    f'<header class="mwc-story-head"><p class="eyebrow">Matchweek {mw}</p>'
                    f"<h3>Awaiting matchweek {mw}</h3></header>"
                    f'{render_awaiting(art, group[0] if group else None, mw)}</article>'
                )
                archive.append(
                    f'<li class="is-await"><span><b>Matchweek {mw}</b><span>{esc(sub)}</span></span><em>Awaiting</em></li>'
                )
        chronicles = f"""
<section class="mwc" id="chronicles" data-mwc>
  <div class="section-head"><div><div class="eyebrow">Original BRYME comic</div>
  <h2>BRYME Matchweek Chronicles</h2></div></div>
  <p class="section-note">Cartoon storylines drawn from sourced full-time results. No broadcast stills, no player photographs. Speech bubbles are fictional squad chatter, not quotes.</p>
  <img class="mwc-masthead" src="{esc(art.get("masthead") or "")}" alt="BRYME Matchweek Chronicles original cartoon banner" width="1200" height="669" loading="lazy" decoding="async">
  <div class="mwc-carousel">
    <button type="button" class="sp-hero-arrow sp-hero-prev" data-mwc-prev aria-label="Previous matchweek">‹</button>
    <div class="mwc-track" data-mwc-track>{''.join(cards)}</div>
    <button type="button" class="sp-hero-arrow sp-hero-next" data-mwc-next aria-label="Next matchweek">›</button>
  </div>
  <div class="mwc-stories">{''.join(stories_html)}</div>
  <div class="mwc-archive" id="archive"><h3>Matchweek archive</h3><ul>{''.join(archive)}</ul></div>
</section>"""

    up_html = "".join(match_card(m, league, by_id) for m in upcoming) or '<p class="td-empty">No upcoming league fixture in the file.</p>'
    res_html = "".join(match_card(m, league, by_id) for m in reversed(completed)) or '<p class="td-empty">No sourced full-time result yet.</p>'

    others = [t for t in teams if t["league"] == league and t["id"] != team["id"]]
    other_links = "".join(
        f'<a href="{esc(team_href(t["league"], t["id"]))}"><img src="{esc(t["crest"])}" alt="" width="22" height="22">{esc(t["name"])}</a>'
        for t in others
    )
    rel = "".join(f'<a href="{esc(href)}">{esc(label)}</a>' for href, label in team.get("related") or [])

    crumb = (
        f'<div class="td-crumb"><a href="/">Home</a> / <a href="/sports/">Sports</a> / '
        f'<a href="/sports/{esc(league)}/">{esc(team["leagueName"])}</a> / '
        f'<a href="{esc(league_teams_href(league))}">Teams</a> / {esc(team["name"])}</div>'
    )
    body = f"""<body data-nav="sports" class="team-desk" style="--td:{esc(team['color'])}">
{HEADER}
<main class="td-wrap">
  {crumb}
  {chronicles}
  {hero}
  {overview}
  <section class="td-sec" id="fixtures">
    <div class="td-sec-head"><div><p class="eyebrow">Calendar</p><h2>Upcoming fixtures</h2></div>
    <a href="/sports/{esc(league)}/fixtures/">Full {esc(team['leagueName'])} list</a></div>
    <div class="td-list">{up_html}</div>
  </section>
  <section class="td-sec" id="results">
    <div class="td-sec-head"><div><p class="eyebrow">History</p><h2>Results</h2></div>
    <a href="/sports/{esc(league)}/results/">All sourced results</a></div>
    <div class="td-list">{res_html}</div>
  </section>
  <section class="td-sec" id="also">
    <div class="td-sec-head"><div><p class="eyebrow">Same league</p><h2>Other {esc(team['leagueName'])} clubs</h2></div>
    <a href="{esc(league_teams_href(league))}">All {esc(team['leagueName'])} teams</a></div>
    <div class="td-clubs">{other_links}</div>
    <div class="td-clubs" style="margin-top:14px">{rel}<a href="/sports/clubs/">Club directory</a><a href="/sports/">Sports hub</a></div>
  </section>
</main>
{FOOTER}
</body></html>"""
    return page_head(title, desc, url, page_ld) + body


def render_league_dir(league: str, club: list[dict], ctxs: dict) -> str:
    name = LEAGUE_NAME[league]
    title = f"{name} Teams — Fixtures & Results | BRYME"
    desc = f"Every {name} club on BRYME. Fixtures, sourced results and form for the 2026/27 season."
    url = SITE + league_teams_href(league)
    cards = []
    for t in club:
        matches = ctxs[t["id"]]["matches"]
        nxt = pick_next([m for m in matches if not m.get("result")])
        prev = pick_prev([m for m in matches if m.get("result")])
        nxt_line = f"Next · {nxt['homeName']} vs {nxt['awayName']}" if nxt else "No upcoming fixture in the file"
        prev_line = (
            f"Last · {prev['homeName']} {prev['result']['hs']}–{prev['result']['as']} {prev['awayName']}"
            if prev else "No sourced result yet"
        )
        cards.append(
            f'<a class="td-card" href="{esc(team_href(league, t["id"]))}" style="--td:{esc(t["color"])}">'
            f'<div class="td-card-top"><img src="{esc(t["crest"])}" alt="{esc(t["name"])} crest" width="56" height="56">'
            f'<div><b>{esc(t["name"])}</b><span>{esc(t.get("city") or name)}</span></div></div>'
            f'<p>{esc(nxt_line)}<br>{esc(prev_line)}</p></a>'
        )
    ld = [
        {"@context": "https://schema.org", "@type": "CollectionPage", "name": f"{name} teams",
         "description": desc, "url": url},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "BRYME Sports", "item": SITE + "/sports/"},
            {"@type": "ListItem", "position": 3, "name": name, "item": f"{SITE}/sports/{league}/"},
            {"@type": "ListItem", "position": 4, "name": f"{name} teams", "item": url},
        ]},
        {"@context": "https://schema.org", "@type": "ItemList", "name": f"{name} teams",
         "numberOfItems": len(club),
         "itemListElement": [
             {"@type": "ListItem", "position": i, "url": SITE + team_href(league, t["id"]), "name": t["name"]}
             for i, t in enumerate(club, 1)
         ]},
    ]
    body = f"""<body data-nav="sports" class="team-desk">
{HEADER}
<main class="td-wrap td-dir">
  <div class="td-crumb"><a href="/">Home</a> / <a href="/sports/">Sports</a> / <a href="/sports/{esc(league)}/">{esc(name)}</a> / Teams</div>
  <p class="eyebrow">{esc(name)} · 2026/27</p>
  <h1>{esc(name)} clubs</h1>
  <p class="lead">All {len(club)} clubs, each on its own page. Fixtures and sourced results. Matchweek comics stay on the big clubs only.</p>
  <div class="td-grid">{''.join(cards)}</div>
</main>
{FOOTER}
</body></html>"""
    return page_head(title, desc, url, ld) + body


def render_all_hub(teams: list[dict], ctxs: dict) -> str:
    title = "Football Clubs by League | BRYME"
    desc = "Every Premier League, La Liga, Serie A, Bundesliga and Ligue 1 club on BRYME — fixtures, sourced results and form."
    url = f"{SITE}/sports/teams/"
    blocks = []
    for lg in LEAGUE_ORDER:
        club = [t for t in teams if t["league"] == lg]
        cards = []
        for t in club:
            matches = ctxs[t["id"]]["matches"]
            nxt = pick_next([m for m in matches if not m.get("result")])
            line = f"Next · {nxt['oppName']}" if nxt else "Season list on the club page"
            cards.append(
                f'<a class="td-card" href="{esc(team_href(lg, t["id"]))}" style="--td:{esc(t["color"])}">'
                f'<div class="td-card-top"><img src="{esc(t["crest"])}" alt="{esc(t["name"])} crest" width="56" height="56">'
                f'<div><b>{esc(t["name"])}</b><span>{esc(line)}</span></div></div></a>'
            )
        blocks.append(
            f'<section class="td-league-block" id="{esc(lg)}">'
            f'<div class="section-head"><h2>{esc(LEAGUE_NAME[lg])}</h2>'
            f'<a href="{esc(league_teams_href(lg))}">Open the {esc(LEAGUE_NAME[lg])} club list</a></div>'
            f'<div class="td-grid">{"".join(cards)}</div></section>'
        )
    ld = [
        {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Football clubs by league",
         "description": desc, "url": url},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "BRYME Sports", "item": SITE + "/sports/"},
            {"@type": "ListItem", "position": 3, "name": "Teams", "item": url},
        ]},
    ]
    body = f"""<body data-nav="sports" class="team-desk">
{HEADER}
<main class="td-wrap td-dir">
  <div class="td-crumb"><a href="/">Home</a> / <a href="/sports/">Sports</a> / Teams</div>
  <p class="eyebrow">⚽ BRYME Sports</p>
  <h1>Clubs by league</h1>
  <p class="lead">Each club lives under its league. Open a league list, or go straight to a team page for fixtures and sourced results.</p>
  {''.join(blocks)}
</main>
{FOOTER}
</body></html>"""
    return page_head(title, desc, url, ld) + body


def rebuild_sitemap():
    urls = []
    for p in ROOT.rglob("index.html"):
        if any(x in p.parts for x in (".git", "reports", "node_modules", "__pycache__")):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        head = text[:5000]
        if "noindex" in head:
            continue
        rel = "/" + str(p.parent.relative_to(ROOT)).replace("\\", "/")
        if rel.endswith("/."):
            rel = ""
        if rel == "/.":
            rel = ""
        url = (rel if rel != "/" else "") + "/"
        can = re.search(r'rel="canonical" href="([^"]+)"', head)
        if can:
            dest = can.group(1).replace(SITE, "")
            if dest.rstrip("/") != url.rstrip("/") and dest.rstrip("/") + "/" != url:
                continue
        urls.append(SITE + (url if url.startswith("/") else "/" + url))
    seen, ordered = set(), []
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        ordered.append(u)
    ordered.sort()
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in ordered)
        + "</urlset>\n"
    )
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")
    return len(ordered)


def patch_clubs_directory(teams: list[dict]) -> int:
    p = ROOT / "sports/clubs/index.html"
    html = p.read_text(encoding="utf-8")
    n = 0
    for t in teams:
        href = team_href(t["league"], t["id"])
        for raw in (t["name"], H.escape(t["name"])):
            old = f"<td><b>{raw}</b></td>"
            old2 = f'<td><b><a href="/sports/teams/{t["slug"]}/">{raw} fixtures</a></b></td>'
            new = f'<td><b><a href="{href}">{raw}</a></b></td>'
            if old in html:
                html = html.replace(old, new, 1)
                n += 1
                break
            if old2 in html:
                html = html.replace(old2, new, 1)
                n += 1
                break
            # already linked last round with old path
            old3 = f'<td><b><a href="/sports/teams/{PRETTY.get(t["id"], t["id"])}/">{raw} fixtures</a></b></td>'
            if old3 in html:
                html = html.replace(old3, new, 1)
                n += 1
                break
    p.write_text(html, encoding="utf-8")
    return n


def patch_sports_hub() -> None:
    p = ROOT / "sports/index.html"
    html = p.read_text(encoding="utf-8")
    html = html.replace('href="/sports/teams/"', 'href="/sports/teams/"')
    # keep hub card, retarget copy
    html = html.replace(
        "<em>Clubs</em><b>Team pages</b><span>Fixtures, sourced results, form and BRYME matchweek comics for the biggest clubs.</span>",
        "<em>Clubs</em><b>Clubs by league</b><span>Every top-five club, filed under its own league.</span>",
    )
    p.write_text(html, encoding="utf-8")
    s = ROOT / "scripts/rebuild-sports-hub.py"
    t = s.read_text(encoding="utf-8")
    t = t.replace(
        "<em>Clubs</em><b>Team pages</b><span>Fixtures, sourced results, form and BRYME matchweek comics for the biggest clubs.</span>",
        "<em>Clubs</em><b>Clubs by league</b><span>Every top-five club, filed under its own league.</span>",
    )
    s.write_text(t, encoding="utf-8")


def patch_league_hubs(teams: list[dict]) -> int:
    n = 0
    for lg in LEAGUE_ORDER:
        p = ROOT / f"sports/{lg}/index.html"
        if not p.exists():
            continue
        html = p.read_text(encoding="utf-8")
        club = [t for t in teams if t["league"] == lg]
        cards = "".join(
            f'<a href="{esc(team_href(lg, t["id"]))}">'
            f'<img src="{esc(t["crest"])}" alt="{esc(t["name"])} crest" width="40" height="40">'
            f'<b>{esc(t["name"])}</b></a>'
            for t in club
        )
        block = (
            f'<section class="td-band" id="team-pages"><div class="shell">'
            f'<div class="td-band-inner"><div><p class="eyebrow">The {len(club)} clubs</p>'
            f'<h2>{esc(LEAGUE_NAME[lg])} teams</h2></div>'
            f'<a class="cta-ghost" href="{esc(league_teams_href(lg))}">Open the full club list</a></div>'
            f'<div class="td-band-grid">{cards}</div></div></section>'
        )
        if 'id="team-pages"' in html:
            html = re.sub(r'<section class="(?:tp-league-teams|td-band)" id="team-pages">[\s\S]*?</section>', block, html, count=1)
        elif '<section class="sp-hero"' in html:
            html = html.replace('<section class="sp-hero"', block + '<section class="sp-hero"', 1)
        else:
            html = html.replace("</main>", block + "</main>", 1)
        p.write_text(html, encoding="utf-8")
        n += 1
    return n


def patch_match_pages(teams: list[dict], ctxs: dict) -> int:
    by_id = {t["id"]: t for t in teams}
    n = 0
    seen = set()
    for t in teams:
        for m in ctxs[t["id"]]["matches"]:
            path = ROOT / f"sports/{t['league']}/matches/{m['slug']}/index.html"
            if not path.exists() or str(path) in seen:
                continue
            seen.add(str(path))
            html = path.read_text(encoding="utf-8")
            links = []
            for tid, name in ((m["homeId"], m["homeName"]), (m["awayId"], m["awayName"])):
                if tid in by_id:
                    tm = by_id[tid]
                    links.append(
                        f'<a href="{team_href(tm["league"], tm["id"])}">{H.escape(tm["name"])} fixtures</a>'
                    )
            if not links:
                continue
            jump = f'<p class="tp-match-jump">Team pages: {" · ".join(links)}</p>'
            if 'class="tp-match-jump"' in html:
                html = re.sub(r'<p class="tp-match-jump">[\s\S]*?</p>', jump, html, count=1)
            elif '<div class="sp-match-hero">' in html:
                html = html.replace('<div class="sp-match-hero">', jump + '<div class="sp-match-hero">', 1)
            else:
                continue
            path.write_text(html, encoding="utf-8")
            n += 1
    return n


def upsert_redirects(teams: list[dict]) -> int:
    p = ROOT / "_redirects"
    text = p.read_text(encoding="utf-8")
    lines = ["# Team pages live under each league"]
    n = 0
    for t in teams:
        canon = team_href(t["league"], t["id"])
        aliases = {f"/sports/teams/{t['slug']}/", f"/sports/teams/{t['id']}/"}
        if t["slug"] != t["id"]:
            aliases.add(f"/sports/{t['league']}/teams/{t['id']}/")
        for a in sorted(aliases):
            if a.rstrip("/") == canon.rstrip("/"):
                continue
            lines.append(f"{a}  {canon}  301")
            n += 1
    # leftover pretty slugs from the first 24-club hub
    for old, lg, tid in (
        ("manchester-united", "premier-league", "man-united"),
        ("manchester-city", "premier-league", "man-city"),
        ("newcastle-united", "premier-league", "newcastle"),
        ("inter-milan", "serie-a", "inter"),
        ("ac-milan", "serie-a", "milan"),
        ("bayern-munich", "bundesliga", "bayern"),
        ("borussia-dortmund", "bundesliga", "dortmund"),
        ("bayer-leverkusen", "bundesliga", "leverkusen"),
        ("rb-leipzig", "bundesliga", "leipzig"),
        ("paris-saint-germain", "ligue-1", "psg"),
        ("atletico-madrid", "la-liga", "atletico-madrid"),
    ):
        lines.append(f"/sports/teams/{old}/  {team_href(lg, tid)}  301")
        n += 1
    block = "\n".join(dict.fromkeys(lines)) + "\n"
    if "# Team page aliases" in text or "# Team pages live under each league" in text:
        text = re.sub(
            r"# Team page(?: aliases|s live under each league)[\s\S]*?(?=\n# |\Z)",
            block,
            text,
            count=1,
        )
    else:
        text = text.rstrip() + "\n" + block
    p.write_text(text, encoding="utf-8")
    return n


def clear_old_flat_team_pages(teams: list[dict]):
    root = ROOT / "sports/teams"
    keep = {"index.html"}
    if not root.exists():
        return
    for child in list(root.iterdir()):
        if child.name in keep:
            continue
        if child.is_dir():
            idx = child / "index.html"
            if idx.exists():
                idx.unlink()
            try:
                child.rmdir()
            except OSError:
                pass


def main():
    comics = load_json("content/matchweek-comics.json")
    results = load_json("content/results.json")
    fixtures_by_league = {lg: load_json(f"content/{fn}") for lg, fn in FIXTURE_FILES.items()}
    teams = build_registry(fixtures_by_league)
    (ROOT / "content/teams.json").write_text(
        json.dumps({"season": "2026/27", "urlPattern": "/sports/{league}/teams/{slug}/",
                    "comicsOnly": sorted(COMIC_TEAMS), "teams": teams}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    by_id = {t["id"]: t for t in teams}
    table_by, ranked_by = {}, {}
    for lg, fx in fixtures_by_league.items():
        table, ranked = standings_for(lg, fx, results)
        table_by[lg], ranked_by[lg] = table, ranked
    ctxs = {}
    for t in teams:
        lg = t["league"]
        ctxs[t["id"]] = {
            "matches": collect_team_matches(t["id"], fixtures_by_league[lg], results, lg),
            "table": table_by[lg],
            "ranked": ranked_by[lg],
            "comics": comics,
            "by_id": by_id,
            "teams": teams,
        }

    clear_old_flat_team_pages(teams)
    hub = ROOT / "sports/teams/index.html"
    hub.parent.mkdir(parents=True, exist_ok=True)
    hub.write_text(render_all_hub(teams, ctxs), encoding="utf-8")

    for lg in LEAGUE_ORDER:
        club = [t for t in teams if t["league"] == lg]
        dest = ROOT / "sports" / lg / "teams" / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render_league_dir(lg, club, ctxs), encoding="utf-8")
        for t in club:
            page = ROOT / "sports" / lg / "teams" / t["slug"] / "index.html"
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text(render_team_page(t, ctxs[t["id"]]), encoding="utf-8")

    clubs_n = patch_clubs_directory(teams)
    patch_sports_hub()
    lg_n = patch_league_hubs(teams)
    match_n = patch_match_pages(teams, ctxs)
    redir_n = upsert_redirects(teams)
    sm = rebuild_sitemap()
    print(f"Built {len(teams)} team pages across 5 leagues")
    print(f"Comics on {sum(1 for t in teams if t['comics'])} clubs")
    print(f"Clubs directory rows: {clubs_n}")
    print(f"League hubs: {lg_n}")
    print(f"Match pages linked: {match_n}")
    print(f"Redirects: {redir_n}")
    print(f"Sitemap URLs: {sm}")


if __name__ == "__main__":
    main()

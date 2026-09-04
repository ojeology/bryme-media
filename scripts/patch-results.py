#!/usr/bin/env python3
"""BRYME · Surgically convert 2 played-match pages to result pages.
Real Betis 1-0 Real Sociedad (La Liga, Fri 21 Aug) and Marseille 4-0 Strasbourg
(Ligue 1, Fri 21 Aug) — both verified via BBC Sport.
"""
import re, json, html as H

def esc(s): return H.escape(str(s), quote=True)

def patch(page, home, away, hs, as_, scorers, src_name, src_url, played):
    s = open(page, encoding='utf-8').read()
    orig = s

    # 1. <title>
    s = re.sub(r'<title>.*?</title>',
               f'<title>{home} {hs}-{as_} {away} — Result &amp; Analysis | BRYME</title>',
               s, count=1, flags=re.S)
    # 2. meta description
    desc = f'{home} {hs}-{as_} {away}: full-time result, goalscorers and BRYME post-match analysis.'
    s = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{esc(desc)}"', s, count=1)
    # 3. og/twitter
    ogt = f'{home} {hs}-{as_} {away} — Result &amp; Analysis | BRYME'
    s = re.sub(r'<meta property="og:title" content="[^"]*"', f'<meta property="og:title" content="{ogt}"', s, count=1)
    s = re.sub(r'<meta name="twitter:title" content="[^"]*"', f'<meta name="twitter:title" content="{ogt}"', s, count=1)
    s = re.sub(r'<meta property="og:description" content="[^"]*"', f'<meta property="og:description" content="{esc(desc)}"', s, count=1)
    s = re.sub(r'<meta name="twitter:description" content="[^"]*"', f'<meta name="twitter:description" content="{esc(desc)}"', s, count=1)

    # 4. hero pill
    s = s.replace('<span class="sp-pill">Upcoming — not yet played</span>',
                  f'<span class="sp-pill sp-pill-ft">FT {hs}&ndash;{as_}</span>', 1)

    # 5. replace ONLY the sp-truth div (not the following section)
    truth = re.search(r'<div class="sp-truth">.*?</div>', s, re.S)
    home_goals = ''.join(f'<li>{esc(p)}{f" <span>{m}&#x27;</span>" if m else ""}</li>' for p, m, team in scorers if team == 'home') or '<li class="sp-none">—</li>'
    away_goals = ''.join(f'<li>{esc(p)}{f" <span>{m}&#x27;</span>" if m else ""}</li>' for p, m, team in scorers if team == 'away') or '<li class="sp-none">—</li>'
    result_html = (
        f'<div class="sp-result"><span class="sp-pill sp-pill-ft">FT</span>\n'
        f'    <div class="sp-score"><span>{esc(home)}</span><b>{hs}</b><i>&ndash;</i><b>{as_}</b><span>{esc(away)}</span></div>\n'
        f'    <p class="sp-result-meta">Played {played}</p>\n'
        f'    <div class="sp-scorers"><div><b>{esc(home)}</b><ul>{home_goals}</ul></div>'
        f'<div><b>{esc(away)}</b><ul>{away_goals}</ul></div></div>\n'
        f'    <p class="sp-source-note">Result confirmed via <a href="{esc(src_url)}" rel="nofollow noopener">{esc(src_name)}</a> · checked {played}.</p></div>'
    )
    if truth:
        s = s[:truth.start()] + result_html + s[truth.end():]

    # 6. preview -> archived with note
    s = s.replace('<section class="sp-preview">',
                  '<section class="sp-preview sp-preview-archived">\n    <div class="sp-archive-note"><b>What BRYME said before kickoff</b><p>This preview was published before the match and is preserved unchanged. It is what we expected, not what happened.</p></div>', 1)

    # 7. JSON-LD result markers
    def ld_fix(m):
        try:
            d = json.loads(m.group(1))
            items = d if isinstance(d, list) else [d]
            for it in items:
                if it.get('@type') == 'SportsEvent':
                    it['eventStatus'] = 'https://schema.org/EventCompleted'
                if it.get('@type') == 'Article':
                    it['headline'] = f'{home} {hs}-{as_} {away}: result and analysis'
                    # datePublished stays the editorial publish date (from match-editorial.json);
                    # dateModified becomes the verification date (today) to match the test's rule:
                    # expected = res.verifiedOn || res.playedOn
                    if 'datePublished' not in it or not it['datePublished']:
                        it['datePublished'] = played
                    it['dateModified'] = '2026-08-22'
            # compact separators to match the site's JS JSON.stringify output
            return '<script type="application/ld+json">' + json.dumps(items, ensure_ascii=False, separators=(',', ':')) + '</script>'
        except Exception:
            return m.group(0)
    s = re.sub(r'<script type="application/ld\+json">(.*?)</script>', ld_fix, s, count=1, flags=re.S)

    if s != orig:
        open(page, 'w', encoding='utf-8').write(s)
        return True
    return False

if __name__ == '__main__':
    jobs = [
        ('sports/la-liga/matches/real-betis-vs-real-sociedad/index.html',
         'Real Betis', 'Real Sociedad', 1, 0,
         [('Riquelme', '63', 'home')],
         'BBC Sport — Real Betis v Real Sociedad', 'https://www.bbc.com/sport/football/live/cmz644qxd96yt',
         '2026-08-21'),
        ('sports/ligue-1/matches/marseille-vs-strasbourg/index.html',
         'Olympique de Marseille', 'RC Strasbourg', 4, 0,
         [('Gouiri', '46', 'home'), ('Gouiri', '68', 'home'), ('Abdallah', '89', 'home'), ('Højbjerg', '90+6', 'home'), ('El Mourabet', '59', 'away')],
         'BBC Sport — Marseille v Strasbourg', 'https://www.bbc.com/sport/football/live/c85yvv136pr0t',
         '2026-08-21'),
    ]
    for j in jobs:
        ok = patch(*j)
        print(('OK  ' if ok else 'SKIP') + '  ' + j[0])

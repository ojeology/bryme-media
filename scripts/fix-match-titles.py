#!/usr/bin/env python3
"""BRYME · Restore phrase-inclusive match titles (Result & Analysis / Preview, Form & Prediction).
The earlier 60-char SEO trim clipped these phrases. Regenerates <title>, og:title and
twitter:title from each page's h1 + state so the editorial workflow test passes and
the titles stay meaningful. Uses the compact format (no round/league suffix)."""
import os, re, json, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def esc(s): return H.escape(str(s), quote=True)

RESULTS = json.load(open(os.path.join(ROOT, 'content/results.json')))
ED = json.load(open(os.path.join(ROOT, 'content/match-editorial.json')))
FIELDS = ['overview','recentForm','headToHead','lastFiveMeetings','homeAwayForm','keyPlayers',
  'injuries','suspensions','expectedLineups','tacticalMatchup','historicalContext','underdog','outlook','scorePrediction']
def filled(e):
    if not e: return 0
    return sum(1 for k in FIELDS if (isinstance(e.get(k), list) and len(e[k])>0) or (isinstance(e.get(k), str) and e[k].strip() and len(e[k].strip())>12))

def h1_of(html):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S)
    return re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else ''

fixed = 0
for lg in ['premier-league','la-liga','serie-a','bundesliga','ligue-1']:
    d = os.path.join(ROOT, 'sports', lg, 'matches')
    if not os.path.isdir(d): continue
    for slug in os.listdir(d):
        p = os.path.join(d, slug, 'index.html')
        if not os.path.exists(p): continue
        html = open(p, encoding='utf-8').read()
        res = (RESULTS.get(lg) or {}).get(slug)
        e = (ED.get(lg) or {}).get(slug)
        # determine required phrase
        if res:
            phrase = f'Result & Analysis'
        elif e and filled(e) >= 3:
            phrase = 'Preview, Form & Prediction'
        else:
            continue
        h1 = h1_of(html)
        if not h1: continue
        if res:
            home, away = re.split(r'\s+v\s+', h1, maxsplit=1)
            new_title = f'{home} {res["homeScore"]}-{res["awayScore"]} {away} — Result & Analysis | BRYME'
        else:
            new_title = f'{h1} — Preview, Form & Prediction | BRYME'
        # current title
        t = re.search(r'<title>(.*?)</title>', html, re.S)
        cur = H.unescape(t.group(1)).strip() if t else ''
        if 'Result & Analysis' in cur or 'Preview, Form & Prediction' in cur:
            continue  # already fine
        html2 = re.sub(r'<title>.*?</title>', f'<title>{esc(new_title)}</title>', html, count=1, flags=re.S)
        html2 = re.sub(r'<meta property="og:title" content="[^"]*"', f'<meta property="og:title" content="{esc(new_title)}"', html2, count=1)
        html2 = re.sub(r'<meta name="twitter:title" content="[^"]*"', f'<meta name="twitter:title" content="{esc(new_title)}"', html2, count=1)
        if html2 != html:
            open(p, 'w', encoding='utf-8').write(html2)
            fixed += 1
            print(f"  {lg}/{slug}: {cur[:60]} -> {new_title[:70]}")
print("fixed:", fixed)

#!/usr/bin/env python3
"""BRYME · Mark played matches in the season fixture lists with FT scores."""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = json.load(open(os.path.join(ROOT, 'content/results.json')))

FIX_FILES = {
    'premier-league': 'sports/premier-league/fixtures/index.html',
    'la-liga': 'sports/la-liga/fixtures/index.html',
    'serie-a': 'sports/serie-a/fixtures/index.html',
    'bundesliga': 'sports/bundesliga/fixtures/index.html',
    'ligue-1': 'sports/ligue-1/fixtures/index.html',
}

done = 0
for lg, path in FIX_FILES.items():
    if not os.path.exists(path):
        continue
    s = open(path, encoding='utf-8').read()
    orig = s
    n = 0
    for slug, r in (RESULTS.get(lg) or {}).items():
        if r.get('homeScore') is None: continue
        # In the fixture row (sp-fixture) containing this match's link, replace the
        # kickoff-time span <span class="sp-fixt-time">20:00 UK</span> with an FT score.
        pat = re.compile(
            r'(<div class="sp-fixture"[^>]*>.*?<a[^>]*href="/sports/' + re.escape(lg) + r'/matches/' + re.escape(slug) + r'/"[^>]*>.*?</div>\s*<div class="sp-fixt-info"><span class="sp-fixt-time">)[^<]*(</span>)',
            re.S)
        s2 = pat.sub(lambda m: m.group(1) + 'FT ' + str(r['homeScore']) + '&ndash;' + str(r['awayScore']) + m.group(2), s, count=1)
        if s2 != s:
            s = s2
            n += 1
        else:
            print(f"  [no row] {lg}/{slug}")
    if s != orig:
        open(path, 'w', encoding='utf-8').write(s)
        print(f"  {path}: {n} fixtures marked FT")
        done += n
print("total marked:", done)

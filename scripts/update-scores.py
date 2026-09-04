#!/usr/bin/env python3
"""BRYME · Update scores everywhere a played match still shows as upcoming.
Applies FT tags to match-centre hero cards, league-hub hero cards, fixtures
lists, and fixes stale hub result counts/text.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = json.load(open(os.path.join(ROOT, 'content/results.json')))

# slug -> (league, score tag "3-0")
def played_map():
    m = {}
    for lg, matches in RESULTS.items():
        if lg.startswith('_'): continue
        for slug, r in matches.items():
            if r.get('homeScore') is None: continue
            m[(lg, slug)] = f"FT {r['homeScore']}&ndash;{r['awayScore']}"
    return m

PM = played_map()
print("played map:", PM)

def patch_card_tags(path, slug_prefix, score_tag, played_slugs, tag_regex=None):
    """Replace the <span class="sp-hero-tag">…</span> right after a card's href with FT score."""
    s = open(path, encoding='utf-8').read()
    orig = s
    n = 0
    for (lg, slug) in played_slugs:
        score = PM.get((lg, slug))
        if not score: continue
        # card pattern: <a class="sp-hero-card... href="/sports/LG/matches/SLUG/"> ... <span class="sp-hero-tag">OLD</span>
        pat = re.compile(
            r'(<a class="sp-hero-card[^"]*" href="/sports/' + re.escape(lg) + r'/matches/' + re.escape(slug) + r'/"\s*[^>]*>.*?<span class="sp-hero-tag">)[^<]*(</span>)',
            re.S)
        s2, cnt = pat.subn(lambda m: m.group(1) + score + m.group(2), s, count=1)
        if cnt:
            s = s2
            n += 1
        else:
            print(f"  [no card match] {lg}/{slug} in {path}")
    if s != orig:
        open(path, 'w', encoding='utf-8').write(s)
        print(f"  {path}: updated {n} cards")
    return n

# All played matches by file
def slugs_for(league):
    return [(lg, slug) for (lg, slug) in PM if lg == league]

for lg in ('premier-league', 'la-liga', 'ligue-1'):
    patch_card_tags(f'sports/{lg}/matches/index.html', lg, None, slugs_for(lg))
    # league hub (exists for la-liga/ligue-1/premier-league)
    hub = f'sports/{lg}/index.html'
    if os.path.exists(hub):
        patch_card_tags(hub, lg, None, slugs_for(lg))

# Fix hub result-count texts
def fix_count(path, old, new):
    s = open(path, encoding='utf-8').read()
    if old in s:
        s = s.replace(old, new, 1)
        open(path, 'w', encoding='utf-8').write(s)
        print(f"  {path}: count '{old}' -> '{new}'")
    else:
        print(f"  {path}: count text '{old}' not found")

fix_count('sports/la-liga/index.html', '6 verified results', '7 verified results')
fix_count('sports/ligue-1/index.html',
          'Season starts Friday 21 August 2026 — no results yet',
          '1 verified result — Marseille 4-0 Strasbourg')
# PL hub results text?
pl = open('sports/premier-league/index.html').read()
m = re.search(r'Results</b><span>[^<]*</span>', pl)
print("  PL hub results text:", m.group(0) if m else "none")

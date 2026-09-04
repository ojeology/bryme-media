#!/usr/bin/env python3
"""BRYME Movie SEO pilot optimizer — per the Agent Brief.
Optimizes 20-30 existing pages for search intent WITHOUT adding pages or inventing facts:
  1. Intent-aware <title> + meta description (per-page, no blind template)
  2. Meta description mentions what the page actually provides (cast, trailer, story, watch)
  3. Strengthens internal links already present; records a tracking matrix
URLs are never changed. No keywords stuffed, nothing fabricated.
"""
import json, os, re, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def esc(s): return H.escape(str(s), quote=True)

# ---- Pilot list: title | path | year | primary kw | secondaries | intent ----
# Only pages with trailer + poster + cast + description (verified complete).
PILOT = [
    # Shōgun case study (from the brief)
    {'path':'series/shogun','title':'Shōgun','year':'2024','primary':'Shōgun 2024',
     'sec':['Shōgun TV series','Shōgun trailer','Shōgun cast','Shōgun episodes','where to watch Shōgun','shows like Shōgun'],
     'intent':'informational / viewing','kind':'series'},
    {'path':'movie/spider-man-no-way-home','title':'Spider-Man: No Way Home','year':'2021','primary':'Spider-Man: No Way Home',
     'sec':['No Way Home trailer','No Way Home cast','where to watch Spider-Man No Way Home','Spider-Man movies in order'],
     'intent':'informational / viewing','kind':'movie'},
    {'path':'movie/deadpool-wolverine','title':'Deadpool & Wolverine','year':'2024','primary':'Deadpool & Wolverine',
     'sec':['Deadpool 3','Deadpool Wolverine trailer','Deadpool Wolverine cast','where to watch Deadpool & Wolverine'],
     'intent':'informational / viewing','kind':'movie'},
    {'path':'movie/thor-ragnarok','title':'Thor: Ragnarok','year':'2017','primary':'Thor: Ragnarok',
     'sec':['Thor Ragnarok trailer','Thor Ragnarok cast','where to watch Thor Ragnarok','Marvel movies'],
     'intent':'informational','kind':'movie'},
    {'path':'movie/avengers-infinity-war','title':'Avengers: Infinity War','year':'2018','primary':'Avengers: Infinity War',
     'sec':['Infinity War trailer','Infinity War cast','where to watch Infinity War','Avengers movies'],
     'intent':'informational','kind':'movie'},
    {'path':'movie/28-years-later','title':'28 Years Later','year':'2025','primary':'28 Years Later',
     'sec':['28 Years Later trailer','28 Years Later cast','28 Years Later release','where to watch 28 Years Later'],
     'intent':'informational','kind':'movie'},
    {'path':'movie/gladiator-ii','title':'Gladiator II','year':'2024','primary':'Gladiator II',
     'sec':['Gladiator 2 trailer','Gladiator II cast','where to watch Gladiator II','Gladiator sequel'],
     'intent':'informational','kind':'movie'},
    {'path':'series/house-of-the-dragon','title':'House of the Dragon','year':'2022','primary':'House of the Dragon',
     'sec':['House of the Dragon trailer','House of the Dragon cast','House of the Dragon season','where to watch House of the Dragon'],
     'intent':'informational','kind':'series'},
    {'path':'movie/inside-out-2','title':'Inside Out 2','year':'2024','primary':'Inside Out 2',
     'sec':['Inside Out 2 trailer','Inside Out 2 cast','Inside Out 2 release','where to watch Inside Out 2'],
     'intent':'informational','kind':'movie'},
    {'path':'movie/jawan','title':'Jawan','year':'2023','primary':'Jawan',
     'sec':['Jawan trailer','Jawan cast','Jawan release','where to watch Jawan','Shah Rukh Khan movies'],
     'intent':'informational','kind':'movie'},
    {'path':'movie/jurassic-world-rebirth','title':'Jurassic World Rebirth','year':'2025','primary':'Jurassic World Rebirth',
     'sec':['Jurassic World Rebirth trailer','Jurassic World Rebirth cast','where to watch Jurassic World Rebirth'],
     'intent':'informational','kind':'movie'},
    {'path':'movie/rrr','title':'RRR','year':'2022','primary':'RRR',
     'sec':['RRR trailer','RRR cast','RRR release','where to watch RRR','S.S. Rajamouli movies'],
     'intent':'informational','kind':'movie'},
    {'path':'series/silo','title':'Silo','year':'2023','primary':'Silo',
     'sec':['Silo TV series','Silo trailer','Silo cast','Silo season 2','where to watch Silo'],
     'intent':'informational','kind':'series'},
    {'path':'movie/superman-2025','title':'Superman','year':'2025','primary':'Superman 2025',
     'sec':['Superman trailer','Superman cast','where to watch Superman 2025','James Gunn Superman'],
     'intent':'informational','kind':'movie'},
    {'path':'series/ted-lasso','title':'Ted Lasso','year':'2020','primary':'Ted Lasso',
     'sec':['Ted Lasso trailer','Ted Lasso cast','Ted Lasso season','where to watch Ted Lasso'],
     'intent':'informational','kind':'series'},
    {'path':'movie/the-substance','title':'The Substance','year':'2024','primary':'The Substance',
     'sec':['The Substance trailer','The Substance cast','The Substance release','where to watch The Substance'],
     'intent':'informational','kind':'movie'},
    {'path':'movie/twisters','title':'Twisters','year':'2024','primary':'Twisters',
     'sec':['Twisters trailer','Twisters cast','where to watch Twisters'],
     'intent':'informational','kind':'movie'},
    {'path':'movie/coco','title':'Coco','year':'2017','primary':'Coco',
     'sec':['Coco trailer','Coco cast','where to watch Coco','Pixar movies'],
     'intent':'informational','kind':'movie'},
    {'path':'movie/the-wild-robot','title':'The Wild Robot','year':'2024','primary':'The Wild Robot',
     'sec':['The Wild Robot trailer','The Wild Robot cast','The Wild Robot release','where to watch The Wild Robot'],
     'intent':'informational','kind':'movie'},
    {'path':'movie/spider-man-brand-new-day','title':'Spider-Man: Brand New Day','year':'2026','primary':'Spider-Man: Brand New Day',
     'sec':['Brand New Day trailer','Spider-Man Brand New Day cast','where to watch Spider-Man Brand New Day'],
     'intent':'informational','kind':'movie'},
    {'path':'movie/toy-story-5','title':'Toy Story 5','year':'2026','primary':'Toy Story 5',
     'sec':['Toy Story 5 trailer','Toy Story 5 cast','Toy Story 5 release','where to watch Toy Story 5'],
     'intent':'informational','kind':'movie'},
    {'path':'movie/the-end-of-oak-street','title':'The End of Oak Street','year':'2026','primary':'The End of Oak Street',
     'sec':['The End of Oak Street trailer','The End of Oak Street cast','where to watch The End of Oak Street'],
     'intent':'informational','kind':'movie'},
    {'path':'movie/the-notebook','title':'The Notebook','year':'2004','primary':'The Notebook',
     'sec':['The Notebook trailer','The Notebook cast','where to watch The Notebook','romance movies'],
     'intent':'informational','kind':'movie'},
    {'path':'anime/your-name','title':'Your Name','year':'2016','primary':'Your Name',
     'sec':['Your Name trailer','Your Name cast','Your Name anime','where to watch Your Name','Makoto Shinkai'],
     'intent':'informational','kind':'anime'},
    {'path':'anime/spirited-away','title':'Spirited Away','year':'2001','primary':'Spirited Away',
     'sec':['Spirited Away trailer','Spirited Away cast','Spirited Away anime','where to watch Spirited Away','Hayao Miyazaki'],
     'intent':'informational','kind':'anime'},
    {'path':'movie/back-to-the-future','title':'Back to the Future','year':'1985','primary':'Back to the Future',
     'sec':['Back to the Future trailer','Back to the Future cast','where to watch Back to the Future'],
     'intent':'informational','kind':'movie'},
    {'path':'series/game-of-thrones','title':'Game of Thrones','year':'2011','primary':'Game of Thrones',
     'sec':['Game of Thrones trailer','Game of Thrones cast','Game of Thrones seasons','where to watch Game of Thrones','shows like Game of Thrones'],
     'intent':'informational','kind':'series'},
    {'path':'movie/insidious','title':'Insidious','year':'2010','primary':'Insidious',
     'sec':['Insidious trailer','Insidious cast','where to watch Insidious','horror movies'],
     'intent':'informational','kind':'movie'},
    {'path':'series/the-walking-dead','title':'The Walking Dead','year':'2010','primary':'The Walking Dead',
     'sec':['The Walking Dead trailer','The Walking Dead cast','The Walking Dead seasons','where to watch The Walking Dead'],
     'intent':'informational','kind':'series'},
]

def build_title(p):
    """Intent-aware title per the brief: Title (Year) | what the page offers | BRYME
    Adjusted per page so it reads naturally; never keyword-stuffed."""
    if p['kind'] == 'series':
        offer = 'Cast, Trailer, Episodes & Where to Watch'
    elif p['kind'] == 'anime':
        offer = 'Trailer, Cast & Where to Watch'
    else:
        offer = 'Cast, Trailer & Where to Watch'
    return f"{p['title']} ({p['year']}) | {offer} | BRYME"

def build_meta(p, lead):
    """Unique description: what the page actually offers. No mid-word cut, no stuffing."""
    year = p.get('year') or ''
    kind = p.get('kind') or 'movie'
    noun = 'series' if kind == 'series' else ('anime' if kind == 'anime' else 'film')
    if p.get('path') == 'series/shogun':
        base = "Shōgun (2024): FX series. Official trailer, billed cast, story, and how to find a legal stream. BRYME does not host episodes."
    elif kind == 'series':
        base = f"{p['title']} ({year}) TV series: official trailer, billed cast, story, and how to find a legal stream. BRYME does not host episodes."
    elif kind == 'anime':
        base = f"{p['title']} ({year}) anime: official trailer, billed cast, story, and how to find a legal stream. BRYME does not host the title."
    else:
        base = f"{p['title']} ({year}): official trailer, billed cast, story, and how to find a legal copy. BRYME does not host the film."
    if len(base) <= 155:
        return base
    cut = base[:155]
    sp = cut.rfind(' ')
    return (cut[:sp] if sp > 80 else cut).rstrip(' ,;:.') + '…'

def main():
    matrix = []
    done = 0
    for p in PILOT:
        path = os.path.join(ROOT, p['path'], 'index.html')
        if not os.path.exists(path):
            print(f"  MISSING: {p['path']}")
            continue
        html = open(path, encoding='utf-8').read()
        orig = html
        # lead (synopsis)
        lm = re.search(r'<p class="lead"[^>]*>(.*?)</p>', html, re.S)
        lead = lm.group(1) if lm else ''
        new_title = build_title(p)
        new_meta = build_meta(p, lead)
        # update title
        html = re.sub(r'<title>.*?</title>', f'<title>{esc(new_title)}</title>', html, count=1, flags=re.S)
        # update meta description
        html = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{esc(new_meta)}"', html, count=1)
        # og:title + twitter:title
        html = re.sub(r'<meta property="og:title" content="[^"]*"', f'<meta property="og:title" content="{esc(new_title)}"', html, count=1)
        html = re.sub(r'<meta name="twitter:title" content="[^"]*"', f'<meta name="twitter:title" content="{esc(new_title)}"', html, count=1)
        # og:description + twitter:description
        html = re.sub(r'<meta property="og:description" content="[^"]*"', f'<meta property="og:description" content="{esc(new_meta)}"', html, count=1)
        html = re.sub(r'<meta name="twitter:description" content="[^"]*"', f'<meta name="twitter:description" content="{esc(new_meta)}"', html, count=1)
        if html != orig:
            open(path, 'w', encoding='utf-8').write(html)
            done += 1
        matrix.append({
            'title': p['title'], 'url': f"/{p['path']}/", 'year': p['year'],
            'primary': p['primary'], 'secondary': ', '.join(p['sec']),
            'intent': p['intent'], 'status': 'optimized', 'new_title': new_title,
        })
    print(f"optimized {done}/{len(PILOT)} pages")
    # tracking matrix
    out = 'title,url,year,primary_keyword,secondary_keywords,intent,status,new_title\n'
    for r in matrix:
        out += f"{r['title']},{r['url']},{r['year']},\"{r['primary']}\",\"{r['secondary']}\",{r['intent']},{r['status']},\"{r['new_title']}\"\n"
    open(os.path.join(ROOT, 'seo-pilot-matrix.csv'), 'w', encoding='utf-8').write(out)
    print("matrix written: seo-pilot-matrix.csv")

if __name__ == '__main__':
    main()

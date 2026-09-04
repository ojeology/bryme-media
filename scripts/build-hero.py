#!/usr/bin/env python3
"""Build the /entertainment/ hero carousel: 10 slides, each with a real backdrop
image (YouTube trailer thumbnail as full-bleed background), age badge, rating,
description, Watch Now + More Info, and dots. The 10 titles are the top-rated
catalog titles that have official trailer embeds."""
import json, os, re, sys, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from nm_catalog import unique

def esc(s): return H.escape(str(s), quote=True)
uniq = unique()
emb = json.load(open(os.path.join(ROOT, 'scripts/embeds.json')))

# top 10 by rating among embedded titles (ties broken by year desc)
cands = []
for slug, (title, td, rating, year, cert) in uniq.items():
    if not emb.get(slug):
        continue
    cands.append((slug, title, td, rating or 0, year, cert or '', emb[slug]))
cands.sort(key=lambda c: (-c[3], -c[4]))
TOP10 = cands[:10]

# hand-written short descriptions (match the reference style: 1-2 lines)
DESC = {
 'project-hail-mary': 'Science teacher Ryland Grace wakes up on a spaceship light years from home with no recollection of who he is or how he got there.',
 'swapped': 'A tiny woodland creature and a majestic bird swap bodies — forcing two sworn enemies to team up and survive the wildest adventure of their lives.',
 'avatar-aang-2026': 'The Avatar returns. Aang and his friends face a new threat that will test the balance of the four nations.',
 'game-of-thrones': 'Nine noble families fight for control of the Iron Throne while an ancient enemy returns from beyond the Wall.',
 'the-rookie': 'Small-town guy John Nolan becomes the LAPD\u2019s oldest rookie, starting over in the most dangerous job in the world.',
 'from': 'In a mysterious town, everyone is trapped. The residents search for a way out while unknown forces keep them from leaving.',
 'forrest-gump': 'Imprisoned in no one\u2019s story but his own, Forrest Gump runs through three decades of American history.',
 'spirited-away': 'A young girl wanders into a world of spirits, where she must work in a bathhouse to free her parents.',
 'house-of-the-dragon': 'The Targaryen dynasty is at the height of its power \u2014 and on the edge of civil war.',
 'chainsaw-man-reze': 'Denji returns to the big screen in the Reze Arc \u2014 a violent, tender chapter in the Chainsaw Man saga.',
}

def slide(slug, title, td, rating, year, cert, vid, active):
    tb = 'tb-series' if td == 'series' else 'tb-anime' if td == 'anime' else 'tb-movie'
    tlabel = 'SERIES' if td == 'series' else 'ANIME' if td == 'anime' else 'MOVIE'
    act = ' is-active' if active else ''
    age = cert or 'U/A 13+'
    img = f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg'
    desc = DESC.get(slug, 'Watch the official trailer and explore the full catalogue on BRYME.')
    return (f'<div class="hero-slide{act}" data-slide data-video="{vid}" data-title="{esc(title)}" '
            f'data-url="/{td}/{slug}/" data-age="{esc(age)}" '
            f'style="background-image:url(\'{img}\')">'
            f'<div class="hero-slide-shade"></div>'
            f'<div class="shell hero-slide-inner"><div class="hero-trend-tag">\U0001f525 TRENDING NOW</div>'
            f'<div class="hero-slide-kicker"><span class="type-badge {tb}">{tlabel}</span>'
            f'<span class="chip-hd">HD</span><span>{year}</span><span class="dot">\u00b7</span><span>{esc(tlabel.title())}</span></div>'
            f'<h1>{esc(title)}</h1><p class="hero-slide-rating">\u2605 {rating}/10</p>'
            f'<p>{esc(desc)}</p>'
            f'<div class="hero-actions"><button type="button" class="cta hero-watch" data-hero-watch>\u25b6 Watch Now</button>'
            f'<a class="cta cta-ghost" href="/{td}/{slug}/">More Info</a></div></div></div>')

slides = ''.join(slide(*c, active=(i == 0)) for i, c in enumerate(TOP10))
dots = ''.join(
    f'<button type="button" class="hero-dot{" is-active" if i == 0 else ""}" data-hero-dot="{i}" role="tab" '
    f'aria-label="{esc(c[1])}" aria-selected="{str(i == 0).lower()}"></button>'
    for i, c in enumerate(TOP10))

hero = ('<section class="hero-carousel" data-hero role="region" aria-roledescription="carousel" '
        'aria-label="Featured titles" data-interval="5000"><div class="hero-slides">' + slides + '</div>'
        '<button type="button" class="hero-ctrl hero-prev" data-hero-prev aria-label="Previous featured title">&#8249;</button>'
        '<button type="button" class="hero-ctrl hero-next" data-hero-next aria-label="Next featured title">&#8250;</button>'
        '<div class="hero-dots" data-hero-dots role="tablist" aria-label="Featured title slides">' + dots + '</div>'
        '<button type="button" class="hero-vctrl hero-mute" data-hero-mute aria-label="Unmute trailer" hidden>&#128263;</button>'
        '<button type="button" class="hero-vctrl hero-pause" data-hero-pause aria-label="Pause rotation" hidden>&#9208;</button>'
        '<div class="hero-video" data-hero-video hidden></div></section>')

ent = os.path.join(ROOT, 'entertainment', 'index.html')
s = open(ent, encoding='utf-8').read()
old = re.search(r'<section class="hero-carousel".*?</section>', s, re.S)
if not old:
    print('ERR: hero not found'); sys.exit(1)
s = s[:old.start()] + hero + s[old.end():]
open(ent, 'w', encoding='utf-8').write(s)
print('hero rebuilt with', len(TOP10), 'slides')
for i, c in enumerate(TOP10):
    print(f'  {i+1}. {c[1]} ({c[2]}) ★{c[3]} — img={emb[c[0]]}')

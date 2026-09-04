#!/usr/bin/env python3
"""Wire official trailer embeds into BRYME title pages from scripts/embeds.json.
For each catalog slug with an ID: replace any trailer-unavailable placeholder with a
real data-trailer-box. Pages already carrying a trailer box are left untouched."""
import json, os, re, sys, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
embeds = json.load(open(os.path.join(ROOT, 'scripts/embeds.json')))
esc = lambda s: H.escape(str(s), quote=True)

def box_html(vid, title):
    return (f'<section class="shell trailer-section" id="trailer"><div class="trailer-section-inner" data-trailer-box '
            f"data-trailer-candidates='[{{\"id\":\"{vid}\",\"type\":\"official-trailer\",\"label\":\"Official Trailer\",\"channel\":\"YouTube\",\"verified\":true,\"watch\":\"https://www.youtube.com/watch?v={vid}\"}}]' "
            f'data-trailer-title="{esc(title)}"><div class="trailer-head"><span class="eyebrow">Trailer</span>'
            f'<span class="trailer-status t-ok">\U0001f7e2 Official Trailer</span></div>'
            f'<div class="trailer-frame" data-trailer-id="{vid}"><img loading="lazy" src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="{esc(title)} trailer thumbnail">'
            f'<button type="button" class="trailer-play">Play trailer</button></div>'
            f'<div class="trailer-controls" data-trailer-controls hidden><button type="button" class="cta" data-trailer-unmute>Unmute</button>'
            f'<a class="quiet-link" href="https://www.youtube.com/watch?v={vid}" target="_blank" rel="noopener">Watch on YouTube</a></div>'
            f'<p class="trailer-meta">YouTube \u00b7 Official trailer</p>'
            f'<div class="trailer-error" data-trailer-error hidden><b>Trailer currently unavailable.</b>'
            f'<span class="trailer-error-actions"><a class="quiet-link" data-trailer-watch target="_blank" rel="noopener">Watch on YouTube</a>'
            f'<button type="button" class="trailer-retry" data-trailer-retry>Try again</button></span></div></div></section>')

wired = 0; skipped = 0; notfound = 0
for slug, vid in embeds.items():
    # find the page in any type dir
    target = None
    for td in ('movie', 'series', 'anime'):
        p = os.path.join(ROOT, td, slug, 'index.html')
        if os.path.exists(p):
            target = p
            break
    if not target:
        notfound += 1
        continue
    s = open(target, encoding='utf-8').read()
    if 'data-trailer-box' in s:
        skipped += 1
        continue
    m = re.search(r'<section class="shell trailer-section" id="trailer"><div class="trailer-unavailable">.*?</div></section>', s, re.S)
    if not m:
        # maybe no trailer section at all -> append one before </main>
        title = (re.search(r'<h1>([^<]+)</h1>', s) or [None, slug])[1]
        box = box_html(vid, title)
        if '</main>' in s:
            s = s.replace('</main>', box + '</main>')
        else:
            s = s.replace('</body>', box + '</body>')
        open(target, 'w', encoding='utf-8').write(s)
        wired += 1
        continue
    title = (re.search(r'<h1>([^<]+)</h1>', s) or [None, slug])[1]
    s = s[:m.start()] + box_html(vid, title) + s[m.end():]
    open(target, 'w', encoding='utf-8').write(s)
    wired += 1

print('wired:', wired, '| already had box:', skipped, '| no page:', notfound)

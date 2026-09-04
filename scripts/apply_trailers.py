#!/usr/bin/env python3
"""Apply verified trailer IDs to catalogue entries by slug/id.
Usage: python3 apply_trailers.py 'slug=ID' ..."""
import json, sys, re

c = json.load(open('content/catalogue.json'))
by_id = {m['id']: m for m in c}
applied = 0
for arg in sys.argv[1:]:
    if '=' not in arg: continue
    slug, vid = arg.split('=', 1)
    vid = vid.strip()
    m = by_id.get(slug)
    if not m:
        print(f"SKIP {slug}: not in catalogue")
        continue
    m['youtubeId'] = vid
    m['trailer'] = f"https://www.youtube.com/watch?v={vid}"
    m['poster'] = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
    applied += 1
    print(f"OK {slug} <- {vid}")
json.dump(c, open('content/catalogue.json','w'), indent=1, ensure_ascii=False)
print(f"Applied {applied}. Catalogue: {len(c)}")

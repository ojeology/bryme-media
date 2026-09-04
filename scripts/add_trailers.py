#!/usr/bin/env python3
"""Update catalogue.json with verified trailer IDs.
Usage: python3 add_trailers.py 'slug1=ID1' 'slug2=ID2' ...
Only updates youtubeId + poster (poster = yt thumbnail). Never touches other fields."""
import json, sys, re

path = 'content/catalogue.json'
data = json.load(open(path))

def verify(id):
    """Verify a YouTube ID via oEmbed — returns (ok, author, title) or (False, '', '')."""
    import urllib.request
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={id}&format=json"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            j = json.loads(r.read().decode())
            return True, j.get('author_name',''), j.get('title','')
    except Exception:
        return False, '', ''

updated = []
failed = []
for arg in sys.argv[1:]:
    if '=' not in arg: continue
    slug, vid = arg.split('=', 1)
    vid = vid.strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', vid):
        print(f"SKIP {slug}: bad ID format {vid}")
        continue
    ok, auth, title = verify(vid)
    found = next((m for m in data if m['id'] == slug), None)
    if not found:
        print(f"SKIP {slug}: not in catalogue")
        continue
    if not ok:
        failed.append((slug, vid))
        print(f"FAIL {slug}: {vid} not found on YouTube")
        continue
    found['youtubeId'] = vid
    found['poster'] = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
    found['trailer'] = f"https://www.youtube.com/watch?v={vid}"
    updated.append((slug, auth, title))
    print(f"OK {slug} <- {vid} ({auth}: {title[:40]})")

json.dump(data, open(path, 'w'), indent=1, ensure_ascii=False)
print(f"\nDone. Updated {len(updated)}. Failed {len(failed)}.")

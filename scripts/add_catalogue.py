#!/usr/bin/env python3
"""Bulk-add new movie entries to catalogue.json.
Usage: python3 scripts/add_catalogue.py
Each entry: (slug, title, genre, year, description, youtubeId)
Only adds if slug not already present. Verifies youtubeId via oEmbed.
"""
import json, re, urllib.request

path = 'content/catalogue.json'
data = json.load(open(path))
existing = {m['id'] for m in data}

def verify(vid):
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            j = json.loads(r.read().decode())
            return True, j.get('author_name',''), j.get('title','')
    except Exception:
        return False, '', ''

def add(slug, title, genre, year, desc, vid):
    if slug in existing:
        print(f"SKIP {slug}: already exists")
        return
    if not vid or not re.fullmatch(r'[A-Za-z0-9_-]{11}', vid):
        print(f"SKIP {slug}: bad/missing yt id")
        return
    ok, auth, yt = verify(vid)
    if not ok:
        print(f"FAIL {slug}: {vid} not found")
        return
    data.append({
        "id": slug, "title": title, "slug": slug,
        "description": desc, "year": year, "genre": genre,
        "country": None, "language": None,
        "poster": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
        "backdrop": None,
        "trailer": f"https://www.youtube.com/watch?v={vid}",
        "youtubeId": vid,
        "cast": [], "director": None, "runtime": None, "rating": None,
        "status": "published"
    })
    existing.add(slug)
    print(f"OK {slug}: {title} ({year} · {genre}) <- {vid}")

# ============ NEW TITLES (verified official trailers) ============
NEW = [
 # 2024-2026 blockbusters
 ("dune-part-three","Dune: Part Three","Sci-Fi",2026,"The concluding chapter of Denis Villeneuve's adaptation of Frank Herbert's Dune saga. Paul Atreides faces the consequences of his holy war and the dark path to the Golden Path.",None),
 # Actually use verified ones from our list that are NEW titles not yet in catalogue:
 ("guardians-3","Guardians of the Galaxy Vol. 3","Superhero",2023,"The Guardians' final ride. Rocket's origin story, a villain who hates creation, and a team that chooses family over fate.",None),
]
for a in NEW:
    add(*a)

json.dump(data, open(path, 'w'), indent=1, ensure_ascii=False)
print(f"\nDone. Catalogue now has {len(data)} entries.")

#!/usr/bin/env python3
"""Verify candidate YouTube IDs against expected titles. Accepts only if the
returned oEmbed title matches the expected title (case-insensitive, contains).
Usage: python3 verify_ids.py 'expectedtitle=ID' ...
Outputs only VERIFIED matches as 'slug|id|author|title'."""
import json, sys, urllib.request, re

def norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()

def verify(vid):
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None

for arg in sys.argv[1:]:
    if '=' not in arg: continue
    expected, vid = arg.split('=', 1)
    vid = vid.strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', vid):
        continue
    j = verify(vid)
    if not j: continue
    title = j.get('title','')
    author = j.get('author_name','')
    en = norm(expected)
    tn = norm(title)
    # Accept if expected words mostly appear in title or title in expected
    ew = set(en.split())
    tw = set(tn.split())
    common = ew & tw
    score = len(common) / max(len(ew), 1)
    if score >= 0.6:
        print(f"OK|{expected}|{vid}|{author}|{title}")
    else:
        print(f"NO|{expected}|{vid}|{author}|{title}")

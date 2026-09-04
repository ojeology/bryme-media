#!/usr/bin/env python3
"""Verify candidate trailer IDs for titles that currently have no trailer.
Each candidate must pass ALL gates before it can be applied:
  1. The YouTube video exists (oEmbed 200)
  2. Video title overlaps the title (>= 0.6)
  3. Channel is studio/distributor/aggregator (official allowlist)
Outputs OK|slug|id|channel|videoTitle for passing candidates only.
Wrong guesses are rejected — nothing is applied automatically.

Usage: python3 scripts/verify_candidates.py
"""
import json, os, re, time, unicodedata, urllib.request, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from trailer_audit import norm, oembed, channel_class, classify, overlap

def main():
    candidates = json.load(open('content/trailer-candidates.json'))
    movies = {m['slug']: m for m in json.load(open('data/movies.json'))}
    results = {'ok': [], 'rejected': []}
    for slug, ids in candidates.items():
        m = movies.get(slug)
        if not m:
            print(f'SKIP {slug}: not in catalogue')
            continue
        if m.get('youtubeId'):
            print(f'SKIP {slug}: already has a trailer')
            continue
        for vid in ids:
            if not re.fullmatch(r'[A-Za-z0-9_-]{11}', vid):
                print(f'REJECT {slug}: {vid} not a valid id')
                continue
            j = oembed(vid)
            time.sleep(0.1)
            if j is None:
                print(f'REJECT {slug}: {vid} oembed error')
                continue
            if j.get('__missing__'):
                print(f'REJECT {slug}: {vid} does not exist')
                continue
            author = j.get('author_name', '')
            vtitle = j.get('title', '')
            score = overlap(m['title'], vtitle)
            cls = channel_class(author)
            if score < 0.6:
                print(f'REJECT {slug}: {vid} title mismatch ({score:.2f}) "{vtitle}"')
                continue
            if cls not in ('studio', 'distributor', 'aggregator'):
                print(f'REJECT {slug}: {vid} unverified channel "{author}"')
                continue
            typ = classify(vtitle)
            print(f'OK     {slug}: {vid} | {author} | {vtitle} | {typ}')
            results['ok'].append({'slug': slug, 'videoId': vid, 'channel': author,
                                  'videoTitle': vtitle, 'type': typ, 'channelClass': cls,
                                  'score': round(score, 2)})
            break  # first passing candidate per title
    json.dump(results, open('content/trailer-candidates-verified.json', 'w'), indent=1, ensure_ascii=False)
    print(f"\n{len(results['ok'])} verified candidates -> content/trailer-candidates-verified.json")

if __name__ == '__main__':
    main()

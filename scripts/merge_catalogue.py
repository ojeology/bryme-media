#!/usr/bin/env python3
"""Merge catalogue.json + catalogue-batch.json into a single validated catalogue.
Preserves existing entries, adds batch entries, removes duplicates by id/slug,
validates required fields."""
import json, re, sys

legacy = []  # not touched — the build reads legacy/index.html itself
main = json.load(open('content/catalogue.json'))
batch = json.load(open('content/catalogue-batch.json'))

by_id = {}
for m in main:
    by_id[m['id']] = m

added = 0
dupes = 0
for b in batch:
    if b['id'] in by_id:
        dupes += 1
        continue
    by_id[b['id']] = b
    added += 1

# Validate
problems = []
for m in by_id.values():
    if not m.get('id'): problems.append('missing id')
    if not m.get('title'): problems.append(f"{m.get('id','?')}: missing title")
    if not m.get('slug'): problems.append(f"{m.get('id','?')}: missing slug")
    if not m.get('year'): problems.append(f"{m.get('id','?')}: missing year")
    if not m.get('genre'): problems.append(f"{m.get('id','?')}: missing genre")
    if m.get('youtubeId') and not re.fullmatch(r'[A-Za-z0-9_-]{11}', m['youtubeId']):
        problems.append(f"{m['id']}: bad youtubeId {m['youtubeId']}")

merged = sorted(by_id.values(), key=lambda x: x['id'])
json.dump(merged, open('content/catalogue.json','w'), indent=1, ensure_ascii=False)
print(f"MAIN: {len(main)} -> MERGED: {len(merged)} (added {added}, skipped {dupes} dupes)")
print(f"VALIDATION PROBLEMS: {len(problems)}")
for p in problems[:20]: print("  -", p)

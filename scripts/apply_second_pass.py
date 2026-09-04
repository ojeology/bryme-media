#!/usr/bin/env python3
"""Apply second-pass verified trailer results to the catalogue.

- catalogue.json records: write youtubeId / trailer / poster (primary ID).
  The next audit run re-derives type, channel, language automatically.
- legacy records (not in catalogue.json): write candidates into
  content/trailers.json overrides so the build can use them.

Usage: python3 scripts/apply_second_pass.py
"""
import json, os, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

results = json.load(open('content/second-pass-results.json'))['records']
verified = [r for r in results if r.get('verified')]

cat = json.load(open('content/catalogue.json'))
cat_by_slug = {r['slug']: r for r in cat}

overrides = {}
if os.path.exists('content/trailers.json'):
    overrides = json.load(open('content/trailers.json'))

applied_cat, applied_legacy, skipped = [], [], []
for r in verified:
    slug = r['slug']
    vid = r['videoId']
    if r.get('type') == 'fan-made':
        cand = {'videoId': vid, 'type': 'fan-made', 'title': 'Community trailer',
                'source': 'YouTube', 'channel': r.get('channel', ''),
                'verified': False, 'lastChecked': r.get('lastChecked')}
    else:
        cand = {'videoId': vid, 'type': r.get('type', 'official-trailer'),
                'title': (r.get('type') or 'official-trailer').replace('-', ' ').title(),
                'source': 'YouTube', 'channel': r.get('channel', ''),
                'verified': True, 'lastChecked': r.get('lastChecked')}
    if slug in cat_by_slug:
        rec = cat_by_slug[slug]
        rec['youtubeId'] = vid
        rec['trailer'] = f"https://www.youtube.com/watch?v={vid}"
        rec['poster'] = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
        applied_cat.append(slug)
    else:
        ov = overrides.setdefault(slug, {})
        if 'excludeTrailers' in ov:
            ov.pop('excludeTrailers', None)
        ov['candidates'] = [c for c in ov.get('candidates', []) if c.get('videoId') != vid]
        ov['candidates'].append(cand)
        applied_legacy.append(slug)

json.dump(cat, open('content/catalogue.json', 'w'), indent=1, ensure_ascii=False)
json.dump(overrides, open('content/trailers.json', 'w'), indent=1, ensure_ascii=False)

print(f"applied to catalogue.json: {len(applied_cat)}")
print(f"applied to trailers.json overrides (legacy): {len(applied_legacy)}")
for s in applied_legacy[:20]:
    print('  legacy:', s)

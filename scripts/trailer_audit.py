#!/usr/bin/env python3
"""Full trailer audit: verifies every existing YouTube ID in the catalogue
against YouTube oEmbed, checks the channel against an official-source
allowlist, checks the video title matches the title, and classifies the
trailer type + channel trust class.

Classes:
  studio      - official studio/streaming channel
  distributor - licensed distributor (Madman, All the Anime, GKIDS, Well Go, IFC...)
  aggregator  - trailer news/aggregation channel (video is the official trailer)
  community   - community/fan channel (fallback only, clearly labelled)

Writes content/trailer-audit.json (consumed by the build). Broken/mismatch
records are excluded from display by the build but kept for the admin workflow.

Usage: python3 scripts/trailer_audit.py
"""
import json, os, re, time, unicodedata, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

_ROMAN = {'i': '1', 'ii': '2', 'iii': '3', 'iv': '4', 'v': '5', 'vi': '6',
           'vii': '7', 'viii': '8', 'ix': '9', 'x': '10', 'xi': '11', 'xii': '12',
           'xiii': '13', 'xiv': '14', 'xv': '15', 'xx': '20', 'xxi': '21', 'xxii': '22'}

def norm(s):
    s = unicodedata.normalize('NFKD', str(s))
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()

def oembed(vid, retries=2):
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {'__missing__': True}
            time.sleep(1.5)
        except Exception:
            time.sleep(1.5)
    return None

# Channel -> trust class. Substring match on lowercased author_name.
CHANNEL_CLASSES = {
    'studio': [
        'marvel', 'warner bros', 'warnermedia', 'wbd', 'disney', 'pixar',
        'netflix', 'hbo', 'hbomax', 'max', 'apple tv', 'prime video', 'amazon',
        'paramount', 'universal pictures', 'sony pictures', 'columbia',
        'lionsgate', '20th century', 'searchlight', 'focus features', 'a24',
        'neon', 'mubi', 'crunchyroll', 'viz media', 'aniplex', 'toho',
        'gkids', 'cartoon saloon', 'funimation', 'adult swim', 'amc',
        'fx networks', 'starz', 'showtime', 'hulu', 'peacock', 'star wars',
        'avatar', 'james bond', 'illumination', 'the fast saga', 'legendary',
        'dc', 'gameofthrones', 'game of thrones', 'eone', 'youtube movies',
        'utv motion pictures', 'panorama studios', 'excel movies',
        'hombale', 'kemi adetiba', 'ifc', 'sony pics at home', 'eros universe',
        'think music', 'ratatouillemovie', 'baahubali', 'pen movies',
        'klokline', 'walt disney', 'disneyplus', 'disney+', 'paramount pictures',
        'universal', 'tri-star', 'tristar', 'mgm', 'warner bros pictures',
        'roadshow', 'village roadshow', 'studio canal', 'pathé', 'pathe',
        'miramax', 'film4', 'bbc', 'bbc america', 'sky', 'itv', 'channel 4',
        'cbs', 'nbc', 'abc', 'fx', 'showtime', 'tnt', 'tbs', 'toei',
        'bandai', 'pierrot', 'mappa', 'ufotable', 'sunrise', 'bones',
        'wit studio', 'studio ghibli', 'ghibli', 'kyoto animation',
        'madhouse', 'production i.g', 'j.c.staff', 'aniplex', 'kadokawa',
        'kodansha', 'shueisha', 'shonen jump', 'viz', 'kino lorber',
        'criterion', 'janus', 'magnolia', 'roadside', 'shout factory', 'saban',
        'well go usa', 'tiff', 'bfi', 'motion picture association',
        'rotten tomatoes', 'movieclips', 'ign', 'trailer blend', 'flickdirect',
    ],
    'distributor': [
        'madman films', 'all the anime', 'anime limited', 'gscinemas',
        'klokline cinema', 'muse asia', 'muse india', 'well go',
        'ifc first take', 'ifc films', 'mubi', 'gkids', 'uip', 'united international',
        'elevation pictures', 'universal pictures home', 'sony pictures home',
        'pinnacle films', 'bafta', 'london film', 'sundance',
        'cult trailers', 'trailer world',
    ],
    'aggregator': [
        'one media', 'kinocheck', 'entertainment access', 'trailer spotlight',
        'filmselect', 'trailer addict', 'movie trailers', 'worldmovie',
        'top movie clips', 'justwatch', 'film trailers', 'cine trailers',
    ],
    'community': [
        'horror society', 'nollycritic', 'mpm premium', 'alextvshows',
        'george m.c', 'prime movies', 'andrew henderson', 'superanon',
        'nathansmoviereviews', '3idiots', 'klokline', 'superanon9876',
    ],
}
# Extra concatenated variants that would otherwise break word boundaries
CHANNEL_CLASSES['studio'] += ['nbcuniversal', 'paramountplus', 'peacocktv', 'disneystudios', 'sonypicturesentertainment',
                              'searchlightpictures', 'vizmedia', 'africaonnetflix', 'matchbox',
                              'eonefilms', 'imax', 'bfitrailers', 'ifcfirsttake', 'indiamarvel']

def channel_class(author):
    """Word-boundary substring match: 'dc' must not match 'podcast'."""
    a = (author or '').lower()
    for cls, keys in CHANNEL_CLASSES.items():
        for k in keys:
            if re.search(r'(?<![a-z0-9])' + re.escape(k) + r'(?![a-z0-9])', a):
                return cls
    return None

def classify(video_title):
    t = norm(video_title)
    if 'teaser' in t:
        return 'official-teaser'
    if re.search(r'\b(clip|scene|featurette)\b', t) or 'behind the scenes' in t:
        return 'official-clip'
    return 'official-trailer'

def overlap(expected, video_title):
    ew = set(norm(expected).split())
    tw = set(norm(video_title).split())
    if not ew:
        return 0.0
    score = len(ew & tw) / len(ew)
    # Roman->digit on the FINAL token of the expected title only
    # (Frozen II vs "Frozen 2", Rocky IV vs "Rocky 4") — never touches X-Men.
    last = norm(expected).split()[-1]
    if last in _ROMAN and _ROMAN[last] in tw:
        ew2 = (ew - {last}) | {_ROMAN[last]}
        score = max(score, len(ew2 & tw) / max(len(ew2), 1))
    return score

STATUS_RANK = {'verified': 0, 'community': 1, 'unverified-channel': 2, 'mismatch': 3, 'error': 4, 'broken': 5}

def check_video(m, vid, seen, errors):
    """Verify one video for a title; returns the record dict."""
    if vid in seen:
        return dict(seen[vid])
    j = oembed(vid)
    if j is None:
        rec = {'status': 'error', 'type': None, 'channel': None, 'channelClass': None, 'videoTitle': None}
        errors.append(vid)
    elif j.get('__missing__'):
        rec = {'status': 'broken', 'type': None, 'channel': None, 'channelClass': None, 'videoTitle': None}
    else:
        author = j.get('author_name', '')
        vtitle = j.get('title', '')
        score = overlap(m['title'], vtitle)
        cls = channel_class(author)
        if score < 0.5:
            rec = {'status': 'mismatch', 'type': None, 'channel': author, 'channelClass': cls,
                   'videoTitle': vtitle, 'score': round(score, 2)}
        elif cls is None:
            rec = {'status': 'unverified-channel', 'type': classify(vtitle), 'channel': author,
                   'channelClass': None, 'videoTitle': vtitle, 'score': round(score, 2)}
        elif cls == 'community':
            rec = {'status': 'community', 'type': 'fan-made', 'channel': author, 'channelClass': cls,
                   'videoTitle': vtitle, 'score': round(score, 2)}
        else:
            rec = {'status': 'verified', 'type': classify(vtitle), 'channel': author,
                   'channelClass': cls, 'videoTitle': vtitle, 'score': round(score, 2)}
    rec['videoId'] = vid
    rec['lastChecked'] = time.strftime('%Y-%m-%d')
    seen[vid] = rec
    return dict(rec)

def main():
    movies = json.load(open('data/trailer-sources.json'))
    audit = {}
    seen = {}
    errors = []
    for m in movies:
        ids = [(f'v{i}', v) for i, v in enumerate(m.get('youtubeIds') or [])]
        if not ids:
            audit[m['slug']] = {'slug': m['slug'], 'id': m.get('id') or m['slug'], 'title': m['title'],
                                'videoId': None, 'status': 'missing', 'type': None,
                                'channel': None, 'channelClass': None, 'videoTitle': None,
                                'lastChecked': None, 'candidates': []}
            continue
        recs = [check_video(m, vid, seen, errors) for _, vid in ids]
        recs.sort(key=lambda r: STATUS_RANK.get(r['status'], 9))
        best = recs[0]
        audit[m['slug']] = dict(best, slug=m['slug'], id=m.get('id') or m['slug'], title=m['title'],
                                candidates=[{k: r.get(k) for k in ('videoId', 'status', 'type', 'channel', 'channelClass', 'videoTitle', 'lastChecked')} for r in recs])
        time.sleep(0.05)

    overrides_path = 'content/trailers.json'
    if os.path.exists(overrides_path):
        try:
            overrides = json.load(open(overrides_path))
            for slug, rec in overrides.items():
                if slug in audit:
                    audit[slug]['adminOverride'] = rec
        except Exception as e:
            print('WARN: could not read overrides:', e)

    os.makedirs('content', exist_ok=True)
    json.dump(audit, open('content/trailer-audit.json', 'w'), indent=1, ensure_ascii=False)

    counts = {}
    for rec in audit.values():
        counts[rec['status']] = counts.get(rec['status'], 0) + 1
    print('TRAILER AUDIT SUMMARY')
    print('  titles audited:', len(audit))
    for k in ['verified', 'community', 'aggregator-note', 'broken', 'mismatch', 'unverified-channel', 'error', 'missing']:
        print(f'  {k}: {counts.get(k, 0)}')
    byclass = {}
    for rec in audit.values():
        if rec['status'] == 'verified':
            c = rec.get('channelClass') or '?'
            byclass[c] = byclass.get(c, 0) + 1
    print('  verified by channel class:', byclass)
    for t in ['official-trailer', 'official-teaser', 'official-clip', 'fan-made']:
        n = sum(1 for r in audit.values() if r.get('type') == t and r['status'] in ('verified', 'community'))
        print(f'  displayable {t}: {n}')
    print('  transient errors (retry later):', errors)
    print('written: content/trailer-audit.json')

if __name__ == '__main__':
    main()

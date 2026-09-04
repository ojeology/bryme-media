#!/usr/bin/env python3
"""SECOND-PASS TRAILER DISCOVERY

For every title without a verified trailer:
  1. Run adapted YouTube searches ("[TITLE] official trailer", year-aware,
     language-aware for regional content, teaser fallback).
  2. Collect candidate video IDs from search results.
  3. Verify EVERY candidate: video exists, title overlap >= 0.6 (year-aware),
     channel on the official allowlist (studio/distributor/aggregator) or
     community (labelled fan-made, used only when nothing official exists).
  4. Classify: official-trailer / official-teaser / official-clip / fan-made,
     with a language hint for regional trailers.
  5. Emit verified candidates only (content/second-pass-results.json).

Usage: python3 scripts/second_pass_discovery.py [--start N] [--count M] [--query "extra"]
"""
import argparse, json, os, re, sys, time, unicodedata, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from trailer_audit import norm, channel_class, classify, STATUS_RANK, overlap

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36',
      'Accept-Language': 'en-US,en;q=0.9'}

LANG_KEYWORDS = [
    ('Hindi', ['hindi', 'hindī']), ('Tamil', ['tamil']), ('Telugu', ['telugu']),
    ('Malayalam', ['malayalam']), ('Kannada', ['kannada']), ('Korean', ['korean', 'korea']),
    ('Japanese', ['japanese', 'japan', '日本語']), ('Chinese', ['chinese', 'mandarin', 'cantonese', '中文']),
    ('Yoruba', ['yoruba']), ('Hausa', ['hausa']), ('Igbo', ['igbo']),
    ('French', ['french', 'français']), ('German', ['german', 'deutsch']),
    ('Spanish', ['spanish', 'español']), ('Arabic', ['arabic', 'عربي']),
]
REGIONAL = {'Korea': 'Korean', 'South Korea': 'Korean', 'Japan': 'Japanese', 'China': 'Chinese',
            'Hong Kong': 'Chinese', 'Taiwan': 'Chinese', 'India': 'Hindi', 'Nigeria': 'Yoruba',
            'France': 'French', 'Germany': 'German', 'Spain': 'Spanish'}

def detect_language(vtitle):
    t = vtitle.lower()
    for lang, kws in LANG_KEYWORDS:
        if any(k in t for k in kws):
            return lang
    return None

def yt_search(q, max_results=12):
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(q)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode('utf-8', 'ignore')
    ids = re.findall(r'"videoId":"([A-Za-z0-9_-]{11})"', html)
    seen, out = set(), []
    for i in ids:
        if i not in seen:
            seen.add(i); out.append(i)
    return out[:max_results]

OEMBED_CACHE = {}
def oembed(vid):
    if vid in OEMBED_CACHE:
        return OEMBED_CACHE[vid]
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            j = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        j = {'__missing__': True} if e.code == 404 else None
    except Exception:
        j = None
    OEMBED_CACHE[vid] = j
    return j

def verify(m, vid):
    """Returns (ok, record) with strict gates."""
    j = oembed(vid)
    if j is None:
        return False, ('oembed error', None)
    if j.get('__missing__'):
        return False, ('does not exist', None)
    author = j.get('author_name', '')
    vtitle = j.get('title', '')
    score = overlap(m['title'], vtitle)
    if score < 0.6:
        return False, (f'title mismatch {score:.2f}', None)
    # Year check: if the video title has a different 4-digit year and the
    # record has a known year, reject (protects remakes/sequels).
    years_in_title = set(re.findall(r'\b(19|20)\d{2}\b', vtitle))
    if m.get('year') and years_in_title:
        # tolerate +-1 year (series airing across year boundaries, teasers a
        # year ahead of release), reject anything further off.
        off = [int(y) for y in years_in_title if abs(int(y) - int(m['year'])) > 1]
        if off:
            return False, (f'year mismatch (video mentions {sorted(years_in_title)})', None)
    cls = channel_class(author)
    if cls is None:
        return False, ('unverifiable channel', None)
    # Accuracy gate: the video title must indicate trailer content
    # (trailer/teaser/clip/preview...). Rejects full-movie listings
    # like "Alien 3 (Special Edition)".
    tn = norm(vtitle)
    if not re.search(r'\b(trailer|teaser|clip|scene|featurette|preview|spot|promo)\b', tn):
        return False, ('video title has no trailer-indicating words', None)
    # Guard: title phrase appearing only in a date/return context
    # ("... Returns October 1", "... Premieres This Fall") is NOT a match.
    if re.search(r'\b(returns|returning|premieres|premiere|starting|coming)\b', tn) and m['title'].lower().split() and re.search(
            r'\b' + re.escape(re.sub(r'[^a-z0-9]+', ' ', m['title'].lower()).strip().replace(' ', r'\s+')) + r'\b', tn):
        # only reject when the title tokens sit adjacent to a date-word cluster
        if re.search(r'(returns?|premieres?|starting|coming)\s+(in\s+|on\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{1,2}|this\s+(fall|summer|winter|spring))', tn):
            return False, ('title match is only a date context ("Returns October 1")', None)
    # Guard: spin-off/adaptation colon-extensions ("The Walking Dead: Dead
    # City Season 1 Trailer" is not a "The Walking Dead" trailer).
    rt = re.sub(r'[^a-z0-9]+', ' ', m['title'].lower()).strip()
    if ':' not in m['title']:
        raw_lower = vtitle.lower().replace('\u2019', "'")
        colon_ext = re.search(r'^' + re.escape(rt) + r'\s*:\s*([a-z0-9]+)', raw_lower)
        if colon_ext and colon_ext.group(1) in ('season', 'part', 'chapter', 'volume', 'movie', 'film', 'episode', 'special', 's1', 's2', 's3', 's4', 's5'):
            return False, ('spin-off/adaptation colon-extension', None)
        # "The Walking Dead: Dead City" -> "the walking dead dead city" after
        # norm; catch by checking the raw phrase pattern too.
        if re.search(r'^' + re.escape(rt) + r'\s*:\s*[a-z]', raw_lower):
            after_colon = raw_lower.split(':', 1)[1].strip()
            if not re.match(r'^(official|trailer|teaser|clip|hd|the|a|part|full|extended|final)', after_colon):
                return False, ('spin-off colon-extension (raw)', None)
    # Guard: "exclusive" videos are usually IMAX featurettes, not the trailer
    if 'exclusive' in tn and not re.search(r'\b(clip|scene|featurette)\b', tn):
        return False, ('exclusive featurette, not the main trailer', None)
    # Guard: short titles (<=2 tokens) must START the video title with a
    # trailer-word immediately after ("Poetry Season" is not "Poetry").
    title_tokens = re.sub(r'[^a-z0-9]+', ' ', m['title'].lower()).strip().split()
    if len(title_tokens) <= 2:
        start_match = re.match(r'^(the\s+)?' + re.escape(' '.join(title_tokens)) + r'\b', tn)
        if not start_match:
            return False, ('short title must appear at the start of the video title', None)
        after = tn[start_match.end():].strip()
        if after and not re.match(r'^[\-\|–:]', after) and not re.match(r'^(official|hd|trailer|teaser|clip|scene|preview|spot|promo|1080p|4k|movie|film)', after):
            return False, ('short title followed by unrelated word (e.g. "Poetry Season")', None)
    typ = 'fan-made' if cls == 'community' else classify(vtitle)
    lang = detect_language(vtitle)
    rec = {'videoId': vid, 'channel': author, 'channelClass': cls, 'videoTitle': vtitle,
           'type': typ, 'score': round(score, 2), 'language': lang,
           'lastChecked': time.strftime('%Y-%m-%d')}
    return True, ('ok', rec)

def build_queries(m):
    t = m['title']
    year = m.get('year')
    country = m.get('country') or ''
    queries = []
    if year and re.search(r'\b(19|20)\d{2}\b', t) is None:
        q = f"{t} ({year}) official trailer"
    else:
        q = f"{t} official trailer"
    queries.append(q)
    queries.append(f"{t} official teaser")
    # Platform/type adaptation for known streaming franchises
    g = (m.get('typeDir') or '')
    if g == 'Anime':
        queries.append(f"{t} official trailer crunchyroll")
    elif g == 'Series':
        queries.append(f"{t} official trailer netflix")
        queries.append(f"{t} official trailer hbo")
    # Regional adaptation
    if country in REGIONAL:
        lang = REGIONAL[country]
        if lang == 'Hindi':
            queries.append(f"{t} official trailer hindi")
        elif lang == 'Yoruba':
            queries.append(f"{t} official trailer yoruba")
        elif lang == 'Korean':
            queries.append(f"{t} official trailer korean")
        elif lang == 'Japanese':
            queries.append(f"{t} official trailer japanese")
        elif lang == 'Chinese':
            queries.append(f"{t} official trailer chinese")
    return queries

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--count', type=int, default=10**9)
    args = ap.parse_args()

    audit = json.load(open('content/trailer-audit.json'))
    sources = json.load(open('data/trailer-sources.json'))
    catalogue = {r.get('slug'): r for r in json.load(open('content/catalogue.json'))}

    missing = []
    for m in sources:
        a = audit.get(m['slug'], {})
        status = a.get('status', 'missing')
        if status in ('missing', 'broken', 'mismatch', 'error', 'unverified-channel'):
            rec = {'slug': m['slug'], 'title': m['title'],
                   'year': catalogue.get(m['slug'], {}).get('year'),
                   'country': catalogue.get(m['slug'], {}).get('country'),
                   'language': catalogue.get(m['slug'], {}).get('language'),
                   'typeDir': catalogue.get(m['slug'], {}).get('genre'),
                   'currentStatus': status}
            missing.append(rec)

    # load previous verified results to skip already-found titles
    prev = {}
    if os.path.exists('content/second-pass-results.json'):
        data = json.load(open('content/second-pass-results.json'))
        records = data.get('records', data) if isinstance(data, dict) else data
        prev = {r['slug']: r for r in records if r.get('verified')}

    batch = missing[args.start:args.start + args.count]
    print(f"second pass: {len(missing)} missing total, processing {len(batch)} (start={args.start})")

    results = []
    rejected_log = []
    for idx, m in enumerate(batch):
        slug = m['slug']
        if slug in prev:
            results.append(prev[slug])
            continue
        found = None
        attempts = []
        prev_rec = prev_all.get(slug) if 'prev_all' in dir() else None
        rejected_ids = set((prev_rec or {}).get('rejectedIds', [])) if isinstance(prev_rec, dict) else set()
        for q in build_queries(m):
            attempts.append(q)
            try:
                ids = yt_search(q)
            except Exception as e:
                print(f"  search error {slug}: {e}")
                continue
            for vid in ids[:8]:
                if vid in rejected_ids:
                    continue
                ok, info = verify(m, vid)
                if ok:
                    rec = {'slug': slug, 'title': m['title'], 'videoId': vid,
                           'channel': info[1]['channel'], 'channelClass': info[1]['channelClass'],
                           'videoTitle': info[1]['videoTitle'], 'type': info[1]['type'],
                           'score': info[1]['score'], 'language': info[1]['language'],
                           'lastChecked': info[1]['lastChecked'], 'query': q,
                           'verified': True, 'year': m['year']}
                    found = rec
                    break
                else:
                    rejected_log.append({'slug': slug, 'vid': vid, 'reason': info[0]})
            if found:
                break
            time.sleep(0.4)
        if found:
            results.append(found)
        if found:
            results.append(found)
            print(f"  OK  {slug}: {found['videoId']} | {found['type']} | {found['channel'][:30]} | {found['language'] or 'en'} | {found['videoTitle'][:50]}")
        else:
            rejected = prev_rec.get('rejectedIds', []) if prev_rec else []
            for item in rejected_log:
                if item['slug'] == slug and item['vid'] not in rejected:
                    rejected.append(item['vid'])
            results.append({'slug': slug, 'title': m['title'], 'year': m['year'],
                            'currentStatus': m['currentStatus'], 'verified': False,
                            'attempts': attempts, 'rejectedIds': rejected[-40:]})
        time.sleep(0.3)
        if (idx + 1) % 15 == 0:
            print(f"  ...{idx + 1}/{len(batch)} done")

    # merge with previous — keep ALL previous records (verified and failed)
    prev_all = {}
    if os.path.exists('content/second-pass-results.json'):
        d0 = json.load(open('content/second-pass-results.json'))
        prev_all = {r['slug']: r for r in (d0.get('records', d0) if isinstance(d0, dict) else d0)}
    merged = dict(prev_all)
    for r in results:
        merged[r['slug']] = r
    json.dump({'generatedAt': time.strftime('%Y-%m-%dT%H:%M:%S'),
               'records': list(merged.values())},
              open('content/second-pass-results.json', 'w'), indent=1, ensure_ascii=False)
    ok_now = sum(1 for r in merged.values() if r.get('verified'))
    print(f"\npass done: {ok_now} verified so far across all passes")

if __name__ == '__main__':
    main()

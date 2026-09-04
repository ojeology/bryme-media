#!/usr/bin/env python3
"""BRYME trailer admin CLI.

Manage trailer information without touching frontend code. All changes are
written to content/trailers.json (per-title candidate lists).

Usage:
  python3 scripts/trailer_admin.py list [--status official|fan-made|none|broken] [--q text]
  python3 scripts/trailer_admin.py show <slug>
  python3 scripts/trailer_admin.py set <slug> <videoId> [--type official-trailer|official-teaser|official-clip|fan-made] [--channel "Name"]
  python3 scripts/trailer_admin.py add <slug> <videoId> [--type ...] [--channel "Name"]   # append fallback candidate
  python3 scripts/trailer_admin.py unset <slug> [--index 0]                              # remove a candidate (default first)
  python3 scripts/trailer_admin.py exclude <slug> on|off                                # hide all trailers for a title
  python3 scripts/trailer_admin.py verify <slug>                                        # re-verify override video IDs via oEmbed

Every set/add writes only after the videoId passes verification (exists,
title overlap, official/community channel). Use --force to bypass checks.
"""
import argparse, json, os, re, sys, time, unicodedata, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from trailer_audit import norm, channel_class

OVERRIDES = 'content/trailers.json'
TYPES = ['official-trailer', 'official-teaser', 'official-clip', 'fan-made']

def load_overrides():
    if not os.path.exists(OVERRIDES):
        return {}
    return json.load(open(OVERRIDES))

def save_overrides(d):
    json.dump(d, open(OVERRIDES, 'w'), indent=1, ensure_ascii=False)

def find_movie(slug):
    movies = {m['slug']: m for m in json.load(open('data/movies.json'))}
    return movies.get(slug)

def oembed(vid):
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {'__missing__': True}
        return None
    except Exception:
        return None

def verify(vid, title):
    """Returns (ok, info) — ok=True only if the video exists, title overlaps
    and the channel is identifiable."""
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', vid):
        return False, 'invalid videoId format'
    j = oembed(vid)
    if j is None:
        return False, 'oEmbed request failed (retry)'
    if j.get('__missing__'):
        return False, 'video does not exist on YouTube'
    author = j.get('author_name', '')
    vtitle = j.get('title', '')
    ew = set(norm(title).split())
    tw = set(norm(vtitle).split())
    score = len(ew & tw) / max(len(ew), 1) if ew else 0
    cls = channel_class(author)
    if score < 0.6:
        return False, f'title mismatch ({score:.2f}): "{vtitle}"'
    if cls is None:
        return False, f'unidentifiable channel "{author}"'
    return True, {'channel': author, 'channelClass': cls, 'videoTitle': vtitle, 'score': round(score, 2), 'lastChecked': time.strftime('%Y-%m-%d')}

def cmd_list(args):
    d = load_overrides()
    audit = json.load(open('content/trailer-audit.json'))
    movies = {m['slug']: m for m in json.load(open('data/movies.json'))}
    rows = []
    for slug, m in movies.items():
        if args.q and args.q.lower() not in (m['title'] + ' ' + slug).lower():
            continue
        a = audit.get(slug, {})
        ov = d.get(slug)
        if ov and ov.get('excludeTrailers'):
            status = 'excluded'
        elif ov and ov.get('candidates'):
            status = ov['candidates'][0].get('type', 'official-trailer')
        elif a.get('videoId') and a.get('status') in ('verified', 'community'):
            status = 'fan-made' if a['status'] == 'community' else (a.get('type') or 'official-trailer')
        elif a.get('videoId'):
            status = 'broken'
        else:
            status = 'none'
        if args.status and status != args.status:
            continue
        vid = (ov and ov.get('candidates', [{}])[0].get('videoId')) or a.get('videoId') or ''
        rows.append((status, m['title'], slug, vid))
    for status, title, slug, vid in sorted(rows):
        print(f"{status:22s} {title[:44]:44s} {slug:30s} {vid}")
    print(f"\n{len(rows)} titles")

def cmd_show(args):
    m = find_movie(args.slug)
    if not m:
        print('not found'); return
    d = load_overrides().get(args.slug)
    audit = json.load(open('content/trailer-audit.json')).get(args.slug, {})
    print(f"title:        {m['title']}")
    print(f"audit:        {audit.get('status', 'missing')} | {audit.get('type', '')} | {audit.get('channel', '')} | checked {audit.get('lastChecked', '-')}")
    if d:
        print(f"override:     {'excluded' if d.get('excludeTrailers') else 'candidates:'}")
        for c in d.get('candidates', []):
            print(f"  - {c.get('videoId')} | {c.get('type')} | {c.get('channel', '')} | verified={c.get('verified')} | checked {c.get('lastChecked', '-')}")
    else:
        print("override:     none (audit/default applies)")

def write_candidate(slug, vid, typ, channel, append=False, force=False):
    m = find_movie(slug)
    if not m:
        print(f"ERROR: {slug} not in catalogue"); return 1
    ok, info = verify(vid, m['title'])
    if not ok and not force:
        print(f"REJECTED: {info} — use --force only if you have verified this externally.")
        return 1
    d = load_overrides()
    rec = d.setdefault(slug, {})
    rec.setdefault('candidates', [])
    cand = {'videoId': vid, 'type': typ, 'title': typ.replace('-', ' ').title(), 'source': 'YouTube',
            'channel': channel or (info.get('channel') if isinstance(info, dict) else ''),
            'verified': ok, 'lastChecked': time.strftime('%Y-%m-%d') if ok else None}
    if append:
        rec['candidates'].append(cand)
    else:
        rec['candidates'] = [cand] + rec['candidates']
    save_overrides(d)
    print(f"OK {slug} <- {vid} ({typ}, verified={ok})")

def cmd_set(args):
    return write_candidate(args.slug, args.videoId, args.type, args.channel, append=False, force=args.force)

def cmd_add(args):
    return write_candidate(args.slug, args.videoId, args.type, args.channel, append=True, force=args.force)

def cmd_unset(args):
    d = load_overrides()
    if args.slug not in d:
        print(f"{args.slug}: no override"); return
    cands = d[args.slug].get('candidates', [])
    if not cands:
        print(f"{args.slug}: no candidates"); return
    removed = cands.pop(args.index)
    if not cands:
        del d[args.slug]
    save_overrides(d)
    print(f"removed {removed['videoId']} from {args.slug}")

def cmd_exclude(args):
    d = load_overrides()
    if args.on == 'on':
        d.setdefault(args.slug, {})['excludeTrailers'] = True
    else:
        d.get(args.slug, {}).pop('excludeTrailers', None)
        if not d.get(args.slug):
            d.pop(args.slug, None)
    save_overrides(d)
    print(f"{args.slug}: excludeTrailers={args.on == 'on'}")

def cmd_verify(args):
    d = load_overrides()
    if args.slug not in d:
        print(f"{args.slug}: no override"); return
    m = find_movie(args.slug)
    for c in d[args.slug].get('candidates', []):
        ok, info = verify(c['videoId'], m['title'])
        c['verified'] = ok
        if isinstance(info, dict):
            c['channel'] = info['channel']
            c['lastChecked'] = info['lastChecked']
        print(f"  {c['videoId']}: {'VERIFIED' if ok else 'FAILED — ' + str(info)}")
    save_overrides(d)

def main():
    ap = argparse.ArgumentParser(description='BRYME trailer admin')
    sub = ap.add_subparsers(dest='cmd')
    p = sub.add_parser('list'); p.add_argument('--status'); p.add_argument('--q')
    sub.add_parser('show').add_argument('slug')
    p = sub.add_parser('set'); p.add_argument('slug'); p.add_argument('videoId'); p.add_argument('--type', choices=TYPES, default='official-trailer'); p.add_argument('--channel'); p.add_argument('--force', action='store_true')
    p = sub.add_parser('add'); p.add_argument('slug'); p.add_argument('videoId'); p.add_argument('--type', choices=TYPES, default='official-trailer'); p.add_argument('--channel'); p.add_argument('--force', action='store_true')
    p = sub.add_parser('unset'); p.add_argument('slug'); p.add_argument('--index', type=int, default=0)
    p = sub.add_parser('exclude'); p.add_argument('slug'); p.add_argument('on', choices=['on', 'off'])
    sub.add_parser('verify').add_argument('slug')
    args = ap.parse_args()
    if not args.cmd:
        ap.print_help(); return
    {'list': cmd_list, 'show': cmd_show, 'set': cmd_set, 'add': cmd_add,
     'unset': cmd_unset, 'exclude': cmd_exclude, 'verify': cmd_verify}[args.cmd](args)

if __name__ == '__main__':
    main()

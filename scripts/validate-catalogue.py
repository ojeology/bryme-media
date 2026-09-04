#!/usr/bin/env python3
"""Full catalogue validation report per project spec."""
import json, re, os

m = json.load(open('data/movies.json'))
c = json.load(open('content/catalogue.json'))
a = json.load(open('reports/youtube-audit.json'))

# Type breakdown
types = {'movie': 0, 'series': 0, 'anime': 0}
for x in m:
    lt = x.get('legacyType','movie')
    if lt == 'legacy-anime': types['anime'] += 1
    elif lt == 'legacy-series': types['series'] += 1
    else:
        g = x.get('genre','')
        if g == 'Anime': types['anime'] += 1
        elif g == 'Series': types['series'] += 1
        else: types['movie'] += 1

# Duplicates
ids = [x['id'] for x in m]
slugs = [x['slug'] for x in m]
dup_ids = len(ids) - len(set(ids))
dup_slugs = len(slugs) - len(set(slugs))

# Broken / missing
no_poster = sum(1 for x in m if not x.get('poster'))
no_desc = sum(1 for x in m if not x.get('description'))
bad_year = sum(1 for x in m if not x.get('year') or not (1900 <= int(x['year']) <= 2030))
bad_trailer = 0
for x in m:
    yt = x.get('youtubeId')
    if yt and not re.fullmatch(r'[A-Za-z0-9_-]{11}', yt):
        bad_trailer += 1

# Genre validity
valid_genres = {'Drama','Action','Superhero','Sci-Fi','Horror','Thriller','Series','Animation','Anime','Comedy','Crime','Fantasy','War','Romance','Korean','Western','French','German','Nigerian','Indian','Chinese','Japanese','Hong Kong','Taiwan','Spain','South Africa','New Zealand'}
bad_genre = sum(1 for x in m if x.get('genre') not in valid_genres)

print("=" * 60)
print("BRYME CATALOGUE VALIDATION REPORT")
print("=" * 60)
print(f"Total titles:            {len(m)}")
print(f"  Movies:                {types['movie']}")
print(f"  Series:                {types['series']}")
print(f"  Anime:                 {types['anime']}")
print(f"Titles with verified trailers: {a['valid']}")
print(f"Titles without trailers:      {a['unavailable']}")
print(f"Titles with posters:     {len(m) - no_poster}")
print(f"Duplicate ids:           {dup_ids}")
print(f"Duplicate slugs:         {dup_slugs}")
print(f"Missing descriptions:    {no_desc}")
print(f"Invalid years:           {bad_year}")
print(f"Invalid trailer URLs:    {bad_trailer}")
print(f"Invalid genres:          {bad_genre}")
print(f"Indexable URLs:          {len([f for f in os.listdir('.') if os.path.isdir(f)])} dirs (pages)")
# count generated pages
import subprocess
print(f"Movie pages generated:   {len(os.listdir('movie')) if os.path.isdir('movie') else 0}")
print(f"Article pages:           {len(os.listdir('article')) if os.path.isdir('article') else 0}")
print(f"Genre pages:             {len(os.listdir('genre')) if os.path.isdir('genre') else 0}")
print(f"Year pages:              {len(os.listdir('year')) if os.path.isdir('year') else 0}")
print("=" * 60)

# Adding match results — BRYME Sports

The site has 1,752 match pages across five leagues. Until a match has a result they are
fixtures: useful to a reader, but `noindex` and kept out of `sitemap.xml`, because a page
that says "this match has not been played yet" is not something to submit to Google.

**Adding a result flips that automatically.** The page gains a scoreline, scorers and a
source, drops the noindex tag, and enters the sitemap on the next build. You never edit the
match page, the results page or the sitemap by hand.

---

## The one rule

**A result will not publish without a source URL.** Not a warning — a refusal. The tooling
rejects it, the build refuses to render it and exits non-zero, and the validator fails.

This is deliberate. The scoreline is the one thing on a sports site nobody should have to
take on trust, and an unsourced score is indistinguishable from a fabricated one.

---

## Adding a result

See what still needs one:

```bash
node scripts/add-result.js --league premier-league --list
```

```
premier-league: 0 played, 380 still to come

  2026-08-21  Arsenal v Coventry City            arsenal-vs-coventry
  2026-08-22  Hull City v Manchester United      hull-vs-man-united
```

Add it:

```bash
node scripts/add-result.js \
  --league premier-league \
  --match arsenal-vs-coventry \
  --score 2-1 \
  --source-name "Premier League" \
  --source-url "https://www.premierleague.com/match/..." \
  --played 2026-08-21
```

Then rebuild:

```bash
node scripts/build-static-foundation.js
```

That is the whole matchday loop. About thirty seconds per match.

### Optional extras

```bash
  --scorer "home:Saka:23" --scorer "away:Wright:71"   # repeatable
  --attendance 60704
  --status "AET"                                      # or "FT (pens)"
  --penalties "4-3"                                   # required with FT (pens)
  --verified 2026-08-22                               # defaults to today
```

Leagues: `premier-league`, `la-liga`, `serie-a`, `bundesliga`, `ligue-1`.

---

## Checking your work

```bash
node scripts/validate-results.js
```

Confirms every result points at a real fixture, has integer scores, and carries a working
source URL. Catches a mistyped slug before it reaches the site.

```bash
NODE_PATH=/home/user/node_modules node tests/bryme-sports-tests.js
```

Asserts the whole rule holds: played matches are indexable and in the sitemap, unplayed ones
are noindex and out of it.

---

## What happens on the page

Before: kick-off time, venue, TV, pre-match notes, and an explicit statement that there is
no result to report. `noindex`, not in the sitemap.

After: full-time score, scorers by side, attendance, and a line reading *"Result confirmed
via [source] · checked [date]"*. Indexable, in the sitemap, and listed on
`/sports/<league>/results/` — which builds itself from the same file.

---

## Editing by hand

`content/results.json` is plain JSON if you prefer. Same structure, same rules — the build
and validator enforce them either way.

```json
{
  "premier-league": {
    "arsenal-vs-coventry": {
      "homeScore": 2,
      "awayScore": 1,
      "status": "FT",
      "playedOn": "2026-08-21",
      "scorers": [{ "team": "home", "player": "Saka", "minute": "23" }],
      "attendance": 60704,
      "source": { "name": "Premier League", "url": "https://www.premierleague.com/match/..." },
      "verifiedOn": "2026-08-21"
    }
  }
}
```

The match slug is the fixture's `id` + `-vs-` + `away`, exactly as it appears in the URL.

---

## Not built, and why

There is **no automatic results feed**. Every result is entered deliberately, with a source,
by a person who checked it. A feed would be faster and would also mean the site could publish
a wrong scoreline without anyone having looked at it. If you want one later, the place to add
it is a script that writes `content/results.json` in this format — everything downstream
already works and would need no changes.

After a sourced result is in, rebuild team pages so next/previous, form and
Matchweek Chronicles stay in sync:

```
python3 scripts/build-team-pages.py
```

See `docs/TEAM-PAGES.md`.

# Weekly editorial workflow — BRYME match pages

BRYME holds the complete fixture schedule for five leagues: **1,752 fixtures, every one with
a permanent page**. That database is never trimmed or regenerated.

What the workflow controls is a different question: *which of those pages is an indexable
editorial page*. A fixture nobody has written about is a schedule entry — `noindex`, absent
from `sitemap.xml`. Writing a preview promotes it. This is why the site is not submitting
thousands of empty fixture URLs to Google.

```
FULL FIXTURE DATABASE  (1,752 pages, always available)
        ↓  3–5 days before kickoff
WRITE THE PREVIEW      (add an entry to content/match-editorial.json)
        ↓  rebuild
INDEXABLE + IN SITEMAP (datePublished set, lastmod set)
        ↓  Wednesday–Friday: Google crawls it
MATCH KICKS OFF
        ↓  record the result
RESULT ON THE SAME URL (title flips to "Result & Analysis", dateModified updates)
        ↓  add post-match analysis
PREVIEW PRESERVED BELOW ("What BRYME said before kickoff")
        ↓
PERMANENT HISTORICAL PAGE
```

---

## Monday/Tuesday — what needs writing

```bash
node scripts/editorial-queue.js
```

```
TO WRITE - kickoff within 5 days, no preview yet (18)
  2026-08-21  T- 4  premier-league  Arsenal v Coventry City      arsenal-vs-coventry
  2026-08-22  T- 5  serie-a         Genoa v Napoli               genoa-vs-napoli

ALREADY LIVE - preview published, indexable (5)
  2026-08-22  T- 5  premier-league  Hull City v Manchester United  hull-vs-man-united

!! 2 fixture(s) inside the 3-day mark with no preview. Run --overdue.

Today: 2026-08-17. Window opens T-5, page should be live by T-3.
```

Useful flags: `--overdue` (inside 3 days, still unwritten), `--played` (finished, no result
recorded), `--league premier-league`, `--days 7`, `--today 2026-08-20` to plan ahead.

## Writing a preview

Add an entry to `content/match-editorial.json` under the league, keyed by the **same slug as
the URL**:

```json
"premier-league": {
  "arsenal-vs-coventry": {
    "publishedAt": "2026-08-17",
    "updatedAt": "2026-08-17",
    "overview": "…",
    "recentForm": "…",
    "headToHead": "…",
    "lastFiveMeetings": ["…", "…"],
    "homeAwayForm": "…",
    "keyPlayers": "…",
    "tacticalMatchup": "…",
    "historicalContext": "…",
    "underdog": "…",
    "outlook": "…",
    "scorePrediction": "…",
    "sources": [{ "name": "Premier League", "url": "https://…" }]
  }
}
```

Then `node scripts/build-static-foundation.js`.

**Three populated fields is the minimum** to go live. Below that the page stays dormant —
a stub cannot slip into the sitemap.

### Never invent team news

`injuries`, `suspensions` and `expectedLineups` are **deliberately omitted** unless a club or
official source has confirmed them. An omitted field renders as an explicit gap:

> **Expected lineups** — *No lineup has been announced. Expected XIs are not published here
> as speculation.*

That is the correct output, not a failure. It is better to show a reader that something is
unknown than to fill the space with a guess.

## After the match

Two steps, **on the same URL** — never a second page.

**1. The score** (sourced; the build refuses an unsourced result):

```bash
node scripts/add-result.js --league premier-league --match arsenal-vs-coventry \
  --score 2-1 --source-name "Premier League" --source-url "https://…" --played 2026-08-21
```

**2. The analysis** — add a `postMatch` object to the same editorial entry:

```json
"postMatch": {
  "publishedAt": "2026-08-22",
  "whatHappened": "…",
  "tacticalDevelopments": "…",
  "keyPerformers": "…",
  "disappointing": "…",
  "vsPrediction": "…",
  "analysis": "…"
}
```

Rebuild. The page now:

- keeps the **same URL and canonical**
- retitles to `Hull City 1-2 Manchester United — Result & Analysis`
- shows result → post-match analysis → **the original preview, preserved and dated**
- keeps `datePublished` at the preview date and moves `dateModified` to the update
- updates `<lastmod>` in the sitemap

**The pre-match text is never overwritten.** The validator and tests both fail if a
post-match update removes it. Readers can see what BRYME expected and what actually happened.

## Checks

```bash
node scripts/validate-editorial.js   # entries map to real fixtures, ISO dates, history intact
node scripts/validate-results.js     # every score sourced
NODE_PATH=/home/user/node_modules node tests/editorial-workflow-tests.js
```

The test suite covers the activation window, indexable/non-indexable state, sitemap
inclusion, `datePublished`, `dateModified`, the post-match transition, duplicate-URL
prevention and historical preservation.

## Asking Google to recrawl

```bash
node scripts/request-indexing.js --since 2026-08-15
```

Prints only the URLs whose content actually changed, for manual submission in Search
Console. **It does not call any indexing API and does not resubmit the site** — mass
automated submission is what buried these pages before. The sitemap advertises `lastmod`;
normal recrawling handles the rest. Use manual requests only where the delay matters.

## Rules the system enforces for you

| Rule | Enforced by |
|---|---|
| A fixture page exists for every scheduled match | build; test asserts >1,700 pages |
| Only written-up fixtures are indexable and in the sitemap | `editorialFor()` gate; tests |
| One fixture = one URL, forever | tests reject `-result`/`-preview` variants |
| Dates are ISO 8601 | build drops non-ISO and exits non-zero |
| A result must carry a source | `add-result.js`, build, validator all refuse |
| Post-match never erases the preview | validator + tests fail |
| Unknown team news is marked, not invented | renderer prints an explicit unconfirmed state |

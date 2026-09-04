# BRYME team pages + Matchweek Chronicles

Every top-five club lives under its league. One template. Comics only on the big clubs.

## URLs

Canonical pattern:

```
/sports/{league}/teams/{slug}/
```

Examples:

- `/sports/premier-league/teams/manchester-united/`
- `/sports/premier-league/teams/brentford/`
- `/sports/la-liga/teams/real-madrid/`
- `/sports/premier-league/teams/` — all 20 Premier League clubs

The old flat URLs (`/sports/teams/manchester-united/`) 301 to the league path.

Hub: `/sports/teams/` (clubs grouped by league).

## Rebuild

After a sourced result is added with `node scripts/add-result.js`:

```
python3 scripts/build-team-pages.py
```

That refreshes every team page, the hub, standings-from-results, next/previous, comics, sitemap inclusion, and the team-page jumps on match reports.

Do **not** run `node scripts/build-static-foundation.js` to refresh team pages. The foundation rebuild overwrites other sports HTML.

## Data

| File | Role |
| --- | --- |
| `content/teams.json` | Registry. Add a club here to mint a page. `id` must match `fixtures*.json`. |
| `content/matchweek-comics.json` | Original cartoon storylines. Only for matches that already have a sourced FT. |
| `content/fixtures.json` + `fixtures-la-liga.json` + `fixtures-serie-a.json` + `fixtures-bundesliga.json` + `fixtures-ligue-1.json` | Calendar |
| `content/results.json` | Sourced full-time scores only |
| `assets/img/sports/comics/` | Original generated artwork. No broadcast stills, no player photos. |

## Rules

- Do not lock a score without a `source.url`.
- Do not invent scorers. Comics may name a scorer only if `results.json` already has them.
- Speech bubbles are fictional cartoon-squad chatter, not quotes from real people.
- League position on a team page is computed from BRYME's sourced results. It is labelled as such. It is not an official table.
- Some 2026/27 Premier League second-half rows are stored as Jan–May 2026. Team pages sort/display those as 2027. Do not silently rewrite `fixtures.json` without a separate, checked pass.
- Do not create a new URL every matchweek. The team URL stays. The comic is a section on that page (`#mw-1`).
- Do not put noindex team pages in the sitemap. The builder rebuilds the sitemap from on-disk self-canonical indexable pages.

## Adding a club later

1. Confirm the fixture `id` in the right `content/fixtures-*.json`.
2. Add a record to `content/teams.json` (`slug`, `id`, crest path, founding/city/stadium from `content/club-history`).
3. Optionally write a comic in `content/matchweek-comics.json` after a sourced result.
4. Run `python3 scripts/build-team-pages.py`.

## Indexing

Index the 25 canonical URLs once after the first deploy. Do not resubmit Google sitemaps. Do not blast IndexNow with the whole sitemap. After later result updates, leave Google to recrawl; optionally ping only the team URLs that actually changed.

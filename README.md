# BRYME Media

BRYME Media is the extracted sports and entertainment archive from the main BRYME repository.

It contains:

- sports pages, match pages, reports and source datasets;
- movie, series and anime title interfaces;
- original entertainment articles;
- genre/year discovery routes;
- trailer and catalogue data; and
- the media assets and historical build scripts required to preserve the work.

## Migration status

Every page is deliberately `noindex,follow` until a final host is deployed and the following are approved:

1. permanent domain and canonical host;
2. sports-data source rights and update integrity;
3. title-image and other media rights;
4. current, accurate metadata;
5. a media-specific index allowlist; and
6. production HTTP behavior.

Do not remove `noindex` in bulk.

## Staging preview (GitHub Pages)

The archive is published as a QA preview at:

**https://ojeology.github.io/bryme-media/**

`.github/workflows/pages.yml` rebuilds and redeploys it on every push to `main`. The publish step runs `scripts/build-gh-pages.py`, which copies the static tree into `dist/` and rewrites absolute paths (`/assets/…`, `fetch("/content/…")`, canonicals) for the Pages URL prefix — the source tree is never modified, and the dead `bryme-media.onrender.com` canonical host is repointed to the preview URL.

Indexing safeguards (house rule: staging must never become an accidental Google index):

- every page carries `<meta name="robots" content="noindex,follow">` — the build script fails if any published page lacks it;
- the published copy ships a `Disallow: /` robots.txt as a secondary signal;
- no sitemap is published;
- do not submit this URL to Search Console or link to it from indexed pages.

The preview exists for visual and functional QA of the Sports & Entertainment rebuild — it is not an SEO surface. Search-engine verification token files are deliberately not published (the stale copies were removed from the repo root on 2026-10-01; the live domain keeps its own).

## Build

```bash
npm run build
npm test
npm start
```

`npm run build` applies the media navigation and forest-green compatibility layer without rewriting article bodies.

## Relationship to BRYME

The main BRYME publication now focuses on jobs, paid writing, opportunities and practical guides. This repository is maintained separately so Search and users receive a clear topical purpose from each publication.

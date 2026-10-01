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

## Landing & migration rule (owner directive)

**Work lands in bryme-media. A niche moves to nextclip (live) only when it is FULL and has NO
THIN pages.** Approval of a sample does not trigger migration — the gate below does.

- `npm run niche:status` audits each rebuilt niche against `content/niche-manifests.json`:
  **FULL** (rebuild set at target, every referenced title upgraded, hubs fully linked),
  **NO THIN** (every rebuild-set page clears its authored-copy floor) and **link integrity**
  (every root-relative link resolves). `--strict` exits non-zero until the gate is green.
- The floors live in `content/niche-manifests.json` and are read by the sample validator too,
  so the two gates can never drift apart.
- Migration additionally requires owner sign-off, an unfrozen live window (after the AdSense
  verdict) and the nextclip-side pre-flight (URL map, canonicals, sitemap/robots/allowlist,
  rollback plan) — tracked in the manifest's `migration_checklist`.

## Mass upgrade (v3 "Watch Next")

The archive is being rebuilt inside this repo — see `docs/UPGRADE-PROGRAM-BRYME-MEDIA.md`.
The upgrade is deliberately two-layered:

- **the system is mass:** `assets/media-v3.css` + the v3 shell (header, footer, mobile
  navigation, homepage) are applied to every page by `npm run build` — one build step
  upgrades the chrome of the whole archive without touching archived article bodies;
- **the content is a sample:** the new architectures ship as a reviewed sample only —
  4 recommendation lists (`/watch-next/…`), 8 sports explainers (`/sports/explainers/…`),
  5 upgraded title pages, and 3 hubs. Scale-up happens only after owner sign-off
  (roadmap Part 15).

Trailer facades mean pages ship **no iframes at all**; the privacy-enhanced player is
created by `assets/media-v3.js` only on an explicit play action.

## Build

```bash
npm run build
npm test
npm start
```

`npm run build` regenerates the v3 architecture sample (`scripts/build-v3-upgrade.py`),
then applies the v3 shell and rebuilds the homepage without rewriting article bodies
(`scripts/apply-media-brand.py`). The build must be a fixed point: running it twice
changes nothing (CI enforces `git diff --exit-code`).

`npm test` runs three gates: the media-shell validator (every page noindex + v3 theme +
bottom navigation), the upgrade validator (sample integrity, thin-content floor,
facade-only embeds, link resolution) and the HTTP validator (routes 200, containment
404s, security headers).

## Relationship to BRYME

The main BRYME publication now focuses on jobs, paid writing, opportunities and practical guides. This repository is maintained separately so Search and users receive a clear topical purpose from each publication.

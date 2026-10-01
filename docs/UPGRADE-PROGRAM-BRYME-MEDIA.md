# BRYME Media — Mass Upgrade Program (v3 "Watch Next")

Status: **drop 1 in progress** · Owner: BRYME · Scope: staging repo only (`ojeology/bryme-media`)
This program implements Parts 13–15 of the approved sitewide roadmap inside the staging
environment. Nothing here touches the live publication until the sample is reviewed and
approved for migration (Part 18, step 11).

## Why this exists

The approved roadmap splits BRYME's identity:

- **Writers** stays the flagship on the live site (research intelligence for writers).
- **Entertainment** becomes discovery: *"I loved this — what should I watch next?"*
- **Sports** becomes explanation: *"What does this football thing actually mean?"*

`bryme-media` holds the retired Sports & Entertainment archive. It is the safe place to build,
test and visually inspect the new layouts, recommendation architecture, internal linking and
video presentation **before** anything migrates live.

## The problem with the archive as it stood

The archive (~3,250 pages: 2,035 sports, 764 movies, 145 series, 128 anime) is a preserved
legacy build:

- pages average 150–400 words and read like database cards;
- the "hub" pages are walls — `movies/index.html` alone is 344 KB with 501 tiles;
- the shell was a 3.4 KB compatibility skin (`media-v2.css`) on top of a 264 KB legacy sheet;
- there is no recommendation layer, no explainer layer, and no video-first presentation.

## What "mass upgrade" means here (and what it does not)

**Mass = the system, not the content.** This drop upgrades:

1. **The shell — once, for every page.** A new design system (`assets/media-v3.css`) plus a
   v3 header / footer / mobile navigation applied to all ~3,258 pages by the build. One build
   step upgrades the chrome of the entire archive.
2. **The architecture — as a representative sample.** Per roadmap Part 15, new *content types*
   ship as small, strong examples, not hundreds of pages:
   - 3 entertainment **recommendation pages** (`/watch-next/…`);
   - 5 upgraded **title pages** (in place, same URLs);
   - 8 sports **explainer pages** (`/sports/explainers/…`);
   - 3 hubs (`/entertainment/`, `/watch-next/`, `/sports/explainers/`) + a rebuilt homepage.
3. **The quality gates.** New validator (`scripts/validate-upgrade.js`) that fails the build if
   the sample drifts: missing noindex, thin copy, video-only pages, autoplay embeds, broken
   internal links, tracking code.

**Not in this drop (deliberately):** bulk-generating hundreds of rec/title/explainer pages.
That happens only after the owner reviews the sample and approves the structures
(roadmap Part 15 → Part 18 step 11).

## Visual identity (v3)

- Deeper cinematic base (`#070a13`), poster-led layouts, editorial serif display type for
  headlines, system sans for UI — no external fonts, no external JS.
- BRYME green (`#58e39b`) kept as the family thread; Entertainment accent coral (`#ff7a59`);
  Sports accent lime (`#c9f26e`).
- Video presentation upgrade: **click-to-play facade** — the page ships zero iframes; the
  privacy-enhanced `youtube-nocookie.com` player is injected only on an explicit play action.
- Legacy pages keep their article bodies untouched; they inherit the new shell, background
  and type scale only.

## Acceptance gates (all must pass before this drop is considered done)

- `npm run build` is a fixed point (`git diff --exit-code` clean on a second run) — CI enforces.
- `npm test` green: media shell validator (all pages noindex + v3 theme + bottom nav),
  upgrade validator (sample integrity), HTTP validator (routes 200, containment 404s).
- GitHub Pages preview rebuilds; every new URL answers 200 with the v3 shell.
- Every new page: noindex,follow · ≥350 words of authored copy · ≥3 working internal links ·
  no autoplay · no ads/tracking.

## Phases after this drop (need owner sign-off)

1. **Review pass** — owner walks the preview: `/entertainment/`, `/watch-next/`,
   `/sports/explainers/`, the 5 upgraded title pages, comparison page `/entertainment/classic/`.
2. **Scale entertainment** — once approved, extend the recommendation engine
   (data/rec-data.json has 648 titles + 34 curated relation sets; the generator scales).
3. **Scale sports** — expand the explainer network from the same template.
4. **Migration plan** — map approved structures onto the live site (canonicals, redirects,
   sitemap policy) per roadmap Part 18 step 11.

## Files of record

| Path | Role |
| --- | --- |
| `assets/media-v3.css` | design system (shell + components) |
| `assets/media-v3.js` | click-to-play facade, rails, small a11y helpers |
| `scripts/build-v3-upgrade.py` | generator: hubs, rec pages, title upgrades, explainers |
| `content/upgrade-entertainment.json` | authored Entertainment pack (rec + title copy) |
| `content/upgrade-sports.json` | authored Sports explainer pack |
| `scripts/validate-upgrade.js` | sample integrity gate (CI) |
| `scripts/apply-media-brand.py` | shell application (v3 chrome, css swap, homepage) |

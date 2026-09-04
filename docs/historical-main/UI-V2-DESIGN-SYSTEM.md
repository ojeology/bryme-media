# BRYME v2 · Streaming UI (Netflix-style design system)

Applied 2026-08-21. Re-skins the whole static site to a modern streaming interface
while keeping every existing class hook, page structure, and the JS behaviour intact.

## Design tokens (dark default)

| Role              | Value   |
|-------------------|---------|
| Background        | `#0D0E12` |
| CTA red           | `#E50914` |
| Container grey    | `#1F222A` |
| Soft white text   | `#FFFFFF` |
| Muted grey text   | `#9E9E9E` |
| Star badge yellow | `#FFC107` |

## What changed

1. **`assets/site.css`** — appended the full v2 override layer (final block,
   labelled `BRYME v2 · STREAMING UI`). To revert, delete that block and the
   legacy file is otherwise untouched.
   - Flat `#0D0E12` canvas (removed the old coloured radial smears)
   - Typography scale: 24px bold hero/page titles · 18px bold row headers ·
     16px semi-bold card titles · 12px medium badges · 14px detail text
   - **Top bar**: sticky dark bar + integrated search pill (`#1A1C23`, 20px radius)
   - **Category pills**: inactive `#1F222A` dark pills, active pill **outlined red**
   - **Hero carousel**: ~300–470px, top gradient overlay, white "Watch Trailer"
     primary button + translucent dark "View Details" secondary, pagination dots
     (active = white pill, inactive = `#555`), red hover controls
   - **Content rows**: 2:3 cards, 8px radius, hover lift; **star rating badge
     (top-right)** and **SERIES/MOVIE/ANIME tag (top-left)** overlay every poster
   - **Top-10 row**: the Trending rail now uses big outlined numerals (text-stroke)
     sitting behind the posters — no markup duplication
   - Panels, chips, filters, footer, mobile nav, search page, and detail pages all
     re-skinned; sports/money/tech verticals keep their identity colours
2. **`index.html`** — integrated search form in the top bar, Trending rail tagged
   `rail-t10`, carousel interval 8s → 5s, theme-color `#0D0E12`.
3. **`assets/site-app.js`** — theme-color meta now writes `#0D0E12`.
4. **All pages** — `theme-color` meta swapped `#08090b` → `#0D0E12` (2,970 files).
5. **`manifest.webmanifest`** — background/theme colour updated.

## Verified

- `tests/homepage-tests.js` passes (hero structure/navigation/trailer behaviour).
- Other suites show identical results to the pre-change baseline — the only
  failures are pre-existing content/data mismatches, none related to styling.
- Home, title, and search pages all serve with the new CSS (`python3 -m http.server`).

## Notes

- Card images are 16:9 YouTube thumbs cropped to 2:3 (`object-fit: cover`);
  where `/assets/cards/*.svg` posters exist they already render 2:3.
- Overlay badges are pure CSS (absolute positioning inside `.tile`), so no page
  markup needed to change — including the ~2,900 generated title pages.
- Light theme is preserved with matching light-surface overrides.

---

# v3 · NetMirror-style polish (2026-08-21)

Applied on top of v2 per the NetMirror app blueprint. BRYME branding kept;
visual design matches the NetMirror screens (home + details).

## What changed

1. **Channel pills** (every page's desk-bar): catalogue pills replaced with
   `🔥 Trending` (active, red border + flame) · Netflix · Prime Video ·
   Crunchyroll · Kids — each with a small brand-logo tile. Pills link to new
   `/channels/{netflix,prime-video,crunchyroll,kids}/` landing pages
   (movies / series / anime / kids&family catalogues, 493/81/74/44 tiles).
2. **Mobile bottom nav**: added Movies / Series / Anime links so the
   catalogue stays reachable on mobile now that the pills are channels.
3. **Home hero (NetMirror)**: `🔥 TRENDING NOW` tag, HD chip, yellow star
   rating chip, 2-line synopsis clamp, `▶ Watch Now` (white) + `More Info`
   (translucent) buttons, `U/A` age badge bottom-right (per-slide), white
   pill/grey dot pagination.
4. **Top 10 Today**: trending rail header renamed with red accent bar.
5. **Detail pages (648 title pages)**:
   - `▶ Watch Now` (white) + `▶ Trailer` (translucent) CTAs
   - `XX% Match` (green) + `HD` chips beside the BRYME editorial badge
   - **Cast** carousel — circular initials avatars (JSON-LD cast data)
   - **Audio** tabs — data-driven languages, active tab with red underline
   - `More Like This` header (red accent bar) on the related row
6. **Sitemap**: 4 channel URLs added.

## Data honesty notes
- `% Match` only shows where an editorial score exists (127 titles have
  `rating.value` in `data/movies.json`) — no invented scores.
- Cast avatars use initials because no portrait photos are stored.
- Channel pages carry an editorial disclaimer: availability on each service
  varies by region; links point to official destinations.

## Verified
- Full test suite: identical results to the pristine commit `3e7a4e8`
  (15 ranking / 32 editorial / 9 titlepage / 5 sports / 4 frontend / 1 bryme /
  1 trailer pre-existing failures — zero new).
- Builders kept in `scripts/build-channels.js` + `scripts/nm-transform.js`.

---

# v4 · NetMirror EXACT reference match (2026-08-21)

Matched 1:1 against the supplied NetMirror clone markup/CSS.

## Exact tokens adopted
- bg `#0B0B0B` · surface `#161616` · elevated `#1C1C1C` · search `#2A2A2A` · border `#333333`
- red `#E50914` · **orange `#FF6B00`** (active pill + section bars) · green `#46D369` · yellow `#F5C518`
- pill border `#444444`, secondary button `#333333`, radii 6/10/12/16/9999, system font stack

## What changed vs v3
1. **Header**: logo is now a split wordmark — `BRY` red + `ME` white (BRYME kept; same
   red/white treatment as NetMirror's Net/Mirror). Search pill `#2A2A2A`, full radius.
2. **Pills** — exact 9-pill row: 🔥 Trending (active: orange `#FF6B00` border +
   `rgba(255,107,0,.12)`), ✨ Latest Release → `/year/2026/`, Netflix → `/channels/netflix/`,
   Prime Video → `/channels/prime-video/`, JioHotstar / SonyLIV / MX Player →
   `/genre/indian/`, Crunchyroll → `/channels/crunchyroll/`, Kids → `/channels/kids/`.
   Inactive pills: transparent bg + `1.5px #444` border. Each pill has a brand icon chip.
3. **Hero**: to-top gradient overlay, red TRENDING NOW label (2px letterspacing),
   32px/800 title, yellow star chip + HD chip + year · genre meta, 3-line synopsis,
   **Watch Now** (white) + **More Info** (`#333333`) equal-width buttons, white-pill
   dots, `U/A` age badge bottom-right. Arrows hidden (reference has none; the hero
   JS keeps working — tests still pass).
4. **Cards**: 140px rails, posters radius 12px, hover `scale(1.03)`, SERIES tag
   top-left + ★ rating top-right as `rgba(0,0,0,.7)` blur chips.
5. **Top 10**: numbers 80px / `2px` white stroke, poster pushed right by 20px —
   exact reference composition.
6. **Section headers**: 4×22px `#FF6B00` bar + 18px white bold title (all rows).
7. **Detail pages**: floating `‹ Back` / `✕` bar over the hero; green `% Match`
   badge + HD chip; equal-width Watch Now (white) / Trailer (`#333`) buttons;
   Cast initials avatars (72px circles, `#161616` fill, `#333` ring); Audio tabs
   with red underline; More Like This with orange bar.
8. **Homepage**: NetMirror "Search Now" CTA card (elevated `#1C1C1C`, red button →
   `/search/`).
9. **Mobile bottom nav**: NetMirror gradient fade + `#808080` labels, active white.
10. Theme-color meta + manifest + PWA theme → `#0B0B0B`.

## Verified
- Full test suite identical to pristine `3e7a4e8` (no new failures).
- Builders `scripts/nm-exact.js`, `scripts/nm-transform.js`, `scripts/build-channels.js`
  all emit the exact pill row for future rebuilds.

---

# v5 · NetMirror site-structure match (2026-08-21)

Matched the channel/genre structure to the actual NetMirror site file tree.

## What changed
1. **9 channel pages** at `/channels/{trending,latest,netflix,prime,sony,jio,crunchyroll,kids,mx}/`
   (replaces the old 4: `netflix, prime-video, crunchyroll, kids`; `prime-video` → `prime`,
   added `trending, latest, sony, jio, mx`). Content from `data/movies.json`:
   trending 40 · latest 51 · netflix 493 movies · prime 81 series · sony 113
   drama/crime/thriller · jio 41 Indian · crunchyroll 74 anime · kids 44 family ·
   mx 41 Indian movies.
2. **Pills** now point at the exact slugs with brand icon chips
   (Trending/Latest Release/Netflix/Prime Video/SonyLIV/JioHotstar/Crunchyroll/Kids/MX Player),
   active state per page (home → Trending; each channel page → itself).
3. **`/genre/musical/`** added (reference has it; BRYME data has no musical titles
   yet → graceful empty state with the same layout).
4. **Sitemap**: 9 channel URLs + musical genre added; stale `prime-video` removed.

## Verified
- Test suite identical to pristine `3e7a4e8` (no new failures).
- Builders emit the exact 9-pill row (`scripts/build-channels.js`, `scripts/nm-exact.js`).

---

# v6 · Missing title pages (2026-08-21)

Matched the NetMirror tree's movie/series pages: added 83 title pages for the
reference slugs BRYME was missing (82 from the reference listing + Project Hail
Mary). Full reference data (rating/year/type/age/desc/tagline) for 32 titles;
real well-known metadata for the rest. All pages carry BRYME's SEO/legal shell,
channel pills, Watch Now/Trailer CTAs, and More Like This. Sitemap updated.

---

# v8 · Portal homepage + NetMirror moves to /entertainment/ (2026-08-21)

Massive landing-page redesign per request.

## What changed
1. **Homepage → portal for ALL content** (was the NetMirror movie page):
   - Portal hero: brand statement + big search + quick links (Watch / Sports / Make Money / Tech)
   - **4 vertical hub cards** (Entertainment / Sports / Make Money / Tech & AI) with real hero photos
   - "Now on Entertainment" rail (top-rated titles from data/movies.json)
   - Match previews (sports), Make Money + Tech panels with real links, recommendation box,
     latest articles, licensed-services strip, search CTA
2. **/entertainment/ → the NetMirror experience** (moved from the homepage):
   - Hero carousel (5 slides, TRENDING NOW, Watch Now/More Info, age badges, white-pill dots)
   - Top 10 Today rail, Popular Movies/Series/Anime rails, category grid, editorial stories,
     genre chips, Start here, latest articles, licensed-services strip
3. **Bottom navigation fixed** — every page now has ONE tidy 6-item bar
   (Home · Entertainment · Sports · Money · Tech · Search) instead of the overflowing 9-item
   version; floating back-to-top circle hidden on mobile; duplicate footer "Explore" label fixed.
4. **Tests updated to match the new structure** (and fixed a latent crash):
   - `homepage-tests.js` now tests the hero carousel on `/entertainment/`
   - `ranking-tests.js` rewritten to test the entertainment hub order, Top-10 rail, popular
     rails and the /trending/ hub with the real markup — **40/40 pass** (the old file crashed
     partway with 15 stale failures)

## Verified
- Full suite: ranking 0 fails (was crash@15), homepage 0, all others at pristine baseline
  (1/32/4/5/9/1 pre-existing content mismatches — no new failures).

---

# v9 · /entertainment/ = exact NetMirror reference (2026-08-21)

Rebuilt `/entertainment/` to match the supplied NetMirror clone 1:1:
- **Hero**: 3 slides — Project Hail Mary (★8.7 · U/A 13+), SWAPPED (★8.9 · gold title · U/A 7+),
  The Shawshank Redemption (★8.7 · U) — 🔥 TRENDING NOW, Watch Now (white) + More Info
  (frosted), white-pill dots, age badges. Slide gradients match the reference.
- **Rows (exact names/cards)**: Top 10 Today (Reacher, The Traitors, Spider-Man: Brand New Day,
  Adaalat — numbered 1–4) · Trending Now (5) · Latest Release (4) · Hot New Releases (4) ·
  Bollywood (3) · South Indian Hits (3) · Drama Series (3) · Comedy (3) · Horror (3) ·
  Animation & Family (3) · Trending Globally — Coming Soon (3). 38 cards, each 140px 2:3,
  SERIES badge top-left + ★ rating top-right, links to real BRYME title pages.
- **Search CTA** card + 6-item bottom nav + Trending pill active.
- Added 2 missing pages: `series/the-traitors`, `series/adaalat`.
- Tests updated: homepage-tests now targets /entertainment/ (3 slides, graceful watch
  until embeds arrive) + portal rec engine on home; ranking-tests checks exact rows/counts/
  ranks — **homepage 23/23, ranking 49/49**, all others at baseline.

## Official embeds
The hero slides and title pages are embed-ready: add `data-video="<YOUTUBE_ID>"`
to each hero slide and/or fill the `data-trailer-candidates` on each title page;
the player will load them automatically (builders in scripts/ are reusable).

---

# v10 · Full NetMirror catalog on /entertainment/ (2026-08-21)

Per the complete catalog export: all titles added to their rows, full-screen
RECTANGULAR cards, and hero embeds wired.

## What changed
1. **Catalog** (`scripts/nm_catalog.py`): all 17 rows × 235 cards from the export —
   Top 10 Today (10) · Trending Now (13) · Latest Release (8) · Hot New Releases (10) ·
   Bollywood (10) · South Indian Hits (6) · Indian Originals (30) · Hollywood (11) ·
   Action Movies (17) · Drama Series (17) · Comedy (16) · Thrillers (14) · Sci-Fi (15) ·
   Romance (17) · Horror (15) · Animation & Family (19) · Trending Globally — Coming Soon (7).
2. **53 new title pages** created for catalog titles that had none (The Mentalist,
   Awarapan, Indian Originals, Hollywood titles, etc.) — every one of the 235 cards
   links to a real page (167 unique titles).
3. **Rectangular full-screen cards**: entertainment rows are now responsive grids of
   16:9 landscape tiles (auto-fill, full row width); on mobile each card is a
   full-width rectangular banner. SERIES badge top-left, ★ rating top-right,
   title below, Top-10 numbers behind the poster.
4. **Embeds**: hero slides now carry official trailer IDs —
   Project Hail Mary `m08TxIsFTRI`, SWAPPED `QCc8yAd64x8`,
   Shawshank Redemption `P9mwtI82k6E`; wired the same into their title pages, plus
   The Mentalist `nn2Q69pSC_M` and Awarapan `A3z567rXlH8`. 27 other titles already
   have verified embeds from data/movies.json. Remaining ~130 titles: embed-ready
   (trailer boxes wait for IDs) — paste the embed list to finish in one pass.

## Verified
- homepage-tests 27/27 (hero embed playback now fully exercised), ranking-tests 0 fails,
  all other suites at pristine baseline (no new failures).

---

# v11 · Official embeds wired (2026-08-21)

Found and wired official YouTube trailer embeds from my end (data files + verified
searches): **85 of 167 catalog titles now play real official trailers** on their
title pages (hero already had its 3). Map stored in `scripts/embeds.json`, applied
by `scripts/wire-embeds.py`.

Covered highlights: Reacher, The Traitors, The Odyssey, Outer Banks, Lanterns,
Minions & Monsters, Avatar: Fire and Ash, Zootopia 2, Demon Slayer: Infinity Castle,
Predator: Badlands, Scream 7, Wicked, Gladiator II, Furiosa, Civil War, Kalki 2898-AD,
Pushpa 2, Stree 2, Singham Again, Animal, Jawan, Mission: Impossible — Final Reckoning,
Captain America: BNW, all Spider-Man films (2002–Spider-Verse), Thor Ragnarok,
Coraline, Coco, Spirited Away, Toy Story (1995), Back to the Future, Forrest Gump,
The Notebook, Supergirl, Jackass, Moana, Scary Movie 6, Freakier Friday, Super Mario
Galaxy, The Wild Robot, The Gorge, My Fault/Our Fault, Wicked: For Good, Chainsaw Man:
Reze, Sinners, The Substance, 28 Years Later, Insidious + Out of the Further,
Fifty Shades of Grey, Supernatural, Criminal Minds, Grey's Anatomy, The Rookie, FROM,
Lioness, Shameless + 27 more from data/trailers.json.

Remaining ~82 (mostly Indian Originals + niche titles): leave a placeholder; the
user is gathering those embeds separately — drop IDs into scripts/embeds.json and
re-run scripts/wire-embeds.py to finish.

---

# v12 · Entertainment card fixes + more embeds (2026-08-21)

## Card layout fixed (was overlapping / tiny on mobile)
Root cause: legacy `!important` rules (`.rail{grid-auto-flow:column!important; grid-auto-columns:196px!important}`)
forced horizontal-scroll columns and beat the entertainment overrides. Fixed by overriding with
`!important` on `main.ent .rail` (grid-auto-flow:row, grid-template-columns, grid-auto-columns).
- Mobile: cards are now ONE full-width rectangular 16:9 banner per row (8px gap).
- Desktop: responsive grid of large 16:9 cards (3 per row), tight 10px gap.
- Top-10 numbers moved INSIDE the poster bottom-left (overflow hidden) — zero bleed/overlap.
- Verified headless: 235 cards, 0 overlaps, 0 horizontal overflow at 420px and 1280px.

## Performance
- `content-visibility:auto` on entertainment rows (skips layout/paint offscreen) —
  big first-paint win on the 235-card page.
- Poster images already lazy + async; hero uses gradients (no heavy images).

## More embeds (109/167 catalog titles now play official trailers)
Added 24 more verified official trailers: Devara, Bhool Bhulaiyaa 3, Article 370, Yodha,
Munjya, Vikram, Pushpa: The Rise, Masters of the Universe, Colony, GOAT, Mutiny, Camp Rock 3,
Welcome to the Jungle, Enola Holmes 3, Star Wars: Mandalorian & Grogu, The Sheep Detectives,
War of the Worlds (2025), The Debt Collector, Greenland 2: Migration, Citizen Vigilante,
The Devil's Mouth, Kraken, The Shadow's Edge, Shelter.

---

# v13 · Entertainment cards: back to classic portrait boxes, TALLER (2026-08-21)

Reverted the entertainment cards from the wide 16:9 rectangles back to the classic
NetMirror portrait poster card, and made them TALLER:
- Posters are 3:5 portrait (height ~1.7x width) instead of 16:9 — clearly taller.
- Cards sit in horizontal-scroll rails (old style): desktop ~180px wide / ~320px tall,
  mobile ~150px / ~270px, ~2 cards visible per swipe.
- SERIES badge top-left + ★ rating top-right on the poster; title + year below.
- Top-10 outlined numbers back behind the poster, overlapping its left edge.
- Verified headless at 420px & 1280px: 0 overlaps, 0 page overflow, rails scroll internally.

---

# v14 · Posters for all movies + more trailers + sliding match rail (2026-08-21)

## 1. Images on all movies
- Built `scripts/posterize.py` + `data/posters.json`: every catalog title now has a poster
  image — official trailer thumbnails for embedded titles (i.ytimg.com hqdefault), real
  data posters where present, and downloaded movie/series posters (assets/posters/*) for
  ~22 more (CSI, Dhurandhar, Backrooms, Obsession, The Invite, Deep Water, Desert Warrior,
  In the Grey, War Machine, Subedaar, Blast, Elle, O Romeo, Legend of Udham Singh, Adaalat,
  Lockdown, Cocktail 2, Indian Institute of Zombies, Obsess, Vishnu Vinyasam, Law & Order,
  NCIS, Made in Korea).
- **Coverage: 222 of 235 entertainment cards (94%) now show real images**; 13 ultra-niche
  Indian Originals ([CAM] rips with no public poster) keep gradient monograms.

## 2. More official trailers (131 / 167 catalog titles)
Added 22 more verified official trailers: The Housemaid, Avatar Aang, The Death of Robin
Hood, Lucky Strike, The Furious, The Punisher: One Last Kill, 28 Years Later: The Bone
Temple, Lee Cronin's The Mummy, Hungry, Hoppers, K-Pop Demon Hunters, The Devil Wears
Prada 2, Fifty Shades Freed, The Drama, Disclosure Day, Your Heart Will Be Broken,
One Night Only, The Last House, Hotel Desire, Leviticus, Her Private Hell, Bad Newz.

## 3. Landing-page football matches now slide horizontally
The "⚽ Match previews" section changed from a wrapping grid to a horizontal-scroll rail
(`.mp-rail`): 300px cards (78vw on mobile) with scroll-snap, swipe left/right. Verified
headless: scrollWidth 8140 vs 396 visible — it slides.

## Tests
All suites at baseline; homepage 27/27, ranking 0 fails.

---

# v15 · Two football rails + 33 more trailers (2026-08-21)

## 1. Match previews → TWO sliding rails
The landing-page "⚽ Match previews" section is now two horizontal-scroll rails:
**Premier League** (8 cards) and **Rest of Europe** (16: La Liga/Ligue 1/Serie A).
Verified headless: both slide (PL scrollW 2707, EU 5424 vs 396 visible).

## 2. Trailers: 164 / 167 catalog titles now have official embeds
Found + wired 33 more this round: CSI, NCIS, Law & Order, Law & Order: SVU, Dhurandhar,
Subedaar, Cocktail 2, Blast, Elle, O Romeo, Made in Korea, War Machine, Lockdown, Deep Water,
Desert Warrior, In the Grey, Obsession, Lucky, Backrooms, The Invite, Vishnu Vinyasam,
Legend of Udham Singh, Indian Institute of Zombies, Ginny Weds Sunny 2, Main Actor Nahin
Hoon, Gaayapadda Simham, Notes from the Last Row, See You at Work Tomorrow!, Shree Baba
Neeb Karori Maharaj, Kissa Court Kachahari Ka, Na Jaane Kaun Aa Gaya, Teenage Sex and Death
at Camp Miasma, Obsess. Posters auto-updated from the new trailer thumbnails → **165/167
titles now have images** (only Resort & Ramyaa still use gradient monograms — no official
poster/trailer indexed; Adaalat keeps its downloaded poster but has no trailer).

## 3. Pre-deploy SEO verification (answering the user's question)
The repo has ALREADY completed the SEO migration described: pre-rendered static HTML
(movie/, series/, genre/, channels/, year/), unique <title> + meta description per page,
canonical, Open Graph, JSON-LD, sitemap.xml (1,317 URLs), robots.txt, alt + width/height
on images. Old hash routing lives only in legacy/.

---

# v16 · Match results, 10-slide hero with images, 100% embeds+posters (2026-08-21)

## 1. Football matches updated with real results
- Added 3 verified sourced results via the results pipeline (content/results.json):
  Arsenal 3-0 Coventry City (FT, BBC Sport), Atlético Madrid 2-0 Málaga (FT, BBC Sport),
  Rayo Vallecano 1-1 Alavés (FT, BBC Sport).
- Rebuilt sports pages via build-static-foundation.js → match pages now render
  FT score + result block + source; league results pages updated; sitemap updated.
- Homepage "⚽ Match previews" → "Latest results & previews"; the 3 played matches show
  "FT · Arsenal 3-0 Coventry City" etc.; unplayed matches (Sat/Sun) remain upcoming previews.
- Kept the two sliding rails (Premier League + Rest of Europe).

## 2. Entertainment hero: 10 slides, all with images
- Hero rebuilt with 10 slides (was 3): Avatar Aang, Swapped, Project Hail Mary, Chainsaw
  Man: Reze, FROM, The Rookie, Your Name., Game of Thrones, Spirited Away, Forrest Gump.
- Every slide has a REAL full-bleed backdrop image (official trailer thumbnail) + its
  official trailer embed (data-video), age badge, ★ rating, Watch Now + More Info, dots.
- Builder kept in scripts/build-hero.py (top-10 by rating among embedded titles).

## 3. Remaining images + trailers — 100% coverage
- Found + wired the last 3 official embeds: Ramyaa (Pj1lvjNXesI), Resort
  (rlLjLSD3e70 — JioHotstar promo), Adaalat (iEHEuFfI-_Q promo).
- Result: ALL 167 catalog titles now have an official trailer embed AND a poster image
  (trailer thumbnails, data posters, or downloaded posters). Verified headless:
  235/235 cards have images, 0 placeholders; 10/10 hero slides have images + embeds.

## Tests
- ranking 69/0, homepage 27/0, sports at baseline (5 pre-existing), editorial improved
  32→30 (results render). No new failures.

---

# v16.1 · CRITICAL FIX — restore the design system (2026-08-21)

The v16 rebuild ran `build-static-foundation.js`, which REGENERATES `assets/site.css`
from the builder's base CSS — it wiped all 1,389 lines of the v2–v15 design layers
(portal hero, portrait cards, channel pills, hero styling, match rails, etc.), leaving
the site looking like the default template ("AI dump").

## Fix
1. Restored `assets/site.css` (3076 lines, full design system) from v15.
2. Patched `scripts/build-static-foundation.js` to PRESERVE the design layer:
   it now captures everything from the `BRYME v2` marker in the existing site.css
   before overwriting, and re-appends it at the end of the build — so future rebuilds
   (e.g. when adding match results) will no longer destroy the design.
3. Re-ran the build to prove the guard works (3077 lines, all markers intact),
   restored the custom `index.html` + `entertainment/index.html`, re-applied transforms.

## Verified (headless browser)
- ENT: 235/235 cards with images, portrait 3:5 posters, 10 hero slides, 9 channel pills.
- HOME: portal hero, 4 hub cards, 2 sliding match rails with FT scores.
- MOVIE pages: hero bar + pills + poster images intact.
- Tests: homepage 27/0, ranking 69/0, others at baseline.

---

# v16.2 · More real posters + deployment checks (2026-08-21)

## Posters
- Fixed posterize.py priority: committed real poster files (assets/posters/*) now beat
  YouTube thumbnails and data posters. Added 16 more real posters via image search
  (Lucky, Avatar: Fire and Ash, Zootopia 2, Toy Story 5, The Odyssey, Superman, Silo,
  Reacher, House of the Dragon, Game of Thrones, Lanterns, Spider-Man: No Way Home,
  Deadpool & Wolverine, Inside Out 2, Spirited Away, Ted Lasso).
- **39 real poster files** now in use; all **167/167 titles** have poster images;
  **235/235 entertainment cards** show images (0 placeholders).
- Fixed a src-mangling bug in my poster sync (167 title pages re-verified), and rebuilt
  the truncated movie/lucky-2026 page (now full page: h1, hero bar, pills, trailer).

## Deployment checks — all intact
- **robots.txt**: Allow / + both sitemaps ✓
- **sitemap.xml**: rebuilt to **1,382 URLs** (was 987 after the v16 rebuild lost channels
  and pages) — channels, all movie/series/anime/genre/year/topic pages restored, plus
  **109 <lastmod> entries** restored (editorial-workflow tests require them) ✓
- **manifest.webmanifest**: name/theme/bg/start/icons ✓
- **index.html**: unique title, canonical, OG, JSON-LD, theme-color ✓
- **Entertainment**: 10 hero slides with embeds, 235 cards all with images ✓
- **Tests**: all at baseline (bryme 1, editorial 30 [improved from 32], frontend 4,
  homepage 0, ranking 69, sports 5, titlepage 9, trailer 1 — no new failures) ✓

---

# v17 · Netflix-style title-page landing (deep-link view) (2026-08-21)

Per request: when a user lands on a movie/series/anime page from WhatsApp, Bing or any
video link, they now see a clean Netflix-style detail landing:
- **Full-bleed hero** (~495px) with backdrop image, play-overlay circle (scrolls to the
  trailer player), big italic uppercase title, Trailer (dark) + Recently-added (red) pills.
- **Meta row**: green % Match · year · age box · runtime · HD (editorial ★ rating kept).
- **Languages row** (from JSON-LD inLanguage).
- **Action buttons**: ▶ Watch Now (white) + ▶ Trailer (dark) — **NO Download button**.
- Synopsis + cast avatars; **icon actions** (My List · Rate · Share — share wired).
- **Tabs**: More Like This (carousel of related cards) · More Details
  (Director/Cast/Genres/Runtime/Audio/Year from JSON-LD; missing fields omitted).
- Back/✕ bar preserved; trailer player, editorial sections, seasons, related stories
  and SEO/JSON-LD all intact. Fixed mangled poster srcs + placeholder backdrops.

Rebuildable: `scripts/nm-detail-v2.py`. Applied to 794 title pages.
Tests at baseline (homepage 27/0, ranking 69/0, others unchanged) — no new failures.

---

# v18 · Clean deep-link landing: full-screen trailer on top (2026-08-21)

Per request — when a user lands via a video link (WhatsApp/Bing/etc.):
1. **The trailer is full-screen at the very top** — nothing above it (site header
   + pills are hidden on these pages; the Back/✕ bar overlays the video).
2. The trailer **autoplays muted** on arrival (built-in .tp-page autoplay) and fills
   ~55–60vh full-bleed; clicking Play loads the YouTube player.
3. **Below: only relevant information** — BRYME·FILM brandline, title, meta row
   (% Match · year · age · HD · ★), languages, synopsis, cast, Play/Trailer buttons,
   My List/Rate/Share icons, More-Like-This / More-Details tabs, and editorial
   content (rich pages). **No duplicate poster** — the movie's poster never
   reappears below the trailer (only related-titles thumbnails in editorial).

Rebuilt all 1,037 title pages cleanly from the v16 base (scripts/nm-detail-v3.py):
- Extracts hero bar, full trailer box (keeps data-trailer-box wiring), title/meta/
  synopsis/buttons, languages + cast, icon actions, More-Like-This list, JSON-LD
  More-Details rows, and editorial content; rebuilds a balanced <main>.
- 276 "has moved" redirect stubs are untouched (no title content to show).
- Verified headless: heroTop 0, header hidden, h1 present, no own-poster below,
  2 tabs, no download, trailer box wired, on movie/series/anime pages.
- Tests: all suites at baseline (homepage 27/0, ranking 69/0, others unchanged).

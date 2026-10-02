# BRYME Media — Mass Upgrade Program (v3 "Watch Next")

Status: **Drop 6 staged (2026-10-02)** — Sports has 64/1,213 explainers, zero thin pages and clean concept/hub/link checks, but remains **NOT READY** for migration. Build/tests pass; all rebuilt pages stay noindex. · Owner: BRYME · Scope: staging repo only (`ojeology/bryme-media`)

## Review the drop (owner)

| What | URL |
| --- | --- |
| New front door | https://ojeology.github.io/bryme-media/ |
| Entertainment hub (new) | https://ojeology.github.io/bryme-media/entertainment/ |
| Entertainment hub (old, for comparison) | https://ojeology.github.io/bryme-media/entertainment/classic/ |
| Recommendation lists | https://ojeology.github.io/bryme-media/watch-next/ |
| Football explainers | https://ojeology.github.io/bryme-media/sports/explainers/ |
| Title page example (upgraded) | https://ojeology.github.io/bryme-media/movie/dune-part-two/ |

Verification on ship: quality gate + Pages publish both green; consecutive builds
byte-identical (fixpoint); all sample pages noindex with v3 theme; 0 iframes in source;
internal links resolve; live URLs 200 (10/10 checked).
This program implements Parts 13–15 of the approved sitewide roadmap inside the staging
environment. Nothing here touches the live publication until the sample is reviewed and
approved for migration (Part 18, step 11).

## Drop 6 — athletics opens with five sourced explainers (2026-10-02)

The next phase-2 sport is athletics. Batch 6a adds five question-led pages: the 100m race, false
starts, the 4×100m exchange, long-jump scoring and the high jump. Each page is 1,082–1,150 visible words, includes official World Athletics rule references, has three concept links and keeps the
same answer → explanation → example → misunderstandings → FAQ anatomy. The generator now renders
an optional “Rules and sources” block for authored citations.

**QA:** `npm run build` and `npm test` pass; a second build is byte-stable for the Sports explainer
tree. The full Sports readiness audit now sees **64 / 1,213** explainers, zero thin pages, zero
weak concept networks, zero missing hub entries and zero link issues. This is still **NOT READY**:
1,149 remain by total count, and the per-sport target table still sums to 1,211, with cycling and
swimming unallocated. All five pages remain `noindex,follow`; this batch stays in `bryme-media`
staging and has not been migrated to Nextclip.

## Drop 3 — ten more evergreen questions (2026-10-01)

Continuing the directive to cover **all** the evergreen football questions in detail, with each
page wired into the ones it depends on. Library now **37 explainers** (8 → 27 → 37).

| Theme | New questions | Count now |
| --- | --- | --- |
| Football laws | how a penalty kick works, what a yellow card costs, the backpass rule, throw-ins / goal kicks / corners | 12 |
| Knockout football | — | 5 |
| Governance & competitions | league vs cup, Champions League vs Europa vs Conference League | 6 |
| League rules | — | 4 |
| Match mechanics | how long a match is and why 90 minutes, how many players are on a team | 4 |
| Transfers & money | loan deals (option vs obligation) | 3 |
| Tactics & data | what formations mean — how to read 4-3-3, 4-2-3-1, 3-5-2 | 3 |

All ten pages run 798–972 words (floor 320), so the desk remains **zero thin**. The hub now reads
as a browsable library: seven themes, per-section counts, and every page linking onward —
penalties → shootouts → what counts as a foul; yellow cards → red cards → who writes the laws;
throw-ins → offside (no offside from a restart) → when a goal is a goal.

## Drop 4 — ten more evergreen questions (2026-10-01)

Continuing the directive: cover **all** the evergreen football questions in detail, each wired into
the ones it depends on. Library now **47 explainers** (8 → 27 → 37 → 47) across eight themes.

| Theme | New questions | Count now |
| --- | --- | --- |
| Football laws | the drop ball, professional fouls (denying an obvious goal-scoring opportunity), own goals | 14 |
| Match mechanics | pitch dimensions, what the coin toss decides, the drop ball | 7 |
| Governance & competitions | the Club World Cup, how clubs qualify for the Champions League | 8 |
| League rules | play-offs — promotion, relegation and last-resort deciders | 5 |
| Transfers & money | free agents, the Bosman ruling, release clauses | 4 |
| Football language | football terms explained — hat-trick, clean sheet, parking the bus, false nine | 1 |

All ten run 830–936 words (floor 320); the desk stays **zero thin**, and the migration gate reads
**sports READY 47/47**.

New connections in this drop: the drop ball → when a goal is a goal → stoppage time; professional
fouls → what counts as a foul → red cards → direct and indirect free kicks; own goals → offside →
restarts; pitch dimensions → formations → match length; free agents → transfer windows → loans →
financial fair play; play-offs → promotion and relegation → tied-on-points → knockout ties.

### Process note (worth keeping)

The first attempt at this commit shipped the new pages without the wiring: a blanket
`git restore .` — used to recover asset files the workspace snapshot drops between turns — also
silently reverted the manifest target and the generator's batch list, and CI caught it because
`validate-upgrade` read the old target against the new page count. Fixed in `90897f6`. From now on
dropped files are recovered with a targeted `git checkout HEAD -- <deleted paths>`; a blanket
restore is never safe once edits are in the tree.

## Drop 5 — football completes at 51, basketball opens (2026-10-01)

**47 → 59 explainers.** Football reaches its approved target, and the desk proves the page anatomy
transfers to a second sport.

**Football (+4, now 51):** referee signals and what each one means · what a captain actually does —
and does not have the power to do · how injuries and suspected concussions are handled, including
additional concussion substitutes · why teams have home, away and third kits.

**Basketball (+8, desk opened):** the shot clock (24s NBA/FIBA, 30s college, 14s reset after an
offensive rebound) · travelling and the gather step · the double dribble and carrying · fouls, the
bonus and free throws · the three-second rule, including the NBA-only defensive version · goaltending
and basket interference · overtime · technical and flagrant fouls.

**Structural, so the desk can keep growing:** every explainer now carries a `sport` field; the hub
groups **sport → theme**; the "keep reading" rail suggests the next questions from the same sport;
and the migration gate checks **per-sport targets** from the manifest rather than only the total, so
a new sport must reach its own approved number before the desk counts as FULL.

**Phase 2 candidates:** athletics (track & field), combat sports, tennis, cricket, American football,
rugby — same anatomy, one question per page, evergreen.

## Drop 2 — the football rules library (2026-10-01)

Owner directive: **add lots of evergreen sports content, and show how the ideas connect** — the
offside page must not stop at the definition, it has to cover how a player is offside and what
happens next. Football first, because it covers the most ground; other sports after it. And the
positioning is now explicit: **BRYME is not a livescore or a news desk — it breaks down the rules.**

**19 new explainers** (8 → 27), each one question, answered straight, then explained properly:

| Theme | Questions | Count |
| --- | --- | --- |
| Football laws | offside (rebuilt), handball, fouls, advantage, direct vs indirect free kicks, when a goal is a goal, VAR, red cards | 8 |
| Knockout football | aggregate score, away goals, how a tie is decided, extra time, shootouts | 5 |
| League rules | goal difference, teams level on points, points needed to stay up, promotion & relegation | 4 |
| Governance & competitions | what UEFA is, who writes the laws, why the World Cup is every four years, Champions League seeding | 4 |
| Tactics & data | the offside trap, xG | 2 |
| Transfers & money | transfer windows, financial fair play | 2 |
| Match mechanics | stoppage time, substitutions | 2 |

**The offside page was rebuilt to answer the whole question** — the three conditions, how a player
actually gets into an offside position, the moment of judgement, the three ways of "getting
involved", what happens next (indirect free kick from where the player stood, no card), the
deliberate-play vs deflection distinction, and the restart exceptions. It is now the deepest page
in the library at ~1,480 words, up from ~650.

**It is a network, not a list.** The hub groups all 27 by theme, and every page links to the
concepts it depends on: offside → the trap → VAR → when a goal is a goal; tied points → goal
difference → survival maths → relegation. Every one of those links is verified by the build, which
exits non-zero on a single unresolved internal link.

- Word counts: 648–1,485 per page (floor 320). Zero thin pages.
- The sports desk now reads **READY** on the migration gate (27/27, 0 thin, links clean); the
  entertainment desk is still short, so migration stays blocked overall.
- Scale limits now live in `content/niche-manifests.json` instead of hardcoded numbers: a desk may
  grow to its approved target, and the gate fails only if it goes beyond what was signed off.
- Authoring is split into batch files (`upgrade-sports.json`, `…-batch2a.json`, `…-batch2b.json`)
  so each drop stays reviewable; the generator merges them and rejects duplicate slugs.
- **Phase 2** (after football is full and approved): basketball, athletics, combat sports, tennis,
  cricket, American football — same page anatomy, one question per page.

## Landing & migration rule (owner directive, 2026-10-01) — supersedes the old "sample review" gate

**Work lands in bryme-media. A niche moves to nextclip (live) only when it is FULL and has NO
THIN pages.** Structural approval of a sample is necessary but no longer sufficient: the niche
must be genuinely complete, and every page that would migrate must clear its authored-copy
floor.

Operationalised as `npm run niche:status` (`scripts/audit-niche-readiness.js`), configured by
`content/niche-manifests.json`:

| Dimension | Measured as | Today (sample) |
| --- | --- | --- |
| FULL — entertainment | rec-list count at target + every referenced title upgraded + hubs fully linked | 4/12 lists (target proposed, owner to confirm); 5/19 referenced titles upgraded |
| FULL — sports | explainer count at target + concept network intact + index fully linked | 8/16 (target proposed, owner to confirm) |
| NO THIN | every rebuild-set page clears its floor (rec 350 / explainer 320 / title 280 words; single source of truth in the manifest) | 0 thin ✓ on both desks |
| LINKS | every root-relative link resolves | 0 issues ✓ |

Verdict today: **migration BLOCKED — both niches not yet full.** That is the expected state;
the gate exists to make the "full and no thin" condition measurable rather than a judgement
call. Migration also requires owner sign-off, an unfrozen live window (AdSense verdict), and
the nextclip-side pre-flight in the manifest's `migration_checklist`.

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

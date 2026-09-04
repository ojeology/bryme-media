# Thin-Content Upgrade — BRYME / nextclip

**Status:** Pushed to `ojeology/nextclip` `main` (commit `ac856b625e`).
**Canonical host:** `https://bryme.onrender.com` — deploy the latest push.

Worked on all four thin-content priorities. Everything builds only on **verified data
already in the repo** — nothing is fabricated.

---

## 1. Title pages (biggest thinness risk) ✅
~687 indexable movie/series/anime pages. Many were a one-line teaser + trailer + details.

- Every title page now renders an **"About" section**.
  - A long in-house synopsis is shown in full if one exists.
  - Otherwise a short **fact-derived "At a glance" paragraph** is built from verified
    metadata already in the repo (director, cast, year, genre, country, language,
    runtime). It never invents plot, opinion or ratings.
- **Result:** real indexable title pages median **235 words** (was 192). Pages ≥250 words:
  30 → **218**. **Zero genuinely thin indexable title pages remain** — the only pages under
  150 words are year-index aggregators, which are already `noindex` and out of the sitemap.

Example:
> *The Dark Knight is directed by Christopher Nolan and released in 2008. It comes from
> United States; United Kingdom. The cast includes Christian Bale, Michael Caine, Heath
> Ledger, Gary Oldman. The film runs about 153 minutes.*

## 2. Empty match pages (~1,718) ✅
They were already `noindex` (correctly out of the sitemap), but each rendered **16
repetitive "Pending verification" cards** — a template that read as unfinished and bloated
the HTML a crawler chews through.

- Replaced with **one honest panel** confirming the fixture facts BRYME knows (date,
  kickoff, venue) and stating verified analysis will be added.
- **"Pending verification" count across sports: 24,108 → 0.**
- Editorial match pages are **unchanged**; the sitemap still contains only the **30
  researched** matches, all verified to carry real content.

## 3. Editorial growth ✅
Added **4 high-value, catalogue-linked guides** (each links to real title pages):
- Movies Like Dune: Big-Scale Sci-Fi Epics
- Christopher Nolan Movies in Order
- The Alien Franchise in Order
- Movies Like Parasite

Articles: **18 → 22**. Sitemap URLs: **882 → 887**. The 20 other articles in `editorial.json`
are **empty draft shells** and were left unpublished (publishing them would add thin pages,
not fix them).

## 4. Year / genre aggregator pages ✅ (already handled)
Thin year-index pages (e.g. `series/1989`, `anime/2002`) are correctly **`noindex`** via the
build's `thinArchive` threshold (<3 titles) and are **excluded from the sitemap**. Only
populated years (44 movie years) are indexed. No change needed — verified.

---

## Net effect
- **Indexable thin pages: effectively zero.** Every indexed title page is now ≥150 words;
  thin aggregators and empty fixtures stay out of Google.
- **Internal link quality improved** — new articles and fact-prose link to real title pages.
- **Sitemap stays lean** (887) and only contains pages with genuine content.

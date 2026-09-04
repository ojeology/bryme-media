#!/usr/bin/env python3
"""
enrich-wikidata.py — fill verified title metadata from Wikidata.

WHY: every catalogue record ships with empty director / cast / runtime and, for
most legacy records, empty country / language. The title page template already
renders those fields, so filling them from a citable source immediately deepens
632 pages without inventing anything.

SOURCE: Wikidata, via a public SPARQL endpoint (QLever mirror, official
endpoint as fallback). Structured statements there
are released under CC0, so the facts can be reused; every enriched record keeps
the Wikidata QID and the English Wikipedia link so the page can say where the
facts came from.

SAFETY RULES (a wrong match is worse than no data):
  * the entity must be a film / TV series / anime-type entity
  * its publication year must match the catalogue year (±1) — the year is the
    anchor that separates "Parasite (2019)" from "Parasite (1982)"
  * when several entities share a title and year, the record is skipped as
    ambiguous rather than guessed
  * existing values are never overwritten — the overlay only fills blanks
  * anything unmatched is written to the report for human review

OUTPUT: content/title-metadata.json     (overlay keyed by catalogue id)
        reports/wikidata-enrichment.json (matched / unmatched / ambiguous)

USAGE:
  python3 scripts/enrich-wikidata.py              # enrich everything pending
  python3 scripts/enrich-wikidata.py --limit 100  # first 100 pending
  python3 scripts/enrich-wikidata.py --force      # re-fetch all
"""

import argparse
import json
import os
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOGUE = os.path.join(ROOT, "data", "movies.json")
OVERLAY = os.path.join(ROOT, "content", "title-metadata.json")
REPORT = os.path.join(ROOT, "reports", "wikidata-enrichment.json")

# QLever is a fast public Wikidata mirror that tolerates batch queries; the
# official endpoint is kept as a fallback (it rate-limits anonymous bulk use
# very aggressively).
ENDPOINTS = [
    "https://qlever.cs.uni-freiburg.de/api/wikidata",
    "https://query.wikidata.org/sparql",
]
UA = "BRYME-catalogue-enrichment/1.0 (static site title metadata; polite batch use)"

# Entity types accepted as a film / series / anime.
TYPES = " ".join([
    "wd:Q11424",      # film
    "wd:Q202866",     # animated film
    "wd:Q24869",      # feature film
    "wd:Q29168811",   # animated feature film
    "wd:Q506240",     # television film
    "wd:Q20650540",   # adult animation film
    "wd:Q5398426",    # television series
    "wd:Q63952888",   # anime television series
    "wd:Q1259759",    # miniseries
    "wd:Q117467246",  # animated television series
    "wd:Q581714",     # animated series
    "wd:Q220898",     # OVA
    "wd:Q11086742",   # anime
])

BATCH = 30
MAX_CAST = 6


def norm(text):
    t = unicodedata.normalize("NFD", str(text or ""))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def sparql(query, retries=3):
    """Try each endpoint in turn; cap backoff so one slow mirror cannot stall the run."""
    last = None
    for endpoint in ENDPOINTS:
        for attempt in range(retries):
            url = endpoint + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": UA,
                    "Accept": "application/sparql-results+json",
                })
                with urllib.request.urlopen(req, timeout=120) as r:
                    return json.load(r)["results"]["bindings"]
            except urllib.error.HTTPError as exc:
                last = exc
                if exc.code in (429, 500, 502, 503, 504):
                    wait = min(float(exc.headers.get("Retry-After") or 0) or (5 * (attempt + 1)), 45)
                    print(f"    · {endpoint.split('/')[2]} busy ({exc.code}), waiting {wait:.0f}s", flush=True)
                    time.sleep(wait)
                    continue
                break  # non-retryable on this endpoint — try the next one
            except Exception as exc:
                last = exc
                time.sleep(3 * (attempt + 1))
        print(f"    · falling back from {endpoint.split('/')[2]}", flush=True)
    raise RuntimeError(f"all SPARQL endpoints failed: {last}")


PREFIXES = """
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
"""


def facts_query(titles):
    values = " ".join('"%s"@en' % t.replace('\\', '\\\\').replace('"', '\\"') for t in titles)
    return PREFIXES + f"""
SELECT ?item ?itemLabel (?title AS ?matchedTitle) ?year ?startYear ?runtime ?enwiki
       (GROUP_CONCAT(DISTINCT ?dL; separator="; ") AS ?directors)
       (GROUP_CONCAT(DISTINCT ?coL; separator="; ") AS ?countries)
       (GROUP_CONCAT(DISTINCT ?laL; separator="; ") AS ?languages)
WHERE {{
  VALUES ?title {{ {values} }}
  {{ ?item rdfs:label ?title }} UNION {{ ?item skos:altLabel ?title }}
  ?item wdt:P31 ?type . VALUES ?type {{ {TYPES} }}
  ?item rdfs:label ?itemLabel . FILTER(LANG(?itemLabel)="en")
  OPTIONAL {{ ?item wdt:P577 ?pub . BIND(YEAR(?pub) AS ?year) }}
  OPTIONAL {{ ?item wdt:P580 ?start . BIND(YEAR(?start) AS ?startYear) }}
  OPTIONAL {{ ?item wdt:P2047 ?runtime }}
  OPTIONAL {{ ?item wdt:P57  ?d  . ?d  rdfs:label ?dL  . FILTER(LANG(?dL)="en") }}
  OPTIONAL {{ ?item wdt:P495 ?co . ?co rdfs:label ?coL . FILTER(LANG(?coL)="en") }}
  OPTIONAL {{ ?item wdt:P364 ?la . ?la rdfs:label ?laL . FILTER(LANG(?laL)="en") }}
  OPTIONAL {{ ?enwiki schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }}
}}
GROUP BY ?item ?itemLabel ?title ?year ?startYear ?runtime ?enwiki
"""


def cast_query(qids):
    values = " ".join("wd:" + q for q in qids)
    return PREFIXES + f"""
SELECT ?item ?castLabel ?ordinal WHERE {{
  VALUES ?item {{ {values} }}
  ?item p:P161 ?st .
  ?st ps:P161 ?cast .
  OPTIONAL {{ ?st pq:P1545 ?ordinal }}
  ?cast rdfs:label ?castLabel . FILTER(LANG(?castLabel)="en")
}}
"""


def qid_of(uri):
    return uri.rsplit("/", 1)[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--sleep", type=float, default=1.0, help="pause between batches")
    args = ap.parse_args()

    catalogue = json.load(open(CATALOGUE, encoding="utf-8"))
    overlay = json.load(open(OVERLAY, encoding="utf-8")) if os.path.exists(OVERLAY) else {}

    pending = [r for r in catalogue if args.force or r["id"] not in overlay]
    if args.limit:
        pending = pending[:args.limit]
    print(f"catalogue: {len(catalogue)} · enriched: {len(overlay)} · pending: {len(pending)}")

    unmatched, ambiguous = [], []
    staged = {}

    for start in range(0, len(pending), BATCH):
        chunk = pending[start:start + BATCH]
        titles = sorted({r["title"] for r in chunk if r.get("title")})
        print(f"  batch {start // BATCH + 1}/{(len(pending) + BATCH - 1) // BATCH} — {len(titles)} titles", flush=True)

        try:
            rows = sparql(facts_query(titles))
        except Exception as exc:
            print(f"    ! batch failed ({exc}); these titles stay pending")
            continue

        # Index rows by the entity label AND by every requested title the row
        # could satisfy (an alternate-label hit will not equal the main label).
        by_label = defaultdict(list)
        norm_titles = {norm(t): t for t in titles}
        for row in rows:
            label = row.get("itemLabel", {}).get("value", "")
            by_label[norm(label)].append(row)
        for row in rows:
            alt = row.get("matchedTitle", {}).get("value")
            if alt and norm(alt) in norm_titles:
                bucket = by_label[norm(alt)]
                if row not in bucket:
                    bucket.append(row)

        for rec in chunk:
            want_year = rec.get("year")
            cands = by_label.get(norm(rec.get("title")), [])
            if not cands:
                unmatched.append({"id": rec["id"], "title": rec.get("title"), "year": want_year, "reason": "no entity with this exact title"})
                continue

            def years_of(row):
                out = []
                for key in ("year", "startYear"):
                    v = row.get(key, {}).get("value")
                    try:
                        out.append(int(v))
                    except (TypeError, ValueError):
                        continue
                return out

            def year_of(row):
                ys = years_of(row)
                if not ys:
                    return None
                if want_year and want_year in ys:
                    return want_year
                return ys[0]

            exact = [r for r in cands if want_year and year_of(r) == want_year]
            near = [r for r in cands if want_year and year_of(r) is not None and abs(year_of(r) - want_year) <= 1]
            pool = exact or near
            if not pool:
                unmatched.append({"id": rec["id"], "title": rec.get("title"), "year": want_year, "reason": "no candidate with a matching year"})
                continue

            distinct = {qid_of(r["item"]["value"]) for r in pool}
            if len(distinct) > 1:
                ambiguous.append({"id": rec["id"], "title": rec.get("title"), "year": want_year,
                                  "candidates": sorted(distinct)})
                continue

            row = pool[0]
            qid = qid_of(row["item"]["value"])
            runtime = row.get("runtime", {}).get("value")
            try:
                runtime = int(round(float(runtime))) if runtime else None
            except (TypeError, ValueError):
                runtime = None

            staged[rec["id"]] = {
                "title": rec.get("title"),
                "year": want_year,
                "qid": qid,
                "director": row.get("directors", {}).get("value") or None,
                "country": row.get("countries", {}).get("value") or None,
                "language": row.get("languages", {}).get("value") or None,
                "runtime": f"{runtime} min" if runtime else None,
                "wikipedia": row.get("enwiki", {}).get("value") or None,
            }

        time.sleep(args.sleep)

    # ── cast, ordered by billing position where Wikidata records it ──────────
    qids = [v["qid"] for v in staged.values()]
    cast_by_qid = defaultdict(list)
    print(f"fetching cast for {len(qids)} titles…")
    for start in range(0, len(qids), BATCH):
        chunk = qids[start:start + BATCH]
        try:
            rows = sparql(cast_query(chunk))
        except Exception as exc:
            print(f"    ! cast batch failed ({exc})")
            continue
        for row in rows:
            q = qid_of(row["item"]["value"])
            name = row.get("castLabel", {}).get("value")
            ordinal = row.get("ordinal", {}).get("value")
            try:
                ordinal = int(ordinal)
            except (TypeError, ValueError):
                ordinal = 9999
            if name:
                cast_by_qid[q].append((ordinal, name))
        time.sleep(args.sleep)

    for rid, data in staged.items():
        names, seen = [], set()
        for _, name in sorted(cast_by_qid.get(data["qid"], []), key=lambda x: x[0]):
            if name not in seen:
                seen.add(name)
                names.append(name)
        overlay[rid] = {
            "title": data["title"],
            "year": data["year"],
            "director": data["director"],
            "cast": names[:MAX_CAST],
            "country": data["country"],
            "language": data["language"],
            "runtime": data["runtime"],
            "source": {
                "name": "Wikidata",
                "id": data["qid"],
                "url": f"https://www.wikidata.org/wiki/{data['qid']}",
                "wikipedia": data["wikipedia"],
                "retrieved": time.strftime("%Y-%m-%d"),
            },
        }

    os.makedirs(os.path.dirname(OVERLAY), exist_ok=True)
    with open(OVERLAY, "w", encoding="utf-8") as f:
        json.dump(overlay, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump({
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": "Wikidata SPARQL endpoint (CC0 structured data)",
            "catalogueSize": len(catalogue),
            "enrichedTotal": len(overlay),
            "matchedThisRun": len(staged),
            "unmatchedThisRun": len(unmatched),
            "ambiguousThisRun": len(ambiguous),
            "unmatched": unmatched,
            "ambiguous": ambiguous,
        }, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"\nmatched {len(staged)} · unmatched {len(unmatched)} · ambiguous {len(ambiguous)}")
    print(f"overlay now holds {len(overlay)} records → {OVERLAY}")
    print(f"report → {REPORT}")


if __name__ == "__main__":
    main()

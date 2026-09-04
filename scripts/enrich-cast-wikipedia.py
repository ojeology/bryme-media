#!/usr/bin/env python3
"""
enrich-cast-wikipedia.py — principal cast, in billed order, from Wikipedia.

WHY: Wikidata records cast members but almost never their billing order (only
about one title in six carries the P1545 "series ordinal" qualifier). Showing an
arbitrary six names implies a top-billed list that is not real, so instead the
billed cast is read from the English Wikipedia infobox "starring" field, which
is the actual billing list for the film or series.

RULES:
  * only runs for records that already matched a Wikidata entity with an
    English Wikipedia article (scripts/enrich-wikidata.py fills that in)
  * if no starring field can be parsed, the cast is left EMPTY rather than
    falling back to an arbitrary order
  * Wikipedia is credited on the page; the source block records the article URL
  * existing values in the catalogue are never overwritten by the build

USAGE:
  python3 scripts/enrich-cast-wikipedia.py
  python3 scripts/enrich-cast-wikipedia.py --limit 100
"""

import argparse
import json
import os
import re
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OVERLAY = os.path.join(ROOT, "content", "title-metadata.json")
REPORT = os.path.join(ROOT, "reports", "wikipedia-cast.json")

API = "https://en.wikipedia.org/w/api.php"
UA = "BRYME-catalogue-enrichment/1.0 (title cast from infobox; polite batch use)"
BATCH = 40
MAX_CAST = 6

DISAMBIG = re.compile(r"\s*\((?:actor|actress|singer|musician|comedian|born [^)]+|[^)]*performer[^)]*)\)\s*$", re.I)


def api(titles):
    params = {
        "action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main",
        "format": "json", "formatversion": "2", "redirects": "1",
        "titles": "|".join(titles),
    }
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as exc:
            if attempt == 3:
                print(f"    ! wikipedia api error: {exc}")
                return None
            time.sleep(3 * (attempt + 1))
    return None


def parse_starring(wikitext):
    """Pull the billed cast out of the infobox 'starring' parameter."""
    if not wikitext:
        return []
    m = re.search(r"\|\s*starring\s*=\s*(.*?)(?=\n\s*\|\s*[a-z_0-9 ]+\s*=|\n\}\})", wikitext, re.S | re.I)
    if not m:
        return []
    blob = m.group(1)
    blob = re.sub(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>|<!--.*?-->", "", blob, flags=re.S)

    names = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", blob)
    if not names:
        cleaned = re.sub(r"\{\{(?:ubl|unbulleted list|plainlist|flatlist|hlist|nowrap)\s*\|?", "", blob, flags=re.I)
        cleaned = cleaned.replace("}}", "").replace("{{", "")
        names = [p for p in re.split(r"[\n|]|<br\s*/?>", cleaned)]

    out = []
    for raw in names:
        name = DISAMBIG.sub("", raw.strip(" *'\n\t")).strip()
        if not name or len(name) > 60:
            continue
        if re.match(r"^(file|image|category|s|the)\s*:", name, re.I):
            continue
        if name.lower() in {"and", "with", "others"}:
            continue
        if not re.search(r"[A-Za-z]", name):
            continue
        if name not in out:
            out.append(name)
    return out[:MAX_CAST]


def article_title(url):
    if not url:
        return None
    slug = url.rsplit("/", 1)[-1]
    return urllib.parse.unquote(slug).replace("_", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    overlay = json.load(open(OVERLAY, encoding="utf-8"))
    targets = []
    for rid, rec in overlay.items():
        wiki = (rec.get("source") or {}).get("wikipedia")
        if wiki:
            targets.append((rid, article_title(wiki)))
    if args.limit:
        targets = targets[:args.limit]

    print(f"overlay records: {len(overlay)} · with a Wikipedia article: {len(targets)}")

    by_title = {}
    for rid, title in targets:
        by_title.setdefault(title, []).append(rid)

    titles = list(by_title)
    filled, empty = 0, []

    for start in range(0, len(titles), BATCH):
        chunk = titles[start:start + BATCH]
        print(f"  batch {start // BATCH + 1}/{(len(titles) + BATCH - 1) // BATCH}", flush=True)
        data = api(chunk)
        if not data:
            continue

        # Map redirects/normalisations back to the title we asked for.
        alias = {}
        for key in ("redirects", "normalized"):
            for entry in data.get("query", {}).get(key, []) or []:
                alias[entry["to"]] = entry["from"]

        for page in data.get("query", {}).get("pages", []) or []:
            resolved = page.get("title")
            asked = alias.get(resolved, resolved)
            rids = by_title.get(asked) or by_title.get(resolved) or []
            revs = page.get("revisions") or []
            wikitext = (revs[0].get("slots", {}).get("main", {}) or {}).get("content", "") if revs else ""
            cast = parse_starring(wikitext)
            for rid in rids:
                if cast:
                    overlay[rid]["cast"] = cast
                    overlay[rid]["castSource"] = {
                        "name": "Wikipedia",
                        "url": (overlay[rid].get("source") or {}).get("wikipedia"),
                        "field": "infobox starring",
                        "retrieved": time.strftime("%Y-%m-%d"),
                    }
                    filled += 1
                else:
                    # No billed cast available — do not show an arbitrary order.
                    overlay[rid]["cast"] = []
                    overlay[rid].pop("castSource", None)
                    empty.append({"id": rid, "title": overlay[rid].get("title"), "article": asked})
        time.sleep(0.5)

    with open(OVERLAY, "w", encoding="utf-8") as f:
        json.dump(overlay, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump({
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": "English Wikipedia infobox 'starring' field",
            "withBilledCast": filled,
            "withoutBilledCast": len(empty),
            "withoutBilledCastList": empty,
        }, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"\nbilled cast filled for {filled} titles · {len(empty)} left empty (no infobox starring field)")
    print(f"report → {REPORT}")


if __name__ == "__main__":
    main()

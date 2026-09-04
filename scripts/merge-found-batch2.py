#!/usr/bin/env python3
"""Merge Wikipedia batch-2 credits + original synopses into found-movies.json."""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKIP = {"goat-2026", "jackass-best-and-last", "the-last-house"}

SYN = {
    "avatar-fire-and-ash": "The third Avatar film. Jake and Neytiri take the family into fire-clan country after the way of water. James Cameron is still in the chair; Sam Worthington and Zoe Saldaña return.",
    "backrooms": "A Kane Parsons feature built from the internet’s yellow-room creepypasta. Chiwetel Ejiofor and Renate Reinsve are the billed leads. Not a found-footage YouTube compilation.",
    "bad-newz": "A messy love triangle sold as a comedy. Vicky Kaushal, Triptii Dimri and Ammy Virk. Anand Tiwari’s 2024 Hindi film, not a news satire.",
    "bhool-bhulaiyaa-3": "Kartik Aaryan walks into another haunted palace; Vidya Balan and Madhuri Dixit are already inside the joke. Anees Bazmee’s third Bhool Bhulaiyaa, still a horror-comedy.",
    "camp-rock-3": "Disney’s camp musical comes back with a new set of kids. Liamani, Malachi Barton and Lumi Pollack are the billed names. A sequel, not a reunion of the first two films’ whole cast.",
    "chainsaw-man-reze": "The Reze Arc, as a movie. Tatsuya Yoshihara directs; Kikunosuke Toya returns as Denji. A theatrical Chainsaw Man chapter, not a recap of the TV season.",
    "citizen-vigilante": "Uwe Boll’s late-period action film with Armie Hammer. A man takes the law personally. BRYME lists the billed names and the trailer — not a review of Boll’s catalogue.",
    "freakier-friday": "Lindsay Lohan is back in the body-swap comedy, this time with a next generation in the mix. Nisha Ganatra directs. A sequel to Freaky Friday, not a remake of the 2003 film.",
    "devara-part-1": "N. T. Rama Rao Jr. in a coastal-action saga from Koratala Siva. Saif Ali Khan and Janhvi Kapoor are billed opposite him. Part 1 of a two-film story.",
    "greenland-2": "The family that survived the comet now has to move. Gerard Butler returns in Ric Roman Waugh’s sequel to Greenland. A disaster chase, not a documentary.",
    "disclosure-day": "Steven Spielberg’s UFO film. Emily Blunt and Josh O’Connor are the billed leads. A first-contact story from a director who has done this neighbourhood before.",
    "hoppers": "Pixar-adjacent creature comedy from Daniel Chong. Piper Curda, Bobby Moynihan and Jon Hamm are the billed voices. Animals with jobs; not a Zootopia clone by default.",
    "dhurandhar": "Aditya Dhar’s spy-action film with Ranveer Singh. Akshaye Khanna and Arjun Rampal are billed in the opposition. A Hindi espionage picture, not a biopic claim.",
    "colony-2026": "Yeon Sang-ho’s sci-fi with Jun Ji-hyun, Koo Kyo-hwan and Ji Chang-wook. A future colony under pressure. From the director of Train to Busan, not a sequel to that film.",
    "moana-2026": "Disney’s live-action Moana. Thomas Kail directs; the billed cast includes Rena Owen, John Tui and Frankie Adams. A new telling of the 2016 animation, not a shot-for-shot copy claim.",
    "mutiny-2026": "Jean-François Richet’s shipboard thriller. Annabelle Wallis, Roland Møller and Adrian Lester are billed. A mutiny story, not a franchise reboot.",
    "munjya": "A Konkan wedding, a family curse, and a spirit who will not stay in the tree. Aditya Sarpotdar’s horror-comedy with Abhay Verma and Sharvari. Hindi, 2024.",
    "minions-monsters": "Pierre Coffin’s next Minions outing. Trey Parker, Allison Janney and Christoph Waltz are among the billed voices. Illumination slapstick, not a Despicable Me recap.",
    "obsession-2026": "Curry Barker’s obsession thriller. Michael Johnston and Inde Navarrette are billed. A small-cast spiral, not a remake of the 1976 De Palma film.",
    "supergirl-2026": "Milly Alcock as Kara in James Gunn’s DCU. Craig Gillespie directs; Matthias Schoenaerts is billed opposite her. A new Supergirl, not a continuation of the CW show.",
    "project-hail-mary": "Phil Lord and Christopher Miller adapt Andy Weir. A lone scientist and a problem that will not wait. Sandra Hüller is among the billed names. Not a The Martian sequel.",
    "swapped": "Nathan Greno’s body-swap comedy. Michael B. Jordan, Juno Temple and Tracy Morgan are billed. A high-concept switch, not a Freaky Friday remake.",
    "scream-7": "Ghostface again. Neve Campbell returns; Kevin Williamson is billed as director. Isabel May and Jasmin Savoy Brown join. A new Scream, not a reboot of the 1996 film from zero.",
    "singham-again": "Rohit Shetty’s cop-universe pile-up. Kareena Kapoor Khan, Arjun Kapoor and Jackie Shroff are billed alongside the Singham brand. A masala ensemble, not a single-hero origin.",
    "scary-movie-2026": "The Wayans-era names come back: Anna Faris, Regina Hall, Marlon Wayans. Michael Tiddes directs. A new Scary Movie, not a recut of the 2000 film.",
    "shelter-2026": "Ric Roman Waugh’s survival picture. Naomi Ackie and Daniel Mays are billed. A family under a sky that has gone wrong. Not a remake of the 2010 Julianne Moore Shelter.",
    "vikram": "Lokesh Kanagaraj’s Tamil action film. Kamal Haasan’s title role sits opposite Vijay Sethupathi and Fahadh Faasil. A 2022 hit, not a remake of the 1986 Vikram.",
    "the-gorge": "Two snipers watch a valley they are not allowed to explain. Scott Derrickson directs Miles Teller and Anya Taylor-Joy. A 2025 thriller, not a war documentary.",
    "the-super-mario-galaxy-movie": "Aaron Horvath and Michael Jelenic send Mario off-world. Chris Pratt, Anya Taylor-Joy and Charlie Day are billed again. A sequel to The Super Mario Bros. Movie.",
    "the-devil-wears-prada-2": "Miranda Priestly is not done. David Frankel returns with Meryl Streep, Anne Hathaway and Emily Blunt. A sequel to the 2006 fashion-desk film.",
    "the-devils-mouth": "Jeff Wadlow’s young-adult horror. Kathryn Newton, Lana Condor and Gavin Casalegno are billed. A town with a hole it should have left closed.",
    "the-shadows-edge": "Jackie Chan in a contemporary action film from Larry Yang. Zhang Zifeng and Tony Leung Ka-fai are billed. A 2025 crime-action picture, not a period kung-fu remake.",
    "yodha": "Siddharth Malhotra in an airborne action film. Raashii Khanna and Disha Patani are billed. A 2024 Hindi thriller set around a hijack, not a mythological epic.",
    "insidious-out-of-further": "The sixth Insidious film. Jacob Chase directs; Amelia Eve, Brandon Perea and Maisie Richardson-Sellers lead, with Lin Shaye back. A 2026 continuation, not a remake of the 2010 original.",
}

REL = {
    "avatar-fire-and-ash": ["avatar-the-way-of-water", "dune-part-two", "the-abyss"],
    "backrooms": ["a-quiet-place", "the-substance", "insidious"],
    "bad-newz": ["jawan", "stree-2", "animal"],
    "bhool-bhulaiyaa-3": ["stree-2", "stree", "jawan"],
    "camp-rock-3": ["coco", "inside-out-2", "the-wild-robot"],
    "chainsaw-man-reze": ["demon-slayer", "jujutsu-kaisen", "chainsaw-man"],
    "citizen-vigilante": ["taken", "john-wick", "the-batman"],
    "freakier-friday": ["inside-out-2", "coco", "zootopia"],
    "devara-part-1": ["rrr", "pushpa", "kalki-2898-ad"],
    "greenland-2": ["a-quiet-place", "war-of-the-worlds", "twisters"],
    "disclosure-day": ["arrival", "close-encounters", "dune-part-two"],
    "hoppers": ["zootopia", "zootopia-2", "the-wild-robot", "inside-out-2"],
    "dhurandhar": ["jawan", "pathaan", "animal"],
    "colony-2026": ["train-to-busan", "alien", "a-quiet-place"],
    "moana-2026": ["moana", "coco", "the-wild-robot"],
    "mutiny-2026": ["master-and-commander", "gladiator-ii", "1917"],
    "munjya": ["stree-2", "stree", "bhool-bhulaiyaa-3"],
    "minions-monsters": ["despicable-me-3", "inside-out-2", "the-super-mario-bros-movie"],
    "obsession-2026": ["the-substance", "gone-girl", "the-housemaid-2025"],
    "supergirl-2026": ["superman-2025", "wonder-woman", "the-batman"],
    "project-hail-mary": ["the-martian", "interstellar", "arrival"],
    "swapped": ["freakier-friday", "inside-out-2", "coco"],
    "scream-7": ["scream", "insidious", "a-quiet-place"],
    "singham-again": ["jawan", "rrr", "pushpa"],
    "scary-movie-2026": ["scream", "insidious", "zombieland"],
    "shelter-2026": ["greenland-2", "a-quiet-place", "twisters"],
    "vikram": ["rrr", "pushpa", "jawan", "kalki-2898-ad"],
    "the-gorge": ["civil-war", "a-quiet-place", "the-substance"],
    "the-super-mario-galaxy-movie": ["the-super-mario-bros-movie", "inside-out-2", "coco"],
    "the-devil-wears-prada-2": ["the-notebook", "la-la-land", "barbie"],
    "the-devils-mouth": ["insidious", "the-substance", "scream"],
    "the-shadows-edge": ["john-wick", "the-batman", "rrr"],
    "yodha": ["jawan", "pathaan", "rrr"],
    "insidious-out-of-further": ["insidious", "a-quiet-place", "the-conjuring"],
}

GENRE = {
    "avatar-fire-and-ash": ("Sci-Fi", ["Sci-Fi", "Adventure"]),
    "backrooms": ("Horror", ["Horror", "Sci-Fi"]),
    "bad-newz": ("Comedy", ["Comedy", "Romance"]),
    "bhool-bhulaiyaa-3": ("Horror", ["Horror", "Comedy"]),
    "camp-rock-3": ("Music", ["Music", "Family"]),
    "chainsaw-man-reze": ("Anime", ["Anime", "Action"]),
    "citizen-vigilante": ("Action", ["Action", "Thriller"]),
    "freakier-friday": ("Comedy", ["Comedy", "Family"]),
    "devara-part-1": ("Action", ["Action", "Drama"]),
    "greenland-2": ("Action", ["Action", "Thriller"]),
    "disclosure-day": ("Sci-Fi", ["Sci-Fi", "Drama"]),
    "hoppers": ("Animation", ["Animation", "Comedy"]),
    "dhurandhar": ("Action", ["Action", "Thriller"]),
    "colony-2026": ("Sci-Fi", ["Sci-Fi", "Thriller"]),
    "moana-2026": ("Adventure", ["Adventure", "Family"]),
    "mutiny-2026": ("Thriller", ["Thriller", "Action"]),
    "munjya": ("Horror", ["Horror", "Comedy"]),
    "minions-monsters": ("Animation", ["Animation", "Comedy"]),
    "obsession-2026": ("Thriller", ["Thriller", "Drama"]),
    "supergirl-2026": ("Superhero", ["Superhero", "Action"]),
    "project-hail-mary": ("Sci-Fi", ["Sci-Fi", "Adventure"]),
    "swapped": ("Comedy", ["Comedy", "Fantasy"]),
    "scream-7": ("Horror", ["Horror", "Mystery"]),
    "singham-again": ("Action", ["Action", "Crime"]),
    "scary-movie-2026": ("Comedy", ["Comedy", "Horror"]),
    "shelter-2026": ("Thriller", ["Thriller", "Drama"]),
    "vikram": ("Action", ["Action", "Crime"]),
    "the-gorge": ("Thriller", ["Thriller", "Sci-Fi"]),
    "the-super-mario-galaxy-movie": ("Animation", ["Animation", "Adventure"]),
    "the-devil-wears-prada-2": ("Comedy", ["Comedy", "Drama"]),
    "the-devils-mouth": ("Horror", ["Horror"]),
    "the-shadows-edge": ("Action", ["Action", "Crime"]),
    "yodha": ("Action", ["Action", "Thriller"]),
    "insidious-out-of-further": ("Horror", ["Horror"]),
}

STUDIO = {
    "avatar-fire-and-ash": "20th Century Studios",
    "moana-2026": "Walt Disney Pictures",
    "hoppers": "Pixar",
    "minions-monsters": "Illumination",
    "supergirl-2026": "DC / Warner Bros.",
    "the-super-mario-galaxy-movie": "Illumination / Nintendo",
}


def clean_name(n):
    n = re.sub(r"\s*\((?:director|screenwriter|actor|actress)\)\s*$", "", n).strip()
    n = n.replace("Phil Lord and Christopher Miller", "Phil Lord")
    return n


def clean_list(xs):
    out = []
    for x in xs or []:
        x = clean_name(x)
        if x == "Phil Lord" and "Christopher Miller" not in out:
            out.extend(["Phil Lord", "Christopher Miller"])
            continue
        if x and x not in out:
            out.append(x)
    return out


def main():
    wiki = json.load(open("/tmp/wiki-batch2.json"))
    found_path = os.path.join(ROOT, "content", "found-movies.json")
    found = json.load(open(found_path))
    have = {t["slug"] for t in found["titles"]}
    have_cast = {t["slug"] for t in found["catalogueCast"]}

    # manual Insidious 2026
    wiki["insidious-out-of-further"] = {
        "slug": "insidious-out-of-further",
        "kind": "extra",
        "ok": True,
        "article": "Insidious: Out of the Further",
        "wikipedia": "https://en.wikipedia.org/wiki/Insidious:_Out_of_the_Further",
        "director": ["Jacob Chase"],
        "cast": ["Amelia Eve", "Brandon Perea", "Maisie Richardson-Sellers", "Lin Shaye"],
        "runtime": "",
        "country": ["United States"],
        "language": ["English"],
        "_h1": "Insidious: Out of the Further",
        "_year": 2026,
        "_yt": "jxU8FU3o75A",
    }

    added = 0
    for slug, rec in wiki.items():
        if slug in SKIP or not rec.get("ok") or rec.get("kind") != "extra":
            continue
        if slug in have:
            continue
        if slug not in SYN:
            print("no synopsis, skip", slug)
            continue
        yt = rec.get("_yt")
        if not yt:
            print("no trailer id, skip", slug)
            continue
        g, gs = GENRE.get(slug, ("Film", ["Film"]))
        dirs = clean_list(rec.get("director"))
        cast = clean_list(rec.get("cast"))
        title = rec.get("_h1") or rec.get("article") or slug
        title = title.replace("&amp;", "&").replace("&#39;", "'")
        found["titles"].append(
            {
                "slug": slug,
                "title": title,
                "year": rec.get("_year") or rec.get("year") or 0,
                "genre": g,
                "genres": gs,
                "director": "; ".join(dirs),
                "cast": cast,
                "runtime": rec.get("runtime") or "",
                "country": (rec.get("country") or ["United States"])[0] if rec.get("country") else "",
                "language": (rec.get("language") or ["English"])[0] if rec.get("language") else "English",
                "youtubeId": yt,
                "wikipedia": rec.get("wikipedia"),
                "studio": STUDIO.get(slug),
                "description": SYN[slug],
                "related": REL.get(slug) or [],
            }
        )
        added += 1
        print("extra", slug)

    # catalogue cast
    extra_cast_fix = {
        "alien-resurrection": ["Sigourney Weaver"],
    }
    for slug, rec in wiki.items():
        if not rec.get("ok") or rec.get("kind") != "cast":
            continue
        if slug in have_cast:
            continue
        dirs = clean_list(rec.get("director"))
        cast = extra_cast_fix.get(slug, []) + clean_list(rec.get("cast"))
        # dedupe
        seen = set()
        cast2 = []
        for n in cast:
            if n not in seen:
                seen.add(n)
                cast2.append(n)
        found["catalogueCast"].append(
            {
                "slug": slug,
                "director": "; ".join(dirs),
                "cast": cast2[:8],
                "runtime": rec.get("runtime") or "",
                "wikipedia": rec.get("wikipedia"),
            }
        )
        print("cast", slug, cast2[:4])

    json.dump(found, open(found_path, "w"), ensure_ascii=False, indent=2)
    print("wrote found-movies.json extras", len(found["titles"]), "cast", len(found["catalogueCast"]))


if __name__ == "__main__":
    main()

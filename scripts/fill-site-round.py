#!/usr/bin/env python3
"""Site-wide fill: remaining tech stubs, honest money hubs, Signal + Notion."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://bryme.onrender.com"
CHECKED = "2026-08-23"
AUTHOR = "Ibrahim Sodiq"
AUTHOR_URL = "/author/ibrahim-sodiq/"

HERO_PRIV = "/assets/img/tech/hero-privacy.jpg"
HERO_AI = "/assets/img/tech/hero-assistants.jpg"
HERO_TOOLS = "/assets/img/tech/hero-tools.jpg"
HERO_PHONE = "/assets/img/tech/hero-phone-code.jpg"
HERO_HOST = "/assets/img/tech/hero-hosting.jpg"
HERO_DEP = "/assets/img/tech/hero-deploy.jpg"
HERO_ALT = "/assets/img/tech/hero-alternatives.jpg"
HERO_WRITE = "/assets/img/money/hero-writing.jpg"
HERO_BEG = "/assets/img/money/hero-beginner.jpg"
HERO_FEE = "/assets/img/money/hero-fees.jpg"
HERO_REM = "/assets/img/money/hero-remote.jpg"

def esc(s: str) -> str:
    return html.escape(s, quote=True)

def paras(text: str) -> str:
    return "".join(f"<p>{esc(c.strip())}</p>" for c in text.split("\n\n") if c.strip())

def desc_meta(excerpt: str, limit: int = 155) -> str:
    excerpt = " ".join(excerpt.split())
    if len(excerpt) <= limit:
        return excerpt
    return excerpt[:limit].rsplit(" ", 1)[0].rstrip(".,;:") + "…"

def chrome(nav: str) -> tuple[str, str, str]:
    active_m = ' class="active"' if nav == "make-money" else ""
    active_t = ' class="active"' if nav == "tech" else ""
    head = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#08090b"><meta name="color-scheme" content="dark light"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="icon" href="/assets/favicon.png" type="image/png" sizes="32x32"><link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png"><link rel="manifest" href="/manifest.webmanifest"><link rel="preconnect" href="https://i.ytimg.com" crossorigin><link rel="preconnect" href="https://www.youtube-nocookie.com" crossorigin><link rel="preconnect" href="https://www.youtube.com" crossorigin>"""
    header = f"""</head><body data-nav="{nav}"><header class="top"><div class="shell"><a class="brand" href="/">BRY<b>ME</b></a><nav class="topnav"><a href="/">Home</a><a href="/entertainment/">🎬 Entertainment</a><a href="/sports/">⚽ Sports</a><a href="/make-money/"{active_m}>💰 Make Money</a><a href="/tech/"{active_t}>🤖 Tech &amp; AI</a><a class="nav-search" href="/search/">Search</a></nav><div class="top-tools"><a class="header-search" href="/search/" aria-label="Search">Search</a></div></div></header>"""
    footer = """<nav class="mobile-nav"><a href="/"><span class="mn-ico">🏠</span>Home</a><a href="/entertainment/"><span class="mn-ico">🎬</span>Entertain</a><a href="/sports/"><span class="mn-ico">⚽</span>Sports</a><a href="/make-money/"%s><span class="mn-ico">💰</span>Money</a><a href="/tech/"%s><span class="mn-ico">🤖</span>Tech</a><a href="/search/"><span class="mn-ico">🔍</span>Search</a></nav><footer class="footer"><div class="shell"><div class="footer-grid">
  <div class="footer-brand"><a class="brand" href="/">BRY<b>ME</b></a><p>Discover what you love. Learn what you need. Find what's next.</p></div>
  <nav class="footer-col" aria-label="Explore"><h3>Verticals</h3><a href="/entertainment/">🎬 Entertainment</a><a href="/sports/">⚽ Sports</a><a href="/make-money/">💰 Make Money</a><a href="/tech/">🤖 Tech &amp; AI</a></nav>
  <nav class="footer-col" aria-label="Explore"><h3>Entertainment</h3><a href="/trending/">What's Trending</a><a href="/movies/">Movies</a><a href="/series/">Series</a><a href="/anime/">Anime</a><a href="/articles/">Articles</a><a href="/genres/">Genres</a></nav>
  <nav class="footer-col" aria-label="Information"><h3>Information</h3><a href="/about/">About</a><a href="/contact/">Contact</a><a href="/editorial-policy/">Editorial Policy</a></nav>
  <nav class="footer-col" aria-label="Legal"><h3>Legal</h3><a href="/privacy/">Privacy Policy</a><a href="/terms/">Terms of Use</a><a href="/disclaimer/">Disclaimer</a><a href="/copyright/">Copyright / DMCA</a></nav>
</div>
<p class="footer-note">BRYME · Discover what you love. Learn what you need. Find what's next. Trailer links lead to YouTube and viewing links lead to third parties.<small>Trending Now is editorially curated by BRYME — it is not live traffic data. Popular and Editor's Picks are independent rankings. Real user analytics will replace trending once the site has enough traffic. · Build 2026-08-23 08:25 UTC</small></div></footer><script>window.BRYME_BASE=''</script><script src="/assets/site-app.js"></script></body></html>""" % (
        ' class="active"' if nav == "make-money" else "",
        ' class="active"' if nav == "tech" else "",
    )
    return head, header, footer

def card(href, title, excerpt, hero):
    return f'<a class="vcat vcat-photo" href="{href}" style="--card-img:url(\'{hero}\')"><b>{esc(title)}</b><span>{esc(excerpt)}</span></a>'

ARTICLES = [
    {
        "id": "signal-vs-whatsapp",
        "slug": "signal-vs-whatsapp",
        "title": "Signal vs WhatsApp: Free, and What That Word Means",
        "seoTitle": "Signal vs WhatsApp: Free, No Ads, No Tracking",
        "excerpt": "Signal’s official support page: free, no ads, no affiliate marketers, no tracking. WhatsApp is also free to message. Those are not the same product. I opened Signal’s own cost page on 23 August 2026.",
        "category": "Android Apps",
        "categorySlug": "android-apps",
        "nav": "tech",
        "tags": ["signal", "whatsapp", "privacy", "android"],
        "readingTime": "6 min read",
        "hero": HERO_PRIV,
        "content": [
            {
                "heading": "Both are free. Only one writes the sentence.",
                "body": "People ask for a WhatsApp alternative the way they ask for a Spotify alternative: they want the same job without the company attached.\n\nSignal’s official cost page, today: “Signal is free to use and there are no ads, no affiliate marketers, and no tracking in Signal.” It is an independent nonprofit, funded by grants and donations. Registration needs an SMS or call. After that it uses mobile data or Wi‑Fi, which your carrier may charge for. Signal does not charge for the app.\n\nWhatsApp is also free to install and message. I am not going to invent a WhatsApp subscription. Meta’s business is not “charge you ₦500 a month for chat.” The comparison is who sees the graph of who you talk to, and whether the app is funded by ads. Signal puts that in writing. I am not going to paraphrase WhatsApp’s privacy policy from memory.",
            },
            {
                "heading": "What Signal is not",
                "body": "It is not a drop-in status-and-channels clone. If your family lives in WhatsApp groups, broadcast lists and business catalogues, Signal will feel empty until they move. Official support even has a page titled “Does my contact need Signal?” — both sides need the app.\n\nIt is not a second phone number product. You register with a number. Your carrier may bill the registration SMS.\n\nIt is not a money app. There is no official “Signal pays you” angle. This is a tech page, not a Make Money listing.",
            },
            {
                "heading": "How I would choose, labelled as opinion",
                "body": "If I need one private thread with a person who will install another app, I would use Signal.\n\nIf the group is already on WhatsApp and will not move, I would stay there and stop pretending a blog post migrates a family.\n\nI would not install a “WhatsApp Plus” APK. That is how you donate the chat.\n\nI have not audited Signal’s protocol for this page. “No tracking” is their published claim. Open their cost page if that sentence is why you are switching.",
            },
        ],
        "sources": [
            {"name": "Signal Support — Cost to use Signal", "url": "https://support.signal.org/hc/en-us/articles/5286774014362-Cost-to-use-Signal"},
            {"name": "Signal — Speak Freely", "url": "https://signal.org/"},
        ],
    },
    {
        "id": "notion-free-plan",
        "slug": "notion-free-plan",
        "title": "Notion’s Free Plan: $0, 5MB Files, 7-Day History",
        "seoTitle": "Notion Free Plan: $0, 5MB Files, 7-Day History",
        "excerpt": "Notion’s official pricing page: Free is $0 per member. Unlimited pages for one person. File uploads cap at 5MB. Page history is 7 days. Plus is $10. Business is $20. That is the cheap notes alternative I could source.",
        "category": "Productivity",
        "categorySlug": "productivity",
        "nav": "tech",
        "tags": ["notion", "notes", "productivity", "alternatives"],
        "readingTime": "7 min read",
        "hero": HERO_TOOLS,
        "content": [
            {
                "heading": "Free is real. Unlimited is not.",
                "body": "Notion sells itself as the one tool to run a company. The useful question for this site is the free row.\n\nOfficial pricing page, 23 August 2026: Free is $0 per member per month, for individuals to organise personal projects. Included: a trial of Notion AI, basic forms, basic sites, Notion Calendar, databases.\n\nThe comparison table is the part listicles skip. Pages and blocks: unlimited for individuals, limited once two or more members share the workspace. File uploads on Free: up to 5MB each. Page history: 7 days. External guests: 10. Offline: you choose pages to download.\n\nPlus is $10 per member per month: unlimited collaborative blocks, unlimited file uploads, 30-day history, unlimited guests, custom sites, unlimited charts, basic connections.\n\nBusiness is $20 per member: Notion Agent, AI meeting notes, SSO, private teamspaces, premium connections.\n\nEnterprise is custom. Custom Agents: free to try, then $10 per 1,000 monthly Notion credits.",
            },
            {
                "heading": "What you are not buying",
                "body": "Free Notion is not a second brain with infinite attachments. A 6MB PDF will not go up. A page you edited eight days ago will not roll back on Free.\n\nIt is also not “ChatGPT in a wiki.” AI is a trial on Free and Plus. The $20 Business plan is where Notion Agent is listed as included.\n\nGoogle Docs remains free with a Google account and a different job: documents, not databases. I am not ranking them. I am saying Notion’s free row has printed limits.",
            },
            {
                "heading": "How I would choose, labelled as opinion",
                "body": "If I want a personal wiki of text pages, Free is enough.\n\nIf two people need to share a living workspace, I would read the “limited for 2+ members” line before I invited anyone. That is the upsell.\n\nIf I only need a to-do list, I would not open another SaaS account.\n\nI have not paid for Notion Plus. I am quoting their pricing table, not a month of invoices.",
            },
        ],
        "sources": [
            {"name": "Notion — Pricing (Free $0, Plus $10, Business $20)", "url": "https://www.notion.com/pricing"},
        ],
    },
]

def article_html(art):
    head, header, footer = chrome(art["nav"])
    url = f"{SITE}/tech/{art['slug']}/"
    page_title = f"{art['seoTitle']} | BRYME"
    desc = desc_meta(art["excerpt"])
    hero = art["hero"]
    body = "".join(f"<h2>{esc(b['heading'])}</h2>{paras(b['body'])}" for b in art["content"])
    sources = " · ".join(f'<a href="{esc(s["url"])}" rel="nofollow noopener">{esc(s["name"])}</a>' for s in art["sources"])
    more = "".join(
        card(f"/tech/{a['slug']}/", a["title"], a["excerpt"], a["hero"])
        for a in ARTICLES if a["slug"] != art["slug"]
    )
    more += card("/tech/bitwarden-free-password-manager/", "Bitwarden’s free plan", "Unlimited devices and passwords, officially.", HERO_PRIV)
    more += card("/tech/app-alternatives/", "App alternatives we checked", "Only comparisons that survived a source check.", HERO_ALT)
    ld = [
        {"@context": "https://schema.org", "@type": "Article", "headline": art["title"],
         "description": art["excerpt"], "datePublished": CHECKED, "dateModified": CHECKED,
         "author": {"@type": "Person", "name": AUTHOR, "url": SITE + AUTHOR_URL,
                    "jobTitle": "Writer — Make Money, Tech & AI, Sports"},
         "publisher": {"@type": "Organization", "name": "BRYME"},
         "mainEntityOfPage": url, "articleSection": art["category"], "image": SITE + hero},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "BRYME Tech & AI", "item": SITE + "/tech/"},
            {"@type": "ListItem", "position": 3, "name": art["category"], "item": f"{SITE}/tech/{art['categorySlug']}/"},
            {"@type": "ListItem", "position": 4, "name": art["title"], "item": url},
        ]},
    ]
    return (
        head + f"<title>{esc(page_title)}</title>"
        + f'<meta name="description" content="{esc(desc)}"><link rel="canonical" href="{url}">'
        + '<meta property="og:type" content="article"><meta property="og:site_name" content="BRYME">'
        + f'<meta property="og:title" content="{esc(page_title)}"><meta property="og:description" content="{esc(desc)}">'
        + f'<meta property="og:url" content="{url}"><meta property="og:image" content="{SITE}{hero}">'
        + '<meta property="og:image:type" content="image/jpeg"><meta property="og:image:alt" content="BRYME">'
        + f'<meta name="twitter:image" content="{SITE}{hero}"><meta name="twitter:image:alt" content="BRYME">'
        + '<meta name="twitter:card" content="summary_large_image">'
        + f'<meta name="twitter:title" content="{esc(page_title)}"><meta name="twitter:description" content="{esc(desc)}">'
        + '<link rel="stylesheet" href="/assets/site.css">'
        + f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(",", ":"))}</script>'
        + header + '<main class="shell">'
        + f'<div class="crumb"><a href="/">Home</a> / <a href="/tech/">BRYME Tech &amp; AI</a> / '
        + f'<a href="/tech/{art["categorySlug"]}/">{esc(art["category"])}</a> / {esc(art["title"])}</div>'
        + f'<section class="article-hero article-hero-photo" style="--hero-img:url(\'{hero}\')">'
        + f'<div class="eyebrow">{esc(art["category"])}</div><h1>{esc(art["title"])}</h1>'
        + f'<p class="lead">{esc(art["excerpt"])}</p>'
        + f'<div class="article-meta"><span><a href="{AUTHOR_URL}" rel="author">{esc(AUTHOR)}</a></span>'
        + f'<span>{CHECKED}</span><span>{esc(art["readingTime"])}</span></div></section>'
        + f'<article class="prose article-body">{body}</article>'
        + f'<section class="sp-source"><h2>Sources</h2><p>{sources}</p>'
        + f'<p class="sp-source-note">Figures were checked against the sources above on {CHECKED}. '
        + "Published terms change — confirm on the provider's own site before relying on them.</p></section>"
        + f'<section class="section"><div class="section-head"><h2>More on BRYME Tech</h2></div>'
        + f'<div class="vcat-grid">{more}</div></section></main>' + footer
    )

C = {
    "privacy": card("/tech/ai-assistant-data-training-settings/", "What they do with your chats", "ChatGPT, Claude and Gemini training toggles — and the ways around them.", HERO_PRIV),
    "termux": card("/tech/learning-to-code-on-a-phone-termux/", "Learning to code on a phone", "The wall was installing the numerical stack in Termux.", HERO_PHONE),
    "host": card("/tech/where-to-host-website-for-free/", "Where to host a website for free", "What GitHub, Cloudflare, Render, Vercel and Netlify actually document.", HERO_HOST),
    "render": card("/tech/render-deployment-failures-what-they-taught-me/", "The site worked. The deploy didn't.", "Four real Render failures, including this site.", HERO_DEP),
    "chatgpt": card("/tech/chatgpt-claude-alternatives/", "Free and cheap ChatGPT alternatives", "Official prices. No fake top ten.", HERO_AI),
    "arena": card("/tech/arena-ai-vs-chatgpt/", "Arena.ai vs ChatGPT", "Free multi-model arena. The privacy notice is the product.", HERO_PRIV),
    "deepseek": card("/tech/deepseek-vs-chatgpt/", "DeepSeek vs ChatGPT", "Free chat on the homepage. API is a separate bill.", HERO_AI),
    "affinity": card("/tech/affinity-now-free/", "Affinity is free now", "Official $0 desktop suite with a free Canva account.", HERO_ALT),
    "bitwarden": card("/tech/bitwarden-free-password-manager/", "Bitwarden’s free plan", "Unlimited devices and passwords, officially.", HERO_PRIV),
    "signal": card("/tech/signal-vs-whatsapp/", "Signal vs WhatsApp", "Officially free, no ads, no tracking. Both sides need the app.", HERO_PRIV),
    "notion": card("/tech/notion-free-plan/", "Notion’s free plan", "$0, 5MB files, 7-day history. Plus is $10.", HERO_TOOLS),
    "beginner": card("/make-money/beginners-guide-to-making-money-online/", "Beginner guide without the lie", "Skills, traps, and what is not a job. No fake income figures.", HERO_BEG),
    "fees": card("/make-money/freelance-platform-fees-explained/", "What Upwork and Fiverr take in 2026", "From their own documentation.", HERO_FEE),
    "writing": card("/make-money/writing/", "Writing markets we checked", "Official rates and doors. A gig is not guaranteed.", HERO_WRITE),
    "notes": card("/make-money/writing-field-notes-how-this-works/", "Writing field notes", "How listings are researched. A gig is not guaranteed.", HERO_WRITE),
    "remote": card("/make-money/remote-work/", "Remote jobs", "Legitimate platforms by country. Official apply links.", HERO_REM),
    "coding": card("/make-money/coding/", "Coding jobs", "Freelance marketplaces and job boards with real rates.", HERO_HOST),
    "nigeria": card("/make-money/make-money-online-nigeria/", "Making money in Nigeria", "Verified platforms that accept Nigerians.", HERO_BEG),
    "monetize": card("/make-money/website-monetization-guide/", "Website monetization", "A real audience, without wrecking trust.", HERO_BEG),
}

def hub(path, nav, crumb_parent, crumb_name, title, lead, hero, keys, eyebrow):
    head, header, footer = chrome(nav)
    url = f"{SITE}{path}"
    page_title = f"{title} | BRYME"
    cards = "".join(C[k] for k in keys)
    parent_href, parent_label = crumb_parent
    ld = [
        {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "description": lead, "url": url},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": parent_label, "item": SITE + parent_href},
            {"@type": "ListItem", "position": 3, "name": title, "item": url},
        ]},
    ]
    vchip_other = (
        '<a class="vchip vchip-tech" href="/tech/"><span class="vchip-emoji">🤖</span><span class="vchip-name">Tech &amp; AI</span><span class="vchip-tag">Practical tools, no theatre</span></a>'
        if nav == "make-money" else
        '<a class="vchip vchip-make-money" href="/make-money/"><span class="vchip-emoji">💰</span><span class="vchip-name">Make Money</span><span class="vchip-tag">Verified writing markets and honest guides</span></a>'
    )
    return (
        head + f"<title>{esc(page_title)}</title>"
        + f'<meta name="description" content="{esc(lead)}"><link rel="canonical" href="{url}">'
        + '<meta property="og:type" content="website"><meta property="og:site_name" content="BRYME">'
        + f'<meta property="og:title" content="{esc(page_title)}"><meta property="og:description" content="{esc(lead)}">'
        + f'<meta property="og:url" content="{url}"><meta property="og:image" content="{SITE}{hero}">'
        + '<meta property="og:image:type" content="image/jpeg"><meta property="og:image:alt" content="BRYME">'
        + f'<meta name="twitter:image" content="{SITE}{hero}"><meta name="twitter:image:alt" content="BRYME">'
        + '<meta name="twitter:card" content="summary_large_image">'
        + f'<meta name="twitter:title" content="{esc(page_title)}"><meta name="twitter:description" content="{esc(lead)}">'
        + '<link rel="stylesheet" href="/assets/site.css">'
        + f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(",", ":"))}</script>'
        + header + '<main class="shell">'
        + f'<div class="crumb"><a href="/">Home</a> / <a href="{parent_href}">{esc(parent_label)}</a> / {esc(crumb_name)}</div>'
        + f'<section class="hero vhero vhero-{"make-money" if nav=="make-money" else "tech"} vhero-photo" data-vertical="{nav}" style="--hero-img:url(\'{hero}\')">'
        + f'<div class="eyebrow">{esc(eyebrow)}</div>'
        + f'<h1>{esc(title)}</h1><p class="lead">{esc(lead)}</p></section>'
        + f'<section class="section"><div class="vcat-grid">{cards}</div></section>'
        + '<section class="section core-hubs" data-core-hubs><div class="section-head"><h2>Also on BRYME</h2></div>'
        + '<p class="section-note">The main sections of the site. Open the next one that matches what you came for.</p>'
        + '<div class="vchips">'
        + '<a class="vchip vchip-entertainment" href="/entertainment/"><span class="vchip-emoji">🎬</span><span class="vchip-name">Entertainment</span><span class="vchip-tag">Movies, series, anime and articles</span></a>'
        + '<a class="vchip vchip-sports" href="/sports/"><span class="vchip-emoji">⚽</span><span class="vchip-name">Sports</span><span class="vchip-tag">Football covered properly</span></a>'
        + vchip_other
        + "</div></section></main>" + footer
    )

def write_articles():
    path = ROOT / "content" / "tech-articles.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    by_id = {a["id"]: i for i, a in enumerate(data)}
    for art in ARTICLES:
        dest = ROOT / "tech" / art["slug"] / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(article_html(art), encoding="utf-8")
        rec = {k: art[k] for k in ("id", "slug", "title", "seoTitle", "excerpt", "category", "categorySlug", "tags")}
        rec.update({"relatedMovieSlugs": [], "status": "published", "author": AUTHOR,
                    "publishedAt": CHECKED, "updatedAt": CHECKED, "readingTime": art["readingTime"],
                    "content": art["content"], "sources": art["sources"], "sourcesCheckedOn": CHECKED})
        if art["id"] in by_id:
            data[by_id[art["id"]]] = rec
        else:
            data.append(rec)
        print("article", art["slug"])
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

TECH_HUBS = {
    "ai-tutorials": ("AI Tutorials", "Start with the settings and the phone setup. Not a prompt-pack shop.", HERO_AI,
                     ["privacy", "termux", "chatgpt"], "🤖 BRYME Tech & AI · AI Tutorials"),
    "automation": ("Automation", "What we have actually written: Termux, deploys, a password manager. Not a Zapier clone list.", HERO_DEP,
                   ["termux", "render", "bitwarden"], "🤖 BRYME Tech & AI · Automation"),
    "developer-tools": ("Developer Tools", "Hosting, Termux and the Render failures from this site.", HERO_DEP,
                        ["host", "render", "termux"], "🤖 BRYME Tech & AI · Developer Tools"),
    "new-tech": ("New Technology", "Things that changed on official pages this year: Affinity went free. Arena and DeepSeek are live.", HERO_AI,
                 ["affinity", "arena", "deepseek", "notion"], "🤖 BRYME Tech & AI · New Technology"),
}

MONEY_HUBS = {
    "content-creation": ("Content Creation", "We do not have a YouTube-pay list. We do have writing markets and the process behind them.", HERO_WRITE,
                         ["writing", "notes", "monetize"], "💰 BRYME Make Money · Content Creation"),
    "income-skills": ("Income Skills", "Writing, coding and the beginner guide. No fake hourly rates.", HERO_BEG,
                      ["beginner", "writing", "coding"], "💰 BRYME Make Money · Income Skills"),
    "ai-assisted-work": ("AI-Assisted Work", "Many paying markets on this site ban AI. Read the privacy piece and the field notes before you paste a draft into a chatbot.", HERO_AI,
                         ["privacy", "notes", "chatgpt"], "💰 BRYME Make Money · AI-Assisted Work"),
    "platform-reviews": ("Platform Reviews", "Honest pages about platforms that pay — fees, remote jobs, coding boards. Not a dump of unverified apps.", HERO_FEE,
                         ["fees", "remote", "coding", "nigeria"], "💰 BRYME Make Money · Platform Reviews"),
}

def write_hubs():
    for slug, (title, lead, hero, keys, eye) in TECH_HUBS.items():
        dest = ROOT / "tech" / slug / "index.html"
        dest.write_text(hub(f"/tech/{slug}/", "tech", ("/tech/", "BRYME Tech & AI"), title, title, lead, hero, keys, eye), encoding="utf-8")
        print("tech hub", slug)
    for slug, (title, lead, hero, keys, eye) in MONEY_HUBS.items():
        dest = ROOT / "make-money" / slug / "index.html"
        dest.write_text(hub(f"/make-money/{slug}/", "make-money", ("/make-money/", "BRYME Make Money"), title, title, lead, hero, keys, eye), encoding="utf-8")
        print("money hub", slug)

def patch_existing_hubs():
    # add new articles onto already-filled hubs
    patches = {
        ROOT / "tech" / "android-apps" / "index.html": ("signal", "/tech/signal-vs-whatsapp/"),
        ROOT / "tech" / "cybersecurity" / "index.html": ("signal", "/tech/signal-vs-whatsapp/"),
        ROOT / "tech" / "productivity" / "index.html": ("notion", "/tech/notion-free-plan/"),
        ROOT / "tech" / "useful-websites" / "index.html": ("notion", "/tech/notion-free-plan/"),
        ROOT / "tech" / "app-alternatives" / "index.html": ("signal", "/tech/signal-vs-whatsapp/"),
    }
    for path, (key, href) in patches.items():
        t = path.read_text(encoding="utf-8")
        if href in t:
            continue
        t = t.replace('<div class="vcat-grid">', '<div class="vcat-grid">' + C[key], 1)
        path.write_text(t, encoding="utf-8")
        print("patched", path.parent.name)

def patch_home():
    path = ROOT / "index.html"
    t = path.read_text(encoding="utf-8")
    old = """      <a href="/tech/ai-assistants/">AI assistants, compared for real work</a>
      <a href="/tech/ai-assistant-data-training-settings/">What &ldquo;train on your data&rdquo; actually means</a>
      <a href="/articles/">All BRYME stories</a>"""
    new = """      <a href="/tech/chatgpt-claude-alternatives/">Free and cheap ChatGPT alternatives</a>
      <a href="/tech/app-alternatives/">App alternatives we actually checked</a>
      <a href="/tech/ai-assistant-data-training-settings/">What &ldquo;train on your data&rdquo; actually means</a>
      <a href="/tech/where-to-host-website-for-free/">Where to host a website for free</a>"""
    if old in t:
        t = t.replace(old, new, 1)
        path.write_text(t, encoding="utf-8")
        print("patched homepage")
    else:
        print("homepage block not found")

def patch_author():
    path = ROOT / "author" / "ibrahim-sodiq" / "index.html"
    t = path.read_text(encoding="utf-8")
    needle = '<a class="vcat vcat-photo" href="/tech/where-to-host-website-for-free/"'
    add = ""
    for art in ARTICLES:
        href = f"/tech/{art['slug']}/"
        if href not in t:
            add += card(href, art["title"], art["excerpt"], art["hero"])
    if add:
        t = t.replace(needle, add + needle, 1)
        path.write_text(t, encoding="utf-8")
        print("patched author")

def patch_sitemap():
    path = ROOT / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    locs = re.findall(r"<loc>([^<]+)</loc>", text)
    add = [f"{SITE}/tech/{a['slug']}/" for a in ARTICLES]
    add += [f"{SITE}/tech/{s}/" for s in TECH_HUBS]
    add += [f"{SITE}/make-money/{s}/" for s in MONEY_HUBS]
    new = [u for u in add if u not in locs]
    all_urls = sorted(set(locs + new))
    body = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    body += "".join(f"  <url><loc>{u}</loc></url>\n" for u in all_urls)
    body += "</urlset>\n"
    path.write_text(body, encoding="utf-8")
    print("sitemap", len(locs), "->", len(all_urls))

def patch_search():
    path = ROOT / "data" / "search-index.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    verts = data.setdefault("verticals", [])
    slugs = {v.get("slug") for v in verts}
    extras = [
        ("tech", "Signal vs WhatsApp", "tech/signal-vs-whatsapp", "Officially free, no ads, no tracking."),
        ("tech", "Notion free plan", "tech/notion-free-plan", "$0, 5MB files, 7-day history. Plus is $10."),
        ("make-money", "Platform reviews", "make-money/platform-reviews", "Fees, remote jobs and coding boards we actually wrote."),
    ]
    for typ, title, slug, desc in extras:
        if slug not in slugs:
            verts.append({"type": typ, "title": title, "slug": slug, "description": desc})
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")

def main():
    write_articles()
    write_hubs()
    patch_existing_hubs()
    patch_home()
    patch_author()
    patch_sitemap()
    patch_search()

if __name__ == "__main__":
    main()

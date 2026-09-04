#!/usr/bin/env python3
"""Fill empty tech category cards + three sourced alternative pages."""
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
HERO_ALT = "/assets/img/tech/hero-alternatives.jpg"
HERO_PRIV = "/assets/img/tech/hero-privacy.jpg"
HERO_TOOLS = "/assets/img/tech/hero-tools.jpg"
HERO_PHONE = "/assets/img/tech/hero-phone-code.jpg"
HERO_HOST = "/assets/img/tech/hero-hosting.jpg"
HERO_AI = "/assets/img/tech/hero-assistants.jpg"

HEAD = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#08090b"><meta name="color-scheme" content="dark light"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="icon" href="/assets/favicon.png" type="image/png" sizes="32x32"><link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png"><link rel="manifest" href="/manifest.webmanifest"><link rel="preconnect" href="https://i.ytimg.com" crossorigin><link rel="preconnect" href="https://www.youtube-nocookie.com" crossorigin><link rel="preconnect" href="https://www.youtube.com" crossorigin>"""
HEADER = """</head><body data-nav="tech"><header class="top"><div class="shell"><a class="brand" href="/">BRY<b>ME</b></a><nav class="topnav"><a href="/">Home</a><a href="/entertainment/">🎬 Entertainment</a><a href="/sports/">⚽ Sports</a><a href="/make-money/">💰 Make Money</a><a href="/tech/" class="active">🤖 Tech &amp; AI</a><a class="nav-search" href="/search/">Search</a></nav><div class="top-tools"><a class="header-search" href="/search/" aria-label="Search">Search</a></div></div></header>"""
FOOTER = """<nav class="mobile-nav"><a href="/"><span class="mn-ico">🏠</span>Home</a><a href="/entertainment/"><span class="mn-ico">🎬</span>Entertain</a><a href="/sports/"><span class="mn-ico">⚽</span>Sports</a><a href="/make-money/"><span class="mn-ico">💰</span>Money</a><a href="/tech/" class="active"><span class="mn-ico">🤖</span>Tech</a><a href="/search/"><span class="mn-ico">🔍</span>Search</a></nav><footer class="footer"><div class="shell"><div class="footer-grid">
  <div class="footer-brand"><a class="brand" href="/">BRY<b>ME</b></a><p>Discover what you love. Learn what you need. Find what's next.</p></div>
  <nav class="footer-col" aria-label="Explore"><h3>Verticals</h3><a href="/entertainment/">🎬 Entertainment</a><a href="/sports/">⚽ Sports</a><a href="/make-money/">💰 Make Money</a><a href="/tech/">🤖 Tech &amp; AI</a></nav>
  <nav class="footer-col" aria-label="Explore"><h3>Entertainment</h3><a href="/trending/">What's Trending</a><a href="/movies/">Movies</a><a href="/series/">Series</a><a href="/anime/">Anime</a><a href="/articles/">Articles</a><a href="/genres/">Genres</a></nav>
  <nav class="footer-col" aria-label="Information"><h3>Information</h3><a href="/about/">About</a><a href="/contact/">Contact</a><a href="/editorial-policy/">Editorial Policy</a></nav>
  <nav class="footer-col" aria-label="Legal"><h3>Legal</h3><a href="/privacy/">Privacy Policy</a><a href="/terms/">Terms of Use</a><a href="/disclaimer/">Disclaimer</a><a href="/copyright/">Copyright / DMCA</a></nav>
</div>
<p class="footer-note">BRYME · Discover what you love. Learn what you need. Find what's next. Trailer links lead to YouTube and viewing links lead to third parties.<small>Trending Now is editorially curated by BRYME — it is not live traffic data. Popular and Editor's Picks are independent rankings. Real user analytics will replace trending once the site has enough traffic. · Build 2026-08-23 08:10 UTC</small></div></footer><script>window.BRYME_BASE=''</script><script src="/assets/site-app.js"></script></body></html>"""

ARTICLES = [
    {
        "id": "affinity-now-free",
        "slug": "affinity-now-free",
        "title": "Affinity Is Free Now. That Is Not a Canva Clone.",
        "seoTitle": "Affinity Is Free Now. Not a Canva Clone",
        "excerpt": "Canva’s official Affinity pages say the desktop app is $0 with a free Canva account. Pixel, vector and layout tools included. Canva AI inside Affinity is the part that still wants Pro.",
        "category": "App Alternatives",
        "categorySlug": "app-alternatives",
        "tags": ["affinity", "canva", "photoshop", "design-tools"],
        "readingTime": "7 min read",
        "hero": HERO_ALT,
        "content": [
            {
                "heading": "The sentence that changed the shelf",
                "body": "Most “Canva alternative” lists still price Affinity as a one-time $70–$90 download. That is stale.\n\nOn 23 August 2026, Canva’s own Affinity download page prints “$0, free.” The FAQ is blunt: every tool in the Pixel, Vector and Layout studios is included, with free updates, and you do not need Canva Pro to use those studios. You do need a Canva account — free is enough — because Affinity is now a Canva product.\n\nThat is a bigger fact than Plasfy’s $199 lifetime deal. Affinity was already the serious desktop editor people named when they were tired of Photoshop’s subscription. Canva bought it and took the price to zero.",
            },
            {
                "heading": "What official pages say you get",
                "body": "The Get Affinity page lists: vector, pixel and layout in one app; customizable studios; non-destructive editing; pixel-perfect export; PSD, AI, PDF, SVG and IDML import; one-click export to Canva; full RAW editing; retouching tools they name as inpainting, healing, dodge and burn; batch macros, HDR merge and panoramas; pen/node/pencil tools; print-ready CMYK, spot colour, preflight and bleed.\n\nDesktop is what they are shipping. The same FAQ says there is no release date yet for the new Affinity on iPad, and tells people to keep running V2 on iPad for now. I am not going to invent a tablet app.\n\nYou must be online to download and activate the licence with the Canva account. After that, they say you can work offline, including for extended periods.",
            },
            {
                "heading": "What is still paid",
                "body": "Canva AI inside Affinity — generative fill, expand, generate images and vectors, remove background, super resolution, brand system — is documented as a Canva premium unlock (Pro, Business, Enterprise or Education).\n\nSo: the editor is free. The Canva AI layer is not. That is the opposite of Plasfy’s “pay once, everything unlocked” pitch, and it is the opposite of “Affinity replaced Canva.” Affinity is the desktop suite. Canva is still the template-and-brand web app. They now share a login.",
            },
            {
                "heading": "Not Photoshop, not Canva, not Photopea",
                "body": "If you want Photoshop’s subscription, cloud libraries and Adobe’s plugin world, Affinity is a different vendor. I did not copy Adobe’s current monthly price onto this page. Open Adobe’s own plan page if that number is why you are leaving.\n\nIf you want Canva’s 1.6 million free templates in a browser, Affinity will feel empty. It is a blank professional surface.\n\nIf you want a no-account PSD editor in a tab, that is Photopea, written up separately. Affinity is a desktop install tied to a Canva login.",
            },
            {
                "heading": "How I would choose, labelled as opinion",
                "body": "If I was paying Adobe only for layers, RAW and print PDF, I would download Affinity on a free Canva account before I renewed.\n\nIf I make Instagram posts from templates, I would stay in Canva Free and ignore Affinity until I actually need a desktop studio.\n\nIf I already paid Plasfy $199 to escape Canva, I would still open Affinity. The official price is $0. The jobs overlap less than the marketing implies.\n\nI have not run a client print job through the new Canva-era Affinity. I am repeating their pages, not a press proof.",
            },
        ],
        "sources": [
            {"name": "Get Affinity — official download ($0, free)", "url": "https://www.affinity.studio/get-affinity"},
            {"name": "Canva / Affinity — free, not-for-profit FAQ", "url": "https://affinity.serif.com/en-us/affinity-canva-free-not-for-profit/"},
            {"name": "Canva newsroom — Why we made Affinity free", "url": "https://www.canva.com/newsroom/news/affinity-free/"},
        ],
    },
    {
        "id": "photopea-vs-photoshop",
        "slug": "photopea-vs-photoshop",
        "title": "Photopea: Photoshop in the Browser, Files Stay Local",
        "seoTitle": "Photopea: Photoshop in the Browser, Local Files",
        "excerpt": "Photopea’s own site: free online editor, full PSD open and save, no uploads — it runs on your CPU and GPU. Ads fund the free tier. I am not inventing the Premium dollar figure they keep inside the Account window.",
        "category": "Useful Websites",
        "categorySlug": "useful-websites",
        "tags": ["photopea", "photoshop", "photo-editing", "alternatives"],
        "readingTime": "7 min read",
        "hero": HERO_TOOLS,
        "content": [
            {
                "heading": "The useful Photoshop alternative is a website",
                "body": "Photopea is not a Canva clone. It is a browser editor that copies the Photoshop job: layers, masks, smart objects, PSD as the main format.\n\nI opened photopea.com on 23 August 2026. The homepage calls itself a free online photo editor. The claims that matter are specific: “There are no uploads. Photopea runs on your device, using your CPU and your GPU. All files open instantly, and never leave your device.” And: it fully supports opening and saving PSD.\n\nThat local-processing sentence is why this page exists. Most “free Photoshop” web tools upload the file. Photopea says it does not.",
            },
            {
                "heading": "What they document besides PSD",
                "body": "Official homepage: layers, masks, layer styles, smart objects, adjustment layers, channels, paths; Levels, Curves, Gaussian Blur, Liquify, Puppet Warp; vector drawing; RAW formats they list as DNG, CR2, CR3, NEF, ARW, RW2, RAF, ORF and FFF; plus PNG, JPG, GIF, WEBP, SVG, PDF, AI and a long tail they point at a GitHub formats list.\n\nThey also advertise one-click background removal and generative replace. Those are AI features on a local editor. I did not test whether those particular AI calls stay on-device. The “no uploads” paragraph is about your files in the editor. I will not extend it to every AI button without their docs saying so.",
            },
            {
                "heading": "Free means ads. Premium is real. The price is not on the marketing page.",
                "body": "Photopea’s official accounts page: two consumer account types, Free and Premium. Free is available to anybody at photopea.com. Premium “lets you use Photopea without advertisement and may have other benefits.” Prices, they say, live in the Account window after you log in with Google or Facebook.\n\nI am not going to print “$5 a month” from comparison blogs. It is not on the page I can cite. Open Account if you want the live number.\n\nSchools can buy a yearly domain whitelist starting at $450 a year for the whole school, no student logins. Self-hosted Photopea is a different product they price between $500 and $2,000 a month, paid a year ahead. That is for people embedding the editor, not for opening a PSD.",
            },
            {
                "heading": "Versus Photoshop, Pixlr, Affinity, Canva",
                "body": "Photoshop is Adobe’s subscription desktop suite. Photopea is the “I was sent a PSD and I do not have Adobe this afternoon” tool.\n\nPixlr is a photo/AI editor with a published Plus price. It is not a PSD-first Photoshop surface.\n\nAffinity is now a free desktop install via a Canva account. Use that if you want an app. Use Photopea if you want no install and a file that never leaves the tab.\n\nCanva is templates. Photopea will feel hostile if you came for Instagram sizes and stock photos.",
            },
            {
                "heading": "How I would choose, labelled as opinion",
                "body": "If someone mails me a layered PSD, I would open Photopea before I paid Adobe for one afternoon.\n\nIf I edit photos every day and I want no ads, I would look at the Account window, or download Affinity for $0, and stop living in a tab.\n\nI have not subscribed to Photopea Premium. I am not going to invent a cloud-storage limit I did not see on the accounts page.",
            },
        ],
        "sources": [
            {"name": "Photopea homepage", "url": "https://www.photopea.com/"},
            {"name": "Photopea — Accounts (Free vs Premium)", "url": "https://www.photopea.com/api/accounts"},
            {"name": "Photopea — Schools (ads-free from $450/year)", "url": "https://www.photopea.com/schools/"},
        ],
    },
    {
        "id": "bitwarden-free-password-manager",
        "slug": "bitwarden-free-password-manager",
        "title": "Bitwarden’s Free Plan: Unlimited Devices, Officially",
        "seoTitle": "Bitwarden Free Plan: Unlimited Devices",
        "excerpt": "Bitwarden’s pricing page still offers a free account: unlimited devices and unlimited passwords. Premium is $1.65 a month if you pay the year. That is the cheap password-manager alternative I could source.",
        "category": "Cybersecurity",
        "categorySlug": "cybersecurity",
        "tags": ["bitwarden", "passwords", "security", "android"],
        "readingTime": "7 min read",
        "hero": HERO_PRIV,
        "content": [
            {
                "heading": "The free plan the others dropped",
                "body": "A password manager is not a Canva alternative. It is the app that stops you using the same password on the bank and the blog.\n\nI opened bitwarden.com/pricing on 23 August 2026. Under personal plans, after Premium and Families, they print: “Just getting started? Get basic password management today. Always free.” Core features they list on every account include: open source, zero-knowledge encryption, unlimited devices, unlimited passwords, browser/mobile/desktop apps, a generator, passkeys, encrypted export, and free sharing with one other user.\n\nThat “unlimited devices” line is the comparison. Bitwarden’s own LastPass comparison page says LastPass’s free plan is limited to one device. I am treating Bitwarden’s statement about LastPass as Bitwarden’s claim, not as LastPass’s current terms. Open LastPass if you still live there.",
            },
            {
                "heading": "What $1.65 actually buys",
                "body": "Premium is $1.65 a month, billed annually at $19.80. Official extras: integrated authenticator (TOTP), file attachments (5GB personal, expandable), emergency access, vault health reports, priority support. You can share vault items with one other user.\n\nFamilies is $3.99 a month, billed annually at $47.88, for up to six people.\n\nPrices are USD, annual billing, taxes not included. I did not find a naira table.\n\nTeams is $4 per user per month annual. Enterprise is $6. Those are work products. The free personal plan is the one this page is about.",
            },
            {
                "heading": "What free does not include",
                "body": "On the comparison table, TOTP, vault health reports, emergency access and the 5GB attachments sit on Premium, not on the “core / every account” list. So: free stores the passwords across devices. Paid adds the authenticator and the “what if I get hit by a bus” contact.\n\nI would not call free “fully featured” the way Bitwarden’s marketing sometimes does. Their pricing table is more honest than the slogan. Use the table.",
            },
            {
                "heading": "Have I Been Pwned is the other free check",
                "body": "haveibeenpwned.com is Troy Hunt’s free site for checking whether an email appeared in a known breach. The About page says that is the whole public job: type an address, see if it was in a dump. Domain-monitoring subscriptions exist for organisations. The personal check is free.\n\nThat is not a password manager. It tells you the leak already happened. Bitwarden is how you stop the next login using the same password. Use both. Do not paste your actual password into random “password checkers.” HIBP’s Pwned Passwords page is the official way to check a password against breach lists.",
            },
            {
                "heading": "How I would choose, labelled as opinion",
                "body": "If I still keep passwords in Chrome or a notes app, I would open Bitwarden’s free account today and move the bank and email first.\n\nIf I already pay 1Password or a family iCloud Keychain and it works, I would not migrate for sport.\n\nIf I want TOTP in the same vault, $19.80 a year is the official Premium number. That is cheaper than most “security suite” ads.\n\nI have not audited Bitwarden’s code. “Open source” is their claim and a real repo. It is not a personal security review.",
            },
        ],
        "sources": [
            {"name": "Bitwarden — Pricing", "url": "https://bitwarden.com/pricing/"},
            {"name": "Bitwarden vs LastPass (Bitwarden’s comparison)", "url": "https://bitwarden.com/bitwarden-vs-lastpass/"},
            {"name": "Have I Been Pwned — About", "url": "https://haveibeenpwned.com/About"},
            {"name": "Have I Been Pwned — Pwned Passwords", "url": "https://haveibeenpwned.com/Passwords"},
        ],
    },
]


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def paras(text: str) -> str:
    return "".join(f"<p>{esc(c.strip())}</p>" for c in text.split("\n\n") if c.strip())


def desc_meta(excerpt: str, limit: int = 155) -> str:
    excerpt = " ".join(excerpt.split())
    if len(excerpt) <= limit:
        return excerpt
    return excerpt[:limit].rsplit(" ", 1)[0].rstrip(".,;:") + "…"


def card(href: str, title: str, excerpt: str, hero: str) -> str:
    return (
        f'<a class="vcat vcat-photo" href="{href}" style="--card-img:url(\'{hero}\')">'
        f"<b>{esc(title)}</b><span>{esc(excerpt)}</span></a>"
    )


KNOWN = {
    "where-to-host": card("/tech/where-to-host-website-for-free/", "Where to host a website for free", "GitHub Pages, Cloudflare, Render, Vercel, Netlify. What their docs actually say.", HERO_HOST),
    "render": card("/tech/render-deployment-failures-what-they-taught-me/", "The site worked. The deploy didn't.", "Four real Render failures, including the package.json error on this site.", "/assets/img/tech/hero-deploy.jpg"),
    "privacy": card("/tech/ai-assistant-data-training-settings/", "What they actually do with your chats", "ChatGPT, Claude and Gemini each have a training toggle — and a way around it.", HERO_PRIV),
    "termux": card("/tech/learning-to-code-on-a-phone-termux/", "Learning to code on a phone", "The wall was installing the numerical stack in Termux, not the screen.", HERO_PHONE),
    "chatgpt-alts": card("/tech/chatgpt-claude-alternatives/", "Free and cheap ChatGPT alternatives", "Official prices for Gemini, DeepSeek, Arena, Copilot and Perplexity.", HERO_AI),
    "arena": card("/tech/arena-ai-vs-chatgpt/", "Arena.ai vs ChatGPT", "A free multi-model arena, not a Plus plan. The privacy notice is the product.", HERO_PRIV),
    "gemini": card("/tech/gemini-vs-chatgpt/", "Gemini vs ChatGPT: the $4.99 step", "Google AI Plus is $4.99. ChatGPT Go is $8 US. Plus is $20.", HERO_AI),
    "deepseek": card("/tech/deepseek-vs-chatgpt/", "DeepSeek vs ChatGPT", "Homepage still says free chat. The API is a separate bill.", HERO_AI),
    "plasfy": card("/tech/plasfy-vs-canva/", "Plasfy vs Canva", "$199 lifetime on Plasfy’s homepage. Canva still has a $0 plan.", HERO_ALT),
    "pixlr": card("/tech/pixlr-vs-canva/", "Pixlr vs Canva", "Photo/AI editor, not a template product. Plus starts at $1.99/mo yearly.", HERO_ALT),
    "polotno": card("/tech/polotno-studio-vs-canva/", "Polotno Studio vs Canva", "Still free, still no signup. The paid product is the SDK.", HERO_ALT),
    "lyra": card("/tech/lyra-vs-spotify/", "Lyra vs Spotify", "A real app. A YouTube pipe. Nigeria Premium is ₦1,600.", HERO_ALT),
    "affinity": card("/tech/affinity-now-free/", "Affinity is free now", "Official $0 desktop suite with a free Canva account. Not a Canva clone.", HERO_ALT),
    "photopea": card("/tech/photopea-vs-photoshop/", "Photopea vs Photoshop", "Browser PSD editor. Files stay local. Ads fund free.", HERO_TOOLS),
    "bitwarden": card("/tech/bitwarden-free-password-manager/", "Bitwarden’s free plan", "Unlimited devices and passwords, officially. Premium is $1.65/mo annual.", HERO_PRIV),
    "appalts": card("/tech/app-alternatives/", "App alternatives we checked", "Only the comparisons that survived a source check.", HERO_ALT),
}

HUBS = {
    "ai-tools": {
        "title": "AI Tools",
        "lead": "What the official pages say these tools cost and do — not a fake top ten.",
        "hero": HERO_AI,
        "keys": ["chatgpt-alts", "arena", "gemini", "deepseek", "privacy", "pixlr"],
    },
    "useful-websites": {
        "title": "Useful Websites",
        "lead": "Sites worth opening. Each one has a sourced BRYME page, not a directory blurb.",
        "hero": HERO_TOOLS,
        "keys": ["photopea", "polotno", "affinity", "bitwarden", "where-to-host", "appalts"],
    },
    "android-apps": {
        "title": "Android Apps",
        "lead": "Phone tools we have actually written up: Termux, Lyra, Bitwarden.",
        "hero": HERO_PHONE,
        "keys": ["termux", "lyra", "bitwarden"],
    },
    "cybersecurity": {
        "title": "Cybersecurity Awareness",
        "lead": "Passwords and breaches, from official pages. No scare-suite ads.",
        "hero": HERO_PRIV,
        "keys": ["bitwarden", "privacy"],
    },
    "productivity": {
        "title": "Productivity",
        "lead": "Editors and assistants that replace a paid subscription — when the official price says so.",
        "hero": HERO_TOOLS,
        "keys": ["affinity", "photopea", "plasfy", "pixlr", "chatgpt-alts"],
    },
    "website-building": {
        "title": "Website Building",
        "lead": "Getting a real site online. Start with what free hosting actually means.",
        "hero": HERO_HOST,
        "keys": ["where-to-host", "render"],
    },
    "ai-image-video": {
        "title": "AI Image & Video",
        "lead": "Image tools we sourced. Not a Midjourney clone list.",
        "hero": HERO_TOOLS,
        "keys": ["pixlr", "photopea", "affinity"],
    },
    "internet-tools": {
        "title": "Internet Tools",
        "lead": "Browser utilities with a BRYME page behind them.",
        "hero": HERO_PRIV,
        "keys": ["photopea", "polotno", "bitwarden"],
    },
    "ai-coding": {
        "title": "AI Coding",
        "lead": "Coding with a phone, and with an agent. Two sourced pages. Not a Copilot review.",
        "hero": HERO_PHONE,
        "keys": ["termux", "arena"],
    },
}


def article_html(art: dict) -> str:
    url = f"{SITE}/tech/{art['slug']}/"
    page_title = f"{art['seoTitle']} | BRYME"
    desc = desc_meta(art["excerpt"])
    hero = art["hero"]
    body = "".join(f"<h2>{esc(b['heading'])}</h2>{paras(b['body'])}" for b in art["content"])
    sources = " · ".join(f'<a href="{esc(s["url"])}" rel="nofollow noopener">{esc(s["name"])}</a>' for s in art["sources"])
    sibs = "".join(
        card(f"/tech/{a['slug']}/", a["title"], a["excerpt"], a["hero"])
        for a in ARTICLES if a["slug"] != art["slug"]
    ) + KNOWN["appalts"]
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
        HEAD + f"<title>{esc(page_title)}</title>"
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
        + HEADER + '<main class="shell">'
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
        + f'<div class="vcat-grid">{sibs}</div></section></main>' + FOOTER
    )


def hub_html(slug: str, meta: dict) -> str:
    url = f"{SITE}/tech/{slug}/"
    title = f"{meta['title']} | BRYME"
    desc = meta["lead"]
    cards = "".join(KNOWN[k] for k in meta["keys"])
    ld = [
        {"@context": "https://schema.org", "@type": "CollectionPage", "name": meta["title"],
         "description": desc, "url": url},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "BRYME Tech & AI", "item": SITE + "/tech/"},
            {"@type": "ListItem", "position": 3, "name": meta["title"], "item": url},
        ]},
    ]
    return (
        HEAD + f"<title>{esc(title)}</title>"
        + f'<meta name="description" content="{esc(desc)}"><link rel="canonical" href="{url}">'
        + '<meta property="og:type" content="website"><meta property="og:site_name" content="BRYME">'
        + f'<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">'
        + f'<meta property="og:url" content="{url}"><meta property="og:image" content="{SITE}{meta["hero"]}">'
        + '<meta property="og:image:type" content="image/jpeg"><meta property="og:image:alt" content="BRYME">'
        + f'<meta name="twitter:image" content="{SITE}{meta["hero"]}"><meta name="twitter:image:alt" content="BRYME">'
        + '<meta name="twitter:card" content="summary_large_image">'
        + f'<meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}">'
        + '<link rel="stylesheet" href="/assets/site.css">'
        + f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(",", ":"))}</script>'
        + HEADER + '<main class="shell">'
        + f'<div class="crumb"><a href="/">Home</a> / <a href="/tech/">BRYME Tech &amp; AI</a> / {esc(meta["title"])}</div>'
        + f'<section class="hero vhero vhero-tech vhero-photo" data-vertical="tech" style="--hero-img:url(\'{meta["hero"]}\')">'
        + f'<div class="eyebrow">🤖 BRYME Tech &amp; AI · {esc(meta["title"])}</div>'
        + f'<h1>{esc(meta["title"])}</h1><p class="lead">{esc(meta["lead"])}</p></section>'
        + f'<section class="section"><div class="vcat-grid">{cards}</div></section>'
        + '<section class="section core-hubs" data-core-hubs><div class="section-head"><h2>Also on BRYME</h2></div>'
        + '<p class="section-note">The main sections of the site. Open the next one that matches what you came for.</p>'
        + '<div class="vchips">'
        + '<a class="vchip vchip-entertainment" href="/entertainment/"><span class="vchip-emoji">🎬</span><span class="vchip-name">Entertainment</span><span class="vchip-tag">Movies, series, anime and articles</span></a>'
        + '<a class="vchip vchip-sports" href="/sports/"><span class="vchip-emoji">⚽</span><span class="vchip-name">Sports</span><span class="vchip-tag">Football covered properly</span></a>'
        + '<a class="vchip vchip-make-money" href="/make-money/"><span class="vchip-emoji">💰</span><span class="vchip-name">Make Money</span><span class="vchip-tag">Verified writing markets and honest guides</span></a>'
        + '<a class="vchip vchip-tech" href="/tech/"><span class="vchip-emoji">🤖</span><span class="vchip-name">Tech &amp; AI</span><span class="vchip-tag">Practical tools, no theatre</span></a>'
        + "</div></section></main>" + FOOTER
    )


def write_articles() -> None:
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
        print("article", art["slug"], "titlec", len(art["seoTitle"] + " | BRYME"))
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_hubs() -> None:
    for slug, meta in HUBS.items():
        dest = ROOT / "tech" / slug / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(hub_html(slug, meta), encoding="utf-8")
        print("hub", slug, "cards", len(meta["keys"]))


def patch_app_alts() -> None:
    path = ROOT / "tech" / "app-alternatives" / "index.html"
    t = path.read_text(encoding="utf-8")
    extra = KNOWN["affinity"] + KNOWN["photopea"] + KNOWN["bitwarden"]
    if "/tech/affinity-now-free/" not in t:
        t = t.replace("</div>\n</section>\n<section class=\"section\">\n  <div class=\"section-head\"><h2>AI assistants</h2>", extra + "</div>\n</section>\n<section class=\"section\">\n  <div class=\"section-head\"><h2>AI assistants</h2>", 1)
        if "/tech/affinity-now-free/" not in t:
            t = t.replace("</div>\n</section>\n<section class=\"section\">\n  <div class=\"section-head\"><h2>Still in research</h2>", extra + "</div>\n</section>\n<section class=\"section\">\n  <div class=\"section-head\"><h2>Still in research</h2>", 1)
    note = (
        "<p><b>YouTube Music</b> is a real Spotify alternative. I did not get an official Nigeria naira price "
        "I would print today, so there is no page yet. US Premium figures are not Nigeria.</p>"
        "<p><b>Adobe Express</b> is real. I did not open a comparison page this round.</p>"
    )
    if "YouTube Music" not in t:
        t = t.replace("<p><b>Suno</b>", note + "<p><b>Suno</b>", 1)
    path.write_text(t, encoding="utf-8")
    print("patched app-alternatives")


def patch_author() -> None:
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


def patch_sitemap() -> None:
    path = ROOT / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    locs = re.findall(r"<loc>([^<]+)</loc>", text)
    add = [f"{SITE}/tech/{a['slug']}/" for a in ARTICLES]
    add += [f"{SITE}/tech/{s}/" for s in HUBS]
    new = [u for u in add if u not in locs]
    if not new:
        print("sitemap already current")
        return
    all_urls = sorted(set(locs + new))
    body = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    body += "".join(f"  <url><loc>{u}</loc></url>\n" for u in all_urls)
    body += "</urlset>\n"
    path.write_text(body, encoding="utf-8")
    print("sitemap", len(locs), "->", len(all_urls))


def patch_search() -> None:
    path = ROOT / "data" / "search-index.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    verts = data.setdefault("verticals", [])
    slugs = {v.get("slug") for v in verts}
    for slug, meta in HUBS.items():
        key = f"tech/{slug}"
        if key not in slugs:
            verts.append({"type": "tech", "title": meta["title"], "slug": key, "description": meta["lead"]})
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print("search verticals", len(verts))


def patch_landing() -> None:
    path = ROOT / "tech" / "index.html"
    t = path.read_text(encoding="utf-8")
    t = t.replace(
        "<span>The most useful AI tools and what they actually do.</span>",
        "<span>Gemini, DeepSeek, Arena, Pixlr — official prices, no fake top ten.</span>",
    )
    t = t.replace(
        "<span>Apps that make your phone more useful.</span>",
        "<span>Termux, Lyra, Bitwarden. Written up, not a Play Store dump.</span>",
    )
    t = t.replace(
        "<span>Staying safe online without the scare tactics.</span>",
        "<span>Bitwarden’s free plan and what HIBP actually checks.</span>",
    )
    t = t.replace(
        "<span>Websites worth knowing about.</span>",
        "<span>Photopea, Polotno, Affinity, Bitwarden. Each has a sourced page.</span>",
    )
    path.write_text(t, encoding="utf-8")
    print("patched landing blurbs")


def main() -> None:
    write_articles()
    write_hubs()
    patch_app_alts()
    patch_author()
    patch_sitemap()
    patch_search()
    patch_landing()


if __name__ == "__main__":
    main()

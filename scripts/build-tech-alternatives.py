#!/usr/bin/env python3
"""Build sourced Canva/Spotify alternative pages. Surgical — does not rebuild the site."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://bryme.onrender.com"
CHECKED = "2026-08-23"
HERO = "/assets/img/tech/hero-alternatives.jpg"
AUTHOR = "Ibrahim Sodiq"
AUTHOR_URL = "/author/ibrahim-sodiq/"

HEAD_CHROME = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#08090b"><meta name="color-scheme" content="dark light"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="icon" href="/assets/favicon.png" type="image/png" sizes="32x32"><link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png"><link rel="manifest" href="/manifest.webmanifest"><link rel="preconnect" href="https://i.ytimg.com" crossorigin><link rel="preconnect" href="https://www.youtube-nocookie.com" crossorigin><link rel="preconnect" href="https://www.youtube.com" crossorigin>"""

HEADER = """</head><body data-nav="tech"><header class="top"><div class="shell"><a class="brand" href="/">BRY<b>ME</b></a><nav class="topnav"><a href="/">Home</a><a href="/entertainment/">🎬 Entertainment</a><a href="/sports/">⚽ Sports</a><a href="/make-money/">💰 Make Money</a><a href="/tech/" class="active">🤖 Tech &amp; AI</a><a class="nav-search" href="/search/">Search</a></nav><div class="top-tools"><a class="header-search" href="/search/" aria-label="Search">Search</a></div></div></header>"""

FOOTER = """<nav class="mobile-nav"><a href="/"><span class="mn-ico">🏠</span>Home</a><a href="/entertainment/"><span class="mn-ico">🎬</span>Entertain</a><a href="/sports/"><span class="mn-ico">⚽</span>Sports</a><a href="/make-money/"><span class="mn-ico">💰</span>Money</a><a href="/tech/" class="active"><span class="mn-ico">🤖</span>Tech</a><a href="/search/"><span class="mn-ico">🔍</span>Search</a></nav><footer class="footer"><div class="shell"><div class="footer-grid">
  <div class="footer-brand"><a class="brand" href="/">BRY<b>ME</b></a><p>Discover what you love. Learn what you need. Find what's next.</p></div>
  <nav class="footer-col" aria-label="Explore"><h3>Verticals</h3><a href="/entertainment/">🎬 Entertainment</a><a href="/sports/">⚽ Sports</a><a href="/make-money/">💰 Make Money</a><a href="/tech/">🤖 Tech &amp; AI</a></nav>
  <nav class="footer-col" aria-label="Explore"><h3>Entertainment</h3><a href="/trending/">What's Trending</a><a href="/movies/">Movies</a><a href="/series/">Series</a><a href="/anime/">Anime</a><a href="/articles/">Articles</a><a href="/genres/">Genres</a></nav>
  <nav class="footer-col" aria-label="Information"><h3>Information</h3><a href="/about/">About</a><a href="/contact/">Contact</a><a href="/editorial-policy/">Editorial Policy</a></nav>
  <nav class="footer-col" aria-label="Legal"><h3>Legal</h3><a href="/privacy/">Privacy Policy</a><a href="/terms/">Terms of Use</a><a href="/disclaimer/">Disclaimer</a><a href="/copyright/">Copyright / DMCA</a></nav>
</div>
<p class="footer-note">BRYME · Discover what you love. Learn what you need. Find what's next. Trailer links lead to YouTube and viewing links lead to third parties.<small>Trending Now is editorially curated by BRYME — it is not live traffic data. Popular and Editor's Picks are independent rankings. Real user analytics will replace trending once the site has enough traffic. · Build 2026-08-23 07:30 UTC</small></div></footer><script>window.BRYME_BASE=''</script><script src="/assets/site-app.js"></script></body></html>"""

ARTICLES = [
    {
        "id": "plasfy-vs-canva",
        "slug": "plasfy-vs-canva",
        "title": "Plasfy vs Canva: Lifetime Deal or Real Free Plan",
        "seoTitle": "Plasfy vs Canva: Lifetime Deal or Real Free Plan",
        "excerpt": "Plasfy sells a one-time Canva-shaped editor. Canva still has a $0 plan. I opened both official pages on 23 August 2026. Here is what they actually publish — including the number Plasfy contradicts on its own homepage.",
        "category": "App Alternatives",
        "categorySlug": "app-alternatives",
        "tags": ["plasfy", "canva", "design-tools", "alternatives"],
        "readingTime": "8 min read",
        "hero": HERO,
        "content": [
            {
                "heading": "This is not a ranking",
                "body": "Most “Canva alternative” pages are a list of ten logos and a paragraph copied from each homepage. That is not a comparison. It is a directory.\n\nPlasfy is interesting for a narrower reason. It positions itself as the thing you buy so you can stop paying Canva every month. Its own homepage says “Professional Designs Made Easy — Without the Monthly Fees” and “Zero Subscriptions Forever.” That is a real decision, not a vibe.\n\nI am not going to tell you Plasfy is better. I have not run a client project through it. I opened plasfy.com and canva.com/pricing on 23 August 2026 and wrote down what those pages actually publish. Where a number is missing, or the same page disagrees with itself, I will say so.",
            },
            {
                "heading": "What Plasfy is selling today",
                "body": "Plasfy is a browser design editor. The live homepage advertises 20,000+ templates, 100+ formats, canvas resize, 10 million images, 2,500 fonts and 30 million graphics, plus an AI graphics creator, an AI background remover and transparent PNG export.\n\nThe commercial offer on that same page, today, is not a free plan. It is a “Lifetime Founders” deal at $199. The card lists: all features unlocked, Plasfy AI Graphics Factory, those 20,000+ templates, 100+ formats, unlimited AI background remover, millions of royalty-free stock images, transparent PNG exports, unlimited projects, 200GB image cloud storage, a commercial licence, tutorials, and “all future updates included.” It also advertises a 30-day money-back guarantee and a one-time payment.\n\nTwo FAQ answers matter more than the feature list. Plasfy says it is cloud software that works in a web browser. And it says, in plain language: “We don’t support iPads or Tablets.” If your design work lives on a tablet, that sentence ends the comparison before price does.\n\nThe checkout URL on the page is app.plasfy.com/order/professional/. There is also a path branded plasfy-free. That is a sales funnel name. It is not a $0 product.",
            },
            {
                "heading": "What Canva is selling today",
                "body": "Canva’s official pricing page, with the yearly toggle on, currently lists four consumer and business plans.\n\nFree is US$0. Official inclusions: a drag-and-drop editor and 1,000+ design types, 1.6 million+ templates, 4.7 million+ photos, videos, graphics and audio, one Brand Kit limited to three colours, 5GB of cloud storage, and an AI allowance of up to 200 Standard uses or 20 Premium uses.\n\nPro is US$180 per year for one person. Official extras include premium tools they name as resize, translate and remove background; 3.6 million+ templates including premium; 141 million+ premium photos, videos, graphics and audio; five Brand Kits; social content scheduling; 100GB of storage; and ten times the Free AI allowance.\n\nBusiness is US$250 per year per person. Enterprise is “let’s talk.” Canva also states that K-12 education organisations and not-for-profits can get most premium features for free, and that prices exclude tax.\n\nThose are US-dollar figures on canva.com/pricing. A Nigerian or other local checkout may show a different number. I am not going to invent the naira price.",
            },
            {
                "heading": "The free question, answered without the brochure",
                "body": "If the question is “is Plasfy a free Canva alternative?”, the honest answer on 23 August 2026 is no.\n\nCanva has a documented $0 plan with a large free library. Plasfy’s live homepage is selling a $199 lifetime seat. Older Plasfy sales pages — still on the same domain — have advertised other one-time prices, including $19 and $29, and have also talked about a future $144-per-year subscription. I am not treating those archived funnels as today’s price. I am treating the $199 on the current homepage as today’s price, and I am noting that Plasfy’s own marketing has moved that number before.\n\n“Lifetime” is a sales word. It means Plasfy is promising this purchase covers future updates. It does not mean the company, the editor, or the stock library is immortal. If that promise is why you would pay, read their current terms before you pay — I am not going to paraphrase a legal page I have not quoted.",
            },
            {
                "heading": "What the two libraries actually claim",
                "body": "Canva Free already claims 1.6 million+ templates. Plasfy claims 20,000+. That is not close. If your job is “open a social template and change the text,” Canva’s free shelf is the larger shelf, on their own numbers.\n\nPlasfy’s bet is different: pay once, stop hitting Pro crowns, keep commercial-licence assets without a monthly bill. Whether $199 is cheaper than Canva Pro depends on how long you would have paid Canva. US$180 a year is the Pro figure on Canva’s yearly page today. Two years of Pro is already more than $199. That arithmetic only helps if you would have paid Pro, and if Plasfy still does the work you need.\n\nI have not counted either library myself. I am repeating the numbers each company prints.",
            },
            {
                "heading": "The comparison page you cannot read",
                "body": "Plasfy published a blog post titled “Plasfy vs Canva: A Balanced Look at Pros, Cons, and Key User Concerns.” On 23 August 2026 that URL is password-protected. I am not going to pretend I read a balanced official comparison that the public cannot open.\n\nThat is useful information on its own. If a company that sells against Canva locks its own comparison, you should not treat third-party “Plasfy vs Canva” charts as gospel either. Several of those charts still list monthly Plasfy plans around $9. That is not what plasfy.com is selling today.",
            },
            {
                "heading": "How I would choose, labelled as opinion",
                "body": "If I only need a social graphic and I can stay inside Canva’s free assets, I would stay on Canva Free. The $0 plan is real. Paying $199 to escape a bill I am not paying is a bad trade.\n\nIf I was already paying Canva Pro every year for resize, background removal and premium stock, and I do my work in a desktop browser, Plasfy is worth opening before the next renewal. The $199 figure is the one on their homepage today. I would confirm the tablet limitation first. I would not buy it from a “closes this page and the price goes up” banner without reading the refund terms.\n\nIf I needed brand kits, team approvals, a social planner, or an Education plan, Plasfy’s homepage does not document those as Canva documents them. I would not migrate a team on a feature list I cannot see.",
            },
            {
                "heading": "What I did not check",
                "body": "I did not create a paid Plasfy account, so I cannot verify that every item on the $199 card is actually unlocked. I did not test export quality, the AI background remover, or the commercial licence against a real client job. I did not time a design in both editors.\n\nI also did not copy Plasfy’s testimonial block. Testimonials on a sales page are not a source.\n\nIf you need a simpler free editor with no account at all, that is a different product. Polotno Studio is the one on this site that still matches that sentence.",
            },
        ],
        "sources": [
            {"name": "Plasfy homepage (checked 23 August 2026)", "url": "https://plasfy.com/"},
            {"name": "Canva — Plans and pricing", "url": "https://www.canva.com/pricing/"},
            {"name": "Plasfy vs Canva blog post (password-protected on 23 August 2026)", "url": "https://plasfy.com/blog/plasfy-vs-canva-full-review/"},
        ],
    },
    {
        "id": "pixlr-vs-canva",
        "slug": "pixlr-vs-canva",
        "title": "Pixlr vs Canva: Photo Editor or Design Tool",
        "seoTitle": "Pixlr vs Canva: Photo Editor or Design Tool",
        "excerpt": "People still search “Pixlr X vs Canva.” Pixlr’s own site now leads with Express, Editor and AI tools. Canva is still a template product. I checked both official pricing pages on 23 August 2026.",
        "category": "App Alternatives",
        "categorySlug": "app-alternatives",
        "tags": ["pixlr", "pixlr-x", "canva", "photo-editing", "alternatives"],
        "readingTime": "7 min read",
        "hero": HERO,
        "content": [
            {
                "heading": "The name has moved. The job has not.",
                "body": "If you typed “Pixlr X alternative to Canva,” you are not lost. You are a year or two behind Pixlr’s own navigation.\n\nOn 23 August 2026, pixlr.com does not lead with “Pixlr X.” The public products are Pixlr Express, Pixlr Editor, an image generator, an instruct editor, and a stack of AI tools: background remover, object remover, generative fill, upscaler, face swap, collage, video generator. The homepage line is “Free AI Photo Editor & Image Generator.”\n\nThat is a different job from Canva. Canva is a template-and-brand design product. Pixlr is a photo editor that has grown an AI generation layer. Comparing them as if they were two copies of the same app is how you pick the wrong one.",
            },
            {
                "heading": "What Pixlr actually charges",
                "body": "Pixlr’s official pricing page lists paid plans. I am quoting that page, not a review blog.\n\nPlus is $2.49 a month, or $1.99 a month billed yearly. Official Plus inclusions: ad-free, unlimited saves, one concurrent AI generation, 80 monthly AI credits.\n\nPremium is $9.99 a month, or $7.99 a month billed yearly. Official extras: access to all image, video and audio models, four concurrent AI generations, 1,000 monthly AI credits, private mode for AI generations, and a larger library of fonts, templates, elements and animations.\n\nUltra starts at $24.99 a month, or $19.99 billed yearly, and advertises unlimited “fast” image generations subject to fair use. Ultra MAX is $49.99 a month, or $39.99 yearly, and doubles the Ultra credit pile.\n\nPixlr also sells AI credit packs. Subscription credits reset on renewal. Credit-pack credits, they say, do not expire. Cancel, and subscription credits go to zero. They state they cannot process subscription refunds once payment has gone through.",
            },
            {
                "heading": "The free plan, without inventing the daily number",
                "body": "Pixlr’s marketing homepage still says you can edit and generate online for free. The paid Plus plan, on the same company’s pricing page, sells “Ad-Free” and “Unlimited saves” as the first two bullets.\n\nThose two bullets only make sense if the free editor has ads and a save cap. I am comfortable writing that. I am not comfortable writing “three saves a day” or “five saves a day,” because that number is not on the official pricing page I checked. Third-party reviews disagree with each other. When a company will not print the cap, I will not invent it.\n\nIf you need to know the exact free save limit, open Pixlr, make a file, and watch what the save button does. That is a worse sentence than a confident integer. It is also the true one.",
            },
            {
                "heading": "What Canva is, on its own pricing page",
                "body": "Canva Free is still US$0, with 1.6 million+ templates, 4.7 million+ media items, a three-colour Brand Kit and 5GB of storage. Pro is US$180 a year on the yearly toggle I checked. Those figures live on canva.com/pricing and exclude tax.\n\nCanva’s paid tools that matter for this comparison are the design ones: Magic Resize, background removal, Brand Kits, a social planner, collaboration. Pixlr’s paid tools that matter are the photo and generation ones: unlimited saves, more AI credits, private generations, model access.\n\nIf your Tuesday is “resize this Instagram post for Stories and keep the brand colours,” that is Canva. If your Tuesday is “heal this portrait, cut the background, upscale it, generate a new sky,” that is Pixlr.",
            },
            {
                "heading": "Beginners get sold the wrong comparison",
                "body": "A lot of “Pixlr X vs Canva for beginners” pieces treat both as first design apps. Only one of them is built as a first design app.\n\nCanva’s free editor assumes you will start from a template. Pixlr Express is closer to a simplified photo surface. Pixlr Editor is closer to a layered retouching surface. None of those three sentences makes Pixlr a Canva clone.\n\nIf you have never designed anything and you need a birthday flyer this afternoon, I would open Canva Free. If you already take photos on your phone and you want a browser editor that is not Photoshop, I would open Pixlr Express and stay on the free tier until the save cap or the ads actually annoy you. Then Plus at $1.99 a month yearly is the documented escape hatch.",
            },
            {
                "heading": "How I would choose, labelled as opinion",
                "body": "I would not cancel Canva Pro to move a brand system into Pixlr. Pixlr’s pricing page does not document Brand Kits, team approvals or a social calendar the way Canva does.\n\nI would not pay Canva Pro just to retouch photographs. That is the wrong product.\n\nIf I needed both jobs — templates for the site, retouching for the pictures — I would use both free tiers until one of them charged me for a specific unlock. That is cheaper than picking a winner in a blog comment.\n\nI have not timed a full client edit in Pixlr Editor for this piece. I am not going to invent field notes.",
            },
            {
                "heading": "What “Pixlr X” searches should do now",
                "body": "Search for Pixlr X if that is the name you know. Then look at what Pixlr is shipping under Express and Editor, because that is the product that still exists.\n\nDo not buy a plan from a 2023 screenshot. Plus, Premium and Ultra on pixlr.com/pricing are the live ladder. Canva’s live ladder is on canva.com/pricing. Both pages have moved in the last year. Open them.",
            },
        ],
        "sources": [
            {"name": "Pixlr — Pricing and plans", "url": "https://pixlr.com/pricing/"},
            {"name": "Pixlr homepage", "url": "https://pixlr.com/"},
            {"name": "Canva — Plans and pricing", "url": "https://www.canva.com/pricing/"},
        ],
    },
    {
        "id": "polotno-studio-vs-canva",
        "slug": "polotno-studio-vs-canva",
        "title": "Polotno Studio vs Canva: Still Free, Still Smaller",
        "seoTitle": "Polotno Studio vs Canva: Still Free, Still Smaller",
        "excerpt": "Older posts call Polotno a no-signup Canva killer. Newer posts imply the free ride ended. I checked Polotno’s own pages on 23 August 2026. Studio is still free. The paid product is a different thing.",
        "category": "App Alternatives",
        "categorySlug": "app-alternatives",
        "tags": ["polotno", "canva", "design-tools", "privacy", "alternatives"],
        "readingTime": "7 min read",
        "hero": HERO,
        "content": [
            {
                "heading": "The discrepancy is the story",
                "body": "Polotno is the tool people describe two opposite ways.\n\nOne version: a free, no-account, no-ads design editor you open in a browser and export from. The other version: a paid product, because something changed.\n\nBoth sentences can be true at once if you mix up two products with the same first name. I opened Polotno’s official pages on 23 August 2026. Studio and the SDK are not the same offer.",
            },
            {
                "heading": "What Polotno Studio still is",
                "body": "Polotno Studio is at studio.polotno.com, also linked from polotno.com/studio. The official “free, no sign-up, privacy-friendly” page is specific.\n\nYou can use every core feature without logging in. The editor loads in the browser. Exports — they list PNG, JPG, PDF, GIF and MP4 — render on your device and save locally. Designs stay in the browser session unless you choose to save to an online workspace. Accounts are optional, and only for cloud save across sessions.\n\nThey also document the small leaks that “nothing leaves your machine” marketing usually skips. The editor may load fonts from Google Fonts. It may use lightweight analytics depending on your browser and ad-blocker. They say those requests do not send your design data.\n\nThat is still a free editor. I did not hit a paywall opening the studio. I am not going to claim I designed a 40-page brand book in it.",
            },
            {
                "heading": "What changed is the other product",
                "body": "Polotno the company also sells Polotno SDK: a white-label editor you embed in your own app, with a programmatic API. That is a developer product. The public marketing points at a pricing page for API keys and lists business customers.\n\nIf you are a person who wants to make a thumbnail, you do not need the SDK. If a comparison site says “Polotno is paid-only,” check whether they are pricing the SDK. Pricing the SDK as if it were Studio is how the “free ride ended” rumour gets written down as fact.\n\nI am not putting an SDK dollar figure on this page. That number is for a different buyer, and it is not what makes Studio a Canva alternative.",
            },
            {
                "heading": "What you give up if you leave Canva",
                "body": "Canva Free, on canva.com/pricing today, still claims 1.6 million+ templates, 4.7 million+ media items, a Brand Kit and 5GB of cloud storage. Pro adds resize, translate, background removal, five Brand Kits, a social planner and 100GB.\n\nPolotno Studio’s official pitch is the opposite shape: start immediately, keep the file on the device, skip the account. It does not claim a Canva-scale template or stock library on the page I read. Older write-ups that call it “open source Canva” are also sloppy. The Studio is a free web app. The company’s GitHub exists. That is not the same as “the whole Canva clone is MIT and you should self-host it instead of opening studio.polotno.com.”\n\nYou also give up Canva’s collaboration, Brand Kits, Education plan, print pipeline and mobile apps — unless Polotno has added them since this sentence was written. They were not on the privacy-friendly feature page I used as a source.",
            },
            {
                "heading": "Who this is actually for",
                "body": "Polotno’s own page names the audience: schools, kids, people who do not want another account, teams with strict IT policies, and anyone who wants to sketch an idea without handing over an email.\n\nThat is a good list. It is also a smaller list than “everyone who is tired of Canva.”\n\nIf you need to stay signed out, export a PNG and close the tab, Studio still does that. If you need a shared brand folder and a colleague in another city, Canva is still the product that documents that job.",
            },
            {
                "heading": "How I would choose, labelled as opinion",
                "body": "For a one-off graphic where I do not want a new login, I would try Polotno Studio before I created another SaaS account. The official no-signup claim is the whole point.\n\nFor anything I expect to reopen next month, I would use Canva Free or accept Polotno’s optional account. Local-only work dies when the browser profile dies. That is not a moral failing. It is how browsers work.\n\nI would not tell a small business to “switch from Canva to Polotno” as a strategy. I would tell them to open Studio once and see whether the canvas is enough. If it is not, they have lost ten minutes, not a migration.",
            },
            {
                "heading": "What I did not check",
                "body": "I did not measure the template count. I did not test video export length or PDF print marks. I did not review the SDK licence. I did not create a Polotno cloud account, so I cannot describe that save flow from use.\n\nThe useful fact that survives those gaps: on 23 August 2026, the no-signup Studio is still there. The paid thing with the same name is for people building software, not for people leaving Canva Pro.",
            },
        ],
        "sources": [
            {"name": "Polotno — Free, no sign-up, privacy-friendly design editor", "url": "https://polotno.com/for-creators/features/free-privacy-friendly"},
            {"name": "Polotno Studio", "url": "https://polotno.com/studio"},
            {"name": "Canva — Plans and pricing", "url": "https://www.canva.com/pricing/"},
        ],
    },
    {
        "id": "lyra-vs-spotify",
        "slug": "lyra-vs-spotify",
        "title": "Lyra vs Spotify: Free Player, Not a Catalogue",
        "seoTitle": "Lyra vs Spotify: Free Player, Not a Catalogue",
        "excerpt": "Lyra is a real app with store listings and a polished site. Its makers have said the streams are YouTube. Spotify in Nigeria is ₦1,600 a month for Premium Individual. Those are not the same product.",
        "category": "App Alternatives",
        "categorySlug": "app-alternatives",
        "tags": ["lyra", "spotify", "music", "android", "alternatives"],
        "readingTime": "8 min read",
        "hero": HERO,
        "content": [
            {
                "heading": "A free Spotify is usually a different pipe",
                "body": "When a new music app is free, has no ads, imports your Spotify playlists and still plays “everything,” the useful question is not “is the interface nice?” The useful question is “where is the audio coming from?”\n\nLyra is a real product. On 23 August 2026, lyramusic.app is live. It links to the App Store, Google Play, the Microsoft Store, and desktop builds for Windows, Mac and Linux. The site advertises millions of tracks, playlists, synced lyrics, CarPlay and Android Auto, no account required to start, and “we don’t track your listening habits to sell ads.”\n\nThat is enough to write about. It is not enough to call Lyra a licensed Spotify replacement.",
            },
            {
                "heading": "What Lyra’s own site claims",
                "body": "The homepage, today: stream millions of tracks, create playlists, live social listening, high-quality audio, synced lyrics, import your own tracks from Dropbox, Google Drive and OneDrive, equalizer, crossfade, gapless playback, sleep timer, Last.fm scrobbling, optional account for sync, podcasts, and clients on iOS, Android, desktop, car and the web.\n\nIt also shows store badges and a GitHub releases path for the desktop builds. If you install it, install it from those official links. I am not going to send you to a random APK blog. Those pages are how people collect a second, worse problem.",
            },
            {
                "heading": "What Lyra’s makers have said about the catalogue",
                "body": "The marketing site does not lead with the licensing sentence. The team has, in public.\n\nOn Product Hunt, answering how a free, ad-free music app pays artists, a Lyra maker wrote that the app is based on YouTube, that every stream is a standard YouTube playback, that each listen counts as a YouTube view, and that YouTube handles licensing, copyright and royalties. On Reddit, the same project account has described the app as working like a browser / webview, and has said offline music is not offered because the app is based on YouTube.\n\nI am treating those as the makers’ own description of the pipe. I am not treating lyramusic.app’s quieter homepage as a contradiction that erases them.\n\nIf the audio is YouTube, Lyra is a YouTube listening client with a music-first interface and a playlist importer. That can be a good client. It is not a second Spotify catalogue.",
            },
            {
                "heading": "What Spotify actually sells in Nigeria",
                "body": "Spotify’s Nigeria Premium page, checked 23 August 2026:\n\nFree still exists. It is the ad-supported plan. Premium Individual is ₦1,600 a month after a ₦0 three-month offer for people who have not tried Premium before. That offer ends 23 September 2026. Student is ₦800 a month after a one-month ₦0 trial, for eligible students. Duo is ₦2,100 a month for two people at the same address. Family is ₦2,500 a month for up to six people at the same address, with parental controls for the plan manager.\n\nOfficial Premium extras they list against Free: ad-free listening, offline downloads, play songs in any order, higher audio quality, listen with friends in real time, organise the queue.\n\nThose naira figures are from spotify.com/ng/premium. They are not US$12.99. If you are in Lagos, use the Nigeria page.",
            },
            {
                "heading": "Side by side, without pretending they match",
                "body": "Catalogue: Spotify licenses a streaming catalogue and pays through that system. Lyra’s makers say the stream is YouTube. Missing on Spotify can exist as an upload on YouTube. Missing on YouTube will not appear in Lyra just because Spotify has it.\n\nCost: Spotify Free is $0 with ads. Spotify Premium Individual in Nigeria is ₦1,600 a month. Lyra’s site presents listening as free. The team has also said there is an optional upgrade for higher audio quality. I did not find a public price for that upgrade on the homepage I checked, so I am not inventing one.\n\nOffline: Spotify documents downloads on Premium. Lyra’s makers have said offline is not offered on the YouTube pipe.\n\nAccount: Spotify needs one. Lyra says you can start without one; an account is for sync.\n\nCars and speakers: both claim car support. Spotify also documents a long hardware list — watches, TVs, consoles, smart speakers. Lyra claims CarPlay, Android Auto, AirPlay and Google Cast. I have not tested either claim in a car for this piece.\n\nPodcasts: both advertise them. I did not audit either library.",
            },
            {
                "heading": "The question people actually type",
                "body": "“Why don’t people use Lyra instead of Spotify?” is a real search, and it has a boring answer.\n\nPeople stay on Spotify because the catalogue, the offline cache, the family plan, the wrapped-style recap and the speaker in the corner of the room are one account. People try Lyra because ₦1,600 is a bill, Spotify Free has ads, and a clean player that imports playlists feels like relief.\n\nRelief is not the same as a replacement. If YouTube takes the stream down, Lyra cannot play it. If Google or Apple decide a YouTube-wrapper music app is a problem — they have decided that about other apps — the store listing is not a constitutional right. I am not forecasting a takedown. I am saying a YouTube client has a different risk than a licensed service.",
            },
            {
                "heading": "How I would choose, labelled as opinion",
                "body": "If I want a licensed catalogue, offline downloads and a family plan in Nigeria, I would pay Spotify or use Spotify Free and live with the ads. ₦1,600 is the official Individual number today.\n\nIf I already live in YouTube for music and I want a nicer shell than the YouTube app, I would try Lyra from the official store listing and keep my expectations at “YouTube in a music skin.” I would not move a family’s offline library onto it.\n\nI would not install a “Spotify Premium APK” or a third-party Lyra APK. That is how you donate a password. Lyra’s own site already links the stores.\n\nI have not used Lyra as my daily player. I am not going to invent battery-life notes or a sound-quality score.",
            },
            {
                "heading": "What this page will not do",
                "body": "It will not tell you Lyra is “Spotify but free.” It will not list cracked Spotify clients. It will not treat Suno, or any AI music generator, as a Spotify alternative — that is a different job, and it is not on this page.\n\nIt will also not stay current forever. Store availability, YouTube rules and Spotify’s naira price all move. The source links are below. If you are about to cancel a family plan, open those pages again rather than this article.",
            },
        ],
        "sources": [
            {"name": "Lyra Music homepage", "url": "https://lyramusic.app/"},
            {"name": "Lyra Music on Product Hunt (makers: streams are YouTube playback)", "url": "https://www.producthunt.com/products/lyra-music"},
            {"name": "Spotify Premium — Nigeria", "url": "https://www.spotify.com/ng/premium/"},
            {"name": "Spotify Support — Premium plans (Nigeria prices)", "url": "https://support.spotify.com/ng/article/premium-plans/"},
        ],
    },
]


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def paras(text: str) -> str:
    chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
    return "".join(f"<p>{esc(c)}</p>" for c in chunks)


def desc_meta(excerpt: str, limit: int = 155) -> str:
    excerpt = " ".join(excerpt.split())
    if len(excerpt) <= limit:
        return excerpt
    cut = excerpt[:limit].rsplit(" ", 1)[0].rstrip(".,;:")
    return cut + "…"


def word_count(art: dict) -> int:
    return sum(len((b.get("heading", "") + " " + b.get("body", "")).split()) for b in art["content"])


def related_html(current: str) -> str:
    cards = []
    cards.append(
        f'<a class="vcat vcat-photo" href="/tech/app-alternatives/" style="--card-img:url(\'{HERO}\')">'
        f"<b>App alternatives we actually checked</b>"
        f"<span>Only the comparisons that survived a source check. The rest stayed in research.</span></a>"
    )
    for art in ARTICLES:
        if art["slug"] == current:
            continue
        cards.append(
            f'<a class="vcat vcat-photo" href="/tech/{art["slug"]}/" style="--card-img:url(\'{art["hero"]}\')">'
            f"<b>{esc(art['title'])}</b><span>{esc(art['excerpt'])}</span></a>"
        )
    return (
        '<section class="section"><div class="section-head"><h2>More app alternatives</h2></div>'
        f'<div class="vcat-grid">{"".join(cards)}</div></section>'
    )


def article_html(art: dict) -> str:
    url = f"{SITE}/tech/{art['slug']}/"
    title = art["seoTitle"]
    page_title = f"{title} | BRYME"
    desc = desc_meta(art["excerpt"])
    hero = art["hero"]
    abs_hero = SITE + hero
    body = "".join(f"<h2>{esc(b['heading'])}</h2>{paras(b['body'])}" for b in art["content"])
    sources = " · ".join(
        f'<a href="{esc(s["url"])}" rel="nofollow noopener">{esc(s["name"])}</a>' for s in art["sources"]
    )
    ld = [
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": art["title"],
            "description": art["excerpt"],
            "datePublished": CHECKED,
            "dateModified": CHECKED,
            "author": {
                "@type": "Person",
                "name": AUTHOR,
                "url": SITE + AUTHOR_URL,
                "jobTitle": "Writer — Make Money, Tech & AI, Sports",
            },
            "publisher": {"@type": "Organization", "name": "BRYME"},
            "mainEntityOfPage": url,
            "articleSection": art["category"],
            "image": abs_hero,
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "BRYME Tech & AI", "item": SITE + "/tech/"},
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": art["category"],
                    "item": SITE + "/tech/app-alternatives/",
                },
                {"@type": "ListItem", "position": 4, "name": art["title"], "item": url},
            ],
        },
    ]
    ld_json = json.dumps(ld, ensure_ascii=False, separators=(",", ":"))
    return (
        HEAD_CHROME
        + f"<title>{esc(page_title)}</title>"
        + f'<meta name="description" content="{esc(desc)}">'
        + f'<link rel="canonical" href="{url}">'
        + '<meta property="og:type" content="article">'
        + '<meta property="og:site_name" content="BRYME">'
        + f'<meta property="og:title" content="{esc(page_title)}">'
        + f'<meta property="og:description" content="{esc(desc)}">'
        + f'<meta property="og:url" content="{url}">'
        + f'<meta property="og:image" content="{abs_hero}">'
        + '<meta property="og:image:type" content="image/jpeg">'
        + '<meta property="og:image:alt" content="BRYME">'
        + f'<meta name="twitter:image" content="{abs_hero}">'
        + '<meta name="twitter:image:alt" content="BRYME">'
        + '<meta name="twitter:card" content="summary_large_image">'
        + f'<meta name="twitter:title" content="{esc(page_title)}">'
        + f'<meta name="twitter:description" content="{esc(desc)}">'
        + '<link rel="stylesheet" href="/assets/site.css">'
        + f'<script type="application/ld+json">{ld_json}</script>'
        + HEADER
        + '<main class="shell">'
        + f'<div class="crumb"><a href="/">Home</a> / <a href="/tech/">BRYME Tech &amp; AI</a> / '
        + f'<a href="/tech/app-alternatives/">App Alternatives</a> / {esc(art["title"])}</div>'
        + f'<section class="article-hero article-hero-photo" style="--hero-img:url(\'{hero}\')">'
        + f'<div class="eyebrow">{esc(art["category"])}</div>'
        + f"<h1>{esc(art['title'])}</h1>"
        + f'<p class="lead">{esc(art["excerpt"])}</p>'
        + f'<div class="article-meta"><span><a href="{AUTHOR_URL}" rel="author">{esc(AUTHOR)}</a></span>'
        + f'<span>{CHECKED}</span><span>{esc(art["readingTime"])}</span></div></section>'
        + f'<article class="prose article-body">{body}</article>'
        + '<section class="sp-source"><h2>Sources</h2>'
        + f"<p>{sources}</p>"
        + f'<p class="sp-source-note">Figures were checked against the sources above on {CHECKED}. '
        + "Published terms change — confirm on the provider's own site before relying on them.</p></section>"
        + related_html(art["slug"])
        + "</main>"
        + FOOTER
    )


def hub_html() -> str:
    url = f"{SITE}/tech/app-alternatives/"
    title = "App Alternatives We Actually Checked | BRYME"
    desc = "Plasfy, Pixlr, Polotno and Lyra — comparison pages only after a source check. The rest stayed in research."
    cards = []
    for art in ARTICLES:
        cards.append(
            f'<a class="vcat vcat-photo" href="/tech/{art["slug"]}/" style="--card-img:url(\'{art["hero"]}\')">'
            f"<b>{esc(art['title'])}</b><span>{esc(art['excerpt'])}</span></a>"
        )
    ld = [
        {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": "App Alternatives",
            "description": desc,
            "url": url,
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "BRYME Tech & AI", "item": SITE + "/tech/"},
                {"@type": "ListItem", "position": 3, "name": "App Alternatives", "item": url},
            ],
        },
    ]
    body = """
<section class="section">
  <div class="prose article-body">
    <p>An alternatives page is easy to fake. Pick a big app, scrape a directory, publish ten names. BRYME will not do that.</p>
    <p>For every candidate I asked the same six questions: is the product real and online today; is it actually an alternative to the thing people search; does it have a free or freemium path, or a clear price; are people searching the comparison; are the current results weak or dishonest; and can this page say something the official pages do not.</p>
    <p>Plasfy, Pixlr, Polotno Studio and Lyra cleared enough of that bar to publish. Figma, Piccolo, Overtune, Lux Offline and Suno did not — not as the comparisons they get filed under. The notes are at the bottom, not dressed up as reviews.</p>
  </div>
  <div class="vcat-grid" style="margin-top:22px">""" + "".join(cards) + """</div>
</section>
<section class="section">
  <div class="section-head"><h2>Still in research</h2></div>
  <div class="prose article-body">
    <p><b>Figma</b> is real and widely used. It is a product-design and collaboration tool. Calling it a free Canva replacement is the wrong sentence, so there is no “Figma vs Canva” page here yet.</p>
    <p><b>Piccolo.ai</b> stayed in the research bucket. I could not stand up an official product, price and current availability I was willing to put my name under on 23 August 2026.</p>
    <p><b>Overtune</b> is a name collision. One result is an AI beatmaker. Another trail leads to OuterTune, a YouTube Music client whose own GitHub now says it is no longer in active development. That is not a Spotify alternative I will publish.</p>
    <p><b>Lux Offline</b> did not resolve to an official, current Spotify alternative I could verify. A listing on an alternatives site is not a source.</p>
    <p><b>Suno</b> generates music with AI. That is a different job from playing a licensed catalogue. It will not appear on a Spotify alternatives page.</p>
  </div>
</section>"""
    return (
        HEAD_CHROME
        + f"<title>{esc(title)}</title>"
        + f'<meta name="description" content="{esc(desc)}">'
        + f'<link rel="canonical" href="{url}">'
        + '<meta property="og:type" content="website">'
        + '<meta property="og:site_name" content="BRYME">'
        + f'<meta property="og:title" content="{esc(title)}">'
        + f'<meta property="og:description" content="{esc(desc)}">'
        + f'<meta property="og:url" content="{url}">'
        + f'<meta property="og:image" content="{SITE}{HERO}">'
        + '<meta property="og:image:type" content="image/jpeg">'
        + '<meta property="og:image:alt" content="BRYME">'
        + f'<meta name="twitter:image" content="{SITE}{HERO}">'
        + '<meta name="twitter:image:alt" content="BRYME">'
        + '<meta name="twitter:card" content="summary_large_image">'
        + f'<meta name="twitter:title" content="{esc(title)}">'
        + f'<meta name="twitter:description" content="{esc(desc)}">'
        + '<link rel="stylesheet" href="/assets/site.css">'
        + f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(",", ":"))}</script>'
        + HEADER
        + '<main class="shell">'
        + '<div class="crumb"><a href="/">Home</a> / <a href="/tech/">BRYME Tech &amp; AI</a> / App Alternatives</div>'
        + f'<section class="hero vhero vhero-tech vhero-photo" data-vertical="tech" style="--hero-img:url(\'{HERO}\')">'
        + '<div class="eyebrow">🤖 BRYME Tech &amp; AI · App Alternatives</div>'
        + "<h1>App alternatives we actually checked</h1>"
        + '<p class="lead">Comparison pages only when the product is real, active, and genuinely comparable. Four passed. The rest stayed in research.</p>'
        + "</section>"
        + body
        + '<section class="section core-hubs" data-core-hubs><div class="section-head"><h2>Also on BRYME</h2></div>'
        + '<p class="section-note">The main sections of the site. Open the next one that matches what you came for.</p>'
        + '<div class="vchips">'
        + '<a class="vchip vchip-entertainment" href="/entertainment/"><span class="vchip-emoji">🎬</span><span class="vchip-name">Entertainment</span><span class="vchip-tag">Movies, series, anime and articles</span></a>'
        + '<a class="vchip vchip-sports" href="/sports/"><span class="vchip-emoji">⚽</span><span class="vchip-name">Sports</span><span class="vchip-tag">Football covered properly</span></a>'
        + '<a class="vchip vchip-make-money" href="/make-money/"><span class="vchip-emoji">💰</span><span class="vchip-name">Make Money</span><span class="vchip-tag">Verified writing markets and honest guides</span></a>'
        + '<a class="vchip vchip-tech" href="/tech/"><span class="vchip-emoji">🤖</span><span class="vchip-name">Tech &amp; AI</span><span class="vchip-tag">Practical tools, no theatre</span></a>'
        + "</div></section></main>"
        + FOOTER
    )


def write_pages() -> None:
    for art in ARTICLES:
        dest = ROOT / "tech" / art["slug"] / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(article_html(art), encoding="utf-8")
        print("wrote", dest.relative_to(ROOT), "words", word_count(art))
    hub = ROOT / "tech" / "app-alternatives" / "index.html"
    hub.parent.mkdir(parents=True, exist_ok=True)
    hub.write_text(hub_html(), encoding="utf-8")
    print("wrote", hub.relative_to(ROOT))


def upsert_tech_articles() -> None:
    path = ROOT / "content" / "tech-articles.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    by_id = {a["id"]: i for i, a in enumerate(data)}
    for art in ARTICLES:
        rec = {
            "id": art["id"],
            "slug": art["slug"],
            "title": art["title"],
            "seoTitle": art["seoTitle"],
            "excerpt": art["excerpt"],
            "category": art["category"],
            "categorySlug": art["categorySlug"],
            "tags": art["tags"],
            "relatedMovieSlugs": [],
            "status": "published",
            "author": AUTHOR,
            "publishedAt": CHECKED,
            "updatedAt": CHECKED,
            "readingTime": art["readingTime"],
            "content": art["content"],
            "sources": art["sources"],
            "sourcesCheckedOn": CHECKED,
        }
        if art["id"] in by_id:
            data[by_id[art["id"]]] = rec
        else:
            data.append(rec)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("tech-articles.json now", len(data), "entries")


def patch_tech_landing() -> None:
    path = ROOT / "tech" / "index.html"
    html_txt = path.read_text(encoding="utf-8")
    tile = (
        '<a class="sp-comp-card sp-comp-wide" href="/tech/app-alternatives/" '
        f"style=\"--card-img:url('{HERO}')\"><em>Compare</em><b>App Alternatives</b>"
        "<span>Plasfy, Pixlr, Polotno, Lyra — only the comparisons that survived a source check.</span></a>"
    )
    if "/tech/app-alternatives/" not in html_txt:
        html_txt = html_txt.replace(
            '<div class="sp-comp-grid">',
            '<div class="sp-comp-grid">\n      ' + tile + "\n      ",
            1,
        )
    feat = """
<section class="sp-feat tech-feat" aria-label="App alternatives">
  <div class="shell">
    <div class="section-head"><div><div class="eyebrow">Comparisons</div><h2>App alternatives</h2></div><a class="more" href="/tech/app-alternatives/">All checked</a></div>
    <div class="sp-feat-grid">
      <a class="sp-feat-main" href="/tech/lyra-vs-spotify/" style="--card-img:url('HERO')">
        <span class="tag">Music</span>
        <h2>Lyra vs Spotify</h2>
        <p>A real app. A YouTube pipe. Not a licensed catalogue. Nigeria Premium is ₦1,600.</p>
      </a>
      <div class="sp-feat-side">
        <a href="/tech/plasfy-vs-canva/" style="--card-img:url('HERO')">
          <span class="tag">Design</span>
          <h3>Plasfy vs Canva</h3>
          <p>$199 lifetime on Plasfy’s homepage. Canva still has a $0 plan.</p>
        </a>
        <a href="/tech/polotno-studio-vs-canva/" style="--card-img:url('HERO')">
          <span class="tag">Free editor</span>
          <h3>Polotno Studio vs Canva</h3>
          <p>Still free, still no signup. The paid product is the SDK.</p>
        </a>
      </div>
    </div>
  </div>
</section>
""".replace("HERO", HERO)
    if 'aria-label="App alternatives"' not in html_txt:
        html_txt = html_txt.replace(
            '<section class="sp-comp tech-comp hub-guides">',
            feat + '\n<section class="sp-comp tech-comp hub-guides">',
            1,
        )
    # keep the existing featured block; just make sure nav chip exists
    if 'href="/tech/app-alternatives/"' in html_txt and ">App alternatives<" not in html_txt.replace(
        "App Alternatives", "App alternatives"
    ):
        html_txt = html_txt.replace(
            '<a href="/tech/cybersecurity/">Stay safe</a>',
            '<a href="/tech/app-alternatives/">App alternatives</a>\n      <a href="/tech/cybersecurity/">Stay safe</a>',
            1,
        )
    path.write_text(html_txt, encoding="utf-8")
    print("patched tech/index.html")


def patch_author() -> None:
    path = ROOT / "author" / "ibrahim-sodiq" / "index.html"
    html_txt = path.read_text(encoding="utf-8")
    needle = '<a class="vcat vcat-photo" href="/tech/where-to-host-website-for-free/"'
    cards = []
    for art in ARTICLES:
        href = f"/tech/{art['slug']}/"
        if href in html_txt:
            continue
        cards.append(
            f'<a class="vcat vcat-photo" href="{href}" style="--card-img:url(\'{art["hero"]}\')">'
            f"<b>{esc(art['title'])}</b><span>{esc(art['excerpt'])}</span></a>"
        )
    if cards:
        html_txt = html_txt.replace(needle, "".join(cards) + needle, 1)
        path.write_text(html_txt, encoding="utf-8")
        print("patched author page", len(cards), "cards")
    else:
        print("author page already has cards")


def patch_sitemap() -> None:
    path = ROOT / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    locs = re.findall(r"<loc>([^<]+)</loc>", text)
    add = [
        f"{SITE}/tech/app-alternatives/",
        f"{SITE}/tech/lyra-vs-spotify/",
        f"{SITE}/tech/pixlr-vs-canva/",
        f"{SITE}/tech/plasfy-vs-canva/",
        f"{SITE}/tech/polotno-studio-vs-canva/",
    ]
    new = [u for u in add if u not in locs]
    if not new:
        print("sitemap already has alternative URLs")
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
    if not any(v.get("slug") == "tech/app-alternatives" for v in verts):
        # insert after the main tech vertical if present
        rec = {
            "type": "tech",
            "title": "App Alternatives",
            "slug": "tech/app-alternatives",
            "description": "Plasfy, Pixlr, Polotno and Lyra — comparison pages only after a source check.",
        }
        idx = next((i for i, v in enumerate(verts) if v.get("slug") == "tech"), 0)
        verts.insert(idx + 1, rec)
        path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        print("search-index: added app-alternatives vertical")
    else:
        print("search-index already has vertical")


def main() -> None:
    write_pages()
    upsert_tech_articles()
    patch_tech_landing()
    patch_author()
    patch_sitemap()
    patch_search()
    for art in ARTICLES:
        print(f"  /tech/{art['slug']}/  title={len(art['seoTitle'] + ' | BRYME')}c  words={word_count(art)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Sourced ChatGPT/Claude alternative pages. Surgical — does not rebuild the site."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://bryme.onrender.com"
CHECKED = "2026-08-23"
HERO = "/assets/img/tech/hero-assistants.jpg"
HERO_PRIVACY = "/assets/img/tech/hero-privacy.jpg"
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
<p class="footer-note">BRYME · Discover what you love. Learn what you need. Find what's next. Trailer links lead to YouTube and viewing links lead to third parties.<small>Trending Now is editorially curated by BRYME — it is not live traffic data. Popular and Editor's Picks are independent rankings. Real user analytics will replace trending once the site has enough traffic. · Build 2026-08-23 07:45 UTC</small></div></footer><script>window.BRYME_BASE=''</script><script src="/assets/site-app.js"></script></body></html>"""

ARTICLES = [
    {
        "id": "chatgpt-claude-alternatives",
        "slug": "chatgpt-claude-alternatives",
        "title": "Free and Cheap ChatGPT Alternatives We Actually Checked",
        "seoTitle": "Free and Cheap ChatGPT Alternatives We Checked",
        "excerpt": "ChatGPT Plus is $20 a month. Claude Pro is $20 a month, or $17 if you pay a year up front. I opened the official pages for the big free and cheap names on 23 August 2026. Three earned their own pages. The rest stay in research.",
        "category": "AI Assistants",
        "categorySlug": "ai-assistants",
        "tags": ["chatgpt", "claude", "gemini", "deepseek", "arena", "alternatives"],
        "readingTime": "8 min read",
        "hero": HERO,
        "content": [
            {
                "heading": "Leave a product, not a brand",
                "body": "“ChatGPT alternative” usually means one of three jobs: a free chat box, a cheaper paid plan, or a different pipe — search with citations, a Microsoft account, a multi-model arena.\n\nThose are not the same product. A listicle that ranks Gemini, DeepSeek, Copilot, Perplexity and Arena as if they were ten flavours of Plus is how people pick the wrong bill.\n\nI opened the official pricing and product pages on 23 August 2026. Dollar figures below are what those pages print, mostly US. A Nigerian checkout can show another number. I am not inventing naira prices I did not see.",
            },
            {
                "heading": "What you are actually leaving",
                "body": "ChatGPT still has a Free plan. The live pricing page lists unlimited text chats with GPT-5.6 Luna, subject to abuse guardrails, and limited uploads, images, voice, deep research, memory and Codex. OpenAI’s own 16 January 2026 post put ChatGPT Go at $8 a month in the US and said that plan may include ads. Official help, updated this month, still prices Plus at $20 a month, billed monthly, with no annual option. Pro exists as a higher tier. The January post said $200 a month. The live pricing table I opened today did not print a dollar figure in the HTML, so I am not locking Pro to either $100 or $200 on this page.\n\nClaude’s official pricing page: Free is $0. Pro is $17 a month if you pay $200 a year up front, or $20 if you pay monthly. Max starts at $100 a month. Official help matches the $20 monthly US figure and says Pro is at least five times the free usage per session, with a weekly cap on top. Claude Code and Cowork sit on Pro, not Free.\n\nIf you only use Free ChatGPT or Free Claude, you are not “escaping a $20 bill.” You are shopping for a different free box.",
            },
            {
                "heading": "The three that earned their own pages",
                "body": "Gemini is Google’s assistant. Official subscriptions page: Free is $0 with a Google account. Google AI Plus is $4.99 a month — the cheapest official paid step I found among the big consumer assistants. Google AI Pro is $19.99 a month. Ultra starts at $99.99. That is a real ChatGPT-shaped product with a cheaper first upgrade.\n\nDeepSeek’s homepage, today, offers “Chat Now — Free access to DeepSeek.” The chat product is advertised as free. The API is a different product with its own token prices. Do not mix them up.\n\nArena.ai is the one people keep filing under the wrong heading. It is a public model arena and an Agent Mode, not a single-vendor assistant with a Plus plan. The official homepage is explicit about privacy: prompts go to third-party providers and may be disclosed publicly. That page is written up separately, including the fact that this research was done in Arena Agent Mode.",
            },
            {
                "heading": "Big names that are real, but a different job",
                "body": "Microsoft Copilot has a free chat at copilot.microsoft.com. Microsoft’s own support page separates that free Copilot from Copilot inside Microsoft 365. The free one is general Q&A and web tasks. The Office-embedded product is a different licence. I am not publishing “Copilot is free ChatGPT” as if Word and Excel came with the website.\n\nPerplexity’s official pricing hub: Free is $0, search with citations, limited daily use. Pro is $20 a month. Max is $200 a month. That is a cited-research product that also routes across other companies’ models. At $20 it is not cheaper than ChatGPT Plus. The free tier is the interesting part, if what you want is sources, not a writing partner.\n\nClaude itself is a ChatGPT alternative, and ChatGPT is a Claude alternative. Both have free tiers. Both charge $20 a month for the everyday paid plan. Switching from Plus to Pro Claude is a lateral move, not a cheaper one.",
            },
            {
                "heading": "How I would choose, labelled as opinion",
                "body": "If I already live in Gmail and Drive and I want a $0 box, I would try Gemini Free before I opened a fourth account.\n\nIf I was about to pay $20 for Plus just to send more messages, I would look at ChatGPT Go at $8 US, or Google AI Plus at $4.99, and read the current inclusions — Go may carry ads — before I paid Plus.\n\nIf I wanted one vendor’s memory, custom GPTs and a stable app, I would stay on ChatGPT or Claude and stop shopping “alternatives.”\n\nIf I wanted to compare models on one prompt, I would use Arena and I would not paste anything I would not want a lab to see.\n\nI have not run a week of paid work through DeepSeek or Gemini Plus for this piece. I am not going to invent quality scores.",
            },
            {
                "heading": "Still in research",
                "body": "Grok is real. I did not get a current official consumer price I was willing to print as “cheap.” SuperGrok figures on third-party blogs are not a source.\n\nMistral’s public chat now presents as Vibe. I did not get a clean official free/paid table from that surface today, so there is no Mistral page.\n\nMeta AI is free inside Facebook, Instagram and WhatsApp. That is a social assistant, not a ChatGPT work replacement. No page.\n\nPoe, HuggingChat, Pi and Character.AI were not checked to the same standard. They stay off this list until they are.\n\nArena PLM at arenasolutions.com is a product-lifecycle tool from PTC. It is not this Arena. Do not confuse them.",
            },
        ],
        "sources": [
            {"name": "OpenAI — Introducing ChatGPT Go (16 January 2026)", "url": "https://openai.com/index/introducing-chatgpt-go/"},
            {"name": "OpenAI Help — What is ChatGPT Plus? ($20/month)", "url": "https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus"},
            {"name": "ChatGPT — Pricing", "url": "https://chatgpt.com/pricing/"},
            {"name": "Claude — Plans & Pricing", "url": "https://claude.com/pricing"},
            {"name": "Anthropic Help — What is the Pro plan?", "url": "https://support.claude.com/en/articles/8325606-what-is-the-pro-plan"},
            {"name": "Google — Gemini subscriptions", "url": "https://gemini.google/subscriptions/"},
            {"name": "DeepSeek homepage", "url": "https://www.deepseek.com/en/"},
            {"name": "Arena.ai homepage", "url": "https://arena.ai/"},
            {"name": "Microsoft Support — Copilot free vs Microsoft 365", "url": "https://support.microsoft.com/en-us/microsoft-365-copilot/what-s-the-difference-between-microsoft-copilot-free-and-copilot-in-microsoft-365"},
            {"name": "Perplexity — Pricing", "url": "https://www.perplexity.ai/hub/pricing"},
        ],
    },
    {
        "id": "arena-ai-vs-chatgpt",
        "slug": "arena-ai-vs-chatgpt",
        "title": "Arena.ai vs ChatGPT: A Free Arena, Not a Plus Plan",
        "seoTitle": "Arena.ai vs ChatGPT: Free Arena, Not a Plus Plan",
        "excerpt": "Arena.ai is a real product. It is not ChatGPT with a different logo. Official pages: multi-model chat, a leaderboard, Agent Mode, and a privacy notice that says your prompts may go public. This page was researched in Arena Agent Mode. That belongs on the record.",
        "category": "AI Assistants",
        "categorySlug": "ai-assistants",
        "tags": ["arena", "chatgpt", "claude", "privacy", "alternatives"],
        "readingTime": "8 min read",
        "hero": HERO_PRIVACY,
        "content": [
            {
                "heading": "Say the conflict of interest first",
                "body": "I researched and drafted this page inside Arena Agent Mode on 23 August 2026. Arena is the platform. ChatGPT and Claude are two of the model families it can route to. That is useful and it is also a bias. I am not going to write a brochure for the desk I am sitting at.\n\nThe useful comparison is not “which chatbot is nicer.” It is whether Arena is the same job as ChatGPT or Claude. On the official pages, it is not.",
            },
            {
                "heading": "What Arena.ai actually is",
                "body": "arena.ai titles itself “The Official AI Ranking & LLM Leaderboard.” The live site offers a new chat, a leaderboard, search, Battle Mode, and Agent Mode at arena.ai/agent. Agent Mode’s public page is a prompt box: files, a GitHub connect, “what would you like to do?” Structured data on that page lists web search, code execution, deep research and model comparison, and an offer price of $0.\n\nI did not find a consumer Plus/Pro ladder on arena.ai comparable to ChatGPT or Claude. I am not going to invent one. If a paid Agent plan exists behind a login, it is not on the public pages I used as sources.\n\nThere is a different company, Arena PLM at arenasolutions.com, owned around PTC. That is manufacturing software. It is not this product.",
            },
            {
                "heading": "The sentence on the homepage that decides the use case",
                "body": "Arena’s homepage, today, is blunter than most AI products:\n\nInputs are processed by third-party AI. Conversations and certain other personal information will be disclosed to the relevant AI providers and may otherwise be disclosed publicly to help support the community and advance AI research. Do not submit personal or sensitive information you would not want shared publicly.\n\nThey also say conversations are used for automated evaluation — prompts sent to providers later to score models — and that you can write to privacy@arena.ai to ask about opting out.\n\nChatGPT and Claude both document training toggles, temporary or incognito chats, and business plans that do not train by default. I already wrote that comparison. Arena’s public notice is a different shape: the research/leaderboard product is built on sharing prompts. If that sentence is unacceptable, Arena is the wrong tool, full stop. Price does not fix it.",
            },
            {
                "heading": "What ChatGPT and Claude still are",
                "body": "ChatGPT is a single-vendor assistant. Free text chat exists. Official help prices Plus at $20 a month. Go is $8 a month in the US per OpenAI’s January 2026 post, and that post says ads may appear on Free and Go. Memory, custom GPTs, Codex and a stable account live on that ladder.\n\nClaude is also a single-vendor assistant. Free is $0. Pro is $20 a month, or $17 if you pay $200 a year. Max starts at $100. Pro is where Claude Code and Cowork officially sit.\n\nNeither company is selling “use every lab’s model in one box.” Arena is. That is the product difference people flatten when they type “Arena ChatGPT alternative.”",
            },
            {
                "heading": "When Arena is the alternative, and when it is not",
                "body": "Use Arena if the job is “I want this prompt tried on more than one model” or “I want an agent that can search and write files without paying Plus.” The $0 Agent Mode page is the official offer I can point at.\n\nDo not use Arena if the job is a private client brief, a password, a medical note, a school essay you would not want in a research set, or a long-running personal memory. The homepage told you not to.\n\nDo not use Arena as a drop-in replacement for Claude Code on Pro, or for ChatGPT’s billed model picker, unless you have checked what the current Agent session actually routed to. I am not going to publish a model list. It changes, and I would be inventing today’s roster.\n\nClaude and ChatGPT remain the products with documented consumer subscriptions, apps, and (on paid business tiers) a training default that is off. Arena remains the product with a public leaderboard and a sharing notice.",
            },
            {
                "heading": "How I would choose, labelled as opinion",
                "body": "For this site’s research — open official pages, write a sourced article, keep the work in one thread — Arena Agent Mode is the cheaper desk. That is why this page exists here.\n\nFor anything I would not paste into a public GitHub issue, I would use ChatGPT Temporary Chat or Claude Incognito, or a business plan, and I would not use Arena.\n\nIf I was paying $20 only to have “a good model in a chat box,” I would try Gemini Free or DeepSeek’s advertised free chat first, then decide. If I was paying $20 for memory, files and a vendor I can name in a contract, I would stay on Plus or Claude Pro.\n\nI will not score Arena’s writing against Claude’s. I am inside one of them.",
            },
        ],
        "sources": [
            {"name": "Arena.ai homepage (privacy notice)", "url": "https://arena.ai/"},
            {"name": "Arena.ai — Agent Mode", "url": "https://arena.ai/agent"},
            {"name": "OpenAI Help — What is ChatGPT Plus?", "url": "https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus"},
            {"name": "OpenAI — Introducing ChatGPT Go", "url": "https://openai.com/index/introducing-chatgpt-go/"},
            {"name": "Claude — Plans & Pricing", "url": "https://claude.com/pricing"},
            {"name": "BRYME — What ChatGPT, Claude and Gemini do with chats", "url": "https://bryme.onrender.com/tech/ai-assistant-data-training-settings/"},
        ],
    },
    {
        "id": "gemini-vs-chatgpt",
        "slug": "gemini-vs-chatgpt",
        "title": "Gemini vs ChatGPT: The $4.99 Step",
        "seoTitle": "Gemini vs ChatGPT: The $4.99 Step",
        "excerpt": "Google’s official Gemini page still has a $0 plan. The first paid step is Google AI Plus at $4.99 a month. ChatGPT’s first named paid step is Go at $8 in the US, then Plus at $20. That is the comparison. Not a quality score.",
        "category": "AI Assistants",
        "categorySlug": "ai-assistants",
        "tags": ["gemini", "chatgpt", "google", "alternatives"],
        "readingTime": "7 min read",
        "hero": HERO,
        "content": [
            {
                "heading": "Two consumer ladders, printed",
                "body": "Gemini and ChatGPT are the two assistants most people can open without a lecture. Both have a free tier. Both sell higher limits. The useful page is the price and what each company says you get — not a vibes ranking from a listicle.\n\nI opened gemini.google/subscriptions and chatgpt.com/pricing on 23 August 2026, plus OpenAI’s Go announcement and the ChatGPT Plus help article.",
            },
            {
                "heading": "Gemini’s official prices",
                "body": "Free is $0 a month with a Google Account. Official inclusions on that page: Gemini app access to 3.6 Flash, varying access to 3.1 Pro, image generation and editing, Deep Research, Gemini Live, Canvas, Gems, limited Flow, Gemini Notebook, and the usual 15GB of Google storage.\n\nGoogle AI Plus is $4.99 a month. Official extras: 2× the Free usage, video generation and Daily Brief, 200 Flow credits, Gemini in Gmail, Vids and more, Gemini in Chrome (early access), 400GB storage. Google says Plus is available in more than 160 countries.\n\nGoogle AI Pro is $19.99 a month: 4× Free usage, 1,000 Flow credits, more Search/agent features, Jules, 5TB storage, YouTube Premium Lite, Google Home Premium (standard). Ultra starts at $99.99 a month, with a $199.99 option for 20× Pro usage.\n\nThose are US figures on Google’s subscriptions page. Local price can differ.",
            },
            {
                "heading": "ChatGPT’s official prices",
                "body": "Free: the live pricing page lists unlimited text chats with GPT-5.6 Luna, subject to abuse guardrails, and limited everything else — uploads, images, voice, deep research, memory, Codex.\n\nGo: OpenAI’s 16 January 2026 post prices it at $8 a month in the US, localized in some markets, with about 10× the free tier on messages, uploads and images on the Instant model, plus longer memory. The same post says OpenAI planned to test ads on Free and Go. Plus, Pro, Business and Enterprise stay ad-free.\n\nPlus: official help still says $20 a month, billed monthly, no annual plan. Broader models, faster replies, priority access, voice, images, files, deep research where available.\n\nPro: a higher tier exists. I am not printing a Pro dollar figure from a January blog when today’s pricing HTML did not show one.",
            },
            {
                "heading": "The cheap question, answered",
                "body": "If the question is “what is the cheapest official paid upgrade among these two?”, Google AI Plus at $4.99 is lower than ChatGPT Go at $8 US, which is lower than Plus or Claude Pro at $20.\n\nIf the question is “what is free?”, both. Gemini Free wants a Google account. ChatGPT Free wants an OpenAI account. Gemini’s free tier is also the front door to Gmail and Drive features. ChatGPT’s free tier is not.\n\nIf the question is “which writes better?”, I did not run a blind test for this page. I will not fake one.",
            },
            {
                "heading": "What you actually switch",
                "body": "Moving from ChatGPT to Gemini is also moving into Google’s data and storage world. I already wrote what Gemini Apps Activity does with chats, including the human-review copy that can outlast deletion. Open that piece before you paste a client file into a $0 Gemini window because it is cheap.\n\nMoving the other way, you lose Gemini-in-Gmail and you gain ChatGPT’s model picker and, on Plus, the documented $20 feature set. You do not automatically gain a better privacy default. OpenAI still trains on consumer chats unless you opt out.\n\nNeither product is Arena. Neither product is DeepSeek. Do not treat “AI chatbot” as one SKU.",
            },
            {
                "heading": "How I would choose, labelled as opinion",
                "body": "If I already pay for nothing and I live in Google, Gemini Free is the first try.\n\nIf Free ChatGPT’s limits are the only pain, I would look at Go at $8 or Google AI Plus at $4.99 before Plus at $20. I would read whether ads are on in my country first.\n\nIf I needed the current ChatGPT reasoning models and Codex as OpenAI documents them, I would pay Plus and stop pretending a $4.99 Google plan is the same SKU.\n\nI have not subscribed to Google AI Plus. I am describing their page, not a month of invoices.",
            },
        ],
        "sources": [
            {"name": "Google — Gemini subscriptions (Free, Plus $4.99, Pro $19.99, Ultra from $99.99)", "url": "https://gemini.google/subscriptions/"},
            {"name": "ChatGPT — Pricing", "url": "https://chatgpt.com/pricing/"},
            {"name": "OpenAI — Introducing ChatGPT Go ($8 US)", "url": "https://openai.com/index/introducing-chatgpt-go/"},
            {"name": "OpenAI Help — What is ChatGPT Plus? ($20/month)", "url": "https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus"},
            {"name": "BRYME — ChatGPT, Claude and Gemini training settings", "url": "https://bryme.onrender.com/tech/ai-assistant-data-training-settings/"},
        ],
    },
    {
        "id": "deepseek-vs-chatgpt",
        "slug": "deepseek-vs-chatgpt",
        "title": "DeepSeek vs ChatGPT: Free Chat, Paid API",
        "seoTitle": "DeepSeek vs ChatGPT: Free Chat, Paid API",
        "excerpt": "DeepSeek’s homepage still offers free access to the chat. The API is a separate, priced product. ChatGPT’s free tier is real too. The mistake is treating a 2025 “100% free” press note as a forever contract.",
        "category": "AI Assistants",
        "categorySlug": "ai-assistants",
        "tags": ["deepseek", "chatgpt", "alternatives"],
        "readingTime": "7 min read",
        "hero": HERO,
        "content": [
            {
                "heading": "Two products with one name",
                "body": "DeepSeek is the name people use for a free ChatGPT-shaped app. It is also the name of an API you pay for by the token. Mixing those up is how a “free forever” post gets written.\n\nOn 23 August 2026, deepseek.com still says “Chat Now — Free access to DeepSeek. Experience the intelligent model,” and separately “Access API — Build with the latest DeepSeek models.” The chat login is at chat.deepseek.com. The homepage banner says DeepSeek-V4-Pro is out on web, mobile and API. I am repeating their words. I am not scoring V4-Pro against GPT-5.6.",
            },
            {
                "heading": "What “free” is documented as",
                "body": "The live homepage offer is free access to the chat. That is the claim I will stand on.\n\nA January 2025 DeepSeek post said the official app was 100% free, no ads, no in-app purchases, and warned people to download only from official stores. That post is a year and a half old. I am not going to treat 2025 marketing as 2026 terms. If you need “no ads” in writing today, open the current app listing or the current terms — I did not find a 2026 pricing page for the consumer chat that restates the no-ads line.\n\nChatGPT Free is also $0. Official pricing: unlimited text chats with GPT-5.6 Luna, with guardrails, and limited uploads, images, voice and research. It is not an empty product. “Switch to DeepSeek because ChatGPT costs $20” is only true if you were about to pay Plus.",
            },
            {
                "heading": "The API is not the chat",
                "body": "DeepSeek’s official API docs publish per-million-token prices, with peak and off-peak rates, and a note dated for 23 August 2026 about weekend off-peak billing. That is a developer bill. It is how people say DeepSeek is “200× cheaper than GPT.” Those ratios are API maths. They are not the consumer chat.\n\nChatGPT’s API is likewise a different bill from Plus. Official Plus help says API usage is not included.\n\nIf you are a person in a browser, the API table is trivia. If you are wiring a bot, it is the whole product.",
            },
            {
                "heading": "What I will not pretend",
                "body": "I will not pretend DeepSeek is hosted in the same legal and privacy regime as OpenAI or Anthropic. DeepSeek is a Chinese company. The chat login page links terms and a privacy policy. I am not going to summarise a legal PDF I have not quoted section by section. If data residency is why you opened this page, read those policies, or do not use the chat.\n\nI will not invent daily message caps. DeepSeek’s homepage does not print one.\n\nI will not invent a DeepSeek Plus price. I did not find one on the homepage.",
            },
            {
                "heading": "How I would choose, labelled as opinion",
                "body": "If I want a second free chat box to compare answers with ChatGPT Free, I would open DeepSeek’s official chat and I would not paste anything I would not put in a random web form.\n\nIf I want memory, a US/EU vendor I can name on an invoice, and the $20 feature set, I would stay on ChatGPT Plus or Claude Pro.\n\nIf I want cheap tokens for a program I am writing, I would read DeepSeek’s current API price table and OpenAI’s current API table on the same day, not a screenshot from 2025.\n\nI have not used DeepSeek as my daily driver. I am not going to invent coding-benchmark bragging.",
            },
        ],
        "sources": [
            {"name": "DeepSeek homepage (free chat / separate API)", "url": "https://www.deepseek.com/en/"},
            {"name": "DeepSeek chat", "url": "https://chat.deepseek.com/"},
            {"name": "DeepSeek API — Models & Pricing", "url": "https://api-docs.deepseek.com/quick_start/pricing/"},
            {"name": "ChatGPT — Pricing", "url": "https://chatgpt.com/pricing/"},
            {"name": "OpenAI Help — What is ChatGPT Plus?", "url": "https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus"},
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


def word_count(art: dict) -> int:
    return sum(len((b.get("heading", "") + " " + b.get("body", "")).split()) for b in art["content"])


def related_html(current: str) -> str:
    cards = [
        f'<a class="vcat vcat-photo" href="/tech/chatgpt-claude-alternatives/" style="--card-img:url(\'{HERO}\')">'
        f"<b>Free and cheap ChatGPT alternatives we checked</b>"
        f"<span>Official prices for the big names. Three earned their own pages.</span></a>"
    ]
    for art in ARTICLES:
        if art["slug"] == current:
            continue
        cards.append(
            f'<a class="vcat vcat-photo" href="/tech/{art["slug"]}/" style="--card-img:url(\'{art["hero"]}\')">'
            f"<b>{esc(art['title'])}</b><span>{esc(art['excerpt'])}</span></a>"
        )
    cards.append(
        '<a class="vcat vcat-photo" href="/tech/ai-assistant-data-training-settings/" '
        f"style=\"--card-img:url('{HERO_PRIVACY}')\">"
        "<b>What ChatGPT, Claude and Gemini do with your chats</b>"
        "<span>The training toggle is real. Each vendor also keeps a way around it.</span></a>"
    )
    return (
        '<section class="section"><div class="section-head"><h2>More AI assistants</h2></div>'
        f'<div class="vcat-grid">{"".join(cards)}</div></section>'
    )


def article_html(art: dict) -> str:
    url = f"{SITE}/tech/{art['slug']}/"
    page_title = f"{art['seoTitle']} | BRYME"
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
            "author": {"@type": "Person", "name": AUTHOR, "url": SITE + AUTHOR_URL,
                       "jobTitle": "Writer — Make Money, Tech & AI, Sports"},
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
                {"@type": "ListItem", "position": 3, "name": "AI Assistants", "item": SITE + "/tech/ai-assistants/"},
                {"@type": "ListItem", "position": 4, "name": art["title"], "item": url},
            ],
        },
    ]
    return (
        HEAD_CHROME
        + f"<title>{esc(page_title)}</title>"
        + f'<meta name="description" content="{esc(desc)}">'
        + f'<link rel="canonical" href="{url}">'
        + '<meta property="og:type" content="article"><meta property="og:site_name" content="BRYME">'
        + f'<meta property="og:title" content="{esc(page_title)}">'
        + f'<meta property="og:description" content="{esc(desc)}">'
        + f'<meta property="og:url" content="{url}">'
        + f'<meta property="og:image" content="{abs_hero}">'
        + '<meta property="og:image:type" content="image/jpeg"><meta property="og:image:alt" content="BRYME">'
        + f'<meta name="twitter:image" content="{abs_hero}"><meta name="twitter:image:alt" content="BRYME">'
        + '<meta name="twitter:card" content="summary_large_image">'
        + f'<meta name="twitter:title" content="{esc(page_title)}">'
        + f'<meta name="twitter:description" content="{esc(desc)}">'
        + '<link rel="stylesheet" href="/assets/site.css">'
        + f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(",", ":"))}</script>'
        + HEADER
        + '<main class="shell">'
        + f'<div class="crumb"><a href="/">Home</a> / <a href="/tech/">BRYME Tech &amp; AI</a> / '
        + f'<a href="/tech/ai-assistants/">AI Assistants</a> / {esc(art["title"])}</div>'
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


def write_pages() -> None:
    for art in ARTICLES:
        dest = ROOT / "tech" / art["slug"] / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(article_html(art), encoding="utf-8")
        print("wrote", dest.relative_to(ROOT), "words", word_count(art), "titlec", len(art["seoTitle"] + " | BRYME"))


def upsert_json() -> None:
    path = ROOT / "content" / "tech-articles.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    by_id = {a["id"]: i for i, a in enumerate(data)}
    for art in ARTICLES:
        rec = {
            "id": art["id"], "slug": art["slug"], "title": art["title"], "seoTitle": art["seoTitle"],
            "excerpt": art["excerpt"], "category": art["category"], "categorySlug": art["categorySlug"],
            "tags": art["tags"], "relatedMovieSlugs": [], "status": "published", "author": AUTHOR,
            "publishedAt": CHECKED, "updatedAt": CHECKED, "readingTime": art["readingTime"],
            "content": art["content"], "sources": art["sources"], "sourcesCheckedOn": CHECKED,
        }
        if art["id"] in by_id:
            data[by_id[art["id"]]] = rec
        else:
            data.append(rec)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("tech-articles.json", len(data))


def patch_ai_assistants_hub() -> None:
    path = ROOT / "tech" / "ai-assistants" / "index.html"
    t = path.read_text(encoding="utf-8")
    cards = []
    for art in ARTICLES:
        href = f"/tech/{art['slug']}/"
        if href in t:
            continue
        cards.append(
            f'<a class="vcat vcat-photo" href="{href}" style="--card-img:url(\'{art["hero"]}\')">'
            f"<b>{esc(art['title'])}</b><span>{esc(art['excerpt'])}</span></a>"
        )
    if cards:
        t = t.replace('<div class="vcat-grid">', '<div class="vcat-grid">' + "".join(cards), 1)
        path.write_text(t, encoding="utf-8")
        print("patched ai-assistants hub", len(cards))


def patch_app_alt_hub() -> None:
    path = ROOT / "tech" / "app-alternatives" / "index.html"
    t = path.read_text(encoding="utf-8")
    if "/tech/chatgpt-claude-alternatives/" in t:
        print("app-alternatives already linked")
        return
    block = (
        '<section class="section"><div class="section-head"><h2>AI assistants</h2></div>'
        '<div class="vcat-grid">'
        f'<a class="vcat vcat-photo" href="/tech/chatgpt-claude-alternatives/" style="--card-img:url(\'{HERO}\')">'
        "<b>Free and cheap ChatGPT alternatives we checked</b>"
        "<span>Official prices for Gemini, DeepSeek, Arena, Copilot and Perplexity. Three earned their own pages.</span></a>"
        f'<a class="vcat vcat-photo" href="/tech/arena-ai-vs-chatgpt/" style="--card-img:url(\'{HERO_PRIVACY}\')">'
        "<b>Arena.ai vs ChatGPT</b>"
        "<span>A free multi-model arena, not a Plus plan. The homepage privacy notice is the decision.</span></a>"
        "</div></section>"
    )
    t = t.replace('<section class="section core-hubs"', block + '<section class="section core-hubs"', 1)
    path.write_text(t, encoding="utf-8")
    print("patched app-alternatives hub")


def patch_tech_landing() -> None:
    path = ROOT / "tech" / "index.html"
    t = path.read_text(encoding="utf-8")
    if "/tech/chatgpt-claude-alternatives/" not in t:
        t = t.replace(
            '<a class="cta-ghost" href="/tech/ai-assistant-data-training-settings/">AI privacy settings</a>',
            '<a class="cta-ghost" href="/tech/chatgpt-claude-alternatives/">ChatGPT alternatives</a>',
            1,
        )
        tile = (
            f'<a class="sp-comp-card" href="/tech/chatgpt-claude-alternatives/" style="--card-img:url(\'{HERO}\')">'
            "<em>Chat</em><b>ChatGPT alternatives</b>"
            "<span>Official prices for Gemini, DeepSeek and Arena. No fake top ten.</span></a>"
        )
        t = t.replace(
            '<a class="sp-comp-card" href="/tech/ai-assistants/"',
            tile + '\n      <a class="sp-comp-card" href="/tech/ai-assistants/"',
            1,
        )
    # featured comparisons: add arena as a side card if missing
    if 'href="/tech/arena-ai-vs-chatgpt/"' not in t:
        extra = f"""        <a href="/tech/arena-ai-vs-chatgpt/" style="--card-img:url('{HERO_PRIVACY}')">
          <span class="tag">AI</span>
          <h3>Arena.ai vs ChatGPT</h3>
          <p>Free multi-model arena. The privacy notice is the product.</p>
        </a>
"""
        t = t.replace(
            '<a href="/tech/polotno-studio-vs-canva/"',
            extra + '        <a href="/tech/polotno-studio-vs-canva/"',
            1,
        )
    path.write_text(t, encoding="utf-8")
    print("patched tech/index.html")


def patch_author() -> None:
    path = ROOT / "author" / "ibrahim-sodiq" / "index.html"
    t = path.read_text(encoding="utf-8")
    needle = '<a class="vcat vcat-photo" href="/tech/where-to-host-website-for-free/"'
    cards = []
    for art in ARTICLES:
        href = f"/tech/{art['slug']}/"
        if href in t:
            continue
        cards.append(
            f'<a class="vcat vcat-photo" href="{href}" style="--card-img:url(\'{art["hero"]}\')">'
            f"<b>{esc(art['title'])}</b><span>{esc(art['excerpt'])}</span></a>"
        )
    if cards:
        t = t.replace(needle, "".join(cards) + needle, 1)
        path.write_text(t, encoding="utf-8")
        print("patched author", len(cards))


def patch_sitemap() -> None:
    path = ROOT / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    locs = re.findall(r"<loc>([^<]+)</loc>", text)
    add = [f"{SITE}/tech/{a['slug']}/" for a in ARTICLES]
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
    if not any(v.get("slug") == "tech/chatgpt-claude-alternatives" for v in verts):
        verts.append({
            "type": "tech",
            "title": "ChatGPT & Claude alternatives",
            "slug": "tech/chatgpt-claude-alternatives",
            "description": "Official prices for Gemini, DeepSeek, Arena and the other big free or cheap assistants.",
        })
        path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        print("search-index vertical added")
    else:
        print("search-index already has vertical")


def main() -> None:
    write_pages()
    upsert_json()
    patch_ai_assistants_hub()
    patch_app_alt_hub()
    patch_tech_landing()
    patch_author()
    patch_sitemap()
    patch_search()


if __name__ == "__main__":
    main()

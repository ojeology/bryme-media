#!/usr/bin/env python3
"""Build BRYME's focused, source-first public pages.

This builder owns only the small set of hand-reviewed focus pages listed below.
It deliberately does not regenerate the legacy catalogue or sports trees.
Run from anywhere: python3 scripts/build-focus-site.py
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://bryme.onrender.com"
TODAY = "2026-09-04"
TODAY_HUMAN = "4 September 2026"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def nav(current: str = "") -> str:
    links = [
        ("jobs", "/jobs/", "Jobs"),
        ("money", "/make-money/", "Opportunities"),
        ("tech", "/tech/", "Practical Tech"),
        ("read", "/articles/", "Watch & Read"),
        ("about", "/about/", "About"),
    ]
    items = []
    for key, href, label in links:
        aria = ' aria-current="page"' if key == current else ""
        cls = ' class="nav-cta"' if key == "jobs" else ""
        items.append(f'<a{cls}{aria} href="{href}">{label}</a>')
    return f'''<a class="skip-link" href="#main">Skip to content</a>
<header class="site-head"><div class="wrap head-in">
  <a class="logo" href="/" aria-label="BRYME home"><span class="logo-mark" aria-hidden="true">B</span>BRYME</a>
  <nav class="main-nav" aria-label="Primary">{''.join(items)}</nav>
</div></header>'''


def footer() -> str:
    return '''<footer class="site-foot"><div class="wrap foot-grid">
  <div class="foot-brand"><a class="logo" href="/"><span class="logo-mark" aria-hidden="true">B</span>BRYME</a><p>Verified opportunities and practical technology for Nigerians and Africa-based applicants. We link to primary sources and show when a human checked them.</p></div>
  <div class="foot-col"><b>Use BRYME</b><a href="/jobs/">Verified jobs</a><a href="/make-money/">Opportunities</a><a href="/tech/">Practical tech</a><a href="/articles/">Watch &amp; read</a></div>
  <div class="foot-col"><b>Trust</b><a href="/jobs/methodology/">Verification method</a><a href="/editorial-policy/">Editorial policy</a><a href="/corrections/">Corrections</a><a href="/privacy/">Privacy</a><a href="/contact/">Contact</a></div>
</div><div class="wrap foot-bottom">© 2026 BRYME · Independent editorial project · No application or earning outcome is guaranteed.</div></footer>'''


def schema(data: object) -> str:
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>"


def page(*, title: str, description: str, route: str, current: str, body: str,
         schema_data: object | None = None, robots: str = "index,follow") -> str:
    canonical = BASE + route
    structured = schema_data or {
        "@context": "https://schema.org", "@type": "WebPage",
        "name": title.split(" | ")[0], "description": description, "url": canonical,
        "publisher": {"@type": "Organization", "name": "BRYME", "url": BASE + "/"},
    }
    return f'''<!doctype html>
<html lang="en-NG"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#07100d">
<meta name="color-scheme" content="dark">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="{esc(robots)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website"><meta property="og:site_name" content="BRYME">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(description)}">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="icon" href="/favicon.ico" sizes="any">
<link rel="stylesheet" href="/assets/bryme-v2.css">
{schema(structured)}
</head><body>{nav(current)}<main id="main">{body}</main>{footer()}</body></html>'''


def write(route: str, content: str) -> None:
    if route == "/":
        target = ROOT / "index.html"
    else:
        target = ROOT / route.strip("/") / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    print("wrote", target.relative_to(ROOT))


JOBS = json.loads((ROOT / "content/jobs.json").read_text(encoding="utf-8"))


def job_card(job: dict, heading: str = "h2") -> str:
    pay = f'<span class="pill warn">{esc(job["compensationRaw"])}</span>' if job.get("compensationRaw") else ""
    return f'''<article class="job-card">
  <div><div class="job-company">{esc(job['employer'])} · {esc(job['employerType'])}</div>
  <{heading}>{esc(job['title'])}</{heading}>
  <div class="job-meta"><span class="pill good">Open when checked</span><span class="pill">{esc(job['locationTextRaw'])}</span><span class="pill">{esc(job['workMode'])}</span><span class="pill">{esc(job['employmentType'])}</span>{pay}</div>
  <p class="job-note">{esc(job['notes'])}</p></div>
  <a class="btn secondary job-apply" href="{esc(job['sourceUrl'])}" target="_blank" rel="noopener external">Open official role ↗</a>
</article>'''


def home() -> None:
    jobs = JOBS["jobs"]
    featured = "".join(job_card(j, "h3") for j in jobs[:4])
    body = f'''<section class="hero"><div class="wrap hero-grid"><div>
  <p class="kicker"><span class="kicker-dot"></span>Direct sources. Human checks. Nigeria context.</p>
  <h1>Find work you can <em>actually apply for.</em></h1>
  <p class="hero-copy">BRYME checks employer and applicant-tracking pages, reports the location details they really state, and pairs opportunities with practical technology guides.</p>
  <div class="actions"><a class="btn" href="/jobs/">See verified jobs →</a><a class="btn secondary" href="/jobs/methodology/">How verification works</a></div>
</div><aside class="verify-card" aria-label="Latest verification snapshot"><div class="verify-head"><h2 class="verify-title">Latest jobs snapshot</h2><span class="live-tag">Checked</span></div><p class="verify-date">{TODAY_HUMAN} · Africa/Lagos</p><div class="metric-row"><div class="metric"><b>{len(jobs)}</b><span>Exact roles</span></div><div class="metric"><b>{len(set(j['employer'] for j in jobs))}</b><span>Sources</span></div><div class="metric"><b>1</b><span>Conflict corrected</span></div></div><p class="verify-note">“Open when checked” is a timestamp, not a guarantee. Always confirm the employer page before applying.</p></aside></div></section>
<section class="trust-strip"><div class="wrap trust-grid"><div class="trust-item"><span class="trust-icon">✓</span>Exact employer or ATS link</div><div class="trust-item"><span class="trust-icon">✓</span>Location wording checked manually</div><div class="trust-item"><span class="trust-icon">✓</span>Agency and contract work labelled</div></div></section>
<section class="section"><div class="wrap"><div class="section-head"><div><p class="eyebrow">Choose a useful path</p><h2>Less browsing. More confidence.</h2></div><p>BRYME is being rebuilt around one promise: help people find a real opportunity and take the next practical step.</p></div><div class="card-grid">
<a class="path-card" href="/jobs/"><span class="card-num">01 / VERIFIED JOBS</span><h3>Nigeria-relevant roles</h3><p>Dated checks of direct employer and ATS vacancies, with remote and hybrid details clarified.</p><span class="card-link">Browse the snapshot →</span></a>
<a class="path-card" href="/make-money/"><span class="card-num">02 / OPPORTUNITIES</span><h3>Work and paid calls</h3><p>Evergreen guides plus an archive of paid-writing sources being reverified before wider Search publication.</p><span class="card-link">Explore opportunities →</span></a>
<a class="path-card" href="/tech/"><span class="card-num">03 / PRACTICAL TECH</span><h3>Tools that help you act</h3><p>Tested guides for applications, safer accounts, design, coding and getting a site online.</p><span class="card-link">Open practical tech →</span></a>
</div></div></section>
<section class="section alt"><div class="wrap"><div class="section-head"><div><p class="eyebrow">Verified {TODAY_HUMAN}</p><h2>A sample from the current desk</h2></div><p>Every link below goes to the source—not a copied BRYME job page.</p></div><div class="job-list">{featured}</div><div class="actions"><a class="btn" href="/jobs/verified-2026-09-04/">See all {len(jobs)} checked roles →</a></div></div></section>
<section class="section"><div class="wrap"><div class="section-head"><div><p class="eyebrow">Transparent by design</p><h2>What BRYME will—and will not—claim</h2></div></div><div class="card-grid">
<div class="path-card"><span class="card-num">SOURCE</span><h3>Primary pages first</h3><p>Employer boards and official submission guidelines outrank search snippets and reposts.</p></div>
<div class="path-card"><span class="card-num">CONTEXT</span><h3>“Remote” gets inspected</h3><p>If a card says remote but the detail says two Lagos office days, BRYME reports the stricter condition.</p></div>
<div class="path-card"><span class="card-num">LIMIT</span><h3>No guaranteed outcome</h3><p>An open form does not guarantee an interview, project allocation, earnings or continued availability.</p></div>
</div></div></section>'''
    structured = [{
        "@context": "https://schema.org", "@type": "WebSite", "name": "BRYME",
        "url": BASE + "/", "description": "Verified opportunities and practical technology for Nigerians and Africa-based applicants."
    }, {
        "@context": "https://schema.org", "@type": "Organization", "name": "BRYME", "url": BASE + "/",
        "founder": {"@type": "Person", "name": "Ibrahim Sodiq", "url": BASE + "/author/ibrahim-sodiq/"}
    }]
    write("/", page(title="BRYME | Verified jobs and practical tech for Nigerians", description="BRYME checks direct employer roles, Nigeria eligibility and work conditions, then pairs them with practical technology guides.", route="/", current="", body=body, schema_data=structured))


def jobs_index() -> None:
    jobs = JOBS["jobs"]
    companies = sorted(set(j["employer"].split(" /")[0] for j in jobs))
    body = f'''<div class="wrap"><nav class="breadcrumb"><a href="/">Home</a> / Jobs</nav><section class="page-hero"><p class="kicker"><span class="kicker-dot"></span>Human-verified source desk</p><h1>Jobs checked for Nigerian applicants.</h1><p>BRYME opens the exact employer or ATS page, records what it says, and flags location contradictions instead of bulk-importing them.</p><div class="source-line"><span><b>{len(jobs)}</b> exact roles</span><span><b>{len(companies)}</b> source organisations</span><span>Last checked <b>{TODAY_HUMAN}</b></span></div></section>
<section class="section"><div class="notice"><strong>Freshness rule:</strong> these roles were open when checked. Employers can close or change them without warning. Confirm the source before investing time in an application.</div><div class="card-grid">
<a class="path-card" href="/jobs/verified-2026-09-04/"><span class="card-num">LATEST SNAPSHOT</span><h3>{len(jobs)} roles verified {TODAY_HUMAN}</h3><p>Paystack, Moniepoint, SAND Technologies, M-KOPA, Swoop, Canonical, LILT and Remotasks.</p><span class="card-link">Open the dated roundup →</span></a>
<a class="path-card" href="/jobs/methodology/"><span class="card-num">METHOD</span><h3>How BRYME checks a role</h3><p>See the source hierarchy, remote-work rules, conflict handling and closure process.</p><span class="card-link">Read the method →</span></a>
<a class="path-card" href="/contact/"><span class="card-num">CORRECTIONS</span><h3>Report a closed or changed job</h3><p>Send the exact BRYME or employer URL. Corrections are recorded publicly.</p><span class="card-link">Contact the desk →</span></a>
</div></section></div>'''
    structured = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Verified jobs for Nigerian applicants", "description": "Dated, human-checked links to direct employer and ATS roles relevant to Nigerian applicants.", "url": BASE + "/jobs/", "dateModified": TODAY, "publisher": {"@type": "Organization", "name": "BRYME", "url": BASE + "/"}}
    write("/jobs/", page(title="Verified jobs for Nigerians | BRYME", description="Dated, human-checked links to direct employer and ATS vacancies relevant to Nigerian applicants.", route="/jobs/", current="jobs", body=body, schema_data=structured))


def jobs_roundup() -> None:
    jobs = JOBS["jobs"]
    cards = "".join(job_card(j) for j in jobs)
    item_list = [{"@type": "ListItem", "position": i + 1, "name": j["employer"] + " — " + j["title"], "url": j["sourceUrl"]} for i, j in enumerate(jobs)]
    body = f'''<div class="wrap"><nav class="breadcrumb"><a href="/">Home</a> / <a href="/jobs/">Jobs</a> / {TODAY_HUMAN}</nav><section class="page-hero"><p class="kicker"><span class="kicker-dot"></span>Dated editorial roundup</p><h1>{len(jobs)} Nigeria-relevant roles verified {TODAY_HUMAN}.</h1><p>Direct links, raw location wording and the caveats a search snippet leaves out. This page is an editorial roundup—not a job-board mirror.</p><div class="source-line"><span>Reviewed by <b>Ibrahim Sodiq</b></span><span>Verified <time datetime="2026-09-04T08:35:00+01:00"><b>{TODAY_HUMAN}, 08:35 WAT</b></time></span><span><a href="/jobs/methodology/">Verification method</a></span></div></section>
<section class="section"><p class="checked-line">Published <time datetime="{TODAY}">{TODAY}</time> · Last source check {TODAY_HUMAN}</p><div class="notice"><strong>Check again before applying.</strong> “Open when checked” means the exact page displayed an application path during this review. It does not guarantee the employer has not closed or changed it since.</div><div class="job-list">{cards}</div></section>
<section class="section alt"><div class="prose"><h2>What BRYME deliberately excluded</h2><p>The recently promoted Kuda 2026 SIWES page was excluded because Kuda's direct Workable page said the job was no longer available. A Swoop Country Manager record was excluded because its title said Eswatini while structured location metadata said Nigeria. Scale Army records were excluded from this roundup because sampled location metadata and role-body restrictions conflicted.</p><h2>How to use this list</h2><ol><li>Open the official role and recheck location and closing status.</li><li>Read every requirement before sharing personal information.</li><li>Never pay to apply for a job.</li><li>Confirm that emails and interview links use the employer's legitimate domain.</li><li><a href="/contact/">Tell BRYME</a> if a role has changed or closed.</li></ol></div></section></div>'''
    structured = [{
        "@context": "https://schema.org", "@type": "Article", "headline": f"{len(jobs)} Nigeria-relevant roles verified {TODAY_HUMAN}",
        "description": "A dated BRYME editorial roundup linking directly to employer and ATS vacancies relevant to Nigerian applicants.",
        "datePublished": TODAY, "dateModified": TODAY, "mainEntityOfPage": BASE + "/jobs/verified-2026-09-04/",
        "author": {"@type": "Person", "name": "Ibrahim Sodiq", "url": BASE + "/author/ibrahim-sodiq/"},
        "publisher": {"@type": "Organization", "name": "BRYME", "url": BASE + "/"}
    }, {"@context": "https://schema.org", "@type": "ItemList", "name": "Nigeria-relevant jobs verified 4 September 2026", "numberOfItems": len(jobs), "itemListElement": item_list}]
    write("/jobs/verified-2026-09-04/", page(title=f"{len(jobs)} Nigeria-relevant jobs verified 4 September 2026 | BRYME", description="BRYME checked 13 exact employer and ATS role pages for Nigeria relevance, location conditions and a working application path.", route="/jobs/verified-2026-09-04/", current="jobs", body=body, schema_data=structured))


def jobs_method() -> None:
    body = '''<div class="wrap"><nav class="breadcrumb"><a href="/">Home</a> / <a href="/jobs/">Jobs</a> / Verification method</nav><section class="page-hero"><p class="kicker"><span class="kicker-dot"></span>Published methodology</p><h1>How BRYME verifies a job.</h1><p>A repeatable process for finding the difference between “listed somewhere” and “safe to publish as open when checked.”</p><div class="source-line"><span>Method owner <b>Ibrahim Sodiq</b></span><span>Version <b>1.0</b></span><span>Effective <b>4 September 2026</b></span></div></section><section class="section"><div class="prose">
<h2>The source hierarchy</h2><ol class="steps"><li><b>Exact employer vacancy.</b><br>Use the employer's own careers site or the exact ATS page. A search result, newsletter or repost can lead us there but cannot prove current status.</li><li><b>Full role description.</b><br>Read the body, not only a filter card. The body wins when a card says “remote” but the role requires office days or limits countries.</li><li><b>Working application path.</b><br>The page must display a real application action. A board title without a working leaf page is not published as active.</li><li><b>Human timestamp.</b><br>Record who checked it and when in Africa/Lagos time. “Open” is always qualified by that timestamp.</li><li><b>Recheck and correct.</b><br>Changed, inconsistent or removed records are flagged for review; BRYME does not treat a bot's 403 or timeout as proof of closure.</li></ol>
<h2>Location rules</h2><p>BRYME never turns “remote” into “worldwide.” We preserve the employer's raw location text and separately record eligible countries only when the full page supports them. Hybrid and onsite requirements are shown even when ATS metadata uses a looser label.</p>
<h2>Employer, agency or platform</h2><p>Direct employment, staffing-agency recruitment and variable contributor work are different products. Every listing is labelled. A platform application does not guarantee tasks, hours or earnings.</p>
<h2>Pay and deadlines</h2><p>Compensation appears only when the source states it. “Competitive” is not converted into a number. BRYME does not invent a deadline; absent deadlines remain absent.</p>
<h2>What is not published</h2><ul><li>Roles visible only in snippets or copied job sites.</li><li>Expired direct pages.</li><li>Records whose location fields conflict and cannot be resolved.</li><li>Applications requiring a fee.</li><li>Claims of guaranteed interviews, placement, tasks or income.</li></ul>
<h2>Structured data</h2><p>Dated roundups use Article and ItemList markup. BRYME does not use JobPosting markup on roundup pages. Single-job pages will not launch until authorization, working applications, expiry automation and removal controls exist.</p>
<h2>Corrections</h2><p>Email the exact URL to <a href="mailto:Sodiqibrahim03@gmail.com">Sodiqibrahim03@gmail.com</a>. Material corrections are added to the <a href="/corrections/">public corrections log</a>.</p>
</div></section></div>'''
    structured = {"@context": "https://schema.org", "@type": "WebPage", "name": "How BRYME verifies jobs", "description": "BRYME's source hierarchy, location rules, status definitions and corrections process for job roundups.", "url": BASE + "/jobs/methodology/", "datePublished": TODAY, "dateModified": TODAY, "author": {"@type": "Person", "name": "Ibrahim Sodiq"}, "publisher": {"@type": "Organization", "name": "BRYME", "url": BASE + "/"}}
    write("/jobs/methodology/", page(title="How BRYME verifies jobs | Methodology", description="BRYME's published source hierarchy, location rules, status definitions and corrections process for job roundups.", route="/jobs/methodology/", current="jobs", body=body, schema_data=structured))


TECH_GUIDES = [
    ("Learning to code on a phone with Termux", "/tech/learning-to-code-on-a-phone-termux/", "A practical Android-first coding workflow."),
    ("Where to host a website for free", "/tech/where-to-host-website-for-free/", "A deployment guide with realistic platform trade-offs."),
    ("What Render deployment failures taught me", "/tech/render-deployment-failures-what-they-taught-me/", "First-hand debugging lessons from a real deployment."),
    ("AI assistant data-training settings", "/tech/ai-assistant-data-training-settings/", "Find and understand privacy/training controls."),
    ("Bitwarden free password manager", "/tech/bitwarden-free-password-manager/", "A safer account-security starting point."),
    ("Photopea vs Photoshop", "/tech/photopea-vs-photoshop/", "Choose a browser editor or a professional desktop workflow."),
    ("Signal vs WhatsApp", "/tech/signal-vs-whatsapp/", "Compare privacy, reach and day-to-day usability."),
    ("Notion free plan", "/tech/notion-free-plan/", "Understand practical limits before moving your workflow."),
]


def cards_for(items: list[tuple[str, str, str]]) -> str:
    return "".join(f'<a class="guide-card" href="{href}"><h2>{esc(title)}</h2><p>{esc(desc)}</p><span class="card-link">Read guide →</span></a>' for title, href, desc in items)


def tech_hub() -> None:
    body = f'''<div class="wrap"><nav class="breadcrumb"><a href="/">Home</a> / Practical Tech</nav><section class="page-hero"><p class="kicker"><span class="kicker-dot"></span>Tested, task-first guidance</p><h1>Technology that helps you do the work.</h1><p>Focused guides for applying, building, protecting accounts and getting useful work done—without pretending every tool fits every user.</p></section><section class="section"><div class="section-head"><div><p class="eyebrow">Start here</p><h2>Eight maintained practical guides</h2></div><p>Thin topic labels have been removed from Search while they are merged or rebuilt.</p></div><div class="guide-grid">{cards_for(TECH_GUIDES)}</div></section></div>'''
    write("/tech/", page(title="Practical technology guides | BRYME", description="Task-first BRYME guides for coding, deployment, account security, AI settings and useful work tools.", route="/tech/", current="tech", body=body, schema_data={"@context": "https://schema.org", "@type": "CollectionPage", "name": "Practical technology guides", "url": BASE + "/tech/", "dateModified": TODAY, "publisher": {"@type": "Organization", "name": "BRYME", "url": BASE + "/"}}))


MONEY_GUIDES = [
    ("Beginner's guide to making money online", "/make-money/beginners-guide-to-making-money-online/", "A grounded framework before choosing a platform."),
    ("Freelance platform fees explained", "/make-money/freelance-platform-fees-explained/", "Understand the deductions before quoting a rate."),
    ("Making money online in Nigeria", "/make-money/make-money-online-nigeria/", "Nigeria-specific constraints and practical routes."),
    ("Mindrift vs Alignerr vs Prolific", "/make-money/mindrift-vs-alignerr-vs-prolific/", "Compare different forms of platform work."),
    ("Outlier AI in Nigeria", "/make-money/outlier-ai-nigeria/", "Eligibility and project-work caveats."),
    ("Website monetization guide", "/make-money/website-monetization-guide/", "Build value before adding ads."),
    ("How the paid-writing field notes work", "/make-money/writing-field-notes-how-this-works/", "Sources, rates, uncertainty and verification."),
]


def money_hub() -> None:
    body = f'''<div class="wrap"><nav class="breadcrumb"><a href="/">Home</a> / Opportunities</nav><section class="page-hero"><p class="kicker"><span class="kicker-dot"></span>Evidence before earnings claims</p><h1>Opportunity guides without guaranteed-income promises.</h1><p>Start with maintained guidance and the new direct-source jobs desk. The larger paid-writing archive remains available to users but is being reverified before broad Search publication.</p><div class="actions"><a class="btn" href="/jobs/">Open verified jobs →</a><a class="btn secondary" href="/make-money/writing/">Browse writing archive</a></div></section><section class="section"><div class="section-head"><div><p class="eyebrow">Maintained guides</p><h2>Understand the work before you apply</h2></div><p>Fees, eligibility and task availability can change. Each guide states its limits.</p></div><div class="guide-grid">{cards_for(MONEY_GUIDES)}</div></section><section class="section alt"><div class="notice"><strong>Archive status:</strong> individual paid-writing market pages are temporarily excluded from Search until each open/closed state, rate and submission URL receives a fresh human check.</div></section></div>'''
    write("/make-money/", page(title="Verified work and opportunity guides | BRYME", description="Grounded BRYME guides to online work, platform fees and Nigeria-relevant opportunities, without guaranteed-income claims.", route="/make-money/", current="money", body=body, schema_data={"@context": "https://schema.org", "@type": "CollectionPage", "name": "Verified work and opportunity guides", "url": BASE + "/make-money/", "dateModified": TODAY, "publisher": {"@type": "Organization", "name": "BRYME", "url": BASE + "/"}}))


def articles_hub() -> None:
    items = [
        ("10 anime like Solo Leveling", "/article/10-anime-like-solo-leveling-you-should-watch/", "Original recommendations grouped by the specific appeal of Solo Leveling."),
        ("10 shows like Alice in Borderland", "/article/10-shows-like-alice-in-borderland-you-should-watch-next/", "Survival-game and high-stakes series recommendations."),
        ("Christopher Nolan movies in order", "/article/christopher-nolan-movies-order/", "Release order plus a gentler first-time watch path."),
        ("Why Prison Break season one still works", "/article/why-prison-break-season-1-is-still-one-of-the-best-tv-seasons/", "An authored television opinion."),
        ("Nigerian thrillers worth your time", "/article/nigerian-thrillers-worth-your-time/", "A focused entry point to Nigerian thrillers."),
        ("Was Eren Yeager really the villain?", "/article/was-eren-yeager-really-the-villain/", "An authored character argument."),
    ]
    body = f'''<div class="wrap"><nav class="breadcrumb"><a href="/">Home</a> / Watch &amp; Read</nav><section class="page-hero"><p class="kicker"><span class="kicker-dot"></span>Original entertainment editorial</p><h1>Read the argument, not another database card.</h1><p>BRYME's searchable entertainment catalogue has been paused for quality review. Authored recommendations, explainers and opinions remain.</p></section><section class="section"><div class="guide-grid">{cards_for(items)}</div><div class="notice" style="margin-top:28px"><strong>Catalogue status:</strong> title and provider-channel pages are temporarily excluded from Search while descriptions, sources, rights, ratings and availability claims are reviewed.</div></section></div>'''
    write("/articles/", page(title="Entertainment guides and opinions | BRYME", description="Authored BRYME entertainment recommendations, explainers and opinions; the database catalogue is under quality review.", route="/articles/", current="read", body=body, schema_data={"@context": "https://schema.org", "@type": "CollectionPage", "name": "BRYME entertainment guides and opinions", "url": BASE + "/articles/", "dateModified": TODAY, "publisher": {"@type": "Organization", "name": "BRYME", "url": BASE + "/"}}))


def trust_pages() -> None:
    about_body = '''<div class="wrap"><nav class="breadcrumb"><a href="/">Home</a> / About</nav><section class="page-hero"><p class="kicker"><span class="kicker-dot"></span>About BRYME</p><h1>A smaller promise, kept properly.</h1><p>BRYME is an independent Lagos-based editorial project led by Ibrahim Sodiq. It helps Nigerians and Africa-based applicants find source-backed opportunities and practical technology guidance.</p></section><section class="section"><div class="prose"><h2>What changed</h2><p>BRYME previously tried to operate entertainment, football, money and technology products at the same time. A full-site audit on 4 September 2026 found that the publishing surface had grown faster than its verification systems. The site is now being simplified.</p><h2>What BRYME publishes now</h2><ul><li>Dated job roundups linking to exact employer or ATS vacancies.</li><li>Evergreen opportunity guidance with clear limits.</li><li>Practical technology guides with named authors and dates.</li><li>A smaller body of original entertainment editorial.</li></ul><h2>What is paused</h2><p>Sports data pages, generic entertainment title pages and provider-branded “channel” pages are excluded from Search while data accuracy, licensing, rights and editorial value are resolved. BRYME does not stream films or accept job applications.</p><h2>Who is accountable</h2><p>BRYME is created and edited by <a href="/author/ibrahim-sodiq/">Ibrahim Sodiq</a>. Report factual, link or status errors through the <a href="/contact/">Contact page</a>; material changes are recorded in <a href="/corrections/">Corrections</a>.</p></div></section></div>'''
    about_schema = {"@context": "https://schema.org", "@type": "AboutPage", "name": "About BRYME", "url": BASE + "/about/", "dateModified": TODAY, "mainEntity": {"@type": "Organization", "name": "BRYME", "url": BASE + "/", "founder": {"@type": "Person", "name": "Ibrahim Sodiq", "url": BASE + "/author/ibrahim-sodiq/"}}}
    write("/about/", page(title="About BRYME | Source-first opportunities and tech", description="BRYME is an independent Lagos editorial project for source-backed opportunities and practical technology guidance.", route="/about/", current="about", body=about_body, schema_data=about_schema))

    editorial_body = '''<div class="wrap"><nav class="breadcrumb"><a href="/">Home</a> / Editorial policy</nav><section class="page-hero"><p class="kicker"><span class="kicker-dot"></span>Trust standard</p><h1>Editorial policy.</h1><p>How BRYME separates facts, source metadata, first-hand experience, opinion, automation and advertising.</p></section><section class="section"><div class="prose"><h2>People first</h2><p>Every indexable page must solve a distinct reader task. A slug, card grid, feed record or embedded video is not enough by itself.</p><h2>Sources</h2><p>Trust-sensitive claims use direct primary sources where available. Job roundups use exact employer or ATS pages. Pay, location, deadlines and availability are not inferred. Entertainment facts must carry lawful provenance; a public webpage is not automatically a commercial licence.</p><h2>Authorship and dates</h2><p>Articles identify a person or the BRYME Editorial Desk and show published, modified or verified dates as applicable. A build date is not presented as a content update.</p><h2>Opinion and reviews</h2><p>Personal judgments are labelled as opinion. BRYME will not display an editorial score, “Match” percentage or HD/provider badge without a published method and supporting evidence.</p><h2>Automation and AI</h2><p>Automation may help collect candidates, structure records and run quality checks. It may not publish a job, result, factual claim or scaled page without a defined source and human approval. A green automation run must mean the publication step actually succeeded.</p><h2>Advertising</h2><p>Third-party advertising is disabled during the quality rebuild. Any future sponsored or affiliate relationship will be labelled and will not determine editorial conclusions.</p><h2>Corrections</h2><p>Minor spelling fixes may be made silently. Material factual, availability, pay, location or source corrections are recorded in the <a href="/corrections/">corrections log</a>.</p></div></section></div>'''
    write("/editorial-policy/", page(title="Editorial policy | BRYME", description="BRYME's rules for sources, authorship, dates, opinion, automation, advertising and corrections.", route="/editorial-policy/", current="about", body=editorial_body, schema_data={"@context": "https://schema.org", "@type": "WebPage", "name": "BRYME editorial policy", "url": BASE + "/editorial-policy/", "dateModified": TODAY, "publisher": {"@type": "Organization", "name": "BRYME", "url": BASE + "/"}}))

    privacy_body = '''<div class="wrap"><nav class="breadcrumb"><a href="/">Home</a> / Privacy</nav><section class="page-hero"><p class="kicker"><span class="kicker-dot"></span>Privacy</p><h1>Privacy policy.</h1><p>What this website does and does not collect in the current quality-rebuild release.</p></section><section class="section"><div class="prose"><p><b>Effective:</b> 4 September 2026.</p><h2>Analytics and advertising</h2><p>BRYME does not load Google Analytics, Monetag or an AdSense publisher tag in the current release. Advertising and analytics were disabled during the quality rebuild. This policy must be updated before either is reintroduced.</p><h2>Hosting logs</h2><p>BRYME is hosted on Render and delivered through infrastructure that may process technical request data such as IP address, user agent, requested URL and time for security and service operation. BRYME does not receive those details through an analytics dashboard in the current release.</p><h2>Local storage</h2><p>Some legacy interfaces may use browser storage for a chosen theme or interface preference. It is not used by BRYME to create an advertising profile.</p><h2>External links</h2><p>Job applications, official guidelines and video links lead to third parties. Their privacy terms apply once you leave BRYME. BRYME does not collect job applications.</p><h2>Embedded video</h2><p>Retained legacy trailer pages use click-to-load YouTube embeds. A YouTube request should begin only after a visitor intentionally plays a trailer.</p><h2>Contact</h2><p>For a privacy request, email <a href="mailto:Sodiqibrahim03@gmail.com">Sodiqibrahim03@gmail.com</a>. Do not send sensitive job-application documents to BRYME.</p><h2>Future consent controls</h2><p>Before personalized advertising is introduced, BRYME will implement region-appropriate controls and a Google-certified consent-management platform where Google requires one.</p></div></section></div>'''
    write("/privacy/", page(title="Privacy policy | BRYME", description="BRYME's current privacy policy covering disabled analytics and ads, hosting logs, local storage, links and click-to-load video.", route="/privacy/", current="about", body=privacy_body))

    corrections_body = '''<div class="wrap"><nav class="breadcrumb"><a href="/">Home</a> / Corrections</nav><section class="page-hero"><p class="kicker"><span class="kicker-dot"></span>Public record</p><h1>Corrections and material changes.</h1><p>BRYME records changes that alter a reader's understanding of availability, eligibility, pay, provenance or product behavior.</p></section><section class="section"><div class="prose"><h2>4 September 2026 — full-site containment</h2><ul><li>Retired misleading Netflix, Prime Video, Crunchyroll and other provider “channel” collections from Search because they were genre/type approximations rather than verified availability.</li><li>Paused sports routes from Search after identifying a failed merge workflow and incorrect stored goal-difference values.</li><li>Corrected catalogue runtime values for <i>Oppenheimer</i> and <i>The Black Book</i>, and corrected an IMDb source mislabeled as Wikipedia.</li><li>Removed unsupported “Match,” HD, My List and Rate interface claims; renamed Watch Now as Play trailer.</li><li>Disabled GA4 and Monetag while privacy and monetization controls are rebuilt.</li><li>Launched a dated direct-source jobs roundup and excluded a stale Kuda SIWES page plus unresolved location-conflict records.</li></ul><h2>Report an error</h2><p>Email <a href="mailto:Sodiqibrahim03@gmail.com">Sodiqibrahim03@gmail.com</a> with the exact URL, the disputed text and a primary source if possible.</p></div></section></div>'''
    write("/corrections/", page(title="Corrections | BRYME", description="BRYME's public record of material factual, source, availability and product corrections.", route="/corrections/", current="about", body=corrections_body, schema_data={"@context": "https://schema.org", "@type": "WebPage", "name": "BRYME corrections", "url": BASE + "/corrections/", "datePublished": TODAY, "dateModified": TODAY, "publisher": {"@type": "Organization", "name": "BRYME", "url": BASE + "/"}}))

    contact_body = '''<div class="wrap"><nav class="breadcrumb"><a href="/">Home</a> / Contact</nav><section class="page-hero"><p class="kicker"><span class="kicker-dot"></span>Contact the desk</p><h1>Report a problem with evidence.</h1><p>Corrections, closed jobs, broken source links, copyright concerns and privacy requests are welcome.</p></section><section class="section"><div class="prose"><h2>Email</h2><p><a href="mailto:Sodiqibrahim03@gmail.com">Sodiqibrahim03@gmail.com</a></p><h2>Include</h2><ul><li>The exact BRYME page URL.</li><li>The specific claim or link that changed.</li><li>A direct primary source, when available.</li><li>Whether the correction is urgent—for example, a fake application or fee request.</li></ul><p>Do not send CVs, identity documents, passwords, bank details or full job applications to BRYME. Apply only through the official destination linked on the employer page.</p></div></section></div>'''
    write("/contact/", page(title="Contact BRYME | Corrections and source reports", description="Contact BRYME about corrections, closed jobs, broken sources, copyright or privacy.", route="/contact/", current="about", body=contact_body, schema_data={"@context": "https://schema.org", "@type": "ContactPage", "name": "Contact BRYME", "url": BASE + "/contact/", "dateModified": TODAY}))

    disclaimer_body = '''<div class="wrap"><nav class="breadcrumb"><a href="/">Home</a> / Disclaimer</nav><section class="page-hero"><p class="kicker"><span class="kicker-dot"></span>Important limits</p><h1>Disclaimer.</h1><p>Source checks reduce uncertainty; they do not remove it.</p></section><section class="section"><div class="prose"><h2>Jobs and opportunities</h2><p>BRYME is not an employer, recruiter or placement agency and does not accept applications. An open page does not guarantee continued availability, eligibility, an interview, project allocation or earnings. Never pay to apply for a job.</p><h2>Money and technology guidance</h2><p>Content is general information, not financial, legal, tax or professional advice. Products, fees, laws and platform terms can change; verify decisions independently.</p><h2>Entertainment</h2><p>BRYME does not stream films. Third-party video and availability information can change. Legacy catalogue pages are under review and excluded from Search.</p><h2>External websites</h2><p>Third parties control their content, applications, cookies and terms. A link is a source or route to apply, not a guarantee or endorsement.</p></div></section></div>'''
    write("/disclaimer/", page(title="Disclaimer | BRYME", description="Important limits on BRYME job checks, opportunity guidance, technology content and external links.", route="/disclaimer/", current="about", body=disclaimer_body))

    terms_body = '''<div class="wrap"><nav class="breadcrumb"><a href="/">Home</a> / Terms</nav><section class="page-hero"><p class="kicker"><span class="kicker-dot"></span>Terms of use</p><h1>Use BRYME responsibly.</h1><p>These terms describe the current editorial website.</p></section><section class="section"><div class="prose"><p><b>Effective:</b> 4 September 2026.</p><h2>Informational service</h2><p>BRYME provides editorial information and links. It is not a party to an employment, application, purchase, platform or viewing agreement.</p><h2>No guarantee</h2><p>Information can change after verification. You are responsible for checking the current source and protecting your personal information.</p><h2>Permitted use</h2><p>You may read and share links to BRYME. Do not scrape, republish or present BRYME's original editorial work as your own, and do not use the service to distribute malware, impersonate an employer or collect fraudulent fees.</p><h2>Third-party rights</h2><p>Names and trademarks belong to their owners. External links remain subject to the destination's terms.</p><h2>Corrections and contact</h2><p>Use the <a href="/contact/">Contact page</a> for corrections, rights concerns or questions.</p></div></section></div>'''
    write("/terms/", page(title="Terms of use | BRYME", description="Terms for using BRYME's editorial information, source links and original content.", route="/terms/", current="about", body=terms_body))


if __name__ == "__main__":
    home()
    jobs_index()
    jobs_roundup()
    jobs_method()
    tech_hub()
    money_hub()
    articles_hub()
    trust_pages()

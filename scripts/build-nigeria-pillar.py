#!/usr/bin/env python3
"""BRYME · Build the 'How to make money online in Nigeria' pillar (backlog cluster 5).
Uses only the verified 20-platform database + selector guide. No invented facts.
"""
import json, os, re, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def esc(s): return H.escape(str(s), quote=True)

platforms = json.load(open('/tmp/platforms.json'))
ng = [p for p in platforms if 'nigeria' in p['countries'].lower()]

def ng_rows():
    rows = []
    for p in ng:
        rows.append(
            '<tr><td><a href="' + esc(p['url']) + '" rel="nofollow noopener" target="_blank"><b>' + esc(p['name']) + '</b></a></td>'
            '<td>' + esc(p['cat']) + '</td>'
            '<td>' + esc(p['pay']) + '</td>'
            '<td>' + esc(p['req'][:90]) + '…</td>'
            '<td>' + esc(p['payMethod']) + '</td></tr>'
        )
    return ''.join(rows)

def build():
    dirp = os.path.join(ROOT, 'make-money', 'make-money-online-nigeria')
    os.makedirs(dirp, exist_ok=True)
    p = os.path.join(dirp, 'index.html')

    title = 'How to Make Money Online in Nigeria | BRYME'
    meta = 'A factual guide to making money online in Nigeria in 2026: verified platforms that accept Nigerians, real pay ranges, universal scam rules and red flags. No shortcuts, no invented promises.'

    main = (
        '<main class="shell">'
        '<div class="crumb"><a href="/">Home</a> / <a href="/make-money/">BRYME Make Money</a> / How to Make Money Online in Nigeria</div>'
        '<section class="article-hero article-hero-photo" style="--hero-img:url(\'/assets/img/money/hero-beginner.jpg\')">'
        '<div class="eyebrow">Make Money \u00b7 Nigeria</div>'
        '<h1>How to Make Money Online in Nigeria</h1>'
        '<p class="lead">The honest version: which platforms actually accept Nigerians, what they really pay, the rules that apply everywhere, and the red flags that should make you walk away. Every platform on this page is verified \u2014 nothing here is a guarantee of acceptance or payment.</p>'
        '<div class="article-meta"><span>By BRYME Editorial</span><span>Last verified 22 August 2026</span></div></section>'

        '<article class="prose article-body">'
        '<h2>The short version</h2>'
        '<p>Five platforms on the BRYME database explicitly list Nigeria as an accepted country: <b>Outlier AI, Mindrift, Alignerr, Prolific and Remotasks</b>. Several more accept a broad country list that almost always includes Nigeria \u2014 Appen (170+ countries), Clickworker (136), TELUS Digital (100+), OneForma (global) and Toloka (100+ including most of Africa) \u2014 but you should verify at signup, because eligibility changes often.</p>'
        '<p>The realistic picture: pay is <b>region-tiered</b> \u2014 the same task that pays a US contributor $30/hr can pay a Nigerian contributor $10/hr. That is standard industry practice across Outlier, Mindrift and most of this space, not a scam. And <b>task availability</b>, not the advertised hourly rate, is the real bottleneck: the queue empties unpredictably, so the realistic model is running two or three platforms at once.</p>'

        '<h2>Platforms that accept Nigerians (verified 22 Aug 2026)</h2>'
        '<div class="sp-table-wrap"><table class="sp-table"><thead><tr><th>Platform</th><th>Type</th><th>Pay (USD/hr)</th><th>Requirements</th><th>Payout</th></tr></thead><tbody>'
        + ng_rows() +
        '</tbody></table></div>'
        '<p class="sp-result-meta">Full detail \u2014 registration steps, key rules, red flags and official links \u2014 for all 20 platforms lives on the <a href="/make-money/platform-reviews/">Platform Reviews</a> page, which you can filter by country.</p>'

        '<h2>The six rules that apply no matter where you are</h2>'
        '<ol>'
        '<li><b>No legitimate platform charges you to join.</b> Not for a \u201cstarter kit\u201d, not for \u201cpremium access\u201d. If a page asks for payment before you can work, it is not legit.</li>'
        '<li><b>Nobody needs your bank password.</b> Payment setup only ever needs your PayPal email, bank account/routing number, or Payoneer/Wise \u2014 never bank login credentials.</li>'
        '<li><b>Unpaid assessments are normal \u2014 budget the time.</b> DataAnnotation\u2019s qualifying test is 1\u20133 hours with a low pass rate. Appen\u2019s exams run 20\u201350 questions. Treat a failed assessment as data, not a loss.</li>'
        '<li><b>Pay is region-tiered \u2014 expect it.</b> Identical work pays different rates by country. It is standard, it is not personal, and it is worth knowing before you start so the first payslip does not feel like a scam.</li>'
        '<li><b>Task availability beats hourly rate.</b> The money is real but the queue empties unpredictably. Run 2\u20133 platforms, not one.</li>'
        '<li><b>\u201cLegit but inconsistent\u201d is not \u201cnot legit\u201d.</b> Complaints across these platforms are mostly about empty task queues, not stolen wages. That distinction is your most useful filter.</li>'
        '</ol>'

        '<h2>Red flags that should end the conversation</h2>'
        '<p>These patterns are enough to walk away from any page, platform or \u201cmentor\u201d claiming to get you rich:</p>'
        '<ul>'
        '<li>Any upfront payment \u2014 \u201cstarter kit\u201d, \u201cpremium access\u201d, \u201cregistration fee\u201d.</li>'
        '<li>Requests for your bank login or OTP \u2014 legitimate platforms never need these.</li>'
        '<li>\u201cMake \u20a6500,000 in seven days with no skills\u201d \u2014 excitement is the sales pitch, not the product.</li>'
        '<li>An \u201cOutlier\u201d, \u201cAppen\u201d or other known-name page that asks for a fee or crypto \u2014 it is an impersonator, not the platform.</li>'
        '<li>Pressure to act fast, or payment via gift cards or crypto to a \u201cthird party\u201d.</li>'
        '</ul>'

        '<h2>Where the writing money is</h2>'
        '<p>AI and microtask platforms are one lane. The other is paid writing: publications that pay for essays, fiction and reported pieces \u2014 many with no nationality restriction. BRYME keeps a <a href="/make-money/writing-opportunities/">verified, country-filtered list of writing opportunities</a> with pay rates, word counts and official submission links. For a Nigerian writer, the combination of a couple of AI platforms for steady income plus one or two paying publications for skill-building is the most honest \u201cstrategy\u201d there is.</p>'

        '<h2>What actually works</h2>'
        '<p>Nothing on this page is a shortcut, because shortcuts are not real. What works is the same boring combination everywhere: build one useful skill (writing, coding, design, data, AI-assisted work), keep your profile honest, apply to several verified platforms, treat unpaid assessments as part of the process, and let reputation compound. The <a href="/make-money/beginners-guide-to-making-money-online/">Beginner\u2019s Guide to Making Money Online</a> covers the skill-building side in full.</p>'
        '</article>'

        '<section class="sp-related"><h2>Related</h2><div class="sp-rel-grid">'
        '<a class="sp-rel" href="/make-money/platform-reviews/">Platform Reviews (filter by country)</a>'
        '<a class="sp-rel" href="/make-money/writing-opportunities/">Writing opportunities</a>'
        '<a class="sp-rel" href="/make-money/beginners-guide-to-making-money-online/">Beginner\u2019s guide</a>'
        '<a class="sp-rel" href="/make-money/">BRYME Make Money</a>'
        '</div></section>'
        '</main>'
    )

    ld = json.dumps([{
        "@context": "https://schema.org", "@type": "Article",
        "headline": "How to Make Money Online in Nigeria",
        "description": meta,
        "datePublished": "2026-08-22", "dateModified": "2026-08-22",
        "author": {"@type": "Organization", "name": "BRYME Editorial"},
        "publisher": {"@type": "Organization", "name": "BRYME"},
        "mainEntityOfPage": "https://bryme.onrender.com/make-money/make-money-online-nigeria/"
    }, {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://bryme.onrender.com/"},
            {"@type": "ListItem", "position": 2, "name": "Make Money", "item": "https://bryme.onrender.com/make-money/"},
            {"@type": "ListItem", "position": 3, "name": "How to Make Money Online in Nigeria", "item": "https://bryme.onrender.com/make-money/make-money-online-nigeria/"}
        ]
    }], ensure_ascii=False, separators=(',', ':'))

    # Clone a valid HTML shell from an existing make-money guide page
    shell = open(os.path.join(ROOT, 'make-money/beginners-guide-to-making-money-online/index.html'), encoding='utf-8').read()
    i = shell.find('<main'); j = shell.find('</main>')
    head = shell[:i]
    tail = shell[j + len('</main>'):]
    # rewrite head SEO
    head = re.sub(r'<title>.*?</title>', f'<title>{esc(title)}</title>', head, count=1, flags=re.S)
    head = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{esc(meta)}"', head, count=1)
    head = re.sub(r'rel="canonical" href="[^"]*"', 'rel="canonical" href="https://bryme.onrender.com/make-money/make-money-online-nigeria/"', head, count=1)
    head = re.sub(r'<meta property="og:title" content="[^"]*"', f'<meta property="og:title" content="{esc(title)}"', head, count=1)
    head = re.sub(r'<meta name="twitter:title" content="[^"]*"', f'<meta name="twitter:title" content="{esc(title)}"', head, count=1)
    head = re.sub(r'<meta property="og:description" content="[^"]*"', f'<meta property="og:description" content="{esc(meta)}"', head, count=1)
    head = re.sub(r'<meta name="twitter:description" content="[^"]*"', f'<meta name="twitter:description" content="{esc(meta)}"', head, count=1)
    head = re.sub(r'<meta property="og:url" content="[^"]*"', '<meta property="og:url" content="https://bryme.onrender.com/make-money/make-money-online-nigeria/"', head, count=1)
    # swap JSON-LD
    if '<script type="application/ld+json">' in head:
        head = re.sub(r'<script type="application/ld\+json">.*?</script>', f'<script type="application/ld+json">{ld}</script>', head, count=1, flags=re.S)
    else:
        head = head.replace('</head>', f'<script type="application/ld+json">{ld}</script></head>', 1)

    out = head + main + tail
    open(p, 'w', encoding='utf-8').write(out)
    print("built make-money-online-nigeria:", len(out))

if __name__ == '__main__':
    build()

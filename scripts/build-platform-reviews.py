#!/usr/bin/env python3
"""BRYME · Build make-money/platform-reviews from the legit-platforms database + selector guide."""
import json, os, re, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def esc(s): return H.escape(str(s), quote=True)

platforms = json.load(open('/tmp/platforms.json'))

# ---- universal rules (from the nationality-selector guide) ----
rules = [
    ("No legitimate platform charges you to join", "Not for a \u201cstarter kit\u201d, not for \u201cpremium access\u201d, not for anything. If a page asks for payment before you can work, it is not on this list and it is not legit."),
    ("Nobody needs your bank password", "Payment setup only ever requires your PayPal email, bank account/routing number, or a payout service like Payoneer/Wise \u2014 never login credentials to your bank itself."),
    ("Unpaid assessments are normal, but know the time cost upfront", "DataAnnotation\u2019s is 1\u20133 hours with a low pass rate. Appen\u2019s exams run 20\u201350 questions. Budget the time before starting, and treat a failed assessment as data, not a loss."),
    ("Pay is very often region-tiered", "The same task can pay a US contributor $30/hr and a Nigerian contributor $10/hr for identical work. This is standard across Outlier, Mindrift and most of the industry \u2014 worth stating plainly so nobody feels singled out."),
    ("Task availability beats hourly rate as the real bottleneck", "The money is real, but the queue empties out unpredictably. The realistic model is running 2\u20133 platforms at once, not depending on one."),
    ("\u201cLegit but inconsistent\u201d and \u201cnot legit\u201d are different categories", "Complaints across nearly all these platforms are about empty task queues, not stolen wages. That distinction is the single most useful filter for a first-time visitor."),
]

def rules_html():
    items = ''.join(f'<li><b>{esc(t)}</b> \u2014 {esc(d)}</li>' for t, d in rules)
    return ('<div class="sp-msec"><b>Universal rules \u2014 apply on every platform</b><ul>' + items + '</ul></div>')

def platform_cards():
    cards = []
    for p in platforms:
        cards.append(
            '<div class="pr-card" data-pr="' + esc(p['name'].lower()) + '" data-pr-cat="' + esc(p['cat'].lower()) + '" data-pr-country="' + esc(p['countries'].lower()) + '">'
            '<div class="pr-head"><div><b>' + esc(p['name']) + '</b>'
            '<span class="pr-owner">' + esc(p['owner']) + '</span></div>'
            '<span class="pr-cat">' + esc(p['cat']) + '</span></div>'
            '<dl>'
            '<div><dt>Countries</dt><dd>' + esc(p['countries']) + '</dd></div>'
            '<div><dt>Pay</dt><dd>' + esc(p['pay']) + '</dd></div>'
            '<div><dt>Requirements</dt><dd>' + esc(p['req']) + '</dd></div>'
            '<div><dt>Registration</dt><dd>' + esc(p['steps']) + '</dd></div>'
            '<div><dt>Payment</dt><dd>' + esc(p['payMethod']) + ((' \u00b7 threshold ' + esc(p['threshold'])) if p['threshold'] else '') + '</dd></div>'
            '<div class="pr-rules"><dt>Key rules</dt><dd>' + esc(p['rules']) + '</dd></div>'
            '<div class="pr-flags"><dt>Red flags to know</dt><dd>' + esc(p['flags']) + '</dd></div>'
            '</dl>'
            '<p class="pr-url">Official site: <a href="' + esc(p['url']) + '" rel="nofollow noopener" target="_blank">' + esc(p['url']) + '</a></p>'
            '</div>'
        )
    return ''.join(cards)

# country list for the filter dropdown (common countries from data)
country_list = ['Nigeria', 'Kenya', 'Ghana', 'South Africa', 'Egypt', 'United States', 'United Kingdom', 'Canada', 'Australia', 'India', 'Philippines', 'Germany', 'France']

def build():
    p = os.path.join(ROOT, 'make-money/platform-reviews/index.html')
    s = open(p, encoding='utf-8').read()

    # ---- SEO head ----
    s = re.sub(r'<title>.*?</title>',
               '<title>20 Legit Earning Platforms by Country | BRYME</title>', s, count=1, flags=re.S)
    meta = "20 legitimate earning platforms reviewed with country eligibility, pay ranges, requirements, payment methods, red flags and official links. Updated with verification dates."
    s = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{esc(meta)}"', s, count=1)
    s = re.sub(r'<meta property="og:title" content="[^"]*"', '<meta property="og:title" content="20 Legit Earning Platforms by Country | BRYME"', s, count=1)
    s = re.sub(r'<meta name="twitter:title" content="[^"]*"', '<meta name="twitter:title" content="20 Legit Earning Platforms by Country | BRYME"', s, count=1)
    s = re.sub(r'<meta property="og:description" content="[^"]*"', f'<meta property="og:description" content="{esc(meta)}"', s, count=1)
    s = re.sub(r'<meta name="twitter:description" content="[^"]*"', f'<meta name="twitter:description" content="{esc(meta)}"', s, count=1)

    data_json = json.dumps(platforms, ensure_ascii=False)

    main = (
        '<main class="shell">'
        '<div class="crumb"><a href="/">Home</a> / <a href="/make-money/">BRYME Make Money</a> / Platform Reviews</div>'
        '<section class="hero vhero vhero-make-money vhero-photo" data-vertical="make-money" style="--hero-img:url(\'/assets/img/money/hero-writing.jpg\')">'
        '<div class="eyebrow">\U0001F4B0 BRYME Make Money \u00b7 Platform Reviews</div>'
        '<h1>20 Legit Earning Platforms, by Country</h1>'
        '<p class="lead">A real answer \u2014 not a wall of affiliate links. Country eligibility, pay, requirements, payment methods, red flags and the official site for each platform. Every entry carries a \u201clast verified\u201d date because this space changes every few months.</p>'
        '</section>'

        '<section class="section">'
        '<div class="sp-truth"><b>How to read this list.</b><p>Each platform shows: <b>countries accepted</b> (verify at signup \u2014 eligibility changes often), <b>pay range</b> (region-tiered, so your actual rate depends on where you are), <b>requirements and registration steps</b> (including unpaid assessments where they exist), <b>payment method and threshold</b>, and the <b>red flags</b> specific to that platform. Nothing here is a guarantee of acceptance or payment \u2014 it is the honest picture before you sign up.</p></div>'
        '<div class="sp-msec-grid">' + rules_html() + '</div>'
        '</section>'

        '<section class="section" id="platforms">'
        '<div class="section-head"><div><div class="eyebrow">The database</div><h2>Platform Reviews</h2>'
        '<p class="section-note">' + str(len(platforms)) + ' platforms, verified 22 August 2026. Filter by country or search by name.</p></div></div>'
        '<div class="pr-toolbar">'
        '<input id="pr-q" class="searchbox" style="max-width:340px;margin:0" placeholder="Search platforms\u2026" aria-label="Search platforms">'
        '<select id="pr-country" class="stabs" style="background:#101318;border:1px solid var(--line);color:var(--text);padding:10px 14px;border-radius:8px;font:inherit" aria-label="Filter by country">'
        '<option value="">All countries</option>' + ''.join(f'<option value="{esc(c.lower())}">{esc(c)}</option>' for c in country_list) + '</select>'
        '<span class="pr-count" id="pr-count" style="font-size:13px;color:var(--muted);font-weight:700"></span></div>'
        '<div class="pr-grid" id="pr-grid">' + platform_cards() + '</div>'
        '</section>'

        '<section class="section"><div class="vnote"><b>Last verified:</b> 22 August 2026. Eligibility and pay figures fluctuate \u2014 the official platform page is the source of truth. Toloka\u2019s crowd work folded into Mindrift in 2026, and MTurk is closed to new signups. A few of these change ownership and policy every few months, so always check the official URL before investing assessment time.</div></section>'

        '<section class="section core-hubs" data-core-hubs><div class="section-head"><h2>Also on BRYME</h2></div><p class="section-note">The main sections of the site.</p>'
        '<div class="vcat-grid">'
        '<a class="vcat" href="/make-money/"><b>\U0001F4B0 Make Money</b><span>Verified paid opportunities, filtered by your country.</span></a>'
        '<a class="vcat" href="/make-money/writing-opportunities/"><b>\u270D\uFE0F Writing opportunities</b><span>Publications that pay for writing \u2014 country-filtered.</span></a>'
        '<a class="vcat" href="/make-money/freelance-platform-fees-explained/"><b>Freelance platform fees</b><span>What platforms actually take from your earnings.</span></a>'
        '</div></section>'
        '</main>'

        '<script type="application/json" id="pr-data">' + data_json + '</script>'
        '<script>(function(){'
        'var grid=document.getElementById("pr-grid"),q=document.getElementById("pr-q"),c=document.getElementById("pr-country"),cnt=document.getElementById("pr-count");'
        'function apply(){var t=(q.value||"").toLowerCase().trim(),cc=c.value,shown=0;'
        'Array.prototype.forEach.call(grid.querySelectorAll(".pr-card"),function(card){'
        'var ok=1;'
        'if(cc&&card.getAttribute("data-pr-country").indexOf(cc)===-1)ok=0;'
        'if(t){var blob=(card.getAttribute("data-pr")+" "+card.getAttribute("data-pr-cat")).toLowerCase();'
        'var toks=t.split(/\\s+/);for(var i=0;i<toks.length;i++){if(blob.indexOf(toks[i])===-1){ok=0;break;}}}'
        'card.style.display=ok?"":"none";if(ok)shown++;});'
        'cnt.textContent=shown+" of "+grid.querySelectorAll(".pr-card").length+" platforms";}'
        'q.addEventListener("input",apply);c.addEventListener("change",apply);apply();})();</script>'
    )

    i = s.find('<main'); j = s.find('</main>')
    if i < 0 or j < 0:
        print("NO MAIN"); return
    s = s[:i] + main + s[j + len('</main>'):]
    # add JSON-LD
    ld = json.dumps([{
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "20 Legit Earning Platforms by Country",
        "description": meta,
        "url": "https://bryme.onrender.com/make-money/platform-reviews/",
        "isPartOf": {"@type": "WebSite", "name": "BRYME"}
    }], ensure_ascii=False, separators=(',', ':'))
    if '<script type="application/ld+json">' in s:
        s = re.sub(r'<script type="application/ld\+json">.*?</script>', f'<script type="application/ld+json">{ld}</script>', s, count=1, flags=re.S)
    else:
        s = s.replace('</head>', f'<script type="application/ld+json">{ld}</script></head>', 1)

    open(p, 'w', encoding='utf-8').write(s)
    print("platform-reviews rebuilt, len:", len(s))

if __name__ == '__main__':
    build()

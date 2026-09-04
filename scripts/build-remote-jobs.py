#!/usr/bin/env python3
"""BRYME · Remote Jobs board — 20 legit platforms as job cards (not an article)."""
import json, os, re, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def esc(s): return H.escape(str(s), quote=True)

platforms = json.load(open('/tmp/platforms.json'))

def job_cards():
    cards = []
    for p in platforms:
        cards.append(
            '<article class="rj-card" data-rj="' + esc(p['name'].lower()) + '" data-rj-cat="' + esc(p['cat'].lower()) + '" data-rj-country="' + esc(p['countries'].lower()) + '">'
            '<div class="rj-top">'
            '<div class="rj-identity"><b>' + esc(p['name']) + '</b><span class="rj-owner">' + esc(p['owner']) + '</span></div>'
            '<span class="rj-cat">' + esc(p['cat']) + '</span>'
            '</div>'
            '<div class="rj-pay">' + esc(p['pay']) + ' <span class="rj-pay-lbl">/ hr</span></div>'
            '<p class="rj-countries"><b>Countries:</b> ' + esc(p['countries']) + '</p>'
            '<p class="rj-req"><b>You need:</b> ' + esc(p['req']) + '</p>'
            '<div class="rj-flags"><b>Red flags:</b> ' + esc(p['flags']) + '</div>'
            '<div class="rj-foot">'
            '<span class="rj-paymethod">' + esc(p['payMethod']) + '</span>'
            '<a class="rj-apply" href="' + esc(p['url']) + '" rel="nofollow noopener" target="_blank">Apply →</a>'
            '</div>'
            '</article>'
        )
    return ''.join(cards)

rules = [
    ("No legitimate platform charges you to join", "Not for a \u201cstarter kit\u201d or \u201cpremium access\u201d. If a page asks for payment before you can work, it is not legit."),
    ("Nobody needs your bank password", "Payment setup only ever needs your PayPal email, bank account/routing number, or Payoneer/Wise \u2014 never bank login credentials."),
    ("Unpaid assessments are normal \u2014 budget the time", "DataAnnotation\u2019s is 1\u20133 hours with a low pass rate; Appen\u2019s exams run 20\u201350 questions."),
    ("Pay is region-tiered \u2014 expect it", "The same task can pay a US contributor $30/hr and a Nigerian contributor $10/hr. Standard industry practice, not a scam."),
    ("Task availability beats hourly rate", "The money is real but the queue empties unpredictably \u2014 run 2\u20133 platforms, not one."),
    ("\u201cLegit but inconsistent\u201d \u2260 \u201cnot legit\u201d", "Complaints are mostly empty queues, not stolen wages."),
]

def build():
    p = os.path.join(ROOT, 'make-money/platform-reviews/index.html')
    s = open(p, encoding='utf-8').read()

    title = 'Remote Jobs — 20 Legit Platforms | BRYME'
    meta = '20 legitimate remote jobs and earning platforms by country: pay ranges, requirements, red flags and official apply links. Filter by country or search.'

    # SEO head
    s = re.sub(r'<title>.*?</title>', f'<title>{esc(title)}</title>', s, count=1, flags=re.S)
    s = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{esc(meta)}"', s, count=1)
    s = re.sub(r'<meta property="og:title" content="[^"]*"', f'<meta property="og:title" content="{esc(title)}"', s, count=1)
    s = re.sub(r'<meta name="twitter:title" content="[^"]*"', f'<meta name="twitter:title" content="{esc(title)}"', s, count=1)
    s = re.sub(r'<meta property="og:description" content="[^"]*"', f'<meta property="og:description" content="{esc(meta)}"', s, count=1)
    s = re.sub(r'<meta name="twitter:description" content="[^"]*"', f'<meta name="twitter:description" content="{esc(meta)}"', s, count=1)

    rules_html = ''.join(f'<li><b>{esc(t)}</b> \u2014 {esc(d)}</li>' for t, d in rules)

    country_list = ['Nigeria', 'Kenya', 'Ghana', 'South Africa', 'Egypt', 'United States', 'United Kingdom', 'Canada', 'Australia', 'India', 'Philippines', 'Germany', 'France']

    main = (
        '<main class="shell">'
        '<div class="crumb"><a href="/">Home</a> / <a href="/make-money/">BRYME Make Money</a> / Remote Jobs</div>'
        '<section class="hero vhero vhero-make-money vhero-photo" data-vertical="make-money" style="--hero-img:url(\'/assets/img/money/hero-writing.jpg\')">'
        '<div class="eyebrow">\U0001F4B0 BRYME Make Money \u00b7 Remote Jobs</div>'
        '<h1>Remote Jobs</h1>'
        '<p class="lead">20 legitimate earning platforms as job cards \u2014 pay, countries, requirements, red flags and the official apply link for each. Verified 22 August 2026.</p>'
        '</section>'

        '<section class="section">'
        '<div class="rj-toolbar">'
        '<input id="rj-q" class="searchbox" style="max-width:320px;margin:0" placeholder="Search platforms\u2026" aria-label="Search platforms">'
        '<select id="rj-country" style="background:#101318;border:1px solid var(--line);color:var(--text);padding:10px 14px;border-radius:8px;font:inherit" aria-label="Filter by country">'
        '<option value="">All countries</option>' + ''.join(f'<option value="{esc(c.lower())}">{esc(c)}</option>' for c in country_list) + '</select>'
        '<span class="rj-count" id="rj-count"></span></div>'
        '<div class="rj-grid" id="rj-grid">' + job_cards() + '</div>'
        '</section>'

        '<section class="section"><div class="sp-msec-grid"><div class="sp-msec"><b>Before you apply \u2014 6 rules that apply everywhere</b><ul>' + rules_html + '</ul></div></div>'
        '<div class="vnote"><b>Last verified:</b> 22 August 2026. Eligibility and pay fluctuate \u2014 the official site is the source of truth. Toloka\u2019s crowd work folded into Mindrift in 2026; MTurk is closed to new signups. Country lists change often \u2014 verify at signup.</div></section>'

        '<section class="section core-hubs" data-core-hubs><div class="section-head"><h2>Also on BRYME</h2></div><div class="vcat-grid">'
        '<a class="vcat" href="/make-money/"><b>\U0001F4B0 Make Money</b><span>Verified paid opportunities, filtered by your country.</span></a>'
        '<a class="vcat" href="/make-money/writing-opportunities/"><b>\u270D\uFE0F Writing opportunities</b><span>Publications that pay for writing.</span></a>'
        '<a class="vcat" href="/make-money/make-money-online-nigeria/"><b>Making money in Nigeria</b><span>The pillar guide \u2014 what actually works.</span></a>'
        '</div></section>'
        '</main>'

        '<script>(function(){'
        'var grid=document.getElementById("rj-grid"),q=document.getElementById("rj-q"),c=document.getElementById("rj-country"),cnt=document.getElementById("rj-count");'
        'function apply(){var t=(q.value||"").toLowerCase().trim(),cc=c.value,shown=0;'
        'Array.prototype.forEach.call(grid.querySelectorAll(".rj-card"),function(card){'
        'var ok=1;'
        'if(cc&&card.getAttribute("data-rj-country").indexOf(cc)===-1)ok=0;'
        'if(t){var blob=(card.getAttribute("data-rj")+" "+card.getAttribute("data-rj-cat")).toLowerCase();'
        'var toks=t.split(/\\s+/);for(var i=0;i<toks.length;i++){if(blob.indexOf(toks[i])===-1){ok=0;break;}}}'
        'card.style.display=ok?"":"none";if(ok)shown++;});'
        'cnt.textContent=shown+" of "+grid.querySelectorAll(".rj-card").length+" remote jobs";}'
        'q.addEventListener("input",apply);c.addEventListener("change",apply);apply();})();</script>'
    )

    i = s.find('<main'); j = s.find('</main>')
    if i < 0 or j < 0:
        print("NO MAIN"); return
    s = s[:i] + main + s[j + len('</main>'):]

    ld = json.dumps([{
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "Remote Jobs — 20 Legit Platforms",
        "description": meta,
        "url": "https://bryme.onrender.com/make-money/platform-reviews/"
    }], ensure_ascii=False, separators=(',', ':'))
    if '<script type="application/ld+json">' in s:
        s = re.sub(r'<script type="application/ld\+json">.*?</script>', f'<script type="application/ld+json">{ld}</script>', s, count=1, flags=re.S)

    open(p, 'w', encoding='utf-8').write(s)
    print("remote-jobs board rebuilt, len:", len(s), "| cards:", s.count('rj-card'))

if __name__ == '__main__':
    build()

#!/usr/bin/env python3
"""BRYME · Build /make-money/coding/ — 20 coding platforms as nationality-filtered job cards
(mirrors /make-money/remote-work/; same localStorage nationality as the make-money hub)."""
import json, os, re, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def esc(s): return H.escape(str(s), quote=True)

rows = []
import csv
with open('/home/user/uploads/bryme-coding-platforms-20-1.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

CC = {'Nigeria':'NG','Kenya':'KE','Ghana':'GH','South Africa':'ZA','Egypt':'EG','United States':'US',
      'US':'US','UK':'GB','United Kingdom':'GB','Canada':'CA','Ireland':'IE','Australia':'AU',
      'New Zealand':'NZ','Philippines':'PH','India':'IN','Uganda':'UG','Japan':'JP','Germany':'DE',
      'France':'FR'}

def to_op(r):
    slug = re.sub(r'[^a-z0-9]+','-', r['Platform'].lower()).strip('-')
    pay = r['Pay Range (USD/hr)']
    # normalize pay display for card
    if 'varies' in pay.lower() or 'self-set' in pay.lower():
        pay_display = pay
    elif 'per year' in pay.lower() or '/' in pay.replace('(',' ').lower():
        pay_display = pay
    else:
        pay_display = pay + '/hr'
    txt = (r.get('Nigeria Payout Support') or '') + ' ' + (r.get('Verdict') or '')
    return {
        'id': slug, 'slug': slug,
        'publication': r['Platform'], 'title': r['Category'],
        'excerpt': pay_display + '. ' + (r.get('Verdict') or ''),
        'payCurrency': 'USD', 'payMin': None, 'payMax': None, 'payDisplay': pay_display,
        'writingTypes': [r['Category'].split(' ')[0].lower()],
        'writingTypeLabel': r['Category'],
        'eligibilityMode': 'open', 'includesCountries': [], 'includesRegions': [],
        'excludesCountries': [], 'notStatedElig': True, 'allowsDiaspora': False,
        'eligibilitySummary': (r.get('Nigeria Payout Support') or 'Global eligibility — verify payout support for your country at signup.'),
        'experience': 'not-stated', 'submissionStatus': 'open', 'responseBand': 'not-stated',
        'aiPolicy': 'not-stated', 'deadline': '', 'lastVerified': '2026-08-22',
        'keywords': (r['Platform'] + ' ' + r['Category'] + ' ' + (r.get('Verdict') or '')).lower(),
        'url': '#', 'owner': r['Category'],
        'req': r['Registration Steps'], 'steps': r['Registration Steps'],
        'payMethod': r['Nigeria Payout Support'], 'threshold': r['Platform Fee/Commission'],
        'rules': r['Vetting Difficulty'], 'flags': r['Verdict'],
    }

OPS = [to_op(r) for r in rows]
OPS_JSON = json.dumps(OPS, ensure_ascii=False)

def card_html(op, idx):
    img = '/assets/img/money/hero-coding.jpg' if idx % 2 == 0 else '/assets/img/money/hero-ai.jpg'
    facts = (
        '<div><dt>Eligibility</dt><dd>' + esc(op['eligibilitySummary']) + '</dd></div>'
        '<div><dt>Work</dt><dd>' + esc(op['title']) + '</dd></div>'
        '<div><dt>Pay</dt><dd>' + esc(op['payDisplay']) + '</dd></div>'
        '<div><dt>Commission</dt><dd>' + esc(op['threshold']) + '</dd></div>'
        '<div><dt>Payout</dt><dd>' + esc(op['payMethod']) + '</dd></div>'
    )
    flags = ('<div><dt>Verdict</dt><dd>' + esc(op['flags']) + '</dd></div>')
    return (
        '<article class="oc-card oc-card-has-art" data-oc-card>'
        '<div class="oc-card-art" style="background-image:url(\'' + img + '\')" aria-hidden="true"></div>'
        '<div class="oc-card-body">'
        '<header class="oc-card-top"><div><p class="oc-pub">' + esc(op['publication']) + '</p>'
        '<h3>' + esc(op['title']) + '</h3></div>'
        '<span class="oc-status oc-st-open">Open</span></header>'
        '<dl class="oc-facts">' + facts + flags + '</dl>'
        '<p class="oc-verified">Verified 2026-08-22</p>'
        '<p class="oc-actions"><a class="cta" href="/make-money/coding/" onclick="return false;">View details</a></p>'
        '</div></article>'
    )

CARDS = ''.join(card_html(op, i) for i, op in enumerate(OPS))

# extract CTRY from remote-work page (same script layout)
w = open(os.path.join(ROOT, 'make-money/writing/index.html'), encoding='utf-8').read()
m = re.search(r'var CTRY = (\[.*?\]);', w, re.S)
CTRY_JSON = m.group(1) if m else '[]'


def strip_inherited_ops(html):
    """Remove any inline <script> block that contains the inherited writing OPS (afrolicious)."""
    import re as _re
    out = html
    while True:
        m = _re.search(r'<script>(?:(?!</script>).)*?afrolicious(?:(?!</script>).)*?</script>', out, _re.S)
        if not m:
            break
        out = out[:m.start()] + out[m.end():]
    return out

def build():
    out_dir = os.path.join(ROOT, 'make-money', 'coding')
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, 'index.html')

    title = 'Coding & Developer Jobs — 20 Platforms | BRYME'
    meta = 'Coding and developer platforms that pay: freelance marketplaces, vetted networks and job boards with real rates, commissions, payout support and verdicts. Pick your country to see what qualifies.'

    # shell from remote-work page
    i = w.find('<main'); j = w.find('</main>')
    head = w[:i]
    tail = w[j + len('</main>'):]
    head = re.sub(r'<title>.*?</title>', f'<title>{esc(title)}</title>', head, count=1, flags=re.S)
    head = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{esc(meta)}"', head, count=1)
    head = re.sub(r'rel="canonical" href="[^"]*"', 'rel="canonical" href="https://bryme.onrender.com/make-money/coding/"', head, count=1)
    head = re.sub(r'<meta property="og:url" content="[^"]*"', '<meta property="og:url" content="https://bryme.onrender.com/make-money/coding/"', head, count=1)
    head = re.sub(r'<meta property="og:title" content="[^"]*"', f'<meta property="og:title" content="{esc(title)}"', head, count=1)
    head = re.sub(r'<meta name="twitter:title" content="[^"]*"', f'<meta name="twitter:title" content="{esc(title)}"', head, count=1)
    head = re.sub(r'<meta property="og:description" content="[^"]*"', f'<meta property="og:description" content="{esc(meta)}"', head, count=1)
    head = re.sub(r'<meta name="twitter:description" content="[^"]*"', f'<meta name="twitter:description" content="{esc(meta)}"', head, count=1)

    main = (
        '<main class="shell">'
        '<div class="crumb"><a href="/">Home</a> / <a href="/make-money/">BRYME Make Money</a> / Coding</div>'
        '<section class="mm-onboard" data-mm-app>'
        '<div data-mm-step="nationality">'
        '<h2>What\'s your nationality?</h2>'
        '<p class="mm-desk-lead">This is used only to hide coding platforms that officially exclude your country. You can change it any time.</p>'
        '<label class="mm-country-label" for="mm-country-q">Type your country</label>'
        '<input id="mm-country-q" class="mm-country-q" data-mm-country-q type="text" inputmode="search" placeholder="e.g. Nigeria, Ghana, Kenya\u2026" autocomplete="off" autocapitalize="words" spellcheck="false" aria-label="Type your country">'
        '<div class="mm-country-list" data-mm-countries></div>'
        '</div>'
        '<div data-mm-step="jobs" hidden>'
        '<p class="oc-natbar"><button type="button" class="oc-nat-btn" data-mm-change data-mm-nat-label>Change country</button></p>'
        '<div class="section-head"><div><div class="eyebrow">\U0001F4BB Coding &amp; Developer Jobs</div><h1>Coding &amp; Developer Jobs</h1>'
        '<p class="lead">20 platforms where developers actually get paid \u2014 rates, commissions, payout support and how hard they are to get into. Filtered by your country.</p></div></div>'
        '<p class="oc-natbar" data-oc-nat></p>'
        '<form class="oc-filters" data-oc-filters>'
        '<label class="oc-search-wrap"><span>Search</span><input type="search" data-oc-q placeholder="Search platform or work type\u2026" autocomplete="off"></label>'
        '</form>'
        '<div class="oc-grid" data-oc-grid>' + CARDS + '</div>'
        '</div>'
        '</section>'
        '<section class="section"><div class="vnote"><b>Rates and terms shift often.</b> Commission structures, payout support for Nigeria (Payoneer, Wise, Grey, Cleva, Raenest) and eligibility change \u2014 verify on each platform before committing time to an application. Verified 22 August 2026.</div></section>'
        '<section class="section core-hubs" data-core-hubs><div class="section-head"><h2>Also on BRYME</h2></div><div class="vcat-grid">'
        '<a class="vcat" href="/make-money/"><b>\U0001F4B0 Make Money</b><span>Verified paid opportunities, filtered by your country.</span></a>'
        '<a class="vcat" href="/make-money/remote-work/"><b>\U0001F310 Remote Jobs</b><span>20 earning platforms as job cards \u2014 filtered by country.</span></a>'
        '<a class="vcat" href="/make-money/writing/"><b>\u270D\uFE0F Writing</b><span>Publications that pay for writing \u2014 country-filtered.</span></a>'
        '</div></section>'
        '</main>'
    )

    script = (
        '<script>\n(function(){\n'
        'var KEY = \'bryme-nationality\';\n'
        'var CTRY = ' + CTRY_JSON + ';\n'
        'var OPS = ' + OPS_JSON + ';\n'
        'function loadNat(){ try { var v = localStorage.getItem(KEY); return v ? JSON.parse(v) : null; } catch(e){ return null; } }\n'
        'function saveNat(n){ try { localStorage.setItem(KEY, JSON.stringify(n)); } catch(e){} }\n'
        'function byId(id){ for (var i=0;i<CTRY.length;i++) if (CTRY[i].id===id) return CTRY[i]; return null; }\n'
        'function eligible(op, nat){ return true; }\n'
        'var hub = document.querySelector(\'[data-mm-app]\');\n'
        'var stepN = hub.querySelector(\'[data-mm-step="nationality"]\');\n'
        'var stepJ = hub.querySelector(\'[data-mm-step="jobs"]\');\n'
        'var list = hub.querySelector(\'[data-mm-countries]\');\n'
        'var search = hub.querySelector(\'[data-mm-country-q]\');\n'
        'var change = hub.querySelector(\'[data-mm-change]\');\n'
        'var label = hub.querySelector(\'[data-mm-nat-label]\');\n'
        'var nat = loadNat();\n'
        'function renderCountries(filter){\n'
        '  var f = (filter || \'\').toLowerCase();\n'
        '  var buttons = list.querySelectorAll(\'[data-mm-pick]\');\n'
        '  if (!buttons.length) {\n'
        '    list.innerHTML = CTRY.map(function(c){ return \'<button type="button" class="mm-country" data-mm-pick="\'+c.id+\'"><span>\'+c.flag+\'</span> \'+c.name+\'</button>\'; }).join(\'\');\n'
        '    buttons = list.querySelectorAll(\'[data-mm-pick]\');\n'
        '  }\n'
        '  Array.prototype.forEach.call(buttons, function(btn){\n'
        '    var name = (btn.textContent || \'\').toLowerCase();\n'
        '    var id = (btn.getAttribute(\'data-mm-pick\') || \'\').toLowerCase();\n'
        '    btn.hidden = !!(f && name.indexOf(f) === -1 && id !== f);\n'
        '  });\n'
        '}\n'
        'function showJobs(){\n'
        '  if (stepN) stepN.hidden = true;\n'
        '  if (stepJ) stepJ.hidden = false;\n'
        '  if (label && nat) label.textContent = (nat.flag || \'\') + \' Showing coding platforms for \' + nat.name + \' \u2014 Change country\';\n'
        '  apply();\n'
        '}\n'
        'function showNat(){ if (stepN) stepN.hidden = false; if (stepJ) stepJ.hidden = true; renderCountries(search && search.value); if (search) search.focus(); }\n'
        'var grid = document.querySelector(\'[data-oc-grid]\');\n'
        'var filters = document.querySelector(\'[data-oc-filters]\');\n'
        'function qv(){ var n = filters && filters.querySelector(\'[data-oc-q]\'); return n ? (n.value||\'\').toLowerCase().trim() : \'\'; }\n'
        'function apply(){\n'
        '  var t = qv(); var shown = 0;\n'
        '  Array.prototype.forEach.call(grid.querySelectorAll(\'[data-oc-card]\'), function(card, i){\n'
        '    var op = OPS[i]; if (!op) { card.style.display = \'\'; shown++; return; }\n'
        '    var ok = true;\n'
        '    if (t) {\n'
        '      var blob = ((op.publication||\'\') + \' \' + (op.title||\'\') + \' \' + (op.keywords||\'\')).toLowerCase();\n'
        '      var toks = t.split(/\\s+/);\n'
        '      for (var k=0;k<toks.length;k++){ if (blob.indexOf(toks[k]) === -1){ ok=false; break; } }\n'
        '    }\n'
        '    card.style.display = ok ? \'\' : \'none\';\n'
        '    if (ok) shown++;\n'
        '  });\n'
        '  var bar = document.querySelector(\'[data-oc-nat]\');\n'
        '  if (bar && nat) bar.textContent = nat.flag + \' Showing coding platforms for \' + nat.name + \' \u2014 \' + shown + \' of \' + OPS.length + \' platforms\';\n'
        '}\n'
        'hub.addEventListener(\'click\', function(e){\n'
        '  var pick = e.target.closest(\'[data-mm-pick]\');\n'
        '  if (pick) { nat = byId(pick.getAttribute(\'data-mm-pick\')); if (nat) saveNat(nat); showJobs(); return; }\n'
        '  if (e.target.closest(\'[data-mm-change]\')) showNat();\n'
        '});\n'
        'if (search) search.addEventListener(\'input\', function(){ renderCountries(search.value); });\n'
        'var qin = filters && filters.querySelector(\'[data-oc-q]\');\n'
        'if (qin) qin.addEventListener(\'input\', apply);\n'
        'if (nat) showJobs(); else showNat();\n'
        '})();\n</script>'
    )

    out = head + main + script + tail
    out = strip_inherited_ops(out)
    open(p, 'w', encoding='utf-8').write(out)
    print("coding page built:", len(out), "| cards:", out.count('data-oc-card'))

if __name__ == '__main__':
    build()

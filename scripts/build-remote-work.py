#!/usr/bin/env python3
"""BRYME · Build /make-money/remote-work/ — the 20 legit platforms as nationality-filtered
job cards on the landing-page flow (same localStorage nationality as the make-money hub)."""
import json, os, re, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def esc(s): return H.escape(str(s), quote=True)

platforms = json.load(open(os.path.join(ROOT, 'scripts/platforms.json')))

# ---- country code map for eligibility ----
CC = {'Nigeria':'NG','Kenya':'KE','Ghana':'GH','South Africa':'ZA','Egypt':'EG','United States':'US',
      'US':'US','UK':'GB','United Kingdom':'GB','Canada':'CA','Ireland':'IE','Australia':'AU',
      'New Zealand':'NZ','Philippines':'PH','India':'IN','Uganda':'UG','Japan':'JP','Germany':'DE',
      'France':'FR','most of EU':'EU'}

def to_op(p):
    """convert a platform row to the opportunity-format the eligible() filter expects"""
    slug = re.sub(r'[^a-z0-9]+','-', p['name'].lower()).strip('-')
    txt = p['countries'].lower()
    mode = 'open'; inc = []; regs = []; ex = []
    if 'primarily' in txt or txt.startswith('confirmed:'):
        mode = 'restricted'
        for name, code in CC.items():
            if name != 'most of EU' and name.lower() in txt and code not in inc:
                inc.append(code)
        if 'most of eu' in txt or 'europe' in txt:
            regs.append('europe')
    if p['name'].lower().startswith('sama'):
        mode = 'restricted'; inc = ['KE','UG']
    return {
        'id': slug, 'slug': slug,
        'publication': p['name'], 'title': p['cat'],
        'excerpt': p['pay'] + ' per hour. ' + p['countries'] + '. ' + p['flags'],
        'payCurrency': 'USD', 'payMin': None, 'payMax': None, 'payDisplay': p['pay'],
        'writingTypes': [p['cat'].split(' ')[0].lower().replace('&','and')],
        'writingTypeLabel': p['cat'],
        'eligibilityMode': mode, 'includesCountries': inc, 'includesRegions': regs,
        'excludesCountries': ex, 'notStatedElig': False, 'allowsDiaspora': False,
        'eligibilitySummary': p['countries'],
        'experience': 'not-stated', 'submissionStatus': 'open', 'responseBand': 'not-stated',
        'aiPolicy': 'not-stated', 'deadline': '', 'lastVerified': '2026-08-22',
        'keywords': p['name'].lower() + ' ' + p['cat'].lower() + ' remote job earn ai training microtask',
        'url': p['url'], 'owner': p['owner'], 'req': p['req'], 'steps': p['steps'],
        'payMethod': p['payMethod'], 'threshold': p['threshold'], 'rules': p['rules'], 'flags': p['flags'],
    }

OPS = [to_op(p) for p in platforms]

# ---- build card HTML (oc-card style, external apply link) ----
def card_html(op, idx):
    img = '/assets/img/money/hero-ai.jpg' if idx % 2 == 0 else '/assets/img/money/hero-writing.jpg'
    facts = (
        '<div><dt>Eligibility</dt><dd>' + esc(op['eligibilitySummary']) + '</dd></div>'
        '<div><dt>Work</dt><dd>' + esc(op['title']) + '</dd></div>'
        '<div><dt>Pay</dt><dd>' + esc(op['payDisplay']) + '/hr</dd></div>'
        '<div><dt>Payout</dt><dd>' + esc(op['payMethod']) + (' \u00b7 ' + esc(op['threshold']) if op['threshold'] else '') + '</dd></div>'
        '<div><dt>You need</dt><dd>' + esc(op['req'][:140]) + '</dd></div>'
    )
    flags = ('<div><dt>Red flags</dt><dd>' + esc(op['flags']) + '</dd></div>') if op['flags'] else ''
    return (
        '<article class="oc-card oc-card-has-art" data-oc-card>'
        '<div class="oc-card-art" style="background-image:url(\'' + img + '\')" aria-hidden="true"></div>'
        '<div class="oc-card-body">'
        '<header class="oc-card-top"><div><p class="oc-pub">' + esc(op['publication']) + '</p>'
        '<h3>' + esc(op['title']) + '</h3></div>'
        '<span class="oc-status oc-st-open">Open</span></header>'
        '<dl class="oc-facts">' + facts + flags + '</dl>'
        '<p class="oc-verified">Verified 2026-08-22</p>'
        '<p class="oc-actions"><a class="cta" href="' + esc(op['url']) + '" rel="nofollow noopener" target="_blank">Apply \u2192</a></p>'
        '</div></article>'
    )

CARDS = ''.join(card_html(op, i) for i, op in enumerate(OPS))
OPS_JSON = json.dumps(OPS, ensure_ascii=False)

# ---- extract CTRY from the writing page ----
w = open(os.path.join(ROOT, 'make-money/writing/index.html'), encoding='utf-8').read()
m = re.search(r'var CTRY = (\[.*?\]);', w, re.S)
CTRY_JSON = m.group(1) if m else '[]'
print("CTRY extracted:", len(json.loads(CTRY_JSON)), "countries")


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
    out_dir = os.path.join(ROOT, 'make-money', 'remote-work')
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, 'index.html')

    title = 'Remote Jobs \u2014 20 Legit Platforms | BRYME'
    meta = 'Remote jobs and earning platforms that accept your country: pay ranges, requirements, red flags and official apply links. Pick your country to see which of the 20 verified platforms qualify.'

    # shell from writing page (keep head/footer/css)
    i = w.find('<main'); j = w.find('</main>')
    head = w[:i]
    tail = w[j + len('</main>'):]
    head = re.sub(r'<title>.*?</title>', f'<title>{esc(title)}</title>', head, count=1, flags=re.S)
    head = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{esc(meta)}"', head, count=1)
    head = re.sub(r'rel="canonical" href="[^"]*"', 'rel="canonical" href="https://bryme.onrender.com/make-money/remote-work/"', head, count=1)
    head = re.sub(r'<meta property="og:url" content="[^"]*"', '<meta property="og:url" content="https://bryme.onrender.com/make-money/remote-work/"', head, count=1)
    head = re.sub(r'<meta property="og:title" content="[^"]*"', f'<meta property="og:title" content="{esc(title)}"', head, count=1)
    head = re.sub(r'<meta name="twitter:title" content="[^"]*"', f'<meta name="twitter:title" content="{esc(title)}"', head, count=1)
    head = re.sub(r'<meta property="og:description" content="[^"]*"', f'<meta property="og:description" content="{esc(meta)}"', head, count=1)
    head = re.sub(r'<meta name="twitter:description" content="[^"]*"', f'<meta name="twitter:description" content="{esc(meta)}"', head, count=1)

    main = (
        '<main class="shell">'
        '<div class="crumb"><a href="/">Home</a> / <a href="/make-money/">BRYME Make Money</a> / Remote Jobs</div>'

        '<section class="mm-onboard" data-mm-app>'
        '<div data-mm-step="nationality">'
        '<h2>What\'s your nationality?</h2>'
        '<p class="mm-desk-lead">This is used only to hide remote jobs that officially exclude your country. You can change it any time.</p>'
        '<label class="mm-country-label" for="mm-country-q">Type your country</label>'
        '<input id="mm-country-q" class="mm-country-q" data-mm-country-q type="text" inputmode="search" placeholder="e.g. Nigeria, Ghana, Kenya\u2026" autocomplete="off" autocapitalize="words" spellcheck="false" aria-label="Type your country">'
        '<div class="mm-country-list" data-mm-countries></div>'
        '</div>'
        '<div data-mm-step="jobs" hidden>'
        '<p class="oc-natbar"><button type="button" class="oc-nat-btn" data-mm-change data-mm-nat-label>Change country</button></p>'
        '<div class="section-head"><div><div class="eyebrow">\U0001F4B0 Remote Jobs</div><h1>Remote Jobs</h1>'
        '<p class="lead">20 legitimate earning platforms as job cards \u2014 pay, countries, requirements, red flags and the official apply link. Filtered by your country.</p></div></div>'
        '<p class="oc-natbar" data-oc-nat></p>'
        '<form class="oc-filters" data-oc-filters>'
        '<label class="oc-search-wrap"><span>Search</span><input type="search" data-oc-q placeholder="Search platform or work type\u2026" autocomplete="off"></label>'
        '</form>'
        '<div class="oc-grid" data-oc-grid>' + CARDS + '</div>'
        '</div>'
        '</section>'

        '<section class="section"><div class="vnote"><b>Last verified:</b> 22 August 2026. Eligibility and pay fluctuate \u2014 the official site is the source of truth. Toloka\u2019s crowd work folded into Mindrift in 2026; MTurk is closed to new signups. If a page asks for payment before you can work, it is not legitimate.</div></section>'

        '<section class="section core-hubs" data-core-hubs><div class="section-head"><h2>Also on BRYME</h2></div><div class="vcat-grid">'
        '<a class="vcat" href="/make-money/"><b>\U0001F4B0 Make Money</b><span>Verified paid opportunities, filtered by your country.</span></a>'
        '<a class="vcat" href="/make-money/writing/"><b>\u270D\uFE0F Writing</b><span>Publications that pay for writing \u2014 country-filtered.</span></a>'
        '<a class="vcat" href="/make-money/make-money-online-nigeria/"><b>Making money in Nigeria</b><span>The pillar guide \u2014 what actually works.</span></a>'
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
        'function eligible(op, nat){\n'
        '  if (!nat) return true;\n'
        '  var ex = op.excludesCountries || [];\n'
        '  if (ex.indexOf(nat.id) !== -1) return false;\n'
        '  if (op.notStatedElig || op.eligibilityMode === \'open\') return true;\n'
        '  var inc = op.includesCountries || [];\n'
        '  if (inc.length && inc.indexOf(nat.id) !== -1) return true;\n'
        '  var regs = op.includesRegions || [];\n'
        '  if (regs.length && regs.indexOf(nat.region) !== -1) return true;\n'
        '  if (inc.length || regs.length) return false;\n'
        '  return true;\n'
        '}\n'
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
        '  if (label && nat) label.textContent = (nat.flag || \'\') + \' Showing remote jobs for \' + nat.name + \' \u2014 Change country\';\n'
        '  var bar = document.querySelector(\'[data-oc-nat]\');\n'
        '  if (bar) bar.textContent = nat ? (nat.flag + \' Showing remote jobs for \' + nat.name + \' \u2014 \' + visibleCount() + \' of \' + OPS.length + \' platforms\') : \'\';\n'
        '  apply();\n'
        '}\n'
        'function showNat(){ if (stepN) stepN.hidden = false; if (stepJ) stepJ.hidden = true; renderCountries(search && search.value); if (search) search.focus(); }\n'
        'var grid = document.querySelector(\'[data-oc-grid]\');\n'
        'var filters = document.querySelector(\'[data-oc-filters]\');\n'
        'function qv(){ var n = filters && filters.querySelector(\'[data-oc-q]\'); return n ? (n.value||\'\').toLowerCase().trim() : \'\'; }\n'
        'function visibleCount(){ var n=0; Array.prototype.forEach.call(grid.querySelectorAll(\'[data-oc-card]\'), function(c){ if (c.style.display !== \'none\') n++; }); return n; }\n'
        'function apply(){\n'
        '  var t = qv(); var shown = 0;\n'
        '  Array.prototype.forEach.call(grid.querySelectorAll(\'[data-oc-card]\'), function(card, i){\n'
        '    var op = OPS[i]; if (!op) { card.style.display = \'\'; shown++; return; }\n'
        '    var ok = eligible(op, nat);\n'
        '    if (ok && t) {\n'
        '      var blob = ((op.publication||\'\') + \' \' + (op.title||\'\') + \' \' + (op.keywords||\'\')).toLowerCase();\n'
        '      var toks = t.split(/\\s+/);\n'
        '      for (var k=0;k<toks.length;k++){ if (blob.indexOf(toks[k]) === -1){ ok=false; break; } }\n'
        '    }\n'
        '    card.style.display = ok ? \'\' : \'none\';\n'
        '    if (ok) shown++;\n'
        '  });\n'
        '  var bar = document.querySelector(\'[data-oc-nat]\');\n'
        '  if (bar && nat) bar.textContent = nat.flag + \' Showing remote jobs for \' + nat.name + \' \u2014 \' + shown + \' of \' + OPS.length + \' platforms\';\n'
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
    print("remote-work built:", len(out), "| cards:", out.count('data-oc-card'))

if __name__ == '__main__':
    build()

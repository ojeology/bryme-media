/* BRYME verified paid-opportunity catalog.
   Data: content/opportunities.json + content/countries.json
   Overwrites /make-money/ and /make-money/writing/ after the foundation build. */
module.exports = function buildOpportunityCatalog(ctx) {
  const {
    fs, path, root, esc, url, absUrl, layout, write, breadcrumbs,
    TODAY, PAGE_LASTMOD, WRITING_EXTRA_PATHS, warnings, VERTICALS, verticalChip, coreHubStrip, sendBar, SENDABLE_META, site
  } = ctx;

  const ISO = /^\d{4}-\d{2}-\d{2}$/;
  const oppPath = path.join(root, 'content', 'opportunities.json');
  const ctryPath = path.join(root, 'content', 'countries.json');
  if (!fs.existsSync(oppPath) || !fs.existsSync(ctryPath)) {
    warnings.push('opportunity catalog skipped — missing JSON');
    return;
  }
  const data = JSON.parse(fs.readFileSync(oppPath, 'utf8'));
  const countries = JSON.parse(fs.readFileSync(ctryPath, 'utf8'));
  const cats = data.earningCategories || [];
  const all = (data.opportunities || []).filter(o => o && o.status === 'published' && o.vertical === 'writing');

  all.forEach(o => {
    if (!o.slug || !o.publication || !o.lastVerified || !ISO.test(o.lastVerified)) {
      throw new Error('opportunity ' + (o.id || '?') + ' needs slug, publication and YYYY-MM-DD lastVerified');
    }
    if (!o.officialUrl) throw new Error('opportunity ' + o.slug + ' needs officialUrl');
    if (!o.applyUrl && !o.applyEmail) throw new Error('opportunity ' + o.slug + ' needs applyUrl or applyEmail');
  });

  const flag = id => {
    if (!id || id.length !== 2) return '';
    const A = 0x1F1E6;
    return String.fromCodePoint(...id.toUpperCase().split('').map(c => A + c.charCodeAt(0) - 65));
  };

  const payHeadline = o => {
    const tmp = o.pay && o.pay.temporary;
    if (tmp && tmp.until && tmp.until >= TODAY) {
      return tmp.display + ' bonus until ' + tmp.until;
    }
    return (o.pay && o.pay.display) || 'Not publicly stated';
  };

  const statusMeta = o => {
    const d = o.deadline;
    if (d && d.windowEnd && d.windowEnd < TODAY) return { key: 'closed', label: 'Closed' };
    const map = { open: 'Open', rolling: 'Rolling', deadline: 'Deadline', closed: 'Closed', upcoming: 'Upcoming', unknown: 'Status not publicly confirmed' };
    let label = map[o.submissionStatus] || 'Not publicly stated';
    if (o.submissionStatus === 'deadline' && d && d.display) label = d.display;
    if (o.submissionStatus === 'rolling' && d && d.display) label = d.display;
    if (o.submissionStatus === 'upcoming' && d && d.display) label = d.display;
    return { key: o.submissionStatus || 'open', label };
  };

  const editorLabel = st => ({
    'not-yet-submitted': 'Not yet submitted',
    submitted: 'Submitted',
    'awaiting-response': 'Awaiting response',
    accepted: 'Accepted',
    rejected: 'Rejected',
    published: 'Published',
    paid: 'Paid',
    'payment-pending': 'Payment pending',
    'no-response': 'No response',
    'opportunity-closed': 'Opportunity closed'
  }[st] || st || 'Not yet submitted');

  const embed = all.map(o => ({
    id: o.id,
    slug: o.slug,
    publication: o.publication,
    title: o.title,
    excerpt: o.excerpt || '',
    writingTypes: o.writingTypes || [],
    writingTypeLabel: o.writingTypeLabel || '',
    payCurrency: (o.pay && o.pay.currency) || '',
    payMin: o.pay && o.pay.amountMin != null ? o.pay.amountMin : null,
    payMax: o.pay && o.pay.amountMax != null ? o.pay.amountMax : null,
    payDisplay: payHeadline(o),
    wordMin: o.wordCount && o.wordCount.min != null ? o.wordCount.min : null,
    wordMax: o.wordCount && o.wordCount.max != null ? o.wordCount.max : null,
    responseBand: (o.response && o.response.band) || 'not-stated',
    aiPolicy: o.aiPolicy || 'not-stated',
    experience: o.experience || 'not-stated',
    submissionStatus: statusMeta(o).key,
    deadline: o.deadline && o.deadline.date ? o.deadline.date : (o.deadline && o.deadline.windowEnd) || '',
    lastVerified: o.lastVerified,
    publishedAt: o.publishedAt || o.lastVerified,
    eligibilityMode: (o.eligibility && o.eligibility.mode) || 'open',
    includesRegions: (o.eligibility && o.eligibility.includesRegions) || [],
    includesCountries: (o.eligibility && o.eligibility.includesCountries) || [],
    excludesCountries: (o.eligibility && o.eligibility.excludesCountries) || [],
    allowsDiaspora: !!(o.eligibility && o.eligibility.allowsDiaspora),
    notStatedElig: !!(o.eligibility && o.eligibility.notStated),
    eligibilitySummary: (o.eligibility && o.eligibility.summary) || '',
    keywords: (o.keywords || []).join(' '),
    url: '/make-money/writing/' + o.slug + '/'
  }));

  const countryEmbed = countries.map(c => ({ id: c.id, name: c.name, region: c.region, flag: flag(c.id) }));

  const listingArt = o => {
    const types = Array.isArray(o.writingTypes) ? o.writingTypes : [];
    if (types.includes('poetry')) return '/assets/img/money/hero-poetry.jpg';
    if (types.includes('fiction')) return '/assets/img/money/hero-fiction.jpg';
    if (types.includes('journalism') || types.includes('analysis') || types.includes('articles')) return '/assets/img/money/hero-journalism.jpg';
    if (types.includes('personal-essays') || types.includes('essays') || types.includes('creative-nonfiction')) return '/assets/img/money/hero-writing.jpg';
    return '/assets/img/money/hero-beginner.jpg';
  };
  const card = o => {
    const st = statusMeta(o);
    const elig = (o.eligibility && o.eligibility.summary) || 'Not publicly stated';
    const art = listingArt(o);
    return `<article class="oc-card oc-card-has-art" data-oc-card>
      <div class="oc-card-art" style="background-image:url('${art}')" aria-hidden="true"></div>
      <div class="oc-card-body">
      <header class="oc-card-top">
        <div><p class="oc-pub">${esc(o.publication)}</p><h3><a href="${url('/make-money/writing/' + o.slug + '/')}">${esc(o.title)}</a></h3></div>
        <span class="oc-status oc-st-${esc(st.key)}">${esc(st.label)}</span>
      </header>
      <dl class="oc-facts">
        <div><dt>Eligibility</dt><dd>${esc(elig)}</dd></div>
        <div><dt>Writing</dt><dd>${esc(o.writingTypeLabel || 'Not publicly stated')}</dd></div>
        <div><dt>Pay</dt><dd>${esc(payHeadline(o))}</dd></div>
        <div><dt>Length</dt><dd>${esc((o.wordCount && o.wordCount.display) || 'Not publicly stated')}</dd></div>
        <div><dt>Response</dt><dd>${esc((o.response && o.response.label) || 'Not publicly stated')}</dd></div>
        <div><dt>Submission</dt><dd>${esc(o.applyMethod || 'See official source')}</dd></div>
      </dl>
      <p class="oc-verified">Verified ${esc(o.lastVerified)}</p>
      <p class="oc-actions"><a class="cta" href="${url('/make-money/writing/' + o.slug + '/')}">View details</a></p>
      </div>
    </article>`;
  };

  const disclaimer = `<p class="oc-disclaimer">${esc(data.disclaimer)}</p>`;

  const filterBar = `<form class="oc-filters" data-oc-filters>
    <label class="oc-search-wrap"><span>Search</span>
      <input type="search" data-oc-q placeholder="Search publication, essay, eligibility…" autocomplete="off">
    </label>
    <div class="oc-filter-grid">
      <label>Writing type
        <select data-oc-type>
          <option value="">All</option>
          <option value="articles">Articles</option>
          <option value="essays">Essays</option>
          <option value="personal-essays">Personal Essays</option>
          <option value="creative-nonfiction">Creative Nonfiction</option>
          <option value="fiction">Fiction</option>
          <option value="poetry">Poetry</option>
          <option value="opinion">Opinion</option>
          <option value="journalism">Journalism</option>
          <option value="reviews">Reviews</option>
          <option value="copywriting">Copywriting</option>
          <option value="technical-writing">Technical Writing</option>
          <option value="interviews">Interviews</option>
          <option value="long-form">Long-form</option>
          <option value="other">Other</option>
        </select>
      </label>
      <label>Payment
        <select data-oc-pay>
          <option value="">All</option>
          <option value="USD:25">$25+</option>
          <option value="USD:50">$50+</option>
          <option value="USD:100">$100+</option>
          <option value="USD:250">$250+</option>
          <option value="USD:500">$500+</option>
          <option value="USD:1000">$1,000+</option>
          <option value="NGN:10000">₦10,000+</option>
          <option value="NGN:20000">₦20,000+</option>
          <option value="NGN:50000">₦50,000+</option>
          <option value="NGN:100000">₦100,000+</option>
        </select>
      </label>
      <label>Word count
        <select data-oc-words>
          <option value="">All</option>
          <option value="0-499">Under 500</option>
          <option value="500-1000">500–1,000</option>
          <option value="1000-2000">1,000–2,000</option>
          <option value="2000-5000">2,000–5,000</option>
          <option value="5000-999999">5,000+</option>
        </select>
      </label>
      <label>Experience
        <select data-oc-exp>
          <option value="">All</option>
          <option value="beginner">Beginner friendly</option>
          <option value="intermediate">Intermediate</option>
          <option value="experienced">Experienced</option>
          <option value="not-stated">No stated requirement</option>
        </select>
      </label>
      <label>Status
        <select data-oc-status>
          <option value="">All</option>
          <option value="open">Open</option>
          <option value="rolling">Rolling</option>
          <option value="deadline">Deadline</option>
          <option value="upcoming">Upcoming</option>
          <option value="closed">Closed</option>
        </select>
      </label>
      <label>Response time
        <select data-oc-resp>
          <option value="">All</option>
          <option value="under-2-weeks">Under 2 weeks</option>
          <option value="2-4-weeks">2–4 weeks</option>
          <option value="1-3-months">1–3 months</option>
          <option value="3-plus-months">3+ months</option>
          <option value="not-stated">Not stated</option>
        </select>
      </label>
      <label>AI policy
        <select data-oc-ai>
          <option value="">All</option>
          <option value="prohibited">AI prohibited</option>
          <option value="permitted">AI permitted</option>
          <option value="not-stated">AI policy not stated</option>
        </select>
      </label>
      <label>Sort
        <select data-oc-sort>
          <option value="verified">Recently verified</option>
          <option value="pay-high">Highest payment</option>
          <option value="pay-low">Lowest payment</option>
          <option value="deadline">Deadline soonest</option>
          <option value="az">Alphabetical</option>
          <option value="newest">Newest opportunity</option>
        </select>
      </label>
    </div>
    <div class="oc-filter-actions">
      <button type="button" class="fbtn" data-oc-clear>Clear filters</button>
      <p class="oc-count" data-oc-count></p>
    </div>
  </form>`;

  const catalogScript = `<script>
  (function(){
    var KEY = 'bryme-nationality';
    var OPS = ${JSON.stringify(embed).replace(/</g, '\\\\u003c')};
    var CTRY = ${JSON.stringify(countryEmbed).replace(/</g, '\\\\u003c')};
    function loadNat(){
      try { return JSON.parse(localStorage.getItem(KEY) || 'null'); } catch (e) { return null; }
    }
    function saveNat(n){ try { localStorage.setItem(KEY, JSON.stringify(n)); } catch (e) {} }
    function q(name){ try { return new URLSearchParams(location.search).get(name) || ''; } catch (e) { return ''; } }
    function byId(id){ for (var i=0;i<CTRY.length;i++) if (CTRY[i].id===id) return CTRY[i]; return null; }
    function eligible(op, nat){
      if (!nat) return true;
      var ex = op.excludesCountries || [];
      if (ex.indexOf(nat.id) !== -1) return false;
      if (op.notStatedElig || op.eligibilityMode === 'open') return true;
      if (op.allowsDiaspora) return true;
      var inc = op.includesCountries || [];
      if (inc.length && inc.indexOf(nat.id) !== -1) return true;
      var regs = op.includesRegions || [];
      if (regs.length && regs.indexOf(nat.region) !== -1) return true;
      if (inc.length || regs.length) return false;
      return true;
    }
    function wordOverlap(op, range){
      if (!range) return true;
      if (op.wordMin == null && op.wordMax == null) return false;
      var a = range.split('-'); var lo = +a[0], hi = +a[1];
      var omin = op.wordMin != null ? op.wordMin : 0;
      var omax = op.wordMax != null ? op.wordMax : 999999;
      return omin <= hi && omax >= lo;
    }
    function payMatch(op, token){
      if (!token) return true;
      var parts = token.split(':');
      var cur = parts[0], min = +parts[1];
      if (!op.payCurrency || op.payMin == null) return false;
      if (op.payCurrency !== cur) return false;
      return op.payMin >= min || (op.payMax != null && op.payMax >= min);
    }
    var nat = loadNat();
    var qid = q('country');
    if (qid && byId(qid)) { nat = byId(qid); saveNat(nat); }

    /* ----- hub onboarding ----- */
    var hub = document.querySelector('[data-mm-app]');
    if (hub) {
      var stepN = hub.querySelector('[data-mm-step="nationality"]');
      var stepC = hub.querySelector('[data-mm-step="categories"]');
      var list = hub.querySelector('[data-mm-countries]');
      var search = hub.querySelector('[data-mm-country-q]');
      var change = hub.querySelector('[data-mm-change]');
      var label = hub.querySelector('[data-mm-nat-label]');
      function renderCountries(filter){
        if (!list) return;
        var f = (filter || '').toLowerCase();
        var buttons = list.querySelectorAll('[data-mm-pick]');
        if (!buttons.length) {
          list.innerHTML = CTRY.map(function(c){
            return '<button type="button" class="mm-country" data-mm-pick="'+c.id+'"><span>'+c.flag+'</span> '+c.name+'</button>';
          }).join('');
          buttons = list.querySelectorAll('[data-mm-pick]');
        }
        Array.prototype.forEach.call(buttons, function(btn){
          var name = (btn.textContent || '').toLowerCase();
          var id = (btn.getAttribute('data-mm-pick') || '').toLowerCase();
          btn.hidden = !!(f && name.indexOf(f) === -1 && id !== f);
        });
      }
      function showCats(){
        if (stepN) stepN.hidden = true;
        if (stepC) stepC.hidden = false;
        if (label && nat) label.textContent = (nat.flag || '') + ' Showing opportunities for ' + nat.name + ' — Change country';
        hub.querySelectorAll('a[data-mm-live]').forEach(function(a){
          var base = a.getAttribute('data-href') || a.getAttribute('href').split('?')[0];
          a.setAttribute('href', nat ? base + '?country=' + encodeURIComponent(nat.id) : base);
        });
      }
      function showNat(){
        if (stepN) stepN.hidden = false;
        if (stepC) stepC.hidden = true;
        renderCountries(search && search.value);
        if (search) search.focus();
      }
      if (list) renderCountries('');
      if (search) {
        search.addEventListener('input', function(){ renderCountries(search.value); });
        search.addEventListener('keydown', function(e){
          if (e.key !== 'Enter') return;
          e.preventDefault();
          var first = list && list.querySelector('[data-mm-pick]:not([hidden])');
          if (first) first.click();
        });
      }
      hub.addEventListener('click', function(e){
        var pick = e.target.closest('[data-mm-pick]');
        if (pick) {
          nat = byId(pick.getAttribute('data-mm-pick'));
          if (nat) saveNat(nat);
          showCats();
          return;
        }
        if (e.target.closest('[data-mm-change]')) showNat();
      });
      if (q('change') === '1') showNat();
      else if (nat) showCats();
      else showNat();
    }

    /* ----- writing catalog ----- */
    var grid = document.querySelector('[data-oc-grid]');
    if (!grid) return;
    var cards = {};
    Array.prototype.slice.call(grid.querySelectorAll('[data-oc-card]')).forEach(function(el, i){
      var slug = OPS[i] && OPS[i].slug;
      if (slug) cards[slug] = el;
    });
    var bar = document.querySelector('[data-oc-nat]');
    var filters = document.querySelector('[data-oc-filters]');
    function val(sel){ var n = filters && filters.querySelector(sel); return n ? n.value : ''; }
    function apply(){
      var type = val('[data-oc-type]');
      var pay = val('[data-oc-pay]');
      var words = val('[data-oc-words]');
      var exp = val('[data-oc-exp]');
      var st = val('[data-oc-status]');
      var resp = val('[data-oc-resp]');
      var ai = val('[data-oc-ai]');
      var sort = val('[data-oc-sort]') || 'verified';
      var qv = (val('[data-oc-q]') || '').toLowerCase().trim();
      var shown = OPS.filter(function(op){
        if (!eligible(op, nat)) return false;
        if (type && (op.writingTypes || []).indexOf(type) === -1) return false;
        if (!payMatch(op, pay)) return false;
        if (!wordOverlap(op, words)) return false;
        if (exp && op.experience !== exp) return false;
        if (st && op.submissionStatus !== st) return false;
        if (resp && op.responseBand !== resp) return false;
        if (ai && op.aiPolicy !== ai) return false;
        if (qv) {
          var hay = [op.publication, op.title, op.excerpt, op.writingTypeLabel, op.eligibilitySummary, op.keywords].join(' ').toLowerCase();
          if (hay.indexOf(qv) === -1) return false;
        }
        return true;
      });
      shown.sort(function(a, b){
        function num(v, fallback){ return v == null ? fallback : v; }
        if (sort === 'az') return a.publication.localeCompare(b.publication) || a.title.localeCompare(b.title);
        if (sort === 'newest') return (b.publishedAt || '').localeCompare(a.publishedAt || '');
        if (sort === 'verified') return (b.lastVerified || '').localeCompare(a.lastVerified || '');
        if (sort === 'deadline') {
          if (a.deadline && !b.deadline) return -1;
          if (!a.deadline && b.deadline) return 1;
          return (a.deadline || '9999').localeCompare(b.deadline || '9999');
        }
        if (sort === 'pay-high' || sort === 'pay-low') {
          var aHas = a.payMin != null, bHas = b.payMin != null;
          if (aHas !== bHas) return aHas ? -1 : 1;
          if (!aHas) return 0;
          if (a.payCurrency !== b.payCurrency) return a.payCurrency.localeCompare(b.payCurrency);
          return sort === 'pay-high' ? (b.payMin - a.payMin) : (a.payMin - b.payMin);
        }
        return 0;
      });
      OPS.forEach(function(op){ if (cards[op.slug]) cards[op.slug].hidden = true; });
      var frag = document.createDocumentFragment();
      shown.forEach(function(op){
        var el = cards[op.slug];
        if (!el) return;
        el.hidden = false;
        frag.appendChild(el);
      });
      grid.appendChild(frag);
      var empty = document.querySelector('[data-oc-empty]');
      if (empty) empty.hidden = shown.length !== 0;
      var count = document.querySelector('[data-oc-count]');
      if (count) count.textContent = shown.length + ' opportunit' + (shown.length === 1 ? 'y' : 'ies') + (nat ? ' for ' + nat.name : '');
      if (bar && nat) bar.innerHTML = '<button type="button" class="oc-nat-btn" data-oc-change>'+(nat.flag||'')+' Showing opportunities for '+nat.name+' — Change country</button>';
      else if (bar && !nat) bar.innerHTML = '<button type="button" class="oc-nat-btn" data-oc-change>Choose your nationality to personalise</button>';
    }
    if (filters) {
      filters.addEventListener('input', apply);
      filters.addEventListener('change', apply);
      var clear = filters.querySelector('[data-oc-clear]');
      if (clear) clear.addEventListener('click', function(){
        Array.prototype.slice.call(filters.querySelectorAll('input,select')).forEach(function(n){ n.value = ''; });
        apply();
      });
    }
    if (bar) bar.addEventListener('click', function(e){
      if (!e.target.closest('[data-oc-change]')) return;
      location.href = '/make-money/?change=1';
    });
    apply();
  })();
  </script>`;

  /* ---------- CSS ---------- */
  fs.appendFileSync(path.join(root, 'assets/site.css'), `
/* Opportunity catalog */
.mm-onboard{max-width:820px;margin:0 auto 28px}
.mm-onboard h1{font-size:clamp(28px,6vw,44px);margin:8px 0 12px}
.mm-country-label{display:block;font-size:13px;font-weight:800;margin:0 0 6px}
.mm-country-q{display:block;width:100%;max-width:520px;background:#101318;border:1px solid var(--line);border-radius:8px;color:var(--text);font:inherit;font-size:16px;padding:12px 14px;margin:0 0 14px;position:relative;z-index:2;-webkit-user-select:text;user-select:text}
.mm-country-list{display:flex;flex-wrap:wrap;gap:8px;max-height:340px;overflow:auto;padding:2px}
.mm-onboard .mm-country{display:inline-flex;align-items:center;gap:6px}
.mm-cat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin:16px 0}
.mm-cat{display:flex;flex-direction:column;gap:6px;padding:16px;border:1px solid var(--line);border-radius:10px;background:#101318;min-height:120px}
.mm-cat.is-live{border-color:rgba(231,187,92,.45)}
.mm-cat.is-soon{opacity:.7}
.mm-cat b{font-size:16px}
.mm-cat span{font-size:13px;color:var(--muted);line-height:1.45}
.oc-natbar{margin:0 0 14px}
.oc-nat-btn{background:transparent;border:1px dashed var(--line);color:var(--text);font:inherit;font-size:14px;font-weight:700;padding:8px 12px;border-radius:8px;cursor:pointer}
.oc-filters{background:#101318;border:1px solid var(--line);border-radius:12px;padding:14px;margin:0 0 18px}
.oc-search-wrap{display:block;margin:0 0 12px}
.oc-search-wrap span{display:block;font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
.oc-search-wrap input{width:100%;background:#0d1013;border:1px solid var(--line);border-radius:8px;color:var(--text);font:inherit;font-size:16px;padding:11px 12px}
.oc-filter-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}
.oc-filters label{display:flex;flex-direction:column;gap:4px;font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.oc-filters select{background:#0d1013;border:1px solid var(--line);border-radius:6px;color:var(--text);font:inherit;font-size:13px;padding:8px}
.oc-filter-actions{display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin-top:12px}
.oc-count{margin:0;color:var(--muted);font-size:13px;font-weight:700}
.oc-grid{display:flex;flex-direction:column;gap:18px}
.oc-card{border:1px solid var(--line);border-radius:12px;background:linear-gradient(160deg,#161b23,#0f1216);padding:16px 16px 14px}
.oc-card-has-art{display:grid;grid-template-columns:148px minmax(0,1fr);padding:0;overflow:hidden}
.oc-card-art{min-height:100%;background-size:cover;background-position:center;background-color:#12151a}
.oc-card-body{padding:16px 16px 14px;min-width:0}
.oc-card-top{display:flex;justify-content:space-between;gap:10px;align-items:flex-start}
.oc-pub{margin:0 0 2px;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--gold)}
.oc-card h3{margin:0;font-size:20px;line-height:1.2}
.oc-status{flex:none;font-size:11px;font-weight:800;padding:3px 9px;border-radius:12px;border:1px solid rgba(61,220,132,.4);color:#3ddc84}
.oc-st-deadline{color:var(--gold);border-color:rgba(231,187,92,.45)}
.oc-st-closed{color:#ff9d8a;border-color:rgba(233,75,44,.4)}
.oc-facts{display:grid;grid-template-columns:1fr;gap:8px;margin:12px 0}
.oc-facts div{border:1px solid var(--line);border-radius:8px;padding:8px 10px}
.oc-facts dt{font-size:10px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 3px}
.oc-facts dd{margin:0;font-size:14px;line-height:1.45}
.oc-verified{font-size:12px;color:var(--gold);font-weight:800;margin:0 0 10px}
.oc-disclaimer,.oc-note{font-size:13px;color:var(--muted);line-height:1.6;max-width:720px}
.oc-official{border:1px solid var(--line);border-radius:12px;padding:8px 0 4px}
.oc-editor{margin-top:36px;padding:18px;border:1px dashed rgba(231,187,92,.45);border-radius:12px;background:rgba(231,187,92,.05)}
.oc-editor h2{margin-top:0}
.oc-editor-kicker{font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--gold)}
.oc-report{margin-top:28px}
.oc-report details{border:1px solid var(--line);border-radius:8px;padding:10px 14px}
.oc-report a{display:block;padding:6px 0;font-size:14px}
[data-theme="light"] .oc-card,[data-theme="light"] .oc-filters,[data-theme="light"] .mm-cat,[data-theme="light"] .mm-country-q{background:#fff}
[data-theme="light"] .oc-filters select,[data-theme="light"] .oc-search-wrap input,[data-theme="light"] .oc-filters select option{background:#fff;color:#161b22;border-color:var(--line)}
[data-theme="light"] .oc-card-has-art{background:#fff}
@media(min-width:700px){
  .oc-facts{grid-template-columns:1fr 1fr}
}
@media(max-width:760px){
  .oc-card-has-art{grid-template-columns:1fr}
  .oc-card-art{min-height:120px}

  .mm-cat-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .oc-filter-grid{grid-template-columns:1fr 1fr}
  .oc-card h3{font-size:18px}
}
`);

  /* ---------- Make Money hub ---------- */
  const liveWriting = cats.find(c => c.id === 'writing') || { name: 'Writing', emoji: '✍️' };
  const catCards = cats.map(c => {
    if (c.status === 'live') {
      return `<a class="mm-cat is-live" data-mm-live data-href="${url('/make-money/writing/')}" href="${url('/make-money/writing/')}"><b>${esc(c.emoji)} ${esc(c.name)}</b><span>${esc(c.blurb || 'Verified opportunities.')}</span></a>`;
    }
    return `<div class="mm-cat is-soon"><b>${esc(c.emoji)} ${esc(c.name)}</b><span>Coming soon. We will not invent listings to fill this category.</span></div>`;
  }).join('');

  const mmArticles = (require(path.join(root, 'content', 'make-money-articles.json')) || [])
    .filter(a => a.status === 'published');
  const guideCards = mmArticles.map(a =>
    `<a class="vcat" href="${url('/make-money/' + a.slug + '/')}"><b>${esc(a.title)}</b><span>${esc(a.excerpt || '')}</span></a>`
  ).join('');

  const countryButtons = countries.map(c =>
    `<button type="button" class="mm-country" data-mm-pick="${esc(c.id)}"><span>${flag(c.id)}</span> ${esc(c.name)}</button>`
  ).join('');

  const hubCrumbs = [{ name: 'Home', path: '/' }, { name: 'BRYME Make Money', path: '/make-money/' }];
  const hubBody = `<main class="shell">
    <div class="crumb"><a href="${url('/')}">Home</a> / BRYME Make Money</div>
    <section class="mm-feature"><div class="sports-feature-inner"><div class="eyebrow">💰 BRYME Make Money</div>
      <h1>Legitimate opportunities, filtered to you.</h1>
      <p>Find paid work that matches your country and skill. We verify listings against official guidelines. Nothing here is a guarantee of acceptance or payment.</p>
    </div></section>
    <section class="mm-onboard" data-mm-app>
      <div data-mm-step="nationality">
        <h2>What's your nationality?</h2>
        <p class="mm-desk-lead">This is used only to hide opportunities that officially exclude your country. You can change it any time.</p>
        <label class="mm-country-label" for="mm-country-q">Type your country</label>
        <input id="mm-country-q" class="mm-country-q" data-mm-country-q type="text" inputmode="search" placeholder="e.g. Nigeria, Ghana, Kenya…" autocomplete="off" autocapitalize="words" spellcheck="false" aria-label="Type your country">
        <div class="mm-country-list" data-mm-countries>${countryButtons}</div>
      </div>
      <div data-mm-step="categories" hidden>
        <p class="oc-natbar"><button type="button" class="oc-nat-btn" data-mm-change data-mm-nat-label>Change country</button></p>
        <h2>What do you want to earn from?</h2>
        <p class="mm-desk-lead">Writing is live. Other categories stay empty until we have verified listings.</p>
        <div class="mm-cat-grid">${catCards}</div>
      </div>
    </section>
    ${disclaimer}
    <section class="sp-hero" aria-label="Featured Make Money pages"><div class="sp-hero-track">
      <a class="sp-hero-card sp-hero-first mm-tint" href="${url('/make-money/writing/')}" style="--card-img:url('/assets/img/money/hero-writing.jpg')"><span class="sp-hero-tag">Writing</span><h3>Markets we actually checked</h3><p>Official rates and doors. A gig is not guaranteed. Fifty-five listings, not a dump.</p><span class="sp-hero-go">Open the catalog →</span></a>
      <a class="sp-hero-card mm-tint" href="${url('/make-money/freelance-platform-fees-explained/')}" style="--card-img:url('/assets/img/money/hero-fees.jpg')"><span class="sp-hero-tag">Fees</span><h3>What Upwork and Fiverr take in 2026</h3><p>From their own documentation, not a recycled listicle. Price so the cut does not surprise you.</p><span class="sp-hero-go">Read the fees →</span></a>
      <a class="sp-hero-card mm-tint" href="${url('/make-money/beginners-guide-to-making-money-online/')}" style="--card-img:url('/assets/img/money/hero-beginner.jpg')"><span class="sp-hero-tag">Start here</span><h3>The beginner guide without the lie</h3><p>Skills, traps, and what is not a job. No fake income figures.</p><span class="sp-hero-go">Read the guide →</span></a>
    </div></section>
    <section class="section"><div class="section-head"><h2>More guides</h2></div>
      <div class="vcat-grid">${guideCards}</div>
    </section>
    ${typeof coreHubStrip === 'function' ? coreHubStrip('make-money') : `<section class="section"><div class="section-head"><h2>Explore BRYME</h2></div><div class="vchips">${VERTICALS.map(verticalChip).join('')}</div></section>`}
  </main>${catalogScript}`;

  write('make-money', layout({
    title: 'BRYME Make Money – verified paid opportunities by country',
    description: 'Find legitimate paid writing and other online opportunities for your country. Listings are checked against official guidelines. Acceptance is not guaranteed.',
    path: '/make-money/',
    activeNav: 'make-money',
    schema: [{ '@context': 'https://schema.org', '@type': 'CollectionPage', name: 'BRYME Make Money', url: absUrl('/make-money/') }, breadcrumbs(hubCrumbs)],
    body: hubBody
  }));

  /* ---------- Writing catalog ---------- */
  const wCrumbs = hubCrumbs.concat([{ name: 'Writing', path: '/make-money/writing/' }]);
  const wBody = `<main class="shell wo-page">
    <div class="crumb"><a href="${url('/')}">Home</a> / <a href="${url('/make-money/')}">Make Money</a> / Writing</div>
    <section class="mm-feature mm-feature-photo" style="--hero-img:url('/assets/img/money/hero-writing.jpg')"><div class="sports-feature-inner"><div class="eyebrow">✍️ Writing opportunities</div>
      <h1>Verified places that pay writers.</h1>
      <p>Official rates, eligibility, word counts and how to submit — checked against the publication, not copied from a listicle. A gig is not guaranteed.</p>
      ${typeof sendBar === 'function' ? sendBar('/make-money/writing/', (SENDABLE_META && SENDABLE_META.writing && SENDABLE_META.writing.title) || 'Writing markets BRYME checked') : ''}
    </div></section>
    <p class="oc-natbar" data-oc-nat></p>
    ${filterBar}
    ${disclaimer}
    <p class="oc-note">Payment filters are currency-specific. A naira fee is not converted into dollars. Opportunities with no stated word count drop out of a word-count filter.</p>
    <div class="oc-grid" data-oc-grid>${all.map(card).join('')}</div>
    <div class="vstate" data-oc-empty hidden><b>No matching opportunities</b><p>Nothing in the verified set matches those filters for your country. Clear filters, or change country. We will not invent listings to fill the gap.</p></div>
    <section class="section"><a class="quiet-link" href="${url('/make-money/writing-field-notes-how-this-works/')}">How BRYME researches writing opportunities</a></section>
  </main>${catalogScript}`;

  write('make-money/writing', layout({
    title: 'Writing opportunities – verified paid calls',
    description: 'Paid writing opportunities verified against official guidelines. Filter by country, pay, word count, AI policy and deadline. Acceptance is not guaranteed.',
    path: '/make-money/writing/',
    activeNav: 'make-money',
    schema: [{ '@context': 'https://schema.org', '@type': 'CollectionPage', name: 'Writing opportunities', url: absUrl('/make-money/writing/') }, breadcrumbs(wCrumbs)],
    body: wBody
  }));
  WRITING_EXTRA_PATHS.push('/make-money/writing/');
  if (data.updatedAt && ISO.test(data.updatedAt)) PAGE_LASTMOD.set('/make-money/writing/', data.updatedAt);

  /* redirect old URL */
  write('make-money/writing-opportunities', layout({
    title: 'Writing opportunities',
    description: 'This catalogue has moved.',
    path: '/make-money/writing-opportunities/',
    canonical: '/make-money/writing/',
    noindex: true,
    activeNav: 'make-money',
    body: `<main class="shell" style="padding-top:80px;text-align:center"><p>This catalogue has moved. <a href="${url('/make-money/writing/')}">Open writing opportunities</a>.</p></main><meta http-equiv="refresh" content="0;url=${url('/make-money/writing/')}">`
  }));

  /* ---------- Detail pages ---------- */
  const listBlock = (heading, items) => {
    if (!items) return '';
    if (Array.isArray(items) && items.length) {
      return `<h2>${esc(heading)}</h2><ul>${items.map(x => `<li>${esc(x)}</li>`).join('')}</ul>`;
    }
    if (typeof items === 'string' && items.trim()) return `<h2>${esc(heading)}</h2><p>${esc(items)}</p>`;
    return '';
  };

  all.forEach(o => {
    const pagePath = '/make-money/writing/' + o.slug + '/';
    WRITING_EXTRA_PATHS.push(pagePath);
    PAGE_LASTMOD.set(pagePath, o.lastVerified);
    const st = statusMeta(o);
    const apply = o.applyUrl
      ? `<p><a class="cta" href="${esc(o.applyUrl)}" rel="nofollow noopener"${o.applyUrl.startsWith('http') ? ' target="_blank"' : ''}>Submit / apply (official)</a></p>`
      : '';
    const sources = (o.sources || []).map(s =>
      s.url ? `<a href="${esc(s.url)}" rel="nofollow noopener">${esc(s.name || s.url)}</a>` : esc(s.name || '')
    ).join(' · ');
    const ed = o.editorExperience || { status: 'not-yet-submitted' };
    const report = [
      ['payment-changed', 'Payment changed'],
      ['submissions-closed', 'Submissions closed'],
      ['link-broken', 'Link broken'],
      ['eligibility-changed', 'Eligibility changed'],
      ['deadline-passed', 'Deadline passed'],
      ['category-gone', 'Publication no longer accepts this category'],
      ['other', 'Other incorrect information']
    ].map(([id, label]) => {
      const subj = encodeURIComponent('BRYME outdated listing: ' + o.publication + ' / ' + id);
      return `<a href="mailto:Sodiqibrahim03@gmail.com?subject=${subj}">${esc(label)}</a>`;
    }).join('');

    const dCrumbs = wCrumbs.concat([{ name: o.publication, path: pagePath }]);
    const body = `<main class="shell wo-page">
      <div class="crumb"><a href="${url('/')}">Home</a> / <a href="${url('/make-money/')}">Make Money</a> / <a href="${url('/make-money/writing/')}">Writing</a> / ${esc(o.publication)}</div>
      <section class="article-hero">
        <div class="eyebrow">${esc(o.publication)}</div>
        <h1>${esc(o.title)}</h1>
        <p class="lead">${esc(o.excerpt || '')}</p>
        <div class="article-meta"><span class="oc-status oc-st-${esc(st.key)}">${esc(st.label)}</span><span>Last verified ${esc(o.lastVerified)}</span></div>
      </section>
      <article class="prose article-body oc-official">
        <p class="oc-editor-kicker">Official information</p>
        <h2>Overview</h2>
        <dl class="oc-facts">
          <div><dt>Publication</dt><dd>${esc(o.publication)}</dd></div>
          <div><dt>Eligibility</dt><dd>${esc((o.eligibility && o.eligibility.summary) || 'Not publicly stated')}</dd></div>
          <div><dt>Writing</dt><dd>${esc(o.writingTypeLabel || 'Not publicly stated')}</dd></div>
          <div><dt>Payment</dt><dd>${esc(payHeadline(o))}</dd></div>
          <div><dt>Currency</dt><dd>${esc((o.pay && o.pay.currency) || 'Not publicly stated')}</dd></div>
          <div><dt>Payment conditions</dt><dd>${esc((o.pay && o.pay.conditions) || 'Not publicly stated')}</dd></div>
          <div><dt>When paid</dt><dd>${esc((o.pay && o.pay.timing) || 'Not publicly stated')}</dd></div>
          <div><dt>Word count</dt><dd>${esc((o.wordCount && o.wordCount.display) || 'Not publicly stated')}</dd></div>
          <div><dt>Response time</dt><dd>${esc((o.response && o.response.label) || 'Not publicly stated')}</dd></div>
          <div><dt>Status</dt><dd>${esc(st.label)}</dd></div>
          <div><dt>Deadline</dt><dd>${esc((o.deadline && o.deadline.display) || 'Not publicly stated')}</dd></div>
          <div><dt>How to submit</dt><dd>${esc(o.applyMethod || 'See official source')}</dd></div>
          <div><dt>AI policy</dt><dd>${esc(o.aiPolicy === 'prohibited' ? 'AI-generated work prohibited' : o.aiPolicy === 'permitted' ? 'AI permitted (as stated)' : 'Not publicly stated')}</dd></div>
        </dl>
        ${listBlock('What they want', o.whatTheyWant)}
        ${listBlock("What they don't want", o.whatTheyDontWant)}
        ${listBlock('Requirements', o.requirements)}
        <h2>Rights</h2><p>${esc(o.rights || 'Not publicly stated')}</p>
        ${listBlock('How to submit', o.howToSubmit)}
        ${apply}
        <section class="sp-source"><h2>Official source</h2><p>${sources}</p>
          <p class="sp-source-note">Last verified ${esc(o.lastVerified)}. Always re-read the official page before you send work.</p>
        </section>
        ${disclaimer}
      </article>
      <section class="oc-editor">
        <p class="oc-editor-kicker">Separate from the official listing</p>
        <h2>Editor's Experience</h2>
        <p><b>${esc(editorLabel(ed.status))}</b></p>
        ${ed.submittedOn ? `<p>Submitted: ${esc(ed.submittedOn)}</p>` : ''}
        ${ed.notes ? `<p>${esc(ed.notes)}</p>` : '<p>BRYME has not submitted to this opportunity yet. This section will be updated only after a real submission.</p>'}
      </section>
      <section class="oc-report">
        <h2>Report outdated information</h2>
        <details><summary>Something on this page looks wrong</summary>${report}</details>
      </section>
    </main>`;

    write('make-money/writing/' + o.slug, layout({
      title: o.seoTitle || (o.publication + ' — ' + o.title),
      description: (o.excerpt || '').slice(0, 158),
      path: pagePath,
      activeNav: 'make-money',
      ogType: 'article',
      schema: [{
        '@context': 'https://schema.org', '@type': 'Article',
        headline: o.publication + ' — ' + o.title,
        dateModified: o.lastVerified,
        description: o.excerpt || undefined,
        mainEntityOfPage: absUrl(pagePath)
      }, breadcrumbs(dCrumbs)],
      body
    }));
  });

  console.log('Opportunity catalog: ' + all.length + ' writing listings.');
};

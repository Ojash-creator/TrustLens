(() => {
'use strict';
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const sleep = ms => new Promise(r => setTimeout(r, ms));
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

class Raw { constructor(s) { this.s = s; } }
const raw = s => new Raw(String(s));
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const flat = v => (v === false || v == null) ? '' : Array.isArray(v) ? v.map(flat).join('') : v instanceof Raw ? v.s : esc(v);
const html = (strings, ...vals) => new Raw(strings.reduce((a, s, i) => a + s + (i < vals.length ? flat(vals[i]) : ''), ''));
const mount = (el, tpl) => { el.innerHTML = tpl.s; return el; };

const ICONS = {
  pin: '<path d="M12 21s-7-6.2-7-11a7 7 0 1 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
  briefcase: '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M3 13h18"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',
  news: '<path d="M5 4h11a2 2 0 0 1 2 2v13H7a2 2 0 0 1-2-2V4z"/><path d="M18 9h2a1 1 0 0 1 1 1v7a2 2 0 0 1-2 2M8 8h6M8 12h6M8 16h4"/>',
  cart: '<circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M3 4h2.5l2.2 10.5a1 1 0 0 0 1 .8h8.6a1 1 0 0 0 1-.8L20 8H6.2"/>',
  chat: '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.3A8 8 0 1 1 21 12z"/>',
  building: '<path d="M4 21V5a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v16M14 10h5a1 1 0 0 1 1 1v10M3 21h18M8 8h2M8 12h2M8 16h2"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>', alert: '<path d="M12 4l9 16H3L12 4z"/><path d="M12 10v4M12 17.5v.01"/>',
  x: '<path d="M6 6l12 12M18 6L6 18"/>', info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 7.5v.01"/>',
  question: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.4-1 .9-1 1.7M12 17v.01"/>',
  chev: '<path d="M6 9l6 6 6-6"/>', copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/>',
  download: '<path d="M12 4v11M7 11l5 5 5-5M5 20h14"/>',
  printer: '<path d="M7 9V4h10v5M7 17H5a1 1 0 0 1-1-1v-5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v5a1 1 0 0 1-1 1h-2"/><rect x="7" y="14" width="10" height="6"/>',
  share: '<circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="18" cy="18" r="2.5"/><path d="M8.2 10.8l7.6-3.6M8.2 13.2l7.6 3.6"/>',
  trash: '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>', play: '<path d="M7 5l12 7-12 7V5z"/>',
};
const ic = name => raw(`<svg class="ic" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ''}</svg>`);

const ENGINE_ICON = { google_maps: 'pin', google_maps_reviews: 'chat', google_jobs: 'briefcase', google_shopping: 'cart', google_news: 'news', google: 'search' };
const ENGINE_LABEL = { google_maps: 'Google Maps', google_maps_reviews: 'Maps reviews', google_jobs: 'Google Jobs', google_shopping: 'Google Shopping', google_news: 'Google News', google: 'Google Search' };
const VERDICT_LABEL = { high_risk: 'High risk', caution: 'Proceed with caution', trustworthy: 'Looks legitimate', insufficient: 'Not enough evidence' };
const STATUS_ICON = { pass: 'check', warn: 'alert', fail: 'x', info: 'info', unknown: 'question' };
const SHORT = { 'job-fake-wfh': 'Fake work-from-home offer', 'job-legit-analyst': 'Real analytics job', 'job-bpo-mixed': 'Shaky call-centre job',
  'job-unknown': 'Tiny unknown firm', 'shop-fake-headphones': '80% off headphones', 'shop-legit-headphones': 'Established store',
  'local-coaching-advance': 'Coaching asks full fee', 'local-dental-clinic': 'Neighbourhood clinic' };

const fmtINR = n => '\u20b9' + Math.round(n).toLocaleString('en-IN');
const fmtPts = p => p > 0 ? `+${p}` : p < 0 ? `\u2212${Math.abs(p)}` : '0';
const ptsClass = p => p > 0 ? 'pos' : p < 0 ? 'neg' : 'zero';
const reEsc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const fmtDate = iso => { try { return new Date(iso).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }); } catch { return iso || ''; } };

function toast(msg) {
  const t = $('#toast'); t.textContent = msg; t.classList.add('on');
  clearTimeout(toast.h); toast.h = setTimeout(() => t.classList.remove('on'), 2200);
}

const MODES = {
  job: { label: 'Job offer', icon: 'briefcase',
    intro: 'Enter what the offer says. Adding the recruiter e-mail and the message lets TrustLens check who is really writing to you.',
    fields: [
      { key: 'name', label: 'Company name', ph: 'e.g. Kestrel Analytics Pvt Ltd', req: true },
      { key: 'role', label: 'Job title', ph: 'e.g. Junior Data Analyst', opt: true },
      { key: 'location', label: 'City', ph: 'e.g. Hyderabad', opt: true },
      { key: 'email', label: 'Recruiter e-mail', ph: 'e.g. careers@company.com', opt: true },
      { key: 'message', label: 'The offer message', ph: 'Paste the WhatsApp, SMS or e-mail text here', opt: true, wide: true, area: true,
        hint: 'TrustLens highlights phrases that match known job scams, such as fees and "no interview".' },
    ] },
  shop: { label: 'Online shop', icon: 'cart',
    intro: 'Enter the store, the product and the price you were shown. The price is compared with Google Shopping sellers.',
    fields: [
      { key: 'name', label: 'Store name', ph: 'e.g. UrbanCart India', opt: true },
      { key: 'url', label: 'Store link', ph: 'e.g. https://www.store.in/product', opt: true },
      { key: 'product', label: 'Product', ph: 'e.g. Sony WH-1000XM5 headphones', opt: true },
      { key: 'price', label: 'Price you were shown (\u20b9)', ph: 'e.g. 24990', opt: true },
      { key: 'message', label: 'What the seller told you', ph: 'Paste the ad text, DM or WhatsApp chat', opt: true, wide: true, area: true,
        hint: 'Payment demands like "personal UPI only" are flagged.' },
    ] },
  local: { label: 'Local business', icon: 'building',
    intro: 'For coaching centres, clinics, contractors, agents and any business asking for money before service.',
    fields: [
      { key: 'name', label: 'Business name', ph: 'e.g. Green Leaf Dental Clinic', req: true },
      { key: 'location', label: 'City', ph: 'e.g. Bengaluru', opt: true },
      { key: 'message', label: 'What they asked you to do', ph: 'e.g. Pay the full fee in advance, no refund', opt: true, wide: true, area: true,
        hint: 'Promises like "guaranteed selection" and full advance payment are flagged.' },
    ] },
};

const SOURCES = [
  { icon: 'pin', title: 'Google Maps', body: 'Does the business exist at a real address, and what do its customers say?' },
  { icon: 'briefcase', title: 'Google Jobs', body: 'Is the role advertised publicly by the company that claims to be hiring?' },
  { icon: 'cart', title: 'Google Shopping', body: 'How does the price compare with what other sellers charge for the same product?' },
  { icon: 'search', title: 'Google Search', body: 'Do other pages link the name to scams or complaints? A follow-up search digs into forums when the first pass finds smoke.' },
  { icon: 'news', title: 'Google News', body: 'Is there reputable coverage, good or bad, about this name?' },
  { icon: 'chat', title: 'Maps reviews', body: 'What do the lowest-rated customers actually complain about?' },
];

const HOW = [
  ['Describe it', 'Paste the offer, the link or the name. Add the message text if you have it, so TrustLens can highlight what they asked of you.'],
  ['Plan the searches', 'TrustLens picks the SerpApi engines that fit the case and adds follow-up searches when the first results look suspicious.'],
  ['Score the evidence', 'Each finding moves the score by a fixed, published amount. Missing data lowers the evidence coverage instead of being guessed.'],
  ['Decide with proof', 'You get a verdict, the reasons, every source, and the exact steps to take next, including where to report a scam in India.'],
];

const SCORING = {
  job: [
    ['Business footprint', 'Google Maps', 12, -10, 'A matching business listing with an address.'],
    ['Public reviews', 'Google Maps', 8, -10, 'Rating and number of reviews.'],
    ['What unhappy customers say', 'Maps reviews', 6, -12, 'Fetched only when the rating is below 3.6.'],
    ['Listed on Google Jobs', 'Google Jobs', 16, -6, 'A live posting from the same company.'],
    ['Recruiter e-mail', 'Your input', 10, -16, 'Free-mail senders, look-alike domains, domain that does not match the company.'],
    ['What they asked of you', 'Your input', 4, -35, 'Fees, WhatsApp-only, "no interview", Aadhaar requests, pressure.'],
    ['Scam and complaint reports', 'Google Search', 10, -24, 'Pages linking the name to scams, with a follow-up on forums.'],
    ['News coverage', 'Google News', 6, -16, 'Reputable stories, positive or negative.'],
  ],
  shop: [
    ['Price against the market', 'Google Shopping', 10, -26, 'Listed price versus the median of comparable sellers.'],
    ['Known seller', 'Google Shopping', 14, -4, 'Is the store one of Google\'s listed sellers?'],
    ['Business footprint', 'Google Maps', 8, -2, 'Online-only stores are not penalised much.'],
    ['Public reviews', 'Google Maps', 8, -10, 'Rating and number of reviews.'],
    ['Website address', 'Your input', 6, -24, 'Look-alike brands, cheap endings, hyphens, missing HTTPS.'],
    ['What they asked of you', 'Your input', 4, -35, 'Personal UPI, full advance, no returns, extreme discounts.'],
    ['Scam and complaint reports', 'Google Search', 10, -24, 'Pages linking the store to scams, with a forum follow-up.'],
    ['News coverage', 'Google News', 5, -16, 'Reputable stories, positive or negative.'],
  ],
  local: [
    ['Business footprint', 'Google Maps', 16, -18, 'A local business that cannot be found is a serious flag.'],
    ['Public reviews', 'Google Maps', 14, -14, 'Rating and number of reviews.'],
    ['What unhappy customers say', 'Maps reviews', 6, -16, 'Repeated fraud or refund complaints in the lowest-rated reviews.'],
    ['Contact details', 'Google Maps', 6, -6, 'Phone, website and address all published.'],
    ['What they asked of you', 'Your input', 4, -35, 'Guaranteed results, full upfront payment, no refund, cash only.'],
    ['Scam and complaint reports', 'Google Search', 10, -24, 'Pages linking the name to scams, with a forum follow-up.'],
    ['News coverage', 'Google News', 5, -16, 'Reputable stories, positive or negative.'],
  ],
};

const GROUPS = [['identity', 'Who they are'], ['reputation', 'What people say'], ['market', 'How it compares'], ['behaviour', 'How they behave'], ['coverage', 'What the web says']];
const STATUS_ORDER = { fail: 0, warn: 1, info: 2, pass: 3, unknown: 4 };

const SPECIMEN = [
  'Congratulations! You are selected for Data Entry Executive at SwiftHire Global Services. ',
  { t: 'No interview required.', tag: 'skips hiring' }, ' Earn \u20b94,000 daily by simple typing tasks. To confirm your seat, ',
  { t: 'pay a refundable registration fee of \u20b92,499', tag: 'asks for money' }, ' and ',
  { t: 'send your Aadhaar and bank details on WhatsApp only.', tag: 'wants your documents' }, ' ',
  { t: 'Only 5 vacancies left, hurry!', tag: 'pressure' },
];

const state = { mode: 'job', sample: null, samples: [], api: null, forceDemo: false, running: false,
  values: { job: {}, shop: {}, local: {} }, report: null, source: 'live' };
const HKEY = 'trustlens.history.v1';

async function init() {
  renderTabs(); renderFields(); renderSources(); renderHow(); renderScoring('job'); renderSpecimen();
  await detectBackend();
  renderQuickSamples(); renderCases(); renderHistory(); updateCost();
  bindGlobal();
  const m = location.hash.match(/^#run=([\w-]+)/);
  if (m) { const s = state.samples.find(x => x.id === m[1]); if (s) { applySample(s); run(); } }
}

async function detectBackend() {
  const pill = $('#modePill');
  const set = (cls, txt) => { pill.className = 'mode-pill ' + cls; $('.txt', pill).textContent = txt; };
  try {
    if (location.protocol === 'file:') throw new Error('static file');
    const ctl = new AbortController(); const t = setTimeout(() => ctl.abort(), 1800);
    const res = await fetch('/api/health', { cache: 'no-store', signal: ctl.signal }); clearTimeout(t);
    if (!res.ok) throw new Error('no api');
    state.api = await res.json();
    state.samples = await (await fetch('/api/samples')).json();
    if (state.api.live_available) {
      set('live', `Live search on, ${state.api.searches_today}/${state.api.daily_limit} used today`);
      $('#demoSwitchWrap').hidden = false;
    } else { set('demo', 'Demo mode: recorded data'); }
  } catch {
    state.api = null;
    state.samples = (window.TRUSTLENS_DEMO && window.TRUSTLENS_DEMO.samples) || [];
    set('static', 'Offline demo: recorded cases');
  }
}

function renderTabs() {
  const tabs = $('#modeTabs');
  mount(tabs, html`${Object.entries(MODES).map(([k, m]) => html`
    <button type="button" class="tab" role="tab" id="tab-${k}" data-mode="${k}" aria-selected="${k === state.mode}" tabindex="${k === state.mode ? 0 : -1}">${ic(m.icon)}${m.label}</button>`)}`);
  tabs.onclick = e => { const b = e.target.closest('.tab'); if (b) setMode(b.dataset.mode); };
  tabs.onkeydown = e => {
    const keys = Object.keys(MODES); let i = keys.indexOf(state.mode);
    if (e.key === 'ArrowRight') i = (i + 1) % keys.length; else if (e.key === 'ArrowLeft') i = (i + keys.length - 1) % keys.length; else return;
    e.preventDefault(); setMode(keys[i]); $(`#tab-${keys[i]}`).focus();
  };
}

function setMode(mode) {
  if (mode === state.mode) return;
  stashValues(); state.mode = mode; state.sample = null;
  renderTabs(); renderFields(); renderQuickSamples(); updateCost(); hideError();
}
function stashValues() { $$('#fields [name]').forEach(el => { state.values[state.mode][el.name] = el.value; }); }

function renderFields() {
  const m = MODES[state.mode], v = state.values[state.mode];
  $('#modeIntro').textContent = m.intro;
  mount($('#fields'), html`${m.fields.map(f => html`
    <div class="field ${f.wide ? 'wide' : ''}">
      <label for="f-${f.key}">${f.label}${f.opt ? html` <span class="opt">(optional)</span>` : ''}</label>
      ${f.area
        ? html`<textarea id="f-${f.key}" name="${f.key}" placeholder="${f.ph}" maxlength="4000">${v[f.key] || ''}</textarea>`
        : html`<input id="f-${f.key}" name="${f.key}" type="text" placeholder="${f.ph}" value="${v[f.key] || ''}" maxlength="300" ${f.key === 'price' ? 'inputmode="numeric"' : ''}>`}
      ${f.hint ? html`<span class="hint">${f.hint}</span>` : ''}
    </div>`)}`);
  $('#fields').oninput = () => { stashValues(); syncSample(); };
}

function syncSample() {
  if (!state.sample) return;
  const s = state.samples.find(x => x.id === state.sample);
  const cur = state.values[state.mode];
  const same = s && Object.entries(s.inputs).every(([k, val]) => (cur[k] || '') === val);
  if (!same) { state.sample = null; $$('.sample-row .chip').forEach(c => c.classList.remove('active')); }
}

function renderQuickSamples() {
  const list = state.samples.filter(s => s.mode === state.mode);
  const row = $('#quickSamples');
  if (!list.length) { row.hidden = true; return; }
  row.hidden = false;
  mount(row, html`<span class="lbl">Try a recorded case:</span>${list.map(s => html`
    <button type="button" class="chip ${state.sample === s.id ? 'active' : ''}" data-id="${s.id}">${SHORT[s.id] || s.title}</button>`)}`);
  row.onclick = e => { const c = e.target.closest('.chip'); if (c) applySample(state.samples.find(s => s.id === c.dataset.id)); };
}

function applySample(s) {
  if (!s) return;
  state.mode = s.mode; state.sample = s.id; state.values[s.mode] = { ...s.inputs };
  renderTabs(); renderFields(); renderQuickSamples(); updateCost(); hideError();
}

function updateCost() {
  const demo = !state.api || !state.api.live_available || state.forceDemo;
  $('#costNote').textContent = demo ? 'Recorded data, no search credits used' : 'Uses about 4 to 6 searches';
}

function showError(msg) { const e = $('#formError'); e.textContent = msg; e.hidden = false; }
function hideError() { $('#formError').hidden = true; }

function collect() {
  stashValues();
  const v = { ...state.values[state.mode] }, out = {};
  for (const f of MODES[state.mode].fields) out[f.key] = (v[f.key] || '').trim();
  return out;
}
function validate(inputs) {
  if (state.mode === 'shop' && !(inputs.name || inputs.url || inputs.product)) return 'Enter a store name, a store link or a product.';
  if (state.mode === 'job' && inputs.name.length < 2) return 'Enter the company name from the job offer.';
  if (state.mode === 'local' && inputs.name.length < 2) return 'Enter the business name.';
  return '';
}

async function analyze(mode, inputs, sampleId) {
  if (state.api) {
    const res = await fetch('/api/analyze', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode, inputs, sample_id: sampleId, demo: state.forceDemo }) });
    const data = await res.json().catch(() => ({ error: 'The server sent an unexpected response.' }));
    if (!res.ok) throw new Error(data.error || 'The check failed.');
    return data;
  }
  const rep = window.TRUSTLENS_DEMO && window.TRUSTLENS_DEMO.reports && window.TRUSTLENS_DEMO.reports[sampleId];
  if (sampleId && rep) return JSON.parse(JSON.stringify(rep));
  throw new Error('This offline copy can only replay the recorded cases. Run "python run.py" and add a SerpApi key to check anything you like.');
}

async function run() {
  if (state.running) return;
  const inputs = collect(), problem = validate(inputs);
  if (problem) { showError(problem); return; }
  hideError(); state.running = true;
  const btn = $('#runBtn'); btn.disabled = true; $('.btn-label', btn).textContent = 'Checking\u2026';
  const section = $('#report'); section.hidden = false; $('#sheetMount').innerHTML = '';
  renderTracePlanning();
  section.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' });
  try {
    const report = await analyze(state.mode, inputs, state.sample);
    await playTrace(report);
    state.report = report; renderReport(report); saveHistory(report); renderHistory();
  } catch (err) {
    section.hidden = true; showError(err.message || 'Something went wrong. Try again.');
    $('#checker').scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'center' });
  } finally { state.running = false; btn.disabled = false; $('.btn-label', btn).textContent = 'Run the check'; }
}

function traceShell(sub, rows) {
  return html`<div class="card trace">
    <div class="trace-head"><h3>Search log</h3><span class="sub" id="traceSub">${sub}</span></div>
    <div class="trace-list" id="traceList">${rows}</div></div>`;
}
function renderTracePlanning() {
  mount($('#traceMount'), traceShell('Planning the searches\u2026', html`
    <div class="trace-row pending"><span class="eng"><span class="spin"></span>TrustLens</span><span class="q">choosing which SerpApi engines fit this case</span><span class="t-meta"></span></div>`));
}
function traceRow(t, st) {
  const done = st === 'done';
  const meta = !done ? html`<span class="spin"></span>` : html`
    ${t.followup && html`<span class="tag fu">follow-up</span>`}${t.cached && html`<span class="tag cache">cached</span>`}
    <span>${t.status === 'ok' ? `${t.results} result${t.results === 1 ? '' : 's'}` : t.status === 'empty' ? 'no results' : 'failed'}, ${t.ms} ms</span>`;
  return html`<div class="trace-row ${done ? 'done' : 'pending'}" data-step="${t.step}">
    <span class="eng">${ic(ENGINE_ICON[t.engine] || 'search')}${t.engine_label || ENGINE_LABEL[t.engine] || t.engine}</span>
    <span class="q">${t.query}</span><span class="t-meta">${meta}</span></div>`;
}
async function playTrace(report) {
  const list = $('#traceList'); list.innerHTML = '';
  const fast = reduced || report.source === 'live';
  for (const t of report.trace) {
    list.insertAdjacentHTML('beforeend', traceRow(t, 'pending').s);
    const row = list.lastElementChild;
    await sleep(fast ? 160 : Math.min(760, Math.max(360, t.ms * .55)));
    row.outerHTML = traceRow(t, 'done').s;
  }
  const fu = report.trace.filter(t => t.followup).length, cached = report.trace.filter(t => t.cached).length;
  $('#traceSub').textContent = `${report.trace.length} search${report.trace.length === 1 ? '' : 'es'}` + (fu ? `, ${fu} follow-up` : '') + (cached ? `, ${cached} from cache` : '');
  const card = $('#traceList').closest('.trace');
  card.insertAdjacentHTML('beforeend', html`<div class="trace-foot">Engines used: ${report.usage.engines.map(e => ENGINE_LABEL[e] || e).join(', ') || 'none'}. Billable searches: ${report.usage.searches}${report.source === 'demo' ? ' (recorded, none charged)' : ''}.</div>`.s);
  await sleep(fast ? 120 : 380);
}

function link(url, text) {
  const shown = text || url;
  if (state.source === 'demo' || !/^https?:\/\//i.test(url || '')) {
    return html`<span class="fake-link" ${state.source === 'demo' ? raw('title="Illustrative link from recorded demo data"') : ''}>${shown}</span>`;
  }
  return html`<a href="${url}" target="_blank" rel="noopener noreferrer nofollow">${shown}</a>`;
}
function highlightTerms(text, terms) {
  const t = String(text || '');
  if (!terms || !terms.length) return html`${t}`;
  const re = new RegExp('(' + terms.map(reEsc).join('|') + ')\\w*', 'gi');
  let out = '', last = 0, m;
  while ((m = re.exec(t))) { out += esc(t.slice(last, m.index)) + `<mark>${esc(m[0])}</mark>`; last = m.index + m[0].length; }
  return raw(out + esc(t.slice(last)));
}
function xray(text, highlights) {
  const cps = Array.from(text || ''); let out = '', pos = 0;
  for (const h of highlights || []) {
    if (h.start < pos) continue;
    out += esc(cps.slice(pos, h.start).join('')) + `<mark class="hl ${esc(h.severity)}" title="${esc(h.label)}">${esc(cps.slice(h.start, h.end).join(''))}</mark>`;
    pos = h.end;
  }
  return raw(out + esc(cps.slice(pos).join('')));
}

function renderReport(r) {
  state.source = r.source;
  const p = r.panels || {}, lvl = r.verdict.level;
  const banner = r.source === 'demo' && r.sample_id
    ? 'Recorded demo data. Every business here is fictional and links are illustrative.' : (r.notes && r.notes[0]) || '';
  const sheet = html`
  <article class="card sheet" id="sheet" tabindex="-1" aria-label="TrustLens report for ${r.entity}">
    <div class="sheet-head"><span><strong>${r.mode_label} check</strong></span><span>${r.entity}</span>
      <span class="grow">Case ${r.id}, ${fmtDate(r.generated_at)}</span></div>
    ${banner && html`<p class="banner">${banner}</p>`}
    <div class="reading">
      <div><div class="score-num ${lvl}" id="scoreNum">0</div><div class="score-of">out of 100</div></div>
      <div class="range" aria-label="Score ${r.score} on a scale of 0 to 100">
        <div class="range-bar"><span class="z z1"></span><span class="z z2"></span><span class="z z3"></span><span class="marker" id="marker"></span></div>
        <div class="range-labels"><span class="l1">High risk</span><span class="l2">Caution</span><span class="l3">Looks legitimate</span></div></div>
      <div class="stamp ${lvl}" id="stamp">${r.verdict.label}</div>
    </div>
    <div class="verdict-copy"><h2 class="headline">${r.verdict.headline}</h2><p class="summary">${r.summary}</p>
      ${r.summary_source === 'claude' && html`<p class="src-note">Summary written by Claude from the findings below. It did not influence the score.</p>`}</div>
    <div class="meta-row">
      <div class="cov" title="How much of the picture TrustLens could see"><div class="cov-bar"><i style="width:${r.confidence.pct}%"></i></div><span class="cov-t">Evidence coverage ${r.confidence.pct}%</span></div>
      <div class="counts">
        ${r.counts.fail ? html`<span class="count fail">${ic('x')}${r.counts.fail} red flag${r.counts.fail > 1 ? 's' : ''}</span>` : ''}
        ${r.counts.warn ? html`<span class="count warn">${ic('alert')}${r.counts.warn} caution${r.counts.warn > 1 ? 's' : ''}</span>` : ''}
        ${r.counts.pass ? html`<span class="count pass">${ic('check')}${r.counts.pass} reassuring</span>` : ''}
        ${r.counts.unknown ? html`<span class="count unknown">${ic('question')}${r.counts.unknown} no data</span>` : ''}
      </div>
      <div class="actions">
        <button class="btn small" data-act="copy">${ic('copy')}Copy summary</button>
        <button class="btn small" data-act="wa">${ic('share')}Share on WhatsApp</button>
        <button class="btn small" data-act="json">${ic('download')}Download JSON</button>
        <button class="btn small" data-act="print">${ic('printer')}Print</button>
      </div>
    </div>
    <section class="block" aria-labelledby="whyH"><h3 id="whyH">How the score was built</h3>
      <p class="sub">Every check starts at 50. Each finding below moved the score by the amount shown.</p>${waterfall(r)}</section>
    <section class="block" aria-labelledby="findH"><h3 id="findH">Findings</h3>
      <p class="sub">Open any row to see the reasoning and the evidence behind it.</p>
      <div class="filters" id="filters">${filterButtons(r)}</div><div class="ledger" id="ledger">${ledger(r)}</div></section>
    ${evidenceBlock(r, p)}
    <section class="block" aria-labelledby="nextH"><h3 id="nextH">What to do next</h3>
      <div class="next">${r.next_steps.map((s, i) => html`<label class="next-item"><input type="checkbox" id="ns${i}"><div><b>${s.title}</b><p>${s.body}</p></div></label>`)}</div>
      ${(lvl === 'high_risk' || lvl === 'caution') && html`<div class="report-where"><span><b>1930</b>Cyber crime helpline</span><span><b>1915</b>National Consumer Helpline</span><span>cybercrime.gov.in</span></div>`}
    </section>
  </article>`;
  mount($('#sheetMount'), sheet);
  animateReport(r);
  $('#sheet').focus({ preventScroll: true });
  setTimeout(() => $('#sheetMount').scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' }), 60);
}

function animateReport(r) {
  const num = $('#scoreNum'), marker = $('#marker'), stamp = $('#stamp');
  requestAnimationFrame(() => requestAnimationFrame(() => {
    marker.style.left = r.score + '%'; stamp.classList.add('land');
    $$('.wf-bar').forEach(b => { b.style.width = b.dataset.w; });
  }));
  if (reduced) { num.textContent = r.score; return; }
  const t0 = performance.now(), dur = 1000;
  const step = now => { const k = Math.min(1, (now - t0) / dur); num.textContent = Math.round(r.score * (1 - Math.pow(1 - k, 3))); if (k < 1) requestAnimationFrame(step); };
  requestAnimationFrame(step);
}

function waterfall(r) {
  const rows = r.waterfall; if (!rows.length) return html`<p class="empty-note">No scored findings yet.</p>`;
  const max = Math.max(...rows.map(x => Math.abs(x.points)), 10);
  return html`<div class="wf" role="list">
    ${rows.map(x => html`<div class="wf-row" role="listitem"><span>${x.title}</span>
      <span class="wf-track"><span class="wf-bar ${x.points > 0 ? 'pos' : 'neg'}" data-w="${(Math.abs(x.points) / max) * 50}%"></span></span>
      <span class="wf-val ${x.points > 0 ? 'pos' : 'neg'}">${fmtPts(x.points)}</span></div>`)}
    <div class="wf-axis"><span></span><span class="mid"><span>Lowers trust</span><span>Raises trust</span></span><span></span></div>
    <div class="wf-total"><span>Start at 50, add the findings${r.score !== 50 + rows.reduce((a, x) => a + x.points, 0) ? ' (kept between 3 and 97)' : ''}</span><b>${r.score}</b></div>
  </div>`;
}

function filterButtons(r) {
  const c = r.counts, all = r.signals.length;
  const defs = [['all', `All (${all})`], ['fail', `Red flags (${c.fail})`], ['warn', `Cautions (${c.warn})`], ['pass', `Reassuring (${r.signals.filter(s => s.status === 'pass' || s.status === 'info').length})`], ['unknown', `No data (${c.unknown})`]];
  return html`${defs.map(([k, l], i) => html`<button class="filter" data-f="${k}" aria-pressed="${i === 0}">${l}</button>`)}`;
}

function ledger(r) {
  return html`${GROUPS.map(([cat, label]) => {
    const sigs = r.signals.filter(s => s.category === cat).sort((a, b) => STATUS_ORDER[a.status] - STATUS_ORDER[b.status] || Math.abs(b.points) - Math.abs(a.points));
    if (!sigs.length) return '';
    return html`<div class="group"><div class="group-title">${label}</div>${sigs.map(s => signalRow(s))}</div>`;
  })}`;
}

function signalRow(s) {
  const open = s.status === 'fail';
  const engines = (s.engines || []).map(e => html`<span class="src-chip">${ic(ENGINE_ICON[e] || 'search')}${ENGINE_LABEL[e] || e}</span>`);
  const pts = s.status === 'unknown' ? '\u2013' : fmtPts(s.points);
  return html`<div class="row" data-status="${s.status}">
    <button class="row-btn" aria-expanded="${open}" aria-controls="b-${s.id}">
      <span class="glyph ${s.status}">${ic(STATUS_ICON[s.status] || 'info')}</span>
      <span><span class="row-title" style="display:block">${s.title}${s.critical && s.status !== 'pass' ? html`<span class="crit-note">critical</span>` : ''}</span><span class="row-find" style="display:block">${s.finding}</span></span>
      <span class="row-src">${engines}</span>
      <span class="impact ${s.status === 'unknown' ? 'zero' : ptsClass(s.points)}">${pts}</span>
      <span class="chev">${ic('chev')}</span>
    </button>
    <div class="row-body ${open ? 'open' : ''}" id="b-${s.id}">
      ${s.detail && html`<p class="why">${s.detail}</p>`}
      ${(s.evidence || []).length ? html`<dl class="ev">${s.evidence.map(e => html`<div class="ev-row"><dt>${e.label}</dt><dd>${e.url ? link(e.url, e.value) : e.value}</dd></div>`)}</dl>` : ''}
    </div>
  </div>`;
}

function evidenceBlock(r, p) {
  const tabs = [];
  const msg = p.message, url = p.url;
  if ((msg && msg.text) || (url && url.host)) tabs.push(['xray', 'Message X-ray', panelXray(msg, url)]);
  if (p.place || (p.near && p.near.length)) tabs.push(['place', 'Business listing', panelPlace(p)]);
  if (p.prices) tabs.push(['prices', 'Price check', panelPrices(p.prices)]);
  if (p.jobs && p.jobs.length) tabs.push(['jobs', 'Job postings', panelJobs(p.jobs)]);
  if (p.web && p.web.length) tabs.push(['web', 'Web pages', panelWeb(p.web)]);
  if (p.news && p.news.length) tabs.push(['news', 'News', panelNews(p.news)]);
  if (p.reviews && p.reviews.length) tabs.push(['reviews', 'Lowest-rated reviews', panelReviews(p.reviews)]);
  if (!tabs.length) return '';
  const first = (msg && msg.flags && msg.flags.length) ? 'xray' : tabs[0][0];
  return html`<section class="block" aria-labelledby="evH"><h3 id="evH">The evidence</h3>
    <p class="sub">The raw material behind the findings, straight from the searches.</p>
    <div class="ev-tabs"><div class="tabs small" role="tablist" id="evTabs">${tabs.map(([k, l]) => html`
      <button class="tab" role="tab" data-p="${k}" aria-selected="${k === first}" aria-controls="p-${k}">${l}</button>`)}</div>
    ${tabs.map(([k, , body]) => html`<div class="panel" id="p-${k}" role="tabpanel" ${k === first ? '' : raw('hidden')}>${body}</div>`)}</div>
  </section>`;
}

function panelXray(msg, url) {
  const parts = [];
  if (msg && msg.text) {
    parts.push(html`<div class="xray-grid"><div class="xray-bubble">${xray(msg.text, msg.highlights)}</div>
      <div class="xray-flags">${msg.flags.length ? msg.flags.map(f => html`
        <div class="xf ${f.severity}"><b>${f.label}</b><span>${f.why}</span><i>${f.matches.map(m => '\u201c' + m + '\u201d').join('  ')}</i></div>`)
        : html`<p class="empty-note">No known scam phrases found in this message.</p>`}</div></div>`);
  }
  if (url && url.host) {
    parts.push(html`<div style="margin-top:${msg && msg.text ? 30 : 0}px"><h4 style="font-size:19px;margin-bottom:10px">Web address: ${url.registrable || url.host}</h4>
      ${url.flags.length ? html`<div class="xray-flags">${url.flags.map(f => html`<div class="xf ${f.points >= 8 ? 'high' : ''}"><b>${f.label}</b><span>${f.why}</span></div>`)}</div>`
        : html`<p class="empty-note">No warning signs in the address itself.</p>`}</div>`);
  }
  return html`${parts}`;
}

function panelPlace(p) {
  const pl = p.place;
  if (!pl) {
    return html`<p class="empty-note">No Google Maps listing matched this name closely enough.</p>
      ${p.near && p.near.length ? html`<div class="near">Closest listings found: ${p.near.map(n => `${n.title} (${Math.round(n.match * 100)}% match)`).join('; ')}. These are different businesses.</div>` : ''}`;
  }
  const stars = pl.rating ? '\u2605'.repeat(Math.round(pl.rating)) + '\u2606'.repeat(5 - Math.round(pl.rating)) : '';
  return html`<div class="place">
    <div><h4>${pl.title}</h4>
      <div class="stars"><span class="s" aria-hidden="true">${stars}</span>${pl.rating ? `${pl.rating} from ${pl.reviews.toLocaleString('en-IN')} reviews` : 'No rating yet'}</div>
      <p style="margin-top:10px;color:var(--ink-2)">${pl.type || ''}</p>
      <p style="margin-top:14px">${link(pl.link, 'Open in Google Maps')}</p></div>
    <dl class="kv"><div><dt>Address</dt><dd>${pl.address || 'not shown'}</dd></div>
      <div><dt>Phone</dt><dd>${pl.phone || 'not shown'}</dd></div>
      <div><dt>Website</dt><dd>${pl.website ? link(pl.website, pl.website.replace(/^https?:\/\/(www\.)?/, '')) : 'not shown'}</dd></div>
      <div><dt>Name match</dt><dd><span class="flagchip match">${Math.round(pl.match * 100)}%</span></dd></div></dl>
  </div>`;
}

function priceChart(p) {
  const W = 720, H = 242, padL = 30, padR = 30, axisY = 156;
  const max = Math.max(p.max, p.listed) * 1.07, x = v => padL + (v / max) * (W - padL - padR);
  const tone = p.ratio < 0.6 ? 'var(--fail)' : p.ratio < 0.8 ? 'var(--warn)' : 'var(--pass)';
  const clampX = v => Math.min(W - 96, Math.max(96, v));
  const fmtK = v => v >= 1000 ? Math.round(v / 1000) + 'k' : Math.round(v);
  const ticks = [0, 1, 2, 3, 4].map(i => (max * i) / 4);
  const dots = p.items.map((it, i) => `<circle cx="${x(it.price).toFixed(1)}" cy="${axisY + ((i % 3) - 1) * 17}" r="7" fill="#5A6F93" stroke="#fff" stroke-width="2"><title>${esc(it.seller)}: ${esc(fmtINR(it.price))}</title></circle>`).join('');
  return raw(`<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Listed price ${esc(fmtINR(p.listed))} compared with market median ${esc(fmtINR(p.median))}">
    <rect x="${x(p.q1).toFixed(1)}" y="${axisY - 42}" width="${Math.max(4, x(p.q3) - x(p.q1)).toFixed(1)}" height="84" rx="4" fill="var(--brand-soft)"/>
    <line x1="${padL}" x2="${W - padR}" y1="${axisY}" y2="${axisY}" stroke="var(--rule-2)"/>
    ${ticks.map(t => `<line x1="${x(t).toFixed(1)}" x2="${x(t).toFixed(1)}" y1="${axisY + 44}" y2="${axisY + 50}" stroke="var(--rule-2)"/><text x="${x(t).toFixed(1)}" y="${axisY + 64}" font-size="12" text-anchor="middle">\u20b9${fmtK(t)}</text>`).join('')}
    <line x1="${x(p.median).toFixed(1)}" x2="${x(p.median).toFixed(1)}" y1="62" y2="${axisY + 44}" stroke="var(--brand)" stroke-width="2" stroke-dasharray="5 4"/>
    <text x="${clampX(x(p.median)).toFixed(1)}" y="22" font-size="13" text-anchor="middle" class="lbl-strong">Market median ${esc(fmtINR(p.median))}</text>
    ${dots}
    <line x1="${x(p.listed).toFixed(1)}" x2="${x(p.listed).toFixed(1)}" y1="84" y2="${axisY + 44}" stroke="${tone}" stroke-width="3"/>
    <circle cx="${x(p.listed).toFixed(1)}" cy="${axisY}" r="10" fill="${tone}" stroke="#fff" stroke-width="3"/>
    <text x="${clampX(x(p.listed)).toFixed(1)}" y="64" font-size="14" text-anchor="middle" class="lbl-strong" style="fill:${tone}">You were shown ${esc(fmtINR(p.listed))}</text>
  </svg>`);
}

function panelPrices(pr) {
  const pct = Math.round(Math.abs(1 - pr.ratio) * 100);
  return html`<p style="font-size:17px;max-width:70ch">The listed price is <b>${pct}% ${pr.ratio < 1 ? 'below' : 'above'}</b> the median of ${pr.items.length} sellers on Google Shopping.</p>
    ${priceChart(pr)}
    <div class="chart-legend"><span><i style="background:#5A6F93"></i>Seller price</span><span><i style="background:var(--brand-soft);border:1px solid var(--brand)"></i>Middle half of prices</span><span><i style="background:var(--brand)"></i>Median</span><span><i style="background:${pr.ratio < 0.6 ? 'var(--fail)' : pr.ratio < 0.8 ? 'var(--warn)' : 'var(--pass)'}"></i>Price you were shown</span></div>
    <div class="list" style="margin-top:22px">${pr.items.slice(0, 8).map(i => html`<div class="item" style="grid-template-columns:1fr auto;gap:12px"><span>${i.link ? link(i.link, i.seller) : i.seller}</span><b>${fmtINR(i.price)}</b></div>`)}</div>`;
}

function panelJobs(jobs) {
  return html`<div class="list">${jobs.map(j => html`<div class="item">
    <div class="item-title">${j.link ? link(j.link, j.title) : j.title}</div>
    <div class="item-meta"><span>${j.company || 'Unknown company'}</span>${j.location && html`<span>${j.location}</span>`}${j.via && html`<span>${j.via}</span>`}${j.posted && html`<span>${j.posted}</span>`}
      ${j.from_company ? html`<span class="flagchip match">Posted by this company</span>` : html`<span class="flagchip weak">Different employer</span>`}</div></div>`)}</div>`;
}
function panelWeb(items) {
  return html`<div class="list">${items.map(i => html`<div class="item">
    <div class="item-title">${link(i.link, i.title)}</div>
    <div class="item-meta"><span>${i.host}</span><span>${i.kind}</span>
      ${i.flag === 'strong' && html`<span class="flagchip strong">Scam or fraud report</span>`}${i.flag === 'weak' && html`<span class="flagchip weak">Complaints</span>`}${i.official && html`<span class="flagchip official">Official site</span>`}</div>
    <p class="item-snip">${highlightTerms(i.snippet, i.terms)}</p></div>`)}</div>`;
}
function panelNews(items) {
  return html`<div class="list">${items.map(i => html`<div class="item">
    <div class="item-title">${i.link ? link(i.link, i.title) : i.title}</div>
    <div class="item-meta"><span>${i.source || 'News'}</span>${i.date && html`<span>${i.date}</span>`}
      ${i.tone !== 'neutral' && html`<span class="flagchip ${i.tone}">${i.tone === 'negative' ? 'Negative' : 'Positive'}</span>`}</div>
    ${i.snippet && html`<p class="item-snip">${i.snippet}</p>`}</div>`)}</div>`;
}
function panelReviews(items) {
  return html`<p style="color:var(--ink-2);margin-bottom:8px">TrustLens asked Google Maps for the lowest-rated reviews first, because that is where honest warnings live.</p>
  <div class="list">${items.map(i => html`<div class="item">
    <div class="item-meta"><span style="color:#E0A100;letter-spacing:2px">${'\u2605'.repeat(i.rating || 0)}${'\u2606'.repeat(5 - (i.rating || 0))}</span><span>${i.user || 'Anonymous'}</span><span>${i.date || ''}</span>
      ${i.terms && i.terms.length ? html`<span class="flagchip strong">Serious complaint</span>` : ''}</div>
    <p class="item-snip">${highlightTerms(i.text, i.terms)}</p></div>`)}</div>`;
}

function summaryText(r) {
  return `TrustLens check for ${r.entity}: ${r.verdict.label} (${r.score}/100). ${r.verdict.headline} ${r.summary} Checked ${fmtDate(r.generated_at)}. Advisory only: verify independently before paying.`;
}
async function copyText(text) {
  try { await navigator.clipboard.writeText(text); }
  catch { const ta = document.createElement('textarea'); ta.value = text; document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); } catch { } ta.remove(); }
  toast('Summary copied');
}
function bindGlobal() {
  $('#checker').addEventListener('submit', e => { e.preventDefault(); run(); });
  $('#demoSwitch').addEventListener('change', e => { state.forceDemo = e.target.checked; updateCost(); });
  $('#clearHistory').addEventListener('click', () => { saveHistoryList([]); renderHistory(); toast('History cleared'); });
  document.addEventListener('click', e => {
    const act = e.target.closest('[data-act]'); const r = state.report;
    if (act && r) {
      const a = act.dataset.act;
      if (a === 'copy') copyText(summaryText(r));
      if (a === 'wa') window.open('https://wa.me/?text=' + encodeURIComponent(summaryText(r)), '_blank', 'noopener');
      if (a === 'print') window.print();
      if (a === 'json') {
        const blob = new Blob([JSON.stringify(r, null, 2)], { type: 'application/json' });
        const a2 = document.createElement('a'); a2.href = URL.createObjectURL(blob); a2.download = `trustlens-${r.id}.json`; a2.click(); URL.revokeObjectURL(a2.href);
      }
    }
    const rb = e.target.closest('.row-btn');
    if (rb) { const open = rb.getAttribute('aria-expanded') === 'true'; rb.setAttribute('aria-expanded', String(!open)); $('#' + rb.getAttribute('aria-controls')).classList.toggle('open', !open); }
    const f = e.target.closest('.filter'); if (f) applyFilter(f.dataset.f);
    const pt = e.target.closest('#evTabs .tab');
    if (pt) { $$('#evTabs .tab').forEach(t => t.setAttribute('aria-selected', String(t === pt))); $$('.ev-tabs .panel').forEach(p => { p.hidden = p.id !== 'p-' + pt.dataset.p; }); }
    const st = e.target.closest('#scoreTabs .tab'); if (st) renderScoring(st.dataset.m);
  });
}
function applyFilter(f) {
  $$('#filters .filter').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.f === f)));
  const show = s => f === 'all' || (f === 'pass' ? (s === 'pass' || s === 'info') : s === f);
  $$('#ledger .row').forEach(r => { r.hidden = !show(r.dataset.status); });
  $$('#ledger .group').forEach(g => { g.hidden = !$$('.row', g).some(r => !r.hidden); });
}

function renderSources() { mount($('#sourceList'), html`${SOURCES.map(s => html`<li><span class="src-ic">${ic(s.icon)}</span><h3>${s.title}</h3><p>${s.body}</p></li>`)}`); }
function renderHow() { mount($('#howSteps'), html`${HOW.map(([t, b]) => html`<li><h3>${t}</h3><p>${b}</p></li>`)}`); }
function renderScoring(mode) {
  const tabs = $('#scoreTabs');
  mount(tabs, html`${Object.entries(MODES).map(([k, m]) => html`<button class="tab" role="tab" data-m="${k}" aria-selected="${k === mode}">${ic(m.icon)}${m.label}</button>`)}`);
  mount($('#scoreTable'), html`<thead><tr><th>Check</th><th>Source</th><th>Best case</th><th>Worst case</th><th>What it looks at</th></tr></thead>
    <tbody>${SCORING[mode].map(([t, s, best, worst, d]) => html`<tr><td><b>${t}</b></td><td>${s}</td><td class="n pos">${fmtPts(best)}</td><td class="n neg">${fmtPts(worst)}</td><td>${d}</td></tr>`)}</tbody>`);
  mount($('#scoreRules'), html`
    <div><h4>Start at 50</h4><p>Scores are kept between 3 and 97, because public search can never prove anything absolutely.</p></div>
    <div><h4>Verdict bands</h4><p>72 or more looks legitimate. 45 to 71 means proceed with caution. Below 45 is high risk.</p></div>
    <div><h4>Safety rules</h4><p>Critical findings, such as a fee request or a bait price, cap the verdict at caution even if everything else looks good. A low score caused only by missing data becomes "Not enough evidence", never "High risk".</p></div>`);
}
function renderCases() {
  const list = $('#caseList');
  if (!state.samples.length) { mount(list, html`<p class="empty">Recorded cases are not available in this build.</p>`); return; }
  mount(list, html`${state.samples.map(s => html`<div class="case">
    <span class="m-ic">${ic(MODES[s.mode].icon)}</span><div><h3>${s.title}</h3><p>${s.blurb}</p></div>
    <span class="outcome ${s.expected}"><i></i>Recorded outcome: ${VERDICT_LABEL[s.expected]}</span>
    <button class="btn small" data-case="${s.id}">${ic('play')}Run this case</button></div>`)}`);
  list.onclick = e => { const b = e.target.closest('[data-case]'); if (b) { applySample(state.samples.find(s => s.id === b.dataset.case)); run(); } };
}
function renderSpecimen() {
  const el = $('#specimenText');
  mount(el, html`${SPECIMEN.map(p => typeof p === 'string' ? p : html`<span class="hl">${p.t}</span><span class="hl-tag">${p.tag}</span>`)}`);
  const hls = $$('.hl', el), tags = $$('.hl-tag', el), stamp = $('.mini-stamp');
  (async () => {
    await sleep(reduced ? 0 : 700);
    for (let i = 0; i < hls.length; i++) { hls[i].classList.add('on'); await sleep(reduced ? 0 : 380); tags[i].classList.add('on'); await sleep(reduced ? 0 : 420); }
    stamp.classList.add('on');
  })();
}

function loadHistory() { try { return JSON.parse(localStorage.getItem(HKEY) || '[]'); } catch { return []; } }
function saveHistoryList(list) {
  try { localStorage.setItem(HKEY, JSON.stringify(list.slice(0, 10))); }
  catch { try { localStorage.setItem(HKEY, JSON.stringify(list.slice(0, 3))); } catch { } }
}
function saveHistory(r) {
  const list = loadHistory().filter(h => h.id !== r.id);
  list.unshift({ id: r.id, at: r.generated_at, entity: r.entity, mode: r.mode_label, score: r.score, level: r.verdict.level, report: r });
  saveHistoryList(list);
}
function renderHistory() {
  const list = loadHistory(), box = $('#historyList');
  $('#clearHistory').hidden = !list.length;
  if (!list.length) { mount(box, html`<p class="empty">Your checks will appear here after you run one.</p>`); return; }
  mount(box, html`${list.map(h => html`<div class="h-row">
    <span class="h-score ${h.level}">${h.score}</span>
    <div><b>${h.entity}</b><span class="sm">${h.mode}, ${VERDICT_LABEL[h.level]}, ${fmtDate(h.at)}</span></div>
    <button class="btn small" data-open="${h.id}">Open report</button>
    <button class="btn small quiet" data-del="${h.id}" aria-label="Delete this check">${ic('trash')}</button></div>`)}`);
  box.onclick = e => {
    const o = e.target.closest('[data-open]'), d = e.target.closest('[data-del]');
    if (o) { const h = loadHistory().find(x => x.id === o.dataset.open); if (h && h.report) { state.report = h.report; $('#report').hidden = false; $('#traceMount').innerHTML = ''; renderReport(h.report); } }
    if (d) { saveHistoryList(loadHistory().filter(x => x.id !== d.dataset.del)); renderHistory(); }
  };
}

init();
})();

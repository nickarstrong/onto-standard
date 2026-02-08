// ONTO Chrome Extension — Content Script
// Detects AI responses on ChatGPT, Claude, Gemini and injects risk badges

const ONTO_API = 'https://api.ontostandard.org/v1/check';

const PLATFORMS = {
  'chatgpt.com': {
    responseSelector: '[data-message-author-role="assistant"]',
    textSelector: '.markdown',
    insertTarget: '.markdown',
    insertPosition: 'afterend'
  },
  'chat.openai.com': {
    responseSelector: '[data-message-author-role="assistant"]',
    textSelector: '.markdown',
    insertTarget: '.markdown',
    insertPosition: 'afterend'
  },
  'claude.ai': {
    responseSelector: '.font-claude-response',
    textSelector: null,
    insertTarget: null,
    insertPosition: 'append'
  },
  'gemini.google.com': {
    responseSelector: '.model-response-text',
    textSelector: null,
    insertTarget: null,
    insertPosition: 'append'
  }
};

let platform = null;
let processedSet = new WeakSet();
let apiKey = null;

function detectPlatform() {
  const host = window.location.hostname;
  for (const [domain, config] of Object.entries(PLATFORMS)) {
    if (host.includes(domain)) return config;
  }
  return null;
}

async function init() {
  platform = detectPlatform();
  if (!platform) return;

  try {
    const data = await chrome.storage.sync.get(['onto_api_key']);
    apiKey = data.onto_api_key || null;
  } catch(e) {}

  const observer = new MutationObserver(debounce(scanResponses, 500));
  observer.observe(document.body, { childList: true, subtree: true });
  setTimeout(scanResponses, 1000);
}

function debounce(fn, ms) {
  let timer;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), ms);
  };
}

function scanResponses() {
  if (!platform) return;
  const responses = document.querySelectorAll(platform.responseSelector);
  responses.forEach(el => {
    if (processedSet.has(el)) return;
    const text = getResponseText(el);
    if (!text || text.length < 2) return;
    processedSet.add(el);
    injectBadge(el, text);
  });
}

function getResponseText(el) {
  const textEl = platform.textSelector ? el.querySelector(platform.textSelector) : el;
  if (!textEl) return el.innerText?.trim() || '';
  return textEl.innerText?.trim() || '';
}

function injectBadge(responseEl, text) {
  const target = platform.insertTarget ? responseEl.querySelector(platform.insertTarget) : responseEl;
  if (!target) return;
  if (responseEl.querySelector('.onto-badge-btn, .onto-result')) return;

  const btn = document.createElement('span');
  btn.className = 'onto-badge-btn';
  btn.innerHTML = '<span class="onto-sigma">\u03C3</span> check';
  btn.title = 'Evaluate with ONTO Standard';
  btn.onclick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    evaluateResponse(btn, text);
  };

  if (platform.insertPosition === 'afterend') {
    target.parentNode.insertBefore(btn, target.nextSibling);
  } else {
    target.appendChild(btn);
  }
}

async function evaluateResponse(badgeEl, text) {
  const parent = badgeEl.parentNode;
  const loading = document.createElement('span');
  loading.className = 'onto-loading';
  loading.innerHTML = '<span class="onto-dot">\u03C3</span> evaluating...';
  parent.replaceChild(loading, badgeEl);

  try {
    const body = {
      output: text.substring(0, 10000),
      domain: detectDomain(text)
    };

    const headers = { 'Content-Type': 'application/json' };
    if (apiKey) headers['x-api-key'] = apiKey;

    const resp = await fetch(ONTO_API, {
      method: 'POST',
      headers,
      body: JSON.stringify(body)
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || 'HTTP ' + resp.status);
    }

    const data = await resp.json();
    showResult(parent, loading, data);

    // Track count
    try {
      const today = new Date().toDateString();
      const store = await chrome.storage.sync.get(['onto_checks_today', 'onto_checks_date']);
      const count = (store.onto_checks_date === today) ? (store.onto_checks_today || 0) : 0;
      await chrome.storage.sync.set({ onto_checks_today: count + 1, onto_checks_date: today });
    } catch(e) {}

  } catch (err) {
    loading.innerHTML = '<span style="color:#dc2626">\u2715</span> ' + err.message;
    setTimeout(() => {
      if (loading.parentNode) {
        parent.replaceChild(badgeEl, loading);
      }
    }, 3000);
  }
}

function showResult(parent, loadingEl, data) {
  const risk = parseFloat(data.risk_score || 0);
  const cls = risk < 0.35 ? 'low' : risk < 0.65 ? 'medium' : 'high';
  const compLabel = data.compliance || 'N/A';

  // Engine indicator
  var engineHtml = '';
  if (data.engine && data.engine !== 'error') {
    var engineCls = data.engine === 'rust' ? 'onto-engine-rust' : 'onto-engine-fallback';
    var engineLabel = data.engine === 'rust' ? '\u26A1' : '\uD83D\uDC0D';
    engineHtml = '<span class="onto-engine ' + engineCls + '">' + engineLabel + '</span>';
  }

  // Proof indicator
  var proofHtml = '';
  if (data.proof_hash) {
    proofHtml = '<span class="onto-proof" title="Proof: ' + data.proof_hash + '">\uD83D\uDD0F</span>';
  }

  const result = document.createElement('span');
  result.className = 'onto-result ' + cls;
  result.style.position = 'relative';
  result.innerHTML = '<span class="onto-score">' + risk.toFixed(2) + '</span>' +
    '<span class="onto-layer">' + (data.layer || '') + '</span>' +
    '<span class="onto-comp">' + compLabel + '</span>' +
    engineHtml + proofHtml +
    '<span class="onto-brand">ONTO</span>';

  // Hover tooltip
  let tooltip = null;
  result.onmouseenter = () => {
    if (tooltip) return;
    tooltip = createTooltip(data);
    result.appendChild(tooltip);
  };
  result.onmouseleave = () => {
    if (tooltip) { tooltip.remove(); tooltip = null; }
  };

  parent.replaceChild(result, loadingEl);
}

function createTooltip(data) {
  const factors = data.factors || {};

  // All 7 factors — show N/A for unavailable
  const allFactors = [
    ['linguistic_uncertainty', 'Linguistic'],
    ['confidence_calibration', 'Confidence'],
    ['logprob_entropy', 'Entropy'],
    ['semantic_consistency', 'Semantic'],
    ['ground_truth_accuracy', 'Accuracy'],
    ['refusal_awareness', 'Refusal'],
    ['domain_risk', 'Domain Risk']
  ];

  const tip = document.createElement('div');
  tip.className = 'onto-tooltip';

  let html = '';

  // Factor bars
  for (var i = 0; i < allFactors.length; i++) {
    var k = allFactors[i][0], label = allFactors[i][1];
    var raw = factors[k];
    var nv = (raw != null) ? parseFloat(raw) : NaN;
    var hasVal = !isNaN(nv);
    var pct = hasVal ? Math.min(nv * 100, 100) : 0;
    var color = hasVal ? (nv < 0.3 ? '#00ff88' : nv < 0.6 ? '#d97706' : '#dc2626') : 'transparent';
    var opacity = hasVal ? '' : ' style="opacity:0.3"';
    html += '<div class="onto-factor-row"' + opacity + '>' +
      '<span class="onto-factor-label">' + label + '</span>' +
      '<div class="onto-factor-bar"><div class="onto-factor-fill" style="width:' + pct + '%;background:' + color + '"></div></div>' +
      '<span class="onto-factor-val">' + (hasVal ? nv.toFixed(2) : 'N/A') + '</span></div>';
  }

  // ONTO Core Metrics section
  if (data.u_recall != null || data.ece != null) {
    html += '<div class="onto-tip-sep"></div>';
    html += '<div class="onto-tip-section">ONTO CORE</div>';

    var ur = parseFloat(data.u_recall);
    if (!isNaN(ur)) {
      var urC = ur >= 0.75 ? '#00ff88' : ur >= 0.5 ? '#d97706' : '#dc2626';
      html += '<div class="onto-factor-row">' +
        '<span class="onto-factor-label">U-Recall</span>' +
        '<div class="onto-factor-bar"><div class="onto-factor-fill" style="width:' + Math.min(ur * 100, 100) + '%;background:' + urC + '"></div></div>' +
        '<span class="onto-factor-val">' + ur.toFixed(2) + '</span></div>';
    }

    var ec = parseFloat(data.ece);
    if (!isNaN(ec)) {
      var ecC = ec <= 0.1 ? '#00ff88' : ec <= 0.3 ? '#d97706' : '#dc2626';
      html += '<div class="onto-factor-row">' +
        '<span class="onto-factor-label">ECE</span>' +
        '<div class="onto-factor-bar"><div class="onto-factor-fill" style="width:' + Math.min(ec * 100, 100) + '%;background:' + ecC + '"></div></div>' +
        '<span class="onto-factor-val">' + ec.toFixed(2) + '</span></div>';
    }
  }

  // Sigma + Proof
  if (data.sigma_id || data.proof_hash) {
    html += '<div class="onto-tip-sep"></div>';
    if (data.sigma_id) {
      html += '<div class="onto-tip-meta"><span class="onto-tip-k">Signal</span><span class="onto-tip-v">' + data.sigma_id + '</span></div>';
    }
    if (data.proof_hash) {
      html += '<div class="onto-tip-meta"><span class="onto-tip-k">Proof</span><span class="onto-tip-v onto-tip-hash">' + data.proof_hash + '</span></div>';
    }
    if (data.onto_status) {
      var statusLabel = data.onto_status.indexOf('SANDBOX') >= 0 ? 'SANDBOX MODE' :
        (data.onto_status.indexOf('NON') >= 0 ? 'NON COMPLIANT' : 'COMPLIANT');
      var statusCls = data.onto_status.indexOf('SANDBOX') >= 0 ? 'onto-st-sandbox' :
        (data.onto_status.indexOf('NON') >= 0 ? 'onto-st-fail' : 'onto-st-pass');
      html += '<div class="onto-tip-meta"><span class="onto-tip-k">Status</span><span class="onto-tip-status ' + statusCls + '">' + statusLabel + '</span></div>';
    }
  }

  // Remaining
  if (data.remaining_today != null) {
    html += '<div class="onto-tip-sep"></div>';
    html += '<div style="color:#555;font-size:9px">' + data.remaining_today + ' checks remaining today</div>';
  }

  // Recommendations (top 2)
  var recs = data.recommendations || [];
  if (recs.length) {
    html += '<div class="onto-tip-sep"></div>';
    for (var j = 0; j < Math.min(recs.length, 2); j++) {
      var r = recs[j];
      var msg = typeof r === 'string' ? r : (r.message || '');
      html += '<div style="color:#888;font-size:9px;margin-bottom:2px">\u2022 ' + msg + '</div>';
    }
  }

  tip.innerHTML = html;
  return tip;
}

function detectDomain(text) {
  const lower = text.toLowerCase();
  const domainKeywords = {
    medical: ['diagnosis', 'symptom', 'treatment', 'patient', 'medication', 'disease', 'clinical', 'mg', 'dose', 'therapy', 'prognosis'],
    legal: ['court', 'statute', 'plaintiff', 'defendant', 'jurisdiction', 'liability', 'attorney', 'regulation', 'compliance', 'contract'],
    finance: ['stock', 'portfolio', 'dividend', 'market cap', 'revenue', 'earnings', 'invest', 'interest rate', 'inflation', 'fiscal'],
    technical: ['algorithm', 'function', 'database', 'api', 'server', 'compile', 'runtime', 'kubernetes', 'deployment', 'repository']
  };

  let maxScore = 0;
  let detected = 'general';

  for (const [domain, keywords] of Object.entries(domainKeywords)) {
    const score = keywords.filter(kw => lower.includes(kw)).length;
    if (score > maxScore) {
      maxScore = score;
      detected = domain;
    }
  }

  return maxScore >= 2 ? detected : 'general';
}

init();

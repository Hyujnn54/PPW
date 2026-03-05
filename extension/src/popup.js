/**
 * PPW Extension — popup.js
 * Drives all popup screens: vault list, detail view, generator, settings.
 * Communicates with the PPW desktop app via the local API (localhost:27227).
 */

import { Api } from './api.js';
import { renderCard, renderDetail, categoryIcon, strengthInfo } from './ui.js';
import { generatePassword, strengthScore } from './generator.js';

// ── State ─────────────────────────────────────────────────────────────────────
let accounts      = [];
let currentDetail = null;
let autofillMatch = null;
let settings      = {};
const api         = new Api();

// ── DOM refs ──────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);

const screens = {
  lock:      $('screen-lock'),
  vault:     $('screen-vault'),
  detail:    $('screen-detail'),
  generator: $('screen-generator'),
  settings:  $('screen-settings'),
};

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  settings = await loadSettings();
  api.baseUrl = settings.apiUrl || 'http://localhost:27227';

  await tryConnect();
  setupNav();
  setupGenerator();
  setupSettings();
});

// ── Connection ────────────────────────────────────────────────────────────────
async function tryConnect() {
  $('btn-retry').textContent = 'Connecting…';
  const ok = await api.ping();
  $('btn-retry').textContent = 'Try again';

  if (ok) {
    showShell();
    await loadVault();
    await checkAutofill();
  } else {
    showLock();
  }
}

$('btn-retry').addEventListener('click', tryConnect);

function showShell() {
  $('screen-lock').style.display = 'none';
  $('shell').style.display = 'block';
  $('header-actions').style.display = 'flex';
}

function showLock() {
  $('screen-lock').style.display = 'flex';
  $('shell').style.display = 'none';
  $('header-actions').style.display = 'none';
}

// ── Navigation ────────────────────────────────────────────────────────────────
function setupNav() {
  document.querySelectorAll('.nav-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.screen;
      switchScreen(target);
      document.querySelectorAll('.nav-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      if (target === 'generator') runGenerator();
    });
  });
}

function switchScreen(name) {
  Object.values(screens).forEach(s => s && s.classList.remove('active'));
  const el = $(`screen-${name}`);
  if (el) el.classList.add('active');
}

// ── Vault ─────────────────────────────────────────────────────────────────────
async function loadVault() {
  const list = $('account-list');
  list.innerHTML = '<div class="empty-state">Loading…</div>';

  const result = await api.getAccounts();
  if (!result.ok) {
    list.innerHTML = '<div class="empty-state">Could not load vault.<br>Is PPW unlocked?</div>';
    return;
  }

  accounts = result.data || [];
  renderList(accounts);
}

function renderList(items) {
  const list = $('account-list');
  if (!items.length) {
    list.innerHTML = '<div class="empty-state">No accounts found.</div>';
    return;
  }
  list.innerHTML = '';
  items.forEach(acc => {
    const card = renderCard(acc, {
      onView: () => openDetail(acc),
      onCopy: () => copyPassword(acc),
      onFill: () => fillForm(acc),
    });
    list.appendChild(card);
  });
}

$('search-input').addEventListener('input', e => {
  const q = e.target.value.toLowerCase();
  const filtered = accounts.filter(a =>
    a.title.toLowerCase().includes(q) ||
    (a.username || '').toLowerCase().includes(q) ||
    (a.url || '').toLowerCase().includes(q)
  );
  renderList(filtered);
});

// ── Detail view ───────────────────────────────────────────────────────────────
async function openDetail(acc) {
  currentDetail = acc;
  switchScreen('detail');

  // Fetch full details including password
  const result = await api.getAccountDetail(acc.account_id);
  const full = result.ok ? result.data : acc;

  const { score, label, color } = strengthInfo(full.strength_score || 0);

  $('detail-icon').textContent  = categoryIcon(full.category);
  $('detail-title').textContent = full.title;
  $('detail-badge').textContent  = label;
  $('detail-badge').className    = `badge badge-${label.toLowerCase()}`;

  $('detail-fields').innerHTML = '';
  $('detail-fields').appendChild(
    renderDetail(full, { onCopy: copyToClipboard })
  );
}

$('btn-back').addEventListener('click', () => {
  switchScreen('vault');
  // re-activate vault tab
  document.querySelector('[data-screen="vault"]').classList.add('active');
  document.querySelectorAll('.nav-tab').forEach(b => {
    b.classList.toggle('active', b.dataset.screen === 'vault');
  });
});

// ── Auto-fill ─────────────────────────────────────────────────────────────────
async function checkAutofill() {
  if (!settings.autofill) return;

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.url) return;

  try {
    const url = new URL(tab.url);
    const host = url.hostname.replace(/^www\./, '');
    autofillMatch = accounts.find(a => a.url && a.url.includes(host));

    if (autofillMatch) {
      const banner = $('autofill-banner');
      $('autofill-title').textContent = autofillMatch.title;
      banner.classList.add('show');
    }
  } catch {}
}

$('btn-autofill').addEventListener('click', () => {
  if (autofillMatch) fillForm(autofillMatch);
});

async function fillForm(acc) {
  const result = await api.getAccountDetail(acc.account_id);
  const full = result.ok ? result.data : acc;

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  chrome.tabs.sendMessage(tab.id, {
    type: 'PPW_FILL',
    username: full.username || full.email || '',
    password: full.password || '',
  });
  window.close();
}

// ── Password copy ─────────────────────────────────────────────────────────────
async function copyPassword(acc) {
  const result = await api.getAccountDetail(acc.account_id);
  if (result.ok && result.data.password) {
    await copyToClipboard(result.data.password);
    showCopied();
  }
}

async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    // Fallback
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
  }
}

function showCopied() {
  chrome.notifications?.create({
    type: 'basic',
    iconUrl: '../icons/icon48.png',
    title: 'PPW',
    message: 'Password copied to clipboard!',
  });
}

// ── Header actions ────────────────────────────────────────────────────────────
$('btn-lock').addEventListener('click', async () => {
  await api.lock();
  showLock();
});

$('btn-add').addEventListener('click', () => {
  // Open the desktop app via the local API
  api.openDesktopVault();
});

// ── Generator ─────────────────────────────────────────────────────────────────
function setupGenerator() {
  const lenSlider  = $('gen-length');
  const lenDisplay = $('gen-len-display');

  lenSlider.addEventListener('input', () => {
    lenDisplay.textContent = lenSlider.value;
    runGenerator();
  });

  ['gen-upper','gen-lower','gen-digits','gen-syms'].forEach(id => {
    $(id).addEventListener('change', runGenerator);
  });

  $('btn-regen').addEventListener('click', runGenerator);
  $('btn-copy-gen').addEventListener('click', async () => {
    const pw = $('gen-pw').textContent;
    await copyToClipboard(pw);
    flashStatus('status-gen', '✓ Copied!');
  });
}

function runGenerator() {
  const opts = {
    length:     parseInt($('gen-length').value),
    uppercase:  $('gen-upper').checked,
    lowercase:  $('gen-lower').checked,
    digits:     $('gen-digits').checked,
    symbols:    $('gen-syms').checked,
  };
  const pw    = generatePassword(opts);
  const score = strengthScore(pw);
  const { label, color } = strengthInfo(score);

  $('gen-pw').textContent              = pw;
  $('gen-strength-fill').style.width   = `${score}%`;
  $('gen-strength-fill').style.background = color;
  $('gen-strength-label').textContent  = `${label} — ${score}/100`;
  $('gen-strength-label').style.color  = color;
}

// ── Settings ──────────────────────────────────────────────────────────────────
function setupSettings() {
  // Load saved settings into inputs
  $('setting-api-url').value     = settings.apiUrl   || 'http://localhost:27227';
  $('setting-autofill').checked  = settings.autofill !== false;
  $('setting-alerts').checked    = settings.alerts   !== false;

  $('btn-save-settings').addEventListener('click', async () => {
    settings = {
      apiUrl:   $('setting-api-url').value.trim(),
      autofill: $('setting-autofill').checked,
      alerts:   $('setting-alerts').checked,
    };
    await chrome.storage.local.set({ ppw_settings: settings });
    api.baseUrl = settings.apiUrl;
    flashStatus('status-settings', '✓ Settings saved');
  });
}

async function loadSettings() {
  const result = await chrome.storage.local.get('ppw_settings');
  return result.ppw_settings || {};
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function flashStatus(id, msg, ms = 2000) {
  const el = $(id);
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), ms);
}


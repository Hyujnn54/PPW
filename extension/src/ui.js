/**
 * PPW Extension — ui.js
 * Pure DOM factory functions for reusable UI components.
 */

export const CATEGORY_ICONS = {
  'Email':         '📧',
  'Social Media':  '💬',
  'Banking':       '🏦',
  'Shopping':      '🛒',
  'Entertainment': '🎬',
  'Work':          '💼',
  'Education':     '📚',
  'Other':         '🔑',
};

export function categoryIcon(cat) {
  return CATEGORY_ICONS[cat] || '🔑';
}

export function strengthInfo(score) {
  if (score >= 80) return { score, label: 'Strong', color: '#48bb78' };
  if (score >= 50) return { score, label: 'Medium', color: '#ed8936' };
  return { score, label: 'Weak', color: '#fc8181' };
}

/**
 * Render an account card for the vault list.
 */
export function renderCard(acc, { onView, onCopy, onFill }) {
  const card = document.createElement('div');
  card.className = 'account-card';

  card.innerHTML = `
    <div class="account-icon">${categoryIcon(acc.category)}</div>
    <div class="account-info">
      <div class="title">${esc(acc.title)}</div>
      <div class="sub">${esc(acc.username || acc.email || acc.url || acc.category || '')}</div>
    </div>
    <div class="card-actions">
      <button class="btn-fill"  title="Fill on page">⌨️</button>
      <button class="btn-copy"  title="Copy password">📋</button>
      <button class="btn-view"  title="View details">👁</button>
    </div>
  `;

  card.querySelector('.btn-view').addEventListener('click', e => { e.stopPropagation(); onView(); });
  card.querySelector('.btn-copy').addEventListener('click', e => { e.stopPropagation(); onCopy(); });
  card.querySelector('.btn-fill').addEventListener('click', e => { e.stopPropagation(); onFill(); });
  card.addEventListener('click', onView);

  return card;
}

/**
 * Render detail fields for the detail screen.
 */
export function renderDetail(acc, { onCopy }) {
  const wrap = document.createElement('div');

  const fields = [
    { label: 'Username', value: acc.username, copyable: true  },
    { label: 'Email',    value: acc.email,    copyable: true  },
    { label: 'URL',      value: acc.url,      copyable: false },
    { label: 'Category', value: acc.category, copyable: false },
  ];

  fields.filter(f => f.value).forEach(f => {
    wrap.appendChild(fieldRow(f.label, f.value, f.copyable, onCopy));
  });

  // Password row — masked by default
  if (acc.password) {
    const row = document.createElement('div');
    row.className = 'field-row';
    row.innerHTML = `
      <label>Password</label>
      <div class="field-value">
        <span class="pw-masked" id="pw-val">••••••••••••</span>
        <button class="copy-btn" id="btn-toggle-pw" title="Show/hide">👁</button>
        <button class="copy-btn" id="btn-copy-pw"   title="Copy">📋</button>
      </div>
    `;
    let shown = false;
    row.querySelector('#btn-toggle-pw').addEventListener('click', () => {
      shown = !shown;
      row.querySelector('#pw-val').textContent = shown ? acc.password : '••••••••••••';
      row.querySelector('#btn-toggle-pw').textContent = shown ? '🙈' : '👁';
    });
    row.querySelector('#btn-copy-pw').addEventListener('click', () => onCopy(acc.password));
    wrap.appendChild(row);
  }

  // Strength bar
  if (typeof acc.strength_score === 'number') {
    const { label, color } = strengthInfo(acc.strength_score);
    const row = document.createElement('div');
    row.style.marginTop = '12px';
    row.innerHTML = `
      <div class="strength-bar">
        <div class="strength-fill"
             style="width:${acc.strength_score}%;background:${color}"></div>
      </div>
      <div class="strength-label" style="color:${color}">
        ${label} — ${acc.strength_score}/100
      </div>
    `;
    wrap.appendChild(row);
  }

  // Action buttons
  const actions = document.createElement('div');
  actions.style.cssText = 'display:flex;gap:8px;margin-top:16px;';
  actions.innerHTML = `
    <button class="btn btn-outline" id="btn-detail-fill">⌨️  Fill in page</button>
    <button class="btn" id="btn-detail-copy">📋  Copy password</button>
  `;
  if (acc.password) {
    actions.querySelector('#btn-detail-copy')
      .addEventListener('click', () => onCopy(acc.password));
  }
  wrap.appendChild(actions);

  return wrap;
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function fieldRow(label, value, copyable, onCopy) {
  const row = document.createElement('div');
  row.className = 'field-row';
  row.innerHTML = `
    <label>${esc(label)}</label>
    <div class="field-value">
      <span>${esc(value)}</span>
      ${copyable ? `<button class="copy-btn" title="Copy">📋</button>` : ''}
    </div>
  `;
  if (copyable) {
    row.querySelector('.copy-btn').addEventListener('click', () => onCopy(value));
  }
  return row;
}

function esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}


/**
 * PPW Extension — content.js
 * Injected into every page.
 *
 * Responsibilities:
 *  1. Detect login forms and notify the popup/background
 *  2. Listen for PPW_FILL messages and fill username + password fields
 *  3. Detect form submissions and notify background to offer save
 */

(function () {
  'use strict';

  // ── Detect login form ────────────────────────────────────────────────────
  function findLoginForm() {
    const pwFields = Array.from(document.querySelectorAll('input[type="password"]'))
      .filter(el => isVisible(el));
    if (!pwFields.length) return null;

    const pwField = pwFields[0];
    const form    = pwField.closest('form') || document.body;

    // Find the username / email field closest to the password field
    const userField = findUserField(form, pwField);

    return { form, pwField, userField };
  }

  function findUserField(form, pwField) {
    const candidates = Array.from(
      form.querySelectorAll('input[type="text"], input[type="email"], input[name*="user"], input[name*="email"], input[id*="user"], input[id*="email"]')
    ).filter(isVisible);

    // Prefer the one directly before the password field in DOM order
    const all  = Array.from(form.querySelectorAll('input')).filter(isVisible);
    const pwIdx = all.indexOf(pwField);
    for (let i = pwIdx - 1; i >= 0; i--) {
      if (candidates.includes(all[i])) return all[i];
    }
    return candidates[0] || null;
  }

  function isVisible(el) {
    return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  }

  // ── Notify popup about detected form (once) ──────────────────────────────
  let notified = false;
  function notifyFormDetected() {
    if (notified) return;
    notified = true;
    chrome.runtime.sendMessage({
      type: 'PPW_FORM_DETECTED',
      url:  window.location.href,
      host: window.location.hostname,
    }).catch(() => {});   // ignore if background is not ready
  }

  // ── Fill form ────────────────────────────────────────────────────────────
  function fillField(el, value) {
    if (!el) return;
    el.focus();
    // Native input value setter to trigger React / Vue reactive handlers
    const nativeSetter = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype, 'value'
    )?.set;
    if (nativeSetter) nativeSetter.call(el, value);
    else el.value = value;
    el.dispatchEvent(new Event('input',  { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    el.blur();
  }

  // ── Message handler ──────────────────────────────────────────────────────
  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg.type === 'PPW_FILL') {
      const login = findLoginForm();
      if (!login) {
        sendResponse({ ok: false, reason: 'No login form found' });
        return;
      }
      if (login.userField && msg.username) fillField(login.userField, msg.username);
      fillField(login.pwField, msg.password);
      sendResponse({ ok: true });
    }

    if (msg.type === 'PPW_CHECK_FORM') {
      sendResponse({ hasForm: !!findLoginForm() });
    }
  });

  // ── Save prompt on form submit ───────────────────────────────────────────
  document.addEventListener('submit', e => {
    const login = findLoginForm();
    if (!login || !login.pwField.value) return;

    chrome.runtime.sendMessage({
      type:     'PPW_OFFER_SAVE',
      url:      window.location.href,
      host:     window.location.hostname,
      username: login.userField?.value || '',
      password: login.pwField.value,
    }).catch(() => {});
  }, true);

  // ── Initial check ────────────────────────────────────────────────────────
  if (findLoginForm()) notifyFormDetected();

  // Also check after dynamic content loads
  const observer = new MutationObserver(() => {
    if (findLoginForm()) {
      notifyFormDetected();
      observer.disconnect();
    }
  });
  observer.observe(document.body, { subtree: true, childList: true });
})();


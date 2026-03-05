/**
 * PPW Extension — background.js  (service worker, MV3)
 *
 * Responsibilities:
 *  - Periodically poll the desktop app to keep the badge updated
 *  - Handle save-password offers from content.js
 *  - Update extension badge icon based on locked / unlocked state
 */

import { Api } from './api.js';

const api = new Api();

// ── Badge helpers ─────────────────────────────────────────────────────────────
function setBadge(text, color) {
  chrome.action.setBadgeText({ text });
  chrome.action.setBadgeBackgroundColor({ color });
}

function setUnlocked() { setBadge('',  '#48bb78'); }
function setLocked()   { setBadge('🔒', '#718096'); }

// ── Startup ───────────────────────────────────────────────────────────────────
chrome.runtime.onInstalled.addListener(() => {
  setLocked();
  schedulePolling();
});

chrome.runtime.onStartup.addListener(() => {
  schedulePolling();
});

// ── Polling ───────────────────────────────────────────────────────────────────
async function poll() {
  const { ppw_settings } = await chrome.storage.local.get('ppw_settings');
  api.baseUrl = ppw_settings?.apiUrl || 'http://localhost:27227';

  const ok = await api.ping();
  ok ? setUnlocked() : setLocked();
}

function schedulePolling() {
  // Poll every 30 seconds using an alarm
  chrome.alarms.create('ppw_poll', { periodInMinutes: 0.5 });
}

chrome.alarms.onAlarm.addListener(alarm => {
  if (alarm.name === 'ppw_poll') poll();
});

// Initial poll
poll();

// ── Save-password offer ───────────────────────────────────────────────────────
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'PPW_OFFER_SAVE') {
    handleSaveOffer(msg, sender);
    sendResponse({ ok: true });
  }

  if (msg.type === 'PPW_FORM_DETECTED') {
    // Update badge to show a match hint
    chrome.action.setBadgeText({ text: '★', tabId: sender.tab?.id });
    chrome.action.setBadgeBackgroundColor({ color: '#6c63ff', tabId: sender.tab?.id });
    sendResponse({ ok: true });
  }
});

async function handleSaveOffer(msg, sender) {
  // Show a notification offering to save the password
  const notifId = `ppw_save_${Date.now()}`;

  chrome.notifications.create(notifId, {
    type:    'basic',
    iconUrl: '../icons/icon48.png',
    title:   'PPW — Save this password?',
    message: `Save credentials for ${msg.host}?\nClick to open PPW.`,
    buttons: [{ title: 'Save' }, { title: 'Dismiss' }],
  });

  // Store temporarily so user can act on it
  await chrome.storage.session.set({
    ppw_pending_save: {
      url:      msg.url,
      host:     msg.host,
      username: msg.username,
      password: msg.password,
    }
  });
}

chrome.notifications.onButtonClicked.addListener(async (notifId, btnIdx) => {
  if (!notifId.startsWith('ppw_save_')) return;
  chrome.notifications.clear(notifId);

  if (btnIdx === 0) {
    // Open popup so user can confirm the save
    chrome.action.openPopup?.();
  } else {
    await chrome.storage.session.remove('ppw_pending_save');
  }
});


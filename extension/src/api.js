/**
 * PPW Extension — api.js
 * Thin HTTP client that talks to the PPW desktop local API on localhost:27227.
 * The desktop app must be running and unlocked for calls to succeed.
 */
export class Api {
  constructor(baseUrl = 'http://localhost:27227') {
    this.baseUrl = baseUrl;
  }

  async _get(path) {
    try {
      const token = await this._getToken();
      const res = await fetch(`${this.baseUrl}${path}`, {
        headers: { 'X-PPW-Token': token, 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(4000),
      });
      if (!res.ok) return { ok: false, status: res.status };
      return { ok: true, data: await res.json() };
    } catch {
      return { ok: false };
    }
  }

  async _post(path, body = {}) {
    try {
      const token = await this._getToken();
      const res = await fetch(`${this.baseUrl}${path}`, {
        method: 'POST',
        headers: { 'X-PPW-Token': token, 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(4000),
      });
      if (!res.ok) return { ok: false, status: res.status };
      return { ok: true, data: await res.json() };
    } catch {
      return { ok: false };
    }
  }

  async _getToken() {
    const result = await chrome.storage.local.get('ppw_token');
    return result.ppw_token || '';
  }

  /** Check if the desktop app is running and the vault is unlocked */
  async ping() {
    try {
      const res = await fetch(`${this.baseUrl}/api/ping`, {
        signal: AbortSignal.timeout(2000),
      });
      if (!res.ok) return false;
      const data = await res.json();
      // If there's a fresh session token, store it
      if (data.token) {
        await chrome.storage.local.set({ ppw_token: data.token });
      }
      return data.status === 'ok' && data.unlocked === true;
    } catch {
      return false;
    }
  }

  /** Fetch all accounts (metadata only — no passwords) */
  async getAccounts() {
    return this._get('/api/ext/accounts');
  }

  /** Fetch full account details including decrypted password */
  async getAccountDetail(accountId) {
    return this._get(`/api/ext/accounts/${accountId}`);
  }

  /** Lock the vault remotely */
  async lock() {
    return this._post('/api/ext/lock');
  }

  /** Tell the desktop app to bring its window to the foreground */
  async openDesktopVault() {
    return this._post('/api/ext/focus');
  }
}


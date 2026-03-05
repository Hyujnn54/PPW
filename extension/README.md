# PPW Browser Extension

Auto-fill, copy, and manage your PPW vault directly from Chrome or Firefox.

## How it works

```
Browser Extension  ←→  PPW Desktop App  ←→  MongoDB Atlas
   (popup UI)          (localhost:27227)      (your cloud DB)
```

The extension talks to a **local API server** that the desktop app runs on
`localhost:27227` while it is open and unlocked. Your passwords **never go
through any external server** — the extension only ever contacts your own machine.

---

## Publishing — is it free?

| Store | Cost | Notes |
|-------|------|-------|
| **Firefox Add-ons** | ✅ **100% free** | No fee, no waiting. Upload and publish immediately. |
| **Chrome Web Store** | ⚠️ $5 one-time | One-time developer registration fee (not per-extension, not recurring). |
| **Edge Add-ons** | ✅ **100% free** | Uses Chrome's MV3 extension unchanged — submit the same zip. |

**Recommended path:** Publish to Firefox first (free, instant), then Chrome ($5 one-time when ready).

---

## Installing during development (no store needed)

### Chrome / Edge
1. Open `chrome://extensions` (or `edge://extensions`)
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked** → select the `extension/` folder
4. The 🔐 PPW icon appears in the toolbar immediately

### Firefox
1. Open `about:debugging#/runtime/this-firefox`
2. Click **Load Temporary Add-on** → select `extension/manifest.json`
3. Reloads each time you restart Firefox (permanent via Add-ons store)

---

## Usage

| Action | How |
|--------|-----|
| View vault | Click the 🔐 toolbar icon |
| Auto-fill a login | Open popup → click ⌨️ next to the account |
| Copy a password | Click 📋 next to the account |
| Generate a password | Click the ⚡ Generator tab |
| Lock vault remotely | Click 🔒 in the popup header |

### Auto-fill
When you visit a site matching an account in your vault, PPW shows a banner
at the top of the popup: **"Match found → Fill in page"**. One click fills
the username and password fields.

### Save new passwords
When you submit a new login form, PPW shows a system notification offering
to save it. Click **Save** → desktop app opens to confirm.

---

## Security

- Extension **only connects to `127.0.0.1:27227`** — never to the internet
- Every request requires a **per-session token** generated at vault unlock
- Token rotates every time you sign in
- If the desktop app is closed or locked → extension shows the lock screen
- Passwords are decrypted on your machine only

---

## File structure

```
extension/
├── manifest.json        ← Chrome/Edge/Firefox MV3 manifest
├── popup.html           ← Extension popup UI
├── icons/               ← PNG icons (see below)
└── src/
    ├── popup.js         ← Vault list, detail, generator, settings
    ├── api.js           ← HTTP client → desktop app (localhost:27227)
    ├── ui.js            ← DOM factory functions
    ├── generator.js     ← Password generation + strength scoring
    ├── background.js    ← Service worker (badge, save-offer notifications)
    └── content.js       ← Page script (form detection + auto-fill injection)
```

---

## Adding icons

Place PNG files in `extension/icons/`:

| File | Size |
|------|------|
| `icon16.png`  | 16×16  |
| `icon32.png`  | 32×32  |
| `icon48.png`  | 48×48  |
| `icon128.png` | 128×128 |

Free tools to generate them from an emoji or SVG:
- [favicon.io](https://favicon.io/emoji-favicons/) — emoji → PNG in one click
- [realfavicongenerator.net](https://realfavicongenerator.net) — SVG → all sizes

---

## Publishing step-by-step

### Firefox (free)
1. Zip the `extension/` folder contents (not the folder itself)
2. Go to [addons.mozilla.org/developers](https://addons.mozilla.org/en-US/developers/)
3. Sign in → **Submit a New Add-on** → **Upload** the zip
4. Fill in name, description, screenshots → **Submit for Review**
5. Auto-reviewed in minutes for unlisted; ~1–3 days for listed

### Chrome Web Store ($5 one-time)
1. Go to [chrome.google.com/webstore/devconsole](https://chrome.google.com/webstore/devconsole)
2. Pay the $5 developer registration (one-time, covers all your extensions)
3. **New Item** → upload the zip
4. Fill in store listing → **Submit for Review** (~1–3 business days)

### Microsoft Edge (free)
1. Go to [partner.microsoft.com/dashboard/microsoftedge](https://partner.microsoft.com/dashboard/microsoftedge)
2. **New Extension** → upload the same zip (no changes needed)
3. Fill in listing → **Publish**

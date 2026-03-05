# PPW Browser Extension

Auto-fill, copy, and manage your PPW vault directly from Chrome or Firefox.

## How it works

```
Browser Extension  ←→  PPW Desktop App  ←→  MongoDB Atlas
   (popup UI)          (localhost:27227)      (your cloud DB)
```

The extension talks to a **local API server** that the desktop app runs on `localhost:27227` while it is open and unlocked. Your passwords **never go through any external server** — the extension only ever contacts your own machine.

## Installing (Developer Mode)

Until the extension is published to the Chrome Web Store, install it manually:

1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked**
4. Select the `extension/` folder inside your PPW project
5. The 🔐 PPW icon appears in your toolbar

### Firefox
1. Open `about:debugging#/runtime/this-firefox`
2. Click **Load Temporary Add-on**
3. Select `extension/manifest.json`

## Usage

| Action | How |
|--------|-----|
| View vault | Click the 🔐 icon |
| Auto-fill a login form | Open PPW popup → click ⌨️ next to the account |
| Copy a password | Click 📋 next to the account |
| Generate a password | Click the ⚡ Generator tab |
| Lock remotely | Click 🔒 in the popup header |

### Auto-fill
When you visit a site that has a matching account in your vault, PPW shows a banner at the top of the popup with a **Fill in page** button. Click it to fill the username and password fields automatically.

### Save new passwords
When you submit a login form on a new site, PPW shows a notification offering to save the credentials. Click **Save** to open the desktop app and confirm.

## Security

- The extension **only connects to `127.0.0.1:27227`** — never to the internet
- Every request requires a **session token** issued by the desktop app on login
- The token changes every time you unlock the vault
- If the desktop app is closed or locked, the extension shows the lock screen
- Passwords are **decrypted on your machine** — the extension receives the plaintext only for the instant it fills/copies

## File structure

```
extension/
├── manifest.json        ← Chrome MV3 manifest
├── popup.html           ← Extension popup UI
├── icons/               ← Extension icons (add icon16/32/48/128.png)
└── src/
    ├── popup.js         ← Popup logic (vault list, detail, generator, settings)
    ├── api.js           ← HTTP client for the desktop API
    ├── ui.js            ← DOM factory functions
    ├── generator.js     ← Password generation + strength scoring
    ├── background.js    ← Service worker (badge, save-offer notifications)
    └── content.js       ← Page injector (form detect, auto-fill)
```

## Publishing to Chrome Web Store

1. Zip the `extension/` folder
2. Go to [Chrome Developer Dashboard](https://chrome.google.com/webstore/devconsole)
3. Click **New Item** → upload the zip
4. Fill in store listing (description, screenshots, privacy policy)
5. Pay the one-time $5 developer fee (first time only)
6. Submit for review (~1–3 business days)

## Adding icons

Place PNG icons in `extension/icons/`:
- `icon16.png`  — 16×16
- `icon32.png`  — 32×32
- `icon48.png`  — 48×48
- `icon128.png` — 128×128

Use a simple lock or key emoji rendered to PNG, or use any icon tool.


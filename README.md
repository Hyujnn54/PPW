# PPW — Personal Password Manager 🔐

> One master password. Every password, safe and synced.

[![Version](https://img.shields.io/badge/version-1.0.0-6c63ff.svg)](https://github.com/Hyujnn54/PPW/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-3776ab.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Windows-0078d4.svg)](https://github.com/Hyujnn54/PPW/releases)
[![Database](https://img.shields.io/badge/database-MongoDB-47a248.svg)](https://mongodb.com)
[![Encryption](https://img.shields.io/badge/encryption-AES--256--GCM-brightgreen.svg)](#the-encryption-behind-it)
[![Browser Extension](https://img.shields.io/badge/browser-Chrome%20%7C%20Firefox%20%7C%20Edge-ff7f00.svg)](#browser-extension)

---

## Download

**[→ Download PPW for Windows](https://github.com/Hyujnn54/PPW/releases/latest)**

Run `PPW-Setup.exe` — installs like any normal Windows app with a Start Menu shortcut and uninstaller.

---

## What is PPW?

PPW is a password manager. Instead of reusing the same password everywhere (which is dangerous), or writing passwords on sticky notes (also dangerous), PPW stores all your passwords in one secure, encrypted place.

You only need to remember **one strong master password**. PPW handles everything else.

---

## Getting started

### 1. Install
Download and run `PPW-Setup.exe`. Click through the installer — it takes about 10 seconds.

### 2. Create your account
When the app opens, click **Create a new account** and fill in:
- **Username** — whatever name you want to use
- **Email** — for account recovery in the future
- **Master password** — this is the one password you must remember. Make it strong: at least 12 characters with a mix of uppercase, lowercase, numbers, and symbols

> ⚠️ **Write your master password down and keep it somewhere safe.** If you forget it, your vault cannot be recovered. This is by design — it means nobody else can recover it either.

### 3. Add your passwords
Click the **+** button, enter the site name, your username or email for that site, and the password. Hit **Save** — it's encrypted and stored instantly.

That's it. You're set up.

---

## Your passwords are safe — here's why

This is the most important thing to understand about PPW.

### Nobody can read your passwords — not even us

When you save a password, PPW **encrypts it on your device** before sending anything to the cloud. What gets stored is scrambled, unreadable data — not your actual password.

To unscramble it, you need your master password. Since your master password is never stored anywhere (not on your device, not in the cloud, nowhere), there is nothing to steal.

### What happens when you save a password

```
You type your password
        ↓
PPW scrambles it using your master password as the key
        ↓
Only the scrambled version is saved to the cloud
        ↓
When you need it, PPW unscrambles it on your device
```

Your master password never leaves your device. It's used as a key to lock and unlock your data — and then it's gone from memory.

### What if someone breaks into the database?

They would get a collection of scrambled data that is mathematically impossible to read without your master password. It would look something like this:

```
K7fQx2mB9pLnRtYvWcAeHjUsDzXo...  ← this is what a stolen password looks like
```

Completely useless without the key — which only you have.

### The encryption behind it

PPW uses **AES-256-GCM** — the same encryption standard used by banks, governments, and the military worldwide. Every single password is encrypted individually with its own random value, so even if one were somehow compromised, the rest of your vault stays completely safe.

Your master password is never stored — not on your device, not in the cloud, nowhere. Instead, PPW runs it through **100,000 rounds of processing** combined with a unique random value tied to your account before using it as an encryption key. This makes guessing attacks completely impractical — even with powerful computers it would take longer than the age of the universe to try all possible combinations.

When you change your master password, your saved passwords don't need to be re-encrypted — only the key that unlocks them is re-wrapped. Your data is never exposed during the process.

---

## Features

### Vault
Your password list. Search, filter by category, and manage all your saved accounts in one place.

- **View** — reveal a password when you need it
- **Copy** — copy to clipboard in one click without the password appearing on screen
- **Edit** — update saved details at any time
- **Delete** — permanently remove an entry

### Password Generator
Can't think of a strong password? Go to the **Generator** tab:
- Set the length (8 to 64 characters)
- Choose whether to include uppercase, lowercase, numbers, and symbols
- Click **Copy** — paste it wherever you need it

The generator is also built into the Add/Edit form so you can create and save in one step.

### Security Dashboard
The **Security** tab gives you an overview of your vault health:
- Which passwords are weak or too short
- Which accounts don't have two-factor authentication enabled
- Your overall security score

### Cloud Sync
Your vault is stored securely in the cloud. Log in on any Windows device with your username and master password and all your passwords are there, up to date.

### Auto-lockout
After 5 wrong master password attempts, your account locks for 30 minutes. This stops anyone from trying to guess their way in.

### Browser Extension
PPW has a browser extension for Chrome, Firefox, and Edge that lets you fill in login forms without opening the app.

> The extension only works while the PPW desktop app is open and unlocked on your computer. It never connects to the internet directly — it only talks to the app on your own machine.

---

## Frequently asked questions

**Can I use PPW on multiple computers?**
Yes. Install PPW on any Windows computer, log in with the same username and master password, and your vault is there.

**What if I forget my master password?**
Your data cannot be recovered without it. This is intentional — it means no one else can get into your vault either, even if they contact support. Write it down somewhere safe when you create your account.

**Is my data safe if PPW gets hacked?**
Yes. Everything stored is encrypted. Attackers would get scrambled data that is useless without your master password, which is never stored anywhere.

**Does PPW ever see my passwords?**
No. Encryption and decryption happen entirely on your device. The only thing stored in the cloud is the already-encrypted version.

**What does the browser extension do?**
It lets you fill in login forms from your browser without copying and pasting. It reads your vault through the PPW desktop app — nothing is sent to any website or server.

---

## License

[MIT](LICENSE) — free to use and share.

---

## Tags

`password-manager` `security` `encryption` `AES-256-GCM` `python` `windows` `mongodb` `browser-extension` `vault` `cloud-sync`

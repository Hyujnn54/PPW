# PPW — Personal Password Manager 🔐

> A secure, modern desktop password manager built with Python and MongoDB Atlas.
> AES-256-GCM encryption · Cloud sync · Zero-knowledge · Browser extension

[![Version](https://img.shields.io/badge/version-1.0.0-6c63ff.svg)](https://github.com/yourusername/PPW/releases)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MongoDB Atlas](https://img.shields.io/badge/MongoDB-Atlas-00ED64.svg)](https://www.mongodb.com/cloud/atlas)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 📥 Download

**→ [Latest Release](https://github.com/yourusername/PPW/releases/latest)**

| Platform | File |
|----------|------|
| Windows 10 / 11 | `PPW-PasswordManager.exe` |

Just download and double-click. No Python, no installer, no setup.

---

## ✨ What it does

PPW stores all your passwords encrypted in the cloud so you can access them from anywhere.
You remember **one strong master password** — PPW remembers everything else.

| | |
|---|---|
| 🔐 **AES-256-GCM encryption** | Every password encrypted individually before it leaves your device |
| 🧠 **Zero-knowledge** | Your master password is never stored anywhere — not even hashed in a way that's reversable |
| ☁️ **Cloud sync** | Powered by MongoDB Atlas — your vault is available on every device you sign in to |
| ⚡ **Password generator** | Configurable length and charset with live strength scoring |
| 🛡 **Security dashboard** | See weak passwords, old passwords, and 2FA coverage at a glance |
| 🔍 **Search and filter** | Find any account instantly by title, username, or URL |
| 📋 **One-click copy** | Copy passwords to clipboard without ever seeing them |
| 🧩 **Browser extension** | Auto-fill login forms in Chrome, Firefox, and Edge |
| 🚫 **Auto-lockout** | 5 failed login attempts locks the account for 30 minutes |

---

## 🚀 Getting started (users)

1. **[Download the latest release](https://github.com/yourusername/PPW/releases/latest)**
2. Double-click `PPW-PasswordManager.exe`
3. Click **Create a new account**
4. Choose a username and a strong master password *(12+ chars, mix of upper/lower/digits/symbols)*
5. Start adding passwords — they're instantly encrypted and saved to the cloud

> ⚠️ **Your master password cannot be recovered.** There is no "forgot password" — this is intentional. Write it down somewhere safe when you first set it up.

---

## 🔒 How your passwords are protected

```
Your master password   (only ever in your head — never stored anywhere)
         │
         ▼
PBKDF2-HMAC-SHA256  ←─── unique random salt per account (100,000 iterations)
         │
         ▼
Derived key  (exists only in RAM during your session, never written to disk)
         │
         ▼
Decrypts your Encryption Key  (stored encrypted in the cloud)
         │
         ▼
AES-256-GCM  decrypts each password individually
         │
         ▼
Plaintext password  (shown in the app / copied to clipboard)
```

**What this means:** Even if someone broke into the database and downloaded everything,
they would have a collection of encrypted blobs they can never read without your master password.
Not even the developer can read your passwords.

---

## 🌐 Browser Extension

The extension lets you auto-fill login forms directly from your browser.

| Store | Cost |
|-------|------|
| Firefox Add-ons | ✅ Free |
| Microsoft Edge Add-ons | ✅ Free |
| Chrome Web Store | ⚠️ $5 one-time developer registration |

**How it works:** The extension connects to the PPW desktop app running on your machine
via `localhost:27227`. The desktop app must be open and unlocked. Passwords are
decrypted locally — the extension never contacts any external server.

**Install during development:**
1. Chrome: `chrome://extensions` → Developer mode → Load unpacked → select `extension/`
2. Firefox: `about:debugging` → Load Temporary Add-on → select `extension/manifest.json`

---

## 🏗 Architecture

```
PPW/
├── main.py                       ← entry point
├── gui_app.py                    ← PyQt6 dark-themed desktop UI
├── config.py                     ← settings (reads from .env in dev, bundled in prod)
├── build.py                      ← builds the release EXE
│
├── controllers/                  ← business logic
│   ├── auth_controller.py        ← register, login, sessions, rate limiting
│   ├── account_controller.py     ← CRUD, password generation, strength analysis
│   └── security_controller.py   ← audit logs, weak/old password reports
│
├── services/                     ← data access
│   ├── master_password_service.py
│   └── account_service.py
│
├── db/
│   ├── database.py               ← MongoDB connection manager
│   └── schemas.py                ← indexes and collection structure
│
├── utils/
│   ├── encryption.py             ← AES-256-GCM, PBKDF2, password generator
│   ├── extension_api.py          ← local HTTP server for browser extension
│   ├── logger.py                 ← activity audit log
│   ├── security.py               ← validators, session manager, rate limiter
│   └── email_service.py          ← SMTP email (disabled by default)
│
├── extension/                    ← browser extension (Chrome/Firefox/Edge MV3)
│
└── .github/workflows/
    └── release.yml               ← auto-build EXE on git tag push
```

### GUI screens

```
Auth Screen  (login / register)
      └─ Vault Screen
           ├─ 🗄  Vault       — card list, search, filter, add/view/copy/delete
           ├─ 🛡  Security    — strength stats, weak password list
           └─ ⚡  Generator   — length slider, charset options, live strength bar
```

---

## 💻 Development setup

### Requirements
- Python 3.11+
- A free [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) account

### Steps

```bash
# 1. Clone
git clone https://github.com/yourusername/PPW.git
cd PPW

# 2. Virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# 3. Dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Open .env and fill in MONGO_URI and SECRET_KEY

# 5. Run
python main.py
```

### `.env` reference

```env
# Required
MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/?appName=PPW

# What each key does
DATABASE_NAME=password_manager        # name of the MongoDB database
SECRET_KEY=<32-byte hex string>       # signs session tokens — keep secret
```

Generate a `SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📦 Releasing a new version

### Automated (recommended)

1. Update `version.py` and add a section to `CHANGELOG.md`
2. Commit, tag, push:

```bash
git add -A
git commit -m "chore: release v1.1.0"
git tag v1.1.0
git push origin main --tags
```

GitHub Actions automatically:
- Builds `PPW-PasswordManager.exe` with your secrets baked in
- Creates a GitHub Release
- Attaches the EXE for users to download

### GitHub Secrets required (one-time setup)

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Value |
|--------|-------|
| `MONGO_URI` | Your Atlas connection string |
| `SECRET_KEY` | Output of `python -c "import secrets; print(secrets.token_hex(32))"` |

---

## 🗄 Database

PPW uses **one shared MongoDB Atlas cluster** that you own. Users never see or configure the database — they just register an account like any other app.

**Free tier (M0):** 512 MB storage — enough for tens of thousands of users.

**Atlas setup (one-time):**
1. [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas) → Try Free
2. Create cluster → **M0 Free**
3. Database Access → Add User
4. Network Access → Allow from anywhere (`0.0.0.0/0`)
5. Connect → Drivers → copy URI → paste into `.env`

---

## 📄 License

[MIT](LICENSE) — free to use, modify, and distribute.

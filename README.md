# PPW — Personal Password Manager 🔐

> A secure, modern password manager built with Python and MongoDB Atlas.
> Dark-themed desktop GUI · AES-256-GCM encryption · Zero-knowledge architecture

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MongoDB Atlas](https://img.shields.io/badge/MongoDB-Atlas-green.svg)](https://www.mongodb.com/cloud/atlas)
[![Version](https://img.shields.io/badge/version-1.0.0-purple.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## Table of Contents

1. [Features](#-features)
2. [How Users Install the App](#-how-users-install-the-app)
3. [How the Database Works for Users](#-how-the-database-works-for-users)
4. [Cloud vs Local Database — Security Analysis](#-cloud-vs-local-database--security-analysis)
5. [Architecture](#-architecture)
6. [Security](#-security)
7. [Browser Extension](#-browser-extension-roadmap)
8. [Development Setup](#-development-setup)
9. [Releasing a New Version](#-releasing-a-new-version)

---

## ✨ Features

| Feature | Details |
|---------|---------|
| 🖥 Modern dark GUI | Sidebar navigation, card-based vault, strength bars |
| 🔐 AES-256-GCM encryption | Every password encrypted individually |
| 🧠 Zero-knowledge | Your master password is **never stored** |
| ☁️ MongoDB Atlas | Cloud sync — access from any device |
| ⚡ Password generator | Configurable length, charset, live strength score |
| 🛡 Security dashboard | Weak/old password detection, 2FA tracking |
| 🔍 Smart search | Filter by title, username, category |
| 📋 One-click copy | Copy password to clipboard instantly |
| 🚪 Auto-lockout | 5 failed attempts → 30-minute lockout |
| 📜 Activity logs | Full audit trail of every action |

---

## 📦 How Users Install the App

### Option A — Download the Pre-built Executable *(recommended for end-users)*

1. Go to the [Releases page](https://github.com/yourusername/PPW/releases)
2. Download the file for your platform:
   - **Windows**: `PPW-PasswordManager.exe`
   - **macOS**: `PPW-PasswordManager.app`
   - **Linux**: `PPW-PasswordManager`
3. Double-click to run — **no Python, no setup, no database config**
4. Click **Create a new account**, enter a username + email + master password
5. Done — start saving passwords

> **Users never see a database, a URI, or any configuration screen.**
> The database connection is baked into the app by you before you build and release it.

---

### Option B — Install from Source *(developers / power users)*

```bash
# 1. Clone
git clone https://github.com/yourusername/PPW.git
cd PPW

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure (copy the template and fill in your MongoDB URI)
cp .env.example .env
# Edit .env — add MONGO_URI and SECRET_KEY

# 5. Run
python main.py               # launches GUI automatically
python main.py --cli         # CLI fallback
```

---

## 🗄 How the Database Works

### The simple version

This works **exactly like any other app** — like Gmail, Spotify, or any website you've ever signed up for:

```
You (developer)          Users
─────────────            ─────────────────────────────────────
Set up 1 MongoDB    →    Register an account in YOUR app
Atlas cluster            ↓
                         Their encrypted passwords get saved
                         in YOUR database
                         ↓
                         They log in with their username +
                         master password to access them
```

- **You** set up ONE MongoDB Atlas cluster and put the URI in your `.env`
- **Users** download the app, register, and use it — they never see or touch the database
- It works exactly like Bitwarden, 1Password, or any other password manager

### Do users need to configure anything?

**No.** Users just:
1. Download the app
2. Register with username + email + master password
3. Start saving passwords

That's it. Zero database setup on their end.

### What's stored in your database?

```
Collection: master_password
  → username, email, hashed password, encrypted encryption key, salt

Collection: accounts
  → title, username, email, URL, category — all fine in plaintext
  → password field → AES-256-GCM encrypted (only decryptable with their master password)

Collection: activity_logs
  → login history, actions, timestamps

Collection: categories
  → account organisation
```

**The critical part:** Even if someone steals your entire database,
they cannot read a single password. Every password is encrypted with a key
that is itself encrypted with the user's master password — which is **never stored**.

### Setting up YOUR database (one-time, you do this, not users)

1. Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas) → **Try Free**
2. Create a project → **Create Cluster** → choose **M0 Free Tier** (512 MB, always free)
3. **Database Access** → Add Database User → username + password
4. **Network Access** → Add IP Address → **Allow Access from Anywhere** (`0.0.0.0/0`)
5. **Connect** → **Drivers** → copy the connection string
6. Paste into your `.env` as `MONGO_URI`
7. Ship the app — users never see any of this

---

## 🔒 Security Model

### Why cloud (MongoDB Atlas) is the right choice

You host one Atlas cluster. All user data goes into it — encrypted. Even if Atlas is breached, every password in the database is AES-256-GCM encrypted and **completely unreadable** without the user's master password, which is never stored anywhere.

```
User's master password  (lives only in their head — never stored)
        ↓
PBKDF2-HMAC-SHA256  (100,000 iterations + unique salt per user)
        ↓
Derived key  (in memory only, discarded after session)
        ↓
Decrypts the user's Encryption Key  (stored encrypted in Atlas)
        ↓
AES-256-GCM decrypts each individual password
        ↓
Plaintext  (shown/copied, never written to disk)
```

### What this means in practice

| Threat | Impact |
|--------|--------|
| Your Atlas cluster is breached | Attacker gets encrypted blobs — useless without every user's master password |
| Someone clones the entire database | Same — all ciphertext, no keys |
| Your `.env` file is stolen | Attacker can connect to Atlas but still can't read any passwords |
| A user forgets their master password | Their data is permanently inaccessible — this is intentional |

### Attack surface

| Attack | Countermeasure |
|--------|---------------|
| Brute-force login | 5 attempts → 30 min lockout |
| Weak master passwords | Min 12 chars, upper+lower+digit+symbol enforced |
| Session hijacking | Cryptographically random tokens, 15-min timeout |
| Rainbow tables | Unique per-user PBKDF2 salt |
| Timing attacks | `secrets.compare_digest` for all comparisons |

---

## 🏗 Architecture

```
PPW/
├── main.py                      ← entry point (GUI by default, --cli flag)
├── gui_app.py                   ← PyQt6 dark-themed desktop application
├── config.py                    ← settings loaded from .env
├── version.py                   ← version string
├── requirements.txt
├── .env.example                 ← template — copy to .env and fill in
│
├── controllers/                 ← business logic layer
│   ├── auth_controller.py       ← register, login, sessions, rate limiting
│   ├── account_controller.py    ← CRUD, password generation, strength
│   └── security_controller.py  ← audit logs, weak/old password reports
│
├── services/                    ← data access layer
│   ├── master_password_service.py
│   └── account_service.py
│
├── db/
│   ├── database.py              ← MongoDB connection manager
│   └── schemas.py               ← collection schemas and indexes
│
└── utils/
    ├── encryption.py            ← AES-256-GCM, PBKDF2, password generator
    ├── logger.py                ← activity logging
    └── security.py              ← validators, session manager, rate limiter
```

### GUI Screens

```
App start
  └─ Setup Wizard (first run only — enter MongoDB URI)
       └─ Auth Screen (login / register)
            └─ Vault Screen
                 ├─ 🗄  Vault       — card list, search, add/view/copy/delete
                 ├─ 🛡  Security    — stats grid, weak password list
                 └─ ⚡  Generator   — configurable password generator
```

---

## 🌐 Browser Extension

The `extension/` folder contains a full Chrome/Firefox/Edge MV3 extension.

### Publishing cost

| Store | Cost |
|-------|------|
| Firefox Add-ons | ✅ Free |
| Microsoft Edge Add-ons | ✅ Free |
| Chrome Web Store | ⚠️ $5 one-time registration |

**Start with Firefox** (free, no waiting). Use the same zip for Edge (also free). Chrome requires a $5 one-time developer fee — not per extension, not recurring.

### How it connects

```
Extension popup → http://127.0.0.1:27227 → PPW desktop app (when open + unlocked)
```

The desktop app runs a local API server. The extension talks only to your own machine — never to any external server. See `extension/README.md` for full details.

---

## 💻 Development Setup

```bash
# Install all dependencies
pip install -r requirements.txt

# Run the app
python main.py

# Run CLI mode
python main.py --cli
```

### Environment variables (`.env`)

```env
# Required
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/?appName=PPW

# Optional — defaults work for development
DATABASE_NAME=password_manager
SECRET_KEY=generate_with__python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🚀 Releasing a New Version

### 1. Update the version

```python
# version.py
__version__ = "1.1.0"
```

### 2. Update the changelog

Edit `CHANGELOG.md` — add a new `## [1.1.0] - YYYY-MM-DD` section.

### 3. Commit and tag

```bash
git add -A
git commit -m "chore: release v1.1.0"
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin main --tags
```

### 4. Build the executable

```bash
pip install pyinstaller

# Windows
pyinstaller --name PPW-PasswordManager --onefile --windowed main.py

# macOS
pyinstaller --name "PPW Password Manager" --onefile --windowed main.py

# Linux
pyinstaller --name ppw-password-manager --onefile main.py
```

Output is in `dist/`.

### 5. Create the GitHub Release

- Go to **Releases → Draft a new release**
- Choose tag `v1.1.0`
- Title: `PPW v1.1.0 — <short description>`
- Body: paste from `CHANGELOG.md`
- Upload the `dist/` executables
- Publish

> Users then just download the `.exe` / `.app` / binary and run it.
> No Python, no pip, no terminal required.

---

## 📄 License

MIT — see [LICENSE](LICENSE)

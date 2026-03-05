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
3. Double-click to run — **no Python or dependencies needed**
4. On first launch the app shows a **Setup Wizard**:
   - Paste your MongoDB Atlas connection string
   - The app tests the connection, saves it to a local `.env` file, and takes you straight to the login screen
5. Create your account and start saving passwords

> **That's it.** Users never touch a terminal.

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

## 🗄 How the Database Works for Users

### Does the user need to manage a database?

**Short answer: No.** For regular users installing via the executable, they never interact with the database directly. Here is exactly what happens:

```
User downloads .exe
        ↓
First launch → Setup Wizard appears
        ↓
User pastes their MongoDB Atlas URI
(free account, takes 2 minutes to create)
        ↓
App saves URI to local .env file
        ↓
App auto-creates all collections and indexes
        ↓
User registers → passwords are encrypted and stored
        ↓
All future launches connect automatically
```

### Do users need their own MongoDB Atlas account?

**Yes — each user needs their own Atlas account.** This is intentional and is the correct architecture for a password manager:

- Every user's data lives in **their own private database cluster**
- You (the developer) have **zero access** to any user's data
- If your servers are breached, **no user passwords are exposed**
- Users control their own data and can delete it at any time

### Setting up MongoDB Atlas (2 minutes, free)

Tell users to follow these steps:

1. Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas) → **Try Free**
2. Create a project → **Create a Cluster** → choose **M0 Free Tier** (512 MB, always free)
3. **Database Access** → Add Database User → set username + password
4. **Network Access** → Add IP Address → click **Allow Access from Anywhere** (`0.0.0.0/0`)
5. **Clusters** → click **Connect** → **Drivers** → copy the connection string
6. Replace `<password>` in the string with the password from step 3
7. Paste into the PPW Setup Wizard

### What gets stored in the database?

```
Collections created automatically by PPW:
┌─────────────────────────────────────────────────────────────┐
│  master_password   — hashed master password + encrypted key │
│  accounts          — all stored passwords (AES-256 encrypted)│
│  activity_logs     — login history, actions, timestamps     │
│  categories        — account organization                   │
└─────────────────────────────────────────────────────────────┘
```

**Critically — what is NOT stored:**
- ❌ Your master password in plaintext
- ❌ Your encryption key in plaintext
- ❌ Any password in plaintext
- ❌ Any data that can be read without knowing your master password

---

## 🔒 Cloud vs Local Database — Security Analysis

> **TL;DR: Cloud (MongoDB Atlas) is the right choice for a password manager.** Here's the full analysis.

### Cloud Database (MongoDB Atlas) ✅ Recommended

| Aspect | Detail |
|--------|--------|
| **Accessibility** | Access passwords from any device, anywhere |
| **Backup** | Atlas handles automated backups — no data loss |
| **Availability** | 99.9%+ uptime SLA |
| **Breach impact** | Even if Atlas is breached, all data is AES-256 encrypted. Attacker gets ciphertext only |
| **Your control** | Each user owns their cluster — you can't read their data |
| **Cost** | M0 free tier is genuinely free forever |
| **Browser extension** | Cloud is required for the browser extension to sync |
| **Multi-device** | Phone, laptop, desktop all in sync |

### Local Database (self-hosted MongoDB) ⚠️ Advanced users only

| Aspect | Detail |
|--------|--------|
| **Accessibility** | Only on the machine it's installed on |
| **Backup** | User is responsible — if disk dies, data is gone |
| **Availability** | Depends on the user's machine being on |
| **Breach impact** | If the machine is compromised, encrypted data could be extracted |
| **Browser extension** | Would need a local API server running — complex setup |
| **Multi-device** | Not possible without extra infrastructure |

### What actually protects users regardless of where the DB lives

The real security model is **encryption at the application layer**, not database-level security:

```
Master Password (user's brain — never stored anywhere)
        ↓
PBKDF2-HMAC-SHA256  (100,000 iterations + unique salt)
        ↓
Derived Key  (used only in memory, discarded after session)
        ↓
Decrypts the Encryption Key  (stored encrypted in DB)
        ↓
AES-256-GCM  encrypts/decrypts each individual password
```

This means:
- **Even if MongoDB Atlas is fully compromised** → attacker sees only random bytes
- **Even if someone steals your `.env` file** → they can connect to Atlas but still can't read passwords without your master password
- **Even if someone clones your entire database** → all they have is encrypted data

### Verdict

Use **MongoDB Atlas** (cloud). It gives users:
- Free storage
- Automatic backups
- Multi-device access
- Required for the browser extension

The encryption guarantees mean cloud storage is just as safe as local — and far more practical.

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

## 🔐 Security

### Encryption model

```
User types master password
        │
        ▼
PBKDF2-HMAC-SHA256
iterations = 100,000
salt       = random 32 bytes (unique per user, stored in DB)
        │
        ▼
Master Key  ──────────────────────────────────────────────┐
(never stored)                                            │
                                          AES-256-GCM     │
                                   Encryption Key ◄───────┘
                                   (stored encrypted)
                                          │
                                          ▼
                               AES-256-GCM per password
                               (nonce random each time)
                                          │
                                          ▼
                               Ciphertext stored in Atlas
```

### Attack resistance

| Attack | Countermeasure |
|--------|---------------|
| Brute-force login | 5 attempts → 30 min lockout + rate limiting |
| Stolen database | All data AES-256 encrypted, useless without master password |
| Weak master passwords | Validator: min 12 chars, upper+lower+digit+symbol required |
| Session hijacking | Cryptographically random tokens, 15-min timeout |
| Rainbow tables | Unique per-user PBKDF2 salt |
| Timing attacks | `secrets.compare_digest` for all token comparisons |
| Injection | MongoDB (no SQL), all inputs sanitized |

---

## 🌐 Browser Extension Roadmap

The extension will communicate with PPW using a **local REST API** that the desktop app exposes while it's running.

### Architecture

```
Browser Extension (Chrome / Firefox)
        │
        │  HTTP  localhost:27227
        ▼
PPW Desktop App  ──►  MongoDB Atlas
(local API server)         (encrypted data)
```

### What the extension will do

- **Auto-fill** — detect login forms, suggest matching accounts
- **Auto-save** — prompt to save new passwords as you type them
- **Generator** — generate passwords directly in the browser
- **Quick copy** — copy username/password with one click from the popup

### Security for the extension

- Communication is **localhost only** — not exposed to the internet
- Requests require a **session token** issued by the desktop app
- The browser extension **never stores passwords** — it always fetches from the app
- App must be running and unlocked for the extension to work

### Why cloud DB is required for the extension

The extension works via the desktop app's local API. If the desktop app is closed, the extension needs to fall back to a **direct Atlas connection** to still serve passwords. This requires the database to be reachable from the browser — which means cloud.

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

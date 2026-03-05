# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) · [Semantic Versioning](https://semver.org/)

---

## [Unreleased]

---

## [1.0.0] — 2026-03-05

### 🎉 Initial release

#### Features
- **Dark-themed desktop GUI** built with PyQt6
  - Login + Register screens (confirm password, required email)
  - Vault screen with card list, search, category filter, add/view/copy/delete
  - Security dashboard: strength stats grid, weak password list
  - Password generator with length slider and live strength bar
- **AES-256-GCM encryption** — every password encrypted individually before saving
- **Zero-knowledge architecture** — master password never stored, not even hashed reversibly
- **PBKDF2-HMAC-SHA256** key derivation (100,000 iterations, unique salt per user)
- **MongoDB Atlas** cloud storage — one cluster, all users, fully encrypted at rest
- **Browser extension** (Chrome / Firefox / Edge MV3)
  - Vault popup, auto-fill, password generator, save-offer
  - Connects to desktop app via `localhost:27227` — never to any external server
- **Automated release pipeline** via GitHub Actions
  - Push a tag → builds `PPW-PasswordManager.exe` → creates GitHub Release automatically
  - Secrets (MONGO_URI, SECRET_KEY) baked into EXE at build time, never committed

#### Security hardening
- 5 failed login attempts → 30-minute account lockout
- Session tokens are cryptographically signed and expire after 15 minutes
- Extension API token rotated on every vault unlock
- `secrets.compare_digest` used for all token comparisons (timing-attack resistant)
- Input sanitization on all user-supplied fields

#### Fixed (during development)
- `char.iscntrl()` AttributeError — Python str has no such method, fixed to `ord(char) < 32`
- `create_account()` silently failed — missing `two_factor_enabled` param caused TypeError swallowed by except block
- MongoDB `OperationFailure` (bad auth) was unhandled — now caught and shown as a friendly GUI error
- Extension manifest referenced missing icon files — removed, Chrome uses default icon
- `datetime.utcnow()` deprecated warnings — replaced with `datetime.now(timezone.utc)` throughout

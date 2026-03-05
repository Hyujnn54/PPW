"""
Configuration — PPW Password Manager.

Secret injection strategy
──────────────────────────
Development  : secrets live in .env (never committed)
Production   : PyInstaller bakes a _bundled_config.py into the frozen exe.
               build.py writes that file from GitHub Actions secrets before
               running PyInstaller, then deletes it after.
"""
import os
import sys
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# ── Try bundled config first (production build) ───────────────────────────────
_bundled_mongo_uri = ""
_bundled_db_name   = ""

if getattr(sys, 'frozen', False):
    # Running inside a PyInstaller bundle
    try:
        import _bundled_config as _bc          # noqa: F401
        _bundled_mongo_uri  = getattr(_bc, 'MONGO_URI',    "")
        _bundled_db_name    = getattr(_bc, 'DATABASE_NAME',"")
    except ImportError:
        pass
else:
    # Running from source — try a local _bundled_config.py too (CI convenience)
    try:
        import _bundled_config as _bc          # noqa: F401
        _bundled_mongo_uri  = getattr(_bc, 'MONGO_URI',    "")
        _bundled_db_name    = getattr(_bc, 'DATABASE_NAME',"")
    except ImportError:
        pass

# ── Application ───────────────────────────────────────────────────────────────
APP_NAME = "PPW — Personal Password Manager"
VERSION  = "1.0.0"

# ── MongoDB Atlas ─────────────────────────────────────────────────────────────
MONGO_URI     = _bundled_mongo_uri or os.getenv("MONGO_URI",     "")
DATABASE_NAME = _bundled_db_name   or os.getenv("DATABASE_NAME", "password_manager")

# Collections
COLLECTION_MASTER     = "master_password"
COLLECTION_ACCOUNTS   = "accounts"
COLLECTION_LOGS       = "activity_logs"
COLLECTION_CATEGORIES = "categories"

# ── Security ──────────────────────────────────────────────────────────────────
PASSWORD_MIN_LENGTH        = 8
MASTER_PASSWORD_MIN_LENGTH = 12
SESSION_TIMEOUT            = timedelta(minutes=15)
MAX_LOGIN_ATTEMPTS         = 5
LOCKOUT_DURATION           = timedelta(minutes=30)
PBKDF2_ITERATIONS          = 100_000
ENCRYPTION_ALGORITHM       = "AES-256-GCM"

# ── Developer guard ────────────────────────────────────────────────────────────
import logging as _logging
if not MONGO_URI:
    _logging.warning(
        "\n  MONGO_URI is not set!\n"
        "  Copy .env.example to .env and add your MongoDB Atlas URI.\n"
    )

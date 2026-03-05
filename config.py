"""
Configuration file for the Password Manager
"""
import os
import secrets
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# ── Application ───────────────────────────────────────────────────────────────
APP_NAME    = "Personal Password Manager"
VERSION     = "1.0.0"

# ── MongoDB Atlas ─────────────────────────────────────────────────────────────
MONGO_URI      = os.getenv("MONGO_URI", "")
DATABASE_NAME  = os.getenv("DATABASE_NAME", "password_manager")

# Collections
COLLECTION_MASTER     = "master_password"
COLLECTION_ACCOUNTS   = "accounts"
COLLECTION_LOGS       = "activity_logs"
COLLECTION_CATEGORIES = "categories"

# ── Security ──────────────────────────────────────────────────────────────────
SECRET_KEY               = os.getenv("SECRET_KEY", secrets.token_hex(32))
PASSWORD_MIN_LENGTH      = 8
MASTER_PASSWORD_MIN_LENGTH = 12
SESSION_TIMEOUT          = timedelta(minutes=15)
MAX_LOGIN_ATTEMPTS       = 5
LOCKOUT_DURATION         = timedelta(minutes=30)
PBKDF2_ITERATIONS        = 100_000
ENCRYPTION_ALGORITHM     = "AES-256-GCM"


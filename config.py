"""
PPW Configuration.

In the frozen EXE: pyi_rth_ppw.py (runtime hook) sets MONGO_URI as an env
var before this file loads, so os.getenv finds it automatically.
In development: loaded from .env via python-dotenv.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()   # no-op in frozen EXE (no .env file), works fine in dev

APP_NAME = "PPW"
VERSION  = "1.0.0"

MONGO_URI     = os.getenv("MONGO_URI", "")
DATABASE_NAME = os.getenv("DATABASE_NAME", "password_manager")

COLLECTION_MASTER     = "master_password"
COLLECTION_ACCOUNTS   = "accounts"
COLLECTION_LOGS       = "activity_logs"
COLLECTION_CATEGORIES = "categories"

PASSWORD_MIN_LENGTH        = 8
MASTER_PASSWORD_MIN_LENGTH = 12
SESSION_TIMEOUT            = timedelta(minutes=15)
MAX_LOGIN_ATTEMPTS         = 5
LOCKOUT_DURATION           = timedelta(minutes=30)
PBKDF2_ITERATIONS          = 100_000
ENCRYPTION_ALGORITHM       = "AES-256-GCM"

if not MONGO_URI:
    import logging
    logging.warning("MONGO_URI is not set. Copy .env.example to .env and add your MongoDB Atlas URI.")


"""
PPW Configuration.

When running as a built EXE: imports config_frozen (baked in by build.py).
When running from source:    reads from .env file.
"""
import os
from datetime import timedelta

# In the frozen EXE, config_frozen is bundled with the URI already set.
# In development, this import fails and we fall back to .env below.
try:
    import config_frozen as _f
    MONGO_URI                  = _f.MONGO_URI
    DATABASE_NAME              = _f.DATABASE_NAME
    APP_NAME                   = _f.APP_NAME
    VERSION                    = _f.VERSION
    COLLECTION_MASTER          = _f.COLLECTION_MASTER
    COLLECTION_ACCOUNTS        = _f.COLLECTION_ACCOUNTS
    COLLECTION_LOGS            = _f.COLLECTION_LOGS
    COLLECTION_CATEGORIES      = _f.COLLECTION_CATEGORIES
    PASSWORD_MIN_LENGTH        = _f.PASSWORD_MIN_LENGTH
    MASTER_PASSWORD_MIN_LENGTH = _f.MASTER_PASSWORD_MIN_LENGTH
    SESSION_TIMEOUT            = _f.SESSION_TIMEOUT
    MAX_LOGIN_ATTEMPTS         = _f.MAX_LOGIN_ATTEMPTS
    LOCKOUT_DURATION           = _f.LOCKOUT_DURATION
    PBKDF2_ITERATIONS          = _f.PBKDF2_ITERATIONS
    ENCRYPTION_ALGORITHM       = _f.ENCRYPTION_ALGORITHM

except ImportError:
    # Running from source -- load from .env
    from dotenv import load_dotenv
    load_dotenv()

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
        logging.warning(
            "MONGO_URI is not set. Copy .env.example to .env and add your MongoDB Atlas URI."
        )



"""
Encryption utilities for PPW Password Manager.

Algorithm stack
───────────────
Master password hashing:
  PBKDF2-HMAC-SHA256  (100 000 iterations, 32-byte random salt per user)
  → produces a 32-byte derived key

Password / data encryption:
  AES-256-GCM  (256-bit key, 96-bit random nonce per encrypt call)
  → authenticated encryption — detects any tampering
  → stored as  base64( nonce || ciphertext || tag )

Encryption key wrapping:
  The user's per-account encryption key is itself encrypted with the
  PBKDF2-derived key using AES-256-GCM, so changing the master password
  only requires re-wrapping that one key, not re-encrypting every password.
"""

import os
import base64
import secrets
import string
from typing import Tuple

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from config import PBKDF2_ITERATIONS

# AES-256-GCM constants
_NONCE_LEN = 12   # 96-bit nonce  (GCM standard)
_KEY_LEN   = 32   # 256-bit key


class EncryptionManager:
    """AES-256-GCM encryption with PBKDF2-HMAC-SHA256 key derivation."""

    @staticmethod
    def generate_salt() -> str:
        """Return a URL-safe base64-encoded 32-byte random salt."""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()

    @staticmethod
    def generate_key() -> str:
        """Return a URL-safe base64-encoded 32-byte random encryption key."""
        return base64.urlsafe_b64encode(os.urandom(_KEY_LEN)).decode()

    @staticmethod
    def derive_key_from_password(password: str, salt: str) -> bytes:
        """
        PBKDF2-HMAC-SHA256 → 32-byte key.
        salt must be a base64-encoded string (from generate_salt).
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=_KEY_LEN,
            salt=salt.encode(),
            iterations=PBKDF2_ITERATIONS,
        )
        return kdf.derive(password.encode())

    @staticmethod
    def hash_master_password(password: str, salt: str) -> str:
        """Return base64 of the PBKDF2-derived key (used as the stored verifier)."""
        key = EncryptionManager.derive_key_from_password(password, salt)
        return base64.b64encode(key).decode()

    @staticmethod
    def verify_master_password(password: str, salt: str, stored_hash: str) -> bool:
        computed = EncryptionManager.hash_master_password(password, salt)
        return secrets.compare_digest(computed, stored_hash)

    # ── AES-256-GCM helpers ───────────────────────────────────────────────────

    @staticmethod
    def _raw_encrypt(plaintext: bytes, key_bytes: bytes) -> str:
        """
        Encrypt *plaintext* with *key_bytes* (32 bytes) using AES-256-GCM.
        Returns base64( nonce[12] || ciphertext || tag[16] ).
        """
        nonce = os.urandom(_NONCE_LEN)
        aesgcm = AESGCM(key_bytes)
        ct_and_tag = aesgcm.encrypt(nonce, plaintext, None)   # includes 16-byte tag
        return base64.urlsafe_b64encode(nonce + ct_and_tag).decode()

    @staticmethod
    def _raw_decrypt(token: str, key_bytes: bytes) -> bytes:
        """
        Decrypt a token produced by _raw_encrypt.
        Raises ValueError if authentication fails (tampered data).
        """
        raw   = base64.urlsafe_b64decode(token.encode())
        nonce = raw[:_NONCE_LEN]
        ct    = raw[_NONCE_LEN:]
        return AESGCM(key_bytes).decrypt(nonce, ct, None)

    # ── Public API (string in / string out) ───────────────────────────────────

    @staticmethod
    def encrypt_data(data: str, encryption_key: str) -> str:
        """
        Encrypt a UTF-8 string with AES-256-GCM.
        encryption_key must be a base64-encoded 32-byte key (from generate_key).
        """
        key_bytes = base64.urlsafe_b64decode(encryption_key.encode())
        return EncryptionManager._raw_encrypt(data.encode(), key_bytes)

    @staticmethod
    def decrypt_data(token: str, encryption_key: str) -> str:
        """Decrypt a token produced by encrypt_data. Returns the original string."""
        key_bytes = base64.urlsafe_b64decode(encryption_key.encode())
        return EncryptionManager._raw_decrypt(token, key_bytes).decode()

    @staticmethod
    def encrypt_encryption_key(encryption_key: str, master_password: str, salt: str) -> str:
        """
        Wrap the per-user encryption key with the PBKDF2-derived master key.
        Allows changing master password without re-encrypting every password.
        """
        derived = EncryptionManager.derive_key_from_password(master_password, salt)
        return EncryptionManager._raw_encrypt(encryption_key.encode(), derived)

    @staticmethod
    def decrypt_encryption_key(encrypted_key: str, master_password: str, salt: str) -> str:
        """Unwrap the per-user encryption key."""
        derived = EncryptionManager.derive_key_from_password(master_password, salt)
        return EncryptionManager._raw_decrypt(encrypted_key, derived).decode()


# ── Password Generator ────────────────────────────────────────────────────────

class PasswordGenerator:
    """Generate cryptographically secure random passwords."""

    @staticmethod
    def generate_password(
        length: int = 20,
        use_uppercase: bool = True,
        use_lowercase: bool = True,
        use_digits: bool = True,
        use_symbols: bool = True,
    ) -> str:
        if length < 4:
            length = 4

        charset = ""
        required = []
        if use_lowercase:
            charset += string.ascii_lowercase
            required.append(secrets.choice(string.ascii_lowercase))
        if use_uppercase:
            charset += string.ascii_uppercase
            required.append(secrets.choice(string.ascii_uppercase))
        if use_digits:
            charset += string.digits
            required.append(secrets.choice(string.digits))
        if use_symbols:
            sym = "!@#$%^&*()-_=+[]{}|;:,.<>?"
            charset += sym
            required.append(secrets.choice(sym))

        if not charset:
            charset = string.ascii_letters + string.digits

        rest = [secrets.choice(charset) for _ in range(length - len(required))]
        combined = required + rest
        secrets.SystemRandom().shuffle(combined)
        return "".join(combined)

    @staticmethod
    def calculate_strength(password: str) -> Tuple[int, str]:
        """Score 0-100 + feedback string."""
        if not password:
            return 0, "No password"

        score    = 0
        feedback = []
        n        = len(password)

        has_lower  = any(c.islower()  for c in password)
        has_upper  = any(c.isupper()  for c in password)
        has_digit  = any(c.isdigit()  for c in password)
        has_symbol = any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password)

        # Length  (0-40 pts)
        score += 40 if n >= 16 else 30 if n >= 12 else 20 if n >= 8 else 10
        if n < 12:
            feedback.append("Use at least 12 characters")

        # Complexity  (0-40 pts)
        score += sum([has_lower, has_upper, has_digit, has_symbol]) * 10
        if not has_upper:  feedback.append("Add uppercase letters")
        if not has_lower:  feedback.append("Add lowercase letters")
        if not has_digit:  feedback.append("Add numbers")
        if not has_symbol: feedback.append("Add special characters")

        # Uniqueness  (0-20 pts)
        ratio = len(set(password)) / n
        score += int(ratio * 20)
        if ratio < 0.5:
            feedback.append("Too many repeated characters")

        score = min(100, score)

        if score >= 80:   label = "Very Strong"
        elif score >= 60: label = "Strong"
        elif score >= 40: label = "Medium"
        elif score >= 20: label = "Weak"
        else:             label = "Very Weak"

        fb_str = f"{label}: {', '.join(feedback)}" if feedback else label
        return score, fb_str

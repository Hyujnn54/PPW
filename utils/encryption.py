"""
Encryption and Security utilities for password management
Uses Fernet (symmetric encryption) for password storage
"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import secrets
import hashlib
import string
from typing import Tuple
from config import PBKDF2_ITERATIONS


class EncryptionManager:
    """
    Handles all encryption/decryption operations
    """

    @staticmethod
    def generate_salt() -> str:
        """Generate a random salt for hashing"""
        return base64.b64encode(secrets.token_bytes(32)).decode('utf-8')

    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key"""
        return Fernet.generate_key().decode('utf-8')

    @staticmethod
    def derive_key_from_password(password: str, salt: str) -> bytes:
        """
        Derive an encryption key from master password using PBKDF2
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode('utf-8'),
            iterations=PBKDF2_ITERATIONS,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
        return key

    @staticmethod
    def hash_master_password(password: str, salt: str) -> str:
        """
        Hash the master password with salt using PBKDF2
        Returns base64 encoded hash
        """
        key = EncryptionManager.derive_key_from_password(password, salt)
        return base64.b64encode(key).decode('utf-8')

    @staticmethod
    def verify_master_password(password: str, salt: str, stored_hash: str) -> bool:
        """
        Verify master password against stored hash
        """
        computed_hash = EncryptionManager.hash_master_password(password, salt)
        return secrets.compare_digest(computed_hash, stored_hash)

    @staticmethod
    def encrypt_data(data: str, encryption_key: str) -> str:
        """
        Encrypt data using Fernet symmetric encryption
        """
        fernet = Fernet(encryption_key.encode('utf-8'))
        encrypted_data = fernet.encrypt(data.encode('utf-8'))
        return encrypted_data.decode('utf-8')

    @staticmethod
    def decrypt_data(encrypted_data: str, encryption_key: str) -> str:
        """
        Decrypt data using Fernet symmetric encryption
        """
        fernet = Fernet(encryption_key.encode('utf-8'))
        decrypted_data = fernet.decrypt(encrypted_data.encode('utf-8'))
        return decrypted_data.decode('utf-8')

    @staticmethod
    def encrypt_encryption_key(encryption_key: str, master_password: str, salt: str) -> str:
        """
        Encrypt the main encryption key using a key derived from master password
        This allows changing master password without re-encrypting all passwords
        """
        derived_key = EncryptionManager.derive_key_from_password(master_password, salt)
        fernet = Fernet(derived_key)
        encrypted_key = fernet.encrypt(encryption_key.encode('utf-8'))
        return encrypted_key.decode('utf-8')

    @staticmethod
    def decrypt_encryption_key(encrypted_key: str, master_password: str, salt: str) -> str:
        """
        Decrypt the main encryption key using master password
        """
        derived_key = EncryptionManager.derive_key_from_password(master_password, salt)
        fernet = Fernet(derived_key)
        decrypted_key = fernet.decrypt(encrypted_key.encode('utf-8'))
        return decrypted_key.decode('utf-8')


class PasswordGenerator:
    """
    Generate secure random passwords
    """

    @staticmethod
    def generate_password(
        length: int = 16,
        use_uppercase: bool = True,
        use_lowercase: bool = True,
        use_digits: bool = True,
        use_symbols: bool = True
    ) -> str:
        """
        Generate a secure random password
        """
        if length < 4:
            length = 4

        characters = ""
        if use_lowercase:
            characters += string.ascii_lowercase
        if use_uppercase:
            characters += string.ascii_uppercase
        if use_digits:
            characters += string.digits
        if use_symbols:
            characters += "!@#$%^&*()-_=+[]{}|;:,.<>?"

        if not characters:
            characters = string.ascii_letters + string.digits

        # Ensure at least one character from each selected type
        password = []
        if use_lowercase:
            password.append(secrets.choice(string.ascii_lowercase))
        if use_uppercase:
            password.append(secrets.choice(string.ascii_uppercase))
        if use_digits:
            password.append(secrets.choice(string.digits))
        if use_symbols:
            password.append(secrets.choice("!@#$%^&*()-_=+[]{}|;:,.<>?"))

        # Fill the rest randomly
        remaining_length = length - len(password)
        password.extend(secrets.choice(characters) for _ in range(remaining_length))

        # Shuffle to avoid predictable patterns
        secrets.SystemRandom().shuffle(password)

        return ''.join(password)

    @staticmethod
    def calculate_strength(password: str) -> Tuple[int, str]:
        """
        Calculate password strength score (0-100) and feedback
        """
        score = 0
        feedback = []

        length = len(password)
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password)

        # Length score (0-40 points)
        if length >= 16:
            score += 40
        elif length >= 12:
            score += 30
        elif length >= 8:
            score += 20
        else:
            score += 10
            feedback.append("Password should be at least 12 characters")

        # Complexity score (0-40 points)
        complexity = sum([has_lower, has_upper, has_digit, has_symbol])
        score += complexity * 10

        if not has_upper:
            feedback.append("Add uppercase letters")
        if not has_lower:
            feedback.append("Add lowercase letters")
        if not has_digit:
            feedback.append("Add numbers")
        if not has_symbol:
            feedback.append("Add special characters")

        # Uniqueness score (0-20 points)
        unique_chars = len(set(password))
        uniqueness_ratio = unique_chars / length if length > 0 else 0
        score += int(uniqueness_ratio * 20)

        if uniqueness_ratio < 0.5:
            feedback.append("Too many repeated characters")

        # Determine strength label
        if score >= 80:
            strength = "Very Strong"
        elif score >= 60:
            strength = "Strong"
        elif score >= 40:
            strength = "Medium"
        elif score >= 20:
            strength = "Weak"
        else:
            strength = "Very Weak"

        feedback_str = f"{strength}: {', '.join(feedback)}" if feedback else strength

        return min(score, 100), feedback_str


if __name__ == "__main__":
    # Test encryption functionality
    print("Testing Encryption Manager...")

    # Test password hashing
    master_password = "MySecureMasterPassword123!"
    salt = EncryptionManager.generate_salt()
    password_hash = EncryptionManager.hash_master_password(master_password, salt)

    print(f"Salt: {salt}")
    print(f"Hash: {password_hash}")
    print(f"Verification: {EncryptionManager.verify_master_password(master_password, salt, password_hash)}")

    # Test encryption/decryption
    encryption_key = EncryptionManager.generate_key()
    test_data = "MySecretPassword123"
    encrypted = EncryptionManager.encrypt_data(test_data, encryption_key)
    decrypted = EncryptionManager.decrypt_data(encrypted, encryption_key)

    print(f"\nOriginal: {test_data}")
    print(f"Encrypted: {encrypted}")
    print(f"Decrypted: {decrypted}")

    # Test password generation
    print("\n\nTesting Password Generator...")
    generated_pwd = PasswordGenerator.generate_password(16)
    score, feedback = PasswordGenerator.calculate_strength(generated_pwd)

    print(f"Generated Password: {generated_pwd}")
    print(f"Strength Score: {score}/100")
    print(f"Feedback: {feedback}")


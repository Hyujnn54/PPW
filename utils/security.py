"""
Enhanced security utilities and validators
"""
import re
import secrets
import string
from typing import Tuple, Optional
from datetime import datetime, timedelta
import hashlib


class SecurityValidator:
    """Enhanced security validation"""

    @staticmethod
    def validate_master_password(password: str) -> Tuple[bool, str]:
        """
        Validate master password meets security requirements
        Returns: (is_valid, error_message)
        """
        if len(password) < 12:
            return False, "Master password must be at least 12 characters"

        if len(password) > 128:
            return False, "Master password too long (max 128 characters)"

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password)

        if not (has_upper and has_lower and has_digit and has_special):
            return False, "Master password must contain uppercase, lowercase, digit, and special character"

        # Check for common weak patterns
        common_patterns = ['password', '123456', 'qwerty', 'admin', 'letmein']
        password_lower = password.lower()
        if any(pattern in password_lower for pattern in common_patterns):
            return False, "Password contains common weak patterns"

        # Check for sequential characters
        for i in range(len(password) - 2):
            if password[i:i+3] in string.ascii_lowercase or \
               password[i:i+3] in string.digits:
                return False, "Password contains sequential characters"

        return True, "Password is strong"

    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """Validate username format"""
        if not username:
            return False, "Username cannot be empty"

        if len(username) < 3:
            return False, "Username must be at least 3 characters"

        if len(username) > 30:
            return False, "Username too long (max 30 characters)"

        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "Username can only contain letters, numbers, underscore, and hyphen"

        return True, "Username is valid"

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email format"""
        if not email:
            return True, "Email is optional"

        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"

        return True, "Email is valid"

    @staticmethod
    def validate_url(url: str) -> Tuple[bool, str]:
        """Validate URL format"""
        if not url:
            return True, "URL is optional"

        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(pattern, url, re.IGNORECASE):
            return False, "Invalid URL format"

        return True, "URL is valid"

    @staticmethod
    def sanitize_input(text: str, max_length: int = 500) -> str:
        """Sanitize user input to prevent injection attacks"""
        if not text:
            return ""

        # Remove null bytes
        text = text.replace('\x00', '')

        # Trim to max length
        text = text[:max_length]

        # Remove control characters except newline and tab
        text = ''.join(char for char in text if char == '\n' or char == '\t' or not char.iscntrl())

        return text.strip()


class SessionManager:
    """Secure session management"""

    _sessions = {}  # In production, use Redis or database

    @staticmethod
    def create_session(user_id: str, timeout_minutes: int = 15) -> str:
        """Create a new secure session"""
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)

        SessionManager._sessions[session_token] = {
            'user_id': user_id,
            'expires_at': expires_at,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow()
        }

        return session_token

    @staticmethod
    def validate_session(session_token: str) -> Optional[str]:
        """Validate session and return user_id if valid"""
        if not session_token or session_token not in SessionManager._sessions:
            return None

        session = SessionManager._sessions[session_token]

        # Check expiration
        if datetime.utcnow() > session['expires_at']:
            SessionManager.destroy_session(session_token)
            return None

        # Update last activity
        session['last_activity'] = datetime.utcnow()

        return session['user_id']

    @staticmethod
    def extend_session(session_token: str, timeout_minutes: int = 15):
        """Extend session timeout"""
        if session_token in SessionManager._sessions:
            SessionManager._sessions[session_token]['expires_at'] = \
                datetime.utcnow() + timedelta(minutes=timeout_minutes)

    @staticmethod
    def destroy_session(session_token: str):
        """Destroy a session"""
        if session_token in SessionManager._sessions:
            del SessionManager._sessions[session_token]

    @staticmethod
    def cleanup_expired_sessions():
        """Remove expired sessions"""
        now = datetime.utcnow()
        expired = [token for token, session in SessionManager._sessions.items()
                  if now > session['expires_at']]

        for token in expired:
            del SessionManager._sessions[token]

        return len(expired)


class RateLimiter:
    """Rate limiting to prevent brute force attacks"""

    _attempts = {}  # In production, use Redis

    @staticmethod
    def check_rate_limit(identifier: str, max_attempts: int = 5,
                        window_minutes: int = 15) -> Tuple[bool, int]:
        """
        Check if identifier is within rate limit
        Returns: (is_allowed, remaining_attempts)
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)

        if identifier not in RateLimiter._attempts:
            RateLimiter._attempts[identifier] = []

        # Remove old attempts outside window
        RateLimiter._attempts[identifier] = [
            attempt for attempt in RateLimiter._attempts[identifier]
            if attempt > window_start
        ]

        current_attempts = len(RateLimiter._attempts[identifier])

        if current_attempts >= max_attempts:
            return False, 0

        return True, max_attempts - current_attempts

    @staticmethod
    def record_attempt(identifier: str):
        """Record an attempt"""
        if identifier not in RateLimiter._attempts:
            RateLimiter._attempts[identifier] = []

        RateLimiter._attempts[identifier].append(datetime.utcnow())

    @staticmethod
    def reset_attempts(identifier: str):
        """Reset attempts for identifier"""
        if identifier in RateLimiter._attempts:
            del RateLimiter._attempts[identifier]


class CSRFProtection:
    """CSRF token generation and validation"""

    @staticmethod
    def generate_token() -> str:
        """Generate a CSRF token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def validate_token(token: str, expected_token: str) -> bool:
        """Validate CSRF token"""
        if not token or not expected_token:
            return False

        return secrets.compare_digest(token, expected_token)


class SecureRandom:
    """Cryptographically secure random operations"""

    @staticmethod
    def generate_id() -> str:
        """Generate a secure random ID"""
        return secrets.token_urlsafe(16)

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_numeric_code(length: int = 6) -> str:
        """Generate a numeric code (for 2FA, etc.)"""
        return ''.join(secrets.choice(string.digits) for _ in range(length))


class IPValidator:
    """IP address validation and security"""

    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        """Validate IPv4 address"""
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def is_local_ip(ip: str) -> bool:
        """Check if IP is local/private"""
        if not IPValidator.is_valid_ip(ip):
            return False

        parts = [int(x) for x in ip.split('.')]

        # Check for private ranges
        if parts[0] == 10:  # 10.0.0.0/8
            return True
        if parts[0] == 172 and 16 <= parts[1] <= 31:  # 172.16.0.0/12
            return True
        if parts[0] == 192 and parts[1] == 168:  # 192.168.0.0/16
            return True
        if ip == '127.0.0.1':  # Localhost
            return True

        return False

    @staticmethod
    def hash_ip(ip: str) -> str:
        """Hash IP for privacy-preserving logging"""
        return hashlib.sha256(ip.encode()).hexdigest()[:16]


class SecureMemory:
    """Utilities for secure memory handling"""

    @staticmethod
    def secure_delete(data: any):
        """Securely delete sensitive data from memory"""
        if isinstance(data, str):
            # Overwrite string data
            data = '\x00' * len(data)
        elif isinstance(data, bytearray):
            # Zero out bytearray
            for i in range(len(data)):
                data[i] = 0
        # Let garbage collector handle the rest
        del data


if __name__ == "__main__":
    # Test validators
    print("=== Testing Security Validators ===\n")

    # Test password validation
    print("1. Password Validation:")
    passwords = [
        "weak",
        "StrongPass123!",
        "password123",
        "P@ssw0rd"
    ]

    for pwd in passwords:
        valid, msg = SecurityValidator.validate_master_password(pwd)
        status = "✓" if valid else "✗"
        print(f"  {status} '{pwd}': {msg}")

    # Test username validation
    print("\n2. Username Validation:")
    usernames = ["ab", "valid_user", "user@name", "valid-user-123"]

    for username in usernames:
        valid, msg = SecurityValidator.validate_username(username)
        status = "✓" if valid else "✗"
        print(f"  {status} '{username}': {msg}")

    # Test session management
    print("\n3. Session Management:")
    token = SessionManager.create_session("user123", timeout_minutes=1)
    print(f"  Created session: {token[:16]}...")
    user_id = SessionManager.validate_session(token)
    print(f"  Validated session: user_id = {user_id}")

    # Test rate limiting
    print("\n4. Rate Limiting:")
    identifier = "test_user"
    for i in range(6):
        allowed, remaining = RateLimiter.check_rate_limit(identifier, max_attempts=5)
        if allowed:
            RateLimiter.record_attempt(identifier)
            print(f"  Attempt {i+1}: ✓ Allowed ({remaining} remaining)")
        else:
            print(f"  Attempt {i+1}: ✗ Blocked (rate limit exceeded)")

    print("\n=== Tests Complete ===")


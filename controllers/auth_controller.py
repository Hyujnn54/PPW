"""
Authentication Controller - Handles authentication logic
"""
from typing import Optional, Tuple, Dict
from datetime import datetime, timezone
from services.master_password_service import MasterPasswordService
from utils.security import (
    SecurityValidator, SessionManager, RateLimiter,
    IPValidator, SecureMemory
)
from utils.logger import ActivityLogger, ActionType


class AuthController:
    """Controller for authentication operations"""

    @staticmethod
    def register(
        username: str,
        password: str,
        email: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Register a new user
        Returns: (success, message, user_id)
        """
        try:
            # Validate username
            valid, msg = SecurityValidator.validate_username(username)
            if not valid:
                return False, msg, None

            # Validate password
            valid, msg = SecurityValidator.validate_master_password(password)
            if not valid:
                return False, msg, None

            # Validate email if provided
            if email:
                valid, msg = SecurityValidator.validate_email(email)
                if not valid:
                    return False, msg, None

            # Create master password
            success, message = MasterPasswordService.create_master_password(
                username=username,
                password=password,
                email=email
            )

            if success:
                # Extract user_id from message or query database
                from db.database import db_manager
                user = db_manager.master_password.find_one({'username': username})
                if user:
                    user_id = user['user_id']

                    # Log registration
                    ActivityLogger.log_activity(
                        user_id=user_id,
                        action_type="user_registered",
                        status="success",
                        ip_address=ip_address,
                        details=f"New user registration: {username}"
                    )

                    return True, "Registration successful", user_id

            return False, message, None

        except Exception as e:
            return False, f"Registration error: {str(e)}", None
        finally:
            # Secure cleanup
            SecureMemory.secure_delete(password)

    @staticmethod
    def login(
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        create_session: bool = True
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Authenticate user and create session
        Returns: (success, message, session_data)
        """
        try:
            # Rate limiting check
            identifier = f"login:{username}"
            if ip_address:
                identifier += f":{IPValidator.hash_ip(ip_address)}"

            allowed, remaining = RateLimiter.check_rate_limit(identifier, max_attempts=5)
            if not allowed:
                return False, "Too many failed attempts. Please try again later.", None

            # Attempt authentication
            success, user, message = MasterPasswordService.verify_master_password(
                username, password
            )

            if success and user:
                # Reset rate limiter on success
                RateLimiter.reset_attempts(identifier)

                # Create session
                session_data = None
                if create_session:
                    session_token = SessionManager.create_session(
                        user_id=user['user_id'],
                        timeout_minutes=15
                    )

                    session_data = {
                        'session_token': session_token,
                        'user_id': user['user_id'],
                        'username': user['username'],
                        'email': user.get('email')
                    }

                return True, message, session_data
            else:
                # Record failed attempt
                RateLimiter.record_attempt(identifier)

                return False, f"{message} ({remaining - 1} attempts remaining)", None

        except Exception as e:
            return False, f"Login error: {str(e)}", None
        finally:
            # Secure cleanup
            SecureMemory.secure_delete(password)

    @staticmethod
    def logout(session_token: str, user_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Logout user and destroy session
        """
        try:
            if user_id:
                ActivityLogger.log_activity(
                    user_id=user_id,
                    action_type=ActionType.LOGOUT,
                    status="success"
                )

            SessionManager.destroy_session(session_token)
            return True, "Logged out successfully"

        except Exception as e:
            return False, f"Logout error: {str(e)}"

    @staticmethod
    def validate_session(session_token: str) -> Tuple[bool, Optional[str]]:
        """
        Validate session token
        Returns: (is_valid, user_id)
        """
        try:
            user_id = SessionManager.validate_session(session_token)
            if user_id:
                return True, user_id
            return False, None

        except Exception as e:
            return False, None

    @staticmethod
    def change_password(
        user_id: str,
        old_password: str,
        new_password: str,
        session_token: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Change master password with validation
        """
        try:
            # Validate new password
            valid, msg = SecurityValidator.validate_master_password(new_password)
            if not valid:
                return False, msg

            # Check if new password is different
            if old_password == new_password:
                return False, "New password must be different from old password"

            # Change password
            success, message = MasterPasswordService.change_master_password(
                user_id=user_id,
                old_password=old_password,
                new_password=new_password
            )

            if success and session_token:
                # Invalidate current session for security
                SessionManager.destroy_session(session_token)

            return success, message

        except Exception as e:
            return False, f"Password change error: {str(e)}"
        finally:
            # Secure cleanup
            SecureMemory.secure_delete(old_password)
            SecureMemory.secure_delete(new_password)

    @staticmethod
    def check_account_status(username: str) -> Dict:
        """
        Check if account is locked or has any issues
        """
        from db.database import db_manager
        from datetime import datetime

        try:
            user = db_manager.master_password.find_one({'username': username})

            if not user:
                return {'exists': False}

            locked = False
            locked_until = None

            if user.get('locked_until'):
                if datetime.now(timezone.utc) < user['locked_until']:
                    locked = True
                    locked_until = user['locked_until']

            return {
                'exists': True,
                'locked': locked,
                'locked_until': locked_until,
                'failed_attempts': user.get('failed_attempts', 0),
                'last_login': user.get('last_login')
            }

        except Exception as e:
            return {'exists': False, 'error': str(e)}


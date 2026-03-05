"""
Master Password Service - Handles master password operations and authentication
"""
from datetime import datetime
from typing import Optional, Tuple
import uuid
from db.database import db_manager
from utils.encryption import EncryptionManager
from utils.logger import ActivityLogger, ActionType
from config import MAX_LOGIN_ATTEMPTS, LOCKOUT_DURATION


class MasterPasswordService:
    """Service for managing master password and user authentication"""

    @staticmethod
    def create_master_password(
        username: str,
        password: str,
        email: Optional[str] = None,
        security_questions: Optional[list] = None
    ) -> Tuple[bool, str]:
        """Create a new master password entry"""
        try:
            if db_manager.master_password.find_one({'username': username}):
                return False, "Username already exists"

            user_id = str(uuid.uuid4())
            salt = EncryptionManager.generate_salt()
            password_hash = EncryptionManager.hash_master_password(password, salt)

            encryption_key = EncryptionManager.generate_key()
            encrypted_encryption_key = EncryptionManager.encrypt_encryption_key(
                encryption_key, password, salt
            )

            security_questions_hashed = []
            if security_questions:
                for sq in security_questions:
                    sq_salt = EncryptionManager.generate_salt()
                    answer_hash = EncryptionManager.hash_master_password(
                        sq['answer'].lower().strip(), sq_salt
                    )
                    security_questions_hashed.append({
                        'question': sq['question'],
                        'answer_hash': answer_hash,
                        'salt': sq_salt
                    })

            master_doc = {
                'user_id': user_id,
                'username': username,
                'password_hash': password_hash,
                'salt': salt,
                'encryption_key_encrypted': encrypted_encryption_key,
                'security_question_1': security_questions_hashed[0] if len(security_questions_hashed) > 0 else None,
                'security_question_2': security_questions_hashed[1] if len(security_questions_hashed) > 1 else None,
                'failed_attempts': 0,
                'locked_until': None,
                'password_changed_at': datetime.utcnow(),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'last_login': None,
                'email': email
            }

            db_manager.master_password.insert_one(master_doc)

            ActivityLogger.log_activity(
                user_id=user_id,
                action_type="master_password_created",
                status="success",
                details=f"Master password created for username: {username}"
            )

            return True, f"Master password created successfully for user: {username}"

        except Exception as e:
            return False, f"Error creating master password: {str(e)}"

    @staticmethod
    def verify_master_password(username: str, password: str) -> Tuple[bool, Optional[dict], str]:
        """Verify master password and return user data if successful"""
        try:
            user = db_manager.master_password.find_one({'username': username})

            if not user:
                return False, None, "Invalid username or password"

            if user.get('locked_until'):
                if datetime.utcnow() < user['locked_until']:
                    remaining = (user['locked_until'] - datetime.utcnow()).seconds // 60
                    return False, None, f"Account locked. Try again in {remaining} minutes"
                else:
                    db_manager.master_password.update_one(
                        {'user_id': user['user_id']},
                        {'$set': {'locked_until': None, 'failed_attempts': 0}}
                    )

            if EncryptionManager.verify_master_password(password, user['salt'], user['password_hash']):
                db_manager.master_password.update_one(
                    {'user_id': user['user_id']},
                    {
                        '$set': {
                            'failed_attempts': 0,
                            'last_login': datetime.utcnow(),
                            'locked_until': None
                        }
                    }
                )

                ActivityLogger.log_activity(
                    user_id=user['user_id'],
                    action_type=ActionType.LOGIN,
                    status="success"
                )

                return True, user, "Login successful"
            else:
                failed_attempts = user.get('failed_attempts', 0) + 1
                update_data = {'failed_attempts': failed_attempts}

                if failed_attempts >= MAX_LOGIN_ATTEMPTS:
                    update_data['locked_until'] = datetime.utcnow() + LOCKOUT_DURATION

                db_manager.master_password.update_one(
                    {'user_id': user['user_id']},
                    {'$set': update_data}
                )

                ActivityLogger.log_activity(
                    user_id=user['user_id'],
                    action_type=ActionType.FAILED_LOGIN,
                    status="failure",
                    details=f"Failed attempt {failed_attempts}/{MAX_LOGIN_ATTEMPTS}"
                )

                if failed_attempts >= MAX_LOGIN_ATTEMPTS:
                    return False, None, f"Account locked due to too many failed attempts. Try again in {LOCKOUT_DURATION.seconds // 60} minutes"

                return False, None, f"Invalid username or password. {MAX_LOGIN_ATTEMPTS - failed_attempts} attempts remaining"

        except Exception as e:
            return False, None, f"Error verifying password: {str(e)}"

    @staticmethod
    def change_master_password(user_id: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change the master password"""
        try:
            user = db_manager.master_password.find_one({'user_id': user_id})

            if not user:
                return False, "User not found"

            if not EncryptionManager.verify_master_password(old_password, user['salt'], user['password_hash']):
                return False, "Current password is incorrect"

            encryption_key = EncryptionManager.decrypt_encryption_key(
                user['encryption_key_encrypted'],
                old_password,
                user['salt']
            )

            new_salt = EncryptionManager.generate_salt()
            new_password_hash = EncryptionManager.hash_master_password(new_password, new_salt)

            new_encrypted_key = EncryptionManager.encrypt_encryption_key(
                encryption_key, new_password, new_salt
            )

            db_manager.master_password.update_one(
                {'user_id': user_id},
                {
                    '$set': {
                        'password_hash': new_password_hash,
                        'salt': new_salt,
                        'encryption_key_encrypted': new_encrypted_key,
                        'password_changed_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                }
            )

            ActivityLogger.log_activity(
                user_id=user_id,
                action_type=ActionType.MASTER_PASSWORD_CHANGE,
                status="success"
            )

            return True, "Master password changed successfully"

        except Exception as e:
            return False, f"Error changing password: {str(e)}"

    @staticmethod
    def get_encryption_key(user_id: str, master_password: str) -> Optional[str]:
        """Get the decrypted encryption key for a user"""
        try:
            user = db_manager.master_password.find_one({'user_id': user_id})

            if not user:
                return None

            encryption_key = EncryptionManager.decrypt_encryption_key(
                user['encryption_key_encrypted'],
                master_password,
                user['salt']
            )

            return encryption_key

        except Exception as e:
            print(f"Error getting encryption key: {e}")
            return None


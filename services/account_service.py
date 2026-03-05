"""
Account Service - Handles operations for stored account credentials
"""
from datetime import datetime
from typing import Optional, List, Tuple
import uuid
from db.database import db_manager
from utils.encryption import EncryptionManager, PasswordGenerator
from utils.logger import ActivityLogger, ActionType


class AccountService:
    """Service for managing stored account credentials"""

    @staticmethod
    def add_account(
        user_id: str,
        encryption_key: str,
        title: str,
        password: str,
        username: Optional[str] = None,
        email: Optional[str] = None,
        url: Optional[str] = None,
        category: str = "Other",
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        two_factor_enabled: bool = False
    ) -> Tuple[bool, str]:
        """Add a new account credential"""
        try:
            password_encrypted = EncryptionManager.encrypt_data(password, encryption_key)
            notes_encrypted = EncryptionManager.encrypt_data(notes, encryption_key) if notes else None

            strength_score, _ = PasswordGenerator.calculate_strength(password)

            account_id = str(uuid.uuid4())
            account_doc = {
                'account_id': account_id,
                'user_id': user_id,
                'title': title,
                'username': username,
                'email': email,
                'password_encrypted': password_encrypted,
                'url': url,
                'category': category,
                'notes_encrypted': notes_encrypted,
                'tags': tags or [],
                'favorite': False,
                'strength_score': strength_score,
                'last_password_change': datetime.utcnow(),
                'password_expiry_days': None,
                'two_factor_enabled': two_factor_enabled,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'last_accessed': None,
                'access_count': 0
            }

            db_manager.accounts.insert_one(account_doc)

            ActivityLogger.log_activity(
                user_id=user_id,
                action_type=ActionType.ADD_ACCOUNT,
                status="success",
                account_id=account_id,
                details=f"Added account: {title}"
            )

            return True, f"Account '{title}' added successfully"

        except Exception as e:
            return False, f"Error adding account: {str(e)}"

    @staticmethod
    def get_account(user_id: str, account_id: str) -> Optional[dict]:
        """Get a single account by ID"""
        try:
            account = db_manager.accounts.find_one({
                'user_id': user_id,
                'account_id': account_id
            })

            if account:
                db_manager.accounts.update_one(
                    {'account_id': account_id},
                    {
                        '$set': {'last_accessed': datetime.utcnow()},
                        '$inc': {'access_count': 1}
                    }
                )

            return account

        except Exception as e:
            print(f"Error getting account: {e}")
            return None

    @staticmethod
    def get_all_accounts(
        user_id: str,
        category: Optional[str] = None,
        search: Optional[str] = None,
        favorites_only: bool = False
    ) -> List[dict]:
        """Get all accounts for a user with optional filtering"""
        try:
            query = {'user_id': user_id}

            if category:
                query['category'] = category

            if favorites_only:
                query['favorite'] = True

            if search:
                query['$or'] = [
                    {'title': {'$regex': search, '$options': 'i'}},
                    {'username': {'$regex': search, '$options': 'i'}},
                    {'url': {'$regex': search, '$options': 'i'}},
                    {'tags': {'$regex': search, '$options': 'i'}}
                ]

            accounts = list(db_manager.accounts.find(query).sort('title', 1))
            return accounts

        except Exception as e:
            print(f"Error getting accounts: {e}")
            return []

    @staticmethod
    def update_account(
        user_id: str,
        account_id: str,
        encryption_key: str,
        **updates
    ) -> Tuple[bool, str]:
        """Update an existing account"""
        try:
            account = AccountService.get_account(user_id, account_id)

            if not account:
                return False, "Account not found"

            update_data = {'updated_at': datetime.utcnow()}

            if 'password' in updates:
                update_data['password_encrypted'] = EncryptionManager.encrypt_data(
                    updates['password'], encryption_key
                )
                update_data['last_password_change'] = datetime.utcnow()
                strength_score, _ = PasswordGenerator.calculate_strength(updates['password'])
                update_data['strength_score'] = strength_score
                del updates['password']

            if 'notes' in updates:
                update_data['notes_encrypted'] = EncryptionManager.encrypt_data(
                    updates['notes'], encryption_key
                ) if updates['notes'] else None
                del updates['notes']

            for key, value in updates.items():
                if key in ['title', 'username', 'email', 'url', 'category', 'tags',
                          'favorite', 'two_factor_enabled', 'password_expiry_days']:
                    update_data[key] = value

            db_manager.accounts.update_one(
                {'account_id': account_id, 'user_id': user_id},
                {'$set': update_data}
            )

            ActivityLogger.log_activity(
                user_id=user_id,
                action_type=ActionType.UPDATE_ACCOUNT,
                status="success",
                account_id=account_id,
                details=f"Updated account: {account['title']}"
            )

            return True, "Account updated successfully"

        except Exception as e:
            return False, f"Error updating account: {str(e)}"

    @staticmethod
    def delete_account(user_id: str, account_id: str) -> Tuple[bool, str]:
        """Delete an account"""
        try:
            account = AccountService.get_account(user_id, account_id)

            if not account:
                return False, "Account not found"

            result = db_manager.accounts.delete_one({
                'account_id': account_id,
                'user_id': user_id
            })

            if result.deleted_count > 0:
                ActivityLogger.log_activity(
                    user_id=user_id,
                    action_type=ActionType.DELETE_ACCOUNT,
                    status="success",
                    account_id=account_id,
                    details=f"Deleted account: {account['title']}"
                )
                return True, "Account deleted successfully"
            else:
                return False, "Account not found"

        except Exception as e:
            return False, f"Error deleting account: {str(e)}"

    @staticmethod
    def get_password(user_id: str, account_id: str, encryption_key: str) -> Optional[str]:
        """Get decrypted password for an account"""
        try:
            account = AccountService.get_account(user_id, account_id)

            if not account:
                return None

            password = EncryptionManager.decrypt_data(
                account['password_encrypted'],
                encryption_key
            )

            ActivityLogger.log_activity(
                user_id=user_id,
                action_type=ActionType.VIEW_PASSWORD,
                status="success",
                account_id=account_id,
                details=f"Viewed password for: {account['title']}"
            )

            return password

        except Exception as e:
            print(f"Error getting password: {e}")
            return None

    @staticmethod
    def get_accounts_by_category(user_id: str) -> dict:
        """Get accounts grouped by category with counts"""
        try:
            pipeline = [
                {'$match': {'user_id': user_id}},
                {'$group': {
                    '_id': '$category',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'count': -1}}
            ]

            results = list(db_manager.accounts.aggregate(pipeline))
            return {item['_id']: item['count'] for item in results}

        except Exception as e:
            print(f"Error getting accounts by category: {e}")
            return {}

    @staticmethod
    def toggle_favorite(user_id: str, account_id: str) -> Tuple[bool, str]:
        """Toggle favorite status of an account"""
        try:
            account = AccountService.get_account(user_id, account_id)

            if not account:
                return False, "Account not found"

            new_status = not account.get('favorite', False)

            db_manager.accounts.update_one(
                {'account_id': account_id, 'user_id': user_id},
                {'$set': {'favorite': new_status, 'updated_at': datetime.utcnow()}}
            )

            status = "added to" if new_status else "removed from"
            return True, f"Account {status} favorites"

        except Exception as e:
            return False, f"Error toggling favorite: {str(e)}"


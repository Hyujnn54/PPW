"""
Account Controller - Handles account management logic
"""
from typing import Optional, List, Tuple, Dict
from services.account_service import AccountService
from services.master_password_service import MasterPasswordService
from utils.security import SecurityValidator
from utils.encryption import PasswordGenerator


class AccountController:
    """Controller for account management operations"""

    @staticmethod
    def create_account(
        user_id: str,
        master_password: str,
        title: str,
        password: str,
        username: Optional[str] = None,
        email: Optional[str] = None,
        url: Optional[str] = None,
        category: str = "Other",
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """Create a new account with validation."""
        try:
            title = SecurityValidator.sanitize_input(title, max_length=100)
            if not title:
                return False, "Title is required"

            if username:
                username = SecurityValidator.sanitize_input(username, max_length=100)
            if email:
                valid, msg = SecurityValidator.validate_email(email)
                if not valid:
                    return False, msg
            if url:
                valid, msg = SecurityValidator.validate_url(url)
                if not valid:
                    return False, msg
            if notes:
                notes = SecurityValidator.sanitize_input(notes, max_length=1000)

            encryption_key = MasterPasswordService.get_encryption_key(user_id, master_password)
            if not encryption_key:
                return False, "Failed to get encryption key — check your master password"

            return AccountService.add_account(
                user_id=user_id,
                encryption_key=encryption_key,
                title=title,
                password=password,
                username=username,
                email=email,
                url=url,
                category=category,
                notes=notes,
                tags=tags
            )
        except Exception as e:
            return False, f"Error creating account: {str(e)}"

    @staticmethod
    def get_accounts(
        user_id: str,
        category: Optional[str] = None,
        search: Optional[str] = None,
        favorites_only: bool = False
    ) -> List[Dict]:
        """Get all accounts with filtering."""
        try:
            if search:
                search = SecurityValidator.sanitize_input(search, max_length=100)

            accounts = AccountService.get_all_accounts(
                user_id=user_id,
                category=category,
                search=search,
                favorites_only=favorites_only
            )

            return [
                {
                    'account_id': a['account_id'],
                    'title': a['title'],
                    'username': a.get('username'),
                    'email': a.get('email'),
                    'url': a.get('url'),
                    'category': a['category'],
                    'tags': a.get('tags', []),
                    'favorite': a.get('favorite', False),
                    'strength_score': a.get('strength_score', 0),
                    'two_factor_enabled': a.get('two_factor_enabled', False),
                    'created_at': a.get('created_at'),
                    'last_accessed': a.get('last_accessed'),
                }
                for a in accounts
            ]
        except Exception as e:
            print(f"Error getting accounts: {e}")
            return []

    @staticmethod
    def get_account_details(
        user_id: str,
        account_id: str,
        include_password: bool = False,
        master_password: Optional[str] = None,
        encryption_key: Optional[str] = None
    ) -> Optional[Dict]:
        """Get detailed account information, optionally with decrypted password."""
        try:
            account = AccountService.get_account(user_id, account_id)
            if not account:
                return None

            account_data = {
                'account_id': account['account_id'],
                'title': account['title'],
                'username': account.get('username'),
                'email': account.get('email'),
                'url': account.get('url'),
                'category': account['category'],
                'tags': account.get('tags', []),
                'favorite': account.get('favorite', False),
                'strength_score': account.get('strength_score', 0),
                'two_factor_enabled': account.get('two_factor_enabled', False),
                'created_at': account.get('created_at'),
                'updated_at': account.get('updated_at'),
                'last_accessed': account.get('last_accessed'),
                'access_count': account.get('access_count', 0),
            }

            if include_password:
                key = encryption_key
                if not key and master_password:
                    key = MasterPasswordService.get_encryption_key(user_id, master_password)
                if key:
                    account_data['password'] = AccountService.get_password(
                        user_id, account_id, key)
                    if account.get('notes_encrypted'):
                        from utils.encryption import EncryptionManager
                        account_data['notes'] = EncryptionManager.decrypt_data(
                            account['notes_encrypted'], key)

            return account_data
        except Exception as e:
            print(f"Error getting account details: {e}")
            return None

    @staticmethod
    def update_account(
        user_id: str,
        account_id: str,
        master_password: str,
        **updates
    ) -> Tuple[bool, str]:
        """Update account with validation."""
        try:
            encryption_key = MasterPasswordService.get_encryption_key(user_id, master_password)
            if not encryption_key:
                return False, "Failed to get encryption key"

            if 'title' in updates and updates['title']:
                updates['title'] = SecurityValidator.sanitize_input(updates['title'], max_length=100)
            if 'username' in updates and updates['username']:
                updates['username'] = SecurityValidator.sanitize_input(updates['username'], max_length=100)
            if 'email' in updates and updates['email']:
                valid, msg = SecurityValidator.validate_email(updates['email'])
                if not valid:
                    return False, msg
            if 'url' in updates and updates['url']:
                valid, msg = SecurityValidator.validate_url(updates['url'])
                if not valid:
                    return False, msg
            if 'notes' in updates and updates['notes']:
                updates['notes'] = SecurityValidator.sanitize_input(updates['notes'], max_length=1000)

            return AccountService.update_account(
                user_id=user_id,
                account_id=account_id,
                encryption_key=encryption_key,
                **updates
            )
        except Exception as e:
            return False, f"Error updating account: {str(e)}"

    @staticmethod
    def delete_account(user_id: str, account_id: str) -> Tuple[bool, str]:
        """Delete an account."""
        try:
            return AccountService.delete_account(user_id, account_id)
        except Exception as e:
            return False, f"Error deleting account: {str(e)}"

    @staticmethod
    def toggle_favorite(user_id: str, account_id: str) -> Tuple[bool, str]:
        """Toggle favorite status."""
        try:
            return AccountService.toggle_favorite(user_id, account_id)
        except Exception as e:
            return False, f"Error toggling favorite: {str(e)}"

    @staticmethod
    def get_categories_summary(user_id: str) -> Dict:
        """Get summary of accounts by category."""
        try:
            return AccountService.get_accounts_by_category(user_id)
        except Exception as e:
            print(f"Error getting categories: {e}")
            return {}

    @staticmethod
    def generate_strong_password(
        length: int = 20,
        use_uppercase: bool = True,
        use_lowercase: bool = True,
        use_digits: bool = True,
        use_symbols: bool = True
    ) -> Dict:
        """Generate a strong password with strength analysis."""
        try:
            length = max(8, min(128, length))
            password = PasswordGenerator.generate_password(
                length=length,
                use_uppercase=use_uppercase,
                use_lowercase=use_lowercase,
                use_digits=use_digits,
                use_symbols=use_symbols,
            )
            score, feedback = PasswordGenerator.calculate_strength(password)
            return {'password': password, 'strength_score': score,
                    'feedback': feedback, 'length': len(password)}
        except Exception as e:
            return {'password': None, 'error': str(e)}

    @staticmethod
    def analyze_password_strength(password: str) -> Dict:
        """Analyze password strength."""
        try:
            score, feedback = PasswordGenerator.calculate_strength(password)
            return {'score': score, 'feedback': feedback,
                    'length': len(password), 'is_strong': score >= 70}
        except Exception as e:
            return {'score': 0, 'error': str(e)}

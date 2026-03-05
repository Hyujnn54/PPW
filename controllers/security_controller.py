"""
Security Controller - Handles security operations
"""
from typing import Dict, List
from utils.logger import ActivityLogger
from utils.security import SessionManager, RateLimiter
from datetime import datetime, timedelta


class SecurityController:
    """Controller for security operations"""

    @staticmethod
    def get_activity_logs(
        user_id: str,
        limit: int = 50,
        action_type: str = None,
        days: int = 30
    ) -> List[Dict]:
        """
        Get activity logs for user
        """
        try:
            logs = ActivityLogger.get_user_logs(
                user_id=user_id,
                limit=limit,
                action_type=action_type
            )

            # Filter by date if specified
            if days:
                cutoff = datetime.utcnow() - timedelta(days=days)
                logs = [log for log in logs if log.get('timestamp', datetime.min) >= cutoff]

            # Format logs for display
            formatted_logs = []
            for log in logs:
                formatted_log = {
                    'action': log.get('action_type'),
                    'status': log.get('status'),
                    'timestamp': log.get('timestamp'),
                    'details': log.get('details'),
                    'ip_address': log.get('ip_address')
                }
                formatted_logs.append(formatted_log)

            return formatted_logs

        except Exception as e:
            print(f"Error getting activity logs: {e}")
            return []

    @staticmethod
    def get_security_summary(user_id: str) -> Dict:
        """
        Get security summary for user
        """
        from db.database import db_manager
        from services.account_service import AccountService

        try:
            # Get user info
            user = db_manager.master_password.find_one({'user_id': user_id})
            if not user:
                return {}

            # Get all accounts
            accounts = AccountService.get_all_accounts(user_id)

            # Calculate statistics
            total_accounts = len(accounts)
            weak_passwords = sum(1 for acc in accounts if acc.get('strength_score', 0) < 50)
            medium_passwords = sum(1 for acc in accounts if 50 <= acc.get('strength_score', 0) < 75)
            strong_passwords = sum(1 for acc in accounts if acc.get('strength_score', 0) >= 75)

            with_2fa = sum(1 for acc in accounts if acc.get('two_factor_enabled', False))

            # Get recent activity
            recent_logs = ActivityLogger.get_user_logs(user_id, limit=10)
            recent_failed_logins = sum(
                1 for log in recent_logs
                if log.get('action_type') == 'failed_login'
            )

            # Password age check
            now = datetime.utcnow()
            old_passwords = sum(
                1 for acc in accounts
                if (now - acc.get('last_password_change', now)).days > 90
            )

            return {
                'total_accounts': total_accounts,
                'password_strength': {
                    'weak': weak_passwords,
                    'medium': medium_passwords,
                    'strong': strong_passwords
                },
                'accounts_with_2fa': with_2fa,
                '2fa_percentage': round(with_2fa / total_accounts * 100, 1) if total_accounts > 0 else 0,
                'old_passwords': old_passwords,
                'recent_failed_logins': recent_failed_logins,
                'last_login': user.get('last_login'),
                'password_changed_at': user.get('password_changed_at'),
                'account_created_at': user.get('created_at')
            }

        except Exception as e:
            print(f"Error getting security summary: {e}")
            return {}

    @staticmethod
    def get_weak_passwords(user_id: str, threshold: int = 60) -> List[Dict]:
        """
        Get list of accounts with weak passwords
        """
        from services.account_service import AccountService

        try:
            accounts = AccountService.get_all_accounts(user_id)

            weak_accounts = [
                {
                    'account_id': acc['account_id'],
                    'title': acc['title'],
                    'strength_score': acc.get('strength_score', 0),
                    'category': acc['category']
                }
                for acc in accounts
                if acc.get('strength_score', 0) < threshold
            ]

            # Sort by weakest first
            weak_accounts.sort(key=lambda x: x['strength_score'])

            return weak_accounts

        except Exception as e:
            print(f"Error getting weak passwords: {e}")
            return []

    @staticmethod
    def get_old_passwords(user_id: str, days: int = 90) -> List[Dict]:
        """
        Get accounts with passwords older than specified days
        """
        from services.account_service import AccountService

        try:
            accounts = AccountService.get_all_accounts(user_id)
            cutoff = datetime.utcnow() - timedelta(days=days)

            old_accounts = [
                {
                    'account_id': acc['account_id'],
                    'title': acc['title'],
                    'last_password_change': acc.get('last_password_change'),
                    'days_old': (datetime.utcnow() - acc.get('last_password_change', datetime.utcnow())).days,
                    'category': acc['category']
                }
                for acc in accounts
                if acc.get('last_password_change', datetime.utcnow()) < cutoff
            ]

            # Sort by oldest first
            old_accounts.sort(key=lambda x: x['days_old'], reverse=True)

            return old_accounts

        except Exception as e:
            print(f"Error getting old passwords: {e}")
            return []

    @staticmethod
    def cleanup_sessions():
        """Clean up expired sessions"""
        try:
            count = SessionManager.cleanup_expired_sessions()
            return {'cleaned': count}
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def get_active_sessions_count() -> int:
        """Get count of active sessions"""
        try:
            return len(SessionManager._sessions)
        except Exception as e:
            return 0


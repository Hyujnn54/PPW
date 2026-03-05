"""
Activity logging utilities
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
from db.database import db_manager


class ActivityLogger:
    """Log all user activities for security auditing"""

    @staticmethod
    def log_activity(
        user_id: str,
        action_type: str,
        status: str = "success",
        account_id: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        device_info: Optional[str] = None
    ) -> bool:
        """Log an activity to the database"""
        try:
            log_entry = {
                'log_id': str(uuid.uuid4()),
                'user_id': user_id,
                'action_type': action_type,
                'account_id': account_id,
                'status': status,
                'details': details,
                'ip_address': ip_address,
                'device_info': device_info,
                'timestamp': datetime.now(timezone.utc)
            }

            db_manager.activity_logs.insert_one(log_entry)
            return True
        except Exception as e:
            print(f"Error logging activity: {e}")
            return False

    @staticmethod
    def get_user_logs(user_id: str, limit: int = 50, action_type: Optional[str] = None):
        """Retrieve activity logs for a user"""
        try:
            query = {'user_id': user_id}
            if action_type:
                query['action_type'] = action_type

            logs = db_manager.activity_logs.find(query).sort('timestamp', -1).limit(limit)
            return list(logs)
        except Exception as e:
            print(f"Error retrieving logs: {e}")
            return []

    @staticmethod
    def get_recent_failed_logins(user_id: str, minutes: int = 30):
        """Get recent failed login attempts"""
        try:
            from datetime import timedelta
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)

            failed_logins = db_manager.activity_logs.count_documents({
                'user_id': user_id,
                'action_type': 'failed_login',
                'timestamp': {'$gte': cutoff_time}
            })

            return failed_logins
        except Exception as e:
            print(f"Error counting failed logins: {e}")
            return 0

    @staticmethod
    def clear_old_logs(days: int = 90):
        """Clear logs older than specified days"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            result = db_manager.activity_logs.delete_many({
                'timestamp': {'$lt': cutoff_date}
            })

            return result.deleted_count
        except Exception as e:
            print(f"Error clearing old logs: {e}")
            return 0


class ActionType:
    """Action type constants"""
    LOGIN = "login"
    LOGOUT = "logout"
    FAILED_LOGIN = "failed_login"
    MASTER_PASSWORD_CHANGE = "master_password_change"
    ADD_ACCOUNT = "add_account"
    UPDATE_ACCOUNT = "update_account"
    DELETE_ACCOUNT = "delete_account"
    VIEW_PASSWORD = "view_password"
    COPY_PASSWORD = "copy_password"
    EXPORT_DATA = "export_data"
    IMPORT_DATA = "import_data"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"


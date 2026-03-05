"""
MongoDB Schema Definitions for Password Manager
MongoDB is schema-less, but we define structures for consistency
"""
from datetime import datetime
from typing import TypedDict, Optional, List


class MasterPasswordSchema(TypedDict):
    """
    Master Password Collection Schema
    Stores the hashed master password and related settings
    """
    user_id: str  # Unique identifier for the user
    username: str  # Username for the password manager
    password_hash: str  # Hashed master password (PBKDF2 + salt)
    salt: str  # Salt used for password hashing
    encryption_key_encrypted: str  # Encrypted encryption key for account passwords
    security_question_1: Optional[dict]  # {"question": str, "answer_hash": str}
    security_question_2: Optional[dict]
    failed_attempts: int  # Track failed login attempts
    locked_until: Optional[datetime]  # Account lockout timestamp
    password_changed_at: datetime
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    email: Optional[str]  # For recovery purposes


class AccountSchema(TypedDict):
    """
    Accounts Collection Schema
    Stores encrypted account credentials
    """
    account_id: str  # Unique identifier for each account
    user_id: str  # Reference to master password user_id
    title: str  # Display name (e.g., "Gmail", "Facebook")
    username: Optional[str]  # Username/email for the account
    email: Optional[str]  # Email if different from username
    password_encrypted: str  # Encrypted password
    url: Optional[str]  # Website URL
    category: str  # Category (e.g., "Social Media", "Banking", "Email")
    notes_encrypted: Optional[str]  # Encrypted additional notes
    tags: List[str]  # Tags for organization
    favorite: bool  # Mark as favorite
    strength_score: int  # Password strength (0-100)
    last_password_change: Optional[datetime]
    password_expiry_days: Optional[int]  # Alert if password is old
    two_factor_enabled: bool
    created_at: datetime
    updated_at: datetime
    last_accessed: Optional[datetime]
    access_count: int  # How many times password was viewed


class ActivityLogSchema(TypedDict):
    """
    Activity Logs Collection Schema
    Track all actions for security auditing
    """
    log_id: str  # Unique log identifier
    user_id: str  # Reference to user
    action_type: str  # "login", "logout", "add_account", "update_account", "delete_account", "view_password", "failed_login", "master_password_change"
    account_id: Optional[str]  # Reference to account if applicable
    ip_address: Optional[str]  # IP address of action
    device_info: Optional[str]  # Device/browser information
    status: str  # "success", "failure", "warning"
    details: Optional[str]  # Additional details about the action
    timestamp: datetime


class CategorySchema(TypedDict):
    """
    Categories Collection Schema
    Define custom categories for organizing accounts
    """
    category_id: str
    user_id: str
    name: str  # Category name
    icon: Optional[str]  # Icon name or emoji
    color: Optional[str]  # Hex color code
    description: Optional[str]
    account_count: int  # Number of accounts in this category
    created_at: datetime
    updated_at: datetime


# Default categories
DEFAULT_CATEGORIES = [
    {"name": "Social Media", "icon": "👥", "color": "#1DA1F2"},
    {"name": "Email", "icon": "📧", "color": "#EA4335"},
    {"name": "Banking", "icon": "🏦", "color": "#00A86B"},
    {"name": "Shopping", "icon": "🛒", "color": "#FF9900"},
    {"name": "Entertainment", "icon": "🎬", "color": "#E50914"},
    {"name": "Work", "icon": "💼", "color": "#0077B5"},
    {"name": "Education", "icon": "📚", "color": "#4285F4"},
    {"name": "Other", "icon": "📌", "color": "#6C757D"},
]


# MongoDB Indexes for better performance
INDEXES = {
    'master_password': [
        {'keys': [('user_id', 1)], 'unique': True},
        {'keys': [('username', 1)], 'unique': True},
        {'keys': [('email', 1)], 'sparse': True},
    ],
    'accounts': [
        {'keys': [('account_id', 1)], 'unique': True},
        {'keys': [('user_id', 1), ('title', 1)]},
        {'keys': [('user_id', 1), ('category', 1)]},
        {'keys': [('user_id', 1), ('favorite', -1)]},
        {'keys': [('user_id', 1), ('created_at', -1)]},
    ],
    'activity_logs': [
        {'keys': [('log_id', 1)], 'unique': True},
        {'keys': [('user_id', 1), ('timestamp', -1)]},
        {'keys': [('action_type', 1), ('timestamp', -1)]},
        {'keys': [('timestamp', -1)]},  # For cleanup of old logs
    ],
    'categories': [
        {'keys': [('category_id', 1)], 'unique': True},
        {'keys': [('user_id', 1), ('name', 1)], 'unique': True},
    ],
}


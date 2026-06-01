"""
Simple user authentication for PyPrint.
Users are stored in SQLite database.
"""
import os
import sys
from typing import Optional, Dict, List

# Import from db_users module
from utils.db_users import (
    create_user as db_create_user,
    verify_user as db_verify_user,
    get_user as db_get_user,
    list_users as db_list_users,
    delete_user as db_delete_user,
    update_user_role as db_update_user_role,
    change_password as db_change_password,
    admin_reset_password as db_admin_reset_password,
    hash_password as hash_pwd
)


class UserManager:
    """User manager with database-backed authentication."""

    def __init__(self):
        # Import here to avoid circular imports
        from utils.database import init_db
        init_db()

        # Create default admin user if no users exist
        if not db_list_users():
            local_only = os.environ.get('PYPRINT_LOCAL_ONLY', 'true').lower() == 'true'
            if local_only and sys.platform in ['win32', 'linux']:
                db_create_user('admin', 'admin', role='admin')

    def verify_user(self, username: str, password: str) -> Optional[Dict]:
        """Verify username and password. Returns user dict if valid."""
        return db_verify_user(username, password)

    def get_user(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        return db_get_user(username)

    def add_user(self, username: str, password: str, role: str = 'user') -> bool:
        """Add a new user."""
        result = db_create_user(username, password, role=role)
        return 'error' not in result

    def list_users(self) -> List[Dict]:
        """List all users (for admin)."""
        return db_list_users()

    def remove_user(self, username: str) -> bool:
        """Remove a user."""
        return db_delete_user(username)

    def update_user_role(self, username: str, role: str) -> bool:
        """Update user role."""
        return db_update_user_role(username, role)

    def change_password(self, username: str, old_password: str, new_password: str) -> dict:
        """Change password with old password verification."""
        return db_change_password(username, old_password, new_password)

    def admin_reset_password(self, username: str, new_password: str) -> dict:
        """Admin force-reset a user's password."""
        return db_admin_reset_password(username, new_password)


# Singleton instance
_user_manager = None

def get_user_manager() -> UserManager:
    """Get the singleton UserManager instance."""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
    return _user_manager
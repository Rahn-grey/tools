"""
PyPrint User Persistence Layer
Handles user CRUD operations with SQLite.
"""
import sqlite3
import hashlib
from utils.database import get_db, init_db

# Password hashing salt (reuse from original auth.py)
SALT = 'pyprint_salt_v1'

def hash_password(password: str) -> str:
    """Hash password with salt using SHA256."""
    return hashlib.sha256(f"{SALT}{password}".encode()).hexdigest()

def create_user(username: str, password: str, email: str = '', role: str = 'user') -> dict:
    """Create a new user."""
    init_db()
    password_hash = hash_password(password)

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash, email, role)
            VALUES (?, ?, ?, ?)
        ''', (username, password_hash, email, role))
        conn.commit()
        return {
            'id': cursor.lastrowid,
            'username': username,
            'email': email,
            'role': role,
            'is_active': True
        }
    except sqlite3.IntegrityError:
        return {'error': 'Username already exists'}
    finally:
        conn.close()

def verify_user(username: str, password: str) -> dict:
    """Verify user credentials. Returns user dict if valid, None if invalid."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND is_active = 1', (username,))
    row = cursor.fetchone()
    conn.close()

    if row and row['password_hash'] == hash_password(password):
        return {
            'username': row['username'],
            'email': row['email'],
            'role': row['role']
        }
    return None

def get_user(username: str) -> dict:
    """Get user by username."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            'username': row['username'],
            'email': row['email'],
            'role': row['role'],
            'is_active': bool(row['is_active']),
            'created_at': row['created_at']
        }
    return None

def list_users() -> list:
    """List all users (for admin)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, role, created_at, is_active FROM users ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def delete_user(username: str) -> bool:
    """Delete a user by username."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE username = ?', (username,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

def update_user_role(username: str, role: str) -> bool:
    """Update user role."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET role = ? WHERE username = ?', (role, username))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

def change_password(username: str, old_password: str, new_password: str) -> dict:
    """Change a user's password. Requires old password verification."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {'success': False, 'error': '用户不存在'}
    if row['password_hash'] != hash_password(old_password):
        conn.close()
        return {'success': False, 'error': '原密码错误'}
    new_hash = hash_password(new_password)
    cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', (new_hash, username))
    conn.commit()
    conn.close()
    return {'success': True}

def admin_reset_password(username: str, new_password: str) -> dict:
    """Admin force-reset a user's password without old password."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    if not cursor.fetchone():
        conn.close()
        return {'success': False, 'error': '用户不存在'}
    new_hash = hash_password(new_password)
    cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', (new_hash, username))
    conn.commit()
    conn.close()
    return {'success': True}
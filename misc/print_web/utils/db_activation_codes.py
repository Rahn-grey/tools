"""
PyPrint Activation Code Management
Handles activation code generation and validation with SQLite.
"""
import secrets
import string
from datetime import datetime, timedelta
from utils.database import get_db, init_db

def generate_code(created_by: str, expires_in_days: int = 7) -> dict:
    """Generate a new activation code."""
    init_db()

    # Generate random8-character code
    chars = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(chars) for _ in range(8))

    expires_at = datetime.now() + timedelta(days=expires_in_days)

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO activation_codes (code, created_by, expires_at)
            VALUES (?, ?, ?)
        ''', (code, created_by, expires_at.isoformat()))
        conn.commit()
        return {
            'code': code,
            'created_by': created_by,
            'expires_at': expires_at.isoformat(),
            'is_used': False
        }
    finally:
        conn.close()

def validate_code(code: str) -> dict:
    """Validate an activation code. Returns code info if valid, None if invalid."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM activation_codes WHERE code = ?', (code,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    if row['is_used']:
        return {'valid': False, 'error': 'Code already used'}

    expires_at = datetime.fromisoformat(row['expires_at'])
    if datetime.now() > expires_at:
        return {'valid': False, 'error': 'Code expired'}

    return {
        'valid': True,
        'code': row['code'],
        'created_by': row['created_by'],
        'expires_at': row['expires_at']
    }

def use_code(code: str, used_by: str) -> bool:
    """Mark an activation code as used."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE activation_codes
        SET is_used = 1, used_by = ?, used_at = ?
        WHERE code = ?
    ''', (used_by, datetime.now().isoformat(), code))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

def list_codes(include_used: bool = False) -> list:
    """List all activation codes."""
    conn = get_db()
    cursor = conn.cursor()

    if include_used:
        cursor.execute('SELECT * FROM activation_codes ORDER BY created_at DESC')
    else:
        cursor.execute('SELECT * FROM activation_codes WHERE is_used = 0 ORDER BY created_at DESC')

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_code(code: str) -> bool:
    """Delete an activation code."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM activation_codes WHERE code = ?', (code,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted
"""
PyPrint SQLite Database Module
Provides database connection and schema initialization.
"""
import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime, timedelta

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'pyprint.db')

def get_db():
    """Get database connection with Row factory."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db_cursor():
    """Context manager for database operations."""
    conn = get_db()
    try:
        yield conn.cursor()
        conn.commit()
    finally:
        conn.close()

def init_db():
    """Initialize database schema."""
    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')

    # Activation codes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activation_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            created_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_used BOOLEAN DEFAULT 0,
            used_by TEXT,
            used_at TIMESTAMP
        )
    ''')

    # Print jobs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS print_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT,
            user_id TEXT NOT NULL,
            printer_name TEXT NOT NULL,
            file_name TEXT NOT NULL,
            pages INTEGER DEFAULT 1,
            copies INTEGER DEFAULT 1,
            status TEXT DEFAULT 'completed',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print(f"Database initialized at: {DATABASE_PATH}")
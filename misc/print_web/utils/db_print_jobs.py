"""
PyPrint Print Job Logging
Handles print job logging and statistics with SQLite.
"""
from datetime import datetime
from utils.database import get_db, init_db

def log_print_job(job_id: str, user_id: str, printer_name: str, file_name: str,
                  pages: int = 1, copies: int = 1, status: str = 'completed',
                  **options) -> dict:
    """Log a print job to the database."""
    init_db()

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO print_jobs (job_id, user_id, printer_name, file_name, pages, copies, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (job_id, user_id, printer_name, file_name, pages, copies, status))
        conn.commit()
        return {
            'id': cursor.lastrowid,
            'job_id': job_id,
            'user_id': user_id,
            'printer_name': printer_name,
            'file_name': file_name,
            'pages': pages,
            'copies': copies,
            'status': status
        }
    finally:
        conn.close()

def get_print_history(user_id: str = None, limit: int = 50, offset: int = 0) -> list:
    """Get print history, optionally filtered by user."""
    conn = get_db()
    cursor = conn.cursor()

    if user_id:
        cursor.execute('''
            SELECT * FROM print_jobs
            WHERE user_id = ?
            ORDER BY submitted_at DESC
            LIMIT ? OFFSET ?
        ''', (user_id, limit, offset))
    else:
        cursor.execute('''
            SELECT * FROM print_jobs
            ORDER BY submitted_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_print_stats(from_date: str = None, to_date: str = None,
                    user_id: str = None, printer_name: str = None) -> dict:
    """Get aggregated print statistics."""
    conn = get_db()
    cursor = conn.cursor()

    query = 'SELECT COUNT(*) as total_jobs, SUM(pages * copies) as total_pages, SUM(copies) as total_copies FROM print_jobs WHERE 1=1'
    params = []

    if from_date:
        query += ' AND submitted_at >= ?'
        params.append(from_date)
    if to_date:
        query += ' AND submitted_at <= ?'
        params.append(to_date)
    if user_id:
        query += ' AND user_id = ?'
        params.append(user_id)
    if printer_name:
        query += ' AND printer_name = ?'
        params.append(printer_name)

    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()

    return {
        'total_jobs': row['total_jobs'] or 0,
        'total_pages': row['total_pages'] or 0,
        'total_copies': row['total_copies'] or 0
    }

def get_user_print_stats(user_id: str) -> dict:
    """Get print statistics for a specific user."""
    return get_print_stats(user_id=user_id)

def get_printer_print_stats(printer_name: str) -> dict:
    """Get print statistics for a specific printer."""
    return get_print_stats(printer_name=printer_name)
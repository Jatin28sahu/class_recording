"""
SQLite Database operations for class recording management
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path


DB_PATH = Path(__file__).parent / "recordings.db"


def init_database():
    """Initialize the database with the recordings table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            class TEXT NOT NULL,
            section TEXT,
            subject TEXT NOT NULL,
            audio_filename TEXT NOT NULL,
            combined_md TEXT,
            job_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


def insert_recording(
    class_name: str,
    subject: str,
    audio_filename: str,
    job_id: str,
    section: Optional[str] = None
) -> int:
    """
    Insert a new recording entry into the database.
    
    Returns:
        int: The ID of the inserted record
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("""
        INSERT INTO recordings (date, class, section, subject, audio_filename, job_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (current_date, class_name, section, subject, audio_filename, job_id))
    
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return record_id


def update_combined_md(job_id: str, combined_md: str):
    """Update the combined_md field for a specific job."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE recordings
        SET combined_md = ?
        WHERE job_id = ?
    """, (combined_md, job_id))
    
    conn.commit()
    conn.close()


def get_recording_by_job_id(job_id: str) -> Optional[Dict[str, Any]]:
    """Get a recording by job_id."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, date, class, section, subject, audio_filename, combined_md, job_id, created_at
        FROM recordings
        WHERE job_id = ?
    """, (job_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_all_recordings(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Get all recordings with pagination."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, date, class, section, subject, audio_filename, job_id, created_at
        FROM recordings
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_recording_by_id(record_id: int) -> Optional[Dict[str, Any]]:
    """Get a recording by ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, date, class, section, subject, audio_filename, combined_md, job_id, created_at
        FROM recordings
        WHERE id = ?
    """, (record_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


# Initialize database on module import
init_database()

"""Database connection helpers. Credentials come from environment variables."""
import os

import mysql.connector


def get_db():
    """Open a new MySQL connection."""
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "job_tracker"),
    )


def query(sql, params=(), one=False):
    """Run a SELECT. Returns a list of dict rows, or one row (or None) if one=True."""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        cursor.close()
    finally:
        conn.close()
    if one:
        return rows[0] if rows else None
    return rows


def execute(sql, params=()):
    """Run an INSERT/UPDATE/DELETE and commit. Returns the last inserted id."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        last_id = cursor.lastrowid
        cursor.close()
    finally:
        conn.close()
    return last_id

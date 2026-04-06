"""
database.py
-----------
Handles all SQLite database operations for the Palm Vein Payment System.
Tables: users, transactions, authentication_logs
"""

import sqlite3
import os
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(__file__), "payment_system.db")


def get_connection():
    """Create and return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allows dict-like access to rows
    return conn


def initialize_database():
    """
    Create all necessary tables if they do not already exist.
    Call this once at application startup.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # --- Users Table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            palm_image_path TEXT NOT NULL,
            balance     REAL NOT NULL DEFAULT 1000.0,
            created_at  TEXT NOT NULL
        )
    """)

    # --- Transactions Table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id  TEXT PRIMARY KEY,
            user_id         TEXT NOT NULL,
            amount          REAL NOT NULL,
            timestamp       TEXT NOT NULL,
            status          TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # --- Authentication Logs Table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS authentication_logs (
            log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL,
            result      TEXT NOT NULL,
            timestamp   TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Database initialized successfully.")


# ──────────────────────────────────────────────
# USER OPERATIONS
# ──────────────────────────────────────────────

def register_user(user_id: str, name: str, palm_image_path: str, balance: float = 1000.0) -> bool:
    """
    Register a new user in the database.

    Args:
        user_id:         Unique identifier for the user.
        name:            Full name of the user.
        palm_image_path: Path to the user's registered palm image.
        balance:         Starting wallet balance (default: 1000.0).

    Returns:
        True if registration succeeded, False if user_id already exists.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (user_id, name, palm_image_path, balance, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, palm_image_path, balance, datetime.now().isoformat()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # user_id already exists
        return False
    finally:
        conn.close()


def get_user(user_id: str):
    """
    Fetch a user record by user_id.

    Returns:
        A sqlite3.Row object (dict-like) or None if not found.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def get_all_users():
    """Return a list of all registered users."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, name, balance, created_at FROM users")
    users = cursor.fetchall()
    conn.close()
    return users


def update_balance(user_id: str, new_balance: float) -> bool:
    """Update the wallet balance for a given user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


# ──────────────────────────────────────────────
# TRANSACTION OPERATIONS
# ──────────────────────────────────────────────

def record_transaction(transaction_id: str, user_id: str, amount: float, status: str) -> bool:
    """
    Insert a new transaction record.

    Args:
        transaction_id: Unique transaction identifier (UUID).
        user_id:        The user performing the payment.
        amount:         Payment amount.
        status:         'SUCCESS' or 'FAILED'.

    Returns:
        True on success.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (transaction_id, user_id, amount, timestamp, status)
        VALUES (?, ?, ?, ?, ?)
    """, (transaction_id, user_id, amount, datetime.now().isoformat(), status))
    conn.commit()
    conn.close()
    return True


def get_user_transactions(user_id: str):
    """Return all transactions for a specific user, newest first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM transactions
        WHERE user_id = ?
        ORDER BY timestamp DESC
    """, (user_id,))
    txns = cursor.fetchall()
    conn.close()
    return txns


# ──────────────────────────────────────────────
# AUTHENTICATION LOG OPERATIONS
# ──────────────────────────────────────────────

def log_authentication(user_id: str, result: str) -> None:
    """
    Record an authentication attempt in the log.

    Args:
        user_id: The user being authenticated.
        result:  'SUCCESS' or 'FAILED'.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO authentication_logs (user_id, result, timestamp)
        VALUES (?, ?, ?)
    """, (user_id, result, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_auth_logs(user_id: str = None):
    """
    Retrieve authentication logs, optionally filtered by user_id.

    Args:
        user_id: If provided, returns logs only for that user.

    Returns:
        List of log rows.
    """
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("""
            SELECT * FROM authentication_logs
            WHERE user_id = ?
            ORDER BY timestamp DESC
        """, (user_id,))
    else:
        cursor.execute("SELECT * FROM authentication_logs ORDER BY timestamp DESC")
    logs = cursor.fetchall()
    conn.close()
    return logs
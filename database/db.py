
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = Path(__file__).resolve().parent / "correlation.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                column_count INTEGER NOT NULL,
                summary TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)


def create_user(username, password):
    password_hash = generate_password_hash(password)

    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None


def verify_user(username, password):
    with get_connection() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

    if user and check_password_hash(user["password_hash"], password):
        return dict(user)

    return None


def save_analysis(user_id, source, row_count, column_count, summary):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO analysis_history
            (user_id, source, row_count, column_count, summary)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, source, row_count, column_count, summary)
        )


def get_history(user_id, limit=10):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT source, row_count, column_count, summary, created_at
            FROM analysis_history
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit)
        ).fetchall()

    return [dict(row) for row in rows]

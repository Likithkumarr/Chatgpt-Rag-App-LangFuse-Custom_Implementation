import sqlite3
import chromadb
from datetime import datetime
from config import CHROMA_PATH, SQLITE_DB_PATH

_conn = None

def get_sqlite_conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _init_sqlite_db(_conn)
    return _conn


def _init_sqlite_db(conn):
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            display_name TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            title TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            document TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            session_id TEXT,
            prompt TEXT,
            response TEXT,
            rating TEXT NOT NULL DEFAULT 'good',
            created_at TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            username TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            feedback TEXT DEFAULT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    _ensure_feedback_rating_column(conn)
    _ensure_chat_feedback_column(conn)


def _ensure_feedback_rating_column(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(feedback)")
    columns = [row["name"] for row in cursor.fetchall()]
    if "rating" not in columns:
        try:
            cursor.execute("ALTER TABLE feedback ADD COLUMN rating TEXT NOT NULL DEFAULT 'good'")
            conn.commit()
        except Exception:
            pass


def _ensure_chat_feedback_column(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(chat_messages)")
    columns = [row["name"] for row in cursor.fetchall()]
    if "feedback" not in columns:
        try:
            cursor.execute("ALTER TABLE chat_messages ADD COLUMN feedback TEXT DEFAULT NULL")
            conn.commit()
        except Exception:
            pass


def get_user(username):
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    return cursor.fetchone()


def create_user(username, password, display_name=None):
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users(username, password, display_name) VALUES(?, ?, ?)",
        (username, password, display_name or username)
    )
    conn.commit()


def get_user_sessions(username):
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM sessions WHERE username = ? ORDER BY updated_at DESC",
        (username,)
    )
    return cursor.fetchall()


def get_session(session_id):
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
    return cursor.fetchone()


def save_session(session_id, username, document, title=None):
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    existing = get_session(session_id)
    timestamp = datetime.utcnow().isoformat()

    if existing:
        cursor.execute(
            "UPDATE sessions SET document = ?, title = ?, updated_at = ? WHERE session_id = ?",
            (document, title or existing["title"], timestamp, session_id)
        )
    else:
        cursor.execute(
            "INSERT INTO sessions(session_id, username, title, created_at, updated_at, document) VALUES(?, ?, ?, ?, ?, ?)",
            (session_id, username, title or "", timestamp, timestamp, document)
        )
    conn.commit()


def delete_user_sessions(username):
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM chat_messages WHERE session_id IN (SELECT session_id FROM sessions WHERE username = ?)",
        (username,)
    )
    cursor.execute("DELETE FROM sessions WHERE username = ?", (username,))
    conn.commit()


def get_session_messages(session_id):
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,)
    )
    return cursor.fetchall()


def get_last_chat_message(session_id, role="assistant"):
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM chat_messages WHERE session_id = ? AND role = ? ORDER BY id DESC LIMIT 1",
        (session_id, role)
    )
    return cursor.fetchone()


def update_chat_message_feedback(message_id, feedback):
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE chat_messages SET feedback = ? WHERE id = ?",
        (feedback, message_id)
    )
    conn.commit()


def save_chat_message(session_id, username, role, content, feedback=None):
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_messages(session_id, username, role, content, feedback, created_at) VALUES(?, ?, ?, ?, ?, ?)",
        (session_id, username, role, content, feedback, datetime.utcnow().isoformat())
    )
    conn.commit()


def save_feedback(feedback_id, username, session_id, prompt, response, rating="good"):
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO feedback(id, username, session_id, prompt, response, rating, created_at) VALUES(?, ?, ?, ?, ?, ?, ?)",
        (feedback_id, username, session_id, prompt, response, rating, datetime.utcnow().isoformat())
    )
    conn.commit()

# Chroma is used only for embedding persistence and retrieval of uploaded documents.
client = chromadb.PersistentClient(path=CHROMA_PATH)

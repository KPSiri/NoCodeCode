import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/memory.db")


def _get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    # User preferences — one row per user
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_memory (
            user_id     TEXT PRIMARY KEY,
            preferences TEXT NOT NULL DEFAULT '{}',
            updated_at  TEXT NOT NULL
        )
    """)

    # Every task ever run — full history log
    conn.execute("""
        CREATE TABLE IF NOT EXISTS task_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL,
            session_id  TEXT NOT NULL,
            task        TEXT NOT NULL,
            language    TEXT,
            success     INTEGER,
            created_at  TEXT NOT NULL
        )
    """)

    # Named chat sessions — each has a title and thread_id
    # thread_id links to LangGraph's SqliteSaver checkpoints
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id  TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL,
            title       TEXT NOT NULL,
            thread_id   TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        )
    """)

    # Full message history per session — every user message + agent reply
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            role        TEXT NOT NULL,
            content     TEXT NOT NULL,
            created_at  TEXT NOT NULL
        )
    """)

    conn.commit()
    return conn


# ── Preferences ────────────────────────────────────────────────────

def load_preferences(user_id: str) -> dict:
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT preferences FROM user_memory WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        if row is None:
            return {}
        return json.loads(row[0])
    finally:
        conn.close()


def save_preferences(user_id: str, preferences: dict) -> None:
    conn = _get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO user_memory (user_id, preferences, updated_at) VALUES (?, ?, ?)",
            (user_id, json.dumps(preferences), datetime.utcnow().isoformat())
        )
        conn.commit()
    finally:
        conn.close()


# ── Task history ───────────────────────────────────────────────────

def save_task(user_id: str, session_id: str, task: str, language: str, success: bool) -> None:
    conn = _get_connection()
    try:
        conn.execute(
            "INSERT INTO task_history (user_id, session_id, task, language, success, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, session_id, task, language, int(success), datetime.utcnow().isoformat())
        )
        conn.commit()
    finally:
        conn.close()


def load_recent_tasks(user_id: str, limit: int = 5) -> list:
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT task, language, success, created_at FROM task_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
        return [
            {"task": r[0], "language": r[1], "success": bool(r[2]), "at": r[3]}
            for r in rows
        ]
    finally:
        conn.close()


# ── Sessions ───────────────────────────────────────────────────────

def create_session(user_id: str, title: str, thread_id: str) -> str:
    """Create a new named session. Returns the session_id."""
    import uuid
    session_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    conn = _get_connection()
    try:
        conn.execute(
            "INSERT INTO sessions (session_id, user_id, title, thread_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, user_id, title, thread_id, now, now)
        )
        conn.commit()
    finally:
        conn.close()
    return session_id


def list_sessions(user_id: str) -> list:
    """Return all sessions for a user, newest first."""
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT session_id, title, thread_id, created_at, updated_at FROM sessions WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,)
        ).fetchall()
        return [
            {
                "session_id": r[0],
                "title":      r[1],
                "thread_id":  r[2],
                "created_at": r[3],
                "updated_at": r[4],
            }
            for r in rows
        ]
    finally:
        conn.close()


def get_session(session_id: str) -> dict | None:
    """Load a single session by ID. Returns None if not found."""
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT session_id, title, thread_id, created_at, updated_at FROM sessions WHERE session_id = ?",
            (session_id,)
        ).fetchone()
        if row is None:
            return None
        return {
            "session_id": row[0],
            "title":      row[1],
            "thread_id":  row[2],
            "created_at": row[3],
            "updated_at": row[4],
        }
    finally:
        conn.close()


def update_session_timestamp(session_id: str) -> None:
    """Bump updated_at so the session sorts to the top of the list."""
    conn = _get_connection()
    try:
        conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
            (datetime.utcnow().isoformat(), session_id)
        )
        conn.commit()
    finally:
        conn.close()


def delete_session(session_id: str) -> None:
    """Delete a session and all its chat history."""
    conn = _get_connection()
    try:
        conn.execute("DELETE FROM sessions     WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM task_history WHERE session_id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()


def rename_session(session_id: str, new_title: str) -> None:
    conn = _get_connection()
    try:
        conn.execute(
            "UPDATE sessions SET title = ?, updated_at = ? WHERE session_id = ?",
            (new_title, datetime.utcnow().isoformat(), session_id)
        )
        conn.commit()
    finally:
        conn.close()


# ── Chat history ───────────────────────────────────────────────────

def save_message(session_id: str, role: str, content: str) -> None:
    """
    Save one message to chat history.
    role is either 'user' or 'agent'.
    content is the text of the message.
    """
    conn = _get_connection()
    try:
        conn.execute(
            "INSERT INTO chat_history (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, datetime.utcnow().isoformat())
        )
        conn.commit()
    finally:
        conn.close()


def load_chat_history(session_id: str) -> list:
    """Return all messages in a session in chronological order."""
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT role, content, created_at FROM chat_history WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,)
        ).fetchall()
        return [
            {"role": r[0], "content": r[1], "at": r[2]}
            for r in rows
        ]
    finally:
        conn.close()
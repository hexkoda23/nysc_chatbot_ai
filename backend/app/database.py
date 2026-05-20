from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_database_path() -> Path:
    raw = os.getenv("DATABASE_URL", "sqlite:///./nysc_chatbot.db").strip()
    if raw.startswith("sqlite:///"):
        raw = raw.replace("sqlite:///", "", 1)
    elif raw.startswith("sqlite://"):
        raw = raw.replace("sqlite://", "", 1)

    path = Path(raw)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(get_database_path())
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                title TEXT
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                sources_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                rating TEXT NOT NULL CHECK (rating IN ('good', 'bad')),
                comment TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT NOT NULL UNIQUE,
                title TEXT,
                topic TEXT,
                source_url TEXT,
                last_checked TEXT,
                official INTEGER NOT NULL DEFAULT 0,
                checksum TEXT NOT NULL,
                indexed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS rag_chunks (
                id TEXT PRIMARY KEY,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                title TEXT,
                topic TEXT,
                filepath TEXT NOT NULL,
                source_url TEXT,
                last_checked TEXT,
                official INTEGER NOT NULL DEFAULT 0,
                checksum TEXT NOT NULL UNIQUE,
                metadata_json TEXT NOT NULL,
                indexed_at TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS eval_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                expected_topic TEXT,
                answer TEXT NOT NULL,
                passed INTEGER NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL
            );
            """
        )
        try:
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS rag_chunks_fts
                USING fts5(chunk_id UNINDEXED, content, title, topic, filepath);
                """
            )
        except sqlite3.OperationalError:
            # Some Python builds omit FTS5. Retrieval falls back to lexical scoring.
            pass


def upsert_conversation(conversation_id: str, title: Optional[str] = None) -> None:
    now = utc_now()
    clean_title = (title or "New conversation").strip()[:120]
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO conversations (id, created_at, updated_at, title)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                updated_at = excluded.updated_at,
                title = COALESCE(conversations.title, excluded.title)
            """,
            (conversation_id, now, now, clean_title),
        )


def insert_message(
    conversation_id: str,
    role: str,
    content: str,
    sources: Optional[Iterable[Dict[str, Any]]] = None,
    message_id: Optional[str] = None,
) -> str:
    import uuid

    msg_id = message_id or str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO messages (id, conversation_id, role, content, sources_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                msg_id,
                conversation_id,
                role,
                content,
                json.dumps(list(sources or []), ensure_ascii=False),
                utc_now(),
            ),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (utc_now(), conversation_id),
        )
    return msg_id


def insert_feedback(message_id: str, rating: str, comment: Optional[str]) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO feedback (message_id, rating, comment, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (message_id, rating, (comment or "").strip()[:1000], utc_now()),
        )
        return int(cur.lastrowid)


def insert_eval_result(
    question: str,
    expected_topic: str,
    answer: str,
    passed: bool,
    notes: str,
) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO eval_results (question, expected_topic, answer, passed, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (question, expected_topic, answer, 1 if passed else 0, notes, utc_now()),
        )
        return int(cur.lastrowid)


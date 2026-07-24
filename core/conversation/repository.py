"""SQLite persistence for JARVIS conversation sessions."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import Any

from core.conversation.contracts import ConversationMessage, ConversationRole, utc_now


class ConversationRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._lock, self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversation_sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    message_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    request_id TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    FOREIGN KEY(session_id) REFERENCES conversation_sessions(session_id)
                );
                CREATE INDEX IF NOT EXISTS idx_conversation_messages_session
                    ON conversation_messages(session_id, created_at);
                """
            )

    def ensure_session(self, session_id: str, metadata: dict[str, Any] | None = None) -> None:
        now = utc_now()
        encoded = json.dumps(metadata or {}, sort_keys=True)
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO conversation_sessions(session_id, created_at, updated_at, metadata_json)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET updated_at=excluded.updated_at
                """,
                (session_id, now, now, encoded),
            )

    def append(self, message: ConversationMessage) -> None:
        self.ensure_session(message.session_id)
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO conversation_messages(
                    message_id, session_id, role, content, created_at, request_id, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message.message_id,
                    message.session_id,
                    message.role.value,
                    message.content,
                    message.created_at,
                    message.request_id,
                    json.dumps(message.metadata, sort_keys=True),
                ),
            )
            connection.execute(
                "UPDATE conversation_sessions SET updated_at=? WHERE session_id=?",
                (message.created_at, message.session_id),
            )

    def messages(self, session_id: str, *, limit: int = 100) -> list[ConversationMessage]:
        bounded = max(1, min(int(limit), 500))
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM conversation_messages
                WHERE session_id=? ORDER BY created_at ASC LIMIT ?
                """,
                (session_id, bounded),
            ).fetchall()
        return [
            ConversationMessage(
                message_id=row["message_id"],
                session_id=row["session_id"],
                role=ConversationRole(row["role"]),
                content=row["content"],
                created_at=row["created_at"],
                request_id=row["request_id"],
                metadata=json.loads(row["metadata_json"] or "{}"),
            )
            for row in rows
        ]

    def session(self, session_id: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM conversation_sessions WHERE session_id=?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "session_id": row["session_id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "metadata": json.loads(row["metadata_json"] or "{}"),
        }

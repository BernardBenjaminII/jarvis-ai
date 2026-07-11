"""
Runtime database schema for controlled JARVIS knowledge assimilation.

Phase VI-B:
- retry accounting
- failure diagnostics
- append-only attempt journal

Phase VI-C:
- persistent missions
- persistent mission-item checkpoints
- pause and resume support

All migrations are idempotent and preserve existing catalog data.
"""

from __future__ import annotations

import sqlite3
from typing import Any


QUEUE_COLUMNS: dict[str, str] = {
    "attempt_count": "INTEGER NOT NULL DEFAULT 0",
    "max_attempts": "INTEGER NOT NULL DEFAULT 3",
    "last_error": "TEXT",
    "last_attempt_at": "TEXT",
    "completed_at": "TEXT",
}


def ensure_assimilation_runtime_schema(
    connection: sqlite3.Connection,
) -> None:
    """Ensure all Phase VI-B and VI-C assimilation tables and columns."""

    _ensure_queue_columns(connection)
    _ensure_attempt_schema(connection)
    _ensure_mission_schema(connection)


def queue_columns(connection: sqlite3.Connection) -> set[str]:
    """Return knowledge_assimilation_queue column names."""

    rows = connection.execute(
        'PRAGMA table_info("knowledge_assimilation_queue")'
    ).fetchall()

    return {str(row[1]) for row in rows}


def database_path_from(db: Any) -> str:
    """Resolve a useful database path from a KnowledgeDatabase object."""

    for attribute in (
        "path",
        "db_path",
        "database_path",
        "filename",
    ):
        value = getattr(db, attribute, None)

        if value is not None:
            return str(value)

    return "<configured KnowledgeDatabase>"


def _ensure_queue_columns(connection: sqlite3.Connection) -> None:
    existing = queue_columns(connection)

    for column_name, declaration in QUEUE_COLUMNS.items():
        if column_name in existing:
            continue

        quoted_name = _quote_identifier(column_name)

        connection.execute(
            f"""
            ALTER TABLE knowledge_assimilation_queue
            ADD COLUMN {quoted_name} {declaration}
            """
        )


def _ensure_attempt_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_assimilation_attempts (
            attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_uuid TEXT NOT NULL,
            object_path TEXT,
            object_type TEXT,
            handler_name TEXT NOT NULL,
            attempt_number INTEGER NOT NULL,
            attempt_state TEXT NOT NULL,
            started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            error_type TEXT,
            error_message TEXT,
            text_chars INTEGER,
            chunk_count INTEGER,
            checksum TEXT
        )
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_assimilation_attempts_object_uuid
        ON knowledge_assimilation_attempts (
            object_uuid,
            attempt_id
        )
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_assimilation_attempts_state
        ON knowledge_assimilation_attempts (
            attempt_state,
            started_at
        )
        """
    )


def _ensure_mission_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_assimilation_missions (
            mission_id TEXT PRIMARY KEY,
            fingerprint TEXT NOT NULL,
            mission_status TEXT NOT NULL,
            database_path TEXT NOT NULL,
            requested_limit INTEGER NOT NULL,
            requested_object_types_json TEXT NOT NULL,
            planning_notes_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            started_at TEXT,
            paused_at TEXT,
            completed_at TEXT,
            last_checkpoint_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            processed_count INTEGER NOT NULL DEFAULT 0,
            failed_count INTEGER NOT NULL DEFAULT 0,
            skipped_count INTEGER NOT NULL DEFAULT 0,
            blocked_count INTEGER NOT NULL DEFAULT 0,
            total_items INTEGER NOT NULL DEFAULT 0,
            mission_json TEXT NOT NULL,
            last_error TEXT
        )
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_assimilation_missions_status
        ON knowledge_assimilation_missions (
            mission_status,
            last_checkpoint_at
        )
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_assimilation_missions_created_at
        ON knowledge_assimilation_missions (
            created_at
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_assimilation_mission_items (
            mission_id TEXT NOT NULL,
            sequence INTEGER NOT NULL,
            object_uuid TEXT NOT NULL,
            object_path TEXT NOT NULL,
            object_type TEXT NOT NULL,
            handler_name TEXT NOT NULL,
            item_status TEXT NOT NULL,
            message TEXT,
            result_json TEXT,
            started_at TEXT,
            completed_at TEXT,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            item_json TEXT NOT NULL,
            PRIMARY KEY (mission_id, sequence),
            FOREIGN KEY (mission_id)
                REFERENCES knowledge_assimilation_missions(mission_id)
                ON DELETE CASCADE
        )
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_assimilation_mission_items_uuid
        ON knowledge_assimilation_mission_items (
            object_uuid,
            mission_id
        )
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_assimilation_mission_items_status
        ON knowledge_assimilation_mission_items (
            mission_id,
            item_status,
            sequence
        )
        """
    )


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'

from __future__ import annotations

import sqlite3


def init_validation(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_validation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_uuid TEXT NOT NULL UNIQUE,
            object_path TEXT NOT NULL,
            object_type TEXT NOT NULL,
            validation_state TEXT NOT NULL,
            score REAL NOT NULL,
            reason TEXT NOT NULL,
            validated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_validation_state
        ON knowledge_validation(validation_state)
        """
    )

    conn.commit()

from __future__ import annotations

import sqlite3


def init_queue(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_assimilation_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_uuid TEXT NOT NULL UNIQUE,
            object_path TEXT NOT NULL,
            object_type TEXT NOT NULL,
            priority INTEGER NOT NULL DEFAULT 50,
            queue_state TEXT NOT NULL,
            reason TEXT NOT NULL,
            queued_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_assimilation_queue_state
        ON knowledge_assimilation_queue(queue_state)
        """
    )

    conn.commit()

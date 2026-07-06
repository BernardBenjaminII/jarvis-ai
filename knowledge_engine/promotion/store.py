from __future__ import annotations
import sqlite3


def init_promotion(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS promotion_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_uuid TEXT NOT NULL,
            action TEXT NOT NULL,
            source_path TEXT NOT NULL,
            destination_path TEXT,
            reason TEXT NOT NULL,
            promoted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_promotion_history_object_uuid
        ON promotion_history(object_uuid)
    """)

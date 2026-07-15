"""
SQLite schema for durable acquisition missions.
"""

from __future__ import annotations

import sqlite3


def ensure_acquisition_mission_schema(
    conn: sqlite3.Connection,
) -> None:
    """Create acquisition mission tables and indexes idempotently."""

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS acquisition_missions (
            mission_id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL,
            provider_id TEXT NOT NULL,
            campaign_id TEXT,
            mission_state TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            item_count INTEGER NOT NULL
                CHECK (item_count >= 0),
            accepted_count INTEGER NOT NULL
                CHECK (accepted_count >= 0),
            review_count INTEGER NOT NULL
                CHECK (review_count >= 0),
            ignored_count INTEGER NOT NULL
                CHECK (ignored_count >= 0),
            rejected_count INTEGER NOT NULL
                CHECK (rejected_count >= 0),
            UNIQUE(request_id, provider_id, campaign_id)
        );

        CREATE INDEX IF NOT EXISTS
            idx_acquisition_missions_state
        ON acquisition_missions(mission_state);

        CREATE TABLE IF NOT EXISTS acquisition_mission_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            mission_id TEXT NOT NULL,
            item_order INTEGER NOT NULL
                CHECK (item_order >= 0),
            candidate_id TEXT NOT NULL,
            provider_id TEXT NOT NULL,
            source_uri TEXT NOT NULL,
            local_path TEXT NOT NULL,
            checksum_sha256 TEXT NOT NULL,
            item_state TEXT NOT NULL,
            decision_fingerprint TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(mission_id)
                REFERENCES acquisition_missions(mission_id)
                ON DELETE CASCADE,
            UNIQUE(mission_id, item_order),
            UNIQUE(mission_id, candidate_id)
        );

        CREATE INDEX IF NOT EXISTS
            idx_acquisition_mission_items_state
        ON acquisition_mission_items(
            mission_id,
            item_state
        );

        CREATE INDEX IF NOT EXISTS
            idx_acquisition_mission_items_candidate
        ON acquisition_mission_items(candidate_id);
        """
    )


__all__ = [
    "ensure_acquisition_mission_schema",
]

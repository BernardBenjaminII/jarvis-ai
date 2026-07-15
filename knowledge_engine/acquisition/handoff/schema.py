"""
SQLite schema for controlled assimilation handoffs.
"""

from __future__ import annotations

import sqlite3


def ensure_assimilation_handoff_schema(
    conn: sqlite3.Connection,
) -> None:
    """Create handoff tables and indexes idempotently."""

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS acquisition_assimilation_handoffs (
            handoff_id TEXT PRIMARY KEY,
            mission_id TEXT NOT NULL,
            mission_item_id INTEGER NOT NULL,
            candidate_id TEXT NOT NULL,
            provider_id TEXT NOT NULL,
            source_uri TEXT NOT NULL,
            local_path TEXT NOT NULL,
            checksum_sha256 TEXT NOT NULL,
            decision_fingerprint TEXT NOT NULL,
            handoff_state TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            dispatch_attempt_count INTEGER NOT NULL DEFAULT 0
                CHECK (dispatch_attempt_count >= 0),
            assimilation_reference TEXT,
            last_error TEXT,
            FOREIGN KEY(mission_id)
                REFERENCES acquisition_missions(mission_id)
                ON DELETE CASCADE,
            FOREIGN KEY(mission_item_id)
                REFERENCES acquisition_mission_items(item_id)
                ON DELETE CASCADE,
            UNIQUE(mission_id, mission_item_id),
            UNIQUE(mission_id, candidate_id)
        );

        CREATE INDEX IF NOT EXISTS
            idx_acquisition_handoffs_state
        ON acquisition_assimilation_handoffs(
            handoff_state,
            created_at
        );

        CREATE INDEX IF NOT EXISTS
            idx_acquisition_handoffs_mission
        ON acquisition_assimilation_handoffs(
            mission_id,
            mission_item_id
        );

        CREATE INDEX IF NOT EXISTS
            idx_acquisition_handoffs_candidate
        ON acquisition_assimilation_handoffs(candidate_id);
        """
    )


__all__ = [
    "ensure_assimilation_handoff_schema",
]

"""
SQLite schema for acquisition provenance persistence.
"""

from __future__ import annotations

import sqlite3


def ensure_provenance_schema(
    conn: sqlite3.Connection,
) -> None:
    """Create provenance tables and indexes idempotently."""

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS acquisition_provenance (
            candidate_id TEXT PRIMARY KEY,
            provider_id TEXT NOT NULL,
            source_uri TEXT NOT NULL,
            local_path TEXT NOT NULL,
            filename TEXT NOT NULL,
            checksum_sha256 TEXT NOT NULL,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            sighting_count INTEGER NOT NULL DEFAULT 1
                CHECK (sighting_count >= 1),
            last_action TEXT NOT NULL,
            last_decision_fingerprint TEXT NOT NULL,
            campaign_id TEXT,
            UNIQUE(provider_id, source_uri)
        );

        CREATE INDEX IF NOT EXISTS
            idx_acquisition_provenance_checksum
        ON acquisition_provenance(checksum_sha256);

        CREATE INDEX IF NOT EXISTS
            idx_acquisition_provenance_provider
        ON acquisition_provenance(provider_id);

        CREATE TABLE IF NOT EXISTS acquisition_admission_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id TEXT NOT NULL,
            seen_at TEXT NOT NULL,
            action TEXT NOT NULL,
            decision_fingerprint TEXT NOT NULL,
            decision_json TEXT NOT NULL,
            campaign_id TEXT,
            FOREIGN KEY(candidate_id)
                REFERENCES acquisition_provenance(candidate_id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS
            idx_acquisition_history_candidate
        ON acquisition_admission_history(
            candidate_id,
            history_id
        );

        CREATE INDEX IF NOT EXISTS
            idx_acquisition_history_fingerprint
        ON acquisition_admission_history(
            decision_fingerprint
        );
        """
    )


__all__ = [
    "ensure_provenance_schema",
]

from __future__ import annotations

import sqlite3

from knowledge_engine.registry.models import RegistryRecord


def init_registry(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_uuid TEXT NOT NULL UNIQUE,
            object_path TEXT NOT NULL UNIQUE,
            object_type TEXT NOT NULL,
            title TEXT,
            status TEXT NOT NULL,
            lifecycle_state TEXT NOT NULL,
            validation_state TEXT NOT NULL,
            assimilation_state TEXT NOT NULL,
            source TEXT,
            trust_level TEXT NOT NULL,
            duplicate_of TEXT,
            notes TEXT,
            registered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_registry_status
        ON knowledge_registry(status)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_registry_lifecycle
        ON knowledge_registry(lifecycle_state)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_registry_validation
        ON knowledge_registry(validation_state)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_registry_assimilation
        ON knowledge_registry(assimilation_state)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_registry_object_type
        ON knowledge_registry(object_type)
        """
    )

    conn.commit()


class KnowledgeRegistryStore:
    def __init__(self, db):
        self.db = db

    def initialize(self) -> None:
        with self.db.connect() as conn:
            init_registry(conn)

    def upsert(self, record: RegistryRecord) -> None:
        with self.db.connect() as conn:
            init_registry(conn)

            conn.execute(
                """
                INSERT INTO knowledge_registry (
                    object_uuid,
                    object_path,
                    object_type,
                    title,
                    status,
                    lifecycle_state,
                    validation_state,
                    assimilation_state,
                    source,
                    trust_level,
                    duplicate_of,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(object_path)
                DO UPDATE SET
                    object_uuid = excluded.object_uuid,
                    object_type = excluded.object_type,
                    title = excluded.title,
                    status = excluded.status,
                    lifecycle_state = excluded.lifecycle_state,
                    validation_state = excluded.validation_state,
                    assimilation_state = excluded.assimilation_state,
                    source = excluded.source,
                    trust_level = excluded.trust_level,
                    duplicate_of = excluded.duplicate_of,
                    notes = excluded.notes,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    record.object_uuid,
                    record.object_path,
                    record.object_type,
                    record.title,
                    record.status,
                    record.lifecycle_state,
                    record.validation_state,
                    record.assimilation_state,
                    record.source,
                    record.trust_level,
                    record.duplicate_of,
                    record.notes,
                ),
            )

            conn.commit()

    def summary(self) -> dict[str, int]:
        with self.db.connect() as conn:
            init_registry(conn)

            total = conn.execute(
                "SELECT COUNT(*) FROM knowledge_registry"
            ).fetchone()[0]

            return {
                "registry_records": total,
            }

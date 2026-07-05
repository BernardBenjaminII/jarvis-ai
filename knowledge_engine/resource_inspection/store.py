from __future__ import annotations

import sqlite3

from knowledge_engine.resource_inspection.models import ResourceInspection


def init_resource_inspection(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS resource_inspections (
            object_uuid TEXT PRIMARY KEY,
            object_path TEXT NOT NULL,
            object_type TEXT NOT NULL,
            title TEXT,
            description TEXT,
            language TEXT,
            primary_subject TEXT,
            keywords TEXT,
            metadata_json TEXT NOT NULL,
            status TEXT NOT NULL,
            error TEXT,
            inspected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(object_uuid) REFERENCES knowledge_objects(object_uuid)
        )
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_resource_inspections_type
        ON resource_inspections(object_type)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_resource_inspections_status
        ON resource_inspections(status)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_resource_inspections_subject
        ON resource_inspections(primary_subject)
        """
    )


class ResourceInspectionStore:
    def __init__(self, db):
        self.db = db

    def upsert(self, inspection: ResourceInspection) -> None:
        with self.db.connect() as conn:
            init_resource_inspection(conn)

            conn.execute(
                """
                INSERT INTO resource_inspections (
                    object_uuid,
                    object_path,
                    object_type,
                    title,
                    description,
                    language,
                    primary_subject,
                    keywords,
                    metadata_json,
                    status,
                    error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(object_uuid) DO UPDATE SET
                    object_path=excluded.object_path,
                    object_type=excluded.object_type,
                    title=excluded.title,
                    description=excluded.description,
                    language=excluded.language,
                    primary_subject=excluded.primary_subject,
                    keywords=excluded.keywords,
                    metadata_json=excluded.metadata_json,
                    status=excluded.status,
                    error=excluded.error,
                    inspected_at=CURRENT_TIMESTAMP
                """,
                (
                    inspection.object_uuid,
                    inspection.object_path,
                    inspection.object_type,
                    inspection.title,
                    inspection.description,
                    inspection.language,
                    inspection.primary_subject,
                    inspection.keywords,
                    inspection.metadata_json,
                    inspection.status,
                    inspection.error,
                ),
            )

            conn.commit()

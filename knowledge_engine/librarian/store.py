from __future__ import annotations

import sqlite3


def init_librarian(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS librarian_catalog (
            object_uuid TEXT PRIMARY KEY,
            object_path TEXT NOT NULL,
            object_type TEXT NOT NULL,
            canonical_title TEXT NOT NULL,
            display_title TEXT,
            subject TEXT,
            subject_confidence REAL NOT NULL DEFAULT 0,
            subject_reason TEXT,
            keywords TEXT,
            language TEXT,
            description TEXT,
            quality_score REAL NOT NULL DEFAULT 0,
            work_key TEXT NOT NULL,
            duplicate_group TEXT,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            cataloged_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(object_uuid) REFERENCES knowledge_objects(object_uuid)
        )
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_librarian_subject
        ON librarian_catalog(subject)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_librarian_object_type
        ON librarian_catalog(object_type)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_librarian_work_key
        ON librarian_catalog(work_key)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_librarian_quality
        ON librarian_catalog(quality_score)
        """
    )


def upsert_catalog_entry(
    conn: sqlite3.Connection,
    *,
    object_uuid: str,
    object_path: str,
    object_type: str,
    canonical_title: str,
    display_title: str | None,
    subject: str | None,
    subject_confidence: float,
    subject_reason: str,
    keywords: str | None,
    language: str | None,
    description: str | None,
    quality_score: float,
    work_key: str,
    duplicate_group: str | None,
    metadata_json: str,
) -> None:
    conn.execute(
        """
        INSERT INTO librarian_catalog (
            object_uuid,
            object_path,
            object_type,
            canonical_title,
            display_title,
            subject,
            subject_confidence,
            subject_reason,
            keywords,
            language,
            description,
            quality_score,
            work_key,
            duplicate_group,
            metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(object_uuid) DO UPDATE SET
            object_path=excluded.object_path,
            object_type=excluded.object_type,
            canonical_title=excluded.canonical_title,
            display_title=excluded.display_title,
            subject=excluded.subject,
            subject_confidence=excluded.subject_confidence,
            subject_reason=excluded.subject_reason,
            keywords=excluded.keywords,
            language=excluded.language,
            description=excluded.description,
            quality_score=excluded.quality_score,
            work_key=excluded.work_key,
            duplicate_group=excluded.duplicate_group,
            metadata_json=excluded.metadata_json,
            updated_at=CURRENT_TIMESTAMP
        """,
        (
            object_uuid,
            object_path,
            object_type,
            canonical_title,
            display_title,
            subject,
            subject_confidence,
            subject_reason,
            keywords,
            language,
            description,
            quality_score,
            work_key,
            duplicate_group,
            metadata_json,
        ),
    )

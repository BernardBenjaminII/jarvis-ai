from __future__ import annotations

import sqlite3
from pathlib import Path

from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.knowledge_catalog.database import migrate


def search_catalog(query: str, db_path: Path = DEFAULT_CATALOG_DB, limit: int = 25) -> list[sqlite3.Row]:
    migrate(db_path)
    q = f"%{query.lower()}%"

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            """
            SELECT DISTINCT
                ds.subject,
                ds.confidence,
                ds.assigned_by,
                ds.file_path
            FROM document_subjects ds
            WHERE lower(ds.subject) LIKE ?
               OR lower(ds.file_path) LIKE ?
            ORDER BY ds.confidence DESC, ds.file_path
            LIMIT ?
            """,
            (q, q, limit),
        ).fetchall()

from __future__ import annotations

import sqlite3
from pathlib import Path

from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.knowledge_catalog.schema import (
    SCHEMA_SQL,
    COLLECTIONS_SQL,
    CONCEPTS_SQL,
    INGESTION_SQL,
    STRUCTURE_SQL,
)


OPTIONAL_ALTERS = [
    "ALTER TABLE catalog_documents ADD COLUMN detected_type TEXT",
    "ALTER TABLE catalog_documents ADD COLUMN inspection_reason TEXT",
    "ALTER TABLE catalog_documents ADD COLUMN readable INTEGER DEFAULT 0",
    "ALTER TABLE catalog_documents ADD COLUMN content_chars INTEGER DEFAULT 0",
]


def connect(db_path: Path = DEFAULT_CATALOG_DB) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate(db_path: Path = DEFAULT_CATALOG_DB) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.executescript(COLLECTIONS_SQL)
        conn.executescript(CONCEPTS_SQL)
        conn.executescript(INGESTION_SQL)
        conn.executescript(STRUCTURE_SQL)

        for stmt in OPTIONAL_ALTERS:
            try:
                conn.execute(stmt)
            except sqlite3.OperationalError as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise

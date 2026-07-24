from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_CKO_DB = Path("/media/abdullah/JARVIS_RUNTIME_L/knowledge/cko.sqlite")

SCHEMA = """
CREATE TABLE IF NOT EXISTS knowledge_objects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cko_id TEXT NOT NULL UNIQUE,
    source TEXT NOT NULL,
    course TEXT,
    title TEXT NOT NULL,
    object_type TEXT NOT NULL DEFAULT 'resource',
    topic TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS representations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cko_id TEXT NOT NULL,
    representation_type TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    mime_guess TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(cko_id) REFERENCES knowledge_objects(cko_id)
);

CREATE INDEX IF NOT EXISTS idx_representations_cko ON representations(cko_id);
CREATE INDEX IF NOT EXISTS idx_representations_sha ON representations(sha256);
CREATE INDEX IF NOT EXISTS idx_cko_course ON knowledge_objects(course);
"""


def connect(db_path: Path = DEFAULT_CKO_DB) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def migrate(db_path: Path = DEFAULT_CKO_DB) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)

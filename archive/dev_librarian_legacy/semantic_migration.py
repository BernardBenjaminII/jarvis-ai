#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB = Path("/media/abdullah/JARVIS_RUNTIME_L/knowledge/librarian.sqlite")


SCHEMA = """
CREATE TABLE IF NOT EXISTS document_subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    sha256 TEXT,
    subject TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    assigned_by TEXT NOT NULL DEFAULT 'rule',
    assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_path, subject)
);

CREATE TABLE IF NOT EXISTS document_concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    sha256 TEXT,
    concept TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    assigned_by TEXT NOT NULL DEFAULT 'rule',
    assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_path, concept)
);

CREATE INDEX IF NOT EXISTS idx_document_subjects_subject
ON document_subjects(subject);

CREATE INDEX IF NOT EXISTS idx_document_subjects_sha256
ON document_subjects(sha256);

CREATE INDEX IF NOT EXISTS idx_document_concepts_concept
ON document_concepts(concept);
"""


def main() -> None:
    DEFAULT_DB.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DEFAULT_DB) as conn:
        conn.executescript(SCHEMA)

    print(f"[OK] Semantic catalog tables ready: {DEFAULT_DB}")


if __name__ == "__main__":
    main()

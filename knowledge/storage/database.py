from pathlib import Path
import sqlite3


class KnowledgeDatabase:
    def __init__(self, db_path: Path):
        self.db_path = db_path.expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self):
        return sqlite3.connect(self.db_path)

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL UNIQUE,
                    relative_path TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    extension TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    modified_time REAL NOT NULL,
                    sha256 TEXT NOT NULL,
                    category TEXT,
                    status TEXT NOT NULL,
                    first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_seen TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS inspections (
                    document_path TEXT PRIMARY KEY,
                    inspector TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metadata_json TEXT,
                    error TEXT,
                    inspected_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS document_structure (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_path TEXT NOT NULL,
                    title TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    page INTEGER,
                    order_index INTEGER NOT NULL,
                    parent_title TEXT,
                    source TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS document_text (
                    document_path TEXT PRIMARY KEY,
                    extractor TEXT NOT NULL,
                    text TEXT,
                    checksum TEXT,
                    status TEXT NOT NULL,
                    error TEXT,
                    extracted_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_path TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    source_page INTEGER,
                    structure_title TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS concepts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    document_path TEXT NOT NULL,
                    chunk_id INTEGER,
                    confidence REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_documents_sha256 ON documents(sha256);
                CREATE INDEX IF NOT EXISTS idx_documents_extension ON documents(extension);
                CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
                CREATE INDEX IF NOT EXISTS idx_structure_document ON document_structure(document_path);
                CREATE INDEX IF NOT EXISTS idx_structure_title ON document_structure(title);
                CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_path);
                CREATE INDEX IF NOT EXISTS idx_concepts_name ON concepts(name);
                """
            )

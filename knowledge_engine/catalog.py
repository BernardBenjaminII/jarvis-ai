from pathlib import Path
import sqlite3

from knowledge_engine.document import DocumentRecord


SCHEMA = """
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

CREATE INDEX IF NOT EXISTS idx_structure_document
ON document_structure(document_path);

CREATE INDEX IF NOT EXISTS idx_structure_title
ON document_structure(title);

CREATE INDEX IF NOT EXISTS idx_structure_level
ON document_structure(level);

CREATE INDEX IF NOT EXISTS idx_documents_sha256
ON documents(sha256);

CREATE INDEX IF NOT EXISTS idx_documents_extension
ON documents(extension);

CREATE INDEX IF NOT EXISTS idx_documents_category
ON documents(category);

CREATE INDEX IF NOT EXISTS idx_inspections_status
ON inspections(status);

CREATE INDEX IF NOT EXISTS idx_inspections_inspector
ON inspections(inspector);
"""


class KnowledgeCatalog:
    def __init__(self, db_path: Path):
        self.db_path = db_path.expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self):
        return sqlite3.connect(self.db_path)

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def upsert_document(self, doc: DocumentRecord) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO documents (
                    path,
                    relative_path,
                    filename,
                    extension,
                    size_bytes,
                    modified_time,
                    sha256,
                    category,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    relative_path = excluded.relative_path,
                    filename = excluded.filename,
                    extension = excluded.extension,
                    size_bytes = excluded.size_bytes,
                    modified_time = excluded.modified_time,
                    sha256 = excluded.sha256,
                    category = excluded.category,
                    status = excluded.status,
                    last_seen = CURRENT_TIMESTAMP
                """,
                (
                    str(doc.path),
                    doc.relative_path,
                    doc.filename,
                    doc.extension,
                    doc.size_bytes,
                    doc.modified_time,
                    doc.sha256,
                    doc.category,
                    doc.status,
                ),
            )

    def upsert_inspection(
        self,
        document_path: str,
        inspector: str,
        status: str,
        metadata_json: str | None = None,
        error: str | None = None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO inspections (
                    document_path,
                    inspector,
                    status,
                    metadata_json,
                    error
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(document_path) DO UPDATE SET
                    inspector = excluded.inspector,
                    status = excluded.status,
                    metadata_json = excluded.metadata_json,
                    error = excluded.error,
                    inspected_at = CURRENT_TIMESTAMP
                """,
                (
                    document_path,
                    inspector,
                    status,
                    metadata_json,
                    error,
                ),
            )

    def summary(self) -> dict:
        with self.connect() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM documents"
            ).fetchone()[0]

            by_extension = conn.execute(
                """
                SELECT extension, COUNT(*)
                FROM documents
                GROUP BY extension
                ORDER BY COUNT(*) DESC
                """
            ).fetchall()

            by_category = conn.execute(
                """
                SELECT COALESCE(category, 'uncategorized'), COUNT(*)
                FROM documents
                GROUP BY category
                ORDER BY COUNT(*) DESC
                """
            ).fetchall()

            duplicates = conn.execute(
                """
                SELECT sha256, COUNT(*)
                FROM documents
                GROUP BY sha256
                HAVING COUNT(*) > 1
                """
            ).fetchall()

            inspection_summary = conn.execute(
                """
                SELECT inspector, status, COUNT(*)
                FROM inspections
                GROUP BY inspector, status
                ORDER BY inspector, status
                """
            ).fetchall()

        return {
            "total": total,
            "by_extension": by_extension,
            "by_category": by_category,
            "duplicates": duplicates,
            "inspection_summary": inspection_summary,
        }

    def duplicate_groups(self) -> dict:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT sha256, path
                FROM documents
                ORDER BY sha256, path
                """
            ).fetchall()

        groups = {}

        for sha, path in rows:
            groups.setdefault(sha, []).append(path)

        return {
            sha: paths
            for sha, paths in groups.items()
            if len(paths) > 1
        }

    def replace_structure(self, document_path: str, nodes: list) -> None:
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM document_structure WHERE document_path = ?",
                (document_path,),
            )

            conn.executemany(
                """
                INSERT INTO document_structure (
                    document_path,
                    title,
                    level,
                    page,
                    order_index,
                    parent_title,
                    source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        node.document_path,
                        node.title,
                        node.level,
                        node.page,
                        node.order_index,
                        node.parent_title,
                        node.source,
                    )
                    for node in nodes
                ],
            )

    def structure_summary(self) -> list:
        with self.connect() as conn:
            return conn.execute(
                """
                SELECT source, COUNT(*)
                FROM document_structure
                GROUP BY source
                ORDER BY COUNT(*) DESC
                """
            ).fetchall()

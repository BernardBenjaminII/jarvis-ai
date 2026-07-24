from __future__ import annotations

import sqlite3

from core.knowledge_catalog.models import Document, FileAsset, Source, Topic, utc_now


class CatalogRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def upsert_source(self, source: Source) -> int:
        now = utc_now()
        self.conn.execute(
            """
            INSERT INTO sources (name, trust_tier, source_type, base_url, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                trust_tier=excluded.trust_tier,
                source_type=excluded.source_type,
                base_url=excluded.base_url,
                notes=excluded.notes,
                updated_at=excluded.updated_at
            """,
            (source.name, source.trust_tier, source.source_type, source.base_url, source.notes, now, now),
        )
        return self.conn.execute("SELECT id FROM sources WHERE name = ?", (source.name,)).fetchone()["id"]

    def upsert_topic(self, topic: Topic) -> int:
        now = utc_now()
        self.conn.execute(
            """
            INSERT INTO topics (path, name, parent_path, desired_depth, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                name=excluded.name,
                parent_path=excluded.parent_path,
                desired_depth=excluded.desired_depth,
                updated_at=excluded.updated_at
            """,
            (topic.path, topic.name, topic.parent_path, topic.desired_depth, now, now),
        )
        return self.conn.execute("SELECT id FROM topics WHERE path = ?", (topic.path,)).fetchone()["id"]

    def create_document(self, document: Document) -> int:
        now = utc_now()
        source_id = None
        if document.source_name:
            row = self.conn.execute("SELECT id FROM sources WHERE name = ?", (document.source_name,)).fetchone()
            if row:
                source_id = row["id"]

        cur = self.conn.execute(
            """
            INSERT INTO documents (
                title, document_type, language, publication_year, edition,
                source_id, trust_score, quality_score, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document.title,
                document.document_type,
                document.language,
                document.publication_year,
                document.edition,
                source_id,
                document.trust_score,
                document.quality_score,
                now,
                now,
            ),
        )
        return int(cur.lastrowid)

    def add_file_asset(self, asset: FileAsset) -> int:
        now = utc_now()
        self.conn.execute(
            """
            INSERT INTO file_assets (
                document_id, file_path, sha256, size_bytes, extension,
                verification_status, verification_message, magic_type,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_path) DO UPDATE SET
                document_id=excluded.document_id,
                sha256=excluded.sha256,
                size_bytes=excluded.size_bytes,
                extension=excluded.extension,
                verification_status=excluded.verification_status,
                verification_message=excluded.verification_message,
                magic_type=excluded.magic_type,
                updated_at=excluded.updated_at
            """,
            (
                asset.document_id,
                str(asset.file_path),
                asset.sha256,
                asset.size_bytes,
                asset.extension,
                asset.verification_status,
                asset.verification_message,
                asset.magic_type,
                now,
                now,
            ),
        )
        return self.conn.execute("SELECT id FROM file_assets WHERE file_path = ?", (str(asset.file_path),)).fetchone()["id"]

    def link_document_topic(self, document_id: int, topic_path: str, confidence: float = 1.0) -> None:
        now = utc_now()
        row = self.conn.execute("SELECT id FROM topics WHERE path = ?", (topic_path,)).fetchone()
        if not row:
            raise ValueError(f"Topic does not exist: {topic_path}")
        topic_id = row["id"]

        self.conn.execute(
            """
            INSERT OR REPLACE INTO document_topics (document_id, topic_id, confidence, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (document_id, topic_id, confidence, now),
        )

    def stats(self) -> dict[str, int]:
        return {
            "sources": self.conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0],
            "topics": self.conn.execute("SELECT COUNT(*) FROM topics").fetchone()[0],
            "documents": self.conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
            "file_assets": self.conn.execute("SELECT COUNT(*) FROM file_assets").fetchone()[0],
        }

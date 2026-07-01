from knowledge_engine.document import DocumentRecord


class CatalogStore:
    def __init__(self, db):
        self.db = db

    def upsert_document(self, doc: DocumentRecord) -> None:
        with self.db.connect() as conn:
            conn.execute(
                """
                INSERT INTO documents (
                    path, relative_path, filename, extension,
                    size_bytes, modified_time, sha256, category, status
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

    def summary(self) -> dict:
        with self.db.connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]

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

        return {
            "total": total,
            "by_extension": by_extension,
            "by_category": by_category,
        }

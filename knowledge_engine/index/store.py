from knowledge_engine.index.models import IndexRecord


class KnowledgeIndexStore:
    def __init__(self, db):
        self.db = db

    def upsert(self, record: IndexRecord) -> None:
        with self.db.connect() as conn:
            conn.execute(
                """
                INSERT INTO knowledge_index (
                    document_path,
                    filename,
                    extension,
                    category,
                    title,
                    author,
                    subject,
                    keywords,
                    pages,
                    toc_entries,
                    structure_terms,
                    language,
                    fingerprint
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_path) DO UPDATE SET
                    filename = excluded.filename,
                    extension = excluded.extension,
                    category = excluded.category,
                    title = excluded.title,
                    author = excluded.author,
                    subject = excluded.subject,
                    keywords = excluded.keywords,
                    pages = excluded.pages,
                    toc_entries = excluded.toc_entries,
                    structure_terms = excluded.structure_terms,
                    language = excluded.language,
                    fingerprint = excluded.fingerprint,
                    indexed_at = CURRENT_TIMESTAMP
                """,
                (
                    record.document_path,
                    record.filename,
                    record.extension,
                    record.category,
                    record.title,
                    record.author,
                    record.subject,
                    record.keywords,
                    record.pages,
                    record.toc_entries,
                    record.structure_terms,
                    record.language,
                    record.fingerprint,
                ),
            )

    def summary(self) -> dict:
        with self.db.connect() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM knowledge_index"
            ).fetchone()[0]

            with_toc = conn.execute(
                """
                SELECT COUNT(*)
                FROM knowledge_index
                WHERE toc_entries > 0
                """
            ).fetchone()[0]

        return {
            "index_total": total,
            "index_with_toc": with_toc,
        }

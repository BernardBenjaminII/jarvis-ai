class TextStore:
    def __init__(self, db):
        self.db = db

    def upsert(self, document_path, extractor, text, checksum, status, error=None):
        with self.db.connect() as conn:
            conn.execute(
                """
                INSERT INTO document_text (
                    document_path, extractor, text, checksum, status, error
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_path) DO UPDATE SET
                    extractor = excluded.extractor,
                    text = excluded.text,
                    checksum = excluded.checksum,
                    status = excluded.status,
                    error = excluded.error,
                    extracted_at = CURRENT_TIMESTAMP
                """,
                (document_path, extractor, text, checksum, status, error),
            )

class InspectionStore:
    def __init__(self, db):
        self.db = db

    def upsert(self, document_path, inspector, status, metadata_json=None, error=None):
        with self.db.connect() as conn:
            conn.execute(
                """
                INSERT INTO inspections (
                    document_path, inspector, status, metadata_json, error
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(document_path) DO UPDATE SET
                    inspector = excluded.inspector,
                    status = excluded.status,
                    metadata_json = excluded.metadata_json,
                    error = excluded.error,
                    inspected_at = CURRENT_TIMESTAMP
                """,
                (document_path, inspector, status, metadata_json, error),
            )

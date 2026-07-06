from __future__ import annotations

from pathlib import Path


class ObjectAssimilationStage:
    def __init__(self, db):
        self.db = db

    def run_one(self) -> dict:
        with self.db.connect() as conn:
            row = conn.execute(
                """
                SELECT object_uuid, object_path, object_type
                FROM knowledge_assimilation_queue
                WHERE queue_state='queued'
                  AND object_type='single_document'
                ORDER BY priority DESC, queued_at ASC
                LIMIT 1
                """
            ).fetchone()

            if row is None:
                return {"processed": 0, "message": "no queued single_document object found"}

            object_uuid = row["object_uuid"]
            object_path = row["object_path"]
            path = Path(object_path)

            stat = path.stat()

            conn.execute(
                """
                INSERT INTO catalog_documents (
                    file_path,
                    filename,
                    extension,
                    size_bytes,
                    modified_time,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_path) DO UPDATE SET
                    filename=excluded.filename,
                    extension=excluded.extension,
                    size_bytes=excluded.size_bytes,
                    modified_time=excluded.modified_time,
                    status=excluded.status
                """,
                (
                    str(path),
                    path.name,
                    path.suffix.lower(),
                    stat.st_size,
                    stat.st_mtime,
                    "registered_from_knowledge_object",
                ),
            )

            conn.execute(
                """
                INSERT INTO document_assimilation (
                    file_path,
                    subject,
                    status
                )
                VALUES (?, ?, ?)
                ON CONFLICT(file_path) DO UPDATE SET
                    subject=excluded.subject,
                    status=excluded.status
                """,
                (
                    str(path),
                    "knowledge_object",
                    "queued",
                ),
            )

            conn.execute(
                """
                UPDATE knowledge_assimilation_queue
                SET queue_state='completed',
                    updated_at=CURRENT_TIMESTAMP
                WHERE object_uuid=?
                """,
                (object_uuid,),
            )

            conn.execute(
                """
                UPDATE knowledge_registry
                SET lifecycle_state='assimilation_queued',
                    assimilation_state='cataloged',
                    updated_at=CURRENT_TIMESTAMP
                WHERE object_uuid=?
                """,
                (object_uuid,),
            )

            conn.commit()

        return {
            "processed": 1,
            "object_uuid": object_uuid,
            "file_path": str(path),
        }

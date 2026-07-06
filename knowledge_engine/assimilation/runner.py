from __future__ import annotations

from pathlib import Path

from knowledge_engine.assimilation.single_document import (
    checksum,
    chunk_text,
    read_text,
)


class AssimilationRunner:
    def __init__(self, db):
        self.db = db

    def run_one_single_document(self) -> dict:
        with self.db.connect() as conn:
            row = conn.execute(
                """
                SELECT object_uuid, object_path, object_type
                FROM knowledge_registry
                WHERE lifecycle_state='queued'
                  AND assimilation_state='queued'
                  AND object_type='single_document'
                ORDER BY updated_at ASC
                LIMIT 1
                """
            ).fetchone()

            if row is None:
                return {
                    "processed": 0,
                    "message": "no queued single_document object found",
                }

            object_uuid = row["object_uuid"]
            document_path = row["object_path"]
            path = Path(document_path)

            conn.execute(
                """
                UPDATE knowledge_registry
                SET lifecycle_state='extracting',
                    assimilation_state='processing',
                    updated_at=CURRENT_TIMESTAMP
                WHERE object_uuid=?
                """,
                (object_uuid,),
            )

            conn.execute(
                """
                UPDATE knowledge_assimilation_queue
                SET queue_state='processing',
                    updated_at=CURRENT_TIMESTAMP
                WHERE object_uuid=?
                """,
                (object_uuid,),
            )

            text = read_text(path)
            text_checksum = checksum(text)

            conn.execute(
                """
                INSERT INTO document_text (
                    document_path,
                    extractor,
                    text,
                    checksum,
                    status,
                    error
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_path) DO UPDATE SET
                    extractor=excluded.extractor,
                    text=excluded.text,
                    checksum=excluded.checksum,
                    status=excluded.status,
                    error=excluded.error,
                    extracted_at=CURRENT_TIMESTAMP
                """,
                (
                    document_path,
                    "single_document_assimilation",
                    text,
                    text_checksum,
                    "extracted",
                    None,
                ),
            )

            conn.execute(
                """
                DELETE FROM chunks
                WHERE document_path=?
                """,
                (document_path,),
            )

            chunks = chunk_text(text)

            for index, chunk in enumerate(chunks):
                conn.execute(
                    """
                    INSERT INTO chunks (
                        document_path,
                        chunk_index,
                        text,
                        source_page,
                        structure_title
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        document_path,
                        index,
                        chunk,
                        None,
                        None,
                    ),
                )

            conn.execute(
                """
                UPDATE knowledge_registry
                SET lifecycle_state='chunked',
                    assimilation_state='chunked',
                    updated_at=CURRENT_TIMESTAMP
                WHERE object_uuid=?
                """,
                (object_uuid,),
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

            conn.commit()

        return {
            "processed": 1,
            "object_uuid": object_uuid,
            "document_path": document_path,
            "text_chars": len(text),
            "chunks": len(chunks),
        }

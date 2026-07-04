from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from knowledge_engine.chunking.models import DocumentChunk
from knowledge_engine.chunking.store import DocumentChunkStore
from knowledge_engine.chunking.strategies import chunk_text


class DocumentChunkBuilder:
    def __init__(self, db):
        self.db = db
        self.store = DocumentChunkStore(db)

    def build_ready_documents(self, limit: int = 5) -> dict:
        built = 0
        documents = 0
        errors: list[tuple[str, str]] = []

        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT kr.object_uuid,
                       dt.file_path,
                       dt.text
                FROM knowledge_registry kr
                JOIN catalog_documents cd
                  ON cd.file_path = kr.object_path
                     OR cd.file_path LIKE kr.object_path || '/%'
                JOIN document_text dt
                  ON dt.file_path = cd.file_path
                WHERE kr.assimilation_state='ready_for_chunking'
                  AND dt.status='processed'
                  AND dt.content_chars > 0
                ORDER BY kr.updated_at ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        for row in rows:
            try:
                file_path = row["file_path"]
                text = row["text"] or ""

                raw_chunks = chunk_text(text)
                chunks = [
                    self._make_chunk(file_path, i, chunk)
                    for i, chunk in enumerate(raw_chunks)
                ]

                count = self.store.replace_chunks(file_path, chunks)

                with self.db.connect() as conn:
                    conn.execute(
                        """
                        UPDATE knowledge_registry
                        SET lifecycle_state='chunked',
                            assimilation_state='ready_for_embedding',
                            updated_at=?
                        WHERE object_uuid=?
                        """,
                        (
                            datetime.now(timezone.utc).isoformat(),
                            row["object_uuid"],
                        ),
                    )
                    conn.commit()

                built += count
                documents += 1

            except Exception as exc:
                errors.append((row["file_path"], str(exc)))

        return {
            "documents_chunked": documents,
            "chunks_built": built,
            "chunk_errors": errors,
        }

    def _make_chunk(self, file_path: str, index: int, text: str) -> DocumentChunk:
        checksum = hashlib.sha256(
            text.encode("utf-8", errors="ignore")
        ).hexdigest()

        chunk_uuid = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"{file_path}:{index}:{checksum}",
            )
        )

        return DocumentChunk(
            chunk_uuid=chunk_uuid,
            file_path=file_path,
            chunk_index=index,
            chunk_type="paragraph_window",
            heading=None,
            text=text,
            char_count=len(text),
            checksum=checksum,
            embedding_state="not_embedded",
        )

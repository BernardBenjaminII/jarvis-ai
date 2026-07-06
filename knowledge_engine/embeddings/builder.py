from __future__ import annotations

from knowledge_engine.embeddings.models import ChunkEmbedding
from knowledge_engine.embeddings.provider import LocalEmbeddingProvider
from knowledge_engine.embeddings.store import ChunkEmbeddingStore, init_embeddings


class ChunkEmbeddingBuilder:
    def __init__(self, db, provider: LocalEmbeddingProvider | None = None):
        self.db = db
        self.provider = provider or LocalEmbeddingProvider()
        self.store = ChunkEmbeddingStore(db)

    def build_pending_embeddings(
        self,
        limit: int = 25,
        min_chars: int = 200,
    ) -> dict:
        embedded = 0
        skipped = 0
        errors: list[tuple[str, str]] = []

        with self.db.connect() as conn:
            init_embeddings(conn)

            rows = conn.execute(
                """
                SELECT chunk_uuid,
                       file_path,
                       chunk_index,
                       text,
                       char_count
                FROM document_chunks
                WHERE embedding_state='not_embedded'
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        for row in rows:
            try:
                chunk_uuid = row["chunk_uuid"]
                text = row["text"] or ""
                char_count = int(row["char_count"] or 0)

                if char_count < min_chars:
                    self._mark_skipped(chunk_uuid)
                    skipped += 1
                    continue

                vector = self.provider.embed(text)

                embedding = ChunkEmbedding(
                    chunk_uuid=chunk_uuid,
                    provider=self.provider.provider_name,
                    model=self.provider.model_name,
                    dimensions=self.provider.dimensions,
                    vector=vector,
                )

                self.store.upsert_embedding(embedding)
                embedded += 1

            except Exception as exc:
                errors.append((row["chunk_uuid"], str(exc)))

        self._advance_ready_documents()

        return {
            "chunks_embedded": embedded,
            "chunks_skipped": skipped,
            "embedding_errors": errors,
        }

    def _mark_skipped(self, chunk_uuid: str) -> None:
        with self.db.connect() as conn:
            conn.execute(
                """
                UPDATE document_chunks
                SET embedding_state='skipped_too_small'
                WHERE chunk_uuid=?
                """,
                (chunk_uuid,),
            )
            conn.commit()

    def _advance_ready_documents(self) -> None:
        """
        Move registry objects from ready_for_embedding to embedded
        only when all chunks for that file are no longer not_embedded.
        """

        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT kr.object_uuid,
                       kr.object_path
                FROM knowledge_registry kr
                WHERE kr.assimilation_state='ready_for_embedding'
                """
            ).fetchall()

            for row in rows:
                object_uuid = row["object_uuid"]
                object_path = row["object_path"]

                pending = conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM document_chunks
                    WHERE file_path = ?
                      AND embedding_state='not_embedded'
                    """,
                    (object_path,),
                ).fetchone()[0]

                if pending == 0:
                    conn.execute(
                        """
                        UPDATE knowledge_registry
                        SET lifecycle_state='embedded',
                            assimilation_state='ready_for_concepts',
                            updated_at=CURRENT_TIMESTAMP
                        WHERE object_uuid=?
                        """,
                        (object_uuid,),
                    )

            conn.commit()

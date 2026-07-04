from __future__ import annotations

import json
import sqlite3

from knowledge_engine.embeddings.models import ChunkEmbedding


def init_embeddings(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chunk_embeddings (
            chunk_uuid TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            dimensions INTEGER NOT NULL,
            vector_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(chunk_uuid) REFERENCES document_chunks(chunk_uuid)
        )
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_provider_model
        ON chunk_embeddings(provider, model)
        """
    )


class ChunkEmbeddingStore:
    def __init__(self, db):
        self.db = db

    def upsert_embedding(self, embedding: ChunkEmbedding) -> None:
        with self.db.connect() as conn:
            init_embeddings(conn)

            conn.execute(
                """
                INSERT INTO chunk_embeddings (
                    chunk_uuid,
                    provider,
                    model,
                    dimensions,
                    vector_json
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(chunk_uuid) DO UPDATE SET
                    provider=excluded.provider,
                    model=excluded.model,
                    dimensions=excluded.dimensions,
                    vector_json=excluded.vector_json
                """,
                (
                    embedding.chunk_uuid,
                    embedding.provider,
                    embedding.model,
                    embedding.dimensions,
                    json.dumps(embedding.vector),
                ),
            )

            conn.execute(
                """
                UPDATE document_chunks
                SET embedding_state='embedded'
                WHERE chunk_uuid=?
                """,
                (embedding.chunk_uuid,),
            )

            conn.commit()

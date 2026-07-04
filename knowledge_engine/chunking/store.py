from __future__ import annotations

import sqlite3

from knowledge_engine.chunking.models import DocumentChunk


def init_chunks(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS document_chunks(
            chunk_uuid TEXT PRIMARY KEY,
            file_path TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            chunk_type TEXT NOT NULL,
            heading TEXT,
            text TEXT NOT NULL,
            char_count INTEGER NOT NULL,
            checksum TEXT NOT NULL,
            embedding_state TEXT NOT NULL DEFAULT 'not_embedded',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(file_path, chunk_index)
        )
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_document_chunks_file_path
        ON document_chunks(file_path)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_state
        ON document_chunks(embedding_state)
        """
    )


class DocumentChunkStore:
    def __init__(self, db):
        self.db = db

    def replace_chunks(self, file_path: str, chunks: list[DocumentChunk]) -> int:
        with self.db.connect() as conn:
            init_chunks(conn)

            conn.execute(
                "DELETE FROM document_chunks WHERE file_path=?",
                (file_path,),
            )

            for chunk in chunks:
                conn.execute(
                    """
                    INSERT INTO document_chunks(
                        chunk_uuid,
                        file_path,
                        chunk_index,
                        chunk_type,
                        heading,
                        text,
                        char_count,
                        checksum,
                        embedding_state
                    )
                    VALUES(?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        chunk.chunk_uuid,
                        chunk.file_path,
                        chunk.chunk_index,
                        chunk.chunk_type,
                        chunk.heading,
                        chunk.text,
                        chunk.char_count,
                        chunk.checksum,
                        chunk.embedding_state,
                    ),
                )

            conn.commit()

        return len(chunks)

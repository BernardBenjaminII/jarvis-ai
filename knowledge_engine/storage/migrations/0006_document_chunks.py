TABLES = ["document_chunks"]


def up(conn):
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

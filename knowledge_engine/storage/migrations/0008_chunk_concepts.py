TABLES = ["chunk_concepts"]


def up(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chunk_concepts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chunk_uuid TEXT NOT NULL,
            file_path TEXT NOT NULL,
            concept TEXT NOT NULL,
            concept_type TEXT NOT NULL,
            domain TEXT,
            confidence REAL NOT NULL,
            evidence TEXT,
            extractor TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(chunk_uuid, concept, concept_type)
        )
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chunk_concepts_chunk
        ON chunk_concepts(chunk_uuid)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chunk_concepts_concept
        ON chunk_concepts(concept)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chunk_concepts_domain
        ON chunk_concepts(domain)
        """
    )

    conn.execute(
        """
        ALTER TABLE document_chunks
        ADD COLUMN concept_state TEXT DEFAULT 'not_extracted'
        """
    )

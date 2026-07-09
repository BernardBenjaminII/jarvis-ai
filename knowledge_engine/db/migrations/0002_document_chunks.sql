CREATE TABLE IF NOT EXISTS document_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    source_path TEXT NOT NULL,
    text TEXT NOT NULL,
    text_hash TEXT NOT NULL,
    char_start INTEGER,
    char_end INTEGER,
    page_start INTEGER,
    page_end INTEGER,
    heading TEXT,
    parent_section TEXT,
    token_estimate INTEGER,
    embedding_status TEXT NOT NULL DEFAULT 'pending',
    semantic_status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(document_id, chunk_index),
    UNIQUE(document_id, text_hash)
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id
ON document_chunks(document_id);

CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_status
ON document_chunks(embedding_status);

CREATE INDEX IF NOT EXISTS idx_document_chunks_semantic_status
ON document_chunks(semantic_status);

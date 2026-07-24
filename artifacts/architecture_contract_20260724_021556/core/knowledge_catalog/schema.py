SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    trust_tier INTEGER NOT NULL DEFAULT 2,
    source_type TEXT NOT NULL DEFAULT 'unknown',
    base_url TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    parent_path TEXT,
    desired_depth TEXT NOT NULL DEFAULT 'medium',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    document_type TEXT NOT NULL DEFAULT 'unknown',
    language TEXT NOT NULL DEFAULT 'unknown',
    publication_year INTEGER,
    edition TEXT,
    source_id INTEGER,
    trust_score INTEGER NOT NULL DEFAULT 50,
    quality_score INTEGER NOT NULL DEFAULT 50,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(source_id) REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS file_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    extension TEXT NOT NULL,
    verification_status TEXT NOT NULL DEFAULT 'unknown',
    verification_message TEXT,
    magic_type TEXT,
    ingested INTEGER NOT NULL DEFAULT 0,
    embedded INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(document_id) REFERENCES documents(id)
);

CREATE TABLE IF NOT EXISTS document_topics (
    document_id INTEGER NOT NULL,
    topic_id INTEGER NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    PRIMARY KEY(document_id, topic_id),
    FOREIGN KEY(document_id) REFERENCES documents(id),
    FOREIGN KEY(topic_id) REFERENCES topics(id)
);

CREATE TABLE IF NOT EXISTS document_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_document_id INTEGER NOT NULL,
    to_document_id INTEGER NOT NULL,
    relationship_type TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(from_document_id) REFERENCES documents(id),
    FOREIGN KEY(to_document_id) REFERENCES documents(id)
);

CREATE INDEX IF NOT EXISTS idx_file_assets_sha256 ON file_assets(sha256);
CREATE INDEX IF NOT EXISTS idx_documents_title ON documents(title);
CREATE INDEX IF NOT EXISTS idx_topics_path ON topics(path);
"""

COLLECTIONS_SQL = """
CREATE TABLE IF NOT EXISTS collections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    collection_type TEXT NOT NULL DEFAULT 'knowledge',
    domain TEXT,
    discipline TEXT,
    subject TEXT,
    description TEXT,
    authority_score REAL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS collection_documents (
    collection_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    sha256 TEXT,
    confidence REAL NOT NULL DEFAULT 1.0,
    assigned_by TEXT NOT NULL DEFAULT 'rule',
    created_at TEXT NOT NULL,
    PRIMARY KEY(collection_id, file_path)
);

CREATE TABLE IF NOT EXISTS document_subjects (
    file_path TEXT NOT NULL,
    sha256 TEXT,
    subject TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    assigned_by TEXT NOT NULL DEFAULT 'rule',
    created_at TEXT NOT NULL,
    PRIMARY KEY(file_path, subject)
);

CREATE INDEX IF NOT EXISTS idx_document_subjects_subject
ON document_subjects(subject);

CREATE INDEX IF NOT EXISTS idx_collection_documents_collection
ON collection_documents(collection_id);
"""

CONCEPTS_SQL = """
CREATE TABLE IF NOT EXISTS document_concepts (
    file_path TEXT NOT NULL,
    sha256 TEXT,
    concept TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    assigned_by TEXT NOT NULL DEFAULT 'rule',
    created_at TEXT NOT NULL,
    PRIMARY KEY(file_path, concept)
);

CREATE INDEX IF NOT EXISTS idx_document_concepts_concept
ON document_concepts(concept);
"""

INGESTION_SQL = """
CREATE TABLE IF NOT EXISTS catalog_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    sha256 TEXT NOT NULL,
    title TEXT,
    file_type TEXT,
    size_bytes INTEGER,
    source_name TEXT,
    collection_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS document_keywords (
    file_path TEXT NOT NULL,
    keyword TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    assigned_by TEXT NOT NULL DEFAULT 'rule',
    created_at TEXT NOT NULL,
    PRIMARY KEY(file_path, keyword)
);

CREATE INDEX IF NOT EXISTS idx_catalog_documents_sha256
ON catalog_documents(sha256);

CREATE INDEX IF NOT EXISTS idx_catalog_documents_collection
ON catalog_documents(collection_id);

CREATE INDEX IF NOT EXISTS idx_document_keywords_keyword
ON document_keywords(keyword);
"""

INSPECTION_SQL = """
ALTER TABLE catalog_documents ADD COLUMN detected_type TEXT;
ALTER TABLE catalog_documents ADD COLUMN inspection_reason TEXT;
ALTER TABLE catalog_documents ADD COLUMN readable INTEGER DEFAULT 0;
ALTER TABLE catalog_documents ADD COLUMN content_chars INTEGER DEFAULT 0;
"""

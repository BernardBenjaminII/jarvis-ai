from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS chunk_identity_bridge(
    runtime_chunk_id INTEGER PRIMARY KEY,
    runtime_document_id INTEGER NOT NULL,
    chunk_uuid TEXT NOT NULL UNIQUE,
    content_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chunk_identity_document
ON chunk_identity_bridge(runtime_document_id);

CREATE TABLE IF NOT EXISTS semantic_vectors(
    runtime_chunk_id INTEGER PRIMARY KEY,
    chunk_uuid TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    dimensions INTEGER NOT NULL,
    vector_blob BLOB NOT NULL,
    vector_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(runtime_chunk_id) REFERENCES chunk_identity_bridge(runtime_chunk_id)
);

CREATE INDEX IF NOT EXISTS idx_semantic_vectors_model
ON semantic_vectors(provider, model);

CREATE TABLE IF NOT EXISTS embedding_campaign(
    runtime_chunk_id INTEGER PRIMARY KEY,
    stage TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    detail TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_embedding_campaign_stage
ON embedding_campaign(stage);

CREATE TABLE IF NOT EXISTS semantic_runs(
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    selected INTEGER NOT NULL DEFAULT 0,
    complete INTEGER NOT NULL DEFAULT 0,
    failed INTEGER NOT NULL DEFAULT 0
);
"""

def now():
    return datetime.now(timezone.utc).isoformat()

class SemanticStore:
    def __init__(self, path: Path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(self.path) as c:
            c.executescript(SCHEMA)
            c.commit()

    def connect(self):
        c=sqlite3.connect(self.path,timeout=30.0)
        c.row_factory=sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        c.execute("PRAGMA busy_timeout=30000")
        return c

    def counts(self):
        with self.connect() as c:
            return {
                "bridge_rows":int(c.execute("SELECT COUNT(*) FROM chunk_identity_bridge").fetchone()[0]),
                "vector_rows":int(c.execute("SELECT COUNT(*) FROM semantic_vectors").fetchone()[0]),
                "campaign_rows":int(c.execute("SELECT COUNT(*) FROM embedding_campaign").fetchone()[0]),
                "stage_counts":{
                    str(r["stage"]):int(r["n"])
                    for r in c.execute("SELECT stage,COUNT(*) n FROM embedding_campaign GROUP BY stage")
                },
            }

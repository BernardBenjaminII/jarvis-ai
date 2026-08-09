import sqlite3
from pathlib import Path
def ensure_context_schema(path:Path):
    c=sqlite3.connect(path,timeout=30)
    try:
        c.execute("""CREATE TABLE IF NOT EXISTS semantic_fragments(
          fragment_uuid TEXT PRIMARY KEY,
          runtime_chunk_id INTEGER NOT NULL,
          fragment_index INTEGER NOT NULL,
          start_char INTEGER NOT NULL,
          end_char INTEGER NOT NULL,
          fragment_text TEXT NOT NULL,
          fragment_sha256 TEXT NOT NULL,
          stage TEXT NOT NULL DEFAULT 'PENDING',
          attempts INTEGER NOT NULL DEFAULT 0,
          detail TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          UNIQUE(runtime_chunk_id,fragment_index))""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_semantic_fragments_chunk ON semantic_fragments(runtime_chunk_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_semantic_fragments_stage ON semantic_fragments(stage)")
        c.execute("""CREATE TABLE IF NOT EXISTS semantic_fragment_vectors(
          fragment_uuid TEXT PRIMARY KEY,
          runtime_chunk_id INTEGER NOT NULL,
          fragment_index INTEGER NOT NULL,
          provider TEXT NOT NULL,
          model TEXT NOT NULL,
          dimensions INTEGER NOT NULL,
          vector_blob BLOB NOT NULL,
          vector_sha256 TEXT NOT NULL,
          created_at TEXT NOT NULL)""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_semantic_fragment_vectors_chunk ON semantic_fragment_vectors(runtime_chunk_id)")
        c.commit()
    finally:c.close()

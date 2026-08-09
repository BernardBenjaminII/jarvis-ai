from __future__ import annotations
import sqlite3
from pathlib import Path

def _table_sql(c):
    row=c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='semantic_fragments'").fetchone()
    return row[0] if row else ""

def migrate_fragment_schema(path: Path):
    """
    Rebuild semantic_fragments so recursive identity is keyed by fragment_path,
    not by the legacy UNIQUE(runtime_chunk_id, fragment_index) constraint.
    """
    c=sqlite3.connect(path,timeout=30.0)
    c.row_factory=sqlite3.Row
    try:
        sql=_table_sql(c)
        if "UNIQUE(runtime_chunk_id,fragment_index)" not in sql.replace(" ",""):
            c.execute("""CREATE UNIQUE INDEX IF NOT EXISTS uq_semantic_fragments_chunk_path
                         ON semantic_fragments(runtime_chunk_id,fragment_path)""")
            c.commit()
            return {"rebuilt":False}

        c.execute("PRAGMA foreign_keys=OFF")
        c.execute("BEGIN IMMEDIATE")
        c.execute("""CREATE TABLE semantic_fragments_v3(
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
            parent_fragment_uuid TEXT,
            fragment_depth INTEGER NOT NULL DEFAULT 0,
            fragment_path TEXT NOT NULL DEFAULT '',
            is_leaf INTEGER NOT NULL DEFAULT 1,
            UNIQUE(runtime_chunk_id,fragment_path)
        )""")
        c.execute("""INSERT INTO semantic_fragments_v3(
            fragment_uuid,runtime_chunk_id,fragment_index,start_char,end_char,
            fragment_text,fragment_sha256,stage,attempts,detail,created_at,updated_at,
            parent_fragment_uuid,fragment_depth,fragment_path,is_leaf)
            SELECT fragment_uuid,runtime_chunk_id,fragment_index,start_char,end_char,
                   fragment_text,fragment_sha256,stage,attempts,detail,created_at,updated_at,
                   parent_fragment_uuid,fragment_depth,
                   CASE WHEN fragment_path='' OR fragment_path IS NULL
                        THEN CAST(fragment_index AS TEXT) ELSE fragment_path END,
                   is_leaf
            FROM semantic_fragments""")
        c.execute("DROP TABLE semantic_fragments")
        c.execute("ALTER TABLE semantic_fragments_v3 RENAME TO semantic_fragments")
        c.execute("CREATE INDEX idx_semantic_fragments_chunk ON semantic_fragments(runtime_chunk_id)")
        c.execute("CREATE INDEX idx_semantic_fragments_stage ON semantic_fragments(stage)")
        c.execute("CREATE INDEX idx_semantic_fragments_parent ON semantic_fragments(parent_fragment_uuid)")
        c.execute("CREATE INDEX idx_semantic_fragments_leaf_stage ON semantic_fragments(is_leaf,stage)")
        c.execute("COMMIT")
        c.execute("PRAGMA foreign_keys=ON")
        return {"rebuilt":True}
    except Exception:
        try:c.execute("ROLLBACK")
        except Exception:pass
        raise
    finally:
        c.close()

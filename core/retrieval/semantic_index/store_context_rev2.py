from __future__ import annotations
import sqlite3
from pathlib import Path

def ensure_rev2_schema(path:Path):
    c=sqlite3.connect(path,timeout=30); c.row_factory=sqlite3.Row
    try:
        cols={r['name'] for r in c.execute('PRAGMA table_info(semantic_fragments)')}
        for name,ddl in [('parent_fragment_uuid','TEXT'),('fragment_depth','INTEGER NOT NULL DEFAULT 0'),('fragment_path',"TEXT NOT NULL DEFAULT ''"),('is_leaf','INTEGER NOT NULL DEFAULT 1')]:
            if name not in cols: c.execute(f'ALTER TABLE semantic_fragments ADD COLUMN {name} {ddl}')
        c.execute('CREATE INDEX IF NOT EXISTS idx_semantic_fragments_parent ON semantic_fragments(parent_fragment_uuid)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_semantic_fragments_leaf_stage ON semantic_fragments(is_leaf,stage)')
        c.execute("""UPDATE semantic_fragments SET fragment_depth=COALESCE(fragment_depth,0),
                     fragment_path=CASE WHEN fragment_path='' OR fragment_path IS NULL THEN CAST(fragment_index AS TEXT) ELSE fragment_path END,
                     is_leaf=COALESCE(is_leaf,1) WHERE parent_fragment_uuid IS NULL""")
        c.commit()
    finally: c.close()

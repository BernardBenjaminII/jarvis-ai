import sqlite3
from pathlib import Path

def ensure_reliability_schema(path:Path):
    c=sqlite3.connect(path,timeout=30); c.row_factory=sqlite3.Row
    try:
        cols={r["name"] for r in c.execute("PRAGMA table_info(embedding_campaign)")}
        for name,ddl in [
            ("failure_class","TEXT NOT NULL DEFAULT ''"),
            ("http_status","INTEGER"),
            ("provider_error","TEXT NOT NULL DEFAULT ''"),
            ("last_batch_size","INTEGER NOT NULL DEFAULT 0"),
        ]:
            if name not in cols: c.execute(f"ALTER TABLE embedding_campaign ADD COLUMN {name} {ddl}")
        c.execute("""CREATE TABLE IF NOT EXISTS embedding_failures(
          id INTEGER PRIMARY KEY AUTOINCREMENT,occurred_at TEXT NOT NULL,
          runtime_chunk_id INTEGER,batch_size INTEGER NOT NULL,attempt INTEGER NOT NULL,
          classification TEXT NOT NULL,http_status INTEGER,detail TEXT NOT NULL,provider_error TEXT NOT NULL)""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_embedding_failures_chunk ON embedding_failures(runtime_chunk_id)")
        c.commit()
    finally:c.close()

def retry_first_ids(path:Path,limit:int):
    c=sqlite3.connect(path,timeout=30); c.row_factory=sqlite3.Row
    try:
        retry=[int(r["runtime_chunk_id"]) for r in c.execute(
          "SELECT runtime_chunk_id FROM embedding_campaign WHERE stage='RETRY' ORDER BY runtime_chunk_id LIMIT ?",(limit,))]
        remain=max(0,limit-len(retry))
        pending=[int(r["runtime_chunk_id"]) for r in c.execute(
          "SELECT runtime_chunk_id FROM embedding_campaign WHERE stage='PENDING' ORDER BY runtime_chunk_id LIMIT ?",(remain,))] if remain else []
        return retry+pending
    finally:c.close()

from __future__ import annotations
import sqlite3
from pathlib import Path

def conn(path:Path):
    c=sqlite3.connect(path,timeout=30.0)
    c.row_factory=sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=30000")
    return c

def has_path(path:Path,file_path:str):
    c=conn(path)
    try:return c.execute("SELECT 1 FROM runtime_documents WHERE file_path=?",(file_path,)).fetchone() is not None
    finally:c.close()

def remove_path(path:Path,file_path:str):
    c=conn(path)
    try:
        c.execute("BEGIN IMMEDIATE")
        row=c.execute("SELECT id FROM runtime_documents WHERE file_path=?",(file_path,)).fetchone()
        if row is None:
            c.rollback(); return {"removed":False,"documents":0,"chunks":0,"fts":0}
        did=int(row["id"])
        chunk_ids=[int(r["id"]) for r in c.execute("SELECT id FROM runtime_chunks WHERE document_id=?",(did,))]
        fts=0
        for cid in chunk_ids:
            c.execute("DELETE FROM runtime_chunks_fts WHERE CAST(chunk_id AS INTEGER)=?",(cid,))
            fts+=int(c.execute("SELECT changes()").fetchone()[0])
        c.execute("DELETE FROM runtime_chunks WHERE document_id=?",(did,))
        chunks=int(c.execute("SELECT changes()").fetchone()[0])
        c.execute("DELETE FROM runtime_documents WHERE id=?",(did,))
        docs=int(c.execute("SELECT changes()").fetchone()[0])
        c.commit()
        return {"removed":bool(docs),"documents":docs,"chunks":chunks,"fts":fts}
    except Exception:
        c.rollback(); raise
    finally:c.close()

def integrity(path:Path):
    c=conn(path)
    try:
        ic=str(c.execute("PRAGMA integrity_check").fetchone()[0])
        docs=int(c.execute("SELECT COUNT(*) FROM runtime_documents").fetchone()[0])
        chunks=int(c.execute("SELECT COUNT(*) FROM runtime_chunks").fetchone()[0])
        fts=int(c.execute("SELECT COUNT(*) FROM runtime_chunks_fts").fetchone()[0])
        dup=int(c.execute("""SELECT COUNT(*) FROM (
          SELECT file_path FROM runtime_documents GROUP BY file_path HAVING COUNT(*)>1)""").fetchone()[0])
        orphan=int(c.execute("""SELECT COUNT(*) FROM runtime_chunks c
          LEFT JOIN runtime_documents d ON d.id=c.document_id WHERE d.id IS NULL""").fetchone()[0])
        return {"integrity_check":ic,"runtime_documents":docs,"runtime_chunks":chunks,
                "runtime_chunks_fts":fts,"chunk_fts_parity":chunks==fts,
                "duplicate_runtime_paths":dup,"orphan_chunks":orphan}
    finally:c.close()

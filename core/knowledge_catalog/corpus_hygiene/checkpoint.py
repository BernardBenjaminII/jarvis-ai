from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

def now():
    return datetime.now(timezone.utc).isoformat()

def connect(path: Path):
    c=sqlite3.connect(path,timeout=30.0)
    c.row_factory=sqlite3.Row
    c.execute("PRAGMA busy_timeout=30000")
    return c

def failed_items(path: Path):
    c=connect(path)
    try:
        return list(c.execute("""SELECT candidate_id,path,title,category,extension,sha256,stage,detail,attempts
                                 FROM items WHERE stage='FAILED' ORDER BY candidate_id"""))
    finally:c.close()

def stage_counts(path: Path):
    c=connect(path)
    try:
        return {str(r["stage"]):int(r["n"]) for r in c.execute("SELECT stage,COUNT(*) n FROM items GROUP BY stage")}
    finally:c.close()

def set_stage(path: Path,candidate_id:str,stage:str,detail:str):
    c=connect(path)
    try:
        c.execute("BEGIN IMMEDIATE")
        c.execute("UPDATE items SET stage=?,detail=?,updated_at=? WHERE candidate_id=?",
                  (stage,detail,now(),candidate_id))
        c.execute("""INSERT INTO events(occurred_at,candidate_id,event_type,stage,detail)
                     VALUES(?,?,?,?,?)""",
                  (now(),candidate_id,"X_A2_2_TERMINAL_DISPOSITION",stage,detail))
        c.commit()
    except Exception:
        c.rollback(); raise
    finally:c.close()

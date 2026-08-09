from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
SCHEMA="""CREATE TABLE IF NOT EXISTS actions(
 id INTEGER PRIMARY KEY AUTOINCREMENT,occurred_at TEXT NOT NULL,candidate_id TEXT,
 path TEXT NOT NULL,action TEXT NOT NULL,classification TEXT NOT NULL,detail TEXT NOT NULL);"""
def now():return datetime.now(timezone.utc).isoformat()
class HygieneStore:
    def __init__(self,path:Path):
        self.path=path; path.parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(path) as c:c.executescript(SCHEMA);c.commit()
    def record(self,**kw):
        with sqlite3.connect(self.path) as c:
            c.execute("INSERT INTO actions(occurred_at,candidate_id,path,action,classification,detail) VALUES(?,?,?,?,?,?)",
                      (now(),kw.get("candidate_id"),kw["path"],kw["action"],kw["classification"],kw["detail"]))
            c.commit()
    def counts(self):
        with sqlite3.connect(self.path) as c:
            return dict(c.execute("SELECT classification,COUNT(*) FROM actions GROUP BY classification").fetchall())

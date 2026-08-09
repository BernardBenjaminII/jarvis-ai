from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS recovery_runs(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 started_at TEXT NOT NULL,
 completed_at TEXT,
 command TEXT NOT NULL,
 dry_run INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS candidate_recovery(
 candidate_id TEXT PRIMARY KEY,
 path TEXT NOT NULL,
 original_detail TEXT NOT NULL,
 strategy TEXT NOT NULL,
 status TEXT NOT NULL,
 detail TEXT NOT NULL,
 chars INTEGER NOT NULL DEFAULT 0,
 pages_total INTEGER NOT NULL DEFAULT 0,
 pages_attempted INTEGER NOT NULL DEFAULT 0,
 pages_recovered INTEGER NOT NULL DEFAULT 0,
 quality_score REAL NOT NULL DEFAULT 0,
 updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_candidate_recovery_status
ON candidate_recovery(status);
"""

def now():
    return datetime.now(timezone.utc).isoformat()

class OCRRecoveryStore:
    def __init__(self,path:Path):
        self.path=path
        path.parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(path) as c:
            c.executescript(SCHEMA); c.commit()

    def record(self,candidate,result):
        with sqlite3.connect(self.path) as c:
            c.execute("""
            INSERT INTO candidate_recovery(
              candidate_id,path,original_detail,strategy,status,detail,chars,
              pages_total,pages_attempted,pages_recovered,quality_score,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(candidate_id) DO UPDATE SET
              path=excluded.path,
              original_detail=excluded.original_detail,
              strategy=excluded.strategy,
              status=excluded.status,
              detail=excluded.detail,
              chars=excluded.chars,
              pages_total=excluded.pages_total,
              pages_attempted=excluded.pages_attempted,
              pages_recovered=excluded.pages_recovered,
              quality_score=excluded.quality_score,
              updated_at=excluded.updated_at
            """,(
              candidate.candidate_id,candidate.path,candidate.detail,result.strategy,
              result.status,result.detail,result.chars,result.pages_total,
              result.pages_attempted,result.pages_recovered,result.quality_score,now()
            ))
            c.commit()

    def counts(self):
        with sqlite3.connect(self.path) as c:
            return dict(c.execute(
                "SELECT status,COUNT(*) FROM candidate_recovery GROUP BY status"
            ).fetchall())

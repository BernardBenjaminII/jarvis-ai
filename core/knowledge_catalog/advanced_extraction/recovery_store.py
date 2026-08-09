import sqlite3
from datetime import datetime,timezone
from pathlib import Path
SCHEMA="CREATE TABLE IF NOT EXISTS recoveries(candidate_id TEXT PRIMARY KEY,path TEXT,original_detail TEXT,strategy TEXT,recovery_status TEXT,recovery_detail TEXT,chars INTEGER,pages INTEGER,updated_at TEXT)"
class RecoveryStore:
 def __init__(self,p):self.path=Path(p);self.path.parent.mkdir(parents=True,exist_ok=True);c=sqlite3.connect(self.path);c.execute(SCHEMA);c.commit();c.close()
 def record(self,c,o):
  db=sqlite3.connect(self.path);db.execute("INSERT OR REPLACE INTO recoveries VALUES(?,?,?,?,?,?,?,?,?)",(c.candidate_id,c.path,c.detail,o.strategy,o.status,o.detail,o.chars,o.pages,datetime.now(timezone.utc).isoformat()));db.commit();db.close()
 def counts(self):
  db=sqlite3.connect(self.path);d=dict(db.execute("SELECT recovery_status,COUNT(*) FROM recoveries GROUP BY recovery_status"));db.close();return d

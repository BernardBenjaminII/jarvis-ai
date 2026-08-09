import sqlite3
from pathlib import Path
from .models import FailedCandidate
def _ro(p):
 c=sqlite3.connect(f"file:{Path(p).resolve()}?mode=ro",uri=True,timeout=30); c.row_factory=sqlite3.Row; c.execute("PRAGMA busy_timeout=30000"); return c
def failed_candidates(p):
 c=_ro(p)
 try:
  rows=c.execute("SELECT candidate_id,path,title,category,extension,sha256,detail,attempts FROM items WHERE stage='FAILED' ORDER BY candidate_id").fetchall()
  return tuple(FailedCandidate(str(r['candidate_id']),str(r['path']),str(r['title']),r['category'],str(r['extension']).lower(),r['sha256'],str(r['detail'] or ''),int(r['attempts'] or 0)) for r in rows)
 finally:c.close()
def stage_counts(p):
 c=_ro(p)
 try:return {str(r[0]):int(r[1]) for r in c.execute("SELECT stage,COUNT(*) FROM items GROUP BY stage")}
 finally:c.close()

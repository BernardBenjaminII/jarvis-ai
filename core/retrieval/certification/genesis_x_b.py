from __future__ import annotations
import sqlite3,time,statistics
from dataclasses import dataclass,asdict
from pathlib import Path
DEFAULT_DB=Path("/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite")
BENCHMARKS=[
 ("exact_phrase",'"incident response"'),
 ("technical","python memory management"),
 ("medical","ANCA vasculitis kidney"),
 ("strategy","urban warfare doctrine"),
 ("security","NIST incident response"),
 ("language","Arabic grammar"),
]
@dataclass
class QueryResult:
 category:str; query:str; hits:int; unique_documents:int; latency_ms:float; top_results:list
def ro(db):
 c=sqlite3.connect(f"file:{Path(db).resolve()}?mode=ro",uri=True,timeout=30); c.row_factory=sqlite3.Row; return c
def counts(db):
 with ro(db) as c:
  return {n:c.execute(f"SELECT COUNT(*) FROM {n}").fetchone()[0] for n in ("runtime_documents","runtime_chunks","runtime_chunks_fts")}
def audit(db):
 x=counts(db)
 with ro(db) as c:
  integ=c.execute("PRAGMA integrity_check").fetchone()[0]
  dup=c.execute("SELECT COUNT(*) FROM (SELECT file_path FROM runtime_documents GROUP BY file_path HAVING COUNT(*)>1)").fetchone()[0]
  orphan=c.execute("SELECT COUNT(*) FROM runtime_chunks c LEFT JOIN runtime_documents d ON d.id=c.document_id WHERE d.id IS NULL").fetchone()[0]
  empty=c.execute("SELECT COUNT(*) FROM runtime_chunks WHERE trim(chunk_text)=''").fetchone()[0]
  no_chunks=c.execute("SELECT COUNT(*) FROM runtime_documents d LEFT JOIN runtime_chunks c ON c.document_id=d.id WHERE c.id IS NULL").fetchone()[0]
  fts=c.execute("SELECT sql FROM sqlite_master WHERE name='runtime_chunks_fts'").fetchone()
 return {"runtime_counts":x,"checks":{"sqlite_integrity_ok":integ=="ok","chunk_fts_parity":x["runtime_chunks"]==x["runtime_chunks_fts"],"no_duplicate_runtime_paths":dup==0,"no_orphan_chunks":orphan==0},"quality":{"empty_chunks":empty,"documents_without_chunks":no_chunks},"fts_definition":fts[0] if fts else None}
def search(db,q,limit=10):
 t=time.perf_counter()
 with ro(db) as c:
  rows=c.execute("""SELECT document_id,chunk_id,title,file_path,bm25(runtime_chunks_fts) rank,
  snippet(runtime_chunks_fts,0,'[',']',' … ',24) excerpt
  FROM runtime_chunks_fts WHERE runtime_chunks_fts MATCH ? ORDER BY rank LIMIT ?""",(q,limit)).fetchall()
 return (time.perf_counter()-t)*1000,[dict(r) for r in rows]
def benchmark(db,limit=10):
 out=[]
 for cat,q in BENCHMARKS:
  try:
   ms,r=search(db,q,limit); out.append(QueryResult(cat,q,len(r),len({str(x["document_id"]) for x in r}),round(ms,2),r))
  except sqlite3.Error as e: out.append(QueryResult(cat,q,0,0,0,[{"error":f"{type(e).__name__}: {e}"}]))
 return out
def certify(db):
 a=audit(db); b=benchmark(db); lat=[x.latency_ms for x in b if x.latency_ms]
 checks=dict(a["checks"])
 checks["benchmark_queries_execute"]=all(not(x.top_results and "error" in x.top_results[0]) for x in b)
 checks["all_benchmark_queries_return_results"]=all(x.hits>0 for x in b)
 return {"status":"EXCELLENT" if all(checks.values()) else "REVIEW_REQUIRED","checks":checks,"runtime_counts":a["runtime_counts"],"benchmark":{"queries":len(b),"median_latency_ms":round(statistics.median(lat),2) if lat else None,"max_latency_ms":max(lat) if lat else None,"results":[asdict(x) for x in b]}}

from __future__ import annotations
import os, sqlite3
from collections import Counter
from pathlib import Path
TRANSIENT=("database is locked","unable to open database file","resource temporarily unavailable","timeout","timed out")
CORRUPT=("invalid pdf header","eof marker not found","cannot find /root","malformed","corrupt","xref")
UNSUPPORTED=("unsupported","not implemented","unknown format")
NO_TEXT=("no usable text","produced no usable text","chunker produced no chunks")
def open_ro(p):
 c=sqlite3.connect(f"file:{Path(p).resolve()}?mode=ro",uri=True,timeout=30); c.row_factory=sqlite3.Row; c.execute("PRAGMA busy_timeout=30000"); return c
def classify(detail):
 t=(detail or '').casefold()
 if any(x in t for x in TRANSIENT): return 'TRANSIENT_RETRYABLE'
 if any(x in t for x in CORRUPT): return 'CORRUPT_OR_MALFORMED'
 if any(x in t for x in UNSUPPORTED): return 'UNSUPPORTED_OR_EXTRACTOR_GAP'
 if any(x in t for x in NO_TEXT): return 'NO_EXTRACTABLE_TEXT'
 if 'permission' in t:return 'PERMISSION_OR_ACCESS'
 if 'no such file' in t or 'not found' in t:return 'MISSING_SOURCE'
 return 'UNKNOWN_REQUIRES_REVIEW'
def run(runtime,checkpoint,preexisting=69):
 with open_ro(checkpoint) as c:
  rows=[dict(r) for r in c.execute("SELECT candidate_id,path,title,category,extension,stage,detail,attempts,extraction_seconds,write_seconds FROM items ORDER BY candidate_id")]
 stages=Counter(r['stage'] for r in rows); failures=[r for r in rows if r['stage']=='FAILED']
 with open_ro(runtime) as c:
  integ=c.execute('PRAGMA integrity_check').fetchone()[0]
  docs=c.execute('SELECT COUNT(*) FROM runtime_documents').fetchone()[0]
  chunks=c.execute('SELECT COUNT(*) FROM runtime_chunks').fetchone()[0]
  fts=c.execute('SELECT COUNT(*) FROM runtime_chunks_fts').fetchone()[0]
  dup=c.execute("SELECT COUNT(*) FROM (SELECT file_path FROM runtime_documents GROUP BY file_path HAVING COUNT(*)>1)").fetchone()[0]
  orphan_chunks=c.execute("SELECT COUNT(*) FROM runtime_chunks c LEFT JOIN runtime_documents d ON d.id=c.document_id WHERE d.id IS NULL").fetchone()[0]
  orphan_fts=c.execute("SELECT COUNT(*) FROM runtime_chunks_fts f LEFT JOIN runtime_chunks c ON CAST(f.chunk_id AS INTEGER)=c.id WHERE c.id IS NULL").fetchone()[0]
  runtime_paths={r[0] for r in c.execute('SELECT file_path FROM runtime_documents')}
 detailed=[]; classes=Counter(); exts=Counter(); disp=Counter(); failed_in_runtime=0
 for r in failures:
  p=Path(r['path']); state={'exists':p.exists(),'regular_file':p.is_file(),'readable':os.access(p,os.R_OK) if p.exists() else False,'size_bytes':p.stat().st_size if p.is_file() else None}
  cl=classify(r['detail']); ext=p.suffix.casefold() or '<none>'; classes[cl]+=1; exts[ext]+=1
  if r['path'] in runtime_paths: failed_in_runtime+=1
  if cl=='TRANSIENT_RETRYABLE' and state['exists'] and state['readable']: d='RETRY'
  elif cl in {'CORRUPT_OR_MALFORMED','NO_EXTRACTABLE_TEXT','UNSUPPORTED_OR_EXTRACTOR_GAP'}: d='QUARANTINE_OR_REPAIR'
  elif not state['exists']: d='MISSING_SOURCE_REVIEW'
  elif not state['readable']: d='ACCESS_REPAIR'
  else:d='MANUAL_REVIEW'
  disp[d]+=1; detailed.append({**r,'classification':cl,'recommended_disposition':d,'file_state':state,'already_in_runtime':r['path'] in runtime_paths,'extension':ext})
 registered=sum(stages.values()); complete=stages.get('COMPLETE',0); failed=stages.get('FAILED',0); pending=registered-complete-failed
 delta=docs-(complete+preexisting)
 checks={'no_pending_candidates':pending==0,'sqlite_integrity_ok':str(integ).lower()=='ok','chunk_fts_parity':chunks==fts,'no_duplicate_runtime_paths':dup==0,'no_orphan_chunks':orphan_chunks==0,'no_orphan_fts_rows':orphan_fts==0,'runtime_document_reconciliation':delta==0,'failed_not_present_in_runtime':failed_in_runtime==0}
 bad=[k for k,v in checks.items() if not v]
 return {'status':'EXCELLENT' if not bad else 'FAILED','classification':'MATERIALIZATION_COMPLETE_WITH_ISOLATED_EXCEPTIONS' if not bad else 'MATERIALIZATION_COMPLETION_INTEGRITY_EXCEPTION','checkpoint':{'registered_total':registered,'complete':complete,'failed':failed,'pending':pending,'completion_rate_percent':complete/registered*100 if registered else 0,'stage_counts':dict(sorted(stages.items()))},'runtime':{'integrity_check':integ,'counts':{'runtime_documents':docs,'runtime_chunks':chunks,'runtime_chunks_fts':fts},'duplicate_runtime_paths':dup,'orphan_chunks':orphan_chunks,'orphan_fts_rows':orphan_fts,'chunk_fts_equal':chunks==fts},'reconciliation':{'expected_preexisting_runtime_documents':preexisting,'expected_runtime_documents':complete+preexisting,'actual_runtime_documents':docs,'runtime_document_delta':delta,'failed_present_in_runtime':failed_in_runtime},'failure_summary':{'total':len(detailed),'by_classification':dict(sorted(classes.items())),'by_extension':dict(sorted(exts.items())),'by_disposition':dict(sorted(disp.items()))},'failures':detailed,'checks':checks,'failed_checks':bad}

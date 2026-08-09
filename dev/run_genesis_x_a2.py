import argparse,json,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from dev.runtime import bootstrap_runtime
R=bootstrap_runtime(Path(__file__));PROJECT_ROOT=R.project_root
from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.knowledge_catalog.advanced_extraction.checkpoint import failed_candidates,stage_counts
from core.knowledge_catalog.advanced_extraction.extractor import AdvancedExtractor
from core.knowledge_catalog.advanced_extraction.recovery import RecoveryService
from core.knowledge_catalog.advanced_extraction.recovery_store import RecoveryStore
def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=('audit','recover','status','certify'));p.add_argument('--runtime-catalog',type=Path,default=DEFAULT_CATALOG_DB);p.add_argument('--checkpoint-db',type=Path,default=PROJECT_ROOT/'.runtime/materialization/genesis_x_a1_engine.sqlite');p.add_argument('--recovery-db',type=Path,default=PROJECT_ROOT/'.runtime/materialization/genesis_x_a2_recovery.sqlite');p.add_argument('--report-dir',type=Path,default=PROJECT_ROOT/'docs/audits/genesis_x_a2');p.add_argument('--limit',type=int);p.add_argument('--dry-run',action='store_true');p.add_argument('--writer-batch-size',type=int,default=10);a=p.parse_args();cands=failed_candidates(a.checkpoint_db);a.report_dir.mkdir(parents=True,exist_ok=True)
 if a.command=='status':print(json.dumps({'stage_counts':stage_counts(a.checkpoint_db),'remaining_failed':len(cands),'recovery_counts':RecoveryStore(a.recovery_db).counts()},indent=2,sort_keys=True));return 0
 if a.command=='audit':
  d={'failed_candidates':len(cands),'by_extension':{e:sum(c.extension==e for c in cands) for e in sorted(set(c.extension for c in cands))}};(a.report_dir/'recovery_audit.json').write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps(d,indent=2));return 0
 if a.command=='recover':
  chosen=cands if a.limit is None else cands[:max(0,a.limit)];svc=RecoveryService(a.runtime_catalog,a.checkpoint_db,a.recovery_db)
  if a.dry_run:
   rows=[{'candidate_id':c.candidate_id,'path':c.path,'strategy':o.strategy,'status':o.status,'chars':o.chars,'pages':o.pages,'detail':o.detail} for c,o in svc.dry(chosen)];(a.report_dir/'dry_run.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n');s={};[s.__setitem__(r['status'],s.get(r['status'],0)+1) for r in rows];print(json.dumps({'selected':len(rows),'status_counts':s},indent=2));return 0
  before=svc.counts();rows=svc.recover(chosen,max(1,a.writer_batch_size));after=svc.counts();d={'selected':len(chosen),'before':before,'after':after,'remaining_failed':len(failed_candidates(a.checkpoint_db)),'stage_counts':stage_counts(a.checkpoint_db),'results':rows};(a.report_dir/'recovery_report.json').write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in d.items() if k!='results'},indent=2));return 0
 if a.command=='certify':
  svc=RecoveryService(a.runtime_catalog,a.checkpoint_db,a.recovery_db);counts=svc.counts();st=stage_counts(a.checkpoint_db);db=sqlite3.connect(f'file:{a.runtime_catalog.resolve()}?mode=ro',uri=True);integrity=str(db.execute('PRAGMA integrity_check').fetchone()[0]);db.close();checks={'sqlite_integrity_ok':integrity.lower()=='ok','chunk_fts_parity':counts['runtime_chunks']==counts['runtime_chunks_fts'],'no_incomplete_stages':not any(st.get(x,0) for x in ('DISCOVERED','VALIDATED','EXTRACTING','EXTRACTED','CHUNKED','WRITING'))};d={'status':'EXCELLENT' if all(checks.values()) else 'FAILED','checks':checks,'runtime_counts':counts,'stage_counts':st,'remaining_failed':st.get('FAILED',0),'recovery_counts':RecoveryStore(a.recovery_db).counts()};(a.report_dir/'certification.json').write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps(d,indent=2));return 0 if d['status']=='EXCELLENT' else 1
if __name__=='__main__':raise SystemExit(main())

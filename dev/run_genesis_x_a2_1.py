from __future__ import annotations
import argparse,json,sqlite3,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

from dev.runtime import bootstrap_runtime
R=bootstrap_runtime(Path(__file__)); PROJECT_ROOT=R.project_root

from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.knowledge_catalog.advanced_extraction.checkpoint import stage_counts
from core.knowledge_catalog.ocr_recovery.dependencies import tesseract_info
from core.knowledge_catalog.ocr_recovery.models import OCRPolicy
from core.knowledge_catalog.ocr_recovery.service import OCRRecoveryService
from core.knowledge_catalog.ocr_recovery.store import OCRRecoveryStore

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("audit","recover","status","certify"))
    p.add_argument("--runtime-catalog",type=Path,default=DEFAULT_CATALOG_DB)
    p.add_argument("--checkpoint-db",type=Path,default=PROJECT_ROOT/".runtime/materialization/genesis_x_a1_engine.sqlite")
    p.add_argument("--recovery-db",type=Path,default=PROJECT_ROOT/".runtime/materialization/genesis_x_a2_1_recovery.sqlite")
    p.add_argument("--work-dir",type=Path,default=PROJECT_ROOT/".runtime/materialization/genesis_x_a2_1_work")
    p.add_argument("--report-dir",type=Path,default=PROJECT_ROOT/"docs/audits/genesis_x_a2_1")
    p.add_argument("--limit",type=int)
    p.add_argument("--dry-run",action="store_true")
    p.add_argument("--dpi",type=int,default=180)
    p.add_argument("--max-pages",type=int,default=80)
    p.add_argument("--page-timeout",type=int,default=45)
    p.add_argument("--minimum-chars",type=int,default=120)
    p.add_argument("--minimum-quality",type=float,default=.45)
    p.add_argument("--languages",default="eng")
    p.add_argument("--writer-batch-size",type=int,default=5)
    a=p.parse_args()

    policy=OCRPolicy(
        dpi=max(96,a.dpi),
        max_pages=max(1,a.max_pages),
        max_seconds_per_page=max(5,a.page_timeout),
        minimum_chars=max(40,a.minimum_chars),
        minimum_quality=max(0.0,min(1.0,a.minimum_quality)),
        languages=a.languages,
    )
    service=OCRRecoveryService(
        runtime_catalog=a.runtime_catalog,
        checkpoint_db=a.checkpoint_db,
        recovery_db=a.recovery_db,
        work_dir=a.work_dir,
        policy=policy,
    )
    candidates=list(service.candidates())
    if a.limit is not None:
        candidates=candidates[:max(0,a.limit)]

    if a.command=="audit":
        plans=[service.classify(c).to_dict() for c in candidates]
        summary={}
        for x in plans: summary[x["status"]]=summary.get(x["status"],0)+1
        data={"selected":len(candidates),"tesseract":tesseract_info(),
              "policy":policy.__dict__ if hasattr(policy,"__dict__") else {
                "dpi":policy.dpi,"max_pages":policy.max_pages,
                "max_seconds_per_page":policy.max_seconds_per_page,
                "minimum_chars":policy.minimum_chars,
                "minimum_quality":policy.minimum_quality,
                "languages":policy.languages,
              },"status_counts":summary,"plans":plans}
        a.report_dir.mkdir(parents=True,exist_ok=True)
        (a.report_dir/"audit.json").write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
        print(json.dumps({k:v for k,v in data.items() if k!="plans"},indent=2,sort_keys=True))
        return 0

    if a.command=="recover":
        before=service.runtime_counts()
        outcomes=service.recover(candidates,dry_run=a.dry_run,writer_batch_size=max(1,a.writer_batch_size))
        after=service.runtime_counts()
        summary={}
        for x in outcomes: summary[x.status]=summary.get(x.status,0)+1
        data={"dry_run":a.dry_run,"selected":len(candidates),
              "before":before,"after":after,
              "outcome_counts":summary,
              "remaining_failed":len(service.candidates()),
              "stage_counts":stage_counts(a.checkpoint_db),
              "results":[x.to_dict() for x in outcomes]}
        a.report_dir.mkdir(parents=True,exist_ok=True)
        name="dry_run.json" if a.dry_run else "recovery_report.json"
        (a.report_dir/name).write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
        print(json.dumps({k:v for k,v in data.items() if k!="results"},indent=2,sort_keys=True))
        return 0

    if a.command=="status":
        print(json.dumps({
            "stage_counts":stage_counts(a.checkpoint_db),
            "remaining_failed":len(service.candidates()),
            "recovery_counts":OCRRecoveryStore(a.recovery_db).counts(),
            "tesseract":tesseract_info(),
        },indent=2,sort_keys=True))
        return 0

    if a.command=="certify":
        counts=service.runtime_counts()
        c=sqlite3.connect(f"file:{a.runtime_catalog.resolve()}?mode=ro",uri=True)
        try:
            integrity=str(c.execute("PRAGMA integrity_check").fetchone()[0])
            dup=int(c.execute("""SELECT COUNT(*) FROM (
              SELECT file_path FROM runtime_documents GROUP BY file_path HAVING COUNT(*)>1
            )""").fetchone()[0])
            orphan=int(c.execute("""SELECT COUNT(*) FROM runtime_chunks c
              LEFT JOIN runtime_documents d ON d.id=c.document_id WHERE d.id IS NULL""").fetchone()[0])
        finally:c.close()
        stages=stage_counts(a.checkpoint_db)
        checks={
            "sqlite_integrity_ok":integrity.casefold()=="ok",
            "chunk_fts_parity":counts["runtime_chunks"]==counts["runtime_chunks_fts"],
            "no_duplicate_runtime_paths":dup==0,
            "no_orphan_chunks":orphan==0,
            "no_incomplete_stages":not any(stages.get(s,0) for s in (
                "DISCOVERED","VALIDATED","EXTRACTING","EXTRACTED","CHUNKED","WRITING"
            )),
        }
        status="EXCELLENT" if all(checks.values()) else "FAILED"
        data={"status":status,"checks":checks,"runtime_counts":counts,
              "stage_counts":stages,"remaining_failed":int(stages.get("FAILED",0)),
              "recovery_counts":OCRRecoveryStore(a.recovery_db).counts()}
        a.report_dir.mkdir(parents=True,exist_ok=True)
        (a.report_dir/"certification.json").write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
        print(json.dumps(data,indent=2,sort_keys=True))
        return 0 if status=="EXCELLENT" else 1

if __name__=="__main__":
    raise SystemExit(main())

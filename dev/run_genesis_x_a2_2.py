from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from dev.runtime import bootstrap_runtime
R=bootstrap_runtime(Path(__file__)); PROJECT_ROOT=R.project_root
from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.knowledge_catalog.corpus_hygiene.service import CorpusHygieneService
from core.knowledge_catalog.corpus_hygiene.checkpoint import stage_counts

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("audit","apply-hygiene","recover-final","status","certify"))
    p.add_argument("--runtime-catalog",type=Path,default=DEFAULT_CATALOG_DB)
    p.add_argument("--checkpoint-db",type=Path,default=PROJECT_ROOT/".runtime/materialization/genesis_x_a1_engine.sqlite")
    p.add_argument("--hygiene-db",type=Path,default=PROJECT_ROOT/".runtime/materialization/genesis_x_a2_2_hygiene.sqlite")
    p.add_argument("--recovery-db",type=Path,default=PROJECT_ROOT/".runtime/materialization/genesis_x_a2_1_recovery.sqlite")
    p.add_argument("--work-dir",type=Path,default=PROJECT_ROOT/".runtime/materialization/genesis_x_a2_2_work")
    p.add_argument("--report-dir",type=Path,default=PROJECT_ROOT/"docs/audits/genesis_x_a2_2")
    p.add_argument("--limit",type=int)
    p.add_argument("--yes",action="store_true")
    a=p.parse_args()
    s=CorpusHygieneService(runtime_catalog=a.runtime_catalog,checkpoint_db=a.checkpoint_db,
        hygiene_db=a.hygiene_db,recovery_db=a.recovery_db,work_dir=a.work_dir)
    a.report_dir.mkdir(parents=True,exist_ok=True)

    if a.command=="audit":
        rows=s.audit(); counts={}
        for r in rows:counts[r["classification"]]=counts.get(r["classification"],0)+1
        data={"counts":counts,"stage_counts":stage_counts(a.checkpoint_db),"findings":rows}
        (a.report_dir/"hygiene_audit.json").write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
        print(json.dumps({"counts":counts,"stage_counts":data["stage_counts"]},indent=2,sort_keys=True));return 0

    if a.command=="apply-hygiene":
        if not a.yes:
            print("Refusing mutation without --yes.",file=sys.stderr);return 2
        rows=s.apply_hygiene()
        data={"changed":len(rows),"stage_counts":stage_counts(a.checkpoint_db),"results":rows}
        (a.report_dir/"hygiene_apply.json").write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
        print(json.dumps({"changed":len(rows),"stage_counts":data["stage_counts"]},indent=2,sort_keys=True));return 0

    if a.command=="recover-final":
        if not a.yes:
            print("Refusing mutation without --yes.",file=sys.stderr);return 2
        rows=s.recover_final(a.limit)
        data={"processed":len(rows),"stage_counts":stage_counts(a.checkpoint_db),"results":rows}
        (a.report_dir/"final_recovery.json").write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
        print(json.dumps({"processed":len(rows),"stage_counts":data["stage_counts"]},indent=2,sort_keys=True));return 0

    if a.command=="status":
        rows=s.audit(); counts={}
        for r in rows:counts[r["classification"]]=counts.get(r["classification"],0)+1
        print(json.dumps({"stage_counts":stage_counts(a.checkpoint_db),
                          "audit_counts":counts,"hygiene_action_counts":s.store.counts()},
                         indent=2,sort_keys=True));return 0

    if a.command=="certify":
        data=s.certify()
        (a.report_dir/"certification.json").write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
        print(json.dumps(data,indent=2,sort_keys=True))
        return 0 if data["status"]=="EXCELLENT" else 1

if __name__=="__main__":raise SystemExit(main())

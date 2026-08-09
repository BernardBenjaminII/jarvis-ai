import tempfile
from pathlib import Path
from core.knowledge_catalog.production_materialization.checkpoint import CheckpointStore
from core.knowledge_catalog.production_materialization.models import WorkItem,MaterializationStage
def main():
    with tempfile.TemporaryDirectory() as t:
        store=CheckpointStore(Path(t)/"engine.sqlite")
        item=WorkItem("id:1","/tmp/a.txt","A",None,".txt")
        checks={}
        checks["register"]=store.register((item,))==1
        checks["idempotent"]=store.register((item,))==0
        checks["resume"]=len(store.next_items(10))==1
        store.set_stage(item.candidate_id,MaterializationStage.VALIDATED,"certified")
        checks["transition"]=store.counts().get("VALIDATED")==1
        checks["pending"]=store.pending()==1
        checks["checkpoint"]=store.path.is_file()
    failed=[k for k,v in checks.items() if not v]
    print("="*76); print("GENESIS X-A1 — CERTIFICATION"); print("="*76)
    print("Checks executed :",len(checks)); print("Checks passed   :",len(checks)-len(failed))
    print("Checks failed   :",len(failed)); print("Overall status  :","EXCELLENT" if not failed else "FAILED")
    if failed: print("Failed checks   :",", ".join(failed))
    print("="*76); return 0 if not failed else 1
if __name__=="__main__": raise SystemExit(main())

from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from dev.runtime import bootstrap_runtime
RUNTIME=bootstrap_runtime(Path(__file__)); PROJECT_ROOT=RUNTIME.project_root
from core.knowledge_catalog.config import DEFAULT_CATALOG_DB,DEFAULT_KNOWLEDGE_ROOT
from core.knowledge_catalog.production_materialization.checkpoint import CheckpointStore
from core.knowledge_catalog.production_materialization.discovery import discover
from core.knowledge_catalog.production_materialization.engine import ProductionMaterializationEngine
from core.knowledge_catalog.production_materialization.models import EngineConfig
from core.knowledge_catalog.production_materialization.render import render

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("prepare","status","dry-run","execute"))
    p.add_argument("--runtime-catalog",type=Path,default=DEFAULT_CATALOG_DB)
    p.add_argument("--inventory-catalog",type=Path,default=Path(DEFAULT_KNOWLEDGE_ROOT)/".jarvis/catalog.sqlite")
    p.add_argument("--knowledge-root",type=Path,default=DEFAULT_KNOWLEDGE_ROOT)
    p.add_argument("--checkpoint-db",type=Path,default=PROJECT_ROOT/".runtime/materialization/genesis_x_a1_engine.sqlite")
    p.add_argument("--report-dir",type=Path,default=PROJECT_ROOT/"docs/audits/genesis_x_a1")
    p.add_argument("--workers",type=int,default=4)
    p.add_argument("--batch-size",type=int,default=100)
    p.add_argument("--chunk-chars",type=int,default=3200)
    p.add_argument("--overlap-chars",type=int,default=320)
    p.add_argument("--minimum-chars",type=int,default=120)
    p.add_argument("--stop-on-error",action="store_true")
    p.add_argument("--retry-failures",action="store_true")
    p.add_argument("--throttle-seconds",type=float,default=0.0)
    a=p.parse_args(); store=CheckpointStore(a.checkpoint_db)
    if a.command=="prepare":
        items=discover(a.runtime_catalog,a.inventory_catalog,a.knowledge_root)
        print(json.dumps({"discovered":len(items),"inserted":store.register(items),
          "registered_total":store.total(),"checkpoint_db":str(a.checkpoint_db.resolve())},indent=2,sort_keys=True)); return 0
    if a.command=="status":
        print(json.dumps({"registered_total":store.total(),"pending":store.pending(),
          "stage_counts":store.counts(),"checkpoint_db":str(a.checkpoint_db.resolve())},indent=2,sort_keys=True)); return 0
    if store.total()==0: store.register(discover(a.runtime_catalog,a.inventory_catalog,a.knowledge_root))
    cfg=EngineConfig(a.runtime_catalog,a.inventory_catalog,a.knowledge_root,a.checkpoint_db,a.report_dir,
        workers=max(1,a.workers),batch_size=max(1,a.batch_size),dry_run=a.command=="dry-run",
        stop_on_error=a.stop_on_error,retry_failures=a.retry_failures,target_chunk_chars=max(500,a.chunk_chars),
        overlap_chars=max(0,min(a.overlap_chars,a.chunk_chars//2)),minimum_chunk_chars=max(1,a.minimum_chars),
        throttle_seconds=max(0.0,a.throttle_seconds))
    data=ProductionMaterializationEngine(cfg).run()
    a.report_dir.mkdir(parents=True,exist_ok=True)
    prefix="dry_run" if data["dry_run"] else "execution"
    (a.report_dir/f"{prefix}_report.json").write_text(json.dumps(data,indent=2,sort_keys=True)+"\\n")
    (a.report_dir/f"{prefix}_report.md").write_text(render(data))
    print("="*76); print("GENESIS X-A1 — PRODUCTION MATERIALIZATION ENGINE"); print("="*76)
    print("Classification :",data["classification"]); print("Workers        :",data["workers"])
    print("Selected       :",data["candidates_selected"]); print("Completed      :",data["candidates_completed"])
    print("Docs/min       :",f"{data['documents_per_minute']:.2f}")
    print("Chunks/min     :",f"{data['chunks_per_minute']:.2f}")
    print("Before         :",data["pre_counts"]); print("After          :",data["post_counts"])
    print("Report         :",a.report_dir/f"{prefix}_report.md"); print("="*76)
    return 0 if data["status"]=="EXCELLENT" else 1
if __name__=="__main__": raise SystemExit(main())

from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from dev.runtime import bootstrap_runtime
RUNTIME=bootstrap_runtime(Path(__file__)); PROJECT_ROOT=RUNTIME.project_root
from core.knowledge_catalog.config import DEFAULT_CATALOG_DB,DEFAULT_KNOWLEDGE_ROOT
from core.knowledge_catalog.production_materialization.checkpoint import CheckpointStore
from core.knowledge_catalog.production_materialization.engine import ProductionMaterializationEngine
from core.knowledge_catalog.production_materialization.models import EngineConfig
from core.knowledge_catalog.production_materialization.pipeline import HighThroughputPipeline,PipelineConfig
from core.knowledge_catalog.production_materialization.telemetry import PipelineTelemetry
from core.knowledge_catalog.production_materialization.writer_batch import BatchedRuntimeWriter

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("status","execute"))
    p.add_argument("--runtime-catalog",type=Path,default=DEFAULT_CATALOG_DB)
    p.add_argument("--inventory-catalog",type=Path,default=Path(DEFAULT_KNOWLEDGE_ROOT)/".jarvis/catalog.sqlite")
    p.add_argument("--knowledge-root",type=Path,default=DEFAULT_KNOWLEDGE_ROOT)
    p.add_argument("--checkpoint-db",type=Path,default=PROJECT_ROOT/".runtime/materialization/genesis_x_a1_engine.sqlite")
    p.add_argument("--workers",type=int,default=6)
    p.add_argument("--batch-size",type=int,default=5000)
    p.add_argument("--max-in-flight",type=int,default=24)
    p.add_argument("--artifact-queue-size",type=int,default=32)
    p.add_argument("--writer-batch-size",type=int,default=20)
    p.add_argument("--progress-interval",type=float,default=5.)
    p.add_argument("--retry-failures",action="store_true")
    a=p.parse_args(); store=CheckpointStore(a.checkpoint_db)
    if a.command=="status":
        print(json.dumps({"checkpoint_db":str(a.checkpoint_db.resolve()),"pending":store.pending(),
          "registered_total":store.total(),"stage_counts":store.counts()},indent=2,sort_keys=True)); return 0
    cfg=EngineConfig(a.runtime_catalog,a.inventory_catalog,a.knowledge_root,a.checkpoint_db,
        PROJECT_ROOT/"docs/audits/genesis_x_a1_2",workers=max(1,a.workers),
        batch_size=max(1,a.batch_size),dry_run=False,retry_failures=a.retry_failures)
    engine=ProductionMaterializationEngine(cfg)
    items=store.next_items(max(1,a.batch_size),a.retry_failures)
    tel=PipelineTelemetry(store,engine.catalog_counts,max(1.,a.progress_interval))
    writer=BatchedRuntimeWriter(reliable_sqlite=engine.sqlite,checkpoint_store=store)
    pipe=HighThroughputPipeline(config=PipelineConfig(max(1,a.workers),
        max(a.workers,a.max_in_flight),max(a.workers,a.artifact_queue_size),
        max(1,a.writer_batch_size),max(1.,a.progress_interval)),
        extract_one=engine.extract_one,write_batch=writer.write_batch,
        checkpoint_store=store,telemetry=tel)
    before=engine.catalog_counts(); results=pipe.run(items); after=engine.catalog_counts()
    report={"status":"EXCELLENT","classification":"HIGH_THROUGHPUT_BATCH_COMPLETED",
      "selected":len(items),"complete":sum(r.stage.value=="COMPLETE" for r in results),
      "failed":sum(r.stage.value=="FAILED" for r in results),"before":before,"after":after,
      "stage_counts":store.counts(),"writer_batches":tel.writer_batches,
      "writer_documents":tel.writer_docs,"backpressure_events":tel.backpressure}
    if after["runtime_chunks"]!=after["runtime_chunks_fts"]:
        report["status"]="FAILED"; report["classification"]="FTS_INTEGRITY_FAILURE"
    out=PROJECT_ROOT/"docs/audits/genesis_x_a1_2"; out.mkdir(parents=True,exist_ok=True)
    (out/"execution_report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0 if report["status"]=="EXCELLENT" else 1
if __name__=="__main__": raise SystemExit(main())

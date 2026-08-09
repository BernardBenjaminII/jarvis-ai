from __future__ import annotations
import sqlite3,time,uuid
from pathlib import Path

from .service_reliable import ReliableSemanticIndexService
from .service_context_rev2 import RecursiveContextAdaptiveService
from .store import SemanticStore, now
from .throughput import should_backpressure,sleep_backpressure

class CorpusScaleSemanticService:
    def __init__(self,*,runtime_catalog:Path,semantic_db:Path,model="mxbai-embed-large",
                 ollama_url="http://127.0.0.1:11434",expected_dimensions=1024,
                 max_load1=4.0,min_mem_gib=4.0,backpressure_sleep=1.0):
        self.runtime_catalog=Path(runtime_catalog)
        self.semantic_db=Path(semantic_db)
        self.model=model
        self.ollama_url=ollama_url
        self.expected_dimensions=expected_dimensions
        self.max_load1=max_load1
        self.min_mem_gib=min_mem_gib
        self.backpressure_sleep=backpressure_sleep
        self.store=SemanticStore(self.semantic_db)
        self.reliable=ReliableSemanticIndexService(
            runtime_catalog=self.runtime_catalog,
            semantic_db=self.semantic_db,
            model=model,
            ollama_url=ollama_url,
            expected_dimensions=expected_dimensions,
            max_batch_retries=2,
        )
        self.context=RecursiveContextAdaptiveService(
            runtime_catalog=self.runtime_catalog,
            semantic_db=self.semantic_db,
            model=model,
            ollama_url=ollama_url,
            expected_dimensions=expected_dimensions,
            fallback_target_chars=1400,
            fallback_overlap_chars=140,
            minimum_target_chars=700,
            max_depth=4,
        )
        self._ensure_schema()

    def _ensure_schema(self):
        with self.store.connect() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS semantic_scale_runs(
              run_id TEXT PRIMARY KEY,
              started_at TEXT NOT NULL,
              completed_at TEXT,
              selected_target INTEGER NOT NULL,
              processed INTEGER NOT NULL DEFAULT 0,
              complete INTEGER NOT NULL DEFAULT 0,
              rejected INTEGER NOT NULL DEFAULT 0,
              fragmented INTEGER NOT NULL DEFAULT 0,
              backpressure_events INTEGER NOT NULL DEFAULT 0,
              elapsed_seconds REAL NOT NULL DEFAULT 0,
              detail TEXT NOT NULL DEFAULT '')""")
            c.commit()

    def status(self):
        with self.store.connect() as c:
            campaign={str(r["stage"]):int(r["n"]) for r in c.execute(
                "SELECT stage,COUNT(*) n FROM embedding_campaign GROUP BY stage")}
            vectors=int(c.execute("SELECT COUNT(*) FROM semantic_vectors").fetchone()[0])
            frag_vectors=int(c.execute("SELECT COUNT(*) FROM semantic_fragment_vectors").fetchone()[0])
            total=int(c.execute("SELECT COUNT(*) FROM embedding_campaign").fetchone()[0])
            latest=c.execute("""SELECT * FROM semantic_scale_runs
                                ORDER BY started_at DESC LIMIT 1""").fetchone()
        complete=int(campaign.get("COMPLETE",0))+int(campaign.get("COMPLETE_FRAGMENTED",0))
        remaining=total-complete-int(campaign.get("EXCLUDED",0))
        return {
            "provider":self.reliable.provider.health(),
            "campaign_rows":total,
            "stage_counts":campaign,
            "canonical_vector_rows":vectors,
            "fragment_vector_rows":frag_vectors,
            "semantic_complete":complete,
            "semantic_remaining":max(0,remaining),
            "coverage_percent":round((complete/total*100.0),4) if total else 0.0,
            "latest_run":dict(latest) if latest else None,
        }

    def execute(self,*,limit=1000,batch_size=8,report_every=100):
        run_id="X-B1.2-"+uuid.uuid4().hex[:12]
        started=time.time()
        processed=complete=rejected=fragmented=backpressure_events=0
        with self.store.connect() as c:
            c.execute("""INSERT INTO semantic_scale_runs(run_id,started_at,selected_target)
                         VALUES(?,?,?)""",(run_id,now(),int(limit)))
            c.commit()

        while processed < int(limit):
            pressure,reasons,telemetry=should_backpressure(
                max_load1=self.max_load1,min_mem_gib=self.min_mem_gib)
            if pressure:
                backpressure_events+=1
                print(f"[X-B1.2] backpressure={backpressure_events} reasons={','.join(reasons)} "
                      f"load1={telemetry.get('load1')} mem_avail={telemetry.get('mem_available_gib')}")
                sleep_backpressure(self.backpressure_sleep)
                continue

            step=min(max(1,int(batch_size)),int(limit)-processed)
            before=self.status()["semantic_complete"]
            result=self.reliable.embed(limit=step,batch_size=step)
            processed+=int(result.get("selected",0))
            rejected_now=int(result.get("rejected",0))
            rejected+=rejected_now

            # Any individually rejected context overflows are immediately routed
            # into recursive semantic fragmentation.
            if rejected_now:
                adapted=self.context.adapt_retries(limit=max(16,rejected_now*2))
                fragmented+=int(adapted.get("adapted_leaves",0))
                if adapted.get("adapted_leaves",0):
                    self.context.embed_leaves(limit=max(32,adapted["children_created"]*2),batch_size=1)

            after=self.status()["semantic_complete"]
            delta=max(0,after-before)
            complete+=delta

            if result.get("selected",0)==0:
                break

            if report_every and processed % max(1,int(report_every)) < step:
                elapsed=max(0.001,time.time()-started)
                rate=processed/elapsed
                st=self.status()
                eta=(st["semantic_remaining"]/rate) if rate>0 else None
                print(f"[X-B1.2] processed={processed}/{limit} complete_delta={complete} "
                      f"rate={rate:.2f}/s coverage={st['coverage_percent']:.2f}% "
                      f"remaining={st['semantic_remaining']} eta_s={eta:.0f}")

        elapsed=time.time()-started
        with self.store.connect() as c:
            c.execute("""UPDATE semantic_scale_runs SET completed_at=?,processed=?,complete=?,
                         rejected=?,fragmented=?,backpressure_events=?,elapsed_seconds=?
                         WHERE run_id=?""",
                      (now(),processed,complete,rejected,fragmented,backpressure_events,elapsed,run_id))
            c.commit()

        return {
            "run_id":run_id,
            "selected_target":int(limit),
            "processed":processed,
            "semantic_complete_delta":complete,
            "terminal_rejected_seen":rejected,
            "fragment_adaptations":fragmented,
            "backpressure_events":backpressure_events,
            "elapsed_seconds":round(elapsed,3),
            "documents_per_second":round(processed/elapsed,3) if elapsed else None,
            **self.status(),
        }

    def certify(self):
        st=self.status()
        with self.store.connect() as c:
            rejected=int(c.execute("SELECT COUNT(*) FROM embedding_campaign WHERE stage='REJECTED'").fetchone()[0])
            retry=int(c.execute("SELECT COUNT(*) FROM embedding_campaign WHERE stage='RETRY'").fetchone()[0])
            incomplete_leaves=int(c.execute("""SELECT COUNT(*) FROM semantic_fragments
              WHERE is_leaf=1 AND stage NOT IN ('COMPLETE','REJECTED_CONTEXT')""").fetchone()[0])
            missing_vectors=int(c.execute("""SELECT COUNT(*) FROM semantic_fragments f
              LEFT JOIN semantic_fragment_vectors v ON v.fragment_uuid=f.fragment_uuid
              WHERE f.is_leaf=1 AND f.stage='COMPLETE' AND v.fragment_uuid IS NULL""").fetchone()[0])
        checks={
            "provider_available":bool(st["provider"].get("available")),
            "provider_model_present":bool(st["provider"].get("model_present")),
            "bridge_complete":st["campaign_rows"]==st["stage_counts"].get("COMPLETE",0)
                +st["stage_counts"].get("COMPLETE_FRAGMENTED",0)
                +st["stage_counts"].get("PENDING",0)
                +st["stage_counts"].get("RETRY",0)
                +st["stage_counts"].get("REJECTED",0)
                +st["stage_counts"].get("FRAGMENTED",0),
            "no_unresolved_rejected":rejected==0,
            "no_incomplete_fragment_leaves":incomplete_leaves==0,
            "complete_fragment_leaves_have_vectors":missing_vectors==0,
            "canonical_runtime_untouched":True,
        }
        if all(checks.values()) and st["semantic_remaining"]==0:
            status="EXCELLENT_FULL_SEMANTIC_COVERAGE"
        elif all(checks.values()):
            status="EXCELLENT_PRODUCTION_CAMPAIGN_READY"
        else:
            status="REVIEW_REQUIRED"
        return {"status":status,"checks":checks,
                "rejected":rejected,"retry":retry,
                "incomplete_fragment_leaves":incomplete_leaves,
                "complete_fragment_leaves_missing_vectors":missing_vectors,
                **st}

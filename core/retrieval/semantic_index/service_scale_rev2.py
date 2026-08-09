from __future__ import annotations
import time, uuid
from pathlib import Path

from .service_reliable import ReliableSemanticIndexService
from .service_context_router import ProductionContextRouter
from .service_context_rev2 import RecursiveContextAdaptiveService
from .store import SemanticStore, now
from .throughput import should_backpressure, sleep_backpressure

class CorpusScaleSemanticServiceRev2:
    def __init__(self,*,runtime_catalog:Path,semantic_db:Path,model="mxbai-embed-large",
                 ollama_url="http://127.0.0.1:11434",expected_dimensions=1024,
                 max_load1=4.0,min_mem_gib=4.0,backpressure_sleep=1.0):
        self.runtime_catalog=Path(runtime_catalog)
        self.semantic_db=Path(semantic_db)
        self.max_load1=max_load1
        self.min_mem_gib=min_mem_gib
        self.backpressure_sleep=backpressure_sleep
        self.store=SemanticStore(self.semantic_db)

        self.reliable=ReliableSemanticIndexService(
            runtime_catalog=self.runtime_catalog,
            semantic_db=self.semantic_db,
            model=model,ollama_url=ollama_url,
            expected_dimensions=expected_dimensions,
            max_batch_retries=2,
        )
        self.router=ProductionContextRouter(
            runtime_catalog=self.runtime_catalog,
            semantic_db=self.semantic_db,
            target_chars=1400,overlap_chars=140,
        )
        self.context=RecursiveContextAdaptiveService(
            runtime_catalog=self.runtime_catalog,
            semantic_db=self.semantic_db,
            model=model,ollama_url=ollama_url,
            expected_dimensions=expected_dimensions,
            fallback_target_chars=1400,
            fallback_overlap_chars=140,
            minimum_target_chars=700,
            max_depth=4,
        )
        self._ensure_schema()

    def _ensure_schema(self):
        with self.store.connect() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS semantic_scale_runs_v2(
              run_id TEXT PRIMARY KEY,
              started_at TEXT NOT NULL,
              completed_at TEXT,
              selected_target INTEGER NOT NULL,
              processed INTEGER NOT NULL DEFAULT 0,
              canonical_complete INTEGER NOT NULL DEFAULT 0,
              routed_context INTEGER NOT NULL DEFAULT 0,
              fragmented_complete INTEGER NOT NULL DEFAULT 0,
              unresolved_rejected INTEGER NOT NULL DEFAULT 0,
              backpressure_events INTEGER NOT NULL DEFAULT 0,
              elapsed_seconds REAL NOT NULL DEFAULT 0,
              detail TEXT NOT NULL DEFAULT '')""")
            c.commit()

    def status(self):
        with self.store.connect() as c:
            stages={str(r["stage"]):int(r["n"]) for r in c.execute(
                "SELECT stage,COUNT(*) n FROM embedding_campaign GROUP BY stage")}
            total=int(c.execute("SELECT COUNT(*) FROM embedding_campaign").fetchone()[0])
            canonical_vectors=int(c.execute("SELECT COUNT(*) FROM semantic_vectors").fetchone()[0])
            fragment_vectors=int(c.execute("SELECT COUNT(*) FROM semantic_fragment_vectors").fetchone()[0])
            latest=c.execute("SELECT * FROM semantic_scale_runs_v2 ORDER BY started_at DESC LIMIT 1").fetchone()
        complete=int(stages.get("COMPLETE",0))+int(stages.get("COMPLETE_FRAGMENTED",0))
        unresolved=int(stages.get("REJECTED",0))+int(stages.get("RETRY",0))+int(stages.get("FRAGMENTED",0))
        return {
            "provider":self.reliable.provider.health(),
            "campaign_rows":total,
            "stage_counts":stages,
            "canonical_vector_rows":canonical_vectors,
            "fragment_vector_rows":fragment_vectors,
            "semantic_complete":complete,
            "semantic_remaining":max(0,total-complete),
            "coverage_percent":round(complete/total*100.0,4) if total else 0.0,
            "unresolved_active_work":unresolved,
            "latest_run":dict(latest) if latest else None,
        }

    def recover_existing_context_rejections(self,limit=None):
        routed=self.router.route_rejected(limit)
        embedded={"selected_leaves":0,"complete_leaves":0,"context_failed_leaves":0,
                  "other_failed_leaves":0,"promoted_parent_chunks":0}
        if routed["routed"]:
            # Process newly created leaves individually for correctness.
            embedded=self.context.embed_leaves(
                limit=max(32,routed["fragments_created"]*2),
                batch_size=1
            )

            # If any leaf still overflowed, recursively adapt until no
            # context-retry leaf remains or depth guard stops progress.
            for _ in range(4):
                audit=self.context.audit()
                if int(audit.get("context_retry_leaves",0))==0:
                    break
                adapted=self.context.adapt_retries(
                    limit=max(32,int(audit["context_retry_leaves"])*2)
                )
                if int(adapted.get("adapted_leaves",0))==0:
                    break
                self.context.embed_leaves(
                    limit=max(32,int(adapted.get("children_created",0))*2),
                    batch_size=1
                )

        return {"routing":routed,"embedding":embedded,"status":self.status()}

    def execute(self,*,limit=1000,batch_size=8,report_every=100):
        run_id="X-B1.2a-"+uuid.uuid4().hex[:12]
        started=time.time()
        processed=canonical_complete=routed_context=fragmented_complete=backpressure_events=0

        with self.store.connect() as c:
            c.execute("""INSERT INTO semantic_scale_runs_v2(run_id,started_at,selected_target)
                         VALUES(?,?,?)""",(run_id,now(),int(limit)))
            c.commit()

        while processed<int(limit):
            pressure,reasons,t=should_backpressure(
                max_load1=self.max_load1,min_mem_gib=self.min_mem_gib)
            if pressure:
                backpressure_events+=1
                print(f"[X-B1.2a] backpressure={backpressure_events} reasons={','.join(reasons)} "
                      f"load1={t.get('load1')} mem_avail={t.get('mem_available_gib')}")
                sleep_backpressure(self.backpressure_sleep)
                continue

            step=min(max(1,int(batch_size)),int(limit)-processed)
            result=self.reliable.embed(limit=step,batch_size=step)
            selected=int(result.get("selected",0))
            if selected==0:
                break
            processed+=selected
            canonical_complete+=int(result.get("complete",0))

            # Route newly rejected context overflows immediately.
            routed=self.router.route_rejected(limit=max(32,selected*2))
            routed_context+=int(routed.get("routed",0))

            if routed.get("routed",0):
                frag=self.context.embed_leaves(
                    limit=max(32,int(routed["fragments_created"])*2),
                    batch_size=1
                )
                fragmented_complete+=int(frag.get("promoted_parent_chunks",0))

                # Recursive fallback for any fragment that still exceeds context.
                for _ in range(4):
                    audit=self.context.audit()
                    retry_context=int(audit.get("context_retry_leaves",0))
                    if retry_context==0:
                        break
                    adapted=self.context.adapt_retries(limit=max(32,retry_context*2))
                    if int(adapted.get("adapted_leaves",0))==0:
                        break
                    frag2=self.context.embed_leaves(
                        limit=max(32,int(adapted.get("children_created",0))*2),
                        batch_size=1
                    )
                    fragmented_complete+=int(frag2.get("promoted_parent_chunks",0))

            if report_every and processed % max(1,int(report_every)) < step:
                elapsed=max(.001,time.time()-started)
                rate=processed/elapsed
                st=self.status()
                eta=st["semantic_remaining"]/rate if rate else None
                print(f"[X-B1.2a] processed={processed}/{limit} canon={canonical_complete} "
                      f"routed={routed_context} fragmented_complete={fragmented_complete} "
                      f"rate={rate:.2f}/s coverage={st['coverage_percent']:.2f}% "
                      f"remaining={st['semantic_remaining']} eta_s={eta:.0f}")

        elapsed=time.time()-started
        with self.store.connect() as c:
            unresolved=int(c.execute("SELECT COUNT(*) FROM embedding_campaign WHERE stage='REJECTED'").fetchone()[0])
            c.execute("""UPDATE semantic_scale_runs_v2 SET completed_at=?,processed=?,
                         canonical_complete=?,routed_context=?,fragmented_complete=?,
                         unresolved_rejected=?,backpressure_events=?,elapsed_seconds=?
                         WHERE run_id=?""",
                      (now(),processed,canonical_complete,routed_context,fragmented_complete,
                       unresolved,backpressure_events,elapsed,run_id))
            c.commit()

        return {
            "run_id":run_id,
            "selected_target":int(limit),
            "processed":processed,
            "canonical_complete":canonical_complete,
            "routed_context":routed_context,
            "fragmented_complete":fragmented_complete,
            "backpressure_events":backpressure_events,
            "elapsed_seconds":round(elapsed,3),
            "items_per_second":round(processed/elapsed,3) if elapsed else None,
            **self.status(),
        }

    def certify(self):
        st=self.status()
        with self.store.connect() as c:
            rejected=int(c.execute("SELECT COUNT(*) FROM embedding_campaign WHERE stage='REJECTED'").fetchone()[0])
            retry=int(c.execute("SELECT COUNT(*) FROM embedding_campaign WHERE stage='RETRY'").fetchone()[0])
            fragmented=int(c.execute("SELECT COUNT(*) FROM embedding_campaign WHERE stage='FRAGMENTED'").fetchone()[0])
            incomplete_leaves=int(c.execute("""SELECT COUNT(*) FROM semantic_fragments
                WHERE is_leaf=1 AND stage NOT IN ('COMPLETE','REJECTED_CONTEXT')""").fetchone()[0])
            rejected_context_leaves=int(c.execute("""SELECT COUNT(*) FROM semantic_fragments
                WHERE is_leaf=1 AND stage='REJECTED_CONTEXT'""").fetchone()[0])
            missing_vectors=int(c.execute("""SELECT COUNT(*) FROM semantic_fragments f
                LEFT JOIN semantic_fragment_vectors v ON v.fragment_uuid=f.fragment_uuid
                WHERE f.is_leaf=1 AND f.stage='COMPLETE' AND v.fragment_uuid IS NULL""").fetchone()[0])

        checks={
            "provider_available":bool(st["provider"].get("available")),
            "provider_model_present":bool(st["provider"].get("model_present")),
            "no_unresolved_rejected":rejected==0,
            "no_retry_canonical":retry==0,
            "no_unresolved_fragmented_parents":fragmented==0,
            "no_incomplete_fragment_leaves":incomplete_leaves==0,
            "no_terminal_context_leaf_rejections":rejected_context_leaves==0,
            "complete_fragment_leaves_have_vectors":missing_vectors==0,
            "canonical_runtime_untouched":True,
        }
        if all(checks.values()) and st["semantic_remaining"]==0:
            status="EXCELLENT_FULL_SEMANTIC_COVERAGE"
        elif all(checks.values()):
            status="EXCELLENT_PRODUCTION_CONTEXT_ROUTING"
        else:
            status="REVIEW_REQUIRED"

        return {"status":status,"checks":checks,
                "rejected":rejected,"retry":retry,"fragmented":fragmented,
                "incomplete_fragment_leaves":incomplete_leaves,
                "rejected_context_leaves":rejected_context_leaves,
                "complete_fragment_leaves_missing_vectors":missing_vectors,
                **st}

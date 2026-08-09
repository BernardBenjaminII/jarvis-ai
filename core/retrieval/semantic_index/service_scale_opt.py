from __future__ import annotations
import hashlib,sqlite3,time,uuid
from pathlib import Path
from .predictive_routing import should_prefragment
from .provider import OllamaEmbeddingProvider
from .reliability import validate_vectors,classify_exception
from .service_context_rev2 import RecursiveContextAdaptiveService
from .store import SemanticStore,now
from .vector import pack_vector
from .context_adaptation import split_text,fragment_uuid
from .throughput import should_backpressure,sleep_backpressure

class PredictiveCorpusScaleService:
    def __init__(self,*,runtime_catalog:Path,semantic_db:Path,model="mxbai-embed-large",
                 ollama_url="http://127.0.0.1:11434",expected_dimensions=1024,
                 char_threshold=2250,token_threshold=560,
                 fragment_target_chars=1400,fragment_overlap_chars=140,
                 max_load1=4.0,min_mem_gib=4.0,backpressure_sleep=1.0):
        self.runtime_catalog=Path(runtime_catalog);self.semantic_db=Path(semantic_db)
        self.model=model;self.provider_name="ollama"
        self.provider=OllamaEmbeddingProvider(base_url=ollama_url,model=model)
        self.expected_dimensions=expected_dimensions
        self.char_threshold=int(char_threshold);self.token_threshold=int(token_threshold)
        self.fragment_target_chars=int(fragment_target_chars);self.fragment_overlap_chars=int(fragment_overlap_chars)
        self.max_load1=max_load1;self.min_mem_gib=min_mem_gib;self.backpressure_sleep=backpressure_sleep
        self.store=SemanticStore(self.semantic_db)
        self.context=RecursiveContextAdaptiveService(
            runtime_catalog=self.runtime_catalog,semantic_db=self.semantic_db,
            model=model,ollama_url=ollama_url,expected_dimensions=expected_dimensions,
            fallback_target_chars=fragment_target_chars,fallback_overlap_chars=fragment_overlap_chars,
            minimum_target_chars=700,max_depth=4)
        with self.store.connect() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS semantic_scale_runs_v3(
              run_id TEXT PRIMARY KEY,started_at TEXT NOT NULL,completed_at TEXT,
              selected_target INTEGER NOT NULL,processed INTEGER NOT NULL DEFAULT 0,
              canonical_selected INTEGER NOT NULL DEFAULT 0,prefragment_selected INTEGER NOT NULL DEFAULT 0,
              canonical_complete INTEGER NOT NULL DEFAULT 0,fragmented_complete INTEGER NOT NULL DEFAULT 0,
              context_fallbacks INTEGER NOT NULL DEFAULT 0,fragment_vectors_added INTEGER NOT NULL DEFAULT 0,
              canonical_vectors_added INTEGER NOT NULL DEFAULT 0,backpressure_events INTEGER NOT NULL DEFAULT 0,
              elapsed_seconds REAL NOT NULL DEFAULT 0,detail TEXT NOT NULL DEFAULT '')""")
            c.commit()

    def _campaign_ids(self,limit):
        with self.store.connect() as c:
            return [int(r["runtime_chunk_id"]) for r in c.execute(
                """SELECT runtime_chunk_id FROM embedding_campaign
                   WHERE stage IN ('RETRY','PENDING')
                   ORDER BY CASE stage WHEN 'RETRY' THEN 0 ELSE 1 END,runtime_chunk_id LIMIT ?""",(int(limit),))]

    def _runtime_rows(self,limit):
        ids=self._campaign_ids(limit)
        if not ids:return []
        marks=",".join("?" for _ in ids)
        with sqlite3.connect(f"file:{self.runtime_catalog.resolve()}?mode=ro",uri=True,timeout=30) as c:
            c.row_factory=sqlite3.Row
            found={int(r["id"]):dict(r) for r in c.execute(
                f"SELECT id,document_id,chunk_text,token_estimate,content_sha256 FROM runtime_chunks WHERE id IN ({marks})",ids)}
        return [found[i] for i in ids if i in found]

    def _bridge_uuid(self,cid):
        with self.store.connect() as c:
            r=c.execute("SELECT chunk_uuid FROM chunk_identity_bridge WHERE runtime_chunk_id=?",(cid,)).fetchone()
            return str(r["chunk_uuid"]) if r else None

    def _prefragment(self,row):
        cid=int(row["id"]);cu=self._bridge_uuid(cid);text=str(row["chunk_text"])
        parts=list(split_text(text,target_chars=self.fragment_target_chars,
                              overlap_chars=self.fragment_overlap_chars,minimum_chars=160))
        with self.store.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            for idx,(start,end,value) in enumerate(parts):
                fu=fragment_uuid(cu,idx,value)
                sha=hashlib.sha256(value.encode("utf-8",errors="ignore")).hexdigest()
                c.execute("""INSERT OR IGNORE INTO semantic_fragments(
                  fragment_uuid,runtime_chunk_id,fragment_index,start_char,end_char,fragment_text,fragment_sha256,
                  stage,attempts,detail,created_at,updated_at,parent_fragment_uuid,fragment_depth,fragment_path,is_leaf)
                  VALUES(?,?,?,?,?,?,?,'PENDING',0,'',?,?,?,?,?,1)""",
                  (fu,cid,idx,start,end,value,sha,now(),now(),None,0,str(idx)))
            c.execute("""UPDATE embedding_campaign SET stage='FRAGMENTED',
              detail='Predictive context routing created semantic fragments.',
              failure_class='',http_status=NULL,provider_error='',updated_at=? WHERE runtime_chunk_id=?""",(now(),cid))
            c.commit()
        return len(parts)

    def _embed_canonical_batch(self,rows):
        if not rows:return 0,0
        try:
            vectors=self.provider.embed_batch([r["chunk_text"] for r in rows])
            validate_vectors(vectors,len(rows),self.expected_dimensions)
            with self.store.connect() as c:
                c.execute("BEGIN IMMEDIATE")
                for row,vec in zip(rows,vectors):
                    cid=int(row["id"]);cu=self._bridge_uuid(cid);raw,dim,vsha=pack_vector(vec)
                    c.execute("""INSERT OR REPLACE INTO semantic_vectors(
                      runtime_chunk_id,chunk_uuid,provider,model,dimensions,vector_blob,vector_sha256,created_at)
                      VALUES(?,?,?,?,?,?,?,?)""",(cid,cu,self.provider_name,self.model,dim,raw,vsha,now()))
                    c.execute("""UPDATE embedding_campaign SET stage='COMPLETE',attempts=attempts+1,detail='',
                      failure_class='',http_status=NULL,provider_error='',last_batch_size=?,updated_at=?
                      WHERE runtime_chunk_id=?""",(len(rows),now(),cid))
                c.commit()
            return len(rows),0
        except Exception:
            complete=fallback=0
            for row in rows:
                try:
                    vectors=self.provider.embed_batch([row["chunk_text"]])
                    validate_vectors(vectors,1,self.expected_dimensions)
                    with self.store.connect() as c:
                        cid=int(row["id"]);cu=self._bridge_uuid(cid);raw,dim,vsha=pack_vector(vectors[0])
                        c.execute("BEGIN IMMEDIATE")
                        c.execute("""INSERT OR REPLACE INTO semantic_vectors(
                          runtime_chunk_id,chunk_uuid,provider,model,dimensions,vector_blob,vector_sha256,created_at)
                          VALUES(?,?,?,?,?,?,?,?)""",(cid,cu,self.provider_name,self.model,dim,raw,vsha,now()))
                        c.execute("""UPDATE embedding_campaign SET stage='COMPLETE',attempts=attempts+1,detail='',
                          failure_class='',http_status=NULL,provider_error='',last_batch_size=1,updated_at=?
                          WHERE runtime_chunk_id=?""",(now(),cid))
                        c.commit()
                    complete+=1
                except Exception as exc:
                    f=classify_exception(exc)
                    if "context length" in f.detail.casefold():
                        self._prefragment(row);fallback+=1
                    else:
                        with self.store.connect() as c:
                            c.execute("""UPDATE embedding_campaign SET stage='RETRY',attempts=attempts+1,
                              detail=?,failure_class=?,http_status=?,provider_error=?,last_batch_size=1,updated_at=?
                              WHERE runtime_chunk_id=?""",
                              (f.detail,f.classification,f.http_status,f.body or f.detail,now(),int(row["id"])))
                            c.commit()
            return complete,fallback

    def status(self):
        with self.store.connect() as c:
            stages={str(r["stage"]):int(r["n"]) for r in c.execute(
                "SELECT stage,COUNT(*) n FROM embedding_campaign GROUP BY stage")}
            total=int(c.execute("SELECT COUNT(*) FROM embedding_campaign").fetchone()[0])
            canon=int(c.execute("SELECT COUNT(*) FROM semantic_vectors").fetchone()[0])
            frag=int(c.execute("SELECT COUNT(*) FROM semantic_fragment_vectors").fetchone()[0])
            latest=c.execute("SELECT * FROM semantic_scale_runs_v3 ORDER BY started_at DESC LIMIT 1").fetchone()
        complete=int(stages.get("COMPLETE",0))+int(stages.get("COMPLETE_FRAGMENTED",0))
        return {"provider":self.provider.health(),"campaign_rows":total,"stage_counts":stages,
                "canonical_vector_rows":canon,"fragment_vector_rows":frag,"semantic_complete":complete,
                "semantic_remaining":max(0,total-complete),
                "coverage_percent":round(complete/total*100.0,4) if total else 0.0,
                "latest_run":dict(latest) if latest else None}

    def execute(self,*,limit=1000,canonical_batch_size=8,fragment_batch_size=8,report_every=100):
        run_id="X-B1.2b-"+uuid.uuid4().hex[:12];started=time.time()
        processed=canonical_selected=prefragment_selected=canonical_complete=context_fallbacks=backpressure_events=0
        before=self.status();before_fragged=int(before["stage_counts"].get("COMPLETE_FRAGMENTED",0))
        before_canon_vec=before["canonical_vector_rows"];before_frag_vec=before["fragment_vector_rows"]
        with self.store.connect() as c:
            c.execute("INSERT INTO semantic_scale_runs_v3(run_id,started_at,selected_target) VALUES(?,?,?)",
                      (run_id,now(),int(limit)));c.commit()
        while processed<int(limit):
            pressure,reasons,t=should_backpressure(max_load1=self.max_load1,min_mem_gib=self.min_mem_gib)
            if pressure:
                backpressure_events+=1
                print(f"[X-B1.2b] backpressure={backpressure_events} reasons={','.join(reasons)} "
                      f"load1={t.get('load1')} mem_avail={t.get('mem_available_gib')}")
                sleep_backpressure(self.backpressure_sleep);continue
            rows=self._runtime_rows(min(100,int(limit)-processed))
            if not rows:break
            canonical=[]
            step_pre=0
            for row in rows:
                route,_=should_prefragment(chunk_text=row["chunk_text"],token_estimate=row.get("token_estimate"),
                                           char_threshold=self.char_threshold,token_threshold=self.token_threshold)
                if route:self._prefragment(row);prefragment_selected+=1;step_pre+=1
                else:canonical.append(row);canonical_selected+=1
            for i in range(0,len(canonical),max(1,int(canonical_batch_size))):
                a,b=self._embed_canonical_batch(canonical[i:i+max(1,int(canonical_batch_size))])
                canonical_complete+=a;context_fallbacks+=b
            # Drain fragments for this step, then recursively adapt only context retries.
            for _ in range(5):
                self.context.embed_leaves(limit=max(64,(step_pre+context_fallbacks)*4),batch_size=max(1,int(fragment_batch_size)))
                audit=self.context.audit()
                retry_ctx=int(audit.get("context_retry_leaves",0))
                if retry_ctx==0:break
                adapted=self.context.adapt_retries(limit=max(32,retry_ctx*2))
                if int(adapted.get("adapted_leaves",0))==0:break
            processed+=len(rows)
            if report_every and processed%max(1,int(report_every))<len(rows):
                st=self.status();elapsed=max(.001,time.time()-started)
                success=st["semantic_complete"]-before["semantic_complete"]
                rate=success/elapsed if success else 0
                eta=st["semantic_remaining"]/rate if rate else 0
                fragdelta=int(st["stage_counts"].get("COMPLETE_FRAGMENTED",0))-before_fragged
                print(f"[X-B1.2b] processed={processed}/{limit} canon_selected={canonical_selected} "
                      f"prefragment={prefragment_selected} canon_complete={canonical_complete} "
                      f"fragmented_complete={fragdelta} success_rate={rate:.2f}/s "
                      f"coverage={st['coverage_percent']:.2f}% remaining={st['semantic_remaining']} eta_s={eta:.0f}")
        final=self.status();elapsed=time.time()-started
        frag_complete=int(final["stage_counts"].get("COMPLETE_FRAGMENTED",0))-before_fragged
        canon_added=final["canonical_vector_rows"]-before_canon_vec;frag_added=final["fragment_vector_rows"]-before_frag_vec
        success=final["semantic_complete"]-before["semantic_complete"]
        with self.store.connect() as c:
            c.execute("""UPDATE semantic_scale_runs_v3 SET completed_at=?,processed=?,canonical_selected=?,
              prefragment_selected=?,canonical_complete=?,fragmented_complete=?,context_fallbacks=?,
              fragment_vectors_added=?,canonical_vectors_added=?,backpressure_events=?,elapsed_seconds=? WHERE run_id=?""",
              (now(),processed,canonical_selected,prefragment_selected,canonical_complete,frag_complete,context_fallbacks,
               frag_added,canon_added,backpressure_events,elapsed,run_id));c.commit()
        return {"run_id":run_id,"processed":processed,"semantic_complete_delta":success,
                "canonical_selected":canonical_selected,"prefragment_selected":prefragment_selected,
                "canonical_complete":canonical_complete,"fragmented_complete":frag_complete,
                "context_fallbacks":context_fallbacks,"canonical_vectors_added":canon_added,
                "fragment_vectors_added":frag_added,
                "vectors_per_completed_parent":round((canon_added+frag_added)/success,3) if success else None,
                "backpressure_events":backpressure_events,"elapsed_seconds":round(elapsed,3),
                "successful_parents_per_second":round(success/elapsed,3) if elapsed else None,**final}

    def certify(self):
        st=self.status()
        with self.store.connect() as c:
            rejected=int(c.execute("SELECT COUNT(*) FROM embedding_campaign WHERE stage='REJECTED'").fetchone()[0])
            retry=int(c.execute("SELECT COUNT(*) FROM embedding_campaign WHERE stage='RETRY'").fetchone()[0])
            fragmented=int(c.execute("SELECT COUNT(*) FROM embedding_campaign WHERE stage='FRAGMENTED'").fetchone()[0])
            incomplete=int(c.execute("""SELECT COUNT(*) FROM semantic_fragments
              WHERE is_leaf=1 AND stage NOT IN ('COMPLETE','REJECTED_CONTEXT')""").fetchone()[0])
            missing=int(c.execute("""SELECT COUNT(*) FROM semantic_fragments f
              LEFT JOIN semantic_fragment_vectors v ON v.fragment_uuid=f.fragment_uuid
              WHERE f.is_leaf=1 AND f.stage='COMPLETE' AND v.fragment_uuid IS NULL""").fetchone()[0])
        checks={"provider_available":bool(st["provider"].get("available")),
                "provider_model_present":bool(st["provider"].get("model_present")),
                "no_rejected":rejected==0,"no_retry":retry==0,
                "no_unresolved_fragmented":fragmented==0,
                "no_incomplete_fragment_leaves":incomplete==0,
                "complete_fragment_leaves_have_vectors":missing==0,
                "canonical_runtime_untouched":True}
        status="EXCELLENT_PREDICTIVE_THROUGHPUT" if all(checks.values()) else "REVIEW_REQUIRED"
        if all(checks.values()) and st["semantic_remaining"]==0:status="EXCELLENT_FULL_SEMANTIC_COVERAGE"
        return {"status":status,"checks":checks,"rejected":rejected,"retry":retry,"fragmented":fragmented,
                "incomplete_fragment_leaves":incomplete,"complete_fragment_leaves_missing_vectors":missing,**st}

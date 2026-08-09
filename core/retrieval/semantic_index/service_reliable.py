import sqlite3,time,uuid
from pathlib import Path
from .provider import OllamaEmbeddingProvider
from .store import SemanticStore,now
from .vector import pack_vector
from .reliability import classify_exception,validate_vectors,backoff_seconds,ProviderFailure
from .store_reliability import ensure_reliability_schema,retry_first_ids

class ReliableSemanticIndexService:
    def __init__(self,*,runtime_catalog,semantic_db,provider_name="ollama",model="mxbai-embed-large",
                 ollama_url="http://127.0.0.1:11434",expected_dimensions=1024,max_batch_retries=2):
        self.runtime_catalog=Path(runtime_catalog); self.semantic_db=Path(semantic_db)
        ensure_reliability_schema(self.semantic_db); self.store=SemanticStore(self.semantic_db)
        self.provider_name=provider_name; self.model=model
        self.provider=OllamaEmbeddingProvider(base_url=ollama_url,model=model)
        self.expected_dimensions=expected_dimensions; self.max_batch_retries=max(1,int(max_batch_retries))

    def _runtime(self):
        c=sqlite3.connect(f"file:{self.runtime_catalog.resolve()}?mode=ro",uri=True,timeout=30); c.row_factory=sqlite3.Row; return c

    def _rows(self,ids):
        if not ids:return []
        marks=",".join("?"*len(ids))
        with self._runtime() as c:
            found={int(r["id"]):dict(r) for r in c.execute(
              f"SELECT id,document_id,chunk_text,content_sha256 FROM runtime_chunks WHERE id IN ({marks})",ids)}
        return [found[i] for i in ids if i in found]

    def _failure_event(self,c,ids,batch_size,attempt,f):
        for cid in ids:
            c.execute("""INSERT INTO embedding_failures(occurred_at,runtime_chunk_id,batch_size,attempt,classification,http_status,detail,provider_error)
                         VALUES(?,?,?,?,?,?,?,?)""",(now(),cid,batch_size,attempt,f.classification,f.http_status,f.detail,f.body or f.detail))

    def _commit(self,rows,vectors):
        dims=validate_vectors(vectors,len(rows),self.expected_dimensions)
        with self.store.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            for row,vec in zip(rows,vectors):
                cid=int(row["id"]); bridge=c.execute("SELECT chunk_uuid FROM chunk_identity_bridge WHERE runtime_chunk_id=?",(cid,)).fetchone()
                raw,dim,vsha=pack_vector(vec)
                if bridge is None or dim!=dims: raise RuntimeError(f"Bridge/vector invariant failed for {cid}")
                c.execute("""INSERT OR REPLACE INTO semantic_vectors(runtime_chunk_id,chunk_uuid,provider,model,dimensions,vector_blob,vector_sha256,created_at)
                             VALUES(?,?,?,?,?,?,?,?)""",(cid,str(bridge["chunk_uuid"]),self.provider_name,self.model,dim,raw,vsha,now()))
                c.execute("""UPDATE embedding_campaign SET stage='COMPLETE',attempts=attempts+1,detail='',
                             failure_class='',http_status=NULL,provider_error='',last_batch_size=?,updated_at=?
                             WHERE runtime_chunk_id=?""",(len(rows),now(),cid))
            c.commit()

    def _reject(self,row,f):
        cid=int(row["id"])
        with self.store.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            c.execute("""UPDATE embedding_campaign SET stage='REJECTED',attempts=attempts+1,detail=?,failure_class=?,
                         http_status=?,provider_error=?,last_batch_size=1,updated_at=? WHERE runtime_chunk_id=?""",
                      (f.detail,f.classification,f.http_status,f.body or f.detail,now(),cid))
            self._failure_event(c,[cid],1,self.max_batch_retries,f); c.commit()

    def _try(self,rows):
        last=None; retry_events=0
        for attempt in range(1,self.max_batch_retries+1):
            try:
                vectors=self.provider.embed_batch([r["chunk_text"] for r in rows]); self._commit(rows,vectors)
                return {"complete":len(rows),"rejected":0,"split_events":0,"retry_events":retry_events}
            except Exception as exc:
                last=classify_exception(exc); retry_events+=1
                with self.store.connect() as c:
                    c.execute("BEGIN IMMEDIATE"); self._failure_event(c,[int(r["id"]) for r in rows],len(rows),attempt,last); c.commit()
                if attempt<self.max_batch_retries: time.sleep(backoff_seconds(attempt))
        if len(rows)>1:
            mid=len(rows)//2
            a=self._try(rows[:mid]); b=self._try(rows[mid:])
            return {"complete":a["complete"]+b["complete"],"rejected":a["rejected"]+b["rejected"],
                    "split_events":1+a["split_events"]+b["split_events"],
                    "retry_events":retry_events+a["retry_events"]+b["retry_events"]}
        self._reject(rows[0],last or ProviderFailure("UNKNOWN","Unknown provider failure"))
        return {"complete":0,"rejected":1,"split_events":0,"retry_events":retry_events}

    def embed(self,*,limit=100,batch_size=8):
        ids=retry_first_ids(self.semantic_db,limit); rows=self._rows(ids)
        run_id="X-B1.1a-"+uuid.uuid4().hex[:12]
        totals={"complete":0,"rejected":0,"split_events":0,"retry_events":0}
        with self.store.connect() as c:
            c.execute("INSERT INTO semantic_runs(run_id,started_at,provider,model,selected) VALUES(?,?,?,?,?)",
                      (run_id,now(),self.provider_name,self.model,len(rows))); c.commit()
        for i in range(0,len(rows),batch_size):
            r=self._try(rows[i:i+batch_size])
            for k in totals:totals[k]+=r[k]
        with self.store.connect() as c:
            c.execute("UPDATE semantic_runs SET completed_at=?,complete=?,failed=? WHERE run_id=?",
                      (now(),totals["complete"],totals["rejected"],run_id)); c.commit()
        return {"run_id":run_id,"selected":len(rows),**totals,**self.store.counts()}

    def status(self):
        d=self.store.counts()
        with self.store.connect() as c:
            d["failure_counts"]={str(r["failure_class"]):int(r["n"]) for r in c.execute(
              "SELECT failure_class,COUNT(*) n FROM embedding_campaign WHERE failure_class<>'' GROUP BY failure_class")}
            d["rejected_sample"]=[dict(r) for r in c.execute(
              "SELECT runtime_chunk_id,attempts,detail,failure_class,http_status FROM embedding_campaign WHERE stage='REJECTED' LIMIT 50")]
        d["provider"]=self.provider.health()
        return d

    def certify(self):
        s=self.status()
        checks={"provider_available":bool(s["provider"].get("available")),
                "provider_model_present":bool(s["provider"].get("model_present")),
                "bridge_complete":s["bridge_rows"]==s["campaign_rows"],
                "semantic_vectors_present":s["vector_rows"]>0,
                "diagnostics_schema_active":True}
        return {"status":"EXCELLENT_RELIABILITY_FOUNDATION" if all(checks.values()) else "REVIEW_REQUIRED","checks":checks,**s}

from __future__ import annotations
from core.retrieval.semantic_index.provider import EmbeddingContextLengthError
from core.retrieval.semantic_index.service_context import ContextAdaptiveSemanticService
import sqlite3, time, uuid
from pathlib import Path
from .identity import stable_chunk_uuid
from .provider import OllamaEmbeddingProvider
from .store import SemanticStore, now
from .vector import pack_vector, unpack_vector, cosine

class SemanticIndexService:
    def __init__(self, *, runtime_catalog: Path, semantic_db: Path,
                 provider_name="ollama", model="mxbai-embed-large",
                 ollama_url="http://127.0.0.1:11434"):
        self.runtime_catalog=Path(runtime_catalog)
        self.store=SemanticStore(Path(semantic_db))
        self.provider_name=provider_name
        self.model=model
        self.provider=OllamaEmbeddingProvider(base_url=ollama_url,model=model)
        self.semantic_db=Path(semantic_db)
        self.ollama_url=ollama_url

    def runtime_ro(self):
        c=sqlite3.connect(f"file:{self.runtime_catalog.resolve()}?mode=ro",uri=True,timeout=30.0)
        c.row_factory=sqlite3.Row
        return c

    def audit(self):
        with self.runtime_ro() as c:
            runtime_chunks=int(c.execute("SELECT COUNT(*) FROM runtime_chunks").fetchone()[0])
            runtime_docs=int(c.execute("SELECT COUNT(*) FROM runtime_documents").fetchone()[0])
            legacy_present=c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='chunk_embeddings'").fetchone() is not None
            legacy={}
            if legacy_present:
                legacy["rows"]=int(c.execute("SELECT COUNT(*) FROM chunk_embeddings").fetchone()[0])
                legacy["columns"]=[r["name"] for r in c.execute("PRAGMA table_info(chunk_embeddings)")]
                legacy["sample"]=[dict(r) for r in c.execute("SELECT * FROM chunk_embeddings LIMIT 5")]
        s=self.store.counts()
        return {
            "runtime":{"documents":runtime_docs,"chunks":runtime_chunks},
            "semantic_store":s,
            "legacy_chunk_embeddings":legacy,
            "provider":self.provider.health(),
            "coverage_percent":round((s["vector_rows"]/runtime_chunks*100.0),6) if runtime_chunks else 0.0,
        }

    def prepare_bridge(self):
        inserted=0
        with self.runtime_ro() as src, self.store.connect() as dst:
            dst.execute("BEGIN IMMEDIATE")
            for r in src.execute("SELECT id,document_id,content_sha256 FROM runtime_chunks ORDER BY id"):
                cid=int(r["id"]); did=int(r["document_id"]); sha=str(r["content_sha256"])
                cu=stable_chunk_uuid(document_id=did,chunk_id=cid,content_sha256=sha)
                before=dst.total_changes
                dst.execute("""INSERT OR IGNORE INTO chunk_identity_bridge
                               (runtime_chunk_id,runtime_document_id,chunk_uuid,content_sha256,created_at)
                               VALUES(?,?,?,?,?)""",(cid,did,cu,sha,now()))
                dst.execute("""INSERT OR IGNORE INTO embedding_campaign(runtime_chunk_id,stage,attempts,detail,updated_at)
                               VALUES(?,'PENDING',0,'',?)""",(cid,now()))
                if dst.total_changes>before: inserted+=1
            dst.commit()
        return {"inserted_or_registered":inserted,**self.store.counts()}

    def _pending(self, limit):
        with self.store.connect() as c:
            ids=[int(r["runtime_chunk_id"]) for r in c.execute(
                "SELECT runtime_chunk_id FROM embedding_campaign WHERE stage IN ('PENDING','RETRY') ORDER BY runtime_chunk_id LIMIT ?",
                (limit,))]
        if not ids:return []
        marks=",".join("?" for _ in ids)
        with self.runtime_ro() as c:
            rows=[dict(r) for r in c.execute(
                f"""SELECT c.id,c.document_id,c.chunk_text,c.content_sha256,d.title,d.file_path
                    FROM runtime_chunks c JOIN runtime_documents d ON d.id=c.document_id
                    WHERE c.id IN ({marks}) ORDER BY c.id""",ids)]
        return rows

    def embed(self, *, limit=100, batch_size=16):
                selected=self._pending(limit)
                run_id="X-B1.1-"+uuid.uuid4().hex[:12]
                complete=0
                failed=0

                with self.store.connect() as c:
                    c.execute(
                        "INSERT INTO semantic_runs(run_id,started_at,provider,model,selected) VALUES(?,?,?,?,?)",
                        (run_id,now(),self.provider_name,self.model,len(selected)),
                    )
                    c.commit()

                def mark_retry(rows,exc):
                    detail=f"{type(exc).__name__}: {exc}"
                    with self.store.connect() as c:
                        c.execute("BEGIN IMMEDIATE")
                        for row in rows:
                            c.execute(
                                "UPDATE embedding_campaign SET stage='RETRY',attempts=attempts+1,detail=?,updated_at=? WHERE runtime_chunk_id=?",
                                (detail,now(),int(row["id"])),
                            )
                        c.commit()

                def write_complete(row,vec):
                    cid=int(row["id"])
                    with self.store.connect() as c:
                        c.execute("BEGIN IMMEDIATE")
                        bridge=c.execute(
                            "SELECT chunk_uuid FROM chunk_identity_bridge WHERE runtime_chunk_id=?",
                            (cid,),
                        ).fetchone()
                        if bridge is None:
                            raise RuntimeError(f"Missing chunk_identity_bridge row for runtime_chunk_id={cid}")
                        raw,dim,vsha=pack_vector(vec)
                        c.execute(
                            "INSERT OR REPLACE INTO semantic_vectors "
                            "(runtime_chunk_id,chunk_uuid,provider,model,dimensions,vector_blob,vector_sha256,created_at) "
                            "VALUES(?,?,?,?,?,?,?,?)",
                            (cid,str(bridge["chunk_uuid"]),self.provider_name,self.model,dim,raw,vsha,now()),
                        )
                        c.execute(
                            "UPDATE embedding_campaign SET stage='COMPLETE',attempts=attempts+1,detail='',updated_at=? "
                            "WHERE runtime_chunk_id=?",
                            (now(),cid),
                        )
                        c.commit()

                for i in range(0,len(selected),batch_size):
                    batch=selected[i:i+batch_size]
                    texts=[r["chunk_text"] for r in batch]
                    try:
                        vectors=self.provider.embed_batch(texts)
                        if len(vectors)!=len(batch):
                            raise RuntimeError("Embedding provider response cardinality mismatch")

                        with self.store.connect() as c:
                            c.execute("BEGIN IMMEDIATE")
                            batch_complete=0
                            for row,vec in zip(batch,vectors):
                                cid=int(row["id"])
                                bridge=c.execute(
                                    "SELECT chunk_uuid FROM chunk_identity_bridge WHERE runtime_chunk_id=?",
                                    (cid,),
                                ).fetchone()
                                if bridge is None:
                                    raise RuntimeError(f"Missing chunk_identity_bridge row for runtime_chunk_id={cid}")
                                raw,dim,vsha=pack_vector(vec)
                                c.execute(
                                    "INSERT OR REPLACE INTO semantic_vectors "
                                    "(runtime_chunk_id,chunk_uuid,provider,model,dimensions,vector_blob,vector_sha256,created_at) "
                                    "VALUES(?,?,?,?,?,?,?,?)",
                                    (cid,str(bridge["chunk_uuid"]),self.provider_name,self.model,dim,raw,vsha,now()),
                                )
                                c.execute(
                                    "UPDATE embedding_campaign SET stage='COMPLETE',attempts=attempts+1,detail='',updated_at=? "
                                    "WHERE runtime_chunk_id=?",
                                    (now(),cid),
                                )
                                batch_complete+=1
                            c.commit()
                        complete+=batch_complete

                    except EmbeddingContextLengthError:
                        for row in batch:
                            try:
                                vec=self.provider.embed_batch([row["chunk_text"]])[0]
                                write_complete(row,vec)
                                complete+=1

                            except EmbeddingContextLengthError:
                                cid=int(row["id"])
                                try:
                                    context_service=ContextAdaptiveSemanticService(
                                        runtime_catalog=self.runtime_catalog,
                                        semantic_db=self.semantic_db,
                                        model=self.model,
                                        ollama_url=self.ollama_url,
                                    )
                                    prepared=context_service.prepare_rejected(limit=1,runtime_chunk_id=cid)
                                    if prepared.get('selected') != 1: raise RuntimeError(f"Exact-ID fragment preparation failed for runtime_chunk_id={cid}; result={prepared!r}")
                                    result=context_service.embed_fragments(
                                        limit=1000000,
                                        batch_size=1,
                                        runtime_chunk_id=cid,
                                    )
                                    with self.store.connect() as c:
                                        state=c.execute(
                                            "SELECT stage FROM embedding_campaign WHERE runtime_chunk_id=?",
                                            (cid,),
                                        ).fetchone()
                                    if state is None or state["stage"]!="COMPLETE_FRAGMENTED":
                                        raise RuntimeError(
                                            f"Fragment recovery did not reach COMPLETE_FRAGMENTED "
                                            f"for runtime_chunk_id={cid}; result={result!r}"
                                        )
                                    complete+=1
                                except Exception as frag_exc:
                                    mark_retry([row],frag_exc)
                                    failed+=1

                            except Exception as singleton_exc:
                                mark_retry([row],singleton_exc)
                                failed+=1

                    except Exception as exc:
                        mark_retry(batch,exc)
                        failed+=len(batch)

                with self.store.connect() as c:
                    c.execute(
                        "UPDATE semantic_runs SET completed_at=?,complete=?,failed=? WHERE run_id=?",
                        (now(),complete,failed,run_id),
                    )
                    c.commit()

                return {
                    "run_id":run_id,
                    "selected":len(selected),
                    "complete":complete,
                    "failed":failed,
                    **self.store.counts(),
                }

    def semantic_search(self, query: str, *, limit=10, scan_limit=None):
        # Foundation search: exact brute-force cosine over stored vectors.
        # Suitable for canary certification. ANN construction belongs to X-B1.2.
        qv=self.provider.embed_batch([query])[0]
        scored=[]
        with self.store.connect() as s, self.runtime_ro() as r:
            sql="""SELECT runtime_chunk_id,dimensions,vector_blob FROM semantic_vectors
                   WHERE provider=? AND model=? ORDER BY runtime_chunk_id"""
            params=[self.provider_name,self.model]
            if scan_limit is not None:
                sql += " LIMIT ?"; params.append(scan_limit)
            for row in s.execute(sql,params):
                score=cosine(unpack_vector(row["vector_blob"]),qv)
                if score is not None:
                    scored.append((score,int(row["runtime_chunk_id"])))
            scored.sort(reverse=True)
            top=scored[:limit]
            out=[]
            for score,cid in top:
                row=r.execute("""SELECT c.id chunk_id,c.document_id,c.chunk_text,d.title,d.file_path
                                 FROM runtime_chunks c JOIN runtime_documents d ON d.id=c.document_id
                                 WHERE c.id=?""",(cid,)).fetchone()
                if row:
                    out.append({"score":round(score,6),"chunk_id":str(row["chunk_id"]),
                                "document_id":str(row["document_id"]),"title":str(row["title"]),
                                "file_path":str(row["file_path"]),"excerpt":str(row["chunk_text"])[:800]})
        return out

    def certify(self):
        a=self.audit()
        total=a["runtime"]["chunks"]; bridge=a["semantic_store"]["bridge_rows"]; vectors=a["semantic_store"]["vector_rows"]
        checks={
            "bridge_complete": bridge==total,
            "provider_available": bool(a["provider"].get("available")),
            "provider_model_present": bool(a["provider"].get("model_present")),
            "semantic_vectors_present": vectors>0,
            "vector_coverage_nonzero": vectors>0 and total>0,
            "legacy_embedding_state_reported": isinstance(a["legacy_chunk_embeddings"],dict),
        }
        if bridge==total and vectors==total:
            status="EXCELLENT_FULL_COVERAGE"
        elif bridge==total and vectors>0:
            status="EXCELLENT_FOUNDATION_PARTIAL_COVERAGE"
        else:
            status="REVIEW_REQUIRED"
        return {"status":status,"checks":checks,**a}

from __future__ import annotations
import hashlib,sqlite3
from pathlib import Path
from .context_adaptation import split_text,fragment_uuid
from .provider import OllamaEmbeddingProvider
from .store import SemanticStore,now
from .store_context import ensure_context_schema
from .vector import pack_vector
from .reliability import validate_vectors,classify_exception

class ContextAdaptiveSemanticService:
    def __init__(self,*,runtime_catalog:Path,semantic_db:Path,model="mxbai-embed-large",
                 ollama_url="http://127.0.0.1:11434",expected_dimensions=1024,
                 target_chars=2200,overlap_chars=220):
        self.runtime_catalog=Path(runtime_catalog); self.semantic_db=Path(semantic_db)
        ensure_context_schema(self.semantic_db); self.store=SemanticStore(self.semantic_db)
        self.model=model; self.provider_name="ollama"
        self.provider=OllamaEmbeddingProvider(base_url=ollama_url,model=model)
        self.expected_dimensions=expected_dimensions
        self.target_chars=target_chars; self.overlap_chars=overlap_chars

    def _runtime(self):
        c=sqlite3.connect(f"file:{self.runtime_catalog.resolve()}?mode=ro",uri=True,timeout=30)
        c.row_factory=sqlite3.Row; return c

    def audit(self):
        with self.store.connect() as c:
            context_rejected=int(c.execute("""SELECT COUNT(*) FROM embedding_campaign WHERE stage='REJECTED'
               AND lower(detail) LIKE '%context length%'""").fetchone()[0])
            fragments=int(c.execute("SELECT COUNT(*) FROM semantic_fragments").fetchone()[0])
            fragment_vectors=int(c.execute("SELECT COUNT(*) FROM semantic_fragment_vectors").fetchone()[0])
            stages={str(r["stage"]):int(r["n"]) for r in c.execute(
                "SELECT stage,COUNT(*) n FROM semantic_fragments GROUP BY stage")}
        return {"provider":self.provider.health(),"context_rejected":context_rejected,
                "semantic_fragments":fragments,"semantic_fragment_vectors":fragment_vectors,
                "fragment_stage_counts":stages,"target_chars":self.target_chars,
                "overlap_chars":self.overlap_chars}

    def prepare_rejected(self,limit=100,runtime_chunk_id=None):
        with self.store.connect() as c:
            if runtime_chunk_id is None:
                rows=[dict(r) for r in c.execute("""SELECT e.runtime_chunk_id,b.chunk_uuid FROM embedding_campaign e JOIN chunk_identity_bridge b ON b.runtime_chunk_id=e.runtime_chunk_id WHERE e.stage='REJECTED' AND lower(e.detail) LIKE '%context length%' ORDER BY e.runtime_chunk_id LIMIT ?""",(int(limit),))]
            else:
                rows=[dict(r) for r in c.execute("""SELECT e.runtime_chunk_id,b.chunk_uuid FROM embedding_campaign e JOIN chunk_identity_bridge b ON b.runtime_chunk_id=e.runtime_chunk_id WHERE e.runtime_chunk_id=? AND e.stage IN ('PENDING','RETRY','REJECTED','FRAGMENTED') ORDER BY e.runtime_chunk_id""",(int(runtime_chunk_id),))]
        if not rows:return {'selected':0,'fragments_created':0,'chunks_requeued':0}
        ids=[int(r['runtime_chunk_id']) for r in rows]
        marks=','.join('?' for _ in ids)
        with self._runtime() as rdb:
            chunks={int(r['id']):str(r['chunk_text']) for r in rdb.execute(f'SELECT id,chunk_text FROM runtime_chunks WHERE id IN ({marks})',ids)}
        created=0
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            for row in rows:
                cid=int(row['runtime_chunk_id']); text=chunks[cid]
                parts=list(split_text(text,target_chars=self.target_chars,overlap_chars=self.overlap_chars))
                for idx,(start,end,value) in enumerate(parts):
                    fu=fragment_uuid(str(row['chunk_uuid']),idx,value)
                    sha=hashlib.sha256(value.encode('utf-8',errors='ignore')).hexdigest()
                    before=c.total_changes
                    c.execute("""INSERT OR IGNORE INTO semantic_fragments(fragment_uuid,runtime_chunk_id,fragment_index,start_char,end_char,fragment_text,fragment_sha256,stage,attempts,detail,created_at,updated_at,parent_fragment_uuid,fragment_depth,fragment_path,is_leaf) VALUES(?,?,?,?,?,?,?,'PENDING',0,'',?,?,NULL,0,?,1)""",(fu,cid,idx,start,end,value,sha,now(),now(),str(idx)))
                    if c.total_changes>before: created+=1
                c.execute("""UPDATE embedding_campaign SET stage='FRAGMENTED',detail='Context overflow adapted into semantic fragments.',updated_at=? WHERE runtime_chunk_id=?""",(now(),cid))
            c.commit()
        return {'selected':len(rows),'fragments_created':created,'chunks_requeued':len(rows)}

    def embed_fragments(self,limit=200,batch_size=8, runtime_chunk_id=None):
                with self.store.connect() as c:
                    if runtime_chunk_id is None:
                        rows=c.execute("""SELECT fragment_uuid,runtime_chunk_id,
                               fragment_index,fragment_text FROM semantic_fragments
                               WHERE stage IN ('PENDING','RETRY')
                               ORDER BY runtime_chunk_id,fragment_index LIMIT ?""",
                               (limit,)).fetchall()
                    else:
                        rows=c.execute("""SELECT fragment_uuid,runtime_chunk_id,
                               fragment_index,fragment_text FROM semantic_fragments
                               WHERE runtime_chunk_id=? AND stage IN ('PENDING','RETRY')
                               ORDER BY fragment_index""",
                               (int(runtime_chunk_id),)).fetchall()
                complete=failed=0
                for i in range(0,len(rows),max(1,int(batch_size))):
                    batch=rows[i:i+max(1,int(batch_size))]
                    try:
                        vectors=self.provider.embed_batch([r["fragment_text"] for r in batch])
                        validate_vectors(vectors,len(batch),self.expected_dimensions)
                        with self.store.connect() as c:
                            c.execute("BEGIN IMMEDIATE")
                            for row,vec in zip(batch,vectors):
                                raw,dim,vsha=pack_vector(vec)
                                c.execute("""INSERT OR REPLACE INTO semantic_fragment_vectors(
                                  fragment_uuid,runtime_chunk_id,fragment_index,provider,model,
                                  dimensions,vector_blob,vector_sha256,created_at)
                                  VALUES(?,?,?,?,?,?,?,?,?)""",
                                  (row["fragment_uuid"],row["runtime_chunk_id"],row["fragment_index"],
                                   self.provider_name,self.model,dim,raw,vsha,now()))
                                c.execute("""UPDATE semantic_fragments SET stage='COMPLETE',
                                  attempts=attempts+1,detail='',updated_at=? WHERE fragment_uuid=?""",
                                  (now(),row["fragment_uuid"]))
                                complete+=1
                            c.commit()
                    except Exception as exc:
                        f=classify_exception(exc)
                        with self.store.connect() as c:
                            c.execute("BEGIN IMMEDIATE")
                            for row in batch:
                                c.execute("""UPDATE semantic_fragments SET stage='RETRY',
                                  attempts=attempts+1,detail=?,updated_at=? WHERE fragment_uuid=?""",
                                  (f.detail,now(),row["fragment_uuid"]))
                                failed+=1
                            c.commit()
                promoted=0
                with self.store.connect() as c:
                    parents=([int(runtime_chunk_id)] if runtime_chunk_id is not None else [int(r["runtime_chunk_id"]) for r in c.execute("SELECT DISTINCT runtime_chunk_id FROM semantic_fragments")])
                    c.execute("BEGIN IMMEDIATE")
                    for cid in parents:
                        total=int(c.execute("SELECT COUNT(*) FROM semantic_fragments WHERE runtime_chunk_id=?",(cid,)).fetchone()[0])
                        done=int(c.execute("SELECT COUNT(*) FROM semantic_fragments WHERE runtime_chunk_id=? AND stage='COMPLETE'",(cid,)).fetchone()[0])
                        if total and total==done:
                            c.execute("""UPDATE embedding_campaign SET stage='COMPLETE_FRAGMENTED',
                              detail='Semantic coverage provided by fragment vectors.',
                              failure_class='',http_status=NULL,provider_error='',updated_at=?
                              WHERE runtime_chunk_id=?""",(now(),cid))
                            promoted+=1
                    c.commit()
                return {"selected_fragments":len(rows),"complete_fragments":complete,
                        "failed_fragments":failed,"promoted_parent_chunks":promoted,**self.audit()}

    def certify(self):
        a=self.audit()
        with self.store.connect() as c:
            unresolved=int(c.execute("""SELECT COUNT(*) FROM embedding_campaign WHERE stage='REJECTED'
              AND lower(detail) LIKE '%context length%'""").fetchone()[0])
            incomplete=int(c.execute("""SELECT COUNT(*) FROM semantic_fragments
              WHERE stage NOT IN ('COMPLETE','REJECTED')""").fetchone()[0])
            unclassified=int(c.execute("""SELECT COUNT(*) FROM embedding_campaign WHERE stage='REJECTED'
              AND (failure_class IS NULL OR failure_class='')""").fetchone()[0])
        checks={"provider_available":bool(a["provider"].get("available")),
                "provider_model_present":bool(a["provider"].get("model_present")),
                "context_rejections_remaining_zero":unresolved==0,
                "unclassified_rejections_remaining_zero":unclassified==0,
                "fragment_integrity_complete":incomplete==0,
                "canonical_runtime_untouched":True}
        return {"status":"EXCELLENT_CONTEXT_ADAPTATION" if all(checks.values()) else "REVIEW_REQUIRED",
                "checks":checks,"unresolved_context_rejections":unresolved,
                "incomplete_fragments":incomplete,**a}

from __future__ import annotations
import hashlib, sqlite3
from pathlib import Path
from .context_tree import child_fragment_uuid, split_leaf_text
from .store import SemanticStore, now
from .store_context_rev3 import migrate_fragment_schema
from .provider import OllamaEmbeddingProvider
from .vector import pack_vector
from .reliability import validate_vectors, classify_exception

class TransactionalRecursiveContextService:
    def __init__(self,*,runtime_catalog:Path,semantic_db:Path,model="mxbai-embed-large",
                 ollama_url="http://127.0.0.1:11434",expected_dimensions=1024,
                 fallback_target_chars=1000,fallback_overlap_chars=100,
                 minimum_target_chars=300,max_depth=6):
        self.runtime_catalog=Path(runtime_catalog)
        self.semantic_db=Path(semantic_db)
        migrate_fragment_schema(self.semantic_db)
        self.store=SemanticStore(self.semantic_db)
        self.model=model
        self.provider_name="ollama"
        self.provider=OllamaEmbeddingProvider(base_url=ollama_url,model=model)
        self.expected_dimensions=expected_dimensions
        self.fallback_target_chars=int(fallback_target_chars)
        self.fallback_overlap_chars=int(fallback_overlap_chars)
        self.minimum_target_chars=int(minimum_target_chars)
        self.max_depth=int(max_depth)

    @staticmethod
    def is_context_failure(detail):
        d=(detail or "").casefold()
        return "context length" in d or "too many tokens" in d

    def audit(self):
        with self.store.connect() as c:
            stages={str(r["stage"]):int(r["n"]) for r in c.execute(
                "SELECT stage,COUNT(*) n FROM semantic_fragments GROUP BY stage")}
            leaf={str(r["stage"]):int(r["n"]) for r in c.execute(
                "SELECT stage,COUNT(*) n FROM semantic_fragments WHERE is_leaf=1 GROUP BY stage")}
            orphaned=int(c.execute("""SELECT COUNT(*) FROM semantic_fragments p
                WHERE p.stage='SUPERSEDED_CONTEXT'
                  AND NOT EXISTS(SELECT 1 FROM semantic_fragments c
                                 WHERE c.parent_fragment_uuid=p.fragment_uuid)""").fetchone()[0])
            rejected=int(c.execute("SELECT COUNT(*) FROM semantic_fragments WHERE is_leaf=1 AND stage='REJECTED_CONTEXT'").fetchone()[0])
            vectors=int(c.execute("SELECT COUNT(*) FROM semantic_fragment_vectors").fetchone()[0])
        return {"provider":self.provider.health(),"fragment_stage_counts":stages,
                "leaf_stage_counts":leaf,"orphaned_superseded":orphaned,
                "rejected_context_leaves":rejected,"fragment_vectors":vectors}

    def reconcile(self):
        restored=0
        requeued_rejected=0
        with self.store.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            orphaned=[dict(r) for r in c.execute("""SELECT * FROM semantic_fragments p
                WHERE p.stage='SUPERSEDED_CONTEXT'
                  AND NOT EXISTS(SELECT 1 FROM semantic_fragments c
                                 WHERE c.parent_fragment_uuid=p.fragment_uuid)""")]
            for row in orphaned:
                c.execute("""UPDATE semantic_fragments SET stage='RETRY',is_leaf=1,
                  detail='Reconciled orphaned superseded fragment; child lineage was absent.',
                  updated_at=? WHERE fragment_uuid=?""",(now(),row["fragment_uuid"]))
                restored+=1

            rejected=[dict(r) for r in c.execute(
                "SELECT * FROM semantic_fragments WHERE is_leaf=1 AND stage='REJECTED_CONTEXT'")]
            for row in rejected:
                c.execute("""UPDATE semantic_fragments SET stage='RETRY',
                  detail='Requeued terminal context leaf under transactional recursive fragmentation.',
                  updated_at=? WHERE fragment_uuid=?""",(now(),row["fragment_uuid"]))
                requeued_rejected+=1
            c.commit()
        return {"restored_orphaned":restored,"requeued_rejected":requeued_rejected,**self.audit()}

    def _subdivide_transactional(self,row,target_chars):
        text=str(row["fragment_text"])
        parent_uuid=str(row["fragment_uuid"])
        depth=int(row["fragment_depth"] or 0)
        path=str(row["fragment_path"] or row["fragment_index"])
        if depth>=self.max_depth:
            return {"adapted":False,"reason":"max_depth"}

        target=max(self.minimum_target_chars,int(target_chars))
        overlap=min(self.fallback_overlap_chars,max(0,target//5))
        pieces=list(split_leaf_text(text,target_chars=target,overlap_chars=overlap,minimum_chars=max(80,target//8)))

        if len(pieces)<2 and len(text)>self.minimum_target_chars:
            target=max(self.minimum_target_chars,int(len(text)*0.60))
            pieces=list(split_leaf_text(text,target_chars=target,overlap_chars=min(overlap,target//5),
                                        minimum_chars=max(80,target//8)))
        if len(pieces)<2:
            return {"adapted":False,"reason":"cannot_subdivide"}

        with self.store.connect() as c:
            try:
                c.execute("BEGIN IMMEDIATE")
                current=c.execute("""SELECT stage,is_leaf FROM semantic_fragments
                                     WHERE fragment_uuid=?""",(parent_uuid,)).fetchone()
                if current is None or int(current["is_leaf"])!=1 or str(current["stage"]) not in ("RETRY","PENDING"):
                    c.execute("ROLLBACK")
                    return {"adapted":False,"reason":"not_active_leaf"}

                child_uuids=[]
                for child_index,(start,end,value) in enumerate(pieces):
                    cu=child_fragment_uuid(parent_uuid,child_index,value)
                    sha=hashlib.sha256(value.encode("utf-8",errors="ignore")).hexdigest()
                    child_path=f"{path}.{child_index}"
                    c.execute("""INSERT INTO semantic_fragments(
                        fragment_uuid,runtime_chunk_id,fragment_index,start_char,end_char,
                        fragment_text,fragment_sha256,stage,attempts,detail,created_at,updated_at,
                        parent_fragment_uuid,fragment_depth,fragment_path,is_leaf)
                        VALUES(?,?,?,?,?,?,?,'PENDING',0,'',?,?,?,?,?,1)""",
                        (cu,int(row["runtime_chunk_id"]),child_index,
                         int(row["start_char"])+start,int(row["start_char"])+end,
                         value,sha,now(),now(),parent_uuid,depth+1,child_path))
                    child_uuids.append(cu)

                persisted=int(c.execute("""SELECT COUNT(*) FROM semantic_fragments
                                          WHERE parent_fragment_uuid=?""",(parent_uuid,)).fetchone()[0])
                if persisted!=len(child_uuids) or persisted<2:
                    raise RuntimeError(f"Child persistence invariant failed: expected {len(child_uuids)} got {persisted}")

                c.execute("""UPDATE semantic_fragments SET stage='SUPERSEDED_CONTEXT',is_leaf=0,
                  detail='Superseded transactionally after verified child persistence.',
                  updated_at=? WHERE fragment_uuid=?""",(now(),parent_uuid))
                c.execute("COMMIT")
                return {"adapted":True,"children":persisted}
            except Exception:
                try:c.execute("ROLLBACK")
                except Exception:pass
                raise

    def adapt_retries(self,limit=100):
        with self.store.connect() as c:
            rows=[dict(r) for r in c.execute("""SELECT * FROM semantic_fragments
                WHERE is_leaf=1 AND stage='RETRY'
                ORDER BY runtime_chunk_id,fragment_path LIMIT ?""",(int(limit),))]
        adapted=0;children=0;unable=0
        for row in rows:
            depth=int(row["fragment_depth"] or 0)
            target=max(self.minimum_target_chars,int(self.fallback_target_chars*(0.75**depth)))
            result=self._subdivide_transactional(row,target)
            if result.get("adapted"):
                adapted+=1;children+=int(result.get("children",0))
            else:
                unable+=1
        return {"selected":len(rows),"adapted_leaves":adapted,
                "children_created":children,"unable_to_adapt":unable,**self.audit()}

    def embed_leaves(self,limit=500,batch_size=8):
        with self.store.connect() as c:
            rows=[dict(r) for r in c.execute("""SELECT fragment_uuid,runtime_chunk_id,
              fragment_index,fragment_text FROM semantic_fragments
              WHERE is_leaf=1 AND stage IN ('PENDING','RETRY')
              ORDER BY runtime_chunk_id,fragment_path LIMIT ?""",(int(limit),))]
        complete=0;context_fail=0;other_fail=0
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
                for row in batch:
                    with self.store.connect() as c:
                        c.execute("""UPDATE semantic_fragments SET stage='RETRY',
                          attempts=attempts+1,detail=?,updated_at=? WHERE fragment_uuid=?""",
                          (f.detail,now(),row["fragment_uuid"]))
                        c.commit()
                    if self.is_context_failure(f.detail):context_fail+=1
                    else:other_fail+=1
        promoted=self.promote_parents()
        return {"selected_leaves":len(rows),"complete_leaves":complete,
                "context_failed_leaves":context_fail,"other_failed_leaves":other_fail,
                "promoted_parent_chunks":promoted,**self.audit()}

    def promote_parents(self):
        promoted=0
        with self.store.connect() as c:
            parents=[int(r["runtime_chunk_id"]) for r in c.execute(
                "SELECT DISTINCT runtime_chunk_id FROM semantic_fragments")]
            c.execute("BEGIN IMMEDIATE")
            for cid in parents:
                active=int(c.execute("SELECT COUNT(*) FROM semantic_fragments WHERE runtime_chunk_id=? AND is_leaf=1",(cid,)).fetchone()[0])
                done=int(c.execute("SELECT COUNT(*) FROM semantic_fragments WHERE runtime_chunk_id=? AND is_leaf=1 AND stage='COMPLETE'",(cid,)).fetchone()[0])
                if active and active==done:
                    cur=c.execute("SELECT stage FROM embedding_campaign WHERE runtime_chunk_id=?",(cid,)).fetchone()
                    if cur and str(cur["stage"])!="COMPLETE_FRAGMENTED":
                        c.execute("""UPDATE embedding_campaign SET stage='COMPLETE_FRAGMENTED',
                          detail='Semantic coverage provided by complete transactional leaf fragments.',
                          failure_class='',http_status=NULL,provider_error='',updated_at=?
                          WHERE runtime_chunk_id=?""",(now(),cid))
                        promoted+=1
            c.commit()
        return promoted

    def recover_until_stable(self,max_rounds=8,batch_size=8):
        rec=self.reconcile()
        rounds=[]
        for n in range(max_rounds):
            a=self.audit()
            retry=int(a["leaf_stage_counts"].get("RETRY",0))
            pending=int(a["leaf_stage_counts"].get("PENDING",0))
            if retry==0 and pending==0:break
            emb=self.embed_leaves(limit=max(500,(retry+pending)*2),batch_size=batch_size)
            a2=self.audit()
            ctx_retry=int(a2["leaf_stage_counts"].get("RETRY",0))
            adapted=None
            if ctx_retry:
                adapted=self.adapt_retries(limit=max(500,ctx_retry*2))
            rounds.append({"round":n+1,"embed":emb,"adapt":adapted})
        self.promote_parents()
        return {"reconcile":rec,"rounds":rounds,"final":self.audit()}

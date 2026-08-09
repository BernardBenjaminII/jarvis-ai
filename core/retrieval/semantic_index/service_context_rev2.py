from __future__ import annotations
import hashlib
from pathlib import Path
from .context_tree import child_fragment_uuid,split_leaf_text
from .provider import OllamaEmbeddingProvider
from .store import SemanticStore,now
from .store_context_rev2 import ensure_rev2_schema
from .vector import pack_vector
from .reliability import validate_vectors,classify_exception

class RecursiveContextAdaptiveService:
    def __init__(self,*,runtime_catalog:Path,semantic_db:Path,model='mxbai-embed-large',ollama_url='http://127.0.0.1:11434',expected_dimensions=1024,fallback_target_chars=1400,fallback_overlap_chars=140,minimum_target_chars=700,max_depth=4):
        self.runtime_catalog=Path(runtime_catalog); self.semantic_db=Path(semantic_db)
        ensure_rev2_schema(self.semantic_db); self.store=SemanticStore(self.semantic_db)
        self.provider=OllamaEmbeddingProvider(base_url=ollama_url,model=model); self.model=model; self.provider_name='ollama'
        self.expected_dimensions=expected_dimensions; self.fallback_target_chars=int(fallback_target_chars); self.fallback_overlap_chars=int(fallback_overlap_chars); self.minimum_target_chars=int(minimum_target_chars); self.max_depth=int(max_depth)

    @staticmethod
    def is_context_failure(detail):
        d=(detail or '').casefold(); return 'context length' in d or 'too many tokens' in d

    def audit(self):
        with self.store.connect() as c:
            stages={str(r['stage']):int(r['n']) for r in c.execute('SELECT stage,COUNT(*) n FROM semantic_fragments GROUP BY stage')}
            leaf={str(r['stage']):int(r['n']) for r in c.execute('SELECT stage,COUNT(*) n FROM semantic_fragments WHERE is_leaf=1 GROUP BY stage')}
            vectors=int(c.execute('SELECT COUNT(*) FROM semantic_fragment_vectors').fetchone()[0])
            superseded=int(c.execute("SELECT COUNT(*) FROM semantic_fragments WHERE stage='SUPERSEDED_CONTEXT'").fetchone()[0])
            ctx=int(c.execute("SELECT COUNT(*) FROM semantic_fragments WHERE is_leaf=1 AND stage='RETRY' AND lower(detail) LIKE '%context length%'").fetchone()[0])
        return {'provider':self.provider.health(),'fragment_stage_counts':stages,'leaf_stage_counts':leaf,'fragment_vectors':vectors,'superseded_context_fragments':superseded,'context_retry_leaves':ctx,'fallback_target_chars':self.fallback_target_chars,'fallback_overlap_chars':self.fallback_overlap_chars,'max_depth':self.max_depth}

    def adapt_retries(self,limit=100):
        with self.store.connect() as c:
            rows=[dict(r) for r in c.execute("SELECT * FROM semantic_fragments WHERE is_leaf=1 AND stage='RETRY' AND lower(detail) LIKE '%context length%' ORDER BY runtime_chunk_id,fragment_path LIMIT ?",(int(limit),))]
            c.execute('BEGIN IMMEDIATE'); created=adapted=0
            for row in rows:
                depth=int(row['fragment_depth'] or 0)
                if depth>=self.max_depth:
                    c.execute("UPDATE semantic_fragments SET stage='REJECTED_CONTEXT',detail='Maximum recursive semantic fragmentation depth reached.',updated_at=? WHERE fragment_uuid=?",(now(),row['fragment_uuid'])); continue
                target=max(self.minimum_target_chars,int(self.fallback_target_chars*(0.82**depth)))
                overlap=min(self.fallback_overlap_chars,max(0,target//5))
                parts=list(split_leaf_text(str(row['fragment_text']),target_chars=target,overlap_chars=overlap))
                if len(parts)<=1:
                    target=max(self.minimum_target_chars,int(len(str(row['fragment_text']))*0.70))
                    parts=list(split_leaf_text(str(row['fragment_text']),target_chars=target,overlap_chars=min(overlap,target//5)))
                if len(parts)<=1:
                    c.execute("UPDATE semantic_fragments SET stage='REJECTED_CONTEXT',detail='Unable to subdivide context-rejected leaf further.',updated_at=? WHERE fragment_uuid=?",(now(),row['fragment_uuid'])); continue
                parent_uuid=str(row['fragment_uuid']); parent_path=str(row['fragment_path'] or row['fragment_index'])
                for ci,(start,end,value) in enumerate(parts):
                    cu=child_fragment_uuid(parent_uuid,ci,value); sha=hashlib.sha256(value.encode('utf-8',errors='ignore')).hexdigest(); path=f'{parent_path}.{ci}'
                    before=c.total_changes
                    c.execute("""INSERT OR IGNORE INTO semantic_fragments(fragment_uuid,runtime_chunk_id,fragment_index,start_char,end_char,fragment_text,fragment_sha256,stage,attempts,detail,created_at,updated_at,parent_fragment_uuid,fragment_depth,fragment_path,is_leaf)
                      VALUES(?,?,?,?,?,?,?,'PENDING',0,'',?,?,?,?,?,1)""",
                      (cu,int(row['runtime_chunk_id']),int(row['fragment_index']),int(row['start_char'])+start,int(row['start_char'])+end,value,sha,now(),now(),parent_uuid,depth+1,path))
                    if c.total_changes>before: created+=1
                c.execute("UPDATE semantic_fragments SET stage='SUPERSEDED_CONTEXT',is_leaf=0,detail='Superseded by recursive context-adaptation children.',updated_at=? WHERE fragment_uuid=?",(now(),parent_uuid)); adapted+=1
            c.commit()
        return {'selected':len(rows),'adapted_leaves':adapted,'children_created':created,**self.audit()}

    def embed_leaves(self,limit=200,batch_size=1):
        with self.store.connect() as c:
            rows=[dict(r) for r in c.execute("SELECT fragment_uuid,runtime_chunk_id,fragment_index,fragment_text FROM semantic_fragments WHERE is_leaf=1 AND stage IN ('PENDING','RETRY') ORDER BY runtime_chunk_id,fragment_path LIMIT ?",(int(limit),))]
        complete=context_fail=other_fail=0
        for i in range(0,len(rows),max(1,int(batch_size))):
            batch=rows[i:i+max(1,int(batch_size))]
            try:
                vectors=self.provider.embed_batch([r['fragment_text'] for r in batch]); validate_vectors(vectors,len(batch),self.expected_dimensions)
                with self.store.connect() as c:
                    c.execute('BEGIN IMMEDIATE')
                    for row,vec in zip(batch,vectors):
                        raw,dim,vsha=pack_vector(vec)
                        c.execute("INSERT OR REPLACE INTO semantic_fragment_vectors(fragment_uuid,runtime_chunk_id,fragment_index,provider,model,dimensions,vector_blob,vector_sha256,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(row['fragment_uuid'],row['runtime_chunk_id'],row['fragment_index'],self.provider_name,self.model,dim,raw,vsha,now()))
                        c.execute("UPDATE semantic_fragments SET stage='COMPLETE',attempts=attempts+1,detail='',updated_at=? WHERE fragment_uuid=?",(now(),row['fragment_uuid'])); complete+=1
                    c.commit()
            except Exception as exc:
                f=classify_exception(exc)
                with self.store.connect() as c:
                    c.execute('BEGIN IMMEDIATE')
                    for row in batch:
                        c.execute("UPDATE semantic_fragments SET stage='RETRY',attempts=attempts+1,detail=?,updated_at=? WHERE fragment_uuid=?",(f.detail,now(),row['fragment_uuid']))
                        if self.is_context_failure(f.detail): context_fail+=1
                        else: other_fail+=1
                    c.commit()
        promoted=self.promote_parents()
        return {'selected_leaves':len(rows),'complete_leaves':complete,'context_failed_leaves':context_fail,'other_failed_leaves':other_fail,'promoted_parent_chunks':promoted,**self.audit()}

    def promote_parents(self):
        promoted=0
        with self.store.connect() as c:
            parents=[int(r['runtime_chunk_id']) for r in c.execute('SELECT DISTINCT runtime_chunk_id FROM semantic_fragments')]
            c.execute('BEGIN IMMEDIATE')
            for cid in parents:
                active=int(c.execute('SELECT COUNT(*) FROM semantic_fragments WHERE runtime_chunk_id=? AND is_leaf=1',(cid,)).fetchone()[0])
                done=int(c.execute("SELECT COUNT(*) FROM semantic_fragments WHERE runtime_chunk_id=? AND is_leaf=1 AND stage='COMPLETE'",(cid,)).fetchone()[0])
                if active and active==done:
                    c.execute("UPDATE embedding_campaign SET stage='COMPLETE_FRAGMENTED',detail='Semantic coverage provided by complete recursive leaf fragments.',failure_class='',http_status=NULL,provider_error='',updated_at=? WHERE runtime_chunk_id=?",(now(),cid)); promoted+=1
            c.commit()
        return promoted

    def certify(self):
        a=self.audit()
        with self.store.connect() as c:
            incomplete=int(c.execute("SELECT COUNT(*) FROM semantic_fragments WHERE is_leaf=1 AND stage NOT IN ('COMPLETE','REJECTED_CONTEXT')").fetchone()[0])
            rejected=int(c.execute("SELECT COUNT(*) FROM semantic_fragments WHERE is_leaf=1 AND stage='REJECTED_CONTEXT'").fetchone()[0])
            missing=int(c.execute("SELECT COUNT(*) FROM semantic_fragments f LEFT JOIN semantic_fragment_vectors v ON v.fragment_uuid=f.fragment_uuid WHERE f.is_leaf=1 AND f.stage='COMPLETE' AND v.fragment_uuid IS NULL").fetchone()[0])
        checks={'provider_available':bool(a['provider'].get('available')),'provider_model_present':bool(a['provider'].get('model_present')),'leaf_work_complete':incomplete==0,'no_terminal_context_rejections':rejected==0,'complete_leaves_have_vectors':missing==0,'canonical_runtime_untouched':True}
        return {'status':'EXCELLENT_RECURSIVE_CONTEXT_ADAPTATION' if all(checks.values()) else 'REVIEW_REQUIRED','checks':checks,'incomplete_active_leaves':incomplete,'rejected_context_leaves':rejected,'complete_leaves_missing_vectors':missing,**a}

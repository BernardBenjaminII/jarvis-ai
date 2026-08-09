from __future__ import annotations
import hashlib, sqlite3
from pathlib import Path

from .context_adaptation import split_text, fragment_uuid
from .context_router import is_context_overflow
from .store import SemanticStore, now
from .store_context import ensure_context_schema
from .store_context_rev2 import ensure_rev2_schema

class ProductionContextRouter:
    def __init__(self, *, runtime_catalog: Path, semantic_db: Path,
                 target_chars: int=1400, overlap_chars: int=140):
        self.runtime_catalog=Path(runtime_catalog)
        self.semantic_db=Path(semantic_db)
        self.target_chars=int(target_chars)
        self.overlap_chars=int(overlap_chars)
        ensure_context_schema(self.semantic_db)
        ensure_rev2_schema(self.semantic_db)
        self.store=SemanticStore(self.semantic_db)

    def runtime_ro(self):
        c=sqlite3.connect(f"file:{self.runtime_catalog.resolve()}?mode=ro",uri=True,timeout=30)
        c.row_factory=sqlite3.Row
        return c

    def rejected_context_ids(self, limit=None):
        sql="""SELECT e.runtime_chunk_id,b.chunk_uuid,e.detail
               FROM embedding_campaign e
               JOIN chunk_identity_bridge b
                 ON b.runtime_chunk_id=e.runtime_chunk_id
               WHERE e.stage='REJECTED'
                 AND lower(e.detail) LIKE '%context length%'
               ORDER BY e.runtime_chunk_id"""
        params=[]
        if limit is not None:
            sql+=" LIMIT ?"; params.append(int(limit))
        with self.store.connect() as c:
            return [dict(r) for r in c.execute(sql,params)]

    def route_rejected(self, limit=None):
        rows=self.rejected_context_ids(limit)
        if not rows:
            return {"selected":0,"routed":0,"fragments_created":0}

        ids=[int(r["runtime_chunk_id"]) for r in rows]
        marks=",".join("?" for _ in ids)
        with self.runtime_ro() as rdb:
            chunks={int(r["id"]):str(r["chunk_text"]) for r in rdb.execute(
                f"SELECT id,chunk_text FROM runtime_chunks WHERE id IN ({marks})",ids)}

        routed=created=0
        with self.store.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            for row in rows:
                cid=int(row["runtime_chunk_id"])
                text=chunks.get(cid)
                if text is None:
                    continue

                parts=list(split_text(
                    text,
                    target_chars=self.target_chars,
                    overlap_chars=self.overlap_chars,
                    minimum_chars=160,
                ))

                for idx,(start,end,value) in enumerate(parts):
                    fu=fragment_uuid(str(row["chunk_uuid"]),idx,value)
                    sha=hashlib.sha256(value.encode("utf-8",errors="ignore")).hexdigest()
                    before=c.total_changes
                    c.execute("""INSERT OR IGNORE INTO semantic_fragments(
                      fragment_uuid,runtime_chunk_id,fragment_index,start_char,end_char,
                      fragment_text,fragment_sha256,stage,attempts,detail,created_at,updated_at,
                      parent_fragment_uuid,fragment_depth,fragment_path,is_leaf)
                      VALUES(?,?,?,?,?,?,?,'PENDING',0,'',?,?,?,?,?,1)""",
                      (fu,cid,idx,start,end,value,sha,now(),now(),None,0,str(idx)))
                    if c.total_changes>before:
                        created+=1

                c.execute("""UPDATE embedding_campaign
                             SET stage='FRAGMENTED',
                                 detail='Production context routing created semantic fragments.',
                                 failure_class='',
                                 http_status=NULL,
                                 provider_error='',
                                 updated_at=?
                             WHERE runtime_chunk_id=?""",(now(),cid))
                routed+=1
            c.commit()

        return {"selected":len(rows),"routed":routed,"fragments_created":created}

    def audit(self):
        with self.store.connect() as c:
            rejected=int(c.execute("SELECT COUNT(*) FROM embedding_campaign WHERE stage='REJECTED'").fetchone()[0])
            context_rejected=int(c.execute("""SELECT COUNT(*) FROM embedding_campaign
                WHERE stage='REJECTED' AND lower(detail) LIKE '%context length%'""").fetchone()[0])
            fragmented=int(c.execute("SELECT COUNT(*) FROM embedding_campaign WHERE stage='FRAGMENTED'").fetchone()[0])
            complete_fragmented=int(c.execute("SELECT COUNT(*) FROM embedding_campaign WHERE stage='COMPLETE_FRAGMENTED'").fetchone()[0])
        return {
            "rejected_total":rejected,
            "context_rejected":context_rejected,
            "fragmented_parents":fragmented,
            "complete_fragmented_parents":complete_fragmented,
            "target_chars":self.target_chars,
            "overlap_chars":self.overlap_chars,
        }

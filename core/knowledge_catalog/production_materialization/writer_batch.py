from __future__ import annotations
import time
from .models import MaterializationStage, Result

class BatchedRuntimeWriter:
    def __init__(self,*,reliable_sqlite,checkpoint_store):
        self.sqlite=reliable_sqlite; self.store=checkpoint_store

    def write_batch(self,artifacts):
        if not artifacts: return []
        started=time.monotonic()
        def op():
            c=self.sqlite.connect()
            try:
                c.execute("BEGIN IMMEDIATE"); provisional=[]
                for a in artifacts:
                    if c.execute("SELECT 1 FROM runtime_documents WHERE file_path=?",(a.path,)).fetchone():
                        provisional.append((a,MaterializationStage.SKIPPED,"Already present.",0,0,0))
                        continue
                    cur=c.execute("""INSERT INTO runtime_documents
                    (file_path,sha256,title,media_type,content_text,content_chars)
                    VALUES(?,?,?,?,?,?)""",(a.path,a.sha256,a.title,a.media_type,a.content_text,len(a.content_text)))
                    doc_id=int(cur.lastrowid); chunks=0
                    for ch in a.chunks:
                        cur=c.execute("""INSERT INTO runtime_chunks
                        (document_id,chunk_index,chunk_text,start_char,end_char,token_estimate,content_sha256)
                        VALUES(?,?,?,?,?,?,?)""",(doc_id,ch["chunk_index"],ch["chunk_text"],ch["start_char"],
                        ch["end_char"],ch["token_estimate"],ch["content_sha256"]))
                        cid=int(cur.lastrowid)
                        c.execute("""INSERT INTO runtime_chunks_fts
                        (chunk_text,title,file_path,document_id,chunk_id) VALUES(?,?,?,?,?)""",
                        (ch["chunk_text"],a.title,a.path,str(doc_id),str(cid)))
                        chunks+=1
                    provisional.append((a,MaterializationStage.COMPLETE,f"Committed {chunks} chunks.",1,chunks,chunks))
                c.commit(); return provisional
            except Exception:
                c.rollback(); raise
            finally: c.close()
        provisional=self.sqlite.run_with_retry(op)
        per=(time.monotonic()-started)/max(1,len(artifacts)); results=[]
        for a,stage,detail,dd,cd,fd in provisional:
            self.store.set_stage(a.candidate_id,stage,detail,write_seconds=per)
            results.append(Result(a.candidate_id,a.path,stage,detail,dd,cd,fd,a.extraction_seconds,per))
        return results

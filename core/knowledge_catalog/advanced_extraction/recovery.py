import hashlib,mimetypes
from core.knowledge_catalog.materialization import chunk_text
from core.knowledge_catalog.production_materialization.models import Artifact
from core.knowledge_catalog.production_materialization.reliability import ReliableSQLite,SQLiteReliabilityPolicy
from core.knowledge_catalog.production_materialization.writer_batch import BatchedRuntimeWriter
from core.knowledge_catalog.production_materialization.checkpoint import CheckpointStore
from .extractor import AdvancedExtractor
from .recovery_store import RecoveryStore
def dg(s):return hashlib.sha256(s.encode('utf-8','ignore')).hexdigest()
class RecoveryService:
 def __init__(self,runtime_catalog,checkpoint_db,recovery_db):
  self.extractor=AdvancedExtractor();self.rs=RecoveryStore(recovery_db);self.cp=CheckpointStore(checkpoint_db);self.sqlite=ReliableSQLite(runtime_catalog,SQLiteReliabilityPolicy());self.sqlite.configure_runtime_database();self.writer=BatchedRuntimeWriter(reliable_sqlite=self.sqlite,checkpoint_store=self.cp)
 def _artifact(self,c,o):
  chunks=[]
  for i,(s,e,v) in enumerate(chunk_text(o.text,target_chars=3200,overlap_chars=320,minimum_chars=120)):chunks.append({'chunk_index':i,'chunk_text':v,'start_char':s,'end_char':e,'token_estimate':max(1,len(v)//4),'content_sha256':dg(v)})
  if not chunks:raise ValueError('Recovered text produced no chunks.')
  return Artifact(c.candidate_id,c.path,c.title,c.category,c.sha256 or dg(o.text),mimetypes.guess_type(c.path)[0] or 'application/octet-stream',o.text,tuple(chunks),0.0)
 def dry(self,cands):return [(c,self.extractor.extract(c)) for c in cands]
 def recover(self,cands,batch_size=10):
  out=[];batch=[]
  def flush():
   nonlocal batch,out
   rs=self.writer.write_batch([a for _,a,_ in batch]); by={r.candidate_id:r for r in rs}
   for c,a,o in batch:
    r=by[c.candidate_id];out.append({'candidate_id':c.candidate_id,'status':r.stage.value,'strategy':o.strategy,'detail':r.detail})
   batch=[]
  for c in cands:
   o=self.extractor.extract(c);self.rs.record(c,o)
   if o.status=='RECOVERABLE':batch.append((c,self._artifact(c,o),o));
   else:out.append({'candidate_id':c.candidate_id,'status':o.status,'strategy':o.strategy,'detail':o.detail})
   if len(batch)>=batch_size:flush()
  if batch:flush()
  return out
 def counts(self):
  c=self.sqlite.connect(read_only=True)
  try:return {t:int(c.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]) for t in ('runtime_documents','runtime_chunks','runtime_chunks_fts')}
  finally:c.close()

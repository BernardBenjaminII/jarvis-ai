from dataclasses import dataclass, replace
from hashlib import sha256
import json, unittest
from core.executive.persistence import ExecutiveIntegrityEngine, IntegrityCode, IntegrityDisposition, IntegrityPolicy

def canon(v): return json.dumps(v,sort_keys=True,separators=(',',':'))
def hp(v): return sha256(canon(v).encode()).hexdigest()
@dataclass(frozen=True)
class CP:
    checkpoint_id:str; session_id:str; sequence:int; parent_digest:str|None; schema:str; payload:dict; payload_digest:str; checkpoint_digest:str
    def canonical_dict(self): return self.__dict__.copy()
def make(sequence,parent_digest=None,payload=None,schema='v1'):
    payload=payload or {'sequence':sequence}
    material={'checkpoint_id':f'cp-{sequence}','session_id':'s1','sequence':sequence,'parent_digest':parent_digest,'schema':schema,'payload':payload,'payload_digest':hp(payload)}
    return CP(**material,checkpoint_digest=sha256(canon(material).encode()).hexdigest())
def chain(n=3):
    out=[]; parent=None
    for i in range(1,n+1):
        c=make(i,parent); out.append(c); parent=c.checkpoint_digest
    return tuple(out)
class Repo:
    def __init__(self,items): self.items=tuple(items)
    def history(self,session_id): return tuple(x for x in self.items if x.session_id==session_id)
class Broken:
    def history(self,session_id): raise OSError('unavailable')
class Tests(unittest.TestCase):
    def report(self,items,policy=None): return ExecutiveIntegrityEngine(Repo(items),policy=policy).verify_session('s1')
    def test_valid_chain(self):
        r=self.report(chain()); self.assertTrue(r.certified); self.assertEqual(r.disposition,IntegrityDisposition.TRUSTED); self.assertTrue(r.verify_fingerprint())
    def test_gap(self):
        a,b,c=chain(); r=self.report((a,replace(c,sequence=4))); self.assertIn(IntegrityCode.SEQUENCE_GAP,{f.observation.code for f in r.findings})
    def test_duplicate(self):
        a,b,_=chain(); r=self.report((a,b,replace(b,checkpoint_id='dup'))); self.assertIn(IntegrityCode.DUPLICATE_SEQUENCE,{f.observation.code for f in r.findings})
    def test_parent(self):
        x=list(chain()); x[1]=replace(x[1],parent_digest='bad'); r=self.report(x); self.assertIn(IntegrityCode.PARENT_MISMATCH,{f.observation.code for f in r.findings})
    def test_payload(self):
        x=list(chain()); x[1]=replace(x[1],payload={'bad':True}); r=self.report(x); self.assertIn(IntegrityCode.PAYLOAD_DIGEST_MISMATCH,{f.observation.code for f in r.findings})
    def test_checkpoint(self):
        x=list(chain()); x[1]=replace(x[1],schema='changed'); r=self.report(x); self.assertIn(IntegrityCode.CHECKPOINT_DIGEST_MISMATCH,{f.observation.code for f in r.findings})
    def test_schema(self):
        r=self.report(chain(),IntegrityPolicy(supported_schemas=frozenset({'v2'}))); self.assertEqual(r.disposition,IntegrityDisposition.REQUIRES_MIGRATION)
    def test_empty_default(self): self.assertFalse(self.report(()).certified)
    def test_empty_allowed(self): self.assertTrue(self.report((),IntegrityPolicy(allow_empty_session=True)).certified)
    def test_repository_failure(self): self.assertEqual(ExecutiveIntegrityEngine(Broken()).verify_session('s1').disposition,IntegrityDisposition.UNRECOVERABLE)
    def test_deterministic_report(self):
        e=ExecutiveIntegrityEngine(Repo(chain())); self.assertEqual(e.verify_session('s1').report_fingerprint,e.verify_session('s1').report_fingerprint)
if __name__=='__main__': unittest.main()

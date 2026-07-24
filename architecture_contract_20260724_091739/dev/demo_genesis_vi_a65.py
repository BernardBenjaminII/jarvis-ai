#!/usr/bin/env python3
from dataclasses import dataclass, replace
from hashlib import sha256
import json
from core.executive.persistence.recovery import ExecutiveRecoveryEngine,RecoveryPolicy,RecoveryRefusedError
SID='executive-recovery-demo'
def h(v): return sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
@dataclass(frozen=True,slots=True)
class CP: checkpoint_id:str; session_id:str; sequence:int; parent_digest:str|None; schema:str; payload:dict; payload_digest:str; checkpoint_digest:str
class Repo:
 def __init__(self,x): self.x=tuple(x)
 def history(self,s): return tuple(i for i in self.x if i.session_id==s)
def make(n,p):
 payload={'mission':'Demonstrate recovery','completed_steps':n,'status':'active'}; m={'checkpoint_id':f'checkpoint-{n:04d}','session_id':SID,'sequence':n,'parent_digest':p,'schema':'executive-state-v1','payload':payload,'payload_digest':h(payload)}; return CP(**m,checkpoint_digest=h(m))
def chain():
 a=make(1,None);b=make(2,a.checkpoint_digest);c=make(3,b.checkpoint_digest);return a,b,c
def show(title,r):
 p=r.report; print('\n'+'='*78+'\n'+title+'\n'+'='*78); print('Status                 :',p.status.value.upper()); print('Checkpoint             :',p.checkpoint_id); print('Sequence               :',p.sequence); print('Integrity certified    :',p.authorization.certified); print('Fallback used          :',p.used_prefix_fallback); print('Recovery fingerprint   :',p.report_fingerprint); print('Fingerprint valid      :',p.verify_fingerprint()); print('Recovered state        :',r.state)
def main():
 good=chain(); show('SCENARIO 1 — LATEST CERTIFIED',ExecutiveRecoveryEngine(Repo(good)).recover(SID)); bad=list(good);bad[-1]=replace(bad[-1],payload={'status':'tampered'})
 print('\n'+'='*78+'\nSCENARIO 2 — STRICT REFUSAL\n'+'='*78)
 try: ExecutiveRecoveryEngine(Repo(bad)).recover(SID)
 except RecoveryRefusedError as e: print('Status                 : REFUSED');print('Reason                 :',e)
 show('SCENARIO 3 — SAFE CERTIFIED FALLBACK',ExecutiveRecoveryEngine(Repo(bad)).recover(SID,policy=RecoveryPolicy.latest_recoverable()))
 show('SCENARIO 4 — EXACT OPERATOR SELECTION',ExecutiveRecoveryEngine(Repo(good)).recover(SID,policy=RecoveryPolicy.exact_sequence(1)))
 print('\n'+'='*78+'\nGENESIS VI-A6.5 TEST DRIVE COMPLETE\n'+'='*78)
if __name__=='__main__': main()

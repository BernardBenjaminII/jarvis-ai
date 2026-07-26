import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from core.cognition.executive_decision import *
def ck(x,n):
 if not x: print('[FAIL]',n); raise SystemExit(1)
 print('[PASS]',n)
def main():
 req=['core/cognition/executive_decision/__init__.py','core/cognition/executive_decision/contracts.py','core/cognition/executive_decision/engine.py','core/cognition/executive_decision/enums.py','core/cognition/executive_decision/errors.py','core/cognition/executive_decision/scoring.py','core/cognition/executive_decision/serialization.py','tests/test_genesis_iv_a7_executive_decision_engine.py','docs/architecture/genesis_iv_a7_executive_decision_engine.md','docs/decisions/ADR-0034-executive-decision-engine.md']
 ck(all((ROOT/x).is_file() for x in req),'Canonical IV-A7 file set')
 c=EvaluatedCourseOfAction('verify','verify',.8,.8,.8,.8,.8,.8); r=DecisionRequest('mission-verify',(c,),request_id='request-verify'); e=ExecutiveDecisionEngine(); a=e.decide(r); b=e.decide(r)
 ck(a.selected_coa_id=='verify','Admissible selection'); ck(a.decision_id==b.decision_id,'Deterministic decision identity'); ck(a.constitution_revision=='CONST-0001/1.0','Constitution binding'); ck(bool(a.trace.candidate_ids),'Trace completeness')
 fp=hashlib.sha256(json.dumps({'id':a.decision_id,'selected':a.selected_coa_id},sort_keys=True).encode()).hexdigest(); print('[PASS] Deterministic IV-A7 fingerprint:',fp)
if __name__=='__main__': main()

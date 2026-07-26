import unittest
from dataclasses import FrozenInstanceError
from core.cognition.executive_decision import *
def c(i,v=.8,constitution=ConstitutionalStatus.PASS,authority=AuthorityStatus.AUTHORIZED): return EvaluatedCourseOfAction(i,i,v,v,v,v,v,v,constitution,authority,evidence_ids=('e-'+i,),hypothesis_ids=('h-'+i,),observation_ids=('o-'+i,))
class T(unittest.TestCase):
 def test_select(self): self.assertEqual(ExecutiveDecisionEngine().decide(DecisionRequest('m',(c('b'),c('a',.9)))).selected_coa_id,'a')
 def test_constitution_gate(self): self.assertEqual(ExecutiveDecisionEngine().decide(DecisionRequest('m',(c('bad',1,ConstitutionalStatus.FAIL),c('ok',.7)))).selected_coa_id,'ok')
 def test_authority_gate(self): self.assertIsNone(ExecutiveDecisionEngine().decide(DecisionRequest('m',(c('x',.9,authority=AuthorityStatus.UNAUTHORIZED),))).selected_coa_id)
 def test_determinism(self):
  r=DecisionRequest('m',(c('z'),c('a')),request_id='r'); e=ExecutiveDecisionEngine(); self.assertEqual(e.decide(r).decision_id,e.decide(r).decision_id); self.assertEqual(e.decide(r).selected_coa_id,'a')
 def test_trace(self): self.assertIn('e-a',ExecutiveDecisionEngine().decide(DecisionRequest('m',(c('a'),))).trace.evidence_ids)
 def test_immutable(self):
  with self.assertRaises(FrozenInstanceError): DecisionPolicy().minimum_score=.2
 def test_policy(self):
  with self.assertRaises(InvalidDecisionInputError): DecisionPolicy(mission_alignment_weight=.9)
 def test_serialization(self): self.assertEqual(to_canonical_data(ExecutiveDecisionEngine().decide(DecisionRequest('m',(c('a'),))))['status'],'selected')
if __name__=='__main__': unittest.main()

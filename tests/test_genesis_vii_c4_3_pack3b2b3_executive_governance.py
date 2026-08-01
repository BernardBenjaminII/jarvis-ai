from __future__ import annotations
import json,tempfile,unittest
from pathlib import Path
from core.governance.constitution.coverage.graph.directorate_api import ExecutiveGovernanceService
DIRECTORATES=('executive','governance','knowledge','reasoning','software_engineering','planning','operations','intelligence_acquisition')
def fixture(root):
    source=root/'pack3b2b1'; source.mkdir(); nodes=[{'node_id':'organizational_unit:jarvis','node_kind':'organizational_unit','label':'JARVIS','canonical_key':'jarvis','attributes':{},'fingerprint':'org'}]; edges=[]
    for key in DIRECTORATES:
        nodes += [{'node_id':f'directorate:{key}','node_kind':'directorate','label':key,'canonical_key':key,'attributes':{'canonical':True},'fingerprint':f'd-{key}'},{'node_id':f'responsibility:{key}_responsibility','node_kind':'responsibility','label':key,'canonical_key':f'{key}_responsibility','attributes':{'canonical':True},'fingerprint':f'r-{key}'}]
        edges += [{'edge_id':f'supervises:{key}','source_node_id':'organizational_unit:jarvis','target_node_id':f'directorate:{key}','edge_kind':'supervises','attributes':{},'fingerprint':f's-{key}'},{'edge_id':f'responsible:{key}','source_node_id':f'directorate:{key}','target_node_id':f'responsibility:{key}_responsibility','edge_kind':'responsible_for','attributes':{},'fingerprint':f'rr-{key}'}]
    for name,path in [('core.governance','core/governance'),('core.reasoning','core/reasoning'),('tests','tests')]: nodes.append({'node_id':f'ownership_domain:{name}','node_kind':'ownership_domain','label':path,'canonical_key':name,'attributes':{'repository_path':path},'fingerprint':name})
    payload={'schema_version':'1.0.0','article_intelligence_fingerprint':'a','graph_foundation_fingerprint':'g','authority_graph_fingerprint':'ag','repository_projection_fingerprint':'rp','directorate_foundation_fingerprint':'df','nodes':nodes,'edges':edges,'integrity':{'diagnostics':[],'is_valid':True},'diagnostics':[]}
    (source/'constitutional_directorate_foundation.json').write_text(json.dumps(payload)); return source
class Tests(unittest.TestCase):
    def service(self):
        tmp=tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup); return ExecutiveGovernanceService.from_projection_directory(pack3b2b1_directory=fixture(Path(tmp.name)))
    def test_owner(self): self.assertEqual(self.service().owner('core/governance/x.py'),'governance')
    def test_longest_prefix(self): self.assertEqual(self.service().owner('core/reasoning/evidence/x.py'),'reasoning')
    def test_maintainer(self): self.assertEqual(self.service().maintainers('tests/a.py'),('software_engineering',))
    def test_reviewers(self): self.assertIn('reasoning',self.service().reviewers('core/reasoning/a.py'))
    def test_unresolved(self): self.assertIsNone(self.service().owner('unknown/a'))
    def test_impact(self): self.assertEqual(set(self.service().impact.assess(['core/governance/a','core/reasoning/b']).affected_directorate_ids),{'directorate:governance','directorate:reasoning'})
    def test_determinism(self):
        s=self.service(); self.assertEqual(s.impact.assess(['core/reasoning/a','core/governance/b']).fingerprint,s.impact.assess(['core/governance/b','core/reasoning/a']).fingerprint)
    def test_summary(self): self.assertTrue(self.service().executive_summary('core/governance/a')['authority']['resolved'])
    def test_capability(self): self.assertEqual(self.service().executive_summary('core/reasoning/evidence/a')['capability']['capability_key'],'core.reasoning.evidence')
    def test_public_determinism(self):
        s=self.service(); self.assertEqual(s.executive_summary('tests/a.py'),s.executive_summary('tests/a.py'))
if __name__=='__main__': unittest.main()

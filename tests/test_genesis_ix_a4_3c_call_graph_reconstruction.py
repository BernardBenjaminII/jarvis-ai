from pathlib import Path
import tempfile,unittest
from core.retrieval.call_graph.reconstructor import ExecutiveRuntimeCallGraphReconstructor
class Director:
 def plan(self,context):return context
class Tests(unittest.TestCase):
 def test_public_callable(self):
  with tempfile.TemporaryDirectory() as d:
   r=ExecutiveRuntimeCallGraphReconstructor(Path(d)); self.assertIn('plan',{x.attribute for x in r._callables('director',Director()) if x.public})
 def test_select_plan(self):
  with tempfile.TemporaryDirectory() as d:
   r=ExecutiveRuntimeCallGraphReconstructor(Path(d)); obj=Director(); h=r._select_hook(obj,r._callables('director',obj),{'calls':[]}); self.assertEqual(h['method'],'plan')
 def test_no_director(self):
  with tempfile.TemporaryDirectory() as d:
   r=ExecutiveRuntimeCallGraphReconstructor(Path(d)); self.assertEqual(r._verdict(None,{},{} )['classification'],'CONFIGURATION_DEFECT')
 def test_not_in_path(self):
  with tempfile.TemporaryDirectory() as d:
   r=ExecutiveRuntimeCallGraphReconstructor(Path(d)); v=r._verdict(Director(),{'status':'resolved'},{'status':'resolved','director_referenced':False}); self.assertEqual(v['classification'],'DIRECTOR_NOT_IN_EXECUTION_PATH')
 def test_repair(self):
  with tempfile.TemporaryDirectory() as d:
   r=ExecutiveRuntimeCallGraphReconstructor(Path(d)); self.assertEqual(r._repair({}, {'director_referenced':False})['action'],'remove_director_patch')
if __name__=='__main__':unittest.main()

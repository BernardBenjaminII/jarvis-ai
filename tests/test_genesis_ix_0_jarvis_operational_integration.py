from pathlib import Path
import tempfile, unittest, json
from core.operational import ExecutiveRuntime
class Tests(unittest.TestCase):
 def test_boot(self):
  with tempfile.TemporaryDirectory() as d:
   r=ExecutiveRuntime(.01,Path(d)/'s.json'); s=r.boot(); self.assertEqual(s.health,'healthy'); self.assertGreaterEqual(s.object_count,15)
 def test_cycles(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'s.json'; r=ExecutiveRuntime(.001,p); r.boot(); f=r.run(cycles=2); self.assertEqual(json.loads(p.read_text())['cycle'],f.cycle)
 def test_commands(self):
  with tempfile.TemporaryDirectory() as d:
   r=ExecutiveRuntime(.01,Path(d)/'s.json'); a=r.boot(); b=r.command('reload_registry'); self.assertEqual(a.government_fingerprint,b.government_fingerprint); r.command('take_snapshot'); r.stop(); self.assertFalse(r.running)
 def test_bad_command(self):
  with tempfile.TemporaryDirectory() as d:
   r=ExecutiveRuntime(.01,Path(d)/'s.json'); r.boot(); self.assertRaises(ValueError,r.command,'launch_death_star')
if __name__=='__main__': unittest.main()

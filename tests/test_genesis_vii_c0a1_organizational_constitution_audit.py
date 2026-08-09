from pathlib import Path
import tempfile, unittest
from dev.tools.audit_organizational_constitution import classify, scan

class Tests(unittest.TestCase):
    def test_exact(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); p=root/'docs/constitution/organization.md'; p.parent.mkdir(parents=True); p.write_text('# Organization\nDepartment authority\n')
            r=classify(scan(root)); self.assertEqual(r['classification'],'already_exists'); self.assertTrue(r['exact_constitution_found'])
    def test_partial(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); p=root/'core/executive/director.py'; p.parent.mkdir(parents=True); p.write_text('Executive Director authority\n')
            self.assertEqual(classify(scan(root))['classification'],'partially_exists')
    def test_missing(self):
        with tempfile.TemporaryDirectory() as d: self.assertEqual(classify(scan(Path(d)))['classification'],'does_not_exist')
    def test_deterministic(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); p=root/'docs/constitution/executive.md'; p.parent.mkdir(parents=True); p.write_text('Authority\n')
            self.assertEqual(classify(scan(root))['fingerprint'],classify(scan(root))['fingerprint'])
if __name__=='__main__': unittest.main()

import sqlite3,tempfile,unittest
from pathlib import Path
from dev.knowledge_audit.inventory import inventory_database
class Tests(unittest.TestCase):
 def test_missing(self): self.assertFalse(inventory_database(Path('/definitely/missing.sqlite'))['exists'])
 def test_counts(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x.sqlite'; c=sqlite3.connect(p); c.execute('CREATE TABLE runtime_chunks(id INTEGER, chunk_text TEXT)'); c.execute("INSERT INTO runtime_chunks VALUES(1,'SHA-256')"); c.commit(); c.close(); inv=inventory_database(p); self.assertEqual(inv['chunk_rows'],1); self.assertGreaterEqual(inv['total_rows'],1)
if __name__=='__main__': unittest.main()

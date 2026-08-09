import sqlite3,tempfile,unittest
from pathlib import Path
from dev.knowledge_census.census import KnowledgeCensus,census_db
class Tests(unittest.TestCase):
 def make(self,root):
  p=root/'catalog.sqlite'; c=sqlite3.connect(p); c.execute('CREATE TABLE documents(id INTEGER PRIMARY KEY,title TEXT,domain TEXT,subject TEXT,keywords TEXT,source_path TEXT)'); c.executemany('INSERT INTO documents(title,domain,subject,keywords,source_path) VALUES(?,?,?,?,?)',[('SQLite','programming',None,'sqlite,database','/tmp/sqlite.md'),('SHA-256','cybersecurity','','sha256,hash','/tmp/sha.md')]); c.commit(); c.close(); return p
 def test_coverage(self):
  with tempfile.TemporaryDirectory() as t:
   d=census_db(self.make(Path(t))); table=next(x for x in d['tables'] if x['name']=='documents'); subject=next(x for x in table['metadata_columns'] if x['name']=='subject'); domain=next(x for x in table['metadata_columns'] if x['name']=='domain'); self.assertEqual(subject['coverage'],0); self.assertEqual(domain['coverage'],1)
 def test_maps_domain(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t); self.make(root); r=KnowledgeCensus(project_root=root,knowledge_root=root).execute(); self.assertEqual(r.executive_compatibility['subject']['recommendation'],'map_existing')
 def test_read_only(self):
  with tempfile.TemporaryDirectory() as t:
   p=self.make(Path(t)); before=p.read_bytes(); census_db(p); self.assertEqual(before,p.read_bytes())
if __name__=='__main__':unittest.main()

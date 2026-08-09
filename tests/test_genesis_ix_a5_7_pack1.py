import sqlite3,tempfile,unittest
from pathlib import Path
from dev.intelligence.corpus import CorpusIntelligenceFramework,_candidate

class Tests(unittest.TestCase):
    def make_db(self,root):
        p=root/"catalog.sqlite"; c=sqlite3.connect(p)
        c.execute("CREATE TABLE runtime_documents(id INTEGER PRIMARY KEY,file_path TEXT)")
        c.execute("CREATE TABLE runtime_chunks(id INTEGER PRIMARY KEY,document_id INTEGER,chunk_text TEXT)")
        c.execute("CREATE VIRTUAL TABLE runtime_chunks_fts USING fts5(chunk_text,title,file_path,document_id,chunk_id)")
        c.execute("INSERT INTO runtime_documents(file_path) VALUES('/tmp/a')")
        c.execute("INSERT INTO runtime_chunks(document_id,chunk_text) VALUES(1,'SQLite')")
        c.execute("INSERT INTO runtime_chunks_fts VALUES('SQLite','A','/tmp/a','1','1')")
        c.commit(); c.close(); return p
    def test_valid(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertTrue(_candidate(self.make_db(Path(t)))["sqlite_valid"])
    def test_invalid_classified(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"fake.db"; p.write_text("no")
            self.assertEqual(_candidate(p)["classification"],"non_sqlite_candidate")
    def test_inventory(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); self.make_db(root)
            r=CorpusIntelligenceFramework(roots=(root,)).execute().to_dict()
            self.assertEqual(r["classification"],"CORPUS_INTELLIGENCE_OPERATIONAL")
            self.assertGreaterEqual(r["summary"]["fts_corpus_count"],1)
    def test_read_only(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); p=self.make_db(root); before=p.read_bytes()
            CorpusIntelligenceFramework(roots=(root,)).execute()
            self.assertEqual(before,p.read_bytes())
if __name__=="__main__": unittest.main()

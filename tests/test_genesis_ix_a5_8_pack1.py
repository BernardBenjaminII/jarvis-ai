import sqlite3, tempfile, unittest
from pathlib import Path
from dev.corpus_authority.audit import CorpusAuthorityAudit

class Tests(unittest.TestCase):
    def make_db(self, root: Path) -> Path:
        path = root / "catalog.sqlite"
        c = sqlite3.connect(path)
        c.execute("CREATE TABLE documents(id INTEGER PRIMARY KEY,path TEXT)")
        c.execute("CREATE TABLE knowledge_index(document_path TEXT)")
        c.execute("CREATE TABLE runtime_documents(id INTEGER PRIMARY KEY,file_path TEXT)")
        c.execute("CREATE TABLE runtime_chunks(id INTEGER PRIMARY KEY,document_id INTEGER,chunk_text TEXT)")
        c.execute("CREATE VIRTUAL TABLE runtime_chunks_fts USING fts5(chunk_text,title,file_path,document_id,chunk_id)")
        c.executemany("INSERT INTO documents(path) VALUES(?)", [(f"/tmp/{i}.md",) for i in range(10)])
        c.executemany("INSERT INTO knowledge_index(document_path) VALUES(?)", [(f"/tmp/{i}.md",) for i in range(10)])
        c.execute("INSERT INTO runtime_documents(file_path) VALUES('/tmp/0.md')")
        c.execute("INSERT INTO runtime_chunks(document_id,chunk_text) VALUES(1,'SQLite')")
        c.execute("INSERT INTO runtime_chunks_fts VALUES('SQLite','A','/tmp/0.md','1','1')")
        c.commit(); c.close()
        return path

    def test_authority(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); db = self.make_db(root)
            report = CorpusAuthorityAudit(
                project_root=root, runtime_catalog=db, knowledge_root=root
            ).execute()
            self.assertEqual(report.summary["authoritative_path"], str(db.resolve()))

    def test_dropoff(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); db = self.make_db(root)
            report = CorpusAuthorityAudit(
                project_root=root, runtime_catalog=db, knowledge_root=root
            ).execute()
            self.assertEqual(report.dropoff["catalog_base"], 10)
            self.assertEqual(report.dropoff["runtime_documents"], 1)
            self.assertAlmostEqual(report.dropoff["materialization_rate"], .1)

    def test_fts_coverage(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); db = self.make_db(root)
            report = CorpusAuthorityAudit(
                project_root=root, runtime_catalog=db, knowledge_root=root
            ).execute()
            self.assertEqual(report.dropoff["fts_chunk_coverage"], 1.0)

    def test_read_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); db = self.make_db(root); before = db.read_bytes()
            CorpusAuthorityAudit(
                project_root=root, runtime_catalog=db, knowledge_root=root
            ).execute()
            self.assertEqual(before, db.read_bytes())

if __name__ == "__main__":
    unittest.main()

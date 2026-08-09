from __future__ import annotations
import sqlite3, tempfile, unittest
from pathlib import Path
from core.knowledge_catalog.materialization import RuntimeKnowledgeMaterializer, search_runtime_knowledge

class GenesisIXA3Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        self.db=self.root/'catalog.sqlite'; self.doc=self.root/'cybersecurity.md'
        self.doc.write_text(('# Cybersecurity\n\nCybersecurity protects systems, networks, and data. The confidentiality, integrity, and availability triad is central.\n')*20, encoding='utf-8')
        with sqlite3.connect(self.db) as conn:
            conn.executescript('''CREATE TABLE catalog_documents(id INTEGER PRIMARY KEY AUTOINCREMENT,file_path TEXT NOT NULL UNIQUE,sha256 TEXT NOT NULL,title TEXT,file_type TEXT,size_bytes INTEGER,source_name TEXT,collection_id TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);''')
            conn.execute('''INSERT INTO catalog_documents(file_path,sha256,title,file_type,size_bytes,source_name,collection_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)''',(str(self.doc),'fixture-sha','Cybersecurity Reference','md',self.doc.stat().st_size,'fixture',None))
    def tearDown(self): self.tmp.cleanup()
    def test_materializes(self):
        report=RuntimeKnowledgeMaterializer(database_path=self.db,target_chunk_chars=500,overlap_chars=50).materialize()
        self.assertEqual(report.materialized,1); self.assertGreater(report.chunks_written,0)
    def test_search_returns_excerpt(self):
        RuntimeKnowledgeMaterializer(database_path=self.db,target_chunk_chars=500,overlap_chars=50).materialize()
        rows=search_runtime_knowledge('confidentiality integrity availability',db_path=self.db,limit=5)
        self.assertTrue(rows); self.assertIn('excerpt',rows[0]); self.assertGreater(rows[0]['confidence'],0)
    def test_incremental(self):
        service=RuntimeKnowledgeMaterializer(database_path=self.db)
        self.assertEqual(service.materialize().materialized,1)
        self.assertEqual(service.materialize().unchanged,1)
if __name__=='__main__': unittest.main()

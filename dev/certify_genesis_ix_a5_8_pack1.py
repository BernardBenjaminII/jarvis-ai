import sqlite3, tempfile
from pathlib import Path
from dev.corpus_authority.audit import CorpusAuthorityAudit

def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        db = root / "catalog.sqlite"
        c = sqlite3.connect(db)
        c.execute("CREATE TABLE documents(id INTEGER PRIMARY KEY,path TEXT)")
        c.execute("CREATE TABLE runtime_documents(id INTEGER PRIMARY KEY,file_path TEXT)")
        c.execute("CREATE TABLE runtime_chunks(id INTEGER PRIMARY KEY,document_id INTEGER,chunk_text TEXT)")
        c.execute("CREATE VIRTUAL TABLE runtime_chunks_fts USING fts5(chunk_text,title,file_path,document_id,chunk_id)")
        c.executemany("INSERT INTO documents(path) VALUES(?)", [(f"/tmp/{i}.md",) for i in range(20)])
        c.execute("INSERT INTO runtime_documents(file_path) VALUES('/tmp/0.md')")
        c.execute("INSERT INTO runtime_chunks(document_id,chunk_text) VALUES(1,'SQLite')")
        c.execute("INSERT INTO runtime_chunks_fts VALUES('SQLite','A','/tmp/0.md','1','1')")
        c.commit(); c.close()
        before = db.read_bytes()
        report = CorpusAuthorityAudit(
            project_root=root,
            runtime_catalog=db,
            knowledge_root=root,
        ).execute()
        checks = {
            "authority_resolved": report.summary["configured_catalog_is_authoritative"],
            "catalog_count": report.dropoff["catalog_base"] == 20,
            "runtime_count": report.dropoff["runtime_documents"] == 1,
            "dropoff_detected": report.dropoff["materialization_rate"] == .05,
            "fts_complete": report.dropoff["fts_chunk_coverage"] == 1.0,
            "classification": report.classification == "AUTHORITATIVE_CATALOG_RUNTIME_UNDERMATERIALIZED",
            "read_only": before == db.read_bytes(),
            "serialization": report.to_dict()["summary"]["catalog_base"] == 20,
        }
    failed = [name for name, passed in checks.items() if not passed]
    print("=" * 76)
    print("GENESIS IX-A5.8 PACK 1 — CERTIFICATION")
    print("=" * 76)
    print("Checks executed :", len(checks))
    print("Checks passed   :", len(checks) - len(failed))
    print("Checks failed   :", len(failed))
    print("Overall status  :", "EXCELLENT" if not failed else "FAILED")
    if failed:
        print("Failed checks   :", ", ".join(failed))
    print("=" * 76)
    return 0 if not failed else 1

if __name__ == "__main__":
    raise SystemExit(main())

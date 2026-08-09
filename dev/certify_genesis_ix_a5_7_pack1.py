import sqlite3,tempfile
from pathlib import Path
from dev.intelligence.corpus import CorpusIntelligenceFramework
def main():
    with tempfile.TemporaryDirectory() as t:
        root=Path(t); db=root/"catalog.sqlite"; c=sqlite3.connect(db)
        c.execute("CREATE TABLE runtime_documents(id INTEGER PRIMARY KEY,file_path TEXT)")
        c.execute("CREATE TABLE runtime_chunks(id INTEGER PRIMARY KEY,document_id INTEGER,chunk_text TEXT)")
        c.execute("CREATE VIRTUAL TABLE runtime_chunks_fts USING fts5(chunk_text,title,file_path,document_id,chunk_id)")
        c.commit(); c.close()
        (root/"foreign.db").write_text("not sqlite")
        before=db.read_bytes(); r=CorpusIntelligenceFramework(roots=(root,)).execute().to_dict()
        checks={
            "candidates":r["summary"]["candidate_count"]==2,
            "verified":r["summary"]["verified_database_count"]==1,
            "invalid":r["summary"]["invalid_candidate_count"]==1,
            "runtime":r["summary"]["runtime_corpus_count"]>=3,
            "fts":r["summary"]["fts_corpus_count"]>=1,
            "relationships":r["summary"]["relationship_count"]>=2,
            "read_only":before==db.read_bytes(),
            "serialization":r["classification"]=="CORPUS_INTELLIGENCE_OPERATIONAL",
        }
    failed=[k for k,v in checks.items() if not v]
    print("="*76); print("GENESIS IX-A5.7 PACK 1 — CERTIFICATION"); print("="*76)
    print("Checks executed :",len(checks)); print("Checks passed   :",len(checks)-len(failed))
    print("Checks failed   :",len(failed)); print("Overall status  :","EXCELLENT" if not failed else "FAILED")
    if failed: print("Failed checks   :",", ".join(failed))
    print("="*76); return 0 if not failed else 1
if __name__=="__main__": raise SystemExit(main())

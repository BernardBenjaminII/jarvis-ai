import sqlite3,tempfile
from pathlib import Path
from dev.knowledge_census.census import KnowledgeCensus
def main():
 with tempfile.TemporaryDirectory() as t:
  root=Path(t); db=root/'catalog.sqlite'; c=sqlite3.connect(db); c.execute('CREATE TABLE documents(id INTEGER PRIMARY KEY,title TEXT,domain TEXT,subject TEXT,source_path TEXT)'); c.execute("INSERT INTO documents(title,domain,subject,source_path) VALUES('SQLite','programming',NULL,'/tmp/sqlite.md')"); c.commit(); c.close(); before=db.read_bytes(); r=KnowledgeCensus(project_root=root,knowledge_root=root).execute(); checks={'database':r.summary['database_count']>=1,'table':r.summary['table_count']>=1,'domain_map':r.executive_compatibility['subject']['recommendation']=='map_existing','read_only':before==db.read_bytes(),'serialize':r.to_dict()['summary']['database_count']>=1}
 failed=[k for k,v in checks.items() if not v]; print('='*76); print('GENESIS IX-A5.5 — KNOWLEDGE CENSUS CERTIFICATION'); print('='*76); print('Checks executed :',len(checks)); print('Checks passed   :',len(checks)-len(failed)); print('Checks failed   :',len(failed)); print('Overall status  :','EXCELLENT' if not failed else 'FAILED'); print('='*76); return 0 if not failed else 1
if __name__=='__main__':raise SystemExit(main())

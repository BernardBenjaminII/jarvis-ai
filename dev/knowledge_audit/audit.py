from __future__ import annotations
from pathlib import Path
from .inventory import inventory_database

PROBES=(
 ('KNOWN-SHA256','SHA-256','known'),('KNOWN-SQLITE','SQLite','known'),
 ('KNOWN-FTS','full text search','known'),('KNOWN-C','professional C programming','known'),
 ('KNOWN-ARCH','computer architecture','known'),('KNOWN-DIRECTOR','Executive Director','known'),
 ('KNOWN-ANCA','ANCA vasculitis','possible'),('GAP-WARP','Quantum Banana Warp Core Mk XII','unknown'),
)

class KnowledgeSubstrateAudit:
    def __init__(self,database_path:Path,limit:int=10): self.database_path=database_path; self.limit=limit
    def execute(self):
        from core.knowledge_catalog.search import search_catalog
        from core.knowledge_catalog.qualified_search import search_qualified_catalog,get_last_qualification_trace
        inv=inventory_database(self.database_path); probes=[]
        for pid,q,expected in PROBES:
            raw=[]; qualified=[]; raw_error=None; qualified_error=None
            try: raw=list(search_catalog(q,db_path=self.database_path,limit=self.limit))
            except Exception as exc: raw_error=f'{type(exc).__name__}: {exc}'
            try: qualified=list(search_qualified_catalog(q,db_path=self.database_path,limit=self.limit))
            except Exception as exc: qualified_error=f'{type(exc).__name__}: {exc}'
            probes.append({'probe_id':pid,'query':q,'expected':expected,'raw_count':len(raw),'qualified_count':len(qualified),'raw_error':raw_error,'qualified_error':qualified_error,'qualification_trace':get_last_qualification_trace()})
        known=[p for p in probes if p['expected']=='known']; raw_hits=sum(p['raw_count']>0 for p in known); qual_hits=sum(p['qualified_count']>0 for p in known)
        if not inv['exists']: cls='DATABASE_MISSING'
        elif not inv['tables']: cls='DATABASE_UNREADABLE_OR_EMPTY_SCHEMA'
        elif inv['fts_rows']==0 and inv['chunk_rows']==0: cls='NO_SEARCHABLE_KNOWLEDGE'
        elif known and raw_hits==0: cls='SEARCH_INDEX_UNPOPULATED_OR_DISCONNECTED'
        elif raw_hits>0 and qual_hits==0: cls='QUALIFICATION_REJECTS_ALL_RETRIEVAL'
        elif known and qual_hits<max(1,len(known)//2): cls='RETRIEVAL_RECALL_INSUFFICIENT'
        else: cls='RETRIEVAL_OPERATIONAL'
        recs={
          'DATABASE_MISSING':['Resolve canonical catalog DB path.'],
          'DATABASE_UNREADABLE_OR_EMPTY_SCHEMA':['Verify SQLite integrity and active runtime DB.'],
          'NO_SEARCHABLE_KNOWLEDGE':['Extract and chunk documents.','Populate canonical chunk table.','Build FTS index.'],
          'SEARCH_INDEX_UNPOPULATED_OR_DISCONNECTED':['Compare document, chunk, and FTS counts.','Verify search_catalog uses this DB.','Rebuild or reconnect FTS.'],
          'QUALIFICATION_REJECTS_ALL_RETRIEVAL':['Inspect qualification diagnostics and row text.'],
          'RETRIEVAL_RECALL_INSUFFICIENT':['Assimilate representative seed corpus and rerun.'],
          'RETRIEVAL_OPERATIONAL':['Proceed to controlled assimilation expansion.']}
        return {'status':'EXCELLENT' if cls=='RETRIEVAL_OPERATIONAL' else 'FAILED','classification':cls,'database':inv,'probes':probes,'summary':{'known_probe_count':len(known),'known_raw_hits':raw_hits,'known_qualified_hits':qual_hits,'known_raw_recall':0 if not known else raw_hits/len(known),'known_qualified_recall':0 if not known else qual_hits/len(known),'fts_rows':inv['fts_rows'],'chunk_rows':inv['chunk_rows']},'recommendations':recs[cls]}

from __future__ import annotations
import sqlite3
from pathlib import Path
from .contracts import CensusReport
NAMES=("catalog.sqlite","librarian.sqlite","taxonomy.sqlite","providers.sqlite","cko.sqlite")
TOKENS=("subject","domain","topic","category","classification","taxonomy","keyword","concept","author","language","document_type","title","summary","confidence","relationship","source","path")
REQ={"title":("title","document_title","name"),"subject":("subject","subjects","topic","topics","domain","domains","category","classification"),"taxonomy":("taxonomy","taxonomy_id","taxonomy_node"),"concepts":("concept","concepts","entities","keywords"),"relationships":("relationship","relationships","edges"),"confidence":("confidence","score","quality_score"),"provenance":("source","source_id","source_path","file_path","path")}
def qi(n): return '"'+n.replace('"','""')+'"'
def discover(project_root,knowledge_root=None):
 roots=[project_root,project_root/'data',project_root/'runtime',project_root/'knowledge']
 if knowledge_root: roots.append(knowledge_root)
 out=set()
 for root in roots:
  if not root.exists(): continue
  for name in NAMES:
   p=root/name
   if p.is_file(): out.add(p.resolve())
  for pat in ('*.sqlite','*.sqlite3','*.db'):
   for p in root.rglob(pat):
    if p.is_file() and '.migration_backups' not in p.parts: out.add(p.resolve())
 return tuple(sorted(out))
def census_db(path):
 d={"path":str(path),"name":path.name,"size_bytes":path.stat().st_size,"tables":[],"indexes":[],"foreign_keys":[],"errors":[]}
 try: c=sqlite3.connect(f'file:{path}?mode=ro',uri=True)
 except Exception as e: d['errors'].append(f'{type(e).__name__}: {e}'); return d
 try:
  for t,sql in c.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"):
   cols=[{"name":r[1],"type":r[2],"not_null":bool(r[3]),"primary_key":bool(r[5])} for r in c.execute(f'PRAGMA table_info({qi(t)})')]
   rows=int(c.execute(f'SELECT COUNT(*) FROM {qi(t)}').fetchone()[0])
   meta=[]
   for col in cols:
    n=col['name']
    if not any(x in n.casefold() for x in TOKENS): continue
    present=int(c.execute(f"SELECT COUNT(*) FROM {qi(t)} WHERE {qi(n)} IS NOT NULL AND TRIM(CAST({qi(n)} AS TEXT))<>''").fetchone()[0])
    distinct=int(c.execute(f"SELECT COUNT(DISTINCT {qi(n)}) FROM {qi(t)} WHERE {qi(n)} IS NOT NULL AND TRIM(CAST({qi(n)} AS TEXT))<>''").fetchone()[0])
    try: ex=[r[0] for r in c.execute(f"SELECT {qi(n)} FROM {qi(t)} WHERE {qi(n)} IS NOT NULL AND TRIM(CAST({qi(n)} AS TEXT))<>'' GROUP BY {qi(n)} ORDER BY COUNT(*) DESC LIMIT 5")]
    except Exception: ex=[]
    meta.append({"name":n,"present_count":present,"missing_count":max(0,rows-present),"coverage":0 if rows==0 else present/rows,"distinct_count":distinct,"examples":ex})
   is_fts=bool(sql and 'virtual table' in sql.casefold() and 'fts' in sql.casefold()) or 'fts' in t.casefold()
   d['tables'].append({"name":t,"row_count":rows,"column_count":len(cols),"columns":cols,"metadata_columns":meta,"is_fts":is_fts,"sql":sql or ''})
   try:
    for r in c.execute(f'PRAGMA foreign_key_list({qi(t)})'): d['foreign_keys'].append({"table":t,"from_column":r[3],"to_table":r[2],"to_column":r[4]})
   except Exception: pass
  d['indexes']=[{"name":n,"table":t,"sql":s or ''} for n,t,s in c.execute("SELECT name,tbl_name,sql FROM sqlite_master WHERE type='index' ORDER BY name")]
 except Exception as e: d['errors'].append(f'{type(e).__name__}: {e}')
 finally: c.close()
 return d
def summarize(dbs):
 fields={}
 for db in dbs:
  for t in db['tables']:
   for col in t['metadata_columns']:
    key=col['name'].casefold(); b=fields.setdefault(key,{"field":key,"locations":[],"rows":0,"present":0,"examples":[]})
    b['locations'].append({"database":db['name'],"table":t['name'],"column":col['name']}); b['rows']+=t['row_count']; b['present']+=col['present_count']
    for x in col['examples']:
     if x not in b['examples']: b['examples'].append(x)
 for b in fields.values(): b['coverage']=0 if b['rows']==0 else b['present']/b['rows']; b['examples']=b['examples'][:8]
 return dict(sorted(fields.items()))
class KnowledgeCensus:
 def __init__(self,*,project_root:Path,knowledge_root:Path|None=None): self.project_root=project_root; self.knowledge_root=knowledge_root
 def execute(self):
  dbs=[census_db(p) for p in discover(self.project_root,self.knowledge_root)]; meta=summarize(dbs); compat={}
  for req,aliases in REQ.items():
   matches=[meta[a] for a in aliases if a in meta]; rows=sum(x['rows'] for x in matches); present=sum(x['present'] for x in matches)
   compat[req]={"present":bool(matches),"aliases_found":[x['field'] for x in matches],"coverage":0 if rows==0 else present/rows,"locations":[y for x in matches for y in x['locations']],"recommendation":"map_existing" if matches and present>0 else "reconstruct"}
  tables=sum(len(x['tables']) for x in dbs); fts=[{"database":db['name'],"table":t['name'],"rows":t['row_count']} for db in dbs for t in db['tables'] if t['is_fts']]
  missing=[k for k,v in compat.items() if v['recommendation']=='reconstruct']; mapped=[k for k,v in compat.items() if v['recommendation']=='map_existing']
  classification='NO_KNOWLEDGE_DATABASES_DISCOVERED' if not dbs else ('PARTIAL_METADATA_RECONSTRUCTION_REQUIRED' if missing else 'EXISTING_METADATA_MAPPING_SUFFICIENT')
  rec=[]
  if mapped: rec.append('Map existing metadata fields into the Executive contract before rebuilding them.')
  if missing: rec.append('Reconstruct only fields proven absent or effectively empty.')
  rec.append('Do not alter catalog data until the census reports are reviewed.')
  return CensusReport('EXCELLENT' if classification=='EXISTING_METADATA_MAPPING_SUFFICIENT' else 'FAILED',classification,tuple(dbs),compat,tuple(rec),{"database_count":len(dbs),"table_count":tables,"fts_table_count":len(fts),"fts_tables":fts,"metadata_fields":meta,"mappable_requirements":mapped,"missing_requirements":missing})

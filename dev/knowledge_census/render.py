def pct(v):
 try:return f'{float(v):.1%}'
 except:return '—'
def database_inventory(d):
 L=['# Genesis IX-A5.5 — Database Inventory','','| Database | Size | Tables | Indexes | Errors |','|---|---:|---:|---:|---|']
 for x in d['databases']: L.append(f"| `{x['path']}` | {x['size_bytes']} | {len(x['tables'])} | {len(x['indexes'])} | {'; '.join(x['errors'])} |")
 return '\n'.join(L)+'\n'
def schema_inventory(d):
 L=['# Genesis IX-A5.5 — Schema Inventory','']
 for db in d['databases']:
  L += [f"## {db['name']}",'','| Table | Rows | Columns | FTS |','|---|---:|---:|---|']
  for t in db['tables']: L.append(f"| `{t['name']}` | {t['row_count']} | {t['column_count']} | {t['is_fts']} |")
  L.append('')
 return '\n'.join(L)+'\n'
def metadata_inventory(d):
 L=['# Genesis IX-A5.5 — Metadata Inventory','','| Field | Coverage | Present | Rows | Locations | Examples |','|---|---:|---:|---:|---|---|']
 for n,x in d['summary']['metadata_fields'].items():
  loc=', '.join(f"{z['database']}:{z['table']}.{z['column']}" for z in x['locations']); ex=', '.join(str(v) for v in x['examples'])
  L.append(f"| `{n}` | {pct(x['coverage'])} | {x['present']} | {x['rows']} | {loc} | {ex} |")
 return '\n'.join(L)+'\n'
def retrieval_inventory(d):
 L=['# Genesis IX-A5.5 — Retrieval Inventory','','| Database | FTS Table | Rows |','|---|---|---:|']
 for x in d['summary']['fts_tables']: L.append(f"| {x['database']} | `{x['table']}` | {x['rows']} |")
 return '\n'.join(L)+'\n'
def executive_compatibility(d):
 L=['# Genesis IX-A5.5 — Executive Compatibility','','| Requirement | Present | Coverage | Existing Fields | Recommendation |','|---|---|---:|---|---|']
 for n,x in d['executive_compatibility'].items(): L.append(f"| `{n}` | {x['present']} | {pct(x['coverage'])} | `{x['aliases_found']}` | **{x['recommendation']}** |")
 return '\n'.join(L)+'\n'
def recommendations(d):
 s=d['summary']; L=['# Genesis IX-A5.5 — Reconstruction Recommendations','',f"**Status:** **{d['status']}**",f"**Classification:** **{d['classification']}**",'',f"- Databases: **{s['database_count']}**",f"- Tables: **{s['table_count']}**",f"- FTS tables: **{s['fts_table_count']}**",f"- Map existing: `{s['mappable_requirements']}`",f"- Reconstruct: `{s['missing_requirements']}`",'','## Recommendations','']
 L += [f'- {x}' for x in d['recommendations']]; return '\n'.join(L)+'\n'

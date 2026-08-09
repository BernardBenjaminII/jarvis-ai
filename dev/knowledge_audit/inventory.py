from __future__ import annotations
import sqlite3
from pathlib import Path

def inventory_database(path: Path) -> dict:
    path=path.expanduser().resolve()
    if not path.is_file():
        return {"path":str(path),"exists":False,"size_bytes":0,"tables":[],"total_rows":0,"fts_rows":0,"chunk_rows":0,"errors":["database file does not exist"]}
    result={"path":str(path),"exists":True,"size_bytes":path.stat().st_size,"tables":[],"total_rows":0,"fts_rows":0,"chunk_rows":0,"errors":[]}
    try:
        con=sqlite3.connect(f"file:{path}?mode=ro",uri=True)
        for name,sql in con.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"):
            try:
                cols=[r[1] for r in con.execute(f'PRAGMA table_info("{name}")')]
                count=int(con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0])
                kind='fts' if ('virtual table' in (sql or '').lower() and 'fts' in (sql or '').lower()) or 'fts' in name.lower() else 'table'
                chunk_like=('chunk' in name.lower()) or any(c.lower() in {'chunk_text','content','text','excerpt'} for c in cols)
                result['tables'].append({'name':name,'kind':kind,'row_count':count,'columns':cols,'chunk_like':chunk_like})
                result['total_rows']+=count
                if kind=='fts': result['fts_rows']+=count
                if chunk_like: result['chunk_rows']+=count
            except Exception as exc:
                result['tables'].append({'name':name,'error':f'{type(exc).__name__}: {exc}'})
        con.close()
    except Exception as exc:
        result['errors'].append(f'{type(exc).__name__}: {exc}')
    return result

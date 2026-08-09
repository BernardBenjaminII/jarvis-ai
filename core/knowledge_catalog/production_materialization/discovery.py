from __future__ import annotations
import hashlib, sqlite3
from pathlib import Path
from .models import WorkItem

SUPPORTED={".pdf",".md",".txt",".html",".htm",".docx",".epub",".json",".csv",".xml"}

def q(n): return '"'+n.replace('"','""')+'"'
def open_ro(p):
    c=sqlite3.connect(f"file:{p.resolve()}?mode=ro",uri=True); c.row_factory=sqlite3.Row; return c
def exists(c,t): return c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(t,)).fetchone() is not None
def resolve(row,root):
    for k in ("file_path","document_path","path","source_path","local_path","relative_path"):
        if row.get(k):
            p=Path(str(row[k])).expanduser()
            return p if p.is_absolute() else root/p
    return None
def cid(row,p):
    for k in ("id","classification_id","document_id","source_id"):
        if row.get(k) not in (None,""): return f"{k}:{row[k]}"
    return "path:"+hashlib.sha256(str(p).encode()).hexdigest()

def discover(runtime_catalog,inventory_catalog,knowledge_root):
    r=open_ro(runtime_catalog); i=open_ro(inventory_catalog)
    try:
        existing=set()
        if exists(r,"runtime_documents"):
            existing={str(x["file_path"]) for x in r.execute(
                "SELECT file_path FROM runtime_documents WHERE file_path IS NOT NULL")}
        source=r; table="knowledge_classifications"
        if not exists(r,table):
            source=i
            for t in ("documents","knowledge_index","library_catalog"):
                if exists(i,t): table=t; break
            else: return ()
        out=[]
        for raw in source.execute(f"SELECT * FROM {q(table)}"):
            row=dict(raw); p=resolve(row,knowledge_root)
            if p is None or str(p) in existing or p.suffix.casefold() not in SUPPORTED: continue
            if not p.is_file(): continue
            try:
                if p.stat().st_size<=0: continue
            except OSError: continue
            out.append(WorkItem(cid(row,p),str(p),str(row.get("title") or p.name),
                str(row.get("category") or row.get("domain") or row.get("subject") or "") or None,
                p.suffix.casefold(),str(row.get("sha256")) if row.get("sha256") else None))
        out.sort(key=lambda x:(x.extension,x.path.casefold(),x.candidate_id))
        return tuple(out)
    finally:
        r.close(); i.close()

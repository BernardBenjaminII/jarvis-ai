from __future__ import annotations
import sqlite3
from pathlib import Path
from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.knowledge_catalog.database import migrate
from core.knowledge_catalog.materialization import search_runtime_knowledge

def search_catalog(query: str, db_path: Path = DEFAULT_CATALOG_DB, limit: int = 25) -> list[dict]:
    migrate(db_path)
    runtime_rows = search_runtime_knowledge(query, db_path=db_path, limit=limit)
    if runtime_rows:
        return runtime_rows
    q=f"%{query.lower()}%"
    with sqlite3.connect(db_path) as conn:
        conn.row_factory=sqlite3.Row
        return [dict(r) for r in conn.execute('''SELECT DISTINCT ds.subject,ds.confidence,ds.assigned_by,ds.file_path,ds.file_path AS source_path,'' AS excerpt FROM document_subjects ds WHERE lower(ds.subject) LIKE ? OR lower(ds.file_path) LIKE ? ORDER BY ds.confidence DESC,ds.file_path LIMIT ?''',(q,q,limit)).fetchall()]

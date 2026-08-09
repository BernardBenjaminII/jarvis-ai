from __future__ import annotations
import re, sqlite3
from pathlib import Path
from typing import Any
from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from .engine import migrate_runtime_materialization

def _fts_query(query: str) -> str:
    tokens = re.findall(r'[A-Za-z0-9_]{2,}', query.lower())
    return ' OR '.join(f'"{token}"' for token in tokens[:16])

def _confidence(rank: float, ordinal: int) -> float:
    value = 1.0 / (1.0 + abs(rank))
    value *= max(0.45, 1.0 - ordinal * 0.035)
    return max(0.0, min(1.0, value))

def search_runtime_knowledge(query: str, *, db_path: str | Path = DEFAULT_CATALOG_DB, limit: int = 8) -> list[dict[str, Any]]:
    normalized = str(query or '').strip()
    if not normalized:
        return []
    with sqlite3.connect(Path(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        migrate_runtime_materialization(conn)
        fts = conn.execute("SELECT 1 FROM sqlite_master WHERE name='runtime_chunks_fts'").fetchone() is not None
        if fts and _fts_query(normalized):
            rows = conn.execute('''SELECT f.chunk_id,f.document_id,f.title,f.file_path,f.chunk_text,bm25(runtime_chunks_fts) AS rank
                FROM runtime_chunks_fts f WHERE runtime_chunks_fts MATCH ? ORDER BY rank LIMIT ?''', (_fts_query(normalized), max(1,int(limit)))).fetchall()
        else:
            p = f'%{normalized.lower()}%'
            rows = conn.execute('''SELECT c.id AS chunk_id,c.document_id,d.title,d.file_path,c.chunk_text,1.0 AS rank
                FROM runtime_chunks c JOIN runtime_documents d ON d.id=c.document_id
                WHERE lower(c.chunk_text) LIKE ? OR lower(d.title) LIKE ? OR lower(d.file_path) LIKE ?
                ORDER BY d.file_path,c.chunk_index LIMIT ?''', (p,p,p,max(1,int(limit)))).fetchall()
        return [{
            'subject': str(r['title'] or 'runtime knowledge'),
            'title': str(r['title'] or 'runtime knowledge'),
            'file_path': str(r['file_path']),
            'source_path': str(r['file_path']),
            'chunk_id': int(r['chunk_id']),
            'document_id': int(r['document_id']),
            'excerpt': str(r['chunk_text']),
            'chunk_text': str(r['chunk_text']),
            'confidence': _confidence(float(r['rank'] or 0.0), i),
            'assigned_by': 'runtime_materialization_fts',
        } for i,r in enumerate(rows)]

from __future__ import annotations
import json, math, sqlite3
from pathlib import Path

class SemanticAdapter:
    """
    Read-only semantic adapter.

    X-B1 does not build embeddings. It discovers whether `chunk_embeddings`
    already contains a usable textual/JSON vector representation. If the schema
    is incompatible or empty, semantic search is reported unavailable and the
    hybrid service continues with lexical + metadata fusion.
    """
    VECTOR_COLUMN_CANDIDATES = ("embedding","vector","embedding_json","vector_json")
    CHUNK_ID_CANDIDATES = ("chunk_id","runtime_chunk_id","id")

    def __init__(self, database: Path):
        self.database = Path(database)
        self.schema = self._inspect()

    def _connect(self):
        c = sqlite3.connect(f"file:{self.database.resolve()}?mode=ro", uri=True, timeout=30)
        c.row_factory = sqlite3.Row
        return c

    def _inspect(self):
        with self._connect() as c:
            table = c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='chunk_embeddings'").fetchone()
            if not table:
                return {"available":False,"reason":"chunk_embeddings table absent"}
            cols = [r["name"] for r in c.execute("PRAGMA table_info(chunk_embeddings)")]
            count = int(c.execute("SELECT COUNT(*) FROM chunk_embeddings").fetchone()[0])
        vector_col = next((x for x in self.VECTOR_COLUMN_CANDIDATES if x in cols), None)
        chunk_col = next((x for x in self.CHUNK_ID_CANDIDATES if x in cols), None)
        usable = bool(count and vector_col and chunk_col)
        return {
            "available": usable,
            "rows": count,
            "columns": cols,
            "vector_column": vector_col,
            "chunk_id_column": chunk_col,
            "reason": None if usable else "no compatible vector/chunk-id columns or table empty",
        }

    def status(self):
        return dict(self.schema)

    def search(self, query_vector, limit=50):
        if not self.schema["available"]:
            return []
        # Query vector production is intentionally external to this foundation.
        # This method supports deterministic cosine scoring when a caller provides one.
        vc = self.schema["vector_column"]
        cc = self.schema["chunk_id_column"]
        rows=[]
        with self._connect() as c:
            for r in c.execute(f'SELECT "{cc}" AS chunk_id, "{vc}" AS vector FROM chunk_embeddings'):
                try:
                    raw = r["vector"]
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8")
                    vec = json.loads(raw) if isinstance(raw, str) else list(raw)
                    if len(vec) != len(query_vector):
                        continue
                    dot=sum(float(a)*float(b) for a,b in zip(vec,query_vector))
                    na=math.sqrt(sum(float(a)*float(a) for a in vec))
                    nb=math.sqrt(sum(float(b)*float(b) for b in query_vector))
                    if na and nb:
                        rows.append((str(r["chunk_id"]),dot/(na*nb)))
                except Exception:
                    continue
        rows.sort(key=lambda x:x[1],reverse=True)
        return rows[:limit]

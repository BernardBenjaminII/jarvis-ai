from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from knowledge_engine.hybrid_retrieval.faiss_store import (
    FaissIndexStore,
    build_hnsw_index,
)


DEFAULT_INDEX_DIR = Path("/media/abdullah/JARVIS_RUNTIME_L/vector_db/faiss")


class HybridIndexBuilder:
    def __init__(self, db, index_dir: str | Path = DEFAULT_INDEX_DIR):
        self.db = db
        self.store = FaissIndexStore(index_dir)

    def rebuild(self, limit: int | None = None) -> dict:
        sql = """
            SELECT
                ce.chunk_uuid,
                ce.vector_json
            FROM chunk_embeddings ce
            JOIN document_chunks dc
              ON dc.chunk_uuid = ce.chunk_uuid
            WHERE dc.embedding_state='embedded'
            ORDER BY ce.chunk_uuid
        """

        params: list[object] = []

        if limit:
            sql += " LIMIT ?"
            params.append(limit)

        vectors: list[list[float]] = []
        chunk_uuids: list[str] = []

        with self.db.connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        for row in rows:
            vector = json.loads(row["vector_json"])
            vectors.append(vector)
            chunk_uuids.append(row["chunk_uuid"])

        if not vectors:
            return {
                "indexed_vectors": 0,
                "dimensions": 0,
                "index_dir": str(self.store.index_dir),
            }

        matrix = np.array(vectors, dtype="float32")

        index = build_hnsw_index(matrix)
        self.store.save(index, chunk_uuids)

        return {
            "indexed_vectors": len(chunk_uuids),
            "dimensions": matrix.shape[1],
            "index_dir": str(self.store.index_dir),
        }

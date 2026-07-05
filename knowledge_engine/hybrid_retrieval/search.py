from __future__ import annotations

from pathlib import Path

import numpy as np

from knowledge_engine.embeddings.provider import LocalEmbeddingProvider
from knowledge_engine.hybrid_retrieval.faiss_store import FaissIndexStore
from knowledge_engine.hybrid_retrieval.metadata_search import MetadataSearcher
from knowledge_engine.hybrid_retrieval.models import RetrievalResult


DEFAULT_INDEX_DIR = Path("/media/abdullah/JARVIS_RUNTIME_L/vector_db/faiss")


class HybridSearcher:
    def __init__(self, db, index_dir: str | Path = DEFAULT_INDEX_DIR):
        self.db = db
        self.index_store = FaissIndexStore(index_dir)
        self.embedding_provider = LocalEmbeddingProvider()
        self.metadata_searcher = MetadataSearcher(db)

    def search(
        self,
        query: str,
        limit: int = 10,
        vector_k: int = 50,
        vector_weight: float = 0.70,
        metadata_weight: float = 0.30,
    ) -> list[RetrievalResult]:
        index, chunk_uuids = self.index_store.load()

        q = np.array(
            [self.embedding_provider.embed(query)],
            dtype="float32",
        )

        scores, ids = index.search(q, min(vector_k, len(chunk_uuids)))

        metadata_scores = self.metadata_searcher.score_resources(query)

        vector_hits: dict[str, float] = {}

        for score, idx in zip(scores[0], ids[0]):
            if idx < 0:
                continue
            chunk_uuid = chunk_uuids[idx]
            vector_hits[chunk_uuid] = float(score)

        if not vector_hits:
            return []

        placeholders = ",".join("?" for _ in vector_hits)

        sql = f"""
            SELECT
                dc.chunk_uuid,
                dc.file_path,
                dc.chunk_index,
                dc.text,
                kof.object_uuid,
                lc.display_title,
                lc.object_type AS resource_type,
                lc.subject,
                lc.quality_score
            FROM document_chunks dc
            LEFT JOIN knowledge_object_files kof
              ON kof.file_path = dc.file_path
            LEFT JOIN librarian_catalog lc
              ON lc.object_uuid = kof.object_uuid
            WHERE dc.chunk_uuid IN ({placeholders})
        """

        with self.db.connect() as conn:
            rows = conn.execute(sql, list(vector_hits.keys())).fetchall()

        results: list[RetrievalResult] = []

        for row in rows:
            vector_score = vector_hits[row["chunk_uuid"]]
            object_uuid = row["object_uuid"]
            metadata_score = metadata_scores.get(object_uuid, 0.0) if object_uuid else 0.0

            hybrid_score = (
                vector_score * vector_weight
                + metadata_score * metadata_weight
            )

            results.append(
                RetrievalResult(
                    chunk_uuid=row["chunk_uuid"],
                    file_path=row["file_path"],
                    chunk_index=row["chunk_index"],
                    text=row["text"],
                    vector_score=vector_score,
                    metadata_score=metadata_score,
                    hybrid_score=hybrid_score,
                    object_uuid=object_uuid,
                    resource_title=row["display_title"],
                    resource_type=row["resource_type"],
                    subject=row["subject"],
                    quality_score=row["quality_score"],
                )
            )

        results.sort(key=lambda r: r.hybrid_score, reverse=True)
        return results[:limit]

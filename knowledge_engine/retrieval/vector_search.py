from __future__ import annotations

import json
import math

from knowledge_engine.embeddings.provider import LocalEmbeddingProvider


class VectorSearcher:
    def __init__(self, db):
        self.db = db
        self.provider = LocalEmbeddingProvider()

    def search(self, query: str, limit: int = 10):
        query_vector = self.provider.embed(query)

        results = []

        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    ce.chunk_uuid,
                    ce.vector_json,
                    dc.text,
                    dc.file_path,
                    dc.chunk_index
                FROM chunk_embeddings ce
                JOIN document_chunks dc
                  ON dc.chunk_uuid = ce.chunk_uuid
                """
            )

            for row in rows:
                vector = json.loads(row["vector_json"])

                score = self.cosine(query_vector, vector)

                results.append(
                    (
                        score,
                        row["file_path"],
                        row["chunk_index"],
                        row["text"],
                    )
                )

        results.sort(reverse=True)

        return results[:limit]

    def cosine(self, a, b):
        return sum(x * y for x, y in zip(a, b)) / (
            math.sqrt(sum(x * x for x in a))
            * math.sqrt(sum(y * y for y in b))
        )

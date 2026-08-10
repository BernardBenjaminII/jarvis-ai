from __future__ import annotations

import heapq
import sqlite3
from pathlib import Path
from typing import Iterable

import numpy as np

from core.retrieval.semantic_index.provider import OllamaEmbeddingProvider
from .math import decode_vector, normalized, cosine_scores
from .models import SemanticCandidate, SemanticSearchResult


class SemanticVectorSearchService:
    """
    Genesis X-B2.1 exact semantic candidate retrieval.

    This implementation intentionally does not mutate either the canonical runtime
    catalog or the X-B1 semantic index. It streams persisted vectors in bounded
    blocks and maintains a fixed-size top-K heap.

    X-B2.1 establishes correctness and provenance. Later X-B2 packs may replace
    the exact scanner with an ANN backend without changing the result contract.
    """

    def __init__(
        self,
        *,
        runtime_catalog: Path,
        semantic_db: Path,
        provider: str = "ollama",
        model: str = "mxbai-embed-large",
        ollama_url: str = "http://127.0.0.1:11434",
        expected_dimensions: int = 1024,
        block_size: int = 2048,
    ):
        self.runtime_catalog = Path(runtime_catalog)
        self.semantic_db = Path(semantic_db)
        self.provider_name = str(provider)
        self.model = str(model)
        self.expected_dimensions = int(expected_dimensions)
        self.block_size = max(64, int(block_size))

        if self.provider_name != "ollama":
            raise ValueError("X-B2.1 currently supports provider='ollama'")

        self.provider = OllamaEmbeddingProvider(
            base_url=ollama_url,
            model=self.model,
        )

    def _semantic_connect(self):
        c = sqlite3.connect(
            f"file:{self.semantic_db.resolve()}?mode=ro",
            uri=True,
            timeout=30.0,
        )
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA query_only=ON")
        c.execute("PRAGMA busy_timeout=30000")
        return c

    def _runtime_connect(self):
        c = sqlite3.connect(
            f"file:{self.runtime_catalog.resolve()}?mode=ro",
            uri=True,
            timeout=30.0,
        )
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA query_only=ON")
        c.execute("PRAGMA busy_timeout=30000")
        return c

    def audit(self) -> dict:
        health = self.provider.health()

        with self._semantic_connect() as c:
            tables = {
                str(r["name"])
                for r in c.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }

            required = {
                "chunk_identity_bridge",
                "semantic_vectors",
                "semantic_fragments",
                "semantic_fragment_vectors",
                "embedding_campaign",
            }

            missing = sorted(required - tables)

            canonical_vectors = (
                int(c.execute("SELECT COUNT(*) FROM semantic_vectors").fetchone()[0])
                if "semantic_vectors" in tables
                else 0
            )
            fragment_vectors = (
                int(c.execute("SELECT COUNT(*) FROM semantic_fragment_vectors").fetchone()[0])
                if "semantic_fragment_vectors" in tables
                else 0
            )
            bridge_rows = (
                int(c.execute("SELECT COUNT(*) FROM chunk_identity_bridge").fetchone()[0])
                if "chunk_identity_bridge" in tables
                else 0
            )
            complete_parents = (
                int(c.execute(
                    """SELECT COUNT(*) FROM embedding_campaign
                       WHERE stage IN ('COMPLETE','COMPLETE_FRAGMENTED')"""
                ).fetchone()[0])
                if "embedding_campaign" in tables
                else 0
            )

            dimensions = []
            if "semantic_vectors" in tables:
                dimensions.extend(
                    int(r[0]) for r in c.execute(
                        "SELECT DISTINCT dimensions FROM semantic_vectors"
                    )
                )
            if "semantic_fragment_vectors" in tables:
                dimensions.extend(
                    int(r[0]) for r in c.execute(
                        "SELECT DISTINCT dimensions FROM semantic_fragment_vectors"
                    )
                )

        return {
            "provider": health,
            "semantic_db": str(self.semantic_db),
            "runtime_catalog": str(self.runtime_catalog),
            "required_tables_present": not missing,
            "missing_tables": missing,
            "bridge_rows": bridge_rows,
            "canonical_vector_rows": canonical_vectors,
            "fragment_vector_rows": fragment_vectors,
            "total_vector_rows": canonical_vectors + fragment_vectors,
            "semantic_complete_parents": complete_parents,
            "dimensions_present": sorted(set(dimensions)),
            "expected_dimensions": self.expected_dimensions,
        }

    def _query_vector(self, query: str) -> np.ndarray:
        query = str(query).strip()
        if not query:
            raise ValueError("query must not be empty")

        vectors = self.provider.embed_batch([query])
        if len(vectors) != 1:
            raise RuntimeError(
                f"embedding provider returned {len(vectors)} vectors for one query"
            )

        q = np.asarray(vectors[0], dtype=np.float32)
        if q.size != self.expected_dimensions:
            raise RuntimeError(
                f"query vector dimension mismatch: expected={self.expected_dimensions} "
                f"actual={q.size}"
            )
        return normalized(q)

    @staticmethod
    def _push(heap: list, k: int, score: float, key: tuple):
        item = (float(score), key)
        if len(heap) < k:
            heapq.heappush(heap, item)
        elif score > heap[0][0]:
            heapq.heapreplace(heap, item)

    def _scan_canonical(
        self,
        q: np.ndarray,
        *,
        k: int,
        scan_limit: int | None,
    ) -> tuple[list, int]:
        heap = []
        scanned = 0

        sql = """
            SELECT
                v.runtime_chunk_id,
                v.chunk_uuid,
                v.dimensions,
                v.vector_blob
            FROM semantic_vectors AS v
            ORDER BY v.runtime_chunk_id
        """

        with self._semantic_connect() as c:
            cur = c.execute(sql)
            while True:
                rows = cur.fetchmany(self.block_size)
                if not rows:
                    break

                if scan_limit is not None:
                    remaining = int(scan_limit) - scanned
                    if remaining <= 0:
                        break
                    rows = rows[:remaining]

                if not rows:
                    break

                matrix = np.vstack([
                    decode_vector(r["vector_blob"], int(r["dimensions"]))
                    for r in rows
                ])
                scores = cosine_scores(matrix, q)

                for r, score in zip(rows, scores):
                    self._push(
                        heap,
                        k,
                        float(score),
                        (
                            "canonical",
                            int(r["runtime_chunk_id"]),
                            str(r["chunk_uuid"]),
                            None,
                            None,
                        ),
                    )

                scanned += len(rows)

                if scan_limit is not None and scanned >= int(scan_limit):
                    break

        return heap, scanned

    def _scan_fragments(
        self,
        q: np.ndarray,
        *,
        k: int,
        scan_limit: int | None,
    ) -> tuple[list, int]:
        heap = []
        scanned = 0

        sql = """
            SELECT
                v.fragment_uuid,
                v.runtime_chunk_id,
                v.fragment_index,
                v.dimensions,
                v.vector_blob,
                b.chunk_uuid
            FROM semantic_fragment_vectors AS v
            JOIN chunk_identity_bridge AS b
              ON b.runtime_chunk_id=v.runtime_chunk_id
            ORDER BY v.runtime_chunk_id, v.fragment_index, v.fragment_uuid
        """

        with self._semantic_connect() as c:
            cur = c.execute(sql)
            while True:
                rows = cur.fetchmany(self.block_size)
                if not rows:
                    break

                if scan_limit is not None:
                    remaining = int(scan_limit) - scanned
                    if remaining <= 0:
                        break
                    rows = rows[:remaining]

                if not rows:
                    break

                matrix = np.vstack([
                    decode_vector(r["vector_blob"], int(r["dimensions"]))
                    for r in rows
                ])
                scores = cosine_scores(matrix, q)

                for r, score in zip(rows, scores):
                    self._push(
                        heap,
                        k,
                        float(score),
                        (
                            "fragment",
                            int(r["runtime_chunk_id"]),
                            str(r["chunk_uuid"]),
                            str(r["fragment_uuid"]),
                            int(r["fragment_index"]),
                        ),
                    )

                scanned += len(rows)

                if scan_limit is not None and scanned >= int(scan_limit):
                    break

        return heap, scanned

    def _hydrate(self, ranked: list[tuple[float, tuple]]) -> tuple[SemanticCandidate, ...]:
        if not ranked:
            return tuple()

        chunk_ids = sorted({int(item[1][1]) for item in ranked})
        placeholders = ",".join("?" for _ in chunk_ids)

        runtime = {}
        with self._runtime_connect() as c:
            for r in c.execute(
                f"""
                SELECT
                    c.id AS runtime_chunk_id,
                    c.document_id AS runtime_document_id,
                    c.chunk_text,
                    d.title,
                    d.file_path
                FROM runtime_chunks AS c
                JOIN runtime_documents AS d
                  ON d.id=c.document_id
                WHERE c.id IN ({placeholders})
                """,
                chunk_ids,
            ):
                runtime[int(r["runtime_chunk_id"])] = dict(r)

        fragment_text = {}
        fragment_ids = [item[1][3] for item in ranked if item[1][3] is not None]
        if fragment_ids:
            placeholders = ",".join("?" for _ in fragment_ids)
            with self._semantic_connect() as c:
                for r in c.execute(
                    f"""
                    SELECT fragment_uuid, fragment_text
                    FROM semantic_fragments
                    WHERE fragment_uuid IN ({placeholders})
                    """,
                    fragment_ids,
                ):
                    fragment_text[str(r["fragment_uuid"])] = str(r["fragment_text"])

        candidates = []
        for rank, (score, key) in enumerate(
            sorted(ranked, key=lambda x: x[0], reverse=True),
            start=1,
        ):
            source, cid, chunk_uuid, fragment_uuid, fragment_index = key
            rr = runtime.get(int(cid), {})

            if fragment_uuid is not None:
                text = fragment_text.get(fragment_uuid, "")
            else:
                text = str(rr.get("chunk_text", ""))

            preview = " ".join(text.split())
            if len(preview) > 420:
                preview = preview[:417] + "..."

            candidates.append(
                SemanticCandidate(
                    rank=rank,
                    score=round(float(score), 8),
                    source=str(source),
                    runtime_chunk_id=int(cid),
                    runtime_document_id=int(rr.get("runtime_document_id", 0)),
                    chunk_uuid=str(chunk_uuid),
                    fragment_uuid=fragment_uuid,
                    fragment_index=fragment_index,
                    document_title=str(rr.get("title", "")),
                    file_path=str(rr.get("file_path", "")),
                    text_preview=preview,
                )
            )

        return tuple(candidates)

    def search(
        self,
        query: str,
        *,
        top_k: int = 10,
        scope: str = "all",
        scan_limit: int | None = None,
    ) -> SemanticSearchResult:
        top_k = max(1, int(top_k))
        scope = str(scope).lower().strip()
        if scope not in {"all", "canonical", "fragment"}:
            raise ValueError("scope must be one of: all, canonical, fragment")

        q = self._query_vector(query)

        combined = []
        scanned_canonical = 0
        scanned_fragments = 0

        # Each side keeps top_k. The final merge then keeps the global top_k.
        if scope in {"all", "canonical"}:
            h, scanned_canonical = self._scan_canonical(
                q,
                k=top_k,
                scan_limit=scan_limit,
            )
            combined.extend(h)

        if scope in {"all", "fragment"}:
            h, scanned_fragments = self._scan_fragments(
                q,
                k=top_k,
                scan_limit=scan_limit,
            )
            combined.extend(h)

        combined = sorted(combined, key=lambda x: x[0], reverse=True)[:top_k]
        candidates = self._hydrate(combined)

        return SemanticSearchResult(
            query=str(query),
            provider=self.provider_name,
            model=self.model,
            dimensions=self.expected_dimensions,
            scope=scope,
            scanned_canonical=scanned_canonical,
            scanned_fragments=scanned_fragments,
            candidates=candidates,
        )

    def certify(self) -> dict:
        a = self.audit()
        checks = {
            "provider_available": bool(a["provider"].get("available")),
            "provider_model_present": bool(a["provider"].get("model_present")),
            "required_tables_present": bool(a["required_tables_present"]),
            "semantic_parent_coverage_nonzero": int(a["semantic_complete_parents"]) > 0,
            "canonical_vectors_present": int(a["canonical_vector_rows"]) > 0,
            "fragment_vectors_present": int(a["fragment_vector_rows"]) > 0,
            "vector_dimensions_consistent": (
                a["dimensions_present"] == [self.expected_dimensions]
            ),
            "canonical_runtime_read_only": True,
            "semantic_index_read_only": True,
        }

        return {
            "status": (
                "EXCELLENT_VECTOR_RETRIEVAL_FOUNDATION"
                if all(checks.values())
                else "REVIEW_REQUIRED"
            ),
            "checks": checks,
            **a,
        }

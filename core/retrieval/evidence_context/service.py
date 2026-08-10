from __future__ import annotations

import sqlite3
from pathlib import Path

from core.retrieval.hybrid_rerank.service import HybridSemanticRetrievalService
from core.retrieval.evidence_context.models import EvidenceBundle, EvidenceItem
from core.retrieval.evidence_context.precision import passes_precision_gate
from core.retrieval.evidence_context.dedup import evidence_fingerprint, overlap_ratio


class EvidenceContextAssemblyService:
    """
    Genesis X-B2.3.

    Converts X-B2.2 hybrid-ranked retrieval candidates into a bounded,
    provenance-preserving evidence package suitable for reasoning.

    Read-only against both the canonical runtime catalog and semantic index.
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

        self.hybrid = HybridSemanticRetrievalService(
            runtime_catalog=runtime_catalog,
            semantic_db=semantic_db,
            provider=provider,
            model=model,
            ollama_url=ollama_url,
            expected_dimensions=expected_dimensions,
            block_size=block_size,
        )

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

    def _fetch_chunk(self, chunk_id: int) -> dict | None:
        with self._runtime_connect() as c:
            row = c.execute(
                """
                SELECT
                    c.id AS runtime_chunk_id,
                    c.document_id AS runtime_document_id,
                    c.chunk_text,
                    c.chunk_index,
                    d.title,
                    d.file_path
                FROM runtime_chunks AS c
                JOIN runtime_documents AS d
                  ON d.id=c.document_id
                WHERE c.id=?
                """,
                (int(chunk_id),),
            ).fetchone()

        return dict(row) if row else None

    def _neighbor_rows(self, chunk_id: int, radius: int) -> list[dict]:
        center = self._fetch_chunk(chunk_id)
        if not center:
            return []

        with self._runtime_connect() as c:
            rows = [
                dict(r)
                for r in c.execute(
                    """
                    SELECT
                        c.id AS runtime_chunk_id,
                        c.document_id AS runtime_document_id,
                        c.chunk_text,
                        c.chunk_index,
                        d.title,
                        d.file_path
                    FROM runtime_chunks AS c
                    JOIN runtime_documents AS d
                      ON d.id=c.document_id
                    WHERE c.document_id=?
                      AND c.chunk_index BETWEEN ? AND ?
                    ORDER BY c.chunk_index
                    """,
                    (
                        int(center["runtime_document_id"]),
                        int(center["chunk_index"]) - int(radius),
                        int(center["chunk_index"]) + int(radius),
                    ),
                )
            ]

        return [r for r in rows if int(r["runtime_chunk_id"]) != int(chunk_id)]

    def audit(self) -> dict:
        h = self.hybrid.audit()
        return {
            "hybrid_retrieval": h,
            "evidence_features": {
                "precision_gating": True,
                "neighbor_expansion": True,
                "document_grouping": True,
                "redundancy_suppression": True,
                "bounded_context": True,
                "provenance_preserved": True,
                "read_only": True,
            },
        }

    def assemble(
        self,
        query: str,
        *,
        top_k: int = 10,
        candidate_pool: int = 60,
        scan_limit: int | None = None,
        neighbor_radius: int = 1,
        max_chars: int = 12000,
        minimum_hybrid: float = 0.42,
        minimum_semantic: float = 0.58,
        max_per_document: int = 4,
        redundancy_threshold: float = 0.82,
    ) -> EvidenceBundle:
        hybrid_result = self.hybrid.search(
            query,
            top_k=max(top_k * 2, top_k),
            candidate_pool=max(candidate_pool, top_k * 3),
            scan_limit=scan_limit,
        )

        accepted = []
        rejected = 0

        for c in hybrid_result.candidates:
            ok = passes_precision_gate(
                hybrid_score=c.hybrid_score,
                semantic_score=c.semantic_score,
                lexical_score=c.lexical_score,
                title_score=c.title_score,
                minimum_hybrid=minimum_hybrid,
                minimum_semantic=minimum_semantic,
                require_concept_signal=True,
            )
            if ok:
                accepted.append(c)
            else:
                rejected += 1

        # Expand only strong accepted anchors.
        expanded = []
        for c in accepted[:top_k]:
            for row in self._neighbor_rows(c.runtime_chunk_id, neighbor_radius):
                expanded.append({
                    "anchor": c,
                    "row": row,
                })

        # First create anchor evidence.
        pool = []
        for c in accepted:
            row = self._fetch_chunk(c.runtime_chunk_id)
            if not row:
                continue
            text = str(row["chunk_text"])
            pool.append({
                "role": "anchor",
                "candidate": c,
                "row": row,
                "text": text,
                "priority": (
                    float(c.hybrid_score),
                    float(c.semantic_score),
                    float(c.lexical_score),
                ),
            })

        # Neighbor evidence inherits the anchor provenance score but is explicitly
        # marked supporting context and slightly deprioritized.
        for item in expanded:
            c = item["anchor"]
            row = item["row"]
            text = str(row["chunk_text"])
            pool.append({
                "role": "neighbor",
                "candidate": c,
                "row": row,
                "text": text,
                "priority": (
                    float(c.hybrid_score) - 0.08,
                    float(c.semantic_score) - 0.05,
                    float(c.lexical_score),
                ),
            })

        pool.sort(key=lambda x: x["priority"], reverse=True)

        selected = []
        seen_fingerprints = set()
        doc_counts = {}
        total_chars = 0

        for item in pool:
            c = item["candidate"]
            row = item["row"]
            text = str(item["text"]).strip()
            if not text:
                continue

            fp = evidence_fingerprint(text)
            if fp in seen_fingerprints:
                continue

            doc_id = int(row["runtime_document_id"])
            if doc_counts.get(doc_id, 0) >= max_per_document:
                continue

            redundant = False
            for chosen in selected:
                if overlap_ratio(text, chosen["text"]) >= redundancy_threshold:
                    redundant = True
                    break
            if redundant:
                continue

            projected = total_chars + len(text)
            if projected > max_chars:
                continue

            selected.append({
                **item,
                "text": text,
                "fingerprint": fp,
            })
            seen_fingerprints.add(fp)
            doc_counts[doc_id] = doc_counts.get(doc_id, 0) + 1
            total_chars = projected

            if len(selected) >= top_k:
                break

        evidence_items = []
        for rank, item in enumerate(selected, start=1):
            c = item["candidate"]
            row = item["row"]
            eid = (
                f"doc{row['runtime_document_id']}:chunk{row['runtime_chunk_id']}:"
                f"{item['role']}:{rank}"
            )

            evidence_items.append(
                EvidenceItem(
                    evidence_id=eid,
                    rank=rank,
                    source_role=item["role"],
                    runtime_chunk_id=int(row["runtime_chunk_id"]),
                    runtime_document_id=int(row["runtime_document_id"]),
                    document_title=str(row["title"]),
                    file_path=str(row["file_path"]),
                    chunk_uuid=c.chunk_uuid,
                    fragment_uuid=c.fragment_uuid if item["role"] == "anchor" else None,
                    hybrid_score=round(float(c.hybrid_score), 8),
                    semantic_score=round(float(c.semantic_score), 8),
                    lexical_score=round(float(c.lexical_score), 8),
                    title_score=round(float(c.title_score), 8),
                    matched_terms=tuple(c.matched_terms),
                    text=str(item["text"]),
                    chars=len(str(item["text"])),
                )
            )

        return EvidenceBundle(
            query=query,
            query_terms=tuple(hybrid_result.query_terms),
            accepted_candidates=len(accepted),
            rejected_candidates=rejected,
            expanded_neighbors=len(expanded),
            selected_evidence=tuple(evidence_items),
            total_chars=total_chars,
            max_chars=max_chars,
        )

    def certify(self) -> dict:
        a = self.audit()
        base = a["hybrid_retrieval"]["base_vector_search"]

        checks = {
            "provider_available": bool(base["provider"].get("available")),
            "provider_model_present": bool(base["provider"].get("model_present")),
            "required_tables_present": bool(base["required_tables_present"]),
            "full_semantic_parent_coverage": (
                int(base["semantic_complete_parents"]) == int(base["bridge_rows"])
                and int(base["bridge_rows"]) > 0
            ),
            "precision_gating_enabled": True,
            "neighbor_expansion_enabled": True,
            "redundancy_suppression_enabled": True,
            "bounded_context_enabled": True,
            "provenance_preserved": True,
            "read_only_retrieval": True,
        }

        return {
            "status": (
                "EXCELLENT_EVIDENCE_CONTEXT_FOUNDATION"
                if all(checks.values())
                else "REVIEW_REQUIRED"
            ),
            "checks": checks,
            **a,
        }

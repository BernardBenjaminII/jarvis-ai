from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.retrieval.hybrid_rerank.service import HybridSemanticRetrievalService


DEFAULT_SEMANTIC_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/semantic_index.sqlite"
)


def emit(v):
    print(json.dumps(v, indent=2, ensure_ascii=False, default=str))


def main():
    p = argparse.ArgumentParser(
        description=(
            "Genesis X-B2.2 — Hybrid Semantic Retrieval, Deduplication "
            "& Relevance Reranking"
        )
    )
    p.add_argument("command", choices=("audit", "status", "query", "certify"))
    p.add_argument("--runtime-catalog", type=Path, default=DEFAULT_CATALOG_DB)
    p.add_argument("--semantic-db", type=Path, default=DEFAULT_SEMANTIC_DB)
    p.add_argument("--provider", default="ollama")
    p.add_argument("--model", default="mxbai-embed-large")
    p.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    p.add_argument("--expected-dimensions", type=int, default=1024)
    p.add_argument("--block-size", type=int, default=2048)
    p.add_argument("--query")
    p.add_argument("--top-k", type=int, default=10)
    p.add_argument("--candidate-pool", type=int, default=50)
    p.add_argument("--scan-limit", type=int, default=None)

    a = p.parse_args()

    s = HybridSemanticRetrievalService(
        runtime_catalog=a.runtime_catalog,
        semantic_db=a.semantic_db,
        provider=a.provider,
        model=a.model,
        ollama_url=a.ollama_url,
        expected_dimensions=a.expected_dimensions,
        block_size=a.block_size,
    )

    if a.command in ("audit", "status"):
        emit(s.audit())
        return

    if a.command == "certify":
        emit(s.certify())
        return

    if not a.query:
        p.error("--query is required for query")

    emit(
        s.search(
            a.query,
            top_k=a.top_k,
            candidate_pool=a.candidate_pool,
            scan_limit=a.scan_limit,
        ).to_dict()
    )


if __name__ == "__main__":
    main()

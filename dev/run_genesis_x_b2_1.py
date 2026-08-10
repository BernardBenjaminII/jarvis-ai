from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.retrieval.vector_search.service import SemanticVectorSearchService


DEFAULT_SEMANTIC_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/semantic_index.sqlite"
)


def emit(value):
    print(json.dumps(value, indent=2, ensure_ascii=False, default=str))


def main():
    p = argparse.ArgumentParser(
        description=(
            "Genesis X-B2.1 — Vector Search & Semantic Candidate Retrieval"
        )
    )
    p.add_argument(
        "command",
        choices=("audit", "status", "query", "certify"),
    )
    p.add_argument(
        "--runtime-catalog",
        type=Path,
        default=DEFAULT_CATALOG_DB,
    )
    p.add_argument(
        "--semantic-db",
        type=Path,
        default=DEFAULT_SEMANTIC_DB,
    )
    p.add_argument("--provider", default="ollama")
    p.add_argument("--model", default="mxbai-embed-large")
    p.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    p.add_argument("--expected-dimensions", type=int, default=1024)
    p.add_argument("--block-size", type=int, default=2048)
    p.add_argument("--query")
    p.add_argument("--top-k", type=int, default=10)
    p.add_argument(
        "--scope",
        choices=("all", "canonical", "fragment"),
        default="all",
    )
    p.add_argument(
        "--scan-limit",
        type=int,
        default=None,
        help=(
            "Optional per-source scan cap for canary/smoke testing. "
            "Omit for exact full-index search."
        ),
    )

    a = p.parse_args()

    s = SemanticVectorSearchService(
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

    result = s.search(
        a.query,
        top_k=a.top_k,
        scope=a.scope,
        scan_limit=a.scan_limit,
    )
    emit(result.to_dict())


if __name__ == "__main__":
    main()

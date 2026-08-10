from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.retrieval.evidence_grounding import EvidenceGroundedSynthesisService


DEFAULT_SEMANTIC_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/semantic_index.sqlite"
)


def emit(value):
    print(json.dumps(value, indent=2, ensure_ascii=False, default=str))


def main():
    p = argparse.ArgumentParser(
        description="Genesis X-B2.4A — Synthesis Quality Hardening"
    )
    p.add_argument(
        "command",
        choices=("audit", "status", "plan", "quality", "answer", "certify"),
    )
    p.add_argument("--runtime-catalog", type=Path, default=DEFAULT_CATALOG_DB)
    p.add_argument("--semantic-db", type=Path, default=DEFAULT_SEMANTIC_DB)
    p.add_argument("--provider", default="ollama")
    p.add_argument("--model", default="mxbai-embed-large")
    p.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    p.add_argument("--expected-dimensions", type=int, default=1024)
    p.add_argument("--block-size", type=int, default=2048)
    p.add_argument("--query")
    p.add_argument("--top-k", type=int, default=8)
    p.add_argument("--candidate-pool", type=int, default=60)
    p.add_argument("--scan-limit", type=int, default=None)
    p.add_argument("--neighbor-radius", type=int, default=1)
    p.add_argument("--max-chars", type=int, default=12000)
    p.add_argument("--minimum-hybrid", type=float, default=0.42)
    p.add_argument("--minimum-semantic", type=float, default=0.58)
    p.add_argument("--max-per-document", type=int, default=4)
    p.add_argument("--redundancy-threshold", type=float, default=0.82)
    a = p.parse_args()

    service = EvidenceGroundedSynthesisService(
        runtime_catalog=a.runtime_catalog,
        semantic_db=a.semantic_db,
        provider=a.provider,
        model=a.model,
        ollama_url=a.ollama_url,
        expected_dimensions=a.expected_dimensions,
        block_size=a.block_size,
    )

    if a.command in ("audit", "status"):
        emit(service.audit())
        return

    if a.command == "certify":
        emit(service.certify())
        return

    if not a.query:
        p.error("--query is required")

    kwargs = dict(
        top_k=a.top_k,
        candidate_pool=a.candidate_pool,
        scan_limit=a.scan_limit,
        neighbor_radius=a.neighbor_radius,
        max_chars=a.max_chars,
        minimum_hybrid=a.minimum_hybrid,
        minimum_semantic=a.minimum_semantic,
        max_per_document=a.max_per_document,
        redundancy_threshold=a.redundancy_threshold,
    )

    if a.command in ("plan", "quality"):
        emit(service.quality_plan(a.query, **kwargs))
        return

    emit(service.deterministic_answer(a.query, **kwargs))


if __name__ == "__main__":
    main()

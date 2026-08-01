from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.governance.constitution.coverage.graph.authority_public_api import (  # noqa: E402
    AuthorityEdgeKind,
    AuthorityNodeKind,
    ConstitutionalAuthorityGraph,
    ConstitutionalAuthorityGraphEngine,
    ConstitutionalAuthorityGraphReporter,
    ConstitutionalAuthorityQueryService,
)


def check(condition: bool, label: str, detail: str = "") -> int:
    status = "PASS" if condition else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"[{status}] {label}{suffix}")
    return 0 if condition else 1


def main() -> int:
    print("=" * 78)
    print("GENESIS VII-C4.3 PACK 3B-1 — CONSTITUTIONAL AUTHORITY GRAPH")
    print("=" * 78)

    pack3a = PROJECT_ROOT / "artifacts/audit/km0000-c4_3-pack3a"
    engine = ConstitutionalAuthorityGraphEngine()
    first = engine.assess(pack3a_directory=pack3a)
    second = engine.assess(pack3a_directory=pack3a)

    failures = 0
    failures += check(
        bool(first.graph_foundation_fingerprint),
        "Graph foundation fingerprint linked",
        first.graph_foundation_fingerprint,
    )
    failures += check(
        bool(first.article_intelligence_fingerprint),
        "Article intelligence fingerprint preserved",
        first.article_intelligence_fingerprint,
    )
    failures += check(
        first.authority_graph_fingerprint == second.authority_graph_fingerprint,
        "Authority graph deterministic",
        first.authority_graph_fingerprint,
    )

    article_nodes = [
        node for node in first.nodes
        if node.node_kind is AuthorityNodeKind.CONSTITUTIONAL_ARTICLE
    ]
    failures += check(
        len(article_nodes) == first.metrics.article_count and bool(article_nodes),
        "Constitutional article projection complete",
        f"articles={len(article_nodes)}",
    )

    class_nodes = [
        node for node in first.nodes
        if node.node_kind is AuthorityNodeKind.AUTHORITY_CLASS
    ]
    failures += check(
        len(class_nodes) == 5,
        "Canonical authority classes established",
        f"classes={len(class_nodes)}",
    )

    authorization_edges = [
        edge for edge in first.edges
        if edge.edge_kind is AuthorityEdgeKind.AUTHORIZES
    ]
    failures += check(
        len(authorization_edges) == first.metrics.authorization_edge_count,
        "Authorization edge registry complete",
        f"edges={len(authorization_edges)}",
    )

    failures += check(
        first.integrity.is_valid,
        "Authority graph integrity verified",
        f"diagnostics={len(first.integrity.diagnostics)}",
    )
    failures += check(
        not first.integrity.duplicate_node_ids,
        "Authority node identifiers unique",
    )
    failures += check(
        not first.integrity.duplicate_edge_ids,
        "Authority edge identifiers unique",
    )
    failures += check(
        not first.integrity.dangling_edge_ids,
        "No dangling authority edges",
    )
    failures += check(
        not first.integrity.invalid_authorization_edge_ids,
        "Authorization edge semantics valid",
    )

    graph = ConstitutionalAuthorityGraph(first.nodes, first.edges)
    queries = ConstitutionalAuthorityQueryService(graph)

    query_deterministic = (
        queries.articles_by_authority_class("cold")
        == queries.articles_by_authority_class("cold")
        and queries.unexercised_articles()
        == queries.unexercised_articles()
    )
    failures += check(
        query_deterministic,
        "Authority query layer deterministic",
    )

    failures += check(
        not first.diagnostics,
        "Authority graph diagnostics clear",
        f"diagnostics={len(first.diagnostics)}",
    )

    output = PROJECT_ROOT / "artifacts/audit/km0000-c4_3-pack3b1"
    written = ConstitutionalAuthorityGraphReporter().write(first, output)
    expected = {
        "constitutional_authority_graph.json",
        "constitutional_authority_nodes.json",
        "constitutional_authority_edges.json",
        "constitutional_authority_metrics.json",
        "constitutional_authority_integrity.json",
        "constitutional_authority_summary.md",
    }
    failures += check(
        {path.name for path in written} == expected,
        "Canonical Pack 3B-1 artifact set",
        f"files={len(written)}",
    )

    invalid = []
    for path in written:
        if path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                invalid.append(path.name)
    failures += check(
        not invalid,
        "Pack 3B-1 JSON artifacts valid",
        f"invalid={len(invalid)}",
    )

    print("-" * 78)
    print(f"Graph foundation fp        : {first.graph_foundation_fingerprint}")
    print(f"Article intelligence fp    : {first.article_intelligence_fingerprint}")
    print(f"Authority graph fp         : {first.authority_graph_fingerprint}")
    print(f"Constitutional articles    : {first.metrics.article_count}")
    print(f"Governed artifacts         : {first.metrics.governed_artifact_count}")
    print(f"Authorization edges        : {first.metrics.authorization_edge_count}")
    print(f"Exercised articles         : {first.metrics.exercised_article_count}")
    print(f"Unexercised articles       : {first.metrics.unexercised_article_count}")
    print(f"Authority utilization      : {first.metrics.authority_utilization_ratio:.2%}")
    print(f"Integrity valid            : {first.integrity.is_valid}")
    print(f"Diagnostics                : {len(first.diagnostics)}")
    print("-" * 78)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 78)

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

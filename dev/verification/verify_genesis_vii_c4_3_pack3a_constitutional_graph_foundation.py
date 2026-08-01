from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.governance.constitution.coverage.graph import (  # noqa: E402
    ConstitutionalGraph,
    ConstitutionalGraphFoundationEngine,
    ConstitutionalGraphFoundationReporter,
)


def check(condition: bool, label: str, detail: str = "") -> int:
    status = "PASS" if condition else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"[{status}] {label}{suffix}")
    return 0 if condition else 1


def main() -> int:
    print("=" * 78)
    print("GENESIS VII-C4.3 PACK 3A — CONSTITUTIONAL GRAPH FOUNDATION")
    print("=" * 78)

    pack2 = PROJECT_ROOT / "artifacts/audit/km0000-c4_3-pack2"
    engine = ConstitutionalGraphFoundationEngine()
    first = engine.assess(pack2_directory=pack2)
    second = engine.assess(pack2_directory=pack2)

    failures = 0
    failures += check(
        bool(first.article_intelligence_fingerprint),
        "Article intelligence fingerprint linked",
        first.article_intelligence_fingerprint,
    )
    failures += check(
        first.graph_fingerprint == second.graph_fingerprint,
        "Constitutional graph deterministic",
        first.graph_fingerprint,
    )
    failures += check(
        len(first.nodes) > 0,
        "Canonical graph node registry established",
        f"nodes={len(first.nodes)}",
    )
    failures += check(
        len(first.edges) > 0,
        "Canonical graph edge registry established",
        f"edges={len(first.edges)}",
    )
    failures += check(
        first.metrics.node_count == len(first.nodes),
        "Graph node metrics complete",
    )
    failures += check(
        first.metrics.edge_count == len(first.edges),
        "Graph edge metrics complete",
    )
    failures += check(
        first.integrity.is_valid,
        "Graph integrity verified",
        f"diagnostics={len(first.integrity.diagnostics)}",
    )
    failures += check(
        not first.integrity.duplicate_node_ids,
        "Graph node identifiers unique",
    )
    failures += check(
        not first.integrity.duplicate_edge_ids,
        "Graph edge identifiers unique",
    )
    failures += check(
        not first.integrity.dangling_edge_ids,
        "No dangling graph edges",
    )
    failures += check(
        not first.integrity.self_loop_edge_ids,
        "No unexpected graph self-loops",
    )

    graph = ConstitutionalGraph(first.nodes, first.edges)
    article_nodes = [
        node for node in first.nodes if node.node_type.value == "article"
    ]
    query_ok = True
    if article_nodes:
        node = article_nodes[0]
        query_ok = graph.node(node.node_id) == node
    failures += check(
        query_ok,
        "Graph query surface deterministic",
    )

    failures += check(
        not first.diagnostics,
        "Graph foundation diagnostics clear",
        f"diagnostics={len(first.diagnostics)}",
    )

    output = PROJECT_ROOT / "artifacts/audit/km0000-c4_3-pack3a"
    written = ConstitutionalGraphFoundationReporter().write(first, output)
    expected = {
        "constitutional_graph_foundation.json",
        "constitutional_graph_nodes.json",
        "constitutional_graph_edges.json",
        "constitutional_graph_metrics.json",
        "constitutional_graph_integrity.json",
        "constitutional_graph_foundation_report.md",
    }
    failures += check(
        {path.name for path in written} == expected,
        "Canonical Pack 3A artifact set",
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
        "Pack 3A JSON artifacts valid",
        f"invalid={len(invalid)}",
    )

    print("-" * 78)
    print(f"Article intelligence fp    : {first.article_intelligence_fingerprint}")
    print(f"Graph fingerprint          : {first.graph_fingerprint}")
    print(f"Nodes                      : {first.metrics.node_count}")
    print(f"Edges                      : {first.metrics.edge_count}")
    print(f"Connected nodes            : {first.metrics.connected_node_count}")
    print(f"Isolated nodes             : {first.metrics.isolated_node_count}")
    print(f"Graph density              : {first.metrics.graph_density:.12f}")
    print(f"Integrity valid            : {first.integrity.is_valid}")
    print(f"Diagnostics                : {len(first.diagnostics)}")
    print("-" * 78)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 78)

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

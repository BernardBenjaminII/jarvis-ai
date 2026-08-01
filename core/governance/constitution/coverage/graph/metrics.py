from __future__ import annotations

from collections import Counter

from ..fingerprints import canonical_fingerprint
from .models import (
    ConstitutionalGraphEdge,
    ConstitutionalGraphMetrics,
    ConstitutionalGraphNode,
)


def compute_graph_metrics(
    nodes: tuple[ConstitutionalGraphNode, ...],
    edges: tuple[ConstitutionalGraphEdge, ...],
) -> ConstitutionalGraphMetrics:
    node_type_counts = Counter(node.node_type.value for node in nodes)
    edge_type_counts = Counter(edge.edge_type.value for edge in edges)

    connected_ids = {
        edge.source_node_id for edge in edges
    } | {
        edge.target_node_id for edge in edges
    }
    isolated = sum(1 for node in nodes if node.node_id not in connected_ids)
    connected = len(nodes) - isolated

    possible_edges = len(nodes) * (len(nodes) - 1)
    density = round(len(edges) / possible_edges, 12) if possible_edges else 0.0

    basis = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_type_counts": dict(sorted(node_type_counts.items())),
        "edge_type_counts": dict(sorted(edge_type_counts.items())),
        "isolated_node_count": isolated,
        "connected_node_count": connected,
        "graph_density": density,
    }
    return ConstitutionalGraphMetrics(
        node_count=len(nodes),
        edge_count=len(edges),
        node_type_counts=basis["node_type_counts"],
        edge_type_counts=basis["edge_type_counts"],
        isolated_node_count=isolated,
        connected_node_count=connected,
        graph_density=density,
        metrics_fingerprint=canonical_fingerprint(basis),
    )

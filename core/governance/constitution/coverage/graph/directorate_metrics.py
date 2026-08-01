from __future__ import annotations

from collections import Counter

from ..fingerprints import canonical_fingerprint
from .directorate_contracts import DirectorateEdgeKind, DirectorateNodeKind
from .directorate_models import DirectorateEdge, DirectorateNode


def compute_directorate_metrics(
    nodes: tuple[DirectorateNode, ...],
    edges: tuple[DirectorateEdge, ...],
) -> dict[str, object]:
    node_counts = Counter(node.node_kind.value for node in nodes)
    edge_counts = Counter(edge.edge_kind.value for edge in edges)

    ownership_by_directorate: dict[str, int] = {}
    for node in nodes:
        if node.node_kind is DirectorateNodeKind.DIRECTORATE:
            ownership_by_directorate[node.canonical_key] = sum(
                1
                for edge in edges
                if edge.source_node_id == node.node_id
                and edge.edge_kind is DirectorateEdgeKind.OWNS
            )

    domain_ids = {
        node.node_id
        for node in nodes
        if node.node_kind is DirectorateNodeKind.OWNERSHIP_DOMAIN
    }
    owned_domain_ids = {
        edge.target_node_id
        for edge in edges
        if edge.edge_kind is DirectorateEdgeKind.OWNS
    }
    unowned = sorted(domain_ids - owned_domain_ids)
    ratio = round(len(owned_domain_ids) / len(domain_ids), 12) if domain_ids else 1.0

    basis = {
        "node_kind_distribution": dict(sorted(node_counts.items())),
        "edge_kind_distribution": dict(sorted(edge_counts.items())),
        "ownership_by_directorate": dict(sorted(ownership_by_directorate.items())),
        "ownership_domain_count": len(domain_ids),
        "owned_domain_count": len(owned_domain_ids),
        "unowned_domain_ids": unowned,
        "ownership_completeness_ratio": ratio,
    }
    return {**basis, "fingerprint": canonical_fingerprint(basis)}

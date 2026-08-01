from __future__ import annotations

from collections import Counter

from ..fingerprints import canonical_fingerprint
from .authority_contracts import (
    AuthorityEdgeKind,
    AuthorityNodeKind,
)
from .authority_models import (
    AuthorityEdge,
    AuthorityGraphIntegrity,
    AuthorityNode,
)


def verify_authority_graph_integrity(
    nodes: tuple[AuthorityNode, ...],
    edges: tuple[AuthorityEdge, ...],
) -> AuthorityGraphIntegrity:
    node_ids = [node.node_id for node in nodes]
    edge_ids = [edge.edge_id for edge in edges]
    node_by_id = {node.node_id: node for node in nodes}
    known_nodes = set(node_by_id)

    duplicate_nodes = tuple(sorted(
        node_id for node_id, count in Counter(node_ids).items() if count > 1
    ))
    duplicate_edges = tuple(sorted(
        edge_id for edge_id, count in Counter(edge_ids).items() if count > 1
    ))
    dangling = tuple(sorted(
        edge.edge_id
        for edge in edges
        if edge.source_node_id not in known_nodes
        or edge.target_node_id not in known_nodes
    ))

    invalid_authorization = []
    for edge in edges:
        if edge.edge_kind is not AuthorityEdgeKind.AUTHORIZES:
            continue
        source = node_by_id.get(edge.source_node_id)
        target = node_by_id.get(edge.target_node_id)
        if (
            source is None
            or target is None
            or source.node_kind is not AuthorityNodeKind.CONSTITUTIONAL_ARTICLE
            or target.node_kind is not AuthorityNodeKind.GOVERNED_ARTIFACT
        ):
            invalid_authorization.append(edge.edge_id)

    diagnostics = []
    if duplicate_nodes:
        diagnostics.append("Duplicate authority node identifiers detected.")
    if duplicate_edges:
        diagnostics.append("Duplicate authority edge identifiers detected.")
    if dangling:
        diagnostics.append("Dangling authority edges detected.")
    if invalid_authorization:
        diagnostics.append("Invalid constitutional authorization edges detected.")

    basis = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "duplicate_node_ids": duplicate_nodes,
        "duplicate_edge_ids": duplicate_edges,
        "dangling_edge_ids": dangling,
        "invalid_authorization_edge_ids": sorted(invalid_authorization),
        "diagnostics": diagnostics,
    }
    return AuthorityGraphIntegrity(
        node_count=len(nodes),
        edge_count=len(edges),
        duplicate_node_ids=duplicate_nodes,
        duplicate_edge_ids=duplicate_edges,
        dangling_edge_ids=dangling,
        invalid_authorization_edge_ids=tuple(sorted(invalid_authorization)),
        diagnostics=tuple(diagnostics),
        fingerprint=canonical_fingerprint(basis),
    )

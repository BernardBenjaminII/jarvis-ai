from __future__ import annotations

from collections import Counter

from ..fingerprints import canonical_fingerprint
from .models import (
    ConstitutionalGraphEdge,
    ConstitutionalGraphIntegrity,
    ConstitutionalGraphNode,
)


def verify_graph_integrity(
    nodes: tuple[ConstitutionalGraphNode, ...],
    edges: tuple[ConstitutionalGraphEdge, ...],
) -> ConstitutionalGraphIntegrity:
    node_ids = [node.node_id for node in nodes]
    edge_ids = [edge.edge_id for edge in edges]
    known_nodes = set(node_ids)

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
    self_loops = tuple(sorted(
        edge.edge_id
        for edge in edges
        if edge.source_node_id == edge.target_node_id
    ))

    diagnostics = []
    if duplicate_nodes:
        diagnostics.append("Duplicate graph node identifiers detected.")
    if duplicate_edges:
        diagnostics.append("Duplicate graph edge identifiers detected.")
    if dangling:
        diagnostics.append("Dangling graph edges detected.")
    if self_loops:
        diagnostics.append("Unexpected graph self-loops detected.")

    basis = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "duplicate_node_ids": duplicate_nodes,
        "duplicate_edge_ids": duplicate_edges,
        "dangling_edge_ids": dangling,
        "self_loop_edge_ids": self_loops,
        "diagnostics": diagnostics,
    }
    return ConstitutionalGraphIntegrity(
        node_count=len(nodes),
        edge_count=len(edges),
        duplicate_node_ids=duplicate_nodes,
        duplicate_edge_ids=duplicate_edges,
        dangling_edge_ids=dangling,
        self_loop_edge_ids=self_loops,
        diagnostics=tuple(diagnostics),
        integrity_fingerprint=canonical_fingerprint(basis),
    )

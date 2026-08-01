from __future__ import annotations

from collections import Counter

from ..fingerprints import canonical_fingerprint
from .directorate_contracts import (
    CANONICAL_DIRECTORATES,
    DirectorateEdgeKind,
    DirectorateNodeKind,
)
from .directorate_models import (
    DirectorateEdge,
    DirectorateNode,
    DirectorateProjectionIntegrity,
)


def verify_directorate_foundation_integrity(
    nodes: tuple[DirectorateNode, ...],
    edges: tuple[DirectorateEdge, ...],
) -> DirectorateProjectionIntegrity:
    node_ids = [node.node_id for node in nodes]
    edge_ids = [edge.edge_id for edge in edges]
    node_by_id = {node.node_id: node for node in nodes}
    known_ids = set(node_by_id)

    duplicate_node_ids = tuple(
        sorted(node_id for node_id, count in Counter(node_ids).items() if count > 1)
    )
    duplicate_edge_ids = tuple(
        sorted(edge_id for edge_id, count in Counter(edge_ids).items() if count > 1)
    )
    dangling_edge_ids = tuple(
        sorted(
            edge.edge_id
            for edge in edges
            if edge.source_node_id not in known_ids
            or edge.target_node_id not in known_ids
        )
    )

    present_directorates = {
        node.canonical_key
        for node in nodes
        if node.node_kind is DirectorateNodeKind.DIRECTORATE
    }
    expected_directorates = {key for key, _ in CANONICAL_DIRECTORATES}
    missing_directorate_keys = tuple(sorted(expected_directorates - present_directorates))

    invalid_edge_ids: list[str] = []
    for edge in edges:
        source = node_by_id.get(edge.source_node_id)
        target = node_by_id.get(edge.target_node_id)
        if source is None or target is None:
            continue
        if edge.edge_kind is DirectorateEdgeKind.SUPERVISES:
            if source.node_kind is not DirectorateNodeKind.ORGANIZATIONAL_UNIT:
                invalid_edge_ids.append(edge.edge_id)
            if target.node_kind is not DirectorateNodeKind.DIRECTORATE:
                invalid_edge_ids.append(edge.edge_id)
        if edge.edge_kind is DirectorateEdgeKind.RESPONSIBLE_FOR:
            if source.node_kind is not DirectorateNodeKind.DIRECTORATE:
                invalid_edge_ids.append(edge.edge_id)
            if target.node_kind is not DirectorateNodeKind.RESPONSIBILITY:
                invalid_edge_ids.append(edge.edge_id)

    responsibility_targets = {
        edge.target_node_id
        for edge in edges
        if edge.edge_kind is DirectorateEdgeKind.RESPONSIBLE_FOR
    }
    orphan_responsibility_ids = tuple(
        sorted(
            node.node_id
            for node in nodes
            if node.node_kind is DirectorateNodeKind.RESPONSIBILITY
            and node.node_id not in responsibility_targets
        )
    )

    diagnostics: list[str] = []
    if duplicate_node_ids:
        diagnostics.append("Duplicate directorate node identifiers detected.")
    if duplicate_edge_ids:
        diagnostics.append("Duplicate directorate edge identifiers detected.")
    if dangling_edge_ids:
        diagnostics.append("Dangling directorate edges detected.")
    if missing_directorate_keys:
        diagnostics.append("Canonical directorates are missing.")
    if invalid_edge_ids:
        diagnostics.append("Invalid directorate edge semantics detected.")
    if orphan_responsibility_ids:
        diagnostics.append("Orphan responsibilities detected.")

    basis = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "directorate_count": len(present_directorates),
        "duplicate_node_ids": duplicate_node_ids,
        "duplicate_edge_ids": duplicate_edge_ids,
        "dangling_edge_ids": dangling_edge_ids,
        "missing_directorate_keys": missing_directorate_keys,
        "invalid_edge_ids": sorted(set(invalid_edge_ids)),
        "orphan_responsibility_ids": orphan_responsibility_ids,
        "diagnostics": diagnostics,
    }

    return DirectorateProjectionIntegrity(
        node_count=len(nodes),
        edge_count=len(edges),
        directorate_count=len(present_directorates),
        duplicate_node_ids=duplicate_node_ids,
        duplicate_edge_ids=duplicate_edge_ids,
        dangling_edge_ids=dangling_edge_ids,
        missing_directorate_keys=missing_directorate_keys,
        invalid_edge_ids=tuple(sorted(set(invalid_edge_ids))),
        orphan_responsibility_ids=orphan_responsibility_ids,
        diagnostics=tuple(diagnostics),
        fingerprint=canonical_fingerprint(basis),
    )

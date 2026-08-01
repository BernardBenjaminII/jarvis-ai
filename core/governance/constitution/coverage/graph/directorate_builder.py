from __future__ import annotations

from typing import Any

from ..fingerprints import canonical_fingerprint
from .directorate_contracts import (
    CANONICAL_DIRECTORATES,
    DirectorateEdgeKind,
    DirectorateNodeKind,
)
from .directorate_models import DirectorateEdge, DirectorateNode


RESPONSIBILITIES: tuple[tuple[str, str, str], ...] = (
    ("executive", "mission_direction", "Mission direction and executive command"),
    ("governance", "constitutional_governance", "Constitutional governance and certification"),
    ("knowledge", "knowledge_stewardship", "Knowledge stewardship and catalog integrity"),
    ("reasoning", "cognitive_reasoning", "Reasoning, evidence synthesis, and inference"),
    ("software_engineering", "software_delivery", "Software architecture and delivery"),
    ("planning", "mission_planning", "Mission planning and plan integrity"),
    ("operations", "operational_execution", "Operational execution and telemetry"),
    ("intelligence_acquisition", "intelligence_acquisition", "External intelligence acquisition"),
)


def _node(
    node_id: str,
    node_kind: DirectorateNodeKind,
    label: str,
    canonical_key: str,
    attributes: dict[str, Any],
) -> DirectorateNode:
    basis = {
        "node_id": node_id,
        "node_kind": node_kind.value,
        "label": label,
        "canonical_key": canonical_key,
        "attributes": attributes,
    }
    return DirectorateNode(
        node_id=node_id,
        node_kind=node_kind,
        label=label,
        canonical_key=canonical_key,
        attributes=attributes,
        fingerprint=canonical_fingerprint(basis),
    )


def _edge(
    edge_id: str,
    source_node_id: str,
    target_node_id: str,
    edge_kind: DirectorateEdgeKind,
    attributes: dict[str, Any],
) -> DirectorateEdge:
    basis = {
        "edge_id": edge_id,
        "source_node_id": source_node_id,
        "target_node_id": target_node_id,
        "edge_kind": edge_kind.value,
        "attributes": attributes,
    }
    return DirectorateEdge(
        edge_id=edge_id,
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        edge_kind=edge_kind,
        attributes=attributes,
        fingerprint=canonical_fingerprint(basis),
    )


def build_directorate_foundation(
    repository_nodes: list[dict[str, Any]],
) -> tuple[tuple[DirectorateNode, ...], tuple[DirectorateEdge, ...]]:
    nodes: dict[str, DirectorateNode] = {}
    edges: dict[str, DirectorateEdge] = {}

    organization_id = "organizational_unit:jarvis"
    nodes[organization_id] = _node(
        organization_id,
        DirectorateNodeKind.ORGANIZATIONAL_UNIT,
        "JARVIS Executive Organization",
        "jarvis",
        {"root": True},
    )

    for key, label in CANONICAL_DIRECTORATES:
        directorate_id = f"directorate:{key}"
        nodes[directorate_id] = _node(
            directorate_id,
            DirectorateNodeKind.DIRECTORATE,
            label,
            key,
            {"canonical": True},
        )
        edge_id = f"supervises:{organization_id}:{directorate_id}"
        edges[edge_id] = _edge(
            edge_id,
            organization_id,
            directorate_id,
            DirectorateEdgeKind.SUPERVISES,
            {"canonical": True},
        )

    for directorate_key, responsibility_key, label in RESPONSIBILITIES:
        responsibility_id = f"responsibility:{responsibility_key}"
        nodes[responsibility_id] = _node(
            responsibility_id,
            DirectorateNodeKind.RESPONSIBILITY,
            label,
            responsibility_key,
            {"canonical": True},
        )
        directorate_id = f"directorate:{directorate_key}"
        edge_id = f"responsible_for:{directorate_id}:{responsibility_id}"
        edges[edge_id] = _edge(
            edge_id,
            directorate_id,
            responsibility_id,
            DirectorateEdgeKind.RESPONSIBLE_FOR,
            {"canonical": True},
        )

    package_paths = sorted(
        {
            str(node.get("path", "")).strip()
            for node in repository_nodes
            if str(node.get("node_kind", "")) == "package"
            and str(node.get("path", "")).strip()
        }
    )
    for path in package_paths:
        domain_key = path.replace("/", ".").replace("\\", ".")
        domain_id = f"ownership_domain:{domain_key}"
        nodes[domain_id] = _node(
            domain_id,
            DirectorateNodeKind.OWNERSHIP_DOMAIN,
            path,
            domain_key,
            {"repository_path": path},
        )

    return (
        tuple(sorted(nodes.values(), key=lambda item: item.node_id)),
        tuple(sorted(edges.values(), key=lambda item: item.edge_id)),
    )

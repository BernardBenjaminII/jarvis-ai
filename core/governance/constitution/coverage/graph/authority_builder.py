from __future__ import annotations

from typing import Any

from ..fingerprints import canonical_fingerprint
from .authority_contracts import (
    AuthorityClass,
    AuthorityEdgeKind,
    AuthorityNodeKind,
)
from .authority_models import AuthorityEdge, AuthorityNode


def normalize_authority_class(value: str) -> AuthorityClass:
    normalized = value.strip().lower()
    if normalized in {"critical", "critical_hotspot"}:
        return AuthorityClass.CRITICAL
    if normalized in {"review", "review_hotspot", "underutilized"}:
        return AuthorityClass.REVIEW
    if normalized in {"active", "exercised"}:
        return AuthorityClass.ACTIVE
    if normalized in {"cold", "unused"}:
        return AuthorityClass.COLD
    return AuthorityClass.UNKNOWN


def _node(
    node_id: str,
    node_kind: AuthorityNodeKind,
    label: str,
    attributes: dict[str, Any],
) -> AuthorityNode:
    basis = {
        "node_id": node_id,
        "node_kind": node_kind.value,
        "label": label,
        "attributes": attributes,
    }
    return AuthorityNode(
        node_id=node_id,
        node_kind=node_kind,
        label=label,
        attributes=attributes,
        fingerprint=canonical_fingerprint(basis),
    )


def _edge(
    edge_id: str,
    source_node_id: str,
    target_node_id: str,
    edge_kind: AuthorityEdgeKind,
    attributes: dict[str, Any],
) -> AuthorityEdge:
    basis = {
        "edge_id": edge_id,
        "source_node_id": source_node_id,
        "target_node_id": target_node_id,
        "edge_kind": edge_kind.value,
        "attributes": attributes,
    }
    return AuthorityEdge(
        edge_id=edge_id,
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        edge_kind=edge_kind,
        attributes=attributes,
        fingerprint=canonical_fingerprint(basis),
    )


def build_authority_graph(
    graph_nodes: list[dict[str, Any]],
    graph_edges: list[dict[str, Any]],
) -> tuple[tuple[AuthorityNode, ...], tuple[AuthorityEdge, ...]]:
    source_nodes = {
        str(node.get("node_id", "")): node
        for node in graph_nodes
        if str(node.get("node_id", ""))
    }

    authority_nodes: dict[str, AuthorityNode] = {}
    authority_edges: dict[str, AuthorityEdge] = {}

    for authority_class in AuthorityClass:
        class_id = f"authority_class:{authority_class.value}"
        authority_nodes[class_id] = _node(
            class_id,
            AuthorityNodeKind.AUTHORITY_CLASS,
            authority_class.value,
            {},
        )

    for node_id, node in sorted(source_nodes.items()):
        node_type = str(node.get("node_type", ""))
        label = str(node.get("label", node_id))
        attributes = dict(node.get("attributes", {}))

        if node_type == "article":
            target_kind = AuthorityNodeKind.CONSTITUTIONAL_ARTICLE
            article_class = normalize_authority_class(
                str(attributes.get("classification", "unknown"))
            )
            authority_nodes[node_id] = _node(
                node_id,
                target_kind,
                label,
                attributes,
            )
            class_node_id = f"authority_class:{article_class.value}"
            edge_id = f"classified:{node_id}:{article_class.value}"
            authority_edges[edge_id] = _edge(
                edge_id,
                node_id,
                class_node_id,
                AuthorityEdgeKind.CLASSIFIED_AS,
                {},
            )

        elif node_type == "repository_artifact":
            authority_nodes[node_id] = _node(
                node_id,
                AuthorityNodeKind.GOVERNED_ARTIFACT,
                label,
                attributes,
            )

        elif node_type == "domain":
            authority_nodes[node_id] = _node(
                node_id,
                AuthorityNodeKind.GOVERNANCE_DOMAIN,
                label,
                attributes,
            )

    for edge in sorted(graph_edges, key=lambda item: str(item.get("edge_id", ""))):
        source_id = str(edge.get("source_node_id", ""))
        target_id = str(edge.get("target_node_id", ""))
        edge_type = str(edge.get("edge_type", ""))
        attributes = dict(edge.get("attributes", {}))

        if source_id not in authority_nodes or target_id not in authority_nodes:
            continue

        if edge_type == "governs":
            edge_id = f"authorizes:{source_id}:{target_id}"
            authority_edges[edge_id] = _edge(
                edge_id,
                source_id,
                target_id,
                AuthorityEdgeKind.AUTHORIZES,
                {
                    **attributes,
                    "derived_from_edge": str(edge.get("edge_id", "")),
                },
            )
        elif edge_type == "observed_in_domain":
            edge_id = f"exercised:{source_id}:{target_id}"
            authority_edges[edge_id] = _edge(
                edge_id,
                source_id,
                target_id,
                AuthorityEdgeKind.EXERCISED_IN,
                {
                    **attributes,
                    "derived_from_edge": str(edge.get("edge_id", "")),
                },
            )
        elif edge_type == "belongs_to_domain":
            edge_id = f"supports-class:{source_id}:{target_id}"
            authority_edges[edge_id] = _edge(
                edge_id,
                source_id,
                target_id,
                AuthorityEdgeKind.SUPPORTS_AUTHORITY_CLASS,
                {
                    **attributes,
                    "derived_from_edge": str(edge.get("edge_id", "")),
                },
            )

    return (
        tuple(sorted(authority_nodes.values(), key=lambda item: item.node_id)),
        tuple(sorted(authority_edges.values(), key=lambda item: item.edge_id)),
    )

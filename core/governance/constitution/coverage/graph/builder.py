from __future__ import annotations

from typing import Any

from ..fingerprints import canonical_fingerprint
from .contracts import ConstitutionalGraphEdgeType, ConstitutionalGraphNodeType
from .models import ConstitutionalGraphEdge, ConstitutionalGraphNode


def _node(
    node_id: str,
    node_type: ConstitutionalGraphNodeType,
    label: str,
    attributes: dict[str, Any],
) -> ConstitutionalGraphNode:
    basis = {
        "node_id": node_id,
        "node_type": node_type.value,
        "label": label,
        "attributes": attributes,
    }
    return ConstitutionalGraphNode(
        node_id=node_id,
        node_type=node_type,
        label=label,
        attributes=attributes,
        node_fingerprint=canonical_fingerprint(basis),
    )


def _edge(
    edge_id: str,
    source_node_id: str,
    target_node_id: str,
    edge_type: ConstitutionalGraphEdgeType,
    attributes: dict[str, Any],
) -> ConstitutionalGraphEdge:
    basis = {
        "edge_id": edge_id,
        "source_node_id": source_node_id,
        "target_node_id": target_node_id,
        "edge_type": edge_type.value,
        "attributes": attributes,
    }
    return ConstitutionalGraphEdge(
        edge_id=edge_id,
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        edge_type=edge_type,
        attributes=attributes,
        edge_fingerprint=canonical_fingerprint(basis),
    )


def build_foundation_graph(
    article_usage: list[dict[str, Any]],
) -> tuple[tuple[ConstitutionalGraphNode, ...], tuple[ConstitutionalGraphEdge, ...]]:
    nodes: dict[str, ConstitutionalGraphNode] = {}
    edges: dict[str, ConstitutionalGraphEdge] = {}

    for article in sorted(article_usage, key=lambda item: str(item.get("article_id", ""))):
        article_id = str(article.get("article_id", ""))
        article_node_id = f"article:{article_id}"
        nodes[article_node_id] = _node(
            article_node_id,
            ConstitutionalGraphNodeType.ARTICLE,
            article_id,
            {
                "classification": str(article.get("classification", "unused")),
                "reference_count": int(article.get("reference_count", 0)),
                "artifact_count": int(article.get("artifact_count", 0)),
                "review_required_count": int(article.get("review_required_count", 0)),
                "noncompliant_count": int(article.get("noncompliant_count", 0)),
                "usage_fingerprint": str(article.get("usage_fingerprint", "")),
            },
        )

        for artifact_id in sorted({str(value) for value in article.get("artifacts", [])}):
            artifact_node_id = f"artifact:{artifact_id}"
            nodes.setdefault(
                artifact_node_id,
                _node(
                    artifact_node_id,
                    ConstitutionalGraphNodeType.REPOSITORY_ARTIFACT,
                    artifact_id,
                    {},
                ),
            )
            edge_id = f"governs:{article_id}:{artifact_id}"
            edges[edge_id] = _edge(
                edge_id,
                article_node_id,
                artifact_node_id,
                ConstitutionalGraphEdgeType.GOVERNS,
                {},
            )

        for domain in sorted({str(value) for value in article.get("domains", [])}):
            domain_node_id = f"domain:{domain}"
            nodes.setdefault(
                domain_node_id,
                _node(
                    domain_node_id,
                    ConstitutionalGraphNodeType.DOMAIN,
                    domain,
                    {},
                ),
            )
            edge_id = f"observed:{article_id}:{domain}"
            edges[edge_id] = _edge(
                edge_id,
                article_node_id,
                domain_node_id,
                ConstitutionalGraphEdgeType.OBSERVED_IN_DOMAIN,
                {},
            )

        artifact_ids = sorted({str(value) for value in article.get("artifacts", [])})
        domains = sorted({str(value) for value in article.get("domains", [])})
        if len(domains) == 1:
            domain = domains[0]
            domain_node_id = f"domain:{domain}"
            for artifact_id in artifact_ids:
                edge_id = f"belongs:{artifact_id}:{domain}"
                edges.setdefault(
                    edge_id,
                    _edge(
                        edge_id,
                        f"artifact:{artifact_id}",
                        domain_node_id,
                        ConstitutionalGraphEdgeType.BELONGS_TO_DOMAIN,
                        {"inference": "single-domain article observation"},
                    ),
                )

    return (
        tuple(sorted(nodes.values(), key=lambda item: item.node_id)),
        tuple(sorted(edges.values(), key=lambda item: item.edge_id)),
    )

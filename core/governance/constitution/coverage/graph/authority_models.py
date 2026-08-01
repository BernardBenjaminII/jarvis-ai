from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .authority_contracts import AuthorityEdgeKind, AuthorityNodeKind


@dataclass(frozen=True, order=True)
class AuthorityNode:
    node_id: str
    node_kind: AuthorityNodeKind
    label: str
    attributes: dict[str, Any] = field(default_factory=dict, compare=False)
    fingerprint: str = field(default="", compare=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_kind": self.node_kind.value,
            "label": self.label,
            "attributes": self.attributes,
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, order=True)
class AuthorityEdge:
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_kind: AuthorityEdgeKind
    attributes: dict[str, Any] = field(default_factory=dict, compare=False)
    fingerprint: str = field(default="", compare=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "edge_kind": self.edge_kind.value,
            "attributes": self.attributes,
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True)
class AuthorityGraphIntegrity:
    node_count: int
    edge_count: int
    duplicate_node_ids: tuple[str, ...]
    duplicate_edge_ids: tuple[str, ...]
    dangling_edge_ids: tuple[str, ...]
    invalid_authorization_edge_ids: tuple[str, ...]
    diagnostics: tuple[str, ...]
    fingerprint: str

    @property
    def is_valid(self) -> bool:
        return not self.diagnostics

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "duplicate_node_ids": list(self.duplicate_node_ids),
            "duplicate_edge_ids": list(self.duplicate_edge_ids),
            "dangling_edge_ids": list(self.dangling_edge_ids),
            "invalid_authorization_edge_ids": list(
                self.invalid_authorization_edge_ids
            ),
            "diagnostics": list(self.diagnostics),
            "is_valid": self.is_valid,
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True)
class AuthorityGraphMetrics:
    article_count: int
    authority_class_count: int
    governed_artifact_count: int
    governance_domain_count: int
    authorization_edge_count: int
    classification_edge_count: int
    domain_edge_count: int
    authority_class_distribution: dict[str, int]
    exercised_article_count: int
    unexercised_article_count: int
    authority_utilization_ratio: float
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "article_count": self.article_count,
            "authority_class_count": self.authority_class_count,
            "governed_artifact_count": self.governed_artifact_count,
            "governance_domain_count": self.governance_domain_count,
            "authorization_edge_count": self.authorization_edge_count,
            "classification_edge_count": self.classification_edge_count,
            "domain_edge_count": self.domain_edge_count,
            "authority_class_distribution": self.authority_class_distribution,
            "exercised_article_count": self.exercised_article_count,
            "unexercised_article_count": self.unexercised_article_count,
            "authority_utilization_ratio": self.authority_utilization_ratio,
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True)
class AuthorityGraphAssessment:
    schema_version: str
    graph_foundation_fingerprint: str
    article_intelligence_fingerprint: str
    authority_graph_fingerprint: str
    nodes: tuple[AuthorityNode, ...]
    edges: tuple[AuthorityEdge, ...]
    metrics: AuthorityGraphMetrics
    integrity: AuthorityGraphIntegrity
    diagnostics: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "graph_foundation_fingerprint": self.graph_foundation_fingerprint,
            "article_intelligence_fingerprint": self.article_intelligence_fingerprint,
            "authority_graph_fingerprint": self.authority_graph_fingerprint,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "metrics": self.metrics.to_dict(),
            "integrity": self.integrity.to_dict(),
            "diagnostics": list(self.diagnostics),
        }

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .repository_contracts import RepositoryEdgeKind, RepositoryNodeKind

@dataclass(frozen=True, order=True)
class RepositoryNode:
    node_id: str
    node_kind: RepositoryNodeKind
    label: str
    path: str
    attributes: dict[str, Any] = field(default_factory=dict, compare=False)
    fingerprint: str = field(default="", compare=False)
    def to_dict(self) -> dict[str, Any]:
        return {"node_id": self.node_id, "node_kind": self.node_kind.value,
                "label": self.label, "path": self.path,
                "attributes": self.attributes, "fingerprint": self.fingerprint}

@dataclass(frozen=True, order=True)
class RepositoryEdge:
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_kind: RepositoryEdgeKind
    attributes: dict[str, Any] = field(default_factory=dict, compare=False)
    fingerprint: str = field(default="", compare=False)
    def to_dict(self) -> dict[str, Any]:
        return {"edge_id": self.edge_id, "source_node_id": self.source_node_id,
                "target_node_id": self.target_node_id, "edge_kind": self.edge_kind.value,
                "attributes": self.attributes, "fingerprint": self.fingerprint}

@dataclass(frozen=True)
class RepositoryProjectionIntegrity:
    node_count: int
    edge_count: int
    duplicate_node_ids: tuple[str, ...]
    duplicate_edge_ids: tuple[str, ...]
    dangling_edge_ids: tuple[str, ...]
    invalid_containment_edge_ids: tuple[str, ...]
    orphan_node_ids: tuple[str, ...]
    diagnostics: tuple[str, ...]
    fingerprint: str
    @property
    def is_valid(self) -> bool:
        return not self.diagnostics
    def to_dict(self) -> dict[str, Any]:
        return {"node_count": self.node_count, "edge_count": self.edge_count,
                "duplicate_node_ids": list(self.duplicate_node_ids),
                "duplicate_edge_ids": list(self.duplicate_edge_ids),
                "dangling_edge_ids": list(self.dangling_edge_ids),
                "invalid_containment_edge_ids": list(self.invalid_containment_edge_ids),
                "orphan_node_ids": list(self.orphan_node_ids),
                "diagnostics": list(self.diagnostics),
                "is_valid": self.is_valid, "fingerprint": self.fingerprint}

@dataclass(frozen=True)
class RepositoryProjectionMetrics:
    repository_count: int
    package_count: int
    module_count: int
    document_count: int
    test_count: int
    verification_count: int
    configuration_count: int
    executable_count: int
    data_artifact_count: int
    unknown_count: int
    containment_edge_count: int
    classified_node_count: int
    unclassified_node_count: int
    classification_completeness_ratio: float
    node_kind_distribution: dict[str, int]
    fingerprint: str
    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

@dataclass(frozen=True)
class RepositoryProjectionAssessment:
    schema_version: str
    authority_graph_fingerprint: str
    graph_foundation_fingerprint: str
    article_intelligence_fingerprint: str
    repository_projection_fingerprint: str
    nodes: tuple[RepositoryNode, ...]
    edges: tuple[RepositoryEdge, ...]
    metrics: RepositoryProjectionMetrics
    integrity: RepositoryProjectionIntegrity
    diagnostics: tuple[str, ...]
    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version,
                "authority_graph_fingerprint": self.authority_graph_fingerprint,
                "graph_foundation_fingerprint": self.graph_foundation_fingerprint,
                "article_intelligence_fingerprint": self.article_intelligence_fingerprint,
                "repository_projection_fingerprint": self.repository_projection_fingerprint,
                "nodes": [n.to_dict() for n in self.nodes],
                "edges": [e.to_dict() for e in self.edges],
                "metrics": self.metrics.to_dict(),
                "integrity": self.integrity.to_dict(),
                "diagnostics": list(self.diagnostics)}

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .contracts import ConstitutionalGraphEdgeType, ConstitutionalGraphNodeType


@dataclass(frozen=True, order=True)
class ConstitutionalGraphNode:
    node_id: str
    node_type: ConstitutionalGraphNodeType
    label: str
    attributes: dict[str, Any] = field(default_factory=dict, compare=False)
    node_fingerprint: str = field(default="", compare=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "label": self.label,
            "attributes": self.attributes,
            "node_fingerprint": self.node_fingerprint,
        }


@dataclass(frozen=True, order=True)
class ConstitutionalGraphEdge:
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: ConstitutionalGraphEdgeType
    attributes: dict[str, Any] = field(default_factory=dict, compare=False)
    edge_fingerprint: str = field(default="", compare=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "edge_type": self.edge_type.value,
            "attributes": self.attributes,
            "edge_fingerprint": self.edge_fingerprint,
        }


@dataclass(frozen=True)
class ConstitutionalGraphIntegrity:
    node_count: int
    edge_count: int
    duplicate_node_ids: tuple[str, ...]
    duplicate_edge_ids: tuple[str, ...]
    dangling_edge_ids: tuple[str, ...]
    self_loop_edge_ids: tuple[str, ...]
    diagnostics: tuple[str, ...]
    integrity_fingerprint: str

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
            "self_loop_edge_ids": list(self.self_loop_edge_ids),
            "diagnostics": list(self.diagnostics),
            "is_valid": self.is_valid,
            "integrity_fingerprint": self.integrity_fingerprint,
        }


@dataclass(frozen=True)
class ConstitutionalGraphMetrics:
    node_count: int
    edge_count: int
    node_type_counts: dict[str, int]
    edge_type_counts: dict[str, int]
    isolated_node_count: int
    connected_node_count: int
    graph_density: float
    metrics_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "node_type_counts": self.node_type_counts,
            "edge_type_counts": self.edge_type_counts,
            "isolated_node_count": self.isolated_node_count,
            "connected_node_count": self.connected_node_count,
            "graph_density": self.graph_density,
            "metrics_fingerprint": self.metrics_fingerprint,
        }


@dataclass(frozen=True)
class ConstitutionalGraphFoundationAssessment:
    schema_version: str
    article_intelligence_fingerprint: str
    graph_fingerprint: str
    nodes: tuple[ConstitutionalGraphNode, ...]
    edges: tuple[ConstitutionalGraphEdge, ...]
    metrics: ConstitutionalGraphMetrics
    integrity: ConstitutionalGraphIntegrity
    diagnostics: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "article_intelligence_fingerprint": self.article_intelligence_fingerprint,
            "graph_fingerprint": self.graph_fingerprint,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "metrics": self.metrics.to_dict(),
            "integrity": self.integrity.to_dict(),
            "diagnostics": list(self.diagnostics),
        }

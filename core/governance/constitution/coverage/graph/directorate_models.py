from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .directorate_contracts import DirectorateEdgeKind, DirectorateNodeKind


@dataclass(frozen=True, order=True)
class DirectorateNode:
    node_id: str
    node_kind: DirectorateNodeKind
    label: str
    canonical_key: str
    attributes: dict[str, Any] = field(default_factory=dict, compare=False)
    fingerprint: str = field(default="", compare=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_kind": self.node_kind.value,
            "label": self.label,
            "canonical_key": self.canonical_key,
            "attributes": self.attributes,
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, order=True)
class DirectorateEdge:
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_kind: DirectorateEdgeKind
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
class DirectorateProjectionIntegrity:
    node_count: int
    edge_count: int
    directorate_count: int
    duplicate_node_ids: tuple[str, ...]
    duplicate_edge_ids: tuple[str, ...]
    dangling_edge_ids: tuple[str, ...]
    missing_directorate_keys: tuple[str, ...]
    invalid_edge_ids: tuple[str, ...]
    orphan_responsibility_ids: tuple[str, ...]
    diagnostics: tuple[str, ...]
    fingerprint: str

    @property
    def is_valid(self) -> bool:
        return not self.diagnostics

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "directorate_count": self.directorate_count,
            "duplicate_node_ids": list(self.duplicate_node_ids),
            "duplicate_edge_ids": list(self.duplicate_edge_ids),
            "dangling_edge_ids": list(self.dangling_edge_ids),
            "missing_directorate_keys": list(self.missing_directorate_keys),
            "invalid_edge_ids": list(self.invalid_edge_ids),
            "orphan_responsibility_ids": list(self.orphan_responsibility_ids),
            "diagnostics": list(self.diagnostics),
            "is_valid": self.is_valid,
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True)
class DirectorateFoundationAssessment:
    schema_version: str
    article_intelligence_fingerprint: str
    graph_foundation_fingerprint: str
    authority_graph_fingerprint: str
    repository_projection_fingerprint: str
    directorate_foundation_fingerprint: str
    nodes: tuple[DirectorateNode, ...]
    edges: tuple[DirectorateEdge, ...]
    integrity: DirectorateProjectionIntegrity
    diagnostics: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "article_intelligence_fingerprint": self.article_intelligence_fingerprint,
            "graph_foundation_fingerprint": self.graph_foundation_fingerprint,
            "authority_graph_fingerprint": self.authority_graph_fingerprint,
            "repository_projection_fingerprint": self.repository_projection_fingerprint,
            "directorate_foundation_fingerprint": self.directorate_foundation_fingerprint,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "integrity": self.integrity.to_dict(),
            "diagnostics": list(self.diagnostics),
        }

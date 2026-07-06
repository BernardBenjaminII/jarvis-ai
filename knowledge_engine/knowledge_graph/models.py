from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GraphNode:
    node_uuid: str
    node_type: str
    name: str
    canonical_name: str
    source_object_uuid: str | None
    confidence: float


@dataclass(frozen=True)
class GraphEdge:
    edge_uuid: str
    source_node_uuid: str
    target_node_uuid: str
    relationship_type: str
    source_object_uuid: str | None
    confidence: float
    evidence: str | None

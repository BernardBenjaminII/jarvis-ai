from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .directorate_contracts import DirectorateEdgeKind, DirectorateNodeKind
from .directorate_models import DirectorateEdge, DirectorateNode


class ConstitutionalDirectorateGraph:
    def __init__(
        self,
        nodes: Iterable[DirectorateNode],
        edges: Iterable[DirectorateEdge],
    ) -> None:
        self._nodes = tuple(sorted(nodes, key=lambda item: item.node_id))
        self._edges = tuple(sorted(edges, key=lambda item: item.edge_id))
        self._node_by_id = {node.node_id: node for node in self._nodes}

        outgoing: dict[str, list[DirectorateEdge]] = defaultdict(list)
        incoming: dict[str, list[DirectorateEdge]] = defaultdict(list)
        for edge in self._edges:
            outgoing[edge.source_node_id].append(edge)
            incoming[edge.target_node_id].append(edge)

        self._outgoing = {
            key: tuple(sorted(value, key=lambda item: item.edge_id))
            for key, value in outgoing.items()
        }
        self._incoming = {
            key: tuple(sorted(value, key=lambda item: item.edge_id))
            for key, value in incoming.items()
        }

    @property
    def nodes(self) -> tuple[DirectorateNode, ...]:
        return self._nodes

    @property
    def edges(self) -> tuple[DirectorateEdge, ...]:
        return self._edges

    def node(self, node_id: str) -> DirectorateNode | None:
        return self._node_by_id.get(node_id)

    def nodes_by_kind(
        self,
        node_kind: DirectorateNodeKind,
    ) -> tuple[DirectorateNode, ...]:
        return tuple(
            node for node in self._nodes if node.node_kind is node_kind
        )

    def outgoing(
        self,
        node_id: str,
        edge_kind: DirectorateEdgeKind | None = None,
    ) -> tuple[DirectorateEdge, ...]:
        edges = self._outgoing.get(node_id, ())
        if edge_kind is None:
            return edges
        return tuple(edge for edge in edges if edge.edge_kind is edge_kind)

    def incoming(
        self,
        node_id: str,
        edge_kind: DirectorateEdgeKind | None = None,
    ) -> tuple[DirectorateEdge, ...]:
        edges = self._incoming.get(node_id, ())
        if edge_kind is None:
            return edges
        return tuple(edge for edge in edges if edge.edge_kind is edge_kind)

    def targets(
        self,
        node_id: str,
        edge_kind: DirectorateEdgeKind,
    ) -> tuple[DirectorateNode, ...]:
        return tuple(
            self._node_by_id[edge.target_node_id]
            for edge in self.outgoing(node_id, edge_kind)
            if edge.target_node_id in self._node_by_id
        )

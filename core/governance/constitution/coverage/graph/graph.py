from __future__ import annotations

from collections import defaultdict, deque
from typing import Iterable

from .models import ConstitutionalGraphEdge, ConstitutionalGraphNode


class ConstitutionalGraph:
    def __init__(
        self,
        nodes: Iterable[ConstitutionalGraphNode],
        edges: Iterable[ConstitutionalGraphEdge],
    ) -> None:
        self._nodes = tuple(sorted(nodes, key=lambda item: item.node_id))
        self._edges = tuple(sorted(edges, key=lambda item: item.edge_id))
        self._node_by_id = {node.node_id: node for node in self._nodes}

        outgoing: dict[str, list[ConstitutionalGraphEdge]] = defaultdict(list)
        incoming: dict[str, list[ConstitutionalGraphEdge]] = defaultdict(list)
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
    def nodes(self) -> tuple[ConstitutionalGraphNode, ...]:
        return self._nodes

    @property
    def edges(self) -> tuple[ConstitutionalGraphEdge, ...]:
        return self._edges

    def node(self, node_id: str) -> ConstitutionalGraphNode | None:
        return self._node_by_id.get(node_id)

    def outgoing_edges(self, node_id: str) -> tuple[ConstitutionalGraphEdge, ...]:
        return self._outgoing.get(node_id, ())

    def incoming_edges(self, node_id: str) -> tuple[ConstitutionalGraphEdge, ...]:
        return self._incoming.get(node_id, ())

    def neighbors(self, node_id: str) -> tuple[ConstitutionalGraphNode, ...]:
        neighbor_ids = {
            edge.target_node_id for edge in self.outgoing_edges(node_id)
        } | {
            edge.source_node_id for edge in self.incoming_edges(node_id)
        }
        return tuple(
            self._node_by_id[item]
            for item in sorted(neighbor_ids)
            if item in self._node_by_id
        )

    def reachable_from(self, node_id: str, max_depth: int | None = None) -> tuple[str, ...]:
        if node_id not in self._node_by_id:
            return ()

        visited = {node_id}
        queue = deque([(node_id, 0)])
        reached: list[str] = []

        while queue:
            current, depth = queue.popleft()
            if max_depth is not None and depth >= max_depth:
                continue
            for edge in self.outgoing_edges(current):
                target = edge.target_node_id
                if target in visited:
                    continue
                visited.add(target)
                reached.append(target)
                queue.append((target, depth + 1))

        return tuple(reached)

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .authority_contracts import AuthorityEdgeKind, AuthorityNodeKind
from .authority_models import AuthorityEdge, AuthorityNode


class ConstitutionalAuthorityGraph:
    def __init__(
        self,
        nodes: Iterable[AuthorityNode],
        edges: Iterable[AuthorityEdge],
    ) -> None:
        self._nodes = tuple(sorted(nodes, key=lambda item: item.node_id))
        self._edges = tuple(sorted(edges, key=lambda item: item.edge_id))
        self._node_by_id = {node.node_id: node for node in self._nodes}

        outgoing: dict[str, list[AuthorityEdge]] = defaultdict(list)
        incoming: dict[str, list[AuthorityEdge]] = defaultdict(list)
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
    def nodes(self) -> tuple[AuthorityNode, ...]:
        return self._nodes

    @property
    def edges(self) -> tuple[AuthorityEdge, ...]:
        return self._edges

    def node(self, node_id: str) -> AuthorityNode | None:
        return self._node_by_id.get(node_id)

    def nodes_by_kind(
        self,
        node_kind: AuthorityNodeKind,
    ) -> tuple[AuthorityNode, ...]:
        return tuple(
            node for node in self._nodes if node.node_kind is node_kind
        )

    def outgoing_edges(
        self,
        node_id: str,
        edge_kind: AuthorityEdgeKind | None = None,
    ) -> tuple[AuthorityEdge, ...]:
        edges = self._outgoing.get(node_id, ())
        if edge_kind is None:
            return edges
        return tuple(edge for edge in edges if edge.edge_kind is edge_kind)

    def incoming_edges(
        self,
        node_id: str,
        edge_kind: AuthorityEdgeKind | None = None,
    ) -> tuple[AuthorityEdge, ...]:
        edges = self._incoming.get(node_id, ())
        if edge_kind is None:
            return edges
        return tuple(edge for edge in edges if edge.edge_kind is edge_kind)

    def artifacts_authorized_by(self, article_node_id: str) -> tuple[AuthorityNode, ...]:
        target_ids = [
            edge.target_node_id
            for edge in self.outgoing_edges(
                article_node_id,
                AuthorityEdgeKind.AUTHORIZES,
            )
        ]
        return tuple(
            self._node_by_id[node_id]
            for node_id in sorted(target_ids)
            if node_id in self._node_by_id
        )

    def authorities_for_artifact(self, artifact_node_id: str) -> tuple[AuthorityNode, ...]:
        source_ids = [
            edge.source_node_id
            for edge in self.incoming_edges(
                artifact_node_id,
                AuthorityEdgeKind.AUTHORIZES,
            )
        ]
        return tuple(
            self._node_by_id[node_id]
            for node_id in sorted(source_ids)
            if node_id in self._node_by_id
        )

    def articles_in_class(self, authority_class: str) -> tuple[AuthorityNode, ...]:
        class_node_id = f"authority_class:{authority_class.strip().lower()}"
        article_ids = [
            edge.source_node_id
            for edge in self.incoming_edges(
                class_node_id,
                AuthorityEdgeKind.CLASSIFIED_AS,
            )
        ]
        return tuple(
            self._node_by_id[node_id]
            for node_id in sorted(article_ids)
            if node_id in self._node_by_id
        )

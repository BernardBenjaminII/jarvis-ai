from collections import defaultdict
from .repository_contracts import RepositoryEdgeKind, RepositoryNodeKind

class ConstitutionalRepositoryProjection:
    def __init__(self, nodes, edges):
        self._nodes = tuple(sorted(nodes, key=lambda x: x.node_id))
        self._edges = tuple(sorted(edges, key=lambda x: x.edge_id))
        self._by_id = {n.node_id: n for n in self._nodes}
        outgoing, incoming = defaultdict(list), defaultdict(list)
        for e in self._edges:
            outgoing[e.source_node_id].append(e); incoming[e.target_node_id].append(e)
        self._out = {k: tuple(sorted(v, key=lambda x: x.edge_id)) for k,v in outgoing.items()}
        self._in = {k: tuple(sorted(v, key=lambda x: x.edge_id)) for k,v in incoming.items()}
    @property
    def nodes(self): return self._nodes
    @property
    def edges(self): return self._edges
    def node(self, node_id): return self._by_id.get(node_id)
    def nodes_by_kind(self, kind: RepositoryNodeKind): return tuple(n for n in self._nodes if n.node_kind is kind)
    def children(self, node_id):
        ids = [e.target_node_id for e in self._out.get(node_id, ()) if e.edge_kind is RepositoryEdgeKind.CONTAINS]
        return tuple(self._by_id[i] for i in sorted(ids) if i in self._by_id)
    def parent(self, node_id):
        ids = [e.source_node_id for e in self._in.get(node_id, ()) if e.edge_kind is RepositoryEdgeKind.CONTAINS]
        return self._by_id.get(sorted(ids)[0]) if ids else None
    def descendants(self, node_id):
        seen, pending, result = set(), [node_id], []
        while pending:
            current = pending.pop(0)
            for child in self.children(current):
                if child.node_id not in seen:
                    seen.add(child.node_id); result.append(child); pending.append(child.node_id)
        return tuple(sorted(result, key=lambda x: x.node_id))

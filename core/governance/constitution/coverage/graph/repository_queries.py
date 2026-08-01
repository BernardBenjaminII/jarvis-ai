from .repository_contracts import RepositoryNodeKind
class ConstitutionalRepositoryQueryService:
    def __init__(self, graph): self._graph = graph
    def packages(self): return self._graph.nodes_by_kind(RepositoryNodeKind.PACKAGE)
    def modules(self): return self._graph.nodes_by_kind(RepositoryNodeKind.MODULE)
    def tests(self): return self._graph.nodes_by_kind(RepositoryNodeKind.TEST)
    def verifications(self): return self._graph.nodes_by_kind(RepositoryNodeKind.VERIFICATION)
    def children_of(self, node_id): return self._graph.children(node_id)
    def descendants_of(self, node_id): return self._graph.descendants(node_id)
    def artifacts_under_path(self, path):
        candidates = [n for n in self._graph.nodes if n.path == path and n.node_kind is RepositoryNodeKind.PACKAGE]
        return self._graph.descendants(candidates[0].node_id) if candidates else ()
    def unknown_artifacts(self): return self._graph.nodes_by_kind(RepositoryNodeKind.UNKNOWN)

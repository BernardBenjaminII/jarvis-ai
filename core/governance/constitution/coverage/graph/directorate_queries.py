from __future__ import annotations
from .directorate_contracts import DirectorateEdgeKind, DirectorateNodeKind
from .directorate_graph import ConstitutionalDirectorateGraph
from .directorate_models import DirectorateNode

class ConstitutionalDirectorateQueryService:
    def __init__(self,graph): self._graph=graph
    def directorates(self): return self._graph.nodes_by_kind(DirectorateNodeKind.DIRECTORATE)
    def responsibilities(self): return self._graph.nodes_by_kind(DirectorateNodeKind.RESPONSIBILITY)
    def ownership_domains(self): return self._graph.nodes_by_kind(DirectorateNodeKind.OWNERSHIP_DOMAIN)
    def owned_by(self,key): return self._graph.targets(f'directorate:{key}',DirectorateEdgeKind.OWNS)
    def maintained_by(self,key): return self._graph.targets(f'directorate:{key}',DirectorateEdgeKind.MAINTAINS)
    def responsibilities_of(self,key): return self._graph.targets(f'directorate:{key}',DirectorateEdgeKind.RESPONSIBLE_FOR)
    def owner_of_domain(self,domain_id):
        incoming=self._graph.incoming(domain_id,DirectorateEdgeKind.OWNS)
        return self._graph.node(incoming[0].source_node_id) if incoming else None
    def maintainers_of_domain(self,domain_id):
        return tuple(node for edge in self._graph.incoming(domain_id,DirectorateEdgeKind.MAINTAINS) if (node:=self._graph.node(edge.source_node_id)) is not None)
    def certifiers_of_domain(self,domain_id):
        return tuple(node for edge in self._graph.incoming(domain_id,DirectorateEdgeKind.CERTIFIES) if (node:=self._graph.node(edge.source_node_id)) is not None)
    def responsible_directorates_for_domain(self,domain_id):
        owner=self.owner_of_domain(domain_id); return (owner,) if owner else ()
    def unowned_domains(self): return tuple(d for d in self.ownership_domains() if not self._graph.incoming(d.node_id,DirectorateEdgeKind.OWNS))

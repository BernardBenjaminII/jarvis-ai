from collections import Counter
from ..fingerprints import canonical_fingerprint
from .repository_contracts import RepositoryEdgeKind, RepositoryNodeKind
from .repository_models import RepositoryProjectionIntegrity

def verify_repository_projection_integrity(nodes, edges):
    node_ids, edge_ids = [n.node_id for n in nodes], [e.edge_id for e in edges]
    by_id, known = {n.node_id: n for n in nodes}, set(node_ids)
    dup_nodes = tuple(sorted(k for k,v in Counter(node_ids).items() if v > 1))
    dup_edges = tuple(sorted(k for k,v in Counter(edge_ids).items() if v > 1))
    dangling = tuple(sorted(e.edge_id for e in edges if e.source_node_id not in known or e.target_node_id not in known))
    invalid = []
    for e in edges:
        if e.edge_kind is RepositoryEdgeKind.CONTAINS:
            s = by_id.get(e.source_node_id)
            if s is None or s.node_kind not in {RepositoryNodeKind.REPOSITORY, RepositoryNodeKind.PACKAGE}:
                invalid.append(e.edge_id)
    contained = {e.target_node_id for e in edges if e.edge_kind is RepositoryEdgeKind.CONTAINS}
    orphans = tuple(sorted(n.node_id for n in nodes if n.node_kind is not RepositoryNodeKind.REPOSITORY and n.node_id not in contained))
    diagnostics = []
    if dup_nodes: diagnostics.append("Duplicate repository node identifiers detected.")
    if dup_edges: diagnostics.append("Duplicate repository edge identifiers detected.")
    if dangling: diagnostics.append("Dangling repository edges detected.")
    if invalid: diagnostics.append("Invalid repository containment edges detected.")
    if orphans: diagnostics.append("Orphan repository nodes detected.")
    basis = {"node_count": len(nodes), "edge_count": len(edges), "duplicate_node_ids": dup_nodes,
             "duplicate_edge_ids": dup_edges, "dangling_edge_ids": dangling,
             "invalid_containment_edge_ids": sorted(invalid), "orphan_node_ids": orphans,
             "diagnostics": diagnostics}
    return RepositoryProjectionIntegrity(len(nodes), len(edges), dup_nodes, dup_edges, dangling,
                                         tuple(sorted(invalid)), orphans, tuple(diagnostics),
                                         canonical_fingerprint(basis))

from collections import Counter
from ..fingerprints import canonical_fingerprint
from .repository_contracts import RepositoryEdgeKind, RepositoryNodeKind
from .repository_models import RepositoryProjectionMetrics

def compute_repository_projection_metrics(nodes, edges):
    nc, ec = Counter(n.node_kind.value for n in nodes), Counter(e.edge_kind.value for e in edges)
    classified = sum(v for k,v in nc.items() if k != RepositoryNodeKind.UNKNOWN.value)
    unclassified = nc[RepositoryNodeKind.UNKNOWN.value]
    total = classified + unclassified
    ratio = round(classified / total, 12) if total else 0.0
    basis = {
        "repository_count": nc[RepositoryNodeKind.REPOSITORY.value],
        "package_count": nc[RepositoryNodeKind.PACKAGE.value],
        "module_count": nc[RepositoryNodeKind.MODULE.value],
        "document_count": nc[RepositoryNodeKind.DOCUMENT.value],
        "test_count": nc[RepositoryNodeKind.TEST.value],
        "verification_count": nc[RepositoryNodeKind.VERIFICATION.value],
        "configuration_count": nc[RepositoryNodeKind.CONFIGURATION.value],
        "executable_count": nc[RepositoryNodeKind.EXECUTABLE.value],
        "data_artifact_count": nc[RepositoryNodeKind.DATA_ARTIFACT.value],
        "unknown_count": unclassified,
        "containment_edge_count": ec[RepositoryEdgeKind.CONTAINS.value],
        "classified_node_count": classified,
        "unclassified_node_count": unclassified,
        "classification_completeness_ratio": ratio,
        "node_kind_distribution": dict(sorted(nc.items())),
    }
    return RepositoryProjectionMetrics(**basis, fingerprint=canonical_fingerprint(basis))

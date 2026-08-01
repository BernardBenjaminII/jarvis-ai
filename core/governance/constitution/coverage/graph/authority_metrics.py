from __future__ import annotations

from collections import Counter

from ..fingerprints import canonical_fingerprint
from .authority_contracts import AuthorityEdgeKind, AuthorityNodeKind
from .authority_models import (
    AuthorityEdge,
    AuthorityGraphMetrics,
    AuthorityNode,
)


def compute_authority_graph_metrics(
    nodes: tuple[AuthorityNode, ...],
    edges: tuple[AuthorityEdge, ...],
) -> AuthorityGraphMetrics:
    node_counts = Counter(node.node_kind.value for node in nodes)
    edge_counts = Counter(edge.edge_kind.value for edge in edges)

    class_distribution: Counter[str] = Counter()
    for edge in edges:
        if edge.edge_kind is AuthorityEdgeKind.CLASSIFIED_AS:
            class_distribution[edge.target_node_id.split(":", 1)[-1]] += 1

    exercised_articles = {
        edge.source_node_id
        for edge in edges
        if edge.edge_kind is AuthorityEdgeKind.AUTHORIZES
    }
    article_count = node_counts[AuthorityNodeKind.CONSTITUTIONAL_ARTICLE.value]
    exercised_count = len(exercised_articles)
    unexercised_count = article_count - exercised_count
    utilization = (
        round(exercised_count / article_count, 12)
        if article_count
        else 0.0
    )

    basis = {
        "article_count": article_count,
        "authority_class_count": node_counts[AuthorityNodeKind.AUTHORITY_CLASS.value],
        "governed_artifact_count": node_counts[AuthorityNodeKind.GOVERNED_ARTIFACT.value],
        "governance_domain_count": node_counts[AuthorityNodeKind.GOVERNANCE_DOMAIN.value],
        "authorization_edge_count": edge_counts[AuthorityEdgeKind.AUTHORIZES.value],
        "classification_edge_count": edge_counts[AuthorityEdgeKind.CLASSIFIED_AS.value],
        "domain_edge_count": edge_counts[AuthorityEdgeKind.EXERCISED_IN.value],
        "authority_class_distribution": dict(sorted(class_distribution.items())),
        "exercised_article_count": exercised_count,
        "unexercised_article_count": unexercised_count,
        "authority_utilization_ratio": utilization,
    }
    return AuthorityGraphMetrics(
        article_count=basis["article_count"],
        authority_class_count=basis["authority_class_count"],
        governed_artifact_count=basis["governed_artifact_count"],
        governance_domain_count=basis["governance_domain_count"],
        authorization_edge_count=basis["authorization_edge_count"],
        classification_edge_count=basis["classification_edge_count"],
        domain_edge_count=basis["domain_edge_count"],
        authority_class_distribution=basis["authority_class_distribution"],
        exercised_article_count=basis["exercised_article_count"],
        unexercised_article_count=basis["unexercised_article_count"],
        authority_utilization_ratio=basis["authority_utilization_ratio"],
        fingerprint=canonical_fingerprint(basis),
    )

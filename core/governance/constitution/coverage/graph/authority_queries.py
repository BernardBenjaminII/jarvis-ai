from __future__ import annotations

from .authority_graph import ConstitutionalAuthorityGraph
from .authority_models import AuthorityNode


class ConstitutionalAuthorityQueryService:
    def __init__(self, graph: ConstitutionalAuthorityGraph) -> None:
        self._graph = graph

    def governed_artifacts_for_article(
        self,
        article_id: str,
    ) -> tuple[AuthorityNode, ...]:
        node_id = (
            article_id
            if article_id.startswith("article:")
            else f"article:{article_id}"
        )
        return self._graph.artifacts_authorized_by(node_id)

    def governing_articles_for_artifact(
        self,
        artifact_id: str,
    ) -> tuple[AuthorityNode, ...]:
        node_id = (
            artifact_id
            if artifact_id.startswith("artifact:")
            else f"artifact:{artifact_id}"
        )
        return self._graph.authorities_for_artifact(node_id)

    def articles_by_authority_class(
        self,
        authority_class: str,
    ) -> tuple[AuthorityNode, ...]:
        return self._graph.articles_in_class(authority_class)

    def unexercised_articles(self) -> tuple[AuthorityNode, ...]:
        cold = self._graph.articles_in_class("cold")
        return tuple(
            node
            for node in cold
            if not self._graph.artifacts_authorized_by(node.node_id)
        )

from __future__ import annotations
from typing import Any

class ConstitutionalArticleQueryService:
    def __init__(self, usage_registry: list[dict[str, Any]], influence_scores: list[dict[str, Any]]) -> None:
        self._usage = sorted(usage_registry, key=lambda x: x["article_id"])
        self._scores = {x["article_id"]: x["influence_score"] for x in influence_scores}

    def top_governing_articles(self, limit: int = 10) -> list[dict[str, Any]]:
        return sorted(
            self._usage,
            key=lambda x: (self._scores.get(x["article_id"], 0.0), x["reference_count"], x["article_id"]),
            reverse=True,
        )[:max(0, limit)]

    def unused_articles(self) -> list[dict[str, Any]]:
        return [x for x in self._usage if x["reference_count"] == 0]

    def articles_for_domain(self, domain: str) -> list[dict[str, Any]]:
        target = domain.strip().lower()
        return [x for x in self._usage if target in {d.lower() for d in x.get("domains", [])}]

    def articles_requiring_review(self) -> list[dict[str, Any]]:
        return [x for x in self._usage if x["review_required_count"] > 0 or x["noncompliant_count"] > 0]

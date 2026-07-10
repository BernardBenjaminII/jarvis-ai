"""Models for Phase V-C Query Understanding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class QueryUnderstanding:
    """Structured interpretation of a user knowledge request."""

    original_query: str
    normalized_query: str
    retrieval_query: str
    task: str
    domains: tuple[str, ...]
    entities: tuple[str, ...]
    keywords: tuple[str, ...]
    desired_output: str
    specialists: tuple[str, ...]
    confidence: float
    explanation: str

    def as_dict(self) -> dict[str, Any]:
        """Return a stable, serializable representation."""

        return {
            "original_query": self.original_query,
            "normalized_query": self.normalized_query,
            "retrieval_query": self.retrieval_query,
            "task": self.task,
            "domains": list(self.domains),
            "entities": list(self.entities),
            "keywords": list(self.keywords),
            "desired_output": self.desired_output,
            "specialists": list(self.specialists),
            "confidence": round(self.confidence, 6),
            "explanation": self.explanation,
        }

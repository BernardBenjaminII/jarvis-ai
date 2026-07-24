"""Knowledge-integrated reasoning pipeline."""

from __future__ import annotations
import hashlib
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any
from core.reasoning.generation import (
    DeterministicHypothesisGenerator,
    HypothesisGenerationResult,
)
from core.reasoning.knowledge import AdaptedEvidenceBatch, KnowledgeEvidenceAdapter
from core.reasoning.models import ReasoningRequest, ReasoningResult
from core.reasoning.service import ReasoningEngine

KnowledgeSearch = Callable[[str, int], Iterable[Any]]


@dataclass(frozen=True, slots=True)
class KnowledgeReasoningOutcome:
    evidence_batch: AdaptedEvidenceBatch
    generation: HypothesisGenerationResult
    reasoning: ReasoningResult


def _request_id(goal: str, query: str) -> str:
    digest = hashlib.sha256(
        f"{goal}\x1f{query}".encode("utf-8")
    ).hexdigest()[:16]
    return f"knowledge_reasoning_{digest}"


class KnowledgeReasoningPipeline:
    """Join an injected Knowledge search callable to reasoning."""

    def __init__(
        self,
        search: KnowledgeSearch,
        *,
        adapter: KnowledgeEvidenceAdapter | None = None,
        generator: DeterministicHypothesisGenerator | None = None,
        engine: ReasoningEngine | None = None,
    ) -> None:
        self._search = search
        self._adapter = adapter or KnowledgeEvidenceAdapter()
        self._generator = generator or DeterministicHypothesisGenerator()
        self._engine = engine or ReasoningEngine()

    def reason(
        self,
        *,
        goal: str,
        query: str | None = None,
        limit: int = 8,
        constraints: tuple[str, ...] = (),
        context: dict[str, Any] | None = None,
    ) -> KnowledgeReasoningOutcome:
        search_query = " ".join((query or goal).split())
        raw_results = tuple(self._search(search_query, limit))
        batch = self._adapter.adapt(search_query, raw_results)
        generation = self._generator.generate(goal, batch.evidence)
        request = ReasoningRequest(
            request_id=_request_id(goal, search_query),
            goal=goal,
            evidence=batch.evidence,
            hypotheses=generation.hypotheses,
            constraints=constraints,
            context={
                **(context or {}),
                "knowledge_query": search_query,
                "knowledge_result_count": len(raw_results),
                "adapted_evidence_count": len(batch.evidence),
                "rejected_result_count": batch.rejected_count,
                "hypothesis_generation_strategy": generation.strategy,
            },
        )
        return KnowledgeReasoningOutcome(
            evidence_batch=batch,
            generation=generation,
            reasoning=self._engine.reason(request),
        )

from __future__ import annotations

from typing import Sequence
from core.cognition.reasoner import ExecutiveReasoningResult
from .enums import DecisionRepositoryDisposition
from .models import (
    DecisionAlternative, DecisionConstraint, DecisionRecord,
    DecisionRisk, DecisionSynthesisPolicy,
)
from .repository import InMemoryDecisionRepository
from .synthesizer import DeterministicDecisionSynthesizer

class ExecutiveDecisionService:
    def __init__(
        self,
        repository: InMemoryDecisionRepository,
        synthesizer: DeterministicDecisionSynthesizer | None = None,
    ) -> None:
        self._repository = repository
        self._synthesizer = synthesizer or DeterministicDecisionSynthesizer()

    def synthesize(
        self,
        *,
        reasoning: ExecutiveReasoningResult,
        alternatives: Sequence[DecisionAlternative],
        risks: Sequence[DecisionRisk] = (),
        constraints: Sequence[DecisionConstraint] = (),
        policy: DecisionSynthesisPolicy | None = None,
    ) -> tuple[DecisionRecord, DecisionRepositoryDisposition]:
        decision = self._synthesizer.synthesize(
            reasoning=reasoning,
            alternatives=alternatives,
            risks=risks,
            constraints=constraints,
            policy=policy,
        )
        created = self._repository.put(decision)
        return (
            decision,
            DecisionRepositoryDisposition.CREATED
            if created else DecisionRepositoryDisposition.DUPLICATE,
        )

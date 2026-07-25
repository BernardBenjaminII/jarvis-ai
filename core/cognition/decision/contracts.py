from __future__ import annotations

from typing import Protocol, Sequence
from core.cognition.reasoner import ExecutiveReasoningResult
from .models import (
    DecisionAlternative, DecisionConstraint, DecisionQuery,
    DecisionRecord, DecisionRisk, DecisionSynthesisPolicy,
)

class DecisionSynthesizer(Protocol):
    def synthesize(
        self,
        *,
        reasoning: ExecutiveReasoningResult,
        alternatives: Sequence[DecisionAlternative],
        risks: Sequence[DecisionRisk] = (),
        constraints: Sequence[DecisionConstraint] = (),
        policy: DecisionSynthesisPolicy | None = None,
    ) -> DecisionRecord: ...

class DecisionRepository(Protocol):
    def put(self, decision: DecisionRecord) -> bool: ...
    def get(self, decision_id: str) -> DecisionRecord: ...
    def query(self, query: DecisionQuery) -> Sequence[DecisionRecord]: ...
    def count(self) -> int: ...
    def close(self) -> None: ...

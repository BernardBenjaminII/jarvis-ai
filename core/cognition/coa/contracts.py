from __future__ import annotations
from typing import Protocol, Sequence, runtime_checkable, Any
from .models import AlternativeGenerationPolicy, AlternativeGenerationResult, CourseOfAction, CourseOfActionTemplate

@runtime_checkable
class ReasoningResultView(Protocol):
    """Minimal structural contract consumed from Genesis IV-A5."""
    @property
    def reasoning_id(self) -> str: ...

@runtime_checkable
class CourseOfActionGenerator(Protocol):
    def generate(self, reasoning_result: Any, templates: Sequence[CourseOfActionTemplate], policy: AlternativeGenerationPolicy | None = None) -> AlternativeGenerationResult: ...

@runtime_checkable
class CourseOfActionRepository(Protocol):
    def add(self, result: AlternativeGenerationResult) -> bool: ...
    def get(self, generation_id: str) -> AlternativeGenerationResult | None: ...
    def list_for_reasoning(self, reasoning_id: str) -> tuple[AlternativeGenerationResult, ...]: ...

__all__ = ["ReasoningResultView", "CourseOfActionGenerator", "CourseOfActionRepository"]

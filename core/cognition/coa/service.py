from __future__ import annotations
from typing import Any, Sequence
from .contracts import CourseOfActionGenerator, CourseOfActionRepository
from .enums import GenerationDisposition
from .models import AlternativeGenerationPolicy, AlternativeGenerationResult, CourseOfActionTemplate

class ExecutiveAlternativeGenerationService:
    def __init__(self, generator: CourseOfActionGenerator, repository: CourseOfActionRepository) -> None:
        self._generator = generator
        self._repository = repository

    def generate(self, reasoning_result: Any, templates: Sequence[CourseOfActionTemplate], policy: AlternativeGenerationPolicy | None = None) -> AlternativeGenerationResult:
        result = self._generator.generate(reasoning_result, templates, policy)
        if result.disposition is GenerationDisposition.DEFERRED:
            return result
        if self._repository.add(result):
            return result
        return AlternativeGenerationResult(result.generation_id, result.reasoning_id, GenerationDisposition.DUPLICATE, result.courses_of_action, result.diagnostics)

__all__ = ["ExecutiveAlternativeGenerationService"]

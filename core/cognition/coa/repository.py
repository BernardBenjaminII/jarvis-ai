from __future__ import annotations
from threading import RLock
from .models import AlternativeGenerationResult

class InMemoryCourseOfActionRepository:
    def __init__(self) -> None:
        self._lock = RLock()
        self._items: dict[str, AlternativeGenerationResult] = {}

    def add(self, result: AlternativeGenerationResult) -> bool:
        with self._lock:
            if result.generation_id in self._items:
                return False
            self._items[result.generation_id] = result
            return True

    def get(self, generation_id: str) -> AlternativeGenerationResult | None:
        with self._lock:
            return self._items.get(generation_id)

    def list_for_reasoning(self, reasoning_id: str) -> tuple[AlternativeGenerationResult, ...]:
        with self._lock:
            return tuple(sorted((r for r in self._items.values() if r.reasoning_id == reasoning_id), key=lambda r: r.generation_id))

__all__ = ["InMemoryCourseOfActionRepository"]

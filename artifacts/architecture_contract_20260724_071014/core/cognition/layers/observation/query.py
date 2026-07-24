from __future__ import annotations

from .enums import ObservationLifecycleState, ObservationSourceMode
from .models import ObservationRecord
from .registry import ObservationRegistry


class ObservationQuery:
    def __init__(self, registry: ObservationRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        *,
        subject: str | None = None,
        lifecycle_state: ObservationLifecycleState | None = None,
        source_mode: ObservationSourceMode | None = None,
        minimum_confidence: float | None = None,
        text: str | None = None,
    ) -> tuple[ObservationRecord, ...]:
        candidates = (
            self._registry.find_by_subject(subject)
            if subject is not None
            else self._registry.all()
        )

        needle = text.casefold() if text is not None else None
        results = []

        for item in candidates:
            if lifecycle_state is not None and item.lifecycle_state != lifecycle_state:
                continue
            if source_mode is not None and item.source_mode != source_mode:
                continue
            if minimum_confidence is not None and item.confidence < minimum_confidence:
                continue
            if needle is not None and needle not in item.normalized_content.casefold():
                continue
            results.append(item)

        return tuple(results)


__all__ = ("ObservationQuery",)

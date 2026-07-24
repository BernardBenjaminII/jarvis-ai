from __future__ import annotations

from dataclasses import dataclass
import re

from .models import ObservationRecord


@dataclass(frozen=True, slots=True)
class ConflictReport:
    conflict: bool
    rationale: str
    shared_subject: bool


class ObservationConflictDetector:
    """Conservative deterministic conflict detector.

    This detector only declares a conflict when observations share a subject
    and one contains explicit negation of the other's normalized statement.
    Rich semantic contradiction belongs to a later reasoning-backed phase.
    """

    _negation = re.compile(r"\b(no|not|never|none|cannot|can't|didn't|doesn't)\b")

    def compare(
        self,
        first: ObservationRecord,
        second: ObservationRecord,
    ) -> ConflictReport:
        shared_subject = (
            first.subject is not None
            and second.subject is not None
            and first.subject.casefold() == second.subject.casefold()
        )
        if not shared_subject:
            return ConflictReport(False, "subjects do not match", False)

        first_text = first.normalized_content.casefold()
        second_text = second.normalized_content.casefold()
        first_negative = bool(self._negation.search(first_text))
        second_negative = bool(self._negation.search(second_text))

        conflict = first_negative != second_negative
        rationale = (
            "shared subject with opposite explicit polarity"
            if conflict
            else "no deterministic contradiction detected"
        )
        return ConflictReport(conflict, rationale, True)


__all__ = ("ConflictReport", "ObservationConflictDetector")

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from .enums import ObservationLifecycleState
from .errors import ObservationValidationError
from .models import ObservationInput, ObservationRecord, utc_now
from .normalization import ObservationNormalizer
from .validation import ObservationValidator


class ObservationFactory:
    def __init__(
        self,
        validator: ObservationValidator | None = None,
        normalizer: ObservationNormalizer | None = None,
    ) -> None:
        self._validator = validator or ObservationValidator()
        self._normalizer = normalizer or ObservationNormalizer()

    def create(self, candidate: ObservationInput) -> ObservationRecord:
        validation = self._validator.validate(candidate)
        if not validation.valid:
            details = "; ".join(
                f"{issue.code}: {issue.message}" for issue in validation.issues
            )
            raise ObservationValidationError(details)

        return ObservationRecord(
            observation_id=uuid4(),
            content=candidate.content.strip(),
            normalized_content=self._normalizer.normalize(candidate.content),
            source_mode=candidate.source_mode,
            provenance=candidate.provenance,
            confidence=float(candidate.confidence),
            observed_at=candidate.observed_at,
            created_at=utc_now(),
            lifecycle_state=ObservationLifecycleState.VALIDATED,
            authority=candidate.authority,
            subject=candidate.subject,
            attributes=candidate.attributes,
        )


__all__ = ("ObservationFactory",)

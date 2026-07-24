from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .models import (
    ObservationInput,
    ObservationValidationIssue,
    ObservationValidationResult,
)


@dataclass(frozen=True, slots=True)
class ObservationValidationPolicy:
    require_provenance: bool = True
    minimum_content_length: int = 3
    maximum_content_length: int = 100_000
    permit_future_observed_at: bool = False


class ObservationValidator:
    def __init__(
        self,
        policy: ObservationValidationPolicy | None = None,
    ) -> None:
        self._policy = policy or ObservationValidationPolicy()

    @property
    def policy(self) -> ObservationValidationPolicy:
        return self._policy

    def validate(self, candidate: ObservationInput) -> ObservationValidationResult:
        issues: list[ObservationValidationIssue] = []
        content = candidate.content.strip()

        if len(content) < self._policy.minimum_content_length:
            issues.append(
                ObservationValidationIssue(
                    code="content_too_short",
                    message="Observation content is shorter than policy permits.",
                    field_name="content",
                )
            )

        if len(content) > self._policy.maximum_content_length:
            issues.append(
                ObservationValidationIssue(
                    code="content_too_long",
                    message="Observation content exceeds policy maximum.",
                    field_name="content",
                )
            )

        if not 0.0 <= float(candidate.confidence) <= 1.0:
            issues.append(
                ObservationValidationIssue(
                    code="invalid_confidence",
                    message="Confidence must be within [0.0, 1.0].",
                    field_name="confidence",
                )
            )

        if self._policy.require_provenance and not candidate.provenance:
            issues.append(
                ObservationValidationIssue(
                    code="missing_provenance",
                    message="At least one provenance reference is required.",
                    field_name="provenance",
                )
            )

        if candidate.observed_at.tzinfo is None:
            issues.append(
                ObservationValidationIssue(
                    code="naive_timestamp",
                    message="observed_at must be timezone-aware.",
                    field_name="observed_at",
                )
            )
        elif (
            not self._policy.permit_future_observed_at
            and candidate.observed_at.astimezone(timezone.utc)
            > datetime.now(timezone.utc)
        ):
            issues.append(
                ObservationValidationIssue(
                    code="future_timestamp",
                    message="observed_at may not be in the future.",
                    field_name="observed_at",
                )
            )

        return ObservationValidationResult(
            valid=not issues,
            issues=tuple(issues),
        )


__all__ = ("ObservationValidationPolicy", "ObservationValidator")

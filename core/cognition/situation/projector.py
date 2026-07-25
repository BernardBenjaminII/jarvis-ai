"""Deterministic observation-to-situation projection."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping, Sequence

from core.cognition.observation import Observation

from .enums import SituationStatus
from .errors import InvalidSituationError
from .models import (
    SituationRelation,
    SituationSnapshot,
    derive_situation_confidence,
    derive_situation_identity,
    derive_situation_severity,
)


class ExecutiveSituationProjector:
    """Build immutable executive situations from IV-A1 observations."""

    def project(
        self,
        *,
        title: str,
        observations: Sequence[Observation],
        relations: Sequence[SituationRelation] = (),
        summary: str | None = None,
        status: SituationStatus = SituationStatus.OPEN,
        labels: Mapping[str, str] | None = None,
        situation_id: str | None = None,
    ) -> SituationSnapshot:
        """Project one coherent observation set."""

        normalized = tuple(observations)
        if not normalized:
            raise InvalidSituationError(
                "at least one observation is required"
            )

        mission_ids = {
            item.mission_id
            for item in normalized
            if item.mission_id is not None
        }
        correlation_ids = {
            item.correlation_id
            for item in normalized
            if item.correlation_id is not None
        }

        mission_id = next(iter(mission_ids)) if len(mission_ids) == 1 else None
        correlation_id = (
            next(iter(correlation_ids))
            if len(correlation_ids) == 1
            else None
        )

        opened_at = min(item.occurred_at for item in normalized)
        updated_at = max(
            max(item.occurred_at, item.recorded_at)
            for item in normalized
        )

        resolved_id = situation_id or derive_situation_identity(
            title=title,
            observations=normalized,
            relations=relations,
            mission_id=mission_id,
            correlation_id=correlation_id,
        )

        return SituationSnapshot(
            situation_id=resolved_id,
            title=title,
            status=status,
            observations=normalized,
            relations=tuple(relations),
            opened_at=opened_at,
            updated_at=updated_at,
            confidence=derive_situation_confidence(normalized),
            severity=derive_situation_severity(normalized),
            mission_id=mission_id,
            correlation_id=correlation_id,
            summary=summary,
            labels=tuple(sorted((labels or {}).items())),
        )

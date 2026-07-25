"""Application service for Genesis IV-A2 Executive Situation Model."""

from __future__ import annotations

from typing import Mapping, Sequence

from core.cognition.observation import Observation

from .enums import SituationDisposition, SituationStatus
from .models import SituationRelation, SituationSnapshot
from .projector import ExecutiveSituationProjector
from .repository import InMemorySituationRepository


class ExecutiveSituationService:
    """Project and persist executive situations."""

    def __init__(
        self,
        repository: InMemorySituationRepository,
        projector: ExecutiveSituationProjector | None = None,
    ) -> None:
        if not isinstance(repository, InMemorySituationRepository):
            raise TypeError(
                "repository must be InMemorySituationRepository"
            )
        self._repository = repository
        self._projector = projector or ExecutiveSituationProjector()

    @property
    def repository(self) -> InMemorySituationRepository:
        """Return the configured repository."""

        return self._repository

    def create(
        self,
        *,
        title: str,
        observations: Sequence[Observation],
        relations: Sequence[SituationRelation] = (),
        summary: str | None = None,
        status: SituationStatus = SituationStatus.OPEN,
        labels: Mapping[str, str] | None = None,
        situation_id: str | None = None,
    ) -> tuple[SituationSnapshot, SituationDisposition]:
        """Project and persist one executive situation."""

        situation = self._projector.project(
            title=title,
            observations=observations,
            relations=relations,
            summary=summary,
            status=status,
            labels=labels,
            situation_id=situation_id,
        )
        inserted = self._repository.put(situation)
        disposition = (
            SituationDisposition.CREATED
            if inserted
            else SituationDisposition.DUPLICATE
        )
        return situation, disposition

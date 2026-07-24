from __future__ import annotations

from dataclasses import replace
from uuid import UUID

from .conflicts import ConflictReport, ObservationConflictDetector
from .duplicates import DuplicateReport, ObservationDuplicateDetector
from .enums import ObservationLifecycleState, ObservationRelationType
from .factory import ObservationFactory
from .lifecycle import ObservationLifecycleManager
from .merge import MergeResult, ObservationMergeEngine
from .models import ObservationInput, ObservationRecord, ObservationRelation
from .query import ObservationQuery
from .registry import ObservationRegistry
from .relationships import ObservationRelationshipManager


class ObservationDirector:
    """Facade coordinating the certified Observation Engine services."""

    def __init__(
        self,
        *,
        registry: ObservationRegistry | None = None,
        factory: ObservationFactory | None = None,
        lifecycle: ObservationLifecycleManager | None = None,
        duplicate_detector: ObservationDuplicateDetector | None = None,
        conflict_detector: ObservationConflictDetector | None = None,
        merge_engine: ObservationMergeEngine | None = None,
        relationships: ObservationRelationshipManager | None = None,
    ) -> None:
        self.registry = registry or ObservationRegistry()
        self.factory = factory or ObservationFactory()
        self.lifecycle = lifecycle or ObservationLifecycleManager()
        self.duplicate_detector = (
            duplicate_detector or ObservationDuplicateDetector()
        )
        self.conflict_detector = (
            conflict_detector or ObservationConflictDetector()
        )
        self.merge_engine = merge_engine or ObservationMergeEngine(
            self.duplicate_detector
        )
        self.relationships = relationships or ObservationRelationshipManager()
        self.query = ObservationQuery(self.registry)

    def observe(
        self,
        candidate: ObservationInput,
        *,
        activate: bool = True,
    ) -> ObservationRecord:
        record = self.factory.create(candidate)
        if activate:
            record = self.lifecycle.transition(
                record,
                ObservationLifecycleState.ACTIVE,
            )
        return self.registry.register(record)

    def get(self, observation_id: UUID) -> ObservationRecord:
        return self.registry.get(observation_id)

    def transition(
        self,
        observation_id: UUID,
        target: ObservationLifecycleState,
    ) -> ObservationRecord:
        current = self.registry.get(observation_id)
        updated = self.lifecycle.transition(current, target)
        return self.registry.register(updated, replace_existing=True)

    def compare_duplicates(
        self,
        first_id: UUID,
        second_id: UUID,
    ) -> DuplicateReport:
        return self.duplicate_detector.compare(
            self.registry.get(first_id),
            self.registry.get(second_id),
        )

    def compare_conflicts(
        self,
        first_id: UUID,
        second_id: UUID,
    ) -> ConflictReport:
        return self.conflict_detector.compare(
            self.registry.get(first_id),
            self.registry.get(second_id),
        )

    def merge(
        self,
        first_id: UUID,
        second_id: UUID,
    ) -> MergeResult:
        result = self.merge_engine.merge(
            self.registry.get(first_id),
            self.registry.get(second_id),
        )
        self.registry.register(result.merged, replace_existing=True)
        self.relationships.add(
            ObservationRelation(
                source_id=result.merged.observation_id,
                target_id=(
                    second_id if result.merged.observation_id == first_id else first_id
                ),
                relation_type=ObservationRelationType.DUPLICATES,
                confidence=1.0,
                rationale=result.rationale,
            )
        )
        return result

    def supersede(
        self,
        old_id: UUID,
        replacement: ObservationInput,
    ) -> ObservationRecord:
        old = self.registry.get(old_id)
        new = self.observe(replacement, activate=True)
        new = replace(new, supersedes_id=old_id)
        self.registry.register(new, replace_existing=True)
        self.transition(old_id, ObservationLifecycleState.SUPERSEDED)
        self.relationships.add(
            ObservationRelation(
                source_id=new.observation_id,
                target_id=old_id,
                relation_type=ObservationRelationType.SUPERSEDES,
                confidence=1.0,
            )
        )
        return new


__all__ = ("ObservationDirector",)

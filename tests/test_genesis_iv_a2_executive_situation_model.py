"""Tests for Genesis IV-A2 Executive Situation Model."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from core.cognition.observation import (
    Observation,
    ObservationKind,
    ObservationProvenance,
    ObservationSeverity,
    SourceAuthority,
)
from core.cognition.situation import (
    ExecutiveSituationProjector,
    ExecutiveSituationService,
    InMemorySituationRepository,
    InvalidSituationError,
    SituationDisposition,
    SituationQuery,
    SituationRelation,
    SituationRelationType,
    SituationStatus,
)


BASE = datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc)


def observation(
    *,
    observation_type: str,
    value: object,
    offset_minutes: int,
    confidence: float,
    severity: ObservationSeverity,
) -> Observation:
    provenance = ObservationProvenance.create(
        producer="iv-a2-test",
        source="fixture",
        authority=SourceAuthority.CONSTITUTIONAL,
    )
    return Observation.create(
        observation_type=observation_type,
        kind=ObservationKind.STATE,
        value=value,
        provenance=provenance,
        occurred_at=BASE + timedelta(minutes=offset_minutes),
        recorded_at=BASE + timedelta(minutes=offset_minutes, seconds=10),
        confidence=confidence,
        severity=severity,
        mission_id="mission-a2",
        correlation_id="cycle-a2",
    )


class Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.first = observation(
            observation_type="runtime.health",
            value={"state": "degraded"},
            offset_minutes=0,
            confidence=0.8,
            severity=ObservationSeverity.WARNING,
        )
        self.second = observation(
            observation_type="knowledge.coverage",
            value={"coverage": 0.61},
            offset_minutes=2,
            confidence=1.0,
            severity=ObservationSeverity.ERROR,
        )

    def test_deterministic_situation_identity(self) -> None:
        projector = ExecutiveSituationProjector()
        first = projector.project(
            title="Executive degradation",
            observations=(self.first, self.second),
        )
        second = projector.project(
            title="Executive degradation",
            observations=(self.second, self.first),
        )

        self.assertEqual(first.situation_id, second.situation_id)
        self.assertEqual(first.observation_ids, second.observation_ids)

    def test_derived_confidence_and_severity(self) -> None:
        situation = ExecutiveSituationProjector().project(
            title="Executive degradation",
            observations=(self.first, self.second),
        )

        self.assertAlmostEqual(situation.confidence, 0.9)
        self.assertEqual(situation.severity, ObservationSeverity.ERROR)
        self.assertEqual(situation.mission_id, "mission-a2")
        self.assertEqual(situation.correlation_id, "cycle-a2")

    def test_explicit_observation_relation(self) -> None:
        relation = SituationRelation(
            source_observation_id=self.first.observation_id,
            target_observation_id=self.second.observation_id,
            relation_type=SituationRelationType.CORRELATED,
            confidence=0.95,
            rationale="Both occurred in the same cognitive cycle.",
        )
        situation = ExecutiveSituationProjector().project(
            title="Correlated condition",
            observations=(self.first, self.second),
            relations=(relation,),
        )

        self.assertEqual(len(situation.relations), 1)
        self.assertEqual(
            situation.relations[0].relation_type,
            SituationRelationType.CORRELATED,
        )

    def test_empty_projection_rejected(self) -> None:
        with self.assertRaises(InvalidSituationError):
            ExecutiveSituationProjector().project(
                title="Empty",
                observations=(),
            )

    def test_repository_query(self) -> None:
        repository = InMemorySituationRepository()
        service = ExecutiveSituationService(repository)

        situation, disposition = service.create(
            title="Executive degradation",
            observations=(self.first, self.second),
            status=SituationStatus.ESCALATING,
        )

        duplicate, duplicate_disposition = service.create(
            title="Executive degradation",
            observations=(self.first, self.second),
            status=SituationStatus.ESCALATING,
        )

        results = repository.query(
            SituationQuery(
                mission_id="mission-a2",
                minimum_severity=ObservationSeverity.WARNING,
            )
        )

        self.assertEqual(disposition, SituationDisposition.CREATED)
        self.assertEqual(
            duplicate_disposition,
            SituationDisposition.DUPLICATE,
        )
        self.assertEqual(situation.situation_id, duplicate.situation_id)
        self.assertEqual(results, (situation,))


if __name__ == "__main__":
    unittest.main()

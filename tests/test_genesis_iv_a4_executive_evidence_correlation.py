"""Tests for Genesis IV-A4 Executive Evidence Correlation Engine."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from core.cognition.evidence_correlation import (
    AssessmentDisposition,
    AssessmentQuery,
    AssessmentStatus,
    EvidenceLink,
    EvidencePolarity,
    EvidenceStrength,
    ExecutiveEvidenceCorrelator,
    ExecutiveEvidenceService,
    InMemoryAssessmentRepository,
    InvalidAssessmentError,
)
from core.cognition.hypothesis import (
    ExecutiveHypothesisGenerator,
    HypothesisKind,
    HypothesisProposal,
)
from core.cognition.observation import (
    Observation,
    ObservationKind,
    ObservationProvenance,
    ObservationSeverity,
    SourceAuthority,
)
from core.cognition.situation import ExecutiveSituationProjector


BASE = datetime(2026, 7, 24, 18, 0, tzinfo=timezone.utc)


def make_observation(
    *,
    observation_type: str,
    value: object,
    offset: int,
) -> Observation:
    provenance = ObservationProvenance.create(
        producer="iv-a4-test",
        source="fixture",
        authority=SourceAuthority.CONSTITUTIONAL,
    )
    return Observation.create(
        observation_type=observation_type,
        kind=ObservationKind.STATE,
        value=value,
        provenance=provenance,
        occurred_at=BASE + timedelta(minutes=offset),
        recorded_at=BASE + timedelta(minutes=offset, seconds=5),
        confidence=0.9,
        severity=ObservationSeverity.WARNING,
        mission_id="mission-a4",
        correlation_id="cycle-a4",
    )


class Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.latency = make_observation(
            observation_type="runtime.latency",
            value={"milliseconds": 950},
            offset=0,
        )
        self.loss = make_observation(
            observation_type="network.loss",
            value={"percent": 25},
            offset=1,
        )
        self.situation = ExecutiveSituationProjector().project(
            title="Degraded connectivity",
            observations=(self.latency, self.loss),
        )
        proposal = HypothesisProposal(
            statement="Network instability is causing runtime latency.",
            kind=HypothesisKind.CAUSAL,
            confidence=0.8,
            supporting_observation_ids=(
                self.latency.observation_id,
                self.loss.observation_id,
            ),
        )
        self.hypothesis = ExecutiveHypothesisGenerator().generate(
            situation=self.situation,
            proposals=(proposal,),
        )[0]

    def link(
        self,
        observation_id: str,
        polarity: EvidencePolarity,
        strength: EvidenceStrength,
        reliability: float,
        admissible: bool = True,
    ) -> EvidenceLink:
        return EvidenceLink(
            observation_id=observation_id,
            hypothesis_id=self.hypothesis.hypothesis_id,
            polarity=polarity,
            strength=strength,
            reliability=reliability,
            admissible=admissible,
        )

    def test_deterministic_assessment_identity(self) -> None:
        links = (
            self.link(
                self.latency.observation_id,
                EvidencePolarity.SUPPORTS,
                EvidenceStrength.MODERATE,
                0.9,
            ),
            self.link(
                self.loss.observation_id,
                EvidencePolarity.SUPPORTS,
                EvidenceStrength.STRONG,
                1.0,
            ),
        )

        correlator = ExecutiveEvidenceCorrelator()
        first = correlator.assess(
            situation=self.situation,
            hypothesis=self.hypothesis,
            links=links,
        )
        second = correlator.assess(
            situation=self.situation,
            hypothesis=self.hypothesis,
            links=tuple(reversed(links)),
        )

        self.assertEqual(first.assessment_id, second.assessment_id)
        self.assertEqual(first.coverage, 1.0)
        self.assertEqual(first.status, AssessmentStatus.COMPLETE)

    def test_support_and_contradiction_are_separate(self) -> None:
        links = (
            self.link(
                self.latency.observation_id,
                EvidencePolarity.SUPPORTS,
                EvidenceStrength.STRONG,
                1.0,
            ),
            self.link(
                self.loss.observation_id,
                EvidencePolarity.CONTRADICTS,
                EvidenceStrength.WEAK,
                0.8,
            ),
        )

        assessment = ExecutiveEvidenceCorrelator().assess(
            situation=self.situation,
            hypothesis=self.hypothesis,
            links=links,
        )

        self.assertGreater(assessment.support_score, 0.0)
        self.assertGreater(assessment.contradiction_score, 0.0)
        self.assertEqual(assessment.status, AssessmentStatus.CONTESTED)

    def test_inadmissible_evidence_does_not_score(self) -> None:
        links = (
            self.link(
                self.latency.observation_id,
                EvidencePolarity.SUPPORTS,
                EvidenceStrength.DECISIVE,
                1.0,
                admissible=False,
            ),
        )

        assessment = ExecutiveEvidenceCorrelator().assess(
            situation=self.situation,
            hypothesis=self.hypothesis,
            links=links,
        )

        self.assertEqual(assessment.support_score, 0.0)
        self.assertEqual(assessment.coverage, 0.0)
        self.assertEqual(assessment.confidence, 0.0)

    def test_foreign_observation_rejected(self) -> None:
        link = self.link(
            "obs_foreign",
            EvidencePolarity.SUPPORTS,
            EvidenceStrength.STRONG,
            1.0,
        )

        with self.assertRaises(InvalidAssessmentError):
            ExecutiveEvidenceCorrelator().assess(
                situation=self.situation,
                hypothesis=self.hypothesis,
                links=(link,),
            )

    def test_repository_query_and_idempotency(self) -> None:
        repository = InMemoryAssessmentRepository()
        service = ExecutiveEvidenceService(repository)
        links = (
            self.link(
                self.latency.observation_id,
                EvidencePolarity.SUPPORTS,
                EvidenceStrength.MODERATE,
                0.9,
            ),
            self.link(
                self.loss.observation_id,
                EvidencePolarity.SUPPORTS,
                EvidenceStrength.STRONG,
                1.0,
            ),
        )

        first = service.assess(
            situation=self.situation,
            hypothesis=self.hypothesis,
            links=links,
        )
        second = service.assess(
            situation=self.situation,
            hypothesis=self.hypothesis,
            links=links,
        )
        results = repository.query(
            AssessmentQuery(
                situation_id=self.situation.situation_id,
                minimum_coverage=1.0,
                strongest_first=True,
            )
        )

        self.assertEqual(first[1], AssessmentDisposition.CREATED)
        self.assertEqual(second[1], AssessmentDisposition.DUPLICATE)
        self.assertEqual(repository.count(), 1)
        self.assertEqual(results, (first[0],))


if __name__ == "__main__":
    unittest.main()

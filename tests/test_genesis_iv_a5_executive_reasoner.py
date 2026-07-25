"""Tests for Genesis IV-A5 Executive Reasoner."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from core.cognition.evidence_correlation import (
    EvidenceLink,
    EvidencePolarity,
    EvidenceStrength,
    ExecutiveEvidenceCorrelator,
)
from core.cognition.hypothesis import (
    ExecutiveHypothesisGenerator,
    HypothesisProposal,
)
from core.cognition.observation import (
    Observation,
    ObservationKind,
    ObservationProvenance,
    ObservationSeverity,
    SourceAuthority,
)
from core.cognition.reasoner import (
    DeterministicExecutiveReasoner,
    ExecutiveReasoningService,
    InMemoryReasoningRepository,
    ReasoningDisposition,
    ReasoningPolicy,
    ReasoningQuery,
    ReasoningRepositoryDisposition,
)
from core.cognition.situation import ExecutiveSituationProjector


BASE = datetime(2026, 7, 24, 20, 0, tzinfo=timezone.utc)


def make_observation(name: str, value: object, offset: int) -> Observation:
    provenance = ObservationProvenance.create(
        producer="iv-a5-test",
        source="fixture",
        authority=SourceAuthority.CONSTITUTIONAL,
    )
    return Observation.create(
        observation_type=name,
        kind=ObservationKind.STATE,
        value=value,
        provenance=provenance,
        occurred_at=BASE + timedelta(minutes=offset),
        recorded_at=BASE + timedelta(minutes=offset, seconds=5),
        confidence=0.9,
        severity=ObservationSeverity.WARNING,
        mission_id="mission-a5",
        correlation_id="cycle-a5",
    )


class Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.latency = make_observation(
            "runtime.latency",
            {"milliseconds": 950},
            0,
        )
        self.loss = make_observation(
            "network.loss",
            {"percent": 25},
            1,
        )
        self.cpu = make_observation(
            "runtime.cpu",
            {"percent": 45},
            2,
        )
        self.situation = ExecutiveSituationProjector().project(
            title="Degraded connectivity",
            observations=(self.latency, self.loss, self.cpu),
        )

        proposals = (
            HypothesisProposal(
                statement="Network instability is the primary cause.",
                confidence=0.85,
                supporting_observation_ids=(
                    self.latency.observation_id,
                    self.loss.observation_id,
                ),
            ),
            HypothesisProposal(
                statement="Host saturation is the primary cause.",
                confidence=0.65,
                supporting_observation_ids=(self.latency.observation_id,),
                contradicting_observation_ids=(self.cpu.observation_id,),
            ),
        )
        self.hypotheses = ExecutiveHypothesisGenerator().generate(
            situation=self.situation,
            proposals=proposals,
        )

    def assessment_for(
        self,
        hypothesis_index: int,
        links: tuple[EvidenceLink, ...],
        questions: tuple[str, ...] = (),
    ):
        return ExecutiveEvidenceCorrelator().assess(
            situation=self.situation,
            hypothesis=self.hypotheses[hypothesis_index],
            links=links,
            missing_evidence_questions=questions,
        )

    def test_selects_strongly_supported_hypothesis(self) -> None:
        first, second = self.hypotheses
        first_assessment = self.assessment_for(
            0,
            (
                EvidenceLink(
                    self.latency.observation_id,
                    first.hypothesis_id,
                    EvidencePolarity.SUPPORTS,
                    EvidenceStrength.STRONG,
                    1.0,
                ),
                EvidenceLink(
                    self.loss.observation_id,
                    first.hypothesis_id,
                    EvidencePolarity.SUPPORTS,
                    EvidenceStrength.DECISIVE,
                    1.0,
                ),
                EvidenceLink(
                    self.cpu.observation_id,
                    first.hypothesis_id,
                    EvidencePolarity.NEUTRAL,
                    EvidenceStrength.TRACE,
                    1.0,
                ),
            ),
        )
        second_assessment = self.assessment_for(
            1,
            (
                EvidenceLink(
                    self.latency.observation_id,
                    second.hypothesis_id,
                    EvidencePolarity.SUPPORTS,
                    EvidenceStrength.MODERATE,
                    0.8,
                ),
                EvidenceLink(
                    self.loss.observation_id,
                    second.hypothesis_id,
                    EvidencePolarity.NEUTRAL,
                    EvidenceStrength.TRACE,
                    1.0,
                ),
                EvidenceLink(
                    self.cpu.observation_id,
                    second.hypothesis_id,
                    EvidencePolarity.CONTRADICTS,
                    EvidenceStrength.STRONG,
                    1.0,
                ),
            ),
        )

        result = DeterministicExecutiveReasoner().reason(
            situation=self.situation,
            hypotheses=self.hypotheses,
            assessments=(first_assessment, second_assessment),
        )

        self.assertEqual(result.disposition, ReasoningDisposition.SELECTED)
        self.assertEqual(
            result.selected_hypothesis_id,
            first.hypothesis_id,
        )
        self.assertEqual(result.rankings[0].hypothesis_id, first.hypothesis_id)

    def test_close_result_is_contested(self) -> None:
        first, second = self.hypotheses
        assessments = (
            self.assessment_for(
                0,
                (
                    EvidenceLink(
                        self.latency.observation_id,
                        first.hypothesis_id,
                        EvidencePolarity.SUPPORTS,
                        EvidenceStrength.MODERATE,
                        0.9,
                    ),
                    EvidenceLink(
                        self.loss.observation_id,
                        first.hypothesis_id,
                        EvidencePolarity.SUPPORTS,
                        EvidenceStrength.MODERATE,
                        0.9,
                    ),
                ),
            ),
            self.assessment_for(
                1,
                (
                    EvidenceLink(
                        self.latency.observation_id,
                        second.hypothesis_id,
                        EvidencePolarity.SUPPORTS,
                        EvidenceStrength.MODERATE,
                        0.9,
                    ),
                    EvidenceLink(
                        self.cpu.observation_id,
                        second.hypothesis_id,
                        EvidencePolarity.SUPPORTS,
                        EvidenceStrength.MODERATE,
                        0.9,
                    ),
                ),
            ),
        )

        result = DeterministicExecutiveReasoner().reason(
            situation=self.situation,
            hypotheses=self.hypotheses,
            assessments=assessments,
            policy=ReasoningPolicy(
                minimum_selection_score=0.05,
                minimum_confidence=0.05,
                minimum_coverage=0.50,
                minimum_margin=0.20,
            ),
        )

        self.assertEqual(result.disposition, ReasoningDisposition.CONTESTED)
        self.assertIsNone(result.selected_hypothesis_id)

    def test_low_coverage_defers_judgment(self) -> None:
        first, second = self.hypotheses
        assessments = (
            self.assessment_for(
                0,
                (
                    EvidenceLink(
                        self.latency.observation_id,
                        first.hypothesis_id,
                        EvidencePolarity.SUPPORTS,
                        EvidenceStrength.STRONG,
                        1.0,
                    ),
                ),
                ("Measure packet loss independently.",),
            ),
            self.assessment_for(
                1,
                (
                    EvidenceLink(
                        self.cpu.observation_id,
                        second.hypothesis_id,
                        EvidencePolarity.CONTRADICTS,
                        EvidenceStrength.STRONG,
                        1.0,
                    ),
                ),
            ),
        )

        result = DeterministicExecutiveReasoner().reason(
            situation=self.situation,
            hypotheses=self.hypotheses,
            assessments=assessments,
        )

        self.assertEqual(result.disposition, ReasoningDisposition.DEFERRED)
        self.assertIn(
            "Measure packet loss independently.",
            result.evidence_requests,
        )

    def test_reasoning_identity_is_deterministic(self) -> None:
        first, second = self.hypotheses
        assessments = (
            self.assessment_for(
                0,
                (
                    EvidenceLink(
                        self.loss.observation_id,
                        first.hypothesis_id,
                        EvidencePolarity.SUPPORTS,
                        EvidenceStrength.STRONG,
                        1.0,
                    ),
                ),
            ),
            self.assessment_for(
                1,
                (
                    EvidenceLink(
                        self.cpu.observation_id,
                        second.hypothesis_id,
                        EvidencePolarity.CONTRADICTS,
                        EvidenceStrength.STRONG,
                        1.0,
                    ),
                ),
            ),
        )
        reasoner = DeterministicExecutiveReasoner()
        first_result = reasoner.reason(
            situation=self.situation,
            hypotheses=self.hypotheses,
            assessments=assessments,
        )
        second_result = reasoner.reason(
            situation=self.situation,
            hypotheses=tuple(reversed(self.hypotheses)),
            assessments=tuple(reversed(assessments)),
        )
        self.assertEqual(
            first_result.reasoning_id,
            second_result.reasoning_id,
        )

    def test_repository_query_and_idempotency(self) -> None:
        first, second = self.hypotheses
        assessments = (
            self.assessment_for(
                0,
                (
                    EvidenceLink(
                        self.latency.observation_id,
                        first.hypothesis_id,
                        EvidencePolarity.SUPPORTS,
                        EvidenceStrength.STRONG,
                        1.0,
                    ),
                    EvidenceLink(
                        self.loss.observation_id,
                        first.hypothesis_id,
                        EvidencePolarity.SUPPORTS,
                        EvidenceStrength.STRONG,
                        1.0,
                    ),
                ),
            ),
            self.assessment_for(
                1,
                (
                    EvidenceLink(
                        self.cpu.observation_id,
                        second.hypothesis_id,
                        EvidencePolarity.CONTRADICTS,
                        EvidenceStrength.STRONG,
                        1.0,
                    ),
                ),
            ),
        )

        repository = InMemoryReasoningRepository()
        service = ExecutiveReasoningService(repository)

        first_result = service.reason(
            situation=self.situation,
            hypotheses=self.hypotheses,
            assessments=assessments,
        )
        second_result = service.reason(
            situation=self.situation,
            hypotheses=self.hypotheses,
            assessments=assessments,
        )

        queried = repository.query(
            ReasoningQuery(
                situation_id=self.situation.situation_id,
                strongest_first=True,
            )
        )

        self.assertEqual(
            first_result[1],
            ReasoningRepositoryDisposition.CREATED,
        )
        self.assertEqual(
            second_result[1],
            ReasoningRepositoryDisposition.DUPLICATE,
        )
        self.assertEqual(repository.count(), 1)
        self.assertEqual(queried, (first_result[0],))


if __name__ == "__main__":
    unittest.main()

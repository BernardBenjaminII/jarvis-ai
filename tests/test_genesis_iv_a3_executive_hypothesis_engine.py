"""Tests for Genesis IV-A3 Executive Hypothesis Engine."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from core.cognition.hypothesis import (
    ExecutiveHypothesisGenerator,
    ExecutiveHypothesisService,
    HypothesisDisposition,
    HypothesisKind,
    HypothesisProposal,
    HypothesisQuery,
    HypothesisStatus,
    InMemoryHypothesisRepository,
    InvalidHypothesisError,
)
from core.cognition.observation import (
    Observation,
    ObservationKind,
    ObservationProvenance,
    ObservationSeverity,
    SourceAuthority,
)
from core.cognition.situation import ExecutiveSituationProjector


BASE = datetime(2026, 7, 24, 15, 0, tzinfo=timezone.utc)


def make_observation(
    *,
    observation_type: str,
    value: object,
    offset: int,
) -> Observation:
    provenance = ObservationProvenance.create(
        producer="iv-a3-test",
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
        mission_id="mission-a3",
        correlation_id="cycle-a3",
    )


class Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.first = make_observation(
            observation_type="runtime.latency",
            value={"milliseconds": 950},
            offset=0,
        )
        self.second = make_observation(
            observation_type="network.loss",
            value={"percent": 25},
            offset=1,
        )
        self.situation = ExecutiveSituationProjector().project(
            title="Degraded connectivity",
            observations=(self.first, self.second),
        )

    def test_deterministic_hypothesis_identity(self) -> None:
        proposal = HypothesisProposal(
            statement="Network instability is causing runtime latency.",
            kind=HypothesisKind.CAUSAL,
            confidence=0.72,
            supporting_observation_ids=(
                self.first.observation_id,
                self.second.observation_id,
            ),
        )

        generator = ExecutiveHypothesisGenerator()
        first = generator.generate(
            situation=self.situation,
            proposals=(proposal,),
        )[0]
        second = generator.generate(
            situation=self.situation,
            proposals=(proposal,),
        )[0]

        self.assertEqual(first.hypothesis_id, second.hypothesis_id)
        self.assertEqual(first.status, HypothesisStatus.PROPOSED)

    def test_competing_hypotheses_are_preserved(self) -> None:
        proposals = (
            HypothesisProposal(
                statement="The local network is unstable.",
                confidence=0.75,
                supporting_observation_ids=(
                    self.second.observation_id,
                ),
            ),
            HypothesisProposal(
                statement="The runtime host is overloaded.",
                confidence=0.55,
                supporting_observation_ids=(
                    self.first.observation_id,
                ),
                unresolved_questions=(
                    "What is the current CPU saturation?",
                ),
            ),
        )

        hypotheses = ExecutiveHypothesisGenerator().generate(
            situation=self.situation,
            proposals=proposals,
        )

        self.assertEqual(len(hypotheses), 2)
        self.assertNotEqual(
            hypotheses[0].hypothesis_id,
            hypotheses[1].hypothesis_id,
        )

    def test_unknown_observation_reference_rejected(self) -> None:
        proposal = HypothesisProposal(
            statement="Unknown input explains the situation.",
            supporting_observation_ids=("obs_missing",),
        )

        with self.assertRaises(InvalidHypothesisError):
            ExecutiveHypothesisGenerator().generate(
                situation=self.situation,
                proposals=(proposal,),
            )

    def test_repository_query_strongest_first(self) -> None:
        repository = InMemoryHypothesisRepository()
        service = ExecutiveHypothesisService(repository)

        proposals = (
            HypothesisProposal(
                statement="Network instability is primary.",
                confidence=0.85,
                supporting_observation_ids=(
                    self.second.observation_id,
                ),
            ),
            HypothesisProposal(
                statement="Host saturation is primary.",
                confidence=0.60,
                supporting_observation_ids=(
                    self.first.observation_id,
                ),
            ),
        )

        results = service.propose(
            situation=self.situation,
            proposals=proposals,
        )

        queried = repository.query(
            HypothesisQuery(
                situation_id=self.situation.situation_id,
                minimum_confidence=0.5,
                strongest_first=True,
            )
        )

        self.assertEqual(repository.count(), 2)
        self.assertEqual(queried[0].confidence, 0.85)
        self.assertTrue(
            all(
                disposition is HypothesisDisposition.CREATED
                for _, disposition in results
            )
        )

    def test_duplicate_proposal_is_idempotent(self) -> None:
        repository = InMemoryHypothesisRepository()
        service = ExecutiveHypothesisService(repository)
        proposal = HypothesisProposal(
            statement="Network instability is primary.",
            confidence=0.85,
            supporting_observation_ids=(
                self.second.observation_id,
            ),
        )

        first = service.propose(
            situation=self.situation,
            proposals=(proposal,),
        )[0]
        second = service.propose(
            situation=self.situation,
            proposals=(proposal,),
        )[0]

        self.assertEqual(first[0].hypothesis_id, second[0].hypothesis_id)
        self.assertEqual(first[1], HypothesisDisposition.CREATED)
        self.assertEqual(second[1], HypothesisDisposition.DUPLICATE)
        self.assertEqual(repository.count(), 1)


if __name__ == "__main__":
    unittest.main()

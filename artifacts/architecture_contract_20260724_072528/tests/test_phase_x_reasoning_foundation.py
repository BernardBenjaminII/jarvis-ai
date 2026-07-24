"""Tests for the JARVIS Phase X Reasoning Engine foundation."""

from __future__ import annotations

import unittest

from core.reasoning import (
    DuplicateReasoningElementError,
    EvidenceItem,
    EvidenceKind,
    EvidenceStance,
    Hypothesis,
    HypothesisDisposition,
    ReasoningEngine,
    ReasoningRequest,
    ReasoningStatus,
    UnknownEvidenceReferenceError,
)


def build_request() -> ReasoningRequest:
    evidence = (
        EvidenceItem(
            evidence_id="evidence_tests",
            proposition="All verification suites pass",
            stance=EvidenceStance.SUPPORTS,
            source_ref="dev/verify_all.sh",
            kind=EvidenceKind.MEASUREMENT,
            reliability=1.0,
            confidence=0.95,
        ),
        EvidenceItem(
            evidence_id="evidence_architecture",
            proposition="The architecture boundaries are explicit",
            stance=EvidenceStance.SUPPORTS,
            source_ref="docs/architecture",
            kind=EvidenceKind.DOCUMENT,
            reliability=0.9,
            confidence=0.9,
        ),
        EvidenceItem(
            evidence_id="evidence_gap",
            proposition="The reasoning layer is not yet implemented",
            stance=EvidenceStance.CONTRADICTS,
            source_ref="architecture audit",
            kind=EvidenceKind.OBSERVATION,
            reliability=1.0,
            confidence=0.8,
        ),
    )

    hypotheses = (
        Hypothesis(
            hypothesis_id="hypothesis_build_foundation",
            statement=(
                "JARVIS is ready for an additive deterministic "
                "reasoning foundation"
            ),
            supporting_evidence_ids=(
                "evidence_tests",
                "evidence_architecture",
            ),
            assumptions=(
                "Existing public executive interfaces remain stable",
            ),
            proposed_actions=(
                "Create immutable reasoning contracts",
                "Implement deterministic hypothesis assessment",
                "Emit a planning recommendation",
            ),
        ),
        Hypothesis(
            hypothesis_id="hypothesis_do_nothing",
            statement="No reasoning work is required",
            contradicting_evidence_ids=("evidence_gap",),
        ),
    )

    return ReasoningRequest(
        request_id="phase_x_fixture",
        goal="Establish the JARVIS Reasoning Engine foundation",
        evidence=evidence,
        hypotheses=hypotheses,
        constraints=(
            "Do not execute tools",
            "Do not mutate planning or runtime missions",
        ),
        context={"phase": "X"},
    )


class ReasoningFoundationTests(unittest.TestCase):
    def test_selects_best_supported_hypothesis(self) -> None:
        result = ReasoningEngine().reason(build_request())

        self.assertEqual(result.status, ReasoningStatus.COMPLETED)
        self.assertEqual(
            result.selected_hypothesis_id,
            "hypothesis_build_foundation",
        )
        self.assertIsNotNone(result.planning_recommendation)

    def test_rejects_contradicted_hypothesis(self) -> None:
        result = ReasoningEngine().reason(build_request())
        by_id = {
            item.hypothesis_id: item
            for item in result.assessments
        }

        self.assertEqual(
            by_id["hypothesis_do_nothing"].disposition,
            HypothesisDisposition.REJECTED,
        )

    def test_preserves_constraints_for_planning(self) -> None:
        request = build_request()
        result = ReasoningEngine().reason(request)

        assert result.planning_recommendation is not None
        self.assertEqual(
            result.planning_recommendation.constraints,
            request.constraints,
        )

    def test_records_unresolved_assumptions(self) -> None:
        result = ReasoningEngine().reason(build_request())

        self.assertIn(
            (
                "Validation of assumption: Existing public executive "
                "interfaces remain stable"
            ),
            result.missing_information,
        )

    def test_produces_deterministic_fingerprint(self) -> None:
        request = build_request()
        engine = ReasoningEngine()

        first = engine.reason(request)
        second = engine.reason(request)

        self.assertEqual(first.fingerprint, second.fingerprint)
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_trace_is_complete_and_ordered(self) -> None:
        result = ReasoningEngine().reason(build_request())

        self.assertEqual(
            [step.sequence for step in result.trace],
            list(range(1, len(result.trace) + 1)),
        )
        self.assertEqual(
            result.trace[0].operation,
            "validate_request",
        )
        self.assertEqual(
            result.trace[-1].operation,
            "select_conclusion",
        )

    def test_rejects_unknown_evidence_reference(self) -> None:
        request = ReasoningRequest(
            request_id="unknown_evidence",
            goal="Test validation",
            evidence=(),
            hypotheses=(
                Hypothesis(
                    hypothesis_id="hypothesis",
                    statement="Unknown evidence should fail",
                    supporting_evidence_ids=("missing",),
                ),
            ),
        )

        with self.assertRaises(UnknownEvidenceReferenceError):
            ReasoningEngine().reason(request)

    def test_rejects_duplicate_identifiers(self) -> None:
        duplicate = EvidenceItem(
            evidence_id="duplicate",
            proposition="A proposition",
            stance=EvidenceStance.SUPPORTS,
            source_ref="fixture",
        )
        request = ReasoningRequest(
            request_id="duplicates",
            goal="Test duplicate validation",
            evidence=(duplicate, duplicate),
            hypotheses=(
                Hypothesis(
                    hypothesis_id="hypothesis",
                    statement="Duplicates should fail",
                    supporting_evidence_ids=("duplicate",),
                ),
            ),
        )

        with self.assertRaises(DuplicateReasoningElementError):
            ReasoningEngine().reason(request)


if __name__ == "__main__":
    unittest.main()

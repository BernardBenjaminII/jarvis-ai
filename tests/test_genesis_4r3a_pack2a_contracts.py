from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from core.evidence import (
    AdmissibilityDecision,
    AdmissibilityReason,
    AdmissibilityStatus,
    AssessmentMethod,
    EvidenceAssessment,
    EvidenceDirection,
    EvidenceGap,
    EvidenceGapType,
    EvidenceRecord,
    EvidenceRelationship,
    EvidenceRelationshipType,
    EvidenceSet,
    EvidenceStatus,
    EvidenceSufficiencyStatus,
    IntegrityStatus,
    Proposition,
    PropositionModality,
    PropositionStatus,
    SourceReliabilityClass,
    WeightBreakdown,
)
from core.evidence.errors import EvidenceValidationError, PropositionValidationError


FIXED_TIME = datetime(2026, 7, 21, 12, 0, 0, tzinfo=timezone.utc)


class EvidenceContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.proposition = Proposition(
            proposition_id="prop-001",
            statement="Pump HP-02 produced pressure below threshold.",
            subject="Pump HP-02",
            predicate="produced pressure below threshold",
            status=PropositionStatus.ACTIVE,
            modality=PropositionModality.ASSERTION,
            context={"mission": {"id": "mission-001", "tags": ["pressure", "safety"]}},
            created_at=FIXED_TIME,
        )
        self.weight = WeightBreakdown(
            reliability=0.9,
            relevance=0.95,
            directness=0.9,
            integrity=1.0,
            freshness=0.8,
            independence=0.85,
            final_weight=0.88,
            formula_version="r3a-test-1",
            rationale="Deterministic fixture.",
        )
        self.record = EvidenceRecord(
            evidence_id="ev-001",
            proposition_id="prop-001",
            observation_id="obs-001",
            assessment_id="assess-001",
            source_id="sensor-a",
            direction=EvidenceDirection.SUPPORTS,
            status=EvidenceStatus.ACTIVE,
            weight=self.weight,
            rationale="Pressure reading supports proposition.",
            provenance={
                "source": "sensor-a",
                "capture": {"sequence": 7, "channels": ["pressure", "temperature"]},
            },
            transformation_chain=(
                {"operation": "unit-normalization", "from": "psi", "to": "kpa"},
            ),
            created_at=FIXED_TIME,
        )

    def test_contracts_are_immutable(self) -> None:
        with self.assertRaises(FrozenInstanceError):
            self.proposition.statement = "changed"  # type: ignore[misc]

    def test_nested_mappings_and_lists_are_immutable(self) -> None:
        with self.assertRaises(TypeError):
            self.record.provenance["source"] = "sensor-b"  # type: ignore[index]

        capture = self.record.provenance["capture"]
        with self.assertRaises(TypeError):
            capture["sequence"] = 8  # type: ignore[index]

        self.assertIsInstance(capture["channels"], tuple)  # type: ignore[index]

    def test_weight_rejects_out_of_range_score(self) -> None:
        with self.assertRaises(EvidenceValidationError):
            WeightBreakdown(
                reliability=1.1,
                relevance=1.0,
                directness=1.0,
                integrity=1.0,
                freshness=1.0,
                independence=1.0,
                final_weight=1.0,
                formula_version="x",
                rationale="x",
            )

    def test_weight_rejects_boolean_score(self) -> None:
        with self.assertRaises(EvidenceValidationError):
            WeightBreakdown(
                reliability=True,
                relevance=1.0,
                directness=1.0,
                integrity=1.0,
                freshness=1.0,
                independence=1.0,
                final_weight=1.0,
                formula_version="x",
                rationale="x",
            )

    def test_relationship_rejects_self_reference(self) -> None:
        with self.assertRaises(EvidenceValidationError):
            EvidenceRelationship(
                relationship_id="rel-001",
                left_evidence_id="ev-001",
                right_evidence_id="ev-001",
                relationship_type=EvidenceRelationshipType.DUPLICATES,
                rationale="Invalid self relationship.",
                confidence=1.0,
                method=AssessmentMethod.DETERMINISTIC_RULE,
                created_at=FIXED_TIME,
            )

    def test_evidence_set_rejects_mismatched_proposition(self) -> None:
        foreign = EvidenceRecord(
            evidence_id="ev-foreign",
            proposition_id="prop-999",
            observation_id="obs-999",
            assessment_id="assess-999",
            source_id="source-x",
            direction=EvidenceDirection.SUPPORTS,
            status=EvidenceStatus.ACTIVE,
            weight=self.weight,
            rationale="Foreign record.",
            provenance={"source": "source-x"},
            created_at=FIXED_TIME,
        )
        with self.assertRaises(PropositionValidationError):
            EvidenceSet(
                evidence_set_id="set-001",
                proposition=self.proposition,
                supporting=(foreign,),
                generated_at=FIXED_TIME,
            )

    def test_evidence_set_rejects_duplicate_record(self) -> None:
        with self.assertRaises(EvidenceValidationError):
            EvidenceSet(
                evidence_set_id="set-001",
                proposition=self.proposition,
                supporting=(self.record,),
                neutral=(self.record,),
                generated_at=FIXED_TIME,
            )

    def test_mappingproxy_serialization_regression(self) -> None:
        payload = self.record.as_dict()

        self.assertEqual(payload["provenance"]["source"], "sensor-a")
        self.assertEqual(payload["provenance"]["capture"]["sequence"], 7)
        self.assertEqual(
            payload["provenance"]["capture"]["channels"],
            ["pressure", "temperature"],
        )

    def test_serialization_is_deterministic_and_key_ordered(self) -> None:
        first = Proposition(
            proposition_id="prop-order",
            statement="Ordering is deterministic.",
            subject="serializer",
            predicate="orders mappings",
            context={"z": 1, "a": 2, "m": {"y": 3, "b": 4}},
            created_at=FIXED_TIME,
        )
        second = Proposition(
            proposition_id="prop-order",
            statement="Ordering is deterministic.",
            subject="serializer",
            predicate="orders mappings",
            context={"a": 2, "m": {"b": 4, "y": 3}, "z": 1},
            created_at=FIXED_TIME,
        )

        self.assertEqual(first.as_dict(), second.as_dict())
        self.assertEqual(list(first.as_dict()["context"].keys()), ["a", "m", "z"])

    def test_evidence_set_serializes(self) -> None:
        gap = EvidenceGap(
            gap_id="gap-001",
            proposition_id="prop-001",
            gap_type=EvidenceGapType.DIRECT_EVIDENCE_MISSING,
            description="Second direct source required.",
            severity=0.6,
        )
        evidence_set = EvidenceSet(
            evidence_set_id="set-001",
            proposition=self.proposition,
            supporting=(self.record,),
            gaps=(gap,),
            aggregate_support=0.88,
            aggregate_contradiction=0.0,
            source_diversity=0.5,
            coverage=0.7,
            sufficiency_status=EvidenceSufficiencyStatus.PARTIALLY_SUFFICIENT,
            generated_at=FIXED_TIME,
        )

        payload = evidence_set.as_dict()

        self.assertEqual(payload["evidence_set_id"], "set-001")
        self.assertEqual(payload["proposition"]["proposition_id"], "prop-001")
        self.assertEqual(payload["supporting"][0]["evidence_id"], "ev-001")
        self.assertEqual(payload["generated_at"], "2026-07-21T12:00:00+00:00")

    def test_assessment_and_admissibility_contracts_serialize(self) -> None:
        decision = AdmissibilityDecision(
            decision_id="decision-001",
            observation_id="obs-001",
            status=AdmissibilityStatus.ADMITTED,
            reason=AdmissibilityReason.ACCEPTED,
            rationale="Observation passed Pack 2A fixture policy.",
            policy_version="test-policy-1",
            assessed_at=FIXED_TIME,
            metadata={"review": {"required": False}},
        )
        assessment = EvidenceAssessment(
            assessment_id="assess-001",
            proposition_id="prop-001",
            observation_id="obs-001",
            direction=EvidenceDirection.SUPPORTS,
            method=AssessmentMethod.DETERMINISTIC_RULE,
            source_reliability=SourceReliabilityClass.HIGH,
            integrity_status=IntegrityStatus.VERIFIED,
            weight=self.weight,
            rationale="Observation supports proposition.",
            assessed_at=FIXED_TIME,
        )

        self.assertEqual(decision.as_dict()["status"], "admitted")
        self.assertEqual(decision.as_dict()["metadata"]["review"]["required"], False)
        self.assertEqual(assessment.as_dict()["direction"], "supports")


if __name__ == "__main__":
    unittest.main()

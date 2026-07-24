"""Tests for Genesis IV-R3A Pack 1."""

from __future__ import annotations

import unittest
from enum import Enum
from types import MappingProxyType

import core.evidence as evidence
from core.evidence.enums import (
    AdmissibilityReason,
    AdmissibilityStatus,
    AssessmentMethod,
    EvidenceDirection,
    EvidenceDirectness,
    EvidenceGapType,
    EvidenceRelationshipType,
    EvidenceStatus,
    EvidenceSufficiencyStatus,
    IntegrityStatus,
    PropositionModality,
    PropositionStatus,
    SourceReliabilityClass,
    StableStringEnum,
)
from core.evidence.errors import (
    EvidenceAdmissibilityError,
    EvidenceAggregationError,
    EvidenceConflictError,
    EvidenceConstructionError,
    EvidenceError,
    EvidenceFingerprintError,
    EvidenceIntegrityError,
    EvidenceNotFoundError,
    EvidencePolicyError,
    EvidenceRelationshipError,
    EvidenceSerializationError,
    EvidenceStateTransitionError,
    EvidenceValidationError,
    ObservationReferenceError,
    PropositionError,
    PropositionNotFoundError,
    PropositionValidationError,
    UnsupportedObservationError,
)


class EvidenceEnumTests(unittest.TestCase):
    def test_all_public_enums_are_string_enums(self) -> None:
        enum_types = (
            AdmissibilityReason,
            AdmissibilityStatus,
            AssessmentMethod,
            EvidenceDirection,
            EvidenceDirectness,
            EvidenceGapType,
            EvidenceRelationshipType,
            EvidenceStatus,
            EvidenceSufficiencyStatus,
            IntegrityStatus,
            PropositionModality,
            PropositionStatus,
            SourceReliabilityClass,
        )

        for enum_type in enum_types:
            with self.subTest(enum_type=enum_type.__name__):
                self.assertTrue(issubclass(enum_type, StableStringEnum))
                self.assertTrue(issubclass(enum_type, str))
                self.assertTrue(issubclass(enum_type, Enum))

    def test_enum_string_conversion_returns_wire_value(self) -> None:
        self.assertEqual(str(EvidenceDirection.SUPPORTS), "supports")
        self.assertEqual(
            str(EvidenceRelationshipType.COMMON_SOURCE),
            "common_source",
        )
        self.assertEqual(
            str(AdmissibilityReason.MISSING_PROVENANCE),
            "missing_provenance",
        )

    def test_enum_values_are_unique_within_each_enum(self) -> None:
        enum_types = (
            AdmissibilityReason,
            AdmissibilityStatus,
            AssessmentMethod,
            EvidenceDirection,
            EvidenceDirectness,
            EvidenceGapType,
            EvidenceRelationshipType,
            EvidenceStatus,
            EvidenceSufficiencyStatus,
            IntegrityStatus,
            PropositionModality,
            PropositionStatus,
            SourceReliabilityClass,
        )

        for enum_type in enum_types:
            with self.subTest(enum_type=enum_type.__name__):
                values = [member.value for member in enum_type]
                self.assertEqual(len(values), len(set(values)))


class EvidenceErrorTests(unittest.TestCase):
    def test_error_hierarchy_uses_single_domain_root(self) -> None:
        error_types = (
            EvidenceAdmissibilityError,
            EvidenceAggregationError,
            EvidenceConflictError,
            EvidenceConstructionError,
            EvidenceFingerprintError,
            EvidenceIntegrityError,
            EvidenceNotFoundError,
            EvidencePolicyError,
            EvidenceRelationshipError,
            EvidenceSerializationError,
            EvidenceStateTransitionError,
            EvidenceValidationError,
            ObservationReferenceError,
            PropositionError,
            PropositionNotFoundError,
            PropositionValidationError,
            UnsupportedObservationError,
        )

        for error_type in error_types:
            with self.subTest(error_type=error_type.__name__):
                self.assertTrue(issubclass(error_type, EvidenceError))

    def test_error_preserves_immutable_context(self) -> None:
        error = EvidenceValidationError(
            "Invalid evidence score.",
            context={"field": "relevance", "value": 1.4},
        )

        self.assertIsInstance(error.context, MappingProxyType)
        self.assertEqual(error.context["field"], "relevance")
        with self.assertRaises(TypeError):
            error.context["field"] = "integrity"  # type: ignore[index]

    def test_error_serializes_deterministically(self) -> None:
        error = EvidenceIntegrityError(
            "Fingerprint mismatch.",
            code="fingerprint_mismatch",
            context={"evidence_id": "ev_001"},
        )

        self.assertEqual(
            error.as_dict(),
            {
                "error_type": "EvidenceIntegrityError",
                "code": "fingerprint_mismatch",
                "message": "Fingerprint mismatch.",
                "context": {"evidence_id": "ev_001"},
            },
        )

    def test_empty_error_message_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            EvidenceError("   ")

    def test_empty_error_code_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            EvidenceError("Failure.", code="   ")


class EvidencePublicApiTests(unittest.TestCase):
    def test_public_api_exports_declared_symbols(self) -> None:
        expected = {
            "AdmissibilityReason",
            "AdmissibilityStatus",
            "AssessmentMethod",
            "EvidenceDirection",
            "EvidenceError",
            "EvidenceRelationshipType",
            "EvidenceStatus",
            "EvidenceValidationError",
            "PropositionNotFoundError",
            "SourceReliabilityClass",
            "UnsupportedObservationError",
        }

        self.assertTrue(expected.issubset(set(evidence.__all__)))
        for symbol in expected:
            with self.subTest(symbol=symbol):
                self.assertTrue(hasattr(evidence, symbol))

    def test_pack1_does_not_export_future_contracts(self) -> None:
        prohibited = {
            "EvidenceRecord",
            "EvidenceSet",
            "EvidenceService",
            "Proposition",
            "WeightBreakdown",
        }

        self.assertTrue(prohibited.isdisjoint(set(evidence.__all__)))


if __name__ == "__main__":
    unittest.main()

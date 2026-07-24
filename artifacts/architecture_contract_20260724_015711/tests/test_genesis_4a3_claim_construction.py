"""Genesis IV-A3 claim-construction tests."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from decimal import Decimal

from core.cognition import (
    AcquisitionMethod,
    ClaimCandidate,
    ClaimConstructionEngine,
    ClaimKind,
    ClaimStatus,
    EvidenceChain,
    EvidenceChainStatus,
    EvidenceDirection,
    EvidenceKind,
    EvidenceQuality,
    EvidenceRecord,
    ExtractionSource,
    ObservationEngine,
    ProvenanceKind,
    ProvenanceRecord,
    SourceReliability,
    canonical_json,
    validate_claim_record,
)


class GenesisIVA3ClaimConstructionTests(unittest.TestCase):
    def setUp(self) -> None:
        source = ExtractionSource(
            source_id="document:battery-report",
            segment_id="segment-0001",
            text="Battery voltage is 10.2 V.",
            start_offset=0,
            end_offset=26,
            evidence_ids=("source-evidence-001",),
        )

        self.observation = ObservationEngine(
            default_source_reliability=SourceReliability.HIGH,
        ).observe(source).observations[0]

        self.provenance = ProvenanceRecord(
            source=self.observation.source,
            kind=ProvenanceKind.REPRESENTATION_SEGMENT,
            acquisition_method=AcquisitionMethod.EXTRACTED,
            origin_system="jarvis-representation",
        )

    def make_evidence(
        self,
        *,
        direction: EvidenceDirection,
        confidence: Decimal,
        description: str,
    ) -> EvidenceRecord:
        kind = (
            EvidenceKind.CONTRADICTING
            if direction is EvidenceDirection.OPPOSES
            else EvidenceKind.DIRECT
        )

        return EvidenceRecord.from_observation(
            self.observation,
            provenance=self.provenance,
            kind=kind,
            direction=direction,
            quality=EvidenceQuality.STRONG,
            confidence=confidence,
            description=description,
        )

    def test_supported_claim(self) -> None:
        support = self.make_evidence(
            direction=EvidenceDirection.SUPPORTS,
            confidence=Decimal("0.95"),
            description="Direct source support.",
        )

        chain = EvidenceChain(
            subject_id=self.observation.observation_id,
            evidence=(support,),
            status=EvidenceChainStatus.COMPLETE,
            confidence=Decimal("0.95"),
        )

        result = ClaimConstructionEngine().construct(
            ClaimCandidate(
                observation=self.observation,
                evidence_chain=chain,
                kind=ClaimKind.QUANTITY,
            )
        )

        self.assertEqual(
            result.claim.status,
            ClaimStatus.SUPPORTED,
        )
        self.assertEqual(result.supporting_count, 1)
        self.assertEqual(result.opposing_count, 0)

        validate_claim_record(result.claim)

    def test_contested_claim(self) -> None:
        support = self.make_evidence(
            direction=EvidenceDirection.SUPPORTS,
            confidence=Decimal("0.90"),
            description="Supporting source.",
        )
        opposition = self.make_evidence(
            direction=EvidenceDirection.OPPOSES,
            confidence=Decimal("0.80"),
            description="Opposing source.",
        )

        chain = EvidenceChain(
            subject_id=self.observation.observation_id,
            evidence=(support, opposition),
            status=EvidenceChainStatus.CONTESTED,
            confidence=Decimal("0.85"),
        )

        result = ClaimConstructionEngine().construct(
            ClaimCandidate(
                observation=self.observation,
                evidence_chain=chain,
                kind=ClaimKind.QUANTITY,
            )
        )

        self.assertEqual(
            result.claim.status,
            ClaimStatus.CONTESTED,
        )
        self.assertEqual(
            result.claim.confidence,
            Decimal("0.70"),
        )

        validate_claim_record(result.claim)

    def test_rejected_claim(self) -> None:
        opposition = self.make_evidence(
            direction=EvidenceDirection.OPPOSES,
            confidence=Decimal("0.90"),
            description="Direct contradiction.",
        )

        chain = EvidenceChain(
            subject_id=self.observation.observation_id,
            evidence=(opposition,),
            status=EvidenceChainStatus.COMPLETE,
            confidence=Decimal("0.90"),
        )

        result = ClaimConstructionEngine().construct(
            ClaimCandidate(
                observation=self.observation,
                evidence_chain=chain,
                kind=ClaimKind.QUANTITY,
            )
        )

        self.assertEqual(
            result.claim.status,
            ClaimStatus.REJECTED,
        )

        validate_claim_record(result.claim)

    def test_deterministic_identity(self) -> None:
        evidence = self.make_evidence(
            direction=EvidenceDirection.SUPPORTS,
            confidence=Decimal("0.95"),
            description="Direct support.",
        )

        chain_a = EvidenceChain(
            subject_id=self.observation.observation_id,
            evidence=(evidence,),
            status=EvidenceChainStatus.COMPLETE,
            confidence=Decimal("0.95"),
            metadata=(
                ("beta", "2"),
                ("alpha", "1"),
            ),
        )

        chain_b = EvidenceChain(
            subject_id=self.observation.observation_id,
            evidence=(evidence,),
            status=EvidenceChainStatus.COMPLETE,
            confidence=Decimal("0.95"),
            metadata=(
                ("alpha", "1"),
                ("beta", "2"),
            ),
        )

        engine = ClaimConstructionEngine()

        claim_a = engine.construct(
            ClaimCandidate(
                observation=self.observation,
                evidence_chain=chain_a,
                kind=ClaimKind.QUANTITY,
                metadata=(
                    ("source", "test"),
                    ("phase", "a3"),
                ),
            )
        ).claim

        claim_b = engine.construct(
            ClaimCandidate(
                observation=self.observation,
                evidence_chain=chain_b,
                kind=ClaimKind.QUANTITY,
                metadata=(
                    ("phase", "a3"),
                    ("source", "test"),
                ),
            )
        ).claim

        self.assertEqual(claim_a, claim_b)
        self.assertEqual(claim_a.claim_id, claim_b.claim_id)
        self.assertEqual(
            canonical_json(claim_a),
            canonical_json(claim_b),
        )

    def test_claim_is_immutable(self) -> None:
        evidence = self.make_evidence(
            direction=EvidenceDirection.SUPPORTS,
            confidence=Decimal("0.95"),
            description="Direct support.",
        )

        chain = EvidenceChain(
            subject_id=self.observation.observation_id,
            evidence=(evidence,),
            status=EvidenceChainStatus.COMPLETE,
            confidence=Decimal("0.95"),
        )

        claim = ClaimConstructionEngine().construct(
            ClaimCandidate(
                observation=self.observation,
                evidence_chain=chain,
                kind=ClaimKind.QUANTITY,
            )
        ).claim

        with self.assertRaises(FrozenInstanceError):
            claim.status = ClaimStatus.REJECTED

    def test_chain_must_reference_observation(self) -> None:
        evidence = self.make_evidence(
            direction=EvidenceDirection.SUPPORTS,
            confidence=Decimal("0.95"),
            description="Direct support.",
        )

        chain = EvidenceChain(
            subject_id="different-observation",
            evidence=(evidence,),
            status=EvidenceChainStatus.COMPLETE,
            confidence=Decimal("0.95"),
        )

        candidate = ClaimCandidate(
            observation=self.observation,
            evidence_chain=chain,
            kind=ClaimKind.QUANTITY,
        )

        with self.assertRaisesRegex(
            Exception,
            "subject is not aligned",
        ):
            ClaimConstructionEngine().construct(candidate)

    def test_construct_many_is_order_independent(self) -> None:
        support = self.make_evidence(
            direction=EvidenceDirection.SUPPORTS,
            confidence=Decimal("0.95"),
            description="Support.",
        )

        chain = EvidenceChain(
            subject_id=self.observation.observation_id,
            evidence=(support,),
            status=EvidenceChainStatus.COMPLETE,
            confidence=Decimal("0.95"),
        )

        first = ClaimCandidate(
            observation=self.observation,
            evidence_chain=chain,
            kind=ClaimKind.QUANTITY,
            description="First candidate.",
        )
        second = ClaimCandidate(
            observation=self.observation,
            evidence_chain=chain,
            kind=ClaimKind.PROPERTY,
            description="Second candidate.",
        )

        engine = ClaimConstructionEngine()

        forward = engine.construct_many((first, second))
        reverse = engine.construct_many((second, first))

        self.assertEqual(forward, reverse)


if __name__ == "__main__":
    unittest.main()

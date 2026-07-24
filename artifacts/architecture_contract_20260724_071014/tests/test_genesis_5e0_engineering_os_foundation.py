from __future__ import annotations
import unittest

from core.engineering import (
    ENGINEERING_CONSTITUTION, ChangeKind, ChangeProposal, ChangeRisk,
    DecisionStatus, EngineeringAssessment, EngineeringGate,
    EngineeringValidationError, EvidenceStatus, GateStatus,
    GovernanceDecision, VerificationEvidence, VerificationKind,
    constitution_fingerprint,
)

class EngineeringOSFoundationTests(unittest.TestCase):
    def test_constitution_unique_and_deterministic(self):
        ids = [item.principle_id for item in ENGINEERING_CONSTITUTION]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(constitution_fingerprint(), constitution_fingerprint())
        self.assertEqual(len(constitution_fingerprint()), 64)

    def test_proposal_is_immutable(self):
        item = ChangeProposal(
            "v-e0", "Foundation", ChangeKind.FEATURE, ChangeRisk.LOW,
            "Establish governance.", ("engineering",), ("core.engineering",),
        )
        with self.assertRaises((AttributeError, TypeError)):
            item.title = "Changed"

    def test_proposal_requires_owner(self):
        with self.assertRaises(EngineeringValidationError):
            ChangeProposal(
                "bad", "Bad", ChangeKind.FEATURE, ChangeRisk.LOW,
                "Fixture.", ("engineering",), (),
            )

    def test_high_risk_requires_rollback(self):
        with self.assertRaises(EngineeringValidationError):
            ChangeProposal(
                "risk", "Risk", ChangeKind.MIGRATION, ChangeRisk.HIGH,
                "Fixture.", ("reasoning",), ("core.reasoning",),
            )

    def test_sufficient_evidence_cannot_fail(self):
        with self.assertRaises(EngineeringValidationError):
            VerificationEvidence(
                "ev", "change", VerificationKind.REGRESSION,
                EvidenceStatus.SUFFICIENT, "verify.sh", "./verify.sh", 5, 1,
            )

    def test_failed_gate_requires_blocker(self):
        with self.assertRaises(EngineeringValidationError):
            EngineeringGate(
                "gate", "Gate", GateStatus.FAILED,
                (VerificationKind.REGRESSION,),
            )

    def test_approved_decision_requires_evidence(self):
        with self.assertRaises(EngineeringValidationError):
            GovernanceDecision(
                "decision", "change", DecisionStatus.APPROVED,
                "Commander", "Approved.",
            )

    def test_complete_assessment(self):
        proposal = ChangeProposal(
            "v-e0", "Foundation", ChangeKind.FEATURE, ChangeRisk.LOW,
            "Establish governance.", ("architecture", "engineering"),
            ("core.engineering",),
        )
        evidence = VerificationEvidence(
            "unit", "v-e0", VerificationKind.UNIT,
            EvidenceStatus.SUFFICIENT, "verify.sh", "./verify.sh", 8, 0,
        )
        gate = EngineeringGate(
            "foundation", "Foundation", GateStatus.PASSED,
            (VerificationKind.UNIT,), ("unit",),
        )
        decision = GovernanceDecision(
            "approve", "v-e0", DecisionStatus.APPROVED,
            "Commander", "Accepted.", ("unit",),
        )
        assessment = EngineeringAssessment(
            "assessment", proposal, (evidence,), (gate,), decision,
            ("Governance is explicit.",),
        )
        self.assertEqual(len(assessment.fingerprint()), 64)

    def test_unknown_decision_evidence_rejected(self):
        proposal = ChangeProposal(
            "change", "Change", ChangeKind.FEATURE, ChangeRisk.LOW,
            "Fixture.", ("engineering",), ("core.engineering",),
        )
        decision = GovernanceDecision(
            "decision", "change", DecisionStatus.APPROVED,
            "Commander", "Fixture.", ("missing",),
        )
        with self.assertRaises(EngineeringValidationError):
            EngineeringAssessment("assessment", proposal, (), (), decision)

if __name__ == "__main__":
    unittest.main()

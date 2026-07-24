import unittest

from core.cognition.workspace import (
    Assumption,
    CognitiveWorkspaceError,
    CognitiveWorkspaceService,
    EvidenceReference,
    Hypothesis,
    HypothesisStatus,
    OpenQuestion,
    WorkspaceStatus,
)


class TestGenesis3A1CognitiveWorkspace(unittest.TestCase):
    def setUp(self) -> None:
        self.service = CognitiveWorkspaceService()
        self.workspace = self.service.create_workspace(
            "Determine the most reliable deployment strategy",
            workspace_id="cws_fixture",
        )

    def test_workspace_creation_is_explicit_and_auditable(self) -> None:
        self.assertEqual(self.workspace.workspace_id, "cws_fixture")
        self.assertEqual(self.workspace.revision, 0)
        self.assertEqual(len(self.workspace.events), 1)

    def test_hypothesis_identity_is_deterministic(self) -> None:
        first = Hypothesis.create("Deploy using a blue-green strategy")
        second = Hypothesis.create("Deploy using a blue-green strategy")
        self.assertEqual(first.hypothesis_id, second.hypothesis_id)

    def test_add_hypothesis_returns_new_revision(self) -> None:
        hypothesis = Hypothesis.create("Use a staged rollout")
        updated = self.service.add_hypothesis(
            self.workspace,
            hypothesis,
        )
        self.assertEqual(self.workspace.revision, 0)
        self.assertEqual(updated.revision, 1)
        self.assertEqual(len(updated.hypotheses), 1)

    def test_evidence_is_attached_to_known_hypothesis(self) -> None:
        hypothesis = Hypothesis.create("Use a staged rollout")
        workspace = self.service.add_hypothesis(
            self.workspace,
            hypothesis,
        )
        evidence = EvidenceReference(
            evidence_id="ev_001",
            summary="Canary deployment reduced incident impact.",
            credibility=0.9,
        )
        updated = self.service.attach_evidence(
            workspace,
            hypothesis.hypothesis_id,
            evidence,
        )
        self.assertEqual(len(updated.evidence), 1)
        self.assertEqual(
            updated.hypotheses[0].evidence_ids,
            ("ev_001",),
        )

    def test_hypothesis_transition_updates_confidence(self) -> None:
        hypothesis = Hypothesis.create("Use a staged rollout")
        workspace = self.service.add_hypothesis(
            self.workspace,
            hypothesis,
        )
        updated = self.service.transition_hypothesis(
            workspace,
            hypothesis.hypothesis_id,
            HypothesisStatus.SUPPORTED,
            confidence=0.85,
            rationale="Evidence supports gradual exposure.",
        )
        self.assertEqual(
            updated.hypotheses[0].status,
            HypothesisStatus.SUPPORTED,
        )
        self.assertEqual(updated.hypotheses[0].confidence, 0.85)

    def test_assumptions_are_explicit(self) -> None:
        assumption = Assumption.create(
            "Traffic can be partitioned safely",
            confidence=0.7,
        )
        updated = self.service.add_assumption(
            self.workspace,
            assumption,
        )
        self.assertEqual(len(updated.assumptions), 1)

    def test_questions_can_be_resolved(self) -> None:
        question = OpenQuestion.create(
            "Does the platform support weighted routing?",
            priority=90,
        )
        workspace = self.service.open_question(
            self.workspace,
            question,
        )
        updated = self.service.resolve_question(
            workspace,
            question.question_id,
            "Yes, through the ingress controller.",
        )
        self.assertTrue(updated.questions[0].resolved)

    def test_snapshot_selects_strongest_active_hypothesis(self) -> None:
        one = Hypothesis.create("Strategy one", confidence=0.4)
        two = Hypothesis.create("Strategy two", confidence=0.8)
        workspace = self.service.add_hypothesis(
            self.workspace,
            one,
        )
        workspace = self.service.add_hypothesis(
            workspace,
            two,
        )
        snapshot = workspace.snapshot()
        self.assertEqual(
            snapshot.strongest_hypothesis_id,
            two.hypothesis_id,
        )

    def test_terminal_workspace_rejects_mutation(self) -> None:
        resolved = self.service.set_workspace_status(
            self.workspace,
            WorkspaceStatus.RESOLVED,
            detail="Decision approved.",
        )
        with self.assertRaises(CognitiveWorkspaceError):
            self.service.add_hypothesis(
                resolved,
                Hypothesis.create("Late hypothesis"),
            )

    def test_invalid_confidence_is_rejected(self) -> None:
        with self.assertRaises(CognitiveWorkspaceError):
            Hypothesis.create("Invalid", confidence=1.1)


if __name__ == "__main__":
    unittest.main()

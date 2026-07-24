from __future__ import annotations

import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from core.cognition.integration import (
    AssumptionSeed,
    CognitiveWorkspaceIntegrationDirector,
    CognitiveWorkspaceIntegrationService,
    EvidenceSeed,
    HypothesisSeed,
    QuestionSeed,
    WorkspaceIntegrationPipeline,
    WorkspaceIntegrationRequest,
)
from core.cognition.workspace import SQLiteCognitiveWorkspaceRepository


class Genesis3A4Tests(unittest.TestCase):
    def request(self, workspace_id: str = "cws_genesis_3a4") -> WorkspaceIntegrationRequest:
        return WorkspaceIntegrationRequest(
            objective="Determine whether knowledge grounding is sufficient",
            workspace_id=workspace_id,
            hypotheses=(HypothesisSeed("Grounding is sufficient", confidence=0.7),),
            evidence=(EvidenceSeed("Grounding is sufficient", "Catalog coverage is complete", source_uri="catalog://coverage", credibility=0.9),),
            assumptions=(AssumptionSeed("Catalog metrics are current", confidence=0.8),),
            questions=(QuestionSeed("Are any critical domains missing?", priority=90),),
        )

    def test_contracts_are_immutable(self) -> None:
        request = self.request()
        with self.assertRaises(FrozenInstanceError):
            request.objective = "changed"  # type: ignore[misc]

    def test_pipeline_builds_complete_workspace_context(self) -> None:
        result = WorkspaceIntegrationPipeline().apply(self.request())
        self.assertTrue(result.created)
        self.assertFalse(result.persisted)
        self.assertEqual(result.snapshot.hypothesis_count, 1)
        self.assertEqual(result.snapshot.evidence_count, 1)
        self.assertEqual(result.snapshot.assumption_count, 1)
        self.assertEqual(result.snapshot.unresolved_question_count, 1)

    def test_pipeline_is_idempotent_against_existing_workspace(self) -> None:
        pipeline = WorkspaceIntegrationPipeline()
        first = pipeline.apply(self.request())
        second = pipeline.apply(self.request(), workspace=first.workspace)
        self.assertEqual(second.workspace, first.workspace)
        self.assertEqual(second.applied_hypotheses, 0)
        self.assertEqual(second.applied_evidence, 0)

    def test_service_persists_and_resumes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteCognitiveWorkspaceRepository(Path(directory) / "workspace.sqlite")
            service = CognitiveWorkspaceIntegrationService(repository)
            first = service.integrate(self.request())
            second = service.integrate(self.request())
            self.assertTrue(first.persisted)
            self.assertTrue(second.persisted)
            self.assertEqual(repository.list_ids(), ("cws_genesis_3a4",))
            self.assertEqual(second.workspace, first.workspace)

    def test_director_exposes_stable_execution_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteCognitiveWorkspaceRepository(Path(directory) / "workspace.sqlite")
            director = CognitiveWorkspaceIntegrationDirector(CognitiveWorkspaceIntegrationService(repository))
            result = director.execute(self.request("cws_director"))
            self.assertEqual(result.workspace.workspace_id, "cws_director")

    def test_unknown_evidence_target_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            WorkspaceIntegrationRequest(
                objective="test",
                evidence=(EvidenceSeed("missing", "evidence"),),
            )


if __name__ == "__main__":
    unittest.main()

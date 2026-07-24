import tempfile
import unittest
from pathlib import Path

from core.cognition import (
    CognitiveWorkspaceCodec,
    CognitiveWorkspaceConflictError,
    CognitiveWorkspaceNotFoundError,
    CognitiveWorkspaceService,
    EvidenceReference,
    Hypothesis,
    SQLiteCognitiveWorkspaceRepository,
)


class TestGenesis3A2PersistentWorkspaceRepository(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.database = Path(self.tempdir.name) / "workspace.sqlite"
        self.repository = SQLiteCognitiveWorkspaceRepository(
            self.database
        )
        self.service = CognitiveWorkspaceService()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_repository_creates_database(self) -> None:
        self.assertTrue(self.database.is_file())

    def test_codec_round_trip_preserves_workspace(self) -> None:
        workspace = self.service.create_workspace(
            "Evaluate deployment options",
            workspace_id="cws_round_trip",
        )
        restored = CognitiveWorkspaceCodec.decode(
            CognitiveWorkspaceCodec.encode(workspace)
        )
        self.assertEqual(restored, workspace)

    def test_save_and_get_workspace(self) -> None:
        workspace = self.service.create_workspace(
            "Evaluate deployment options",
            workspace_id="cws_save_get",
        )
        self.repository.save(workspace)
        restored = self.repository.get(workspace.workspace_id)
        self.assertEqual(restored, workspace)

    def test_update_requires_advancing_revision(self) -> None:
        workspace = self.service.create_workspace(
            "Evaluate deployment options",
            workspace_id="cws_revision",
        )
        self.repository.save(workspace)
        with self.assertRaises(CognitiveWorkspaceConflictError):
            self.repository.save(workspace)

    def test_expected_revision_detects_stale_writer(self) -> None:
        workspace = self.service.create_workspace(
            "Evaluate deployment options",
            workspace_id="cws_conflict",
        )
        self.repository.save(workspace)
        updated = self.service.add_hypothesis(
            workspace,
            Hypothesis.create("Use blue-green deployment"),
        )
        self.repository.save(updated, expected_revision=0)

        second_update = self.service.add_hypothesis(
            workspace,
            Hypothesis.create("Use rolling deployment"),
        )
        with self.assertRaises(CognitiveWorkspaceConflictError):
            self.repository.save(second_update, expected_revision=0)

    def test_list_ids_is_stable_and_sorted(self) -> None:
        for identifier in ("cws_b", "cws_a", "cws_c"):
            self.repository.save(
                self.service.create_workspace(
                    "Objective",
                    workspace_id=identifier,
                )
            )
        self.assertEqual(
            self.repository.list_ids(),
            ("cws_a", "cws_b", "cws_c"),
        )

    def test_exists_reports_presence(self) -> None:
        workspace = self.service.create_workspace(
            "Objective",
            workspace_id="cws_exists",
        )
        self.assertFalse(self.repository.exists(workspace.workspace_id))
        self.repository.save(workspace)
        self.assertTrue(self.repository.exists(workspace.workspace_id))

    def test_delete_removes_workspace(self) -> None:
        workspace = self.service.create_workspace(
            "Objective",
            workspace_id="cws_delete",
        )
        self.repository.save(workspace)
        self.repository.delete(
            workspace.workspace_id,
            expected_revision=0,
        )
        self.assertFalse(self.repository.exists(workspace.workspace_id))

    def test_missing_workspace_raises_typed_error(self) -> None:
        with self.assertRaises(CognitiveWorkspaceNotFoundError):
            self.repository.get("missing")

    def test_complex_workspace_survives_persistence(self) -> None:
        workspace = self.service.create_workspace(
            "Evaluate deployment options",
            workspace_id="cws_complex",
        )
        hypothesis = Hypothesis.create("Use canary deployment")
        workspace = self.service.add_hypothesis(
            workspace,
            hypothesis,
        )
        workspace = self.service.attach_evidence(
            workspace,
            hypothesis.hypothesis_id,
            EvidenceReference(
                evidence_id="ev_1",
                summary="Canary rollout reduced blast radius.",
                credibility=0.95,
            ),
        )
        self.repository.save(workspace)
        self.assertEqual(
            self.repository.get(workspace.workspace_id),
            workspace,
        )


if __name__ == "__main__":
    unittest.main()

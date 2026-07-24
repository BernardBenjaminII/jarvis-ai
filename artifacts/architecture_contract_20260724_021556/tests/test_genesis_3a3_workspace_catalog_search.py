import tempfile
import unittest
from pathlib import Path

from core.cognition import (
    Assumption,
    CognitiveWorkspaceCatalog,
    CognitiveWorkspaceService,
    Hypothesis,
    OpenQuestion,
    SQLiteCognitiveWorkspaceRepository,
    SortDirection,
    WorkspaceQuery,
    WorkspaceSortField,
    WorkspaceStatus,
)


class TestGenesis3A3WorkspaceCatalogSearch(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repository = SQLiteCognitiveWorkspaceRepository(
            Path(self.tempdir.name) / "catalog.sqlite"
        )
        self.service = CognitiveWorkspaceService()
        self.catalog = CognitiveWorkspaceCatalog(self.repository)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def save_workspace(
        self,
        workspace_id: str,
        objective: str,
        confidence: float,
        *,
        status: WorkspaceStatus = WorkspaceStatus.OPEN,
        unresolved_question: bool = False,
        assumption: bool = False,
    ) -> None:
        workspace = self.service.create_workspace(
            objective,
            workspace_id=workspace_id,
        )
        hypothesis = Hypothesis.create(
            f"Hypothesis for {objective}",
            confidence=confidence,
        )
        workspace = self.service.add_hypothesis(
            workspace,
            hypothesis,
        )
        if unresolved_question:
            workspace = self.service.open_question(
                workspace,
                OpenQuestion.create(
                    f"What blocks {objective}?"
                ),
            )
        if assumption:
            workspace = self.service.add_assumption(
                workspace,
                Assumption.create(
                    f"Assumption for {objective}"
                ),
            )
        if status != WorkspaceStatus.OPEN:
            workspace = self.service.set_workspace_status(
                workspace,
                status,
                detail=f"Transition to {status.value}",
            )
        self.repository.save(workspace)

    def test_catalog_rebuilds_from_repository(self) -> None:
        self.save_workspace(
            "cws_one",
            "Deploy mission control",
            0.8,
        )
        entries = self.catalog.rebuild()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].workspace_id, "cws_one")

    def test_text_search_matches_objective(self) -> None:
        self.save_workspace(
            "cws_one",
            "Deploy mission control",
            0.8,
        )
        self.save_workspace(
            "cws_two",
            "Review evidence model",
            0.6,
        )
        results = self.catalog.search(
            WorkspaceQuery(text="mission control")
        )
        self.assertEqual(
            tuple(item.workspace_id for item in results),
            ("cws_one",),
        )

    def test_text_search_matches_hypothesis_content(self) -> None:
        self.save_workspace(
            "cws_one",
            "Deployment",
            0.8,
        )
        results = self.catalog.search(
            WorkspaceQuery(text="hypothesis deployment")
        )
        self.assertEqual(len(results), 1)

    def test_status_filter(self) -> None:
        self.save_workspace(
            "cws_open",
            "Open objective",
            0.5,
        )
        self.save_workspace(
            "cws_resolved",
            "Resolved objective",
            0.9,
            status=WorkspaceStatus.RESOLVED,
        )
        results = self.catalog.search(
            WorkspaceQuery(
                statuses=(WorkspaceStatus.RESOLVED,)
            )
        )
        self.assertEqual(
            tuple(item.workspace_id for item in results),
            ("cws_resolved",),
        )

    def test_confidence_filter(self) -> None:
        self.save_workspace("cws_low", "Low", 0.3)
        self.save_workspace("cws_high", "High", 0.9)
        results = self.catalog.search(
            WorkspaceQuery(maximum_confidence=0.5)
        )
        self.assertEqual(
            tuple(item.workspace_id for item in results),
            ("cws_low",),
        )

    def test_unresolved_question_filter(self) -> None:
        self.save_workspace(
            "cws_blocked",
            "Blocked",
            0.5,
            unresolved_question=True,
        )
        self.save_workspace(
            "cws_clear",
            "Clear",
            0.5,
        )
        results = self.catalog.blocked()
        self.assertEqual(
            tuple(item.workspace_id for item in results),
            ("cws_blocked",),
        )

    def test_assumption_filter(self) -> None:
        self.save_workspace(
            "cws_assumption",
            "Assumption objective",
            0.5,
            assumption=True,
        )
        results = self.catalog.search(
            WorkspaceQuery(has_assumptions=True)
        )
        self.assertEqual(len(results), 1)

    def test_resumable_excludes_terminal_workspaces(self) -> None:
        self.save_workspace(
            "cws_open",
            "Open",
            0.5,
        )
        self.save_workspace(
            "cws_resolved",
            "Resolved",
            0.5,
            status=WorkspaceStatus.RESOLVED,
        )
        self.assertEqual(
            tuple(
                item.workspace_id
                for item in self.catalog.resumable()
            ),
            ("cws_open",),
        )

    def test_sorting_is_deterministic(self) -> None:
        self.save_workspace("cws_b", "Beta", 0.5)
        self.save_workspace("cws_a", "Alpha", 0.5)
        results = self.catalog.search(
            WorkspaceQuery(
                sort_by=WorkspaceSortField.OBJECTIVE,
                direction=SortDirection.ASCENDING,
            )
        )
        self.assertEqual(
            tuple(item.workspace_id for item in results),
            ("cws_a", "cws_b"),
        )

    def test_limit_is_applied_after_sorting(self) -> None:
        self.save_workspace("cws_low", "Low", 0.2)
        self.save_workspace("cws_mid", "Mid", 0.5)
        self.save_workspace("cws_high", "High", 0.9)
        results = self.catalog.search(
            WorkspaceQuery(
                sort_by=WorkspaceSortField.STRONGEST_CONFIDENCE,
                direction=SortDirection.DESCENDING,
                limit=2,
            )
        )
        self.assertEqual(
            tuple(item.workspace_id for item in results),
            ("cws_high", "cws_mid"),
        )

    def test_search_workspaces_returns_full_models(self) -> None:
        self.save_workspace(
            "cws_full",
            "Full workspace",
            0.7,
        )
        workspaces = self.catalog.search_workspaces(
            WorkspaceQuery(text="full")
        )
        self.assertEqual(workspaces[0].workspace_id, "cws_full")


if __name__ == "__main__":
    unittest.main()

"""Genesis III-A3A public-surface compatibility tests."""

import unittest

import core.cognition as cognition
from core.cognition import (
    Assumption,
    CognitiveWorkspaceCatalog,
    CognitiveWorkspaceCodec,
    CognitiveWorkspaceService,
)
from core.cognition.workspace import (
    Assumption as WorkspaceAssumption,
    CognitiveWorkspaceCatalog as WorkspaceCatalog,
    CognitiveWorkspaceCodec as WorkspaceCodec,
    CognitiveWorkspaceService as WorkspaceService,
)


class Genesis3A3APublicSurfaceTests(unittest.TestCase):
    def test_workspace_symbols_are_exported_from_package_root(self) -> None:
        required = {
            "Assumption",
            "CognitiveWorkspaceCatalog",
            "CognitiveWorkspaceCodec",
            "CognitiveWorkspaceService",
        }
        self.assertTrue(required.issubset(set(cognition.__all__)))
        for symbol in required:
            self.assertTrue(hasattr(cognition, symbol), symbol)

    def test_exports_are_identity_preserving_aliases(self) -> None:
        self.assertIs(Assumption, WorkspaceAssumption)
        self.assertIs(CognitiveWorkspaceCatalog, WorkspaceCatalog)
        self.assertIs(CognitiveWorkspaceCodec, WorkspaceCodec)
        self.assertIs(CognitiveWorkspaceService, WorkspaceService)

    def test_workspace_smoke_contract_remains_operational(self) -> None:
        service = CognitiveWorkspaceService()
        workspace = service.create_workspace(
            "Certify restored cognition public surface",
            workspace_id="cws_genesis_3a3a",
        )
        assumption = Assumption.create(
            "Workspace implementation remains canonical",
            confidence=1.0,
        )
        updated = service.add_assumption(workspace, assumption)
        encoded = CognitiveWorkspaceCodec.encode(updated)
        restored = CognitiveWorkspaceCodec.decode(encoded)
        self.assertEqual(restored, updated)


if __name__ == "__main__":
    unittest.main()

"""Deterministic HTTP certification for C-2 Director activation."""
from __future__ import annotations

import importlib
import os
from pathlib import Path
import sys
import types
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient


def _install_brain_import_stub() -> None:
    """Isolate HTTP contracts from optional model/tool dependencies."""
    module = types.ModuleType("core.src.brain")
    module.route_question = lambda question: f"UNUSED: {question}"
    sys.modules["core.src.brain"] = module


class DirectorActivationHttpTests(unittest.TestCase):
    def test_conversation_endpoint_returns_director_activity(self) -> None:
        with TemporaryDirectory() as temp:
            runtime_root = Path(temp)
            os.environ["JARVIS_RUNTIME_ROOT"] = str(runtime_root)
            os.environ["JARVIS_CONVERSATION_DB"] = str(runtime_root / "conversation.sqlite")
            os.environ["JARVIS_EXECUTIVE_DB"] = str(runtime_root / "missions.sqlite")

            _install_brain_import_stub()
            import core.src.routes.api as api_module
            import core.src.main as main_module

            importlib.reload(api_module)
            importlib.reload(main_module)

            with patch.object(
                api_module.conversation_orchestrator,
                "synthesis_handler",
                lambda question: f"SYNTHESIZED: {question}",
            ):
                client = TestClient(main_module.app)
                response = client.post(
                    "/api/conversation/query",
                    json={"question": "Search the catalog", "session_id": "c2-http"},
                )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["state"], "completed")
            self.assertEqual(payload["answer"], "SYNTHESIZED: Search the catalog")
            self.assertEqual(payload["metadata"]["orchestration"], "director_activation")
            self.assertIn("knowledge", payload["metadata"]["directors_activated"])
            self.assertTrue(payload["metadata"]["missions"])
            mission = payload["metadata"]["missions"][0]
            self.assertTrue(mission["mission_id"])
            self.assertTrue(mission["tasks"])


if __name__ == "__main__":
    unittest.main()

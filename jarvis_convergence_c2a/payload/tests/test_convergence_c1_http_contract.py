"""C-1 transport contract after C-2 Executive activation.

The contract remains deterministic by replacing only the natural-language
synthesis boundary. Director mission creation and HTTP serialization remain
real and are therefore still certified.
"""
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


class ConversationHTTPContractTests(unittest.TestCase):
    def test_conversation_endpoint_returns_structured_envelope(self) -> None:
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
                lambda question: f"ok:{question}",
            ):
                client = TestClient(main_module.app)
                response = client.post(
                    "/api/conversation/query",
                    json={"question": "status", "session_id": "http-session"},
                )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["session_id"], "http-session")
            self.assertEqual(payload["state"], "completed")
            self.assertEqual(payload["answer"], "ok:status")
            self.assertTrue(payload["request_id"])
            self.assertTrue(payload["objectives"])
            self.assertTrue(payload["trace"])
            self.assertEqual(payload["metadata"]["orchestration"], "director_activation")
            self.assertTrue(payload["metadata"]["missions"])


if __name__ == "__main__":
    unittest.main()

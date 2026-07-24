"""C-1 transport contract after C-4 knowledge grounding.

The contract replaces only natural-language synthesis. C-4 may enrich the
synthesis input with deterministic knowledge-grounding context, so the
transport test certifies the response prefix and envelope rather than
requiring the pre-C-4 answer to remain byte-for-byte identical.
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
            os.environ["JARVIS_CATALOG_DB"] = str(runtime_root / "catalog.sqlite")

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
            self.assertTrue(payload["answer"].startswith("ok:status"))
            self.assertTrue(payload["request_id"])
            self.assertTrue(payload["objectives"])
            self.assertTrue(payload["trace"])
            self.assertEqual(
                payload["metadata"]["orchestration"],
                "knowledge_grounded_director_activation",
            )
            self.assertTrue(payload["metadata"]["missions"])
            self.assertIn("knowledge_grounding", payload["metadata"])


if __name__ == "__main__":
    unittest.main()

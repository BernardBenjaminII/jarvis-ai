import importlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient


class ConversationHTTPContractTests(unittest.TestCase):
    def test_conversation_endpoint_returns_structured_envelope(self):
        with TemporaryDirectory() as temp:
            os.environ["JARVIS_CONVERSATION_DB"] = str(Path(temp) / "conversation.sqlite")
            import core.src.routes.api as api
            importlib.reload(api)
            from core.src.main import app
            with patch.object(api.conversation_service, "answer_handler", lambda q: f"ok:{q}"):
                client = TestClient(app)
                response = client.post(
                    "/api/conversation/query",
                    json={"question": "status", "session_id": "http-session"},
                )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["session_id"], "http-session")
            self.assertEqual(payload["state"], "completed")
            self.assertEqual(payload["answer"], "ok:status")
            self.assertTrue(payload["trace"])


if __name__ == "__main__":
    unittest.main()

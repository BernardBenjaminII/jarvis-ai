import importlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient


class DirectorActivationHttpTests(unittest.TestCase):
    def test_conversation_endpoint_returns_director_activity(self):
        with TemporaryDirectory() as temp:
            os.environ["JARVIS_RUNTIME_ROOT"] = temp
            import core.src.routes.api as api_module
            import core.src.main as main_module
            importlib.reload(api_module)
            importlib.reload(main_module)
            client = TestClient(main_module.app)
            response = client.post(
                "/api/conversation/query",
                json={"question": "Search the catalog", "session_id": "c2-http"},
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["state"], "completed")
            self.assertEqual(payload["metadata"]["orchestration"], "director_activation")
            self.assertIn("knowledge", payload["metadata"]["directors_activated"])
            self.assertTrue(payload["metadata"]["missions"])


if __name__ == "__main__":
    unittest.main()

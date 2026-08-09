from __future__ import annotations

import unittest

from core.executive.conversation import (
    ExecutiveConversationAdapter,
    WorkspaceConversationRequest,
)


class GenesisIXA2Tests(unittest.TestCase):
    def test_request_normalization(self) -> None:
        request = WorkspaceConversationRequest(question="  Explain Laravel  ")
        self.assertEqual(request.question, "Explain Laravel")
        self.assertEqual(request.mode, "knowledge")

    def test_session_preservation(self) -> None:
        request = WorkspaceConversationRequest(
            question="Continue",
            session_id="session-123",
        )
        self.assertEqual(request.runtime_kwargs()["session_id"], "session-123")

    def test_response_normalization(self) -> None:
        adapter = ExecutiveConversationAdapter(lambda **_: {
            "response": "Laravel is a PHP framework.",
            "session_id": "session-1",
            "metadata": {
                "executive_knowledge_state": {"confidence": 0.92},
                "knowledge_grounding": {
                    "sources": [{"title": "Laravel Documentation"}],
                    "evidence": [{"text": "Laravel is a PHP framework."}],
                },
            },
        })
        response = adapter.execute(
            WorkspaceConversationRequest(question="What is Laravel?")
        )
        self.assertEqual(response.status, "completed")
        self.assertEqual(response.session_id, "session-1")
        self.assertEqual(len(response.sources), 1)
        self.assertEqual(len(response.evidence), 1)

    def test_error_normalization(self) -> None:
        def fail(**_):
            raise TimeoutError("conversation timed out")
        response = ExecutiveConversationAdapter(fail).execute(
            WorkspaceConversationRequest(question="Question")
        )
        self.assertEqual(response.status, "failed")
        self.assertEqual(response.error["code"], "conversation_timeout")

    def test_activity_is_exposed(self) -> None:
        response = ExecutiveConversationAdapter(
            lambda **_: {"answer": "Grounded response"}
        ).execute(WorkspaceConversationRequest(question="Question"))
        stages = {item["stage"] for item in response.activity}
        self.assertIn("Knowledge Directorate", stages)
        self.assertIn("Grounding", stages)

    def test_route_contract(self) -> None:
        from core.src.routes.knowledge_workspace import router
        contracts = {
            (method, route.path)
            for route in router.routes
            for method in getattr(route, "methods", ())
        }
        self.assertIn(("POST", "/api/knowledge/conversation"), contracts)


if __name__ == "__main__":
    unittest.main()

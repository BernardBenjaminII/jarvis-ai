from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from core.conversation import (
    ConversationState,
    ExecutiveConversationService,
    ExecutiveRequestCompiler,
)


class ExecutiveRequestCompilerTests(unittest.TestCase):
    def test_empty_input_is_rejected(self):
        with self.assertRaises(ValueError):
            ExecutiveRequestCompiler().compile("   ")

    def test_compound_request_is_segmented(self):
        objectives = ExecutiveRequestCompiler().compile(
            "Search the catalog; compare the sources and then prepare a plan."
        )
        self.assertGreaterEqual(len(objectives), 2)
        hints = {hint for objective in objectives for hint in objective.routing_hints}
        self.assertIn("knowledge", hints)
        self.assertIn("planning", hints)


class ExecutiveConversationServiceTests(unittest.TestCase):
    def test_request_is_persisted_and_answered(self):
        with TemporaryDirectory() as temp:
            service = ExecutiveConversationService(
                database_path=Path(temp) / "conversation.sqlite",
                answer_handler=lambda question: f"ANSWER: {question}",
            )
            response = service.ask("What is in the catalog?", session_id="session-1")
            self.assertEqual(response.state, ConversationState.COMPLETED)
            self.assertEqual(response.session_id, "session-1")
            self.assertIn("ANSWER", response.answer)
            history = service.history("session-1")
            self.assertEqual([item["role"] for item in history], ["operator", "jarvis"])

    def test_handler_failure_returns_structured_failure(self):
        def fail(_question):
            raise RuntimeError("boom")
        with TemporaryDirectory() as temp:
            service = ExecutiveConversationService(
                database_path=Path(temp) / "conversation.sqlite",
                answer_handler=fail,
            )
            response = service.ask("Fail safely")
            self.assertEqual(response.state, ConversationState.FAILED)
            self.assertEqual(response.error, "boom")
            self.assertTrue(response.trace)


if __name__ == "__main__":
    unittest.main()

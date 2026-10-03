import unittest

from core.conversation.clarification import (
    clear_pending_clarification,
    pending_clarification,
    process_clarification,
    security_question_is_ambiguous,
)


class ClarificationR1Tests(unittest.TestCase):

    def tearDown(self):
        for session in (
            "security-a",
            "security-b",
            "security-c",
            "security-d",
            "security-e",
        ):
            clear_pending_clarification(session)

    def test_broad_security_question_requires_clarification(self):
        self.assertTrue(
            security_question_is_ambiguous(
                "Hey Jarvis, how do I improve my security?"
            )
        )

        result = process_clarification(
            session_id="security-a",
            operator_input="Hey Jarvis, how do I improve my security?",
        )

        self.assertTrue(result.requires_clarification)
        self.assertIn("physical security", result.prompt.lower())
        self.assertIn("cybersecurity", result.prompt.lower())
        self.assertIsNotNone(pending_clarification("security-a"))

    def test_physical_followup_resolves_original_question(self):
        process_clarification(
            session_id="security-b",
            operator_input="How do I improve my security stance?",
        )

        result = process_clarification(
            session_id="security-b",
            operator_input="Physical.",
        )

        self.assertTrue(result.resolved)
        self.assertEqual(result.resolution, "physical")
        self.assertEqual(
            result.resolved_input,
            "How do I improve my physical security stance?",
        )
        self.assertIsNone(pending_clarification("security-b"))

    def test_cyber_followup_resolves_original_question(self):
        process_clarification(
            session_id="security-c",
            operator_input="How can I improve my security?",
        )

        result = process_clarification(
            session_id="security-c",
            operator_input="Cybersecurity",
        )

        self.assertTrue(result.resolved)
        self.assertEqual(
            result.resolved_input,
            "How can I improve my cybersecurity?",
        )

    def test_explicit_physical_security_does_not_clarify(self):
        result = process_clarification(
            session_id="security-d",
            operator_input=(
                "How do I improve my physical security "
                "in a new environment?"
            ),
        )

        self.assertEqual(result.action, "continue")
        self.assertFalse(result.requires_clarification)

    def test_manual_search_is_not_intercepted(self):
        result = process_clarification(
            session_id="security-e",
            operator_input="Find my physical security manuals",
        )

        self.assertEqual(result.action, "continue")


if __name__ == "__main__":
    unittest.main()

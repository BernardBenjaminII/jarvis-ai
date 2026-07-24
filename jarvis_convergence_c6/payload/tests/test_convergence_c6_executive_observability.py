import unittest
from dataclasses import dataclass

from core.conversation.contracts import ConversationTraceEvent, CompiledObjective, ExecutiveRequestContext
from core.observability import ExecutiveObservabilityService


@dataclass(frozen=True)
class Assignment:
    directors: tuple[str, ...]


@dataclass(frozen=True)
class Grounding:
    evidence: tuple[object, ...]
    gaps: tuple[object, ...]


@dataclass(frozen=True)
class KnowledgeState:
    confidence: float
    answerability: str
    contradiction_count: int


@dataclass(frozen=True)
class Result:
    assignments: tuple[Assignment, ...]
    trace: tuple[ConversationTraceEvent, ...]
    grounding: Grounding
    knowledge_state: KnowledgeState


class C6ObservabilityTests(unittest.TestCase):
    def test_projects_ui_safe_mission_transparency(self):
        context = ExecutiveRequestContext(
            request_id="req-1", session_id="session-1", operator_input="status",
            objectives=(CompiledObjective("obj-1", "status", 1, ()),),
            channel="api", mode="executive", metadata={},
        )
        result = Result(
            assignments=(Assignment(("knowledge", "operations")),),
            trace=(
                ConversationTraceEvent("knowledge.grounding", "completed", "Grounded", {"evidence_count": 2}),
                ConversationTraceEvent("executive.synthesis", "completed", "Synthesized", {}),
            ),
            grounding=Grounding((object(), object()), (object(),)),
            knowledge_state=KnowledgeState(0.82, "qualified", 1),
        )
        service = ExecutiveObservabilityService()
        payload = service.project(context=context, result=result).to_dict()
        self.assertEqual(payload["mission_count"], 1)
        self.assertEqual(payload["directors"], ["knowledge", "operations"])
        self.assertEqual(payload["evidence_count"], 2)
        self.assertEqual(payload["knowledge_gap_count"], 1)
        self.assertEqual(payload["contradiction_count"], 1)
        self.assertEqual(payload["current_stage"], "executive.synthesis")
        self.assertNotIn("chain_of_thought", str(payload).lower())

    def test_latest_is_idle_until_projection(self):
        self.assertIsNone(ExecutiveObservabilityService().latest())


if __name__ == "__main__":
    unittest.main()

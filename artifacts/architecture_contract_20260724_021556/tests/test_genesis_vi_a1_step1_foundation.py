"""Tests for Genesis VI-A1 Step 1 — foundational cognition contracts."""

from __future__ import annotations

import unittest
from datetime import timezone

from core.cognition import (
    AttentionCandidate,
    AttentionReason,
    CognitiveCycleStatus,
    CognitiveEvent,
    CognitiveEventKind,
    CognitiveState,
    ExecutiveContext,
    MemoryEntry,
    MemoryEntryKind,
    StateTransition,
)


class CognitionFoundationTests(unittest.TestCase):
    def test_memory_entry_is_valid_and_immutable(self) -> None:
        entry = MemoryEntry(
            entry_id="goal-001",
            kind=MemoryEntryKind.GOAL,
            content="Establish executive cognition.",
            importance=1.0,
            confidence=1.0,
            source="commander",
            metadata={"phase": "Genesis VI-A1"},
        )

        self.assertEqual(entry.kind, MemoryEntryKind.GOAL)
        self.assertEqual(entry.created_at.tzinfo, timezone.utc)

        with self.assertRaises(TypeError):
            entry.metadata["phase"] = "changed"  # type: ignore[index]

    def test_attention_candidate_normalizes_reason_order(self) -> None:
        candidate = AttentionCandidate(
            candidate_id="candidate-001",
            subject="Preserve architecture boundaries",
            reasons=(
                AttentionReason.SAFETY,
                AttentionReason.MISSION_CRITICALITY,
                AttentionReason.SAFETY,
            ),
            mission_criticality=1.0,
            safety_impact=0.8,
        )

        self.assertEqual(
            candidate.reasons,
            (
                AttentionReason.MISSION_CRITICALITY,
                AttentionReason.SAFETY,
            ),
        )

    def test_state_transition_requires_positive_sequence(self) -> None:
        with self.assertRaises(ValueError):
            StateTransition(
                sequence=0,
                previous_state=CognitiveState.IDLE,
                next_state=CognitiveState.INITIALIZING,
                reason="Invalid sequence.",
            )

    def test_cognitive_event_freezes_metadata(self) -> None:
        event = CognitiveEvent(
            sequence=1,
            kind=CognitiveEventKind.CONTEXT_CREATED,
            message="Context created.",
            state=CognitiveState.IDLE,
            metadata={"source": "test"},
        )

        with self.assertRaises(TypeError):
            event.metadata["source"] = "changed"  # type: ignore[index]

    def test_executive_context_snapshot_is_immutable(self) -> None:
        context = ExecutiveContext(
            cycle_id="cycle-001",
            mission_id="mission-001",
            objective_id="objective-001",
            task_id="task-001",
            goal="Establish cognition contracts.",
            state=CognitiveState.IDLE,
            status=CognitiveCycleStatus.CREATED,
            authority="commander",
            constraints=("No model invocation.",),
            metadata={"phase": "Genesis VI-A1"},
        )

        self.assertEqual(context.state, CognitiveState.IDLE)
        self.assertEqual(context.constraints, ("No model invocation.",))

        with self.assertRaises(TypeError):
            context.metadata["phase"] = "changed"  # type: ignore[index]

    def test_invalid_probability_rejected(self) -> None:
        with self.assertRaises(ValueError):
            MemoryEntry(
                entry_id="invalid",
                kind=MemoryEntryKind.FACT,
                content="Invalid confidence.",
                confidence=1.1,
            )


if __name__ == "__main__":
    unittest.main()

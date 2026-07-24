"""Tests for Genesis VI-A2 deterministic working memory."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from core.cognition import (
    DuplicateMemoryEntryError,
    MemoryEntry,
    MemoryEntryKind,
    WorkingMemory,
    WorkingMemoryCapacityError,
    WorkingMemorySnapshot,
)


def entry(
    entry_id: str,
    *,
    kind: MemoryEntryKind = MemoryEntryKind.FACT,
    content: str | None = None,
    importance: float = 0.5,
    confidence: float = 1.0,
    second: int = 0,
) -> MemoryEntry:
    return MemoryEntry(
        entry_id=entry_id,
        kind=kind,
        content=content or entry_id,
        importance=importance,
        confidence=confidence,
        source="test",
        created_at=datetime(2026, 1, 1, 0, 0, second, tzinfo=timezone.utc),
    )


class WorkingMemoryTests(unittest.TestCase):
    def test_capacity_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            WorkingMemory(capacity=0)

    def test_admission_and_lookup(self) -> None:
        memory = WorkingMemory(capacity=2)
        item = entry("fact-001")

        evicted = memory.admit(item)

        self.assertIsNone(evicted)
        self.assertEqual(memory.size, 1)
        self.assertEqual(memory.remaining_capacity, 1)
        self.assertIs(memory.get("fact-001"), item)
        self.assertIs(memory.require("fact-001"), item)
        self.assertIn("fact-001", memory)

    def test_duplicate_identifier_rejected(self) -> None:
        memory = WorkingMemory(capacity=2)
        memory.admit(entry("fact-001"))

        with self.assertRaises(DuplicateMemoryEntryError):
            memory.admit(entry("fact-001", importance=1.0))

    def test_weak_entry_rejected_when_full(self) -> None:
        memory = WorkingMemory(capacity=1)
        memory.admit(entry("strong", importance=0.9))

        with self.assertRaises(WorkingMemoryCapacityError):
            memory.admit(entry("weak", importance=0.2))

        self.assertIn("strong", memory)
        self.assertNotIn("weak", memory)

    def test_stronger_entry_evicts_weakest(self) -> None:
        memory = WorkingMemory(capacity=2)
        weak = entry("weak", importance=0.2)
        medium = entry("medium", importance=0.5)
        strong = entry("strong", importance=0.9)

        memory.admit_many((weak, medium))
        evicted = memory.admit(strong)

        self.assertEqual(evicted, weak)
        self.assertEqual(
            tuple(item.entry_id for item in memory.entries()),
            ("strong", "medium"),
        )

    def test_retention_order_is_deterministic(self) -> None:
        memory = WorkingMemory(capacity=3)
        memory.admit_many(
            (
                entry("alpha", importance=0.5, confidence=0.8, second=1),
                entry("bravo", importance=0.7, confidence=0.4, second=1),
                entry("charlie", importance=0.7, confidence=0.9, second=1),
            )
        )

        self.assertEqual(
            tuple(item.entry_id for item in memory.entries()),
            ("charlie", "bravo", "alpha"),
        )

    def test_kind_index_uses_retention_order(self) -> None:
        memory = WorkingMemory(capacity=4)
        memory.admit_many(
            (
                entry(
                    "goal-low",
                    kind=MemoryEntryKind.GOAL,
                    importance=0.5,
                ),
                entry(
                    "fact",
                    kind=MemoryEntryKind.FACT,
                    importance=1.0,
                ),
                entry(
                    "goal-high",
                    kind=MemoryEntryKind.GOAL,
                    importance=0.9,
                ),
            )
        )

        self.assertEqual(
            tuple(item.entry_id for item in memory.by_kind(MemoryEntryKind.GOAL)),
            ("goal-high", "goal-low"),
        )

    def test_replace_returns_previous_entry(self) -> None:
        memory = WorkingMemory(capacity=2)
        original = entry("fact-001", content="original")
        replacement = entry("fact-001", content="replacement")

        memory.admit(original)
        previous = memory.replace(replacement)

        self.assertEqual(previous, original)
        self.assertEqual(memory.require("fact-001").content, "replacement")

    def test_update_preserves_identity_and_creation_time(self) -> None:
        memory = WorkingMemory(capacity=2)
        original = entry("fact-001", content="original", importance=0.2)
        memory.admit(original)

        updated = memory.update(
            "fact-001",
            content="updated",
            importance=0.8,
            metadata={"reason": "new evidence"},
        )

        self.assertEqual(updated.entry_id, original.entry_id)
        self.assertEqual(updated.created_at, original.created_at)
        self.assertEqual(updated.content, "updated")
        self.assertEqual(updated.importance, 0.8)
        self.assertEqual(updated.metadata["reason"], "new evidence")

    def test_remove_discard_and_clear(self) -> None:
        memory = WorkingMemory(capacity=3)
        first = entry("first", importance=0.1)
        second = entry("second", importance=0.9)
        memory.admit_many((first, second))

        self.assertEqual(memory.remove("first"), first)
        self.assertIsNone(memory.discard("missing"))
        self.assertEqual(memory.discard("second"), second)

        memory.admit_many((first, second))
        prior = memory.clear()

        self.assertEqual(prior, (second, first))
        self.assertEqual(memory.size, 0)

    def test_snapshot_is_immutable_and_detached(self) -> None:
        memory = WorkingMemory(capacity=2)
        first = entry("first")
        memory.admit(first)

        snapshot = memory.snapshot()
        self.assertIsInstance(snapshot, WorkingMemorySnapshot)
        self.assertEqual(snapshot.size, 1)
        self.assertEqual(snapshot.remaining_capacity, 1)
        self.assertEqual(snapshot.get("first"), first)

        memory.remove("first")
        self.assertEqual(snapshot.get("first"), first)
        self.assertEqual(snapshot.size, 1)

    def test_missing_require_and_remove_raise_key_error(self) -> None:
        memory = WorkingMemory(capacity=1)

        with self.assertRaises(KeyError):
            memory.require("missing")

        with self.assertRaises(KeyError):
            memory.remove("missing")


if __name__ == "__main__":
    unittest.main()

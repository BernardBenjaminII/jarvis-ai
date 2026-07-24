"""Phase X-C2 tests."""

from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from typing import Any

from core.representation.articulation import (
    ArticulationKind,
    ArticulationPolicy,
    EmptyArticulationInputError,
    SemanticArticulator,
)
from core.representation.context import (
    ContextAssembler,
    ContextPolicy,
    EmptyContextError,
)


@dataclass(frozen=True)
class Segment:
    segment_id: str
    ordinal: int
    kind: str
    text: str
    provenance: dict[str, Any] = field(default_factory=dict)


def segments() -> tuple[Segment, ...]:
    return (
        Segment("h", 0, "heading", "Operational Readiness",
                {"source_id": "xc2_fixture"}),
        Segment("s1", 1, "sentence",
                "JARVIS preserves deterministic representations.",
                {"source_id": "xc2_fixture"}),
        Segment("s2", 2, "sentence",
                "Every unit retains source identity.",
                {"source_id": "xc2_fixture"}),
        Segment("b1", 3, "bullet",
                "Reasoning consumes bounded context.",
                {"source_id": "xc2_fixture"}),
        Segment("b2", 4, "bullet",
                "Mission execution remains outside this phase.",
                {"source_id": "xc2_fixture"}),
    )


class ArticulationTests(unittest.TestCase):
    def test_groups_prose_and_lists(self) -> None:
        result = SemanticArticulator().articulate(segments())
        self.assertEqual(result.source_id, "xc2_fixture")
        self.assertEqual(len(result.units), 2)
        self.assertEqual(result.units[0].kind, ArticulationKind.PARAGRAPH)
        self.assertEqual(result.units[1].kind, ArticulationKind.LIST)
        self.assertEqual(result.units[0].title, "Operational Readiness")

    def test_preserves_traceability(self) -> None:
        result = SemanticArticulator().articulate(segments())
        self.assertEqual(result.units[0].source_segment_ids, ("s1", "s2"))
        self.assertEqual(result.units[1].source_segment_ids, ("b1", "b2"))

    def test_is_order_independent_after_ordinal_sort(self) -> None:
        first = SemanticArticulator().articulate(segments())
        second = SemanticArticulator().articulate(tuple(reversed(segments())))
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_provenance_is_immutable(self) -> None:
        result = SemanticArticulator().articulate(segments())
        with self.assertRaises(TypeError):
            result.units[0].segment_references[0].provenance["x"] = 1  # type: ignore[index]

    def test_character_budget_splits_units(self) -> None:
        result = SemanticArticulator(
            ArticulationPolicy(max_unit_characters=64)
        ).articulate(segments())
        self.assertGreaterEqual(len(result.units), 3)

    def test_accepts_mapping_segments(self) -> None:
        result = SemanticArticulator().articulate(({
            "id": "m1",
            "index": 0,
            "type": "sentence",
            "content": "Mapping-shaped segments remain compatible.",
            "metadata": {"source_id": "mapping"},
        },))
        self.assertEqual(result.source_id, "mapping")
        self.assertEqual(result.units[0].source_segment_ids, ("m1",))

    def test_empty_input_fails(self) -> None:
        with self.assertRaises(EmptyArticulationInputError):
            SemanticArticulator().articulate(())


class ContextTests(unittest.TestCase):
    def test_builds_bounded_context(self) -> None:
        articulation = SemanticArticulator().articulate(segments())
        context = ContextAssembler().assemble(
            articulation.units,
            source_id=articulation.source_id,
        )
        self.assertFalse(context.truncated)
        self.assertEqual(len(context.entries), 2)
        self.assertIn("Operational Readiness", context.text)

    def test_context_preserves_segment_ids(self) -> None:
        articulation = SemanticArticulator().articulate(segments())
        context = ContextAssembler().assemble(
            articulation.units,
            source_id=articulation.source_id,
        )
        self.assertEqual(context.entries[0].source_segment_ids, ("s1", "s2"))

    def test_context_budget_records_omissions(self) -> None:
        articulation = SemanticArticulator().articulate(segments())
        context = ContextAssembler(ContextPolicy(
            maximum_characters=180,
            maximum_units=1,
        )).assemble(articulation.units, source_id=articulation.source_id)
        self.assertTrue(context.truncated)
        self.assertEqual(len(context.entries), 1)
        self.assertEqual(len(context.omitted_unit_ids), 1)

    def test_context_is_deterministic(self) -> None:
        articulation = SemanticArticulator().articulate(segments())
        assembler = ContextAssembler()
        first = assembler.assemble(
            articulation.units,
            source_id=articulation.source_id,
        )
        second = assembler.assemble(
            tuple(reversed(articulation.units)),
            source_id=articulation.source_id,
        )
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_empty_context_fails(self) -> None:
        with self.assertRaises(EmptyContextError):
            ContextAssembler().assemble((), source_id="empty")


if __name__ == "__main__":
    unittest.main()

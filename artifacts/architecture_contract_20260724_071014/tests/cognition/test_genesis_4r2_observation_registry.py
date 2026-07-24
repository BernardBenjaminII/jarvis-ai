from __future__ import annotations

import unittest

from core.cognition.common.object_model import ProvenanceReference
from core.cognition.layers.observation import (
    DuplicateObservationError,
    ObservationFactory,
    ObservationInput,
    ObservationQuery,
    ObservationRegistry,
    ObservationSourceMode,
)


class ObservationRegistryTests(unittest.TestCase):
    def build(self, content: str, subject: str):
        return ObservationFactory().create(
            ObservationInput(
                content=content,
                subject=subject,
                source_mode=ObservationSourceMode.DOCUMENT,
                provenance=(
                    ProvenanceReference(
                        source_id=content,
                        source_type="document",
                    ),
                ),
            )
        )

    def test_register_and_query(self) -> None:
        registry = ObservationRegistry()
        first = self.build("Alpha is active.", "alpha")
        second = self.build("Beta is active.", "beta")
        registry.register(first)
        registry.register(second)

        query = ObservationQuery(registry)
        self.assertEqual(query.execute(subject="alpha"), (first,))
        self.assertEqual(len(query.execute(text="active")), 2)

    def test_duplicate_identifier_is_rejected(self) -> None:
        registry = ObservationRegistry()
        item = self.build("Alpha is active.", "alpha")
        registry.register(item)
        with self.assertRaises(DuplicateObservationError):
            registry.register(item)


if __name__ == "__main__":
    unittest.main()

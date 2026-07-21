from __future__ import annotations

import unittest

from core.cognition.common.object_model import ProvenanceReference
from core.cognition.layers.observation import (
    ObservationDirector,
    ObservationInput,
    ObservationLifecycleState,
    ObservationSourceMode,
)


class ObservationDirectorTests(unittest.TestCase):
    def candidate(self, content: str, source_id: str) -> ObservationInput:
        return ObservationInput(
            content=content,
            subject="system",
            source_mode=ObservationSourceMode.SYSTEM,
            provenance=(
                ProvenanceReference(
                    source_id=source_id,
                    source_type="system",
                ),
            ),
        )

    def test_observe_activates_and_registers(self) -> None:
        director = ObservationDirector()
        item = director.observe(self.candidate("System is nominal.", "a"))
        self.assertEqual(item.lifecycle_state, ObservationLifecycleState.ACTIVE)
        self.assertEqual(director.get(item.observation_id), item)

    def test_supersede_updates_lifecycle_and_relationship(self) -> None:
        director = ObservationDirector()
        old = director.observe(self.candidate("System is nominal.", "a"))
        new = director.supersede(
            old.observation_id,
            self.candidate("System is degraded.", "b"),
        )
        self.assertEqual(
            director.get(old.observation_id).lifecycle_state,
            ObservationLifecycleState.SUPERSEDED,
        )
        self.assertEqual(new.supersedes_id, old.observation_id)
        self.assertEqual(len(director.relationships.outgoing(new.observation_id)), 1)


if __name__ == "__main__":
    unittest.main()

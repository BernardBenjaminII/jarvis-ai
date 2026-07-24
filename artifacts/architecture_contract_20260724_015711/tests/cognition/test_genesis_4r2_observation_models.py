from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import unittest

from core.cognition.common.object_model import ProvenanceReference
from core.cognition.layers.observation import (
    ObservationFactory,
    ObservationInput,
    ObservationLifecycleState,
    ObservationSourceMode,
    ObservationValidationError,
)


class ObservationModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = ProvenanceReference(
            source_id="sensor-1",
            source_type="sensor",
        )

    def test_factory_builds_validated_immutable_record(self) -> None:
        record = ObservationFactory().create(
            ObservationInput(
                content="  Ambient temperature is 21 C.  ",
                source_mode=ObservationSourceMode.SENSOR,
                provenance=(self.source,),
                confidence=0.9,
            )
        )
        self.assertEqual(record.normalized_content, "Ambient temperature is 21 C.")
        self.assertEqual(
            record.lifecycle_state,
            ObservationLifecycleState.VALIDATED,
        )
        with self.assertRaises(FrozenInstanceError):
            record.confidence = 0.2  # type: ignore[misc]

    def test_missing_provenance_is_rejected(self) -> None:
        with self.assertRaises(ObservationValidationError):
            ObservationFactory().create(
                ObservationInput(
                    content="A valid length statement.",
                    source_mode=ObservationSourceMode.DIRECT,
                    provenance=(),
                )
            )

    def test_hash_is_deterministic(self) -> None:
        candidate = ObservationInput(
            content="System status is nominal.",
            source_mode=ObservationSourceMode.SYSTEM,
            provenance=(self.source,),
            observed_at=datetime(2026, 7, 20, tzinfo=timezone.utc),
        )
        record = ObservationFactory().create(candidate)
        self.assertEqual(record.deterministic_hash, record.deterministic_hash)


if __name__ == "__main__":
    unittest.main()

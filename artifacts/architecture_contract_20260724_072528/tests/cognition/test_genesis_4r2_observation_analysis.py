from __future__ import annotations

import unittest

from core.cognition.common.object_model import ProvenanceReference
from core.cognition.layers.observation import (
    ObservationConflictDetector,
    ObservationDuplicateDetector,
    ObservationFactory,
    ObservationInput,
    ObservationMergeEngine,
    ObservationSourceMode,
)


class ObservationAnalysisTests(unittest.TestCase):
    def make(self, content: str, subject: str, confidence: float = 0.8):
        return ObservationFactory().create(
            ObservationInput(
                content=content,
                subject=subject,
                confidence=confidence,
                source_mode=ObservationSourceMode.TESTIMONY,
                provenance=(
                    ProvenanceReference(
                        source_id=content,
                        source_type="testimony",
                    ),
                ),
            )
        )

    def test_exact_duplicates_are_detected(self) -> None:
        first = self.make("The door is open.", "door")
        second = self.make("The door is open.", "door")
        report = ObservationDuplicateDetector().compare(first, second)
        self.assertTrue(report.duplicate)
        self.assertTrue(report.exact)

    def test_explicit_polarity_conflict_is_detected(self) -> None:
        first = self.make("The door is open.", "door")
        second = self.make("The door is not open.", "door")
        report = ObservationConflictDetector().compare(first, second)
        self.assertTrue(report.conflict)

    def test_duplicate_merge_preserves_best_confidence(self) -> None:
        first = self.make("The door is open.", "door", 0.7)
        second = self.make("The door is open.", "door", 0.9)
        result = ObservationMergeEngine().merge(first, second)
        self.assertEqual(result.merged.confidence, 0.9)
        self.assertEqual(len(result.merged.provenance), 2)


if __name__ == "__main__":
    unittest.main()

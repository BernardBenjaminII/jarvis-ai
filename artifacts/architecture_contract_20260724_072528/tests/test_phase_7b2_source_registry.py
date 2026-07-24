"""Tests for JARVIS Gen 2 Phase VII-B2 source registry."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from knowledge_engine.acquisition_control import (
    AdmissionPolicy,
    SourceAdmissionService,
    SourceKind,
    SourceProposal,
    SourceTrustTier,
)
from knowledge_engine.source_registry import (
    InvalidLifecycleTransitionError,
    SourceLifecycleState,
    SourceNotAdmittedError,
    SourceRegistryConflictError,
    SourceRegistryService,
)


class SourceRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "source_registry.sqlite"
        self.registry = SourceRegistryService(self.db_path)
        self.admission = SourceAdmissionService()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _accepted(self, source_id: str = "nist"):
        return self.admission.evaluate(
            SourceProposal(
                source_id=source_id,
                display_name="NIST",
                location="https://www.nist.gov/publications",
                kind=SourceKind.HTTPS,
                trust_tier=SourceTrustTier.OFFICIAL,
            )
        )

    def test_registers_accepted_source(self) -> None:
        result = self.registry.register_admission(self._accepted())

        self.assertTrue(result.created)
        self.assertEqual(
            result.source.lifecycle_state,
            SourceLifecycleState.ADMITTED,
        )
        self.assertEqual(result.source.source_id, "nist")

    def test_registration_is_idempotent_by_fingerprint(self) -> None:
        first = self.registry.register_admission(self._accepted())
        second = self.registry.register_admission(self._accepted())

        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(
            first.source.registry_id,
            second.source.registry_id,
        )

    def test_rejects_nonaccepted_decision(self) -> None:
        review = self.admission.evaluate(
            SourceProposal(
                source_id="unknown",
                display_name="Unknown",
                location="https://example.com",
                kind=SourceKind.HTTPS,
                trust_tier=SourceTrustTier.UNKNOWN,
            )
        )

        with self.assertRaises(SourceNotAdmittedError):
            self.registry.register_admission(review)

    def test_source_id_conflict_is_detected(self) -> None:
        first = self.admission.evaluate(
            SourceProposal(
                source_id="same-id",
                display_name="First",
                location="https://example.com/one",
                kind=SourceKind.HTTPS,
                trust_tier=SourceTrustTier.OFFICIAL,
            )
        )
        second = self.admission.evaluate(
            SourceProposal(
                source_id="same-id",
                display_name="Second",
                location="https://example.com/two",
                kind=SourceKind.HTTPS,
                trust_tier=SourceTrustTier.OFFICIAL,
            )
        )

        self.registry.register_admission(first)

        with self.assertRaises(SourceRegistryConflictError):
            self.registry.register_admission(second)

    def test_valid_lifecycle_transitions(self) -> None:
        registered = self.registry.register_admission(
            self._accepted()
        ).source

        active = self.registry.transition(
            registered.registry_id,
            SourceLifecycleState.ACTIVE,
        )
        paused = self.registry.transition(
            active.registry_id,
            SourceLifecycleState.PAUSED,
        )
        resumed = self.registry.transition(
            paused.registry_id,
            SourceLifecycleState.ACTIVE,
        )
        retired = self.registry.transition(
            resumed.registry_id,
            SourceLifecycleState.RETIRED,
        )

        self.assertEqual(
            retired.lifecycle_state,
            SourceLifecycleState.RETIRED,
        )

    def test_retired_source_cannot_reactivate(self) -> None:
        registered = self.registry.register_admission(
            self._accepted()
        ).source
        retired = self.registry.transition(
            registered.registry_id,
            SourceLifecycleState.RETIRED,
        )

        with self.assertRaises(InvalidLifecycleTransitionError):
            self.registry.transition(
                retired.registry_id,
                SourceLifecycleState.ACTIVE,
            )

    def test_stats_are_correct(self) -> None:
        first = self.registry.register_admission(
            self._accepted("nist-one")
        ).source
        second_decision = self.admission.evaluate(
            SourceProposal(
                source_id="nist-two",
                display_name="NIST Two",
                location="https://csrc.nist.gov/publications",
                kind=SourceKind.HTTPS,
                trust_tier=SourceTrustTier.OFFICIAL,
            )
        )
        second = self.registry.register_admission(
            second_decision
        ).source

        self.registry.transition(
            first.registry_id,
            SourceLifecycleState.ACTIVE,
        )
        self.registry.transition(
            second.registry_id,
            SourceLifecycleState.RETIRED,
        )

        stats = self.registry.stats()

        self.assertEqual(stats.total, 2)
        self.assertEqual(stats.active, 1)
        self.assertEqual(stats.retired, 1)


if __name__ == "__main__":
    unittest.main()

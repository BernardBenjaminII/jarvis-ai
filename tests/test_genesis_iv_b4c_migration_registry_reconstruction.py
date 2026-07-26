"""Genesis IV-B4C migration-registry reconstruction tests."""

from __future__ import annotations

import unittest

from core.observation.migration_registry import (
    CANONICAL_OBSERVATION_PATH,
    MigrationDisposition,
    MigrationReadiness,
    approved_legacy_entries,
    canonical_observation_entry,
    deprecated_rename_entries,
    migration_entries,
    migration_entry_for,
    migration_registry_fingerprint,
    migration_registry_payload,
)


class GenesisIVB4CMigrationRegistryTests(unittest.TestCase):
    def test_registry_contains_exact_known_definition_set(self) -> None:
        self.assertEqual(
            {entry.path for entry in migration_entries()},
            {
                "core/observation/contracts.py",
                "core/cognition/common/contracts.py",
                "core/cognition/observation/models.py",
                "core/representation/contracts.py",
            },
        )

    def test_public_reexport_is_not_registry_owner(self) -> None:
        self.assertIsNone(
            migration_entry_for("core/cognition/contracts.py")
        )

    def test_exactly_one_canonical_owner(self) -> None:
        canonical = [
            entry
            for entry in migration_entries()
            if entry.disposition is MigrationDisposition.CANONICAL
        ]
        self.assertEqual(len(canonical), 1)
        self.assertEqual(canonical[0].path, CANONICAL_OBSERVATION_PATH)
        self.assertEqual(
            canonical_observation_entry(),
            canonical[0],
        )

    def test_approved_legacy_contract_is_adapter_backed(self) -> None:
        entries = approved_legacy_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(
            entries[0].path,
            "core/cognition/common/contracts.py",
        )
        self.assertEqual(
            entries[0].readiness,
            MigrationReadiness.ADAPTER_AVAILABLE,
        )
        self.assertTrue(entries[0].canonical_adapter)

    def test_deprecated_definitions_have_semantic_targets(self) -> None:
        targets = {
            entry.path: entry.target_name
            for entry in deprecated_rename_entries()
        }
        self.assertEqual(
            targets,
            {
                "core/cognition/observation/models.py":
                "ObservationRecord",
                "core/representation/contracts.py":
                "RepresentedStatement",
            },
        )

    def test_registry_payload_is_path_sorted(self) -> None:
        payload = migration_registry_payload()
        paths = [item["path"] for item in payload]
        self.assertEqual(paths, sorted(paths))

    def test_registry_fingerprint_is_deterministic(self) -> None:
        first = migration_registry_fingerprint()
        second = migration_registry_fingerprint()
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)


if __name__ == "__main__":
    unittest.main()

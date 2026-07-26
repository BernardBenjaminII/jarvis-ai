"""Final Genesis IV-B4 canonical Observation convergence tests."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import core.observation as public_api
from core.observation.audit import audit_observation_definitions
from core.observation.migration_registry import (
    CANONICAL_OBSERVATION_PATH,
    MIGRATION_ENTRIES,
    MIGRATION_SCHEMA_VERSION,
    OBSERVATION_MIGRATION_REGISTRY,
    MigrationDisposition,
    migration_entry_for,
    migration_entry_for_path,
    migration_registry_fingerprint,
)


ROOT = Path(__file__).resolve().parents[1]


class GenesisIVB4FinalCanonicalConvergenceTests(unittest.TestCase):
    def test_legacy_and_new_registry_names_share_identity(self) -> None:
        self.assertIs(
            MIGRATION_ENTRIES,
            OBSERVATION_MIGRATION_REGISTRY,
        )

    def test_legacy_and_new_lookup_functions_agree(self) -> None:
        for entry in MIGRATION_ENTRIES:
            self.assertIs(
                migration_entry_for(entry.path),
                migration_entry_for_path(entry.path),
            )

    def test_schema_version_is_public_and_nonempty(self) -> None:
        self.assertTrue(MIGRATION_SCHEMA_VERSION)
        self.assertEqual(
            public_api.MIGRATION_SCHEMA_VERSION,
            MIGRATION_SCHEMA_VERSION,
        )

    def test_public_reexport_is_not_a_definition_owner(self) -> None:
        self.assertIsNone(
            migration_entry_for_path("core/cognition/contracts.py")
        )

    def test_registry_has_one_canonical_owner(self) -> None:
        canonical = tuple(
            entry
            for entry in MIGRATION_ENTRIES
            if entry.disposition is MigrationDisposition.CANONICAL
        )
        self.assertEqual(len(canonical), 1)
        self.assertEqual(
            canonical[0].path,
            CANONICAL_OBSERVATION_PATH,
        )

    def test_repository_audit_converges(self) -> None:
        report = audit_observation_definitions(ROOT)
        self.assertEqual(
            report.canonical_definitions,
            (CANONICAL_OBSERVATION_PATH,),
        )
        self.assertFalse(report.forbidden_duplicates)

    def test_export_only_module_is_ignored_by_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            module = root / "core" / "example.py"
            module.parent.mkdir(parents=True)
            module.write_text(
                "from core.observation import Observation\n",
                encoding="utf-8",
            )

            report = audit_observation_definitions(root)
            self.assertEqual(report.definitions, ())

    def test_direct_unknown_definition_is_forbidden(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            module = root / "core" / "unknown.py"
            module.parent.mkdir(parents=True)
            module.write_text(
                "class Observation:\n    pass\n",
                encoding="utf-8",
            )

            report = audit_observation_definitions(root)
            self.assertEqual(
                report.forbidden_duplicates,
                ("core/unknown.py",),
            )

    def test_registry_fingerprint_is_deterministic(self) -> None:
        first = migration_registry_fingerprint()
        second = migration_registry_fingerprint()
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_required_legacy_public_names_exist(self) -> None:
        required = (
            "MIGRATION_ENTRIES",
            "MIGRATION_SCHEMA_VERSION",
            "migration_entry_for_path",
            "migration_registry_fingerprint",
        )
        for name in required:
            self.assertTrue(hasattr(public_api, name), name)


if __name__ == "__main__":
    unittest.main()

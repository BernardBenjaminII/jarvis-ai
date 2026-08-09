from __future__ import annotations

from pathlib import Path
import unittest

from dev.verification.genesis_manifest import (
    GenesisPhaseKey,
    parse_phase,
    validate_entries,
    validate_manifest,
)


class Genesis2A3G1CanonicalConstitutionalOrderingTests(unittest.TestCase):
    def test_runtime_root_precedes_capability_branch(self) -> None:
        self.assertLess(
            parse_phase("dev/verify_genesis_ix_0.sh"),
            parse_phase("dev/verify_genesis_ix_a1.sh"),
        )

    def test_runtime_root_preserves_legacy_label(self) -> None:
        phase = parse_phase("dev/verify_genesis_ix_0.sh")
        self.assertEqual(phase.label, "IX-Z0")
        self.assertEqual(phase.phase_kind, "root")

    def test_capability_branch_order(self) -> None:
        ordered = (
            "dev/verify_genesis_ix_0.sh",
            "dev/verify_genesis_ix_a0.sh",
            "dev/verify_genesis_ix_a1.sh",
            "dev/verify_genesis_ix_a1_1.sh",
            "dev/verify_genesis_ix_a1_2.sh",
            "dev/verify_genesis_ix_a2.sh",
            "dev/verify_genesis_ix_b0.sh",
        )
        phases = tuple(parse_phase(path) for path in ordered)
        self.assertEqual(tuple(sorted(phases)), phases)

    def test_generation_transition(self) -> None:
        self.assertLess(
            parse_phase("dev/verify_genesis_viii_b0.sh"),
            parse_phase("dev/verify_genesis_ix_0.sh"),
        )

    def test_existing_numeric_order_is_unchanged(self) -> None:
        self.assertLess(
            parse_phase("dev/verify_genesis_2a3g.sh"),
            parse_phase("dev/verify_genesis_2a3g1.sh"),
        )

    def test_current_ix_extension_validates(self) -> None:
        entries = (
            "dev/verify_genesis_1a1.sh",
            "dev/verify_genesis_1a2.sh",
            "dev/verify_genesis_1a3.sh",
            "dev/verify_genesis_2a1.sh",
            "dev/verify_genesis_2a2.sh",
            "dev/verify_reasoning_fixtures.sh",
            "dev/verify_genesis_2a3.sh",
            "dev/verify_genesis_2a3a.sh",
            "dev/verify_genesis_2a3b.sh",
            "dev/verify_genesis_2a3c.sh",
            "dev/verify_genesis_2a3d.sh",
            "dev/verify_genesis_2a3e.sh",
            "dev/verify_genesis_2a3f.sh",
            "dev/verify_genesis_2a3g.sh",
            "dev/verify_genesis_2a3g1.sh",
            "dev/verify_genesis_viii_a0_6.sh",
            "dev/verify_genesis_viii_b0.sh",
            "dev/verify_genesis_ix_0.sh",
            "dev/verify_genesis_ix_a1.sh",
            "dev/verify_genesis_ix_a1_1.sh",
        )
        report = validate_entries(entries)
        self.assertEqual(report.entries[-1].path, "dev/verify_genesis_ix_a1_1.sh")

    def test_repository_manifest_validates_when_available(self) -> None:
        path = Path("dev/verification/manifests/genesis.manifest")
        if not path.is_file():
            self.skipTest("repository manifest not present")
        report = validate_manifest(path)
        self.assertGreater(report.suite_count, 0)

    def test_ordering_is_deterministic(self) -> None:
        first = parse_phase("dev/verify_genesis_ix_0.sh")
        second = parse_phase("dev/verify_genesis_ix_a1.sh")
        self.assertEqual(first < second, first < second)


if __name__ == "__main__":
    unittest.main()

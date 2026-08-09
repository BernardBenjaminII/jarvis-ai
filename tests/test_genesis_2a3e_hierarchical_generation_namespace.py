
from __future__ import annotations

import unittest

from dev.verification.genesis_manifest import (
    CERTIFIED_BASELINE,
    GenesisManifestError,
    parse_phase,
    validate_entries,
)


class Genesis2A3EHierarchicalGenerationNamespaceTests(unittest.TestCase):
    def test_roman_generation_namespace(self) -> None:
        phase = parse_phase("dev/verify_genesis_vii_b0.sh")
        self.assertEqual(phase.generation, 7)
        self.assertEqual(phase.stream, "b")
        self.assertEqual(phase.ordinal, 0)
        self.assertEqual(phase.namespace, "roman")
        self.assertEqual(phase.label, "VII-B0")

    def test_future_roman_generation(self) -> None:
        phase = parse_phase("dev/verify_genesis_xii_c4a2.sh")
        self.assertEqual(phase.generation, 12)
        self.assertEqual(phase.label, "XII-C4.A.2")

    def test_numeric_namespace_is_unchanged(self) -> None:
        self.assertEqual(
            parse_phase("dev/verify_genesis_2a3b.sh").label,
            "2-A3B",
        )
        self.assertEqual(
            parse_phase("dev/verify_genesis_4a6a1.sh").label,
            "4-A6.A.1",
        )

    def test_numeric_and_roman_generation_order_together(self) -> None:
        self.assertLess(
            parse_phase("dev/verify_genesis_4a62.sh"),
            parse_phase("dev/verify_genesis_vii_b0.sh"),
        )

    def test_equivalent_generation_identity_compares_equal(self) -> None:
        numeric = parse_phase("dev/verify_genesis_7b1.sh")
        roman = parse_phase("dev/verify_genesis_vii_b1.sh")
        self.assertEqual(numeric, roman)

    def test_noncanonical_roman_generation_is_rejected(self) -> None:
        for path in (
            "dev/verify_genesis_iiii_b0.sh",
            "dev/verify_genesis_vx_b0.sh",
            "dev/verify_genesis_VII_b0.sh",
        ):
            with self.subTest(path=path):
                with self.assertRaises(GenesisManifestError):
                    parse_phase(path)

    def test_leading_zero_is_rejected(self) -> None:
        with self.assertRaises(GenesisManifestError):
            parse_phase("dev/verify_genesis_vii_b00.sh")

    def test_current_manifest_extension_validates(self) -> None:
        entries = CERTIFIED_BASELINE + (
            "dev/verify_genesis_2a3b.sh",
            "dev/verify_genesis_2a3c.sh",
            "dev/verify_genesis_2a3d.sh",
            "dev/verify_genesis_2a3e.sh",
            "dev/verify_genesis_2a4.sh",
            "dev/verify_genesis_3a1.sh",
            "dev/verify_genesis_4a62.sh",
            "dev/verify_genesis_vii_b0.sh",
        )
        report = validate_entries(entries)
        self.assertEqual(report.entries[-1].phase.label, "VII-B0")


if __name__ == "__main__":
    unittest.main()

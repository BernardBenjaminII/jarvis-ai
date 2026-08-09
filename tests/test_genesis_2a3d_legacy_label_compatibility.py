from __future__ import annotations

import unittest

from dev.verification.genesis_manifest import GenesisPhaseKey, parse_phase


class Genesis2A3DLegacyLabelCompatibilityTests(unittest.TestCase):
    def test_legacy_numeric_label(self) -> None:
        self.assertEqual(parse_phase("dev/verify_genesis_4a5.sh").label, "4-A5")

    def test_legacy_alphabetic_leaf_label(self) -> None:
        self.assertEqual(parse_phase("dev/verify_genesis_2a3b.sh").label, "2-A3B")

    def test_special_reasoning_fixture_label(self) -> None:
        self.assertEqual(parse_phase("dev/verify_reasoning_fixtures.sh").label, "2-A2R")

    def test_nested_label(self) -> None:
        self.assertEqual(parse_phase("dev/verify_genesis_4a6a1.sh").label, "4-A6.A.1")

    def test_deep_nested_label(self) -> None:
        self.assertEqual(
            parse_phase("dev/verify_genesis_10c3a4b2.sh").label,
            "10-C3.A.4.B.2",
        )

    def test_formatting_does_not_change_identity(self) -> None:
        phase = parse_phase("dev/verify_genesis_2a3b.sh")
        self.assertEqual(phase.hierarchy, ((0, 3), (1, 2)))
        self.assertEqual(phase.ordinal, 3)
        self.assertEqual(phase.suffix, (2,))

    def test_manual_legacy_identity(self) -> None:
        phase = GenesisPhaseKey.create(
            generation=7,
            stream="b",
            hierarchy=((0, 4), (1, 3)),
        )
        self.assertEqual(phase.label, "7-B4C")


if __name__ == "__main__":
    unittest.main()

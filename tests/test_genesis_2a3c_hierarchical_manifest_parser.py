from __future__ import annotations

import unittest

from dev.verification.genesis_manifest import (
    CERTIFIED_BASELINE,
    GenesisManifestError,
    parse_phase,
    validate_entries,
)


class Genesis2A3CHierarchicalManifestParserTests(unittest.TestCase):
    def test_existing_numeric_phase_remains_compatible(self) -> None:
        phase = parse_phase("dev/verify_genesis_4a5.sh")
        self.assertEqual(phase.ordinal, 5)
        self.assertEqual(phase.label, "4-A5")

    def test_existing_alphabetic_leaf_remains_compatible(self) -> None:
        phase = parse_phase("dev/verify_genesis_2a3b.sh")
        self.assertEqual(phase.hierarchy, ((0, 3), (1, 2)))
        self.assertEqual(phase.label, "2-A3B")

    def test_nested_alpha_numeric_phase_is_parseable(self) -> None:
        phase = parse_phase("dev/verify_genesis_4a6a1.sh")
        self.assertEqual(phase.hierarchy, ((0, 6), (1, 1), (0, 1)))
        self.assertEqual(phase.label, "4-A6.A.1")

    def test_deeper_hierarchy_is_parseable(self) -> None:
        phase = parse_phase("dev/verify_genesis_10c3a4b2.sh")
        self.assertEqual(
            phase.hierarchy,
            ((0, 3), (1, 1), (0, 4), (1, 2), (0, 2)),
        )

    def test_numeric_ordinal_is_not_silently_reinterpreted(self) -> None:
        phase = parse_phase("dev/verify_genesis_4a62.sh")
        self.assertEqual(phase.ordinal, 62)
        self.assertEqual(phase.label, "4-A62")

    def test_hierarchical_order_is_deterministic(self) -> None:
        parent = parse_phase("dev/verify_genesis_4a6.sh")
        child = parse_phase("dev/verify_genesis_4a6a1.sh")
        later = parse_phase("dev/verify_genesis_4a62.sh")
        self.assertLess(parent, child)
        self.assertLess(child, later)

    def test_invalid_paths_are_rejected(self) -> None:
        invalid = (
            "dev/verify_genesis_4aa1.sh",
            "dev/verify_genesis_04a1.sh",
            "dev/verify_genesis_4A1.sh",
            "verify_genesis_4a6a1.sh",
        )
        for path in invalid:
            with self.subTest(path=path):
                with self.assertRaises(GenesisManifestError):
                    parse_phase(path)

    def test_manifest_accepts_current_problematic_sequence(self) -> None:
        entries = CERTIFIED_BASELINE + (
            "dev/verify_genesis_2a3b.sh",
            "dev/verify_genesis_2a3c.sh",
            "dev/verify_genesis_2a4.sh",
            "dev/verify_genesis_3a1.sh",
            "dev/verify_genesis_3f1.sh",
            "dev/verify_genesis_4a1.sh",
            "dev/verify_genesis_4a6a1.sh",
            "dev/verify_genesis_4a62.sh",
        )
        report = validate_entries(entries)
        self.assertEqual(report.entries[-2].phase.label, "4-A6.A.1")
        self.assertEqual(report.entries[-1].phase.label, "4-A62")

    def test_parser_is_deterministic(self) -> None:
        path = "dev/verify_genesis_12z7c3a9.sh"
        self.assertEqual(parse_phase(path), parse_phase(path))


if __name__ == "__main__":
    unittest.main()

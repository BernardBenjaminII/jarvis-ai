from __future__ import annotations

import unittest

from dev.verification.genesis_manifest import (
    CERTIFIED_BASELINE,
    GenesisManifestError,
    parse_phase,
    validate_entries,
)


class Genesis2A3FHierarchicalRomanSubphaseParserTests(unittest.TestCase):
    def test_viii_a0_1_is_parseable(self) -> None:
        phase = parse_phase("dev/verify_genesis_viii_a0_1.sh")
        self.assertEqual(phase.generation, 8)
        self.assertEqual(phase.stream, "a")
        self.assertEqual(phase.hierarchy, ((0, 0), (0, 1)))
        self.assertEqual(phase.label, "VIII-A0.1")

    def test_multiple_underscore_subphases_are_parseable(self) -> None:
        phase = parse_phase("dev/verify_genesis_ix_c2_14_3.sh")
        self.assertEqual(phase.hierarchy, ((0, 2), (0, 14), (0, 3)))
        self.assertEqual(phase.label, "IX-C2.14.3")

    def test_subphase_may_include_alphabetic_leaf(self) -> None:
        phase = parse_phase("dev/verify_genesis_xii_f1_4c.sh")
        self.assertEqual(phase.hierarchy, ((0, 1), (0, 4), (1, 3)))
        self.assertEqual(phase.label, "XII-F1.4.C")

    def test_existing_roman_generation_namespace_is_unchanged(self) -> None:
        phase = parse_phase("dev/verify_genesis_vii_b0.sh")
        self.assertEqual(phase.hierarchy, ((0, 0),))
        self.assertEqual(phase.label, "VII-B0")

    def test_numeric_namespaces_remain_unchanged(self) -> None:
        self.assertEqual(
            parse_phase("dev/verify_genesis_2a3b.sh").label,
            "2-A3B",
        )
        self.assertEqual(
            parse_phase("dev/verify_genesis_4a6a1.sh").label,
            "4-A6.A.1",
        )

    def test_subphase_order_is_deterministic(self) -> None:
        parent = parse_phase("dev/verify_genesis_viii_a0.sh")
        child_one = parse_phase("dev/verify_genesis_viii_a0_1.sh")
        child_two = parse_phase("dev/verify_genesis_viii_a0_2.sh")
        self.assertLess(parent, child_one)
        self.assertLess(child_one, child_two)

    def test_invalid_subphase_forms_are_rejected(self) -> None:
        invalid = (
            "dev/verify_genesis_viii_a0_.sh",
            "dev/verify_genesis_viii_a0__1.sh",
            "dev/verify_genesis_viii_a0_a1.sh",
            "dev/verify_genesis_viii_a0_01.sh",
            "dev/verify_genesis_viii_a0_0.sh",
        )
        for path in invalid:
            with self.subTest(path=path):
                with self.assertRaises(GenesisManifestError):
                    parse_phase(path)

    def test_current_viii_extension_validates(self) -> None:
        entries = CERTIFIED_BASELINE + (
            "dev/verify_genesis_2a3b.sh",
            "dev/verify_genesis_2a3c.sh",
            "dev/verify_genesis_2a3d.sh",
            "dev/verify_genesis_2a3e.sh",
            "dev/verify_genesis_2a3f.sh",
            "dev/verify_genesis_2a4.sh",
            "dev/verify_genesis_3a1.sh",
            "dev/verify_genesis_4a62.sh",
            "dev/verify_genesis_vii_b0.sh",
            "dev/verify_genesis_viii_a0_1.sh",
        )
        report = validate_entries(entries)
        self.assertEqual(report.entries[-1].phase.label, "VIII-A0.1")

    def test_parser_is_deterministic(self) -> None:
        path = "dev/verify_genesis_xv_d3_12a4_7.sh"
        self.assertEqual(parse_phase(path), parse_phase(path))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from dev.verification.genesis_manifest import (
    GenesisManifestError,
    parse_phase,
    validate_entries,
)


class Genesis2A3GManifestEvolutionRuntimeCampaignTests(unittest.TestCase):
    def test_ix_0_is_parseable(self) -> None:
        phase = parse_phase("dev/verify_genesis_ix_0.sh")
        self.assertEqual(phase.generation, 9)
        self.assertEqual(phase.stream, "z")
        self.assertEqual(phase.hierarchy, ((0, 0),))
        self.assertEqual(phase.label, "IX-Z0")

    def test_future_runtime_campaigns_are_parseable(self) -> None:
        self.assertEqual(
            parse_phase("dev/verify_genesis_x_1.sh").generation,
            10,
        )
        self.assertEqual(
            parse_phase("dev/verify_genesis_xi_2a.sh").hierarchy,
            ((0, 2), (1, 1)),
        )
        self.assertEqual(
            parse_phase("dev/verify_genesis_xii_10_3.sh").hierarchy,
            ((0, 10), (0, 3)),
        )

    def test_existing_roman_stream_names_are_unchanged(self) -> None:
        self.assertEqual(
            parse_phase("dev/verify_genesis_vii_b0.sh").label,
            "VII-B0",
        )
        self.assertEqual(
            parse_phase("dev/verify_genesis_viii_a0_6.sh").label,
            "VIII-A0.6",
        )

    def test_existing_numeric_names_are_unchanged(self) -> None:
        self.assertEqual(
            parse_phase("dev/verify_genesis_2a3f.sh").label,
            "2-A3F",
        )
        self.assertEqual(
            parse_phase("dev/verify_genesis_4a6a1.sh").label,
            "4-A6.A.1",
        )

    def test_runtime_campaign_orders_after_viii(self) -> None:
        self.assertLess(
            parse_phase("dev/verify_genesis_viii_b0.sh"),
            parse_phase("dev/verify_genesis_ix_0.sh"),
        )

    def test_runtime_manifest_extension_validates(self) -> None:
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
            "dev/verify_genesis_vii_b0.sh",
            "dev/verify_genesis_viii_a0_6.sh",
            "dev/verify_genesis_viii_b0.sh",
            "dev/verify_genesis_ix_0.sh",
        )
        report = validate_entries(entries)
        self.assertEqual(
            report.entries[-1].path,
            "dev/verify_genesis_ix_0.sh",
        )

    def test_malformed_runtime_names_are_rejected(self) -> None:
        invalid = (
            "dev/verify_genesis_ix_.sh",
            "dev/verify_genesis_ix_00.sh",
            "dev/verify_genesis_ix__0.sh",
            "dev/verify_genesis_iix_0.sh",
        )
        for path in invalid:
            with self.subTest(path=path):
                with self.assertRaises(GenesisManifestError):
                    parse_phase(path)


if __name__ == "__main__":
    unittest.main()

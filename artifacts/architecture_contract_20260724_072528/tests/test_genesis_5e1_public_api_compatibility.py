from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.engineering import (
    APIExpectation,
    analyze_compatibility,
    build_restoration_plan,
    expectations_from_tests,
    inventory_package,
)


class PublicAPICompatibilityTests(unittest.TestCase):
    def _fixture(self, root: Path) -> None:
        package = root / "core" / "fixture"
        package.mkdir(parents=True)
        (root / "core" / "__init__.py").write_text("", encoding="utf-8")
        (package / "__init__.py").write_text(
            'from .contracts import Present\n\n__all__ = ["Present"]\n',
            encoding="utf-8",
        )
        (package / "contracts.py").write_text(
            "class Present:\n    pass\n\nclass Hidden:\n    pass\n",
            encoding="utf-8",
        )
        tests = root / "tests"
        tests.mkdir()
        (tests / "test_fixture.py").write_text(
            "from core.fixture import Present, Hidden\n",
            encoding="utf-8",
        )

    def test_expectations_are_derived_from_test_imports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root)
            result = expectations_from_tests(root, root / "tests")
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].package, "core.fixture")
            self.assertEqual(result[0].expected_symbols, ("Hidden", "Present"))

    def test_inventory_finds_exports_and_definitions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root)
            result = inventory_package(root, "core.fixture")
            self.assertEqual(
                tuple(item.symbol for item in result.exported_symbols),
                ("Present",),
            )
            self.assertIn(
                "Hidden",
                {item.symbol for item in result.discovered_definitions},
            )

    def test_missing_export_is_classified_and_recommended(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root)
            inventory = inventory_package(root, "core.fixture")
            report = analyze_compatibility(
                (
                    APIExpectation(
                        package="core.fixture",
                        expected_symbols=("Present", "Hidden"),
                    ),
                ),
                (inventory,),
            )
            self.assertEqual(report.compatibility_score, 0.5)
            self.assertEqual(len(report.findings), 1)
            self.assertEqual(report.findings[0].finding_type, "missing_export")

            plan = build_restoration_plan(report)
            self.assertEqual(plan[0].action, "restore_public_export")
            self.assertEqual(plan[0].source_module, "core.fixture.contracts")
            self.assertEqual(plan[0].target_file, "core/fixture/__init__.py")

    def test_report_fingerprint_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root)
            inventory = inventory_package(root, "core.fixture")
            expectations = (
                APIExpectation("core.fixture", ("Present", "Hidden")),
            )
            first = analyze_compatibility(expectations, (inventory,))
            second = analyze_compatibility(expectations, (inventory,))
            self.assertEqual(first.fingerprint(), second.fingerprint())


if __name__ == "__main__":
    unittest.main()

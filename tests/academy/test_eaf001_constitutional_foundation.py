from pathlib import Path
import unittest

from core.academy import (
    AcademyStatus,
    DepartmentContract,
    ExecutiveAcademyBaseline,
    JurisdictionContract,
    StaticRegistry,
)


ROOT = Path(__file__).resolve().parents[2]


class EAF001ConstitutionalFoundationTests(unittest.TestCase):
    def test_constitution_exists(self) -> None:
        path = ROOT / "docs/executive_academy/EXECUTIVE_ACADEMY_CONSTITUTION.md"
        self.assertTrue(path.is_file())

    def test_expected_department_documents_exist(self) -> None:
        department_dir = ROOT / "docs/executive_academy/departments"
        self.assertEqual(12, len(tuple(department_dir.glob("*.md"))))

    def test_expected_jurisdiction_documents_exist(self) -> None:
        jurisdiction_dir = ROOT / "docs/executive_academy/jurisdictions"
        jurisdiction_files = tuple(
            path for path in jurisdiction_dir.glob("*.md")
            if path.name != "README.md"
        )
        self.assertEqual(11, len(jurisdiction_files))

    def test_baseline_is_dormant(self) -> None:
        baseline = ExecutiveAcademyBaseline(
            version="0.1.0",
            phase="EAF-001",
            departments=(
                DepartmentContract(
                    department_id="department.knowledge",
                    name="Knowledge",
                    status=AcademyStatus.PLANNED,
                ),
            ),
            jurisdictions=(
                JurisdictionContract(
                    jurisdiction_id="jurisdiction.morocco",
                    name="Morocco",
                ),
            ),
        )
        self.assertFalse(baseline.runtime_enabled)

    def test_static_registry_is_deterministic(self) -> None:
        registry = StaticRegistry.create(
            [
                ("department.knowledge", "Knowledge"),
                ("department.engineering", "Engineering"),
            ]
        )
        self.assertEqual(
            ("department.engineering", "department.knowledge"),
            registry.identifiers(),
        )


if __name__ == "__main__":
    unittest.main()

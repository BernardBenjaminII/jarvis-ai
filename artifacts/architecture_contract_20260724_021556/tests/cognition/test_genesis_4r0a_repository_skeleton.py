"""Tests for the Genesis IV permanent cognition repository structure."""

from __future__ import annotations

import importlib
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
COGNITION_ROOT = PROJECT_ROOT / "core" / "cognition"

PERMANENT_PACKAGES = (
    "common",
    "layers",
    "layers.observation",
    "layers.evidence",
    "layers.claims",
    "layers.relationships",
    "layers.hypotheses",
    "layers.interpretation",
    "layers.reasoning",
    "layers.justification",
)

PLACEHOLDER_PACKAGES = (
    "common",
    "layers",
    "layers.evidence",
    "layers.claims",
    "layers.relationships",
    "layers.hypotheses",
    "layers.interpretation",
    "layers.reasoning",
    "layers.justification",
)

IMPLEMENTED_PACKAGE_EXPORTS = {
    "layers.observation": (
        "ObservationDirector",
        "ObservationInput",
        "ObservationRecord",
        "ObservationRegistry",
        "ObservationValidator",
    ),
}

EXISTING_PRODUCTION_MODULES = (
    "contracts.py",
    "errors.py",
    "normalization.py",
    "serialization.py",
    "confidence.py",
    "extraction.py",
    "observation.py",
    "provenance.py",
    "evidence.py",
    "evidence_chain.py",
    "evidence_validation.py",
    "claim.py",
    "claim_construction.py",
    "claim_validation.py",
)

REPRESENTATIVE_PUBLIC_EXPORTS = (
    "Observation",
    "EvidenceRecord",
    "EvidenceChain",
    "ProvenanceRecord",
    "ClaimRecord",
    "ClaimConstructionEngine",
)


class GenesisIVR0ARepositorySkeletonTests(unittest.TestCase):
    """Protect the permanent cognition architecture across later releases."""

    def test_permanent_package_directories_exist(self) -> None:
        for package_name in PERMANENT_PACKAGES:
            package_path = COGNITION_ROOT.joinpath(
                *package_name.split(".")
            )

            with self.subTest(package=package_name):
                self.assertTrue(
                    package_path.is_dir(),
                    f"Missing permanent cognition package: "
                    f"{package_name}",
                )
                self.assertTrue(
                    (package_path / "__init__.py").is_file(),
                    f"Missing package initializer: {package_name}",
                )

    def test_permanent_packages_are_importable(self) -> None:
        for package_name in PERMANENT_PACKAGES:
            with self.subTest(package=package_name):
                module = importlib.import_module(
                    f"core.cognition.{package_name}"
                )
                self.assertIsNotNone(module)

    def test_unimplemented_packages_have_empty_public_api(self) -> None:
        for package_name in PLACEHOLDER_PACKAGES:
            with self.subTest(package=package_name):
                module = importlib.import_module(
                    f"core.cognition.{package_name}"
                )

                self.assertTrue(
                    hasattr(module, "__all__"),
                    f"Placeholder package lacks __all__: "
                    f"{package_name}",
                )
                self.assertEqual(
                    tuple(module.__all__),
                    (),
                    f"Placeholder package unexpectedly exports "
                    f"symbols: {package_name}",
                )

    def test_implemented_packages_expose_required_public_api(self) -> None:
        for package_name, required_exports in (
            IMPLEMENTED_PACKAGE_EXPORTS.items()
        ):
            with self.subTest(package=package_name):
                module = importlib.import_module(
                    f"core.cognition.{package_name}"
                )

                self.assertTrue(
                    hasattr(module, "__all__"),
                    f"Implemented package lacks __all__: "
                    f"{package_name}",
                )

                public_exports = tuple(module.__all__)
                missing = [
                    export_name
                    for export_name in required_exports
                    if export_name not in public_exports
                    or not hasattr(module, export_name)
                ]

                self.assertEqual(
                    missing,
                    [],
                    f"Implemented package is missing required "
                    f"exports: {package_name}",
                )

    def test_existing_production_modules_have_not_moved(self) -> None:
        for module_name in EXISTING_PRODUCTION_MODULES:
            with self.subTest(module=module_name):
                self.assertTrue(
                    (COGNITION_ROOT / module_name).is_file(),
                    f"Existing production module moved too early: "
                    f"{module_name}",
                )

    def test_existing_cognition_facade_is_importable(self) -> None:
        cognition = importlib.import_module("core.cognition")

        self.assertIsNotNone(cognition)
        self.assertTrue(hasattr(cognition, "__all__"))
        self.assertTrue(tuple(cognition.__all__))

    def test_representative_public_exports_remain_available(self) -> None:
        cognition = importlib.import_module("core.cognition")

        missing = [
            export_name
            for export_name in REPRESENTATIVE_PUBLIC_EXPORTS
            if not hasattr(cognition, export_name)
        ]

        self.assertEqual(missing, [])

    def test_architecture_constitution_exists(self) -> None:
        self.assertTrue(
            (PROJECT_ROOT / "ARCHITECTURE.md").is_file()
        )

    def test_cognition_overview_exists(self) -> None:
        self.assertTrue(
            (
                PROJECT_ROOT
                / "docs/architecture/cognition/00_overview.md"
            ).is_file()
        )

    def test_adr_0020_exists(self) -> None:
        self.assertTrue(
            (
                PROJECT_ROOT
                / "docs/decisions/"
                "ADR-0020-genesis-iv-cognition-"
                "architecture-constitution.md"
            ).is_file()
        )


if __name__ == "__main__":
    unittest.main()

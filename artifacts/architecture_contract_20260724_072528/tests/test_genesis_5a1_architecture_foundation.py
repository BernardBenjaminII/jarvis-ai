from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.architecture import (
    ArchitectureFinding,
    ArchitectureSnapshot,
    ArchitectureValidationError,
    CertificationRecord,
    CertificationStatus,
    DependencyEdge,
    FindingCategory,
    FindingSeverity,
    MigrationPlan,
    MigrationStatus,
    MigrationStep,
    ModuleDefinition,
    OwnershipDeclaration,
    OwnershipStatus,
    PublicSymbol,
    SubsystemDefinition,
    SymbolKind,
    architecture_fingerprint,
    canonical_json,
    canonicalize,
    file_fingerprint,
)


class ArchitectureFoundationTests(unittest.TestCase):
    def test_public_symbol_is_immutable(self) -> None:
        symbol = PublicSymbol(
            name="EvidenceRecord",
            qualified_name="core.evidence.EvidenceRecord",
            kind=SymbolKind.CLASS,
            module="core.evidence",
        )
        with self.assertRaises((AttributeError, TypeError)):
            symbol.name = "Changed"  # type: ignore[misc]

    def test_metadata_is_immutable(self) -> None:
        symbol = PublicSymbol(
            name="EvidenceRecord",
            qualified_name="core.evidence.EvidenceRecord",
            kind=SymbolKind.CLASS,
            module="core.evidence",
            metadata={"owner": "evidence"},
        )
        with self.assertRaises(TypeError):
            symbol.metadata["owner"] = "reasoning"  # type: ignore[index]

    def test_canonical_json_is_deterministic(self) -> None:
        left = {"b": 2, "a": {"z", "x", "y"}}
        right = {"a": {"y", "z", "x"}, "b": 2}
        self.assertEqual(canonical_json(left), canonical_json(right))

    def test_fingerprint_is_deterministic(self) -> None:
        first = architecture_fingerprint({"b": 2, "a": 1})
        second = architecture_fingerprint({"a": 1, "b": 2})
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_contract_fingerprint_is_stable(self) -> None:
        module = ModuleDefinition(
            path="core/evidence/contracts.py",
            module="core.evidence.contracts",
            line_count=100,
            imports=("typing", "dataclasses", "typing"),
            public_exports=("EvidenceRecord", "Proposition"),
        )
        self.assertEqual(module.fingerprint(), module.fingerprint())

    def test_subsystem_dependency_overlap_is_rejected(self) -> None:
        with self.assertRaises(ArchitectureValidationError):
            SubsystemDefinition(
                subsystem_id="evidence",
                name="Evidence",
                canonical_package="core.evidence",
                allowed_dependencies=("core.reasoning",),
                forbidden_dependencies=("core.reasoning",),
            )

    def test_ownership_cannot_name_owner_as_legacy(self) -> None:
        with self.assertRaises(ArchitectureValidationError):
            OwnershipDeclaration(
                concept="EvidenceRecord",
                canonical_owner="core.evidence",
                legacy_owners=("core.evidence",),
            )

    def test_dependency_self_edge_is_rejected(self) -> None:
        with self.assertRaises(ArchitectureValidationError):
            DependencyEdge(source="core.evidence", target="core.evidence")

    def test_migration_steps_are_sorted(self) -> None:
        plan = MigrationPlan(
            plan_id="evidence-canonicalization",
            subject="core.reasoning.evidence",
            target_owner="core.evidence",
            status=MigrationStatus.PLANNED,
            steps=(
                MigrationStep(order=2, step_id="verify", description="Verify"),
                MigrationStep(order=1, step_id="audit", description="Audit"),
            ),
        )
        self.assertEqual([step.order for step in plan.steps], [1, 2])

    def test_duplicate_migration_orders_are_rejected(self) -> None:
        with self.assertRaises(ArchitectureValidationError):
            MigrationPlan(
                plan_id="invalid",
                subject="legacy",
                target_owner="canonical",
                status=MigrationStatus.PLANNED,
                steps=(
                    MigrationStep(order=1, step_id="a", description="A"),
                    MigrationStep(order=1, step_id="b", description="B"),
                ),
            )

    def test_passed_certification_cannot_have_failures(self) -> None:
        with self.assertRaises(ArchitectureValidationError):
            CertificationRecord(
                release_id="genesis-v-a1",
                status=CertificationStatus.PASSED,
                checks_passed=10,
                checks_failed=1,
            )

    def test_snapshot_serializes_and_fingerprints(self) -> None:
        snapshot = ArchitectureSnapshot(
            snapshot_id="fixture",
            repository_root="/repo",
            branch="feature/test",
            commit="abc123",
            modules=(
                ModuleDefinition(
                    path="core/evidence/contracts.py",
                    module="core.evidence.contracts",
                    line_count=50,
                    symbols=(
                        PublicSymbol(
                            name="EvidenceRecord",
                            qualified_name="core.evidence.EvidenceRecord",
                            kind=SymbolKind.CLASS,
                            module="core.evidence.contracts",
                            exported=True,
                        ),
                    ),
                ),
            ),
            ownership=(
                OwnershipDeclaration(
                    concept="EvidenceRecord",
                    canonical_owner="core.evidence",
                    status=OwnershipStatus.CANONICAL,
                ),
            ),
            findings=(
                ArchitectureFinding(
                    finding_id="duplicate-evidence-record",
                    category=FindingCategory.DUPLICATION,
                    severity=FindingSeverity.WARNING,
                    title="Duplicate EvidenceRecord",
                    description="A legacy duplicate remains.",
                ),
            ),
        )
        payload = json.loads(snapshot.to_canonical_json())
        self.assertEqual(payload["snapshot_id"], "fixture")
        self.assertEqual(len(snapshot.fingerprint()), 64)

    def test_file_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.txt"
            path.write_text("architecture\n", encoding="utf-8")
            self.assertEqual(file_fingerprint(path), file_fingerprint(path))

    def test_canonicalize_rejects_unsupported_type(self) -> None:
        with self.assertRaises(Exception):
            canonicalize(object())


if __name__ == "__main__":
    unittest.main()

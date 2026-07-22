#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

if [ ! -f core/engineering/constitution.py ]; then
    echo "ERROR: Genesis V-E0 Engineering OS Foundation is required."
    exit 1
fi

mkdir -p \
    core/engineering \
    docs/engineering \
    docs/audits \
    tests \
    dev/verification \
    dev/verification/manifests \
    .artifacts/engineering

cat > core/engineering/api_inventory.py <<'PYEOF'
"""Read-only, deterministic public API inventory for Python packages."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.architecture import architecture_fingerprint, canonical_json

from .errors import EngineeringValidationError


def _text(value: str, name: str) -> str:
    value = value.strip()
    if not value:
        raise EngineeringValidationError(f"{name} must not be empty")
    return value


@dataclass(frozen=True, slots=True)
class PublicSymbol:
    package: str
    symbol: str
    declared_in: str
    implementation_candidates: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "package", _text(self.package, "package"))
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol"))
        object.__setattr__(self, "declared_in", _text(self.declared_in, "declared_in"))
        object.__setattr__(
            self,
            "implementation_candidates",
            tuple(sorted(set(self.implementation_candidates))),
        )


@dataclass(frozen=True, slots=True)
class PackageAPIInventory:
    package: str
    package_path: str
    exported_symbols: tuple[PublicSymbol, ...]
    discovered_definitions: tuple[PublicSymbol, ...]
    parse_findings: tuple[str, ...] = ()

    def to_canonical_json(self) -> str:
        return canonical_json(self)

    def fingerprint(self) -> str:
        return architecture_fingerprint(self)


def _module_name(root: Path, file_path: Path) -> str:
    relative = file_path.relative_to(root).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _read_tree(path: Path) -> ast.Module:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        raise EngineeringValidationError(f"Unable to parse {path}: {exc}") from exc


def _extract_literal_all(tree: ast.Module) -> tuple[str, ...]:
    exports: set[str] = set()
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(target, ast.Name) and target.id == "__all__" for target in targets):
            continue
        value = node.value
        if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            for element in value.elts:
                if isinstance(element, ast.Constant) and isinstance(element.value, str):
                    exports.add(element.value)
    return tuple(sorted(exports))


def _extract_imported_names(tree: ast.Module) -> dict[str, str]:
    imported: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                if alias.name == "*":
                    continue
                public_name = alias.asname or alias.name
                imported[public_name] = module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                public_name = alias.asname or alias.name.split(".")[0]
                imported[public_name] = alias.name
    return imported


def _extract_definitions(tree: ast.Module) -> tuple[str, ...]:
    definitions: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                definitions.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    definitions.add(target.id)
    return tuple(sorted(definitions))


def discover_definition_index(project_root: Path, package_root: Path) -> dict[str, tuple[str, ...]]:
    index: dict[str, set[str]] = {}
    for file_path in sorted(package_root.rglob("*.py")):
        tree = _read_tree(file_path)
        module = _module_name(project_root, file_path)
        for symbol in _extract_definitions(tree):
            index.setdefault(symbol, set()).add(module)
    return {
        symbol: tuple(sorted(modules))
        for symbol, modules in sorted(index.items())
    }


def inventory_package(project_root: Path, package: str) -> PackageAPIInventory:
    project_root = project_root.resolve()
    package_root = project_root.joinpath(*package.split("."))
    init_path = package_root / "__init__.py"

    if not package_root.is_dir():
        raise EngineeringValidationError(f"Package directory not found: {package_root}")
    if not init_path.is_file():
        raise EngineeringValidationError(f"Package initializer not found: {init_path}")

    findings: list[str] = []
    tree = _read_tree(init_path)
    explicit_all = _extract_literal_all(tree)
    imported_names = _extract_imported_names(tree)
    definition_index = discover_definition_index(project_root, package_root)

    if explicit_all:
        public_names = explicit_all
    else:
        public_names = tuple(sorted(
            name for name in imported_names
            if not name.startswith("_")
        ))
        findings.append("Package has no literal __all__; inventory derived from imports.")

    exported = tuple(
        PublicSymbol(
            package=package,
            symbol=name,
            declared_in=f"{package}.__init__",
            implementation_candidates=definition_index.get(name, ()),
        )
        for name in public_names
    )

    discovered = tuple(
        PublicSymbol(
            package=package,
            symbol=symbol,
            declared_in=modules[0],
            implementation_candidates=modules,
        )
        for symbol, modules in sorted(definition_index.items())
    )

    return PackageAPIInventory(
        package=package,
        package_path=str(package_root.relative_to(project_root)),
        exported_symbols=exported,
        discovered_definitions=discovered,
        parse_findings=tuple(sorted(findings)),
    )


def inventory_packages(
    project_root: Path,
    packages: Iterable[str],
) -> tuple[PackageAPIInventory, ...]:
    return tuple(
        inventory_package(project_root, package)
        for package in sorted(set(packages))
    )


__all__ = [
    "PackageAPIInventory",
    "PublicSymbol",
    "discover_definition_index",
    "inventory_package",
    "inventory_packages",
]
PYEOF

cat > core/engineering/compatibility.py <<'PYEOF'
"""Deterministic expected-versus-observed public API compatibility analysis."""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from core.architecture import architecture_fingerprint, canonical_json

from .api_inventory import PackageAPIInventory
from .errors import EngineeringValidationError


@dataclass(frozen=True, slots=True)
class APIExpectation:
    package: str
    expected_symbols: tuple[str, ...]
    sources: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "package", self.package.strip())
        object.__setattr__(
            self, "expected_symbols", tuple(sorted(set(self.expected_symbols)))
        )
        object.__setattr__(self, "sources", tuple(sorted(set(self.sources))))
        if not self.package:
            raise EngineeringValidationError("package must not be empty")


@dataclass(frozen=True, slots=True)
class CompatibilityFinding:
    package: str
    symbol: str
    finding_type: str
    severity: str
    explanation: str
    implementation_candidates: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "implementation_candidates",
            tuple(sorted(set(self.implementation_candidates))),
        )


@dataclass(frozen=True, slots=True)
class CompatibilityReport:
    expectations: tuple[APIExpectation, ...]
    inventories: tuple[PackageAPIInventory, ...]
    findings: tuple[CompatibilityFinding, ...]
    compatibility_score: float

    def to_canonical_json(self) -> str:
        return canonical_json(self)

    def fingerprint(self) -> str:
        return architecture_fingerprint(self)


def expectations_from_tests(
    project_root: Path,
    tests_root: Path,
    package_prefix: str = "core.",
) -> tuple[APIExpectation, ...]:
    project_root = project_root.resolve()
    collected: dict[str, set[str]] = {}
    sources: dict[str, set[str]] = {}

    for path in sorted(tests_root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError):
            continue

        relative = str(path.relative_to(project_root))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            module = node.module or ""
            if not module.startswith(package_prefix):
                continue
            symbols = {
                alias.name
                for alias in node.names
                if alias.name != "*"
            }
            if not symbols:
                continue
            collected.setdefault(module, set()).update(symbols)
            sources.setdefault(module, set()).add(relative)

    return tuple(
        APIExpectation(
            package=package,
            expected_symbols=tuple(sorted(symbols)),
            sources=tuple(sorted(sources.get(package, set()))),
        )
        for package, symbols in sorted(collected.items())
    )


def save_expectations(
    expectations: tuple[APIExpectation, ...],
    path: Path,
) -> None:
    payload = {
        "schema_version": 1,
        "expectations": [
            {
                "package": item.package,
                "expected_symbols": list(item.expected_symbols),
                "sources": list(item.sources),
            }
            for item in expectations
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_expectations(path: Path) -> tuple[APIExpectation, ...]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EngineeringValidationError(f"Invalid expectation manifest {path}: {exc}") from exc

    return tuple(
        APIExpectation(
            package=item["package"],
            expected_symbols=tuple(item.get("expected_symbols", ())),
            sources=tuple(item.get("sources", ())),
        )
        for item in payload.get("expectations", ())
    )


def analyze_compatibility(
    expectations: tuple[APIExpectation, ...],
    inventories: tuple[PackageAPIInventory, ...],
) -> CompatibilityReport:
    by_package: Mapping[str, PackageAPIInventory] = {
        item.package: item for item in inventories
    }
    findings: list[CompatibilityFinding] = []
    expected_total = 0
    compatible_total = 0

    for expectation in expectations:
        expected_total += len(expectation.expected_symbols)
        inventory = by_package.get(expectation.package)

        if inventory is None:
            for symbol in expectation.expected_symbols:
                findings.append(
                    CompatibilityFinding(
                        package=expectation.package,
                        symbol=symbol,
                        finding_type="missing_package",
                        severity="critical",
                        explanation="Expected package could not be inventoried.",
                    )
                )
            continue

        exported = {item.symbol for item in inventory.exported_symbols}
        definitions = {
            item.symbol: item.implementation_candidates
            for item in inventory.discovered_definitions
        }

        for symbol in expectation.expected_symbols:
            if symbol in exported:
                compatible_total += 1
                continue

            candidates = definitions.get(symbol, ())
            if candidates:
                finding_type = "missing_export"
                severity = "high"
                explanation = (
                    "The symbol exists inside the package but is absent from the "
                    "package's certified public surface."
                )
            else:
                finding_type = "missing_symbol"
                severity = "critical"
                explanation = (
                    "The expected symbol is absent from both the public surface "
                    "and discovered package definitions."
                )

            findings.append(
                CompatibilityFinding(
                    package=expectation.package,
                    symbol=symbol,
                    finding_type=finding_type,
                    severity=severity,
                    explanation=explanation,
                    implementation_candidates=candidates,
                )
            )

    score = 1.0 if expected_total == 0 else compatible_total / expected_total

    return CompatibilityReport(
        expectations=tuple(sorted(expectations, key=lambda item: item.package)),
        inventories=tuple(sorted(inventories, key=lambda item: item.package)),
        findings=tuple(sorted(
            findings,
            key=lambda item: (
                item.package,
                item.symbol,
                item.finding_type,
            ),
        )),
        compatibility_score=round(score, 6),
    )


__all__ = [
    "APIExpectation",
    "CompatibilityFinding",
    "CompatibilityReport",
    "analyze_compatibility",
    "expectations_from_tests",
    "load_expectations",
    "save_expectations",
]
PYEOF

cat > core/engineering/restoration.py <<'PYEOF'
"""Evidence-backed, read-only public API restoration recommendations."""

from __future__ import annotations

from dataclasses import dataclass

from core.architecture import architecture_fingerprint, canonical_json

from .compatibility import CompatibilityFinding, CompatibilityReport


@dataclass(frozen=True, slots=True)
class RestorationRecommendation:
    package: str
    symbol: str
    action: str
    target_file: str
    source_module: str | None
    rationale: str
    confidence: float

    def to_canonical_json(self) -> str:
        return canonical_json(self)

    def fingerprint(self) -> str:
        return architecture_fingerprint(self)


def recommendation_for_finding(
    finding: CompatibilityFinding,
) -> RestorationRecommendation:
    target_file = finding.package.replace(".", "/") + "/__init__.py"

    if finding.finding_type == "missing_export" and finding.implementation_candidates:
        source_module = finding.implementation_candidates[0]
        action = "restore_public_export"
        rationale = (
            f"Expose {finding.symbol} from {source_module} through "
            f"{finding.package} without duplicating implementation."
        )
        confidence = 0.99 if len(finding.implementation_candidates) == 1 else 0.82
    elif finding.finding_type == "missing_symbol":
        source_module = None
        action = "investigate_removed_or_renamed_symbol"
        rationale = (
            "No implementation candidate was discovered. Review history, migration "
            "documents, and certified contracts before changing source."
        )
        confidence = 0.55
    else:
        source_module = None
        action = "investigate_missing_package"
        rationale = (
            "The expected package is unavailable. Determine whether the package moved, "
            "was retired, or failed to install before restoration."
        )
        confidence = 0.45

    return RestorationRecommendation(
        package=finding.package,
        symbol=finding.symbol,
        action=action,
        target_file=target_file,
        source_module=source_module,
        rationale=rationale,
        confidence=confidence,
    )


def build_restoration_plan(
    report: CompatibilityReport,
) -> tuple[RestorationRecommendation, ...]:
    return tuple(
        recommendation_for_finding(finding)
        for finding in report.findings
    )


__all__ = [
    "RestorationRecommendation",
    "build_restoration_plan",
    "recommendation_for_finding",
]
PYEOF

cat > core/engineering/reporting.py <<'PYEOF'
"""Human-readable Engineering OS reporting."""

from __future__ import annotations

from pathlib import Path

from .compatibility import CompatibilityReport
from .restoration import RestorationRecommendation


def render_compatibility_markdown(
    report: CompatibilityReport,
    recommendations: tuple[RestorationRecommendation, ...],
) -> str:
    lines = [
        "# Public API Compatibility Report",
        "",
        f"**Compatibility score:** {report.compatibility_score:.2%}",
        f"**Report fingerprint:** `{report.fingerprint()}`",
        f"**Expected packages:** {len(report.expectations)}",
        f"**Findings:** {len(report.findings)}",
        "",
        "## Certification Result",
        "",
        "PASS" if not report.findings else "RESTORATION REQUIRED",
        "",
        "## Findings",
        "",
    ]

    if not report.findings:
        lines.append("No public API compatibility regressions were detected.")
    else:
        lines.extend([
            "| Package | Symbol | Type | Severity |",
            "|---|---|---|---|",
        ])
        for finding in report.findings:
            lines.append(
                f"| `{finding.package}` | `{finding.symbol}` | "
                f"{finding.finding_type} | {finding.severity} |"
            )

    lines.extend(["", "## Restoration Recommendations", ""])

    if not recommendations:
        lines.append("No restoration actions are required.")
    else:
        for recommendation in recommendations:
            lines.extend([
                f"### `{recommendation.package}.{recommendation.symbol}`",
                "",
                f"- **Action:** `{recommendation.action}`",
                f"- **Target:** `{recommendation.target_file}`",
                f"- **Source:** `{recommendation.source_module or 'not discovered'}`",
                f"- **Confidence:** {recommendation.confidence:.3f}",
                f"- **Rationale:** {recommendation.rationale}",
                "",
            ])

    lines.extend([
        "## Engineering Boundary",
        "",
        "This report is advisory. No source files were modified.",
        "",
    ])
    return "\n".join(lines)


def write_compatibility_report(
    report: CompatibilityReport,
    recommendations: tuple[RestorationRecommendation, ...],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_compatibility_markdown(report, recommendations),
        encoding="utf-8",
    )


__all__ = [
    "render_compatibility_markdown",
    "write_compatibility_report",
]
PYEOF

cat > core/engineering/cli.py <<'PYEOF'
"""Command-line interface for Engineering OS compatibility analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .api_inventory import inventory_packages
from .compatibility import (
    analyze_compatibility,
    expectations_from_tests,
    load_expectations,
    save_expectations,
)
from .reporting import write_compatibility_report
from .restoration import build_restoration_plan


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jarvis-engineering",
        description="JARVIS Engineering OS read-only compatibility tooling.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap = subparsers.add_parser(
        "bootstrap-manifest",
        help="Derive expected public imports from test source.",
    )
    bootstrap.add_argument("--project-root", default=".")
    bootstrap.add_argument("--tests-root", default="tests")
    bootstrap.add_argument(
        "--output",
        default="dev/verification/manifests/test_public_api_expectations.json",
    )
    bootstrap.add_argument("--package-prefix", default="core.")

    analyze = subparsers.add_parser(
        "analyze",
        help="Compare an expectation manifest with observed package exports.",
    )
    analyze.add_argument("--project-root", default=".")
    analyze.add_argument(
        "--manifest",
        default="dev/verification/manifests/test_public_api_expectations.json",
    )
    analyze.add_argument(
        "--json-output",
        default=".artifacts/engineering/public_api_compatibility.json",
    )
    analyze.add_argument(
        "--report-output",
        default="docs/audits/public_api_compatibility_report.md",
    )
    return parser


def _bootstrap(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    tests = root / args.tests_root
    output = root / args.output
    expectations = expectations_from_tests(
        project_root=root,
        tests_root=tests,
        package_prefix=args.package_prefix,
    )
    save_expectations(expectations, output)
    print(f"Manifest written: {output}")
    print(f"Packages: {len(expectations)}")
    print(f"Symbols: {sum(len(item.expected_symbols) for item in expectations)}")
    return 0


def _analyze(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    manifest_path = root / args.manifest
    expectations = load_expectations(manifest_path)
    packages = tuple(item.package for item in expectations)

    inventories = inventory_packages(root, packages)
    report = analyze_compatibility(expectations, inventories)
    recommendations = build_restoration_plan(report)

    json_output = root / args.json_output
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(
        json.dumps(
            {
                "compatibility_score": report.compatibility_score,
                "fingerprint": report.fingerprint(),
                "findings": [
                    {
                        "package": item.package,
                        "symbol": item.symbol,
                        "finding_type": item.finding_type,
                        "severity": item.severity,
                        "explanation": item.explanation,
                        "implementation_candidates": list(
                            item.implementation_candidates
                        ),
                    }
                    for item in report.findings
                ],
                "recommendations": [
                    {
                        "package": item.package,
                        "symbol": item.symbol,
                        "action": item.action,
                        "target_file": item.target_file,
                        "source_module": item.source_module,
                        "rationale": item.rationale,
                        "confidence": item.confidence,
                    }
                    for item in recommendations
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    report_output = root / args.report_output
    write_compatibility_report(report, recommendations, report_output)

    print(f"Compatibility score: {report.compatibility_score:.2%}")
    print(f"Findings: {len(report.findings)}")
    print(f"JSON evidence: {json_output}")
    print(f"Markdown report: {report_output}")
    return 0 if not report.findings else 2


def main() -> int:
    args = _parser().parse_args()
    if args.command == "bootstrap-manifest":
        return _bootstrap(args)
    if args.command == "analyze":
        return _analyze(args)
    raise RuntimeError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
PYEOF

cat > core/engineering/__init__.py <<'PYEOF'
"""Public API for the JARVIS Engineering Operating System."""

from .api_inventory import (
    PackageAPIInventory,
    PublicSymbol,
    discover_definition_index,
    inventory_package,
    inventory_packages,
)
from .compatibility import (
    APIExpectation,
    CompatibilityFinding,
    CompatibilityReport,
    analyze_compatibility,
    expectations_from_tests,
    load_expectations,
    save_expectations,
)
from .constitution import ENGINEERING_CONSTITUTION, constitution_fingerprint
from .contracts import (
    ChangeProposal,
    EngineeringAssessment,
    EngineeringContract,
    EngineeringGate,
    EngineeringPrinciple,
    GovernanceDecision,
    VerificationEvidence,
)
from .enums import (
    ChangeKind,
    ChangeRisk,
    DecisionStatus,
    EvidenceStatus,
    GateStatus,
    StableStringEnum,
    VerificationKind,
)
from .errors import (
    EngineeringError,
    EngineeringEvidenceError,
    EngineeringGovernanceError,
    EngineeringValidationError,
)
from .reporting import (
    render_compatibility_markdown,
    write_compatibility_report,
)
from .restoration import (
    RestorationRecommendation,
    build_restoration_plan,
    recommendation_for_finding,
)

__all__ = [
    "APIExpectation",
    "ENGINEERING_CONSTITUTION",
    "ChangeKind",
    "ChangeProposal",
    "ChangeRisk",
    "CompatibilityFinding",
    "CompatibilityReport",
    "DecisionStatus",
    "EngineeringAssessment",
    "EngineeringContract",
    "EngineeringError",
    "EngineeringEvidenceError",
    "EngineeringGate",
    "EngineeringGovernanceError",
    "EngineeringPrinciple",
    "EngineeringValidationError",
    "EvidenceStatus",
    "GateStatus",
    "GovernanceDecision",
    "PackageAPIInventory",
    "PublicSymbol",
    "RestorationRecommendation",
    "StableStringEnum",
    "VerificationEvidence",
    "VerificationKind",
    "analyze_compatibility",
    "build_restoration_plan",
    "constitution_fingerprint",
    "discover_definition_index",
    "expectations_from_tests",
    "inventory_package",
    "inventory_packages",
    "load_expectations",
    "recommendation_for_finding",
    "render_compatibility_markdown",
    "save_expectations",
    "write_compatibility_report",
]
PYEOF

cat > docs/engineering/genesis_v_e1_public_api_compatibility.md <<'EOF'
# Genesis V-E1 — Public API Compatibility Intelligence

## Mission

Give the Engineering OS a deterministic, read-only ability to:

- derive public API expectations from tests;
- inventory package exports without importing runtime modules;
- locate candidate implementations;
- classify compatibility regressions;
- recommend the smallest restoration;
- generate durable engineering evidence.

## Safety Model

V-E1 performs static AST analysis. It does not:

- import analyzed runtime packages;
- modify source;
- write Git state;
- apply recommendations;
- approve migrations;
- delete implementations.

Generated manifests and reports are engineering evidence, not autonomous authority.

## Workflow

```bash
python -m core.engineering.cli bootstrap-manifest
python -m core.engineering.cli analyze
```

The analyzer returns:

- exit code `0` when compatible;
- exit code `2` when restoration is required;
- exit code `1` for an execution failure.

An exit code of `2` is a successful analysis with compatibility findings.

## Produced Evidence

```text
dev/verification/manifests/test_public_api_expectations.json
.artifacts/engineering/public_api_compatibility.json
docs/audits/public_api_compatibility_report.md
```

## Next Step

A human reviews the report. Approved missing exports are then restored through
a separate Evolution Pack with regression verification and rollback evidence.
EOF

cat > tests/test_genesis_5e1_public_api_compatibility.py <<'PYEOF'
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
PYEOF

cat > dev/verification/verify_genesis_5e1_public_api_compatibility.py <<'PYEOF'
#!/usr/bin/env python3
"""Verify Genesis V-E1 Public API Compatibility Intelligence."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def check(condition: bool, label: str) -> int:
    print(f"[{'PASS' if condition else 'FAIL'}] {label}")
    return 0 if condition else 1


def main() -> int:
    failures = 0

    required = (
        ROOT / "core/engineering/api_inventory.py",
        ROOT / "core/engineering/compatibility.py",
        ROOT / "core/engineering/restoration.py",
        ROOT / "core/engineering/reporting.py",
        ROOT / "core/engineering/cli.py",
        ROOT / "docs/engineering/genesis_v_e1_public_api_compatibility.md",
        ROOT / "tests/test_genesis_5e1_public_api_compatibility.py",
    )
    failures += check(all(path.is_file() for path in required), "V-E1 required files")

    compile_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            "core/engineering",
            "tests/test_genesis_5e1_public_api_compatibility.py",
        ],
        cwd=ROOT,
        check=False,
    )
    failures += check(compile_result.returncode == 0, "V-E1 compilation")

    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            ROOT / "core/engineering/api_inventory.py",
            ROOT / "core/engineering/compatibility.py",
            ROOT / "core/engineering/restoration.py",
            ROOT / "core/engineering/reporting.py",
        )
    )
    failures += check("ast.parse" in source, "Static AST inventory")
    failures += check(
        "importlib" not in source
        and "subprocess" not in source
        and "os.system" not in source
        and "requests" not in source,
        "Analyzer has no runtime import, process, or network authority",
    )

    unit_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "-v",
            "tests.test_genesis_5e1_public_api_compatibility",
        ],
        cwd=ROOT,
        check=False,
    )
    failures += check(unit_result.returncode == 0, "V-E1 unit tests")

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        package = root / "core" / "fixture"
        tests = root / "tests"
        package.mkdir(parents=True)
        tests.mkdir()
        (root / "core/__init__.py").write_text("", encoding="utf-8")
        (package / "__init__.py").write_text(
            'from .contracts import Present\n__all__ = ["Present"]\n',
            encoding="utf-8",
        )
        (package / "contracts.py").write_text(
            "class Present:\n    pass\nclass Hidden:\n    pass\n",
            encoding="utf-8",
        )
        (tests / "test_api.py").write_text(
            "from core.fixture import Present, Hidden\n",
            encoding="utf-8",
        )

        smoke = (
            "from pathlib import Path;"
            "from core.engineering import expectations_from_tests,inventory_package,"
            "analyze_compatibility,build_restoration_plan;"
            f"r=Path({str(root)!r});"
            "e=expectations_from_tests(r,r/'tests');"
            "i=inventory_package(r,'core.fixture');"
            "a=analyze_compatibility(e,(i,));"
            "p=build_restoration_plan(a);"
            "assert a.compatibility_score==0.5;"
            "assert p[0].action=='restore_public_export';"
            "print(a.fingerprint())"
        )

        first = subprocess.run(
            [sys.executable, "-c", smoke],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        second = subprocess.run(
            [sys.executable, "-c", smoke],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        failures += check(
            first.returncode == 0
            and second.returncode == 0
            and first.stdout == second.stdout,
            "Deterministic compatibility smoke test",
        )

    genesis_v_e0 = subprocess.run(
        [sys.executable, "dev/verification/verify_genesis_5e0_engineering_os_foundation.py"],
        cwd=ROOT,
        check=False,
    )
    failures += check(genesis_v_e0.returncode == 0, "Genesis V-E0 regression")

    print()
    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 72)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
PYEOF

cat > dev/verify_genesis_5e1.sh <<'SHEOF'
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

echo
echo "========================================================================"
echo "JARVIS GENESIS V-E1 — PUBLIC API COMPATIBILITY INTELLIGENCE"
echo "========================================================================"

"${PYTHON_BIN}" dev/verification/verify_genesis_5e1_public_api_compatibility.py
SHEOF

cat > dev/analyze_public_api_compatibility.sh <<'SHEOF'
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

"${PYTHON_BIN}" -m core.engineering.cli bootstrap-manifest \
    --project-root "${PROJECT_ROOT}" \
    --tests-root tests \
    --output dev/verification/manifests/test_public_api_expectations.json

set +e
"${PYTHON_BIN}" -m core.engineering.cli analyze \
    --project-root "${PROJECT_ROOT}" \
    --manifest dev/verification/manifests/test_public_api_expectations.json \
    --json-output .artifacts/engineering/public_api_compatibility.json \
    --report-output docs/audits/public_api_compatibility_report.md
status=$?
set -e

if [ "${status}" -eq 2 ]; then
    echo
    echo "Compatibility analysis completed successfully."
    echo "Restoration findings are present; review:"
    echo "  docs/audits/public_api_compatibility_report.md"
    exit 0
fi

exit "${status}"
SHEOF

chmod +x \
    dev/verify_genesis_5e1.sh \
    dev/analyze_public_api_compatibility.sh \
    dev/verification/verify_genesis_5e1_public_api_compatibility.py

"${PYTHON_BIN}" dev/verification/verify_genesis_5e1_public_api_compatibility.py

echo
echo "Genesis V-E1 installed and verified."
echo
echo "Run the first repository analysis with:"
echo
echo "PYTHON_BIN=${PYTHON_BIN} ./dev/analyze_public_api_compatibility.sh"

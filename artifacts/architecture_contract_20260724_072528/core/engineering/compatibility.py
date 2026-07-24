"""Deterministic expected-versus-observed public API compatibility analysis."""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from core.architecture import architecture_fingerprint, canonical_json

from .api_inventory import TargetAPIInventory
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
    inventories: tuple[TargetAPIInventory, ...]
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
    inventories: tuple[TargetAPIInventory, ...],
) -> CompatibilityReport:
    by_package: Mapping[str, TargetAPIInventory] = {
        item.import_name: item for item in inventories
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
        inventories=tuple(sorted(inventories, key=lambda item: item.import_name)),
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

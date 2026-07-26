"""Canonical Observation convergence governance.

Genesis IV-B4 Final Convergence integrates definition discovery, export
separation, migration governance, deterministic reporting, and convergence
enforcement into one canonical implementation.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path
from typing import Final, Iterable

from .errors import ObservationConvergenceError
from .migration_registry import (
    CANONICAL_OBSERVATION_PATH,
    MigrationDisposition,
    migration_entry_for_path,
)


AUDIT_SCHEMA_VERSION: Final[str] = (
    "jarvis.observation-convergence-report.v3"
)


class ObservationDefinitionStatus(str, Enum):
    CANONICAL = "canonical"
    APPROVED_LEGACY = "approved_legacy"
    DEPRECATED = "deprecated"
    FORBIDDEN = "forbidden"


@dataclass(frozen=True, slots=True)
class ObservationDefinition:
    path: str
    status: ObservationDefinitionStatus
    semantic_role: str | None = None
    target_name: str | None = None

    @property
    def canonical(self) -> bool:
        return self.status is ObservationDefinitionStatus.CANONICAL

    @property
    def legacy_allowed(self) -> bool:
        return (
            self.status
            is ObservationDefinitionStatus.APPROVED_LEGACY
        )

    @property
    def deprecated(self) -> bool:
        return self.status is ObservationDefinitionStatus.DEPRECATED

    @property
    def forbidden(self) -> bool:
        return self.status is ObservationDefinitionStatus.FORBIDDEN

    def to_canonical_data(self) -> dict[str, str | None]:
        return {
            "path": self.path,
            "status": self.status.value,
            "semantic_role": self.semantic_role,
            "target_name": self.target_name,
        }


@dataclass(frozen=True, slots=True)
class ObservationConvergenceReport:
    schema_version: str
    repository_root: str
    canonical_path: str
    definitions: tuple[ObservationDefinition, ...]
    canonical_definitions: tuple[str, ...]
    approved_legacy_definitions: tuple[str, ...]
    deprecated_definitions: tuple[str, ...]
    forbidden_duplicates: tuple[str, ...]
    fingerprint: str

    @property
    def converged(self) -> bool:
        return (
            self.canonical_definitions == (self.canonical_path,)
            and not self.forbidden_duplicates
        )

    def to_canonical_data(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "canonical_path": self.canonical_path,
            "definitions": [
                item.to_canonical_data() for item in self.definitions
            ],
            "canonical_definitions": list(
                self.canonical_definitions
            ),
            "approved_legacy_definitions": list(
                self.approved_legacy_definitions
            ),
            "deprecated_definitions": list(
                self.deprecated_definitions
            ),
            "forbidden_duplicates": list(
                self.forbidden_duplicates
            ),
            "converged": self.converged,
            "fingerprint": self.fingerprint,
        }


def _module_defines_observation(path: Path) -> bool:
    """Return whether a module directly defines class Observation."""

    try:
        source = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return False

    return any(
        isinstance(node, ast.ClassDef)
        and node.name == "Observation"
        for node in tree.body
    )


def _classify(path: str) -> ObservationDefinition:
    entry = migration_entry_for_path(path)

    if path == CANONICAL_OBSERVATION_PATH:
        return ObservationDefinition(
            path=path,
            status=ObservationDefinitionStatus.CANONICAL,
            semantic_role=(
                entry.semantic_role
                if entry is not None
                else "canonical_observation_contract"
            ),
            target_name=(
                entry.target_name if entry is not None else "Observation"
            ),
        )

    if entry is None:
        return ObservationDefinition(
            path=path,
            status=ObservationDefinitionStatus.FORBIDDEN,
        )

    if entry.disposition is MigrationDisposition.APPROVED_LEGACY:
        status = ObservationDefinitionStatus.APPROVED_LEGACY
    elif entry.disposition is MigrationDisposition.DEPRECATED_RENAME:
        status = ObservationDefinitionStatus.DEPRECATED
    elif entry.disposition is MigrationDisposition.CANONICAL:
        status = ObservationDefinitionStatus.CANONICAL
    else:
        status = ObservationDefinitionStatus.FORBIDDEN

    return ObservationDefinition(
        path=path,
        status=status,
        semantic_role=entry.semantic_role,
        target_name=entry.target_name,
    )


def _ordered(
    definitions: Iterable[ObservationDefinition],
) -> tuple[ObservationDefinition, ...]:
    order = {
        ObservationDefinitionStatus.CANONICAL: 0,
        ObservationDefinitionStatus.APPROVED_LEGACY: 1,
        ObservationDefinitionStatus.DEPRECATED: 2,
        ObservationDefinitionStatus.FORBIDDEN: 3,
    }
    return tuple(
        sorted(
            definitions,
            key=lambda item: (order[item.status], item.path),
        )
    )


def _fingerprint(
    definitions: tuple[ObservationDefinition, ...],
) -> str:
    payload = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "canonical_path": CANONICAL_OBSERVATION_PATH,
        "definitions": [
            item.to_canonical_data() for item in definitions
        ],
    }
    return sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def audit_observation_definitions(
    repository_root: Path | str,
) -> ObservationConvergenceReport:
    """Discover and classify direct Observation definitions only."""

    root = Path(repository_root).resolve()
    discovered: list[ObservationDefinition] = []
    core_root = root / "core"

    if core_root.is_dir():
        for path in sorted(core_root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            if not _module_defines_observation(path):
                continue
            relative = path.relative_to(root).as_posix()
            discovered.append(_classify(relative))

    definitions = _ordered(discovered)
    canonical = tuple(
        item.path for item in definitions if item.canonical
    )
    approved = tuple(
        item.path for item in definitions if item.legacy_allowed
    )
    deprecated = tuple(
        item.path for item in definitions if item.deprecated
    )
    forbidden = tuple(
        item.path for item in definitions if item.forbidden
    )

    return ObservationConvergenceReport(
        schema_version=AUDIT_SCHEMA_VERSION,
        repository_root=str(root),
        canonical_path=CANONICAL_OBSERVATION_PATH,
        definitions=definitions,
        canonical_definitions=canonical,
        approved_legacy_definitions=approved,
        deprecated_definitions=deprecated,
        forbidden_duplicates=forbidden,
        fingerprint=_fingerprint(definitions),
    )


def format_observation_convergence_report(
    report: ObservationConvergenceReport,
) -> str:
    lines = [
        "=" * 72,
        "OBSERVATION CONVERGENCE INVENTORY",
        "=" * 72,
    ]
    groups = (
        ("Canonical", report.canonical_definitions),
        ("Approved Legacy", report.approved_legacy_definitions),
        ("Deprecated", report.deprecated_definitions),
        ("Forbidden", report.forbidden_duplicates),
    )
    for title, paths in groups:
        lines.extend(["", title, "-" * len(title)])
        lines.extend(paths or ("none",))

    lines.extend(
        [
            "",
            "Convergence",
            "-----------",
            "PASS" if report.converged else "FAIL",
            "",
            "Fingerprint",
            "-----------",
            report.fingerprint,
            "=" * 72,
        ]
    )
    return "\n".join(lines)


def render_observation_convergence_markdown(
    report: ObservationConvergenceReport,
) -> str:
    lines = [
        "# Genesis IV-B3/B4 Observation Convergence Report",
        "",
        f"**Schema:** `{report.schema_version}`  ",
        f"**Canonical owner:** `{report.canonical_path}`  ",
        f"**Converged:** `{'YES' if report.converged else 'NO'}`  ",
        f"**Fingerprint:** `{report.fingerprint}`",
        "",
    ]
    for title, paths in (
        ("Canonical", report.canonical_definitions),
        ("Approved Legacy", report.approved_legacy_definitions),
        ("Deprecated", report.deprecated_definitions),
        ("Forbidden", report.forbidden_duplicates),
    ):
        lines.extend([f"## {title}", ""])
        lines.extend(
            (f"- `{path}`" for path in paths)
            if paths
            else ("- None",)
        )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_observation_convergence_reports(
    report: ObservationConvergenceReport,
    output_directory: Path | str,
) -> tuple[Path, Path]:
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)

    json_path = output / (
        "genesis_iv_b3_observation_convergence.json"
    )
    markdown_path = output / (
        "genesis_iv_b3_observation_convergence.md"
    )

    json_path.write_text(
        json.dumps(
            report.to_canonical_data(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(
        render_observation_convergence_markdown(report),
        encoding="utf-8",
    )
    return json_path, markdown_path


def require_observation_convergence(
    repository_root: Path | str,
) -> ObservationConvergenceReport:
    report = audit_observation_definitions(repository_root)

    if report.canonical_definitions != (
        CANONICAL_OBSERVATION_PATH,
    ):
        raise ObservationConvergenceError(
            "expected exactly one canonical Observation definition at "
            f"{CANONICAL_OBSERVATION_PATH}; discovered: "
            + (
                ", ".join(report.canonical_definitions)
                or "none"
            )
        )

    if report.forbidden_duplicates:
        raise ObservationConvergenceError(
            "forbidden Observation definitions: "
            + ", ".join(report.forbidden_duplicates)
        )

    return report


__all__ = [
    "AUDIT_SCHEMA_VERSION",
    "CANONICAL_OBSERVATION_PATH",
    "ObservationConvergenceReport",
    "ObservationDefinition",
    "ObservationDefinitionStatus",
    "audit_observation_definitions",
    "format_observation_convergence_report",
    "render_observation_convergence_markdown",
    "require_observation_convergence",
    "write_observation_convergence_reports",
]

"""Repository-reality contracts for importable engineering artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.architecture import architecture_fingerprint, canonical_json
from .errors import EngineeringValidationError


class InventoryTargetKind:
    PACKAGE = "package"
    MODULE = "module"
    NAMESPACE_PACKAGE = "namespace_package"
    COMPATIBILITY_ALIAS = "compatibility_alias"
    MISSING = "missing"


_VALID_KINDS = {
    InventoryTargetKind.PACKAGE,
    InventoryTargetKind.MODULE,
    InventoryTargetKind.NAMESPACE_PACKAGE,
    InventoryTargetKind.COMPATIBILITY_ALIAS,
    InventoryTargetKind.MISSING,
}


def _required(value: str, name: str) -> str:
    result = value.strip()
    if not result:
        raise EngineeringValidationError(f"{name} must not be empty")
    return result


def normalize_import_name(import_name: str) -> str:
    parts = [part.strip() for part in _required(import_name, "import_name").split(".")]
    if any(not part for part in parts):
        raise EngineeringValidationError(f"Invalid import name: {import_name!r}")
    return ".".join(parts)


def import_name_to_relative_path(import_name: str) -> Path:
    return Path(*normalize_import_name(import_name).split("."))


@dataclass(frozen=True, slots=True)
class InventoryTarget:
    import_name: str
    kind: str
    path: str | None
    package_root: str | None
    exists: bool
    canonical_import_name: str
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "import_name", normalize_import_name(self.import_name))
        object.__setattr__(
            self,
            "canonical_import_name",
            normalize_import_name(self.canonical_import_name),
        )
        if self.kind not in _VALID_KINDS:
            raise EngineeringValidationError(f"Unsupported target kind: {self.kind}")
        object.__setattr__(self, "evidence", tuple(sorted(set(self.evidence))))

    def to_canonical_json(self) -> str:
        return canonical_json(self)

    def fingerprint(self) -> str:
        return architecture_fingerprint(self)


@dataclass(frozen=True, slots=True)
class InventoryResolution:
    requested_import: str
    target: InventoryTarget
    resolution_trace: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "requested_import",
            normalize_import_name(self.requested_import),
        )
        object.__setattr__(self, "resolution_trace", tuple(self.resolution_trace))

    def fingerprint(self) -> str:
        return architecture_fingerprint(self)


def stable_inventory_targets(
    targets: Iterable[InventoryTarget],
) -> tuple[InventoryTarget, ...]:
    return tuple(
        sorted(
            targets,
            key=lambda item: (item.import_name, item.kind, item.path or ""),
        )
    )


__all__ = [
    "InventoryResolution",
    "InventoryTarget",
    "InventoryTargetKind",
    "import_name_to_relative_path",
    "normalize_import_name",
    "stable_inventory_targets",
]

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Component:
    name: str
    layer: str
    responsibility: str
    owns: tuple[str, ...]
    must_not_own: tuple[str, ...]
    source_modules: tuple[str, ...]
    stability: str
    extension_policy: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ("owns", "must_not_own", "source_modules"):
            data[key] = list(data[key])
        return data


@dataclass(frozen=True, slots=True)
class Invariant:
    invariant_id: str
    title: str
    rule: str
    rationale: str
    protected_components: tuple[str, ...]
    validation: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["protected_components"] = list(data["protected_components"])
        return data


@dataclass(frozen=True, slots=True)
class ExtensionPoint:
    name: str
    purpose: str
    attaches_to: tuple[str, ...]
    allowed_responsibilities: tuple[str, ...]
    prohibited_responsibilities: tuple[str, ...]
    intended_phase: str
    compatibility_requirement: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in (
            "attaches_to",
            "allowed_responsibilities",
            "prohibited_responsibilities",
        ):
            data[key] = list(data[key])
        return data

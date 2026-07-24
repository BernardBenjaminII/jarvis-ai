"""Capability declarations and routing evidence for JARVIS directors."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class DirectorReadiness(str, Enum):
    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class Capability:
    name: str
    description: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", normalize_capability(self.name))


@dataclass(slots=True)
class DirectorDescriptor:
    name: str
    description: str = ""
    capabilities: set[str] = field(default_factory=set)
    priority: int = 100
    readiness: DirectorReadiness = DirectorReadiness.READY
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.name = normalize_director_name(self.name)
        self.capabilities = {normalize_capability(c) for c in self.capabilities}
        if self.priority < 0:
            raise ValueError("Director priority cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["capabilities"] = sorted(self.capabilities)
        data["readiness"] = self.readiness.value
        return data


@dataclass(frozen=True, slots=True)
class RoutingCandidate:
    director: str
    matched_capabilities: tuple[str, ...]
    missing_capabilities: tuple[str, ...]
    score: float
    priority: int
    readiness: DirectorReadiness

    def to_dict(self) -> dict[str, Any]:
        return {
            "director": self.director,
            "matched_capabilities": list(self.matched_capabilities),
            "missing_capabilities": list(self.missing_capabilities),
            "score": self.score,
            "priority": self.priority,
            "readiness": self.readiness.value,
        }


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    selected_director: str
    required_capabilities: tuple[str, ...]
    candidates: tuple[RoutingCandidate, ...]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_director": self.selected_director,
            "required_capabilities": list(self.required_capabilities),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "reason": self.reason,
        }


def normalize_capability(value: str) -> str:
    normalized = value.strip().casefold().replace("-", "_").replace(" ", "_")
    if not normalized:
        raise ValueError("Capability name cannot be empty")
    return normalized


def normalize_director_name(value: str) -> str:
    normalized = value.strip().casefold().replace("-", "_").replace(" ", "_")
    if not normalized:
        raise ValueError("Director name cannot be empty")
    return normalized

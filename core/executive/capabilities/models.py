
"""Genesis VII-A0 Pack 4B-2 canonical capability orchestration models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


class CapabilityHealth(str, Enum):
    READY = "ready"
    BUSY = "busy"
    DEGRADED = "degraded"
    FAILED = "failed"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


class CapabilityRisk(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class PlanStatus(str, Enum):
    PLANNED = "planned"
    BLOCKED = "blocked"


def _tuple(values: Iterable[str] | None) -> tuple[str, ...]:
    return tuple(sorted({str(value).strip() for value in values or () if str(value).strip()}))


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True, slots=True)
class CapabilityMetadata:
    capability_id: str
    name: str
    version: str = "1.0.0"
    owner: str = "executive"
    description: str = ""
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    mission_types: tuple[str, ...] = ()
    ui_category: str = "enterprise"
    cost: int = 0
    latency_ms: int = 0
    risk: CapabilityRisk = CapabilityRisk.LOW
    confidence: float = 1.0
    observable: bool = True
    health: CapabilityHealth = CapabilityHealth.UNKNOWN

    def __post_init__(self) -> None:
        if not self.capability_id.strip():
            raise ValueError("capability_id cannot be empty.")
        if not self.name.strip():
            raise ValueError("name cannot be empty.")
        if self.cost < 0:
            raise ValueError("cost cannot be negative.")
        if self.latency_ms < 0:
            raise ValueError("latency_ms cannot be negative.")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1.")
        for attribute in (
            "inputs",
            "outputs",
            "permissions",
            "dependencies",
            "mission_types",
        ):
            object.__setattr__(self, attribute, _tuple(getattr(self, attribute)))
        object.__setattr__(self, "capability_id", self.capability_id.strip())
        object.__setattr__(self, "name", self.name.strip())

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["risk"] = self.risk.value
        payload["health"] = self.health.value
        return payload


@dataclass(frozen=True, slots=True)
class CapabilityRequirement:
    mission_type: str
    required_inputs: tuple[str, ...] = ()
    required_outputs: tuple[str, ...] = ()
    permitted_permissions: tuple[str, ...] = ()
    maximum_risk: CapabilityRisk = CapabilityRisk.HIGH
    maximum_cost: int | None = None
    maximum_latency_ms: int | None = None
    prefer_local: bool = True

    def __post_init__(self) -> None:
        if not self.mission_type.strip():
            raise ValueError("mission_type cannot be empty.")
        for attribute in (
            "required_inputs",
            "required_outputs",
            "permitted_permissions",
        ):
            object.__setattr__(self, attribute, _tuple(getattr(self, attribute)))


@dataclass(frozen=True, slots=True)
class CandidateScore:
    capability_id: str
    eligible: bool
    score: int
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SelectionTrace:
    mission_type: str
    selected_capability_id: str | None
    candidates: tuple[CandidateScore, ...]
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        payload = {
            "mission_type": self.mission_type,
            "selected_capability_id": self.selected_capability_id,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
        }
        object.__setattr__(self, "fingerprint", sha256(_canonical(payload).encode()).hexdigest())

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_type": self.mission_type,
            "selected_capability_id": self.selected_capability_id,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class PlanStep:
    sequence: int
    capability_id: str
    depends_on: tuple[str, ...] = ()
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CapabilityPlan:
    mission_type: str
    status: PlanStatus
    steps: tuple[PlanStep, ...]
    blocked_reasons: tuple[str, ...] = ()
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        payload = {
            "mission_type": self.mission_type,
            "status": self.status.value,
            "steps": [step.to_dict() for step in self.steps],
            "blocked_reasons": list(self.blocked_reasons),
        }
        object.__setattr__(self, "fingerprint", sha256(_canonical(payload).encode()).hexdigest())

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_type": self.mission_type,
            "status": self.status.value,
            "steps": [step.to_dict() for step in self.steps],
            "blocked_reasons": list(self.blocked_reasons),
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class OrchestrationDecision:
    requirement: CapabilityRequirement
    selection: SelectionTrace
    plan: CapabilityPlan

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement": {
                **asdict(self.requirement),
                "maximum_risk": self.requirement.maximum_risk.value,
            },
            "selection": self.selection.to_dict(),
            "plan": self.plan.to_dict(),
        }

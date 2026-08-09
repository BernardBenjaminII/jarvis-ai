
"""Deterministic Executive capability selector."""

from __future__ import annotations

from .models import (
    CandidateScore,
    CapabilityHealth,
    CapabilityRequirement,
    CapabilityRisk,
    SelectionTrace,
)
from .registry import CapabilityRegistry


_HEALTH_SCORE = {
    CapabilityHealth.READY: 1000,
    CapabilityHealth.DEGRADED: 400,
    CapabilityHealth.UNKNOWN: 100,
    CapabilityHealth.BUSY: 50,
    CapabilityHealth.FAILED: -10000,
    CapabilityHealth.DISABLED: -10000,
}

_RISK_ORDER = {
    CapabilityRisk.LOW: 0,
    CapabilityRisk.MODERATE: 1,
    CapabilityRisk.HIGH: 2,
    CapabilityRisk.CRITICAL: 3,
}


class CapabilitySelector:
    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    def select(self, requirement: CapabilityRequirement) -> SelectionTrace:
        candidates = tuple(
            self._score(capability, requirement)
            for capability in self._registry.by_mission_type(requirement.mission_type)
        )
        ordered = tuple(
            sorted(candidates, key=lambda item: (-int(item.eligible), -item.score, item.capability_id))
        )
        eligible = [candidate for candidate in ordered if candidate.eligible]
        selected = eligible[0].capability_id if eligible else None
        return SelectionTrace(
            mission_type=requirement.mission_type,
            selected_capability_id=selected,
            candidates=ordered,
        )

    def _score(self, capability, requirement: CapabilityRequirement) -> CandidateScore:
        reasons: list[str] = []
        eligible = True

        if capability.health in {CapabilityHealth.FAILED, CapabilityHealth.DISABLED}:
            eligible = False
            reasons.append(f"health={capability.health.value}")

        if _RISK_ORDER[capability.risk] > _RISK_ORDER[requirement.maximum_risk]:
            eligible = False
            reasons.append("risk exceeds mission authority")

        if requirement.maximum_cost is not None and capability.cost > requirement.maximum_cost:
            eligible = False
            reasons.append("cost exceeds mission limit")

        if (
            requirement.maximum_latency_ms is not None
            and capability.latency_ms > requirement.maximum_latency_ms
        ):
            eligible = False
            reasons.append("latency exceeds mission limit")

        if not set(requirement.required_inputs).issubset(capability.inputs):
            eligible = False
            reasons.append("required inputs unsupported")

        if not set(requirement.required_outputs).issubset(capability.outputs):
            eligible = False
            reasons.append("required outputs unsupported")

        if requirement.permitted_permissions and not set(capability.permissions).issubset(
            requirement.permitted_permissions
        ):
            eligible = False
            reasons.append("permission boundary exceeded")

        score = _HEALTH_SCORE[capability.health]
        score += int(capability.confidence * 100)
        score -= capability.cost * 10
        score -= capability.latency_ms // 10
        score -= _RISK_ORDER[capability.risk] * 50
        if capability.owner == "local":
            score += 25
            reasons.append("local execution preferred")
        reasons.append(f"deterministic score={score}")

        return CandidateScore(
            capability_id=capability.capability_id,
            eligible=eligible,
            score=score,
            reasons=tuple(reasons),
        )

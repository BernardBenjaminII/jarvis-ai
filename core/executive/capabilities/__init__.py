
"""Unified Executive capability API.

Genesis VII-A0 Pack 4B-3 consolidates the historical
``core.executive.capabilities`` module and the Pack 4B-2 orchestration package
behind one stable package namespace.

Legacy director capability contracts now live in
``core.executive.capability_contracts`` and remain re-exported here.
"""

from __future__ import annotations

from core.executive import capability_contracts as _legacy_contracts

from .graph import CapabilityGraph, CapabilityGraphError
from .models import (
    CandidateScore,
    CapabilityHealth,
    CapabilityMetadata,
    CapabilityPlan,
    CapabilityRequirement,
    CapabilityRisk,
    OrchestrationDecision,
    PlanStatus,
    PlanStep,
    SelectionTrace,
)
from .observability import CapabilityObservabilityService
from .orchestrator import CapabilityOrchestrator
from .planner import CapabilityPlanner
from .registry import CapabilityRegistry
from .selector import CapabilitySelector


def _legacy_public_names() -> tuple[str, ...]:
    declared = getattr(_legacy_contracts, "__all__", None)
    if declared is not None:
        return tuple(
            name
            for name in declared
            if isinstance(name, str) and name and not name.startswith("_")
        )

    return tuple(
        name
        for name in vars(_legacy_contracts)
        if name and not name.startswith("_")
    )


_LEGACY_PUBLIC_NAMES = _legacy_public_names()

for _name in _LEGACY_PUBLIC_NAMES:
    globals()[_name] = getattr(_legacy_contracts, _name)


_ORCHESTRATION_PUBLIC_NAMES = (
    "CandidateScore",
    "CapabilityGraph",
    "CapabilityGraphError",
    "CapabilityHealth",
    "CapabilityMetadata",
    "CapabilityObservabilityService",
    "CapabilityOrchestrator",
    "CapabilityPlan",
    "CapabilityPlanner",
    "CapabilityRegistry",
    "CapabilityRequirement",
    "CapabilityRisk",
    "CapabilitySelector",
    "OrchestrationDecision",
    "PlanStatus",
    "PlanStep",
    "SelectionTrace",
)

__all__ = sorted(set(_LEGACY_PUBLIC_NAMES + _ORCHESTRATION_PUBLIC_NAMES))

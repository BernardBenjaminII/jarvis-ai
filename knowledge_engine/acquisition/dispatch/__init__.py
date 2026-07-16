"""
Canonical acquisition-to-Phase-VI dispatch.

The package provides:

- explicit registration and execution ports
- bounded atomic handoff claiming
- retryable failure transitions
- stale claim recovery
- a narrow Phase VI runner adapter
"""

from knowledge_engine.acquisition.dispatch.models import (
    AssimilationDispatchResult,
)
from knowledge_engine.acquisition.dispatch.phase_vi import (
    PhaseVIRunnerExecutionAdapter,
)
from knowledge_engine.acquisition.dispatch.ports import (
    AcquisitionRegistrationPort,
    PhaseVIExecutionPort,
)
from knowledge_engine.acquisition.dispatch.repository import (
    AssimilationDispatchRepository,
)
from knowledge_engine.acquisition.dispatch.service import (
    CanonicalAssimilationDispatcher,
)

__all__ = [
    "AcquisitionRegistrationPort",
    "AssimilationDispatchRepository",
    "AssimilationDispatchResult",
    "CanonicalAssimilationDispatcher",
    "PhaseVIExecutionPort",
    "PhaseVIRunnerExecutionAdapter",
]

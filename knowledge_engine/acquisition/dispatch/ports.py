"""
Explicit subsystem-boundary ports for Phase VII-A7.

Acquisition must not depend on Phase VI registry SQL or internal service
implementations. The registration port provides the canonical Knowledge
Registry object UUID. The execution port invokes the existing assimilation
entry point.
"""

from __future__ import annotations

from typing import Any, Protocol

from knowledge_engine.acquisition.handoff.models import (
    AssimilationHandoffRecord,
)


class AcquisitionRegistrationPort(Protocol):
    """Register or resolve one accepted source in the Knowledge Registry."""

    def ensure_registered(
        self,
        *,
        handoff: AssimilationHandoffRecord,
    ) -> str:
        """
        Return the canonical Knowledge Registry object UUID.

        Implementations must be idempotent.
        """
        ...


class PhaseVIExecutionPort(Protocol):
    """Execute one canonical Phase VI registry object."""

    def execute_registered_object(
        self,
        *,
        object_uuid: str,
    ) -> dict[str, Any]:
        """Execute one registered object through Phase VI."""
        ...


__all__ = [
    "AcquisitionRegistrationPort",
    "PhaseVIExecutionPort",
]

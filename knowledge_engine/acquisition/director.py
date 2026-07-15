"""
Read-only Knowledge Acquisition Director.

Phase VII-A1 resolves a provider and produces a deterministic acquisition plan.
It does not download, admit, assimilate, or modify source content.
"""

from __future__ import annotations

from knowledge_engine.acquisition.models import (
    AcquisitionPlan,
    AcquisitionRequest,
)
from knowledge_engine.acquisition.provider_registry import (
    AcquisitionProviderRegistry,
)


class KnowledgeAcquisitionDirector:
    """Coordinate provider-based discovery planning."""

    def __init__(
        self,
        registry: AcquisitionProviderRegistry,
    ):
        self.registry = registry

    def plan(
        self,
        *,
        provider_id: str,
        request: AcquisitionRequest,
    ) -> AcquisitionPlan:
        provider = self.registry.get(
            provider_id
        )

        plan = provider.discover(
            request=request
        )

        if plan.provider_id != provider.provider_id:
            raise RuntimeError(
                "Provider returned a mismatched provider_id"
            )

        if plan.request_id != request.request_id:
            raise RuntimeError(
                "Provider returned a mismatched request_id"
            )

        return plan

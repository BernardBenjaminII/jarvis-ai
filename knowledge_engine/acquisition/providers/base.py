"""
Abstract source-provider contract for JARVIS acquisition.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from knowledge_engine.acquisition.models import (
    AcquisitionPlan,
    AcquisitionRequest,
)


class AcquisitionProvider(ABC):
    """Discover sources from one bounded acquisition domain."""

    provider_id: str

    @abstractmethod
    def discover(
        self,
        *,
        request: AcquisitionRequest,
    ) -> AcquisitionPlan:
        """Discover candidate knowledge sources without assimilating them."""

"""
JARVIS Knowledge Acquisition foundation.
"""

from knowledge_engine.acquisition.director import (
    KnowledgeAcquisitionDirector,
)
from knowledge_engine.acquisition.models import (
    AcquisitionPlan,
    AcquisitionRequest,
    SourceCandidate,
)
from knowledge_engine.acquisition.provider_registry import (
    AcquisitionProviderRegistry,
)
from knowledge_engine.acquisition.providers import (
    AcquisitionProvider,
    FilesystemAcquisitionProvider,
)


def build_default_provider_registry() -> AcquisitionProviderRegistry:
    """Construct the canonical Phase VII-A1 provider registry."""

    registry = AcquisitionProviderRegistry()
    registry.register(
        FilesystemAcquisitionProvider()
    )
    return registry


__all__ = [
    "AcquisitionPlan",
    "AcquisitionProvider",
    "AcquisitionProviderRegistry",
    "AcquisitionRequest",
    "FilesystemAcquisitionProvider",
    "KnowledgeAcquisitionDirector",
    "SourceCandidate",
    "build_default_provider_registry",
]

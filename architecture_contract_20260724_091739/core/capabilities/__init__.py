"""Capability framework public API."""

from core.capabilities.base import Capability
from core.capabilities.discovery import (
    CapabilityDiscovery,
    CapabilityDiscoveryResult,
)
from core.capabilities.loader import CapabilityLoader
from core.capabilities.metadata import (
    CapabilityBindingState,
    CapabilityMetadata,
    CapabilityOperation,
    metadata_for,
)
from core.capabilities.models import CapabilityContext, CapabilityResult
from core.capabilities.operations import (
    OperationsReadCapability,
    register_operations_capabilities,
)
from core.capabilities.registry import CapabilityRegistry
from core.capabilities.runner import CapabilityRunner

__all__ = [
    "Capability",
    "CapabilityBindingState",
    "CapabilityContext",
    "CapabilityDiscovery",
    "CapabilityDiscoveryResult",
    "CapabilityLoader",
    "CapabilityMetadata",
    "CapabilityOperation",
    "CapabilityRegistry",
    "CapabilityResult",
    "CapabilityRunner",
    "OperationsReadCapability",
    "metadata_for",
    "register_operations_capabilities",
]

"""Stable public API for the JARVIS Executive Integration Plane."""

from .api import (
    ExecutiveApiEnvelope,
    IntegrationProjectionProvider,
    build_api_envelope,
)
from .audit import RepositoryIntegrationAuditor
from .catalog import build_genesis_iv_capability_registry
from .contracts import (
    CapabilityDefinition,
    CapabilityProjection,
    CommanderBriefProjection,
    ExecutiveProjection,
    ExecutiveTimelineNode,
    IntegrationFinding,
    IntegrationHealthProjection,
    IntegrationLink,
    KnowledgeReadiness,
    MissionControlProjection,
    ProjectionEnvelope,
    ProjectionHealth,
    ProjectionStatus,
    VerificationReference,
    utc_now_iso,
)
from .enums import (
    CapabilityLifecycle,
    HealthStatus,
    IntegrationStatus,
    KnowledgeCoverageStatus,
    Severity,
    VisibilitySurface,
)
from .errors import (
    DuplicateCapabilityError,
    DuplicateProjectionProviderError,
    IntegrationError,
    InvalidIntegrationDefinitionError,
    ProjectionExecutionError,
    ProjectionProviderNotFoundError,
    UnknownCapabilityError,
)
from .knowledge import build_knowledge_readiness
from .projections import (
    build_capability_projection,
    build_commander_brief,
    build_mission_control_projection,
    determine_overall_health,
)
from .registry import CapabilityRegistry, ProjectionRegistry
from .serialization import to_canonical_data
from .service import ExecutiveIntegrationService, ExecutiveProjectionService

__all__ = [
    "CapabilityDefinition",
    "CapabilityLifecycle",
    "CapabilityProjection",
    "CapabilityRegistry",
    "CommanderBriefProjection",
    "DuplicateCapabilityError",
    "DuplicateProjectionProviderError",
    "ExecutiveApiEnvelope",
    "ExecutiveIntegrationService",
    "ExecutiveProjection",
    "ExecutiveProjectionService",
    "ExecutiveTimelineNode",
    "HealthStatus",
    "IntegrationError",
    "IntegrationFinding",
    "IntegrationHealthProjection",
    "IntegrationLink",
    "IntegrationProjectionProvider",
    "IntegrationStatus",
    "InvalidIntegrationDefinitionError",
    "KnowledgeCoverageStatus",
    "KnowledgeReadiness",
    "MissionControlProjection",
    "ProjectionEnvelope",
    "ProjectionExecutionError",
    "ProjectionHealth",
    "ProjectionProviderNotFoundError",
    "ProjectionRegistry",
    "ProjectionStatus",
    "RepositoryIntegrationAuditor",
    "Severity",
    "UnknownCapabilityError",
    "VerificationReference",
    "VisibilitySurface",
    "build_api_envelope",
    "build_capability_projection",
    "build_commander_brief",
    "build_genesis_iv_capability_registry",
    "build_knowledge_readiness",
    "build_mission_control_projection",
    "determine_overall_health",
    "to_canonical_data",
    "utc_now_iso",
]

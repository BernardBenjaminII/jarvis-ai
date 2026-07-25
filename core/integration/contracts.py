from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Mapping, Tuple
from .enums import CapabilityLifecycle, HealthStatus, IntegrationStatus, KnowledgeCoverageStatus, Severity, VisibilitySurface
from .errors import InvalidIntegrationDefinitionError

def utc_now_iso(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def _freeze(value): return MappingProxyType(dict(sorted((value or {}).items())))

@dataclass(frozen=True, slots=True)
class VerificationReference:
    verifier: str
    fingerprint: str=''
    last_verified_at: str=''
    def __post_init__(self):
        if not self.verifier.strip(): raise InvalidIntegrationDefinitionError('verifier is required')

@dataclass(frozen=True, slots=True)
class CapabilityDefinition:
    capability_id: str; name: str; description: str; owner_package: str
    lifecycle: CapabilityLifecycle; health: HealthStatus
    dependencies: Tuple[str,...]=(); input_contracts: Tuple[str,...]=(); output_contracts: Tuple[str,...]=()
    api_routes: Tuple[str,...]=(); ui_surfaces: Tuple[str,...]=(); knowledge_requirements: Tuple[str,...]=()
    executor_capabilities: Tuple[str,...]=(); visibility: Tuple[VisibilitySurface,...]=()
    verification: VerificationReference|None=None
    metadata: Mapping[str,str]=field(default_factory=lambda: MappingProxyType({}))
    def __post_init__(self):
        if not self.capability_id.strip() or not self.name.strip() or not self.owner_package.strip():
            raise InvalidIntegrationDefinitionError('capability identity, name, and owner are required')
        for n in ('dependencies','input_contracts','output_contracts','api_routes','ui_surfaces','knowledge_requirements','executor_capabilities','visibility'):
            object.__setattr__(self,n,tuple(getattr(self,n)))
        object.__setattr__(self,'metadata',_freeze(self.metadata))

@dataclass(frozen=True, slots=True)
class IntegrationLink:
    source_capability: str; target_capability: str; status: IntegrationStatus
    transport: str; contract: str; observable: bool; details: str=''

@dataclass(frozen=True, slots=True)
class IntegrationFinding:
    finding_id: str; severity: Severity; capability_id: str; surface: VisibilitySurface; summary: str; recommendation: str

@dataclass(frozen=True, slots=True)
class KnowledgeReadiness:
    query: str; status: KnowledgeCoverageStatus; coverage: float
    known_domains: Tuple[str,...]=(); missing_domains: Tuple[str,...]=(); recommended_sources: Tuple[str,...]=()
    can_proceed: bool=False; confidence_limit: float=0.0; catalog_reference: str=''
    def __post_init__(self):
        if not 0 <= self.coverage <= 1 or not 0 <= self.confidence_limit <= 1:
            raise InvalidIntegrationDefinitionError('coverage and confidence must be between 0 and 1')
        for n in ('known_domains','missing_domains','recommended_sources'): object.__setattr__(self,n,tuple(getattr(self,n)))

@dataclass(frozen=True, slots=True)
class CapabilityProjection:
    capability_id: str; name: str; lifecycle: CapabilityLifecycle; health: HealthStatus
    runtime_visible: bool; api_visible: bool; ui_visible: bool; knowledge_connected: bool; telemetry_visible: bool
    dependencies: Tuple[str,...]; api_routes: Tuple[str,...]; ui_surfaces: Tuple[str,...]; verification_fingerprint: str

@dataclass(frozen=True, slots=True)
class IntegrationHealthProjection:
    generated_at: str; overall_health: HealthStatus; capabilities: Tuple[CapabilityProjection,...]
    links: Tuple[IntegrationLink,...]; findings: Tuple[IntegrationFinding,...]
    totals: Mapping[str,str]
    def __post_init__(self): object.__setattr__(self,'totals',_freeze(self.totals))

@dataclass(frozen=True, slots=True)
class CommanderBriefProjection:
    generated_at: str; system_health: HealthStatus; available_capabilities: int; degraded_capabilities: int
    unavailable_capabilities: int; not_connected_capabilities: int; pending_approvals: int; active_missions: int
    failed_activities: int; acquisition_queue_depth: int; critical_findings: Tuple[IntegrationFinding,...]
    knowledge_readiness: KnowledgeReadiness|None=None

@dataclass(frozen=True, slots=True)
class ExecutiveTimelineNode:
    node_id: str; node_type: str; status: str; title: str; parent_id: str=''; timestamp: str=''; trace_reference: str=''

@dataclass(frozen=True, slots=True)
class MissionControlProjection:
    commander_brief: CommanderBriefProjection; capability_catalog: Tuple[CapabilityProjection,...]
    integration_health: IntegrationHealthProjection; executive_timeline: Tuple[ExecutiveTimelineNode,...]

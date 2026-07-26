from .contracts import CapabilityProjection, CommanderBriefProjection, MissionControlProjection
from .enums import CapabilityLifecycle as L, HealthStatus as H, Severity, VisibilitySurface as V

def build_capability_projection(c):
    vis=set(c.visibility); fp=c.verification.fingerprint if c.verification else ''
    return CapabilityProjection(c.capability_id,c.name,c.lifecycle,c.health,V.RUNTIME in vis,V.API in vis or bool(c.api_routes),V.UI in vis or bool(c.ui_surfaces),V.KNOWLEDGE in vis,V.TELEMETRY in vis,c.dependencies,c.api_routes,c.ui_surfaces,fp)
def determine_overall_health(items):
    if any(x.health is H.UNAVAILABLE for x in items): return H.UNAVAILABLE
    if any(x.health in {H.DEGRADED,H.UNKNOWN} or x.lifecycle in {L.DEGRADED,L.NOT_CONNECTED} for x in items): return H.DEGRADED
    return H.HEALTHY
def build_commander_brief(health, knowledge_readiness=None, pending_approvals=0, active_missions=0, failed_activities=0, acquisition_queue_depth=0):
    c=health.capabilities
    return CommanderBriefProjection(health.generated_at,health.overall_health,sum(1 for x in c if x.lifecycle is L.AVAILABLE and x.health is H.HEALTHY),sum(1 for x in c if x.lifecycle is L.DEGRADED or x.health in {H.DEGRADED,H.UNKNOWN}),sum(1 for x in c if x.lifecycle is L.UNAVAILABLE or x.health is H.UNAVAILABLE),sum(1 for x in c if x.lifecycle is L.NOT_CONNECTED),pending_approvals,active_missions,failed_activities,acquisition_queue_depth,tuple(f for f in health.findings if f.severity is Severity.CRITICAL),knowledge_readiness)
def build_mission_control_projection(health, knowledge_readiness=None, timeline=(), **counts):
    return MissionControlProjection(build_commander_brief(health,knowledge_readiness,**counts),health.capabilities,health,tuple(timeline))

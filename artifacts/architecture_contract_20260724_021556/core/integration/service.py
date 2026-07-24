from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from core.integration.contracts import ProjectionEnvelope, ProjectionStatus
from core.integration.registry import ProjectionRegistry

class ExecutiveProjectionService:
    def __init__(self, registry: ProjectionRegistry) -> None:
        self.registry = registry
    def projection(self, projection_id: str) -> ProjectionEnvelope:
        return self.registry.get(projection_id).project()
    def all_projections(self) -> dict[str, Any]:
        generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        projections = {}
        summary = {status.value: 0 for status in ProjectionStatus}
        for provider in self.registry.all():
            envelope = provider.project()
            projections[provider.projection_id] = envelope.to_dict()
            summary[envelope.health.status.value] += 1
        return {"schema_version": "1.0", "generated_at": generated_at, "provider_count": len(projections), "summary": summary, "projections": projections}
    def health(self) -> dict[str, Any]:
        providers = []
        overall = ProjectionStatus.AVAILABLE
        for provider in self.registry.all():
            health = provider.health()
            providers.append({"projection_id": provider.projection_id, "health": health.to_dict()})
            if health.status == ProjectionStatus.UNAVAILABLE:
                overall = ProjectionStatus.UNAVAILABLE
            elif health.status in {ProjectionStatus.DEGRADED, ProjectionStatus.UNKNOWN, ProjectionStatus.NOT_CONFIGURED} and overall != ProjectionStatus.UNAVAILABLE:
                overall = ProjectionStatus.DEGRADED
        return {"status": overall.value, "provider_count": len(providers), "providers": providers}

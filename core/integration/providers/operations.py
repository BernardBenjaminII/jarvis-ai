"""Projection provider for the existing OperationsService."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.integration.contracts import (
    ProjectionEnvelope,
    ProjectionHealth,
    ProjectionStatus,
)


class OperationsProjectionProvider:
    projection_id = "operations"
    schema_version = "1.1"

    def __init__(self, operations_service: Any) -> None:
        self.operations_service = operations_service

    def health(self) -> ProjectionHealth:
        try:
            result = self.operations_service.health().to_dict()
        except Exception as exc:
            return ProjectionHealth(
                status=ProjectionStatus.UNAVAILABLE,
                summary="OperationsService health projection failed.",
                errors=(str(exc),),
            )

        status_text = str(
            result.get("status")
            or result.get("state")
            or "unknown"
        ).lower()

        if status_text in {"healthy", "available", "ok", "operational", "ready"}:
            status = ProjectionStatus.AVAILABLE
        elif status_text in {"degraded", "warning"}:
            status = ProjectionStatus.DEGRADED
        elif status_text in {"unhealthy", "failed", "unavailable"}:
            status = ProjectionStatus.UNAVAILABLE
        else:
            status = ProjectionStatus.UNKNOWN

        return ProjectionHealth(
            status=status,
            summary="OperationsService health projection completed.",
            details=result,
        )

    def project(self) -> ProjectionEnvelope:
        generated_at = datetime.now(timezone.utc)
        health = self.health()
        warnings: list[str] = []
        errors: list[str] = []
        data: dict[str, Any] = {}

        projections = {
            "status": lambda: self.operations_service.snapshot().to_dict(),
            "executive": lambda: self.operations_service.executive().to_dict(),
            "missions": lambda: [
                mission.to_dict()
                for mission in self.operations_service.missions()
            ],
            "resources": lambda: self.operations_service.resources().to_dict(),
            "timeline": lambda: self.operations_service.timeline(limit=100).to_dict(),
            "events": lambda: [
                event.to_dict()
                for event in self.operations_service.event_registry.list_events(limit=100)
            ],
        }

        for name, build in projections.items():
            try:
                data[name] = build()
            except Exception as exc:
                data[name] = None
                errors.append(f"{name}: {exc}")

        if errors and health.status == ProjectionStatus.AVAILABLE:
            health = ProjectionHealth(
                status=ProjectionStatus.DEGRADED,
                summary="Operations projection completed with partial failures.",
                details=health.details,
                warnings=tuple(errors),
            )
        elif errors:
            warnings.extend(errors)

        return ProjectionEnvelope(
            projection_id=self.projection_id,
            schema_version=self.schema_version,
            generated_at=generated_at,
            source_timestamp=None,
            provider=f"{self.__class__.__module__}.{self.__class__.__qualname__}",
            health=health,
            data=data,
            warnings=tuple(warnings),
            errors=tuple(errors),
        )

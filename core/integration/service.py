"""Services for the legacy Integration analysis plane and projection plane."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit import RepositoryIntegrationAuditor
from .catalog import build_genesis_iv_capability_registry
from .contracts import (
    ExecutiveProjection,
    ProjectionEnvelope,
    ProjectionHealth,
    ProjectionStatus,
)
from .errors import ProjectionExecutionError
from .knowledge import build_knowledge_readiness
from .projections import build_mission_control_projection
from .registry import ProjectionRegistry


class ExecutiveProjectionService:
    """Execute registered providers and assemble executive projections.

    Typed APIs:
        projection()
        projection_envelopes()
        executive_projection()
        snapshot()

    Historical compatibility API:
        all_projections()
    """

    def __init__(self, registry: ProjectionRegistry) -> None:
        if not isinstance(registry, ProjectionRegistry):
            raise TypeError("registry must be a ProjectionRegistry")
        self._registry = registry

    @property
    def registry(self) -> ProjectionRegistry:
        return self._registry

    @staticmethod
    def _qualified_type(value: object) -> str:
        cls = value.__class__
        return f"{cls.__module__}.{cls.__qualname__}"

    def projection(
        self,
        projection_id: str,
        *,
        strict: bool = False,
    ) -> ProjectionEnvelope:
        """Return one canonical provider envelope."""

        provider = self._registry.get(projection_id)

        try:
            envelope = provider.project()
        except Exception as exc:
            if strict:
                raise ProjectionExecutionError(
                    f"{projection_id}: {exc}"
                ) from exc

            return ProjectionEnvelope(
                projection_id=projection_id,
                schema_version=str(
                    getattr(provider, "schema_version", "unknown")
                ),
                generated_at=datetime.now(timezone.utc),
                source_timestamp=None,
                provider=self._qualified_type(provider),
                health=ProjectionHealth(
                    status=ProjectionStatus.UNAVAILABLE,
                    summary=f"{projection_id} projection failed.",
                    errors=(str(exc),),
                ),
                data={},
                errors=(str(exc),),
            )

        if not isinstance(envelope, ProjectionEnvelope):
            raise ProjectionExecutionError(
                f"{projection_id}: provider returned "
                f"{type(envelope).__name__}, expected ProjectionEnvelope"
            )

        if envelope.projection_id != projection_id:
            raise ProjectionExecutionError(
                f"{projection_id}: provider returned mismatched "
                f"projection_id {envelope.projection_id!r}"
            )

        return envelope

    def get(
        self,
        projection_id: str,
        *,
        strict: bool = False,
    ) -> ProjectionEnvelope:
        """Compatibility alias for projection()."""

        return self.projection(projection_id, strict=strict)

    def projection_envelopes(
        self,
        *,
        strict: bool = False,
    ) -> tuple[ProjectionEnvelope, ...]:
        """Return canonical envelopes in deterministic provider order."""

        return tuple(
            self.projection(provider.projection_id, strict=strict)
            for provider in self._registry.all()
        )

    def executive_projection(
        self,
        *,
        strict: bool = False,
    ) -> ExecutiveProjection:
        """Return the canonical typed aggregate."""

        return ExecutiveProjection.from_envelopes(
            self.projection_envelopes(strict=strict)
        )

    def snapshot(
        self,
        *,
        strict: bool = False,
    ) -> ExecutiveProjection:
        """Return the canonical typed executive snapshot."""

        return self.executive_projection(strict=strict)

    @staticmethod
    def _compatibility_summary(
        envelopes: tuple[ProjectionEnvelope, ...],
    ) -> dict[str, int]:
        counts = {
            status.value: 0
            for status in ProjectionStatus
        }

        for envelope in envelopes:
            counts[envelope.health.status.value] += 1

        return counts

    def all_projections(
        self,
        *,
        strict: bool = False,
    ) -> dict[str, Any]:
        """Return the historical UI compatibility dictionary.

        Canonical ProjectionEnvelope objects are created exactly once and then
        serialized for legacy consumers.
        """

        envelopes = self.projection_envelopes(strict=strict)

        aggregate = ExecutiveProjection.from_envelopes(envelopes)

        counts = {
            status.value: 0
            for status in ProjectionStatus
        }

        for envelope in envelopes:
            counts[envelope.health.status.value] += 1

        return {
            "generated_at": aggregate.generated_at.isoformat(),
            "provider_count": len(envelopes),
            "overall_status": aggregate.overall_status.value,
            "summary": counts,
            "projections": [
                envelope.to_dict()
                for envelope in envelopes
            ],
            "warnings": list(aggregate.warnings),
            "errors": list(aggregate.errors),
            "metadata": dict(aggregate.metadata),
        }

    def to_dict(self, *, strict: bool = False) -> dict[str, Any]:
        """Serialize the canonical aggregate without changing its semantics."""

        return self.executive_projection(strict=strict).to_dict()


class ExecutiveIntegrationService:
    """Legacy repository-analysis service retained for compatibility."""

    def __init__(self, repository_root: Path) -> None:
        self._root = repository_root.resolve()
        self._registry = build_genesis_iv_capability_registry()
        self._auditor = RepositoryIntegrationAuditor()

    def integration_health(self):
        return self._auditor.audit(self._root, self._registry)

    def knowledge_readiness(self, query, **kwargs):
        return build_knowledge_readiness(query=query, **kwargs)

    def mission_control(self, **kwargs):
        return build_mission_control_projection(
            self.integration_health(),
            **kwargs,
        )


__all__ = [
    "ExecutiveIntegrationService",
    "ExecutiveProjectionService",
]

"""Persistence-aware cognitive workspace integration service."""

from __future__ import annotations

from dataclasses import replace

from core.cognition.integration.contracts import WorkspaceIntegrationRequest
from core.cognition.integration.models import WorkspaceIntegrationResult
from core.cognition.integration.pipeline import WorkspaceIntegrationPipeline
from core.cognition.workspace import CognitiveWorkspaceRepository


class CognitiveWorkspaceIntegrationService:
    """Create, resume, integrate, and persist cognitive workspaces."""

    def __init__(
        self,
        repository: CognitiveWorkspaceRepository,
        *,
        pipeline: WorkspaceIntegrationPipeline | None = None,
    ) -> None:
        self._repository = repository
        self._pipeline = pipeline or WorkspaceIntegrationPipeline()

    def integrate(self, request: WorkspaceIntegrationRequest) -> WorkspaceIntegrationResult:
        existing = None
        expected_revision = None
        if request.workspace_id is not None and self._repository.exists(request.workspace_id):
            existing = self._repository.get(request.workspace_id)
            expected_revision = existing.revision

        result = self._pipeline.apply(request, workspace=existing)
        if existing is not None and result.workspace.revision == existing.revision:
            return replace(result, persisted=True)

        self._repository.save(
            result.workspace,
            expected_revision=expected_revision,
        )
        return replace(result, persisted=True)

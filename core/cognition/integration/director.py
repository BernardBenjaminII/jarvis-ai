"""Thin executive-facing director for cognitive workspace integration."""

from __future__ import annotations

from core.cognition.integration.contracts import WorkspaceIntegrationRequest
from core.cognition.integration.models import WorkspaceIntegrationResult
from core.cognition.integration.service import CognitiveWorkspaceIntegrationService


class CognitiveWorkspaceIntegrationDirector:
    """Stable orchestration boundary for future Executive integration."""

    def __init__(self, service: CognitiveWorkspaceIntegrationService) -> None:
        self._service = service

    def execute(self, request: WorkspaceIntegrationRequest) -> WorkspaceIntegrationResult:
        return self._service.integrate(request)

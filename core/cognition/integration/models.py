"""Result models for cognitive workspace integration."""

from __future__ import annotations

from dataclasses import dataclass

from core.cognition.workspace import CognitiveWorkspace, WorkspaceSnapshot


@dataclass(frozen=True, slots=True)
class WorkspaceIntegrationResult:
    """One immutable, inspectable integration outcome."""

    workspace: CognitiveWorkspace
    snapshot: WorkspaceSnapshot
    created: bool
    persisted: bool
    applied_hypotheses: int
    applied_evidence: int
    applied_assumptions: int
    applied_questions: int

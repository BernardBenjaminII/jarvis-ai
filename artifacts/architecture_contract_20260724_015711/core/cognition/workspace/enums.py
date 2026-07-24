"""Enumerations for the cognitive workspace."""

from __future__ import annotations

from enum import StrEnum


class WorkspaceStatus(StrEnum):
    """Lifecycle state of a cognitive workspace."""

    OPEN = "open"
    SUSPENDED = "suspended"
    RESOLVED = "resolved"
    ABANDONED = "abandoned"


class HypothesisStatus(StrEnum):
    """Evaluation state of a hypothesis."""

    PROPOSED = "proposed"
    ACTIVE = "active"
    SUPPORTED = "supported"
    WEAKENED = "weakened"
    REJECTED = "rejected"
    RESOLVED = "resolved"


class WorkspaceEventKind(StrEnum):
    """Auditable cognitive workspace event type."""

    WORKSPACE_CREATED = "workspace_created"
    HYPOTHESIS_ADDED = "hypothesis_added"
    HYPOTHESIS_STATUS_CHANGED = "hypothesis_status_changed"
    EVIDENCE_ATTACHED = "evidence_attached"
    ASSUMPTION_ADDED = "assumption_added"
    QUESTION_OPENED = "question_opened"
    QUESTION_RESOLVED = "question_resolved"
    WORKSPACE_STATUS_CHANGED = "workspace_status_changed"
    NOTE_RECORDED = "note_recorded"

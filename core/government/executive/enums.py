"""Executive integration vocabularies for Genesis VIII-A0-5."""

from __future__ import annotations

from enum import Enum


class AssessmentState(str, Enum):
    UNKNOWN = "unknown"
    NOMINAL = "nominal"
    ATTENTION = "attention"
    DEGRADED = "degraded"
    CRITICAL = "critical"


class RecommendationPriority(str, Enum):
    ROUTINE = "routine"
    IMPORTANT = "important"
    URGENT = "urgent"
    CRITICAL = "critical"


class RecommendationState(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    COMPLETED = "completed"


class DirectiveState(str, Enum):
    DRAFT = "draft"
    AUTHORIZED = "authorized"
    ISSUED = "issued"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AssignmentState(str, Enum):
    PROPOSED = "proposed"
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

"""Canonical enums for JARVIS mission planning."""

from __future__ import annotations

from enum import StrEnum


class PlanState(StrEnum):
    """Canonical mission-plan lifecycle states."""

    DRAFT = "draft"
    CONTEXT_GATHERING = "context_gathering"
    AWAITING_INFORMATION = "awaiting_information"
    CANDIDATE = "candidate"
    UNDER_REVIEW = "under_review"
    REVISION_REQUIRED = "revision_required"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    REPLANNING = "replanning"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"
    ARCHIVED = "archived"


class MissionPriority(StrEnum):
    """Mission scheduling and executive-arbitration priority."""

    ROUTINE = "routine"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class AuthorizationMode(StrEnum):
    """Authorization required before an element may be executed."""

    PLANNING_ONLY = "planning_only"
    COMMANDER_APPROVAL = "commander_approval"
    DELEGATED_APPROVAL = "delegated_approval"
    POLICY_APPROVAL = "policy_approval"
    STANDING_AUTHORIZATION = "standing_authorization"
    AUTOMATIC_WITHIN_BOUNDS = "automatic_within_bounds"
    PROHIBITED = "prohibited"


class RiskLevel(StrEnum):
    """Canonical planning-risk severity."""

    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    CRITICAL = "critical"


class RiskStatus(StrEnum):
    """Current treatment status of a planning risk."""

    IDENTIFIED = "identified"
    ACCEPTED = "accepted"
    MITIGATED = "mitigated"
    TRANSFERRED = "transferred"
    AVOIDED = "avoided"
    MATERIALIZED = "materialized"
    CLOSED = "closed"


class ConstraintKind(StrEnum):
    """Categories of mission-planning constraints."""

    TIME = "time"
    COST = "cost"
    RESOURCE = "resource"
    SECURITY = "security"
    PRIVACY = "privacy"
    SAFETY = "safety"
    POLICY = "policy"
    LEGAL = "legal"
    PLATFORM = "platform"
    GEOGRAPHIC = "geographic"
    DATA = "data"
    CAPABILITY = "capability"
    AUTHORIZATION = "authorization"
    OTHER = "other"


class DependencyType(StrEnum):
    """Relationship between two plan elements."""

    FINISH_TO_START = "finish_to_start"
    START_TO_START = "start_to_start"
    FINISH_TO_FINISH = "finish_to_finish"
    START_TO_FINISH = "start_to_finish"
    INFORMATION = "information"
    RESOURCE = "resource"
    AUTHORIZATION = "authorization"


class ResourceKind(StrEnum):
    """Kinds of resources required by a plan element."""

    HUMAN = "human"
    CAPABILITY = "capability"
    DEVICE = "device"
    COMPUTE = "compute"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    POWER = "power"
    TIME = "time"
    FINANCIAL = "financial"
    DATA = "data"
    OTHER = "other"


class PlanElementKind(StrEnum):
    """Canonical plan hierarchy element kinds."""

    MISSION = "mission"
    OBJECTIVE = "objective"
    TASK = "task"
    ACTIVITY = "activity"
    COMMAND = "command"

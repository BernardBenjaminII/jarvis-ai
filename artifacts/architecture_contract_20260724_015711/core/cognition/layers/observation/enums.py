from __future__ import annotations

from enum import Enum


class ObservationLifecycleState(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    RETIRED = "retired"
    REJECTED = "rejected"


class ObservationSourceMode(str, Enum):
    DIRECT = "direct"
    SENSOR = "sensor"
    DOCUMENT = "document"
    TESTIMONY = "testimony"
    SYSTEM = "system"
    IMPORTED = "imported"


class ObservationRelationType(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    DUPLICATES = "duplicates"
    SUPERSEDES = "supersedes"
    REFINES = "refines"
    DERIVED_FROM = "derived_from"


__all__ = (
    "ObservationLifecycleState",
    "ObservationRelationType",
    "ObservationSourceMode",
)

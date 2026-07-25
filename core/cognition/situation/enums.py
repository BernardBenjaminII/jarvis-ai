"""Enumerations for Genesis IV-A2 Executive Situation Model."""

from __future__ import annotations

from enum import Enum


class SituationStatus(str, Enum):
    """Lifecycle status of an executive situation."""

    OPEN = "open"
    STABLE = "stable"
    ESCALATING = "escalating"
    RESOLVED = "resolved"
    ARCHIVED = "archived"


class SituationRelationType(str, Enum):
    """Explicit relation between observations in a situation."""

    CORRELATED = "correlated"
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CAUSED_BY = "caused_by"
    CAUSES = "causes"
    DUPLICATES = "duplicates"


class SituationDisposition(str, Enum):
    """Repository publication result."""

    CREATED = "created"
    DUPLICATE = "duplicate"
    REPLACED = "replaced"

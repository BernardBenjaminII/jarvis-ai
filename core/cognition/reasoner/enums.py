"""Enumerations for Genesis IV-A5 Executive Reasoner."""

from __future__ import annotations

from enum import Enum


class ReasoningDisposition(str, Enum):
    """Final disposition of an executive reasoning result."""

    SELECTED = "selected"
    DEFERRED = "deferred"
    INCONCLUSIVE = "inconclusive"
    CONTESTED = "contested"


class ReasoningStatus(str, Enum):
    """Lifecycle state of a reasoning result."""

    PROVISIONAL = "provisional"
    COMPLETE = "complete"
    ARCHIVED = "archived"


class ReasoningRepositoryDisposition(str, Enum):
    """Repository insertion result."""

    CREATED = "created"
    DUPLICATE = "duplicate"

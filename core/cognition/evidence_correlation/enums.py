"""Enumerations for Genesis IV-A4 Executive Evidence Correlation Engine."""

from __future__ import annotations

from enum import Enum


class EvidencePolarity(str, Enum):
    """How an evidence item bears on a hypothesis."""

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    NEUTRAL = "neutral"


class EvidenceStrength(str, Enum):
    """Normalized qualitative strength of an evidence item."""

    TRACE = "trace"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    DECISIVE = "decisive"


class AssessmentStatus(str, Enum):
    """Lifecycle state of an evidence assessment."""

    PROVISIONAL = "provisional"
    COMPLETE = "complete"
    INCONCLUSIVE = "inconclusive"
    CONTESTED = "contested"
    ARCHIVED = "archived"


class AssessmentDisposition(str, Enum):
    """Repository insertion result."""

    CREATED = "created"
    DUPLICATE = "duplicate"

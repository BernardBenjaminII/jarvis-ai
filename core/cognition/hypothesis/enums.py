"""Enumerations for Genesis IV-A3 Executive Hypothesis Engine."""

from __future__ import annotations

from enum import Enum


class HypothesisStatus(str, Enum):
    """Lifecycle state of an executive hypothesis."""

    PROPOSED = "proposed"
    ACTIVE = "active"
    SUPPORTED = "supported"
    WEAKENED = "weakened"
    REJECTED = "rejected"
    CONFIRMED = "confirmed"
    ARCHIVED = "archived"


class HypothesisKind(str, Enum):
    """High-level purpose of a hypothesis."""

    EXPLANATORY = "explanatory"
    CAUSAL = "causal"
    PREDICTIVE = "predictive"
    DIAGNOSTIC = "diagnostic"
    OPERATIONAL = "operational"


class HypothesisDisposition(str, Enum):
    """Repository insertion result."""

    CREATED = "created"
    DUPLICATE = "duplicate"

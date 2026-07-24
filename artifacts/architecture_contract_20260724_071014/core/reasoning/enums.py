"""Enumerations for the JARVIS Reasoning Engine foundation."""

from __future__ import annotations

from enum import StrEnum


class EvidenceKind(StrEnum):
    """Origin or semantic class of evidence."""

    FACT = "fact"
    OBSERVATION = "observation"
    TESTIMONY = "testimony"
    DOCUMENT = "document"
    MEASUREMENT = "measurement"
    INFERENCE = "inference"


class EvidenceStance(StrEnum):
    """How an evidence item bears on a proposition or hypothesis."""

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    NEUTRAL = "neutral"


class HypothesisDisposition(StrEnum):
    """Deterministic assessment state for a candidate hypothesis."""

    SUPPORTED = "supported"
    TENTATIVE = "tentative"
    INSUFFICIENT = "insufficient"
    REJECTED = "rejected"


class ReasoningStatus(StrEnum):
    """Lifecycle state of a reasoning result."""

    COMPLETED = "completed"
    INCONCLUSIVE = "inconclusive"

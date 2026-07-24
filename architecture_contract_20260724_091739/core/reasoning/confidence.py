"""Deterministic confidence calculations for JARVIS reasoning."""

from __future__ import annotations

from collections.abc import Iterable

from core.reasoning.enums import HypothesisDisposition
from core.reasoning.models import EvidenceItem


def rounded(value: float) -> float:
    """Normalize floating-point output for stable serialization."""

    return round(value, 6)


def total_weight(items: Iterable[EvidenceItem]) -> float:
    """Return the sum of reliability-adjusted confidence weights."""

    return rounded(sum(item.weight for item in items))


def hypothesis_confidence(
    support_score: float,
    contradiction_score: float,
    assumption_count: int,
) -> float:
    """Calculate conservative confidence for a hypothesis.

    Assumptions add explicit uncertainty rather than being ignored.
    """

    uncertainty = assumption_count * 0.25
    denominator = support_score + contradiction_score + uncertainty

    if denominator == 0.0:
        return 0.0

    return rounded(support_score / denominator)


def classify_disposition(
    support_score: float,
    contradiction_score: float,
    confidence: float,
) -> HypothesisDisposition:
    """Map deterministic scores into an assessment disposition."""

    if contradiction_score > support_score:
        return HypothesisDisposition.REJECTED

    if support_score == 0.0:
        return HypothesisDisposition.INSUFFICIENT

    if confidence >= 0.67:
        return HypothesisDisposition.SUPPORTED

    return HypothesisDisposition.TENTATIVE

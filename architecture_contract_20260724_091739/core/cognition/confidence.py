"""Constitutional confidence policy for Genesis IV-A1 observations.

Confidence measures the quality of the direct observation record. It does not
measure the probability that an inferred conclusion is correct.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Final

from .contracts import normalize_confidence
from .enums import ConfidenceBand, ObservationOrigin
from .errors import CognitionValidationError

_ZERO: Final[Decimal] = Decimal("0")
_ONE: Final[Decimal] = Decimal("1")


class SourceReliability(str, Enum):
    """Conservative source-quality classifications."""

    UNKNOWN = "unknown"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    AUTHORITATIVE = "authoritative"


class ExtractionQuality(str, Enum):
    """Quality of the extraction operation itself."""

    UNCERTAIN = "uncertain"
    PARTIAL = "partial"
    CLEAR = "clear"
    EXACT = "exact"


@dataclass(frozen=True, slots=True)
class ConfidenceFactors:
    """Inputs to deterministic observation-confidence calculation."""

    origin: ObservationOrigin = ObservationOrigin.DIRECT_EXTRACTION
    source_reliability: SourceReliability = SourceReliability.UNKNOWN
    extraction_quality: ExtractionQuality = ExtractionQuality.CLEAR
    has_exact_offsets: bool = False
    has_excerpt: bool = False
    has_evidence_reference: bool = False
    normalization_changed_meaning: bool = False
    source_conflict_detected: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.origin, ObservationOrigin):
            try:
                object.__setattr__(
                    self,
                    "origin",
                    ObservationOrigin(str(self.origin)),
                )
            except ValueError as exc:
                raise CognitionValidationError(
                    f"Unsupported observation origin: {self.origin!r}"
                ) from exc

        if not isinstance(self.source_reliability, SourceReliability):
            try:
                object.__setattr__(
                    self,
                    "source_reliability",
                    SourceReliability(str(self.source_reliability)),
                )
            except ValueError as exc:
                raise CognitionValidationError(
                    "Unsupported source reliability: "
                    f"{self.source_reliability!r}"
                ) from exc

        if not isinstance(self.extraction_quality, ExtractionQuality):
            try:
                object.__setattr__(
                    self,
                    "extraction_quality",
                    ExtractionQuality(str(self.extraction_quality)),
                )
            except ValueError as exc:
                raise CognitionValidationError(
                    "Unsupported extraction quality: "
                    f"{self.extraction_quality!r}"
                ) from exc


@dataclass(frozen=True, slots=True)
class ConfidenceAssessment:
    """Explainable deterministic confidence result."""

    score: Decimal
    band: ConfidenceBand
    reasons: tuple[str, ...]


_ORIGIN_BASE: Final[dict[ObservationOrigin, Decimal]] = {
    ObservationOrigin.DIRECT_EXTRACTION: Decimal("0.60"),
    ObservationOrigin.STRUCTURED_INPUT: Decimal("0.72"),
    ObservationOrigin.OPERATOR_ENTRY: Decimal("0.55"),
}

_SOURCE_ADJUSTMENT: Final[dict[SourceReliability, Decimal]] = {
    SourceReliability.UNKNOWN: Decimal("0.00"),
    SourceReliability.LOW: Decimal("-0.15"),
    SourceReliability.MODERATE: Decimal("0.05"),
    SourceReliability.HIGH: Decimal("0.12"),
    SourceReliability.AUTHORITATIVE: Decimal("0.18"),
}

_EXTRACTION_ADJUSTMENT: Final[dict[ExtractionQuality, Decimal]] = {
    ExtractionQuality.UNCERTAIN: Decimal("-0.22"),
    ExtractionQuality.PARTIAL: Decimal("-0.10"),
    ExtractionQuality.CLEAR: Decimal("0.08"),
    ExtractionQuality.EXACT: Decimal("0.15"),
}


def clamp_confidence(value: Decimal) -> Decimal:
    """Clamp a confidence value to the constitutional zero-to-one range."""

    if value < _ZERO:
        return _ZERO

    if value > _ONE:
        return _ONE

    return value


def confidence_band(score: Decimal | str | int) -> ConfidenceBand:
    """Map normalized confidence to a stable human-readable band."""

    normalized = normalize_confidence(score)

    if normalized < Decimal("0.20"):
        return ConfidenceBand.VERY_LOW

    if normalized < Decimal("0.40"):
        return ConfidenceBand.LOW

    if normalized < Decimal("0.65"):
        return ConfidenceBand.MODERATE

    if normalized < Decimal("0.85"):
        return ConfidenceBand.HIGH

    return ConfidenceBand.VERY_HIGH


def assess_confidence(
    factors: ConfidenceFactors,
) -> ConfidenceAssessment:
    """Calculate deterministic observation confidence with explanations."""

    if not isinstance(factors, ConfidenceFactors):
        raise CognitionValidationError(
            "factors must be a ConfidenceFactors instance."
        )

    score = _ORIGIN_BASE[factors.origin]
    reasons: list[str] = [
        f"origin:{factors.origin.value}",
    ]

    source_adjustment = _SOURCE_ADJUSTMENT[factors.source_reliability]
    score += source_adjustment
    reasons.append(
        f"source_reliability:{factors.source_reliability.value}"
    )

    extraction_adjustment = _EXTRACTION_ADJUSTMENT[
        factors.extraction_quality
    ]
    score += extraction_adjustment
    reasons.append(
        f"extraction_quality:{factors.extraction_quality.value}"
    )

    if factors.has_exact_offsets:
        score += Decimal("0.05")
        reasons.append("provenance:exact_offsets")

    if factors.has_excerpt:
        score += Decimal("0.04")
        reasons.append("provenance:excerpt")

    if factors.has_evidence_reference:
        score += Decimal("0.06")
        reasons.append("provenance:evidence_reference")

    if factors.normalization_changed_meaning:
        score -= Decimal("0.35")
        reasons.append("penalty:normalization_changed_meaning")

    if factors.source_conflict_detected:
        score -= Decimal("0.20")
        reasons.append("penalty:source_conflict_detected")

    normalized_score = normalize_confidence(clamp_confidence(score))

    return ConfidenceAssessment(
        score=normalized_score,
        band=confidence_band(normalized_score),
        reasons=tuple(reasons),
    )


def confidence_for_direct_source(
    *,
    origin: ObservationOrigin = ObservationOrigin.DIRECT_EXTRACTION,
    source_reliability: SourceReliability = SourceReliability.UNKNOWN,
    extraction_quality: ExtractionQuality = ExtractionQuality.CLEAR,
    has_exact_offsets: bool = False,
    has_excerpt: bool = False,
    has_evidence_reference: bool = False,
) -> ConfidenceAssessment:
    """Convenience policy for ordinary direct observations."""

    return assess_confidence(
        ConfidenceFactors(
            origin=origin,
            source_reliability=source_reliability,
            extraction_quality=extraction_quality,
            has_exact_offsets=has_exact_offsets,
            has_excerpt=has_excerpt,
            has_evidence_reference=has_evidence_reference,
        )
    )

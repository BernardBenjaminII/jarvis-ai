"""Operational Genesis IV-A1 observation construction service."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from .confidence import (
    ConfidenceAssessment,
    ConfidenceFactors,
    SourceReliability,
    assess_confidence,
    confidence_band,
)
from .contracts import (
    Observation,
    ObservationValue,
    SourceReference,
    normalize_confidence,
    normalize_metadata,
)
from .enums import ObservationValueKind
from .errors import CognitionValidationError
from .extraction import (
    ExtractionResult,
    ExtractionSource,
    ObservationCandidate,
    extract_candidates,
)
from .normalization import (
    NormalizedObservationValue,
    normalize_concept,
    normalize_identifier_token,
    normalize_observation_value,
)
from .validation import validate_observation


@dataclass(frozen=True, slots=True)
class ObservationConstruction:
    """Explainable result of committing one observation candidate."""

    observation: Observation
    candidate: ObservationCandidate
    normalized_value: NormalizedObservationValue
    confidence_assessment: ConfidenceAssessment


@dataclass(frozen=True, slots=True)
class ObservationBatch:
    """Result of extracting and committing observations from one source."""

    extraction: ExtractionResult
    constructions: tuple[ObservationConstruction, ...]

    @property
    def observations(self) -> tuple[Observation, ...]:
        """Return committed immutable observations."""

        return tuple(
            construction.observation
            for construction in self.constructions
        )


class ObservationEngine:
    """Deterministic service for extracting and committing observations."""

    def __init__(
        self,
        *,
        default_source_reliability: SourceReliability = SourceReliability.UNKNOWN,
    ) -> None:
        if not isinstance(default_source_reliability, SourceReliability):
            try:
                default_source_reliability = SourceReliability(
                    str(default_source_reliability)
                )
            except ValueError as exc:
                raise CognitionValidationError(
                    "Unsupported default source reliability: "
                    f"{default_source_reliability!r}"
                ) from exc

        self._default_source_reliability = default_source_reliability

    @property
    def default_source_reliability(self) -> SourceReliability:
        """Return the engine's default source-reliability policy."""

        return self._default_source_reliability

    def assess_candidate_confidence(
        self,
        candidate: ObservationCandidate,
        *,
        source_reliability: SourceReliability | None = None,
    ) -> ConfidenceAssessment:
        """Assess candidate quality without considering inferred truth."""

        if not isinstance(candidate, ObservationCandidate):
            raise CognitionValidationError(
                "candidate must be an ObservationCandidate."
            )

        if candidate.supplied_confidence is not None:
            supplied = normalize_confidence(
                candidate.supplied_confidence
            )

            return ConfidenceAssessment(
                score=supplied,
                band=confidence_band(supplied),
                reasons=("confidence:explicitly_supplied",),
            )

        reliability = (
            self._default_source_reliability
            if source_reliability is None
            else source_reliability
        )

        if not isinstance(reliability, SourceReliability):
            reliability = SourceReliability(str(reliability))

        source = candidate.source

        return assess_confidence(
            ConfidenceFactors(
                origin=candidate.origin,
                source_reliability=reliability,
                extraction_quality=candidate.extraction_quality,
                has_exact_offsets=(
                    source.start_offset is not None
                    and source.end_offset is not None
                ),
                has_excerpt=bool(source.text),
                has_evidence_reference=bool(source.evidence_ids),
            )
        )

    def normalize_candidate_value(
        self,
        candidate: ObservationCandidate,
    ) -> NormalizedObservationValue:
        """Normalize a candidate value without changing its meaning."""

        if not isinstance(candidate, ObservationCandidate):
            raise CognitionValidationError(
                "candidate must be an ObservationCandidate."
            )

        return normalize_observation_value(
            candidate.raw_value,
            kind=candidate.value_kind,
            unit=candidate.unit,
        )

    def commit_candidate(
        self,
        candidate: ObservationCandidate,
        *,
        source_reliability: SourceReliability | None = None,
    ) -> ObservationConstruction:
        """Commit a validated candidate as an immutable observation."""

        if not isinstance(candidate, ObservationCandidate):
            raise CognitionValidationError(
                "candidate must be an ObservationCandidate."
            )

        normalized_value = self.normalize_candidate_value(candidate)
        assessment = self.assess_candidate_confidence(
            candidate,
            source_reliability=source_reliability,
        )

        observation_value = ObservationValue(
            kind=normalized_value.kind,
            value=normalized_value.source_value,
            normalized_value=normalized_value.normalized_value,
            unit=normalized_value.unit,
        )

        source_reference = SourceReference(
            source_id=candidate.source.source_id,
            segment_id=candidate.source.segment_id,
            start_offset=candidate.source.start_offset,
            end_offset=candidate.source.end_offset,
            excerpt=candidate.source.text,
            evidence_ids=candidate.source.evidence_ids,
        )

        merged_metadata = {}

        merged_metadata.update(dict(candidate.source.metadata))
        merged_metadata.update(dict(candidate.metadata))

        merged_metadata["confidence_band"] = assessment.band.value
        merged_metadata["extraction_pattern"] = (
            candidate.extraction_pattern.value
        )
        merged_metadata["extraction_quality"] = (
            candidate.extraction_quality.value
        )

        combined_metadata = normalize_metadata(merged_metadata)

        observation = Observation.create(
            subject=normalize_concept(candidate.subject),
            predicate=normalize_identifier_token(candidate.predicate),
            value=observation_value,
            source=source_reference,
            polarity=candidate.polarity,
            origin=candidate.origin,
            confidence=assessment.score,
            metadata=combined_metadata,
        )

        validate_observation(observation)

        return ObservationConstruction(
            observation=observation,
            candidate=candidate,
            normalized_value=normalized_value,
            confidence_assessment=assessment,
        )

    def commit_candidates(
        self,
        candidates: Iterable[ObservationCandidate],
        *,
        source_reliability: SourceReliability | None = None,
    ) -> tuple[ObservationConstruction, ...]:
        """Commit candidates deterministically while preserving input order."""

        return tuple(
            self.commit_candidate(
                candidate,
                source_reliability=source_reliability,
            )
            for candidate in candidates
        )

    def observe(
        self,
        source: ExtractionSource,
        *,
        source_reliability: SourceReliability | None = None,
    ) -> ObservationBatch:
        """Extract and commit all supported observations from one source."""

        extraction = extract_candidates(source)

        constructions = self.commit_candidates(
            extraction.candidates,
            source_reliability=source_reliability,
        )

        return ObservationBatch(
            extraction=extraction,
            constructions=constructions,
        )


def build_observation(
    candidate: ObservationCandidate,
    *,
    source_reliability: SourceReliability = SourceReliability.UNKNOWN,
) -> Observation:
    """Build one immutable observation with the default engine."""

    engine = ObservationEngine(
        default_source_reliability=source_reliability,
    )

    return engine.commit_candidate(candidate).observation


def observe_source(
    source: ExtractionSource,
    *,
    source_reliability: SourceReliability = SourceReliability.UNKNOWN,
) -> ObservationBatch:
    """Extract and commit observations using the default engine."""

    engine = ObservationEngine(
        default_source_reliability=source_reliability,
    )

    return engine.observe(source)

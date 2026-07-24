"""Deterministic candidate extraction for Genesis IV-A1.

This module recognizes deliberately narrow source patterns. Unrecognized text
is returned as an extraction miss rather than being guessed or interpreted.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Final, Iterable

from .confidence import ExtractionQuality
from .enums import (
    ObservationOrigin,
    ObservationPolarity,
    ObservationValueKind,
)
from .errors import CognitionValidationError
from .normalization import (
    infer_value_kind,
    normalize_concept,
    normalize_display_text,
    normalize_identifier_token,
)

_COPULAR_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"""
    ^\s*
    (?P<subject>
        [A-Za-z0-9][A-Za-z0-9 _./()\-]{0,199}?
    )
    \s+
    (?P<verb>
        is|are|was|were|equals?|measures?|reads?|reports?|shows?
    )
    \s+
    (?P<value>
        .+?
    )
    \s*[.!?]?\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

_POSSESSIVE_PROPERTY_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"""
    ^\s*
    (?P<subject>
        [A-Za-z0-9][A-Za-z0-9 _./()\-]{0,149}?
    )
    (?:'s|\s+)
    (?P<predicate>
        [A-Za-z][A-Za-z0-9 _./()\-]{0,99}?
    )
    \s+
    (?P<verb>
        is|was|equals?|measures?|reads?
    )
    \s+
    (?P<value>
        .+?
    )
    \s*[.!?]?\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

_PROPERTY_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"""
    ^\s*
    (?P<subject>
        [A-Za-z0-9][A-Za-z0-9 _./()\-]{0,99}?
    )
    \s+
    (?P<predicate>
        voltage|temperature|pressure|speed|status|state|level|count|
        capacity|frequency|weight|mass|length|width|height|duration|
        version|mode|address|identifier|name|type|value|reading
    )
    \s+
    (?P<verb>
        is|was|equals?|measures?|reads?|reports?|shows?
    )
    \s+
    (?P<value>
        .+?
    )
    \s*[.!?]?\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

_KEY_VALUE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"""
    ^\s*
    (?P<key>
        [A-Za-z][A-Za-z0-9 _./()\-]{0,199}?
    )
    \s*[:=]\s*
    (?P<value>
        .+?
    )
    \s*$
    """,
    re.VERBOSE,
)

_NEGATION_PREFIX_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(?:not|no|never)\s+",
    re.IGNORECASE,
)


class ExtractionPattern(str, Enum):
    """Supported deterministic extraction patterns."""

    PROPERTY_STATEMENT = "property_statement"
    POSSESSIVE_PROPERTY = "possessive_property"
    COPULAR_STATEMENT = "copular_statement"
    KEY_VALUE = "key_value"
    STRUCTURED = "structured"


@dataclass(frozen=True, slots=True)
class ExtractionSource:
    """Minimal source material supplied to the extraction layer."""

    source_id: str
    text: str
    segment_id: str | None = None
    start_offset: int | None = None
    end_offset: int | None = None
    evidence_ids: tuple[str, ...] = ()
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        source_id = normalize_display_text(self.source_id)
        text = normalize_display_text(self.text)

        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "text", text)

        if self.segment_id is not None:
            object.__setattr__(
                self,
                "segment_id",
                normalize_display_text(self.segment_id),
            )

        if not isinstance(self.evidence_ids, tuple):
            object.__setattr__(
                self,
                "evidence_ids",
                tuple(self.evidence_ids),
            )

        normalized_evidence_ids = tuple(
            sorted(
                {
                    normalize_display_text(value)
                    for value in self.evidence_ids
                }
            )
        )
        object.__setattr__(
            self,
            "evidence_ids",
            normalized_evidence_ids,
        )

        if not isinstance(self.metadata, tuple):
            object.__setattr__(
                self,
                "metadata",
                tuple(self.metadata),
            )

        normalized_metadata = tuple(
            sorted(
                (
                    normalize_display_text(key),
                    normalize_display_text(value),
                )
                for key, value in self.metadata
            )
        )
        object.__setattr__(
            self,
            "metadata",
            normalized_metadata,
        )

        if (self.start_offset is None) != (self.end_offset is None):
            raise CognitionValidationError(
                "ExtractionSource offsets must be supplied together."
            )

        if self.start_offset is not None:
            if self.start_offset < 0:
                raise CognitionValidationError(
                    "ExtractionSource start_offset must not be negative."
                )

            if self.end_offset is None or self.end_offset <= self.start_offset:
                raise CognitionValidationError(
                    "ExtractionSource end_offset must exceed start_offset."
                )


@dataclass(frozen=True, slots=True)
class ObservationCandidate:
    """Uncommitted direct observation extracted from source representation."""

    subject: str
    predicate: str
    raw_value: str
    source: ExtractionSource
    value_kind: ObservationValueKind | None = None
    unit: str | None = None
    polarity: ObservationPolarity = ObservationPolarity.AFFIRMED
    origin: ObservationOrigin = ObservationOrigin.DIRECT_EXTRACTION
    extraction_pattern: ExtractionPattern = ExtractionPattern.STRUCTURED
    extraction_quality: ExtractionQuality = ExtractionQuality.EXACT
    supplied_confidence: Decimal | None = None
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "subject",
            normalize_concept(self.subject),
        )
        object.__setattr__(
            self,
            "predicate",
            normalize_identifier_token(self.predicate),
        )
        object.__setattr__(
            self,
            "raw_value",
            normalize_display_text(self.raw_value),
        )

        if not isinstance(self.source, ExtractionSource):
            raise CognitionValidationError(
                "ObservationCandidate source must be ExtractionSource."
            )

        if self.value_kind is not None and not isinstance(
            self.value_kind,
            ObservationValueKind,
        ):
            try:
                object.__setattr__(
                    self,
                    "value_kind",
                    ObservationValueKind(str(self.value_kind)),
                )
            except ValueError as exc:
                raise CognitionValidationError(
                    f"Unsupported value kind: {self.value_kind!r}"
                ) from exc

        if not isinstance(self.polarity, ObservationPolarity):
            try:
                object.__setattr__(
                    self,
                    "polarity",
                    ObservationPolarity(str(self.polarity)),
                )
            except ValueError as exc:
                raise CognitionValidationError(
                    f"Unsupported polarity: {self.polarity!r}"
                ) from exc

        if not isinstance(self.origin, ObservationOrigin):
            try:
                object.__setattr__(
                    self,
                    "origin",
                    ObservationOrigin(str(self.origin)),
                )
            except ValueError as exc:
                raise CognitionValidationError(
                    f"Unsupported origin: {self.origin!r}"
                ) from exc

        if not isinstance(self.extraction_pattern, ExtractionPattern):
            try:
                object.__setattr__(
                    self,
                    "extraction_pattern",
                    ExtractionPattern(str(self.extraction_pattern)),
                )
            except ValueError as exc:
                raise CognitionValidationError(
                    "Unsupported extraction pattern: "
                    f"{self.extraction_pattern!r}"
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

        if self.unit is not None:
            object.__setattr__(
                self,
                "unit",
                normalize_display_text(self.unit),
            )

        if not isinstance(self.metadata, tuple):
            object.__setattr__(
                self,
                "metadata",
                tuple(self.metadata),
            )

        normalized_metadata = tuple(
            sorted(
                (
                    normalize_display_text(key),
                    normalize_display_text(value),
                )
                for key, value in self.metadata
            )
        )
        object.__setattr__(
            self,
            "metadata",
            normalized_metadata,
        )


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """Deterministic extraction result that preserves misses explicitly."""

    source: ExtractionSource
    candidates: tuple[ObservationCandidate, ...]
    matched_patterns: tuple[ExtractionPattern, ...]
    rejected_reasons: tuple[str, ...]

    @property
    def matched(self) -> bool:
        """Return whether one or more candidates were extracted."""

        return bool(self.candidates)


def _strip_terminal_punctuation(value: str) -> str:
    return value.rstrip().rstrip(".!?").strip()


def _resolve_polarity(
    raw_value: str,
) -> tuple[str, ObservationPolarity]:
    normalized = normalize_display_text(raw_value)
    match = _NEGATION_PREFIX_PATTERN.match(normalized)

    if match is None:
        return normalized, ObservationPolarity.AFFIRMED

    remaining = normalized[match.end():].strip()

    if not remaining:
        return normalized, ObservationPolarity.UNCERTAIN

    return remaining, ObservationPolarity.NEGATED


def _candidate(
    *,
    source: ExtractionSource,
    subject: str,
    predicate: str,
    raw_value: str,
    extraction_pattern: ExtractionPattern,
    extraction_quality: ExtractionQuality,
) -> ObservationCandidate:
    value_without_punctuation = _strip_terminal_punctuation(raw_value)
    value, polarity = _resolve_polarity(value_without_punctuation)

    return ObservationCandidate(
        subject=subject,
        predicate=predicate,
        raw_value=value,
        source=source,
        value_kind=infer_value_kind(value),
        polarity=polarity,
        extraction_pattern=extraction_pattern,
        extraction_quality=extraction_quality,
        metadata=(
            ("extractor", "genesis_iv_a1"),
            ("pattern", extraction_pattern.value),
        ),
    )


def extract_candidates(
    source: ExtractionSource,
) -> ExtractionResult:
    """Extract direct candidates from supported deterministic text forms."""

    if not isinstance(source, ExtractionSource):
        raise CognitionValidationError(
            "source must be an ExtractionSource instance."
        )

    text = source.text
    candidates: list[ObservationCandidate] = []
    patterns: list[ExtractionPattern] = []
    rejected: list[str] = []

    property_match = _PROPERTY_PATTERN.fullmatch(text)

    if property_match is not None:
        candidate = _candidate(
            source=source,
            subject=property_match.group("subject"),
            predicate=property_match.group("predicate"),
            raw_value=property_match.group("value"),
            extraction_pattern=ExtractionPattern.PROPERTY_STATEMENT,
            extraction_quality=ExtractionQuality.EXACT,
        )
        candidates.append(candidate)
        patterns.append(ExtractionPattern.PROPERTY_STATEMENT)

        return ExtractionResult(
            source=source,
            candidates=tuple(candidates),
            matched_patterns=tuple(patterns),
            rejected_reasons=(),
        )

    possessive_match = _POSSESSIVE_PROPERTY_PATTERN.fullmatch(text)

    if possessive_match is not None:
        candidate = _candidate(
            source=source,
            subject=possessive_match.group("subject"),
            predicate=possessive_match.group("predicate"),
            raw_value=possessive_match.group("value"),
            extraction_pattern=ExtractionPattern.POSSESSIVE_PROPERTY,
            extraction_quality=ExtractionQuality.CLEAR,
        )
        candidates.append(candidate)
        patterns.append(ExtractionPattern.POSSESSIVE_PROPERTY)

        return ExtractionResult(
            source=source,
            candidates=tuple(candidates),
            matched_patterns=tuple(patterns),
            rejected_reasons=(),
        )

    key_value_match = _KEY_VALUE_PATTERN.fullmatch(text)

    if key_value_match is not None:
        key = normalize_display_text(key_value_match.group("key"))
        value = key_value_match.group("value")

        candidate = _candidate(
            source=source,
            subject=key,
            predicate="value",
            raw_value=value,
            extraction_pattern=ExtractionPattern.KEY_VALUE,
            extraction_quality=ExtractionQuality.EXACT,
        )
        candidates.append(candidate)
        patterns.append(ExtractionPattern.KEY_VALUE)

        return ExtractionResult(
            source=source,
            candidates=tuple(candidates),
            matched_patterns=tuple(patterns),
            rejected_reasons=(),
        )

    copular_match = _COPULAR_PATTERN.fullmatch(text)

    if copular_match is not None:
        candidate = _candidate(
            source=source,
            subject=copular_match.group("subject"),
            predicate="state",
            raw_value=copular_match.group("value"),
            extraction_pattern=ExtractionPattern.COPULAR_STATEMENT,
            extraction_quality=ExtractionQuality.CLEAR,
        )
        candidates.append(candidate)
        patterns.append(ExtractionPattern.COPULAR_STATEMENT)

        return ExtractionResult(
            source=source,
            candidates=tuple(candidates),
            matched_patterns=tuple(patterns),
            rejected_reasons=(),
        )

    rejected.append("no_supported_deterministic_pattern")

    return ExtractionResult(
        source=source,
        candidates=(),
        matched_patterns=(),
        rejected_reasons=tuple(rejected),
    )


def extract_many(
    sources: Iterable[ExtractionSource],
) -> tuple[ExtractionResult, ...]:
    """Extract candidates from sources while preserving source order."""

    return tuple(extract_candidates(source) for source in sources)


def structured_candidate(
    *,
    source_id: str,
    subject: str,
    predicate: str,
    value: str,
    value_kind: ObservationValueKind | str | None = None,
    unit: str | None = None,
    segment_id: str | None = None,
    start_offset: int | None = None,
    end_offset: int | None = None,
    excerpt: str | None = None,
    evidence_ids: tuple[str, ...] = (),
    polarity: ObservationPolarity = ObservationPolarity.AFFIRMED,
    origin: ObservationOrigin = ObservationOrigin.STRUCTURED_INPUT,
    extraction_quality: ExtractionQuality = ExtractionQuality.EXACT,
    supplied_confidence: Decimal | None = None,
    metadata: tuple[tuple[str, str], ...] = (),
) -> ObservationCandidate:
    """Create a validated candidate from explicit structured input."""

    source_text = excerpt if excerpt is not None else f"{subject} {predicate} {value}"

    source = ExtractionSource(
        source_id=source_id,
        text=source_text,
        segment_id=segment_id,
        start_offset=start_offset,
        end_offset=end_offset,
        evidence_ids=evidence_ids,
        metadata=metadata,
    )

    resolved_kind: ObservationValueKind | None

    if value_kind is None:
        resolved_kind = infer_value_kind(value)
    elif isinstance(value_kind, ObservationValueKind):
        resolved_kind = value_kind
    else:
        resolved_kind = ObservationValueKind(str(value_kind))

    return ObservationCandidate(
        subject=subject,
        predicate=predicate,
        raw_value=value,
        source=source,
        value_kind=resolved_kind,
        unit=unit,
        polarity=polarity,
        origin=origin,
        extraction_pattern=ExtractionPattern.STRUCTURED,
        extraction_quality=extraction_quality,
        supplied_confidence=supplied_confidence,
        metadata=metadata,
    )

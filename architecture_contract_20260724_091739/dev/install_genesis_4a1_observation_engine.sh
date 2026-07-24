#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
PACKAGE_ROOT="${PROJECT_ROOT}/core/cognition"

echo
echo "======================================================================"
echo "JARVIS GENESIS IV-A1 — PACKAGE 1B OPERATIONAL OBSERVATION ENGINE"
echo "======================================================================"
echo
echo "Project root : ${PROJECT_ROOT}"
echo "Python       : ${PYTHON_BIN}"
echo

if [[ ! -d "${PROJECT_ROOT}/core" ]]; then
    echo "[FAIL] Missing core directory: ${PROJECT_ROOT}/core"
    exit 1
fi

if [[ ! -d "${PACKAGE_ROOT}" ]]; then
    echo "[FAIL] Missing Package 1A cognition directory: ${PACKAGE_ROOT}"
    echo "       Install Genesis IV-A1 Package 1A before Package 1B."
    exit 1
fi

required_package_1a_files=(
    "${PACKAGE_ROOT}/contracts.py"
    "${PACKAGE_ROOT}/enums.py"
    "${PACKAGE_ROOT}/errors.py"
    "${PACKAGE_ROOT}/identifiers.py"
    "${PACKAGE_ROOT}/serialization.py"
    "${PACKAGE_ROOT}/validation.py"
)

for required_file in "${required_package_1a_files[@]}"; do
    if [[ ! -f "${required_file}" ]]; then
        echo "[FAIL] Missing Package 1A prerequisite: ${required_file}"
        exit 1
    fi
done

if ! "${PYTHON_BIN}" --version >/dev/null 2>&1; then
    echo "[FAIL] Python interpreter is unavailable: ${PYTHON_BIN}"
    exit 1
fi

mkdir -p "${PACKAGE_ROOT}"

cat > "${PACKAGE_ROOT}/normalization.py" <<'PYEOF'
"""Deterministic normalization for Genesis IV-A1 observation inputs.

Normalization is intentionally conservative. It removes representational
variation without introducing facts, interpretations, or inferred meaning.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Final

from .enums import ObservationValueKind
from .errors import CognitionValidationError
from .serialization import decimal_to_string

_WHITESPACE_PATTERN: Final[re.Pattern[str]] = re.compile(r"\s+")
_IDENTIFIER_SEPARATOR_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"[\s\-./:]+"
)
_IDENTIFIER_INVALID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"[^a-z0-9_]"
)
_REPEATED_UNDERSCORE_PATTERN: Final[re.Pattern[str]] = re.compile(r"_+")

_QUANTITY_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"""
    ^\s*
    (?P<number>
        [+-]?
        (?:
            \d+(?:[.,]\d+)?
            |
            [.,]\d+
        )
    )
    \s*
    (?P<unit>
        [^\d\s].*?
    )?
    \s*$
    """,
    re.VERBOSE,
)

_INTEGER_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[+-]?\d+$")

_DECIMAL_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[+-]?(?:\d+(?:\.\d+)?|\.\d+)$"
)

_TRUE_VALUES: Final[frozenset[str]] = frozenset(
    {
        "1",
        "true",
        "yes",
        "y",
        "on",
        "enabled",
        "active",
    }
)

_FALSE_VALUES: Final[frozenset[str]] = frozenset(
    {
        "0",
        "false",
        "no",
        "n",
        "off",
        "disabled",
        "inactive",
    }
)

_UNIT_ALIASES: Final[dict[str, str]] = {
    "v": "V",
    "volt": "V",
    "volts": "V",
    "voltage": "V",
    "mv": "mV",
    "millivolt": "mV",
    "millivolts": "mV",
    "a": "A",
    "amp": "A",
    "amps": "A",
    "ampere": "A",
    "amperes": "A",
    "ma": "mA",
    "w": "W",
    "watt": "W",
    "watts": "W",
    "kw": "kW",
    "wh": "Wh",
    "kwh": "kWh",
    "hz": "Hz",
    "khz": "kHz",
    "mhz": "MHz",
    "ghz": "GHz",
    "c": "C",
    "°c": "C",
    "celsius": "C",
    "f": "F",
    "°f": "F",
    "fahrenheit": "F",
    "k": "K",
    "kelvin": "K",
    "g": "g",
    "gram": "g",
    "grams": "g",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "mg": "mg",
    "lb": "lb",
    "lbs": "lb",
    "pound": "lb",
    "pounds": "lb",
    "mm": "mm",
    "cm": "cm",
    "m": "m",
    "km": "km",
    "in": "in",
    "inch": "in",
    "inches": "in",
    "ft": "ft",
    "feet": "ft",
    "foot": "ft",
    "s": "s",
    "sec": "s",
    "second": "s",
    "seconds": "s",
    "ms": "ms",
    "millisecond": "ms",
    "milliseconds": "ms",
    "min": "min",
    "minute": "min",
    "minutes": "min",
    "h": "h",
    "hr": "h",
    "hour": "h",
    "hours": "h",
    "%": "%",
    "percent": "%",
    "percentage": "%",
    "pa": "Pa",
    "kpa": "kPa",
    "mpa": "MPa",
    "bar": "bar",
    "psi": "psi",
    "rpm": "rpm",
    "mb": "MB",
    "gb": "GB",
    "tb": "TB",
    "kb": "KB",
    "mib": "MiB",
    "gib": "GiB",
    "tib": "TiB",
}


@dataclass(frozen=True, slots=True)
class NormalizedQuantity:
    """Canonical numeric quantity extracted without semantic inference."""

    value: str
    unit: str


@dataclass(frozen=True, slots=True)
class NormalizedObservationValue:
    """Normalized value data ready for ObservationValue construction."""

    kind: ObservationValueKind
    source_value: str
    normalized_value: str
    unit: str | None = None


def normalize_unicode(value: str) -> str:
    """Apply deterministic Unicode compatibility normalization."""

    if not isinstance(value, str):
        raise CognitionValidationError("Normalized text must be a string.")

    return unicodedata.normalize("NFKC", value)


def normalize_whitespace(value: str) -> str:
    """Normalize Unicode and collapse repeated whitespace."""

    normalized = normalize_unicode(value)
    return _WHITESPACE_PATTERN.sub(" ", normalized).strip()


def normalize_display_text(value: str) -> str:
    """Normalize source-facing text while preserving case and punctuation."""

    normalized = normalize_whitespace(value)

    if not normalized:
        raise CognitionValidationError(
            "Normalized display text must not be empty."
        )

    return normalized


def normalize_concept(value: str) -> str:
    """Normalize a subject or predicate into a stable concept string.

    This operation does not stem words, resolve synonyms, or infer ontology.
    It only removes superficial formatting variation.
    """

    normalized = normalize_display_text(value)
    return normalized.casefold()


def normalize_identifier_token(value: str) -> str:
    """Normalize a textual token into deterministic snake_case."""

    normalized = normalize_concept(value)
    normalized = _IDENTIFIER_SEPARATOR_PATTERN.sub("_", normalized)
    normalized = _IDENTIFIER_INVALID_PATTERN.sub("", normalized)
    normalized = _REPEATED_UNDERSCORE_PATTERN.sub("_", normalized)
    normalized = normalized.strip("_")

    if not normalized:
        raise CognitionValidationError(
            "Identifier token contains no canonical characters."
        )

    return normalized


def normalize_decimal_text(value: str | int | Decimal) -> str:
    """Normalize an exact decimal representation without binary floats."""

    if isinstance(value, bool):
        raise CognitionValidationError(
            "Boolean values cannot be normalized as decimals."
        )

    if isinstance(value, float):
        raise CognitionValidationError(
            "Binary floating-point values are forbidden. "
            "Provide a string, integer, or Decimal."
        )

    if isinstance(value, Decimal):
        decimal_value = value
    else:
        raw = normalize_whitespace(str(value)).replace(",", ".")

        try:
            decimal_value = Decimal(raw)
        except InvalidOperation as exc:
            raise CognitionValidationError(
                f"Invalid decimal value: {value!r}"
            ) from exc

    if not decimal_value.is_finite():
        raise CognitionValidationError(
            "Decimal values must be finite."
        )

    return decimal_to_string(decimal_value)


def normalize_integer_text(value: str | int) -> str:
    """Normalize an exact integer representation."""

    if isinstance(value, bool):
        raise CognitionValidationError(
            "Boolean values cannot be normalized as integers."
        )

    if isinstance(value, int):
        return str(value)

    raw = normalize_whitespace(value)

    if not _INTEGER_PATTERN.fullmatch(raw):
        raise CognitionValidationError(
            f"Invalid integer value: {value!r}"
        )

    return str(int(raw))


def normalize_boolean_text(value: str | bool | int) -> str:
    """Normalize accepted boolean representations to true or false."""

    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, int) and not isinstance(value, bool):
        if value == 1:
            return "true"
        if value == 0:
            return "false"

        raise CognitionValidationError(
            f"Unsupported integer boolean value: {value!r}"
        )

    raw = normalize_concept(str(value))

    if raw in _TRUE_VALUES:
        return "true"

    if raw in _FALSE_VALUES:
        return "false"

    raise CognitionValidationError(
        f"Unsupported boolean value: {value!r}"
    )


def normalize_unit(value: str) -> str:
    """Normalize a unit using a conservative constitutional alias table."""

    normalized = normalize_display_text(value)
    lookup_key = normalized.casefold().replace(" ", "")

    if lookup_key in _UNIT_ALIASES:
        return _UNIT_ALIASES[lookup_key]

    # Unknown units are retained rather than guessed.
    return normalized


def parse_quantity(value: str) -> NormalizedQuantity:
    """Parse a deterministic numeric quantity from source text."""

    source = normalize_display_text(value)
    match = _QUANTITY_PATTERN.fullmatch(source)

    if match is None:
        raise CognitionValidationError(
            f"Value is not a deterministic quantity: {value!r}"
        )

    number = match.group("number")
    unit = match.group("unit")

    if unit is None:
        raise CognitionValidationError(
            f"Quantity is missing a unit: {value!r}"
        )

    normalized_number = normalize_decimal_text(number)
    normalized_unit = normalize_unit(unit)

    return NormalizedQuantity(
        value=normalized_number,
        unit=normalized_unit,
    )


def infer_value_kind(value: str) -> ObservationValueKind:
    """Classify only syntactically unambiguous value forms.

    This function performs representation classification, not semantic
    interpretation.
    """

    normalized = normalize_display_text(value)
    lowered = normalized.casefold()

    if lowered in _TRUE_VALUES or lowered in _FALSE_VALUES:
        return ObservationValueKind.BOOLEAN

    if _INTEGER_PATTERN.fullmatch(normalized):
        return ObservationValueKind.INTEGER

    decimal_candidate = normalized.replace(",", ".")

    if _DECIMAL_PATTERN.fullmatch(decimal_candidate):
        return ObservationValueKind.DECIMAL

    if _QUANTITY_PATTERN.fullmatch(normalized):
        quantity_match = _QUANTITY_PATTERN.fullmatch(normalized)

        if quantity_match is not None and quantity_match.group("unit"):
            return ObservationValueKind.QUANTITY

    return ObservationValueKind.TEXT


def normalize_observation_value(
    value: str | int | bool | Decimal,
    *,
    kind: ObservationValueKind | str | None = None,
    unit: str | None = None,
) -> NormalizedObservationValue:
    """Normalize source data according to an explicit or syntactic value kind."""

    if isinstance(value, float):
        raise CognitionValidationError(
            "Binary floating-point observation values are forbidden."
        )

    source_value = normalize_display_text(str(value))

    if kind is None:
        resolved_kind = infer_value_kind(source_value)
    elif isinstance(kind, ObservationValueKind):
        resolved_kind = kind
    else:
        try:
            resolved_kind = ObservationValueKind(str(kind))
        except ValueError as exc:
            raise CognitionValidationError(
                f"Unsupported observation value kind: {kind!r}"
            ) from exc

    if resolved_kind is ObservationValueKind.INTEGER:
        normalized_value = normalize_integer_text(source_value)
        normalized_unit = None

    elif resolved_kind is ObservationValueKind.DECIMAL:
        normalized_value = normalize_decimal_text(source_value)
        normalized_unit = None

    elif resolved_kind is ObservationValueKind.BOOLEAN:
        normalized_value = normalize_boolean_text(source_value)
        normalized_unit = None

    elif resolved_kind is ObservationValueKind.QUANTITY:
        if unit is None:
            quantity = parse_quantity(source_value)
            normalized_value = quantity.value
            normalized_unit = quantity.unit
        else:
            normalized_value = normalize_decimal_text(source_value)
            normalized_unit = normalize_unit(unit)

    else:
        if unit is not None:
            raise CognitionValidationError(
                "Units may only be supplied for quantity observations."
            )

        normalized_value = normalize_display_text(source_value)
        normalized_unit = None

    return NormalizedObservationValue(
        kind=resolved_kind,
        source_value=source_value,
        normalized_value=normalized_value,
        unit=normalized_unit,
    )
PYEOF

cat > "${PACKAGE_ROOT}/confidence.py" <<'PYEOF'
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
PYEOF

cat > "${PACKAGE_ROOT}/extraction.py" <<'PYEOF'
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
PYEOF

cat > "${PACKAGE_ROOT}/observation.py" <<'PYEOF'
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
PYEOF

cat > "${PACKAGE_ROOT}/__init__.py" <<'PYEOF'
"""Genesis IV cognition-domain public API.

The cognition layer transforms represented knowledge into deterministic,
immutable cognitive objects without performing planning or execution.
"""

from .confidence import (
    ConfidenceAssessment,
    ConfidenceFactors,
    ExtractionQuality,
    SourceReliability,
    assess_confidence,
    clamp_confidence,
    confidence_band,
    confidence_for_direct_source,
)
from .contracts import (
    GENESIS_IV_A1_SCHEMA_VERSION,
    Metadata,
    Observation,
    ObservationValue,
    SourceReference,
    normalize_confidence,
    normalize_metadata,
)
from .enums import (
    CognitiveObjectKind,
    ConfidenceBand,
    ObservationOrigin,
    ObservationPolarity,
    ObservationValueKind,
)
from .errors import (
    CognitionError,
    CognitionIdentifierError,
    CognitionSerializationError,
    CognitionValidationError,
    UnsupportedCognitiveObjectError,
)
from .extraction import (
    ExtractionPattern,
    ExtractionResult,
    ExtractionSource,
    ObservationCandidate,
    extract_candidates,
    extract_many,
    structured_candidate,
)
from .identifiers import (
    make_cognition_id,
    normalize_kind,
    parse_cognition_id,
    validate_cognition_id,
    verify_cognition_id,
)
from .normalization import (
    NormalizedObservationValue,
    NormalizedQuantity,
    infer_value_kind,
    normalize_boolean_text,
    normalize_concept,
    normalize_decimal_text,
    normalize_display_text,
    normalize_identifier_token,
    normalize_integer_text,
    normalize_observation_value,
    normalize_unicode,
    normalize_unit,
    normalize_whitespace,
    parse_quantity,
)
from .observation import (
    ObservationBatch,
    ObservationConstruction,
    ObservationEngine,
    build_observation,
    observe_source,
)
from .serialization import (
    canonical_fingerprint,
    canonical_json,
    canonicalize,
    decimal_to_string,
    pretty_json,
)
from .validation import (
    validate_cognitive_object,
    validate_observation,
    validate_observation_value,
    validate_source_reference,
)

__all__ = [
    "GENESIS_IV_A1_SCHEMA_VERSION",
    "Metadata",
    "Observation",
    "ObservationValue",
    "SourceReference",
    "CognitiveObjectKind",
    "ConfidenceBand",
    "ObservationOrigin",
    "ObservationPolarity",
    "ObservationValueKind",
    "CognitionError",
    "CognitionIdentifierError",
    "CognitionSerializationError",
    "CognitionValidationError",
    "UnsupportedCognitiveObjectError",
    "ConfidenceAssessment",
    "ConfidenceFactors",
    "ExtractionQuality",
    "SourceReliability",
    "ExtractionPattern",
    "ExtractionResult",
    "ExtractionSource",
    "ObservationCandidate",
    "NormalizedObservationValue",
    "NormalizedQuantity",
    "ObservationBatch",
    "ObservationConstruction",
    "ObservationEngine",
    "assess_confidence",
    "build_observation",
    "canonical_fingerprint",
    "canonical_json",
    "canonicalize",
    "clamp_confidence",
    "confidence_band",
    "confidence_for_direct_source",
    "decimal_to_string",
    "extract_candidates",
    "extract_many",
    "infer_value_kind",
    "make_cognition_id",
    "normalize_boolean_text",
    "normalize_concept",
    "normalize_confidence",
    "normalize_decimal_text",
    "normalize_display_text",
    "normalize_identifier_token",
    "normalize_integer_text",
    "normalize_kind",
    "normalize_metadata",
    "normalize_observation_value",
    "normalize_unicode",
    "normalize_unit",
    "normalize_whitespace",
    "observe_source",
    "parse_cognition_id",
    "parse_quantity",
    "pretty_json",
    "structured_candidate",
    "validate_cognition_id",
    "validate_cognitive_object",
    "validate_observation",
    "validate_observation_value",
    "validate_source_reference",
    "verify_cognition_id",
]
PYEOF

echo "[PASS] Package 1B source files installed"

echo
echo "Compiling complete cognition package..."
"${PYTHON_BIN}" -m compileall -q "${PACKAGE_ROOT}"
echo "[PASS] Cognition package compilation"

echo
echo "Running public import verification..."
PROJECT_ROOT="${PROJECT_ROOT}" "${PYTHON_BIN}" - <<'PYEOF'
import os
import sys
from pathlib import Path

project_root = Path(os.environ["PROJECT_ROOT"])
sys.path.insert(0, str(project_root))

from core.cognition import (
    ExtractionSource,
    ObservationEngine,
    SourceReliability,
    extract_candidates,
    normalize_observation_value,
)

assert ExtractionSource is not None
assert ObservationEngine is not None
assert SourceReliability is not None
assert extract_candidates is not None
assert normalize_observation_value is not None

print("[PASS] Package 1B public imports")
PYEOF

echo
echo "Running deterministic extraction and observation smoke test..."
PROJECT_ROOT="${PROJECT_ROOT}" "${PYTHON_BIN}" - <<'PYEOF'
import os
import sys
from pathlib import Path

project_root = Path(os.environ["PROJECT_ROOT"])
sys.path.insert(0, str(project_root))

from core.cognition import (
    ExtractionSource,
    ObservationEngine,
    ObservationValueKind,
    SourceReliability,
    canonical_json,
    validate_observation,
)

source = ExtractionSource(
    source_id="document:battery-diagnostic",
    segment_id="segment-0001",
    text="The battery voltage is 10.2 V.",
    start_offset=0,
    end_offset=30,
    evidence_ids=("evidence:battery-voltage",),
    metadata=(("document_type", "diagnostic_report"),),
)

engine = ObservationEngine(
    default_source_reliability=SourceReliability.HIGH,
)

first_batch = engine.observe(source)
second_batch = engine.observe(source)

assert first_batch.extraction.matched
assert len(first_batch.observations) == 1
assert len(second_batch.observations) == 1

first = first_batch.observations[0]
second = second_batch.observations[0]

validate_observation(first)
validate_observation(second)

assert first == second
assert first.observation_id == second.observation_id
assert canonical_json(first) == canonical_json(second)

assert first.subject == "the battery"
assert first.predicate == "voltage"
assert first.value.kind is ObservationValueKind.QUANTITY
assert first.value.normalized_value == "10.2"
assert first.value.unit == "V"

print(f"[PASS] Observation ID : {first.observation_id}")
print(f"[PASS] Subject        : {first.subject}")
print(f"[PASS] Predicate      : {first.predicate}")
print(f"[PASS] Value          : {first.value.normalized_value}")
print(f"[PASS] Unit           : {first.value.unit}")
print(f"[PASS] Confidence     : {first.confidence}")
print("[PASS] Deterministic extraction and observation construction")
PYEOF

echo
echo "Running conservative extraction miss test..."
PROJECT_ROOT="${PROJECT_ROOT}" "${PYTHON_BIN}" - <<'PYEOF'
import os
import sys
from pathlib import Path

project_root = Path(os.environ["PROJECT_ROOT"])
sys.path.insert(0, str(project_root))

from core.cognition import ExtractionSource, extract_candidates

source = ExtractionSource(
    source_id="document:ambiguous",
    text="The machine probably needs maintenance because it sounds strange.",
)

result = extract_candidates(source)

assert not result.matched
assert result.candidates == ()
assert result.rejected_reasons == (
    "no_supported_deterministic_pattern",
)

print("[PASS] Ambiguous text was not converted into an observation")
PYEOF

echo
echo "Running structured observation smoke test..."
PROJECT_ROOT="${PROJECT_ROOT}" "${PYTHON_BIN}" - <<'PYEOF'
import os
import sys
from decimal import Decimal
from pathlib import Path

project_root = Path(os.environ["PROJECT_ROOT"])
sys.path.insert(0, str(project_root))

from core.cognition import (
    ExtractionQuality,
    ObservationEngine,
    ObservationValueKind,
    SourceReliability,
    structured_candidate,
)

candidate = structured_candidate(
    source_id="sensor:battery-monitor",
    subject="Battery",
    predicate="Voltage",
    value="10.200",
    value_kind=ObservationValueKind.QUANTITY,
    unit="volts",
    segment_id="reading-0001",
    start_offset=0,
    end_offset=6,
    excerpt="10.200",
    evidence_ids=("evidence:sensor-reading-0001",),
    extraction_quality=ExtractionQuality.EXACT,
    supplied_confidence=Decimal("0.99"),
)

construction = ObservationEngine(
    default_source_reliability=SourceReliability.AUTHORITATIVE,
).commit_candidate(candidate)

observation = construction.observation

assert observation.subject == "battery"
assert observation.predicate == "voltage"
assert observation.value.normalized_value == "10.2"
assert observation.value.unit == "V"
assert observation.confidence == Decimal("0.99")

print(f"[PASS] Structured ID : {observation.observation_id}")
print("[PASS] Structured observation normalization")
PYEOF

echo
echo "Running order-independent metadata test..."
PROJECT_ROOT="${PROJECT_ROOT}" "${PYTHON_BIN}" - <<'PYEOF'
import os
import sys
from pathlib import Path

project_root = Path(os.environ["PROJECT_ROOT"])
sys.path.insert(0, str(project_root))

from core.cognition import (
    ObservationEngine,
    ObservationValueKind,
    structured_candidate,
)

first = structured_candidate(
    source_id="document:metadata-test",
    subject="System",
    predicate="Status",
    value="Operational",
    value_kind=ObservationValueKind.TEXT,
    metadata=(
        ("alpha", "1"),
        ("beta", "2"),
    ),
)

second = structured_candidate(
    source_id="document:metadata-test",
    subject="System",
    predicate="Status",
    value="Operational",
    value_kind=ObservationValueKind.TEXT,
    metadata=(
        ("beta", "2"),
        ("alpha", "1"),
    ),
)

engine = ObservationEngine()

first_observation = engine.commit_candidate(first).observation
second_observation = engine.commit_candidate(second).observation

assert first_observation.observation_id == second_observation.observation_id
assert first_observation == second_observation

print("[PASS] Metadata order does not alter deterministic observations")
PYEOF

echo
echo "======================================================================"
echo "GENESIS IV-A1 PACKAGE 1B INSTALLATION COMPLETE"
echo "======================================================================"
echo
echo "Installed:"
echo "  core/cognition/confidence.py"
echo "  core/cognition/normalization.py"
echo "  core/cognition/extraction.py"
echo "  core/cognition/observation.py"
echo "  core/cognition/__init__.py"
echo
echo "Verified:"
echo "  Package 1A prerequisites"
echo "  Complete package compilation"
echo "  Public API imports"
echo "  Deterministic text extraction"
echo "  Conservative extraction misses"
echo "  Structured observation construction"
echo "  Exact confidence handling"
echo "  Order-independent metadata"
echo
echo "Overall status: EXCELLENT"
echo

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

from ..enums import ObservationValueKind
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


# Public names retained for compatibility with the pre-R0-B module path.
__all__: tuple[str, ...] = tuple(
    name
    for name in globals()
    if not name.startswith("_")
)

"""Structural validation helpers for canonical Evidence contracts."""

from __future__ import annotations

import math
import re
import unicodedata
from datetime import datetime
from decimal import Decimal
from typing import Iterable, TypeVar

from .errors import EvidenceTemporalError, EvidenceValidationError

_IDENTIFIER_COMPONENT = re.compile(r"^[a-z0-9][a-z0-9._:/-]*$")
_LANGUAGE_TAG = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")
_MEDIA_TYPE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]*/"
    r"[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]*$"
)

T = TypeVar("T")


def normalize_text(value: str, *, field_name: str, allow_empty: bool = False) -> str:
    """Return deterministic Unicode-normalized text."""

    if not isinstance(value, str):
        raise EvidenceValidationError(f"{field_name} must be a string")

    normalized = unicodedata.normalize("NFC", value).strip()

    if not allow_empty and not normalized:
        raise EvidenceValidationError(f"{field_name} must not be empty")

    return normalized


def normalize_optional_text(value: str | None, *, field_name: str) -> str | None:
    """Normalize optional text, preserving ``None``."""

    if value is None:
        return None
    return normalize_text(value, field_name=field_name)


def validate_identifier_component(value: str, *, field_name: str) -> str:
    """Validate a stable human-readable identifier component."""

    normalized = normalize_text(value, field_name=field_name).lower()
    if not _IDENTIFIER_COMPONENT.fullmatch(normalized):
        raise EvidenceValidationError(
            f"{field_name} contains unsupported identifier characters"
        )
    return normalized


def validate_language_tag(value: str | None) -> str | None:
    """Validate an optional BCP-47-style language tag."""

    if value is None:
        return None

    normalized = normalize_text(value, field_name="language")
    if not _LANGUAGE_TAG.fullmatch(normalized):
        raise EvidenceValidationError("language is not a valid language tag")
    return normalized


def validate_media_type(value: str) -> str:
    """Validate and normalize an Internet media type."""

    normalized = normalize_text(value, field_name="media_type").lower()
    if not _MEDIA_TYPE.fullmatch(normalized):
        raise EvidenceValidationError("media_type is not a valid media type")
    return normalized


def validate_aware_datetime(
    value: datetime | None,
    *,
    field_name: str,
    required: bool = False,
) -> datetime | None:
    """Require timezone-aware datetimes for deterministic temporal meaning."""

    if value is None:
        if required:
            raise EvidenceTemporalError(f"{field_name} is required")
        return None

    if not isinstance(value, datetime):
        raise EvidenceTemporalError(f"{field_name} must be a datetime")

    if value.tzinfo is None or value.utcoffset() is None:
        raise EvidenceTemporalError(f"{field_name} must be timezone-aware")

    return value


def validate_unit_decimal(
    value: Decimal | int | str | None,
    *,
    field_name: str,
    required: bool = False,
) -> Decimal | None:
    """Validate a finite Decimal in the inclusive range [0, 1]."""

    if value is None:
        if required:
            raise EvidenceValidationError(f"{field_name} is required")
        return None

    if isinstance(value, bool) or isinstance(value, float):
        raise EvidenceValidationError(
            f"{field_name} must use Decimal, int, or decimal string input"
        )

    try:
        decimal_value = value if isinstance(value, Decimal) else Decimal(value)
    except Exception as exc:
        raise EvidenceValidationError(f"{field_name} is not a valid decimal") from exc

    if not decimal_value.is_finite():
        raise EvidenceValidationError(f"{field_name} must be finite")

    if decimal_value < Decimal("0") or decimal_value > Decimal("1"):
        raise EvidenceValidationError(f"{field_name} must be between 0 and 1")

    return decimal_value.normalize()


def validate_nonnegative_decimal(
    value: Decimal | int | str | None,
    *,
    field_name: str,
    required: bool = False,
) -> Decimal | None:
    """Validate a finite non-negative Decimal."""

    if value is None:
        if required:
            raise EvidenceValidationError(f"{field_name} is required")
        return None

    if isinstance(value, bool) or isinstance(value, float):
        raise EvidenceValidationError(
            f"{field_name} must use Decimal, int, or decimal string input"
        )

    try:
        decimal_value = value if isinstance(value, Decimal) else Decimal(value)
    except Exception as exc:
        raise EvidenceValidationError(f"{field_name} is not a valid decimal") from exc

    if not decimal_value.is_finite() or decimal_value < Decimal("0"):
        raise EvidenceValidationError(
            f"{field_name} must be finite and non-negative"
        )

    return decimal_value.normalize()


def normalize_string_tuple(
    values: Iterable[str],
    *,
    field_name: str,
    sort_values: bool = False,
    unique: bool = True,
) -> tuple[str, ...]:
    """Normalize a deterministic tuple of strings."""

    normalized = tuple(
        normalize_text(value, field_name=field_name)
        for value in values
    )

    if unique and len(set(normalized)) != len(normalized):
        raise EvidenceValidationError(f"{field_name} must not contain duplicates")

    if sort_values:
        return tuple(sorted(normalized))

    return normalized


def normalize_key_value_pairs(
    pairs: Iterable[tuple[str, str]],
    *,
    field_name: str,
) -> tuple[tuple[str, str], ...]:
    """Normalize immutable metadata pairs into deterministic key order."""

    normalized: list[tuple[str, str]] = []
    observed_keys: set[str] = set()

    for key, value in pairs:
        normalized_key = validate_identifier_component(
            key,
            field_name=f"{field_name}.key",
        )
        normalized_value = normalize_text(
            value,
            field_name=f"{field_name}.{normalized_key}",
            allow_empty=True,
        )

        if normalized_key in observed_keys:
            raise EvidenceValidationError(
                f"{field_name} contains duplicate key {normalized_key!r}"
            )

        observed_keys.add(normalized_key)
        normalized.append((normalized_key, normalized_value))

    return tuple(sorted(normalized, key=lambda item: item[0]))


def require_nonnegative_integer(value: int, *, field_name: str) -> int:
    """Require a non-negative integer excluding booleans."""

    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EvidenceValidationError(
            f"{field_name} must be a non-negative integer"
        )
    return value

"""Deterministic canonical serialization for cognition objects."""

from __future__ import annotations

import dataclasses
import hashlib
import json
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping, Sequence

from .errors import CognitionSerializationError


def decimal_to_string(value: Decimal) -> str:
    """Return a deterministic non-exponential decimal representation."""

    if not value.is_finite():
        raise CognitionSerializationError(
            "Non-finite decimal values are not canonically serializable."
        )

    normalized = value.normalize()

    if normalized == normalized.to_integral():
        return format(normalized.quantize(Decimal("1")), "f")

    return format(normalized, "f")


def canonicalize(value: Any) -> Any:
    """Convert supported values into deterministic JSON-compatible structures."""

    if value is None or isinstance(value, (str, int, bool)):
        return value

    if isinstance(value, float):
        raise CognitionSerializationError(
            "Binary floating-point values are forbidden in canonical cognition data. "
            "Use Decimal instead."
        )

    if isinstance(value, Decimal):
        return decimal_to_string(value)

    if isinstance(value, Enum):
        return canonicalize(value.value)

    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: canonicalize(getattr(value, field.name))
            for field in dataclasses.fields(value)
        }

    if isinstance(value, Mapping):
        converted: dict[str, Any] = {}

        for key, item in value.items():
            if not isinstance(key, str):
                raise CognitionSerializationError(
                    "Canonical mapping keys must be strings."
                )

            converted[key] = canonicalize(item)

        return {
            key: converted[key]
            for key in sorted(converted)
        }

    if isinstance(value, tuple):
        return [canonicalize(item) for item in value]

    if isinstance(value, list):
        return [canonicalize(item) for item in value]

    if isinstance(value, set) or isinstance(value, frozenset):
        canonical_items = [canonicalize(item) for item in value]
        return sorted(
            canonical_items,
            key=lambda item: json.dumps(
                item,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ),
        )

    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return [canonicalize(item) for item in value]

    raise CognitionSerializationError(
        f"Unsupported canonical serialization type: {type(value).__name__}"
    )


def canonical_json(value: Any) -> str:
    """Serialize a supported object using the canonical cognition JSON form."""

    return json.dumps(
        canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def pretty_json(value: Any) -> str:
    """Serialize a cognition object as stable, human-readable JSON."""

    return (
        json.dumps(
            canonicalize(value),
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    )


def canonical_fingerprint(value: Any) -> str:
    """Return a SHA-256 fingerprint of canonical serialized content."""

    encoded = canonical_json(value).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

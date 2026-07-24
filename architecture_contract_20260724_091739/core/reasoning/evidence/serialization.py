"""Deterministic canonical serialization for Genesis II-A4 contracts."""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from hashlib import sha256
from typing import Any

from .errors import EvidenceSerializationError


def _canonical_decimal(value: Decimal) -> str:
    if not value.is_finite():
        raise EvidenceSerializationError("non-finite Decimal values are unsupported")

    normalized = value.normalize()

    if normalized == 0:
        return "0"

    rendered = format(normalized, "f")

    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")

    return rendered


def _canonical_datetime(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise EvidenceSerializationError(
            "canonical datetime values must be timezone-aware"
        )

    utc_value = value.astimezone(timezone.utc)
    rendered = utc_value.isoformat(timespec="microseconds")
    return rendered.replace("+00:00", "Z")


def to_canonical_primitive(value: Any) -> Any:
    """Convert supported values into deterministic JSON primitives."""

    if value is None or isinstance(value, (str, int, bool)):
        return value

    if isinstance(value, float):
        raise EvidenceSerializationError(
            "floating-point values are prohibited in canonical Evidence serialization"
        )

    if isinstance(value, Decimal):
        return {"$decimal": _canonical_decimal(value)}

    if isinstance(value, datetime):
        return {"$datetime": _canonical_datetime(value)}

    if isinstance(value, Enum):
        return value.value

    if hasattr(value, "canonical_value") and callable(value.canonical_value):
        return value.canonical_value()

    if is_dataclass(value):
        return {
            field.name: to_canonical_primitive(getattr(value, field.name))
            for field in fields(value)
        }

    if isinstance(value, tuple):
        return [to_canonical_primitive(item) for item in value]

    if isinstance(value, list):
        return [to_canonical_primitive(item) for item in value]

    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise EvidenceSerializationError(
                "canonical mappings require string keys"
            )

        return {
            key: to_canonical_primitive(value[key])
            for key in sorted(value)
        }

    raise EvidenceSerializationError(
        f"unsupported canonical serialization type: {type(value).__name__}"
    )


def canonical_json(value: Any) -> str:
    """Serialize a value to canonical compact UTF-8 JSON text."""

    primitive = to_canonical_primitive(value)

    return json.dumps(
        primitive,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_bytes(value: Any) -> bytes:
    """Serialize a value to canonical UTF-8 bytes."""

    return canonical_json(value).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    """Return the SHA-256 digest of canonical serialization."""

    return sha256(canonical_bytes(value)).hexdigest()

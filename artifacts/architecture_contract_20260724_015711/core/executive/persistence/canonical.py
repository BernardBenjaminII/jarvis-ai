"""Canonical value normalization for executive persistence."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping
from uuid import UUID


TYPE_KEY = "__jarvis_type__"
VALUE_KEY = "value"
CLASS_KEY = "class"


class CanonicalizationError(TypeError):
    """Raised when a value cannot be represented canonically."""


def _qualified_name(value: Any) -> str:
    cls = value if isinstance(value, type) else type(value)
    return f"{cls.__module__}.{cls.__qualname__}"


def _normalize_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        raise CanonicalizationError(
            "naive datetime values are not permitted"
        )
    normalized = value.astimezone(timezone.utc)
    text = normalized.isoformat(timespec="microseconds")
    return text.replace("+00:00", "Z")


def to_canonical_value(value: Any) -> Any:
    """Convert a supported Python value into canonical JSON data."""

    if value is None or isinstance(value, (bool, int, str)):
        return value

    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise CanonicalizationError(
                "NaN and infinity are not permitted"
            )
        return value

    if isinstance(value, datetime):
        return {
            TYPE_KEY: "datetime",
            VALUE_KEY: _normalize_datetime(value),
        }

    if isinstance(value, date):
        return {
            TYPE_KEY: "date",
            VALUE_KEY: value.isoformat(),
        }

    if isinstance(value, UUID):
        return {
            TYPE_KEY: "uuid",
            VALUE_KEY: str(value),
        }

    if isinstance(value, Path):
        return {
            TYPE_KEY: "path",
            VALUE_KEY: value.as_posix(),
        }

    if isinstance(value, bytes):
        return {
            TYPE_KEY: "bytes",
            VALUE_KEY: value.hex(),
        }

    if isinstance(value, Enum):
        return {
            TYPE_KEY: "enum",
            CLASS_KEY: _qualified_name(value),
            VALUE_KEY: to_canonical_value(value.value),
        }

    if is_dataclass(value) and not isinstance(value, type):
        payload = {
            field.name: to_canonical_value(getattr(value, field.name))
            for field in fields(value)
        }
        return {
            TYPE_KEY: "dataclass",
            CLASS_KEY: _qualified_name(value),
            VALUE_KEY: payload,
        }

    if isinstance(value, Mapping):
        normalized = {}
        for key in sorted(value, key=lambda item: str(item)):
            if not isinstance(key, str):
                raise CanonicalizationError(
                    "canonical mapping keys must be strings"
                )
            normalized[key] = to_canonical_value(value[key])
        return normalized

    if isinstance(value, tuple):
        return {
            TYPE_KEY: "tuple",
            VALUE_KEY: [to_canonical_value(item) for item in value],
        }

    if isinstance(value, list):
        return [to_canonical_value(item) for item in value]

    if isinstance(value, (set, frozenset)):
        items = [to_canonical_value(item) for item in value]
        items.sort(key=canonical_sort_key)
        return {
            TYPE_KEY: "set",
            VALUE_KEY: items,
        }

    raise CanonicalizationError(
        f"unsupported canonical value: {_qualified_name(value)}"
    )


def canonical_sort_key(value: Any) -> str:
    """Return a stable textual sort key for canonical values."""

    import json

    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


__all__ = [
    "CLASS_KEY",
    "CanonicalizationError",
    "TYPE_KEY",
    "VALUE_KEY",
    "canonical_sort_key",
    "to_canonical_value",
]

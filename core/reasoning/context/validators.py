"""Shared validation helpers for Genesis II-A3 context contracts."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, TypeVar

from core.reasoning.context.errors import (
    DuplicateReasoningContextKeyError,
    ReasoningContextContractError,
)


class KeyedContract(Protocol):
    """Protocol implemented by deterministic keyed constitutional values."""

    key: str


TKeyed = TypeVar("TKeyed", bound=KeyedContract)


def normalize_required_text(value: str, *, field_name: str) -> str:
    """Normalize required text without weakening contract validation."""

    if not isinstance(value, str):
        raise ReasoningContextContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()
    if not normalized:
        raise ReasoningContextContractError(
            f"{field_name} must not be blank"
        )

    return normalized


def normalize_optional_text(
    value: str | None,
    *,
    field_name: str,
) -> str | None:
    """Normalize optional text, converting blank values to ``None``."""

    if value is None:
        return None

    if not isinstance(value, str):
        raise ReasoningContextContractError(
            f"{field_name} must be a string or None"
        )

    normalized = value.strip()
    return normalized or None


def normalize_schema_version(value: str) -> str:
    """Normalize a required schema-version string."""

    return normalize_required_text(
        value,
        field_name="schema_version",
    )


def normalize_keyed_items(
    values: Iterable[TKeyed],
    *,
    collection_name: str,
) -> tuple[TKeyed, ...]:
    """Return a deterministic tuple and reject duplicate normalized keys."""

    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ReasoningContextContractError(
            f"{collection_name} must be iterable"
        ) from exc

    keys: set[str] = set()
    for item in normalized:
        key = getattr(item, "key", None)
        if not isinstance(key, str) or not key:
            raise ReasoningContextContractError(
                f"{collection_name} contains an invalid keyed contract"
            )

        if key in keys:
            raise DuplicateReasoningContextKeyError(
                f"{collection_name} contains duplicate key: {key}"
            )
        keys.add(key)

    return tuple(sorted(normalized, key=lambda item: item.key))


def validate_weight(value: int) -> int:
    """Validate a deterministic decision-criterion weight."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise ReasoningContextContractError(
            "weight must be an integer"
        )

    if not 1 <= value <= 100:
        raise ReasoningContextContractError(
            "weight must be between 1 and 100"
        )

    return value


__all__ = [
    "normalize_keyed_items",
    "normalize_optional_text",
    "normalize_required_text",
    "normalize_schema_version",
    "validate_weight",
]

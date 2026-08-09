from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .normalization import normalize_subjects


def mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}

    if isinstance(value, Mapping):
        return dict(value)

    if hasattr(value, "to_dict") and callable(value.to_dict):
        try:
            result = value.to_dict()
            return dict(result) if isinstance(result, Mapping) else {}
        except Exception:
            return {}

    try:
        return dict(value)
    except Exception:
        return {}


def number(value: Any) -> float | None:
    if value is None:
        return None

    if isinstance(value, Mapping):
        for key in ("value", "score", "final"):
            if key in value:
                return number(value[key])
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def list_like(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()

    if isinstance(value, str):
        raw = value.replace(";", ",").replace("|", ",")
        parts = [
            item.strip()
            for item in raw.split(",")
            if item.strip()
        ]
        return normalize_subjects(parts)

    if isinstance(value, (list, tuple, set)):
        return normalize_subjects(str(item) for item in value)

    return normalize_subjects((str(value),))


def candidate_data(value: Any) -> dict[str, Any]:
    data = mapping(value)
    candidate = mapping(data.get("candidate"))
    metadata = mapping(data.get("metadata"))
    raw_row = mapping(
        metadata.get("raw_row")
        or data.get("raw_row")
    )

    return {
        **raw_row,
        **metadata,
        **candidate,
        **data,
    }


def candidate_subjects(data: dict[str, Any]) -> tuple[str, ...]:
    values = []

    for key in (
        "subject",
        "subjects",
        "topic",
        "topics",
        "domain",
        "domains",
        "category",
        "categories",
        "classification",
        "taxonomy",
        "taxonomy_id",
    ):
        values.extend(list_like(data.get(key)))

    return normalize_subjects(values)


def candidate_domain(data: dict[str, Any]) -> str:
    for key in (
        "domain",
        "subject",
        "topic",
        "category",
        "classification",
    ):
        value = data.get(key)
        if value:
            return str(value)

    return ""


def score_component(
    data: dict[str, Any],
    *names: str,
) -> float | None:
    containers = (
        mapping(data.get("qualification_components")),
        mapping(data.get("components")),
        mapping(data.get("score")),
        data,
    )

    for container in containers:
        for name in names:
            if name in container:
                resolved = number(container[name])
                if resolved is not None:
                    return resolved

    return None

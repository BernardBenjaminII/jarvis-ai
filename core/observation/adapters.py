"""Public Observation adapter API.

Genesis IV-B4 introduced richer migration adapters. Genesis IV-B4A preserves
the stable IV-B3 public adapter names as compatibility facades so existing
imports continue to work while callers migrate deliberately.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Mapping

from .contracts import Observation
from .errors import ObservationAdapterError
from .migration import (
    adapt_cognition_common_observation,
    adapt_operational_observation,
    adapt_registered_observation,
    adapt_representation_observation,
)


def _coerce_legacy_value(
    value: Any | None,
    kwargs: Mapping[str, Any],
) -> Any:
    """Support both object-style and keyword-style legacy adapter calls."""

    if value is not None and kwargs:
        raise ObservationAdapterError(
            "supply either a legacy object or keyword fields, not both"
        )
    if value is not None:
        return value
    if kwargs:
        return SimpleNamespace(**dict(kwargs))
    raise ObservationAdapterError("a legacy Observation value is required")


def adapt_cognition_observation(
    legacy: Any | None = None,
    **kwargs: Any,
) -> Observation:
    """Stable IV-B3 facade for the cognition-domain Observation adapter."""

    return adapt_cognition_common_observation(
        _coerce_legacy_value(legacy, kwargs)
    )


def adapt_executive_observation(
    legacy: Any | None = None,
    **kwargs: Any,
) -> Observation:
    """Stable IV-B3 facade for the executive/runtime Observation adapter."""

    return adapt_operational_observation(
        _coerce_legacy_value(legacy, kwargs)
    )


def adapt_legacy_observation(
    legacy: Any | None = None,
    *,
    legacy_path: str | None = None,
    **kwargs: Any,
) -> Observation:
    """Adapt a known legacy Observation shape.

    ``legacy_path`` is preferred because it makes migration intent explicit.
    When omitted, conservative structural dispatch preserves the IV-B3 API.
    """

    value = _coerce_legacy_value(legacy, kwargs)

    if legacy_path is not None:
        return adapt_registered_observation(
            value,
            legacy_path=legacy_path,
        )

    if hasattr(value, "subject") and hasattr(value, "predicate"):
        return adapt_cognition_common_observation(value)

    if hasattr(value, "observation_type") and hasattr(
        value,
        "occurred_at",
    ):
        return adapt_operational_observation(value)

    if hasattr(value, "statement") and hasattr(value, "confidence"):
        return adapt_representation_observation(value)

    raise ObservationAdapterError(
        "unable to determine legacy Observation contract; "
        "supply legacy_path explicitly"
    )


__all__ = [
    # Stable IV-B3 public API.
    "adapt_cognition_observation",
    "adapt_executive_observation",
    "adapt_legacy_observation",
    # IV-B4 migration API.
    "adapt_cognition_common_observation",
    "adapt_operational_observation",
    "adapt_registered_observation",
    "adapt_representation_observation",
]

"""Compatibility boundary for legacy Observation callers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import warnings

from .contracts import Observation
from .migration import adapt_registered_observation


class LegacyObservationCompatibilityWarning(DeprecationWarning):
    """A legacy Observation entry point crossed the compatibility boundary."""


@dataclass(frozen=True, slots=True)
class CompatibilityReceipt:
    legacy_path: str
    canonical_observation_id: str
    adapter_applied: bool


def canonicalize_observation(
    value: Any,
    *,
    legacy_path: str | None = None,
    warn: bool = True,
) -> tuple[Observation, CompatibilityReceipt]:
    if isinstance(value, Observation):
        return value, CompatibilityReceipt(
            legacy_path="core/observation/contracts.py",
            canonical_observation_id=value.observation_id,
            adapter_applied=False,
        )

    if legacy_path is None:
        raise TypeError(
            "legacy_path is required for non-canonical Observation values"
        )

    if warn:
        warnings.warn(
            f"{legacy_path} is a governed legacy Observation contract; "
            "migrate the caller to core.observation.Observation",
            LegacyObservationCompatibilityWarning,
            stacklevel=2,
        )

    canonical = adapt_registered_observation(
        value,
        legacy_path=legacy_path,
    )
    return canonical, CompatibilityReceipt(
        legacy_path=legacy_path,
        canonical_observation_id=canonical.observation_id,
        adapter_applied=True,
    )

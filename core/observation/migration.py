"""Genesis IV-B4 adapters from legacy Observation shapes to canonical form."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import json
from typing import Any, Mapping

from .contracts import Observation, ObservationContext, ObservationSource
from .enums import (
    ObservationDomain,
    ObservationKind,
    RealityClass,
    SourceAuthority,
    SourceType,
)
from .errors import ObservationAdapterError


_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _enum_member(enum_type: type[Enum], *names: str) -> Enum:
    for name in names:
        member = enum_type.__members__.get(name)
        if member is not None:
            return member
    try:
        return next(iter(enum_type))
    except StopIteration as exc:
        raise ObservationAdapterError(
            f"{enum_type.__name__} has no members"
        ) from exc


def _read(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe(item) for item in value]
    for method_name in (
        "to_canonical_data",
        "to_canonical_dict",
        "identity_payload",
    ):
        method = getattr(value, method_name, None)
        if callable(method):
            return _json_safe(method())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return str(value)


def _timestamp(value: Any, default: datetime = _EPOCH) -> datetime:
    if value is None:
        return default
    if not isinstance(value, datetime):
        raise ObservationAdapterError(
            f"expected datetime, received {type(value).__name__}"
        )
    if value.tzinfo is None or value.utcoffset() is None:
        raise ObservationAdapterError(
            "legacy observation timestamps must be timezone-aware"
        )
    return value.astimezone(timezone.utc)


def _confidence(value: Any) -> float:
    try:
        normalized = float(value)
    except (TypeError, ValueError) as exc:
        raise ObservationAdapterError(
            f"invalid legacy confidence: {value!r}"
        ) from exc
    if not 0.0 <= normalized <= 1.0:
        raise ObservationAdapterError(
            "legacy confidence must be between 0.0 and 1.0"
        )
    return normalized


def _source(
    legacy: Any,
    *,
    reality_class: RealityClass,
    source_type: SourceType,
    producer: str,
    collector: str,
) -> ObservationSource:
    legacy_source = _read(legacy, "source")
    provenance = _read(legacy, "provenance")
    raw = legacy_source if legacy_source is not None else provenance

    identifier = (
        _read(raw, "identifier")
        or _read(raw, "source_id")
        or _read(raw, "uri")
        or _read(raw, "path")
        or _read(legacy, "observation_id")
        or f"legacy:{producer}"
    )
    segment_id = (
        _read(raw, "segment_id")
        or _read(raw, "locator")
        or None
    )

    return ObservationSource.create(
        reality_class=reality_class,
        source_type=source_type,
        identifier=str(identifier),
        producer=producer,
        collector=collector,
        authority=_enum_member(
            SourceAuthority,
            "PRIMARY",
            "DIRECT",
            "UNKNOWN",
        ),
        segment_id=None if segment_id is None else str(segment_id),
    )


def _make_context(metadata: Mapping[str, Any]) -> ObservationContext:
    # Construct canonical context while preserving behavioral fields.
    normalized = {
        str(key): _json_safe(value)
        for key, value in sorted(
            metadata.items(),
            key=lambda item: str(item[0]),
        )
    }

    create = getattr(ObservationContext, "create", None)
    if callable(create):
        return create(metadata=normalized)

    from_mapping = getattr(ObservationContext, "from_mapping", None)
    if callable(from_mapping):
        return from_mapping(normalized)

    annotations = getattr(ObservationContext, "__annotations__", {})
    direct_names = (
        "mission_id",
        "objective_id",
        "task_id",
        "activity_id",
        "session_id",
        "correlation_id",
        "trace_id",
    )
    direct = {
        name: str(normalized[name])
        for name in direct_names
        if name in annotations and normalized.get(name) is not None
    }

    tags_value = normalized.get("tags")
    if "tags" in annotations and tags_value is not None:
        if isinstance(tags_value, (list, tuple, set, frozenset)):
            direct["tags"] = tuple(str(item) for item in tags_value)
        else:
            direct["tags"] = (str(tags_value),)

    metadata_payload = {
        key: value
        for key, value in normalized.items()
        if key not in direct_names and key != "tags"
    }

    if "metadata" in annotations:
        direct["metadata"] = metadata_payload
        try:
            return ObservationContext(**direct)
        except TypeError:
            direct["metadata"] = tuple(sorted(metadata_payload.items()))
            try:
                return ObservationContext(**direct)
            except TypeError:
                pass

    if "labels" in annotations:
        direct["labels"] = tuple(
            (str(key), str(value))
            for key, value in sorted(metadata_payload.items())
        )
        try:
            return ObservationContext(**direct)
        except TypeError:
            pass

    if "attributes" in annotations:
        direct["attributes"] = metadata_payload
        try:
            return ObservationContext(**direct)
        except TypeError:
            direct["attributes"] = tuple(sorted(metadata_payload.items()))
            try:
                return ObservationContext(**direct)
            except TypeError:
                pass

    try:
        return ObservationContext(**direct)
    except TypeError as exc:
        raise ObservationAdapterError(
            "unable to construct canonical ObservationContext while "
            "preserving legacy behavioral fields"
        ) from exc


def _context(legacy: Any, legacy_path: str) -> ObservationContext:
    metadata = {
        "legacy_contract": legacy_path,
    }
    for key in (
        "mission_id",
        "correlation_id",
        "causation_id",
        "severity",
        "origin",
        "polarity",
        "schema_version",
    ):
        value = _read(legacy, key)
        if value is not None:
            metadata[key] = _json_safe(value)
    labels = _read(legacy, "labels")
    if labels:
        metadata["labels"] = _json_safe(labels)
    return _make_context(metadata)


def adapt_cognition_common_observation(legacy: Any) -> Observation:
    """Adapt ``core.cognition.common.contracts.Observation``."""

    subject = str(_read(legacy, "subject", "")).strip()
    predicate = str(_read(legacy, "predicate", "")).strip()
    if not subject or not predicate:
        raise ObservationAdapterError(
            "legacy cognition observation requires subject and predicate"
        )

    return Observation.create(
        domain=_enum_member(
            ObservationDomain,
            "KNOWLEDGE",
            "COGNITION",
        ),
        observation_type="legacy.cognition.fact",
        kind=_enum_member(
            ObservationKind,
            "CONTENT",
            "FACT",
        ),
        subject=subject,
        predicate=predicate,
        value=_json_safe(_read(legacy, "value")),
        source=_source(
            legacy,
            reality_class=_enum_member(
                RealityClass,
                "RECORDED",
                "LIVE",
            ),
            source_type=_enum_member(
                SourceType,
                "FILE",
                "DOCUMENT",
                "BOOK",
            ),
            producer="cognition-common-adapter",
            collector="genesis-iv-b4",
        ),
        observed_at=_timestamp(
            _read(legacy, "observed_at"),
            _EPOCH,
        ),
        recorded_at=_timestamp(
            _read(legacy, "recorded_at"),
            _EPOCH,
        ),
        confidence=_confidence(_read(legacy, "confidence", 1.0)),
        context=_context(
            legacy,
            "core/cognition/common/contracts.py",
        ),
    )


def adapt_operational_observation(legacy: Any) -> Observation:
    """Adapt ``core.cognition.observation.models.Observation``."""

    observation_type = str(
        _read(legacy, "observation_type", "operational.event")
    ).strip()
    value = _json_safe(_read(legacy, "value"))
    subject = str(
        _read(legacy, "mission_id")
        or _read(legacy, "observation_id")
        or "operational-runtime"
    )

    return Observation.create(
        domain=_enum_member(
            ObservationDomain,
            "PLATFORM",
            "OPERATIONS",
            "SYSTEM",
            "KNOWLEDGE",
        ),
        observation_type=observation_type,
        kind=_enum_member(
            ObservationKind,
            "EVENT",
            "STATE",
            "CONTENT",
        ),
        subject=subject,
        predicate="reported",
        value=value,
        source=_source(
            legacy,
            reality_class=_enum_member(
                RealityClass,
                "LIVE",
                "RECORDED",
            ),
            source_type=_enum_member(
                SourceType,
                "SYSTEM",
                "API",
                "FILE",
                "BOOK",
            ),
            producer="operational-observation-adapter",
            collector="genesis-iv-b4",
        ),
        observed_at=_timestamp(
            _read(legacy, "occurred_at"),
            _EPOCH,
        ),
        recorded_at=_timestamp(
            _read(legacy, "recorded_at"),
            _timestamp(_read(legacy, "occurred_at"), _EPOCH),
        ),
        confidence=_confidence(_read(legacy, "confidence", 1.0)),
        context=_context(
            legacy,
            "core/cognition/observation/models.py",
        ),
    )


def adapt_representation_observation(legacy: Any) -> Observation:
    """Adapt ``core.representation.contracts.Observation``."""

    statement = str(_read(legacy, "statement", "")).strip()
    if not statement:
        raise ObservationAdapterError(
            "representation observation requires a statement"
        )

    provenance = _read(legacy, "provenance")
    subject = str(
        _read(legacy, "object_id")
        or _read(legacy, "cognitive_object_id")
        or "represented-statement"
    )

    return Observation.create(
        domain=_enum_member(
            ObservationDomain,
            "KNOWLEDGE",
            "COGNITION",
        ),
        observation_type="representation.statement",
        kind=_enum_member(
            ObservationKind,
            "CONTENT",
            "FACT",
        ),
        subject=subject,
        predicate="states",
        value=statement,
        source=_source(
            provenance or legacy,
            reality_class=_enum_member(
                RealityClass,
                "RECORDED",
                "LIVE",
            ),
            source_type=_enum_member(
                SourceType,
                "DOCUMENT",
                "FILE",
                "BOOK",
            ),
            producer="representation-adapter",
            collector="genesis-iv-b4",
        ),
        observed_at=_timestamp(
            _read(legacy, "observed_at"),
            _EPOCH,
        ),
        recorded_at=_timestamp(
            _read(legacy, "recorded_at"),
            _EPOCH,
        ),
        confidence=_confidence(_read(legacy, "confidence", 1.0)),
        context=_context(
            legacy,
            "core/representation/contracts.py",
        ),
    )


def adapt_registered_observation(
    legacy: Any,
    *,
    legacy_path: str,
) -> Observation:
    adapters = {
        "core/cognition/common/contracts.py": (
            adapt_cognition_common_observation
        ),
        "core/cognition/observation/models.py": (
            adapt_operational_observation
        ),
        "core/representation/contracts.py": (
            adapt_representation_observation
        ),
    }
    try:
        adapter = adapters[legacy_path]
    except KeyError as exc:
        raise ObservationAdapterError(
            f"no registered IV-B4 adapter for {legacy_path!r}"
        ) from exc
    return adapter(legacy)


def migration_payload(observation: Observation) -> str:
    """Return deterministic canonical JSON for verification/reporting."""

    return json.dumps(
        observation.to_canonical_data(),
        sort_keys=True,
        separators=(",", ":"),
    )
